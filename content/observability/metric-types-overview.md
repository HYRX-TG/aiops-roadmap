---
id: metric-types-overview
title: Types of Metrics
zone: observability
edges:
  to:
    - id: counter-metric
      question: >-
        I want to track how many requests my service has handled. What type of
        metric do I use?
      detail: >-
        I want to count things — requests, errors, cache hits. I keep seeing
        the word "counter" but I don't really know what it means or how it
        differs from just storing a number somewhere.
    - id: gauge-metric
      question: >-
        I need to track things that go up and down — like memory usage or the
        number of active connections. Is there a metric type for that?
      detail: >-
        A counter keeps going up forever which doesn't make sense for memory or
        queue depth. I need something that reflects the current value right now,
        whatever that is.
    - id: histogram-metric
      question: >-
        I need to measure how long my requests are taking, especially the slow
        ones. How do I track a distribution instead of just a single value?
      detail: >-
        I want to know what percentage of my requests are slow — not just the
        average. Average latency hides the outliers. I've seen p99 mentioned
        everywhere but I don't know what kind of metric enables that.
difficulty: 1
tags:
  - metrics
  - counters
  - gauges
  - histograms
  - prometheus
  - observability
category: concept
milestones:
  - Name the four metric types in Prometheus and what each one is for
  - Choose the correct metric type for a given use case
  - Understand why using the wrong type produces misleading data
title_zh: "指标类型"

---


Prometheus defines four metric types: Counter, Gauge, Histogram, and Summary. Each one is designed to answer a different category of question about your system. Picking the right type isn't just a matter of style — the type determines what operations make sense on the data, and using the wrong one gives you numbers that look plausible but are fundamentally misleading.

The key insight is that the type tells you how the value behaves over time and what you can do with it. A counter only ever goes up, so the interesting question is always "how fast is it increasing?" A gauge can go in any direction, so you read it directly. A histogram records a distribution of observations, which is what you need when a single number isn't enough to describe what's happening. The fourth type, Summary, is older and less commonly used in new instrumentation — Histograms are generally preferred because they can be aggregated across instances.

Before you add a single metric to your service, you should understand which type fits what you're measuring. The wrong choice is surprisingly easy to make and surprisingly hard to notice — bad metric types produce data that looks fine until you're mid-incident and realise the numbers don't mean what you thought they did.

<!-- DEEP_DIVE -->

## The four types at a glance

| Type | Behaviour | Typical use | Key PromQL function |
|------|-----------|-------------|---------------------|
| **Counter** | Only increases, resets on restart | Total requests, total errors, bytes sent | `rate()`, `increase()` |
| **Gauge** | Can go up or down | Memory usage, active connections, queue depth | Direct query |
| **Histogram** | Samples observations into buckets | Request duration, response size | `histogram_quantile()` |
| **Summary** | Pre-computes quantiles client-side | Same as histogram, but with limitations | Direct query of pre-computed values |

## Why the type matters so much

Consider memory usage. Memory can be 512MB now, drop to 300MB after garbage collection, then climb to 600MB an hour later. If you tracked this as a counter, the value would just keep increasing forever, even as real memory usage fluctuated. The counter would tell you "6.2 million megabytes of memory have been used since the process started" — a number that is technically accurate and completely useless.

The opposite mistake: using a gauge for request counts. Gauges can go up or down. If you store "number of requests" as a gauge and your monitoring system samples it every 15 seconds, you'd store the instantaneous count at each sample. But what does "count" even mean at a moment in time? You'd lose the ability to accurately calculate rate, because you're not capturing the true cumulative total — you're capturing snapshots of some counter variable in your code.

Histograms are worth special attention. If you want to know that your p99 latency is under 200ms, you need a distribution — a single measurement like "average latency is 45ms" cannot tell you that. Histograms are specifically designed to capture distributions of observations so you can answer percentile questions later.

## Summary vs Histogram

You'll see both mentioned in documentation. The short version: use Histograms. Summaries pre-compute percentiles on the client side, which means you can't aggregate them across multiple service instances (you can't average percentiles — the math doesn't work). Histograms ship raw bucket data to Prometheus and let you compute percentiles at query time across the full population of requests, even across 50 instances.

The only advantage of Summary is slightly higher accuracy for the computed quantiles. In practice, correctly configured histogram buckets give you accuracy that's more than good enough, and the ability to aggregate across instances is almost always worth it.

## Choosing the right type

Ask yourself: what question am I trying to answer?

- "How many times did X happen since the service started?" → **Counter**
- "What is the current state of X right now?" → **Gauge**
- "What does the distribution of X look like? What's my p99?" → **Histogram**

If you're unsure, lean toward Histogram for anything that varies — it's the most flexible type and lets you answer questions you haven't thought of yet.

<!-- RESOURCES -->

