"""AIOps 智能体测试台：让大模型**自己查证据**，而不是把答案喂进 prompt。

为什么要有这个文件（这是本轮最关键的实验设计）：
  之前的回放把「变更事件 / 运维审计 / 节点证据」直接拼进 prompt，
  模型只是把答案复述出来——测的是"阅读理解"，不是"排查能力"。
  真正的智能运维核心只有一个问题：
      **只给它症状，它能不能自己决定去查什么、怎么逐步缩小范围、最后定位根因？**

  所以这里给模型一套**只读工具**（模拟真实 SRE 能做的事），
  它必须主动调用工具获取证据。答案不在 prompt 里，而在"环境"里。

工具（全部只读，与真实 SRE 查故障的动作一一对应）：
  list_recent_changes(service?, window)   —— 查近期变更/部署/维护（对应 kubectl rollout history / 变更平台）
  query_ops_audit(host?, window)          —— 查谁在什么时候执行了什么命令（对应堡垒机审计）
  get_metrics(service, metric, window)    —— 查指标序列（对应 Prometheus）
  get_logs(service, level, limit)         —— 查错误日志（对应 Loki / ELK）
  get_topology(service)                   —— 查服务依赖与上下游（对应 CMDB）
  describe_resource(kind, name)           —— 查 K8s 对象详情（对应 kubectl describe）
  run_readonly(cmd)                       —— 执行白名单只读命令（本机沙箱）
  submit_diagnosis(...)                   —— 提交最终结论（结束排查）

设计纪律：
  1. 每轮只允许模型选一个动作，工具结果原样返回，不做任何提示性加工。
  2. 工具返回的数据里**故意混入噪声**（无关告警、正常指标、别人的变更），
     模型必须自己判断哪些相关。
  3. 不告诉模型"这是哪个事故"，不给标准答案，不给提示词暗示。
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable


# ── 环境抽象：一个"世界"，模型只能通过工具访问它 ─────────────
@dataclass
class World:
    """故障现场。所有字段都是模型需要通过工具才能拿到的"事实"。"""
    name: str
    symptom: str                        # 只给模型看这个（外加 service 名）
    service: str
    metrics: dict = field(default_factory=dict)      # {(service, metric): [(ts, value)]}
    logs: dict = field(default_factory=dict)         # {service: [(ts, level, msg)]}
    changes: list = field(default_factory=list)      # 变更事件
    ops_audit: list = field(default_factory=list)    # 运维操作审计
    topology: dict = field(default_factory=dict)     # {service: {"upstream":[],"downstream":[]}}
    resources: dict = field(default_factory=dict)    # {(kind,name): dict}
    truth: str = ""                                  # 真实根因（模型看不到，仅评分用）
    decisive: list = field(default_factory=list)     # 决定性步骤（评分用）
    now: float = 0.0                                 # 世界的"当前时间"（窗口过滤基准）

    def __post_init__(self):
        if not self.now:
            # 取世界里最晚的事件时间作为"现在"
            cands = [_parse_ts(x.get("ts", "")) for x in (self.changes + self.ops_audit)]
            cands = [c for c in cands if c is not None]
            base = max(cands) if cands else time.time()
            # 纯时刻（当天秒偏移）与世界时间混用时，补足到"当天"
            if base < 86400 * 400:
                base += time.mktime(time.strptime("2026-09-14", "%Y-%m-%d"))
            self.now = base + 60      # 略晚于最后一条事件


@dataclass
class ToolCall:
    tool: str
    args: dict
    result: str
    elapsed_ms: int = 0


# ── 工具实现 ─────────────────────────────────────────────────
_BANNED = re.compile(r"(rm |sudo |>\s*/|mkfs|dd if=|kill |systemctl (stop|restart)|"
                     r"kubectl (delete|apply|edit|scale|patch)|shutdown|reboot)", re.I)

READONLY_CMDS = {
    "uptime": lambda: _run(["uptime"]),
    "df": lambda: _run(["df", "-h"]),
    "free": lambda: _run(["free", "-m"]),
    "ps_top_cpu": lambda: _run(["ps", "aux", "--sort=-%cpu"]),
    "netstat": lambda: _run(["sh", "-c", "netstat -an 2>/dev/null | head -20"]),
    "top": lambda: "（沙箱环境不提供 top；用 ps_top_cpu 代替）",
}


def _run(cmd: list[str]) -> str:
    import subprocess
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        return (r.stdout or r.stderr or "")[:3000]
    except Exception as exc:
        return f"命令执行失败：{exc}"


def _parse_ts(ts: str) -> float | None:
    """解析世界里的时间戳。返回 epoch 秒。

    重要：所有世界都内置一个 `now`（取该世界里最晚的事件时间），
    窗口过滤必须相对这个 `now`，不能用真实当前时间——
    否则 2021 年的事故用 "24h" 窗口查永远是空（这是第一版测试台的 bug：
    工具静默返回空，模型被误导成"近期没有变更"）。
    """
    if not ts:
        return None
    ts = ts.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return time.mktime(time.strptime(ts, fmt))
        except ValueError:
            continue
    # 纯时刻 "22:52" / "09:44:51"（同一天内）：返回当天秒偏移
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = time.strptime(ts, fmt)
            return t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
        except ValueError:
            continue
    return None


def _window_filter(items: list[dict], window: str, now: float | None = None) -> list[dict]:
    """窗口过滤：支持 '1h' / '24h' / '7d' / '30d'，相对世界的 now。"""
    if not window or now is None:
        return items
    m = re.match(r"(\d+)([hdm])", window.lower())
    if not m:
        return items
    n, unit = int(m.group(1)), m.group(2)
    secs = n * {"m": 60, "h": 3600, "d": 86400}[unit]
    out = []
    for it in items:
        t = _parse_ts(it.get("ts", ""))
        if t is None:
            out.append(it)          # 解析不了就保留（不让窗口吞掉证据）
        elif now - t <= secs + 1:   # +1 容忍边界
            out.append(it)
    return out


class Toolbox:
    """模型可调用的只读工具集合。每次调用都记录（用于分析思维链路）。"""

    def __init__(self, world: World, history: list[ToolCall] | None = None):
        self.world = world
        self.history: list[ToolCall] = history if history is not None else []

    def _record(self, tool: str, args: dict, result: str, t0: float) -> str:
        self.history.append(ToolCall(tool, args, result,
                                     int((time.time() - t0) * 1000)))
        return result

    # ── 变更/审计 ──
    def list_recent_changes(self, service: str = "", window: str = "30d") -> str:
        t0 = time.time()
        items = _window_filter(self.world.changes, window, self.world.now)
        if service:
            # 真实变更平台按 target/service 过滤。这里用子串匹配（真实平台也常这样），
            # 但**不做语义联想**——"光模块维护" 不会因为和 mysql 有关就自动返回，
            # 模型必须先看全局变更列表，或者主动换关键词查。
            items = [c for c in items
                     if service.lower() in json.dumps(c, ensure_ascii=False).lower()]
        if not items:
            hint = ("（窗口内没有该服务的变更记录。可以试试 service=\"\" 看全局变更，"
                    "或扩大 window）" if service else "")
            return self._record("list_recent_changes", {"service": service, "window": window},
                                f"（窗口 {window} 内没有找到变更记录）{hint}", t0)
        lines = [f"[{c.get('ts','?')}] {c.get('kind','?')} by {c.get('actor','?')} "
                 f"target={c.get('target','?')} :: {c.get('detail','')}"
                 + (f" (ticket={c['ticket']})" if c.get("ticket") else " (无变更单)")
                 for c in items]
        return self._record("list_recent_changes", {"service": service, "window": window},
                            "\n".join(lines), t0)

    def query_ops_audit(self, host: str = "", window: str = "30d") -> str:
        t0 = time.time()
        items = _window_filter(self.world.ops_audit, window, self.world.now)
        if host:
            items = [e for e in items
                     if host.lower() in json.dumps(e, ensure_ascii=False).lower()]
        if not items:
            hint = ("（窗口内没有该主机的操作记录。可以试试 host=\"\" 看全局审计，"
                    "或扩大 window）" if host else "")
            return self._record("query_ops_audit", {"host": host, "window": window},
                                f"（窗口 {window} 内没有运维操作记录）{hint}", t0)
        lines = [f"[{e.get('ts','?')}] {e.get('operator','?')}@{e.get('host','?')} "
                 f"cmd={e.get('command','?')} target={e.get('target','?')} "
                 f"result={e.get('result','?')}"
                 + (f" (ticket={e['change_ticket']})" if e.get("change_ticket") else " (无变更单)")
                 for e in items]
        return self._record("query_ops_audit", {"host": host, "window": window},
                            "\n".join(lines), t0)

    # ── 指标/日志 ──
    def get_metrics(self, service: str = "", metric: str = "", window: str = "2h") -> str:
        t0 = time.time()
        keys = list(self.world.metrics.keys())
        sel = [k for k in keys
               if (not service or k[0] == service) and (not metric or metric in k[1])]
        if not sel:
            avail = ", ".join(f"{s}.{m}" for s, m in keys[:8])
            return self._record("get_metrics", {"service": service, "metric": metric},
                                f"（没有匹配的指标。可用：{avail or '无'}）", t0)
        out = []
        for s, m in sel[:4]:
            series = self.world.metrics[(s, m)]
            pts = " ".join(f"{v}" for _, v in series[-24:])
            out.append(f"{s}.{m}（最近 {len(series[-24:])} 点）: {pts}")
        return self._record("get_metrics", {"service": service, "metric": metric},
                            "\n".join(out), t0)

    def get_logs(self, service: str = "", level: str = "ERROR", limit: int = 20) -> str:
        t0 = time.time()
        items = self.world.logs.get(service, [])
        if not items and service:
            avail = ", ".join(self.world.logs.keys())
            return self._record("get_logs", {"service": service},
                                f"（{service} 没有日志。有日志的服务：{avail or '无'}）", t0)
        sel = [x for x in items if not level or x[1].upper() == level.upper()][-limit:]
        if not sel:
            sel = items[-limit:]
        body = "\n".join(f"[{ts}] {lv} {msg}" for ts, lv, msg in sel)
        return self._record("get_logs", {"service": service, "level": level},
                            body or "（无日志）", t0)

    def get_topology(self, service: str = "") -> str:
        t0 = time.time()
        tp = self.world.topology
        if not service:
            return self._record("get_topology", {}, json.dumps(tp, ensure_ascii=False)[:2000], t0)
        node = tp.get(service)
        if not node:
            return self._record("get_topology", {"service": service},
                                f"（拓扑里没有 {service}。已知服务：{list(tp)[:8]}）", t0)
        return self._record("get_topology", {"service": service},
                            json.dumps({service: node}, ensure_ascii=False), t0)

    def describe_resource(self, kind: str = "", name: str = "") -> str:
        t0 = time.time()
        res = self.world.resources
        sel = [k for k in res if (not kind or k[0] == kind) and (not name or k[1] == name)]
        if not sel:
            return self._record("describe_resource", {"kind": kind, "name": name},
                                f"（没有匹配资源。可用：{list(res)[:8]}）", t0)
        out = [f"=== {k[0]}/{k[1]} ===\n{json.dumps(res[k], ensure_ascii=False, indent=1)}"
               for k in sel[:3]]
        return self._record("describe_resource", {"kind": kind, "name": name},
                            "\n".join(out)[:3000], t0)

    # ── 只读命令（真实执行，白名单） ──
    def run_readonly(self, cmd: str = "") -> str:
        t0 = time.time()
        if _BANNED.search(cmd or ""):
            return self._record("run_readonly", {"cmd": cmd},
                                "拒绝：该命令不是只读操作（安全策略拦截）", t0)
        key = (cmd or "").strip().lower()
        fn = READONLY_CMDS.get(key)
        if not fn:
            return self._record("run_readonly", {"cmd": cmd},
                                f"只支持这些只读命令：{list(READONLY_CMDS)}", t0)
        return self._record("run_readonly", {"cmd": cmd}, fn(), t0)

    # ── 提交结论（终止） ──
    def submit_diagnosis(self, root_cause: str = "", chain: list | None = None,
                         confidence: str = "medium", evidence: list | None = None,
                         fix: str = "", uncertain: list | None = None) -> str:
        t0 = time.time()
        payload = json.dumps({
            "root_cause": root_cause, "chain": chain or [], "confidence": confidence,
            "evidence": evidence or [], "fix": fix, "uncertain": uncertain or []},
            ensure_ascii=False)
        return self._record("submit_diagnosis", {}, payload, t0)


TOOL_SCHEMA = """你可以调用以下只读工具（每次只能调一个，我会把结果返回给你）：

