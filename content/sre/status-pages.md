---
id: status-pages
title: Status Pages
zone: sre
edges:
  to:
    - id: post-mortems
      question: >-
        The incident is over and the status page is updated. Now how do we
        actually learn from what happened?
      detail: >-
        We posted the all-clear and customers know things are back to normal.
        But we closed the ticket without really digging into why it happened.
        I've promised customers a post-incident review — how do I run one that
        actually produces something useful rather than just documenting the
        timeline?
difficulty: 1
tags:
  - status-page
  - incident-communication
  - customer-communication
  - transparency
  - sre
category: practice
milestones:
  - Set up a public status page for your service
  - Write communication templates for common incident severities
  - Establish who owns updating the status page during an incident
  - Practice updating the status page during a non-critical incident
title_zh: "状态页面"

---


Right now, when your service goes down, customers find out from Twitter, from their own users filing support tickets, or from their own dashboards going red. They have no reliable place to check what's happening and whether you know about it. A status page gives them that: a single, always-available source of truth about your service's current status and any ongoing incidents. Done well, it reduces support volume, sets expectations, and signals that you're operating with transparency.

<!-- DEEP_DIVE -->

## What a status page is not

A status page is not a dashboard for internal teams. It's not a replacement for your internal monitoring or alerting. It's an outward-facing communication channel for customers who don't have access to your systems but need to know whether to trust them right now.

The design principle: a customer checking your status page should get a clear, jargon-free answer to the question "is this service working?" without needing any technical knowledge to interpret it.

## What to put on it

**Current status for each major component.** Break your service into meaningful user-facing components — not by internal service name, but by what users actually interact with: "Dashboard", "API", "Billing", "Mobile App". Show the status of each: Operational / Degraded Performance / Partial Outage / Major Outage.

**Incident timeline.** When an incident is in progress, provide timestamped updates in plain language:
- "2:15 PM — We're investigating elevated error rates on the API."
- "2:45 PM — We've identified the cause: a misconfigured deployment rolled out at 2:00 PM. Rollback in progress."
- "3:10 PM — Service has recovered. Error rates are back to normal."

**Historical incidents.** Show past incidents and how they were resolved. This builds trust. A service with no incident history looks suspicious, not reliable.

## Hosted vs self-hosted

**Atlassian Statuspage** — the industry standard. Integrates with PagerDuty, Datadog, and most monitoring tools for automatic status updates. Has a free tier. Powers status pages for Slack, GitHub, Stripe, and thousands of other services.

**Cachet** — open-source, self-hosted alternative. Requires your own infrastructure — which creates a problem: your status page might be down when your service is down.

If you're self-hosting, make absolutely sure the status page runs on infrastructure isolated from the service it reports on. A status page that goes down with the service is useless at the exact moment it's needed most.

## Automation vs manual updates

The best status pages combine both. Automated components update green/yellow/red based on monitoring signals. Incident communications are written by humans because they require context and judgment.

A common pattern: set up automated component status updates from your monitoring (if API error rate exceeds threshold, automatically flip "API" to "Degraded Performance"). Write manual incident updates explaining what's happening and what you're doing.

## Prepare templates in advance

Writing clear communication under pressure is hard. Prepare templates before you need them:

```
Investigating: We are aware of issues affecting [component].
Our team is currently investigating. Next update in 30 minutes.

Update: We have identified the issue: [one sentence].
We are currently [action]. Next update in 30 minutes.

Resolved: This incident has been resolved. [Component] is operating normally.
We will publish a post-incident review by [date].
```

Fill in the specifics during the incident. Don't write from scratch under pressure.

<!-- RESOURCES -->

