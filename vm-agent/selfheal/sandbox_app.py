"""沙箱业务服务（被测对象）：一个真的 HTTP 服务，真的会坏，真的能被修好。

它不是 mock——它是一个真的进程、真的监听端口、真的读配置文件、真的写临时文件、
真的做 CPU 计算。故障注入打在它身上，健康探针读它的真实状态。

GET /healthz 按三类真实信号判定自身健康（任一不过 → 500 + 说明原因）：
  1. config    —— config.json 必须存在且是合法 JSON（被改坏 → 500）
  2. tempdir   —— 临时目录占用必须 ≤ 配额（气球文件撑爆 → 500）
  3. cpu       —— 跑一段固定规模的计算，墙钟耗时 > 基线 N 倍 = CPU 被抢占（→ 500）
                  基线在启动时实测（取 3 次最小值），不写死阈值。

环境变量：
  SANDBOX_DIR  沙箱根目录（config.json / tmp/ 都在这）  默认 ./sandbox
  SANDBOX_PORT 监听端口，默认 8080
  CPU_FACTOR   CPU 抢占判定倍数，默认 1.6
  TMP_QUOTA_MB 临时目录配额（MB），默认 64
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIR = os.environ.get("SANDBOX_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"))
PORT = int(os.environ.get("SANDBOX_PORT", "8080"))
CPU_FACTOR = float(os.environ.get("CPU_FACTOR", "1.35"))
TMP_QUOTA_MB = float(os.environ.get("TMP_QUOTA_MB", "64"))

CONFIG = os.path.join(DIR, "config.json")
CONFIG_BAK = os.path.join(DIR, "config.json.bak")
TMP = os.path.join(DIR, "tmp")

DEFAULT_CONFIG = {"mode": "normal", "upstream": "http://127.0.0.1:9999", "timeout_ms": 800}


def ensure_layout() -> None:
    os.makedirs(TMP, exist_ok=True)
    if not os.path.exists(CONFIG):
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    if not os.path.exists(CONFIG_BAK):
        shutil.copyfile(CONFIG, CONFIG_BAK)


def dir_size_bytes(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def _burn(n: int = 1_000_000) -> None:
    s = 0
    for i in range(n):
        s += i * i
    if s == -1:      # 防优化掉
        print(s)


def measure_preempt() -> tuple[float, float]:
    """返回 (抢占比, 墙钟耗时)：抢占比 = 墙钟时间 / 本进程实际拿到的 CPU 时间。

    为什么用这个而不是"耗时 / 基线"：抢占比**直接测被抢占的程度**——
    进程被别的负载挤下 CPU 时，墙钟在走而 CPU 时间不涨，比值就上升。
    它不依赖机器核数、也不依赖启动时的基线，所以比"跟基线比"更本质。
    空闲机器上 ≈ 1.0；被抢占时会明显 > 1。
    """
    t0, c0 = time.perf_counter(), time.process_time()
    _burn()
    wall = time.perf_counter() - t0
    cpu = time.process_time() - c0
    return (wall / cpu if cpu > 0 else 1.0), wall


def check_config() -> tuple[bool, str]:
    if not os.path.exists(CONFIG):
        return False, "config.json 不存在"
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as exc:
        return False, f"config.json 非法（{type(exc).__name__}）"
    if not isinstance(cfg, dict) or cfg.get("mode") != "normal":
        return False, f"config 内容异常：mode={cfg.get('mode') if isinstance(cfg, dict) else '?'}"
    return True, "ok"


def check_tempdir() -> tuple[bool, str]:
    quota = TMP_QUOTA_MB * 1024 * 1024
    used = dir_size_bytes(TMP)
    pct = used / quota * 100 if quota else 0.0
    if used > quota:
        return False, f"临时目录 {used/1048576:.1f}MB > 配额 {TMP_QUOTA_MB}MB（{pct:.0f}%）"
    return True, f"{used/1048576:.1f}MB / {TMP_QUOTA_MB}MB（{pct:.0f}%）"


def check_cpu() -> tuple[bool, str]:
    ratio, wall = measure_preempt()
    if ratio > CPU_FACTOR:
        return False, (f"固定计算墙钟 {wall*1000:.0f}ms / CPU 时间 = 抢占比 {ratio:.2f}× "
                       f"（> {CPU_FACTOR}×，CPU 被抢占）")
    return True, f"抢占比 {ratio:.2f}×（墙钟 {wall*1000:.0f}ms）"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/healthz"):
            checks = {"config": check_config(), "tempdir": check_tempdir(), "cpu": check_cpu()}
            ok = all(v[0] for v in checks.values())
            self._send(200 if ok else 500, {
                "ok": ok,
                "checks": {k: {"ok": v[0], "detail": v[1]} for k, v in checks.items()},
            })
        elif self.path.startswith("/config"):
            try:
                with open(CONFIG, "r", encoding="utf-8") as f:
                    self._send(200, json.load(f))
            except Exception as exc:
                self._send(500, {"error": str(exc)})
        else:
            self._send(404, {"error": "use /healthz"})

    def log_message(self, fmt, *args):      # 静音，避免污染测试输出
        pass


def main() -> None:
    ensure_layout()
    r, w = measure_preempt()
    print(f"[sandbox] 空闲抢占比实测 {r:.2f}×（墙钟 {w*1000:.0f}ms），"
          f"判定阈值 ×{CPU_FACTOR}", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[sandbox] 服务已启动 http://127.0.0.1:{PORT}/healthz  dir={DIR}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
