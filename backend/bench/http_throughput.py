"""真实 HTTP 接入吞吐实测（复盘：文档曾把"进程内纯函数吞吐"当成系统吞吐）。

两种模式：
  short    每条告警一次 TCP 连接（最坏情况）
  keepalive 复用连接（前端/探针常态）
"""
import http.client
import json
import time
import urllib.request

BASE = "127.0.0.1", 8600
N = 2000


def make_payload(i: int) -> dict:
    return {"source": "business_log", "payload": {"events": [{
        "level": "error", "event": f"bench_probe_{i}",
        "message": f"ERROR bench probe seq={i}", "service": "bench-svc"}]}}


def short_conn(n: int) -> float:
    t0 = time.time()
    for i in range(n):
        req = urllib.request.Request(
            "http://127.0.0.1:8600/api/ingest",
            data=json.dumps(make_payload(i)).encode(), method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read()
    return n / (time.time() - t0)


def keepalive(n: int) -> float:
    conn = http.client.HTTPConnection(*BASE, timeout=10)
    t0 = time.time()
    for i in range(n):
        body = json.dumps(make_payload(i))
        conn.request("POST", "/api/ingest", body=body,
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        resp.read()
        if resp.status != 200:
            raise RuntimeError(f"status {resp.status}")
    dt = time.time() - t0
    conn.close()
    return n / dt


if __name__ == "__main__":
    s = short_conn(300)
    k = keepalive(N)
    print(json.dumps({
        "short_connection_qps": round(s, 1),
        "keepalive_qps": round(k, 1),
        "note": "真实 HTTP + JSON + SQLite 落库；进程内纯函数吞吐见 bench/flood.py",
    }, ensure_ascii=False))
