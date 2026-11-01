---
id: metrics-and-monitoring
title: Metrics and Monitoring
zone: observability
edges:
  to:
    - id: metric-types-overview
      question: >-
        I keep seeing counters, gauges, and histograms mentioned. What's the
        difference and which one should I use?
      detail: >-
        I just want to track things but apparently the type matters. I tried
        using a counter for memory usage and got nonsense. I need to understand
        what each type is actually for before I instrument anything else.
    - id: red-method
      question: >-
        I know I should track metrics but I have no idea which ones matter for
        my service. Where do I even start?
      detail: >-
        I could instrument a hundred different things. I have no idea which
        ones will tell me whether my service is healthy or not. I need a
        framework for deciding what to measure.
    - id: use-method
      question: >-
        My service looks fine but the host it runs on seems stressed. What
        should I be measuring at the infrastructure level?
      detail: >-
        The app metrics look normal but the server is clearly struggling — CPU
        spikes, something is saturating. I don't know what to actually measure
        to understand whether the machine itself is the problem.
    - id: prometheus-basics
      question: OK I understand what metrics are. How do I actually collect and store them?
      detail: >-
        The concept makes sense. But I don't know how metrics get from my app
        into something I can query. Do I push them somewhere? Does something
        pull them? What's the standard way to do this?
difficulty: 1
tags:
  - metrics
  - prometheus
  - cloudwatch
  - four-golden-signals
  - monitoring
  - observability
category: practice
milestones:
  - >-
    Instrument your application to expose the four golden signals: latency,
    traffic, errors, saturation
  - Collect metrics with Prometheus or CloudWatch
  - 'Understand the difference between counters, gauges, and histograms'
  - Explain why p99 latency is more informative than average latency
title_zh: "指标与监控"

---


Metrics are numerical measurements recorded over time. Every 15 seconds (or whatever interval you configure), your monitoring system records a number — the current CPU usage, the total number of requests handled, the amount of memory in use — and stores it with a timestamp. That's it. Metrics are simple, compact, and cheap to store compared to logs.

Logs are different. When something happens — a request comes in, an error is thrown, a user logs in — you write a line of text describing that event. Logs are great for understanding what happened in detail, but they're the wrong tool for performance questions. If you want to know your average request rate over the last hour, you'd have to scan every log line, parse each one, count the requests, and divide. With metrics, that question is a single query against pre-aggregated numbers. Metrics are designed for the kinds of questions you ask constantly during normal operations and during incidents.

The key distinction: logs are individual events, metrics are aggregated measurements. A log entry says "this specific request took 230ms." A metric says "the 99th percentile of all request durations over the last 5 minutes was 450ms." You need both — logs to diagnose what went wrong in a specific case, metrics to know that something is wrong at all and to understand the scope of the problem. The typical workflow is: metrics alert you, logs help you investigate.

<!-- DEEP_DIVE -->

## What metrics actually are

A metric is a time series: a sequence of (timestamp, value) pairs associated with a name and a set of labels. For example:

```
http_requests_total{method="GET", status="200"} 104732  @ 1709000000
http_requests_total{method="GET", status="200"} 104891  @ 1709000015
http_requests_total{method="GET", status="200"} 105043  @ 1709000030
```

The name tells you what you're measuring. The labels let you slice the data — you can query for just POST requests, or just 5xx errors, without needing separate metric names for each combination. The value is the measurement at that moment. And the timestamp tells you when.

This structure is stored in a **time series database (TSDB)**. Unlike a regular database, a TSDB is optimised for writing many data points rapidly and reading ranges of data over time. Prometheus, InfluxDB, and Graphite are examples. Cloud providers have their own: CloudWatch (AWS), Cloud Monitoring (GCP), Azure Monitor. They all work on the same fundamental idea — names, labels, values, timestamps.

## Why logs aren't enough for performance monitoring

Imagine your service is handling 500 requests per second. Over an hour, that's 1.8 million log lines just for request logs. Asking "what was the p99 latency over the last hour?" against that data means parsing 1.8 million lines in real time. Even if you can do it, you'll be doing it again in 5 minutes when the next person checks.

