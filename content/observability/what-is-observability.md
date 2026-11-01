---
id: what-is-observability
title: What Is Observability?
zone: observability
edges:
  to:
    - id: your-first-logs
      question: OK I get it — logs, metrics, traces. But where do I actually start?
      detail: >-
        I've seen people mention logs, metrics, and traces but I don't know
        where to actually begin. Do I try to set up all three at once? If I
        only have time for one right now, which gives me the most value? I
        don't want to spend a week on the wrong thing.
    - id: metrics-and-monitoring
      question: >-
        I already know how logging works. How do I measure what my systems
        are actually doing over time?
      detail: >-
        I've set up logging before — I know about log levels, structured
        logs, aggregation. What I don't have is numbers — request rates,
        error percentages, latency. I want graphs that show me whether things
        are getting better or worse, not just a wall of text to search through.
difficulty: 1
tags:
  - observability
  - three-pillars
  - logs
  - metrics
  - tracing
  - concept
category: concept
milestones:
  - Explain what observability means and how it differs from monitoring
  - Name the three pillars and describe what question each one answers
  - Understand why all three pillars are needed — no single signal tells the full story
  - Identify which pillar helps with what during a real incident
title_zh: "什么是可观测性？"

---


Observability is the ability to understand the internal state of a system by looking at its external outputs. The word comes from control theory, but for SREs and developers it means something concrete: given that something has gone wrong, can you figure out what and why, purely from the signals your system is emitting? If the answer is yes, your system is observable. If the answer is "I need to SSH in and look around," it isn't.

The word gets thrown around a lot, but the underlying idea is straightforward. Observability is built on three types of signals, commonly called the three pillars: logs, metrics, and traces. Each one answers a different kind of question. Logs tell you *what happened*. Metrics tell you *how your system is performing over time*. Traces tell you *why a specific request was slow or failed*. You need all three because no single signal gives you the full picture.

Observability is often confused with monitoring, but they're different things that work together. Monitoring is about watching for known failure conditions and alerting when they're breached — error rate over 5%, disk over 90%. Observability is about being able to investigate what you don't already know to look for. Monitoring gets you the alert. Observability lets you diagnose what's actually wrong.

<!-- DEEP_DIVE -->

## The three pillars

### Logs: what happened

Logs are timestamped records of discrete events. Every time something happens in your application — a request came in, a query ran, an error was thrown, a user logged in — a log line records it. Logs are the most intuitive signal because they're just text you can read.

The strength of logs is specificity. A log line can tell you exactly what happened at exactly what time, for exactly which user, with exactly what input data. When something goes wrong, logs are where you look to understand the concrete sequence of events.

The weakness of logs is volume. A busy service might emit millions of log lines per hour, and making sense of that requires good tooling. Searching through raw logs for a needle in a haystack is painful without a proper query interface.

### Metrics: how is it performing

Metrics are numeric measurements recorded over time. Things like: how many requests per second is my service handling, what percentage of those requests are returning errors, how long is the p99 response time, how much memory is the process using. Metrics are aggregated — you're not storing one row per event, you're storing summaries over time intervals.

The strength of metrics is efficiency and dashboards. Because they're numbers, you can graph them, set alert thresholds on them, and answer "is this getting better or worse over time?" in seconds. Metrics are what power the dashboards on the big screen at an SRE team's wall.

The weakness of metrics is that they're lossy. When your error rate spikes to 12%, metrics tell you that. They don't tell you which users, which endpoint, what error message, or what the request looked like. To dig into the details, you need logs or traces.

### Traces: why is it slow

A trace is a record of a single request as it travels through your system — from the moment it hits your API, through every service call, database query, and cache lookup, until the response goes back. Each step is recorded as a "span," and the spans are assembled into a tree that shows exactly where time was spent.

Traces exist because modern systems are distributed. A slow request might be caused by a slow database query in service B, which is called by service A, which is called by your API. Without tracing, all you know is "this request took 4 seconds." With tracing, you can see that 3.8 of those seconds were spent waiting for a specific SQL query in a specific service.

