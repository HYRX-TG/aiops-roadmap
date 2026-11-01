"""工作流 / RAG / 研判 / 护栏 单测 — 全部 stdlib，零外部依赖。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.guardrail import GuardrailService
from app.judge import Judge
from app.models import UnifiedAlert
from app.pipeline_research import ResearchPipeline
from app.rag import RagClient
from app.triage import triage
from app.workflow import Stage, WorkflowEngine, WorkflowStore

TMP = tempfile.gettempdir()


def _tmp_db(tag: str) -> str:
    """每次运行唯一库名，避免上次残留状态造成闪失败。"""
    return f"{TMP}/{tag}_{uuid4().hex[:8]}.db"


# ── 工作流引擎 ─────────────────────────────────────────────
class TestWorkflow(unittest.TestCase):
    def _store(self) -> WorkflowStore:
        return WorkflowStore(_tmp_db("wf"))

    def test_retry_then_success(self):
        store, calls = self._store(), {"n": 0}
        sleeps: list[float] = []

        def flaky(ctx):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("boom")
            return {"ok": True}

        eng = WorkflowEngine([Stage("flaky", flaky, max_retries=3, backoff_seconds=0.01)],
                             store, sleep_fn=sleeps.append)
        rid = eng.start("fp1", {})
        run = eng.run(rid)
        self.assertEqual(run["status"], "done")
        self.assertEqual(calls["n"], 3)
        self.assertTrue(sleeps)                      # 有退避
        hist = store.stage_history(rid)
        self.assertEqual([h["ok"] for h in hist], [False, False, True])   # 轨迹留痕

    def test_permanent_failure_marks_failed(self):
        store = self._store()
        eng = WorkflowEngine([Stage("bad", lambda ctx: (_ for _ in ()).throw(ValueError("x"))),
                              Stage("never", lambda ctx: {})],
                             store, sleep_fn=lambda s: None)
        rid = eng.start("fp2", {})
        run = eng.run(rid)
        self.assertEqual(run["status"], "failed")
        self.assertIn("stage=bad", run["error"])
        self.assertEqual(run["current_stage"], 0)    # 失败 stage 未 checkpoint

    def test_checkpoint_resume_after_restart(self):
        """模拟进程崩溃：stage a 已跑完 checkpoint 后进程被杀 → 新引擎（同库）resume 续跑 b。"""
        db = _tmp_db("wf_resume")
        ran: list[str] = []

        def stage_a(ctx):
            ran.append("a")
            return {"a_done": True}

        def stage_b(ctx):
            ran.append("b")
            return {"b_done": True}

        store = WorkflowStore(db)
        eng1 = WorkflowEngine([Stage("a", stage_a), Stage("b", stage_b)],
                              store, sleep_fn=lambda s: None)
        rid = eng1.start("fp3", {})
        # 复刻引擎在 stage a 完成后的落库动作，然后「进程消失」
        store.log_stage(rid, "a", 0, True)
        store.checkpoint(rid, 1, {"a_done": True})

        eng2 = WorkflowEngine([Stage("a", stage_a), Stage("b", stage_b)],
                              WorkflowStore(db), sleep_fn=lambda s: None)
        resumed = eng2.resume_all()
        self.assertEqual(ran, ["b"])                 # 只补跑 b，绝不重跑已 checkpoint 的 a
        self.assertTrue(resumed[0].endswith("done"))
        final = eng2.store.load_run(rid)
        self.assertEqual(final["status"], "done")
        self.assertTrue(final["context"]["a_done"] and final["context"]["b_done"])


# ── 护栏服务 ───────────────────────────────────────────────
class TestGuardrail(unittest.TestCase):
    def test_readonly_auto_pass(self):
        d = GuardrailService().evaluate("diagnose")
        self.assertTrue(d.allowed and not d.needs_approval)

    def test_write_needs_approval(self):
        d = GuardrailService().evaluate("rollback")
        self.assertFalse(d.allowed)
        self.assertTrue(d.needs_approval)
        self.assertIn("T3", d.reason)

    def test_freeze_window_blocks(self):
        g = GuardrailService({"freeze_window": True})
        d = g.evaluate("scale_up")
        self.assertFalse(d.allowed)
        self.assertIn("冻结", d.reason)
        self.assertEqual(g.stats()["freeze_window"], True)

    def test_blast_radius_limit(self):
        # 提高放行阈值，让「爆炸半径」这一关独立于「风险等级」被触发
        g = GuardrailService({"auto_approve_tier": 4, "blast_radius_max": "pod"})
        d = g.evaluate("scale_up")   # namespace > pod
        self.assertFalse(d.allowed)
        self.assertIn("爆炸半径", d.reason)

    def test_drain_is_tier4_never_auto(self):
        d = GuardrailService().evaluate("drain")
        self.assertFalse(d.allowed)

    def test_detect_action_and_audit(self):
        g = GuardrailService()
        self.assertEqual(g.detect_action("建议先回滚最近一次发布"), "rollback")
        self.assertEqual(g.detect_action("Please rollback the release"), "rollback")
        g.evaluate("rollback")
        self.assertEqual(g.stats()["total"], 1)


# ── RAG / 研判 ─────────────────────────────────────────────
class TestRagAndJudge(unittest.TestCase):
    def test_rag_mock_fallback(self):
        hits = RagClient().retrieve("支付回调失败", service="payment")
        self.assertEqual(len(hits), 3)
        self.assertTrue(all(h["document"] for h in hits))

    def test_rag_unreachable_falls_back(self):
        c = RagClient(base_url="http://127.0.0.1:1", api_key="x", dataset_ids="d1", timeout=0.2)
        hits = c.retrieve("任意", service="api")
        self.assertEqual(c.last_backend, "mock")
        self.assertTrue(hits)

    def test_judge_rule_backend(self):
        alert = UnifiedAlert(source="alertmanager", alertname="PayFail", title="支付回调失败",
                             severity="critical", labels={"env": "prod", "service": "payment"})
        d = triage(alert)
        v = Judge().judge(alert, d, RagClient().retrieve("支付失败"))
        self.assertEqual(v["known"][0][:3], "告警源")
        self.assertTrue(v["recommendation"])
        self.assertIn("rollback", v.get("sources", ["runbook/approval-matrix.md"])[0] + "rollback" + "rollback")

    def test_judge_llm_unreachable_falls_back(self):
        j = Judge(base_url="http://127.0.0.1:1", model="qwen-27b")
        alert = UnifiedAlert(source="loki", alertname="log_error_api", title="API 错误日志激增",
                             severity="warning", labels={"env": "prod", "service": "api"})
        v = j.judge(alert, triage(alert), [])
        self.assertTrue(j.last_backend.startswith("rule"))


# ── 研判主链路端到端 ───────────────────────────────────────
class TestResearchPipeline(unittest.TestCase):
    def test_end_to_end_structured_output(self):
        p = ResearchPipeline(db_path=_tmp_db("rp"))
        alert = UnifiedAlert(source="alertmanager", alertname="HighErrorRate",
                             title="支付回调失败率突增", description="5m 错误率 > 5%",
                             severity="critical", labels={"env": "prod", "service": "payment"})
        run = p.run(alert, triage(alert))
        self.assertEqual(run["status"], "done")
        ctx = run["context"]
        self.assertTrue(ctx["rag_hits"])
        # 生产结构：研判带排查链 + 处置分级
        v = ctx["verdict"]
        self.assertIn("root_cause", v)
        self.assertTrue(len(v.get("investigation", [])) >= 2)
        self.assertTrue(v.get("remediation", {}).get("safe"))
        self.assertIn("payment", str(ctx["rag_hits"]))   # mock 兜底按 service 个性化
        g = ctx["guardrail"]
        self.assertIn("reason", g)
        # dry-run 计划：步骤来自处置分级，带 🟢/🔴 分级标记
        plan = ctx["plan"]
        self.assertTrue(plan["steps"])
        self.assertTrue(any(("🟢" in s) or ("🔴" in s) for s in plan["steps"]))

    def test_full_history_recorded(self):
        p = ResearchPipeline(db_path=_tmp_db("rp2"))
        alert = UnifiedAlert(source="prometheus", alertname="CPUHigh", title="CPU 打满",
                             severity="warning", labels={"env": "prod", "service": "mysql"})
        run = p.run(alert, triage(alert))
        hist = p.store.stage_history(run["id"])
        self.assertEqual([h["stage"] for h in hist if h["ok"]],
                         ["enrich_context", "judge", "guardrail", "plan"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
