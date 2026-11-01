"""多源告警接入层：8 类异构源 → 统一 UnifiedAlert。

8 类源（对齐同类研判系统的接入面；第 8 类是 L3 真实事故回放后新增）：
  1. prometheus     —— Prometheus 告警规则 fire（结构同 Alertmanager webhook）
  2. alertmanager   —— Alertmanager webhook v2
  3. loki           —— Loki 日志查询/推流（stream 标签 + 日志行）
  4. elastic        —— Elasticsearch 命中文档（错误日志告警）
  5. business_log   —— 业务日志事件（自研上报）
  6. ticket         —— 工单系统（人工/自动开单）
  7. cloud_monitor  —— 云监控告警（阿里云/腾讯云风格）
  8. ops_audit      —— 运维操作审计（谁在何时在哪台机执行了什么命令/有无变更单）
  9. change_log     —— 变更时间线（部署/配置/维护窗口：谁在何时对什么目标做了什么变更）

每个适配器都是 纯函数：payload(dict) -> list[UnifiedAlert]，坏数据跳过不抛异常。
"""
from __future__ import annotations

from .models import UnifiedAlert, now_iso

SOURCE_NAMES = (
    "prometheus", "alertmanager", "loki", "elastic",
    "business_log", "ticket", "cloud_monitor", "ops_audit", "change_log",
)


def _am_like(source: str, payload: dict) -> list[UnifiedAlert]:
    """Prometheus / Alertmanager 共通的 webhook 结构。"""
    out: list[UnifiedAlert] = []
    for a in payload.get("alerts", []):
        labels = a.get("labels", {}) or {}
        annotations = a.get("annotations", {}) or {}
        out.append(UnifiedAlert(
            source=source,
            alertname=labels.get("alertname", "unknown"),
            title=annotations.get("summary") or labels.get("alertname", "unknown"),
            description=annotations.get("description", ""),
            severity=labels.get("severity", "warning"),
            labels=dict(labels),
            starts_at=a.get("startsAt", "") or now_iso(),
            raw={"labels": labels, "annotations": annotations},
        ))
    return out


def normalize_prometheus(payload: dict) -> list[UnifiedAlert]:
    return _am_like("prometheus", payload)


def normalize_alertmanager(payload: dict) -> list[UnifiedAlert]:
    return _am_like("alertmanager", payload)


def normalize_loki(payload: dict) -> list[UnifiedAlert]:
    """Loki: {"data": {"result": [{"stream": {...}, "values": [["<ns>", "line"]]}]}}"""
    out: list[UnifiedAlert] = []
    result = (payload.get("data") or {}).get("result", []) or []
    for stream in result:
        labels = stream.get("stream", {}) or {}
        for _ts, line in stream.get("values", []) or []:
            level = labels.get("level") or labels.get("detected_level", "error")
            svc = labels.get("service") or labels.get("app", "unknown")
            out.append(UnifiedAlert(
                source="loki",
                alertname=f"log_{level}_{svc}",
                title=f"[{svc}] 错误日志激增",
                description=str(line)[:500],
                severity=level,
                labels={**labels, "service": svc},
                raw={"stream": labels, "line": str(line)[:500]},
            ))
    return out


def normalize_elastic(payload: dict) -> list[UnifiedAlert]:
    """Elasticsearch: {"hits": {"hits": [{"_source": {...}}, ...]}}"""
    out: list[UnifiedAlert] = []
    hits = ((payload.get("hits") or {}).get("hits")) or []
    for h in hits:
        s = h.get("_source", {}) or {}
        severity = s.get("loglevel") or s.get("level", "error")
        out.append(UnifiedAlert(
            source="elastic",
            alertname=s.get("error.type", "es_error"),
            title=str(s.get("message", "ES 错误日志命中"))[:120],
            description=str(s.get("message", ""))[:500],
            severity=severity,
            labels={"service": s.get("service", "unknown"), "env": s.get("env", "prod")},
            raw={"_source": {k: s.get(k) for k in ("service", "env", "message", "loglevel") if k in s}},
        ))
    return out


def normalize_business_log(payload: dict) -> list[UnifiedAlert]:
    """业务日志事件: {"events": [{"level","message","service","env","ts","event","investigation"}]}

    investigation = 探针采集的节点侧只读排查证据（K8s/系统），原样透传到 raw 供研判引用。
    """
    out: list[UnifiedAlert] = []
    for e in payload.get("events", []) or []:
        out.append(UnifiedAlert(
            source="business_log",
            alertname=e.get("event", "biz_event"),
            title=str(e.get("message", ""))[:120] or "业务事件",
            description=str(e.get("detail", "")),
            severity=e.get("level", "warning"),
            labels={"service": e.get("service", "unknown"), "env": e.get("env", "prod")},
            starts_at=e.get("ts", "") or now_iso(),
            raw={"event": e, "investigation": str(e.get("investigation", ""))},
        ))
    return out


def normalize_ticket(payload: dict) -> list[UnifiedAlert]:
    """工单: {"tickets": [{"id","title","priority","system","env"}]}"""
    prio_map = {"P0": "critical", "P1": "critical", "P2": "warning", "P3": "info"}
    out: list[UnifiedAlert] = []
    for t in payload.get("tickets", []) or []:
        prio = str(t.get("priority", "P2")).upper()
        out.append(UnifiedAlert(
            source="ticket",
            alertname=f"ticket_{t.get('id', 'NA')}",
            title=str(t.get("title", "工单"))[:120],
            description=str(t.get("detail", "")),
            severity=prio_map.get(prio, "warning"),
            labels={"system": t.get("system", "unknown"), "env": t.get("env", "prod"), "ticket_id": str(t.get("id", ""))},
            raw={"ticket": t},
        ))
    return out