- [Prometheus Metric Types (official docs)](https://prometheus.io/docs/concepts/metric_types/) -- type: article, time: 10m
- [Prometheus: Up & Running (O'Reilly)](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- type: book, time: 360m
- [How Prometheus Metric Types Work](https://grafana.com/blog/2022/03/01/how-prometheus-metric-types-work/) -- type: article, time: 12m

<!-- ZH_SUMMARY -->
Prometheus 定义了四种指标类型：Counter、Gauge、Histogram 和 Summary。每一种都旨在回答关于系统的不同类别的问题。选择正确的类型不仅仅是风格问题——类型决定了哪些操作对数据有意义，而使用错误的类型会得到看似合理但实际上具有根本性误导的数字。

关键的洞见在于，类型告诉你值随时间的行为方式以及你可以对它做什么。Counter 只会上升，所以有趣的问题始终是“它增长得有多快？”Gauge 可以朝任何方向变化，所以你可以直接读取它。Histogram 记录观测值的分布，当你用单个数字不足以描述正在发生的事情时，就需要它。第四种类型 Summary 较老，在新的埋点中不太常用——通常更倾向于使用 Histogram，因为它们可以跨实例进行聚合。

在向服务中添加哪怕一个指标之前，你都应该理解哪种类型适合你正在测量的内容。选错类型出奇地容易，而且出奇地难以察觉——错误的指标类型产生的数据看起来没问题，直到你正处于故障处理中，才意识到这些数字并不是你以为的含义。

<!-- ZH_DEEP_DIVE -->
## 四种类型一览

| 类型 | 行为 | 典型用途 | 关键 PromQL 函数 |
|------|-----------|-------------|---------------------|
| **Counter** | 只增不减，重启时重置 | 总请求数、总错误数、发送字节数 | `rate()`、`increase()` |
| **Gauge** | 可升可降 | 内存使用量、活跃连接数、队列深度 | 直接查询 |
| **Histogram** | 将观测值采样到桶中 | 请求耗时、响应大小 | `histogram_quantile()` |
| **Summary** | 在客户端预先计算分位数 | 与 histogram 相同，但有局限 | 直接查询预计算值 |

## 为什么类型如此重要

以内存使用量为例。内存现在可能是 512MB，垃圾回收后降到 300MB，一小时后攀升到 600MB。如果你把它当作 counter 来跟踪，这个值就会一直不断增加，即使实际内存使用量在波动。counter 会告诉你“自进程启动以来已使用 620 万 MB 内存”——这个数字技术上准确，但完全没用。

反过来的错误：用 gauge 记录请求数。Gauge 可升可降。如果你把“请求数”存为 gauge，监控系统每 15 秒采样一次，你存下的就是每个采样点的瞬时计数。但“计数”在某个时间点究竟意味着什么？你会失去准确计算速率的能力，因为你捕获的不是真正的累计总量——而是代码中某个计数器变量的快照。

Histogram 值得特别关注。如果你想知道 p99 延迟低于 200ms，你需要一个分布——“平均延迟是 45ms”这样的单一测量值无法告诉你这一点。Histogram 专门设计用于捕获观测值的分布，以便你之后回答百分位数问题。

## Summary 与 Histogram 对比

你会在文档中看到两者都被提及。简短版本：用 Histogram。Summary 在客户端预先计算百分位数，这意味着你无法跨多个服务实例聚合它们（你不能对百分位数求平均——数学上不成立）。Histogram 将原始桶数据发送到 Prometheus，让你在查询时跨全部请求总体计算百分位数，即使跨越 50 个实例也可以。

Summary 的唯一优势是计算出的分位数精度略高。在实践中，正确配置的 histogram 桶提供的精度已经足够好，而跨实例聚合的能力几乎总是值得的。

## 选择正确的类型

问自己：我想回答什么问题？

- “自服务启动以来 X 发生了多少次？” → **Counter**
- “X 现在的当前状态是什么？” → **Gauge**
- “X 的分布是什么样的？我的 p99 是多少？” → **Histogram**

如果不确定，对于任何会变化的东西都倾向于 Histogram——它是最灵活的类型，能让你回答还没想到的问题。

<!-- ZH_RESOURCES -->
- [Prometheus 指标类型（官方文档）](https://prometheus.io/docs/concepts/metric_types/) -- 类型：文章，时长：10m
- [Prometheus: Up & Running（O'Reilly）](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- 类型：书籍，时长：360m
- [Prometheus 指标类型如何工作](https://grafana.com/blog/2022/03/01/how-prometheus-metric-types-work/) -- 类型：文章，时长：12m

<!-- ZH_UI -->
1. 说出 Prometheus 中的四种指标类型及其各自用途
2. 为给定用例选择正确的指标类型
3. 理解为什么使用错误的类型会产生误导性数据
4. 我想跟踪我的服务已处理了多少请求。我该使用哪种指标类型？
5. 我想对事物计数——请求、错误、缓存命中。我不断看到“counter”这个词，但我并不真正理解它的含义，也不清楚它与仅仅在某处存一个数字有什么区别。
6. 我需要跟踪会上下波动的量——比如内存使用量或活跃连接数。有对应的指标类型吗？
7. counter 会一直上升，这对内存或队列深度来说说不通。我需要能反映当前瞬时值的东西，不管它是什么。
8. 我需要测量我的请求耗时，尤其是慢请求。我如何跟踪一个分布，而不是仅仅一个单一值？
9. 我想知道我的请求中有百分之多少是慢的——而不只是平均值。平均延迟会掩盖离群值。我到处都看到 p99 被提及，但我不知道是哪种指标类型能实现这一点。