1. list_recent_changes(service="", window="30d")
   查近期变更/部署/配置/维护。window 形如 "1h" / "24h" / "7d" / "30d"。

2. query_ops_audit(host="", window="30d")
   查运维操作审计：谁在什么机器上执行了什么命令、有无变更单。

3. get_metrics(service="", metric="", window="2h")
   查指标序列。metric 是子串匹配（如 "cpu"、"latency"、"error"）。

4. get_logs(service="", level="ERROR", limit=20)
   查某服务的日志。

5. get_topology(service="")
   查服务依赖关系（上下游）。不填则返回全局拓扑。

6. describe_resource(kind="", name="")
   查 K8s 资源详情（pod / deployment / service / node / pvc）。

7. run_readonly(cmd="")
   执行白名单只读命令：uptime / df / free / ps_top_cpu / netstat。

8. submit_diagnosis(root_cause="", chain=[...], confidence="high|medium|low",
                    evidence=[...], fix="", uncertain=[...])
   提交最终结论（调用后排查结束）。
   chain 是排查链：[{"step":"...","finding":"...","evidence":"..."}]
   evidence 是你实际查到并引用的证据原文片段。
"""


def build_prompt(world: World, history: list[ToolCall], max_steps: int = 12) -> str:
    """构造当前这一轮给模型的 prompt（不含任何答案线索）。"""
    remaining = max_steps - len(history)
    lines = [
        "你是值班 SRE，正在处理一起线上故障。你只能通过工具查证据，不能凭猜测下结论。",
        "",
        f"【故障现象】{world.symptom}",
        f"【受影响服务】{world.service}",
        "",
        TOOL_SCHEMA,
        f"你最多可以调用 {max_steps} 次工具。已调用 {len(history)} 次，还剩 {remaining} 次。",
        "策略建议：先确认影响面和范围，再查最近有没有变更/操作，再看指标和日志，最后定位。",
        "",
    ]
    if remaining <= 2:
        lines.append(f"⚠️ 只剩 {remaining} 次工具调用！如果你已经有足够证据，"
                     "现在就应该调用 submit_diagnosis 提交结论——"
                     "**用光步数而不提交等于本次排查失败**。"
                     "证据不足也要给出当前最佳判断并写进 uncertain。")
    else:
        lines.append("不要急着下结论——证据不足时继续查。每轮只输出一个 JSON。")
    lines += [
        "",
        "输出格式（严格 JSON，不要 markdown 代码块）：",
        '{"tool":"工具名","args":{...},"reasoning":"我为什么现在要查这个"}',
    ]
    if history:
        lines += ["", "【已经查过的证据】"]
        for i, h in enumerate(history, 1):
            res = h.result if len(h.result) <= 1200 else h.result[:1200] + "…[截断]"
            lines.append(f"--- 第 {i} 次：{h.tool}({json.dumps(h.args, ensure_ascii=False)}) ---")
            lines.append(res)
    return "\n".join(lines)


def parse_action(text: str) -> dict | None:
    """从模型输出里解析 {tool, args}。容忍 markdown 代码块与多余文字。"""
    if not text:
        return None
    t = text.strip()
    if "```" in t:
        t = re.sub(r"```(?:json)?", "", t)
    try:
        i, j = t.index("{"), t.rindex("}")
        return json.loads(t[i:j + 1])
    except Exception:
        return None


def run_agent(world: World, call_llm: Callable[[list[dict]], str],
              max_steps: int = 12, verbose: bool = False,
              progress: Callable[[str], None] | None = None) -> dict:
    """跑一次完整的自主排查。返回结论 + 完整工具调用轨迹。"""
    tb = Toolbox(world)
    step = 0
    while step < max_steps:
        prompt = build_prompt(world, tb.history, max_steps)
        raw = call_llm([{"role": "user", "content": prompt}])
        act = parse_action(raw)
        if not act:
            # 解析失败：告诉模型重来一次（不消耗工具步数，但记一笔）
            tb.history.append(ToolCall("_parse_error", {}, (raw or "")[:300], 0))
            step += 1
            continue
        tool = act.get("tool", "")
        args = act.get("args") or {}
        reasoning = act.get("reasoning", "")
        if progress:
            progress(f"  [{step+1}] {tool}({json.dumps(args, ensure_ascii=False)[:80]}) "
                     f"— {reasoning[:70]}")
        fn = getattr(tb, tool, None)
        if tool not in ("submit_diagnosis",) and not callable(fn):
            tb.history.append(ToolCall("_bad_tool", {"tool": tool},
                                       f"没有这个工具：{tool}", 0))
            step += 1
            continue
        if tool == "submit_diagnosis":
            fn(**{k: v for k, v in args.items()
                  if k in ("root_cause", "chain", "confidence", "evidence",
                           "fix", "uncertain")})
            final = tb.history[-1].result
            return {"ok": True, "steps": step + 1, "diagnosis": json.loads(final),
                    "history": tb.history, "reasoning": reasoning}
        try:
            fn(**args)
        except TypeError as exc:
            tb.history.append(ToolCall(tool, args, f"参数错误：{exc}", 0))
        except Exception as exc:
            tb.history.append(ToolCall(tool, args, f"工具异常：{exc}", 0))
        step += 1

    return {"ok": False, "steps": step, "diagnosis": None, "history": tb.history,
            "reasoning": "", "error": f"超过 {max_steps} 步仍未提交结论"}
