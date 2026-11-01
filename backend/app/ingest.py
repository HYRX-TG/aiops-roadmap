"""接入层编排器：归一化 → 去重 → 门控 → 分级分流，一次跑完并累计统计。

这是「告警风暴 → 研判主链路」的总闸门；压测脚本直接驱动它。

两类数据走不同路径（复盘缺口：曾经把两者混在一起，导致两个方向都错）：
  - 事件源（7 类告警 + business_log）：走完整降噪/分级/分流，可能进研判主链路。
  - 上下文源（ops_audit / change_log）：是"研判要用的事实"，不是"要处理的事故"。
    它们只做去重并落库供时间线召回，**不进分级、不进研判**——否则一条运维审计
    事件可能被当成 P0 送进 LLM，既错又烧钱。同时它们不能被门控的"低价值 info"
    规则丢掉（变更事件天然是 info），否则变更关联层在生产上永远拿到空时间线。
"""
from __future__ import annotations

import threading

from .dedup import SlidingWindowDedup
from .gate import EntryGate
from .models import UnifiedAlert
from .sources import normalize_any, SOURCE_NAMES
from .triage import TriageDecision, TriageStats, triage

RESEARCH, BATCH, NOTIFY = "research", "batch", "notify"

# 上下文源：只落库供研判召回，不参与分级/分流
CONTEXT_SOURCES = frozenset({"ops_audit", "change_log"})
CONTEXT_LEVEL = "context"


class IngestPipeline:
    def __init__(self, window_seconds: float = 300.0, max_per_window: int = 1,
                 store=None):
        self.dedup = SlidingWindowDedup(window_seconds=window_seconds, max_per_window=max_per_window)
        self.gate = EntryGate()
        self.triaged = TriageStats()
        self.store = store   # 可选 IngestStore：放行告警落库（告警流数据源）
        self._lock = threading.Lock()
        self.rejected_by_dedup = 0
        self.rejected_by_gate = 0
        self.context_stored = 0
        # 有界缓冲：只保留最近 N 条待研判记录（防止长跑内存泄漏——幻灯片演示跑一小时也不涨）
        self.output: list[tuple[UnifiedAlert, TriageDecision]] = []
        self._output_maxlen = 1000

    def _remember(self, item: tuple[UnifiedAlert, TriageDecision]) -> None:
        with self._lock:
            self.output.append(item)
            if len(self.output) > self._output_maxlen:
                del self.output[:-self._output_maxlen]

    def ingest(self, source: str, payload: dict) -> list[tuple[UnifiedAlert, TriageDecision]]:
        """接入一批原始告警，返回需要进入后续链路的 (告警, 分级) 列表。

        上下文源返回空列表（它们不进后续链路），但会落库供时间线召回。
        """
        admitted: list[tuple[UnifiedAlert, TriageDecision]] = []
        for alert in normalize_any(source, payload):
            dup, _ = self.dedup.check(alert.fingerprint)
            if dup:
                with self._lock:
                    self.rejected_by_dedup += 1
                continue

            # ── 上下文源：跳过门控与分级，只落库 ──
            if alert.source in CONTEXT_SOURCES:
                t = TriageDecision(level=CONTEXT_LEVEL, route="context", score=0.0,
                                   reasons=["上下文数据（变更/操作时间线），非事故"])
                if self.store is not None:
                    self.store.record(alert, t)
                with self._lock:
                    self.context_stored += 1
                continue

            decision = self.gate.admit(alert)
            if not decision.passed:
                with self._lock:
                    self.rejected_by_gate += 1
                continue
            t = triage(alert)
            self.triaged.record(t)
            if self.store is not None:
                self.store.record(alert, t)
            admitted.append((alert, t))
            if t.route == RESEARCH:
                self._remember((alert, t))
        return admitted

    def ingest_raw(self, source: str, payload: dict):
        return self.ingest(source, payload)

    def stats(self) -> dict:
        total_in = self.dedup.total_seen
        total_out = self.triaged.routes["research"] + self.triaged.routes["batch"] + self.triaged.routes["notify"]
        return {
            "sources_supported": list(SOURCE_NAMES),
            "context_sources": sorted(CONTEXT_SOURCES),
            "ingested": total_in,
            "dropped_dedup": self.rejected_by_dedup,
            "dropped_gate": self.rejected_by_gate,
            "context_stored": self.context_stored,
            "forwarded": total_out,
            "noise_reduction_ratio": round(
                (self.rejected_by_dedup + self.rejected_by_gate) / total_in, 4) if total_in else 0.0,
            "dedup": self.dedup.stats(),
            "gate": self.gate.stats(),
            "triage": self.triaged.snapshot(),
        }
