---
id: aiops-overview
title: AIOps 总览：用大模型重构运维闭环
title_en: "AIOps Overview: Rebuilding the Ops Loop with LLMs"
zone: aiops
difficulty: 1
tags: [AIOps, 大模型, 运维自动化, 概览]
category: concept
milestones:
  - 能说清 AIOps 与传统规则/脚本自动化的本质区别
  - 能画出"监控→诊断→决策→执行→反馈"的闭环
  - 能区分本项目中"可直接复用开源"与"需要自研"的部分
edges:
  to:
    - id: aiops-stack
      question: 想看整体技术栈与分层架构？
    - id: aiops-monitoring
      question: 想先从监控数据接入做起？
---

## 什么是 AIOps

**AIOps（Artificial Intelligence for IT Operations）** 是把机器学习 / 大模型能力引入 IT 运维，让系统具备"感知异常、定位根因、辅助决策、安全执行"的能力。

它并不是要取代 SRE，而是把 SRE 从重复劳动中解放出来：告警降噪、故障定位、变更影响分析、自动执行标准化动作。

## 为什么是现在

三个条件在最近几年才同时成熟：

1. **可观测性数据爆炸**——日志、指标、链路追踪早已普及，但数据太多、人看不过来；
2. **大模型理解非结构化文本的能力跃迁**——日志报错、告警描述、变更记录这些"非结构化信息"第一次能被模型直接读懂；
3. **Agent / 工具调用协议成熟**——MCP 这类协议让模型能安全地"动手"查询和执行，而不只是聊天。

## 与传统自动化的区别

| 维度 | 传统自动化 | AIOps |
| --- | --- | --- |
| 触发条件 | 人写死的规则 / 脚本 | 模型理解语义后判断 |
| 处理对象 | 结构化指标阈值 | 日志、告警、链路等半结构化文本 |
| 应对未知 | 没覆盖就失效 | 能基于上下文做泛化推理 |
| 执行方式 | 全自动或人工 | 建议 + 分级审批 |

<!-- DEEP_DIVE -->

## 闭环 vs 开环

很多"AI 运维"停留在**开环**：模型给建议，人去执行。真正的 AIOps 是**闭环**：

```
监控采集 → 异常检测 / 告警
   → 大模型根因分析（RCA）
   → 决策：建议执行什么动作
   → 护栏：分级审批 / dry-run
   → 执行动作（扩容、回滚、重启…）
   → 反馈：结果再回流到监控
```

落地的难点从来不在"分析"，而在**"执行"**——怎么让 AI 动真格又不闯祸，这正是护栏层要解决的事（见 `AIOps 执行护栏` 节点）。

## 本项目的定位

这个项目本身是一个**交互式知识图谱**，而 `aiops` 分区是我在开源 `infra-roadmap` 基础上自研的核心：它把"基础设施 / SRE / 可观测性"作为地基，再往上搭一套由大模型驱动的 AIOps 闭环。

关键判断是：**6 层里有 5.5 层都能直接复用成熟开源组件，只有"跨工具编排 + 公司特有 RCA 接线 + 护栏策略 + 模型胶水"这一薄层需要自己写。**

<!-- RESOURCES -->

## 参考资料

- [Google SRE Book（免费）](https://sre.google/books/)
- [夜莺监控 Nightingale 文档](https://n9e.github.io/)
- [什么是 AIOps — Gartner 概念来源](https://www.gartner.com/en/information-technology/glossary/aiops-artificial-intelligence-for-it-operations)
