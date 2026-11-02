# AIOps 知识地图 · 启动 / 使用 / 魔改指南

> 本仓库是从 [MansoorMajeed/infra-roadmap](https://github.com/MansoorMajeed/infra-roadmap)（MIT License, © 2026 Mansoor A）**浅克隆魔改**而来，作为我们「AIOps 知识体系 + 自研智能运维闭环」的底座。
> 原项目是「SRE/DevOps 交互式路线图」，用问答驱动的图谱组织知识；我们要做的是：**复用它的知识载体，往上叠加自研的 AI 诊断/编排/护栏能力**。

> ✅ **当前状态（已落地）**：
> ① 全站 UI 中文化（13 个 zone + 设置页 + 搜索等）；② 自研 `aiops` 分区（7 个中文知识节点）；③ 构建不依赖外网；
> ④ **人性化交互**：首步引导、完成庆祝、首页进度总览与「推荐下一步」；
> ⑤ **自研功能层**：`aiops` 节点内嵌「AI 助手」面板（🤖诊断 / 📚Runbook / ⚡执行），`🟢已知/🟡推测/⚪无法确认/💡建议` + 执行审批状态机；
> ⑥ **真后端**（`backend/`，Python + FastAPI）：9 类源接入（7 告警 + 运维审计 + 变更时间线） → 指纹滑动窗口去重 → 入口门控降噪 → P0-P3 分流 → SQLite 持久化工作流 → RAGFlow 检索 → 可插拔 LLM 研判 → 护栏审批 API；核心逻辑纯 stdlib、**117 个单测（含接口契约层与安全关卡）**；
> ⑦ **双模式前端**：AI 面板填后端地址即走真数据（CORS 已配 + payload 契约对齐 + 联调失败显示警示条，不再静默降级），未配置/后端不可达自动回退 mock，演示永不挂；
> ⑧ **实时告警染色**：后端 `/api/alerts` → 知识节点脉冲染红 + 🚨 等级徽标（同类后台系统没有的可视层）；
> ⑨ **压测量化**：`bench/flood.py` 1 万条告警风暴实测降噪 67.9%；**LLM 主链路占接入量 18.5%（相对全量进模型省 42.4%）**；端到端 HTTP 吞吐 37-93 QPS（瓶颈 SQLite 逐条 commit）——口径详见 `backend/bench/report.md`。
> ⑩ **生产级盲测**：虚拟机真实注入 8 场景（归因精度）+ 4 场景（SRE 排查链/处置分级），规则大脑 10/24 → DeepSeek 24/24，记录在 `vm-agent/TEST-RESULTS.md`。
>
> 📄 项目讲解与设计取舍见 `README.md` 与 `docs/`；运行方式见本文。

---

## 0. 已就位信息

| 项 | 值 |
|---|---|
| 克隆位置 | `D:\aiops-roadmap` |
| 许可证 | **MIT**（可自由修改、私有部署、商用，只需保留版权声明） |
| 前端 | Next.js 16 (App Router) + React 19 + TypeScript + Tailwind v4 + @xyflow/react + gray-matter + react-markdown，`output:"export"` 纯静态导出 |
| 后端 | **Python 3.10+ + FastAPI**（`backend/`），核心逻辑纯 stdlib（零框架依赖可单测），FastAPI 仅薄壳 |
| 已有内容 | 13 个 zone、300 个知识节点（foundations → kubernetes → observability → sre → aiops 全链路）；**中英双语，293/300 节点有译文**，右上角一键切换 |
| 测试 | 前端 vitest **46 例** + 后端 unittest **117 例**（含接口契约层与安全关卡：CORS/400/404/409/fail-closed/自动研判/鉴权/回滚深度/上下文源） |

---

## 1. 如何启动

### 1.1 前端（知识图谱）
```powershell
cd D:\aiops-roadmap
npm install        # 首次；常开 VPN 的话先设 $env:HTTPS_PROXY="http://127.0.0.1:10809"
npm run dev        # → http://localhost:3000
```
其他：`npm run build`（生产构建，严格校验 frontmatter）· `npm run test`（vitest 40 例）

### 1.2 后端（真数据研判，可选——不配前端自动走 mock）
```powershell
cd D:\aiops-roadmap\backend
pip install -r requirements.txt
uvicorn app.server:app --port 8600
python bench\flood.py --total 10000     # 压测 → bench/report.md + summary.json
```

**🖥️ 可视化大盘（拿给人看的主界面）**：起后端后打开 **`http://127.0.0.1:8600/dashboard`**——
实时告警流（P0 脉冲告警卡）、KPI 总览（接入量/降噪率/放行/护栏拦截/待审批/Token 节省）、
**多层下钻**（点告警卡 → 🟢已知/🟡推测/⚪无法确认 → RAG 命中 → 🛡️护栏判定 → ⚡dry-run 计划 + 确认/拒绝 → stage 时间线）、
审批中心、审计日志，3s 轮询。不配任何外部服务也能演示：大盘右侧「演示注入」可一键造 P0/重复/测试/心跳告警，直观看降噪与分流。

### 1.3 可选环境变量（不配则 mock 兜底，演示不依赖外部服务）
| 变量 | 说明 |
|---|---|
| `RAGFLOW_BASE_URL` / `RAGFLOW_API_KEY` / `RAGFLOW_DATASET_IDS` | 接本机 RAGFlow 做真实混合检索 |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | OpenAI 兼容端点（本机 vLLM/Ollama 27B 或云端），不配走规则兜底 |

前端连后端：任一 AIOps 节点 → AI 助手面板底部输入框填 `http://127.0.0.1:8600`（存 localStorage）。
之后：诊断/Runbook 走真实研判链路；图谱节点按实时告警染红（10s 轮询）；执行审批回写服务端审计。

---

## 2. 界面怎么用

1. **首页 / Zone 地图**：所有知识分区，点卡片进入；首次访问有引导卡，头部有总进度，零进度有 AIOps 入口推荐。
2. **Zone 内问答图谱**：节点之间用「学习者会问的问题」连边，只展开下一步，越探索越展开。
3. **⌘K 搜索**：跨全部分区秒搜。
4. **进度跟踪**：完成状态存 localStorage；标记完成弹庆祝 toast。
5. **节点详情面板（ContentPanel）**：Summary → Deep Dive → Milestones → Resources → Where to go next，底部是**自研 AI 助手面板**（仅 `aiops` 分区）与后端地址配置。

---

## 3. 内容格式（加知识只改 Markdown，不用碰代码）

每个节点 = `content/<zoneId>/<slug>.md`，**YAML frontmatter（zod 严格校验，缺一不可）+ 正文三段**。

```yaml
---
id: aiops-overview            # 全局唯一，连边靠它
title: 什么是 AIOps？
zone: aiops
edges:
  to:
    - id: aiops-stack
      question: AIOps 具体由哪些能力组成？
      detail: >-
        想搞清楚平台、模型、数据三层分别负责什么。
difficulty: 1                # 1 | 2 | 3
tags: [aiops, observability] # 字符串数组
category: concept            # concept | tool | practice | principle
milestones:                  # 进度跟踪
  - 理解 AIOps 解决的核心痛点
---
```

正文用 `<!-- DEEP_DIVE -->` / `<!-- RESOURCES -->` 分隔三段。
跨分区连边在 `content/_zones.yaml` 的 `zoneEdges`；节点 `edges.to[].zone` 渲染成「分区传送门」。

> ⚠️ zone 目录下所有 `.md` 都会被当节点加载（不跳过 `_` 前缀）——草稿/模板别放进去。

---

## 4. 自研架构：前端 + 后端全景

```
9 类源（7 告警：prometheus/alertmanager/loki/elastic/business_log/ticket/cloud
         + ops_audit 运维操作审计 + change_log 变更时间线）
        │
        ▼
[接入层] 归一化(UnifiedAlert+指纹) → 滑动窗口去重 → 入口门控降噪 → P0-P3 分流
        │  P0/P1→research 主链路        P2→batch        P3→notify(0 Token)
        ▼
[主链路] SQLite 持久化工作流（checkpoint / 节点级重试+退避 / 断点续跑 / 失败留痕）
        ▼
[上下文] RAGFlow 混合检索（真实 API 优先，mock 兜底）+ 指标/日志上下文
        ▼
[研判]   可插拔 LLM（OpenAI 兼容 / 规则兜底）→ 🟢已知 / 🟡推测 / ⚪无法确认 / 💡建议
        ▼
[护栏]   服务端强制关卡：T1-T4 风险分级 / 爆炸半径 / 冻结窗口 → 审批 API + 审计日志
        ▼
[执行]   dry-run 计划 → 人工审批 → StackStorm/Ansible 承接 → 回传状态
        ▼
[前端]   知识图谱（实时告警染色）+ AI 助手面板（真后端优先，mock 兜底）
```

### 文件地图

**前端（`src/`）**
| 文件 | 职责 |
|---|---|
| `lib/aiEngine.ts` | 编排入口：真后端优先（fetch `/api/research`），失败回退 mock；审批回写 `submitApproval` |
| `lib/guardrails.ts` | 前端等价护栏（演示用；真关卡在后端） |
| `lib/incidents.ts` | 实时告警 → 知识节点匹配（服务名→中文别称桥接） |
| `components/ContentPanel.tsx` | `AiAssistantPanel`：三动作按钮 + 四色结果 + 审批状态机 + 后端地址配置 |
| `components/NodeGraph.tsx` | 轮询 `/api/alerts`（10s），把告警注入节点 data |
| `components/NodeCard.tsx` | 节点卡：红色脉冲光环 + 🚨 等级徽标 |

**后端（`backend/`，核心全 stdlib）**
| 文件 | 职责 |
|---|---|
| `app/models.py` | UnifiedAlert 统一模型 + fingerprint |
| `app/sources.py` | 9 类源适配器（纯函数，坏报文跳过）；后两类是上下文源，只落库供召回 |
| `app/dedup.py` | 滑动窗口去重（同指纹窗口内只研判一次） |
| `app/gate.py` | 入口门控（测试环境/心跳/低价值 info/维护窗口，逐规则计数） |
| `app/triage.py` | P0-P3 可解释评分 + 三路分流 |
| `app/workflow.py` | 持久化工作流：SQLite checkpoint / 节点级重试+指数退避 / 断点续跑 / 失败留痕 |
| `app/rag.py` | RAGFlow 检索（真实 API 优先，mock 兜底） |
| `app/judge.py` | 可插拔研判（OpenAI 兼容端点 / 规则兜底） |
| `app/guardrail.py` | 护栏服务（风险分级 / 爆炸半径 / 冻结窗）+ 审计日志 |
| `app/pipeline_research.py` | 主链路组装：enrich→judge→guardrail→plan 四节点工作流 |
| `app/server.py` | FastAPI 薄壳：`/api/ingest` `/api/research` `/api/approve` `/api/alerts` `/api/runs/{id}` `/api/audit` `/api/stats` |
| `bench/flood.py` | 告警风暴压测 → `bench/report.md` + `summary.json` |
| `tests/` | 117 个单测（核心纯 stdlib + 接口契约） |

---

## 5. 为什么不用 Temporal（面试高频）

单机自用项目引入 Temporal = 多一个有状态服务 + SDK 学习成本，收益不匹配。
`backend/app/workflow.py` 用 SQLite checkpoint 实现了它的三个核心能力——**持久化、节点级重试、断点恢复**，
约 150 行、每一行讲得清；checkpoint 语义与 Temporal 对齐，未来迁移路径平滑。
测试见 `backend/tests/test_workflow_rag.py::test_checkpoint_resume_after_restart`（模拟进程崩溃后新引擎只补跑未完成节点）。

---

## 6. 压测与量化指标（简历数字都出自这里）

```powershell
cd D:\aiops-roadmap\backend
python bench\flood.py --total 10000
```
风暴构成：40% 真实告警（唯一指纹）+ 25% 精确重放 + 15% 测试环境 + 10% 心跳 + 10% info 噪声。
当前实测（本机）：**综合降噪 67.9%**（去重+门控）、**LLM 主链路占接入量 18.5%**（相对全量进模型省 42.4%）、
**端到端 HTTP 吞吐 37 QPS（短连接）/ 93 QPS（keep-alive）**（瓶颈：SQLite 逐条 commit）。
注意两个口径不要混用：**进程内纯函数吞吐 11.5 万条/秒**（bench/flood.py，算法上限）
≠ **系统吞吐**（含 HTTP/JSON/落库）。研判主链路 P95 约 100ms 是**规则大脑**口径。
详细口径与复现方式见 `backend/bench/report.md`。

### 研判能力盲测（A/B 实验，记录见 `vm-agent/TEST-RESULTS.md`）

两轮各 8 场景（跨应用/磁盘/CPU/K8s/服务/DNS/配置权限/下游依赖 8 层，真实虚拟机注入），
平台只见症状不见答案，固定 rubric 打分：

| 大脑 | 得分 | 说明 |
|---|---|---|
| A：规则兜底 | **10/24** | 7/8 场景误判为「依赖超时」（mock 知识库仅 1 篇 + 零推理） |
| B：DeepSeek LLM | **24/24** | 根因全命中；主动指出知识库不匹配、建议补充 Runbook、无指标时诚实标注「尚未确认」 |

结论：**RAG 覆盖决定上限，LLM 推理决定精度**；8 次研判总成本约 ¥0.05（LLM 只进 P0/P1 主链路）。

### 生产级场景盲测（P1-P4，2026-10-25，记录见 `vm-agent/TEST-RESULTS.md`）

第一轮之后按生产 SRE 标准重建了测试基建（真实服务 + 真实故障 + 看门狗实测 + 变更台账），
四个场景全部真实跑通（注入→看门狗→探针→证据采集→研判→大盘）：

| 场景 | 生产原型 | 平台输出 |
|---|---|---|
| P1 资源抢占 | 隔壁团队 make -j24 批处理吃满 CPU（90s） | 命中《资源抢占》剧本；证据：24 个忙循环进程 + 台账；🟢设 Limit/扩容 🔴驱逐需对方 owner 审批 |
| P2 跨部门变更 | 别的团队改坏 upstream 配置并重启 | 命中《变更引入故障》剧本；台账精确关联到 team-billing 09:19:41 的配置修改 |
| P3 内存耗尽 | 内存分析任务申请 1.4GB 逼近 OOM | 命中《OOMKilled》剧本；证据：mem-analyzer 进程 36.3% MEM + 内存守卫报警 |
| P4 服务断线 | **租用机器服务突然不可用** | 命中《节点/服务断线》剧本；自底向上证据：机器 uptime 14:35 没重启、kubelet/sshd 全 active、唯独 payment-api inactive → 判定服务级而非机器级 |

每场景输出：**根因 + 排查链（4 步带只读命令）+ 验证命令 + 处置分级（🟢可自动/🔴需审批+停机风险+审批人）+ dry-run 计划（爆炸半径）+ 原始证据**。
去重在真实故障下同样成立（P1 每秒 1 条 × 90s → 3 条告警；累计降噪 56.2%）。

### 真实事故回放（L3，2026-10-25，`vm-agent/replay/`）

前两轮的故障和答案都是自己设计的，有"自己出题自己答"的循环性。第三轮换成**第三方事实**：
4 个公开官方复盘事故（Cloudflare 2019 / AWS S3 2017 / GitLab 2017 / Meta 2021），
输入只含当时可观测症状，决定性步骤与真实根因跑前从复盘原文固定。

| 大脑 | 合成场景（L1） | **真实事故回放（L3）** |
|---|---|---|
| 规则兜底 | 10/24 | **5/12** |

**结论：合成场景测的是"链路通不通"，真实事故测的是"会不会看病"。** 暴露的结构性缺陷：
剧本系统是关键词路由而非诊断（3/4 匹配错剧本）；无运维操作审计数据源；无网络层/数据库层推理；
缺"控制面与数据面同链路""恢复路径自身受损"两个高阶模式。附带一次方法论自纠：
第一版评分器虚高（10/12），修正"通用样板不计分 + 禁用单字信号词"纪律后为 5/12，
纪律由 7 个测试锁死。路线：补剧本 → 接审计数据源 → LLM 重跑同一回放。

---

## 7. 与调研 OSS 的对接清单

| 能力 | 接哪个 OSS | 怎么接 |
|---|---|---|
| 告警接入 | 夜莺 Nightingale（v9 内置 MCP Server）/ Keep | webhook 进 `/api/ingest` |
| 根因分析 RCA | HolmesGPT / K8sGPT | `judge.py` 的 LLM 端点指向其接口 |
| 公司知识 / Runbook / 事故库 | **RAGFlow（本机已部署）** | 配 `RAGFLOW_*` 环境变量，`rag.py` 直接检索 |
| 执行与审计 | StackStorm / Robusta / Ansible | 审批通过后由 dry-run 计划承接（当前为演示态） |

---

## 8. 虚拟机实盘接线（造真错 → 平台真看见 → AI 真找根因）

完整步骤见 **`vm-agent/README.md`**，骨架：

1. **宿主机**：`uvicorn app.server:app --port 8600 --host 0.0.0.0 --reload`（⚠️ 不绑 0.0.0.0 虚拟机够不到），浏览器开 `/dashboard` 自检（点「💥 P0 支付故障」）。
2. **虚拟机**（vmrun 文件模式，宿主机 PowerShell）：
   ```powershell
   vmrun -T ws -gu tbt -gp 123 copyFileFromHostToGuest "$vmx" D:\aiops-roadmap\vm-agent\agent.py /tmp/agent.py
   vmrun -T ws -gu tbt -gp 123 runProgramInGuest "$vmx" /usr/bin/python3 /tmp/agent.py --selftest
   vmrun -T ws -gu tbt -gp 123 runProgramInGuest "$vmx" /bin/sh -c "cd /tmp && nohup python3 agent.py > /tmp/agent.log 2>&1 &"
   vmrun -T ws -gu tbt -gp 123 runProgramInGuest "$vmx" /bin/sh /tmp/inject.sh   # 造错
   ```
3. **预期**：10s 内大盘告警流出现 P0/P1「支付回调超时」→ 点「⚡ 送研判」看四层报告 → 审批/拒绝入审计。
4. **云端大脑**：后端设 `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL`（任意 OpenAI 兼容端点），`judge.py` 即切换真 LLM；`RAGFLOW_*` 同理接本机 RAGFlow。

> 探针 `agent.py` 零依赖、只做采集上报；造错脚本 4 类故障全部自动恢复（可重复跑）。

---

## 8.5 自动修复引擎与自愈实测（第四轮）

**为什么不做"无护栏全自动"**：系统在留出集上诊断正确率只有 2/6（见 §9 三层丈量），
让一个大概率判错的系统拿着高危命令全自动执行，是把小故障放大成事故的标准姿势。
行业真实形状（AWS/Google 的 auto-remediation）是：**动作白名单 + 有界爆炸半径
+ 执行后验证 + 失败回滚 + 全程审计**。

**引擎设计**（`backend/app/auto_remediation.py`）：

| 层 | 机制 |
|---|---|
| 动作登记表 | 4 个 A 类（清临时文件/终止失控进程/从备份恢复自己的配置/重启自己的服务）+ 7 个 B 类（drain 节点/删数据/恢复数据库备份/改 BGP/全局关 WAF/版本回滚/扩缩容） |
| 双端白名单 | 后端只登记动作下单；节点侧 agent（`vm-agent/selfheal/executor.py`）另持一份白名单，不认识的 action_id **拒绝执行**（防后端被注入伪造订单） |
| 执行后验证 | 每个动作带探针（process_gone / disk_below_pct / http_probe），验证不过 → 自动下回滚单 |
| 审批通道 | B 类可被人放行，但放行后仍须落在登记表内——**审批绕不过白名单** |
| 开关 | `AIOPS_AUTO_REMEDIATE=1` 才开启 A 类自动下单，默认关闭 |

**自愈实测**（`vm-agent/selfheal/`）：4 个真实故障 **4/4 被真正修好**
（3 个全自动 + S4 OOM 重启按设计被护栏拦下、由人放行后修好）。
判定标准是独立健康探针 `GET /healthz` 从 500 变回 200，检查的是真实状态
（配置是否合法 JSON、临时目录是否超配额、抢占比 = 墙钟/CPU 时间是否回落）。

```bash
# 后端带自动修复开关启动
AIOPS_AUTO_REMEDIATE=1 uvicorn app.server:app --port 8600
# 跑自愈实测
cd vm-agent/selfheal && python run_selfheal.py --out SELFHEAL-RESULTS.md
# 节点侧常驻 agent（生产形态）
python executor.py --loop --service sandbox-payment
```

---

## 8.6 中英双语（2026-10-26）

- **内容**：`content/<zone>/<slug>.md` 里用 `<!-- ZH_SUMMARY -->` / `<!-- ZH_DEEP_DIVE -->` /
  `<!-- ZH_RESOURCES -->` / `<!-- ZH_UI -->` 内联中文；frontmatter 加 `title_zh`。
  `content.ts` 在构建期切分，运行时零开销。**293/300 节点已翻译**（7 个 aiops 节点是中文原创）。
- **UI 外壳**：`src/lib/i18n.tsx` 的 `STRINGS` 表 + `useT()`。缺 en 回退 zh，缺 key 回退 key。
- **分区标题**：`_zones.yaml` 加 `title_en`（13/13）。
- **切换**：右上角 `GlobalControls`（中/EN + 深色模式），存 `localStorage`，同步 `<html lang>`。
- **校验**：`scripts/check_zh_ui.py` 扫全部内容，验证 `ZH_UI` 编号行数 == 里程碑 + 边数。
  当前 **293 篇对齐、0 错位**。
- **边界**：aiops 分区是中文原创，EN 模式下显示明确提示条，不假装已翻译。

## 8.7 RAGFlow 真实事故知识库（2026-10-26）

- `ragflow-kb/incident_docs.py`：6 个公开事故的结构化复盘（症状 / 红鲱鱼 / 真实根因 /
  决定性步骤 / 关联变更 / 止血处置 / 可复用经验）。
- `ragflow-kb/build_kb.py`：一键建库 → 上传 → 解析 → 轮询 → 抽检。打印 DATASET_ID
  填进 `RAGFLOW_DATASET_IDS`。支持云端 Starter / 自托管；本地地址强制不走代理。
- `ragflow-kb/verify_ragflow.py`：**零依赖** mock RAGFlow（实现 v0.27.2 契约 + 内置索引），
  用真实 `RagClient` 验证三条路径：真实优先 / 未配置回退 / 不可达回退。**三项全过**。
- ⚠️ **评测污染**：这 6 篇文档正好就是 replay/heldout 评测的 6 个事故，且都含「真实根因」。
  接 RAGFlow 后端跑评测会**分数虚高**。当前默认不配 RAGFlow（走 mock），评测仍有效。
  `ragflow-kb/check_eval_contamination.py` 可一键检测（实测确认会泄漏）。

## 8.8 Dify 工作流骨架（2026-10-26）

- `alert-diagnosis-workflow.yml`：可导入 Dify 的 DSL，`开始(alert) → LLM RCA → 结束`。
  LLM 节点输出固定结构：告警摘要 / 可能根因（按概率）/ 影响范围 / 建议处置 / 紧急等级。
- 定位：接执行层（StackStorm / Ansible）的"大脑"。
- 修过的问题：原文件 `\u` 转义后跟空格导致 YAML 解析失败（导不进 Dify），已修复。

## 8.9 智能体自主排查实测（2026-10-26）★

回答项目最核心的问题：**只给症状，大模型能不能自己查出根因？**

三组对照（`vm-agent/agentic/`）：

| 组 | 做法 | 静态 4 事故 | 动态真实系统 |
|---|---|---|---|
| A 单轮 | 只给症状，无工具 | 10/16 | — |
| **B 工具自主** | 只读工具，模型自己决定查什么 | **13/16** | **16/16** |
| C 喂全证据 | 证据全摆好塞 prompt | 16/16 | — |

- 四个世界里有一个是**完全虚构**的（两层网关配额缓存 TTL 不一致），训练数据里不存在：
  单轮 **0/4**、工具自主 **4/4** —— 证明它在真推理而非背答案。
- 动态组：真起进程、真写文件、真改配置、真杀进程，4/4 故障**独立验证真实生效**，模型 16/16。
- **结论：推理不是瓶颈，数据可得性才是瓶颈**（B→C 差的 3 分全是"没查到"）。
- 完整结论：`vm-agent/agentic/INTELLIGENT-OPS-VERDICT.md`；
  复现：`python run_agentic.py --api-key ...` / `python run_dynamic.py --api-key ...`

## 9. 下一步建议

0. **先看清诊断能力的边界**（`vm-agent/replay/REPLAY-SUMMARY.md` + `agentic/INTELLIGENT-OPS-VERDICT.md`）：
   - 规则大脑：合成 24/24 → 训练集 12/12 → **留出集 4/6**（走真实接入层口径）
   - 智能体自主排查：静态 13/16、动态真实系统 16/16
   - 结论：**剧本库是"记忆"；给模型工具+数据才是"推理"**。
   按性价比的下一步：① 补**指标时序源**（当前完全缺失，是最大瓶颈）；
   ② 把 `ops_audit` / `change_log` 接到真实系统（堡垒机 / 变更平台）；
   ③ 执行层从沙箱换成 kubectl（真正作用于集群）。
1. ✅ 已全部落地：知识图谱 + 人性化交互 + AI 助手面板 + 后端数据链路 + 护栏审批 + 告警染色 + 压测。
2. 真机联调：起后端 → 配 `RAGFLOW_*`（本机 RAGFlow）→ AI 面板填 `http://127.0.0.1:8600` → 看真 RAG 命中与告警染色。
3. 把 `judge.py` 的 `LLM_*` 指向本机 27B（vLLM/Ollama）替换规则兜底。
4. 可选：`src/lib/types.ts` 给 frontmatter 加 `guardrailTier` / `playbookRef` 字段，让护栏分级写进知识节点本身。
5. 可选：`NodeGraph` 增加告警点击 → 直接跳到对应研判 run 的详情。

---

## 附：本仓库与原版的差异（魔改记录）
- 新增 `AIOPS-GUIDE.md`、`frontend-showcase.html`、`backend/` 全目录。
- 全站 UI 中文化；新增 `content/aiops/` 知识节点；ContentPanel 增加自研 AI 助手面板 + 后端配置。
- "Improve this page" 链接对自研 `aiops` 分区自动隐藏（避免指向原作者仓库）。
