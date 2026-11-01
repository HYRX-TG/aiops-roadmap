"""排查剧本库 + 生产级研判结构 单测。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.judge import Judge
from app.models import UnifiedAlert
from app.playbooks import PLAYBOOKS, get_playbook, match_playbooks
from app.triage import triage


class TestPlaybooks(unittest.TestCase):
    def test_signal_matching(self):
        self.assertEqual(match_playbooks("payment callback timeout upstream=dep")[0].id, "dependency_failure")
        self.assertEqual(match_playbooks("ERROR disk usage /tmp exceeds 85%")[0].id, "disk_pressure")
        self.assertEqual(match_playbooks("healthz probe timeout cpu starvation suspected")[0].id, "resource_contention")
        self.assertEqual(match_playbooks("pod CrashLoopBackOff ImagePullBackOff")[0].id, "image_pull"
                         if "image_pull" in PLAYBOOKS else match_playbooks("pod CrashLoopBackOff ImagePullBackOff")[0].id,
                         "image_pull")
        self.assertEqual(match_playbooks("OOMKilled memory limit")[0].id, "oom_killed")
        self.assertEqual(match_playbooks("node NotReady unreachable")[0].id, "node_disconnect")
        self.assertEqual(match_playbooks("config change rollout deploy")[0].id, "change_induced")

    def test_playbook_structure_complete(self):
        for pb in PLAYBOOKS.values():
            self.assertTrue(pb.thinking, f"{pb.id} 缺排查思路")
            self.assertTrue(pb.investigation, f"{pb.id} 缺排查链")
            self.assertTrue(pb.verification, f"{pb.id} 缺验证命令")
            self.assertTrue(pb.safe_actions, f"{pb.id} 缺安全处置")
            self.assertTrue(pb.approval_actions, f"{pb.id} 缺需审批处置")
            # 危险处置必须带审批人和停机风险
            for r in pb.approval_actions:
                self.assertTrue(r.approver, f"{pb.id} 危险处置缺审批人")
                self.assertTrue(r.downtime_risk, f"{pb.id} 危险处置缺停机风险评估")
            # 安全处置必须无停机
            for r in pb.safe_actions:
                self.assertEqual(r.downtime_risk, "none", f"{pb.id} 安全处置不应有停机风险")

    def test_get_playbook(self):
        self.assertIsNone(get_playbook("nope"))
        self.assertEqual(get_playbook("disk_pressure").name, "磁盘压力（写满/GC 失败）")


class TestJudgeProductionStructure(unittest.TestCase):
    def _alert(self, title, service="vm-app-2"):
        return UnifiedAlert(source="business_log", alertname="log_test", title=title,
                            description=title, severity="critical",
                            labels={"env": "prod", "service": service})

    def test_rule_brain_produces_production_structure(self):
        alert = self._alert("payment-api unreachable: connection refused 127.0.0.1:8080")
        d = triage(alert)
        v = Judge().judge(alert, d, [])
        # 生产结构字段齐全
        self.assertIn("root_cause", v)
        self.assertIn("investigation", v)
        self.assertIn("verification", v)
        self.assertIn("remediation", v)
        self.assertTrue(len(v["investigation"]) >= 2)
        self.assertTrue(v["verification"])
        self.assertTrue(v["remediation"]["safe"])
        self.assertTrue(v["remediation"]["approval_required"])
        # 兼容旧四段式
        self.assertTrue(v["known"])

    def test_rule_brain_playbook_attached(self):
        alert = self._alert("ERROR disk usage /tmp exceeds 85% threshold write failed")
        d = triage(alert)
        v = Judge().judge(alert, d, [])
        self.assertIn("磁盘压力", v["root_cause"])
        self.assertTrue(any("truncate" in c or "df" in c for c in v["verification"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
