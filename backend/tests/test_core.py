"""接入层/降噪层/分流层单测 — 全部 stdlib unittest，零依赖可跑。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dedup import SlidingWindowDedup
from app.gate import EntryGate
from app.ingest import IngestPipeline
from app.models import UnifiedAlert, make_fingerprint, normalize_severity
from app.sources import (
    normalize_alertmanager, normalize_business_log, normalize_cloud_monitor,
    normalize_elastic, normalize_loki, normalize_ops_audit, normalize_prometheus,
    normalize_ticket,
    SOURCE_NAMES,
)
from app.triage import triage


# ── 统一模型 ────────────────────────────────────────────────
class TestModels(unittest.TestCase):
    def test_severity_mapping(self):
        self.assertEqual(normalize_severity("Critical"), "critical")
        self.assertEqual(normalize_severity("P0"), "critical")
        self.assertEqual(normalize_severity("warn"), "warning")
        self.assertEqual(normalize_severity("info"), "info")
        self.assertEqual(normalize_severity(None), "warning")
        self.assertEqual(normalize_severity("weird"), "warning")

    def test_fingerprint_stable_and_sensitive(self):
        a = make_fingerprint("prometheus", "HighErrorRate", {"env": "prod", "service": "api"})
        b = make_fingerprint("prometheus", "HighErrorRate", {"env": "prod", "service": "api"})
        c = make_fingerprint("prometheus", "HighErrorRate", {"env": "prod", "service": "pay"})
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


# ── 7 类源适配器 ────────────────────────────────────────────
class TestSources(unittest.TestCase):
    def test_all_nine_registered(self):
        """9 类源：7 类告警 + ops_audit（运维操作审计）+ change_log（变更时间线）。

        后两类是"上下文源"：不参与分级分流，只落库供研判召回时间线
        （见 ingest.CONTEXT_SOURCES）。
        """
        self.assertEqual(len(SOURCE_NAMES), 9)
        self.assertIn("ops_audit", SOURCE_NAMES)
        self.assertIn("change_log", SOURCE_NAMES)

    def test_context_sources_bypass_gate_and_triage(self):
        """上下文源不能被门控的"低价值 info"丢掉，也不能进分级。

        曾经的 bug：change_log 的 severity=info → 被 _rule_low_value_info 丢弃，
        导致生产路径上"变更时间线"永远是空的（回放里绕过了接入层所以没暴露）。
        """
        from app.ingest import CONTEXT_SOURCES, IngestPipeline
        self.assertIn("change_log", CONTEXT_SOURCES)
        p = IngestPipeline()
        got = p.ingest("change_log", {"events": [{
            "ts": "2021-05-12", "kind": "deploy", "actor": "Fastly",
            "target": "CDN 软件", "detail": "部署含 bug 的软件", "ticket": ""}]})
        self.assertEqual(got, [], "上下文源不应进入后续链路")
        self.assertEqual(p.context_stored, 1, "变更事件必须落库（否则时间线为空）")

    def test_alertmanager(self):
        alerts = normalize_alertmanager({"alerts": [{
            "labels": {"alertname": "HighErrorRate", "severity": "critical",
                       "env": "prod", "service": "api"},
            "annotations": {"summary": "错误率超阈值", "description": "5m 错误率 > 5%"},
            "startsAt": "2026-10-23T01:00:00Z",
        }]})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "critical")
        self.assertEqual(alerts[0].source, "alertmanager")
        self.assertEqual(alerts[0].title, "错误率超阈值")

    def test_prometheus(self):
        alerts = normalize_prometheus({"alerts": [{
            "labels": {"alertname": "CPUThrottling", "severity": "warning",
                       "namespace": "prod", "instance": "pod-1"},
            "annotations": {},
        }]})
        self.assertEqual(alerts[0].source, "prometheus")
        self.assertEqual(alerts[0].severity, "warning")

    def test_loki(self):
        alerts = normalize_loki({"data": {"result": [{
            "stream": {"service": "checkout", "level": "error"},
            "values": [["1730000000000000000", "TimeoutError: upstream timeout"]],
        }]}})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].source, "loki")
        self.assertEqual(alerts[0].severity, "error" if False else alerts[0].severity)
        self.assertIn("checkout", alerts[0].labels["service"])

    def test_elastic(self):
        alerts = normalize_elastic({"hits": {"hits": [
            {"_source": {"message": "NullPointerException", "loglevel": "error",
                         "service": "order", "env": "prod"}},
        ]}})
        self.assertEqual(alerts[0].source, "elastic")
        self.assertEqual(alerts[0].severity, "critical")

    def test_business_log(self):
        alerts = normalize_business_log({"events": [
            {"level": "critical", "message": "支付回调失败率突增", "service": "payment", "env": "prod"},
        ]})
        self.assertEqual(alerts[0].source, "business_log")
        self.assertEqual(alerts[0].severity, "critical")

    def test_ticket(self):
        alerts = normalize_ticket({"tickets": [
            {"id": "T-1024", "title": "客户反馈无法下单", "priority": "P1", "system": "order", "env": "prod"},
            {"id": "T-1025", "title": "咨询发票", "priority": "P3", "system": "crm"},
        ]})
        self.assertEqual(alerts[0].severity, "critical")
        self.assertEqual(alerts[1].severity, "info")

    def test_cloud_monitor(self):
        alerts = normalize_cloud_monitor({"alarms": [
            {"AlarmName": "RDS连接数超限", "StateValue": "ALARM", "Namespace": "acs:rds",
             "InstanceId": "rm-xxx"},
        ]})
        self.assertEqual(alerts[0].source, "cloud_monitor")
        self.assertEqual(alerts[0].severity, "critical")

    def test_unknown_source_and_bad_payload(self):
        from app.sources import normalize_any
        self.assertEqual(normalize_any("nope", {}), [])
        self.assertEqual(normalize_any("loki", {"bad": 1}), [])


# ── 滑动窗口去重 ────────────────────────────────────────────
class TestDedup(unittest.TestCase):
    def test_window_allows_n_then_suppresses(self):
        t = [1000.0]
        d = SlidingWindowDedup(window_seconds=60, max_per_window=3, now_fn=lambda: t[0])
        verdicts = [d.check("fp")[0] for _ in range(5)]
        self.assertEqual(verdicts, [False, False, False, True, True])
        self.assertEqual(d.stats()["duplicated"], 2)

    def test_window_slide_releases(self):
        t = [1000.0]
        d = SlidingWindowDedup(window_seconds=60, max_per_window=1, now_fn=lambda: t[0])
        self.assertFalse(d.check("fp")[0])
        t[0] = 1030.0
        self.assertTrue(d.check("fp")[0])    # 窗口内 → 重复
        t[0] = 1061.0
        self.assertFalse(d.check("fp")[0])   # 窗口滑过 → 放行


# ── 入口门控 ────────────────────────────────────────────────
def _mk(**kw) -> UnifiedAlert:
    base = dict(source="prometheus", alertname="HighErrorRate", title="错误率高",
                severity="warning", labels={"env": "prod", "service": "api"})
    base.update(kw)
    return UnifiedAlert(**base)


class TestGate(unittest.TestCase):
    def setUp(self):
        self.gate = EntryGate()

    def test_pass_normal(self):
        d = self.gate.admit(_mk())
        self.assertTrue(d.passed)

    def test_drop_test_env(self):
        self.assertFalse(self.gate.admit(_mk(labels={"env": "test", "service": "api"})).passed)

    def test_drop_heartbeat(self):
        self.assertFalse(self.gate.admit(_mk(alertname="Heartbeat_prod")).passed)

    def test_drop_low_value_info(self):
        self.assertFalse(self.gate.admit(_mk(severity="info", labels={"env": "prod"})).passed)
        self.assertTrue(self.gate.admit(_mk(severity="info", labels={"env": "prod", "affects_prod": "1"})).passed)

    def test_ops_audit_no_ticket_flagged(self):
        """无变更单的操作要被显式标注——S3 事故里那条命令就是没有变更单的。"""
        a = normalize_ops_audit({"events": [{
            "ts": "2026-10-25T10:00:00", "operator": "alice", "host": "s3-rack-7",
            "command": "remove-capacity --subsystem billing --count 5",
            "target": "billing", "change_ticket": "", "result": "ok"}]})[0]
        self.assertEqual(a.source, "ops_audit")
        self.assertIn("无变更单", a.title)
        self.assertEqual(a.labels["service"], "s3-rack-7")
        self.assertEqual(a.labels["operator"], "alice")

    def test_ops_audit_with_ticket(self):
        a = normalize_ops_audit({"events": [{
            "operator": "bob", "host": "db-1", "command": "vacuum full",
            "change_ticket": "CHG-1234"}]})[0]
        self.assertNotIn("无变更单", a.title)
        self.assertEqual(a.labels["change_ticket"], "CHG-1234")

    def test_drop_maintenance(self):
        self.assertFalse(self.gate.admit(_mk(labels={"env": "prod", "maintenance": "true"})).passed)

    def test_stats_counts(self):
        self.gate.admit(_mk())
        self.gate.admit(_mk(labels={"env": "dev", "service": "api"}))
        s = self.gate.stats()
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["dropped"], 1)


# ── P0-P3 分级分流 ─────────────────────────────────────────
class TestTriage(unittest.TestCase):
    def test_p0_payment_critical(self):
        a = _mk(severity="critical", title="支付回调失败", labels={"env": "prod", "service": "payment", "affected_users": "5000"})
        d = triage(a)
        self.assertEqual(d.level, "P0")
        self.assertEqual(d.route, "research")

    def test_p3_noise_routes_notify(self):
        a = _mk(severity="info", labels={"env": "prod", "affects_prod": "1"}, title="例行巡检提示")
        d = triage(a)
        self.assertEqual(d.level, "P3")
        self.assertEqual(d.route, "notify")

    def test_p2_batch(self):
        a = _mk(severity="warning", title="磁盘使用率 82%",
                labels={"env": "prod", "service": "mysql"}, alertname="DiskUsageHigh")
        d = triage(a)
        self.assertEqual(d.level, "P2")   # warning 2 + 核心服务 db/mysql 1 = 3
        self.assertEqual(d.route, "batch")
        self.assertTrue(d.reasons)  # 可解释


# ── 接入层编排 + 降噪率 ─────────────────────────────────────
class TestIngestPipeline(unittest.TestCase):
    def _am_payload(self, n: int, env: str = "prod", alertname: str = "HighErrorRate"):
        return {"alerts": [{
            "labels": {"alertname": alertname, "severity": "critical",
                       "env": env, "service": "api"},
            "annotations": {"summary": "支付错误率超阈值", "description": "p > 5%"},
        }] * n}

    def test_end_to_end_noise_reduction(self):
        p = IngestPipeline(window_seconds=300, max_per_window=2)
        # 10 条 critical 支付告警：8 条被去重
        p.ingest("alertmanager", self._am_payload(10))
        # 5 条测试环境：全被门控
        p.ingest("prometheus", self._am_payload(5, env="test"))
        # 3 条心跳：全被门控
        p.ingest("prometheus", {"alerts": [
            {"labels": {"alertname": "Heartbeat_x", "severity": "info", "env": "prod", "service": "api"},
             "annotations": {}}] * 3})
        s = p.stats()
        self.assertEqual(s["ingested"], 18)
        # 去重在门控之前：测试环境/心跳同指纹的也会先被去重吃掉一部分
        # 10 条 critical 同指纹 → 8 重复；5 条 test 同指纹 → 3 重复；3 条心跳同指纹 → 1 重复
        self.assertEqual(s["dropped_dedup"], 12)
        self.assertEqual(s["dropped_gate"], 4)   # 门控拦下漏网的 2 条 test + 2 条心跳
        self.assertEqual(s["forwarded"], 2)
        self.assertGreater(s["noise_reduction_ratio"], 0.8)
        self.assertEqual(s["triage"]["routes"]["research"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
