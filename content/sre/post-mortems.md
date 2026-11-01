---
id: post-mortems
title: Blameless Post-Mortems
zone: sre
edges:
  to:
    - id: error-budgets-in-practice
      question: >-
        The post-mortem is done. But now I have to explain to the product team
        why we need to slow down on features.
      detail: >-
        The action items are written and everyone nodded in the meeting. But
        half of them are reliability investments that compete directly with the
        feature roadmap, and product is pushing back. How do I make this a data
        conversation instead of a political one?
difficulty: 2
tags:
  - post-mortem
  - blameless
  - sre
  - incident-review
  - learning
  - reliability
category: practice
milestones:
  - >-
    Write a post-mortem for a real or simulated incident using a standard
    template
  - Identify contributing factors without assigning individual blame
  - >-
    Generate action items with owners and deadlines — not vague 'we should
    improve X'
  - Run a post-mortem review meeting and publish the document internally
title_zh: "无责事后复盘"

---


A post-mortem is a structured review of an incident whose purpose is to understand what happened well enough to prevent the next one. The word "blameless" is crucial: the goal is to understand why the system and the process failed, not to identify who made a mistake. This distinction sounds simple but is genuinely hard to maintain under organizational pressure, especially after expensive incidents. Getting post-mortems right is one of the highest-leverage practices in reliability engineering.

<!-- DEEP_DIVE -->

## Why blameless?

When individuals are blamed for incidents, two things happen: they stop admitting mistakes, and they stop sharing information. Both make the system less safe. A culture where engineers fear consequences for mistakes is a culture that produces less reliable systems — because you can't fix problems you can't talk about.

The blameless approach, pioneered by organizations like Etsy, Airbnb, and Google, treats incidents as symptoms of system-level failures rather than individual failures. The right question isn't "who caused the outage?" but "what series of conditions made it possible for this error to have this impact?" An engineer who made a mistake is almost always acting rationally given the information and tools available to them. The system created the conditions for the mistake.

This doesn't mean no accountability. It means accountability is directed at fixing the system, not punishing the individual.

## The post-mortem template

A good post-mortem document answers these questions:

**Summary**: What happened, when, what was the user impact, and what was the resolution? One paragraph. This should be readable by non-technical stakeholders.

**Timeline**: Timestamped events from the start of the incident to resolution. Pulled from the scribe's log during the incident. Include detection, declaration, key diagnostic events, resolution.