- [Atlassian Statuspage](https://www.atlassian.com/software/statuspage) -- type: tool, time: 30m
- [Cachet - Open Source Status Page](https://cachethq.io/) -- type: tool, time: 1h
- [Writing Good Incident Status Updates](https://www.atlassian.com/blog/statuspage/incident-communication-best-practices) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
目前，当你的服务宕机时，客户是从 Twitter、从自己的用户提交支持工单、或者从自己的仪表盘变红才得知的。他们没有一个可靠的地方去查看正在发生什么，以及你是否已经知晓。状态页面正好提供了这一点：一个始终可用的、关于你服务当前状态和任何正在进行中的事故的唯一可信来源。做好它，可以减少支持请求量、设定预期，并表明你是在以透明的方式运营。

<!-- ZH_DEEP_DIVE -->
## 状态页面不是什么

状态页面不是内部团队用的仪表盘。它不能替代你的内部监控或告警。它是面向客户的对外沟通渠道——这些客户无法访问你的系统，但需要知道此刻是否还能信任它们。

设计原则：客户查看你的状态页面时，应该能对“这个服务是否正常？”这个问题得到一个清晰、无术语的答案，而不需要任何技术知识来解读。

## 上面应该放什么

**每个主要组件的当前状态。** 把服务拆分成对用户有意义的组件——不要按内部服务名来分，而要按用户实际交互的对象来分：“Dashboard”、“API”、“Billing”、“Mobile App”。展示每个组件的状态：Operational / Degraded Performance / Partial Outage / Major Outage。

**事件时间线。** 当事件正在进行时，用平实的语言提供带时间戳的更新：
- “下午 2:15 — 我们正在调查 API 上异常升高的错误率。”
- “下午 2:45 — 我们已定位原因：下午 2:00 上线了一次配置错误的部署。正在回滚。”
- “下午 3:10 — 服务已恢复。错误率已回到正常水平。”

**历史事件。** 展示过去的事件及其解决方式。这能建立信任。一个没有任何事件历史的服务看起来可疑，而不是可靠。

## 托管 vs 自托管

**Atlassian Statuspage** — 行业标准。可与 PagerDuty、Datadog 以及大多数监控工具集成，实现状态自动更新。有免费套餐。为 Slack、GitHub、Stripe 以及数千个其他服务提供状态页面支持。

**Cachet** — 开源、自托管替代方案。需要你自己的基础设施——这会带来一个问题：你的服务宕机时，你的状态页面可能也宕机了。

如果你采用自托管，务必确保状态页面运行在与其所报告服务相互隔离的基础设施上。一个随服务一起宕机的状态页面，在最需要它的那一刻毫无用处。

## 自动化 vs 手动更新

最好的状态页面将两者结合。自动化组件根据监控信号更新绿色/黄色/红色。事件沟通由人来撰写，因为这类沟通需要上下文和判断力。

一种常见模式：从监控系统设置组件状态的自动更新（如果 API 错误率超过阈值，自动将“API”切换为“Degraded Performance”）。手动撰写事件更新，说明正在发生什么以及你正在做什么。

## 提前准备模板

在压力下写出清晰的沟通内容很难。在需要之前就准备好模板：

```
Investigating: We are aware of issues affecting [component].
Our team is currently investigating. Next update in 30 minutes.

Update: We have identified the issue: [one sentence].
We are currently [action]. Next update in 30 minutes.

Resolved: This incident has been resolved. [Component] is operating normally.
We will publish a post-incident review by [date].
```

在事件期间填入具体内容。不要在压力下从零开始写。

<!-- ZH_RESOURCES -->
- [Atlassian Statuspage](https://www.atlassian.com/software/statuspage) -- 类型：工具，时间：30m
- [Cachet - 开源状态页面](https://cachethq.io/) -- 类型：工具，时间：1h
- [编写良好的事故状态更新](https://www.atlassian.com/blog/statuspage/incident-communication-best-practices) -- 类型：文章，时间：10m

<!-- ZH_UI -->
1. 为你的服务搭建公开状态页面
2. 为常见事故严重等级编写沟通模板
3. 明确事故期间由谁负责更新状态页面
4. 在非关键事故中演练更新状态页面
5. 事故已结束，状态页面也已更新。现在我们该如何真正从发生的事件中学习？
6. 我们已发布全部恢复通知，客户知道一切恢复正常。但我们没真正深挖原因就关闭了工单。我已向客户承诺做事故后复盘——如何开展一次真正有产出、而不只是记录时间线的复盘？
