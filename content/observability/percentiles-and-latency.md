---
id: percentiles-and-latency
title: Percentiles and Latency
zone: observability
edges:
  to:
    - id: prometheus-basics
      question: >-
        I understand what I should be measuring now. How do I actually collect
        all of this in my running service?
      detail: >-
        I know I need counters for request counts, gauges for memory, histograms
        for latency — but I've never actually wired any of this up end to end.
        Where does the data go? What collects it? How does it get from my app
        into something I can query?
difficulty: 2
tags:
  - metrics
  - percentiles
  - latency
  - p99
  - observability
category: concept
milestones:
  - Explain why p99 latency is more useful than average latency
  - Understand how the "long tail" of slow requests affects user experience
  - Read a percentile from a histogram query in Prometheus
  - Understand why averaging percentiles across instances is statistically wrong
title_zh: "百分位数与延迟"

---


Average latency is the most dangerous metric in observability. It looks like useful information, it appears on every dashboard, and it will confidently hide the fact that a meaningful fraction of your users are having a terrible experience. If 95% of your requests complete in 10ms and 5% take 2 seconds, your average comes out around 110ms — a number that says "everything is fine" while thousands of users per minute stare at a spinner.

Percentiles tell the truth. The p99 latency — the 99th percentile — means that 99% of requests completed in that time or less. If your p99 is 2.1 seconds, you know that 1 in every 100 requests is slow enough to frustrate users. The p50 (median) tells you what a typical request looks like. The p95 shows you whether things are trending toward problematic. Running p50, p95, and p99 on the same graph gives you a complete picture of your latency distribution that an average can never provide.

The reason the slow requests matter is that they don't happen to a random sample of users — they happen repeatedly to the same users, on the same endpoints, under the same conditions. If checkout is your p99 endpoint, the users experiencing slow checkout are exactly the users most actively trying to give you money. A 1% slow rate sounds trivial in aggregate but lands disproportionately on your highest-intent users.

<!-- DEEP_DIVE -->

## Why average latency lies

Here's a concrete example. Suppose your API handles 1,000 requests per minute:

- 990 requests: 10ms each
- 10 requests: 5,000ms each (5 seconds — a timeout somewhere)

Average latency: `(990 × 10 + 10 × 5000) / 1000 = 59.9ms`

A dashboard showing 60ms average looks healthy. But 1% of your users are waiting 5 seconds. If this is a search endpoint and you handle 10 million requests per day, that's 100,000 requests per day where users are timing out or giving up.

Now look at the percentiles:
- p50: 10ms (the median request is fast)
- p95: 10ms (still fast — the problem is below the surface)
- p99: 5,000ms (now you see it — the worst 1% are terrible)
- p99.9: 5,000ms (same story)

The p99 immediately tells you there's a problem that the average was hiding.

## What each percentile means

| Percentile | Reading | What it tells you |
|-----------|---------|-------------------|
| **p50** | 50% of requests are faster than this | The experience for a typical user |
| **p75** | 75% of requests are faster than this | Upper-middle of the distribution |
| **p95** | 95% of requests are faster than this | Near-worst case for most users |
| **p99** | 99% of requests are faster than this | The tail — the slowest 1% |
| **p99.9** | 99.9% of requests are faster than this | The very worst (relevant at high scale) |

At 100 requests per second, p99 represents 1 request per second that's slow. At 10,000 requests per second, p99 represents 100 requests per second — a significant problem.

## The long tail

High-scale systems often exhibit what's called a "long tail" of latency — a small percentage of requests that are dramatically slower than the rest. These can be caused by:

- **GC pauses** — a garbage collection cycle blocks all threads for tens to hundreds of milliseconds
- **Lock contention** — a slow request holds a lock, queuing others behind it
- **Cold paths** — code or data that rarely executes and isn't cached
- **External dependencies** — a database or API call that occasionally times out
- **Resource exhaustion** — thread pool full, connection pool depleted, causing queuing

The long tail matters not just for individual user experience, but because slow requests often hold resources. A request blocked waiting for a database connection holds a thread. If the p99 requests hold threads for 5 seconds each, they're consuming 500x the resources of a normal request — and at scale, they can cause cascading failures.

## Querying percentiles in PromQL

Using a Prometheus histogram (see the Histograms node for instrumentation), you compute percentiles with `histogram_quantile()`:

```promql
# p50 (median) latency over the last 5 minutes
histogram_quantile(0.50,
  rate(http_request_duration_seconds_bucket[5m])
)

# p99 latency over the last 5 minutes
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket[5m])
)

# p99 latency, broken down by endpoint
histogram_quantile(0.99,
  sum by (endpoint, le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

The `le` label must be included in any `sum by()` that wraps a histogram — `histogram_quantile()` needs it to see the bucket boundaries.

## Why you must NOT average percentiles

This is a common and consequential mistake. If you have 3 instances of your service and each reports a p99 of 200ms, 250ms, and 300ms, the actual p99 across all instances is not the average of those three numbers (250ms). It could be anywhere in the range — you simply cannot know without the underlying data.

The mathematically correct approach is to aggregate the raw histogram buckets first, then compute the percentile:

```promql
# WRONG — averages pre-computed percentiles
avg(p99_latency_precomputed)

# RIGHT — aggregate buckets, then compute quantile
histogram_quantile(0.99,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

The `sum by (le)` adds up the bucket counts across all instances, giving you a single histogram that represents the full population of requests. Then `histogram_quantile()` computes the actual p99 across all of them. This is why Histograms are preferred over Summaries — Summaries pre-compute percentiles on each instance and can't be aggregated correctly.

## Practical alerting guidance

For production services, a common alerting setup:

- **Alert on p99 latency** — catches the tail that matters for user experience
- **Graph p50, p95, p99 together** — gives you the full shape of the distribution
- **Set SLO-based thresholds** — if your SLA says "95% of requests under 200ms," alert when `histogram_quantile(0.95, ...) > 0.2`

Alerting on p50 (median) is appropriate when even typical requests being slow would be a problem. Alerting on p99 catches outliers before they become widespread.

<!-- RESOURCES -->

- [Latency SLOs Done Right](https://www.circonus.com/2018/08/latency-slos-done-right/) -- type: article, time: 12m
- [Why Percentiles Don't Work the Way You Think](https://www.percona.com/blog/2021/05/04/why-percentile-don-t-work-the-way-you-think/) -- type: article, time: 10m
- [Histograms and Summaries (Prometheus docs)](https://prometheus.io/docs/practices/histograms/) -- type: article, time: 12m
- [How NOT to Measure Latency (Gil Tene, video)](https://www.youtube.com/watch?v=lJ8ydIuPFeU) -- type: video, time: 42m
- [The Tail at Scale (Google Research)](https://research.google/pubs/the-tail-at-scale/) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
平均延迟是可观测性中最危险的指标。它看起来像是有用信息，出现在每个仪表盘上，却会自信地掩盖一个事实：相当一部分用户正在经历糟糕的体验。如果 95% 的请求在 10ms 内完成，而 5% 的请求耗时 2 秒，你的平均值大约会算出 110ms——这个数字在说“一切正常”，而每分钟有成千上万的用户盯着加载转圈。

百分位数说出真相。p99 延迟——即第 99 百分位——意味着 99% 的请求在该时间内或更短时间内完成。如果你的 p99 是 2.1 秒，你就知道每 100 个请求中有 1 个慢到足以让用户沮丧。p50（中位数）告诉你典型请求的样子。p95 向你展示情况是否正朝着有问题的方向发展。在同一张图上绘制 p50、p95 和 p99，能给你一个平均值永远无法提供的完整延迟分布图景。

慢请求之所以重要，是因为它们并非随机发生在用户样本上——它们反复发生在同一批用户、同一批端点、同样的条件下。如果结账是你的 p99 端点，那么经历慢结账的用户，恰恰是最积极想给你付钱的用户。1% 的慢速率在总量上听起来微不足道，却不成比例地落在你意图最高的用户身上。

<!-- ZH_DEEP_DIVE -->
## 为什么平均延迟会骗人

这里有一个具体的例子。假设你的 API 每分钟处理 1,000 个请求：

- 990 个请求：每个 10ms
- 10 个请求：每个 5,000ms（5 秒——某处发生了超时）

平均延迟：`(990 × 10 + 10 × 5000) / 1000 = 59.9ms`

一个显示 60ms 平均值的仪表盘看起来很正常。但 1% 的用户正在等待 5 秒。如果这是一个搜索端点，而你每天处理 1,000 万个请求，那就是每天有 100,000 个请求让用户超时或放弃。

现在看看百分位数：
- p50：10ms（中位数请求很快）
- p95：10ms（仍然很快——问题藏在水面之下）
- p99：5,000ms（现在你看到了——最差的 1% 非常糟糕）
- p99.9：5,000ms（情况相同）

p99 立刻告诉你存在一个被平均值掩盖的问题。

## 每个百分位数的含义

| 百分位数 | 解读 | 它告诉你什么 |
|-----------|---------|-------------------|
| **p50** | 50% 的请求比这个值更快 | 典型用户的体验 |
| **p75** | 75% 的请求比这个值更快 | 分布的中上部分 |
| **p95** | 95% 的请求比这个值更快 | 大多数用户的接近最坏情况 |
| **p99** | 99% 的请求比这个值更快 | 尾部——最慢的 1% |
| **p99.9** | 99.9% 的请求比这个值更快 | 最差的情况（在大规模下才有意义） |

在每秒 100 个请求时，p99 代表每秒有 1 个请求很慢。在每秒 10,000 个请求时，p99 代表每秒有 100 个请求——这是一个显著的问题。

## 长尾

大规模系统常常表现出所谓的延迟“长尾”——一小部分请求比其他请求慢得多。这些可能由以下原因引起：

- **GC 暂停**——一次垃圾回收周期会阻塞所有线程数十到数百毫秒
- **锁竞争**——一个慢请求持有锁，导致其他请求排队等待
- **冷路径**——很少执行且未被缓存的代码或数据
- **外部依赖**——偶尔超时的数据库或 API 调用
- **资源耗尽**——线程池满、连接池耗尽，导致排队

长尾之所以重要，不仅因为个体用户体验，还因为慢请求通常会占用资源。一个等待数据库连接的请求会占用一个线程。如果 p99 请求每个占用线程 5 秒，它们消耗的资源是正常请求的 500 倍——在大规模下，它们可能导致级联故障。

## 在 PromQL 中查询百分位数

使用 Prometheus 直方图（关于埋点请参见 Histograms 节点），你可以用 `histogram_quantile()` 计算百分位数：

```promql
# p50 (median) latency over the last 5 minutes
histogram_quantile(0.50,
  rate(http_request_duration_seconds_bucket[5m])
)

# p99 latency over the last 5 minutes
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket[5m])
)

# p99 latency, broken down by endpoint
histogram_quantile(0.99,
  sum by (endpoint, le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

任何包裹直方图的 `sum by()` 都必须包含 `le` 标签——`histogram_quantile()` 需要它来查看桶边界。

## 为什么绝对不能对百分位数求平均

这是一个常见且后果严重的错误。如果你有 3 个服务实例，每个报告的 p99 分别是 200ms、250ms 和 300ms，那么所有实例的实际 p99 并不是这三个数字的平均值（250ms）。它可能在该范围内的任何位置——没有底层数据，你根本无法知道。

数学上正确的做法是先聚合原始直方图桶，然后计算百分位数：

```promql
# WRONG — averages pre-computed percentiles
avg(p99_latency_precomputed)

# RIGHT — aggregate buckets, then compute quantile
histogram_quantile(0.99,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

`sum by (le)` 将所有实例的桶计数相加，得到一个代表全部请求总体的单一历史图。然后 `histogram_quantile()` 计算所有请求的实际 p99。这就是为什么直方图优于摘要——摘要在每个实例上预先计算百分位数，无法正确聚合。

## 实用的告警指导

对于生产服务，一种常见的告警设置：

- **对 p99 延迟告警**——捕捉对用户体验重要的尾部
- **同时绘制 p50、p95、p99**——让你看到分布的完整形状
- **设置基于 SLO 的阈值**——如果你的 SLA 规定“95% 的请求在 200ms 以下”，那么当 `histogram_quantile(0.95, ...) > 0.2` 时告警

当即使典型请求变慢也会成为问题时，对 p50（中位数）告警是合适的。对 p99 告警可以在异常值变得普遍之前捕捉到它们。

<!-- ZH_RESOURCES -->
- [正确实现延迟 SLO](https://www.circonus.com/2018/08/latency-slos-done-right/) -- 类型: 文章, 时长: 12m
- [为什么百分位数并非你以为的那样工作](https://www.percona.com/blog/2021/05/04/why-percentile-don-t-work-the-way-you-think/) -- 类型: 文章, 时长: 10m
- [直方图与摘要（Prometheus 文档）](https://prometheus.io/docs/practices/histograms/) -- 类型: 文章, 时长: 12m
- [如何错误地测量延迟（Gil Tene，视频）](https://www.youtube.com/watch?v=lJ8ydIuPFeU) -- 类型: 视频, 时长: 42m
- [规模下的长尾（Google Research）](https://research.google/pubs/the-tail-at-scale/) -- 类型: 文章, 时长: 20m

<!-- ZH_UI -->
1. 解释为什么 p99 延迟比平均延迟更有用
2. 理解慢请求的“长尾”如何影响用户体验
3. 从 Prometheus 的直方图查询中读取百分位数
4. 理解为什么跨实例平均百分位数在统计上是错误的
5. 我现在明白应该测量什么了。但在运行中的服务里，我实际该如何收集所有这些数据？
6. 我知道请求数需要计数器、内存需要仪表、延迟需要直方图——但我从未真正端到端地把这些接起来过。数据去哪里？谁来收集？它如何从我的应用进入我可以查询的东西？
