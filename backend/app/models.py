"""统一告警模型：7 类异构源 → 归一化 UnifiedAlert。

对标设计（同类研判系统通用做法）：
- 多源格式各异，必须先归一化，后续去重/门控/分流才有统一抓手。
- fingerprint 是去重的关键：同一 (源, 告警名, 关键维度标签) 视为同一告警。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import hashlib
import json

# 归一化后的三档严重度（P0-P3 细分在 triage 层做）
SEVERITY_LEVELS = ("critical", "warning", "info")

# 原始严重度 → 归一化严重度（大小写不敏感，覆盖 7 类源常见取值）
_SEVERITY_MAP: dict[str, str] = {}
for _k in ("critical", "crit", "fatal", "error", "p0", "p1", "down", "alert", "紧急", "严重"):
    _SEVERITY_MAP[_k] = "critical"
for _k in ("warning", "warn", "p2", "degraded", "flapping", "警告"):
    _SEVERITY_MAP[_k] = "warning"
for _k in ("info", "informational", "notice", "ok", "resolved", "p3", "提示", "通知"):
    _SEVERITY_MAP[_k] = "info"

# 参与指纹的关键维度标签（不同源口径不同，这里取交集通用维度）
FINGERPRINT_LABEL_KEYS = ("env", "service", "instance", "namespace", "host", "system", "cluster")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_severity(raw: str | None) -> str:
    if not raw:
        return "warning"
    return _SEVERITY_MAP.get(str(raw).strip().lower(), "warning")


def make_fingerprint(source: str, alertname: str, labels: dict) -> str:
    """同一 (源, 告警名, 关键维度) 视为同一告警 → 用于滑动窗口去重。"""
    payload = {"source": source, "alertname": alertname}
    for k in FINGERPRINT_LABEL_KEYS:
        payload[k] = labels.get(k, "")
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


@dataclass
class UnifiedAlert:
    source: str                       # prometheus / alertmanager / loki / elastic / business_log / ticket / cloud
    alertname: str
    title: str
    description: str = ""
    severity: str = "warning"         # critical / warning / info（归一化后）
    labels: dict = field(default_factory=dict)
    starts_at: str = ""
    fingerprint: str = ""
    received_at: str = field(default_factory=now_iso)
    raw: dict = field(default_factory=dict)   # 原始报文截取，供研判上下文与审计

    def __post_init__(self) -> None:
        self.severity = normalize_severity(self.severity)
        if not self.fingerprint:
            self.fingerprint = make_fingerprint(self.source, self.alertname, self.labels)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "UnifiedAlert":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
