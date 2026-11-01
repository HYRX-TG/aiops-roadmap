---
id: escalation-policies
title: Escalation Policies
zone: sre
edges:
  to:
    - id: incident-management
      question: >-
        Escalation is sorted. But when an incident fires, the response itself
        is still chaotic. What does a structured incident actually look like?
      detail: >-
        I know who to call and when — the escalation tree is clear. But the
        actual incident response still feels like organised chaos. Everyone's
        in a thread, there are duplicate fixes being attempted, nobody's
        tracking what we've tried. The escalation plan assumes we'll hand it
        up cleanly, but I'm not sure we're running the incident well in the
        first place.
    - id: reliability-roadmap
      question: >-
        Escalation is sorted. How do I now build a real plan for improving
        reliability instead of just reacting to incidents?
      detail: >-
        I've fixed the immediate process problems — people know who to call and
        when. But I'm still mostly firefighting. I want to be systematic about
        making reliability improvements, not just better at handling emergencies.
difficulty: 2
tags:
  - escalation
  - on-call
  - incident-response
  - sre
  - paging
  - rotation
category: practice
milestones:
  - Define at least two escalation tiers for your on-call rotation
  - Document who to contact for each type of incident and how
  - Establish time-based escalation — if not acknowledged in N minutes, auto-escalate
  - Understand the difference between escalating for help vs handing off ownership
title_zh: "升级策略"

---


When an incident is serious and the on-call engineer can't fix it alone, they need to know exactly who to call, how to reach them, and under what circumstances. Right now that knowledge is informal — people guess, delay, or ping someone on Slack and hope for the best. An escalation policy is the written, automated answer to "who do I call when I'm stuck?" It exists so that nobody has to figure out escalation procedures while actively fighting an incident.

<!-- DEEP_DIVE -->

## What escalation means

Escalation isn't failure. It's the recognition that a problem requires more expertise, authority, or capacity than the current responder has alone. Escalating quickly is a sign of good incident management. Delaying escalation because you don't want to bother someone, or because you're not sure who to call, extends the incident unnecessarily.

There are two kinds of escalation:

**Help escalation**: the on-call engineer needs additional expertise. The database is behaving strangely and they need someone who knows the database deeply. The network is doing something unexpected and they need a network engineer. This is escalating for knowledge.

**Ownership escalation**: the severity warrants leadership involvement. A SEV1 that's been running for 30 minutes needs an engineering manager in the loop, not because they'll debug it, but because they need situational awareness and may need to make business decisions.

## The escalation chain structure

A standard two-tier escalation chain:

**Tier 1: Primary on-call**. First responder. Handles alerts, owns the incident until resolved or handed off. Typically a rotation of all engineers on the team.

**Tier 2: Secondary on-call / team lead**. Backup if primary is unavailable. Point of escalation if primary has been on the incident for 30 minutes without progress or if the incident reaches a defined severity threshold.

**Tier 3: Engineering management**. Notified for SEV1 incidents. Makes decisions that require business authority. Doesn't debug.

Beyond Tier 3, escalation should be rare — reserved for incidents with major business impact, data loss risk, or security implications.

## Time-based automatic escalation

Human beings are bad at escalating. Pride, uncertainty about severity, desire to solve it themselves — all of these cause delays. Automated escalation removes the decision: if the primary on-call hasn't acknowledged the page within 5 minutes, the secondary is paged automatically. If nobody has acknowledged in 15 minutes, management is notified.

PagerDuty, OpsGenie, and most modern on-call platforms have this built in. Set it up before you need it:

```
Alert fires
  → Page primary on-call
  → If no acknowledgment in 5 minutes: page secondary on-call
  → If no acknowledgment in 15 minutes: page engineering manager
  → If no response in 30 minutes: high-urgency escalation (phone call, not just push notification)
```

## Specialty escalation paths

Beyond the general on-call chain, document escalation for specialty areas:

- **Database incidents**: who owns database infrastructure? How do they prefer to be contacted?
- **Security incidents**: who owns security response? Important: security escalation may need to bypass normal channels to avoid tipping off a potential attacker.
- **Third-party vendor incidents**: does your vendor have an enterprise support line? A dedicated account manager? The number to call needs to be written down, not remembered.

## Escalation vs handoff

Escalation and handoff are different. Escalation means "I need help right now, I'm still the IC." Handoff means "I'm transferring incident ownership to you." When handing off, the outgoing IC must brief the incoming IC: current status, timeline, what's been tried, current hypothesis. The scribe's log makes this briefing possible without relying on memory.

<!-- RESOURCES -->

