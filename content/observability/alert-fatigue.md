---
id: alert-fatigue
title: Alert Fatigue
zone: observability
edges:
  to:
    - id: symptom-vs-cause-alerting
      question: >-
        I've cut down the alert count. But when something breaks I still get
        30 alerts firing at once and I can't tell which is the real problem.
      detail: >-
        Fewer alerts helped but now every real incident floods us with alerts
        at once. The database is slow, so the API is slow, so all five
        downstream services start alerting too. I'm trying to debug through a
        wall of noise. Surely I should only be alerted about the one thing that
        actually matters.
difficulty: 2
tags:
  - alerting
  - alert-fatigue
  - on-call
  - observability
category: concept
milestones:
  - Identify which of your current alerts are noisy and non-actionable
  - Understand the alert debt cycle and how it leads to ignored pages
  - Audit your alert history and calculate what percentage led to real action
  - Set a policy for what makes an alert worth sending at all
title_zh: "告警疲劳"

---


Alert fatigue is what happens when your alerting system has cried wolf too many times. The team starts treating pages as background noise — silencing them, acknowledging without looking, or just learning to sleep through the phone. Then a real incident happens, a page fires into the noise, and nobody responds in time. It's one of the most common ways that a monitoring system that looks good on paper completely fails in practice.

The insidious thing about alert fatigue is that it builds gradually. You add an alert here, another there, a few more after an incident post-mortem. Each individual alert seemed reasonable when you wrote it. But they accumulate, overlap, and fire for things that don't require human action. After enough of that, the team's unconscious response to a page becomes "probably nothing" — which is exactly backwards from what alerting is supposed to accomplish.

The fix isn't to silence alerts or lower volumes. It's to fix the quality. Every alert that fires should require a human decision. If someone's response to a page is to look at it, decide nothing needs to be done, and go back to sleep — that alert should not exist in its current form. Either the condition is genuinely fine and the alert threshold is wrong, or the condition is real but not urgent enough to page (lower its severity to a ticket). Either way, the alert as-is is making your on-call worse.

<!-- DEEP_DIVE -->

## The Alert Debt Cycle

Alert fatigue follows a predictable cycle, and understanding it makes it easier to break.

It starts with **alert accumulation**. Alerts get added over time — after incidents, out of caution, because someone thought a metric looked interesting to watch. Nobody removes old ones. The total count climbs.

Then comes **routine noise**. Some of those alerts fire regularly for conditions that turn out to be fine. The team investigates once or twice, finds nothing, and starts treating that alert as known noise. They still acknowledge it (the system requires it), but they've stopped actually looking.

That leads to **desensitization**. When you've acknowledged 200 false alarms, your brain stops treating a page as a signal that something is wrong. It becomes an administrative task: silence, continue sleeping, deal with it in the morning.

Finally: **missed incidents**. A real problem fires an alert that looks exactly like the noise. It gets silenced or ignored. The incident gets worse while nobody responds. The post-mortem asks "why didn't anyone respond to the alert?" — and the real answer is that the alerting system had long since lost the team's trust.

## Auditing Your Alerts

The most direct way to address alert fatigue is to pull your alert history and measure it. Most alerting systems (PagerDuty, Opsgenie, Alertmanager with a logging backend) give you the ability to export alert events. You want at minimum 30 days of data, ideally 90.

For each alert that fired in that period, answer two questions:

1. Did this alert lead to real action? (a code change, a config fix, an infrastructure change, a rollback — something that addressed a real problem)
2. Was the action taken within a reasonable time of the alert, or did someone investigate and find nothing?

You'll typically find that a large fraction of alerts — often 50% or more in teams that haven't audited before — led to no action. Those are candidates for remediation.

For each no-action alert, you have exactly three options:

**Delete it.** If the condition it detected was never actually a problem, the alert was wrong. Remove it. Don't keep it "just in case."

**Downgrade its severity.** If the condition is real but doesn't require immediate human action, make it a ticket or a Slack notification instead of a page. It stays in your awareness without destroying on-call quality.

**Fix the underlying issue.** Sometimes an alert fires constantly because the underlying system is in a perpetual state it shouldn't be in. The right fix isn't to silence the alert — it's to fix the system so the condition goes away.

## Setting a Standard for What Gets to Page

After an audit, write down a policy. It doesn't have to be long. Something like:

> An alert gets page severity if and only if: a user is experiencing degraded service right now, AND a human action in the next 30 minutes can meaningfully improve the situation.

That second clause is important and often overlooked. If your database is down and there's nothing an engineer can do at 3am to recover it any faster, paging everyone on the team doesn't help users — it just exhausts the people who would need to do real work in the morning.

A useful question for every alert: **what exactly should the person who receives this do?** If you can't write a clear answer, the alert isn't ready to page. Put it in a ticket channel until you've written the runbook.

## The Ratio to Aim For

A healthy on-call rotation has a very high ratio of actionable alerts to total alerts. Some teams aim for 80-90%+ of pages requiring real action. This isn't about being cavalier with monitoring — it's about respecting that every page has a cost (interrupted sleep, on-call burnout, eroded trust in the system) and that cost should be paid only when the benefit is real.

When you hit a stretch of on-call where almost every page requires real action, two things happen: the team trusts the alerts, and the people who carry the pager feel like the system is working for them instead of against them. That's the goal.

## Ongoing Maintenance

Alert debt accumulates again if you don't maintain it. A few practices that help:

