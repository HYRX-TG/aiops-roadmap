"""变更 / 操作时间线关联层（研判链的"上下文召回"核心）。

为什么要有这一层（L3 真实事故回放暴露的结构性缺口）：
  - AWS S3 2017 的真因是"一名运维按 playbook 执行命令，一个参数输错，
    实际下线了远多于预期的服务器"。如果研判链拿不到"这台机最近谁动过、
    执行了什么命令"，这一类根因**结构上就查不出来**——平台只能瞎猜容量/代码。
  - Fastly 2021 / GitHub 2018 的真因分别是"关联 5/12 的软件部署"和"关联 43 秒
    网络维护断连"。如果研判链拿不到"近期部署 / 维护窗口时间线"，这类关联
    只能靠 LLM 从散文里硬猜，命中不稳定。

本层把两类输入统一成一条**按时间排序的不可信数据时间线**，供研判消费：
  1. ops_audit（运维操作审计）：谁/何时/在哪台机/执行了什么命令/目标/变更单
  2. change_log（部署/配置/维护变更）：何时/什么类型/谁/目标/内容/变更单

消费方：
  - 规则大脑（免费、不耗 token）：受影响主机有近期操作 → 命中 ops_change_incident；
    近期有部署/配置/维护 → 做变更关联（命中 change_induced）。常见故障走这条便宜路径。
  - LLM 大脑（少见/难定位才需要）：把归一化时间线作为结构化证据段直接喂入提示词，
    不必再从散文里钓鱼，命中更稳、也更省 token。

数据来源（两种，同一代码路径）：
  - 回放 / 单测：嵌入在 alert.raw 的 ops_audit_events / change_events（结构化）。
  - 生产：IngestStore 里 source=ops_audit / change_log 的近期告警（按 host/service 召回）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


# 变更类型 → 中文标签（用于时间线展示与规则匹配）
CHANGE_KIND_LABEL = {
    "deploy": "部署",
    "config": "配置变更",
    "maintenance": "维护窗口",
}


@dataclass
class TimelineEvent:
    ts: str                      # 事件发生时间（ISO 或自由文本，如 "09:37"）
    kind: str                    # "ops"（运维操作）或 "change"（部署/配置/维护）
    actor: str                   # 操作人 / 团队 / 客户
    host: str                    # 受影响主机 / 子系统 / 目标
    detail: str                  # 命令原文 / 变更内容摘要
    change_type: str = ""        # change 专用：deploy/config/maintenance
    ticket: str = ""             # 变更单 / 工单号（空 = 无单）
    result: str = ""             # 操作结果（ops 专用）
    related: bool = True         # 是否与本次受影响对象直接相关（False=全局近期，
                                 # 只进时间线供参考，不抢占主剧本——见 judge 的主剧本选择）


def _as_str(v, default: str = "") -> str:
    return "" if v is None else str(v)


def from_ops_audit(raw_event: dict) -> TimelineEvent:
    """把 normalize_ops_audit 产生的 audit_event / 回放结构化事件归一成 TimelineEvent。"""
    e = raw_event or {}
    return TimelineEvent(
        ts=_as_str(e.get("ts")),
        kind="ops",
        actor=_as_str(e.get("operator")),
        host=_as_str(e.get("host")),
        detail=_as_str(e.get("command")),
        ticket=_as_str(e.get("change_ticket")),
        result=_as_str(e.get("result")),
    )


def from_change_log(raw_event: dict) -> TimelineEvent:
    """把 change_log 事件归一成 TimelineEvent。"""
    e = raw_event or {}
    ctype = _as_str(e.get("kind"), "config").lower()
    return TimelineEvent(
        ts=_as_str(e.get("ts")),
        kind="change",
        actor=_as_str(e.get("actor")),
        host=_as_str(e.get("target")),
        detail=_as_str(e.get("detail")),
        change_type=ctype,
        ticket=_as_str(e.get("ticket")),
    )


def _embedded_events(alert_raw: dict) -> tuple[list[TimelineEvent], list[TimelineEvent]]:
    """从 alert.raw 取出回放 / 单测嵌入的结构化事件。"""
    raw = alert_raw or {}
    ops = [from_ops_audit(e) for e in (raw.get("ops_audit_events") or []) if e]
    changes = [from_change_log(e) for e in (raw.get("change_events") or []) if e]
    return ops, changes


def _service_tokens(alert) -> list[str]:
    """从告警里抽"语义相关"的关键词，供三级召回的第 2 级使用。

    真实事故的变更 target 与告警 service 往往不是同一个字符串
    （"CDN 软件" vs "edge-cdn"、"光模块" vs "mysql-cluster"），
    所以要把 service 拆词（edge-cdn → edge/cdn），并带上标题里的关键词。
    """
    import re as _re
    svc = _service_of(alert)
    raw = (alert.raw if hasattr(alert, "raw") else (alert.get("raw") if isinstance(alert, dict) else {})) or {}
    title = (alert.get("title", "") if isinstance(alert, dict) else getattr(alert, "title", "")) or ""
    desc = (alert.get("description", "") if isinstance(alert, dict) else getattr(alert, "description", "")) or ""
    tokens: list[str] = []
    for part in _re.split(r"[-_./\s]+", svc):
        if len(part) >= 3:
            tokens.append(part)
    if svc and len(svc) >= 3:
        tokens.append(svc)
    # 标题/描述里的英文词与中文片段（用于匹配 target 里的关键词）
    for w in _re.findall(r"[a-zA-Z][a-zA-Z0-9]{2,}", f"{title} {desc}"):
        tokens.append(w.lower())
    for w in ("cdn", "边缘", "dns", "bgp", "数据库", "mysql", "主库", "复制", "网络", "骨干"):
        if w in f"{title} {desc}".lower():
            tokens.append(w)
    return list(dict.fromkeys(tokens))[:20]


def _store_events(store, host: str, service: str, limit: int = 25,
                  alert=None) -> tuple[list[TimelineEvent], list[TimelineEvent]]:
    """从生产 IngestStore 召回近期 ops_audit / change_log 事件。

    三级召回（精确 service → 语义 token → 全局近期）见
    IngestStore.recent_context。返回的事件带 related 标记：
    related=False 的只进时间线作参考，不抢主剧本。
    """
    ops: list[TimelineEvent] = []
    changes: list[TimelineEvent] = []
    if store is None:
        return ops, changes
    tokens = _service_tokens(alert) if alert is not None else []
    for source, collector in (("ops_audit", ops), ("change_log", changes)):
        rows = []
        if hasattr(store, "recent_context"):
            try:
                rows = store.recent_context(source, service=host or service,
                                            limit=limit, service_tokens=tokens)
            except Exception:
                rows = []
        if not rows:
            try:
                rows = store.recent_by_source(source, service=host or service, limit=limit)
            except Exception:
                rows = []
        for r in rows:
            aj = (r.get("alert_json") if isinstance(r, dict) else {}) or {}
            raw = aj.get("raw") or {}
            ev = (from_ops_audit(raw.get("audit_event") or {}) if source == "ops_audit"
                  else from_change_log(raw.get("change_event") or {}))
            related = bool(r.get("related", True)) if isinstance(r, dict) else True
            target = ev.host or ""
            if not related:
                ev.detail = f"[全局近期·目标={target}] {ev.detail}"
                ev.related = False
            collector.append(ev)
    # 丢弃解析失败的空事件
    ops = [e for e in ops if e.actor or e.detail]
    changes = [e for e in changes if e.actor or e.detail]
    return ops, changes


def _fmt_event(e: TimelineEvent) -> str:
    if e.kind == "ops":
        ticket = "无变更单" if not e.ticket else f"变更单 {e.ticket}"
        head = f"[{e.ts or '时间未知'}] [运维操作] {e.actor or '未知操作人'} 在 {e.host or '未知主机'}"
        body = f"执行：{e.detail or '（命令未记录）'}"
        tail = f"（目标：{e.host}；{ticket}"
        if e.result:
            tail += f"；结果：{e.result}"
        tail += "）"
        return f"{head} {body} {tail}"
    label = CHANGE_KIND_LABEL.get(e.change_type, "变更")
    ticket = f"变更单 {e.ticket}" if e.ticket else "无变更单"
    return (f"[{e.ts or '时间未知'}] [变更:{label}] {e.actor or '未知'} 对 "
            f"{e.host or '未知目标'}：{e.detail or '（内容未记录）'}（{ticket}）")


def build_research_context(alert, store=None, limit: int = 25) -> dict:
    """为一个故障告警构建"变更/操作时间线"上下文。

    返回：
      audit_timeline   —— 归一化、按时间排序的时间线文本（喂 LLM 提示词）
      ops_events       —— 运维操作事件列表（规则大脑消费）
      change_events    —— 变更事件列表（规则大脑消费）
      affected_host    —— 受影响主机/服务（关联键）
      has_ops / has_change
    """
    raw = (alert.raw if hasattr(alert, "raw") else (alert.get("raw") if isinstance(alert, dict) else {})) or {}
    embedded_ops, embedded_changes = _embedded_events(raw)
    store_ops, store_changes = _store_events(store, _host_of(alert), _service_of(alert),
                                             limit, alert=alert)

    # 去重合并（以 detail+ts 近似去重，避免回放嵌入与库里重复计数）
    ops = _dedupe(embedded_ops + store_ops)
    changes = _dedupe(embedded_changes + store_changes)

    all_ev = sorted(ops + changes, key=lambda e: e.ts or "")
    timeline = "\n".join(_fmt_event(e) for e in all_ev) if all_ev else "（时间线为空：近期无运维操作 / 变更记录）"

    return {
        "audit_timeline": timeline,
        "ops_events": [e.__dict__ for e in ops],
        "change_events": [e.__dict__ for e in changes],
        "affected_host": _host_of(alert) or _service_of(alert),
        "has_ops": bool(ops),
        "has_change": bool(changes),
    }


def _host_of(alert) -> str:
    if isinstance(alert, dict):
        return (alert.get("labels") or {}).get("host", "") or (alert.get("labels") or {}).get("service", "")
    return (alert.labels or {}).get("host", "") or (alert.labels or {}).get("service", "")


def _service_of(alert) -> str:
    if isinstance(alert, dict):
        return (alert.get("labels") or {}).get("service", "")
    return (alert.labels or {}).get("service", "")


def _dedupe(events: list[TimelineEvent]) -> list[TimelineEvent]:
    seen: set[tuple] = set()
    out: list[TimelineEvent] = []
    for e in events:
        key = (e.kind, e.ts, e.actor, e.host, e.detail)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
