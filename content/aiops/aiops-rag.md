---
id: aiops-rag
title: 知识库 RAG：把私有文档喂给智能体
title_en: "Knowledge Base RAG: Feeding Private Docs to Agents"
zone: aiops
difficulty: 2
tags: [RAG, RAGFlow, 知识库, runbook, 检索增强]
category: tool
milestones:
  - 能解释为什么需要 RAG 而不是把文档全塞进提示词
  - 能说清 RCA 智能体在何时调用知识库
  - 能在 RAGFlow 里建一个 runbook 知识库
edges:
  to:
    - id: aiops-overview
      question: 回到总览，串起整个 AIOps 闭环？
---

## 为什么需要 RAG

让模型做诊断时，**纯靠它自己的训练知识是不够的**：你们公司的 runbook、历史故障复盘、CMDB 字段含义、内部告警约定——这些"私有知识"模型根本没见过。

直接把全部文档塞进提示词不现实（太贵、超窗口、噪声大）。正确做法是 **RAG（检索增强生成）**：先检索最相关的几段，再连同问题一起喂给模型。

## 在 AIOps 里，RAG 喂给谁

它是 `aiops-stack` 架构里的**第 6 层（知识层）**，主要服务于 RCA 智能体：

```
故障上下文（告警/指标/变更）
   → RAGFlow 检索：相似历史故障 + 对应 runbook
   → 拼进 RCA 提示词
   → 模型结合"公司经验"给出更靠谱的根因与动作
```

## 为什么选 RAGFlow

RAGFlow 对**长文档、表格、扫描件**的解析比较友好，适合喂"故障复盘 PDF""值班手册"这类材料；而且自带检索与引用，能告诉模型"这条建议来自哪份文档"，便于审计和人工核对。

<!-- DEEP_DIVE -->

## 落地要点

1. **知识要分层**：runbook（怎么处理）和历史复盘（之前踩过什么坑）分开建库，召回更准；
2. **引用要可查**：模型给出的每条建议最好能附上来源文档，否则人不敢照做；
3. **持续更新**：runbook 会过期，复盘要回流——知识库是活的，不是一次性导入。

## 与"纯提示词"的对比

| 方式 | 优点 | 缺点 |
| --- | --- | --- |
| 全塞提示词 | 简单 | 超窗口、贵、噪声大、无法更新 |
| RAG | 精准、可更新、可溯源 | 需要维护检索质量 |

<!-- RESOURCES -->

## 参考资料

- [RAGFlow 官网与文档](https://ragflow.io/)
- [What is RAG — AWS 解释](https://aws.amazon.com/what-is/retrieval-augmented-generation/)
- [Dify 知识库能力](https://docs.dify.ai/)
