"""回放实验的数据/计分纪律测试。

为什么需要：第一版实验的评分器自己虚高（单字关键词「段」匹配到"手段"、
通用样板被计成"覆盖事故特有步骤"），总分从 10/12 修正到真实的 5/12。
这些测试把当时的修正固化成纪律，防止以后有人（包括我自己）再把评分放水。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from incidents import INCIDENTS  # noqa: E402
from run_replay import SIGNALS, scored_steps, grade, coverage  # noqa: E402


class ReplayDataTest(unittest.TestCase):
    def test_every_incident_has_source_and_fixed_answers(self):
        for inc in INCIDENTS:
            self.assertTrue(inc.get("source", "").startswith("http"), inc["id"])
            self.assertTrue(inc.get("true_root_cause"), inc["id"])
            self.assertTrue(inc.get("evidence"), inc["id"])
            self.assertTrue(inc.get("alert", {}).get("severity"), inc["id"])

    def test_every_incident_has_non_generic_steps(self):
        """每个事故必须至少 2 个"需要真领域推理"的步骤，否则实验没意义。"""
        for inc in INCIDENTS:
            specific = [s for s in inc["decisive_steps"] if not s.get("generic")]
            self.assertGreaterEqual(len(specific), 2, inc["id"])

    def test_no_single_char_keywords(self):
        """单字信号词会制造假命中（「段」→"手段"），一律禁止。"""
        for iid, groups in SIGNALS.items():
            for group in groups:
                for kw in group:
                    self.assertGreater(len(kw), 1, f"{iid} 含单字信号词：{kw}")

    def test_signals_cover_all_incidents(self):
        for inc in INCIDENTS:
            self.assertIn(inc["id"], SIGNALS, inc["id"])
            self.assertEqual(len(SIGNALS[inc["id"]]), len(inc["decisive_steps"]), inc["id"])

    def test_generic_steps_never_score(self):
        """通用样板（看变更/时间线）即使命中也不计分——这是 5/12 的来由。"""
        inc = INCIDENTS[0]   # cloudflare：step3 是 generic
        cov = [False, False, True, False]
        scored = scored_steps(inc, cov)
        self.assertFalse(scored[2])
        self.assertEqual(sum(scored), 0)

    def test_grade_scale(self):
        self.assertEqual(grade([True, True], "x"), 3)
        self.assertEqual(grade([True], "x"), 2)
        self.assertEqual(grade([], "x"), 1)
        self.assertEqual(grade([], ""), 0)

    def test_coverage_matches_platform_text(self):
        """用平台真实输出文本验证：'wal' 能命中、'段' 类单字不存在。"""
        text = "replication lag: check wal retention and archiving on primary"
        self.assertTrue(coverage("gitlab-2017-db-deletion", text)[0])


class HeldOutTest(unittest.TestCase):
    """留出集纪律：它必须是真的"没见过"，否则泛化检验就没意义。"""

    def setUp(self):
        import heldout
        self.held = heldout

    def test_heldout_ids_never_overlap_training(self):
        """留出集事故不能与训练集重复——重复就等于把考题又给了一次。"""
        train_ids = {i["id"] for i in INCIDENTS}
        for inc in self.held.INCIDENTS:
            self.assertNotIn(inc["id"], train_ids, inc["id"])

    def test_heldout_has_own_signals_and_fixes(self):
        for inc in self.held.INCIDENTS:
            self.assertIn(inc["id"], self.held.SIGNALS, inc["id"])
            self.assertEqual(len(self.held.SIGNALS[inc["id"]]), len(inc["decisive_steps"]))
            self.assertIn(inc["id"], self.held.DECISIVE_FIXES, inc["id"])

    def test_heldout_no_single_char_keywords(self):
        for iid, groups in self.held.SIGNALS.items():
            for group in groups:
                for kw in group:
                    self.assertGreater(len(kw), 1, f"{iid} 含单字信号词：{kw}")

    def test_fix_signals_not_single_char(self):
        from fixes import DECISIVE_FIXES
        for name, table in (("train", DECISIVE_FIXES), ("heldout", self.held.DECISIVE_FIXES)):
            for iid, spec in table.items():
                self.assertTrue(spec.get("text"), iid)
                self.assertTrue(spec.get("note"), iid)
                for s in spec.get("signals", []):
                    self.assertGreater(len(s), 1, f"{name}/{iid} 含单字信号词：{s}")


if __name__ == "__main__":
    unittest.main()