**Root cause**: What was the underlying cause? Not just the proximate cause (the deployment that broke things) but the contributing causes (why was that config change possible, why wasn't it caught in testing, why did it reach production, why did it take 40 minutes to diagnose).

**Contributing factors**: The system conditions that allowed the root cause to have the impact it did. Lack of monitoring. Incomplete testing. Unclear ownership. Complex deployment process. These are the things to fix.

**Action items**: Specific, scoped, assigned engineering tasks that address the contributing factors. Not "improve monitoring" (vague, unassignable) but "Add alert when connection pool utilization exceeds 80% (owner: X, due: Y date)."

**What went well**: Deliberately include what worked. Good incident coordination, fast detection, a runbook that helped — these deserve acknowledgment and reinforce the practices you want to keep.

## The five whys technique

When digging into root cause, ask "why" five times, each time going deeper:

1. Why did checkout fail? → Database connection pool exhausted.
2. Why did the pool exhaust? → New deployment added a feature that opened extra connections per request.
3. Why wasn't this caught? → No connection pool monitoring, and the load test didn't simulate enough concurrent users.
4. Why didn't load testing catch it? → Load tests run against a separate environment that has a larger pool configured.
5. Why is the pool size different in that environment? → Config drift — nobody audited the test environment against production.

Each "why" gets closer to a system-level fix. The action items follow from level 4 and 5: fix config drift, add connection pool monitoring, update load test environment.

## Sharing post-mortems

Post-mortems are most valuable when they're shared broadly — within the team, across engineering, sometimes publicly. The information in a post-mortem helps others avoid similar failures in their systems. A culture of open post-mortems is a culture that learns. A culture of post-mortems as private shame is a culture that repeats mistakes.

Many companies now publish post-mortems externally for major incidents. This is a trust-building move: it shows customers that when things break, you investigate seriously and take action.

<!-- RESOURCES -->

- [Google SRE Book - Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) -- type: book, time: 20m
- [Blameless Post-Mortem Template - PagerDuty](https://postmortems.pagerduty.com/) -- type: guide, time: 15m
- [Etsy's Blameless Post-Mortems - John Allspaw](https://www.etsy.com/codeascraft/blameless-postmortems/) -- type: article, time: 15m
- [Awesome Post-Mortems - Collection of real examples](https://github.com/danluu/post-mortems) -- type: reference, time: varies

<!-- ZH_SUMMARY -->
事后复盘（post-mortem）是对一次事故的结构化回顾，其目的是充分理解发生了什么，从而防止下一次事故的发生。“无责”（blameless）一词至关重要：目标是理解系统和流程为何失败，而不是找出谁犯了错误。这一区分听起来简单，但在组织压力下，尤其是在代价高昂的事故之后，确实很难坚持。做好事后复盘是可靠性工程中杠杆率最高的实践之一。

<!-- ZH_DEEP_DIVE -->
## 为什么需要无责文化？

当个人因事故被指责时，会发生两件事：他们不再承认错误，也不再分享信息。这两者都会让系统变得更不安全。如果工程师因为犯错而害怕承担后果，这种文化就会导致系统可靠性降低——因为你无法修复自己不敢谈论的问题。

无责文化方法由 Etsy、Airbnb 和 Google 等组织率先实践，它将事故视为系统级故障的症状，而非个人的失败。正确的问题不是“谁导致了这次宕机？”，而是“是什么样的条件组合让这个错误造成了如此影响？”一个犯了错的工程师，在可获得的信息和工具下，几乎总是做出了理性的行为。是系统创造了犯错的条件。

这并不意味着没有问责。它意味着问责指向修复系统，而非惩罚个人。

## 事后复盘模板

一份好的事后复盘文档回答以下问题：

**摘要**：发生了什么、何时发生、对用户的影响是什么、如何解决的？一段话。应让非技术相关方也能读懂。

**时间线**：从事故开始到解决的时间戳事件记录。取自事故期间记录员的日志。包括检测、宣告、关键诊断事件、解决。

**根因**：底层原因是什么？不仅是直接原因（导致故障的部署），还包括促成原因（为什么那个配置变更成为可能，为什么测试没有捕获，为什么它进入了生产环境，为什么诊断花了 40 分钟）。

**促成因素**：让根因产生如此影响的系统条件。缺乏监控。测试不完整。归属不清。部署流程复杂。这些才是需要修复的东西。

**行动项**：具体、有范围、已分配的工程任务，针对促成因素。不是“改进监控”（模糊、无法分配），而是“当连接池利用率超过 80% 时添加告警（负责人：X，截止日期：Y）”。

**做得好的地方**：刻意记录哪些方面做得好。良好的事故协调、快速检测、起了作用的运行手册——这些都值得肯定，并能强化你希望保持的实践。

## 五个为什么技术

在深挖根因时，问五次“为什么”，每次更深入一层：

1. 为什么结账失败？→ 数据库连接池耗尽。
2. 为什么连接池耗尽？→ 新部署添加了一个功能，每个请求会打开额外连接。
3. 为什么没被发现？→ 没有连接池监控，且负载测试没有模拟足够的并发用户。
4. 为什么负载测试没捕获？→ 负载测试运行在单独环境中，该环境配置了更大的连接池。
5. 为什么那个环境的连接池大小不同？→ 配置漂移——没有人将测试环境与生产环境进行审计对比。

每个“为什么”都更接近系统级修复。行动项来自第 4 层和第 5 层：修复配置漂移、添加连接池监控、更新负载测试环境。

## 分享事后复盘

事后复盘在广泛分享时最有价值——在团队内、跨工程部门、有时公开。事后复盘中的信息帮助他人在自己的系统中避免类似故障。开放的事后复盘文化是一种学习文化。将事后复盘视为私下羞耻的文化是一种重复犯错的文化。

许多公司现在会对外发布重大事故的事后复盘。这是一种建立信任的举措：它向客户表明，当事情出问题时，你会认真调查并采取行动。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 事后复盘文化](https://sre.google/sre-book/postmortem-culture/) -- 类型: 书籍, 时长: 20m
- [无责事后复盘模板 - PagerDuty](https://postmortems.pagerduty.com/) -- 类型: 指南, 时长: 15m
- [Etsy 的无责事后复盘 - John Allspaw](https://www.etsy.com/codeascraft/blameless-postmortems/) -- 类型: 文章, 时长: 15m
- [Awesome Post-Mortems - 真实案例合集](https://github.com/danluu/post-mortems) -- 类型: 参考, 时长: 不定

<!-- ZH_UI -->
1. 使用标准模板为真实或模拟事故撰写事后复盘
2. 识别促成因素，不追究个人责任
3. 生成带有负责人和截止日期的行动项——而不是含糊的“我们应该改进 X”
4. 召开事后复盘评审会议并在内部发布文档
5. 事后复盘已完成。但现在我必须向产品团队解释为什么我们需要放缓功能开发。
6. 行动项已写好，会上大家都点头同意。但其中一半是与功能路线图直接竞争的可靠性投入，产品团队正在抵制。我如何让这成为一场数据对话而不是政治对话？
