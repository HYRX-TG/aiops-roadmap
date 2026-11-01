---
id: error-budgets-in-practice
title: Error Budgets in Practice
zone: sre
edges:
  to:
    - id: reliability-roadmap
      question: >-
        I have a pile of reliability problems to fix. How do I prioritize them
        and make sure they don't just get deprioritized forever?
      detail: >-
        The post-mortem generated eight action items and the error budget
        analysis flagged five more. I don't know which ones matter most, how to
        frame them for planning, or how to stop them from getting pushed to the
        bottom of the backlog every sprint.
difficulty: 2
tags:
  - error-budget
  - slo
  - sre
  - reliability
  - feature-velocity
  - policy
category: practice
milestones:
  - Write an error budget policy document for a service
  - 'Define what happens at 75%, 50%, and 0% remaining budget'
  - Run an error budget review meeting with your team
  - 'Understand why the error budget belongs to the product team, not just SRE'
title_zh: "实践中的错误预算"

---


Understanding error budgets conceptually is one thing. Using them to make actual engineering decisions is another. The budget becomes real when it starts changing what your team works on — when it causes a product conversation, when it stops a risky deployment, when it gives reliability work the priority it needs to actually happen. This node is about turning the theory into a practice your team lives by.

<!-- DEEP_DIVE -->

## Running an error budget review

The budget is only useful if someone looks at it regularly. A monthly error budget review (30 minutes, the whole team including a product stakeholder) should answer three questions:

1. **How much budget did we consume this month, and what consumed it?** Break it down by incident or failure mode. Was it a single bad deployment? Slow infrastructure? Dependency failures? Pattern recognition across months is where the real insights come from.

2. **What's our burn rate trajectory?** Are we improving month-over-month? Is consumption concentrated in a few incidents or spread across many small failures?

3. **What reliability work did we complete, and did it have measurable impact?** Close the loop between engineering investment and measured outcomes.

## Translating incidents into budget terms

When a post-mortem produces action items, not all of them are equally valuable. Budget-aware prioritization asks: "How much of our budget would be recovered if this were fixed?"

An incident that burned 30 minutes of a 43-minute monthly budget is a high-priority item. A bug that causes 1 in 10,000 requests to fail is low-priority unless your request volume is enormous. Frame the reliability work in budget terms and the prioritization becomes data-driven rather than political.

## When budget runs out mid-month

This is the moment the policy either means something or it doesn't. When the budget hits zero:

- Check whether the error budget policy has been signed off by product. If not, have that conversation now — but know you're doing it under pressure, which is the worst time.
- Notify product stakeholders that the feature freeze is in effect per the agreed policy.
- Shift the team's focus to reliability work: fixing the root causes of budget consumption, improving observability, reducing technical debt that caused the incidents.
- Track recovery: when does the 30-day window reset enough that budget starts returning?

The temptation is to treat the budget exhaustion as a one-time anomaly and keep shipping anyway. This is exactly when the policy must hold, or it never will.

## Reliability backlog management

Post-mortems and error budget reviews generate reliability work. That work needs to live somewhere real — in the same backlog that feature work lives in, with real sprint allocation.

A common pattern: reserve 20% of each sprint for reliability work. This isn't heroism — it's a policy. When reliability work is on the backlog alongside features, it competes for attention. When it's siloed into a "reliability sprint" that happens "someday," it never happens.

The error budget gives you the evidence to defend that 20%. When a stakeholder asks why you're fixing infrastructure instead of shipping, the answer is: "We burned 65% of our error budget last month. The policy we agreed on says we invest in reliability until the budget recovers."

<!-- RESOURCES -->

