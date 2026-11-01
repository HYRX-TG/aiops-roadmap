---
id: incident-management
title: Incident Management
zone: sre
edges:
  to:
    - id: post-mortems
      question: >-
        The incident is resolved. How do I make sure we actually learn from it
        instead of just moving on?
      detail: >-
        Every post-mortem I've seen either turns into a blame session or
        produces a list of action items that nobody follows through on. I want
        to run one that actually changes how we work — not just fills out a
        document.
    - id: incident-communication
      question: >-
        While I'm trying to fix the incident, how do I keep stakeholders and
        customers in the loop without it derailing the response?
      detail: >-
        The responders need to focus on debugging. But I'm also getting pinged
        by engineering leadership, the support team, and customers all at once.
        All that communication is pulling focus away from the actual fix. I need
        to handle both without sacrificing either.
difficulty: 2
tags:
  - incident-management
  - incident-response
  - on-call
  - sre
  - severity
  - incident-commander
category: practice
milestones:
  - 'Define severity levels for your organisation (SEV1, SEV2, SEV3)'
  - Establish the incident commander role and what it's responsible for
  - Practice declaring and running a simulated incident
  - Document your incident response process so anyone can follow it at 3 AM
title_zh: "事件管理"

---


Incident management is the process that turns a chaotic outage into a structured response with a clear owner, a clear timeline, and a clear path to resolution. The goal isn't to eliminate incidents — it's to make them predictable. When the process is right, any engineer in the rotation can handle any incident with confidence, because the process tells them what to do even when their technical knowledge runs out.

<!-- DEEP_DIVE -->

## Incident lifecycle

A well-run incident has five phases:

**1. Detection**: Someone or something notices the service is degraded. Ideally an alert — but users, support tickets, or a developer noticing something wrong all count. The faster detection happens, the less total damage.

**2. Declaration**: Someone explicitly says "this is an incident." This sounds trivial but it matters. Declaration triggers the process: the IC is assigned, the incident channel is created, the severity is set. Without explicit declaration, the response stays informal and coordination breaks down.

**3. Triage**: What is the scope and severity? Is this a complete outage or degraded service? Which users are affected? What's the business impact? Triage determines urgency and guides resource allocation. It also shapes communication — a SEV1 complete outage gets a different response than a SEV3 elevated error rate.

**4. Response**: The technical work of fixing the problem. Form a hypothesis, test it, eliminate or confirm, iterate. The IC coordinates. The scribe documents. The comms lead handles updates. Responders debug.

**5. Resolution and handoff**: The incident is declared resolved when the symptom is gone and the fix is confirmed stable. The IC writes an all-clear. The scribe's log is preserved for the post-mortem.

## Severity levels

Define severity levels before you need them. A typical structure:

| Severity | Description | Response | Example |
|----------|-------------|----------|---------|
| SEV1 | Complete service outage, data loss risk, or security breach | All hands, 24/7 until resolved | Checkout completely down |
| SEV2 | Major feature broken, significant user impact | IC + team, business hours extended | Payment failures for 20% of users |
| SEV3 | Degraded performance, minor feature broken | On-call handles, normal hours | Slow search, non-critical feature failing |
| SEV4 | Minor issue, no immediate user impact | Ticket, fix in normal sprint | Edge case bug, cosmetic issue |

SEV1 and SEV2 require IC + comms roles. SEV3 can often be handled by the on-call engineer alone. SEV4 is a ticket, not an incident.

## The incident channel

Every incident gets its own communication channel (Slack, Teams, or equivalent), created at declaration and archived afterward. The channel becomes the single source of truth: what's happening, what's been tried, who's doing what. Side conversations and DMs during an incident fragment information and hurt coordination.

Channel naming convention: `#incident-YYYY-MM-DD-brief-description` or `#inc-[ticket-number]`. Keep it searchable.

## Declaring resolution

Resolution is the IC's call. The criteria:
- The symptom that triggered the incident is no longer present
- The fix (or mitigation) is confirmed stable — not just "seems better"
- Monitoring shows return to baseline
- There are no obvious secondary effects

Don't rush resolution. A premature all-clear followed by another incident 20 minutes later is worse than a longer incident with a clean resolution.

<!-- RESOURCES -->

