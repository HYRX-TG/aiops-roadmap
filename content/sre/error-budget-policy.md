---
id: error-budget-policy
title: Error Budget Policy
zone: sre
edges:
  to:
    - id: slo-alerting
      question: >-
        The policy is clear on paper. But how do I know the moment the budget
        starts burning — before it's too late to act?
      detail: >-
        We've agreed: when the budget drops below 50%, we stop shipping features
        and focus on reliability. But right now I only find out how much budget
        we've spent by manually checking a dashboard. I need an automatic signal
        the moment the burn rate goes high, not a surprise at the end of the month.
difficulty: 2
tags:
  - error-budget
  - slo
  - sre
  - feature-velocity
  - reliability
  - policy
category: practice
milestones:
  - Write an error budget policy document with defined thresholds (75%, 50%, 0%)
  - Understand why the error budget is a shared tool between SRE and product
  - Explain what "freezing the feature roadmap" means in practice and who decides
  - Know the difference between error budget consumption and SLO breach
title_zh: "错误预算策略"

---


An error budget is only useful if everyone knows what to do when it runs out. Without a policy, you have a metric on a dashboard that produces anxiety but not action. The error budget policy is the written agreement — between engineering, SRE, and product — about what happens at each stage of budget consumption. It converts a concept into a process.

<!-- DEEP_DIVE -->

## What a policy needs to say

A good error budget policy defines behavior at multiple thresholds, not just "zero." The reason: by the time the budget is at zero, it's too late to prevent the breach. You need to start changing behavior earlier.

A typical structure uses three thresholds:

**75% consumed (25% remaining)**: Warning. No immediate action required, but the team discusses it in the next standup. Review what's been consuming the budget — is it a single bad incident or a pattern of small failures?

**50% consumed (50% remaining)**: Caution. Start deprioritizing risky changes. Any deployment that might cause elevated errors should be reviewed carefully. Major migrations or infrastructure changes get postponed.

**0% remaining (budget exhausted)**: Freeze. Feature deployments stop. The team focuses exclusively on reliability improvements until the budget recovers. No new features ship until the next measurement window begins.

## The conversation with product

This policy only works if product management agrees to it before the budget runs low — not during an argument about whether to stop shipping. The most effective approach: propose the policy, explain what it means practically ("if we breach our SLO this month, we hold the release scheduled for week 4"), and get explicit sign-off. When everyone has agreed to the rules in advance, enforcing them is a mechanical process rather than a political fight.

The error budget policy is also a forcing function for product to care about reliability work. When they understand that an unstable platform means their features get held, they have a direct incentive to support engineering reliability investments.

## What "freeze" doesn't mean

A feature freeze triggered by budget exhaustion doesn't mean the team stops working. It means:

- **Reliability work continues** — fixing the root causes of budget consumption is the priority
- **Bug fixes ship** — bugs that were causing reliability problems are exactly what should be fixed
- **Infrastructure changes that improve reliability ship** — adding a circuit breaker, fixing a database index, reducing timeout values
- **New feature development pauses** — features that don't improve reliability are deprioritized until the budget recovers

The freeze is targeted, not total.

## Budget windows and rollover

Most error budget policies use a rolling 30-day window. This means the budget from 31 days ago starts returning to you as each day passes. A bad week 30 days ago is gradually forgotten by the metric. This is generally the right behavior — you don't want to be indefinitely penalized for a past incident that you've already fixed.

Some teams use quarterly budgets for strategic planning alongside monthly budgets for operational alerting. Quarterly consumption tells you whether reliability is trending in the right direction. Monthly consumption tells you whether to ship this week.

<!-- RESOURCES -->

