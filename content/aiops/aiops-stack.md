---
id: aiops-stack
title: AIOps 技术栈与分层架构
title_en: "AIOps Tech Stack & Layered Architecture"
zone: aiops
difficulty: 2
tags: [架构, 技术选型, 分层, 开源复用]
category: concept
milestones:
  - 能画出 6 层 AIOps 架构图
  - 能指出每一层对应的开源组件
  - 能解释"为什么只自研薄薄一层"
edges:
  to:
    - id: aiops-monitoring
      question: 最底层的数据从哪来？先看监控接入
    - id: aiops-rca
      question: 数据齐了，怎么做根因分析？
    - id: aiops-guardrail
      question: 分析出根因后，怎么安全地执行？
    - id: aiops-orchestration
      question: 怎么把诊断和执行串成自动闭环？
    - id: aiops-rag
      question: 怎么给智能体喂私有知识？
---

## 六层架构

一个可落地的 AIOps 系统，从下到上大约长这样：

```
┌─────────────────────────────────────────┐
│ 6. RAG 知识层      RAGFlow 私有文档检索   │
├─────────────────────────────────────────┤
│ 5. 智能体编排层    Dify 诊断链 + 工作流    │
├─────────────────────────────────────────┤
│ 4. K8s / 云 AI 诊断层  HolmesGPT 思路    │
├─────────────────────────────────────────┤
│ 3. 执行与护栏层    StackStorm + 审批流     │
├─────────────────────────────────────────┤
│ 2. CMDB / 拓扑层   服务依赖、资源归属      │
├─────────────────────────────────────────┤
│ 1. 监控数据层      夜莺 / Prometheus 指标  │
└─────────────────────────────────────────┘
```

## 每一层对应什么

| 层 | 作用 | 可直接复用的开源 |
| --- | --- | --- |
| 监控数据层 | 指标、日志、告警统一接入 | 夜莺 Nightingale、Prometheus、VictoriaMetrics |
| CMDB / 拓扑层 | 服务依赖、主机归属、变更记录 | 自研轻量 CMDB 或资产系统 |
| 执行与护栏层 | 真正去执行动作 + 风险拦截 | StackStorm、Argo Workflows |
| K8s / 云诊断层 | 结合上下文做根因假设 | HolmesGPT 思路（可借鉴） |
| 智能体编排层 | 把诊断、决策、执行串成链 | Dify、LangGraph |
| RAG 知识层 | 检索 runbook / 复盘 / 文档 | RAGFlow、Dify 知识库 |

<!-- DEEP_DIVE -->

## 为什么只自研"薄薄一层"

这是面试里最该讲清楚的一句话：**不要重复造轮子，要造"胶水"。**

- 监控、编排、知识库、执行引擎——每一层都有成熟开源，直接拉起来；
- 真正需要自己写的是中间那段**跨工具编排 + 公司特有 RCA 接线 + 护栏策略 + 模型胶水**：
  - 把夜莺的告警格式，转成 HolmesGPT 能吃的上下文；
  - 把 RAGFlow 检索到的 runbook，注入到诊断提示词；
  - 把"高危动作"统一收口到审批流，而不是散落在各处脚本里。

换句话说：**开源解决"能力"，自研解决"接线与治理"。**

<!-- RESOURCES -->

## 参考资料

- [HolmesGPT — LLM 告警根因分析](https://github.com/robustintelligence/holmesgpt)
- [夜莺监控 Nightingale](https://n9e.github.io/)
- [RAGFlow](https://ragflow.io/)
- [Dify](https://dify.ai/)
- [StackStorm](https://stackstorm.com/)
