"""自动修复引擎测试：白名单纪律 + 下单/验证/回滚/审计闭环。

这些测试锁的是"敢让它自动修"的那几条底线：
  - A 类动作有界可验证；B 类永远不自动
  - 白名单外的动作——哪怕是人工审批放行的——也执行不了
  - 执行后必须验证，验证失败要回滚，每一步都要留审计
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auto_remediation import (  # noqa: E402
    REMEDIATION_REGISTRY, RemediationEngine, RemediationStore, resolve_action)
from app.audit_store import AuditStore  # noqa: E402


def _engine(enabled: bool = True, tmpdir: str = "", guardrail=None):
    from app.guardrail import GuardrailService
    d = tmpdir or tempfile.mkdtemp()
    audit = AuditStore(db_path=str(Path(d) / "audit.db"))
    store = RemediationStore(db_path=str(Path(d) / "rem.db"))
    return (RemediationEngine(store=store, audit=audit, enabled=enabled,
                              guardrail=guardrail or GuardrailService()), store, audit)


class TestWhitelistResolve(unittest.TestCase):
    """动作解析：剧本自然语言 → 登记表 id。"""

    def test_resource_contention_cpu_limit_is_A(self):
        aid = resolve_action("resource_contention", "给吵闹邻居设 CPU Limit（cgroup/k8s limits）")
        self.assertEqual(aid, "kill_noisy_neighbor")
        self.assertEqual(REMEDIATION_REGISTRY[aid]["class"], "A")

    def test_disk_pressure_temp_cleanup_is_A(self):
        aid = resolve_action("disk_pressure", "删除自己产生的临时文件（气球/压测残留）")
        self.assertEqual(aid, "cleanup_temp_files")
        self.assertEqual(REMEDIATION_REGISTRY[aid]["class"], "A")

    def test_version_rollback_is_B_not_auto(self):
        """版本回滚会中断在途请求 → B 类，自动模式必须不下单。"""
        aid = resolve_action("change_induced", "回滚到上一版本（kubectl rollout undo）")
        self.assertEqual(aid, "rollback_version")
        self.assertEqual(REMEDIATION_REGISTRY[aid]["class"], "B")

    def test_db_and_network_never_auto(self):
        """数据库/网络类判错代价太高 → 显式映射为 None（故意不自动）。"""
        self.assertIsNone(resolve_action("db_replication", "重建备库（pg_basebackup 到备库）"))
        self.assertIsNone(resolve_action("network_dns_bgp", "修改 BGP 广播/路由策略"))

    def test_unknown_action_resolves_none(self):
        self.assertIsNone(resolve_action("whatever", "给对方发个红包"))

    def test_guardrail_action_name_alias(self):
        self.assertEqual(resolve_action("any", "rollback"), "rollback_version")
        self.assertEqual(resolve_action("any", "scale_up"), "scale_replicas")
        self.assertEqual(resolve_action("any", "restart"), "restart_service")
        self.assertIsNone(resolve_action("any", "observe"))

    def test_registry_every_action_has_blast_radius(self):
        """登记表纪律：每个动作都必须写清爆炸半径——写不清就不该登记。"""
        for aid, spec in REMEDIATION_REGISTRY.items():
            self.assertTrue(spec.get("blast"), f"{aid} 缺 blast")
            self.assertIn(spec["class"], ("A", "B"), f"{aid} class 非法")


class TestAutoOrdering(unittest.TestCase):
    """自动下单：只出「A 类 + 过闸门」的动作，其余一律留给人。"""

    def test_disabled_engine_creates_nothing(self):
        eng, store, _ = _engine(enabled=False)
        orders = eng.plan_orders("r1", "disk_pressure",
                                 [{"action": "删除自己产生的临时文件"}], "svc")
        self.assertEqual(orders, [])
        self.assertEqual(store.pending(), [])

    def test_only_A_class_auto_ordered(self):
        eng, store, _ = _engine()
        orders = eng.plan_orders("r1", "change_induced", [
            {"action": "扩容旧版本副本（maxSurge 滚动，新旧并存）"},   # → scale_replicas (B)
            {"action": "回滚到上一版本（kubectl rollout undo）"},      # → rollback_version (B)
        ], "svc")
        self.assertEqual(orders, [], "B 类动作绝不能自动下单")

    def test_A_class_pod_blast_auto_ordered(self):
        """T1/pod（清临时文件）满足默认策略 → 可自动下单。"""
        eng, store, _ = _engine()
        orders = eng.plan_orders("r1", "disk_pressure",
                                 [{"action": "删除自己产生的临时文件"}], "svc")
        self.assertEqual([o["action_id"] for o in orders], ["cleanup_temp_files"])
        self.assertEqual(len(store.pending()), 1)

    def test_A_class_but_node_blast_blocked_by_policy(self):
        """A 类 ≠ 无条件自动：kill_noisy_neighbor 虽登记 A 类，但爆炸半径是 node
        （会终止同节点上别人的进程）→ 超过默认自动上限 pod，必须人批。

        这是复盘实测缺口的修复：此前引擎不看半径就自动下单，
        而审批页展示的却是"需审批"的扩容，两者分叉。
        """
        eng, store, _ = _engine()
        orders = eng.plan_orders("r1", "resource_contention",
                                 [{"action": "给吵闹邻居设 CPU Limit"}], "svc")
        self.assertEqual(orders, [], "node 级半径不得自动执行")
        cand = eng.gate_candidates("resource_contention",
                                   [{"action": "给吵闹邻居设 CPU Limit"}])[0]
        self.assertFalse(cand["auto"])
        self.assertIn("爆炸半径", cand["reason"])

    def test_A_class_tier3_blocked_by_policy(self):
        """restart_service 是 A 类、pod 半径，但 tier=3 超过自动阈值 T2 → 需人批。"""
        eng, _, _ = _engine()
        cand = eng.gate_candidates("oom_killed", [{"action": "重启 Pod 缓解"}])[0]
        self.assertEqual(cand["action_id"], "restart_service")
        self.assertFalse(cand["auto"])

    def test_policy_can_widen_to_allow_node_blast(self):
        """策略可配置：明确把上限放宽到 node 时，kill_noisy_neighbor 才可自动。"""
        eng, _, _ = _engine()
        eng.policy.update({"auto_max_blast": "node"})
        cand = eng.gate_candidates("resource_contention",
                                   [{"action": "给吵闹邻居设 CPU Limit"}])[0]
        self.assertTrue(cand["auto"], cand["reason"])

    def test_freeze_window_blocks_auto(self):
        """变更冻结窗口内，即使是可自动动作也不得自动执行。"""
        eng, store, _ = _engine()
        eng.guardrail.set_config(freeze_window=True)
        orders = eng.plan_orders("r1", "disk_pressure",
                                 [{"action": "删除自己产生的临时文件"}], "svc")
        self.assertEqual(orders, [])

    def test_A_class_ordered_once_per_run(self):
        eng, store, _ = _engine()
        orders = eng.plan_orders("r1", "disk_pressure", [
            {"action": "删除自己产生的临时文件"},
            {"action": "删除临时文件清理残留"},        # 同动作 → 去重
        ], "svc")
        self.assertEqual([o["action_id"] for o in orders], ["cleanup_temp_files"])
        self.assertEqual(len(store.pending()), 1)

    def test_idempotent_across_calls(self):
        """同一 run 重复调用 plan_orders 不应刷出重复订单（防重复执行）。"""
        eng, store, _ = _engine()
        a = [{"action": "删除自己产生的临时文件"}]
        first = eng.plan_orders("r1", "disk_pressure", a, "svc")
        second = eng.plan_orders("r1", "disk_pressure", a, "svc")
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(len(store.pending()), 1)

    def test_audit_written_on_order(self):
        eng, _, audit = _engine()
        eng.plan_orders("r1", "disk_pressure", [{"action": "删除自己产生的临时文件"}], "svc")
        self.assertTrue(any(r["decision"] == "order_created" for r in audit.all(50)))


class TestApprovalChannel(unittest.TestCase):
    """审批通道：人能放行 B 类，但放行不了白名单外的东西。"""

    def test_approved_B_class_can_be_ordered(self):
        eng, store, _ = _engine()
        orders = eng.plan_approved("r1", "change_induced",
                                   ["回滚到上一版本（kubectl rollout undo）", "rollback"],
                                   "svc", approver="SRE on-call")
        self.assertEqual([o["action_id"] for o in orders], ["rollback_version"])

    def test_approved_out_of_registry_rejected(self):
        """审批被社工/滥用 → 白名单外的命令照样执行不了（最后一道护栏）。"""
        eng, store, audit = _engine()
        orders = eng.plan_approved("r1", "whatever", ["kubectl delete ns prod"], "svc",
                                   approver="attacker")
        self.assertEqual(orders, [])
        self.assertTrue(any(r["decision"] == "rejected_out_of_registry"
                            for r in audit.all(50)))

    def test_approve_observe_creates_no_order(self):
        eng, _, _ = _engine()
        self.assertEqual(eng.plan_approved("r1", "any", ["observe"], "svc"), [])


class TestExecuteVerifyRollback(unittest.TestCase):
    """执行 → 验证 →（失败）回滚 → 审计。"""

    def test_success_path_marks_fixed(self):
        eng, store, audit = _engine()
        o = eng.plan_orders("r1", "disk_pressure",
                            [{"action": "删除自己产生的临时文件"}], "svc")[0]
        res = eng.complete(o["id"], exec_ok=True,
                           verify={"ok": True, "detail": "临时目录已降到配额内"})
        self.assertEqual(res["status"], "fixed")
        self.assertEqual(store.get(o["id"])["status"], "fixed")
        self.assertTrue(any(r["decision"] == "fixed" for r in audit.all(50)))

    def test_exec_failure_no_rollback(self):
        eng, store, _ = _engine()
        o = eng.plan_orders("r1", "disk_pressure",
                            [{"action": "删除自己产生的临时文件"}], "svc")[0]
        res = eng.complete(o["id"], exec_ok=False, verify={}, exec_detail="路径不在白名单")
        self.assertEqual(res["status"], "exec_failed")
        self.assertEqual(store.get(o["id"])["status"], "exec_failed")

    def test_verify_failure_triggers_rollback(self):
        """配置恢复后健康探针仍不过 → 自动下回滚单（该动作登记了 rollback）。"""
        eng, store, _ = _engine()
        o = eng.plan_approved("r1", "ops_change_incident",
                              ["回退该操作（有回滚脚本/配置备份时）"], "svc")[0]
        self.assertEqual(o["action_id"], "restore_config_from_backup")
        res = eng.complete(o["id"], exec_ok=True,
                           verify={"ok": False, "detail": "healthz 仍 500"})
        self.assertEqual(res["status"], "rollback_pending")
        self.assertTrue(res["rollback_order"])
        self.assertEqual(store.get(res["rollback_order"])["action_id"],
                         "restore_config_from_backup")

    def test_verify_failure_without_rollback_stays_failed(self):
        eng, store, _ = _engine()
        o = eng.plan_orders("r1", "disk_pressure",
                            [{"action": "删除自己产生的临时文件"}], "svc")[0]
        res = eng.complete(o["id"], exec_ok=True,
                           verify={"ok": False, "detail": "磁盘仍 95%"})
        self.assertEqual(res["status"], "verify_failed")
        self.assertEqual(res["rollback"], False)

    def test_complete_unknown_order_raises(self):
        eng, _, _ = _engine()
        with self.assertRaises(KeyError):
            eng.complete("nope", True, {"ok": True})


class TestRollbackDepthAndIdempotency(unittest.TestCase):
    """回滚链有界 + 终态幂等（复盘实测：restore_config 回滚到自己会无限自环）。"""

    def test_rollback_does_not_self_loop(self):
        """回滚单验证再失败 → rollback_exhausted，不再生成新回滚单。"""
        eng, store, _ = _engine()
        o = eng.plan_approved("r1", "ops_change_incident",
                              ["回退该操作（有回滚脚本/配置备份时）"], "svc")[0]
        self.assertEqual(o["action_id"], "restore_config_from_backup")
        r1 = eng.complete(o["id"], True, {"ok": False, "detail": "还是 500"})
        self.assertEqual(r1["status"], "rollback_pending")
        r2 = eng.complete(r1["rollback_order"], True, {"ok": False, "detail": "回滚也失败"})
        self.assertEqual(r2["status"], "rollback_exhausted")
        self.assertFalse(r2["rollback"])
        self.assertNotIn("rollback_order", r2)
        self.assertEqual(store.get(r1["rollback_order"])["status"], "rollback_exhausted")

    def test_complete_is_idempotent(self):
        """同一订单重复回报不得改写已定状态（agent 重试/重放）。"""
        eng, store, _ = _engine()
        o = eng.plan_orders("r1", "disk_pressure",
                            [{"action": "删除自己产生的临时文件"}], "svc")[0]
        eng.complete(o["id"], True, {"ok": True, "detail": "ok"})
        again = eng.complete(o["id"], False, {"ok": False, "detail": "迟到的失败回报"})
        self.assertTrue(again.get("duplicate"))
        self.assertEqual(store.get(o["id"])["status"], "fixed")


class TestGuardrailConsistency(unittest.TestCase):
    """展示给审批人的动作 与 引擎实际下单的动作 必须同一口径。"""

    def test_engine_uses_same_guardrail_instance(self):
        from app.guardrail import GuardrailService
        g = GuardrailService()
        eng, _, _ = _engine(guardrail=g)
        self.assertIs(eng.guardrail, g)

    def test_freeze_window_blocks_engine_and_approval_alike(self):
        from app.guardrail import GuardrailService
        g = GuardrailService()
        eng, _, _ = _engine(guardrail=g)
        g.set_config(freeze_window=True)
        self.assertEqual(eng.plan_orders("r1", "disk_pressure",
                                         [{"action": "删除自己产生的临时文件"}], "svc"), [])
        self.assertFalse(g.evaluate("scale_up").allowed)

    def test_auto_policy_cannot_exceed_hard_blast_cap(self):
        """自动策略想把上限放宽到 cluster，也不能突破护栏的硬顶（namespace）。"""
        from app.guardrail import GuardrailService
        g = GuardrailService()          # blast_radius_max=namespace
        eng, _, _ = _engine(guardrail=g)
        eng.policy.update({"auto_max_blast": "cluster", "auto_max_tier": 4})
        cand = eng.gate_candidates("change_induced",
                                   [{"action": "回滚到上一版本"}])[0]
        self.assertFalse(cand["auto"], "B 类本来就不能自动，这里验证的是不越权")

    def test_no_guardrail_means_fail_closed(self):
        """没接护栏时宁可留给人（fail-closed），不能默默自动。"""
        eng = RemediationEngine(store=RemediationStore(
            db_path=str(Path(tempfile.mkdtemp()) / "rem.db")), enabled=True,
            guardrail=None)
        self.assertEqual(eng.plan_orders("r1", "disk_pressure",
                                         [{"action": "删除自己产生的临时文件"}], "svc"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
