"""P0-P3 评级分流：给通过门控的告警打级并路由。

分流转路由（对齐同类系统的成本设计）：
  P0/P1 → research  进研判主链路（RAG 上下文 + LLM 研判 + 护栏审批）
  P2    → batch     进批量研判队列（低峰批处理，省 Token）
  P3    → notify    不进大模型，直接路由通知（0 Token）

评分模型（可解释，面试能逐项讲）：
  score = severity 基础分 + 业务关键词加分 + 核心服务加分 + 影响面加分
  P0 ≥ 8 | P1 ≥ 5 | P2 ≥ 3 | 其余 P3
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import UnifiedAlert

# 业务关键词：命中即视为影响核心交易/安全链路
BUSINESS_KEYWORDS = (
    "支付", "资金", "下单", "结算", "对账", "退款",
    "payment", "checkout", "order", "settle", "auth", "login", "token",
)
# 核心服务标签
CORE_SERVICES = ("api", "gateway", "payment", "order", "auth", "db", "mysql", "redis", "kafka")

_LEVELS = ("P0", "P1", "P2", "P3")


@dataclass
class TriageDecision:
    level: str                  # P0 / P1 / P2 / P3
    route: str                  # research / batch / notify
    score: float
    reasons: list[str] = field(default_factory=list)   # 逐项可解释


def _severity_base(severity: str) -> float:
    return {"critical": 5.0, "warning": 2.0, "info": 0.5}.get(severity, 2.0)


def triage(alert: UnifiedAlert) -> TriageDecision:
    text = f"{alert.title} {alert.description} {alert.alertname}".lower()
    labels_l = {k: str(v).lower() for k, v in alert.labels.items()}
    score = _severity_base(alert.severity)
    reasons: list[str] = [f"severity={alert.severity} 基础分 {_severity_base(alert.severity)}"]

    hits = [kw for kw in BUSINESS_KEYWORDS if kw in text]
    if hits:
        score += 2.0
        reasons.append(f"命中业务关键词 {hits[:3]} +2")

    svc = labels_l.get("service", "") or labels_l.get("system", "")
    if any(core in svc or core in text for core in CORE_SERVICES):
        score += 1.0
        reasons.append("核心服务/组件 +1")

    affected = str(alert.labels.get("affected_users", "") or "")
    if affected.isdigit() and int(affected) >= 1000:
        score += 2.0
        reasons.append(f"影响用户 {affected} ≥1000 +2")

    if alert.source == "ticket":
        score += 0.5
        reasons.append("工单来源（人工确认过）+0.5")

    if score >= 8:
        level = "P0"
    elif score >= 5:
        level = "P1"
    elif score >= 3:
        level = "P2"
    else:
        level = "P3"

    route = {"P0": "research", "P1": "research", "P2": "batch", "P3": "notify"}[level]
    return TriageDecision(level=level, route=route, score=round(score, 2), reasons=reasons)


class TriageStats:
    """分流分布统计（供量化报告）。"""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {lv: 0 for lv in _LEVELS}
        self.routes: dict[str, int] = {"research": 0, "batch": 0, "notify": 0}

    def record(self, d: TriageDecision) -> None:
        self.counts[d.level] += 1
        self.routes[d.route] += 1

    def snapshot(self) -> dict:
        total = sum(self.counts.values())
        return {
            "total": total,
            "levels": dict(self.counts),
            "routes": dict(self.routes),
            "llm_pathway_ratio": round(
                self.routes["research"] / total, 4) if total else 0.0,
        }