Metrics pre-aggregate this. Instead of storing each individual request duration, you record a distribution every 15 seconds. The data you store is tiny. The query is fast. And it works the same whether you're handling 10 requests per second or 10,000.

This doesn't mean logs are useless — they're essential. But their job is different. Metrics tell you something is wrong. Logs tell you why.

## The four golden signals

Google's Site Reliability Engineering book describes four signals that, together, cover most of what you need to know about a service's health:

| Signal | What it answers | Example metric |
|--------|----------------|----------------|
| **Latency** | How long are requests taking? | p99 request duration |
| **Traffic** | How much demand is there? | Requests per second |
| **Errors** | How often are requests failing? | Error rate (%) |
| **Saturation** | How full is the system? | CPU %, queue depth |

If you're just starting out, instrument these four things and you'll have dramatically better visibility than most teams running purely on logs. The RED and USE methods (linked from this node) give you more structured frameworks for thinking about which specific metrics to collect.

## Metrics vs logs vs traces

These three are sometimes called "the three pillars of observability." They're complementary, not competing:

- **Metrics** — aggregate numbers over time. Fast to query. Great for alerting and dashboards.
- **Logs** — structured or unstructured event records. Great for debugging specific incidents.
- **Traces** — records of a single request's journey through distributed services. Great for understanding latency in microservices.

Most teams start with metrics and logs, then add tracing as their systems become more complex. Don't feel like you need all three from day one.

<!-- RESOURCES -->

