#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VM 故障探针 / 上报器 —— 跑在你的虚拟机（guest）里。

作用：周期性采样本机健康度（磁盘 / CPU / 内存 / 关键进程 / 端口连通性），
一旦发现异常，就把一条「标准 Alertmanager 格式」的告警 POST 给宿主机的
AIOps 后端（默认 http://<宿主IP>:8600/api/ingest）。后端会按真实链路跑：
  归一化 → 去重 → 门控 → 分级(P0-P3) → 研判主链路(RCA) → 护栏 → dry-run 计划 → 审批中心
于是你在浏览器打开 8600 的 /dashboard，就能看到「告警流入 → 诊断报告 → 修复计划 → 待审批」。

设计要点：
  - 纯标准库，Linux guest 直接 `python3 vm_probe.py` 就能跑，零依赖。
  - 只读采样，不破坏任何东西；真正的故障由「你手动执行 break 命令」制造。
  - 也支持 --simulate 模式：不真破坏，只发一条贴好标签的告警，方便先跑通链路。

快速开始（在虚拟机里）：
  # 1) 找到能访问宿主后端 IP（VMware NAT 下通常是 default 网关）
  ip route | grep default        # 记下 gateway，比如 192.168.×.1
  # 2) 跑探针（默认每 30s 采样一次，挂在后台）
  python3 vm_probe.py --host 192.168.×.1 --port 8600 \
      --services nginx,redis,mysql \
      --endpoints 127.0.0.1:5432:postgres,127.0.0.1:6379:redis
  # 3) 另开一个终端，制造故障（见 VM-FAULT-LAB.md），回 dashboard 看结果
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

# ── 可调阈值（命令行可覆盖）────────────────────────────
DEFAULT_DISK_PATH = "/"
DEFAULT_DISK_PCT = 85          # 磁盘使用率超此值 → DiskPressure
DEFAULT_LOAD_FACTOR = 0.8       # loadavg(1min) / nproc 超此值 → CPUThrottling
DEFAULT_MEM_FREE_MB = 300       # 可用内存低于此值(MB) → MemoryPressure
COOLDOWN = 240                  # 同一故障最多每 240s 重发一次（后端去重窗 300s）

STATE = {}                      # (alertname, instance) -> last_emit_ts


# ── 采样函数（只读）──────────────────────────────────
def disk_usage(path: str) -> tuple[float, str]:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        pct = (1 - free / total) * 100 if total else 0.0
        return pct, f"df: {path} 使用率 {pct:.1f}%"
    except Exception as e:  # noqa
        return 0.0, f"df 读取失败: {e}"


def load_factor() -> tuple[float, str]:
    try:
        load1, _, _ = os.getloadavg()
        nproc = os.cpu_count() or 1
        f = load1 / nproc
        return f, f"loadavg(1m)={load1:.2f} nproc={nproc} 比值={f:.2f}"
    except Exception as e:  # noqa
        return 0.0, f"loadavg 读取失败: {e}"


def mem_free_mb() -> tuple[float, str]:
    try:
        free_kb = 0.0
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    free_kb = float(line.split()[1])
                    break
        mb = free_kb / 1024.0
        return mb, f"/proc/meminfo MemAvailable={mb:.0f}MB"
    except Exception as e:  # noqa
        return 1e9, f"meminfo 读取失败: {e}"


def service_active(svc: str) -> tuple[bool, str]:
    """返回 (是否存活, 证据)。优先 systemd，回退 pgrep。"""
    try:
        r = subprocess.run(["systemctl", "is-active", svc],
                           capture_output=True, text=True, timeout=5)
        active = r.stdout.strip() == "active"
        return active, f"systemctl is-active {svc} -> {r.stdout.strip()}"
    except Exception:  # noqa
        try:
            r = subprocess.run(["pgrep", "-f", svc],
                               capture_output=True, text=True, timeout=5)
            active = bool(r.stdout.strip())
            return active, f"pgrep -f {svc} -> {'存活' if active else '未找到进程'}"
        except Exception as e:  # noqa
            return True, f"无法探测 {svc}: {e}"


