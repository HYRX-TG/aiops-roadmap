"""轻量持久化工作流引擎（Temporal 简化版，SQLite checkpoint）。

提供 Temporal 的三个核心能力的单机等价物：
  1. 持久化     —— 每个 stage 跑完即落库 checkpoint，进程挂了能从断点续跑
  2. 节点级重试 —— 每 stage 独立 max_retries + 指数退避，重试轨迹全程留痕
  3. 失败告警   —— stage 最终失败 → run 标记 failed，错误与 stage 名落库可查

为什么不用 Temporal（面试话术）：
  单机自用项目引入 Temporal = 多一个有状态服务 + SDK 学习成本，收益不匹配；
  本引擎 ~150 行讲得清每一行，且 checkpoint 语义与 Temporal 对齐，未来迁移路径平滑。
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
import weakref
from dataclasses import dataclass
from typing import Any, Callable

from .models import now_iso

STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


@dataclass
class Stage:
    name: str
    fn: Callable[[dict], dict]          # context -> 本 stage 产出（并入 context）
    max_retries: int = 2                # 首次之外的重试次数
    backoff_seconds: float = 0.2        # 指数退避基数


class WorkflowStore:
    """SQLite 持久化。check_same_thread=False + 显式锁，兼容接入层多线程。"""

    def __init__(self, db_path: str = "workflow.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs(
            id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            current_stage INTEGER NOT NULL DEFAULT 0,
            context TEXT NOT NULL DEFAULT '{}',
            error TEXT DEFAULT '',
            created_at TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS stage_log(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL, stage TEXT NOT NULL,
            attempt INTEGER NOT NULL, ok INTEGER NOT NULL,
            error TEXT DEFAULT '', ts TEXT
        );
        """)
        self._conn.commit()
        # WAL：读写不互斥（大盘轮询不阻塞研判写入）
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        # 连接随对象回收自动关闭（避免 ResourceWarning；也可显式 close()）
        weakref.finalize(self, WorkflowStore._close_conn, self._conn)

    @staticmethod
    def _close_conn(conn: "sqlite3.Connection") -> None:
        try:
            conn.close()
        except Exception:
            pass

    def close(self) -> None:
        WorkflowStore._close_conn(self._conn)

    def create_run(self, run_id: str, fingerprint: str, context: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs(id,fingerprint,status,current_stage,context,created_at,updated_at) "
                "VALUES(?,?,?,0,?,?,?)",
                (run_id, fingerprint, STATUS_RUNNING, json.dumps(context, ensure_ascii=False),
                 now_iso(), now_iso()))
            self._conn.commit()

    def load_run(self, run_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id,fingerprint,status,current_stage,context,error FROM runs WHERE id=?",
                (run_id,)).fetchone()
        if not row:
            return None
        return {"id": row[0], "fingerprint": row[1], "status": row[2],
                "current_stage": row[3], "context": json.loads(row[4]), "error": row[5]}

    def checkpoint(self, run_id: str, stage_idx: int, context: dict) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET current_stage=?, context=?, status=?, updated_at=? WHERE id=?",
                (stage_idx, json.dumps(context, ensure_ascii=False), STATUS_RUNNING, now_iso(), run_id))
            self._conn.commit()

    def finish(self, run_id: str, status: str, error: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET status=?, error=?, updated_at=? WHERE id=?",
                (status, error, now_iso(), run_id))
            self._conn.commit()

    def update_plan_state(self, run_id: str, state: str, decision: str = "",
                          approver: str = "") -> dict | None:
        """审批结果回写：plan.state → approved / rejected（状态机闭环，不再只活在 UI）。

        返回更新后的 context；run 不存在返回 None。
        """
        with self._lock:
            row = self._conn.execute("SELECT context FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            ctx = json.loads(row[0] or "{}")
            plan = ctx.get("plan") or {}
            plan["state"] = state
            if decision:
                plan["decision"] = decision
            if approver:
                plan["approver"] = approver
            plan["decided_at"] = now_iso()
            ctx["plan"] = plan
            self._conn.execute("UPDATE runs SET context=?, updated_at=? WHERE id=?",
                               (json.dumps(ctx, ensure_ascii=False), now_iso(), run_id))
            self._conn.commit()
        return ctx

    def patch_context(self, run_id: str, patch: dict) -> dict | None:
        """把任意补丁并入 run 的 context（自动修复订单回写用）。

        与 update_plan_state 分开：后者是审批状态机（带 decided_at 语义），
        这里只是把引擎产出的附加字段写回去，不该污染审批语义。
        """
        with self._lock:
            row = self._conn.execute("SELECT context FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            ctx = json.loads(row[0] or "{}")
            for k, v in (patch or {}).items():
                if isinstance(v, dict) and isinstance(ctx.get(k), dict):
                    ctx[k].update(v)
                else:
                    ctx[k] = v
            self._conn.execute("UPDATE runs SET context=?, updated_at=? WHERE id=?",
                               (json.dumps(ctx, ensure_ascii=False), now_iso(), run_id))
            self._conn.commit()
        return ctx

    def log_stage(self, run_id: str, stage: str, attempt: int, ok: bool, error: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO stage_log(run_id,stage,attempt,ok,error,ts) VALUES(?,?,?,?,?,?)",
                (run_id, stage, attempt, int(ok), error, now_iso()))
            self._conn.commit()

    def resumable_runs(self) -> list[str]:
        """进程重启后可续跑的 run（中断时停在 running/failed 但未到末尾）。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id FROM runs WHERE status IN (?,?)", (STATUS_RUNNING, STATUS_FAILED)).fetchall()
        return [r[0] for r in rows]

    def latest_run_for_fingerprint(self, fingerprint: str) -> dict | None:
        """按告警指纹找最新研判 run（接入告警 ↔ 研判结果关联）。"""
        with self._lock:
            row = self._conn.execute(
                "SELECT id,status,context,error,updated_at FROM runs"
                " WHERE fingerprint=? ORDER BY updated_at DESC LIMIT 1",
                (fingerprint,)).fetchone()
        if not row:
            return None
        return {"id": row[0], "status": row[1], "context": json.loads(row[2] or "{}"),
                "error": row[3], "updated_at": row[4], "fingerprint": fingerprint}

    def stage_history(self, run_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT stage,attempt,ok,error,ts FROM stage_log WHERE run_id=? ORDER BY seq",
                (run_id,)).fetchall()
        return [{"stage": r[0], "attempt": r[1], "ok": bool(r[2]), "error": r[3], "ts": r[4]} for r in rows]

    def recent_runs(self, limit: int = 50) -> list[dict]:
        """最近的研判 run（供前端「实时告警 → 知识节点染色」与 /api/alerts 合并）。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id,fingerprint,status,context,error,updated_at FROM runs ORDER BY updated_at DESC LIMIT ?",
                (limit,)).fetchall()
        out = []
        for rid, fp, status, ctx_json, err, ts in rows:
            ctx = json.loads(ctx_json or "{}")
            alert = ctx.get("alert", {}) or {}
            triage = ctx.get("triage", {}) or {}
            out.append({
                "run_id": rid, "id": rid, "fingerprint": fp, "status": status,
                "context": ctx,
                "level": triage.get("level", "P2"),
                "service": (alert.get("labels", {}) or {}).get("service", ""),
                "title": alert.get("title") or alert.get("alertname", ""),
                "alertname": alert.get("alertname", ""),
                "plan_state": (ctx.get("plan", {}) or {}).get("state", ""),
                "error": err, "updated_at": ts,
            })
        return out


class WorkflowEngine:
    def __init__(self, stages: list[Stage], store: WorkflowStore,
                 sleep_fn: Callable[[float], None] = time.sleep):
        self.stages = stages
        self.store = store
        self._sleep = sleep_fn

    def start(self, fingerprint: str, context: dict) -> str:
        run_id = uuid.uuid4().hex[:12]
        self.store.create_run(run_id, fingerprint, context)
        return run_id

    def run(self, run_id: str) -> dict:
        run = self.store.load_run(run_id)
        if run is None:
            raise KeyError(f"run {run_id} not found")
        context = run["context"]
        idx = run["current_stage"]
        self.store.finish(run_id, STATUS_RUNNING)
        while idx < len(self.stages):
            stage = self.stages[idx]
            attempt = 0
            while True:
                try:
                    produced = stage.fn(context)
                    context.update(produced or {})
                    self.store.log_stage(run_id, stage.name, attempt, ok=True)
                    break
                except Exception as exc:  # 节点级重试 + 指数退避
                    self.store.log_stage(run_id, stage.name, attempt, ok=False, error=str(exc))
                    if attempt >= stage.max_retries:
                        self.store.finish(run_id, STATUS_FAILED,
                                          error=f"stage={stage.name} attempt={attempt + 1} err={exc}")
                        return self.store.load_run(run_id)
                    self._sleep(stage.backoff_seconds * (2 ** attempt))
                    attempt += 1
            idx += 1
            self.store.checkpoint(run_id, idx, context)   # ✓ stage 完成即 checkpoint
        self.store.finish(run_id, STATUS_DONE)
        return self.store.load_run(run_id)

    def resume_all(self) -> list[str]:
        """进程重启后：把中断的 run 全部续跑到终态。"""
        resumed = []
        for rid in self.store.resumable_runs():
            run = self.store.load_run(rid)
            if run and run["status"] != STATUS_DONE:
                final = self.run(rid)
                resumed.append(f"{rid}:{final['status']}")
        return resumed
