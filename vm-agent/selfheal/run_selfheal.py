"""自愈闭环实测：真的注入故障 → 平台真的诊断 → agent 真的修 → 探针真的验证。

这一轮要回答的问题是"它到底能不能把问题解决掉"——所以这里**没有 mock**：
  · 故障是真的：真起 CPU hogs、真写 80MB 气球文件、真改坏配置文件、真杀进程
  · 诊断是真的：走真实 HTTP API（/api/ingest → 去重 → 门控 → 分级 → 研判 → 护栏）
  · 修复是真的：agent 真的 kill / 真删文件 / 真恢复配置 / 真拉起服务
  · 验证是真的：真发 healthz、真量目录、真查进程是否还活着

用法：
  python run_selfheal.py --api http://127.0.0.1:8600 --out SELFHEAL-RESULTS.md
后端需以 AIOPS_AUTO_REMEDIATE=1 启动，否则 A 类动作不会自动下单（会走审批路径）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = Path(os.environ.get("SANDBOX_DIR", HERE / "sandbox"))
PORT = int(os.environ.get("SANDBOX_PORT", "8080"))
STATE = DIR / "state.json"
TMP = DIR / "tmp"
CONFIG = DIR / "config.json"
CONFIG_BAK = DIR / "config.json.bak"
QUOTA_MB = float(os.environ.get("TMP_QUOTA_MB", "64"))

sys.path.insert(0, str(HERE))
import executor as agent   # noqa: E402  节点侧修复 agent（同一份代码，生产里独立进程跑）

# agent 的日志并进 runner 的日志文件（避免 stdout 编码/截断问题）
_agent_log = agent.log
agent.log = lambda m: log("[agent] " + m)

SERVICE = "sandbox-payment"
# 每轮实测一个唯一标记：① 避免去重层把这次告警和上一轮的合并
# ② find_run 能精确找到本轮刚产出的研判 run，而不是历史 run
RUN_TAG = time.strftime("%H%M%S")


# ── HTTP 小工具 ────────────────────────────────────────────────
API_TOKEN = os.environ.get("AIOPS_API_TOKEN", "")


def http_json(method: str, url: str, payload: dict | None = None, timeout: int = 15) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["X-AIOps-Token"] = API_TOKEN
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


_LOG = open(HERE / "_selfheal.log", "w", encoding="utf-8")


def log(msg: str) -> None:
    print(f"[run {time.strftime('%H:%M:%S')}] {msg}", flush=True)
    _LOG.write(f"[run {time.strftime('%H:%M:%S')}] {msg}\n")
    _LOG.flush()


# ── 沙箱服务生命周期 ────────────────────────────────────────────
def start_service() -> subprocess.Popen:
    if TMP.exists():
        shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({"SANDBOX_DIR": str(DIR), "SANDBOX_PORT": str(PORT),
                "TMP_QUOTA_MB": str(QUOTA_MB)})
    p = subprocess.Popen([sys.executable, str(HERE / "sandbox_app.py")], cwd=str(HERE),
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"app_script": str(HERE / "sandbox_app.py"),
                                 "service_pid": p.pid, "hog_pids": []}, ensure_ascii=False),
                     encoding="utf-8")
    for _ in range(40):
        ok, _ = agent.http_probe()
        if ok:
            log(f"沙箱服务就绪（PID {p.pid}）")
            return p
        time.sleep(0.5)
    raise RuntimeError("沙箱服务未能就绪")


def healthy() -> tuple[bool, str]:
    return agent.http_probe()


# ── 故障注入（每一种都是真的破坏） ──────────────────────────────
def inject_cpu_hog() -> str:
    # 只起 1/4 核数的 hog：够造成可测的抢占就行，别把这台机器压死
    n = max(4, (os.cpu_count() or 4) // 4)
    pids = []
    for _ in range(n):
        # 硬超时 90s：即使后面的清理逻辑没跑到，hog 也会自己退出（不会拖垮机器）
        p = subprocess.Popen(
            [sys.executable, "-c",
             "import time;t=time.time()\nwhile time.time()-t<90: pass"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pids.append(p.pid)
    st = json.loads(STATE.read_text(encoding="utf-8"))
    st["hog_pids"] = pids
    STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return f"启动 {n} 个 CPU hog（PID {pids[:3]}…，90s 后自愈退出）"


def inject_disk_balloon() -> str:
    chunk = b"\0" * (4 * 1024 * 1024)
    need = int(QUOTA_MB * 1.3)          # 超过配额 30%
    written = 0
    i = 0
    while written < need:
        i += 1
        f = TMP / f"balloon_{i}.dat"
        with open(f, "wb") as fh:
            for _ in range(4):          # 每个文件 16MB
                fh.write(chunk)
        written += 16
    return f"写入 {i} 个气球文件共 {written}MB（配额 {QUOTA_MB}MB）"


def inject_config_corrupt() -> str:
    good = CONFIG.read_text(encoding="utf-8")
    with open(CONFIG, "w", encoding="utf-8") as f:
        f.write(good[: len(good) // 2] + ',"mode": "MAINTENANCE-BAD"[[')   # 破坏 JSON
    return "把 config.json 改成非法 JSON（模拟配置变更事故）"


def inject_service_down() -> str:
    st = json.loads(STATE.read_text(encoding="utf-8"))
    pid = int(st.get("service_pid", 0))
    os.kill(pid, signal.SIGTERM)
    time.sleep(0.5)
    return f"杀掉服务进程 PID {pid}"


# ── 场景定义 ────────────────────────────────────────────────────
# 每个场景：注入函数 + 送进平台的告警文本 + 期望剧本 + 期望动作 + 是否需要人工放行
SCENARIOS = [
    {
        "id": "S1", "name": "CPU 被吵闹邻居抢占",
        "inject": inject_cpu_hog,
        "alert": "服务响应变慢，CPU 负载高，怀疑同机其他进程抢占 CPU 资源",
        "expect_playbook": "resource_contention", "expect_action": "kill_noisy_neighbor",
        "expect_approval": False,
    },
    {
        "id": "S2", "name": "临时目录被气球文件撑爆（磁盘写满）",
        "inject": inject_disk_balloon,
        "alert": "磁盘写满：数据分区使用率 96%，写入报 No space left on device",
        "expect_playbook": "disk_pressure", "expect_action": "cleanup_temp_files",
        "expect_approval": False,
    },
    {
        "id": "S3", "name": "运维操作改坏配置（有操作审计）",
        "inject": inject_config_corrupt,
        "alert": "运维执行了配置修改操作后服务不可用，操作审计可见该命令，无变更单",
        "expect_playbook": "ops_change_incident", "expect_action": "restore_config_from_backup",
        "expect_approval": False,
    },
    {
        "id": "S4", "name": "服务进程被杀（OOM）",
        "inject": inject_service_down,
        "alert": "服务进程消失，healthz 无法连接，容器 OOMKilled 内存超限被杀",
        "expect_playbook": "oom_killed", "expect_action": "restart_service",
        "expect_approval": True,
    },
]


def cleanup_after(sid: str) -> None:
    """把沙箱恢复到健康态（只用于跑下一个场景，不参与"是否修好"的判定）。"""
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    for pid in st.get("hog_pids", []):
        agent._terminate(int(pid))
    st["hog_pids"] = []
    if STATE.exists():
        STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    for p in TMP.glob("balloon_*.dat") if TMP.exists() else []:
        try:
            p.unlink()
        except OSError:
            pass
    if CONFIG_BAK.exists():
        shutil.copyfile(CONFIG_BAK, CONFIG)
    for extra in (str(CONFIG) + ".broken",):
        if os.path.exists(extra):
            os.remove(extra)
    time.sleep(1.0)


def wait_broken(timeout: float = 20) -> tuple[bool, str]:
    """等探针真的变坏（证明故障是真发生了，不是我们嘴上说坏了）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok, detail = healthy()
        if not ok:
            return True, detail
        time.sleep(0.5)
    return False, "注入后健康探针仍为 200（故障未生效）"


