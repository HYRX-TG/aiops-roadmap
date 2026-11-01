"""智能体排查能力测试：只给症状，看大模型能不能自己查出根因。

三组对照（同一模型、同一温度）：

  A. 单轮基线（no-tools）
     直接把"症状"丢给模型，不提供任何工具。它只能凭先验知识猜。
     这一组回答："光靠模型脑子里那点通用经验，能抓到多少？"

  B. 工具自主排查（agentic）
     只给症状 + 一套只读工具。它必须自己决定查什么、看什么、怎么收敛。
     这一组回答："给它能力去查，它会不会用、能不能查到？"

  C. 人工喂全证据（oracle，上限参照）
     把世界里的全部证据一次性塞进 prompt（相当于最理想的可观测性）。
     这一组回答："如果证据都摆好了，它能推导到什么程度？"
     A→C 的差 = 证据的价值；B 与 C 的差 = 它自己"取证"的效率损失。

评分（跑前固定，只算需要真推理的步骤）：
  命中 ≥3 步 = 4 分；2 步 = 3 分；1 步 = 2 分；方向沾边 = 1 分；无/误导 = 0 分

用法：
  python run_agentic.py --api-key sk-xxx
  python run_agentic.py --api-key sk-xxx --only W2 --max-steps 15
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from harness import World, build_prompt, run_agent  # noqa: E402
from worlds import WORLDS  # noqa: E402


# ── 评分信号（跑前固定；只匹配"真推理"步骤，不给通用样板分） ──
SIGNALS: dict[str, list[str]] = {
    "edge-cdn-503": [
        # 1) 分层：分清边缘 vs 源站
        r"(边缘|edge|cdn).{0,18}(层|侧|节点).{0,25}(503|错误|返回)|"
        r"(503|错误).{0,18}(来自|产生|出自).{0,15}(边缘|cdn)|"
        r"源站.{0,20}(不是|并非).{0,10}(根因|问题|故障)|"
        r"(排除|不是).{0,12}源站.{0,12}(容量|被打爆|攻击)",
        # 2) 关联部署 + 客户配置变更
        r"(5月12|05-12|数周前|27\s*天前|v7\.2).{0,40}(部署|发布|版本)|"
        r"(部署|发布).{0,30}(5月12|05-12|数周前|27\s*天前|v7\.2)|"
        r"客户.{0,10}配置.{0,20}(变更|更新).{0,30}(关联|吻合|相关|触发)|"
        r"(关联|吻合).{0,20}客户.{0,10}配置",
        # 3) 客户配置合法 / 是触发器，根因在自家代码
        r"配置.{0,15}(合法|合规|本身没问题|没有错|有效)|"
        r"(只是|仅是).{0,10}(触发器|诱因|导火索)|"
        r"根因.{0,20}(在|是).{0,15}(代码|校验|验证逻辑|validator|bug)",
        # 4) 全局影响面 / 无灰度 / 无回退
        r"(无灰度|没有灰度|no canary|全量|同时下发|全网.{0,10}(生效|下发))|"
        r"(没有|缺少|无).{0,12}(回退|降级|fallback).{0,12}(路径|机制)?|"
        r"(校验|验证).{0,15}(失败|不通过).{0,20}(直接|立即).{0,12}(停|拒绝|abort)",
    ],
    "mysql-splitbrain": [
        # 1) 关联 43 秒网络维护
        r"(43\s*秒|forty.three|43s).{0,30}(断|分区|失联|中断)|"
        r"(网络|光模块|骨干|链路).{0,25}(维护|更换|替换).{0,30}(导致|引发|造成|关联)|"
        r"(维护|光模块).{0,25}(关联|吻合|对应|引起).{0,20}(数据库|复制|主库|故障)",
        # 2) 双主/脑裂
        r"(双主|脑裂|split.?brain|两个.{0,6}主库|两边.{0,10}(都|各自).{0,8}(接受|写入)|"
        r"two primaries|各自接受.{0,6}写入)",
        # 3) 自动切换是放大器
        r"(orchestrator|自动.{0,6}(切换|故障转移|failover)).{0,30}(放大|加剧|适得其反|"
        r"跨区|提升|promote|反效果)|"
        r"(跨区|cross.?region).{0,12}(提升|promote).{0,20}(放大|问题|根因|导致)",
        # 4) 完整性优先 + 恢复耗时
        r"(数据完整性|完整性).{0,12}(优先|高于|第一)|"
        r"(暂停|停止).{0,15}(webhook|构建|写入).{0,25}(完整|积压)|"
        r"(恢复|备份).{0,15}(数小时|耗时|没有演练|从未.{0,6}演练)|"
        r"(滞后|积压).{0,20}(非线性|幂|指数)",
    ],
    "S3-capacity-removal": [
        # 1) 查运维操作 / 谁在动容量
        r"(运维|操作|命令).{0,15}(审计|记录|历史)|"
        r"(最近|刚).{0,10}(有人|谁).{0,10}(执行|动|操作).{0,15}(命令|容量)|"
        r"(参数|count|数量).{0,15}(输错|写错|错误|填错)|"
        r"(误操作|人为操作|操作失误)",
        # 2) 区分子系统
        r"(index|索引|元数据).{0,20}(placement|分配|位置)|"
        r"(placement|分配).{0,20}(index|索引|元数据)|"
        r"(子系统|组件).{0,15}(index|placement|元数据|位置服务)|"
        r"(元数据|位置).{0,12}(服务|子系统).{0,12}(不可用|挂了|移除)",
        # 3) 恢复路径耗时
        r"(从未|没有|不曾).{0,12}(完整.{0,4})?(重启|冷启动|演练)|"
        r"(重启|恢复).{0,20}(耗时|数小时|远超预期|风险)|"
        r"(恢复路径|recovery).{0,20}(风险|耗时|没有验证)",
        # 4) 依赖级联
        r"(级联|连带|连锁|下游|依赖).{0,25}(计算|compute|块存储|block|监控|monitoring)|"
        r"(compute|ec2|计算|block|ebs|块存储|monitoring|监控).{0,25}(依赖|因.{0,6}而|受影响|报错)",
    ],
    # W4 虚构事故：信号词描述"机制"，不描述"具体答案"——
    # 避免模型只要猜到关键词就得分的假阳性
    "zephyr-quota-cascade": [
        # 1) 时间吻合 + 外部变更
        r"(14:05|14点05|配额.{0,6}调整).{0,40}(吻合|同时|起点|对应|关联)|"
        r"(积压|延迟|队列).{0,25}(开始|起点).{0,25}(14:05|配额|伙伴|partner)|"
        r"(partner|合作伙伴|外部).{0,20}(配额|quota).{0,20}(调整|变更|改动)",
        # 2) 排除我方发布
        r"(不是|并非|排除|非).{0,15}(我方|我们).{0,12}(发布|变更|部署)|"
        r"(我方|内部).{0,12}(没有|未).{0,12}(发布|变更|改动)|"
        r"非.{0,8}(我方|本地).{0,10}(代码|发布)",
        # 3) 两层配额值不一致（用"l1/l2 与 5000/500 同时出现"的宽松判据，
        #    因为模型可能按"外层/内层"或"上游/下游"表述，不能要求它复述我的措辞）
        r"(l1|l2|外层|内层|第一层|第二层|上游网关|下游网关|两级|两层).{0,200}"
        r"(5000|5k).{0,120}(500)(?!\d)",
        # 4) 静默排队 + 缓存 TTL
        r"(静默|不拒绝|不报错|排队).{0,20}(排队|queue|积压)|"
        r"(缓存|ttl|过期).{0,25}(不一致|延时|延迟|滞后)|"
        r"ttl.{0,20}(1800|30\s*分钟).{0,30}(导致|造成|根因)",
    ],
}

GENERIC_PATTERNS = [
    r"先查最近.{0,8}(变更|发布)",
    r"确认影响面",
    r"查看.{0,6}(日志|指标)",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def score_diagnosis(world: World, diag: dict) -> dict:
    """按预先固定的信号给分（只算决定性命中）。"""
    if not diag:
        return {"grade": 0, "hits": 0, "total": len(world.decisive), "matched": [],
                "reason": "无结论"}
    # 把 chain / evidence / root_cause / uncertain 全部拼起来判读
    parts = [diag.get("root_cause", ""), diag.get("fix", "")]
    for c in diag.get("chain") or []:
        if isinstance(c, dict):
            parts += [str(c.get("step", "")), str(c.get("finding", "")),
                      str(c.get("evidence", ""))]
        else:
            parts.append(str(c))
    parts += [str(x) for x in (diag.get("evidence") or [])]
    parts += [str(x) for x in (diag.get("uncertain") or [])]
    text = _normalize(" ".join(parts))

    sigs = SIGNALS.get(world.name, [])
    matched = [i for i, s in enumerate(sigs) if re.search(s, text)]
    hits = len(matched)
    total = len(sigs)

    if hits >= 3:
        grade = 4
    elif hits == 2:
        grade = 3
    elif hits == 1:
        grade = 2
    elif text.strip() and any(re.search(g, text) for g in GENERIC_PATTERNS):
        grade = 1
    else:
        grade = 0 if not text.strip() else 0
    return {"grade": grade, "hits": hits, "total": total, "matched": matched,
            "reason": f"命中 {hits}/{total} 个决定性步骤"}


# ── LLM 调用 ──────────────────────────────────────────────────
class LLM:
    def __init__(self, api_key: str, base_url: str, model: str, proxy: str = ""):
        self.key, self.base, self.model = api_key, base_url.rstrip("/"), model
        self.proxy = proxy
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def __call__(self, messages: list[dict], temperature: float = 0.2) -> str:
        body = json.dumps({"model": self.model, "messages": messages,
                           "temperature": temperature}).encode()
        req = urllib.request.Request(
            f"{self.base}/chat/completions", data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}"})
        if self.proxy:
            op = urllib.request.build_opener(
                urllib.request.ProxyHandler({"https": self.proxy, "http": self.proxy}))
            resp = op.open(req, timeout=90)
        else:
            resp = urllib.request.urlopen(req, timeout=90)
        data = json.loads(resp.read().decode())
        self.calls += 1
        u = data.get("usage") or {}
        self.prompt_tokens += int(u.get("prompt_tokens") or 0)
        self.completion_tokens += int(u.get("completion_tokens") or 0)
        return data["choices"][0]["message"]["content"]


# ── 三组实验 ──────────────────────────────────────────────────
def arm_no_tools(world: World, llm: LLM) -> dict:
    """A 组：只给症状，不给工具。"""
    prompt = (
        "你是资深 SRE。下面是一起线上故障的现象，你没有权限查任何系统，只能基于经验判断。\n\n"
        f"【现象】{world.symptom}\n【受影响服务】{world.service}\n\n"
        "请输出严格 JSON：\n"
        '{"root_cause":"你认为的根因","confidence":"high|medium|low",'
        '"chain":[{"step":"排查步骤","finding":"你的推断"}],'
        '"fix":"处置建议","uncertain":["你无法确认的"]}'
    )
    raw = llm([{"role": "user", "content": prompt}])
    return {"arm": "no_tools", "raw": raw, "diag": _parse(raw), "tool_calls": []}


def arm_oracle(world: World, llm: LLM) -> dict:
    """C 组：把世界里的全部证据一次性喂进去（理想可观测性）。"""
    changes = "\n".join(f"[{c.get('ts')}] {c.get('kind')} {c.get('actor')} -> "
                        f"{c.get('target')}: {c.get('detail')}" for c in world.changes)
    ops = "\n".join(f"[{e.get('ts')}] {e.get('operator')}@{e.get('host')}: "
                    f"{e.get('command')} -> {e.get('result')}" for e in world.ops_audit)
    metrics = "\n".join(
        f"{s}.{m}: " + " ".join(str(v) for _, v in series[-12:])
        for (s, m), series in world.metrics.items())
    logs = "\n".join(
        f"--- {svc} ---\n" + "\n".join(f"[{ts}] {lv} {msg}" for ts, lv, msg in items[-8:])
        for svc, items in world.logs.items())
    topo = json.dumps(world.topology, ensure_ascii=False)
    res = json.dumps({f"{k[0]}/{k[1]}": v for k, v in world.resources.items()},
                     ensure_ascii=False)
    prompt = (
        "你是资深 SRE。下面是一起线上故障的**全部可观测证据**，请做根因分析。\n\n"
        f"【现象】{world.symptom}\n【受影响服务】{world.service}\n\n"
        f"【变更记录】\n{changes}\n\n【运维操作审计】\n{ops}\n\n"
        f"【指标】\n{metrics}\n\n【日志】\n{logs}\n\n"
        f"【拓扑】\n{topo}\n\n【资源】\n{res}\n\n"
        "注意：有些证据是无关噪声，请自己判断。\n"
        "请输出严格 JSON：\n"
        '{"root_cause":"根因","confidence":"high|medium|low",'
        '"chain":[{"step":"步骤","finding":"从哪条证据看到什么","evidence":"证据原文"}],'
        '"fix":"处置建议","evidence":["你引用的证据"],"uncertain":["无法确认的"]}'
    )
    raw = llm([{"role": "user", "content": prompt}])
    return {"arm": "oracle", "raw": raw, "diag": _parse(raw), "tool_calls": []}


def arm_agentic(world: World, llm: LLM, max_steps: int, verbose: bool) -> dict:
    """B 组：给工具集，让它自主排查。"""
    def progress(msg: str):
        if verbose:
            print(msg)

    res = run_agent(world, llm, max_steps=max_steps, verbose=verbose, progress=progress)
    tools = [{"tool": h.tool, "args": h.args,
              "result_len": len(h.result), "ms": h.elapsed_ms}
             for h in res["history"]]
    return {"arm": "agentic", "ok": res["ok"], "steps": res["steps"],
            "diag": res.get("diagnosis"), "tool_calls": tools,
            "history": res["history"], "error": res.get("error", "")}


def _parse(raw: str) -> dict | None:
    if not raw:
        return None
    t = raw.strip()
    if "```" in t:
        t = re.sub(r"```(?:json)?", "", t)
    try:
        return json.loads(t[t.index("{"): t.rindex("}") + 1])
    except Exception:
        return None


# ── LLM 评审（交叉校验关键词评分）──────────────────────────
# 为什么需要：关键词评分只能判断"有没有说出我要的词"，
# 无法判断"推理是否成立"。W4 的 oracle 明明推出了完整机制（l2 缓存 1800s、
# 按旧配额 500 静默排队），却因为措辞不同只拿到 1/4——这是评分器的错，不是模型的错。
# 一个真正的智能运维平台最终也要用"语义判据/结构化验证"而不是字符串匹配来验收。
JUDGE_PROMPT = """你是资深 SRE 评审。下面是一次故障排查的输出，以及本次事故的
真实根因和"决定性步骤"清单。请判断该排查**是否实质上命中了每一步**——
不要求措辞一致，只要推理链体现了该步骤的核心判断就算命中。

