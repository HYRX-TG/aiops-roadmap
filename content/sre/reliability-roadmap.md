---
id: reliability-roadmap
title: Reliability Roadmap
zone: sre
edges:
  to:
    - id: dora-metrics
      question: >-
        I have a reliability plan. But how do I measure whether the whole
        engineering org is actually getting better over time?
      detail: >-
        I can track whether individual services improve against their SLOs. But
        I want to know if we're actually improving as an org — are we deploying
        more safely, recovering faster, breaking things less often? I've heard
        about DORA metrics doing this but I don't know how to apply them.
    - id: chaos-engineering
      question: >-
        I've fixed the known problems. But I keep getting surprised by failures
        I didn't predict. How do I find the unknown ones?
      detail: >-
        Every time we fix one thing, the next incident is something completely
        different that we never considered. I want to stop only discovering
        weaknesses when users hit them. Is there a way to find them on purpose
        before that happens?
difficulty: 2
tags:
  - reliability
  - roadmap
  - planning
  - sre
  - post-mortem
  - prioritization
category: practice
milestones:
  - Convert post-mortem action items into properly scoped engineering tasks
  - Prioritize reliability work using error budget consumption data
  - Communicate a reliability investment plan to product stakeholders
  - Build a quarterly reliability review process into your team's rhythm
title_zh: "可靠性路线图"

---


You've fixed the most obvious problems. Incidents are handled better, on-call is more sustainable, there are SLOs on the critical services. Now the question is: how do you make reliability improvement a systematic, ongoing practice rather than a series of reactive fixes? The reliability roadmap is how you translate post-mortem action items, error budget data, and engineering judgment into a prioritized plan that competes on equal footing with feature work.

<!-- DEEP_DIVE -->

## Why reliability work gets deprioritized

Reliability work has a structural disadvantage in product organizations. Feature work produces visible, demonstrable value: a new feature ships, users see it, product celebrates it. Reliability work prevents things from happening — things that, because they didn't happen, nobody notices. The value is invisible until it becomes counterfactual: "we would have had a major outage, but we didn't, because of this investment."

This makes reliability work easy to defer. There's always a feature that seems more urgent. The post-mortem action items stay in the backlog for months, then quarters. The next incident reveals the same underlying weakness that the post-mortem identified nine months ago.

The error budget is your primary tool for changing this dynamic. When the budget is depleting, the argument for reliability investment has quantitative backing.

## Building the reliability roadmap

A reliability roadmap is a time-ordered list of reliability investments, prioritized by expected impact, with clear owners and milestones.

**Step 1: Gather inputs.** Sources of reliability work:
- Post-mortem action items (with severity and recurrence rate)
- Error budget analysis (which failure modes are consuming the most budget?)
- On-call data (which alerts are most frequent? which incidents take longest to resolve?)
- Known technical debt that affects reliability
- Capacity concerns (what will break when traffic doubles?)

**Step 2: Estimate impact.** For each item, ask: "If we fix this, how much error budget do we recover per month?" This is often approximate, but it forces prioritization. A fix that recovers 20% of monthly budget should rank above a fix that recovers 2%.

**Step 3: Communicate with stakeholders.** A reliability roadmap isn't just for the engineering team. Product and engineering leadership should see it and understand the tradeoffs. "If we don't fix the connection pool exhaustion issue, we'll continue burning 30% of our error budget from that single failure mode" is a concrete, compelling argument.

**Step 4: Reserve capacity.** The roadmap only works if there's sprint allocation to execute it. Aim for 20% of engineering capacity on reliability work as a default. Adjust based on error budget consumption.

## Quarterly reliability reviews

Build a quarterly reliability review into your team's rhythm. This is a 60-90 minute meeting with the full team and a product stakeholder. The agenda:

1. Error budget consumption over the quarter: how much did we spend, on what?
2. Reliability investments completed: what did we do, and did it have measurable impact?
3. Incidents and post-mortems: what patterns emerged? What surprised us?
4. Roadmap for next quarter: what reliability investments are we committing to?

The quarterly review is where the reliability roadmap gets updated, socialized, and defended. It creates accountability — commitments made in the review are reviewed in the next one.

## The relationship with DORA metrics

Error budget and SLO data tell you how reliable your services are right now. DORA metrics tell you something different: how efficiently is the engineering organization delivering change, and how reliably is it doing so? The two measurement frameworks complement each other — SLOs answer "are we reliable?" while DORA answers "are we improving?"

<!-- RESOURCES -->

