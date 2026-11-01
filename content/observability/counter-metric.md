---
id: counter-metric
title: Counters
zone: observability
edges:
  to:
    - id: prometheus-basics
      question: >-
        I understand counters now. How do I actually start collecting metrics
        from my running service?
      detail: >-
        I know I should use a counter for request counts and error counts. But
        I don't know how to actually wire this up. Where does the data go? What
        collects it? I've never instrumented a service before.
difficulty: 1
tags:
  - metrics
  - counters
  - prometheus
  - observability
category: concept
milestones:
  - Understand that counters only ever increase and reset to zero on restart
  - Know that you query counters with rate() or increase(), not the raw value
  - Instrument a counter for request count and error count in your service
  - Understand why a raw counter value is meaningless without rate()
title_zh: "计数器"

---


A counter is a metric that only ever goes up. It starts at zero when your process starts, and increments every time the thing you're tracking happens. Total requests handled, total errors thrown, total bytes written to disk — anything you're counting over the lifetime of the process is a counter. If the process restarts, the counter resets to zero and starts climbing again.

The critical thing to understand about counters: you almost never care about the raw value. A counter that reads `1,847,293` tells you that 1.8 million requests have been handled since the process last started. That number by itself is nearly useless — you don't know if that was over the last 5 minutes or the last 5 months. What you actually want to know is the rate: how many requests per second is the service handling right now? That's what `rate()` gives you.

The single most common counter mistake is using one for something that can decrease — memory usage, queue depth, active connections. These values go down as well as up, so a counter makes no semantic sense for them. If memory drops after garbage collection, a counter can't represent that. Use a gauge for anything that can go down.

<!-- DEEP_DIVE -->

## How counters work

When your process starts, the counter is zero. Every time the event occurs, you call `inc()` (or `add(n)` for batch operations). The value climbs monotonically. On restart it resets to zero and starts over. Prometheus knows how to handle this reset — when it sees a counter drop (because the process restarted), it treats the new series as starting fresh.

Here's what counter instrumentation looks like in Python and Go:

```python
# Python — prometheus_client library
from prometheus_client import Counter

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'status_code']
)

def handle_request(method, status_code):
    # ... handle the request ...
    REQUEST_COUNT.labels(method=method, status_code=status_code).inc()
```

```go
// Go — prometheus/client_golang library
var requestCount = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total number of HTTP requests",
    },
    []string{"method", "status_code"},
)

func init() {
    prometheus.MustRegister(requestCount)
}

func handleRequest(method, statusCode string) {
    // ... handle the request ...
    requestCount.WithLabelValues(method, statusCode).Inc()
}
```

## Querying counters with PromQL

**Never query the raw counter value in a dashboard or alert.** It's just the total since last restart — a number without context.

Instead, use `rate()` to calculate events per second over a time window:

```promql
# Requests per second, averaged over the last 5 minutes
rate(http_requests_total[5m])

# Only POST requests
rate(http_requests_total{method="POST"}[5m])

# Error rate as a percentage of total requests
rate(http_requests_total{status_code=~"5.."}[5m])
  /
rate(http_requests_total[5m])
* 100
```

Use `increase()` when you want the total increase over a window rather than the per-second rate:

```promql
# Total requests in the last hour (useful for billing, capacity planning)
increase(http_requests_total[1h])
```

The window you pass to `rate()` (the `[5m]` part) matters. A short window (1m) is more reactive and shows rapid changes, but is noisier. A longer window (15m) smooths out spikes but is slower to respond. For alerting, 5 minutes is a common starting point.

## The scrape interval and `rate()` window relationship

Prometheus scrapes metrics at a fixed interval (default 15 seconds). The window you pass to `rate()` must be at least 2x the scrape interval, or Prometheus may not have enough data points to compute the rate accurately. With a 15-second scrape interval, use at minimum `[30s]` — but `[5m]` is usually more appropriate for production alerting, since it filters out momentary spikes.

## Common counter mistakes

**Using a counter for something that decreases.** Memory, queue depth, active connections — these need a gauge. If you try to use a counter for memory and it goes from 512MB to 300MB, the counter would need to go backwards, which it can't. You'd either get a bogus value or an error.

**Querying the raw counter in alerts.** An alert like `http_requests_total > 1000000` will fire once and never reset. You almost certainly want `rate(http_requests_total[5m]) > 100` instead (more than 100 requests per second for 5 minutes).

**Too-wide or too-narrow rate windows.** `rate(http_requests_total[1s])` will produce almost no data because there's likely less than one scrape per second. `rate(http_requests_total[1h])` won't catch a traffic spike that lasted only a few minutes.

<!-- RESOURCES -->

