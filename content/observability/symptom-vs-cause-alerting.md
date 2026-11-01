---
id: symptom-vs-cause-alerting
title: Alert on Symptoms, Not Causes
zone: observability
edges:
  to:
    - id: distributed-tracing
      question: >-
        Alerts are cleaner now. But when one fires I still don't know how to
        find the actual cause. How do I debug across services?
      detail: >-
        I get paged, I see the symptom in the metrics, but I can't tell which
        of my five services is actually responsible. I need a way to follow a
        request through the whole system.
difficulty: 2
tags:
  - alerting
  - symptoms
  - causes
  - slo
  - observability
category: concept
milestones:
  - Understand the difference between symptom-based and cause-based alerts
  - Rewrite one cause-based alert as a symptom-based alert
  - Understand why alerting on user-visible impact reduces false positive rate
  - Know when cause-based alerts are still useful (capacity planning, early warning)
title_zh: "对症状而非原因进行告警"

---


When your database CPU spikes to 95%, how many alerts fire? Just the one? Or does the database alert fire, plus an alert for every service that queries the database (because their latency just went up), plus an alert for the cache layer that depends on those services, plus alerts for the background jobs that are now queuing up? If you've ever been paged into a storm of 25 simultaneous alerts that all started within three seconds of each other, you've experienced the cause-based alerting problem.

Cause-based alerts watch internal system state: CPU percentage, disk fill rate, pod restart count, memory usage, queue depth. These are the things engineers tend to reach for first because they're easy to measure and they feel like they should matter. The problem is that one user-facing failure can trigger dozens of these simultaneously — because in a distributed system, one root cause ripples through many components, each of which has its own alert watching its own internal state.

Symptom-based alerts watch user-visible impact instead: error rate, request latency, availability. When your database goes slow, your symptom-based alert fires once — "API error rate is above 1%" — and stays firing until the problem is resolved. The cause could be the database, a network partition, a bad deploy, or something else entirely. The alert doesn't need to know. It just tells you that users are being affected and someone needs to investigate.

<!-- DEEP_DIVE -->

## The Difference in Practice

Here's the same failure scenario — database becomes slow — and how each alerting strategy handles it.

**Cause-based alerting:**

