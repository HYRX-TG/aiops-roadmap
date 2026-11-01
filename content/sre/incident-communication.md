---
id: incident-communication
title: Incident Communication
zone: sre
edges:
  to:
    - id: status-pages
      question: >-
        I need somewhere customers can see what's happening during an incident.
        How do I set that up?
      detail: >-
        Right now customers find out about outages from Twitter or by flooding
        our support inbox. I want a proper status page so they have a reliable
        source of truth — but I don't know how to structure it, what to put on
        it, or how to keep it updated during a chaotic incident.
    - id: post-mortems
      question: >-
        Communications are wrapped up. Now how do we do a proper review of
        what went wrong?
      detail: >-
        We sent the all-clear update and the ticket is closed. But I'm worried
        we're just going to hit the same thing in three months. We need to do a
        real review, but I've been in bad post-mortems before and I don't want
        to repeat that.
difficulty: 2
tags:
  - incident-communication
  - status-page
  - stakeholder-management
  - sre
  - customer-communication
category: practice
milestones:
  - 'Set up a status page (statuspage.io, Cachet, or equivalent)'
  - Write communication templates for common incident severities
  - >-
    Define who owns external communication vs internal communication during an
    incident
  - >-
    Practice the update cadence: communicate every 30 minutes even if there's no
    update
title_zh: "事件沟通"

---


When something breaks, two things need to happen simultaneously: fix it, and communicate about it. These two activities compete for the same people's attention, and if you don't have a system, communication always loses — until a customer tweets about it, your CEO gets a call, and now communication is suddenly a five-alarm fire on top of the original five-alarm fire. Good incident communication is invisible when it works: stakeholders feel informed, responders stay focused, and nobody is blindsided by something they should have known.

<!-- DEEP_DIVE -->

## Internal vs external communication

Internal and external communication have different audiences, different cadences, and different content.

**Internal communication** targets engineering leadership, product, support, and adjacent teams. It's detailed and technical: what's broken, what we're doing about it, what's the current hypothesis, who owns it. The audience needs enough information to make decisions — should we activate the sales customer success team? Should we notify enterprise accounts directly? When will it be fixed so support can tell customers?

**External communication** targets users, customers, and the public. It's plain language, focused on impact and timeline: "We're experiencing issues with checkout. Orders placed between 2:00 PM and 3:15 PM may not have processed. We're working to resolve this and will update in 30 minutes." No technical details. No speculation. No blame.

## The communication cadence

The most important rule: communicate on a schedule, not just when there's something to say. An update every 30 minutes — even if it's "we're still investigating, no new information" — is dramatically better than silence. Silence breeds speculation, escalation, and angry calls to your CEO.

This is why the communications lead role exists. The IC is too busy to also write stakeholder updates. The comms lead owns the update cadence: set a timer, write the update when it fires, send it.

A simple template:

```
[TIME] STATUS UPDATE - Incident [ID]

Current Status: Investigating / Mitigating / Resolved

Impact: [Who is affected and how]
What we know: [One sentence summary of current understanding]
What we're doing: [Current action being taken]
Next update: [In 30 minutes / When we have more information]
```

## Stakeholder mapping

Know in advance who needs to know about incidents of different severities:

| Severity | Notify |
|----------|--------|
| SEV1 | Engineering VP, product, support team lead, customer success (enterprise accounts) |
| SEV2 | Engineering management, product, support team lead |
| SEV3 | Engineering team, support if tickets increasing |
| SEV4 | Engineering team only |

Have this list written down and linked from your incident runbook. Making this decision during an incident is one more thing for the IC to figure out under pressure.

## The all-clear

When the incident resolves, send a final update with:
- Confirmed resolution time
- A brief description of what happened and what fixed it
- The expected post-mortem date (if SEV1/SEV2)

The all-clear is not a post-mortem. Don't include root cause analysis, blame, or detailed technical explanations. That comes later.

<!-- RESOURCES -->

