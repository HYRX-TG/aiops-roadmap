# VM 故障注入实验手册（自己动手，看大盘怎么诊断与修复）

> 目标：让你在**自己的虚拟机**里制造真实故障，观察 AIOps 后端（`:8600`）如何
> 接入 → 分级 → 研判(RCA) → 护栏 → 出修复计划 → 进审批中心；再亲手执行真正的修复。
> 对应你知识图谱里 `智能运维 / AIOps` 节点讲的“告警 → 诊断 → 建议 → 闭环”。

---

## 0. 架构与数据流

```
  你的虚拟机(guest)               宿主机(host)
  ┌──────────────────┐   HTTP      ┌──────────────────────────────┐
  │ 你手动执行 break  │             │  AIOps 后端 :8600            │
  │ 命令（真破坏）    │             │  /api/ingest (Alertmanager格式)│
  │        │         │  POST       │      ↓                        │
  │  vm_probe.py     │ ──────────▶ │  归一化→去重→门控→分级(P0-P3)  │
  │  (只读采样)      │             │      ↓ P0/P1                  │
  └──────────────────┘             │  研判主链路: RAG→LLM/规则→护栏 │
                                   │      ↓                        │
                                   │  dry-run 计划 + 审批中心       │
                                   │      ↓                        │
                                   │  /dashboard 实时告警流          │
                                   └──────────────────────────────┘
                                         ↑ 浏览器打开看
```

关键点：**真正的故障是你制造的，真正的修复也是你执行的**；平台只做“诊断 + 建议 +
审批”，绝不静默自动执行（这是护栏的设计边界）。`vm_probe.py` 只是把“虚拟机里发生了什么”
翻译成后端认的告警格式送上去。

---

## 1. 前期准备（一次即可）

### 1.1 起后端（带 DeepSeek 才能出“真·LLM 研判”）
在宿主机 `D:\aiops-roadmap\backend` 起服务。两条路：
- **真研判（推荐）**：设 `LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`，并让 DeepSeek 调用走代理
  （你本机常开 VPN 系统代理 `127.0.0.1:10809`）：
  ```bat
  cd /d D:\aiops-roadmap\backend
  set LLM_BASE_URL=https://api.deepseek.com/v1
  set LLM_API_KEY=sk-你的key
  set LLM_MODEL=deepseek-chat
  set HTTPS_PROXY=http://127.0.0.1:10809
  uvicorn app.server:app --port 8600 --host 0.0.0.0 --reload
  ```
- **规则兜底（没 key 也行）**：不设这个环境变量，后端会用 `playbooks.py` 规则库出结构化
  排查链（免费、不烧 token），一样能看完整闭环，只是根因是“按剧本”而非“LLM 推理”。

> 不绑 `0.0.0.0` 虚拟机够不到（你之前的 AIOPS-GUIDE 已踩过）。

### 1.2 在虚拟机里找“能访问宿主后端”的 IP
VMware NAT 下，虚拟机看到的网关就是宿主：
```bash
ip route | grep default        # 记下 gateway，例如 192.168.×.1
```
这个 IP 就是后面 `--host` 的值。

### 1.3 把探针丢进虚拟机并跑起来
把 `vm_probe.py` 拷到虚拟机（guest）任意目录，后台运行：
```bash
# 监控 nginx / redis / mysql 三个服务，并探测 postgres(5432)、redis(6379) 端口
python3 vm_probe.py --host 192.168.×.1 --port 8600 \
    --services nginx,redis,mysql \
    --endpoints 127.0.0.1:5432:postgres,127.0.0.1:6379:redis
```
不破坏任何东西，只每 30s 采样一次。先跑 `--once` 确认能联通后端：
```bash
python3 vm_probe.py --host 192.168.×.1 --port 8600 --once
```

### 1.4 打开大盘
浏览器开 `http://192.168.×.1:8600/dashboard`（或宿主机本地开）。重点看三块：
**实时告警**（告警流 + 分级染色）、**审批中心**（修复计划 + 放行/拒绝）、**演示注入**（对照实验用）。

---

## 2. 实验清单

> 每个实验：**制造故障 → 看大盘 → 真修复 → 复盘**。
> 制造前先 `df -h` / `free -m` 确认空间够造、别把虚拟机真搞挂。
> 探针会在故障出现后 ~30s 内把告警送上去，去重窗 300s，所以反复造同一条不会刷屏。

### 实验 1 · 磁盘写满（DiskPressure）
- **知识图谱对应**：资源/容量管理
- **制造**（虚拟机里）：`dd if=/dev/zero of=/var/bigfile bs=1M count=2500`（约 2.5GB，先确认剩余 >3GB）
- **看大盘**：探针采到 `df` 使用率 > 85% → 发 `DiskPressure`(critical)。分级：critical=5 基础分 → **P1**，自动进研判主链路。报告里 `root_cause` 指向磁盘压力，`verification` 给 `df -h`/`du` 命令，`remediation` 分两档：🟢清理大文件/日志（可自动）、🔴扩容磁盘（需审批）。
- **真修复**：`rm -f /var/bigfile`
- **复盘**：爆炸半径=单节点；平台给的是“建议 + 审批单”，扩容这种有风险的操作必须人批，清理则是安全动作。

### 实验 2 · 杀掉关键服务（ServiceDown）
- **知识图谱对应**：可用性 / 自愈
- **制造**：`systemctl stop nginx`（探针监控列表里要有 nginx）
- **看大盘**：探针 `systemctl is-active nginx` 返回 inactive → 发 `ServiceDown`(critical, service=nginx)。若把 service 写成 `api`/`gateway`/`payment` 会再 +1 分更易到 P0。报告根因=进程退出，`remediation` 里有 `restart`（⚠️ 需审批，爆炸半径 namespace/pod）。
- **真修复**：`systemctl start nginx`
- **复盘**：这就是“人在回路”的典型——平台**不会**自动重启（除非开 `AIOPS_AUTO_REMEDIATE=1` 且节点侧 agent 拉单执行），默认只出计划等你批。

