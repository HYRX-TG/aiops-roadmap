# 虚拟机接线：造错 → 探针上报 → 平台看见 → AI 找根因

目标链路（你的原话："接两个虚拟机进去，搞一些报错，平台看到并自己找错误在哪，云端 API 当大脑"）：

```
┌─ 虚拟机 Server2（Ubuntu 22.04, 192.168.197.133）─┐     ┌─ 虚拟机 server1 ─┐
│  agent.py   探针：tail 错误日志 → POST /api/ingest  │     │  同样部署一份    │
│  inject-errors.sh  一键造 4 类错（自动恢复）          │     └────────┬────────┘
└──────────────────────┬─────────────────────────────┘              │
                       │  VMware NAT：guest → 宿主机 192.168.197.1:8600
                       │  （宿主机防火墙需放行 8600 入站，见步骤 0）
                       ▼
             ┌─ 宿主机后端（必须 --host 0.0.0.0！）──────────────┐
             │ /api/ingest → 去重/门控/分级 → 研判主链路          │
             │   → RAGFlow（知识）→ LLM（大脑：本机 27B 或云端 API）│
             │   → 护栏 dry-run 计划（人审批）                     │
             └──────────────────────┬───────────────────────────┘
                                    ▼
                      http://127.0.0.1:8600/dashboard
                      实时告警流 + 多层研判报告 + 审批中心 + 审计
```

## 三步跑通

### 0. ⚠️ 宿主机防火墙放行 8600（一次性，需管理员 PowerShell）
Windows 防火墙默认拦所有入站，虚拟机探针会被挡住。以**管理员身份**运行一次：
```powershell
New-NetFirewallRule -DisplayName "AIOps Backend 8600" -Direction Inbound -LocalPort 8600 -Protocol TCP -Action Allow -Profile Any
```
> 本机 VMnet8（NAT）地址是 **192.168.197.1**；guest 默认路由里的 192.168.197.2 是 NAT 网关虚拟 IP，**连不到宿主机进程**，所以探针地址必须填 `http://192.168.197.1:8600`。

### 1. 宿主机：后端要对虚拟机开放端口
```powershell
cd D:\aiops-roadmap\backend
uvicorn app.server:app --port 8600 --host 0.0.0.0 --reload
```
> ⚠️ **必须 `--host 0.0.0.0`**：默认只绑 127.0.0.1，虚拟机够不到。浏览器打开
> `http://127.0.0.1:8600/dashboard` 应看到大盘（先点「💥 P0 支付故障」自检注入链路）。

### 2. 虚拟机：部署探针 + 造错脚本（vmrun 文件模式，宿主机 PowerShell 执行）
```powershell
$vmx = "D:\vm 虚拟机\Server2\Clone of serverclone1.vmx"   # 第二个虚拟机换 server1.vmx
vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\agent.py /tmp/agent.py
vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\inject-errors.sh /tmp/inject.sh
# 连通性自检（应在大盘看到一条 SELFTEST 上报日志）
vmrun -T ws -gu <guest用户> -gp <guest密码> runProgramInGuest "$vmx" /usr/bin/python3 /tmp/agent.py --selftest
# 常驻探针
vmrun -T ws -gu <guest用户> -gp <guest密码> runProgramInGuest "$vmx" /bin/sh -c "cd /tmp && nohup python3 agent.py > /tmp/agent.log 2>&1 &"
```
> 坑位提醒（本机实测）：vmrun **不回传 stdout**，Guest 里的输出都落 `/tmp/wb_out.txt`、`/tmp/agent.log`，
> 要看得 `copyFileFromGuestToHost` 拷出来。别把长命令塞进 `-c` 参数（会被吞）。

