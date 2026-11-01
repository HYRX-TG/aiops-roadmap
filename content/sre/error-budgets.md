---
id: error-budgets
title: Error Budgets
zone: sre
edges:
  to:
    - id: error-budget-policy
      question: >-
        How does the error budget change what the team actually works on — and
        how do I make that conversation with product?
      detail: >-
        I understand the concept — if we're burning budget, we should stop
        shipping features. But in practice that's a hard line to hold when
        product has quarterly commitments. How do I make this a policy instead
        of an argument every time?
    - id: slo-alerting
      question: >-
        My error budget is burning. How do I catch it fast enough to actually
        do something about it?
      detail: >-
        The budget is being consumed but I only find out when someone manually
        checks the dashboard. By the time I know about it, we've already burned
        through a chunk of our monthly allowance. I need to be notified
        automatically when the burn rate goes high.
difficulty: 2
tags:
  - error-budget
  - slo
  - sre
  - reliability
  - feature-velocity
category: concept
milestones:
  - Calculate the error budget in minutes for a 99.9% SLO over 30 days
  - Explain the budget metaphor and what it means to "spend" budget
  - Understand why the error budget belongs to both the product team and SRE
  - Describe what happens when the budget runs out and what policy that triggers
title_zh: "错误预算"

---


An error budget is the flip side of an SLO. If you've committed to 99.9% availability, then 0.1% of time is the budget you're allowed to spend on unreliability. That 0.1% is approximately 43 minutes per month. You can spend it however you like — risky deployments, experiments, technical debt — but once it's gone, you've broken your promise to users. The budget metaphor transforms reliability from a vague aspiration into a resource that teams actually manage.

<!-- DEEP_DIVE -->

## The budget metaphor

When engineers want to ship faster, reliability often suffers. When ops teams want maximum stability, feature velocity slows. Historically this tension is resolved through negotiation, politics, or whoever shouts loudest. Error budgets replace that with arithmetic.

Here's how it works: you commit to 99.9% availability over 30 days. That gives you 43 minutes of allowed downtime. Every minute of actual downtime is charged against that budget. If you've had zero incidents, you have 43 minutes of budget remaining — you can afford to take risks, deploy aggressively, ship the thing that might break. If you've already burned 30 minutes, you have 13 left — you should be cautious, maybe hold off on that risky migration.

The budget makes the tradeoff explicit. Shipping fast and breaking things spends budget. Being conservative preserves it. Both sides can see the account balance.

## How error budget consumption works in practice

Budget is consumed by any period during which your SLI is below its target. A 10-minute outage (100% failure rate) consumes 10 minutes of budget. A 24-hour period with 5% error rate (when your SLO allows 0.1% errors) consumes:

```
Bad events = total_requests × 0.05
Good events threshold = total_requests × 0.001
Excess bad events = total_requests × 0.049
Budget consumed proportional to 0.049 / 0.001 = 49x your normal budget rate
```

The precise calculation depends on your SLI definition, but the key insight is that partial failures consume budget faster than they seem. A 30-minute period with elevated errors can burn through a month's budget.

## What the budget enables

The error budget answers the question that previously had no good answer: "How do we decide when to slow down?" When the budget is healthy, the answer is: "Ship." When it's depleted, the answer is: "Stop and fix reliability." No politics, no arguments — just the budget balance.

This also gives SRE teams leverage they didn't have before. An SRE who says "this feature is too risky" can be ignored. An SRE who says "we've consumed 80% of our error budget this month and shipping this risky change will exhaust the rest — the policy says we stop" is making a data-driven argument that's much harder to dismiss.

## The shared ownership principle

The error budget doesn't belong to the SRE team. It belongs to both engineering and product. Product owns the budget because they make decisions (ship features, cut corners, move fast) that consume it. Engineering owns it because they build reliability investments that replenish it. When the budget is managed as a shared resource with shared accountability, the conversation between product and reliability shifts from adversarial to collaborative.

<!-- RESOURCES -->