- [PagerDuty Incident Communication](https://response.pagerduty.com/during/communication/) -- type: guide, time: 15m
- [Writing Good Incident Status Updates - Statuspage Blog](https://www.atlassian.com/blog/statuspage/incident-communication-best-practices) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
当故障发生时，有两件事需要同时进行：修复它，并就它进行沟通。这两项活动争夺同一批人的注意力，如果没有一套体系，沟通总是被牺牲——直到客户在推特上发文、你的 CEO 接到电话，此时沟通突然变成叠加在原有紧急状况之上的又一场紧急状况。良好的事故沟通在奏效时是隐形的：利益相关者感到知情，响应者保持专注，没有人会因为本应知道的事情而措手不及。

<!-- ZH_DEEP_DIVE -->
## 内部沟通与外部沟通

内部沟通与外部沟通面向不同的受众，节奏不同，内容也不同。

**内部沟通**面向工程管理层、产品、支持以及相邻团队。内容详细且偏技术：哪里出了问题、我们正在做什么、当前的假设是什么、谁负责。受众需要足够的信息来做决策——我们是否应该启动销售客户成功团队？是否应该直接通知企业客户？什么时候能修复，以便支持团队告知客户？

**外部沟通**面向用户、客户和公众。使用平实的语言，聚焦于影响和时间线：“我们的结账功能出现问题。下午 2：00 至 3：15 之间下的订单可能未处理成功。我们正在努力解决，并将在 30 分钟内更新进展。”不包含技术细节。不做推测。不追究责任。

## 沟通节奏

最重要的规则：按计划沟通，而不是只在有内容可说时才沟通。每 30 分钟一次更新——即使只是“我们仍在调查，暂无新信息”——也远比沉默好得多。沉默会滋生猜测、升级，以及打给你 CEO 的愤怒电话。

这就是沟通负责人这一角色存在的原因。事件指挥官（IC）太忙，无法同时撰写利益相关者更新。沟通负责人负责更新节奏：设好定时器，时间一到就写更新，然后发送。

一个简单的模板：

```
[TIME] STATUS UPDATE - Incident [ID]

Current Status: Investigating / Mitigating / Resolved

Impact: [Who is affected and how]
What we know: [One sentence summary of current understanding]
What we're doing: [Current action being taken]
Next update: [In 30 minutes / When we have more information]
```

## 利益相关者映射

提前明确不同严重级别的事件需要通知谁：

| 严重级别 | 通知对象 |
|----------|--------|
| SEV1 | 工程 VP、产品、支持团队负责人、客户成功（企业客户） |
| SEV2 | 工程管理层、产品、支持团队负责人 |
| SEV3 | 工程团队，若工单增加则通知支持 |
| SEV4 | 仅工程团队 |

将这份清单写下来，并从事件运行手册中链接到它。在事件进行中做这个决定，只会给 IC 增加一项需要在压力下处理的事情。

## 解除警报

事件解决后，发送最终更新，包含：
- 确认的解决时间
- 发生了什么以及什么修复了问题的简要描述
- 预计的事后复盘日期（如果是 SEV1/SEV2）

解除警报不是事后复盘。不要包含根因分析、责任追究或详细的技术解释。那些留到后面。

<!-- ZH_RESOURCES -->
- [PagerDuty 事件沟通](https://response.pagerduty.com/during/communication/) -- 类型：指南，时长：15分钟
- [编写良好的事件状态更新 - Statuspage 博客](https://www.atlassian.com/blog/statuspage/incident-communication-best-practices) -- 类型：文章，时长：10分钟

<!-- ZH_UI -->
1. 搭建状态页面（statuspage.io、Cachet 或同类工具）
2. 为常见事故等级编写沟通模板
3. 明确事故期间外部沟通与内部沟通的负责人
4. 演练更新节奏：即使没有新进展，也每 30 分钟沟通一次
5. 我需要一个让客户在事故期间能看到当前状况的地方。该怎么搭建？
6. 目前客户通过 Twitter 或涌向我们的支持邮箱才得知故障。我想要一个正式的状态页面，让他们有可靠的信息来源——但我不知道如何组织它、上面放什么内容，也不知道在混乱的事故中如何保持更新。
7. 沟通工作已收尾。接下来我们该如何对出错的地方做一次正式复盘？
8. 我们已发出解除警报的更新，工单也已关闭。但我担心三个月后又会遇到同样的问题。我们需要做一次真正的复盘，但我经历过糟糕的事后复盘，不想重蹈覆辙。