- [Google SRE Workbook - Setting Up a Reliability Practice](https://sre.google/workbook/reaching-beyond-your-first-sre-team/) -- type: book, time: 30m
- [Prioritizing Reliability Work - Google SRE Workbook](https://sre.google/workbook/error-budget-policy/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
你已经解决了最明显的问题。事故处理更好了，on-call 更可持续了，关键服务也有了 SLO。现在的问题是：如何让可靠性改进成为系统化、持续性的实践，而不是一系列被动修复？可靠性路线图正是你用来将事后复盘行动项、错误预算数据和工程判断转化为一份优先级计划的方式，使其能够与功能开发工作平等竞争。

<!-- ZH_DEEP_DIVE -->
## 为什么可靠性工作会被降级

可靠性工作在产品组织中存在结构性劣势。功能开发产生可见、可演示的价值：新功能上线，用户看到它，产品团队为此庆祝。可靠性工作则是防止事情发生——而这些事情因为没发生，所以没人注意到。其价值在成为反事实之前是不可见的：“我们本会发生一次重大故障，但没有，正是因为这项投入。”

这使得可靠性工作很容易被推迟。总有一个功能看起来更紧急。事后复盘的行动项在待办列表中停留数月，然后数个季度。下一次事故揭示了九个月前复盘所发现的同一个底层弱点。

错误预算是你改变这一动态的主要工具。当预算持续消耗时，可靠性投入的论点就有了量化支撑。

## 构建可靠性路线图

可靠性路线图是按时间排序的可靠性投入清单，按预期影响排序，并有明确的负责人和里程碑。

**第 1 步：收集输入。** 可靠性工作的来源：
- 事后复盘行动项（含严重程度和复发率）
- 错误预算分析（哪些故障模式消耗了最多预算？）
- 值班数据（哪些告警最频繁？哪些事故解决耗时最长？）
- 影响可靠性的已知技术债务
- 容量担忧（流量翻倍时什么会崩溃？）

**第 2 步：估算影响。** 对每一项，问：“如果我们修复这个，每月能恢复多少错误预算？”这通常是近似值，但它强制进行优先级排序。一个能恢复每月预算 20% 的修复应排在一个只能恢复 2% 的修复之上。

**第 3 步：与利益相关者沟通。** 可靠性路线图不只是给工程团队看的。产品和工程领导层应看到它并理解其中的权衡。“如果我们不修复连接池耗尽问题，我们将继续因这单一故障模式消耗 30% 的错误预算”是一个具体且有说服力的论点。

**第 4 步：预留容量。** 路线图只有在有冲刺分配来执行时才有效。默认目标是将 20% 的工程容量用于可靠性工作。根据错误预算消耗情况调整。

## 季度可靠性评审

将季度可靠性评审纳入团队节奏。这是一次 60-90 分钟的会议，全体团队和一位产品利益相关者参加。议程：

1. 本季度错误预算消耗：我们花了多少，花在什么上？
2. 已完成的可靠性投入：我们做了什么，是否产生了可衡量的影响？
3. 事故与事后复盘：出现了哪些模式？什么让我们意外？
4. 下季度路线图：我们承诺进行哪些可靠性投入？

季度评审是更新、宣导和捍卫可靠性路线图的场合。它建立了问责制——评审中做出的承诺会在下一次评审中被回顾。

## 与 DORA 指标的关系

错误预算和 SLO 数据告诉你服务当前的可靠性。DORA 指标告诉你不同的东西：工程组织交付变更的效率如何，以及交付的可靠性如何？这两个度量框架相辅相成——SLO 回答“我们可靠吗？”，而 DORA 回答“我们在改进吗？”

<!-- ZH_RESOURCES -->
- [Google SRE 工作手册 - 建立可靠性实践](https://sre.google/workbook/reaching-beyond-your-first-sre-team/) -- 类型：书籍，时长：30分钟
- [确定可靠性工作的优先级 - Google SRE 工作手册](https://sre.google/workbook/error-budget-policy/) -- 类型：书籍，时长：20分钟

<!-- ZH_UI -->
1. 将事后复盘的行动项转化为范围明确的工程任务
2. 利用错误预算消耗数据来排定可靠性工作的优先级
3. 向产品相关方沟通可靠性投入计划
4. 将季度可靠性评审流程纳入团队节奏
5. 我有可靠性计划。但如何衡量整个工程组织是否真的在随时间变好？
6. 我能跟踪单个服务是否在其 SLO 上有所改善。但我想知道我们作为一个组织是否真的在进步——我们是否在更安全地部署、更快地恢复、更少地出故障？我听说过 DORA 指标能做到这一点，但不知道如何应用。
7. 我已经修复了已知问题。但我总是被自己没预料到的故障打个措手不及。如何找到那些未知的问题？
8. 每次我们修好一件事，下一次故障就是完全不同的、我们从未考虑过的事情。我想停止只在用户撞上弱点时才发现它们。有没有办法在那之前主动找到它们？
