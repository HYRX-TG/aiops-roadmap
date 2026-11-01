"""RAGFlow 知识检索：真实 API 优先，断连/未配置时 mock 兜底。

生产接线（用户本机已跑 RAGFlow）：
  RAGFLOW_BASE_URL  如 http://127.0.0.1:9380
  RAGFLOW_API_KEY   RAGFlow 侧生成的 API KEY
  RAGFLOW_DATASET_IDS 逗号分隔的 dataset id
RAGFlow 服务端本身做语义+关键词混合检索，这里只负责调用与结构化。
"""
from __future__ import annotations

import json
import os
import urllib.request


class RagClient:
    def __init__(self, base_url: str = "", api_key: str = "", dataset_ids: str = "",
                 timeout: float = 6.0):
        self.base_url = base_url or os.environ.get("RAGFLOW_BASE_URL", "")
        self.api_key = api_key or os.environ.get("RAGFLOW_API_KEY", "")
        self.dataset_ids = [x for x in (dataset_ids or os.environ.get("RAGFLOW_DATASET_IDS", "")).split(",") if x]
        self.timeout = timeout
        self.last_backend = "uninitialized"

    # ── 真实 RAGFlow ─────────────────────────────────────────
    def _retrieve_real(self, query: str, top_k: int) -> list[dict] | None:
        if not (self.base_url and self.api_key and self.dataset_ids):
            return None
        body = json.dumps({"question": query, "dataset_ids": self.dataset_ids,
                           "page": 1, "page_size": top_k,
                           "similarity_threshold": 0.1,
                           "vector_similarity_weight": 0.3, "knn_top_k": 1024,
                           "highlight": False}).encode()
        req = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/v1/retrieval", data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            chunks = ((data.get("data") or {}).get("chunks")) or []
            self.last_backend = "ragflow"
            return [{"content": c.get("content", ""), "document": c.get("document_keyword", ""),
                     "score": c.get("similarity", 0.0)} for c in chunks[:top_k]]
        except Exception:
            return None

    # ── mock 兜底（演示/离线不依赖外部服务）──────────────────
    def _retrieve_mock(self, alertname: str, service: str) -> list[dict]:
        self.last_backend = "mock"
        return [
            {"content": f"历史故障复盘：2026-03 {service} 依赖超时导致错误率抬升，标准处置为确认影响面→回滚/扩容→验证→归档，平均恢复 12 分钟。",
             "document": "incident/2026-03-dependency-timeout.md", "score": 0.86},
            {"content": f"Runbook《依赖超时处置 v2》：先看 {service} 下游依赖成功率，再判定回滚或扩容；冻结窗口内禁止自动执行。",
             "document": "runbook/dependency-timeout-v2.md", "score": 0.81},
            {"content": "预案：回滚属高风险动作（T3），必须 SRE on-call 审批；扩容属中风险（T2）可半自动。",
             "document": "runbook/approval-matrix.md", "score": 0.74},
        ]

    def retrieve(self, query: str, alertname: str = "", service: str = "unknown",
                 top_k: int = 3) -> list[dict]:
        real = self._retrieve_real(query, top_k)
        if real is not None and real:
            return real
        return self._retrieve_mock(alertname, service)