Run a monthly alert review. Look at which alerts fired in the past month and whether each one resulted in action. Make the review a team ritual, not an individual burden.

After every incident post-mortem, add new alerts deliberately — but also ask whether existing alerts contributed to noise during the incident and whether they should be tuned or removed.

Make it easy to delete alerts. Teams often keep bad alerts because removing one feels risky. A better frame: if an alert isn't earning its place, it's actively making things worse by being there.

<!-- RESOURCES -->

- [My Philosophy on Alerting (Rob Ewaschuk, Google)](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- type: article, time: 20m
- [On-Call Shouldn't Suck (Charity Majors)](https://charity.wtf/2020/10/03/on-call-shouldnt-suck-a-guide-for-managers/) -- type: article, time: 15m
- [Alert Fatigue: Causes, Effects, and Solutions (PagerDuty)](https://www.pagerduty.com/resources/learn/alert-fatigue/) -- type: article, time: 10m
- [Alerting on What Matters (Prometheus docs)](https://prometheus.io/docs/practices/alerting/) -- type: article, time: 15m
- [The Practical Guide to Incident Management (Atlassian)](https://www.atlassian.com/incident-management) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
告警疲劳是指你的告警系统太多次“狼来了”之后产生的后果。团队开始把告警通知当作背景噪音——静音它们、不看就确认、或者干脆学会在电话铃声中继续睡觉。然后真正的事故发生了，一条告警淹没在噪音中触发，却没有人及时响应。这是看似完美的监控系统在实践中彻底失效的最常见方式之一。

告警疲劳的阴险之处在于它是逐渐累积的。你在这里加一条告警，那里加一条，事故复盘后又加几条。每一条告警在编写时看起来都合理。但它们会累积、重叠，并为那些不需要人工处理的事情触发。这样积累到一定程度后，团队对告警通知的潜意识反应就变成了“大概没什么事”——这恰恰与告警本应实现的目标背道而驰。

解决办法不是静音告警或降低告警量，而是提升质量。每一条触发的告警都应该需要一个人工决策。如果某人对告警通知的反应是看一眼、判断不需要做任何事、然后继续睡觉——那这条告警就不应该以当前形式存在。要么该状况确实没问题、告警阈值设错了，要么该状况真实存在但不够紧急、不值得触发告警（将其降级为工单）。无论哪种情况，保持现状的告警只会让你的值班体验更糟。

<!-- ZH_DEEP_DIVE -->
## 告警债务循环

告警疲劳遵循一个可预测的循环，理解它就能更容易打破它。

它始于**告警累积**。告警随时间不断被添加——事故之后、出于谨慎、因为有人觉得某个指标看起来值得关注。没有人删除旧的告警。总数不断攀升。

接着是**例行噪音**。其中一些告警会定期触发，而对应的状况实际上并无问题。团队调查一两次，什么也没发现，于是开始把该告警当作已知噪音。他们仍然会确认它（系统要求如此），但已经不再真正去查看了。

这导致**脱敏**。当你确认了 200 次误报之后，你的大脑就不再把这个呼叫当作“出问题了”的信号。它变成了一项行政任务：静音、继续睡觉、早上再处理。

最后是：**漏掉的事故**。一个真正的问题触发了一条看起来和噪音一模一样的告警。它被静音或忽略了。事故在无人响应的情况下恶化。事后复盘会问“为什么没有人响应这条告警？”——而真正的答案是，告警系统早已失去了团队的信任。

## 审计你的告警

解决告警疲劳最直接的方法是拉取你的告警历史并对其进行度量。大多数告警系统（PagerDuty、Opsgenie、带日志后端的 Alertmanager）都能让你导出告警事件。你至少需要 30 天的数据，理想情况下是 90 天。

对于该时间段内触发的每一条告警，回答两个问题：

1. 这条告警是否带来了真实的行动？（代码变更、配置修复、基础设施变更、回滚——任何解决了真实问题的行动）
2. 行动是在告警后的合理时间内采取的，还是有人调查后什么也没发现？

你通常会发

<!-- ZH_RESOURCES -->
- [My Philosophy on Alerting (Rob Ewaschuk, Google)](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- 类型：文章，时长：20m
- [On-Call Shouldn't Suck (Charity Majors)](https://charity.wtf/2020/10/03/on-call-shouldnt-suck-a-guide-for-managers/) -- 类型：文章，时长：15m
- [Alert Fatigue: Causes, Effects, and Solutions (PagerDuty)](https://www.pagerduty.com/resources/learn/alert-fatigue/) -- 类型：文章，时长：10m
- [Alerting on What Matters (Prometheus docs)](https://prometheus.io/docs/practices/alerting/) -- 类型：文章，时长：15m
- [The Practical Guide to Incident Management (Atlassian)](https://www.atlassian.com/incident-management) -- 类型：文章，时长：20m

<!-- ZH_UI -->
1. 找出当前哪些告警是嘈杂且不可操作的
2. 理解告警债务循环及其如何导致告警被忽视
3. 审计告警历史，计算其中有多大比例促成了真实行动
4. 制定一条策略，明确什么样的告警才值得发送
5. 我已经减少了告警数量。但出问题时仍会同时触发 30 条告警，我分不清哪个才是真正的问题。
6. 减少告警有帮助，但现在每次真实故障都会同时涌来大量告警。数据库变慢，API 就变慢，于是五个下游服务也开始告警。我得在一片噪音中排查。按理说，我只应该收到那一个真正重要事项的告警。