- [Metrics, Logs and Traces: The Golden Triangle of Observability](https://grafana.com/blog/2016/01/05/logs-and-metrics-and-graphs-oh-my/) -- type: article, time: 10m
- [The Four Golden Signals (SRE Book)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: article, time: 15m
- [An introduction to metrics, monitoring, and alerting (DigitalOcean)](https://www.digitalocean.com/community/tutorials/an-introduction-to-metrics-monitoring-and-alerting) -- type: article, time: 20m
- [Monitoring and Observability (Cindy Sridharan)](https://copyconstruct.medium.com/monitoring-and-observability-8417d1952e1c) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
指标是随时间记录的数值测量。每隔 15 秒（或你配置的任何间隔），你的监控系统会记录一个数字——当前 CPU 使用率、已处理请求总数、已使用内存量——并将其与时间戳一起存储。就是这样。与日志相比，指标简单、紧凑且存储成本低。

日志则不同。当某件事发生时——一个请求进来、抛出一个错误、一个用户登录——你会写一行文本描述该事件。日志非常适合详细理解发生了什么，但对于性能问题来说却是错误的工具。如果你想知道过去一小时的平均请求速率，你就必须扫描每一行日志、解析每一行、统计请求数，然后相除。而使用指标，这个问题就是对预聚合数字的一次查询。指标正是为你在日常运维和事故期间不断提出的那类问题而设计的。

关键区别在于：日志是单个事件，指标是聚合测量。一条日志条目说“这个特定请求耗时 230ms”。一个指标说“过去 5 分钟内所有请求时长的第 99 百分位数为 450ms”。两者你都需要——日志用于诊断特定案例中出了什么问题，指标用于知道确实出了问题以及理解问题的范围。典型的工作流程是：指标向你发出告警，日志帮助你调查。

<!-- ZH_DEEP_DIVE -->
## 指标究竟是什么

指标就是一条时间序列：一系列与某个名称和一组标签相关联的 (timestamp, value) 对。例如：

```
http_requests_total{method="GET", status="200"} 104732  @ 1709000000
http_requests_total{method="GET", status="200"} 104891  @ 1709000015
http_requests_total{method="GET", status="200"} 105043  @ 1709000030
```

名称告诉你正在测量什么。标签让你能够对数据进行切片——你可以只查询 POST 请求，或只查询 5xx 错误，而无需为每种组合单独设置指标名称。值是该时刻的测量结果。时间戳则告诉你测量发生的时间。

这种结构存储在**时间序列数据库（TSDB）**中。与常规数据库不同，TSDB 针对快速写入大量数据点以及按时间范围读取数据进行了优化。Prometheus、InfluxDB 和 Graphite 都是例子。云提供商也有自己的方案：CloudWatch（AWS）、Cloud Monitoring（GCP）、Azure Monitor。它们都基于相同的基本理念——名称、标签、值、时间戳。

## 为什么日志不足以支撑性能监控

假设你的服务每秒处理 500 个请求。一小时内，仅请求日志就有 180 万行。要针对这些数据回答“过去一小时的 p99 延迟是多少？”，意味着需要实时解析 180 万行。即使你能做到，5 分钟后下一个人来检查时，你又要再做一遍。

指标对此进行了预聚合。与其存储每个单独的请求耗时，不如每 15 秒记录一次分布。你存储的数据量很小。查询速度很快。而且无论你每秒处理 10 个请求还是 10,000 个请求，效果都一样。

这并不意味着日志没有用——它们至关重要。但它们的职责不同。指标告诉你出了问题。日志告诉你原因。

## 四大黄金信号

Google 的《Site Reliability Engineering》一书描述了四个信号，它们合在一起覆盖了服务健康状况的大部分关键信息：

| 信号 | 它回答的问题 | 示例指标 |
|--------|----------------|----------------|
| **延迟（Latency）** | 请求需要多长时间？ | p99 请求耗时 |
| **流量（Traffic）** | 需求有多大？ | 每秒请求数 |
| **错误（Errors）** | 请求失败的频率如何？ | 错误率（%） |
| **饱和度（Saturation）** | 系统有多满？ | CPU %、队列深度 |

如果你刚刚起步，先对这些四项进行埋点，你的可见性就会比大多数仅依赖日志运行的团队好得多。RED 和 USE 方法（链接自本节点）为你提供了更结构化的框架，用于思考应收集哪些具体指标。

## 指标 vs 日志 vs 追踪

这三者有时被称为“可观测性的三大支柱”。它们是互补的，而非相互竞争的：

- **指标（Metrics）**——随时间变化的聚合数值。查询速度快。非常适合告警和仪表盘。
- **日志（Logs）**——结构化或非结构化的事件记录。非常适合调试特定事件。
- **追踪（Traces）**——单个请求在分布式服务中流转过程的记录。非常适合理解微服务中的延迟。

大多数团队从指标和日志开始，随着系统变得更加复杂再添加追踪。不必觉得从第一天起就需要全部三者。

<!-- ZH_RESOURCES -->
- [指标、日志和追踪：可观测性的黄金三角](https://grafana.com/blog/2016/01/05/logs-and-metrics-and-graphs-oh-my/) -- 类型：文章，时长：10分钟
- [四大黄金信号（SRE 手册）](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型：文章，时长：15分钟
- [指标、监控和告警简介（DigitalOcean）](https://www.digitalocean.com/community/tutorials/an-introduction-to-metrics-monitoring-and-alerting) -- 类型：文章，时长：20分钟
- [监控与可观测性（Cindy Sridharan）](https://copyconstruct.medium.com/monitoring-and-observability-8417d1952e1c) -- 类型：文章，时长：20分钟

<!-- ZH_UI -->
1. 为应用埋点以暴露四大黄金信号：延迟、流量、错误、饱和度
2. 使用 Prometheus 或 CloudWatch 采集指标
3. 理解计数器、仪表和直方图之间的区别
4. 解释为什么 p99 延迟比平均延迟更有参考价值
5. 我总是看到计数器、仪表和直方图这些说法。它们有什么区别，我该用哪一种？
6. 我只想跟踪一些东西，但显然类型很重要。我试着用计数器记录内存使用量，结果完全不对。在继续埋点之前，我需要弄清楚每种类型到底是干什么用的。
7. 我知道应该跟踪指标，但完全不知道哪些指标对我的服务重要。我该从哪里开始？
8. 我可以埋点上百种东西。但我不知道哪些能告诉我服务是否健康。我需要一个框架来决定该测量什么。
9. 我的服务看起来正常，但它运行的主机似乎压力很大。在基础设施层面我应该测量什么？
10. 应用指标看起来正常，但服务器明显在挣扎——CPU 飙升，有东西正在饱和。我不知道该实际测量什么才能判断机器本身是不是问题所在。
11. 好，我理解指标是什么了。我到底该怎么采集和存储它们？
12. 概念说得通。但我不知道指标如何从我的应用进入可查询的地方。是我把它们推送到某处？还是有东西来拉取？标准做法是什么？
