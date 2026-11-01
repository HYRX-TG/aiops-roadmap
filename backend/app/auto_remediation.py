"""自动修复引擎（auto-remediation）：诊断 → 下单 → 执行 → 验证 →（失败）回滚 → 审计。

设计原则（回答"敢不敢让 AI 直接修"）：

  1. **动作白名单**：只有登记在册的动作能被执行。不登记 = 不存在。
     - A 类（可自动）：爆炸半径有界（只动自己的日志/临时文件/自己的配置备份）
       + 执行后可用探针验证 + 不中断业务。典型：清理临时文件、终止失控进程、
       从备份恢复自己的配置、重启自己的服务。
     - B 类（永远人工）：影响他人 / 不可逆数据操作 / 全局基础设施。
       典型：drain 节点、删数据、恢复数据库备份、改 BGP、全局关 WAF、版本回滚。
  2. **双端白名单**：后端只对登记动作下单；节点侧 agent 也持有一份白名单，
     不认识的 action_id 一律拒绝执行（纵深防御：后端被注入伪造订单也执行不了）。
  3. **执行后必须验证**：每个动作带 verify 探针；验证不通过 → 自动回滚（有回滚动作时）
     → 无论成败都记审计。
  4. **审批通道**：B 类动作**可以**被人工审批放行，但放行后仍需落在登记表内——
     "人批准"不等于"可以执行任意命令"，审批不能绕过白名单。
  5. **默认关闭**：AIOPS_AUTO_REMEDIATE=1 才开启 A 类自动下单。

这不是"把 kubectl 交给 LLM"。生产里 AWS/Google 的 auto-remediation 也是这个形状：
动作白名单 + 有界爆炸半径 + 验证回滚 + 审计。**能自动的不是"所有修复"，而是"这一类修复"。**
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
import weakref

from .audit_store import AuditStore
from .models import now_iso


# ── 动作登记表 ────────────────────────────────────────────────
# class         A=可自动 / B=永远人工
# tier          护栏风险等级（与 guardrail.ACTION_RISK 同口径）
# blast         人读的爆炸半径描述
# blast_radius  结构化爆炸半径（pod < node < namespace < service < global），
#               供护栏做上限比较，与 blast 语义必须一致
# verify_type   agent 执行完要跑的探针；rollback 验证失败时自动执行的动作
REMEDIATION_REGISTRY: dict[str, dict] = {
    # ── A 类：爆炸半径有界 + 可验证 + 不中断业务 ──
    "kill_noisy_neighbor": {
        "class": "A", "tier": 2,
        "desc": "终止失控的吵闹邻居进程（生产对应：给吵闹邻居设 CPU Limit，不杀对方进程）",
        "blast": "本节点的非业务进程", "blast_radius": "node",
        "downtime": "none", "verify_type": "process_gone",
        "rollback": None,
        "note": "沙箱内以终止本场景注入的进程等价实现；生产对应动作是设 cgroup limit（不杀对方）",
    },
    "cleanup_temp_files": {
        "class": "A", "tier": 1,
        "desc": "删除/截断本服务自己产生的临时文件与已轮转日志（不动业务数据）",
        "blast": "本服务的临时目录", "blast_radius": "pod",
        "downtime": "none", "verify_type": "disk_below_pct",
        "verify_value": 90, "rollback": None,
        "note": "只删白名单路径（sandbox-tmp/balloon/已轮转日志）；命中业务数据目录则拒绝执行",
    },
    "restore_config_from_backup": {
        "class": "A", "tier": 2,
        "desc": "从本服务自己的配置备份恢复配置（先留一份现场副本，随时可还原）",
        "blast": "本服务的配置文件", "blast_radius": "pod",
        "downtime": "brief", "verify_type": "http_probe",
        "rollback": "restore_config_from_backup",
        "note": "恢复前把当前（坏的）配置另存为 .broken，所以动作本身可逆",
    },
    "restart_service": {
        "class": "A", "tier": 3,
        "desc": "重启本节点自有服务进程（只影响自身，秒级恢复，可反复执行）",
        "blast": "本服务进程", "blast_radius": "pod",
        "downtime": "brief", "verify_type": "http_probe",
        "rollback": None,
    },

    # ── B 类：必须人工审批（判错时后果不可逆或影响他人） ──
    "rollback_version": {
        "class": "B", "tier": 3, "desc": "回滚服务版本（会中断在途请求，需评估版本差异）",
        "blast": "namespace", "blast_radius": "namespace",
        "downtime": "rolling", "verify_type": "http_probe",
        "rollback": None,
    },
    "scale_replicas": {
        "class": "B", "tier": 2, "desc": "扩容/缩容副本（改变容量与调度，成本与级联影响需人评估）",
        "blast": "namespace", "blast_radius": "namespace",
        "downtime": "none", "verify_type": "http_probe",
        "rollback": None,
    },
    "drain_node": {
        "class": "B", "tier": 4, "desc": "排水节点（该节点 Pod 全部驱逐重建）",
        "blast": "node", "blast_radius": "node",
        "downtime": "rolling", "verify_type": None, "rollback": None,
    },
    "restore_from_backup": {
        "class": "B", "tier": 4, "desc": "从备份恢复业务数据（不可逆数据操作，必须先证明备份可用）",
        "blast": "service", "blast_radius": "service",
        "downtime": "full", "verify_type": None, "rollback": None,
    },
    "restore_bgp_routes": {
        "class": "B", "tier": 4, "desc": "修改/恢复 BGP 广播（影响全局可达性）",
        "blast": "global", "blast_radius": "global",
        "downtime": "full", "verify_type": None, "rollback": None,
    },
    "disable_waf_rule": {
        "class": "B", "tier": 4, "desc": "全局关闭 WAF 规则（等于临时摘掉一层防护）",
        "blast": "global", "blast_radius": "global",
        "downtime": "none", "verify_type": None, "rollback": None,
    },
    "delete_data": {
        "class": "B", "tier": 4, "desc": "删除数据目录/业务数据",
        "blast": "service", "blast_radius": "service",
        "downtime": "full", "verify_type": None, "rollback": None,
    },
}

# 回滚链最大深度：回滚本身再失败时不再无脑下单（否则自环刷爆 agent 队列）
MAX_ROLLBACK_DEPTH = 1

# 终态：订单到达终态后拒绝再次 complete（防重复回报篡改状态机）
TERMINAL_STATUSES = {"fixed", "exec_failed", "verify_failed",
                     "rollback_exhausted", "rollback_pending"}

# ── 自动执行策略（A 类 ≠ 无条件自动）──────────────────────────
# 即使动作登记为 A 类，也必须同时满足：tier ≤ 阈值、爆炸半径 ≤ 上限、
# 不在冻结窗口、且有验证探针。默认值刻意保守：
#   auto_max_tier=2 + auto_max_blast=pod
#   → cleanup_temp_files(T1/pod)、restore_config_from_backup(T2/pod) 可自动
#   → restart_service(T3)、kill_noisy_neighbor(T2/node，影响同节点其他进程) 需人批
# 这就是"能自动的不是所有修复，而是这一类修复"的数值化表达。
def policy_from_env() -> dict:
    import os
    tier = os.environ.get("AIOPS_REMEDIATION_AUTO_MAX_TIER", "").strip()
    blast = os.environ.get("AIOPS_REMEDIATION_AUTO_MAX_BLAST", "").strip()
    return {
        "auto_max_tier": int(tier) if tier.isdigit() else 2,
        "auto_max_blast": blast or "pod",
    }


# ── 剧本安全动作 → 登记表动作的解析规则（跑前显式定义，不靠猜） ──
# (playbook_id 或 None=通配, 关键词组, action_id)
# 命中第一个规则即返回；解析不出 = 不自动执行（留给人）。
RESOLVE_RULES: list[tuple[str | None, tuple[str, ...], str]] = [
    # 资源抢占：给吵闹邻居设 limit → 沙箱等价为终止失控进程
    ("resource_contention", ("cpu limit", "吵闹邻居", "限流"), "kill_noisy_neighbor"),
    # 磁盘写满：清理自己的临时文件/轮转日志 → 直接可自动
    ("disk_pressure", ("临时文件", "轮转", "truncate", "日志"), "cleanup_temp_files"),
    ("disk_pressure", ("过期容器镜像", "镜像"), "cleanup_temp_files"),
    # 变更诱发：回到操作前状态 → 有备份即 A 类（先把现场另存）
    ("change_induced", ("回滚", "上一版本", "旧版本"), "rollback_version"),
    ("ops_change_incident", ("回退该操作", "回退", "配置备份", "恢复配置"),
     "restore_config_from_backup"),
    # 容量/副本：改副本数永远 B 类（成本与调度影响）
    (None, ("扩容", "副本", "replicas", "scale"), "scale_replicas"),
    # 重启类：重启自有服务 A 类；重启别人的/kubelet/机器 → 不映射（留人）
    ("oom_killed", ("重启 pod", "重启.*缓解", "重启服务"), "restart_service"),
    ("node_disconnect", ("重启 kubelet", "重启.*服务", "重启/重装"), "restart_service"),
    # 数据库：重建备库/WAL 归档 → 不可逆风险，一律不自动
    ("db_replication", ("重建备库", "pg_basebackup", "wal", "归档"), None),
    # 网络：DNS/BGP 全局基础设施 → 一律不自动
    ("network_dns_bgp", ("备用 dns", "bgp", "停用", "路由"), None),
    # ── 护栏动作名兜底（审批放行时用：审批传进来的是护栏分类名） ──
    # 放最后，优先级最低；^$ 锚定，避免误伤剧本里的自然语言文本
    (None, (r"^rollback$", r"^rollback_version$"), "rollback_version"),
    (None, (r"^scale_up$", r"^scale_down$", r"^扩容$"), "scale_replicas"),
    (None, (r"^restart$", r"^重启$"), "restart_service"),
    (None, (r"^drain$",), "drain_node"),
    (None, (r"^observe$", r"^观察$"), None),
]


def resolve_action(playbook_id: str, action_text: str) -> str | None:
    """把剧本里的处置动作文本解析为登记表动作 id。

    解析不出（返回 None）= 不下单。规则里显式写 None 的（如数据库/网络类）
    是"故意不自动"——那些动作判错代价太高，必须留给人。
    """
    import re
    low = (action_text or "").lower()
    for pb, kws, aid in RESOLVE_RULES:
        if pb and pb != playbook_id:
            continue
        if any(re.search(k, low) for k in kws):
            return aid
    return None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS remediation_orders(
    id TEXT PRIMARY KEY,
    run_id TEXT, service TEXT, action_id TEXT, params TEXT DEFAULT '{}',
    reason TEXT, status TEXT, created_at TEXT, updated_at TEXT,
    exec_result TEXT DEFAULT '', verify_result TEXT DEFAULT '', note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_orders_status ON remediation_orders(status, service);
"""


