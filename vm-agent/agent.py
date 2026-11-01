#!/usr/bin/env python3
"""虚拟机探针（Guest 侧运行）：监听应用错误日志 → 上报 AIOps 后端 /api/ingest。

设计：零依赖（纯 stdlib），在虚拟机里 `python3 agent.py` 即可跑。
它只做「采集 + 上报」，研判/降噪/分流全部在后端完成——探针永远别变聪明。

配置（环境变量）：
  AIOPS_BACKEND   后端地址，默认 http://192.168.197.1:8600（宿主机 VMnet8 地址；
                   注意不是默认路由里的 .2，那是 NAT 网关虚拟 IP，连不到宿主机进程）
  AIOPS_SERVICE   本机服务名，默认 vm-app
  AIOPS_ENV       环境标识，默认 prod
  AIOPS_LOG_FILES 监听的文件（逗号分隔），默认 /var/log/demo-app.log
  AIOPS_THRESHOLD 窗口内错误行数阈值，默认 3
  AIOPS_WINDOW    统计窗口（秒），默认 10
  AIOPS_POLL      轮询间隔（秒），默认 2
  AIOPS_COOLDOWN  同一问题上报冷却（秒），默认 30

用法：
  python3 agent.py              # 常驻探针
  python3 agent.py --selftest   # 立刻上报一条合成错误，验证连通性
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from collections import deque

BACKEND = os.environ.get("AIOPS_BACKEND", "http://192.168.197.1:8600").rstrip("/")
SERVICE = os.environ.get("AIOPS_SERVICE", "vm-app")
ENV = os.environ.get("AIOPS_ENV", "prod")
LOG_FILES = [p.strip() for p in os.environ.get("AIOPS_LOG_FILES", "/var/log/demo-app.log").split(",") if p.strip()]
THRESHOLD = int(os.environ.get("AIOPS_THRESHOLD", "3"))
WINDOW = int(os.environ.get("AIOPS_WINDOW", "10"))
POLL = float(os.environ.get("AIOPS_POLL", "2"))
COOLDOWN = int(os.environ.get("AIOPS_COOLDOWN", "30"))

ERROR_MARKERS = ("ERROR", "FATAL", "CRITICAL", "Exception", "Traceback")

# 上报前是否采集节点侧排查证据（只读 kubectl/系统命令，见 investigate.sh）
INVESTIGATE = os.environ.get("AIOPS_INVESTIGATE", "1") == "1"
INVESTIGATE_SCRIPT = os.environ.get("AIOPS_INVESTIGATE_SCRIPT", "/tmp/investigate.sh")


def collect_investigation() -> str:
    """上报前跑一次只读排查脚本，把 K8s/系统证据带回去（容量截断到 4KB）。"""
    if not INVESTIGATE or not os.path.exists(INVESTIGATE_SCRIPT):
        return ""
    try:
        import subprocess
        r = subprocess.run(["/bin/sh", INVESTIGATE_SCRIPT], capture_output=True,
                           text=True, timeout=25)
        out = (r.stdout or "")[-4000:]
        return out if "INVESTIGATE_DONE" in out else out[-4000:]
    except Exception:
        return ""


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def report(events: list[dict]) -> bool:
    """上报一批错误事件到后端接入层（business_log 源）。"""
    body = json.dumps({
        "source": "business_log",
        "payload": {"events": events},
    }).encode()
    req = urllib.request.Request(
        f"{BACKEND}/api/ingest", data=body, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        admitted = len(data.get("admitted", []))
        stats = data.get("stats", {})
        log(f"上报 {len(events)} 条 → 后端放行 {admitted} 条"
            f"（累计降噪 {(stats.get('noise_reduction_ratio') or 0) * 100:.1f}%）")
        return True
    except Exception as exc:
        log(f"上报失败：{exc}（后端不可达？检查：① 宿主机防火墙是否放行 8600 入站 ② AIOPS_BACKEND 应为 http://192.168.197.1:8600 ③ 后端是否 --host 0.0.0.0）")
        return False


# 行首时间戳（剥掉后再派生 alertname，否则每条日志时间不同 → 指纹全不同 → 去重失效）
_TS_PREFIX = re.compile(
    r"^\s*\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s*")


def make_event(line: str, investigation: str = "") -> dict:
    # alertname 从错误内容派生（不含时间戳）：不同错误类型各占一个指纹，
    # 完全相同错误的重复才会被去重层合并（同一故障刷屏 ≠ 新故障）
    body = _TS_PREFIX.sub("", line.strip())
    head = body[:48]
    slug = "".join(c if (c.isalnum() or c in "._-") else "_" for c in head).strip("_") or "log_error"
    return {"level": "error", "event": f"log_{slug[:40]}", "message": line.strip()[:300],
            "service": SERVICE, "env": ENV, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "investigation": investigation}


def is_error(line: str) -> bool:
    return any(m in line for m in ERROR_MARKERS)


class Tailer:
    """极简 tail：记住 offset，只读新增部分。文件被轮换/不存在时自动重置。"""

    def __init__(self, path: str):
        self.path = path
        self.offset = 0

    def read_new(self) -> list[str]:
        try:
            size = os.path.getsize(self.path)
            if size < self.offset:      # 轮换/清空 → 从头读
                self.offset = 0
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self.offset)
                lines = f.readlines()
                self.offset = f.tell()
            return lines
        except FileNotFoundError:
            return []
        except Exception as exc:
            log(f"读取 {self.path} 失败：{exc}")
            return []


def main() -> None:
    if "--selftest" in sys.argv:
        log(f"连通性自检 → {BACKEND}")
        ok = report([make_event("SELFTEST vm-agent connectivity probe from " + SERVICE)])
        sys.exit(0 if ok else 1)

    missing = [p for p in LOG_FILES if not os.path.exists(p)]
    if missing:
        log(f"提示：这些监听文件暂不存在（等它被创建即可）：{missing}")
    log(f"探针启动：backend={BACKEND} service={SERVICE} logs={LOG_FILES} "
        f"阈值={THRESHOLD}条/{WINDOW}s 冷却={COOLDOWN}s")

    tailers = {p: Tailer(p) for p in LOG_FILES}
    recent: deque[tuple[float, str]] = deque()   # (ts, line) 窗口内的错误行
    last_report = 0.0

    while True:
        now = time.time()
        for path, t in tailers.items():
            for line in t.read_new():
                if is_error(line):
                    recent.append((now, line))
        while recent and now - recent[0][0] > WINDOW:
            recent.popleft()

        if len(recent) >= THRESHOLD and now - last_report >= COOLDOWN:
            evidence = collect_investigation()
            events = [make_event(l, evidence) for _, l in list(recent)[:5]]
            if report(events):
                last_report = now
                recent.clear()
        time.sleep(POLL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("探针停止")
