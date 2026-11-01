# -*- coding: utf-8 -*-
"""本地 mock RAGFlow 服务端到端验证：无需任何真实实例 / API Key。

做什么：
  1. 起一个 ThreadingHTTPServer，实现 RAGFlow v0.27.2 的 /api/v1/retrieval 契约
     （返回 {"data":{"chunks":[{"content","document_keyword","similarity"}]}}），
     内置 6 个事故的微型索引，按查询关键词召回——模拟"相似故障召回"。
  2. 用项目真实的 backend/app/rag.py 的 RagClient 去查它，证明接线契约正确。
  3. 对比"未配置 RAGFlow 时"回退 mock 的行为。

目的：在用户还没决定云端 Starter / 自托管之前，先把"RAGFlow 召回 → 研判"这条链路
的**代码接线**跑通、锁死，避免日后接真实例时踩契约坑。

运行：python verify_ragflow.py
"""
from __future__ import annotations

import sys
import os
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from incident_docs import all_docs

BACKEND_RAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "app")
sys.path.insert(0, os.path.abspath(BACKEND_RAG))

_MOCK_PORT = 9399

# 内置微型索引：文件名 -> 全文
_INDEX = {fname: md for fname, md in all_docs()}


def _score(query: str, text: str) -> float:
    q = query.lower()
    t = text.lower()
    # 中文没有空格，用字符 n-gram 近似：统计 query 里出现的 2 字片段在 text 的出现
    hits = 0
    total = 0
    for i in range(0, len(q) - 1):
        gram = q[i:i + 2]
        if gram.strip():
            total += 1
            if gram in t:
                hits += 1
    return (hits / total) if total else 0.0


def _retrieve_chunks(question: str, dataset_ids, top_k: int = 3):
    scored = []
    for fname, md in _INDEX.items():
        sim = _score(question, md)
        if sim > 0:
            # 取命中的片段（从根因/症状里截一段）
            snippet = md[:400]
            scored.append({
                "content": snippet,
                "document_keyword": fname,
                "similarity": round(sim, 3),
            })
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静默
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            payload = {}
        if self.path.rstrip("/") == "/api/v1/retrieval":
            question = payload.get("question", "")
            ds = payload.get("dataset_ids", [])
            top_k = int(payload.get("page_size", 3))
            chunks = _retrieve_chunks(question, ds, top_k)
            resp = {"code": 0, "data": {"chunks": chunks}}
            self._send(200, resp)
        else:
            self._send(404, {"code": 1, "message": "not found"})

    def _send(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_mock():
    srv = ThreadingHTTPServer(("127.0.0.1", _MOCK_PORT), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def main():
    srv = start_mock()
    # 等 server 起来
    import time
    time.sleep(0.3)

    import rag  # 项目真实模块

    print("=== 测试 1：配置真实 RAGFlow（指向本地 mock）→ 应走 real 路径 ===")
    os.environ["RAGFLOW_BASE_URL"] = f"http://127.0.0.1:{_MOCK_PORT}"
    os.environ["RAGFLOW_API_KEY"] = "ragflow-test"
    os.environ["RAGFLOW_DATASET_IDS"] = "kb-mock"
    c1 = rag.RagClient()
    hits = c1.retrieve("全局 CDN 大量返回 503，源站看起来被打爆，怎么定位根因", service="edge-cdn")
    print(f"  last_backend = {c1.last_backend}")
    print(f"  召回条数      = {len(hits)}")
    for h in hits[:2]:
        print(f"   - [{h['document']}] sim={h['score']:.3f}  {h['content'][:60]}...")
    assert c1.last_backend == "ragflow", "应走真实 RAGFlow 路径"
    assert hits, "应召回到内容"
    assert "fastly" in hits[0]["document"].lower() or "503" in hits[0]["content"], "应召回 Fastly/CDN 事故"

    print("\n=== 测试 2：未配置 RAGFlow → 应回退 mock ===")
    os.environ.pop("RAGFLOW_BASE_URL", None)
    os.environ.pop("RAGFLOW_API_KEY", None)
    os.environ.pop("RAGFLOW_DATASET_IDS", None)
    c2 = rag.RagClient()
    mocks = c2.retrieve("DBReplicationLagCritical", service="postgresql")
    print(f"  last_backend = {c2.last_backend}")
    print(f"  回退条数      = {len(mocks)}  (首条 doc={mocks[0]['document']})")
    assert c2.last_backend == "mock", "未配置应回退 mock"

    print("\n=== 测试 3：配置存在但实例不可达 → 应回退 mock（不报错）===")
    os.environ["RAGFLOW_BASE_URL"] = "http://127.0.0.1:9"  # 不可能连通的端口
    os.environ["RAGFLOW_API_KEY"] = "x"
    os.environ["RAGFLOW_DATASET_IDS"] = "kb"
    c3 = rag.RagClient(timeout=2.0)
    fallback = c3.retrieve("x", service="y")
    print(f"  last_backend = {c3.last_backend}  (不可达应回退)")
    assert c3.last_backend == "mock", "实例不可达应安全回退 mock"

    srv.shutdown()
    print("\n✅ 全部通过：rag.py 召回契约正确；真实实例优先、失败/未配置回退 mock 均正常。")


if __name__ == "__main__":
    main()