def wait_recovered(timeout: float = 60) -> tuple[bool, str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok, detail = healthy()
        if ok:
            return True, detail
        time.sleep(0.5)
    return False, healthy()[1]


def send_alert(api: str, text: str, sid: str) -> dict:
    marker = f"[{sid}-{RUN_TAG}]"
    payload = {"source": "business_log", "payload": {"events": [{
        "level": "critical", "event": f"selfheal_{sid.lower()}_{RUN_TAG}",
        "message": f"{text} {marker}",
        "detail": text, "service": SERVICE, "env": "prod",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "investigation": "top: 见节点侧采集；df/du 见 /api/alerts 证据",
    }]}}
    return http_json("POST", f"{api}/api/ingest", payload)


def find_run(api: str, sid: str, timeout: float = 20) -> tuple[str, dict]:
    """按告警指纹找到研判 run（接入层 → 自动研判队列 → 工作流，全链路异步）。"""
    deadline = time.time() + timeout
    marker = f"[{sid}-{RUN_TAG}]"
    while time.time() < deadline:
        data = http_json("GET", f"{api}/api/alerts?limit=50")
        for it in data.get("items", []):
            if marker in (it.get("title") or "") and it.get("run_id"):
                run = http_json("GET", f"{api}/api/runs/{it['run_id']}")
                if run.get("status") == "done":
                    return it["run_id"], run
        time.sleep(0.5)
    return "", {}


def run_scenario(api: str, sc: dict) -> dict:
    log(f"===== {sc['id']} {sc['name']} =====")
    r: dict = {"id": sc["id"], "name": sc["name"], "expect_action": sc["expect_action"],
               "expect_playbook": sc["expect_playbook"]}

    t0 = time.time()
    r["inject_detail"] = sc["inject"]()
    broken, bdetail = wait_broken()
    r["broken_confirmed"], r["broken_detail"] = broken, bdetail
    r["t_broken"] = round(time.time() - t0, 2)
    log(f"  故障生效：{broken} —— {bdetail[:90]}")
    if not broken:
        r["result"] = "未触发"
        return r

    # ── 送告警 → 平台诊断 ──
    t1 = time.time()
    ing = send_alert(api, sc["alert"], sc["id"])
    r["ingest_admitted"] = len(ing.get("admitted", []))
    run_id, run = find_run(api, sc["id"])
    r["run_id"] = run_id
    r["t_diagnose"] = round(time.time() - t1, 2)
    if not run_id:
        r["result"] = "研判未产出"
        return r

    ctx = run.get("context") or {}
    v = ctx.get("verdict") or {}
    plan = ctx.get("plan") or {}
    r["playbook"] = v.get("playbook", "")
    r["suggested_action"] = ctx.get("suggested_action", "")
    r["plan_state"] = plan.get("state", "")
    r["auto_actions"] = plan.get("auto_actions", [])
    log(f"  诊断：剧本={r['playbook']} 护栏动作={r['suggested_action']} "
        f"自动下单={r['auto_actions']}")

    # ── 没有自动下单 → 走人工审批（我们扮演值班工程师） ──
    r["approved"] = False
    order_ids = list(plan.get("auto_orders") or [])
    if not order_ids:
        t2 = time.time()
        act = ctx.get("suggested_action", "")
        try:
            ap = http_json("POST", f"{api}/api/approve",
                           {"run_id": run_id, "action": act, "decision": "approved",
                            "approver": "值班工程师（自愈实测代履行）",
                            "note": f"{sc['id']} 自愈实测：护栏要求人工放行"})
            order_ids = ap.get("remediation_orders") or []
            r["approved"] = bool(order_ids)
            r["approve_msg"] = ap.get("msg", "")
            log(f"  审批：{r['approved']} —— {ap.get('msg', '')[:80]}")
        except Exception as exc:
            r["approve_error"] = str(exc)
            log(f"  审批失败：{exc}")
        r["t_approve"] = round(time.time() - t2, 2)
    r["order_ids"] = order_ids
    r["need_approval_expected"] = sc["expect_approval"]
    r["approval_matches_expectation"] = (r["approved"] == sc["expect_approval"])

    # ── agent 拉单执行（真的修） ──
    t3 = time.time()
    log(f"  准备让 agent 拉单执行，本轮订单：{order_ids}")
    try:
        results = agent.run_once(SERVICE, only_ids=order_ids) if order_ids else []
    except BaseException as exc:      # 实测脚本不能因为一次异常就丢掉整轮证据
        import traceback
        log(f"  agent 执行阶段异常：{type(exc).__name__}: {exc}")
        log("  " + traceback.format_exc().replace("\n", "\n  ")[-800:])
        results = []
    log(f"  agent 执行阶段结束，结果 {len(results)} 条")
    r["agent_results"] = results
    r["t_exec"] = round(time.time() - t3, 2)
    r["actions_executed"] = [x["action"] for x in results]
    r["exec_ok"] = all(x["exec_ok"] for x in results) if results else False
    r["verify_ok"] = all(x["verify"]["ok"] for x in results) if results else False

    # ── 探针验证是否真的好了 ──
    ok, detail = wait_recovered()
    r["recovered"], r["recover_detail"] = ok, detail
    r["t_recover"] = round(time.time() - t0, 2)
    r["action_matches_expectation"] = (sc["expect_action"] in r["actions_executed"])
    r["result"] = "已自愈" if (ok and r["verify_ok"]) else (
        "执行了但没修好" if results else "未修复")
    log(f"  结果：{r['result']} · 动作={r['actions_executed']} · 健康={ok}")
    return r


def write_report(results: list[dict], out: Path, api: str) -> None:
    total = len(results)
    healed = sum(1 for r in results if r.get("result") == "已自愈")
    auto = sum(1 for r in results if not r.get("approved") and r.get("result") == "已自愈")
    lines = [
        "# 自愈闭环实测（第四轮）：真的注入故障，看平台能不能真的修好",
        "",
        f"后端：{api}　服务：{SERVICE}　时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 一句话结论",
        "",
        f"**{healed}/{total} 个真实故障被真正修复**（其中 {auto} 个是全自动、"
        f"{healed - auto} 个经人工审批放行后修复）。",
        "这里的\"修好\"不是平台自己宣称的：是独立的健康探针（`GET /healthz`）从 500 变回 200，",
        "且探针检查的是**真实状态**——配置文件是否合法 JSON、临时目录是否超配额、",
        "固定规模计算的墙钟耗时是否回到基线。",
        "",
        "## 逐场景结果",
        "",
        "| 场景 | 故障生效 | 命中剧本 | 平台动作 | 是否需审批 | agent 执行 | 探针恢复 | 耗时 | 结果 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} {r['name']} | {'✅' if r.get('broken_confirmed') else '❌'} | "
            f"{r.get('playbook', '-')} | {','.join(r.get('actions_executed') or ['-'])} | "
            f"{'需审批（已放行）' if r.get('approved') else '全自动'} | "
            f"{'✅' if r.get('exec_ok') else '❌'} | {'✅ 200' if r.get('recovered') else '❌ 仍 500'} | "
            f"{r.get('t_recover', '-')}s | **{r.get('result')}** |")

    lines += ["", "## 分阶段耗时（MTTR 拆解）", "",
              "| 场景 | 故障生效 | 诊断 | 审批 | 执行+验证 | 端到端 |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} | {r.get('t_broken', '-')}s | {r.get('t_diagnose', '-')}s | "
                     f"{r.get('t_approve', '-')}s | {r.get('t_exec', '-')}s | "
                     f"**{r.get('t_recover', '-')}s** |")

    lines += ["", "## 每个场景到底发生了什么", ""]
    for r in results:
        lines.append(f"### {r['id']} {r['name']}")
        lines.append(f"- 注入：{r.get('inject_detail')}")
        lines.append(f"- 故障确认：`{r.get('broken_detail')}`")
        lines.append(f"- 平台诊断：剧本 `{r.get('playbook')}` → 护栏动作 `{r.get('suggested_action')}`"
                     f" → 计划状态 `{r.get('plan_state')}`")
        if r.get("approved"):
            lines.append(f"- 人工审批：{r.get('approve_msg')}")
        for x in r.get("agent_results", []):
            lines.append(f"- agent 执行 `{x['action']}`：{x['exec_detail'][:120]}")
            lines.append(f"  - 验证探针（{x['verify'].get('type')}）："
                         f"{'通过' if x['verify']['ok'] else '未通过'} —— {x['verify']['detail'][:120]}")
            lines.append(f"  - 引擎判定：`{x['engine'].get('status')}`")
        lines.append(f"- 最终探针：`{r.get('recover_detail')}`")
        lines.append("")

    lines += ["", "## 诚实说明（这一轮里哪些不是真的）", "",
              "1. **CPU 抢占的判据是「抢占比 = 墙钟时间 / 本进程 CPU 时间」**，不是读 cgroup 配额。"
              "进程被挤下 CPU 时墙钟在走而 CPU 时间不涨，比值就上升（实测空闲 ≈1.0×，"
              "注入 8 个 hog 后 1.76×）。它不依赖核数和启动基线，比\"跟基线比\"更本质，"
              "但仍然只是**间接指标**——生产里应该看 cgroup cpu.stat 的 throttling 计数。",
              "2. **磁盘写满用\"目录配额\"模拟**（写气球文件把临时目录撑过配额），"
              "没有真的把某个分区写满——真写满分区在本机风险太大。"
              "检测与清理逻辑和真实磁盘写满场景是一致的（找大头 → 清安全的文件 → 验证水位）。",
              "3. **沙箱里的\"版本\"就是配置文件**，所以 rollback_version 的实现与"
              "restore_config 相同；生产里版本回滚走 rollout undo。",
              "4. **生产对应动作与沙箱动作不等价**：沙箱里\"终止失控进程\"，"
              "生产里对应的是\"给吵闹邻居设 CPU Limit\"（不杀对方进程）——"
              "沙箱用更激进的等价动作，是因为单机沙箱没有 cgroup。",
              "5. **审批是我们代履行的**：S4 里平台按设计拒绝自动重启（OOM 重启只是缓解、"
              "不解决根因），由脚本扮演值班工程师放行。",
              ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8600")
    ap.add_argument("--out", default=str(HERE / "SELFHEAL-RESULTS.md"))
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    proc = start_service()
    results = []
    try:
        for sc in SCENARIOS:
            if args.only and sc["id"] != args.only:
                continue
            results.append(run_scenario(args.api.rstrip("/"), sc))
            cleanup_after(sc["id"])
            time.sleep(1.5)
    finally:
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except OSError:
            pass

    write_report(results, Path(args.out), args.api)
    print(json.dumps([{"id": r["id"], "result": r.get("result"),
                       "actions": r.get("actions_executed"),
                       "recovered": r.get("recovered"),
                       "approved": r.get("approved")} for r in results],
                     ensure_ascii=False))
    print(f"报告已写入 {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
