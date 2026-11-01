"""节点侧修复 agent（双端白名单的"节点这一份"）。

后端只对登记动作下单；**本 agent 自己还持有一份白名单**——不认识的
action_id 一律拒绝执行。这是纵深防御：后端被注入伪造订单，节点这边也执行不了。

职责：拉单 → 只执行白名单内动作 → 跑验证探针 → 把结果回报后端。
agent 不做诊断、不发明命令——它只会做登记表里写死的几件事。

用法：
  python executor.py --once      # 拉一次单（测试/CI 用）
  python executor.py --loop      # 常驻轮询（生产形态）
环境变量：
  AIOPS_BACKEND    后端地址（默认 http://127.0.0.1:8600）
  AIOPS_SERVICE    本节点服务名（拉单按 service 过滤）
  SANDBOX_DIR      沙箱根目录（默认 ./sandbox）
  SANDBOX_PORT     服务端口（默认 8080）
  SANDBOX_STATE    state.json 路径（默认 <SANDBOX_DIR>/state.json）
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
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = os.environ.get("AIOPS_BACKEND", "http://127.0.0.1:8600").rstrip("/")
SERVICE = os.environ.get("AIOPS_SERVICE", "sandbox-payment")
# 与后端共享的接口鉴权 token（后端设 AIOPS_API_TOKEN 后必须带）
API_TOKEN = os.environ.get("AIOPS_API_TOKEN", "")
HERE = Path(__file__).resolve().parent
DIR = Path(os.environ.get("SANDBOX_DIR", HERE / "sandbox"))
PORT = int(os.environ.get("SANDBOX_PORT", "8080"))
STATE = Path(os.environ.get("SANDBOX_STATE", DIR / "state.json"))
POLL = float(os.environ.get("AIOPS_AGENT_POLL", "2"))

# ── 节点侧白名单（这份与后端登记表独立维护，故意不共享代码） ──
# value = 本机实现函数名
ALLOWED: dict[str, str] = {
    "kill_noisy_neighbor": "_kill_noisy_neighbor",
    "cleanup_temp_files": "_cleanup_temp_files",
    "restore_config_from_backup": "_restore_config",
    "restart_service": "_restart_service",
    "rollback_version": "_restore_config",      # 沙箱内"版本"= 配置文件
    # scale_replicas 故意不在：本节点没有副本概念，做不到就不许做
}

CONFIG = DIR / "config.json"
CONFIG_BAK = DIR / "config.json.bak"
TMP = DIR / "tmp"


def log(msg: str) -> None:
    print(f"[agent {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _terminate(pid: int) -> bool:
    """跨平台终止进程：Windows 上没有 signal.SIGKILL，只能 SIGTERM + taskkill 兜底。"""
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        pass
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            return True
        except Exception:
            return False
    return False


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["X-AIOps-Token"] = API_TOKEN
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ── 动作实现（每个都是真的操作：真杀进程 / 真删文件 / 真拉起服务） ──
def _kill_noisy_neighbor(order: dict) -> tuple[bool, str]:
    """终止失控的吵闹邻居进程（生产对应动作：给它设 CPU Limit，不杀它）。"""
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    pids = [int(p) for p in state.get("hog_pids", [])]
    if not pids:
        return False, "state.json 里没有记录任何吵闹邻居 PID（拒绝盲杀）"
    killed = []
    for pid in pids:
        if _terminate(pid):
            killed.append(pid)
    return bool(killed), f"已终止 PID {killed}（共 {len(pids)} 个记录）"


def _cleanup_temp_files(order: dict) -> tuple[bool, str]:
    """删除/截断本服务自己产生的临时文件（只动白名单路径，绝不动业务数据）。"""
    if not TMP.exists():
        return False, f"临时目录不存在：{TMP}"
    # 路径护栏：只允许清理这些模式，且必须真的在 tmp 目录里
    patterns = ("balloon_", ".tmp", ".log.", "core.", "cache_")
    removed, bytes_freed = [], 0
    for p in sorted(TMP.iterdir()):
        if not p.is_file():
            continue
        if not any(p.name.startswith(pat) or pat in p.name for pat in patterns):
            continue
        real = p.resolve()
        if TMP.resolve() not in real.parents:      # 符号链接逃逸防护
            continue
        try:
            size = p.stat().st_size
            p.unlink()
            removed.append(p.name)
            bytes_freed += size
        except OSError as exc:
            log(f"删除失败 {p.name}：{exc}")
    return bool(removed), f"删除 {len(removed)} 个临时文件，释放 {bytes_freed/1048576:.1f}MB：{removed[:5]}"


def _restore_config(order: dict) -> tuple[bool, str]:
    """从本服务自己的配置备份恢复（先把当前坏配置另存为 .broken，所以可逆）。"""
    if not CONFIG_BAK.exists():
        return False, f"没有配置备份：{CONFIG_BAK}"
    if CONFIG.exists():
        shutil.copyfile(CONFIG, str(CONFIG) + ".broken")
    shutil.copyfile(CONFIG_BAK, CONFIG)
    return True, "已从 config.json.bak 恢复配置（原坏配置另存为 config.json.broken）"


def _restart_service(order: dict) -> tuple[bool, str]:
    """重启本节点自有服务进程（拉起 sandbox_app.py）。"""
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    app = state.get("app_script") or str(HERE / "sandbox_app.py")
    env = dict(os.environ)
    env["SANDBOX_DIR"] = str(DIR)
    env["SANDBOX_PORT"] = str(PORT)
    # 先看看是不是还活着（活着就先停干净，避免端口占用）
    pid = state.get("service_pid")
    if pid:
        _terminate(int(pid))
        time.sleep(0.8)
    try:
        proc = subprocess.Popen([sys.executable, app], cwd=str(HERE), env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        state["service_pid"] = proc.pid
        STATE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        return True, f"已重新拉起服务（PID {proc.pid}）"
    except Exception as exc:
        return False, f"拉起失败：{exc}"


# ── 验证探针（真探针：真发 HTTP、真量目录、真查进程） ──
_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def http_probe() -> tuple[bool, str]:
    """健康探针：200 = 健康；500 = 服务在但自检不过（body 里带着哪一项不过）。

    用无代理 opener：本机配了 http_proxy，走代理会让"进程已死"看起来像 502，
    把"连不上"误报成"服务返回了错误"。
    """
    try:
        with _NO_PROXY_OPENER.open(f"http://127.0.0.1:{PORT}/healthz", timeout=5) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:          # 500 也是"服务在"，要读 body 看原因
        try:
            body = json.loads(exc.read().decode())
        except Exception:
            return False, f"healthz HTTP {exc.code}（无 body）"
        return False, f"healthz HTTP {exc.code} —— {_fmt_checks(body)}"
    except Exception as exc:
        return False, f"healthz 不可达（进程已死？）：{type(exc).__name__}"
    return bool(body.get("ok")), (f"healthz 200 —— {_fmt_checks(body)}" if body.get("ok")
                                  else f"healthz 200 但自检不过 —— {_fmt_checks(body)}")


def _fmt_checks(body: dict) -> str:
    return "; ".join(f"{k}={'ok' if v['ok'] else v['detail']}"
                     for k, v in (body.get("checks") or {}).items())


def process_gone() -> tuple[bool, str]:
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    pids = [int(p) for p in state.get("hog_pids", [])]
    if not pids:
        return False, "state.json 无 hog_pids，无法验证"
    # Windows 的 os.kill(pid, 0) 对已退出进程也返回成功（僵尸进程对象仍在），
    # 不能用来判活。改用 OpenProcess 查询句柄：拿不到句柄才算真死了。
    alive = []
    for pid in pids:
        if os.name == "nt":
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
            if not h:
                continue                      # 拿不到句柄 = 进程已不存在
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            if ok and code.value == 259:      # STILL_ACTIVE
                alive.append(pid)
        else:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except OSError:
                pass
    return not alive, (f"PID {pids} 全部已终止" if not alive else f"仍存活：{alive}")


def disk_below_pct(threshold: float = 90) -> tuple[bool, str]:
    quota_mb = float(os.environ.get("TMP_QUOTA_MB", "64"))
    used = 0
    for p in TMP.rglob("*") if TMP.exists() else []:
        if p.is_file():
            try:
                used += p.stat().st_size
            except OSError:
                pass
    pct = used / (quota_mb * 1048576) * 100
    return pct < threshold, f"临时目录 {used/1048576:.1f}MB = 配额 {pct:.0f}%（阈值 {threshold}%）"


VERIFIERS = {
    "http_probe": lambda: http_probe(),
    "process_gone": lambda: process_gone(),
    "disk_below_pct": lambda: disk_below_pct(90),
}
# 登记表里的 verify_type → 本地探针（与后端登记表独立维护）
VERIFY_BY_ACTION = {
    "kill_noisy_neighbor": "process_gone",
    "cleanup_temp_files": "disk_below_pct",
    "restore_config_from_backup": "http_probe",
    "restart_service": "http_probe",
    "rollback_version": "http_probe",
}


def execute(order: dict) -> tuple[bool, str]:
    aid = order["action_id"]
    if aid not in ALLOWED:
        return False, f"拒绝执行：{aid} 不在本节点白名单内（allowed={sorted(ALLOWED)}）"
    fn = globals()[ALLOWED[aid]]
    try:
        return fn(order)
    except Exception as exc:
        return False, f"执行异常：{type(exc).__name__}: {exc}"


def verify(order: dict) -> dict:
    """执行后探针：HTTP 类动作需要给服务一点恢复时间（轮询最多 12s）。"""
    vtype = VERIFY_BY_ACTION.get(order["action_id"], "http_probe")
    fn = VERIFIERS.get(vtype, http_probe)
    deadline = time.time() + 12
    while True:
        ok, detail = fn()
        if ok or time.time() > deadline:
            return {"ok": ok, "type": vtype, "detail": detail}
        time.sleep(1.5)


def run_once(service: str = SERVICE, only_ids: list[str] | None = None) -> list[dict]:
    """拉单 → 执行 → 验证 → 回报。返回本次处理结果列表。

    only_ids：只处理这些订单（实测时用来精确对应"这一次诊断下的单"，
    避免历史遗留的 pending 订单混进结果——真实常驻 agent 不需要这个参数）。
    """
    try:
        data = http_json("GET", f"{BACKEND}/api/remediation/orders?service={service}")
    except Exception as exc:
        log(f"拉单失败：{exc}")
        return []
    results = []
    for order in data.get("items", []):
        if only_ids is not None and order["id"] not in only_ids:
            continue
        # 双端校验第二段：只执行自己服务的订单。后端已按 service 过滤，
        # 但订单表/接口配置出错时这里必须再拦一次（纵深防御，不靠单一防线）。
        if order.get("service") and service and order["service"] != service:
            log(f"拒绝订单 {order['id']}：service={order['service']} 不属于本节点 {service}")
            continue
        oid, aid = order["id"], order["action_id"]
        log(f"收到订单 {oid} · {aid} · 理由：{order.get('reason', '')[:60]}")
        exec_ok, exec_detail = execute(order)
        log(f"  执行：{'成功' if exec_ok else '失败'} —— {exec_detail[:100]}")
        v = verify(order) if exec_ok else {"ok": False, "type": "skipped",
                                           "detail": "执行失败，跳过验证"}
        log(f"  验证：{'通过' if v['ok'] else '未通过'} —— {v['detail'][:100]}")
        try:
            res = http_json("POST", f"{BACKEND}/api/remediation/complete",
                            {"order_id": oid, "exec_ok": exec_ok, "verify": v,
                             "exec_detail": exec_detail, "service": service})
            log(f"  回报 → 引擎判定 {res.get('status')}"
                + (f"（已自动回滚 {res.get('rollback_order')}）" if res.get("rollback") else ""))
        except Exception as exc:
            res = {"error": str(exc)}
            log(f"  回报失败：{exc}")
        results.append({"order": oid, "action": aid, "exec_ok": exec_ok,
                        "exec_detail": exec_detail, "verify": v, "engine": res})
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="只跑一轮")
    ap.add_argument("--loop", action="store_true", help="常驻轮询")
    ap.add_argument("--service", default=SERVICE)
    args = ap.parse_args()
    if not (args.once or args.loop):
        args.once = True
    log(f"节点 agent 启动 backend={BACKEND} service={args.service} "
        f"白名单={sorted(ALLOWED)}")
    while True:
        run_once(args.service)
        if args.once:
            return
        time.sleep(POLL)


if __name__ == "__main__":
    main()
