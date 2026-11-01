"""接入层持久化：放行的告警落 SQLite，供 /api/alerts 实时流与研判关联。

设计：ingest 是纯内存统计（快），但告警流必须可查、可与研判 run 关联，
     所以放行的每条告警在此落库（含完整告警 JSON，供 /api/research 直接取用）。
"""
from __future__ import annotations

import json
import sqlite3
import threading
import weakref

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingested_alerts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL,
    source TEXT, alertname TEXT, title TEXT, service TEXT,
    severity TEXT, level TEXT, route TEXT,
    alert_json TEXT, received_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_ing_fp ON ingested_alerts(fingerprint);
CREATE INDEX IF NOT EXISTS idx_ing_id ON ingested_alerts(id);
"""


class IngestStore:
    def __init__(self, db_path: str = "ingest.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        # WAL：接入写入不阻塞 /api/alerts 轮询读取
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        weakref.finalize(self, IngestStore._close, self._conn)

    @staticmethod
    def _close(conn: "sqlite3.Connection") -> None:
        try:
            conn.close()
        except Exception:
            pass

    def record(self, alert, decision) -> None:
        """放行一条告警（alert: UnifiedAlert, decision: TriageDecision）。"""
        with self._lock:
            self._conn.execute(
                "INSERT INTO ingested_alerts(fingerprint,source,alertname,title,service,severity,level,route,alert_json,received_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (alert.fingerprint, alert.source, alert.alertname, alert.title,
                 alert.labels.get("service", ""), alert.severity,
                 decision.level, decision.route,
                 json.dumps(alert.to_dict(), ensure_ascii=False), alert.received_at))
            self._conn.commit()

    def recent(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT fingerprint,source,alertname,title,service,severity,level,route,alert_json,received_at"
                " FROM ingested_alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{
            "fingerprint": r[0], "source": r[1], "alertname": r[2], "title": r[3],
            "service": r[4], "severity": r[5], "level": r[6], "route": r[7],
            "alert_json": json.loads(r[8] or "{}"), "received_at": r[9],
        } for r in rows]

    def recent_context(self, source: str, service: str = "", limit: int = 25,
                       service_tokens: list[str] | None = None) -> list[dict]:
        """召回上下文源记录：精确 service → 关键词相关 → 全局近期（三级降级）。

        为什么需要三级（真实事故回放实测缺口）：
          Fastly 的变更 target 是"CDN 软件"，告警 service 是"edge-cdn"；
          GitHub 的维护 target 是"东西海岸骨干光模块"，告警 service 是"mysql-cluster"。
          两者字符串永不相等——只按 service 精确匹配，时间线永远是空的。
          但真实 SRE 的关联逻辑不是字符串相等，而是"时间接近 + 语义相关"。
        所以：
          1. 先按 service 精确匹配（最可信）
          2. 再按 service_tokens 在 target/detail 里做子串匹配（语义相关）
          3. 最后退化到"近期任意变更"（related=False，只作参考，不抢主剧本）
        """
        base = ("SELECT fingerprint,source,alertname,title,service,severity,level,route,"
                "alert_json,received_at FROM ingested_alerts WHERE source=?")
        with self._lock:
            if service:
                rows = self._conn.execute(
                    base + " AND service=? ORDER BY id DESC LIMIT ?",
                    (source, service, limit)).fetchall()
                if rows:
                    return self._rows(rows, related=True)
            # 语义相关：token 命中 target / detail
            tokens = [t.lower() for t in (service_tokens or []) if t and len(t) >= 3]
            if tokens:
                allrows = self._conn.execute(
                    base + " ORDER BY id DESC LIMIT 200", (source,)).fetchall()
                hit = []
                for r in allrows:
                    blob = " ".join(str(x).lower() for x in (r[1], r[2], r[3], r[4]))
                    aj = json.loads(r[8] or "{}")
                    raw = (aj.get("raw") or {})
                    blob += " " + json.dumps(raw, ensure_ascii=False).lower()
                    if any(t in blob for t in tokens):
                        hit.append(r)
                    if len(hit) >= limit:
                        break
                if hit:
                    return self._rows(hit, related=True)
            # 全局近期：只作参考
            rows = self._conn.execute(
                base + " ORDER BY id DESC LIMIT ?", (source, limit)).fetchall()
        return self._rows(rows, related=False)

    @staticmethod
    def _rows(rows, related: bool) -> list[dict]:
        out = []
        for r in rows:
            out.append({
                "fingerprint": r[0], "source": r[1], "alertname": r[2], "title": r[3],
                "service": r[4], "severity": r[5], "level": r[6], "route": r[7],
                "alert_json": json.loads(r[8] or "{}"), "received_at": r[9],
                "related": related,
            })
        return out

    def recent_by_source(self, source: str, service: str = "", limit: int = 50,
                         fallback_any: bool = False) -> list[dict]:
        """召回近期某类源的记录（研判链的"变更/操作时间线"关联用）。

        主要用于 ops_audit / change_log：给定受影响主机/服务，召回它最近的操作与变更，
        作为根因关联的结构化证据。service 命中 labels.service（ops_audit 把 host 存进
        service，change_log 把 target 存进 service，键一致）。

        fallback_any=True：精确匹配为空时退化为"近期任意目标的变更"。
        为什么需要：真实事故里触发方常是别的对象（Fastly 是客户配置、GitHub 是光模块
        维护），按自己的 service 精确匹配会拿到空时间线——那正是"关联不到变更"的根因。
        退化召回会在时间线里标注"来自全局近期变更"，由研判层决定权重。
        """
        base = ("SELECT fingerprint,source,alertname,title,service,severity,level,route,"
                "alert_json,received_at FROM ingested_alerts WHERE source=?")
        sql, params = base, [source]
        if service:
            sql += " AND service=? "
            params.append(service)
        sql += " ORDER BY id DESC LIMIT ? "
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        if not rows and fallback_any and service:
            sql2 = base + " ORDER BY id DESC LIMIT ?"
            with self._lock:
                rows = self._conn.execute(sql2, (source, limit)).fetchall()
        return [{
            "fingerprint": r[0], "source": r[1], "alertname": r[2], "title": r[3],
            "service": r[4], "severity": r[5], "level": r[6], "route": r[7],
            "alert_json": json.loads(r[8] or "{}"), "received_at": r[9],
        } for r in rows]