### 3. 造错，看大盘
```powershell
vmrun -T ws -gu <guest用户> -gp <guest密码> runProgramInGuest "$vmx" /bin/sh /tmp/inject.sh
```
预期（10 秒内）：
1. 大盘 KPI「告警接入 +12、降噪率」变化，告警流出现 **P0/P1「支付回调超时」**（service=vm-app）；
2. 点告警卡「⚡ 送研判主链路」→ 展开四层报告：🟢已知 / 🟡推测 / ⚪无法确认 / RAG 命中 / 🛡️护栏判定 / ⚡dry-run 计划（含爆炸半径 + 审批人）+ stage 时间线；
3. 计划里点「✅ 确认执行 / ❌ 拒绝」→ 审计日志留下记录（"人是主导"全程可见）。

## 接云端 API 当大脑（judge 已留好插槽）
```powershell
# 后端环境变量（任意 OpenAI 兼容端点：DeepSeek / 通义 / vLLM / Ollama 均可）
$env:LLM_BASE_URL="https://api.deepseek.com/v1"     # 例：云端大脑
$env:LLM_API_KEY="sk-xxx"
$env:LLM_MODEL="deepseek-chat"
# 本机 27B 则指向你本地推理服务；不配 = 规则兜底，演示不断链
```
同理 `RAGFLOW_BASE_URL/API_KEY/DATASET_IDS` 接你本机 RAGFlow 做真实知识检索。

## 文件
| 文件 | 作用 |
|---|---|
| `agent.py` | 探针：tail 错误日志，窗口内 ≥3 条 ERROR 即上报（带去重冷却）；上报前自动采集节点侧只读证据（kubectl/ps/free/systemctl/台账） |
| `inject-errors.sh` | 造错：错误日志 ×12 + CPU 满载 30s + 磁盘气球 512M + nginx 停 60s（全部自动恢复） |
| `payment-api.py` | 演示服务：`/healthz` 真的做上游探测 + 固定工作量计算（CPU 被抢占时延迟线性上涨，故障才"可见"） |
| `investigate.sh` | 只读排查工具集：节点状态/资源水位/Top CPU·内存进程/Pod 全景/Warning 事件/变更台账/服务健康/网络连通 |
| `k8s-scenarios.sh` | **生产级场景注入器**：`P1` 资源抢占（make -j24 吵闹邻居 90s）、`P2` 跨部门变更（改坏 upstream 配置 60s）、`P3` 内存耗尽（1.4GB + 内存守卫 80s）、`P4` 服务断线（stop payment-api 60s）、`RESET` 清理 |
| `scenarios.sh` | 第一轮盲测注入器（S1-S8 日志文本级，见 TEST-RESULTS） |
| `TEST-PLAN.md` / `TEST-RESULTS.md` | 盲测协议与两轮实测结果（S1-S8 归因精度 + P1-P4 生产场景） |

## 生产级场景怎么跑（P1-P4）

```powershell
$vmx = "D:\vm 虚拟机\Server2\Clone of serverclone1.vmx"
# 一次性部署（探针 + 服务 + 排查工具 + 场景注入器）
vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\payment-api.py /tmp/payment-api.py
vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\k8s-scenarios.sh /tmp/k8s-scenarios.sh
vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\investigate.sh /tmp/investigate.sh
vmrun -T ws -gu <guest用户> -gp <guest密码> runProgramInGuest "$vmx" /bin/sh /tmp/k8s-scenarios.sh P1   # P1|P2|P3|P4|RESET
```

每个场景都自动完成：**注入真实故障 → 看门狗/内存守卫真实感知（超标才记 ERROR，带实测数字）→ 探针上报（附证据）→ 后端降噪 → 剧本命中 → 排查链+验证命令+处置分级 → 大盘展示 → 人工审批**，60-90s 后自动恢复。

> ⚠️ 前置：`payment-api.py` 要装到 Guest 的 `/usr/local/bin/` 并 `systemctl restart payment-api`
> （看 `k8s-scenarios.sh` 里 ensure_victim 的注释）；没有真实开销的服务，CPU 抢占测不出任何现象。

## 第二台虚拟机（server1）
把第 2 步的 `$vmx` 换成 `D:\vm 虚拟机\server1\server1.vmx` 再跑一遍即双节点；
造错时错开服务名（`AIOPS_SERVICE=vm-app-2`）便于在大盘区分来源。