【真实根因】{truth}

【决定性步骤】
{steps}

【被评审的排查输出】
{answer}

只输出严格 JSON：
{{"hits":[true/false,...按步骤顺序],"score":0-4,"reason":"一句话说明扣分点"}}
评分规则：命中>=3 步=4分；2步=3分；1步=2分；有推理但0步命中=1分；无有效输出=0分。"""


def llm_judge(world: World, diag: dict | None, llm: "LLM") -> dict:
    if not diag:
        return {"hits": [False] * len(world.decisive), "score": 0, "reason": "无结论"}
    answer = json.dumps(diag, ensure_ascii=False)[:6000]
    steps = "\n".join(f"{i}. {d}" for i, d in enumerate(world.decisive, 1))
    prompt = JUDGE_PROMPT.format(truth=world.truth, steps=steps, answer=answer)
    raw = llm([{"role": "user", "content": prompt}], temperature=0.0)
    out = _parse(raw) or {"hits": [], "score": 0, "reason": "评审解析失败"}
    if not isinstance(out.get("hits"), list):
        out["hits"] = []
    return out


# ── 主流程 ────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("LLM_API_KEY", ""))
    ap.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL",
                                                         "https://api.deepseek.com/v1"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL", "deepseek-chat"))
    ap.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY", ""))
    ap.add_argument("--only", default="", help="只跑某个世界（名字或 W1/W2/W3）")
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--arms", default="no_tools,agentic,oracle")
    ap.add_argument("--judge", default="llm", choices=["none", "llm"],
                    help="评分方式：llm=关键词+LLM评审双评（默认）；none=只关键词")
    ap.add_argument("--out", default=str(HERE / "AGENTIC-RESULTS.md"))
    ap.add_argument("--save-json", default=str(HERE / "agentic_raw.json"),
                    help="把全部原始结果存成 JSON（便于离线复评）")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if not args.api_key:
        print("缺少 --api-key（或 LLM_API_KEY 环境变量）")
        return 2

    llm = LLM(args.api_key, args.base_url, args.model, args.proxy)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    worlds = WORLDS
    if args.only:
        worlds = [w for w in WORLDS if args.only in (w.name, w.name.split("-")[0])
                  or args.only.lower() in w.name.lower()]
        if not worlds:
            print(f"找不到世界：{args.only}；可选：{[w.name for w in WORLDS]}")
            return 2

    rows: list[dict] = []
    for world in worlds:
        print(f"\n{'='*70}\n世界：{world.name}　服务={world.service}\n{'='*70}")
        for arm in arms:
            t0 = time.time()
            print(f"\n--- [{arm}] ---")
            if arm == "no_tools":
                res = arm_no_tools(world, llm)
            elif arm == "oracle":
                res = arm_oracle(world, llm)
            elif arm == "agentic":
                res = arm_agentic(world, llm, args.max_steps, args.verbose)
            else:
                continue
            elapsed = round(time.time() - t0, 1)
            sc = score_diagnosis(world, res.get("diag"))
            res.update({"world": world.name, "elapsed_s": elapsed, **sc})
            if args.judge == "llm":
                j = llm_judge(world, res.get("diag"), llm)
                res["llm_judge"] = j
            rows.append(res)
            diag = res.get("diag") or {}
            extra = ""
            if res.get("llm_judge"):
                extra = f" · LLM评审 {res['llm_judge'].get('score')}/4"
            print(f"  得分 {sc['grade']}/4（{sc['reason']}）{extra} · {elapsed}s")
            if arm == "agentic":
                tools_used = [t["tool"] for t in res["tool_calls"]
                              if not t["tool"].startswith("_")]
                print(f"  用了 {len(tools_used)} 次工具：{tools_used}")
            if diag.get("root_cause"):
                print(f"  根因：{diag['root_cause'][:150]}")

    write_report(rows, Path(args.out), args, llm)
    # 存原始结果（工具调用链里有 result 全文，便于事后分析失败模式）
    raw_dump = []
    for r in rows:
        item = {k: v for k, v in r.items() if k != "history"}
        if r.get("history"):
            item["history"] = [{"tool": h.tool, "args": h.args,
                                "result": h.result[:2000]} for h in r["history"]]
        raw_dump.append(item)
    Path(args.save_json).write_text(
        json.dumps(raw_dump, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"原始结果已写入 {args.save_json}")
    print(f"\n报告已写入 {args.out}")
    return 0


def write_report(rows: list[dict], out: Path, args, llm: LLM) -> None:
    worlds = {w.name: w for w in WORLDS}
    lines = [
        "# 智能体排查能力实测：只给症状，看大模型能不能自己查出根因",
        "",
        f"- 模型：`{args.model}`（temperature 0.2）",
        f"- 时间：{time.strftime('%Y-%m-%d %H:%M')}",
        f"- 总调用：{llm.calls} 次 · tokens in/out = "
        f"{llm.prompt_tokens}/{llm.completion_tokens}",
        "",
        "## 三组对照在测什么",
        "",
        "| 组 | 做法 | 回答的问题 |",
        "|---|---|---|",
        "| A 单轮 | 只给症状，不给任何工具 | 光凭模型先验知识能抓到多少？ |",
        "| B 工具自主 | 给只读工具，自己决定查什么 | **它会不会用工具、能不能查到？**（本题核心） |",
        "| C 喂全证据 | 全部证据一次性塞进 prompt | 证据齐全时能推到什么程度？（上限参照） |",
        "",
        "## 结果总表",
        "",
        "| 世界 | A 单轮 | B 工具自主 | C 喂全证据 | B 用的工具 | B 步数 | B 耗时 |",
        "|---|---|---|---|---|---|---|",
    ]
    has_judge = any(r.get("llm_judge") for r in rows)
    if has_judge:
        lines = lines[:-2] + [
            "| 世界 | A 单轮（关键词/LLM） | B 工具自主（关键词/LLM） | C 喂全证据（关键词/LLM） | B 工具数 | B 步数 | B 耗时 |",
            "|---|---|---|---|---|---|---|",
        ]
    for name, world in worlds.items():
        by = {r["arm"]: r for r in rows if r["world"] == name}
        if not by:
            continue
        a = by.get("no_tools", {})
        b = by.get("agentic", {})
        c = by.get("oracle", {})
        tools = [t["tool"] for t in (b.get("tool_calls") or [])
                 if not t["tool"].startswith("_")]

        def g(r):
            if not r:
                return "–"
            kw = f"{r['grade']}/4"
            lj = r.get("llm_judge")
            return f"{kw} / {lj.get('score','–')}/4" if lj else kw
        lines.append(f"| {name} | {g(a)} | **{g(b)}** | {g(c)} | "
                     f"{len(tools)} 次 | {b.get('steps','–')} | {b.get('elapsed_s','–')}s |")

    lines += ["", "## 逐世界详情", ""]
    for name, world in worlds.items():
        by = {r["arm"]: r for r in rows if r["world"] == name}
        if not by:
            continue
        lines += [f"### {name}", "",
                  f"- **症状（模型只看到这个）**：{world.symptom}",
                  f"- **真实根因（模型看不到）**：{world.truth}", "",
                  "**决定性步骤（跑前固定）**："]
        for i, d in enumerate(world.decisive, 1):
            lines.append(f"{i}. {d}")
        lines.append("")

        for arm, label in (("no_tools", "A 单轮基线"),
                           ("agentic", "B 工具自主"),
                           ("oracle", "C 喂全证据")):
            r = by.get(arm)
            if not r:
                continue
            diag = r.get("diag") or {}
            j = r.get("llm_judge")
            jtxt = f"　｜　LLM 评审：{j.get('score')}/4（{j.get('reason','')}）" if j else ""
            lines += [f"#### {label} —— {r['grade']}/4（{r['reason']}）{jtxt}", ""]
            if arm == "agentic":
                tools = [t for t in (r.get("tool_calls") or [])
                         if not t["tool"].startswith("_")]
                lines.append(f"**工具调用链（{len(tools)} 次）**：")
                for t in tools:
                    lines.append(f"- `{t['tool']}` {json.dumps(t['args'], ensure_ascii=False)}")
                lines.append("")
            if diag.get("root_cause"):
                lines.append(f"**根因判定**：{diag['root_cause']}")
            if diag.get("chain"):
                lines.append("")
                lines.append("**排查链**：")
                for c in diag["chain"][:8]:
                    if isinstance(c, dict):
                        lines.append(f"- [{c.get('step','')}] {c.get('finding','')}")
                    else:
                        lines.append(f"- {c}")
            if diag.get("uncertain"):
                lines += ["", f"**不确定项**：{'；'.join(str(x) for x in diag['uncertain'][:4])}"]
            if r.get("error"):
                lines += ["", f"**失败**：{r['error']}"]
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
