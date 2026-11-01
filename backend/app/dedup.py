"""滑动窗口去重：同一指纹在窗口内只放行前 N 条，其余判定为重复并抑制。

对标同类系统："滑动窗口去重机制过滤 60%+ 重复与低信噪比噪声"。
线程安全（threading.Lock），供接入层与压测并发调用。
"""
from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowDedup:
    def __init__(self, window_seconds: float = 300.0, max_per_window: int = 3,
                 now_fn=time.time):
        """
        window_seconds: 滑动窗口长度（秒）
        max_per_window: 窗口内同一指纹最多放行条数，超过即判重复
        now_fn: 时间源（单测可注入假时钟）
        """
        self.window_seconds = window_seconds
        self.max_per_window = max_per_window
        self._now = now_fn
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        # 统计
        self.total_seen = 0
        self.total_duplicated = 0

    def check(self, fingerprint: str) -> tuple[bool, int]:
        """返回 (is_duplicate, count_in_window)。

        窗口内已有条数 >= max_per_window → 本条判重复（抑制），不追加时间戳；
        否则放行并记录。
        """
        with self._lock:
            now = self._now()
            self.total_seen += 1
            q = self._hits.get(fingerprint)
            if q is None:
                q = deque()
                self._hits[fingerprint] = q
            # 淘汰窗口外旧记录
            horizon = now - self.window_seconds
            while q and q[0] <= horizon:
                q.popleft()
            if len(q) >= self.max_per_window:
                self.total_duplicated += 1
                return True, len(q)
            q.append(now)
            # 惰性清理：指纹表过大时丢弃已空窗口
            if len(self._hits) > 100_000:
                self._hits = {fp: dq for fp, dq in self._hits.items() if dq}
            return False, len(q)

    def stats(self) -> dict:
        with self._lock:
            return {
                "seen": self.total_seen,
                "duplicated": self.total_duplicated,
                "dedup_ratio": round(self.total_duplicated / self.total_seen, 4) if self.total_seen else 0.0,
            }