def normalize_cloud_monitor(payload: dict) -> list[UnifiedAlert]:
    """云监控（阿里云风格）: {"alarms": [{"AlarmName","StateValue","Namespace","Level"}]}"""
    out: list[UnifiedAlert] = []
    for a in payload.get("alarms", []) or []:
        state = str(a.get("StateValue", "ALARM")).upper()
        out.append(UnifiedAlert(
            source="cloud_monitor",
            alertname=a.get("AlarmName", "cloud_alarm"),
            title=str(a.get("AlarmName", "云监控告警")),
            description=str(a.get("AlarmDescription", "")),
            severity="critical" if state == "ALARM" else "info",
            labels={"namespace": a.get("Namespace", ""), "env": "prod",
                    "instance": str(a.get("InstanceId", ""))},
            raw={"alarm": {k: a.get(k) for k in ("AlarmName", "StateValue", "Namespace", "InstanceId") if k in a}},
        ))
    return out


def normalize_ops_audit(payload: dict) -> list[UnifiedAlert]:
    """运维操作审计（L3 真实事故回放暴露的数据缺口：AWS S3 2017 的真因是
    "一条参数输错的命令"，平台若没有"谁在何时执行了什么"的输入，这类根因
    结构上就查不出来）。

    payload: {"events": [{"ts","operator","host","command","target",
                          "change_ticket","result"}]}
    每个审计事件归一化为一条告警（service=host，title=操作摘要）。
    """
    out: list[UnifiedAlert] = []
    for e in payload.get("events", []) or []:
        op = e.get("operator", "unknown")
        host = e.get("host", "unknown")
        cmd = str(e.get("command", ""))[:200]
        target = str(e.get("target", ""))[:100]
        ticket = e.get("change_ticket", "")
        summary = f"[ops-audit] {op} 在 {host} 执行：{cmd}"
        if target:
            summary += f"（目标：{target}）"
        if not ticket:
            summary += "（无变更单）"
        out.append(UnifiedAlert(
            source="ops_audit",
            alertname=f"ops_audit_{op}_{e.get('op_id', 'na')}",
            title=summary[:120],
            description=(f"operator={op} host={host} command={cmd} target={target} "
                         f"change_ticket={ticket or '无'} result={e.get('result', '')}"),
            severity="warning",
            labels={"service": host, "env": "prod", "operator": op,
                    "host": host, "change_ticket": str(ticket or "")},
            starts_at=e.get("ts", "") or now_iso(),
            raw={"audit_event": e},
        ))
    return out


def normalize_change_log(payload: dict) -> list[UnifiedAlert]:
    """变更时间线（部署/配置/维护窗口）：L3 回放暴露的"变化点定位"缺口。

    Fastly 2021 的真因要关联"5/12 的软件部署"，GitHub 2018 要关联"43 秒网络维护
    断连"——这类根因依赖"近期有什么变更"的时间线。平台若没有归一化的变更源，
    变更关联就只能靠 LLM 从散文里猜，命中不稳。

    payload: {"events": [{"ts","kind":"deploy|config|maintenance","actor","target",
                          "detail","ticket"}]}
    每个变更事件归一化为一条告警（service=target，title=变更摘要，severity=info）。
    """
    kind_label = {"deploy": "部署", "config": "配置变更", "maintenance": "维护窗口"}
    out: list[UnifiedAlert] = []
    for e in payload.get("events", []) or []:
        kind = str(e.get("kind", "config")).lower()
        actor = e.get("actor", "unknown")
        target = e.get("target", "unknown")
        detail = str(e.get("detail", ""))[:200]
        ticket = e.get("ticket", "")
        label = kind_label.get(kind, "变更")
        summary = f"[{label}] {actor} 对 {target}：{detail}"
        if not ticket:
            summary += "（无变更单）"
        out.append(UnifiedAlert(
            source="change_log",
            alertname=f"change_{kind}_{actor}",
            title=summary[:120],
            description=(f"actor={actor} kind={kind} target={target} detail={detail} "
                         f"ticket={ticket or '无'}"),
            severity="info",
            labels={"service": target, "env": "prod", "kind": kind,
                    "actor": actor, "change_ticket": str(ticket or "")},
            starts_at=e.get("ts", "") or now_iso(),
            raw={"change_event": e},
        ))
    return out


# 注册表：source 名 → 归一化函数（供接入层路由）
NORMALIZERS = {
    "prometheus": normalize_prometheus,
    "alertmanager": normalize_alertmanager,
    "loki": normalize_loki,
    "elastic": normalize_elastic,
    "business_log": normalize_business_log,
    "ticket": normalize_ticket,
    "cloud_monitor": normalize_cloud_monitor,
    "ops_audit": normalize_ops_audit,
    "change_log": normalize_change_log,
}


def normalize_any(source: str, payload: dict) -> list[UnifiedAlert]:
    """按 source 路由到对应适配器；未知源返回空并交给调用方记统计。"""
    fn = NORMALIZERS.get(source)
    if fn is None:
        return []
    try:
        return fn(payload)
    except Exception:
        return []  # 坏报文不拖垮接入层
