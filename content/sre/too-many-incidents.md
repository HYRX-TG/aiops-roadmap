---
id: too-many-incidents
title: Too Many Incidents
zone: sre
edges:
  to:
    - id: incident-roles
      question: >-
        When an incident is happening and everyone's panicking, how do I
        bring some structure to it?
      detail: >-
        Last week three people were all making changes at once, nobody knew
        who was driving, and we made things worse before we got better. I know
        there's a more organised way to handle this but I've never seen it done
        properly. What does good incident response actually look like from the
        inside?
    - id: on-call-health
      question: >-
        Before we talk about running incidents better — the on-call rotation
        itself is broken. People are burning out. Where do I fix that first?
      detail: >-
        Half the incidents feel bad because the on-call experience is already
        miserable before anything even breaks. We're getting paged for things
        that don't matter, ignoring things that do because we've been
        desensitised, and nobody wants to be on rotation. I'm not sure fixing
        the incident process helps if the alerts and the rotation are the
        real problem.
difficulty: 1
tags:
  - incidents
  - sre
  - incident-management
  - reliability
  - on-call
  - firefighting
category: concept
milestones:
  - Identify the patterns that make incident response chaotic vs effective
  - Understand what distinguishes a high-performing incident response team
  - Know the difference between an incident and a bug or maintenance task
  - Recognise the signs that your organisation's incident management is broken
title_zh: "事件过多"

---


There's a difference between incidents and chaos. Every production system will have incidents — unexpected failures, degraded performance, bugs that slip through review. The question isn't whether you'll have incidents, but whether you have a process for handling them that doesn't make things worse. Right now, the process is chaos: no clear owner, multiple people making changes simultaneously, no one knowing the current status, and every incident feeling like the first time you've ever dealt with one.

<!-- DEEP_DIVE -->

## What makes incident response chaotic

There are predictable patterns in dysfunctional incident response:

**No declaration threshold.** Teams debate "is this really an incident?" while the situation deteriorates. Users are affected. The on-call engineer spends ten minutes figuring out if they should escalate while the damage accumulates.

**No single owner.** Everyone joins the call. Multiple people make changes to the same system simultaneously. Someone rolls back a deployment. Someone else changes a config. Nobody knows what changed or in what order. Debugging becomes impossible because the system state is constantly shifting.

**Communication collapse.** Engineering leadership is messaging the on-call engineer for status updates while they're trying to debug. Support is forwarding customer messages. Developers are asking questions in Slack. The person best positioned to fix the problem can't focus because everyone wants a status update.

**No timeline.** Nobody is writing down what happened, what was tried, what the current hypothesis is. When a second engineer joins to help, they have to be briefed from memory while the first engineer continues debugging. Information is lost. The same things get tried twice.

## What high-performing incident response looks like

The best incident responses feel controlled even when the situation is serious. The key characteristics:

One person is clearly in charge and making decisions. Others are executing, investigating, or communicating — not also deciding. There's a written log of what's happened and what's been tried. Stakeholders are getting updates on a predictable cadence, which means they're not interrupting the responders to ask for them. The diagnosis is happening systematically: form a hypothesis, test it, eliminate it or confirm it, move to the next.

High-performing teams also have a clear definition of what an incident is. Not every alert is an incident. Not every bug is an incident. An incident is a situation that's actively degrading user experience and requires coordinated response. Knowing when to declare one — and to do so quickly — is itself a skill.

## The cost of bad incident response

Poor incident response has compounding costs. The direct cost is longer resolution time — every minute of unclear ownership is a minute of additional user impact. The indirect cost is engineer burnout: chaotic incidents are stressful in a way that orderly incidents aren't. Engineers who dread every page start avoiding on-call, making the rotation worse for everyone.

There's also a learning cost. Chaotic incidents don't produce actionable post-mortems. When nobody knows exactly what happened, what was tried, or why it worked, the only lesson is "that was bad." You can't improve what you can't understand.

<!-- RESOURCES -->

