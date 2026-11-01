"""真实事故回放 runner（L3 验证）。

流程：对每个事故，把「当时可观测的症状 + 证据」通过平台真实 API（/api/research）
送研判，捕获完整输出，按**预先固定的决定性步骤**算覆盖率，逐字记录原始输出。

关键：决定性步骤与信号词都在跑之前定义好（见 incidents.py + 本文件 SIGNALS），
不允许看完结果再调整——这是为了不做"事后合理化"。

用法：python run_replay.py [--api http://127.0.0.1:8600] [--out REPLAY-RESULTS.md]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fixes import DECISIVE_FIXES  # noqa: E402
from incidents import INCIDENTS, RUBRIC  # noqa: E402

# ── 决定性步骤的"命中信号词"（跑前定义；命中任一即算该步骤被覆盖） ──
# 纪律：① 不使用单字关键词（曾用「段」匹配到"手段"造成虚高，已禁用）；
#       ② 信号词必须指向该步骤特有的动作，不能用通用样板词充数。
SIGNALS: dict[str, list[list[str]]] = {
    "cloudflare-2019-waf-cpu": [
        ["按组件", "哪个进程", "组件.*cpu", "定位到.*进程", "waf"],
        ["时间差", "时间线", "对齐", "关联.*部署", "部署时间", "变更时间"],
        [],  # generic（看最近变更）——不计分
        ["带外", "控制面", "out-of-band", "kill switch", "紧急开关", "绕过", "旁路"],
    ],
    "aws-s3-2017-capacity-removal": [
        ["运维操作", "谁执行", "操作记录", "误操作", "人为操作", "操作审计", "审计日志"],
        ["子系统", "index", "placement", "元数据", "容量下限", "minimum capacity"],
        ["恢复路径", "恢复时间", "rto", "重启耗时", "冷启动", "恢复.*风险"],
        ["依赖级联", "级联", "连带", "下游影响", "谁.*依赖"],
    ],
    "gitlab-2017-db-deletion": [
        ["wal", "归档", "archiv", "保留策略", "已回收"],
        ["主机名", "角色确认", "主备", "primary", "standby", "目标机", "执行前确认"],
        ["验证备份", "备份有效", "恢复验证", "restore test", "备份.*恢复"],
        [],  # generic（回溯近期操作）——不计分
    ],
    "meta-2021-bgp-dns": [
        ["dns 层", "bgp 层", "解析失败", "servfail", "分层.*定位"],
        ["bgp", "前缀", "prefix", "广播", "外部视角", "announce"],
        [],  # generic（维护窗口变更关联）——不计分
        ["带外", "out-of-band", "物理", "现场", "旁路", "bypass"],
        ["保护机制", "安全设计", "自动撤回", "放大器", "适得其反", "撤回"],
    ],
}


# 数据集名（--dataset 切换；用于报告里写清"这份分数是在哪个集上跑出来的"）
DATASET_NAME = "incidents"


def call(api: str, path: str, body: dict | None = None, timeout: int = 120) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(api + path, data=data, method="POST" if data else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return 0, str(e)


def output_text(resp: dict) -> str:
    """平台全部可判读文本（用于覆盖率匹配）。"""
    ctx = (resp or {}).get("context") or {}
    v = ctx.get("verdict") or {}
    parts = [
        v.get("root_cause", ""), v.get("recommendation", ""),
        " ".join(v.get("known", []) or []), " ".join(v.get("inferred", []) or []),
        " ".join(v.get("uncertain", []) or []),
    ]
    for s in v.get("investigation", []) or []:
        parts += [s.get("step", ""), s.get("finding", ""), s.get("evidence", "")]
    parts += list(v.get("verification", []) or [])
    for a in (v.get("remediation", {}) or {}).get("safe", []) or []:
        parts.append(str(a))
    for a in (v.get("remediation", {}) or {}).get("approval_required", []) or []:
        parts.append(str(a))
    plan = ctx.get("plan") or {}
    parts += list(plan.get("steps", []) or [])
    return "\n".join(parts).lower()


def coverage(incident_id: str, text: str) -> list[bool]:
    import re
    sig = SIGNALS.get(incident_id, [])
    return [any(re.search(k, text) for k in group) for group in sig]


def scored_steps(incident: dict, cov: list[bool]) -> list[bool]:
    """只把非 generic（需要真领域推理）的步骤纳入计分。

    第一版实验的教训：所有剧本都带"看最近变更/核对时间线"样板，
    按全步骤计分会把通用样板误记成"覆盖了事故特有步骤"——那是虚高。
    """
    steps = incident["decisive_steps"]
    out = []
    for i, c in enumerate(cov):
        if i < len(steps):
            out.append(bool(c) and not steps[i].get("generic", False))
        else:
            out.append(False)
    return out


def grade(scored: list[bool], verdict_text: str) -> int:
    """按预先固定的 3/2/1/0 规则打分（只数非 generic 步骤）。"""
    hits = sum(scored)
    if hits >= 2:
        return 3
    if hits == 1:
        return 2
    return 1 if verdict_text.strip() else 0


def remediation_text(resp: dict) -> str:
    """只看平台的**处置方案**文本（不看排查链/根因描述）——
    修复覆盖问的是"它准备做什么"，不是"它说了什么"。"""
    ctx = (resp or {}).get("context") or {}
    v = ctx.get("verdict") or {}
    rem = v.get("remediation", {}) or {}
    parts = []
    for a in rem.get("safe", []) or []:
        parts.append(str(a.get("action", "")))
    for a in rem.get("approval_required", []) or []:
        parts.append(str(a.get("action", "")))
    parts += list((ctx.get("plan") or {}).get("steps", []) or [])
    return "\n".join(parts).lower()


def fix_coverage(incident_id: str, rtext: str) -> bool:
    import re
    spec = DECISIVE_FIXES.get(incident_id)
    if not spec:
        return False
    return any(re.search(s, rtext) for s in spec["signals"])


def _ingest_events(api: str, inc: dict) -> None:
    """把事故的变更/运维操作事件通过真实接入层上报（change_log / ops_audit 源）。

    这样平台要"自己"按 service 召回时间线，而不是被直接喂结构化事件。
    """
    changes = inc.get("change_events") or []
    if changes:
        call(api, "/api/ingest", {"source": "change_log", "payload": {"events": [
            {"ts": e.get("ts", ""), "kind": e.get("kind", "config"),
             "actor": e.get("actor", ""), "target": e.get("target", ""),
             "detail": e.get("detail", ""), "ticket": e.get("ticket", "")}
            for e in changes]}})
    ops = inc.get("ops_audit_events") or []
    if ops:
        call(api, "/api/ingest", {"source": "ops_audit", "payload": {"events": [
            {"ts": e.get("ts", ""), "operator": e.get("operator", ""),
             "host": e.get("host", ""), "command": e.get("command", ""),
             "target": e.get("target", ""), "change_ticket": e.get("change_ticket", ""),
             "result": e.get("result", "")}
            for e in ops]}})


def run(api: str, out_path: Path, via_ingest: bool = True) -> int:
    lines: list[str] = []
    results: list[dict] = []
    total = 0
    a_dataset = DATASET_NAME

    lines.append("# 真实事故回放结果（L3 验证）")
    lines.append("")
    lines.append(f"- 运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 平台 API：`{api}`")
    lines.append(f"- 评分规则（跑前固定）：{RUBRIC}")
    lines.append("- 数据集：%d 个公开官方复盘事故，输入只含当时可观测症状；"
                 "决定性步骤与真实根因在跑前从复盘原文提取固定（见 `%s.py`）"
                 % (len(INCIDENTS), a_dataset))
    lines.append("- 变更/操作事件注入方式：**%s**%s" % (
        "走真实接入层（change_log/ops_audit → 平台自己按 service 召回）" if via_ingest
        else "直接塞进 alert.raw",
        "" if via_ingest else
        "　⚠️ 此方式把答案递给了研判链，分数会虚高（消融实测：留出集 raw=5/6 vs ingest=2/6）"))
    lines.append("")
    lines.append("| 事故 | 决定性步骤覆盖 | 得分 | 平台结论方向 |")
    lines.append("|---|---|---|---|")

    for inc in INCIDENTS:
        iid = inc["id"]
        alert = dict(inc["alert"])
        # ── 数据集注入方式（决定这份分数在测什么）───────────────
        # via_ingest=True（默认，诚实版）：
        #   变更/操作事件先通过真实接入层上报（source=change_log / ops_audit），
        #   再由平台自己按 service 召回时间线。测的是"平台能不能自己关联"。
        # via_ingest=False（旧版，会虚高）：
        #   把结构化事件直接塞进 alert.raw，等于把答案递到研判链手里。
        #   实测消融：留出集 5/6 → 2/6 的差值全部来自这个注入方式。
        raw = {"investigation": inc["evidence"]}
        if via_ingest:
            _ingest_events(api, inc)
        else:
            if inc.get("ops_audit_events"):
                raw["ops_audit_events"] = inc["ops_audit_events"]
            if inc.get("change_events"):
                raw["change_events"] = inc["change_events"]
        alert["raw"] = raw
        status, resp = call(api, "/api/research",
                            {"source": alert["source"], "alert": alert})
        if status != 200 or not isinstance(resp, dict) or not resp.get("context"):
            lines.append(f"| {inc['name']} | 调用失败 HTTP {status} | 0 | {str(resp)[:120]} |")
            results.append({"id": iid, "error": f"HTTP {status}: {resp}"})
            continue

        ctx = resp["context"]
        v = ctx.get("verdict") or {}
        text = output_text(resp)
        cov = coverage(iid, text)
        scored = scored_steps(inc, cov)
        g = grade(scored, v.get("root_cause", ""))
        total += g
        hits = sum(scored)
        n_scored = len(scored)
        rtext = remediation_text(resp)
        fix_ok = fix_coverage(iid, rtext)
        results.append({"id": iid, "grade": g, "coverage": cov, "scored": scored,
                        "fix_ok": fix_ok, "remediation_text": rtext,
                        "root_cause": v.get("root_cause", ""),
                        "verdict": v, "plan": ctx.get("plan"),
                        "judge_backend": ctx.get("judge_backend")})

        detail = "；".join(
            ("✅" if scored[i] else ("➖" if inc["decisive_steps"][i].get("generic") else "❌"))
            + inc["decisive_steps"][i]["text"][:26]
            for i in range(len(cov)))
        lines.append(f"| {inc['name']} | {hits}/{n_scored} 个计分步骤：{detail} | **{g}** | "
                     f"{(v.get('root_cause') or '')[:70]} |")

    lines.append("")
    lines.append(f"**总分：{total}/{len(INCIDENTS) * 3}**（{len(INCIDENTS)} 个事故 × 3 分；"
                 "只数需要领域推理的步骤，通用样板步骤「➖」不计分）")
    lines.append("")
    lines.append("> 判读说明：得分衡量的是「排查链是否包含复盘里真正定位根因的动作」，"
                 "不是最终一句话是否蒙对。❌ 的步骤就是平台**结构性缺失**的能力。")
    lines.append("")
    lines.append("> ⚠️ 注入方式决定了这份分数的含义：`--inject ingest` 测「平台能否自己召回并关联」；"
                 "`--inject raw` 只是把结构化事件直接递给研判链，**不代表泛化能力**。"
                 "两者差值 = 数据层（变更源是否接进链路）的贡献。")
    lines.append("")
    lines.append("## 修复覆盖：平台给的处置里，有没有复盘里真正止血的那一步？")
    lines.append("")
    lines.append("> 这是比「根因判得对不对」更硬的指标：**判对了但给的是通用动作**"
                 "（重启/扩容）在真实事故里等于没解决——复盘里止血的那一步往往不是通用动作。"
                 "信号词跑前固定，见 `fixes.py`。")
    lines.append("")
    lines.append("| 事故 | 复盘里真正止血的动作 | 平台给的处置 | 覆盖 | 该动作在白名单里吗 |")
    lines.append("|---|---|---|---|---|")
    fix_hits = 0
    for inc, r in zip(INCIDENTS, results):
        spec = DECISIVE_FIXES.get(inc["id"], {})
        ok = bool(r.get("fix_ok"))
        fix_hits += 1 if ok else 0
        plat = (r.get("remediation_text") or "").replace("\n", " ")[:110] or "（无处置输出）"
        reg = spec.get("registry_action")
        reg_txt = f"`{reg}`（B 类，需审批）" if reg else "**白名单里没有**"
        lines.append(f"| {inc['name'][:28]} | {spec.get('text', '')[:40]} | {plat} | "
                     f"{'✅' if ok else '❌'} | {reg_txt} |")
    lines.append("")
    lines.append(f"**修复覆盖：{fix_hits}/{len(INCIDENTS)}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 逐字记录 + 与决定性步骤对照
    for inc, r in zip(INCIDENTS, results):
        lines.append(f"## {inc['name']}")
        lines.append("")
        lines.append(f"- 来源（官方复盘）：{inc['source']}")
        lines.append(f"- 真实根因（跑前固定）：{inc['true_root_cause']}")
        lines.append("- 决定性步骤（跑前固定；➖=通用样板不计分）：")
        scored = r.get("scored") or []
        for i, s in enumerate(inc["decisive_steps"]):
            if s.get("generic"):
                mark = "➖"
            else:
                mark = "✅" if (i < len(scored) and scored[i]) else "❌"
            lines.append(f"  {i+1}. {mark} {s['text']}")
        lines.append("")
        if "error" in r:
            lines.append(f"**调用失败**：{r['error']}")
        else:
            v = r["verdict"]
            lines.append("### 平台原始输出（逐字）")
            lines.append("")
            lines.append(f"**根因判定**：{v.get('root_cause', '')}")
            lines.append("")
            lines.append(f"**置信度**：{v.get('confidence', '')} · **大脑**：{r.get('judge_backend', '')}")
            lines.append("")
            lines.append("**排查链**：")
            for s in v.get("investigation", []) or []:
                lines.append(f"- [{s.get('step')}] {s.get('finding')}")
            lines.append("")
            lines.append("**验证命令**：")
            for c in v.get("verification", []) or []:
                lines.append(f"- `{c}`")
            lines.append("")
            rem = v.get("remediation", {}) or {}
            if rem.get("safe"):
                lines.append("**🟢 可自动处置**：" + "；".join(
                    str(a.get("action")) for a in rem["safe"]))
            if rem.get("approval_required"):
                lines.append("**🔴 需审批处置**：" + "；".join(
                    f"{a.get('action')}（{a.get('downtime')}·{a.get('approver')}）"
                    for a in rem["approval_required"]))
            spec = DECISIVE_FIXES.get(inc["id"])
            if spec:
                lines.append("")
                lines.append(f"**修复覆盖对照**：复盘里真正止血的动作是「{spec['text']}」"
                             f"（{spec['note']}）→ 平台"
                             f"{'**覆盖到了**' if r.get('fix_ok') else '**没覆盖到** ❌'}"
                             f"（白名单对应动作：{spec.get('registry_action') or '无'}）")
            lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"total": total, "per_incident": [
        {"id": r["id"], "grade": r.get("grade"),
         "scored_hits": sum(r.get("scored") or []) if r.get("scored") else None}
        for r in results]}, ensure_ascii=False))
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8600")
    ap.add_argument("--out", default=str(Path(__file__).parent / "REPLAY-RESULTS.md"))
    # --dataset heldout：换成"从未参与剧本编写"的留出集，检验泛化能力而非记忆
    ap.add_argument("--dataset", default="incidents",
                    help="数据集模块名：incidents（见过/参与过剧本编写）或 heldout（留出集）")
    ap.add_argument("--inject", default="ingest", choices=["ingest", "raw"],
                    help="事件注入方式：ingest=走真实接入层（诚实版，默认）；"
                         "raw=直接塞进 alert.raw（旧版，会把答案递给研判链，分数虚高）")
    a = ap.parse_args()

    if a.dataset != "incidents":
        import importlib
        m = importlib.import_module(a.dataset)
        globals()["INCIDENTS"], globals()["SIGNALS"] = m.INCIDENTS, m.SIGNALS
        globals()["DECISIVE_FIXES"], globals()["RUBRIC"] = m.DECISIVE_FIXES, m.RUBRIC
        globals()["DATASET_NAME"] = a.dataset
        print(f"[dataset] 使用留出集 {a.dataset}：{len(m.INCIDENTS)} 个事故")

    run(a.api, Path(a.out), via_ingest=(a.inject == "ingest"))