- [PagerDuty Escalation Policies](https://support.pagerduty.com/docs/escalation-policies-and-schedules) -- type: guide, time: 15m
- [On-Call Escalation Best Practices - Atlassian](https://www.atlassian.com/incident-management/on-call/escalations) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
当事故严重且值班工程师无法独自解决时，他们需要确切知道该联系谁、如何联系以及在什么情况下联系。目前这些知识是非正式的——人们靠猜测、拖延，或者在 Slack 上随便找个人碰运气。升级策略是对“我卡住时该找谁”这一问题的书面化、自动化回答。它的存在是为了让任何人都不必在奋力处理事故的同时还要搞清楚升级流程。

<!-- ZH_DEEP_DIVE -->
## 升级意味着什么

升级不是失败。它意味着认识到某个问题需要比当前响应者独自具备的更多专业知识、权限或能力。快速升级是良好事件管理的标志。因为不想打扰别人，或者因为不确定该找谁而延迟升级，会不必要地延长事件。

升级有两种类型：

**求助升级**：值班工程师需要额外的专业知识。数据库行为异常，他们需要深入了解数据库的人。网络出现了意外情况，他们需要网络工程师。这是为了获取知识而升级。

**归属升级**：严重程度需要领导层参与。一个已经持续 30 分钟的 SEV1 需要工程经理介入，不是因为他们会来调试，而是因为他们需要了解情况，并且可能需要做出业务决策。

## 升级链结构

标准的两级升级链：

**第一级：主值班人员**。第一响应者。处理告警，拥有事件直到解决或移交。通常是团队中所有工程师的轮值。

**第二级：备值班人员 / 团队负责人**。主值班人员不可用时的后备。如果主值班人员已经在事件上处理了 30 分钟没有进展，或者事件达到定义的严重程度阈值，则成为升级点。

**第三级：工程管理层**。SEV1 事件时被通知。做出需要业务权限的决策。不进行调试。

超过第三级，升级应该很少见——保留给具有重大业务影响、数据丢失风险或安全影响的事件。

## 基于时间的自动升级

人类不擅长升级。自尊心、对严重程度的不确定、想要自己解决的愿望——所有这些都会导致延迟。自动升级消除了决策：如果主值班人员没有在 5 分钟内确认寻呼，备值班人员会自动被寻呼。如果 15 分钟内没有人确认，管理层会被通知。

PagerDuty、OpsGenie 和大多数现代值班平台都内置了此功能。在需要之前就设置好：

```
Alert fires
  → Page primary on-call
  → If no acknowledgment in 5 minutes: page secondary on-call
  → If no acknowledgment in 15 minutes: page engineering manager
  → If no response in 30 minutes: high-urgency escalation (phone call, not just push notification)
```

## 专业领域升级路径

除了通用值班链之外，还要记录专业领域的升级方式：

- **数据库事件**：谁负责数据库基础设施？他们希望如何被联系？
- **安全事件**：谁负责安全响应？重要：安全升级可能需要绕过正常渠道，以避免惊动潜在攻击者。
- **第三方供应商事件**：你的供应商是否有企业支持热线？是否有专属客户经理？需要拨打的号码必须写下来，而不是靠记忆。

## 升级与交接

升级和交接是不同的。升级意味着“我现在需要帮助，我仍然是 IC。”交接意味着“我正在将事件所有权转移给你。”交接时， outgoing IC 必须向 incoming IC 简报：当前状态、时间线、已经尝试过什么、当前假设。记录员的日志使这种简报成为可能，而不依赖记忆。

<!-- ZH_RESOURCES -->
- [PagerDuty 升级策略](https://support.pagerduty.com/docs/escalation-policies-and-schedules) -- 类型：指南，时长：15 分钟
- [值班升级最佳实践 - Atlassian](https://www.atlassian.com/incident-management/on-call/escalations) -- 类型：文章，时长：10 分钟

<!-- ZH_UI -->
1. 为你的值班轮换定义至少两个升级层级
2. 记录每种事件类型应联系谁以及如何联系
3. 建立基于时间的升级机制——若在 N 分钟内未确认，则自动升级
4. 理解“为求助而升级”与“移交所有权”之间的区别
5. 升级流程已理顺。但事件触发时，响应本身仍然混乱。结构化的事件处理究竟是什么样的？
6. 我知道该联系谁、何时联系——升级树很清晰。但实际的事件响应仍像是有组织的混乱。所有人都在一个讨论串里，有人在尝试重复的修复，没人跟踪我们试过什么。升级计划假设我们能干净地移交，但我不确定我们一开始就把事件处理好了。
7. 升级流程已理顺。我现在该如何制定真正的可靠性改进计划，而不是仅仅对事件做出反应？
8. 我已经解决了眼前的流程问题——人们知道该联系谁、何时联系。但我仍然主要在救火。我想系统性地推进可靠性改进，而不只是更擅长处理紧急情况。
