---
id: incident-roles
title: Incident Roles
zone: sre
edges:
  to:
    - id: incident-management
      question: >-
        We have roles assigned. What's the actual process for running an
        incident from start to finish?
      detail: >-
        I know who the incident commander is now. But I still don't have a
        clear picture of the full lifecycle — how do we track what we've tried,
        how do we decide when it's actually fixed, when do we escalate? The
        whole thing still feels improvised even with roles in place.
difficulty: 2
tags:
  - incident-response
  - incident-roles
  - incident-commander
  - sre
  - coordination
category: practice
milestones:
  - Define the responsibilities of the incident commander role
  - Explain why a dedicated comms lead reduces resolution time
  - Practice assigning roles at the start of a simulated incident
  - Understand what the scribe captures and why that log matters afterward
title_zh: "事件角色"

---


When everyone is equally responsible for an incident, nobody is responsible. The first thing that separates orderly incident response from chaos is role clarity: one person is in charge, one person handles all external communication, and someone is writing everything down. These three roles — Incident Commander, Communications Lead, and Scribe — exist not because of bureaucracy but because human coordination under pressure requires explicit structure to work.

<!-- DEEP_DIVE -->

## Incident Commander (IC)

The IC is the decision-maker. They own the incident from declaration to resolution. Their job is not to fix the problem — it's to coordinate the people who are fixing it. This distinction is critical and counterintuitive. The most senior engineer should not be the IC if they're also the most qualified to debug the system. The IC's value comes from their ability to coordinate, not their technical depth.

IC responsibilities:
- Declare the incident and set the severity
- Assign tasks to other responders and track whether they've been completed
- Make judgment calls about when to escalate, when to rollback, when to call in additional help
- Keep the team focused — cut off rabbit holes, redirect exploratory debugging when the situation is urgent
- Declare resolution when the incident is over

The IC is also the single point of contact for the comms lead. Nobody else is fielding stakeholder questions.

## Communications Lead (Comms)

The comms lead's job is to keep everyone outside the incident room informed so that the responders don't have to. This is not a junior role. The comms lead needs enough technical understanding to accurately represent what's happening without exposing sensitive details or creating additional confusion.

Comms responsibilities:
- Send regular status updates to stakeholders (engineering leadership, support, affected customers via status page) on a defined cadence — typically every 30 minutes, even if there's nothing new to report
- Field incoming questions so they don't reach the responders
- Draft the initial incident declaration and the all-clear message
- Coordinate with support teams on customer-facing communications

A well-functioning comms lead completely shields the technical responders from communication overhead. During a major incident, responders should not be sending status updates — they should be debugging.

## Scribe

The scribe documents everything in real time. Not a summary written after the fact — a timestamped running log during the incident:

```
14:32 - Alert fired: high error rate on checkout service (15% errors)
14:34 - IC assigned: [name]. Severity declared: SEV2
14:37 - Database connection pool exhausted. Investigating connection leak.
14:41 - Found: new deployment at 14:15 introduced connection pool config change
14:44 - Rollback initiated
14:51 - Error rate returning to normal
15:00 - Resolved. Error rate at 0.1% (baseline)
```

This log is invaluable: it tells the post-mortem who did what, when, and why. It makes handoffs between responders possible without context loss. It documents the timeline of changes, which is essential for understanding cascading failures.

## How roles are assigned

Roles are assigned at the start of the incident, not during it. The on-call engineer who acknowledges the page is the default IC until explicitly handed off. The assignment should be explicit: "I'm taking IC. [Name], take comms. [Name], take scribe." First message in the incident channel.

For smaller teams or smaller incidents, the same person can hold multiple roles — but the scribe role is the one most often dropped under pressure, and it's the one most worth protecting.

<!-- RESOURCES -->

