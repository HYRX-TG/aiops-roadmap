#!/usr/bin/env python3
"""Demo Payment API —— 模拟「真实生产服务」的健康检查行为。

关键设计（为什么不用 return b"ok" 的假服务）：
  真实服务的 /healthz 不是常量时间的——它会真的做上游探测、序列化、校验。
  只有健康检查有真实开销，CPU 抢占/内存压力才会体现为**可观测的延迟**，
  排障链路（看门狗→错误日志→探针→研判）才有真实数据可看。

/healthz 返回 JSON，含各环节耗时分解：
  {"status":"ok","total_ms":4.2,"upstream":{...},"work_ms":3.1}
  status=degraded 时仍返回 200（真实服务做法： unhealthy 由调用方判断），
  但 upstream.ok=false 会写进 error 日志——这就是排障的入口。
"""
import http.server
import socketserver
import json
import socket
import time
import hashlib
import os

CFG_PATH = os.environ.get("PAYMENT_API_CONFIG", "/etc/payment-api/config")


def load_config() -> dict:
    cfg = {"listen": "127.0.0.1:8080", "upstream": "dep-payment",
           "timeout_ms": 3000}
    try:
        with open(CFG_PATH) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    except Exception:
        pass
    return cfg


CFG = load_config()
HOST, PORT = CFG["listen"].rsplit(":", 1)


def check_upstream() -> dict:
    """探测配置里的 upstream（模拟依赖健康检查，带真实超时）。"""
    name = CFG["upstream"]
    t0 = time.time()
    try:
        # upstream 是服务名而非 host:port 时，用 127.0.0.1:8081 模拟（演示用）
        if ":" in name:
            h, p = name.rsplit(":", 1)
            p = int(p)
        else:
            h, p = "127.0.0.1", 8081
        try:
            timeout_s = float(CFG["timeout_ms"]) / 1000.0
        except (TypeError, ValueError):
            timeout_s = 3.0
        s = socket.create_connection((h, p), timeout=timeout_s)
        s.close()
        return {"upstream": name, "ok": True,
                "ms": round((time.time() - t0) * 1000, 1)}
    except Exception as exc:
        return {"upstream": name, "ok": False,
                "ms": round((time.time() - t0) * 1000, 1),
                "error": type(exc).__name__}


def do_work() -> float:
    """模拟真实请求处理开销：**固定工作量**（约 4ms CPU 时间）。

    必须用固定迭代数而不是「跑到 4ms 就停」——后者在 CPU 被抢占时
    会自动少干活，延迟反而不涨（自校准陷阱）。固定工作量下，
    延迟随可用 CPU 份额线性上涨，这才是真实服务的可观测行为。
    """
    t0 = time.time()
    payload = {"order_id": "o-8821304721", "amount": 199.0, "currency": "CNY",
               "items": [{"sku": "SKU-%04d" % i, "qty": i % 5 + 1, "price": 9.9}
                         for i in range(24)]}
    blob = json.dumps(payload, sort_keys=True).encode()
    digest = b""
    for _ in range(6000):
        digest = hashlib.sha256(blob + digest).digest()
    return round((time.time() - t0) * 1000, 1)


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, obj: dict, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/healthz"):
            up = check_upstream()
            work_ms = do_work()
            total = round(up["ms"] + work_ms, 1)
            status = "ok" if up["ok"] else "degraded"
            self._json({"status": status, "total_ms": total,
                        "work_ms": work_ms, "upstream": up})
        elif self.path.startswith("/api/pay"):
            work_ms = do_work()
            self._json({"status": "ok", "order_id": "o-8821304721",
                        "amount": 199.0, "work_ms": work_ms})
        else:
            self._json({"service": "payment-api", "endpoints":
                        ["/healthz", "/api/pay"]})

    def log_message(self, *args):
        pass  # 不写 access log，避免自身 I/O 干扰实验


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print("payment-api listening on %s:%s upstream=%s" % (HOST, PORT, CFG["upstream"]),
          flush=True)
    with Server((HOST, int(PORT)), Handler) as httpd:
        httpd.serve_forever()