class RemediationStore:
    """修复订单持久化（SQLite）：下单/执行/验证/回滚每个状态迁移都留痕。"""

    def __init__(self, db_path: str = "remediation.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        weakref.finalize(self, RemediationStore._close, self._conn)

    @staticmethod
    def _close(conn):
        try:
            conn.close()
        except Exception:
            pass

    _COLS = ("id,run_id,service,action_id,params,reason,status,created_at,updated_at,"
             "exec_result,verify_result,note")

    def insert(self, order: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO remediation_orders(id,run_id,service,action_id,params,reason,status,"
                "created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (order["id"], order.get("run_id", ""), order.get("service", ""),
                 order["action_id"], json.dumps(order.get("params", {})),
                 order.get("reason", ""), order["status"],
                 order["created_at"], order["updated_at"]))
            self._conn.commit()

    def update(self, order_id: str, **fields) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        with self._lock:
            self._conn.execute(
                f"UPDATE remediation_orders SET {sets}, updated_at=? WHERE id=?",
                (*fields.values(), now_iso(), order_id))
            self._conn.commit()

    def get(self, order_id: str) -> dict | None:
        with self._lock:
            r = self._conn.execute(
                f"SELECT {self._COLS} FROM remediation_orders WHERE id=?", (order_id,)).fetchone()
        return self._to_dict(r) if r else None

    def pending(self, service: str = "") -> list[dict]:
        q = f"SELECT {self._COLS} FROM remediation_orders WHERE status='pending'"
        args: tuple = ()
        if service:
            q += " AND service=?"
            args = (service,)
        q += " ORDER BY created_at"
        with self._lock:
            rows = self._conn.execute(q, args).fetchall()
        return [self._to_dict(r) for r in rows]

    def recent(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {self._COLS} FROM remediation_orders "
                "ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._to_dict(r) for r in rows]

    def for_run(self, run_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {self._COLS} FROM remediation_orders WHERE run_id=? ORDER BY created_at",
                (run_id,)).fetchall()
        return [self._to_dict(r) for r in rows]

    def count_by_status(self) -> dict:
        with self._lock:
            rows = self._conn.execute(
                "SELECT status, COUNT(*) FROM remediation_orders GROUP BY status").fetchall()
        return {s: n for s, n in rows}

    @staticmethod
    def _to_dict(r: tuple) -> dict:
        return {"id": r[0], "run_id": r[1], "service": r[2], "action_id": r[3],
                "params": json.loads(r[4] or "{}"), "reason": r[5], "status": r[6],
                "created_at": r[7], "updated_at": r[8],
                "exec_result": r[9], "verify_result": r[10], "note": r[11]}


class RemediationEngine:
    """下单 / 判验证 / 触发回滚编排（不含执行——执行在节点侧 agent，双端白名单）。"""

    def __init__(self, store: RemediationStore | None = None,
                 audit: AuditStore | None = None,
                 enabled: bool = False,
                 guardrail=None,
                 policy: dict | None = None):
        self.store = store or RemediationStore()
        self.audit = audit
        self.enabled = enabled
        # 护栏实例（与研判主链路共用同一个）：自动下单前必须过它，
        # 否则"计划展示的动作"和"实际下单的动作"会分叉（复盘实测缺口）。
        self.guardrail = guardrail
        self.policy = dict(policy_from_env())
        if policy:
            self.policy.update(policy)

    # ── 候选动作的闸门判定（无副作用；plan 展示与下单共用同一份） ──
    def gate_candidates(self, playbook_id: str, safe_actions: list[dict]) -> list[dict]:
        """把剧本的🟢安全动作逐个解析 + 过闸门，返回每个候选的判定结果。

        展示层（plan）与执行层（下单）都调它，保证"看到的"和"要做的"是同一份判定。
        闸门判定本身委托给护栏（evaluate_auto）——风险口径只有一个来源。
        """
        out: list[dict] = []
        seen: set[str] = set()
        for a in safe_actions or []:
            text = a.get("action", "") if isinstance(a, dict) else str(a)
            aid = resolve_action(playbook_id, text)
            item = {"text": text[:120], "action_id": aid, "auto": False, "reason": ""}
            if not aid:
                item["reason"] = "解析不到白名单动作（留给人）"
                out.append(item)
                continue
            spec = REMEDIATION_REGISTRY.get(aid, {})
            item.update({"class": spec.get("class"), "tier": spec.get("tier"),
                         "blast_radius": spec.get("blast_radius"),
                         "action_desc": spec.get("desc", "")})
            if spec.get("class") != "A":
                item["reason"] = f"{aid} 属 B 类（必须人工审批）"
            elif aid in seen:
                item["reason"] = "同一 run 已评估过该动作（去重）"
            elif not spec.get("verify_type"):
                item["reason"] = "无验证探针（无法证明修好了，不允许自动）"
            elif self.guardrail is None:
                # 没有护栏就不许自动（fail-closed）：宁可留给人
                item["reason"] = "护栏未接入，禁止自动执行（fail-closed）"
            else:
                d = self.guardrail.evaluate_auto(
                    aid, tier=spec.get("tier", 4),
                    blast_radius=spec.get("blast_radius", "cluster"),
                    max_tier=self.policy["auto_max_tier"],
                    max_blast=self.policy["auto_max_blast"])
                item["auto"] = d.allowed
                item["reason"] = d.reason
            seen.add(aid)
            out.append(item)
        return out

    # ── 从研判结果生成自动修复订单（只出通过闸门的 A 类） ────
    def plan_orders(self, run_id: str, playbook_id: str, safe_actions: list[dict],
                    service: str) -> list[dict]:
        """只对"解析到 A 类且过闸门"的动作下单；其余一律跳过（留给人审批）。"""
        if not self.enabled:
            return []
        candidates = self.gate_candidates(playbook_id, safe_actions)
        for c in candidates:
            if not c["auto"] and c.get("action_id"):
                self._audit(run_id, c["action_id"], "guardrail_blocked",
                            f"自动下单被拦截（{c['reason']}）：{c['text']}")
        allowed = [{"action": c["text"]} for c in candidates if c["auto"]]
        return self._create(run_id, playbook_id, allowed, service,
                            require_class_a=True, prefix="自动下单", gated=True)

    # ── 人工审批放行后下单（B 类也可，但仍必须在登记表内） ──────
    def plan_approved(self, run_id: str, playbook_id: str, action_texts: list[str],
                      service: str, approver: str = "") -> list[dict]:
        """人批准 ≠ 可执行任意命令：动作仍须解析到登记表内，否则拒绝下单。

        这是护栏的最后一道：审批接口被滥用/被社工，也执行不了登记表外的东西。
        返回空列表表示"批准了但没有可执行动作"（要么解析不出，要么 observe 类）。
        """
        for text in action_texts or []:
            aid = resolve_action(playbook_id, text)
            if not aid:
                continue
            return self._create(run_id, playbook_id, [{"action": text}], service,
                                require_class_a=False,
                                prefix=f"人工审批放行（{approver or 'SRE'}）")
        self._audit(run_id, "unresolved", "rejected_out_of_registry",
                    f"审批放行的动作不在白名单内，拒绝下单：{action_texts[:2]}", approver)
        return []

    def _guardrail_allows(self, aid: str, spec: dict) -> tuple[bool, str, int]:
        """自动下单前的护栏判定（与展示给审批人的动作走同一口径）。"""
        if self.guardrail is None:
            return True, "未接入护栏（引擎独立运行）", spec.get("tier", 4)
        d = self.guardrail.evaluate_spec(
            aid, tier=spec.get("tier", 4),
            blast_radius=spec.get("blast_radius", "cluster"),
            read_only=False)
        return d.allowed, d.reason, d.tier

    def _create(self, run_id: str, playbook_id: str, actions: list[dict], service: str,
                require_class_a: bool, prefix: str, gated: bool = False) -> list[dict]:
        """落单。gated=True 表示调用方（plan_orders）已过闸门，不再重复判定；
        plan_approved 走的是人工审批通道，不受自动阈值约束（但仍受白名单约束）。"""
        created: list[dict] = []
        seen: set[str] = set()
        # 同一 run 已有未失败订单的动作不再重复下单（跨调用幂等，
        # 防止 _maybe_remediate 被重复调用/人工补送时刷出一堆重复单）
        existing = {o["action_id"] for o in self.store.for_run(run_id)
                    if o["status"] not in ("exec_failed", "verify_failed", "rollback_exhausted")}
        for a in actions or []:
            text = a.get("action", "") if isinstance(a, dict) else str(a)
            aid = resolve_action(playbook_id, text)
            if not aid:
                continue
            spec = REMEDIATION_REGISTRY.get(aid, {})
            if require_class_a and spec.get("class") != "A":
                continue
            if aid in seen or aid in existing:   # 同一 run 同一动作只下一次单
                continue
            if require_class_a and not gated:
                allowed, reason, _tier = self._guardrail_allows(aid, spec)
                if not allowed:
                    self._audit(run_id, aid, "guardrail_blocked",
                                f"自动下单被护栏拦截（{reason}）：{text[:120]}")
                    continue
            seen.add(aid)
            order = {
                "id": uuid.uuid4().hex[:12], "run_id": run_id, "service": service,
                "action_id": aid, "params": {"playbook": playbook_id},
                "reason": text[:200], "status": "pending",
                "created_at": now_iso(), "updated_at": now_iso(),
            }
            self.store.insert(order)
            created.append(order)
            self._audit(run_id, aid, "order_created", f"{prefix}：{text[:120]}")
        return created

    # ── agent 回报执行结果 → 引擎判定 ─────────────────────────
    def complete(self, order_id: str, exec_ok: bool, verify: dict,
                 exec_detail: str = "") -> dict:
        order = self.store.get(order_id)
        if not order:
            raise KeyError(order_id)
        # 终态幂等：同一订单重复回报不得改写已定状态（agent 重试/重放）
        if order["status"] in TERMINAL_STATUSES:
            return {"status": order["status"], "rollback": False,
                    "duplicate": True,
                    "msg": f"订单已处于终态 {order['status']}，忽略重复回报"}

        self.store.update(order_id, exec_result=json.dumps(
            {"ok": exec_ok, "detail": exec_detail[:500]}, ensure_ascii=False),
            verify_result=json.dumps(verify, ensure_ascii=False))

        if not exec_ok:
            self.store.update(order_id, status="exec_failed")
            self._audit(order["run_id"], order["action_id"], "exec_failed",
                        f"执行失败：{exec_detail[:200]}")
            return {"status": "exec_failed", "rollback": False}

        if verify.get("ok"):
            self.store.update(order_id, status="fixed")
            self._audit(order["run_id"], order["action_id"], "fixed",
                        f"验证通过：{verify.get('detail', '')[:200]}")
            return {"status": "fixed", "rollback": False}

        rb = REMEDIATION_REGISTRY.get(order["action_id"], {}).get("rollback")
        if rb:
            # 回滚深度上限：只允许一层（原单 → 回滚单）。回滚单再失败就停手等人，
            # 否则 restore_config_from_backup 这种"回滚到自己"的动作会无限自环，
            # 把 agent 队列刷爆（复盘实测缺口）。
            depth = int((order.get("params") or {}).get("rollback_depth", 0))
            if depth >= MAX_ROLLBACK_DEPTH:
                self.store.update(order_id, status="rollback_exhausted")
                self._audit(order["run_id"], order["action_id"], "rollback_exhausted",
                            f"回滚已达最大深度 {MAX_ROLLBACK_DEPTH}，停止自动回滚，转人工："
                            f"{verify.get('detail', '')[:160]}")
                return {"status": "rollback_exhausted", "rollback": False,
                        "msg": "回滚链已达上限，需人工介入"}
            rorder = {
                "id": uuid.uuid4().hex[:12], "run_id": order["run_id"],
                "service": order["service"], "action_id": rb,
                "params": {"rollback_depth": depth + 1,
                           "parent_order": order_id},
                "reason": f"回滚：{order['action_id']} 验证失败（{verify.get('detail', '')[:100]}）",
                "status": "pending", "created_at": now_iso(), "updated_at": now_iso(),
            }
            self.store.insert(rorder)
            self.store.update(order_id, status="rollback_pending", note=rorder["id"])
            self._audit(order["run_id"], order["action_id"], "verify_failed",
                        f"验证失败，已下单回滚 {rb}（depth={depth + 1}）")
            return {"status": "rollback_pending", "rollback": True,
                    "rollback_order": rorder["id"]}

        self.store.update(order_id, status="verify_failed")
        self._audit(order["run_id"], order["action_id"], "verify_failed",
                    f"验证失败且无回滚动作：{verify.get('detail', '')[:200]}")
        return {"status": "verify_failed", "rollback": False}

    def stats(self) -> dict:
        return {"enabled": self.enabled,
                "guardrail_wired": self.guardrail is not None,
                "policy": dict(self.policy),
                "orders": self.store.count_by_status(),
                "registry_A": sum(1 for v in REMEDIATION_REGISTRY.values() if v["class"] == "A"),
                "registry_B": sum(1 for v in REMEDIATION_REGISTRY.values() if v["class"] == "B")}

    def _audit(self, run_id: str, action: str, event: str, detail: str,
               approver: str = "auto-remediation") -> None:
        if not self.audit:
            return
        spec = REMEDIATION_REGISTRY.get(action, {})
        blocked = event in ("rejected_out_of_registry", "guardrail_blocked")
        self.audit.record({
            "run_id": run_id, "action": action, "decision": event,
            "approver": approver, "note": detail,
            "guardrail_reason": f"自动修复引擎（enabled={self.enabled}）",
            "tier": spec.get("tier", 1 if event in ("order_created", "fixed") else 2),
            "allowed": not blocked,
            "executed": event in ("fixed",),
        })