- [PagerDuty Incident Response Guide](https://response.pagerduty.com/) -- type: guide, time: 1h
- [Google SRE Book - Managing Incidents](https://sre.google/sre-book/managing-incidents/) -- type: book, time: 25m
- [Atlassian Incident Management Handbook](https://www.atlassian.com/incident-management) -- type: guide, time: 30m

<!-- ZH_SUMMARY -->
事件管理是将混乱的故障转化为结构化响应的过程，它有明确的负责人、明确的时间线和明确的解决路径。目标不是消除事件，而是让事件变得可预测。当流程正确时，轮值中的任何工程师都能自信地处理任何事件，因为即使他们的技术知识不够用，流程也会告诉他们该做什么。

<!-- ZH_DEEP_DIVE -->
## 事件生命周期

一个运转良好的事件处理包含五个阶段：

**1. 检测**：某人或某系统注意到服务出现降级。理想情况下是告警——但用户反馈、支持工单，或开发者自己发现问题，也都算数。检测越快，总损失越小。

**2. 声明**：有人明确说出“这是一个事件”。这听起来微不足道，但很重要。声明会触发流程：指派 IC（事件指挥官）、创建事件频道、设定严重级别。没有明确的声明，响应就会停留在非正式状态，协调也会瓦解。

**3. 分诊**：范围和严重级别是什么？是完全宕机还是服务降级？哪些用户受影响？业务影响是什么？分诊决定紧急程度并指导资源分配。它同时也影响沟通方式——SEV1 完全宕机的响应方式与 SEV3 错误率升高截然不同。

**4. 响应**：修复问题的技术工作。提出假设、验证假设、排除或确认、迭代。IC 负责协调。记录员负责文档。沟通负责人负责更新通报。响应者负责调试。

**5. 解决与交接**：当症状消失且修复被确认稳定后，事件即被宣布解决。IC 发布全部解除通告。记录员的日志被保留，用于事后复盘。

## 严重级别

在需要之前就定义好严重级别。一个典型的结构：

| 严重级别 | 描述 | 响应 | 示例 |
|----------|-------------|----------|---------|
| SEV1 | 完全服务宕机、数据丢失风险或安全泄露 | 全员参与，7×24 直到解决 | 结账完全不可用 |
| SEV2 | 主要功能损坏，显著的用户影响 | IC + 团队，延长工作时间 | 20% 的用户支付失败 |
| SEV3 | 性能降级，次要功能损坏 | 值班人员处理，正常工作时间 | 搜索缓慢，非关键功能失败 |
| SEV4 | 次要问题，无直接用户影响 | 工单，在正常迭代中修复 | 边缘场景 bug，外观问题 |

SEV1 和 SEV2 需要 IC + 沟通角色。SEV3 通常可以由值班工程师单独处理。SEV4 是工单，不是事件。

## 事件频道

每个事件都有自己的沟通频道（Slack、Teams 或类似工具），在声明时创建，事后归档。该频道成为唯一事实来源：发生了什么、尝试过什么、谁在做什么。事件期间的私下对话和私信会割裂信息，损害协调。

频道命名约定：`#incident-YYYY-MM-DD-brief-description` 或 `#inc-[ticket-number]`。保持可搜索。

## 宣布解决

解决由 IC 决定。标准是：
- 触发事件的症状已不再出现
- 修复（或缓解措施）被确认稳定——而不只是“看起来好多了”
- 监控显示已恢复到基线
- 没有明显的次生影响

不要急于宣布解决。过早的全部解除通告，20 分钟后又发生另一起事件，比一个持续时间更长但干净解决的事件更糟糕。

<!-- ZH_RESOURCES -->
- [PagerDuty 事件响应指南](https://response.pagerduty.com/) -- 类型：指南，时长：1小时
- [Google SRE 手册 - 管理事件](https://sre.google/sre-book/managing-incidents/) -- 类型：书籍，时长：25分钟
- [Atlassian 事件管理手册](https://www.atlassian.com/incident-management) -- 类型：指南，时长：30分钟

<!-- ZH_UI -->
1. 为你的组织定义严重级别（SEV1、SEV2、SEV3）
2. 确立事件指挥官角色及其职责
3. 演练一次模拟事件的宣布与执行
4. 记录你的事件响应流程，让任何人凌晨3点都能照着做
5. 事件已解决。如何确保我们真正从中吸取教训，而不是就此翻篇？
6. 我见过的每次复盘要么变成追责会，要么产出一堆没人跟进落实的行动项。我想主持一次真正能改变我们工作方式的复盘——而不只是填完一份文档。
7. 在我努力修复事件的同时，如何让利益相关方和客户保持知情，又不至于干扰响应工作？
8. 响应人员需要专注于调试。但我同时被工程管理层、支持团队和客户轮番轰炸。这些沟通都在把注意力从实际修复上拉走。我需要两者兼顾，不能顾此失彼。
