"""入口门控：在去重之后再做一层规则降噪，从源头抑制告警风暴。

降噪规则（可配置启停）：
  1. test_env        —— 非生产环境（env ∈ test/dev/staging）直接丢弃
  2. heartbeat       —— 心跳/探活类告警无排障价值，丢弃
  3. low_value_info  —— info 级且无生产影响标注，丢弃
  4. maintenance     —— 维护窗口内标注 maintenance=true，丢弃
  5. storm_rate      —— 单指纹超高频（已由去重层覆盖，此处留统计位）

每个规则输出计数，供量化报告；线程安全。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass

from .models import UnifiedAlert


@dataclass
class GateDecision:
    passed: bool
    rule: str          # 通过时为 "pass"，丢弃时为具体规则名
    reason: str


class EntryGate:
    def __init__(self, enabled_rules: set[str] | None = None):
        self.enabled = enabled_rules or {"test_env", "heartbeat", "low_value_info", "maintenance"}
        self._lock = threading.Lock()
        self.counters: dict[str, int] = {"pass": 0}
        self.total = 0

    # ── 规则实现 ─────────────────────────────────────────────
    @staticmethod
    def _rule_test_env(a: UnifiedAlert) -> bool:
        return a.labels.get("env", "prod").lower() in {"test", "dev", "staging", "uat"}

    @staticmethod
    def _rule_heartbeat(a: UnifiedAlert) -> bool:
        name = a.alertname.lower()
        return name.startswith(("heartbeat", "keepalive", "ping_"))

    @staticmethod
    def _rule_low_value_info(a: UnifiedAlert) -> bool:
        return a.severity == "info" and not a.labels.get("affects_prod")

    @staticmethod
    def _rule_maintenance(a: UnifiedAlert) -> bool:
        return str(a.labels.get("maintenance", "")).lower() == "true"

    RULES = {
        "test_env": _rule_test_env,
        "heartbeat": _rule_heartbeat,
        "low_value_info": _rule_low_value_info,
        "maintenance": _rule_maintenance,
    }

    RULE_REASONS = {
        "test_env": "非生产环境告警",
        "heartbeat": "心跳/探活类无排障价值",
        "low_value_info": "info 级且无生产影响",
        "maintenance": "维护窗口内已知变更",
    }

    def admit(self, alert: UnifiedAlert) -> GateDecision:
        with self._lock:
            self.total += 1
        for rule in ("test_env", "heartbeat", "low_value_info", "maintenance"):
            if rule not in self.enabled:
                continue
            try:
                hit = self.RULES[rule](alert)
            except Exception:
                hit = False
            if hit:
                with self._lock:
                    self.counters[rule] = self.counters.get(rule, 0) + 1
                return GateDecision(passed=False, rule=rule, reason=self.RULE_REASONS[rule])
        with self._lock:
            self.counters["pass"] = self.counters.get("pass", 0) + 1
        return GateDecision(passed=True, rule="pass", reason="通过入口门控")

    def stats(self) -> dict:
        with self._lock:
            dropped = self.total - self.counters.get("pass", 0)
            return {
                "total": self.total,
                "passed": self.counters.get("pass", 0),
                "dropped": dropped,
                "drop_ratio": round(dropped / self.total, 4) if self.total else 0.0,
                "by_rule": {k: v for k, v in self.counters.items() if k != "pass"},
            }
