# -*- coding: utf-8 -*-
"""一键把真实事故库建进 RAGFlow（云端 / 自托管通用，同套 v0.27.2 API）。

用法：
  # 云端 Starter（$29/月，给 API Key）或自托管（http://127.0.0.1:9380）
  set RAGFLOW_BASE_URL=https://your-instance.ragflow.cloud   # 或 http://127.0.0.1:9380
  set RAGFLOW_API_KEY=ragflow-xxxx
  python build_kb.py

流程：建库(中文+naive切块) → 逐个上传 md → 批量解析 → 轮询直到解析完 → 抽检检索。
跑完会打印 DATASET_ID，把它填进后端环境变量 RAGFLOW_DATASET_IDS 即可接通研判。

注意：RAGFlow 云端 Free 档（$0）明确无 API 访问，本脚本需要 Starter 及以上或自托管。
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import time
import urllib.parse
from incident_docs import all_docs

KB_NAME = "AIOps 真实事故库（6 大公开复盘）"
POLL_TIMEOUT = 600  # 解析轮询上限（秒）


def _host_only(base_url: str) -> tuple[str, str, bool]:
    p = urllib.parse.urlparse(base_url)
    host = p.hostname or "127.0.0.1"
    port = p.port or (443 if p.scheme == "https" else 80)
    is_https = p.scheme == "https"
    return host, str(port), is_https


def _conn(base_url: str, is_https: bool, host: str, port: str):
    # localhost / 127.0.0.1 不代理（避免被本机 VPN 代理 10809 拦 localhost）
    if host in ("127.0.0.1", "localhost") or base_url.startswith("http://127.0.0.1"):
        if is_https:
            import ssl
            return http.client.HTTPSConnection(host, int(port), context=ssl.create_default_context(), timeout=30)
        return http_client_no_proxy(host, int(port))
    if is_https:
        import ssl
        return http.client.HTTPSConnection(host, int(port), context=ssl.create_default_context(), timeout=30)
    return http.client.HTTPConnection(host, int(port), timeout=30)


class _NoProxyHTTPConnection(http.client.HTTPConnection):
    # 强制不走代理
    def set_tunnel(self, *a, **k):
        raise NotImplementedError("no tunnel")


def http_client_no_proxy(host, port):
    return _NoProxyHTTPConnection(host, port, timeout=30)


def _request(base_url: str, method: str, path: str, api_key: str,
             body: bytes | None = None, headers: dict | None = None,
             is_json: bool = True) -> tuple[int, dict]:
    host, port, is_https = _host_only(base_url)
    conn = _conn(base_url, is_https, host, port)
    h = {"Authorization": f"Bearer {api_key}"}
    if is_json:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    try:
        conn.request(method, path, body=body, headers=h)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {"_raw": raw}
        return resp.status, data
    finally:
        conn.close()


def _post_json(base_url, path, api_key, payload):
    return _request(base_url, "POST", path, api_key,
                    body=json.dumps(payload).encode("utf-8"))


def create_dataset(base_url, api_key, name):
    # v0.27.2：建库输入字段是 chunk_method（parser_id 只是序列化别名，传了会 101）
    status, data = _post_json(base_url, "/api/v1/datasets", api_key, {
        "name": name,
        "language": "Chinese",
        "chunk_method": "naive",
        "description": "真实公开运维事故复盘，供 AIOps 研判时相似故障召回",
    })
    if status != 200 or data.get("code") not in (0, None, "0"):
        raise SystemExit(f"[建库失败] HTTP {status} {json.dumps(data, ensure_ascii=False)}")
    kb_id = data["data"]["id"]
    print(f"[建库] OK id={kb_id} name={name}")
    return kb_id


def upload_doc(base_url, api_key, kb_id, fname, content: bytes) -> str:
    boundary = "----aiopsragflowboundary"
    crlf = b"\r\n"
    body = b""
    body += b"--" + boundary.encode() + crlf
    body += (f'Content-Disposition: form-data; name="file"; filename="{fname}"').encode() + crlf
    body += b"Content-Type: text/markdown" + crlf + crlf
    body += content + crlf
    body += b"--" + boundary.encode() + b"--" + crlf
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"}
    status, data = _request(base_url, "POST", f"/api/v1/datasets/{kb_id}/documents",
                            api_key, body=body, headers=headers, is_json=True)
    if status != 200 or data.get("code") not in (0, None, "0"):
        raise SystemExit(f"[上传失败 {fname}] HTTP {status} {json.dumps(data, ensure_ascii=False)}")
    # 返回可能是单 doc 或 docs 列表
    d = data["data"]
    if isinstance(d, list):
        doc_id = d[0]["id"]
    else:
        doc_id = d["id"]
    print(f"[上传] OK {fname} -> doc_id={doc_id}")
    return doc_id


def parse_docs(base_url, api_key, kb_id, doc_ids):
    status, data = _post_json(base_url, f"/api/v1/datasets/{kb_id}/documents/parse", api_key,
                              {"document_ids": doc_ids})
    print(f"[解析] 提交 {len(doc_ids)} 个文档 -> HTTP {status} {json.dumps(data, ensure_ascii=False)[:120]}")


def poll_parse(base_url, api_key, kb_id, doc_ids, timeout=POLL_TIMEOUT):
    ids = set(doc_ids)
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, data = _request(base_url, "GET", f"/api/v1/datasets/{kb_id}/documents?page=1&page_size=100", api_key)
        docs = (data.get("data") or {}).get("docs", [])
        done = {d["id"]: d for d in docs if d["id"] in ids}
        all_done = all(d.get("run", "").upper() in ("DONE", "SUCCESS", "COMPLETE") for d in done.values())
        pending = [f"{d.get('name')}={d.get('run')}" for d in done.values() if d.get("run","").upper() not in ("DONE","SUCCESS","COMPLETE")]
        if all_done:
            print("[解析] 全部完成")
            return True
        print(f"[解析] 轮询中（{int(deadline-time.time())}s 余）: {', '.join(pending) or '等待'}")
        time.sleep(8)
    print("[解析] 超时未完成，可稍后手动在 UI 查看；脚本继续做检索抽检")
    return False


def retrieval_test(base_url, api_key, kb_id, question: str):
    status, data = _post_json(base_url, "/api/v1/retrieval", api_key, {
        "question": question,
        "dataset_ids": [kb_id],
        "page": 1,
        "page_size": 3,
        "similarity_threshold": 0.1,
        "vector_similarity_weight": 0.3,
        "knn_top_k": 1024,
    })
    if status != 200:
        print(f"[检索抽检] HTTP {status}: {json.dumps(data, ensure_ascii=False)[:200]}")
        return
    chunks = (data.get("data") or {}).get("chunks", [])
    print(f"[检索抽检] 问题：{question}")
    print(f"           命中 {len(chunks)} 条")
    for i, c in enumerate(chunks[:3], 1):
        print(f"  #{i} [{c.get('document_keyword','')}] sim={c.get('similarity'):.3f}")
        print(f"      {str(c.get('content',''))[:160]}")


def main():
    base_url = os.environ.get("RAGFLOW_BASE_URL", "").strip().rstrip("/")
    api_key = os.environ.get("RAGFLOW_API_KEY", "").strip()
    if not (base_url and api_key):
        raise SystemExit(
            "缺少环境变量：\n"
            "  set RAGFLOW_BASE_URL=https://你的实例  (云端 Starter 或 http://127.0.0.1:9380 自托管)\n"
            "  set RAGFLOW_API_KEY=ragflow-xxxx\n"
            "（注意：云端 Free 档 $0 无 API，请用 Starter $29/月 或自托管）")
    if "@" in api_key or " " in api_key:
        raise SystemExit("API Key 看起来带了空格或邮箱，请只填 ragflow- 开头的 Key")

    print(f"目标实例：{base_url}")
    docs = all_docs()
    kb_id = create_dataset(base_url, api_key, KB_NAME)
    doc_ids = []
    for fname, md in docs:
        doc_ids.append(upload_doc(base_url, api_key, kb_id, fname, md.encode("utf-8")))
    parse_docs(base_url, api_key, kb_id, doc_ids)
    poll_parse(base_url, api_key, kb_id, doc_ids)
    retrieval_test(base_url, api_key, kb_id, "全局 CDN 大量返回 503，源站看起来被打爆，怎么定位根因")
    retrieval_test(base_url, api_key, kb_id, "数据库复制滞后并停止，重建备库时误删了主库数据目录怎么办")
    print("\n==== 接通后端 ====")
    print(f"把下面这行填进后端启动环境（或 start-backend.bat / _launch_llm.py）：")
    print(f"  RAGFLOW_BASE_URL={base_url}")
    print(f"  RAGFLOW_API_KEY={api_key}")
    print(f"  RAGFLOW_DATASET_IDS={kb_id}")
    print("后端 rag.py 已支持上述变量，研判时会优先走真实 RAGFlow 召回，失败才回退 mock。")


if __name__ == "__main__":
    main()
