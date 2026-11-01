---
id: on-call-health
title: Sustainable On-Call
zone: sre
edges:
  to:
    - id: escalation-policies
      question: >-
        When something goes wrong and the on-call engineer can't fix it alone,
        who do they call? What are the actual rules?
      detail: >-
        Last week a P1 went on for 40 minutes because nobody knew whether to
        call the database team or the platform team. We need a clear escalation
        chain so people can ask for help without having to figure it out under
        pressure.
    - id: reliability-roadmap
      question: >-
        The rotation is sustainable. How do I turn this into a real plan for
        improving reliability over time?
      detail: >-
        On-call is healthier now, but I'm still mostly reacting. I want to be
        more systematic — actually prioritising reliability work, tracking
        improvement, making it part of how the team operates permanently.
difficulty: 2
tags:
  - on-call
  - sre
  - burnout
  - alert-fatigue
  - toil
  - rotation
  - sustainability
category: practice
milestones:
  - >-
    Track on-call metrics: alert volume per shift, time-to-resolve, pages
    outside business hours
  - Require every actionable alert to have an associated runbook
  - >-
    Establish a policy: any alert that fires without action for N weeks gets
    deleted or silenced
  - >-
    Design an on-call rotation with reasonable primary/secondary coverage and
    handoff
title_zh: "可持续值班"

---


On-call is necessary. But the version most engineers experience — constant paging, alerts that require no action, being woken at 2 AM for something that could have waited until morning — is a reliability dysfunction as much as a human one. Unsustainable on-call burns out engineers, degrades their decision-making, and ultimately makes systems less reliable. A healthy on-call rotation is one where engineers feel prepared, alerts are meaningful, and the burden is shared fairly.

<!-- DEEP_DIVE -->

## What unhealthy on-call looks like

The signs are recognizable: engineers dread their on-call weeks and count down the days. Alert volume is high enough that people stop acknowledging every page. "Alert fatigue" means important alerts get ignored because everything is treated as background noise. People learn which alerts to ignore without looking at them. Night pages happen regularly — not just for genuine emergencies. The same alerts fire every week, addressed the same way every week, with nobody ever fixing the underlying cause.

These aren't just morale problems. An engineer who's been awake since 3 AM is not making good decisions about complex production systems. Alerting systems that cry wolf mean genuine emergencies get slow responses.

## The principle of actionable alerts

Every alert that pages an engineer should require a decision that only a human can make. If the right response to an alert is always the same automated action, the alert should trigger that action automatically, not page a human. If an alert fires and the engineer always resolves it by running the same two commands, that resolution should be automated.

Questions to ask about every alert:
- When this fires, does it always require immediate human action?
- Is the action always the same? If yes, can it be automated?
- Is the firing threshold calibrated correctly, or does it fire too often or too rarely?
- What would happen if this alert were silenced for 30 days? Would anyone notice?

The last question is harsh but revealing. Many alerts are monitoring internal metrics that nobody actually acts on.

## Alert quality metrics

Track these per on-call rotation:

**Alert volume**: total pages per shift, per week, per engineer. If this is high, something is wrong.

**Alert actionability rate**: what percentage of alerts required immediate human action? Low actionability means high noise.

**Pages outside business hours**: how often are engineers woken up? This should be reserved for genuine emergencies.

**Time to acknowledge and resolve**: slow acknowledgment may indicate the alert isn't clear enough about urgency.

Review these numbers in a monthly on-call retrospective. Identify the noisiest alerts and either fix the underlying issue or raise the threshold.

## Rotation design

A healthy rotation has:

**Primary and secondary coverage**: the primary on-call engineer handles the incident. The secondary provides backup if primary is unavailable or overwhelmed. Escalation should be explicit.

**Reasonable shift lengths**: week-long rotations are common. Avoid shorter rotations (daily) — the cognitive load of context-switching is high. Avoid longer ones (two weeks) — the burden per person gets too heavy.

**Adequate rotation depth**: in a week-on rotation with a five-person team, each person is on-call one week in five. That's a meaningful fraction of their time. Below five people, on-call load becomes unsustainable without automation or on-call budget to hire.

**Clear handoff**: start of on-call is a deliberate handoff, not just a schedule change. Incoming on-call reads the previous week's incidents, reviews any known ongoing issues, and acknowledges the state of the system.

## The toil connection

Most on-call burnout comes from toil: the repetitive, manual work that scales with service incidents. Reducing on-call burden means reducing toil — automating the common responses, fixing the noisy alerts, and addressing the root causes of recurring incidents rather than patching them every week. Sustainable on-call is an engineering project, not just a scheduling problem.

<!-- RESOURCES -->

