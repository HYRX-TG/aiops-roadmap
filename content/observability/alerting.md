---
id: alerting
title: Alerting
zone: observability
edges:
  to:
    - id: alert-fatigue
      question: >-
        My phone is buzzing every 10 minutes with alerts. My team has started
        ignoring them. How do I fix this?
      detail: >-
        We have so many alerts that when a real problem happens nobody is sure
        which one to look at first. Half the time someone silences their pager
        just to get some sleep. I know this is bad but I don't know how to
        actually reduce it without missing real incidents.
    - id: symptom-vs-cause-alerting
      question: >-
        When one thing breaks I get 30 alerts firing at once. I can't tell
        which is the real problem and which are just downstream symptoms.
      detail: >-
        The database goes slow and I get alerts for the database, all five
        services talking to it, the cache that depends on it, and the jobs that
        are backing up. I'm trying to debug through a storm of alerts that all
        started at the same second.
    - id: distributed-tracing
      question: >-
        An alert fired. I can see something is wrong in the metrics. How do I
        find out why?
      detail: >-
        I know something is broken but I can't tell where. My service is slow
        but it calls four other services. The metrics show a spike but not
        which hop in the chain is the problem. I feel like I need a map of what
        actually happened to a specific request.
difficulty: 2
tags:
  - alerting
  - pagerduty
  - opsgenie
  - prometheus-alertmanager
  - on-call
  - alert-fatigue
category: practice
milestones:
  - Set up alerts on your four golden signals with appropriate thresholds
  - 'Route alerts to a notification channel (Slack, PagerDuty, email)'
  - Understand the difference between alerting on causes vs symptoms
  - >-
    Experience and reduce alert fatigue by eliminating noisy, non-actionable
    alerts
title_zh: "告警"

---


A dashboard you don't watch catches nothing. Alerting is what transforms passive monitoring into an active system — it's the layer that notices something is wrong and comes to find you. Without it, every incident starts the same way: someone happened to look at the dashboard, or a user complained. With it, you know before the user does.

In the Prometheus ecosystem, alerting is handled by two components working together. Prometheus evaluates your alert rules on a schedule and fires alerts when conditions are met. Alertmanager receives those fired alerts and handles the delivery — routing them to the right team, deduplicating noisy bursts, grouping related alerts together, and sending them to Slack, PagerDuty, email, or wherever your team responds. You define the conditions in Prometheus; you define the routing and delivery in Alertmanager.

The difference between alerting that helps and alerting that hurts is almost entirely about quality, not quantity. An alert that fires when nothing actionable needs to happen is worse than no alert at all — it trains your team to ignore pages, and eventually a real incident gets missed in the noise. The goal is for every alert to demand a human decision, not just an acknowledgement.

<!-- DEEP_DIVE -->

## Prometheus Alert Rules

Alert rules live in YAML files that Prometheus loads (you reference them in `prometheus.yml` under `rule_files`). Each rule has a PromQL expression that evaluates to true or false, and when it's true for long enough, Prometheus fires the alert.

Here's a complete example — an alert that fires when the error rate on an HTTP service exceeds 1% for five minutes:

```yaml
groups:
  - name: api-service
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{job="api", status=~"5.."}[5m])
          /
          rate(http_requests_total{job="api"}[5m])
          > 0.01
        for: 5m
        labels:
          severity: page
          team: backend
        annotations:
          summary: "High error rate on API service"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes."
          runbook: "https://wiki.example.com/runbooks/high-error-rate"
```

The key fields:

- **`expr`** — the PromQL condition. When this evaluates to true, the alert is pending. When it's been true for `for:` duration, it fires.
- **`for`** — how long the condition must hold before the alert fires. This is how you avoid flapping. Without `for:`, a single spike fires and resolves an alert in seconds. With `for: 5m`, you only get paged for sustained problems.
- **`labels`** — metadata that Alertmanager uses for routing. Severity and team are the most common.
- **`annotations`** — human-readable text sent with the alert. The `summary` is a one-line description of what happened. The `description` gives more context and can use template variables like `{{ $value }}` to include the actual metric value. The `runbook` link tells the person who gets paged exactly where to look.

