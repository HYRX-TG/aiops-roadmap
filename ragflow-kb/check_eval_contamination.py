"""验证：接通 RAGFlow 事故库后，评测会不会被"喂答案"污染。

背景：ragflow-kb/docs/ 里 6 篇文档正好就是 replay/heldout 评测用的 6 个事故，
且每篇都含「## 真实根因」。若研判链从 RAGFlow 召回到这些文档，
等于把标准答案直接塞进 prompt——评测分数会虚高，失去意义。

做法：用 ragflow-kb/verify_ragflow.py 里的 mock 服务（内置同一批文档），
把 RagClient 指向它，用 Fastly 事故的**告警文本**做查询，
看召回内容里有没有"真实根因 / bug / 触发条件"。
"""
import sys, os, threading, time, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

# 起 mock RAGFlow
import verify_ragflow as V

srv = threading.Thread(
    target=lambda: __import__("http.server",fromlist=["ThreadingHTTPServer"]).ThreadingHTTPServer(("127.0.0.1", V._MOCK_PORT), V.Handler).serve_forever(),
    daemon=True)
srv.start()
time.sleep(1.0)

from app.rag import RagClient

# 用 Fastly 事故的症状做查询（与实际回放一模一样的输入）
query = "全网 503 错误率飙升 多个站点不可访问 源站流量异常暴涨"
c = RagClient(base_url=f"http://127.0.0.1:{V._MOCK_PORT}", api_key="mock", dataset_ids="d1")
hits = c.retrieve(query, alertname="GlobalEdge503Spike", service="edge-cdn")

print(f"召回后端: {c.last_backend}　条数: {len(hits)}\n")
leak = False
for h in hits:
    content = h["content"]
    doc = h["document"]
    flags = []
    for kw in ("真实根因", "根因", "bug", "触发条件", "合法", "无灰度", "校验"):
        if kw in content:
            flags.append(kw)
    if flags:
        leak = True
    print(f"[{doc}] sim={h['score']}")
    print(f"  泄漏关键词: {flags}")
    print(f"  {content[:150].replace(chr(10), ' | ')}")
    print()

print("=" * 60)
if leak:
    print("❌ 已污染：RAGFlow 返回的片段里含有答案要素（根因/bug/触发条件）")
    print("   如果研判链消费这些片段，模型只需要'阅读理解'就能命中，")
    print("   replay / heldout 的分数将不再代表排查能力。")
else:
    print("✅ 未发现答案泄漏")
print("=" * 60)
print("\n影响范围：")
print("  - 接 RAGFlow 后端跑评测 → 分数虚高（不可信）")
print("  - 不接 RAGFlow（当前默认，mock 兜底）→ 评测有效")
print("  - 生产环境用真实内部知识库 → 无此问题（知识库里本来就有历史复盘，")
print("    这与'给模型看历史事故'是合理的产品行为，只是不能用于评测）")
