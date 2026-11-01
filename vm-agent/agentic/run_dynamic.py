"""动态环境验证：真实系统状态 → 模型自主排查。

与 worlds.py 的区别（这是本轮最硬的验证）：
  worlds.py 是**静态世界**（我预先写好的证据），证明的是"模型会不会用工具"。
  本文件是**真实系统**：真起进程、真写文件、真改配置，工具读的是操作系统实际状态。
  模型看到的一切都必须靠真实的 ps / df / 文件读取得来，我无法预先编造。

流程：
  1. 起沙箱服务（sandbox_app.py），确认健康
  2. 注入真实故障（CPU 抢占 / 磁盘撑爆 / 配置改坏 / 进程被杀）
  3. 用真实工具让模型自主排查（工具直接读 OS 状态）
  4. 模型提交结论 → 用独立探针验证它是否说对了
  5. 恢复现场，跑下一个

用法：
  python run_dynamic.py --api-key sk-xxx
  python run_dynamic.py --only cpu_hog
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELFHEAL = HERE.parent / "selfheal"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SELFHEAL))

from harness import ToolCall, parse_action, _BANNED  # noqa: E402

SANDBOX_DIR = Path(os.environ.get("SANDBOX_DIR", str(HERE / "dyn-sandbox")))
PORT = int(os.environ.get("SANDBOX_PORT", "8099"))
QUOTA_MB = float(os.environ.get("TMP_QUOTA_MB", "64"))
LOG = SANDBOX_DIR / "app.log"
TMP = SANDBOX_DIR / "tmp"
CONFIG = SANDBOX_DIR / "config.json"
CONFIG_BAK = SANDBOX_DIR / "config.json.bak"
STATE = SANDBOX_DIR / "state.json"


# ══════════════════════════════════════════════════════════════
# 真实系统工具（读的是 OS 实际状态，不是预置数据）
# ══════════════════════════════════════════════════════════════
class RealToolbox:
    def __init__(self):
        self.history: list[ToolCall] = []

    def _rec(self, tool, args, result, t0):
        self.history.append(ToolCall(tool, args, result, int((time.time() - t0) * 1000)))
        return result

    # ── 服务健康（真实 HTTP 探测）──
    def get_service_health(self, port: int = PORT) -> str:
        t0 = time.time()
        import urllib.request
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with op.open(f"http://127.0.0.1:{port}/healthz", timeout=5) as r:
                body = r.read().decode()
            return self._rec("get_service_health", {"port": port},
                             f"HTTP {r.status}\n{body}", t0)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            return self._rec("get_service_health", {"port": port},
                             f"HTTP {e.code}（服务活着但自检不过）\n{body}", t0)
        except Exception as e:
            return self._rec("get_service_health", {"port": port},
                             f"不可达（进程可能已死）：{type(e).__name__}", t0)

    # ── 真实进程列表（含 CPU/内存）──
    def list_processes(self, sort_by: str = "cpu", limit: int = 12) -> str:
        t0 = time.time()
        try:
            if os.name == "nt":
                ps = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process | Sort-Object -Descending CPU | "
                     "Select-Object -First 15 Id,ProcessName,CPU,"
                     "@{n='WS_MB';e={[math]::Round($_.WorkingSet64/1MB,1)}} | "
                     "Format-Table -AutoSize | Out-String -Width 200"],
                    capture_output=True, text=True, timeout=20)
                out = ps.stdout or ps.stderr
            else:
                key = "-%mem" if sort_by == "mem" else "-%cpu"
                ps = subprocess.run(["ps", "aux", f"--sort={key}"],
                                    capture_output=True, text=True, timeout=15)
                out = "\n".join(ps.stdout.splitlines()[:limit + 1])
            return self._rec("list_processes", {"sort_by": sort_by}, out[:3000], t0)
        except Exception as e:
            return self._rec("list_processes", {}, f"查询失败：{e}", t0)

    # ── 真实磁盘占用（沙箱临时目录）──
    def get_disk_usage(self) -> str:
        t0 = time.time()
        used = 0
        files = []
        if TMP.exists():
            for p in TMP.rglob("*"):
                if p.is_file():
                    try:
                        sz = p.stat().st_size
                        used += sz
                        files.append((p.name, sz))
                    except OSError:
                        pass
        files.sort(key=lambda x: -x[1])
        pct = used / (QUOTA_MB * 1048576) * 100 if QUOTA_MB else 0
        lines = [f"临时目录 {TMP}", f"配置配额 {QUOTA_MB:.0f}MB，实际占用 {used/1048576:.1f}MB"
                 f"（{pct:.0f}%，阈值 100%）", "最大的文件："]
        for name, sz in files[:8]:
            lines.append(f"  {name}  {sz/1048576:.1f}MB")
        if not files:
            lines.append("  （空）")
        return self._rec("get_disk_usage", {}, "\n".join(lines), t0)

    # ── 真实配置校验 ──
    def check_config(self) -> str:
        t0 = time.time()
        if not CONFIG.exists():
            return self._rec("check_config", {}, f"配置文件不存在：{CONFIG}", t0)
        raw = CONFIG.read_text(encoding="utf-8", errors="replace")
        lines = [f"文件：{CONFIG}（{len(raw)} 字节）",
                 f"备份存在：{CONFIG_BAK.exists()}"]
        try:
            json.loads(raw)
            lines.append("JSON 解析：合法")
        except json.JSONDecodeError as e:
            lines.append(f"JSON 解析：**非法** —— {e}")
        lines.append("--- 内容片段 ---")
        lines.append(raw[:800])
        return self._rec("check_config", {}, "\n".join(lines), t0)

    # ── 真实应用日志 ──
    def get_logs(self, lines: int = 30, grep: str = "") -> str:
        t0 = time.time()
        if not LOG.exists():
            return self._rec("get_logs", {"lines": lines}, "（日志文件不存在）", t0)
        content = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        if grep:
            content = [x for x in content if re.search(grep, x, re.I)]
        sel = content[-lines:]
        return self._rec("get_logs", {"lines": lines, "grep": grep},
                         "\n".join(sel) or "（无匹配）", t0)

    # ── 真实变更台账（每次注入都会写）──
    def get_recent_changes(self) -> str:
        t0 = time.time()
        cl = SANDBOX_DIR / "changes.log"
        if not cl.exists():
            return self._rec("get_recent_changes", {}, "（无变更记录）", t0)
        lines = cl.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
        return self._rec("get_recent_changes", {}, "\n".join(lines), t0)

    # ── 只读命令（真实执行，白名单）──
    def run_readonly(self, cmd: str = "") -> str:
        t0 = time.time()
        if _BANNED.search(cmd or ""):
            return self._rec("run_readonly", {"cmd": cmd},
                             "拒绝：该命令不是只读操作", t0)
        allow = {
            "uptime": ["uptime"] if os.name != "nt" else ["powershell", "-NoProfile",
                                                           "-Command", "Get-Date"],
            "df": (["df", "-h"] if os.name != "nt" else
                   ["powershell", "-NoProfile", "-Command",
                    "Get-PSDrive | Format-Table -AutoSize | Out-String"]),
            "ps_top_cpu": (["ps", "aux", "--sort=-%cpu"] if os.name != "nt" else
                           ["powershell", "-NoProfile", "-Command",
                            "Get-Process | Sort-Object CPU -Descending | "
                            "Select-Object -First 10 | Format-Table -AutoSize | Out-String"]),
            "sandbox_state": None,
        }
        if cmd == "sandbox_state":
            body = STATE.read_text(encoding="utf-8") if STATE.exists() else "（无 state.json）"
            return self._rec("run_readonly", {"cmd": cmd}, body, t0)
        args = allow.get((cmd or "").strip().lower())
        if not args:
            return self._rec("run_readonly", {"cmd": cmd},
                             f"只支持：{list(allow)}", t0)
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=15)
            return self._rec("run_readonly", {"cmd": cmd},
                             (r.stdout or r.stderr)[:2500], t0)
        except Exception as e:
            return self._rec("run_readonly", {"cmd": cmd}, f"执行失败：{e}", t0)

    def submit_diagnosis(self, **kw) -> str:
        t0 = time.time()
        payload = json.dumps(kw, ensure_ascii=False)
        return self._rec("submit_diagnosis", {}, payload, t0)


TOOLS_DOC = """你可以调用以下只读工具（每次一个）：

