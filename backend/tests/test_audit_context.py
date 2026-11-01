"""audit_context（变更/操作时间线关联层）+ change_log 源 单测 —— 全部 stdlib，零外部依赖。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.audit_context import build_research_context
from app.judge import Judge
from app.models import UnifiedAlert
from app.sources import normalize_change_log, SOURCE_NAMES
from app.triage import triage


class TestChangeLogSource(unittest.TestCase):
    def test_normalize_change_log(self):
        alerts = normalize_change_log({"events": [{
            "ts": "2021-05-12", "kind": "deploy", "actor": "Fastly",
            "target": "CDN 软件", "detail": "部署含 bug 的软件", "ticket": ""}]})
        self.assertEqual(len(alerts), 1)
        a = alerts[0]
        self.assertEqual(a.source, "change_log")
        self.assertEqual(a.labels["service"], "CDN 软件")     # 目标存进 service，供关联召回
        self.assertEqual(a.labels["kind"], "deploy")
        self.assertEqual(a.severity, "info")

    def test_change_log_registered(self):
        self.assertIn("change_log", SOURCE_NAMES)


class TestAuditContext(unittest.TestCase):
    def _alert_with_events(self, ops=None, changes=None):
        raw = {}
        if ops:
            raw["ops_audit_events"] = ops
        if changes:
            raw["change_events"] = changes
        return UnifiedAlert(source="cloud_monitor", alertname="x", title="S3 错误率激增",
                            severity="critical", labels={"env": "prod", "service": "s3", "host": "s3"},
                            raw=raw)

    def test_embedded_ops_event(self):
        alert = self._alert_with_events(ops=[{
            "ts": "09:37", "operator": "S3 团队", "host": "s3",
            "command": "容量下线命令（参数输错）", "target": "大量服务器", "ticket": "无"}])
        ctx = build_research_context(alert)
        self.assertTrue(ctx["has_ops"])
        self.assertFalse(ctx["has_change"])
        self.assertIn("S3 团队", ctx["audit_timeline"])
        self.assertIn("参数输错", ctx["audit_timeline"])
        self.assertEqual(ctx["ops_events"][0]["actor"], "S3 团队")

    def test_embedded_change_event(self):
        alert = self._alert_with_events(changes=[{
            "ts": "2021-05-12", "kind": "deploy", "actor": "Fastly",
            "target": "CDN 软件", "detail": "部署含 bug 的软件", "ticket": "无"}])
        ctx = build_research_context(alert)
        self.assertTrue(ctx["has_change"])
        self.assertIn("部署", ctx["audit_timeline"])
        self.assertIn("CDN 软件", ctx["audit_timeline"])

    def test_empty_timeline(self):
        ctx = build_research_context(self._alert_with_events())
        self.assertFalse(ctx["has_ops"])
        self.assertFalse(ctx["has_change"])
        self.assertIn("时间线为空", ctx["audit_timeline"])


class TestRuleJudgeConsumesAudit(unittest.TestCase):
    """规则大脑应消费 ops_audit / 变更时间线：S3 类根因不再瞎猜。"""

    def test_ops_audit_routes_to_ops_change_playbook(self):
        alert = UnifiedAlert(source="cloud_monitor", alertname="S3ApiError",
                             title="S3 API 错误率激增", severity="critical",
                             labels={"env": "prod", "service": "s3", "host": "s3"},
                             raw={"ops_audit_events": [{
                                 "ts": "09:37", "operator": "S3 团队", "host": "s3",
                                 "command": "容量下线命令（参数输错，实际下线远多于预期）",
                                 "target": "index/placement 服务器", "ticket": "无"}]})
        v = Judge().judge(alert, triage(alert), [], ops_events=None)
        # 注意：judge() 不自动 build_research_context，这里直接验证 _judge_rule 的等价路径：
        # 通过 pipeline 的 build_research_context 取事件再喂入更贴近真实；
        # 此处校验 Judge 在给定 ops_events 时能命中运维变更剧本。
        from app.audit_context import build_research_context
        ac = build_research_context(alert)
        v2 = Judge().judge(alert, triage(alert), [],
                          ops_events=ac["ops_events"], change_events=ac["change_events"])
        self.assertEqual(v2["playbook"], "ops_change_incident")
        self.assertIn("参数输错", v2["root_cause"])
        self.assertTrue(any("运维操作审计" in s["step"] for s in v2["investigation"]))

    def test_change_event_routes_to_change_induced(self):
        alert = UnifiedAlert(source="alertmanager", alertname="GlobalEdge503",
                             title="全网 503 错误率飙升", severity="critical",
                             labels={"env": "prod", "service": "edge-cdn"},
                             raw={"change_events": [{
                                 "ts": "2021-05-12", "kind": "deploy", "actor": "Fastly",
                                 "target": "CDN 软件", "detail": "部署含 bug 的软件", "ticket": "无"}]})
        ac = build_research_context(alert)
        v = Judge().judge(alert, triage(alert), [],
                         change_events=ac["change_events"])
        self.assertIn("关联到近期部署", v["root_cause"])

    def test_unrelated_global_change_does_not_hijack_playbook(self):
        """全局近期变更只作参考，不能把无关告警判成"变更引入故障"。

        实测回归：上报一条别人的 edge-cdn 部署后，CPU 抢占告警被误判成
        change_induced（fallback 召回了全局变更并抢占了主剧本）。
        """
        alert = UnifiedAlert(source="alertmanager", alertname="CpuHog",
                             title="服务变慢 CPU 负载高", description="CPU 抢占",
                             severity="critical",
                             labels={"env": "prod", "service": "sandbox-payment"})
        unrelated = [{"ts": "2021-05-12", "kind": "change", "actor": "Fastly",
                      "host": "edge-cdn", "detail": "部署含 bug 的软件",
                      "change_type": "deploy", "ticket": "", "related": False}]
        v = Judge().judge(alert, triage(alert), [], change_events=unrelated)
        self.assertNotEqual(v.get("playbook"), "change_induced",
                            "全局无关变更不得抢占主剧本")
        self.assertEqual(v.get("playbook"), "resource_contention")

    def test_related_change_still_hijacks(self):
        """与本次对象相关的变更仍要抢占主剧本（否则变更关联能力就没了）。"""
        alert = UnifiedAlert(source="alertmanager", alertname="Edge503",
                             title="全网 503", description="多个站点 503",
                             severity="critical",
                             labels={"env": "prod", "service": "edge-cdn"})
        related = [{"ts": "2021-05-12", "kind": "change", "actor": "Fastly",
                    "host": "edge-cdn", "detail": "部署含 bug 的软件",
                    "change_type": "deploy", "ticket": "", "related": True}]
        v = Judge().judge(alert, triage(alert), [], change_events=related)
        self.assertEqual(v.get("playbook"), "change_induced")


if __name__ == "__main__":
    unittest.main(verbosity=2)
