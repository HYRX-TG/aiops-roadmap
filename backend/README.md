# AIOps 研判后端（Temporal 简化版）

对标「AI Agent 智能告警运维研判系统」的后端补齐：**9 类源接入（7 告警 + 运维审计 + 变更时间线）→ 滑动窗口去重 → 入口门控降噪 → P0-P3 分级分流 → 持久化工作流（RAG 上下文 → 研判 → 护栏 → dry-run 计划）**，并自带压测出量化指标。

## 快速开始

```bash
cd backend
pip install -r requirements.txt        # 仅 fastapi/uvicorn/pydantic 三个依赖
uvicorn app.server:app --port 8600     # 服务壳
python bench/flood.py --total 10000    # 压测 → bench/report.md + summary.json
```

- **可视化大盘**：`http://127.0.0.1:8600/dashboard` —— 实时告警流 + 多层研判报告下钻 + 审批中心 + 审计日志，3s 轮询，开箱即用（不配任何外部服务也能演示：大盘右侧有「演示注入」按钮）。
- **虚拟机接线**：虚拟机要够到后端必须 `uvicorn app.server:app --port 8600 --host 0.0.0.0`（默认只绑 127.0.0.1）；探针与造错脚本见仓库 `vm-agent/`（含 vmrun 部署命令）。

单测（零依赖，纯 stdlib）：`python -m unittest discover -s tests`（117 个用例，含接口契约层与安全关卡）
> 接口契约测试需要 fastapi+httpx：`pip install -r requirements.txt pytest`

## 环境变量（可选，不配则走 mock 兜底，演示不依赖外部服务）

| 变量 | 说明 |
|---|---|
| `RAGFLOW_BASE_URL` / `RAGFLOW_API_KEY` / `RAGFLOW_DATASET_IDS` | 接本机 RAGFlow 做真实混合检索 |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | OpenAI 兼容端点（本机 vLLM/Ollama 27B 或云端）；不配 = 规则兜底（剧本库驱动） |
| `AIOPS_CORS_ORIGINS` | 允许跨域的来源（逗号分隔）。默认放行 localhost:3000/8600；生产必须收紧 |
| `AIOPS_AUTO_RESEARCH` | `1`（默认）：接入层放行的 P0/P1 自动进研判主链路；`0` = 手动送研判 |
| `AIOPS_AUTO_REMEDIATE` | `1`：对通过闸门的 A 类动作自动下单；默认 `0`（只出建议 + 审批单） |
| `AIOPS_REMEDIATION_AUTO_MAX_TIER` | 自动修复允许的最大风险等级，默认 `2`（T1/T2 可自动） |
| `AIOPS_REMEDIATION_AUTO_MAX_BLAST` | 自动修复允许的最大爆炸半径，默认 `pod`。注意护栏的 `blast_radius_max` 是硬顶 |
| `AIOPS_FREEZE_WINDOW` | `1`/`true` 开启变更冻结窗口：禁止一切自动执行（只能走紧急审批） |
| `AIOPS_AUTO_APPROVE_TIER` | 护栏自动放行阈值，默认 `1`（仅只读） |
| `AIOPS_BLAST_RADIUS_MAX` | 护栏允许的最大爆炸半径，默认 `namespace` |
| `AIOPS_API_TOKEN` | 设置后以下接口必须带 `X-AIOps-Token` 头：`/api/approve`、`/api/remediation/orders`、`/api/remediation/complete`、`/api/guardrail/config` |
| `AIOPS_MAX_BODY_BYTES` | 请求体上限，默认 1MB（超限 413） |

> 护栏配置还可在运行期通过 `POST /api/guardrail/config` 调整（带 token），
> 每次变更都进审计——值班在大促/故障中拉冻结窗用这个，不用重启服务。

## 模块地图

```
app/
  models.py           统一告警模型 + fingerprint（去重抓手）
  sources.py          9 类源适配器（7 告警源 + ops_audit 运维审计 + change_log 变更时间线）
  audit_context.py    变更/操作时间线关联（三级召回：精确 service → 语义 token → 全局近期）
  auto_remediation.py 自动修复引擎（动作白名单 + 双端校验 + 护栏闸门 + 验证回滚 + 回滚深度上限）
  dedup.py            滑动窗口去重（同指纹窗口内只研判一次）
  gate.py             入口门控降噪（测试环境/心跳/低价值info/维护窗口，逐规则计数）
  triage.py           P0-P3 可解释评分分流（research主链路/batch/notify三路）
  workflow.py         持久化工作流：checkpoint/节点级重试+退避/断点续跑/失败留痕
  rag.py              RAGFlow 检索（真实 API 优先，断连 mock 兜底）
  judge.py            可插拔研判（OpenAI 兼容 / 规则兜底），输出 已知/推测/不确定/建议
  guardrail.py        安全关卡（T1-T4 / 爆炸半径 / 冻结窗）+ evaluate_auto 自动执行闸门 + 审计
  pipeline_research.py 主链路组装：enrich→judge→guardrail→plan 四节点工作流
  server.py           FastAPI 薄壳（/api/ingest /api/research /api/approve /api/stats ...）
bench/flood.py        告警风暴压测 → 降噪率/分流分布/时延/Token节省 → report.md
tests/                117 个单测（核心纯 stdlib + 接口契约层）
```

## 为什么不用 Temporal（面试话术）

单机自用项目引入 Temporal = 多一个有状态服务 + SDK 学习成本，收益不匹配。
`workflow.py` 用 SQLite checkpoint 实现了它的三个核心能力——**持久化、节点级重试、断点恢复**，
约 150 行，每一行都讲得清；checkpoint 语义与 Temporal 对齐，未来迁移路径平滑。