## What Makes a Good Alert

A well-written alert has five properties:

1. **A clear name** that describes the condition, not the metric. `HighErrorRate` not `HttpRequestsTotalFiring`.
2. **Appropriate severity** so the routing and response can scale with urgency.
3. **A summary** that tells you what happened in one sentence.
4. **A description** that tells you what to check first, ideally with the actual value included.
5. **A runbook link** that takes the responder directly to documented steps.

The runbook is the most underrated part. When you're woken at 3am, you don't want to reconstruct from memory what this alert means and what to do about it. The runbook is the answer to "what do I actually do when this fires?"

## Severity Levels: Page vs Ticket vs Info

Not every problem should wake someone up. Calibrating severity is one of the most important things you'll do when setting up alerting.

**Page** (wake someone up, interrupt whatever they're doing): user-facing impact is happening right now. Error rate elevated. p99 latency above SLO. Service returning 503s. Something a user would notice in the next five minutes if left alone.

**Ticket** (address during business hours): something is wrong but not immediately user-facing. Disk at 70% and filling. A non-critical background job is failing. A replica is behind but the primary is fine. These should create tickets automatically, not pages.

**Info / warning**: trends worth knowing about. Traffic dropped 20% from yesterday's baseline. A certificate expires in 30 days. These go to a Slack channel someone checks during the day, not to anyone's phone.

The question to ask for any alert: if this fires at 3am, is it worth waking someone up? If the honest answer is "probably not," make it a ticket.

## Alertmanager: Routing and Delivery

Alertmanager receives fired alerts from Prometheus and decides what to do with them. Its main jobs are routing (which team gets this alert?), grouping (bundle related alerts into one notification), and inhibition (suppress downstream alerts when a higher-level one fires).

A basic Alertmanager config:

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/...'

route:
  receiver: slack-general
  group_by: [alertname, job]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: page
      receiver: pagerduty-backend
    - match:
        severity: ticket
      receiver: slack-tickets

receivers:
  - name: slack-general
    slack_configs:
      - channel: '#alerts'

  - name: pagerduty-backend
    pagerduty_configs:
      - service_key: '<key>'

  - name: slack-tickets
    slack_configs:
      - channel: '#ops-tickets'
```

The `route` block is a tree. Alertmanager walks the tree for each incoming alert, matching against labels, and sends it to the first matching receiver. `group_by` controls which alerts are bundled into one notification — if 20 alerts fire at once with the same `alertname` and `job`, they arrive as one message rather than 20.

`group_wait` (how long to wait before sending the first notification for a new group) and `repeat_interval` (how long before re-notifying if an alert is still firing) are important to tune so you don't get spammed but also don't miss that something is still broken hours later.

## A Starting Set of Alerts

If you're not sure where to start, write alerts for the four golden signals first:

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: page

- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: page

- alert: LowTraffic
  expr: rate(http_requests_total[10m]) < 10
  for: 10m
  labels:
    severity: ticket

- alert: HighSaturation
  expr: 1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) > 0.9
  for: 10m
  labels:
    severity: ticket
```

Start here. Add more only when you discover through real incidents that you're missing something. The most common mistake is adding alerts before you understand what normal looks like.

<!-- RESOURCES -->

- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/) -- type: article, time: 20m
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/) -- type: article, time: 20m
- [My Philosophy on Alerting (Rob Ewaschuk, Google)](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- type: article, time: 20m
- [Alerting on What Matters (Prometheus docs)](https://prometheus.io/docs/practices/alerting/) -- type: article, time: 15m
- [PagerDuty Incident Response Guide](https://response.pagerduty.com/) -- type: article, time: 30m

<!-- ZH_SUMMARY -->
你不看的仪表盘什么都发现不了。告警是将被动监控转变为主动系统的关键——它是那个察觉到出问题并主动来找你的层。没有它，每个故障的开场都一样：有人碰巧看了仪表盘，或者用户来投诉了。有了它，你会在用户之前就知道。

在 Prometheus 生态中，告警由两个协同工作的组件处理。Prometheus 按计划评估你的告警规则，并在条件满足时触发告警。Alertmanager 接收这些已触发的告警并负责投递——将它们路由到正确的团队、对嘈杂的突发告警去重、将相关告警分组，并发送到 Slack、PagerDuty、邮件或你团队响应的任何地方。你在 Prometheus 中定义条件；你在 Alertmanager 中定义路由和投递。

有用的告警和有害的告警之间的区别几乎完全在于质量，而非数量。当没有任何可操作的事情需要发生时却触发的告警，比没有告警更糟——它会让你的团队习惯忽略告警，最终真正的事故会在噪声中被漏掉。目标是让每个告警都要求人做出决策，而不仅仅是确认一下。

<!-- ZH_DEEP_DIVE -->
## Prometheus 告警规则

告警规则存放在 Prometheus 加载的 YAML 文件中（在 `prometheus.yml` 的 `rule_files` 下引用它们）。每条规则都有一个 PromQL 表达式，其求值结果为 true 或 false，当结果为 true 持续足够长时间后，Prometheus 就会触发告警。

下面是一个完整示例——当 HTTP 服务的错误率超过 1% 并持续五分钟时触发的告警：

```yaml
groups:
  - name: api-service
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{job="api", status=~"5.."}[5m])
          /
          rate(http_requests_total{job="api"}[5m])
          > 0.01
        for: 5m
        labels:
          severity: page
          team: backend
        annotations:
          summary: "High error rate on API service"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes."
          runbook: "https://wiki.example.com/runbooks/high-error-rate"
```

关键字段：

- **`expr`** —— PromQL 条件。当它求值为 true 时，告警进入 pending 状态。当它持续为 true 达到 `for:` 指定的时长后，告警触发。
- **`for`** —— 条件必须保持多久告警才会触发。这是避免告警抖动的方式。没有 `for:` 时，单次尖峰就会在几秒内触发并解除告警。有了 `for: 5m`，你只会因持续存在的问题而被呼叫。
- **`labels`** —— Alertmanager 用于路由的元数据。severity 和 team 是最常用的。
- **`annotations`** —— 随告警一起发送的、供人阅读的文本。`summary` 是一句话描述发生了什么。`description` 提供更多上下文，可以使用 `{{ $value }}` 之类的模板变量来包含实际指标值。`runbook` 链接告诉被呼叫的人应该去哪里查看。

## 什么才算好的告警

一条写得好的告警具备五个特性：

1. **清晰的名称**，描述的是条件，而不是指标。用 `HighErrorRate` 而不是 `HttpRequestsTotalFiring`。
2. **合适的严重级别**，使路由和响应能随紧急程度而调整。
3. **一句话的 summary**，告诉你发生了什么。
4. **一段 description**，告诉你首先该检查什么，最好包含实际值。
5. **一个 runbook 链接**，把响应者直接带到有文档记录的步骤。

runbook 是最被低估的部分。当你凌晨 3 点被叫醒时，你不会想凭记忆去重建这条告警意味着什么、该怎么做。runbook 就是"当它触发时我究竟该做什么"的答案。

## 严重级别：Page vs Ticket vs Info

并非每个问题都应该把人叫醒。校准严重级别是你在搭建告警时要做的最重要的事情之一。

**Page**（把人叫醒，打断他正在做的任何事）：用户可见的影响正在发生。错误率升高。p99 延迟超过 SLO。服务返回 503。如果放任不管，用户会在接下来五分钟内察觉到的问题。

**Ticket**（在工作时间处理）：有问题，但不是立即面向用户的。磁盘使用率 70% 且在增长。某个非关键的批处理任务在失败。某个副本落后但主库正常。这些应该自动创建工单，而不是呼叫。

**Info / warning**：值得了解的趋势。流量相比昨天的基线下降了 20%。某张证书 30 天后过期。这些发到有人白天会查看的 Slack 频道，而不是任何人的手机。

对任何告警都要问一个问题：如果它在凌晨 3 点触发，值得把人叫醒吗？如果诚实的答案是"大概不值得"，那就把它做成工单。

## Alertmanager：路由与投递

Alertmanager 接收 Prometheus 发来的已触发告警，并决定如何处理它们。它的主要职责是路由（哪个团队收到这条告警？）、分组（把相关告警打包成一条通知）和抑制（当更高层级的告警触发时，抑制下游告警）。

一个基础的 Alertmanager 配置：

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/...'

route:
  receiver: slack-general
  group_by: [alertname, job]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: page
      receiver: pagerduty-backend
    - match:
        severity: ticket
      receiver: slack-tickets

receivers:
  - name: slack-general
    slack_configs:
      - channel: '#alerts'

  - name: pagerduty-backend
    pagerduty_configs:
      - service_key: '<key>'

  - name: slack-tickets
    slack_configs:
      - channel: '#ops-tickets'
```

`route` 块是一棵树。Alertmanager 对每条传入的告警遍历这棵树，按标签进行匹配，并发送给第一个匹配的 receiver。`group_by` 控制哪些告警被打包成一条通知——如果 20 条告警同时触发且具有相同的 `alertname` 和 `job`，它们会作为一条消息到达，而不是 20 条。

`group_wait`（新分组发送第一条通知前等待多久）和 `repeat_interval`（告警仍在触发时多久重新通知一次）需要仔细调优，这样你既不会被刷屏，也不会在几小时后漏掉"某个东西仍然坏着"的信息。

## 一组起步告警

如果你不确定从哪里开始，先为四大黄金信号编写告警：

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: page

- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: page

- alert: LowTraffic
  expr: rate(http_requests_total[10m]) < 10
  for: 10m
  labels:
    severity: ticket

- alert: HighSaturation
  expr: 1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) > 0.9
  for: 10m
  labels:
    severity: ticket
```

从这里开始。只有当你在真实故障中发现遗漏了什么时，才添加更多告警。最常见的错误是在你理解"正常"是什么样之前就添加告警。

<!-- ZH_RESOURCES -->
- [Prometheus 告警规则](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/) -- 类型：文章，时长：20 分钟
- [Alertmanager 配置](https://prometheus.io/docs/alerting/latest/configuration/) -- 类型：文章，时长：20 分钟
- [我对告警的思考（Rob Ewaschuk，Google）](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- 类型：文章，时长：20 分钟
- [针对关键事项进行告警（Prometheus 文档）](https://prometheus.io/docs/practices/alerting/) -- 类型：文章，时长：15 分钟
- [PagerDuty 事件响应指南](https://response.pagerduty.com/) -- 类型：文章，时长：30 分钟

<!-- ZH_UI -->
1. 为四大黄金指标设置合理阈值的告警
2. 将告警路由到通知渠道（Slack、PagerDuty、邮件）
3. 理解基于原因告警与基于症状告警的区别
4. 通过消除噪音大、不可操作的告警来体验并减少告警疲劳
5. 我的手机每10分钟就因告警震动一次，团队已经开始无视它们了。我该怎么解决？
6. 我们的告警太多了，真正出问题时没人确定该先看哪一个。有一半时间有人直接静音寻呼机就为了睡个觉。我知道这很糟糕，但不知道怎么在不漏掉真实故障的情况下真正减少告警。
7. 一个东西坏了，我同时收到30条告警。我分不清哪个是真正的问题，哪些只是下游症状。
8. 数据库变慢，我收到数据库的告警、所有五个连它的服务的告警、依赖它的缓存的告警，还有积压的任务的告警。我得在一场同一秒爆发的告警风暴中排查问题。
9. 告警触发了。我能从指标看出有问题。怎么找出原因？
10. 我知道有东西坏了，但不知道在哪。我的服务变慢，但它调用了另外四个服务。指标显示有尖峰，但看不出是链路中哪一跳出了问题。我觉得我需要一张能还原某个具体请求实际发生了什么的地图。
