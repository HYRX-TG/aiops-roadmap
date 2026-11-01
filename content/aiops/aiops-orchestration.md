---
id: aiops-orchestration
title: 多智能体编排闭环：Dify + StackStorm
title_en: "Multi-Agent Orchestration Loop: Dify + StackStorm"
zone: aiops
difficulty: 3
tags: [编排, Dify, StackStorm, 工作流, 闭环]
category: practice
milestones:
  - 能画出"诊断→审批→执行→反馈"的编排链路
  - 能说清 Dify 与 StackStorm 各自的职责边界
  - 能解释为什么执行层要独立出来而不是写在提示词里
edges:
  to:
    - id: aiops-rag
      question: 怎么给编排里的智能体喂私有知识？
---

## 把零散能力串成"一条链"

前面几层（监控、RCA、护栏）是独立能力。编排层的作用，是把它们接成一条**可被触发、可被观测、可被打断**的闭环工作流：

```
夜莺告警
  → Dify 工作流：调用 RCA 智能体做诊断
  → 诊断产出"建议动作" + 风险等级
  → 护栏（StackStorm）按风险分级：自动 / 转人工 / 拒绝
  → 执行动作（扩容 / 回滚 / 重启）
  → 结果回写监控，形成反馈
```

## Dify 负责"大脑"，StackStorm 负责"手脚"

- **Dify**：搭诊断链、管理提示词、串 RAG、做 LLM 调用。偏"思考与编排"；
- **StackStorm**：真正去执行动作、处理审批流、对接 K8s / 云平台 API。偏"可靠执行与治理"。

这种分工的好处是：**思考可以迭代得快，执行必须稳**。把执行收口到一个专门的系统里，比把 `kubectl` 直接塞进提示词要安全得多（也呼应 `AIOps 执行护栏`）。

<!-- DEEP_DIVE -->

## 为什么"可被打断"很重要

一条全自动链路最怕"停不下来"。编排层必须支持：

- **人工卡点**：中高风险动作在 StackStorm 里挂起，等人批准；
- **超时与熔断**：某一步超时或异常，整条链回退到安全状态；
- **全链路留痕**：每一步的输入输出都记录，事后能复盘"当时为什么这么处理"。

这三点，决定了它是一条**可审计的生产级闭环**，而不是一个 demo 脚本。

<!-- RESOURCES -->

## 参考资料

- [Dify 文档](https://docs.dify.ai/)
- [StackStorm 文档](https://docs.stackstorm.com/)
- [LangGraph — 另一种智能体编排思路](https://langchain-ai.github.io/langgraph/)