def endpoint_reachable(host: str, port: int, timeout: int = 3) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"tcp {host}:{port} 连通"
    except Exception as e:  # noqa
        return False, f"tcp {host}:{port} 不可达: {e}"


# ── 上报 ─────────────────────────────────────────────
def post_alert(host: str, port: int, alerts: list[dict]) -> bool:
    url = f"http://{host}:{port}/api/ingest"
    body = json.dumps({"source": "alertmanager",
                       "payload": {"alerts": alerts}}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        adm = len(data.get("admitted", []))
        stats = data.get("stats", {})
        dropped = (stats.get("dropped_dedup", 0) + stats.get("dropped_gate", 0))
        print(f"  -> 上报 {len(alerts)} 条 → 后端放行 {adm}，拦截 {dropped}", flush=True)
        return True
    except Exception as e:  # noqa
        print(f"  -> 上报失败: {e}", flush=True)
        return False


def make_alert(alertname: str, severity: str, service: str, host_label: str,
              summary: str, description: str) -> dict:
    """构造一条 alertmanager 格式告警（env=prod，severity+critical+core 服务 → 进研判）。"""
    return {
        "labels": {
            "alertname": alertname,
            "severity": severity,
            "env": "prod",
            "service": service,
            "host": host_label,
            "instance": host_label,
            "affects_prod": "true",
        },
        "annotations": {"summary": summary, "description": description},
    }


def maybe_emit(key: str, alert: dict | None, host: str, port: int) -> None:
    now = time.time()
    if alert is None:
        STATE.pop(key, None)      # 故障恢复 → 重置去重计时
        return
    last = STATE.get(key, 0)
    if now - last < COOLDOWN:
        return                    # 冷却期内不重发（交给后端去重兜底）
    STATE[key] = now
    post_alert(host, port, [alert])


# ── 主循环 ───────────────────────────────────────────
def collect(host_label: str, disk_path: str, disk_pct: float, load_factor_th: float,
            mem_free_th: float, services: list[str], endpoints: list[tuple]) -> list[tuple]:
    out: list[tuple] = []

    pct, ev = disk_usage(disk_path)
    if pct >= disk_pct:
        out.append(("DiskPressure", make_alert(
            "DiskPressure", "critical", "node", host_label,
            f"磁盘使用率 {pct:.1f}% 超阈值 {disk_pct}%",
            f"{ev}；建议清理大文件/日志或扩容。")))
    else:
        out.append(("DiskPressure", None))

    f, ev = load_factor()
    if f >= load_factor_th:
        out.append(("CPUThrottling", make_alert(
            "CPUThrottling", "critical", "node", host_label,
            f"CPU 饱和 比值 {f:.2f} 超阈值 {load_factor_th}",
            f"{ev}；定位高 CPU 进程并限流/重启。")))
    else:
        out.append(("CPUThrottling", None))

    mb, ev = mem_free_mb()
    if mb <= mem_free_th:
        out.append(("MemoryPressure", make_alert(
            "MemoryPressure", "critical", "node", host_label,
            f"可用内存 {mb:.0f}MB 低于阈值 {mem_free_th}MB，OOM 风险",
            f"{ev}；释放内存或扩容。")))
    else:
        out.append(("MemoryPressure", None))

    for svc in services:
        active, ev = service_active(svc)
        if not active:
            out.append((f"SvcDown:{svc}", make_alert(
                "ServiceDown", "critical", svc, host_label,
                f"关键服务 {svc} 不可用（影响核心链路）",
                f"{ev}；检查进程崩溃/配置/依赖，重启服务。")))
        else:
            out.append((f"SvcDown:{svc}", None))

    for (h, p, label) in endpoints:
        ok, ev = endpoint_reachable(h, p)
        if not ok:
            out.append((f"NetUnreach:{label}", make_alert(
                "NetworkPartition", "critical", label, host_label,
                f"依赖 {label}({h}:{p}) 不可达，下游交易受影响",
                f"{ev}；排查网络/防火墙/对端服务状态。")))
        else:
            out.append((f"NetUnreach:{label}", None))

    return out


SIM_PRESETS = {
    "disk": ("DiskPressure", "critical", "node", "磁盘使用率 92% 超阈值 85%", "df: / 使用率 92%"),
    "cpu": ("CPUThrottling", "critical", "node", "CPU 饱和 比值 1.2", "loadavg(1m)=4.8 nproc=4"),
    "mem": ("MemoryPressure", "critical", "node", "可用内存 120MB OOM 风险", "MemAvailable=120MB"),
    "svc": ("ServiceDown", "critical", "api", "关键服务 api 不可用 影响下单", "systemctl is-active api -> inactive"),
    "net": ("NetworkPartition", "critical", "postgres", "依赖 postgres 不可达 支付受影响", "tcp 127.0.0.1:5432 不可达"),
}


def main() -> None:
    ap = argparse.ArgumentParser(description="VM 故障探针 / 上报器")
    ap.add_argument("--host", default="127.0.0.1", help="宿主机 AIOps 后端 IP")
    ap.add_argument("--port", type=int, default=8600)
    ap.add_argument("--interval", type=int, default=30, help="采样间隔(秒)")
    ap.add_argument("--once", action="store_true", help="只采样一次并退出")
    ap.add_argument("--disk-path", default=DEFAULT_DISK_PATH)
    ap.add_argument("--disk-pct", type=float, default=DEFAULT_DISK_PCT)
    ap.add_argument("--load-factor", type=float, default=DEFAULT_LOAD_FACTOR)
    ap.add_argument("--mem-free", type=float, default=DEFAULT_MEM_FREE_MB)
    ap.add_argument("--services", default="", help="逗号分隔的受监控服务名")
    ap.add_argument("--endpoints", default="", help="逗号分隔的 host:port:label")
    ap.add_argument("--simulate", choices=list(SIM_PRESETS.keys()),
                    help="只发一条模拟告警，不真破坏（安全演示）")
    args = ap.parse_args()

    host_label = socket.gethostname()
    services = [s.strip() for s in args.services.split(",") if s.strip()]
    endpoints = []
    for e in args.endpoints.split(","):
        e = e.strip()
        if not e:
            continue
        parts = e.rsplit(":", 2)
        if len(parts) == 3:
            endpoints.append((parts[0], int(parts[1]), parts[2]))

    if args.simulate:
        name, sev, svc, summ, desc = SIM_PRESETS[args.simulate]
        post_alert(args.host, args.port,
                   [make_alert(name, sev, svc, host_label, summ, desc)])
        return

    print(f"[vm_probe] 目标后端 {args.host}:{args.port}  host={host_label}  "
          f"监控服务={services} 端点={[e[2] for e in endpoints]}  间隔={args.interval}s",
          flush=True)
    if args.once:
        for key, alert in collect(host_label, args.disk_path, args.disk_pct,
                                  args.load_factor, args.mem_free, services, endpoints):
            print(f"  {key}: {'FAULT' if alert else 'ok'}")
            if alert:
                post_alert(args.host, args.port, [alert])
        return

    while True:
        try:
            for key, alert in collect(host_label, args.disk_path, args.disk_pct,
                                      args.load_factor, args.mem_free, services, endpoints):
                if alert:
                    print(f"[fault] {key}", flush=True)
                    maybe_emit(key, alert, args.host, args.port)
                else:
                    maybe_emit(key, None, args.host, args.port)  # 恢复则清计时
        except Exception as e:  # noqa
            print(f"[probe error] {e}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