### 实验 3 · CPU 打满（CPUThrottling）
- **制造**：`stress --cpu 4`（没 stress 就用 `python3 -c "while True: pass"` 起 4 个）
- **看大盘**：`loadavg/nproc > 0.8` → 发 `CPUThrottling`(critical) → P1。报告根因=CPU 饱和，`verification` 给 `top`/`pid`，`remediation`：🟢限流/杀异常进程、🔴扩容副本。
- **真修复**：`pkill stress`
- **复盘**：与实验1 对比——CPU/内存类通常“先杀异常进程/调优”，扩容是有爆炸半径的高危动作，所以进审批。

### 实验 4 · 内存打满 / OOM 风险（MemoryPressure）
- **制造**：`stress --vm 2 --vm-bytes 80%`
- **看大盘**：`MemAvailable < 300MB` → 发 `MemoryPressure`(critical) → P1。报告提示 OOM 风险，`remediation`：🟢释放/重启服务、🔴扩容内存。
- **真修复**：`pkill stress`
- **复盘**：OOM 会连坐同机其他服务，所以这类哪怕只是“风险”也按 critical 进研判，比等真的 OOM 再报更靠前。

### 实验 5 · 依赖连不上 / 网络阻断（NetworkPartition）—— 真实版“P0 支付故障”
- **知识图谱对应**：AIOps 核心：告警 → 诊断 → 自愈闭环
- **制造（网络层）**：`iptables -A OUTPUT -p tcp --dport 5432 -j DROP`（阻断到 PG 的流量）
  或 **制造（服务层）**：`systemctl stop postgresql`
- **看大盘**：探针连 `127.0.0.1:5432` 失败 → 发 `NetworkPartition`(critical, service=postgres)；或 `ServiceDown`(service=postgres)。因为 `postgres/db` 在核心服务列表 + critical 基础分，描述里带“支付/下单”关键词再 +2 → **P0**，直接进研判主链路。报告根因=DB 不可达/依赖断连，`remediation`：🟢检查网络/放行、🔴恢复（回滚防火墙规则/重启依赖，需审批）。
- **真修复**：`iptables -D OUTPUT -p tcp --dport 5432 -j DROP` 或 `systemctl start postgresql`
- **复盘**：这就是大盘“演示注入 → P0 支付故障”的**真实版**。区别是：演示注入是假数据，这里是你在 VM 真造的故障，探针真探到、真上报、真走完整链路。

### 实验 6 · 降噪对照（不破坏，看接入层怎么“丢”告警）
- 打开大盘「演示注入」页，依次点：
  - **重复告警 ×5**：同指纹 5 条 → 滑动窗口去重只放 1 条，其余拦截（看 `dropped_dedup`）。
  - **测试环境 ×5**：`env=test` → 入口门控直接全丢（看 `dropped_gate`，规则 `test_env`）。
  - **心跳噪声 ×5**：`alertname=Heartbeat_*` + `info` → 门控 `heartbeat`/`low_value_info` 全丢。
- **复盘**：为什么“接入层降噪”重要——不丢这些，P0/P1 会被噪声淹没，研判主链路（烧 token）会被无效告警占满。这也是你后端 `triage.py` 评分模型 + `gate.py` 门控存在的意义。

---

## 3. 怎么看“它怎么修复”

大盘里一条 P0/P1 告警的完整轨迹：
1. **实时告警**：卡片按 P0/P1/P2/P3 染色，点开看到分级理由（评分逐项可解释）。
2. **研判报告**（点卡片下钻）：`root_cause` / `investigation` 排查链（带可执行的只读验证命令）/ `verification` / `remediation` 分 🟢可自动、🔴需审批。
3. **审批中心**：修复计划 + 爆炸半径 + 审批人。**你在这里点“放行”= 同意执行权交给你**；点“拒绝”= 只留审计。平台默认不开自动执行。
4. **真修复**：回到虚拟机执行实验里的“真修复”命令。修复后探针采到恢复 → 不再发新告警（恢复即清去重计时）。

> 想体验“平台真去修”：开 `AIOPS_AUTO_REMEDIATE=1` 且节点侧 agent 拉 `/api/remediation/orders`
> 执行白名单动作。但**默认关**，演示/教学就用“人批 + 手动修”最直观。

---

## 4. 安全与回收
- 造故障前先确认虚拟机有快照/可回收；`dd` 别超过剩余空间；`iptables` 规则记得 `-D` 删掉。
- 所有制造命令都**可逆**，按“真修复”一行就能回。
- 探针是只读采样，**不会**动你任何东西；`--simulate` 模式更是不破坏只发告警，适合先跑通链路。
- 跑完实验：`kill` 掉后台 `vm_probe.py` 即可。

---

## 5. 不想跑探针？手动上报也行
任何实验都能用一条 curl 直接喂后端（等价探针发出的报文）：
```bash
curl -s -X POST http://192.168.×.1:8600/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"source":"alertmanager","payload":{"alerts":[{"labels":{
        "alertname":"DiskPressure","severity":"critical","env":"prod",
        "service":"node","host":"<虚拟机名>","instance":"<虚拟机名>",
        "affects_prod":"true"},
      "annotations":{"summary":"磁盘使用率 92% 超阈值 85%",
        "description":"df: / 使用率 92%；建议清理大文件/日志或扩容。"}}]}}'
```
把 `alertname/service/severity/description` 换成对应实验即可（service 用 `db`/`api`/`payment` 等核心名更易到 P0）。