- `DatabaseCPUHigh` fires (database CPU > 80%)
- `APIHighLatency` fires (API p99 > 2s, because it queries the database)
- `CheckoutServiceHighLatency` fires (checkout calls the API)
- `UserServiceDegraded` fires (user service queries the database directly)
- `BackgroundJobQueueDepth` fires (jobs are backing up because they can't write)
- `CacheHitRateLow` fires (cache is expiring and refetches are slow)

Six pages, all at once, all for one root cause. The on-call engineer is now trying to figure out which of these is the actual problem versus which are downstream consequences — while more alerts are potentially still coming.

**Symptom-based alerting:**

- `HighErrorRate` fires (error rate on API service > 1% for 5 minutes)

One page. The alert tells you what users are experiencing. The investigation — checking dashboards, looking at traces, querying metrics — tells you why.

## Writing Symptom-Based Alerts

The signal to alert on is user-visible impact. For most services, that maps directly to the four golden signals.

```yaml
# Symptom-based: users are seeing errors
- alert: HighErrorRate
  expr: |
    rate(http_requests_total{status=~"5.."}[5m])
    / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Error rate above 1% for 5 minutes"
    description: "{{ $value | humanizePercentage }} of requests are failing."

# Symptom-based: users are experiencing slowness
- alert: HighLatency
  expr: |
    histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "p99 latency above 2 seconds for 5 minutes"
    description: "99th percentile latency is {{ $value }}s."
```

Notice what these alerts don't mention: they don't say anything about CPU, memory, database, or any other internal component. They describe what the user is experiencing. That's the key property of a good symptom-based alert.

## When Cause-Based Alerts Are Still Useful

Symptom-based alerting doesn't mean you stop watching internal metrics. It means you separate them into two categories with different destinations.

**Page on symptoms.** These require immediate human attention because a user is being affected right now.

**Ticket on causes.** These are early warning signals that something is drifting toward a problem, but users aren't feeling it yet.

Cause-based alerts that belong as tickets:

```yaml
# Disk filling up — users aren't affected yet, but they will be
- alert: DiskFilling
  expr: |
    predict_linear(node_filesystem_avail_bytes[6h], 24 * 3600) < 0
  for: 30m
  labels:
    severity: ticket
  annotations:
    summary: "Disk predicted to fill within 24 hours"

# High memory — not a user problem yet, but a precursor to one
- alert: HighMemoryUsage
  expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
  for: 15m
  labels:
    severity: ticket
  annotations:
    summary: "Less than 10% memory available"
```

The rule is: **page on symptoms, ticket on causes.** Cause-based alerts are genuinely useful for capacity planning and early warning — they just shouldn't wake someone up.

## The Noise Reduction Effect

Beyond reducing the number of simultaneous pages during an incident, symptom-based alerts have a lower false positive rate for a structural reason: they require the problem to be visible to users before they fire.

CPU at 90% might or might not mean users are experiencing problems — CPUs spike all the time for legitimate reasons. But an error rate above 1% for five sustained minutes almost always means something real is wrong. The `for:` duration further filters out transient spikes. By the time the alert fires, you have high confidence that a human actually needs to look at it.

This is why symptom-based alerting and low alert fatigue tend to go together. When your alerts are anchored to user impact, the false positive rate drops dramatically, and the team starts trusting pages again.

## The Translation

If you're looking at an existing cause-based alert and trying to convert it, ask: what would a user experience if this internal condition got bad enough to matter?

| Cause-based alert | Symptom-based equivalent |
|---|---|
| Database CPU > 80% | API error rate > 1% OR API latency > 2s |
| Pod restarted | Service error rate elevated (crash-looping shows up here) |
| Queue depth > 10,000 | Job processing latency > 60s OR job failure rate elevated |
| Memory usage > 90% | Service returning 502s (OOM kills show up here) |
| Disk usage > 80% | Disk fill rate: ticket-level alert only |

The left column measures internal state. The right column measures user impact. For pages, you want the right column.

<!-- RESOURCES -->

- [My Philosophy on Alerting (Rob Ewaschuk, Google)](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- type: article, time: 20m
- [Alerting on What Matters (Prometheus docs)](https://prometheus.io/docs/practices/alerting/) -- type: article, time: 15m
- [The Four Golden Signals (Google SRE Book)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: article, time: 15m
- [SLOs, SLAs, and Error Budgets (Google SRE Book)](https://sre.google/sre-book/service-level-objectives/) -- type: article, time: 20m
- [Symptoms vs Causes in Alerting (Grafana blog)](https://grafana.com/blog/2023/05/30/the-right-and-wrong-way-to-alert/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
当数据库 CPU 飙升到 95% 时，会触发多少条告警？只有一条吗？还是说数据库告警会触发，再加上每个查询数据库的服务各触发一条告警（因为它们的延迟刚刚上升了），再加上依赖这些服务的缓存层触发一条告警，再加上现在开始排队的后台任务触发告警？如果你曾经被卷入过一场由 25 条同时触发的告警组成的风暴——它们全都在彼此相隔三秒内开始——那你就体验过基于原因的告警问题。

基于原因的告警监视内部系统状态：CPU 百分比、磁盘填充率、Pod 重启次数、内存使用量、队列深度。这些是工程师们往往最先想到的东西，因为它们容易测量，而且感觉它们应该很重要。问题在于，一次面向用户的故障可以同时触发几十条这样的告警——因为在分布式系统中，一个根因会波及许多组件，而每个组件都有自己的告警在监视自己的内部状态。

基于症状的告警则监视用户可见的影响：错误率、请求延迟、可用性。当你的数据库变慢时，基于症状的告警只触发一次——“API 错误率高于 1%”——并持续触发，直到问题解决。原因可能是数据库、网络分区、一次糟糕的部署，或者完全是别的什么。告警不需要知道原因。它只是告诉你用户正在受到影响，需要有人去调查。

<!-- ZH_DEEP_DIVE -->
## 实践中的差异

下面是同一个故障场景——数据库变慢——以及每种告警策略如何处理它。

**基于原因的告警：**

- `DatabaseCPUHigh` 触发（数据库 CPU > 80%）
- `APIHighLatency` 触发（API p99 > 2s，因为它要查询数据库）
- `CheckoutServiceHighLatency` 触发（checkout 调用 API）
- `UserServiceDegraded` 触发（用户服务直接查询数据库）
- `BackgroundJobQueueDepth` 触发（任务因无法写入而积压）
- `CacheHitRateLow` 触发（缓存过期，重新获取变慢）

六个告警，同时触发，全都源于同一个根因。值班工程师现在要弄清楚这些告警中哪个是真正的问题、哪些是下游后果——而与此同时可能还有更多告警正在到来。

**基于症状的告警：**

- `HighErrorRate` 触发（API 服务的错误率在 5 分钟内 > 1%）

一个告警。它告诉你用户正在经历什么。而调查——查看仪表盘、追踪链路、查询指标——会告诉你原因。

## 编写基于症状的告警

应当告警的信号是用户可见的影响。对大多数服务而言，这直接对应四大黄金信号。

```yaml
# 基于症状：用户正在遇到错误
- alert: HighErrorRate
  expr: |
    rate(http_requests_total{status=~"5.."}[5m])
    / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Error rate above 1% for 5 minutes"
    description: "{{ $value | humanizePercentage }} of requests are failing."

# 基于症状：用户正在经历变慢
- alert: HighLatency
  expr: |
    histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "p99 latency above 2 seconds for 5 minutes"
    description: "99th percentile latency is {{ $value }}s."
```

注意这些告警没有提到什么：它们完全没有提及 CPU、内存、数据库或任何其他内部组件。它们描述的是用户正在经历的情况。这就是一个好的基于症状的告警的关键特征。

## 基于原因的告警何时仍然有用

基于症状的告警并不意味着你不再关注内部指标。它意味着你要把它们分成两类，并送往不同的目的地。

**对症状发起告警（page）。** 这些需要立即的人工关注，因为用户此刻正受到影响。

**对原因创建工单（ticket）。** 这些是早期预警信号，表明某些东西正在朝问题方向漂移，但用户尚未感受到。

应作为工单的基于原因的告警：

```yaml
# 磁盘即将写满——用户尚未受影响，但很快会受影响
- alert: DiskFilling
  expr: |
    predict_linear(node_filesystem_avail_bytes[6h], 24 * 3600) < 0
  for: 30m
  labels:
    severity: ticket
  annotations:
    summary: "Disk predicted to fill within 24 hours"

# 内存偏高——目前还不是用户问题，但已是问题的前兆
- alert: HighMemoryUsage
  expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
  for: 15m
  labels:
    severity: ticket
  annotations:
    summary: "Less than 10% memory available"
```

规则是：**对症状发起告警，对原因创建工单。** 基于原因的告警对容量规划和早期预警确实有用——只是它们不应该把人叫醒。

## 降噪效果

除了在事故期间减少同时触发的告警数量之外，基于症状的告警还具有更低的误报率，这有其结构性原因：它们要求问题在触发之前已经对用户可见。

CPU 达到 90% 可能意味着用户正在经历问题，也可能不意味着——CPU 因合理原因出现尖峰是常有的事。但错误率在持续五分钟内高于 1%，几乎总是意味着确实出了问题。`for:` 持续时间进一步过滤掉了瞬时尖峰。等到告警触发时，你已经有很高的信心认为确实需要人工介入查看。

这就是为什么基于症状的告警和低告警疲劳往往相伴出现。当你的告警锚定在用户影响上时，误报率会大幅下降，团队也会重新开始信任告警。

## 转换对照

如果你正在审视一个现有的基于原因的告警并试图转换它，请问：如果这个内部状况恶化到足以产生影响的程度，用户会经历什么？

| 基于原因的告警 | 基于症状的等价物 |
|---|---|
| 数据库 CPU > 80% | API 错误率 > 1% 或 API 延迟 > 2s |
| Pod 重启 | 服务错误率升高（崩溃循环会在这里体现） |
| 队列深度 > 10,000 | 任务处理延迟 > 60s 或任务失败率升高 |
| 内存使用率 > 90% | 服务返回 502（OOM kill 会在这里体现） |
| 磁盘使用率 > 80% | 磁盘填充速率：仅工单级告警 |

左列衡量的是内部状态。右列衡量的是用户影响。对于告警（page），你需要的是右列。

<!-- ZH_RESOURCES -->
- [我对告警的思考 (Rob Ewaschuk, Google)](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit) -- 类型: 文章, 时间: 20分钟
- [针对重要事项进行告警 (Prometheus 文档)](https://prometheus.io/docs/practices/alerting/) -- 类型: 文章, 时间: 15分钟
- [四大黄金信号 (Google SRE 手册)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型: 文章, 时间: 15分钟
- [SLO、SLA 与错误预算 (Google SRE 手册)](https://sre.google/sre-book/service-level-objectives/) -- 类型: 文章, 时间: 20分钟
- [告警中的症状与原因 (Grafana 博客)](https://grafana.com/blog/2023/05/30/the-right-and-wrong-way-to-alert/) -- 类型: 文章, 时间: 10分钟

<!-- ZH_UI -->
1. 理解基于症状的告警与基于原因的告警之间的区别
2. 将一条基于原因的告警改写为基于症状的告警
3. 理解为什么针对用户可见影响进行告警能降低误报率
4. 了解基于原因的告警在何时仍然有用（容量规划、早期预警）
5. 现在告警更清晰了。但当告警触发时，我仍然不知道如何找到实际原因。如何跨服务进行调试？
6. 我收到了告警，在指标中看到了症状，但无法判断五个服务中究竟是哪一个真正负责。我需要一种能跟踪请求贯穿整个系统的方法。
