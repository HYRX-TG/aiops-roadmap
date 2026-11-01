"""审批审计存储（SQLite 持久化）。

曾经的坑：审计放在 server.py 的进程内 list 里，重启即清空——一个用来讲
"可审计可追责"的模块，重启丢审计，在生产里是合规事故。
现在：每次审批判定先落库再返回；内存里只保留最近 N 条做快速查询镜像。
"""
from __future__ import annotations

import json
import sqlite3
import threading
import weakref
from collections import deque

from .models import now_iso

_SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals(
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT, run_id TEXT, action TEXT, decision TEXT,
    approver TEXT, note TEXT, guardrail_reason TEXT,
    tier INTEGER, allowed INTEGER, executed INTEGER,
    detail TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_approvals_run ON approvals(run_id);
"""

# 内存镜像上限（SQLite 是全量真相，这里只为 /api/audit 快速返回）
_MEMORY_MIRROR = 500


class AuditStore:
    """线程安全的审批审计存储（check_same_thread=False + 显式锁）。"""

    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        # WAL：读写不互斥，审批写入不阻塞大盘轮询
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        weakref.finalize(self, AuditStore._close_conn, self._conn)
        self._mirror: deque = deque(maxlen=_MEMORY_MIRROR)
        self._load_mirror()

    @staticmethod
    def _close_conn(conn: sqlite3.Connection) -> None:
        try:
            conn.close()
        except Exception:
            pass

    def close(self) -> None:
        AuditStore._close_conn(self._conn)

    def _load_mirror(self) -> None:
        with self._lock:
            rows = self._conn.execute(
                "SELECT ts,run_id,action,decision,approver,note,guardrail_reason,tier,allowed,executed "
                "FROM approvals ORDER BY seq DESC LIMIT ?", (_MEMORY_MIRROR,)).fetchall()
        self._mirror.extend(reversed([self._row_to_dict(r) for r in rows]))

    @staticmethod
    def _row_to_dict(r: tuple) -> dict:
        return {"ts": r[0], "run_id": r[1], "action": r[2], "decision": r[3],
                "approver": r[4], "note": r[5], "guardrail_reason": r[6],
                "tier": r[7], "allowed": bool(r[8]), "executed": bool(r[9])}

    def record(self, entry: dict) -> None:
        """写入一条审批审计（entry: run_id/action/decision/approver/note/guardrail_reason/tier/allowed/executed）。"""
        row = {
            "ts": now_iso(), "run_id": entry.get("run_id", ""), "action": entry.get("action", ""),
            "decision": entry.get("decision", ""), "approver": entry.get("approver", ""),
            "note": entry.get("note", ""), "guardrail_reason": entry.get("guardrail_reason", ""),
            "tier": int(entry.get("tier") or 0), "allowed": int(bool(entry.get("allowed"))),
            "executed": int(bool(entry.get("executed"))),
        }
        with self._lock:
            self._conn.execute(
                "INSERT INTO approvals(ts,run_id,action,decision,approver,note,guardrail_reason,tier,allowed,executed) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (row["ts"], row["run_id"], row["action"], row["decision"], row["approver"],
                 row["note"], row["guardrail_reason"], row["tier"], row["allowed"], row["executed"]))
            self._conn.commit()
            self._mirror.append(row)

    def decisions_for_run(self, run_id: str) -> list[dict]:
        """某个 run 的历史审批记录（用于防重复审批）。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT ts,run_id,action,decision,approver,note,guardrail_reason,tier,allowed,executed "
                "FROM approvals WHERE run_id=? ORDER BY seq", (run_id,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def all(self, limit: int = 200) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT ts,run_id,action,decision,approver,note,guardrail_reason,tier,allowed,executed "
                "FROM approvals ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM approvals").fetchone()[0]

    def snapshot(self) -> dict:
        return {"count": self.count()}