- [Incident Management for Operations - O'Reilly](https://www.oreilly.com/library/view/incident-management-for/9781491917541/) -- type: book, time: varies
- [PagerDuty Incident Response Guide](https://response.pagerduty.com/) -- type: guide, time: 1h
- [Google SRE Book - Emergency Response](https://sre.google/sre-book/emergency-response/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
事故与混乱是有区别的。每个生产系统都会发生事故——意外故障、性能下降、通过评审的 bug。问题不在于是否会发生事故，而在于你是否有处理事故的流程，且该流程不会让情况变得更糟。目前，流程就是混乱：没有明确的负责人，多人同时进行变更，没有人知道当前状态，每次事故都感觉像是第一次处理一样。

<!-- ZH_DEEP_DIVE -->
## 是什么让事件响应变得混乱

功能失调的事件响应中存在可预测的模式：

**没有声明阈值。** 团队在争论“这真的是一个事件吗？”的同时，情况在恶化。用户在受影响。值班工程师花十分钟琢磨自己是否应该升级，而损害在累积。

**没有单一负责人。** 所有人都加入通话。多个人同时对同一系统做变更。有人回滚了部署。另一个人改了配置。没人知道改了什么、按什么顺序改的。调试变得不可能，因为系统状态在不断变化。

**沟通崩溃。** 工程领导层不断给值班工程师发消息要状态更新，而后者正试图调试。支持团队在转发客户消息。开发人员在 Slack 里提问。最有能力解决问题的人无法专注，因为所有人都想要状态更新。

**没有时间线。** 没人在记录发生了什么、尝试了什么、当前假设是什么。当第二位工程师加入帮忙时，必须凭记忆向他简报，而第一位工程师继续调试。信息丢失了。同样的事情被尝试了两次。

## 高绩效的事件响应是什么样的

最好的事件响应即使在情况严重时也感觉受控。关键特征：

一个人明确负责并做决策。其他人在执行、调查或沟通——而不是同时做决策。有一份关于发生了什么、尝试了什么的书面记录。利益相关者按可预测的节奏获得更新，这意味着他们不会打断响应者来索取更新。诊断在系统性地进行：形成假设、验证它、排除或确认它、进入下一个。

高绩效团队还对什么是事件有清晰的定义。不是每个告警都是事件。不是每个 bug 都是事件。事件是正在主动损害用户体验、需要协调响应的情况。知道何时声明事件——并且快速声明——本身就是一项技能。

## 糟糕事件响应的代价

糟糕的事件响应有复合成本。直接成本是更长的解决时间——每一分钟归属不清，就是多一分钟的用户影响。间接成本是工程师倦怠：混乱的事件带来的压力是有序事件所没有的。害怕每一次告警的工程师开始逃避值班，让轮值对所有人都更糟。

还有学习成本。混乱的事件不会产生可执行的复盘。当没人确切知道发生了什么、尝试了什么、为什么奏效时，唯一的教训就是“那很糟糕”。你无法改进你无法理解的东西。

<!-- ZH_RESOURCES -->
- [运维事件管理 - O'Reilly](https://www.oreilly.com/library/view/incident-management-for/9781491917541/) -- 类型: 书籍, 时长: 不定
- [PagerDuty 事件响应指南](https://response.pagerduty.com/) -- 类型: 指南, 时长: 1小时
- [Google SRE 手册 - 应急响应](https://sre.google/sre-book/emergency-response/) -- 类型: 书籍, 时长: 20分钟

<!-- ZH_UI -->
1. 识别导致事件响应混乱与高效的不同模式
2. 理解高效事件响应团队的独特之处
3. 了解事件与缺陷或维护任务之间的区别
4. 识别组织事件管理已失效的迹象
5. 当事件正在发生、所有人都在恐慌时，我该如何引入一些结构？
6. 上周三个人同时在做变更，没人知道谁在主导，情况在好转之前先变得更糟了。我知道有更有条理的处理方式，但我从没见过正确执行的样子。从内部来看，好的事件响应究竟是什么样的？
7. 在我们讨论如何更好地运行事件之前——值班轮换本身就已经坏了。人们在 burnout。我应该先从哪里着手修复？
8. 一半的事件让人感觉糟糕，是因为在出问题之前值班体验就已经很痛苦了。我们被无关紧要的事情呼叫，因为已经麻木而忽略了真正重要的事情，而且没人愿意值班。如果告警和轮换才是真正的问题，我不确定修复事件流程是否有帮助。