- [PagerDuty Incident Response Roles](https://response.pagerduty.com/training/incident_commander/) -- type: guide, time: 20m
- [Google SRE Book - Being On-Call](https://sre.google/sre-book/being-on-call/) -- type: book, time: 20m
- [Incident Command for IT - FEMA ICS adapted](https://response.pagerduty.com/during/during_an_incident/) -- type: guide, time: 15m

<!-- ZH_SUMMARY -->
当每个人都对一起事故负有同等责任时，实际上就没有人真正负责。将有秩序的事故响应与混乱区分开来的第一件事，就是角色清晰：一个人负责指挥，一个人负责所有对外沟通，还有一个人负责记录一切。这三个角色——事故指挥官（Incident Commander）、沟通负责人（Communications Lead）和记录员（Scribe）——之所以存在，并非出于官僚主义，而是因为压力下的人类协作需要明确的结构才能奏效。

<!-- ZH_DEEP_DIVE -->
## 事件指挥官（IC）

IC 是决策者。他们从事件声明到解决全程负责。他们的工作不是修复问题——而是协调正在修复问题的人。这一区分至关重要且反直觉。如果最资深工程师同时也是最有能力调试系统的人，那么他们不应担任 IC。IC 的价值来自其协调能力，而非技术深度。

IC 职责：
- 声明事件并设定严重级别
- 向其他响应者分配任务并跟踪是否完成
- 就何时升级、何时回滚、何时呼叫额外支援做出判断
- 保持团队专注——切断死胡同，在情况紧急时重定向探索性调试
- 在事件结束时宣布解决

IC 也是通信负责人的唯一联系人。没有其他人负责回应利益相关者的问题。

## 通信负责人（Comms）

通信负责人的工作是让事件室外的所有人保持知情，这样响应者就不必分心。这不是初级角色。通信负责人需要足够的技术理解，以准确传达正在发生的事情，同时不暴露敏感细节或造成额外混乱。

通信职责：
- 按固定节奏向利益相关者（工程领导层、支持团队、通过状态页面受影响的客户）发送定期状态更新——通常每 30 分钟一次，即使没有新情况可报告
- 处理 incoming 问题，使其不打扰响应者
- 起草初始事件声明和解除警报消息
- 与支持团队协调面向客户的沟通

一个运作良好的通信负责人能完全屏蔽技术响应者的沟通开销。在重大事件期间，响应者不应发送状态更新——他们应该专注于调试。

## 记录员

记录员实时记录一切。不是事后写的总结——而是事件期间带时间戳的运行日志：

```
14:32 - 告警触发：checkout 服务错误率高（15% 错误）
14:34 - IC 指派：[姓名]。严重级别声明：SEV2
14:37 - 数据库连接池耗尽。正在调查连接泄漏。
14:41 - 发现：14:15 的新部署引入了连接池配置变更
14:44 - 启动回滚
14:51 - 错误率恢复正常
15:00 - 已解决。错误率 0.1%（基线）
```

此日志非常宝贵：它告诉事后复盘谁在何时做了什么以及为什么。它使响应者之间的交接成为可能，而不会丢失上下文。它记录了变更时间线，这对于理解级联故障至关重要。

## 角色如何分配

角色在事件开始时分配，而不是在事件期间。确认告警的待命工程师是默认 IC，直到明确移交。分配应明确：“我来担任 IC。[姓名]，负责通信。[姓名]，负责记录。”这是事件频道中的第一条消息。

对于较小团队或较小事件，同一个人可以担任多个角色——但记录员角色是在压力下最常被放弃的角色，也是最值得保护的角色。

<!-- ZH_RESOURCES -->
- [PagerDuty 事件响应角色](https://response.pagerduty.com/training/incident_commander/) -- 类型：指南，时长：20分钟
- [Google SRE 手册 - 值班](https://sre.google/sre-book/being-on-call/) -- 类型：书籍，时长：20分钟
- [IT 事件指挥 - 改编自 FEMA ICS](https://response.pagerduty.com/during/during_an_incident/) -- 类型：指南，时长：15分钟

<!-- ZH_UI -->
1. 定义事故指挥官角色的职责
2. 解释为什么专职沟通负责人能缩短解决时间
3. 在模拟事故开始时练习分配角色
4. 理解记录员记录什么，以及为什么事后该日志很重要
5. 我们已经分配了角色。从头到尾运行一次事故的实际流程是什么？
6. 我现在知道事故指挥官是谁了。但我仍然不清楚完整生命周期——我们如何跟踪已经尝试过的措施，如何判断问题真正修复了，何时升级？即使角色到位，整个流程仍显得即兴。
