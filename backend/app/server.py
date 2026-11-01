"""FastAPI 薄壳：把核心能力暴露为 HTTP API。

核心逻辑全在 app/ 纯 Python 模块里（可脱离本文件单测）；
本文件只做 参数解析 → 调核心 → 返回 JSON 的粘合。

启动：uvicorn app.server:app --port 8600
前端联调：设置页后端地址填 http://127.0.0.1:8600
"""
from __future__ import annotations

import os
import queue
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .audit_store import AuditStore
from .auto_remediation import REMEDIATION_REGISTRY, RemediationEngine, RemediationStore
from .guardrail import BLAST_RANK, GuardrailService
from .ingest import IngestPipeline, RESEARCH
from .ingest_store import IngestStore
from .models import UnifiedAlert, now_iso
from .pipeline_research import ResearchPipeline
from .sources import SOURCE_NAMES
from .triage import triage
from pathlib import Path
import json

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="AIOps 研判后端", version="1.1.0")

# ── CORS：前端（Next.js :3000 / 静态页）跨域访问后端的唯一放行点 ──
# 默认放行本地开发来源；生产部署用 AIOPS_CORS_ORIGINS="https://ops.example.com" 收紧。
# 之前没配中间件 → 浏览器 OPTIONS 直接 405，真后端模式 100% 不通（见 TEST-RESULTS 复盘）。
_CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "AIOPS_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:8600"
).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# 请求体上限（1MB）：防畸形大包打爆接入层
_MAX_BODY = int(os.environ.get("AIOPS_MAX_BODY_BYTES", str(1024 * 1024)))