- [Prometheus Counter type (official docs)](https://prometheus.io/docs/concepts/metric_types/#counter) -- type: article, time: 5m
- [How does a Prometheus Counter work?](https://www.robustperception.io/how-does-a-prometheus-counter-work/) -- type: article, time: 8m
- [rate() vs increase() in Prometheus](https://www.robustperception.io/rate-then-sum-never-sum-then-rate/) -- type: article, time: 10m
- [Prometheus: Up & Running (O'Reilly)](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- type: book, time: 360m

<!-- ZH_SUMMARY -->
计数器是一种只会上升的指标。它在进程启动时从零开始，每当被跟踪的事件发生时就会递增。处理的总请求数、抛出的总错误数、写入磁盘的总字节数——任何你在进程生命周期内持续计数的东西都是计数器。如果进程重启，计数器会重置为零并重新开始攀升。

关于计数器，最关键的一点是：你几乎从不关心原始值。一个读数为 `1,847,293` 的计数器告诉你，自进程上次启动以来已处理了 180 万个请求。这个数字本身几乎毫无用处——你不知道这是过去 5 分钟还是过去 5 个月内的累计量。你真正想知道的是速率：服务当前每秒处理多少请求？这正是 `rate()` 为你提供的。

最常见的计数器误用，是把计数器用于可能下降的事物——内存使用量、队列深度、活跃连接数。这些值既会上升也会下降，因此用计数器来表示它们在语义上毫无意义。如果垃圾回收后内存下降，计数器无法表达这一点。对于任何可能下降的事物，请使用 gauge。

<!-- ZH_DEEP_DIVE -->
## 计数器的工作原理

当你的进程启动时，计数器为零。每当事件发生时，你调用 `inc()`（或批量操作时调用 `add(n)`）。该值单调递增。重启后它会重置为零并重新开始。Prometheus 知道如何处理这种重置——当它看到计数器下降时（因为进程重启了），它会将新的序列视为从头开始。

以下是 Python 和 Go 中计数器埋点的样子：

```python
# Python — prometheus_client library
from prometheus_client import Counter

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'status_code']
)

def handle_request(method, status_code):
    # ... handle the request ...
    REQUEST_COUNT.labels(method=method, status_code=status_code).inc()
```

```go
// Go — prometheus/client_golang library
var requestCount = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total number of HTTP requests",
    },
    []string{"method", "status_code"},
)

func init() {
    prometheus.MustRegister(requestCount)
}

func handleRequest(method, statusCode string) {
    // ... handle the request ...
    requestCount.WithLabelValues(method, statusCode).Inc()
}
```

## 使用 PromQL 查询计数器

**绝不要在仪表盘或告警中查询计数器的原始值。** 它只是自上次重启以来的总量——一个没有上下文的数字。

相反，使用 `rate()` 计算某个时间窗口内每秒的事件数：

```promql
# Requests per second, averaged over the last 5 minutes
rate(http_requests_total[5m])

# Only POST requests
rate(http_requests_total{method="POST"}[5m])

# Error rate as a percentage of total requests
rate(http_requests_total{status_code=~"5.."}[5m])
  /
rate(http_requests_total[5m])
* 100
```

当你想要某个窗口内的总增量而非每秒速率时，使用 `increase()`：

```promql
# Total requests in the last hour (useful for billing, capacity planning)
increase(http_requests_total[1h])
```

传给 `rate()` 的窗口（即 `[5m]` 部分）很重要。短窗口（1m）反应更灵敏，能显示快速变化，但噪声更大。长窗口（15m）会平滑掉尖峰，但响应更慢。对于告警，5 分钟是一个常见的起点。

## 抓取间隔与 `rate()` 窗口的关系

Prometheus 以固定间隔抓取指标（默认 15 秒）。传给 `rate()` 的窗口必须至少是抓取间隔的 2 倍，否则 Prometheus 可能没有足够的数据点来准确计算速率。在 15 秒抓取间隔下，至少使用 `[30s]`——但在生产告警中，`[5m]` 通常更合适，因为它能过滤掉瞬时尖峰。

## 常见的计数器错误

**用计数器表示会减少的东西。** 内存、队列深度、活跃连接——这些需要 gauge。如果你试图用计数器表示内存，而它从 512MB 降到 300MB，计数器就需要倒退，而它做不到。你要么得到一个虚假的值，要么得到一个错误。

**在告警中查询原始计数器。** 像 `http_requests_total > 1000000` 这样的告警会触发一次，然后永远不会重置。你几乎肯定想要的是 `rate(http_requests_total[5m]) > 100`（5 分钟内每秒超过 100 个请求）。

**速率窗口过宽或过窄。** `rate(http_requests_total[1s])` 几乎不会产生数据，因为很可能每秒不到一次抓取。`rate(http_requests_total[1h])` 则无法捕捉仅持续几分钟的流量尖峰。

<!-- ZH_RESOURCES -->
- [Prometheus Counter 类型（官方文档）](https://prometheus.io/docs/concepts/metric_types/#counter) -- 类型：文章，时长：5 分钟
- [Prometheus Counter 是如何工作的？](https://www.robustperception.io/how-does-a-prometheus-counter-work/) -- 类型：文章，时长：8 分钟
- [Prometheus 中 rate() 与 increase() 的对比](https://www.robustperception.io/rate-then-sum-never-sum-then-rate/) -- 类型：文章，时长：10 分钟
- [Prometheus：Up & Running（O'Reilly）](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- 类型：书籍，时长：360 分钟

<!-- ZH_UI -->
1. 理解计数器只会递增，重启时会重置为零
2. 知道应使用 rate() 或 increase() 查询计数器，而非原始值
3. 在服务中为请求数和错误数埋点计数器
4. 理解为什么原始计数器值在没有 rate() 时毫无意义
5. 我现在理解计数器了。我该如何真正开始从运行中的服务采集指标？
6. 我知道应该用计数器统计请求数和错误数。但我不知道如何实际接起来。数据去哪里？谁来采集？我以前从未做过服务埋点。