The weakness of traces is setup cost. Tracing requires instrumenting your code — either manually or with an auto-instrumentation library — and running trace collection infrastructure. It's the most powerful of the three pillars and also the most expensive to set up.

## Why you need all three

It's tempting to think you can get away with one or two. You can't, at least not at any real scale. Here's why.

Imagine your error rate spikes (metrics alert you). You look at the metrics dashboard — error rate is 15%, up from 0.5% baseline. OK, something is wrong. But metrics don't tell you what. So you go to logs. You filter to errors and see a wave of `database: connection refused` messages. Now you know the what. But why is the database refusing connections? Is it overloaded? Did a connection pool exhaust? This is where traces would show you what's filling the connection pool — some set of requests that's holding connections open too long.

Each pillar narrows the problem down further. Metrics say something is wrong. Logs say what is wrong. Traces say why it's wrong and where in the call chain to look.

## Monitoring vs. observability

Monitoring is a subset of what observability enables. Monitoring means: I know in advance what failure modes look like, and I've set up alerts for them. Observability means: I can investigate failure modes I didn't anticipate.

Both matter. You need monitoring because you can't sit and watch dashboards all day — you need to be alerted when things go wrong. But you need observability because your monitoring will never cover every possible failure mode. Novel problems need investigation, and investigation requires being able to ask questions of your running system without having thought of the question in advance.

The practical way to think about it: monitoring is your smoke detector, observability is your ability to figure out where the fire is.

<!-- RESOURCES -->

