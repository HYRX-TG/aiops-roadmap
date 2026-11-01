"""P0/P1 研判主链路：把「上下文增强 → 研判 → 护栏 → dry-run 计划」组装成持久化工作流。

每个 stage 都是 WorkflowEngine 的一个节点：独立重试 + checkpoint，
进程重启后 resume_all() 从断点续跑。
"""
from __future__ import annotations

from .auto_remediation import RemediationEngine, RemediationStore
from .audit_context import build_research_context
from .guardrail import GuardrailService
from .judge import Judge
from .models import UnifiedAlert
from .rag import RagClient
from .triage import TriageDecision
from .workflow import Stage, WorkflowEngine, WorkflowStore

# 动作 → dry-run 计划模板（真实执行由 StackStorm/Ansible 承接，此处只出计划与审批单）
_PLAN_TEMPLATES: dict[str, dict] = {
    "rollback": {"steps": ["确认最近一次发布版本", "kubectl rollout undo deploy/<svc>",
                            "等待 60s 健康探针通过", "观察 5m 错误率曲线确认恢复"],
                 "blast_radius": "namespace", "approver": "SRE on-call"},
    "scale_up": {"steps": ["确认当前副本与资源水位", "kubectl scale deploy/<svc> --replicas=N+2",
                            "观察 P99 与错误率"],
                 "blast_radius": "namespace", "approver": "值班工程师"},
    "restart":  {"steps": ["kubectl rollout restart deploy/<svc>", "等待健康探针通过"],
                 "blast_radius": "namespace", "approver": "SRE on-call"},
    "observe":  {"steps": ["加大采样密度观察 15m", "若恶化升级为 P1 人工介入"],
                 "blast_radius": "pod", "approver": ""},
}


def build_stages(rag: RagClient, judge: Judge, guardrail: GuardrailService,
                 ingest_store=None, remediation: RemediationEngine | None = None) -> list[Stage]:
    def s_enrich(ctx: dict) -> dict:
        alert = UnifiedAlert.from_dict(ctx["alert"])
        query = f"{alert.title} {alert.description} {alert.labels.get('service', '')}".strip()
        hits = rag.retrieve(query, alertname=alert.alertname,
                            service=alert.labels.get("service", "unknown"))
        # 节点侧排查证据（探针采集的 K8s/系统只读证据，附在 alert.raw.investigation）
        investigation = (ctx.get("alert", {}).get("raw") or {}).get("investigation", "")
        # 变更/操作时间线关联（L3 缺口修复）：把 ops_audit + change_log 按 host/service
        # 召回成时间线，作为根因关联的结构化证据（规则大脑消费 / LLM 提示词段）。
        ac = build_research_context(alert, ingest_store)
        return {"rag_hits": hits, "rag_backend": rag.last_backend,
                "investigation": investigation,
                "audit_timeline": ac["audit_timeline"],
                "ops_events": ac["ops_events"],
                "change_events": ac["change_events"]}

    def s_judge(ctx: dict) -> dict:
        alert = UnifiedAlert.from_dict(ctx["alert"])
        t = TriageDecision(**{k: ctx["triage"][k] for k in ("level", "route", "score", "reasons")})
        verdict = judge.judge(
            alert, t, ctx["rag_hits"], investigation=ctx.get("investigation", ""),
            audit_timeline=ctx.get("audit_timeline", ""),
            ops_events=ctx.get("ops_events"), change_events=ctx.get("change_events"))
        return {"verdict": verdict, "judge_backend": judge.last_backend}

    def s_guardrail(ctx: dict) -> dict:
        v = ctx["verdict"]
        text = f"{v.get('recommendation', '')} {v.get('root_cause', '')}"
        # fail-closed：识别不出动作 → unclassified（T4 需审批），绝不回落 observe 放行
        action = guardrail.classify(text)
        d = guardrail.evaluate(action)
        return {"suggested_action": action, "guardrail": d.__dict__}

    def s_plan(ctx: dict) -> dict:
        action = ctx["suggested_action"]
        v = ctx["verdict"]
        rem = v.get("remediation") or {}
        safe = rem.get("safe") or []
        approval = rem.get("approval_required") or []
        svc = ctx["alert"]["labels"].get("service", "<svc>")
        g = ctx.get("guardrail", {})
        # 护栏判定的爆炸半径是权威值：模板只提供 steps，不能覆盖它。
        # （曾经的 bug：else 分支用 observe 模板的 pod 覆盖了护栏的 cluster，
        #   审批人看到"爆炸半径 pod、审批人空"，而护栏实际判的是整个集群。）
        blast = g.get("blast_radius") or "pod"

        # 🟢 安全动作逐个标注"能否自动"及其理由——展示层与实际下单共用同一份闸门判定，
        # 杜绝"计划写着可自动、引擎却没下单"或反过来"计划写着需审批、引擎已自动执行"。
        auto_steps: list[dict] = []
        if safe:
            if remediation is not None:
                auto_steps = remediation.gate_candidates(
                    v.get("playbook") or "", safe)
            else:
                auto_steps = [{"text": a.get("action", "") if isinstance(a, dict) else str(a),
                               "auto": None, "reason": "闸门未接入"} for a in safe]

        lines_safe: list[str] = []
        for a, c in zip(safe, auto_steps if len(auto_steps) == len(safe) else [None] * len(safe)):
            txt = a.get("action", "") if isinstance(a, dict) else str(a)
            if c is None:
                lines_safe.append(f"🟢 可自动：{txt}")
            elif c.get("auto"):
                lines_safe.append(f"🟢 可自动执行：{txt}")
            else:
                lines_safe.append(f"🟡 待人工确认（{c.get('reason', '')}）：{txt}")

        if safe or approval:
            steps = lines_safe
            steps += [f"🔴 需审批（停机风险:{a.get('downtime', '?')} · 审批人:{a.get('approver', '?')}）：{a.get('action', '')}"
                      for a in approval]
            state = "pending_approval" if approval else "ready"
            approver = approval[0].get("approver", "") if approval else ""
        else:
            tpl = _PLAN_TEMPLATES.get(action, _PLAN_TEMPLATES["observe"])
            steps = [s.replace("<svc>", svc) for s in tpl["steps"]]
            state = "pending_approval"
            # 护栏判需人批时审批人不能为空（至少值班 SRE）
            approver = tpl["approver"] or (
                "SRE on-call" if g.get("needs_approval") else "")
        return {"plan": {"action": action, "steps": steps, "blast_radius": blast,
                         "approver": approver, "state": state,
                         "tier": g.get("tier"),
                         "safe_count": len(safe), "approval_count": len(approval),
                         "auto_candidates": auto_steps,
                         "note": "dry-run 计划：🟢通过闸门的动作可自动执行，其余必须人工审批；执行权在人，永不静默自动执行"}}

    return [
        Stage("enrich_context", s_enrich, max_retries=2),
        Stage("judge", s_judge, max_retries=2),
        Stage("guardrail", s_guardrail, max_retries=1),
        Stage("plan", s_plan, max_retries=1),
    ]