- [Error Budget Policy - Google SRE Workbook](https://sre.google/workbook/error-budget-policy/) -- type: book, time: 20m
- [Implementing SLOs - Google SRE Workbook](https://sre.google/workbook/implementing-slos/) -- type: book, time: 45m

<!-- ZH_SUMMARY -->
从概念上理解错误预算是一回事，用它们做出实际的工程决策则是另一回事。当预算开始改变团队的工作内容时——当它引发产品层面的讨论、叫停高风险部署、让可靠性工作获得真正落地所需的优先级时——预算才变得真实。本节点讲的是把理论转化为团队日常践行的实践。

<!-- ZH_DEEP_DIVE -->
## 执行错误预算评审

预算只有在有人定期关注它时才有用。每月一次的错误预算评审（30 分钟，全体团队成员包括产品相关方参与）应回答三个问题：

1. **本月我们消耗了多少预算，是什么消耗的？** 按事故或故障模式拆解。是单次糟糕的部署？缓慢的基础设施？依赖故障？跨月的模式识别才是真正洞察的来源。

2. **我们的燃烧率轨迹如何？** 我们是否在逐月改善？消耗是集中在少数几次事故中，还是分散在许多小故障上？

3. **我们完成了哪些可靠性工作，是否产生了可衡量的影响？** 闭合工程投入与可衡量结果之间的环路。

## 将事故转化为预算术语

当事后复盘产生行动项时，并非所有行动项都同等有价值。预算感知的优先级排序会问：“如果修复了这个问题，我们能挽回多少预算？”

一次烧掉了 43 分钟月度预算中 30 分钟的事故是高优先级项。一个导致万分之一请求失败的 bug 是低优先级的，除非你的请求量极其庞大。用预算术语来表述可靠性工作，优先级排序就会变得数据驱动，而非政治驱动。

## 当预算在月中耗尽时

这一刻，策略要么有意义，要么毫无意义。当预算归零时：

- 检查错误预算策略是否已由产品方签署确认。如果没有，现在就进行那次对话——但要知道你是在压力下做这件事，而这是最糟糕的时机。
- 通知产品相关方，根据已商定的策略，功能冻结已生效。
- 将团队重心转向可靠性工作：修复预算消耗的根本原因、改进可观测性、减少导致事故的技术债务。
- 跟踪恢复情况：30 天窗口何时重置到足以让预算开始回归？

诱惑在于将预算耗尽视为一次性异常，然后继续交付。而这恰恰是策略必须坚守的时刻，否则它将永远无法坚守。

## 可靠性待办事项管理

事后复盘和错误预算评审会产生可靠性工作。这些工作需要存在于真实的地方——与功能工作相同的待办事项中，有真实的冲刺分配。

一种常见模式：每个冲刺预留 20% 用于可靠性工作。这不是英雄主义——这是策略。当可靠性工作与功能一起出现在待办事项中时，它会争夺注意力。当它被孤立到一个“某天”才发生的“可靠性冲刺”中时，它永远不会发生。

错误预算为你提供了捍卫那 20% 的证据。当相关方问你为什么在修复基础设施而不是交付功能时，答案是：“上个月我们烧掉了 65% 的错误预算。我们商定的策略规定，在预算恢复之前，我们要投资于可靠性。”

<!-- ZH_RESOURCES -->
- [错误预算策略 - Google SRE 工作手册](https://sre.google/workbook/error-budget-policy/) -- 类型: 书籍, 时长: 20分钟
- [实施 SLO - Google SRE 工作手册](https://sre.google/workbook/implementing-slos/) -- 类型: 书籍, 时长: 45分钟

<!-- ZH_UI -->
1. 为服务编写错误预算策略文档
2. 定义剩余预算在 75%、50% 和 0% 时分别会发生什么
3. 与团队召开错误预算评审会议
4. 理解为什么错误预算属于产品团队，而不仅仅是 SRE
5. 我有一堆可靠性问题要修。我该如何排优先级，并确保它们不会一直被无限期搁置？
6. 事后复盘产生了八个行动项，错误预算分析又标出了五个。我不知道哪些最重要、如何在规划中表述它们，也不知道如何阻止它们每个 sprint 都被推到待办列表的最底部。