1. get_service_health(port=8099)        —— 对服务做健康探测（真实 HTTP）
2. list_processes(sort_by="cpu")        —— 列出真实进程及 CPU/内存占用
3. get_disk_usage()                     —— 读真实临时目录占用与配额
4. check_config()                       —— 读真实配置文件并校验 JSON 合法性
5. get_logs(lines=30, grep="")          —— 读真实应用日志（grep 支持正则）
6. get_recent_changes()                 —— 读真实变更台账（谁在什么时候做了什么）
7. run_readonly(cmd="uptime|df|ps_top_cpu|sandbox_state")  —— 执行白名单只读命令
8. submit_diagnosis(root_cause="", chain=[...], confidence="high|medium|low",
                    evidence=[...], fix="", uncertain=[...])  —— 提交结论，结束排查
"""


def build_dyn_prompt(symptom: str, service: str, history: list[ToolCall],
                     max_steps: int) -> str:
    remain = max_steps - len(history)
    lines = [
        "你是值班 SRE，正在处理一起真实线上故障。系统是真的，工具读的是真实状态。",
        "你只能通过工具获取证据，不能凭猜测下结论。",
        "",
        f"【故障现象】{symptom}",
        f"【受影响服务】{service}",
        "",
        TOOLS_DOC,
        f"最多 {max_steps} 次工具调用，已用 {len(history)} 次，剩 {remain} 次。",
    ]
    if remain <= 2:
        lines.append(f"⚠️ 只剩 {remain} 次！有足够证据就立刻 submit_diagnosis，"
                     "用光步数不提交等于失败。")
    else:
        lines.append("按真实排查顺序：先确认现象，再看进程/资源/配置/日志，最后定位。")
    lines += ["", "输出严格 JSON（不要 markdown）：",
              '{"tool":"工具名","args":{...},"reasoning":"为什么要查这个"}']
    if history:
        lines += ["", "【已查到的证据】"]
        for i, h in enumerate(history, 1):
            r = h.result if len(h.result) <= 1500 else h.result[:1500] + "…[截断]"
            lines.append(f"--- 第 {i} 次 {h.tool}({json.dumps(h.args, ensure_ascii=False)}) ---")
            lines.append(r)
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# 故障注入（真实破坏，全部自动恢复）
# ══════════════════════════════════════════════════════════════
def start_service() -> subprocess.Popen:
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({"SANDBOX_DIR": str(SANDBOX_DIR), "SANDBOX_PORT": str(PORT),
                "TMP_QUOTA_MB": str(QUOTA_MB)})
    p = subprocess.Popen([sys.executable, str(SELFHEAL / "sandbox_app.py")],
                         cwd=str(SELFHEAL), env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    STATE.write_text(json.dumps({"app_script": str(SELFHEAL / "sandbox_app.py"),
                                 "service_pid": p.pid, "hog_pids": []}), encoding="utf-8")
    for _ in range(40):
        tb = RealToolbox()
        out = tb.get_service_health()
        if "200" in out:
            print(f"  沙箱服务就绪（PID {p.pid}）")
            return p
        time.sleep(0.5)
    raise RuntimeError("沙箱服务未能就绪")


def log_change(who: str, what: str) -> None:
    with open(SANDBOX_DIR / "changes.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {who}: {what}\n")


def _set_affinity(pid: int, cpu_index: int = 0) -> bool:
    """把进程绑定到指定单核。

    为什么需要：本机 32 核，起几个 hog 只占 25% 的核，健康检查的
    "抢占比"根本测不出来（实测 0.91×，阈值 1.35×）。
    把沙箱和 hog 都绑到同一个核上，抢占就必然发生——
    而且总负载只有 1 个核，不会把用户机器压死（安全优先）。
    """
    try:
        import ctypes
        PROCESS_SET_INFORMATION = 0x0200
        PROCESS_QUERY_INFORMATION = 0x0400
        k32 = ctypes.windll.kernel32 if os.name == "nt" else None
        if not k32:
            return False
        h = k32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION,
                            False, pid)
        if not h:
            return False
        ok = k32.SetProcessAffinityMask(h, 1 << cpu_index)
        k32.CloseHandle(h)
        return bool(ok)
    except Exception:
        return False


def inject_cpu_hog() -> str:
    # 关键：把沙箱绑到 CPU0，hog 也绑到 CPU0，形成必然抢占
    st = json.loads(STATE.read_text(encoding="utf-8"))
    svc_pid = int(st.get("service_pid", 0))
    bound = _set_affinity(svc_pid, 0) if svc_pid else False
    n = 3          # 3 个 hog 抢 1 个核，足够压垮，且机器总负载可忽略
    pids = []
    for _ in range(n):
        p = subprocess.Popen([sys.executable, "-c",
                              "import time;t=time.time()\nwhile time.time()-t<90: pass"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pids.append(p.pid)
        _set_affinity(p.pid, 0)
    st["hog_pids"] = pids
    STATE.write_text(json.dumps(st), encoding="utf-8")
    log_change("batch-team",
               f"启动 {n} 个批处理进程并绑定到同一 CPU 核（PID {pids}）")
    return (f"启动 {n} 个 CPU 密集型进程，与沙箱服务绑定同一核"
            f"（沙箱绑定{'成功' if bound else '失败'}）")


def inject_disk() -> str:
    chunk = b"\0" * (4 * 1024 * 1024)
    need, written, i = int(QUOTA_MB * 1.4), 0, 0
    while written < need:
        i += 1
        with open(TMP / f"balloon_{i}.dat", "wb") as fh:
            for _ in range(4):
                fh.write(chunk)
        written += 16
    log_change("etl-job", f"写入 {i} 个中间文件共 {written}MB 到临时目录")
    return f"向临时目录写入 {written}MB 临时文件"


def inject_config() -> str:
    good = CONFIG.read_text(encoding="utf-8")
    CONFIG.write_text(good[: len(good) // 2] + ',"mode":"MAINTENANCE-BAD"[[',
                      encoding="utf-8")
    log_change("ops-oncall", "手工编辑 config.json（未走变更单，未做语法检查）")
    return "把 config.json 改成非法 JSON"


def _run_text(args, timeout=15) -> str:
    """执行子进程并安全解码。

    Windows 上 netstat/tasklist 输出是本地代码页（GBK），
    直接 text=True 会抛 UnicodeDecodeError——那会让 PID 解析静默返回空，
    进而"杀掉服务"杀错对象（实测踩过：故障没发生却当成已发生）。
    """
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout)
        raw = r.stdout or r.stderr or b""
        for enc in ("utf-8", "gbk", "cp936", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")
    except Exception as exc:
        return f"__ERROR__:{exc}"


def _pids_listening_on(port: int) -> list[int]:
    """找出真正监听该端口的进程 PID（不依赖 state.json 的记录）。"""
    pids: list[int] = []
    if os.name == "nt":
        out = _run_text(["netstat", "-ano"])
        for line in out.splitlines():
            if f":{port} " in line and "LISTENING" in line.upper():
                parts = line.split()
                if parts and parts[-1].isdigit():
                    pids.append(int(parts[-1]))
    else:
        out = _run_text(["sh", "-c", f"lsof -ti tcp:{port} 2>/dev/null || "
                                     f"ss -lptn 'sport = :{port}'"])
        pids = [int(x) for x in re.findall(r"\b(\d{2,})\b", out)]
    return sorted(set(pids))


def inject_kill() -> str:
    # 以"真正在监听端口的进程"为准，不信任 state.json 里的历史 PID
    # （上一版测试踩过：state 记的进程早死了，杀它等于没杀，故障没发生却当成已发生）
    pids = _pids_listening_on(PORT)
    killed = []
    for pid in pids:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=10)
            else:
                os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except Exception:
            pass
    if not killed:
        # 兜底：按 state.json
        st = json.loads(STATE.read_text(encoding="utf-8"))
        pid = int(st.get("service_pid", 0))
        if pid:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=10)
                else:
                    os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            except Exception:
                pass
    log_change("oom-killer", f"服务进程被 OOM killer 终止（PID {killed}）")
    time.sleep(1.2)
    return f"终止监听 :{PORT} 的服务进程（PID {killed or '未找到'}）"


def cleanup() -> None:
    st = {}
    if STATE.exists():
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
    for pid in st.get("hog_pids", []):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(int(pid)), "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=8)
            except Exception:
                pass
    st["hog_pids"] = []
    if STATE.exists():
        STATE.write_text(json.dumps(st), encoding="utf-8")
    if TMP.exists():
        for p in TMP.glob("balloon_*.dat"):
            try:
                p.unlink()
            except OSError:
                pass
    if CONFIG_BAK.exists():
        shutil.copyfile(CONFIG_BAK, CONFIG)
    for extra in (str(CONFIG) + ".broken",):
        if os.path.exists(extra):
            try:
                os.remove(extra)
            except OSError:
                pass
    # 清空证据台账：否则上一个场景的变更会留在本场景的"真实证据"里，
    # 模型会把旧故障误当成本次根因（实测 D4 就混进了 D2/D3 的证据）。
    # 生产里这是"告警风暴后的残留噪声"，同样需要按时间窗口切分。
    changes_log = SANDBOX_DIR / "changes.log"
    if changes_log.exists():
        changes_log.write_text("", encoding="utf-8")
    app_log = SANDBOX_DIR / "app.log"
    if app_log.exists():
        app_log.write_text("", encoding="utf-8")


SCENARIOS = [
    {"id": "D1", "name": "CPU 被外部进程抢占",
     "inject": inject_cpu_hog,
     "symptom": "服务响应明显变慢，健康检查报 CPU 相关异常。不确定是什么原因。",
     # must：必须命中其中一个，才证明它真的定位到了这个原因
     "must": [r"批处理|batch|hog|抢(占|夺).{0,10}cpu|外部进程.{0,10}(抢占|占用)"],
     # forbid：如果把它归因为这些，说明判错了方向
     "forbid": [r"内存.{0,6}(不足|耗尽|oom)", r"磁盘.{0,6}(满|不足)"],
     "verify": "cpu_ratio_high",
     "truth": "隔壁团队的批处理进程占满了 CPU，导致服务被挤下 CPU"},
    {"id": "D2", "name": "临时目录被撑爆",
     "inject": inject_disk,
     "symptom": "服务健康检查失败，报临时目录相关异常。",
     "must": [r"临时目录|tempdir|balloon|etl.{0,10}文件|配额.{0,6}(超|不足)"],
     "forbid": [r"config\.json.{0,10}(非法|损坏)", r"进程.{0,6}(被杀|终止)"],
     "verify": "tempdir_over_quota",
     "truth": "ETL 任务往临时目录写了大量中间文件，超过配额"},
    {"id": "D3", "name": "配置被手工改坏",
     "inject": inject_config,
     "symptom": "服务突然不可用，健康检查失败，报配置相关异常。",
     "must": [r"config\.json|配置文件.{0,10}(非法|损坏|语法)", r"json.{0,10}(非法|解析|语法)"],
     "forbid": [r"进程.{0,6}(被杀|终止|oom)", r"临时目录.{0,10}(超|满)"],
     "verify": "config_invalid",
     "truth": "运维手工编辑 config.json 时写坏 JSON 语法"},
    {"id": "D4", "name": "服务进程被杀",
     "inject": inject_kill,
     "symptom": "服务完全不可用，连不上端口。",
     "must": [r"进程.{0,10}(被|已).{0,6}(杀|终止|退出|消失)|oom.?killer|端口.{0,6}不可达|进程.{0,6}不存在"],
     "forbid": [r"config\.json.{0,10}(非法|损坏)", r"临时目录.{0,6}(超|满)"],
     "verify": "process_dead",
     "truth": "服务进程被 OOM killer 杀掉"},
]


# ── 故障生效的独立验证（不信注入函数的自述）────────────────────
def verify_fault(kind: str) -> tuple[bool, str]:
    """用独立探针确认故障真的发生了。返回 (是否生效, 说明)。"""
    tb = RealToolbox()
    if kind == "cpu_ratio_high":
        out = tb.get_service_health()
        m = re.search(r"抢占比\s*([\d.]+)", out)
        if not m:
            return "200" not in out, "健康检查未体现 CPU 异常"
        ratio = float(m.group(1))
        return ratio > 1.35, f"抢占比 {ratio}×（阈值 1.35×）"
    if kind == "tempdir_over_quota":
        out = tb.get_disk_usage()
        m = re.search(r"实际占用\s*([\d.]+)MB", out)
        used = float(m.group(1)) if m else 0
        return used > QUOTA_MB, f"临时目录 {used}MB / 配额 {QUOTA_MB}MB"
    if kind == "config_invalid":
        out = tb.check_config()
        return "非法" in out, "配置 JSON 校验结果"
    if kind == "process_dead":
        # 必须"连不上"才算真死；HTTP 500 说明还有实例在响应（多实例 bug）
        out = tb.get_service_health()
        dead = "不可达" in out
        listeners = _pids_listening_on(PORT)
        return dead and not listeners, (
            f"{out.splitlines()[0] if out else ''}；剩余监听进程={listeners}")
    return True, "未定义验证"


def score(diag: dict | None, sc: dict) -> dict:
    """严格评分：必须命中 must 之一，且不能命中 forbid。

    为什么改严：第一版只按关键词命中数给分，
    D4 模型把"进程被杀"误判成"宿主机 CPU 抢占"，却因为文本里出现
    "进程/终止/OOM" 等词拿了 4/4——那是评分器的假阳性。
    """
    if not diag:
        return {"grade": 0, "why": "无结论", "must_hit": False, "forbid_hit": []}
    text = json.dumps(diag, ensure_ascii=False)
    must_hit = any(re.search(p, text, re.I) for p in sc["must"])
    forbid_hit = [p for p in sc.get("forbid", []) if re.search(p, text, re.I)]
    if forbid_hit:
        return {"grade": 0, "must_hit": must_hit, "forbid_hit": forbid_hit,
                "why": f"判错方向（命中禁忌：{forbid_hit[0]}）"}
    if not must_hit:
        return {"grade": 1, "must_hit": False, "forbid_hit": [],
                "why": "有结论但未定位到真实根因"}
    # 命中真实根因 → 再看推理链是否完整
    chain = diag.get("chain") or []
    ev = diag.get("evidence") or []
    depth = len([c for c in chain if isinstance(c, dict)]) + len(ev)
    grade = 4 if depth >= 3 else 3
    return {"grade": grade, "must_hit": True, "forbid_hit": [], "depth": depth,
            "why": f"根因正确，推理链 {depth} 条"}


def _kill_all_listeners(port: int) -> list[int]:
    """杀掉端口上的所有监听进程。

    必要：Windows 上 SO_REUSEADDR 允许多个进程同时绑同一端口，
    历史残留实例会让"杀掉服务"看起来没生效（还有另一个在响应）。
    """
    pids = _pids_listening_on(port)
    for pid in pids:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=10)
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    if pids:
        time.sleep(0.8)
    return pids


def ensure_service() -> None:
    """保证端口上只有一个健康的沙箱实例。"""
    # 先清掉所有残留监听者，再起一个干净的（避免多实例）
    leftover = _kill_all_listeners(PORT)
    if leftover:
        print(f"  清理残留监听进程：{leftover}")
    script = str(SELFHEAL / "sandbox_app.py")
    env = dict(os.environ)
    env.update({"SANDBOX_DIR": str(SANDBOX_DIR), "SANDBOX_PORT": str(PORT),
                "TMP_QUOTA_MB": str(QUOTA_MB)})
    p = subprocess.Popen([sys.executable, script], cwd=str(SELFHEAL), env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    st = {}
    if STATE.exists():
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
    st.update({"app_script": script, "service_pid": p.pid, "hog_pids": []})
    STATE.write_text(json.dumps(st), encoding="utf-8")
    tb = RealToolbox()
    for _ in range(40):
        if "200" in tb.get_service_health():
            print(f"  沙箱服务就绪（PID {p.pid}）")
            return
        time.sleep(0.5)
    print("  ⚠️ 沙箱服务未能就绪")


def run_scenario(sc: dict, llm, max_steps: int) -> dict:
    print(f"\n{'='*70}\n{sc['id']} {sc['name']}\n{'='*70}")
    ensure_service()
    tb = RealToolbox()
    detail = sc["inject"]()
    print(f"  注入：{detail}")
    time.sleep(2.0)
    # 独立验证故障是否真的发生（不信注入函数的自述）
    effective, vdetail = verify_fault(sc["verify"])
    print(f"  故障验证：{'✅ 生效' if effective else '❌ 未生效'} —— {vdetail}")
    out = tb.get_service_health()
    print(f"  服务健康：{out.splitlines()[0] if out else '?'}")

    if not effective:
        return {"id": sc["id"], "name": sc["name"], "inject": detail,
                "truth": sc["truth"], "fault_effective": False,
                "steps": 0, "tools": [], "diagnosis": None,
                "grade": 0, "why": f"故障未生效（{vdetail}），本场景不计分",
                "must_hit": False, "forbid_hit": []}

    step, final = 0, None
    while step < max_steps:
        prompt = build_dyn_prompt(sc["symptom"], "sandbox-app", tb.history, max_steps)
        raw = llm([{"role": "user", "content": prompt}])
        act = parse_action(raw)
        if not act:
            tb.history.append(ToolCall("_parse_error", {}, (raw or "")[:200], 0))
            step += 1
            continue
        tool, args = act.get("tool", ""), act.get("args") or {}
        print(f"  [{step+1}] {tool}({json.dumps(args, ensure_ascii=False)[:60]}) "
              f"— {act.get('reasoning','')[:60]}")
        if tool == "submit_diagnosis":
            tb.submit_diagnosis(**args)
            final = json.loads(tb.history[-1].result)
            break
        fn = getattr(tb, tool, None)
        if not callable(fn):
            tb.history.append(ToolCall("_bad_tool", {"tool": tool},
                                       f"没有这个工具：{tool}", 0))
            step += 1
            continue
        try:
            fn(**args)
        except TypeError as e:
            tb.history.append(ToolCall(tool, args, f"参数错误：{e}", 0))
        except Exception as e:
            tb.history.append(ToolCall(tool, args, f"工具异常：{e}", 0))
        step += 1

    sc_score = score(final, sc)
    print(f"  结论：{(final or {}).get('root_cause','（未提交）')[:110]}")
    print(f"  评分：{sc_score['grade']}/4 —— {sc_score['why']}")
    return {"id": sc["id"], "name": sc["name"], "inject": detail,
            "truth": sc["truth"], "fault_effective": True, "verify": vdetail,
            "steps": step,
            "tools": [h.tool for h in tb.history if not h.tool.startswith("_")],
            "diagnosis": final, **sc_score}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("LLM_API_KEY", ""))
    ap.add_argument("--base-url", default="https://api.deepseek.com/v1")
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY", ""))
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=str(HERE / "DYNAMIC-RESULTS.md"))
    args = ap.parse_args()
    if not args.api_key:
        print("缺少 --api-key")
        return 2

    from run_agentic import LLM  # 复用同一个 LLM 客户端
    llm = LLM(args.api_key, args.base_url, args.model, args.proxy)

    proc = start_service()
    results = []
    try:
        for sc in SCENARIOS:
            if args.only and args.only not in (sc["id"], sc["name"]):
                continue
            cleanup()          # 先清掉上个场景的残留证据，保证每个场景证据干净
            time.sleep(1.0)
            results.append(run_scenario(sc, llm, args.max_steps))
            cleanup()
            time.sleep(1.2)
    finally:
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except OSError:
            pass

    lines = ["# 动态环境实测：真实系统故障，模型自主排查", "",
             f"- 模型：`{args.model}`　时间：{time.strftime('%Y-%m-%d %H:%M')}",
             f"- 总调用：{llm.calls} 次 · tokens in/out = "
             f"{llm.prompt_tokens}/{llm.completion_tokens}", "",
             "**评分口径**：必须定位到真实根因（must 命中）+ 不能判错方向（forbid 不命中）。"
             "只数关键词的旧口径会把\"说对了几个词但方向错了\"算成正确——已废弃。", "",
             "## 结果", "",
             "| 场景 | 故障是否真发生 | 真实根因 | 模型结论 | 得分 | 工具数 |",
             "|---|---|---|---|---|---|"]
    for r in results:
        rc = (r.get("diagnosis") or {}).get("root_cause", "（未提交）")
        eff = "✅" if r.get("fault_effective") else "❌ 未生效"
        lines.append(f"| {r['id']} {r['name']} | {eff} | {r['truth']} | {rc[:70]} | "
                     f"**{r['grade']}/4** | {len(r['tools'])} |")
    scored = [r for r in results if r.get("fault_effective")]
    total = sum(r["grade"] for r in scored)
    lines += ["", f"**总分 {total}/{len(scored) * 4}**"
              f"（只统计故障真实生效的场景 {len(scored)}/{len(results)} 个）", ""]
    lines += ["## 逐场景详情", ""]
    for r in results:
        lines += [f"### {r['id']} {r['name']}", "",
                  f"- 注入：{r['inject']}",
                  f"- 真实根因：{r['truth']}",
                  f"- 故障验证：{r.get('verify','—')}",
                  f"- 工具调用链（{len(r['tools'])} 次）："
                  + " → ".join(r["tools"]),
                  f"- 得分：{r['grade']}/4（{r['why']}）"]
        d = r.get("diagnosis") or {}
        if d:
            lines.append(f"- 模型根因：{d.get('root_cause','')}")
            for c in (d.get("chain") or [])[:6]:
                if isinstance(c, dict):
                    lines.append(f"  - [{c.get('step','')}] {c.get('finding','')}")
        lines.append("")
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告：{args.out}")
    total = sum(r["grade"] for r in results)
    print(f"总分 {total}/{len(results) * 4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