class ResearchPipeline:
    """研判主链路入口：start → run，全程 checkpoint。"""

    def __init__(self, db_path: str = "research.db", rag: RagClient | None = None,
                 judge: Judge | None = None, guardrail: GuardrailService | None = None,
                 remediation: RemediationEngine | None = None, ingest_store=None):
        self.rag = rag or RagClient()
        self.judge = judge or Judge()
        self.guardrail = guardrail or GuardrailService()
        self.store = WorkflowStore(db_path)
        self.ingest_store = ingest_store
        # 自动修复引擎（默认关闭；AIOPS_AUTO_REMEDIATE=1 开启）
        self.remediation: RemediationEngine = remediation or RemediationEngine(
            store=RemediationStore(), enabled=False)
        self.engine = WorkflowEngine(
            build_stages(self.rag, self.judge, self.guardrail, self.ingest_store,
                         self.remediation), self.store)

    def run(self, alert: UnifiedAlert, decision: TriageDecision) -> dict:
        run_id = self.engine.start(alert.fingerprint, {
            "alert": alert.to_dict(),
            "triage": {"level": decision.level, "route": decision.route,
                       "score": decision.score, "reasons": decision.reasons},
        })
        run = self.engine.run(run_id)
        self._maybe_remediate(run_id, run)
        return run

    # ── 研判完成 → 自动修复下单（这是"AI 真去修"的唯一入口） ──
    def _maybe_remediate(self, run_id: str, run: dict) -> None:
        """把剧本的🟢安全动作解析成白名单动作并下单；解析不出/高危一律留给人。

        注意这里的边界：**平台只下单，不执行**。执行在 VM/节点侧 agent，
        且 agent 自己还持有一份白名单（双端白名单，纵深防御）。
        """
        if not self.remediation.enabled or run.get("status") != "done":
            return
        ctx = run.get("context") or {}
        v = ctx.get("verdict") or {}
        pb_id = v.get("playbook") or ""
        safe = (v.get("remediation") or {}).get("safe") or []
        svc = ((ctx.get("alert") or {}).get("labels") or {}).get("service", "unknown")
        orders = self.remediation.plan_orders(run_id, pb_id, safe, svc)
        if not orders:
            return
        self.store.patch_context(run_id, {"plan": {
            "auto_orders": [o["id"] for o in orders],
            "auto_actions": [o["action_id"] for o in orders],
            "auto_note": f"已自动下单 {len(orders)} 个白名单动作（等待节点侧 agent 执行+验证）",
        }})
        run["context"] = self.store.load_run(run_id)["context"]

    def resume(self) -> list[str]:
        return self.engine.resume_all()