- [Google SRE Book - Being On-Call](https://sre.google/sre-book/being-on-call/) -- type: book, time: 20m
- [PagerDuty On-Call Best Practices](https://www.pagerduty.com/resources/learn/call-rotations-schedules/) -- type: guide, time: 15m
- [Atlassian On-Call Guide](https://www.atlassian.com/incident-management/on-call) -- type: guide, time: 20m

<!-- ZH_SUMMARY -->
值班是必要的。但大多数工程师所经历的那种值班——持续不断的寻呼、无需采取行动的告警、因为本可以等到早上的事情而在凌晨2点被叫醒——既是一种可靠性失调，也是一种人力失调。不可持续的值班会耗尽工程师的精力，削弱他们的决策能力，最终使系统变得更不可靠。健康的值班轮换应当是工程师感到准备充分、告警有意义、负担被公平分担的轮换。

<!-- ZH_DEEP_DIVE -->
## 不健康的 on-call 是什么样的

这些迹象很容易辨认：工程师害怕自己的 on-call 周，数着日子过。告警量高到人们不再逐条确认每个 page。“告警疲劳”意味着重要告警被忽视，因为所有东西都被当作背景噪音。人们学会了不看内容就知道哪些告警可以忽略。夜间 page 经常发生——不只是真正的紧急情况。同样的告警每周都触发，每周都用同样的方式处理，却从来没有人去修复根本原因。

这些不只是士气问题。一个从凌晨 3 点就醒着的工程师，无法对复杂的生产系统做出好的决策。总是“狼来了”的告警系统，意味着真正的紧急情况会得到迟缓的响应。

## 可执行告警的原则

每一个 page 工程师的告警，都应该要求做出只有人类才能做出的决策。如果对某个告警的正确响应永远是同一个自动化动作，那么这个告警就应该自动触发该动作，而不是 page 一个人。如果某个告警触发后，工程师总是通过运行同样的两条命令来解决，那么这个解决过程就应该被自动化。

对每个告警都要问这些问题：
- 当它触发时，是否总是需要立即的人工操作？
- 操作是否总是相同的？如果是，能否自动化？
- 触发阈值是否校准正确，还是触发得太频繁或太稀少？
- 如果这个告警被静默 30 天，会有人注意到吗？

最后一个问题很尖锐，但很有揭示性。许多告警监控的是内部指标，而实际上没有人会对其采取行动。

## 告警质量指标

按每个 on-call 轮值跟踪这些指标：

**告警量**：每个班次、每周、每个工程师的 page 总数。如果这个数字很高，说明有问题。

**告警可执行率**：有多大比例的告警需要立即的人工操作？可执行率低意味着噪音高。

**非工作时间的 page**：工程师被叫醒的频率有多高？这应该只保留给真正的紧急情况。

**确认和解决时间**：确认缓慢可能表明告警对紧急程度的表达不够清晰。

在每月的 on-call 回顾中审查这些数字。找出最吵的告警，要么修复根本问题，要么提高阈值。

## 轮值设计

健康的轮值具备：

**主备覆盖**：主 on-call 工程师处理事件。备 on-call 在主 on-call 不可用或不堪重负时提供后备支持。升级路径应该明确。

**合理的班次长度**：以周为单位的轮值很常见。避免更短的轮值（每天）——上下文切换的认知负担很高。避免更长的轮值（两周）——每个人的负担会变得太重。

**足够的轮值深度**：在五人团队的一周轮值制中，每个人每五周 on-call 一周。这是他们时间中相当大的一部分。少于五人时，如果没有自动化或用于招聘的 on-call 预算，on-call 负担将变得不可持续。

**清晰的交接**：on-call 的开始是一次刻意的交接，而不仅仅是排班变化。接班的 on-call 阅读上一周的事件，审查任何已知的持续问题，并确认系统的状态。

## 与 toil 的关联

大多数 on-call 倦怠来自 toil：随着服务事件而增长的重复性手工工作。减少 on-call 负担意味着减少 toil——自动化常见响应、修复吵闹的告警，并解决反复发生事件的根因，而不是每周打补丁。可持续的 on-call 是一个工程项目，而不仅仅是排班问题。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 值班](https://sre.google/sre-book/being-on-call/) -- 类型: 书籍, 时长: 20m
- [PagerDuty 值班最佳实践](https://www.pagerduty.com/resources/learn/call-rotations-schedules/) -- 类型: 指南, 时长: 15m
- [Atlassian 值班指南](https://www.atlassian.com/incident-management/on-call) -- 类型: 指南, 时长: 20m

<!-- ZH_UI -->
1. 跟踪值班指标：每班次告警量、解决时长、非工作时间呼叫次数
2. 要求每个可操作告警都关联对应的 runbook
3. 制定策略：任何连续 N 周触发但无需行动的告警将被删除或静默
4. 设计合理的值班轮换，包含主/备覆盖与交接
5. 当出现问题且值班工程师无法独自解决时，他们该联系谁？实际规则是什么？
6. 上周一个 P1 持续了 40 分钟，因为没人知道该联系数据库团队还是平台团队。我们需要清晰的升级链路，让人们能在压力下无需自行判断就能求助。
7. 轮换是可持续的。我如何将其转化为随时间推移持续改进可靠性的实际计划？
8. 值班现在更健康了，但我仍主要是在被动响应。我想更系统化——真正优先安排可靠性工作、跟踪改进、使其永久成为团队运作方式的一部分。