- [Error Budget Policy - Google SRE Workbook](https://sre.google/workbook/error-budget-policy/) -- type: book, time: 20m
- [Managing Risk with Error Budgets - Google Cloud Blog](https://cloud.google.com/blog/products/devops-sre/sre-fundamentals-slis-slas-and-slos) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
只有当所有人都清楚错误预算耗尽时该做什么，错误预算才有用。没有策略，你得到的只是仪表盘上一个制造焦虑却无法促成行动的数字。错误预算策略是工程、SRE 和产品之间就预算消耗各阶段该采取什么行动达成的书面约定。它把一个概念转化为一套流程。

<!-- ZH_DEEP_DIVE -->
## 策略需要说明什么

一个好的错误预算策略会在多个阈值上定义行为，而不仅仅是“零”。原因在于：当预算降到零时，再想防止违规已经太晚了。你需要更早开始改变行为。

典型的结构使用三个阈值：

**已消耗 75%（剩余 25%）**：警告。不需要立即采取行动，但团队要在下一次站会上讨论。回顾是什么在消耗预算——是单次严重事故，还是一连串小故障的模式？

**已消耗 50%（剩余 50%）**：谨慎。开始降低高风险变更的优先级。任何可能造成错误率升高的部署都应仔细审查。重大迁移或基础设施变更予以推迟。

**剩余 0%（预算耗尽）**：冻结。功能部署停止。团队专注于可靠性改进，直到预算恢复。在下一个测量窗口开始之前，不发布任何新功能。

## 与产品团队的沟通

这项策略只有在产品管理层于预算走低之前同意时才有效——而不是在争论是否停止发布时才去谈。最有效的做法是：提出该策略，解释其实际含义（“如果我们本月违反了 SLO，我们就暂缓第 4 周计划的发布”），并获得明确签字确认。当所有人都事先同意了规则，执行规则就是一个机械流程，而不是政治斗争。

错误预算策略也是促使产品团队关注可靠性工作的强制机制。当他们明白平台不稳定意味着他们的功能会被搁置时，他们就有直接动力去支持工程侧的可靠性投入。

## “冻结”并不意味着什么

由预算耗尽触发的功能冻结并不意味着团队停止工作。它意味着：

- **可靠性工作继续**——修复预算消耗的根本原因是优先事项
- **缺陷修复照常发布**——导致可靠性问题的缺陷正是应该修复的
- **提升可靠性的基础设施变更照常发布**——增加熔断器、修复数据库索引、降低超时值
- **新功能开发暂停**——不能提升可靠性的功能被降低优先级，直到预算恢复

冻结是有针对性的，而非全面的。

## 预算窗口与滚动

大多数错误预算策略使用滚动 30 天窗口。这意味着随着每一天过去，31 天前的预算开始返还给你。30 天前糟糕的一周会被指标逐渐遗忘。这通常是正确的行为——你不会希望因为一个已经修复的过往事故而被无限期惩罚。

一些团队在用于运营告警的月度预算之外，还使用季度预算进行战略规划。季度消耗告诉你可靠性是否在朝正确方向发展。月度消耗告诉你本周是否应该发布。

<!-- ZH_RESOURCES -->
- [错误预算策略 - Google SRE 工作手册](https://sre.google/workbook/error-budget-policy/) -- 类型: 书籍, 时间: 20分钟
- [通过错误预算管理风险 - Google Cloud 博客](https://cloud.google.com/blog/products/devops-sre/sre-fundamentals-slis-slas-and-slos) -- 类型: 文章, 时间: 10分钟

<!-- ZH_UI -->
1. 编写错误预算策略文档，定义阈值（75%、50%、0%）
2. 理解为什么错误预算是 SRE 与产品之间的共享工具
3. 解释“冻结功能路线图”在实践中意味着什么以及由谁决定
4. 了解错误预算消耗与 SLO 违约之间的区别
5. 策略在纸面上很清晰。但我如何在预算开始燃烧的那一刻就知道——在来不及行动之前？
6. 我们已达成一致：当预算降至 50% 以下时，停止发布功能并专注于可靠性。但现在我只能通过手动查看仪表盘来了解已消耗多少预算。我需要在燃烧率升高的那一刻获得自动信号，而不是在月底才意外发现。
