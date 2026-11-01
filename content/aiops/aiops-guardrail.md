---
id: aiops-guardrail
title: 执行护栏：让 AI 只建议、不乱动
title_en: "Execution Guardrails: AI Advises, Never Acts Alone"
zone: aiops
difficulty: 2
tags: [护栏, 安全, 审批, 风险分级, 权限]
category: principle
milestones:
  - 能讲清"建议"与"执行"必须分离
  - 能设计一套基于风险分级的审批流
  - 能说明 dry-run 与回滚在护栏里的位置
edges:
  to:
    - id: aiops-orchestration
      question: 怎么把诊断 + 护栏 + 执行串成自动闭环？
---

## 为什么护栏是 AIOps 的命门

分析出错，最多是"建议不准"；**执行出错，可能是一次线上事故**。所以成熟做法只有一个原则：

> **AI 默认只有"建议权"，没有"执行权"。**

能自动执行的，只有事先白名单里、低风险、可逆的标准动作（如"重启单个非核心 Pod"）。其余一律走人工审批。

## 风险分级

| 等级 | 例子 | 处理方式 |
| --- | --- | --- |
| 低（白名单） | 重启单个 Pod、清理日志 | 可自动执行 |
| 中 | 扩容副本、切流量 | 自动执行 + 事后通知 |
| 高 | 回滚发版、删资源、改配置 | 必须人工审批 |
| 危险 | 批量操作、跨集群 | 禁止 / 双人复核 |

## 三道保险

1. **dry-run 优先**：执行前先在护栏层做一次预演，确认影响面；
2. **最小权限**：执行账号只能做它被授权的那一类动作；
3. **可回滚**：凡自动执行的动作，必须配套回滚脚本或快照，且执行后持续监控结果。

<!-- DEEP_DIVE -->

## 护栏放在哪一层

护栏**不是模型的一部分，而是模型与外部系统之间的"网关"**。模型输出"建议执行 X"，护栏层拦截后判断风险等级，再决定：自动放行 / 转人工 / 拒绝。

这样即使模型"发疯"，也不会真的删库——真正的安全边界在网关，不在提示词里。这是和面试官聊"AI 安全落地"时最有说服力的点。

<!-- RESOURCES -->

## 参考资料

- [StackStorm — 自动化执行与审批（Action Chain）](https://stackstorm.com/)
- [OpenAI 关于 AI 安全的工具调用最佳实践](https://platform.openai.com/docs/guides/function-calling)
- [最小权限原则 (PoLP)](https://en.wikipedia.org/wiki/Principle_of_least_privilege)
