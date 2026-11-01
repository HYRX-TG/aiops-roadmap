---
id: service-level-agreements
title: Service Level Agreements
zone: sre
edges:
  to:
    - id: service-level-objectives
      question: >-
        SLAs are what I promise externally. How do I make sure my internal
        targets are tight enough that I never break that promise?
      detail: >-
        We've committed 99.9% uptime to customers in a contract. But I don't
        know how that number was chosen or how I'd know if we're violating it.
        And now the database team wants to know what uptime I need from them —
        is that also an SLA? I'm not sure where the contract ends and the
        engineering target begins.
difficulty: 1
tags:
  - sla
  - sre
  - reliability
  - contracts
  - customer-commitments
  - internal-sla
category: concept
milestones:
  - Explain the difference between an SLA, an SLO, and an SLI
  - Understand why your SLO should be stricter than your SLA
  - Know what happens operationally when you breach an SLA
  - Identify internal team SLAs in your own organisation and whether they're written down
title_zh: "服务等级协议"

---


An SLA is a promise — usually written into a contract — about how reliable your service will be and what happens when it isn't. Enterprise customers ask for them. Sales teams commit to them. Legal drafts them. And then it falls to engineering to actually meet them. Understanding what SLAs actually commit you to, and how they relate to your internal engineering targets, is essential before you can make promises you can keep.

<!-- DEEP_DIVE -->

## What an SLA actually is

An SLA (Service Level Agreement) is a contract between a service provider and a customer that defines the level of service expected. It typically specifies:

- **The metric**: what's being measured ("API availability", "response time")
- **The target**: the minimum acceptable level ("99.9% uptime per calendar month")
- **The remedy**: what happens if you miss it (service credits, refunds, contract termination rights)

The remedy is what makes an SLA different from an SLO. An SLO is a target you set for yourself. An SLA is a commitment to someone else — with consequences.

## Why your SLO must be stricter than your SLA

This is the most important practical relationship between SLAs and SLOs: your internal target needs to be meaningfully higher than your external commitment.

If you commit 99.9% availability to customers in your SLA, your engineering team needs an SLO of 99.95% or better. Why? Because when you notice you're approaching the SLA breach threshold, you need time to react and recover before the breach becomes a financial and legal problem. The gap between your SLO and your SLA is your safety margin.

If your SLO equals your SLA, you'll discover you're breaching the SLA at the same moment you discover you're missing your internal target — which is already too late.

## Internal SLAs

Not all SLAs are customer-facing. Internal teams make commitments to each other too, even if they're not called SLAs. When your database team tells the checkout team "our database will be available 99.9% of the time," that's effectively an internal SLA. When the platform team says "we'll deploy your changes within one hour of a merge," that's a commitment.

The difference from external SLAs is the remedy. Missing an internal SLA usually means a conversation, a post-mortem, and pressure to improve — not financial penalties. But they should still be written down, agreed to explicitly, and tracked. Informal agreements are invisible when they're being violated.

## What actually happens when you breach an SLA

Different SLAs have different remedies, but the common pattern is service credits — if availability drops below the committed level, the customer gets a percentage of their monthly bill back. For enterprise contracts, the credits can be substantial. For SaaS businesses, repeated breaches can trigger contract termination clauses.

Beyond the financial impact, there's the trust impact. Customers who've been burned by availability breaches start building contingency plans. They reduce their dependency on you. They tell other potential customers. The damage to the relationship is usually more costly than the credit itself.

<!-- RESOURCES -->

- [Google SRE Book - Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) -- type: book, time: 30m
- [How to Write Good SLAs - PagerDuty Blog](https://www.pagerduty.com/blog/sla-slo-sli/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
SLA 是一种承诺——通常写入合同——关于你的服务将有多可靠，以及当服务未达到该可靠性时会发生什么。企业客户会要求 SLA。销售团队会对其作出承诺。法务团队会起草它们。然后，实际满足这些承诺就落到了工程团队的肩上。在你能够做出可兑现的承诺之前，理解 SLA 实际让你承诺了什么，以及它们与内部工程目标之间的关系，是至关重要的。

<!-- ZH_DEEP_DIVE -->
## SLA 究竟是什么

SLA（Service Level Agreement，服务等级协议）是服务提供商与客户之间的合同，定义了预期的服务水平。它通常规定：

- **指标**：衡量的是什么（“API 可用性”“响应时间”）
- **目标**：可接受的最低水平（“每个自然月 99.9% 的正常运行时间”）
- **补救措施**：未达标时会发生什么（服务抵扣、退款、合同终止权）

补救措施正是 SLA 与 SLO 的区别所在。SLO 是你为自己设定的目标。SLA 是对他人的承诺——并且带有后果。

## 为什么你的 SLO 必须比 SLA 更严格

这是 SLA 与 SLO 之间最重要的实践关系：你的内部目标需要显著高于你的对外承诺。

如果你在 SLA 中向客户承诺 99.9% 的可用性，你的工程团队就需要 99.95% 或更高的 SLO。为什么？因为当你发现正在接近 SLA 违约阈值时，你需要在违约变成财务和法律问题之前有时间做出反应并恢复。SLO 与 SLA 之间的差距就是你的安全边际。

如果你的 SLO 等于你的 SLA，你会发现自己违反 SLA 的那一刻，正是你发现自己未达内部目标的那一刻——而那时已经太晚了。

## 内部 SLA

并非所有 SLA 都是面向客户的。内部团队之间也会相互做出承诺，即使它们不叫 SLA。当你的数据库团队告诉结账团队“我们的数据库将有 99.9% 的时间可用”时，这实际上就是一个内部 SLA。当平台团队说“我们会在合并后一小时内部署你的变更”时，这也是一项承诺。

与外部 SLA 的区别在于补救措施。未达内部 SLA 通常意味着一次沟通、一次复盘，以及改进的压力——而不是经济处罚。但它们仍然应该被写下来、明确达成一致并加以跟踪。非正式的约定在被违反时是看不见的。

## 违反 SLA 时实际会发生什么

不同的 SLA 有不同的补救措施，但常见的模式是服务抵扣——如果可用性低于承诺水平，客户会获得月度账单一定比例的返还。对于企业合同，抵扣金额可能相当可观。对于 SaaS 业务，反复违约可能触发合同终止条款。

除了财务影响之外，还有信任影响。曾被可用性违约伤害过的客户会开始制定应急计划。他们会减少对你的依赖。他们会告诉其他潜在客户。对关系的损害通常比抵扣本身代价更高。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 服务等级目标](https://sre.google/sre-book/service-level-objectives/) -- 类型: 书籍, 时间: 30分钟
- [如何编写优秀的 SLA - PagerDuty 博客](https://www.pagerduty.com/blog/sla-slo-sli/) -- 类型: 文章, 时间: 10分钟

<!-- ZH_UI -->
1. 解释 SLA、SLO 和 SLI 之间的区别
2. 理解为什么你的 SLO 应该比 SLA 更严格
3. 了解违反 SLA 时运维层面会发生什么
4. 找出你所在组织内部的团队 SLA，以及它们是否被书面记录
5. SLA 是我对外承诺的内容。我如何确保内部目标足够严格，从而永远不会违背这个承诺？
6. 我们在合同中向客户承诺了 99.9% 的正常运行时间。但我不知道这个数字是如何选定的，也不知道如何判断我们是否在违反它。现在数据库团队想知道我需要他们提供多少正常运行时间——那也算 SLA 吗？我不确定合同在哪里结束、工程目标在哪里开始。
