"""验证 ① ops_audit 接入研判链 与 ② 变化点定位层 的规则大脑提升（零 token、零外部依赖）。

做法：用规则大脑（Judge，无 LLM）跑 6 个真实事故，对每个事故各跑两次：
  before = 只给散文 evidence（旧行为，时间线事件不进研判链）
  after  = 额外把结构化 ops_audit_events / change_events 喂给研判链（新行为）
对比规则分数（3/2/1/0，只数需要领域推理的步骤）的前后变化，量化 ①② 的贡献。

用法：python verify_tasks.py
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.resolve().parents[1] / "backend"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(BACKEND))

# 强制规则大脑：清掉一切 LLM 环境变量（零 token）
for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
    os.environ.pop(k, None)

import run_replay as R  # noqa: E402
from app.models import UnifiedAlert  # noqa: E402
from app.pipeline_research import ResearchPipeline  # noqa: E402
from app.triage import triage  # noqa: E402


def build_alert(inc: dict, with_events: bool) -> dict:
    alert = dict(inc["alert"])
    raw = {"investigation": inc["evidence"]}
    if with_events:
        if inc.get("ops_audit_events"):
            raw["ops_audit_events"] = inc["ops_audit_events"]
        if inc.get("change_events"):
            raw["change_events"] = inc["change_events"]
    alert["raw"] = raw
    return alert


def score_incident(rp: ResearchPipeline, inc: dict, with_events: bool) -> tuple[int, list[bool], dict]:
    a = UnifiedAlert.from_dict(build_alert(inc, with_events))
    run = rp.run(a, triage(a))
    ctx = run["context"]
    v = ctx["verdict"]
    text = R.output_text({"context": ctx})
    cov = R.coverage(inc["id"], text)
    scored = R.scored_steps(inc, cov)
    g = R.grade(scored, v.get("root_cause", ""))
    return g, scored, v


def run_dataset(name: str, module) -> None:
    INCIDENTS = module.INCIDENTS
    RUBRIC = module.RUBRIC
    # 动态替换 run_replay 的信号词表（heldout 用 heldout.SIGNALS；训练集信号词在 run_replay 内）
    import run_replay
    orig_signals = run_replay.SIGNALS
    run_replay.SIGNALS = getattr(module, "SIGNALS", None) or run_replay.SIGNALS
    run_replay.DECISIVE_FIXES = getattr(module, "DECISIVE_FIXES", {})

    rp = ResearchPipeline(db_path=tempfile.mktemp(suffix=".db"))
    print(f"\n{'='*78}\n数据集：{name}（{len(INCIDENTS)} 个事故）— 规则大脑 before/after\n{'='*78}")
    print(f"{'事故':42} {'before':>7} {'after':>7}  Δ")
    before_total = after_total = 0
    for inc in INCIDENTS:
        gb, _, _ = score_incident(rp, inc, with_events=False)
        ga, scored, v = score_incident(rp, inc, with_events=True)
        before_total += gb
        after_total += ga
        mark = "+" if ga > gb else ("=" if ga == gb else "-")
        detail = "；".join(
            ("✅" if scored[i] else ("➖" if inc["decisive_steps"][i].get("generic") else "❌"))
            + inc["decisive_steps"][i]["text"][:18]
            for i in range(len(scored)))
        print(f"{inc['name'][:40]:42} {gb:>7} {ga:>7}  {mark}  [{detail}]")
    maxscore = len(INCIDENTS) * 3
    print(f"{'合计':42} {before_total:>7} {after_total:>7}  "
          f"规则分 {before_total}→{after_total} / {maxscore}")
    run_replay.SIGNALS = orig_signals
    return before_total, after_total


def main() -> None:
    import incidents as train_mod
    import heldout as heldout_mod
    b1, a1 = run_dataset("训练集 incidents（S3/GitLab/CloudFlare/Meta）", train_mod)
    b2, a2 = run_dataset("留出集 heldout（Fastly/GitHub，未参与剧本编写）", heldout_mod)
    print(f"\n{'='*78}\n汇总：规则大脑总贡献\n"
          f"  训练集：{b1} → {a1}  （+{a1-b1}）\n"
          f"  留出集：{b2} → {a2}  （+{a2-b2}）\n"
          f"  ops_audit + 变化点定位层让规则大脑（免费路径）多覆盖了 "
          f"{ (a1-b1)+(a2-b2) } 个'需要领域推理的决定性步骤'\n"
          f"  含义：这些故障现在不必每次送 LLM 推理，规则路径即可命中——直接省 token。\n{'='*78}")


if __name__ == "__main__":
    main()