- [Observability vs. Monitoring (Datadog)](https://www.datadoghq.com/knowledge-center/observability/) -- type: article, time: 10m
- [Logs vs Metrics vs Traces (Honeycomb)](https://www.honeycomb.io/blog/metrics-logs-and-traces-oh-my) -- type: article, time: 12m
- [What Is OpenTelemetry? (CNCF)](https://opentelemetry.io/docs/what-is-opentelemetry/) -- type: article, time: 8m
- [Observability Engineering (O'Reilly)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) -- type: book, time: 360m

<!-- ZH_SUMMARY -->
可观测性是指通过查看系统的外部输出来理解其内部状态的能力。这个词来自控制论，但对 SRE 和开发者来说，它意味着具体的东西：假设出了问题，你能仅凭系统发出的信号弄清楚是什么问题以及为什么吗？如果答案是肯定的，你的系统就是可观测的。如果答案是"我需要 SSH 进去看看"，那就不是。

这个词被频繁提及，但底层概念很直接。可观测性建立在三类信号之上，通常被称为三大支柱：日志、指标和追踪。每一类回答不同的问题。日志告诉你*发生了什么*。指标告诉你*系统随时间表现如何*。追踪告诉你*为什么某个特定请求慢或失败*。你需要全部三类，因为没有任何单一信号能给你完整的图景。

可观测性常与监控混淆，但它们是不同的事物，且协同工作。监控是关注已知的故障条件并在被突破时告警——错误率超过 5%、磁盘使用超过 90%。可观测性是能够调查你事先并不知道要寻找的东西。监控给你告警。可观测性让你诊断出实际哪里出了问题。

<!-- ZH_DEEP_DIVE -->
## 三大支柱

### 日志：发生了什么

日志是离散事件的时间戳记录。每当应用程序中发生某些事情——收到请求、执行查询、抛出错误、用户登录——都会有一条日志记录。日志是最直观的信号，因为它们就是你可以阅读的文本。

日志的优势在于具体性。一条日志可以准确告诉你：在什么时间、哪个用户、用什么输入数据、发生了什么。当出现问题时，日志是你了解具体事件序列的地方。

日志的劣势在于数据量。一个繁忙的服务每小时可能产生数百万条日志，要理解这些日志需要好的工具。如果没有合适的查询界面，在原始日志中大海捞针是非常痛苦的。

### 指标：性能如何

指标是随时间记录的数值测量。比如：我的服务每秒处理多少请求、这些请求中返回错误的百分比是多少、p99 响应时间有多长、进程使用了多少内存。指标是聚合的——你不是为每个事件存储一行记录，而是存储时间区间内的汇总数据。

指标的优势在于效率和仪表盘。因为它们是数字，你可以绘制图表、设置告警阈值，并在几秒钟内回答“情况是在变好还是变坏？”指标是 SRE 团队墙上大屏仪表盘的动力来源。

指标的劣势在于有损性。当错误率飙升到 12% 时，指标会告诉你这一点。但它们不会告诉你哪些用户、哪个端点、什么错误消息，或者请求长什么样。要深入细节，你需要日志或追踪。

### 追踪：为什么慢

追踪是对单个请求在系统中流转过程的记录——从请求到达 API 的那一刻起，经过每一次服务调用、数据库查询和缓存查找，直到响应返回。每一步都记录为一个“span”，这些 span 被组装成一棵树，精确显示时间花在了哪里。

追踪之所以存在，是因为现代系统是分布式的。一个慢请求可能是由服务 B 中一个慢数据库查询引起的，而服务 B 被服务 A 调用，服务 A 又被你的 API 调用。没有追踪，你只知道“这个请求花了 4 秒”。有了追踪，你可以看到其中 3.8 秒花在了等待某个特定服务中某个特定 SQL 查询上。

追踪的劣势在于搭建成本。追踪需要对代码进行埋点——无论是手动还是使用自动埋点库——并运行追踪收集基础设施。它是三大支柱中最强大的，也是搭建成本最高的。

## 为什么三者都需要

人们很容易认为一两个就够了。但在任何真实规模下，这是不够的。原因如下。

想象你的错误率飙升（指标告警通知你）。你查看指标仪表盘——错误率是 15%，而基线是 0.5%。好，出问题了。但指标不告诉你出了什么问题。于是你去看日志。你筛选错误，看到大量 `database: connection refused` 消息。现在你知道了是什么。但为什么数据库拒绝连接？是过载了？是连接池耗尽了吗？这时候追踪就能告诉你是什么在占满连接池——某组请求持有连接的时间过长。

每个支柱都进一步缩小问题范围。指标说明出了问题。日志说明出了什么问题。追踪说明为什么出问题以及应该在调用链的哪里排查。

## 监控与可观测性

监控是可观测性所赋能的一个子集。监控意味着：我事先知道故障模式长什么样，并且已经为它们设置了告警。可观测性意味着：我可以调查我没有预料到的故障模式。

两者都很重要。你需要监控，因为你不可能整天坐着盯仪表盘——你需要在出问题时被通知。但你需要可观测性，因为你的监控永远无法覆盖所有可能的故障模式。新问题需要调查，而调查要求你能够对运行中的系统提出问题，即使你事先并没有想到这个问题。

实用的思考方式：监控是你的烟雾探测器，可观测性是你弄清楚火在哪里的能力。

<!-- ZH_RESOURCES -->
- [可观测性与监控 (Datadog)](https://www.datadoghq.com/knowledge-center/observability/) -- 类型: 文章, 时长: 10m
- [日志 vs 指标 vs 追踪 (Honeycomb)](https://www.honeycomb.io/blog/metrics-logs-and-traces-oh-my) -- 类型: 文章, 时长: 12m
- [什么是 OpenTelemetry？(CNCF)](https://opentelemetry.io/docs/what-is-opentelemetry/) -- 类型: 文章, 时长: 8m
- [可观测性工程 (O'Reilly)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) -- 类型: 书籍, 时长: 360m

<!-- ZH_UI -->
1. 解释可观测性的含义以及它与监控的区别
2. 说出三大支柱并描述各自回答什么问题
3. 理解为什么三大支柱都不可或缺——没有任何单一信号能讲述完整故事
4. 识别在真实故障中哪个支柱在什么环节起作用
5. 好我懂了——日志、指标、追踪。但我到底该从哪里开始？
6. 我见过有人提到日志、指标和追踪，但我不知道实际该从哪入手。我要不要三个一起搭？如果现在只有时间做一个，哪个价值最大？我不想把一周时间花错地方。
7. 我已经知道日志怎么用了。我该如何随时间衡量系统实际在做什么？
8. 我以前搭过日志——我了解日志级别、结构化日志、聚合。我缺的是数字——请求率、错误百分比、延迟。我想要能看出情况在变好还是变差的图表，而不是一堵要搜索的文本墙。
