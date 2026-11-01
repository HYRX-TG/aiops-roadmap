"""接入层持久化 + 告警↔研判关联 单测。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingest import IngestPipeline
from app.ingest_store import IngestStore
from app.models import UnifiedAlert
from app.triage import triage
from app.workflow import Stage, WorkflowEngine, WorkflowStore

TMP = tempfile.gettempdir()


def _db(tag: str) -> str:
    return f"{TMP}/{tag}_{uuid4().hex[:8]}.db"


def _am_payload(service: str, severity: str, env: str = "prod", title: str = "支付回调失败率突增"):
    return {"alerts": [{
        "labels": {"alertname": "PayCallbackFail", "severity": severity,
                   "env": env, "service": service, "namespace": "prod"},
        "annotations": {"summary": title, "description": "p > 5%"},
    }]}


class TestIngestStore(unittest.TestCase):
    def test_forwarded_alert_recorded_with_level(self):
        store = IngestStore(_db("ing"))
        pipe = IngestPipeline(store=store)
        admitted = pipe.ingest("alertmanager", _am_payload("payment", "critical"))
        self.assertEqual(len(admitted), 1)
        rows = store.recent(10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["level"], "P0")
        self.assertEqual(rows[0]["route"], "research")
        self.assertEqual(rows[0]["service"], "payment")
        self.assertTrue(rows[0]["alert_json"]["labels"])   # 完整告警载荷已存

    def test_dropped_alerts_not_recorded(self):
        store = IngestStore(_db("ing"))
        pipe = IngestPipeline(store=store)
        pipe.ingest("alertmanager", _am_payload("cart", "critical", env="test"))  # 门控拦
        pipe.ingest("prometheus", {"alerts": [{
            "labels": {"alertname": "Heartbeat_x", "severity": "info", "env": "prod", "service": "api"},
            "annotations": {}}]})                                                  # 心跳拦
        self.assertEqual(len(store.recent(10)), 0)

    def test_duplicate_not_recorded_twice(self):
        store = IngestStore(_db("ing"))
        pipe = IngestPipeline(store=store)
        payload = _am_payload("order", "critical")
        pipe.ingest("alertmanager", payload)
        pipe.ingest("alertmanager", payload)   # 同指纹重放 → 去重
        rows = store.recent(10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(pipe.stats()["dropped_dedup"], 1)

    def test_research_run_links_by_fingerprint(self):
        ws = WorkflowStore(_db("wf"))
        eng = WorkflowEngine([Stage("noop", lambda ctx: {})], ws)
        alert = UnifiedAlert(source="alertmanager", alertname="PayCallbackFail",
                             title="支付回调失败率突增", severity="critical",
                             labels={"env": "prod", "service": "payment"})
        rid = eng.start(alert.fingerprint, {"alert": alert.to_dict(),
                                            "triage": {"level": "P0", "route": "research",
                                                       "score": 8.0, "reasons": ["x"]}})
        eng.run(rid)
        run = ws.latest_run_for_fingerprint(alert.fingerprint)
        self.assertIsNotNone(run)
        self.assertEqual(run["id"], rid)
        self.assertIsNone(ws.latest_run_for_fingerprint("nope"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