@app.middleware("http")
async def _limit_body(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > _MAX_BODY:
            return JSONResponse({"detail": "payload too large"}, status_code=413)
    return await call_next(request)


ingest_store = IngestStore()
pipe = IngestPipeline(store=ingest_store)
guardrail = GuardrailService()
audit_store = AuditStore(db_path="audit.db")

# ── 自动修复引擎：默认关闭，AIOPS_AUTO_REMEDIATE=1 才对通过闸门的 A 类动作自动下单 ──
# 关闭时平台行为与之前完全一致（只出处置建议 + 审批单），开启后多一步"下单"。
# 必须注入同一个 guardrail 实例：自动下单与审批展示走同一套风险口径。
AUTO_REMEDIATE = os.environ.get("AIOPS_AUTO_REMEDIATE", "0") == "1"
remediation = RemediationEngine(store=RemediationStore(), audit=audit_store,
                                enabled=AUTO_REMEDIATE, guardrail=guardrail)

# 与 ResearchPipeline 共用同一个护栏实例——否则 /api/stats 的"护栏拦截数"
# 统计的是另一个对象的 audit，口径是错的（DeepSeek 复盘指出的第 4 类问题）。
# remediation 也在构造期注入，保证 plan 阶段看到的闸门判定与实际下单一致。
research = ResearchPipeline(db_path="research.db", guardrail=guardrail,
                           ingest_store=ingest_store, remediation=remediation)

# ── 自动研判消费者：接入层放行的 P0/P1 自动进主链路（可开关） ──
# AIOPS_AUTO_RESEARCH=0 则回到"自动分级 + 手动送研判"（演示/调试用）。
# 曾经的缺口：/api/ingest 只算 route=research 却没有消费者，所谓"闭环"
# 实际是"自动分级 + 手动触发"。
AUTO_RESEARCH = os.environ.get("AIOPS_AUTO_RESEARCH", "1") == "1"
_research_queue: "queue.Queue" = queue.Queue(maxsize=1000)


def _auto_research_worker() -> None:
    while True:
        item = _research_queue.get()
        try:
            alert, decision = item
            if decision.route == RESEARCH:
                research.run(alert, decision)
        except Exception:
            pass        # 自动研判失败不拖垮接入层，可手动补送
        finally:
            _research_queue.task_done()


def _enqueue_auto_research(admitted) -> None:
    if not AUTO_RESEARCH:
        return
    for alert, t in admitted:
        if t.route != RESEARCH:
            continue
        try:
            _research_queue.put_nowait((alert, t))
        except queue.Full:
            pass        # 队列满说明故障风暴中，丢弃自动研判（降级为手动）


if AUTO_RESEARCH:
    threading.Thread(target=_auto_research_worker, daemon=True,
                     name="auto-research").start()


class IngestBody(BaseModel):
    source: str
    payload: dict


class ResearchBody(BaseModel):
    source: str = "alertmanager"
    alert: dict          # UnifiedAlert 字段（alertname/title/labels/...）


class ApproveBody(BaseModel):
    run_id: str
    action: str          # rollback / scale_up / restart / observe / drain
    decision: str        # approved / rejected
    approver: str = "SRE on-call"
    note: str = ""


# ── 审批接口鉴权（可选）：AIOPS_API_TOKEN 设置后，/api/approve 必须带
#    X-AIOps-Token 头。复盘指出"审批接口无任何认证"——写操作的放行关口
#    不能裸奔。不设置 = 单机演示态（文档如实说明边界）。
_API_TOKEN = os.environ.get("AIOPS_API_TOKEN", "")


def _check_api_token(request: Request) -> None:
    if not _API_TOKEN:
        return
    if request.headers.get("X-AIOps-Token", "") != _API_TOKEN:
        raise HTTPException(401, "缺少或错误的 X-AIOps-Token（审批接口已启用鉴权）")


@app.get("/dashboard")
def dashboard():
    """可视化作战桌面：实时告警流 + 多层研判报告下钻 + 审批中心 + 审计日志。"""
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/")
def root():
    """根路径：服务名片（避免打开浏览器只看到 404）。"""
    return {
        "service": "AIOps 研判后端",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs（Swagger UI，可直接试每个接口）",
        "endpoints": {
            "GET /dashboard": "可视化作战桌面（实时告警流 + 研判报告下钻 + 审批中心）",
            "GET /api/health": "健康检查 + 支持的 7 类告警源",
            "POST /api/ingest": "告警接入（归一化→去重→门控→分级）",
            "POST /api/triage": "单条告警试算分级",
            "POST /api/research": "研判主链路（RAG→研判→护栏→dry-run 计划）",
            "GET /api/runs/{run_id}": "研判 run 详情 + stage 轨迹",
            "POST /api/runs/resume": "重启后恢复中断的工作流",
            "POST /api/approve": "人工审批（护栏放行/拒绝 + 审计）",
            "GET /api/alerts": "实时告警列表（前端图谱染色数据源）",
            "GET /api/audit": "审批审计日志",
            "GET /api/stats": "接入层 + 护栏统计",
        },
    }


@app.get("/api/health")
def health():
    return {"ok": True, "sources": list(SOURCE_NAMES), "time": now_iso()}


@app.post("/api/ingest")
def ingest(body: IngestBody):
    """告警接入（归一化→去重→门控→分级）。返回放行告警与分级结果。

    route=research 的 P0/P1 会同时进自动研判队列（AIOPS_AUTO_RESEARCH 可关），
    大盘告警流的 run_id 随之点亮——"接入即研判"的闭环在这里。
    """
    admitted = pipe.ingest(body.source, body.payload)
    _enqueue_auto_research(admitted)
    return {
        "admitted": [
            {"alert": a.to_dict(), "level": t.level, "route": t.route,
             "score": t.score, "reasons": t.reasons}
            for a, t in admitted
        ],
        "stats": pipe.stats(),
    }


@app.post("/api/triage")
def triage_one(alert: dict):
    """单条告警试算分级（调试用）。"""
    try:
        a = UnifiedAlert.from_dict(alert)
    except TypeError as exc:
        raise HTTPException(400, f"alert 字段不完整（缺少必填字段？）：{exc}")
    t = triage(a)
    return {"level": t.level, "route": t.route, "score": t.score, "reasons": t.reasons}


@app.post("/api/research")
def run_research(body: ResearchBody):
    """P0/P1 研判主链路：RAG 上下文 → 研判 → 护栏 → dry-run 计划（持久化工作流）。"""
    try:
        a = UnifiedAlert.from_dict(body.alert)
    except TypeError as exc:
        # 曾经的坑：alert 漏了 source 等必填字段 → from_dict 直接 TypeError → 500。
        # 契约错误必须回 400 + 说清缺什么，而不是让调用方看到一个无法定位的 500。
        raise HTTPException(400, f"alert 字段不完整（缺少必填字段？）：{exc}")
    t = triage(a)
    if t.route != "research":
        return {"skipped": True, "route": t.route,
                "msg": f"分级 {t.level} 走 {t.route} 路由，不进主链路（省 Token）"}
    run = research.run(a, t)
    return {"run_id": run["id"], "status": run["status"], "context": run["context"]}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = research.store.load_run(run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    run["stage_history"] = research.store.stage_history(run_id)
    return run


@app.post("/api/runs/resume")
def resume_runs():
    """进程重启后恢复中断的工作流（断点续跑）。"""
    return {"resumed": research.resume()}


@app.post("/api/approve")
def approve(body: ApproveBody, request: Request):
    """人工审批：护栏判定后的执行单，只有这里能放行写操作。

    闭环四件事（曾经的缺口：无校验、无回写、可重复审批、审计重启即丢）：
      ① run 必须存在（404）——不能给不存在的 run 盖章
      ② action 必须匹配该 run 的计划动作（400）——不能批了 A 动作去执行 B
      ③ 同一 run 只允许审批一次（409）——不能靠重复提交绕过
      ④ 审批结果写回 plan.state（approved/rejected）+ 审计落 SQLite
    鉴权：设置 AIOPS_API_TOKEN 后必须带 X-AIOps-Token 头（401）。
    """
    _check_api_token(request)
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(400, f"非法 decision：{body.decision}（只允许 approved/rejected）")

    run = research.store.load_run(body.run_id)
    if run is None:
        raise HTTPException(404, f"run 不存在：{body.run_id}")

    ctx = run.get("context") or {}
    planned_action = ctx.get("suggested_action") or (ctx.get("plan") or {}).get("action") or ""
    if planned_action and body.action != planned_action:
        raise HTTPException(
            400, f"action 不匹配：该 run 的计划动作是 {planned_action}，提交的是 {body.action}")

    plan_state = (ctx.get("plan") or {}).get("state", "")
    if plan_state in ("approved", "rejected"):
        raise HTTPException(409, f"该 run 已审批过（state={plan_state}），不可重复审批")

    d = guardrail.evaluate(body.action)
    allowed = d.allowed or (d.needs_approval and body.decision == "approved")

    # 审批结果回写 run（状态机闭环：pending_approval → approved/rejected）
    research.store.update_plan_state(
        body.run_id,
        "approved" if allowed else "rejected",
        decision=body.decision, approver=body.approver)

    # 审计先落库（重启不丢），再返回
    audit_store.record({
        "run_id": body.run_id, "action": body.action, "decision": body.decision,
        "approver": body.approver, "note": body.note, "guardrail_reason": d.reason,
        "tier": d.tier, "allowed": d.allowed, "executed": allowed,
    })

    # 审批放行 → 下单给节点侧 agent 执行（人批准 ≠ 可执行任意命令：
    # 动作仍须解析进白名单，解析不出就只留审计、不下单）
    orders: list[dict] = []
    if allowed:
        ctx2 = research.store.load_run(body.run_id)["context"]
        v = ctx2.get("verdict") or {}
        texts = [a.get("action", "") for a in
                 ((v.get("remediation") or {}).get("approval_required") or [])
                 if isinstance(a, dict)]
        texts.append(body.action)        # 兜底：护栏动作名（rollback/scale_up/...）
        svc = (ctx2["alert"]["labels"] or {}).get("service", "unknown")
        orders = remediation.plan_approved(
            body.run_id, v.get("playbook", ""), texts, svc, approver=body.approver)
        if orders:
            research.store.patch_context(body.run_id, {"plan": {
                "auto_orders": [o["id"] for o in orders],
                "auto_actions": [o["action_id"] for o in orders],
                "auto_note": f"审批放行 → 已下单 {len(orders)} 个白名单动作",
            }})

    return {"executed": allowed, "guardrail": d.__dict__,
            "plan_state": "approved" if allowed else "rejected",
            "remediation_orders": [o["id"] for o in orders],
            "msg": (f"已放行执行，下单 {len(orders)} 个白名单动作（节点侧 agent 执行+验证）"
                    if orders else
                    "已放行执行（dry-run 计划 → StackStorm/Ansible 承接）" if allowed
                    else "已拒绝/未放行，仅留审计记录")}


@app.get("/api/alerts")
def list_alerts(limit: int = 50):
    """实时告警流 = 接入层放行的告警（含 VM 探针上报）∪ 研判 run。

    每条接入告警按指纹关联最新研判 run（run_id/status/plan_state），
    大盘据此显示「送研判 → 报告已生成 → 待审批」的状态推进。
    """
    items: list[dict] = []
    seen_fp: set[str] = set()
    for row in ingest_store.recent(limit):
        seen_fp.add(row["fingerprint"])
        item = dict(row)
        run = research.store.latest_run_for_fingerprint(row["fingerprint"])
        if run:
            ctx = run.get("context") or {}
            item["run_id"] = run["id"]
            item["status"] = run["status"]
            item["level"] = (ctx.get("triage") or {}).get("level", row["level"])
            item["plan_state"] = (ctx.get("plan") or {}).get("state", "")
            item["updated_at"] = run.get("updated_at", row["received_at"])
        else:
            item["run_id"] = ""
            item["status"] = ""
            item["plan_state"] = ""
            item["updated_at"] = row["received_at"]
        items.append(item)
    # 手动研判（未经过接入层）的 run 也并入
    for run in research.store.recent_runs(limit):
        if run["fingerprint"] in seen_fp:
            continue
        ctx = run.get("context") or {}
        alert = ctx.get("alert", {}) or {}
        items.append({
            "fingerprint": run["fingerprint"], "source": alert.get("source", ""),
            "alertname": alert.get("alertname", ""), "title": alert.get("title", ""),
            "service": (alert.get("labels") or {}).get("service", ""),
            "severity": alert.get("severity", ""), "level": run.get("level", ""),
            "route": "research", "alert_json": alert,
            "received_at": run.get("updated_at", ""), "updated_at": run.get("updated_at", ""),
            "run_id": run["run_id"], "status": run["status"],
            "plan_state": (ctx.get("plan") or {}).get("state", ""),
        })
    return {"items": items[:limit], "count": len(items)}


@app.get("/api/audit")
def audit(limit: int = 200):
    """审批审计日志（SQLite 持久化，重启不丢；此前是进程内 list）。"""
    items = audit_store.all(limit)
    return {"count": audit_store.count(), "items": items}


class CompleteBody(BaseModel):
    order_id: str
    exec_ok: bool
    verify: dict
    exec_detail: str = ""
    service: str = ""          # agent 自报服务名（与服务端订单交叉校验）


class GuardrailConfigBody(BaseModel):
    freeze_window: bool | None = None
    auto_approve_tier: int | None = None
    blast_radius_max: str | None = None
    approver: str = "SRE on-call"


@app.get("/api/remediation/registry")
def remediation_registry():
    """修复动作白名单（双端白名单的"后端这一份"；节点侧 agent 还有一份）。"""
    return {"registry": REMEDIATION_REGISTRY, "enabled": remediation.enabled,
            "policy": remediation.policy, "guardrail": guardrail.config}


@app.get("/api/remediation/orders")
def remediation_orders(request: Request, service: str = "", status: str = "pending"):
    """节点侧 agent 拉取待执行订单（只返回 pending）。

    鉴权：设置 AIOPS_API_TOKEN 后必须带 X-AIOps-Token（订单含执行动作与服务名，
    泄露等于把刀递出去）。service 必填，缩小单次拉取范围。
    """
    _check_api_token(request)
    if status == "pending":
        items = remediation.store.pending(service)
    elif status == "all":
        items = remediation.store.recent(100)
    else:
        items = [o for o in remediation.store.recent(100) if o["status"] == status]
    return {"count": len(items), "items": items}


@app.get("/api/remediation/orders/{order_id}")
def remediation_order(order_id: str, request: Request):
    _check_api_token(request)
    order = remediation.store.get(order_id)
    if order is None:
        raise HTTPException(404, "order not found")
    return order


@app.post("/api/remediation/complete")
def remediation_complete(body: CompleteBody, request: Request):
    """agent 回报执行 + 验证结果 → 引擎判定 fixed / 触发回滚 / 记审计。

    exec_ok=false → exec_failed；verify.ok=true → fixed；
    verify 不过且有回滚动作 → 自动下回滚单（深度有上限）；否则 verify_failed。

    鉴权必须开：这个接口决定"修好了没有"，是审计链的一环。
    service 校验：agent 只能回报自己服务的订单（纵深防御的第二段）。
    """
    _check_api_token(request)
    order = remediation.store.get(body.order_id)
    if order is None:
        raise HTTPException(404, f"order 不存在：{body.order_id}")
    if body.service and order.get("service") and body.service != order["service"]:
        raise HTTPException(
            403, f"service 不匹配：订单属于 {order['service']}，回报的是 {body.service}")
    try:
        return remediation.complete(body.order_id, body.exec_ok, body.verify, body.exec_detail)
    except KeyError:
        raise HTTPException(404, f"order 不存在：{body.order_id}")


@app.post("/api/guardrail/config")
def guardrail_config(body: GuardrailConfigBody, request: Request):
    """运行期调整护栏（值班开关：大促/故障中拉冻结窗、收紧自动阈值）。

    这是安全配置，必须鉴权；每次变更都进护栏审计（谁在什么时候放宽了什么）。
    """
    _check_api_token(request)
    if body.freeze_window is None and body.auto_approve_tier is None \
            and body.blast_radius_max is None:
        raise HTTPException(400, "至少提供一个配置项")
    if body.blast_radius_max is not None and body.blast_radius_max not in BLAST_RANK:
        raise HTTPException(400, f"非法 blast_radius_max：{body.blast_radius_max}")
    if body.auto_approve_tier is not None and not (1 <= body.auto_approve_tier <= 4):
        raise HTTPException(400, "auto_approve_tier 必须在 1-4")
    cfg = guardrail.set_config(freeze_window=body.freeze_window,
                               auto_approve_tier=body.auto_approve_tier,
                               blast_radius_max=body.blast_radius_max)
    audit_store.record({
        "run_id": "", "action": "guardrail_config", "decision": "config_changed",
        "approver": body.approver, "note": json.dumps(cfg, ensure_ascii=False),
        "guardrail_reason": "护栏配置变更", "tier": 4, "allowed": True, "executed": False,
    })
    return {"config": cfg}


@app.get("/api/stats")
def stats():
    return {"ingest": pipe.stats(), "guardrail": guardrail.stats(),
            "audit": audit_store.snapshot(),
            "auto_research": AUTO_RESEARCH,
            "auto_remediate": remediation.stats()}