- [Google SRE Book - Motivation for Error Budgets](https://sre.google/sre-book/embracing-risk/#xref_risk-management_motivation-for-error-budgets) -- type: book, time: 20m
- [Error Budget Policy - Google SRE Workbook](https://sre.google/workbook/error-budget-policy/) -- type: book, time: 20m
- [The Error Budget - Increment Magazine](https://increment.com/reliability/error-budget-approach-to-reliability/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
错误预算是 SLO 的另一面。如果你承诺了 99.9% 的可用性，那么 0.1% 的时间就是你可以花在不可靠性上的预算。这 0.1% 大约是每月 43 分钟。你可以随意支配它——风险部署、实验、技术债——但一旦用完，你就违背了对用户的承诺。预算这个比喻把可靠性从模糊的愿望变成了团队真正管理的资源。

<!-- ZH_DEEP_DIVE -->
## 预算隐喻

当工程师想要更快交付时，可靠性往往会受损。当运维团队想要最大稳定性时，功能迭代速度就会放缓。历史上，这种矛盾通过协商、政治手段或谁嗓门最大来解决。错误预算用算术取代了这一切。

其运作方式如下：你承诺在 30 天内达到 99.9% 的可用性。这给你 43 分钟的允许停机时间。每一分钟的实际停机都会从这个预算中扣除。如果你没有发生过任何事故，你还剩 43 分钟预算——你可以承担风险、积极部署、发布可能出问题的东西。如果你已经消耗了 30 分钟，还剩 13 分钟——你应该谨慎行事，也许暂缓那个有风险的迁移。

预算让权衡变得明确。快速交付和打破东西会消耗预算。保守行事则能保留预算。双方都能看到账户余额。

## 错误预算消耗在实践中的运作方式

只要你的 SLI 低于目标，任何时间段都会消耗预算。一次 10 分钟的故障（100% 失败率）会消耗 10 分钟预算。一个 24 小时周期内错误率为 5%（而你的 SLO 允许 0.1% 错误）会消耗：

```
Bad events = total_requests × 0.05
Good events threshold = total_requests × 0.001
Excess bad events = total_requests × 0.049
Budget consumed proportional to 0.049 / 0.001 = 49x your normal budget rate
```

精确计算取决于你的 SLI 定义，但关键洞察是：部分故障消耗预算的速度比看起来更快。一个 30 分钟的错误率升高时段，就可能烧掉一个月的预算。

## 预算能实现什么

错误预算回答了一个此前没有好答案的问题：“我们如何决定何时该放慢速度？”当预算健康时，答案是：“发布。”当预算耗尽时，答案是：“停下来修复可靠性。”没有政治，没有争论——只有预算余额。

这也给了 SRE 团队他们以前没有的杠杆。一个说“这个功能风险太高”的 SRE 可能会被忽视。一个说“我们本月已经消耗了 80% 的错误预算，发布这个有风险的变更将耗尽剩余部分——政策规定我们必须停止”的 SRE，是在提出一个数据驱动的论点，这更难被驳回。

## 共同所有权原则

错误预算不属于 SRE 团队。它属于工程和产品双方。产品拥有预算，因为他们做出的决策（发布功能、偷工减料、快速推进）会消耗它。工程拥有它，因为他们构建的可靠性投资会补充它。当预算作为共享资源、由共同问责来管理时，产品与可靠性之间的对话就会从对抗转向协作。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 错误预算的动机](https://sre.google/sre-book/embracing-risk/#xref_risk-management_motivation-for-error-budgets) -- 类型: 书籍, 时间: 20m
- [错误预算策略 - Google SRE 工作手册](https://sre.google/workbook/error-budget-policy/) -- 类型: 书籍, 时间: 20m
- [错误预算 - Increment 杂志](https://increment.com/reliability/error-budget-approach-to-reliability/) -- 类型: 文章, 时间: 15m

<!-- ZH_UI -->
1. 计算30天内99.9% SLO的错误预算（以分钟计）
2. 解释预算隐喻以及“花费”预算的含义
3. 理解为什么错误预算同时属于产品团队和SRE
4. 描述预算耗尽时会发生什么以及触发什么策略
5. 错误预算如何改变团队实际的工作内容——以及我如何与产品进行这个对话？
6. 我理解这个概念——如果我们正在消耗预算，就应该停止发布功能。但在实践中，当产品有季度承诺时，这很难坚守。我如何把它变成策略，而不是每次都争论？
7. 我的错误预算正在消耗。我如何足够快地发现它，以便真正采取行动？
8. 预算正在被消耗，但我只有在有人手动检查仪表盘时才发现。等我知道时，我们已经烧掉了月度配额的一大块。我需要在燃烧率变高时自动收到通知。
