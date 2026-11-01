"""告警风暴压测：量化降噪率 / 分流分布 / 时延 / Token 节省 → 产出简历可用的真实数字。

风暴构成（默认 10,000 条，可 --total 调整）：
  40% 真实告警（8 类告警 × 10 个服务，critical/warning/info 加权）
  25% 精确重复（同指纹重放）
  15% 测试环境噪声（env=test）
  10% 心跳探活
  10% info 低价值噪声
  —— 后 60% 即「重复与低信噪比噪声」

运行：python bench/flood.py [--total 10000]
输出：bench/report.md + bench/summary.json
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ingest import IngestPipeline          # noqa: E402
from app.pipeline_research import ResearchPipeline  # noqa: E402
from app.models import UnifiedAlert            # noqa: E402
from app.triage import triage                  # noqa: E402

SERVICES = ["payment", "order", "api", "gateway", "auth", "mysql", "redis", "cart", "search", "notify"]
ALERTNAMES = ["HighErrorRate", "LatencyP99High", "CPUThrottling", "DiskUsageHigh",
              "ConnPoolExhausted", "OOMKilled", "CertExpiring", "UpstreamTimeout"]


def _am(alertname: str, severity: str, env: str, service: str, instance: str) -> tuple[str, dict]:
    return "alertmanager", {"alerts": [{
        "labels": {"alertname": alertname, "severity": severity,
                   "env": env, "service": service, "namespace": "prod", "instance": instance},
        "annotations": {"summary": f"{service} {alertname}", "description": f"service={service} env={env}"},
    }]}


def gen_storm(total: int, seed: int = 42):
    """生成 (source, payload) 告警风暴。

    构成（60% 噪声）：
      40% 真实告警   —— 每条唯一 instance，指纹唯一，全部应放行
      25% 精确重放   —— 从真实告警抽样原样重发，应全部被去重抑制
      15% 测试环境   —— env=test，应全部被门控拦截
      10% 心跳探活   —— 应全部被门控拦截
      10% info 噪声  —— 应全部被门控拦截
    """
    rnd = random.Random(seed)
    storm: list[tuple[str, dict]] = []
    n_real = int(total * 0.40)
    n_dup = int(total * 0.25)
    n_test = int(total * 0.15)
    n_hb = int(total * 0.10)
    n_info = total - n_real - n_dup - n_test - n_hb

    real: list[tuple[str, dict]] = []
    for i in range(n_real):
        sev = rnd.choices(["critical", "warning", "info"], weights=[3, 5, 2])[0]
        real.append(_am(rnd.choice(ALERTNAMES), sev, "prod", rnd.choice(SERVICES), f"pod-{i}"))
    storm += real
    storm += [rnd.choice(real) for _ in range(n_dup)]                      # 精确重放
    storm += [_am("HighErrorRate", "critical", "test", rnd.choice(SERVICES), f"test-pod-{i}")
              for i in range(n_test)]
    storm += [_am(f"Heartbeat_{i}", "info", "prod", "api", f"hb-{i}") for i in range(n_hb)]
    storm += [_am("RoutineCheck", "info", "prod", rnd.choice(SERVICES), f"info-{i}")
              for i in range(n_info)]
    rnd.shuffle(storm)
    return storm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=10_000)
    ap.add_argument("--research-sample", type=int, default=30)
    ap.add_argument("--out", default=str(ROOT / "bench"))
    args = ap.parse_args()

    storm = gen_storm(args.total)
    pipe = IngestPipeline(window_seconds=600, max_per_window=1)

    # ── 接入层：降噪 + 分流 ─────────────────────────────────
    latencies: list[float] = []
    t0 = time.perf_counter()
    for source, payload in storm:
        s = time.perf_counter()
        pipe.ingest(source, payload)
        latencies.append((time.perf_counter() - s) * 1000)   # ms / 条
    wall = time.perf_counter() - t0
    lat_sorted = sorted(latencies)
    p50 = lat_sorted[int(len(lat_sorted) * 0.50)]
    p95 = lat_sorted[int(len(lat_sorted) * 0.95)]
    stats = pipe.stats()

    # ── 研判主链路时延（抽样 P0/P1，mock RAG + 规则研判）────
    research_lat: list[float] = []
    rp = ResearchPipeline(db_path=str(ROOT / "bench" / "_bench_research.db"))
    sampled = 0
    for alert, t in list(pipe.output):
        if t.route == "research" and sampled < args.research_sample:
            s = time.perf_counter()
            rp.run(alert, t)
            research_lat.append((time.perf_counter() - s) * 1000)
            sampled += 1
    r_sorted = sorted(research_lat)
    r_p50 = r_sorted[int(len(r_sorted) * 0.50)] if r_sorted else 0
    r_p95 = r_sorted[int(len(r_sorted) * 0.95)] if r_sorted else 0

    # ── Token 节省口径：全量都进 LLM vs 只有 research 路由进 ──
    ingested = stats["ingested"]
    forwarded = stats["forwarded"]
    research_n = stats["triage"]["routes"]["research"]
    token_saved = 1 - research_n / ingested if ingested else 0

    summary = {
        "storm_total": args.total,
        "wall_seconds": round(wall, 3),
        "throughput_per_sec": round(args.total / wall, 1),
        "ingested": ingested,
        "noise_reduction_ratio": stats["noise_reduction_ratio"],
        "dropped_dedup": stats["dropped_dedup"],
        "dropped_gate": stats["dropped_gate"],
        "forwarded": forwarded,
        "triage_levels": stats["triage"]["levels"],
        "triage_routes": stats["triage"]["routes"],
        "ingest_latency_ms": {"p50": round(p50, 3), "p95": round(p95, 3)},
        "research_latency_ms": {"p50": round(r_p50, 1), "p95": round(r_p95, 1),
                                 "sample": len(research_lat)},
        "token_saved_ratio_vs_full_llm": round(token_saved, 4),
    }

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = f"""# 告警风暴压测报告

- 风暴规模：**{args.total:,} 条**（60% 重复与低信噪比噪声），单进程串行接入
- 吞吐：**{summary['throughput_per_sec']:,} 条/秒**（总耗时 {summary['wall_seconds']}s）

## 降噪与分流
| 指标 | 数值 |
|---|---|
| 接入总量 | {ingested:,} |
| 滑动窗口去重拦截 | {stats['dropped_dedup']:,} |
| 入口门控拦截 | {stats['dropped_gate']:,} |
| **综合降噪率** | **{stats['noise_reduction_ratio'] * 100:.1f}%** |
| 放行进后端 | {forwarded:,} |
| P0/P1/P2/P3 | {stats['triage']['levels']['P0']} / {stats['triage']['levels']['P1']} / {stats['triage']['levels']['P2']} / {stats['triage']['levels']['P3']} |
| research 主链路 / batch / notify | {research_n} / {stats['triage']['routes']['batch']} / {stats['triage']['routes']['notify']} |
| **Token 节省（vs 全量进大模型）** | **{token_saved * 100:.1f}%** |

## 时延（本机实测，模拟 RAG + 规则研判）
| 阶段 | P50 | P95 |
|---|---|---|
| 接入层（去重+门控+分流） | {p50:.3f} ms/条 | {p95:.3f} ms/条 |
| 研判主链路端到端（样本 {len(research_lat)}） | {r_p50:.1f} ms | {r_p95:.1f} ms |

> 复现：`python bench/flood.py --total 10000`
"""
    (out / "report.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
