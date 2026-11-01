---
id: histogram-metric
title: Histograms
zone: observability
edges:
  to:
    - id: percentiles-and-latency
      question: >-
        I've got a histogram but I don't understand the buckets or why everyone
        talks about p99 instead of just average latency.
      detail: >-
        The histogram is there but I don't know how to read it. There are all
        these "le" labels and bucket counts and I don't know what any of it
        means. My average latency looks fine but users are complaining the app
        is slow — I feel like I'm missing something important about how to
        interpret this data.
difficulty: 2
tags:
  - metrics
  - histograms
  - latency
  - percentiles
  - prometheus
  - observability
category: concept
milestones:
  - Understand what histogram buckets represent and how to configure them
  - Instrument a histogram for request duration in your service
  - Use histogram_quantile() to compute p50, p95, p99 latency from a histogram
  - Understand the tradeoff between bucket count and accuracy
title_zh: "直方图"

---


When a counter tells you "how many" and a gauge tells you "how much right now," a histogram tells you "what does the distribution look like?" It's designed for measuring things where a single number isn't enough — request latency is the classic example. You don't just want to know the average request duration; you want to know whether a few requests are ruining the experience for a subset of your users. Histograms make that question answerable.

The way a histogram works is by sorting observations into buckets. You define bucket boundaries upfront — say, 10ms, 50ms, 100ms, 500ms, 1s, 5s. Every time a request completes, Prometheus increments every bucket whose upper bound is greater than or equal to the request's duration. A 75ms request increments the 100ms, 500ms, 1s, and 5s buckets (but not the 10ms or 50ms buckets). The bucket counts are cumulative, which is why they always increase as the bucket size increases.

Three time series are created for each histogram metric: `_bucket` for each configured bucket, `_sum` for the running total of all observed values, and `_count` for the total number of observations. Using `histogram_quantile()` in PromQL, Prometheus interpolates across the bucket counts to estimate percentiles — like "90% of requests completed within X milliseconds."

<!-- DEEP_DIVE -->

## Histogram instrumentation

Here's what adding a histogram to a web service looks like:

```python
# Python — prometheus_client
from prometheus_client import Histogram
import time

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

def handle_request(method, endpoint):
    start = time.time()
    try:
        # ... handle the request ...
        pass
    finally:
        duration = time.time() - start
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
```

```go
// Go — prometheus/client_golang
var requestDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request duration in seconds",
        Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0},
    },
    []string{"method", "endpoint"},
)

func init() {
    prometheus.MustRegister(requestDuration)
}

func handleRequest(method, endpoint string, handler func()) {
    start := time.Now()
    handler()
    requestDuration.WithLabelValues(method, endpoint).Observe(time.Since(start).Seconds())
}
```

## What the /metrics output looks like

After some requests have been processed, the `/metrics` endpoint exposes something like this:

```
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.005"} 42
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.01"} 89
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.025"} 201
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.05"} 387
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.1"} 892
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.25"} 1204
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.5"} 1245
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="1.0"} 1247
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="2.5"} 1249
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="5.0"} 1249
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="10.0"} 1250
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="+Inf"} 1250
http_request_duration_seconds_sum{method="GET",endpoint="/api/users"} 52.847
http_request_duration_seconds_count{method="GET",endpoint="/api/users"} 1250
```

The `le` label means "less than or equal to" — it's the upper bound of each bucket. The `+Inf` bucket always equals the total count. The numbers are cumulative: the 0.1s bucket count (892) includes all requests that were also in the 0.005s through 0.05s buckets.

## Querying histograms in PromQL

```promql
# p99 latency for all GET /api/users requests
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket{method="GET",endpoint="/api/users"}[5m])
)

# p50, p95, and p99 together (run as separate queries or use recording rules)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Average request duration (from _sum and _count)
rate(http_request_duration_seconds_sum[5m])
  /
rate(http_request_duration_seconds_count[5m])
```

Note the `rate()` wrapping the bucket metric inside `histogram_quantile()`. This is because each bucket is a counter — it only ever increases. You need `rate()` to turn it into a per-second rate before computing the quantile, so you get the p99 over the recent time window rather than over all time since restart.

## Choosing bucket boundaries

Your buckets need to span the full range of values you expect, with enough resolution to give accurate percentile estimates. If all your requests take between 10ms and 200ms but you only have buckets at 0.1s and 1s, Prometheus has to interpolate across a large range and the p99 estimate could be quite inaccurate.

A practical approach:

1. Start with Prometheus's default buckets: `.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10` (all in seconds)
2. Run in production for a few days
3. Look at where your actual distribution falls — are most values in the 0.05–0.25s range?
4. Tighten the buckets in that range for more precision, and remove buckets at extremes you're not hitting

The tradeoff is storage. Each bucket is a separate time series. 10 buckets × 5 labels × 10 endpoints = 500 time series just for one histogram. More buckets means more storage and higher cardinality. Choose enough buckets to be accurate, not the maximum possible.

## A common mistake: high-cardinality labels

Don't put unique values in histogram labels. If you label by user ID, you'll create one set of histogram buckets per user — potentially millions of time series. Label by things with bounded cardinality: HTTP method, endpoint path (normalized, not including IDs), status code. This applies to all metric types but histograms are especially painful because each label combination multiplies by the number of buckets.

<!-- RESOURCES -->

- [Prometheus Histogram type (official docs)](https://prometheus.io/docs/concepts/metric_types/#histogram) -- type: article, time: 8m
- [How does a Prometheus Histogram work?](https://www.robustperception.io/how-does-a-prometheus-histogram-work/) -- type: article, time: 10m
- [Prometheus histogram_quantile() function](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile) -- type: article, time: 8m
- [Histograms and Summaries (official best practices)](https://prometheus.io/docs/practices/histograms/) -- type: article, time: 12m
- [Prometheus: Up & Running (O'Reilly)](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- type: book, time: 360m

<!-- ZH_SUMMARY -->
计数器告诉你“有多少”，gauge 告诉你“此刻是多少”，而 histogram 告诉你“分布长什么样？”它专为那些单个数字不足以描述的场景而设计——请求延迟就是经典例子。你不仅想知道平均请求时长，还想知道是否有少数请求正在毁掉一部分用户的体验。Histogram 让这个问题变得可回答。

Histogram 的工作原理是将观测值分入各个桶（bucket）。你预先定义桶边界——比如 10ms、50ms、100ms、500ms、1s、5s。每当一个请求完成，Prometheus 就会递增所有上界大于或等于该请求时长的桶。一个 75ms 的请求会递增 100ms、500ms、1s 和 5s 桶（但不会递增 10ms 或 50ms 桶）。桶计数是累积的，这就是为什么随着桶增大，计数总是递增。

每个 histogram 指标会创建三个时间序列：每个已配置桶对应一个 `_bucket`，`_sum` 表示所有观测值的累计总和，`_count` 表示观测总数。在 PromQL 中使用 `histogram_quantile()`，Prometheus 会在各桶计数之间进行插值，以估算百分位数——比如“90% 的请求在 X 毫秒内完成”。

<!-- ZH_DEEP_DIVE -->
## Histogram 埋点

下面是在 Web 服务中添加 histogram 的示例：

```python
# Python — prometheus_client
from prometheus_client import Histogram
import time

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

def handle_request(method, endpoint):
    start = time.time()
    try:
        # ... handle the request ...
        pass
    finally:
        duration = time.time() - start
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
```

```go
// Go — prometheus/client_golang
var requestDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request duration in seconds",
        Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0},
    },
    []string{"method", "endpoint"},
)

func init() {
    prometheus.MustRegister(requestDuration)
}

func handleRequest(method, endpoint string, handler func()) {
    start := time.Now()
    handler()
    requestDuration.WithLabelValues(method, endpoint).Observe(time.Since(start).Seconds())
}
```

## /metrics 输出示例

处理了一些请求之后，`/metrics` 端点会暴露类似下面的内容：

```
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.005"} 42
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.01"} 89
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.025"} 201
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.05"} 387
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.1"} 892
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.25"} 1204
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.5"} 1245
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="1.0"} 1247
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="2.5"} 1249
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="5.0"} 1249
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="10.0"} 1250
http_request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="+Inf"} 1250
http_request_duration_seconds_sum{method="GET",endpoint="/api/users"} 52.847
http_request_duration_seconds_count{method="GET",endpoint="/api/users"} 1250
```

`le` 标签表示 "less than or equal to"（小于或等于）——它是每个 bucket 的上界。`+Inf` bucket 始终等于总数。这些数字是累积的：0.1s bucket 的计数（892）包含了同样落在 0.005s 到 0.05s bucket 中的所有请求。

## 在 PromQL 中查询 histogram

```promql
# p99 latency for all GET /api/users requests
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket{method="GET",endpoint="/api/users"}[5m])
)

# p50, p95, and p99 together (run as separate queries or use recording rules)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Average request duration (from _sum and _count)
rate(http_request_duration_seconds_sum[5m])
  /
rate(http_request_duration_seconds_count[5m])
```

注意 `histogram_quantile()` 内部对 bucket 指标使用了 `rate()`。这是因为每个 bucket 都是一个 counter——它只会增加。你需要用 `rate()` 将其转换为每秒速率，然后再计算分位数，这样得到的是最近时间窗口内的 p99，而不是自重启以来的全时段 p99。

## 选择 bucket 边界

你的 bucket 需要覆盖你预期值的完整范围，并具备足够的分辨率以给出准确的分位数估计。如果你的所有请求耗时都在 10ms 到 200ms 之间，但你只在 0.1s 和 1s 处设置了 bucket，Prometheus 就必须在很大的范围内进行插值，p99 估计可能会相当不准确。

一个实用的方法：

1. 从 Prometheus 的默认 bucket 开始：`.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10`（单位均为秒）
2. 在生产环境运行几天
3. 观察实际分布落在哪里——大多数值是否在 0.05–0.25s 范围内？
4. 在该范围内收紧 bucket 以获得更高精度，并移除你未触及的极端值处的 bucket

权衡在于存储。每个 bucket 都是一个独立的时间序列。10 个 bucket × 5 个标签 × 10 个端点 = 仅一个 histogram 就有 500 个时间序列。更多的 bucket 意味着更多的存储和更高的基数。选择足够准确数量的 bucket，而不是尽可能多的 bucket。

## 常见错误：高基数标签

不要在 histogram 标签中放入唯一值。如果你按 user ID 打标签，就会为每个用户创建一组 histogram bucket——可能产生数百万个时间序列。应使用基数有界的标签：HTTP method、endpoint path（规范化后，不包含 ID）、status code。这适用于所有指标类型，但 histogram 尤其痛苦，因为每个标签组合都会乘以 bucket 数量。

<!-- ZH_RESOURCES -->
- [Prometheus Histogram 类型（官方文档）](https://prometheus.io/docs/concepts/metric_types/#histogram) -- 类型：文章，时长：8 分钟
- [Prometheus Histogram 是如何工作的？](https://www.robustperception.io/how-does-a-prometheus-histogram-work/) -- 类型：文章，时长：10 分钟
- [Prometheus histogram_quantile() 函数](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile) -- 类型：文章，时长：8 分钟
- [Histograms 与 Summaries（官方最佳实践）](https://prometheus.io/docs/practices/histograms/) -- 类型：文章，时长：12 分钟
- [Prometheus: Up & Running（O'Reilly）](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- 类型：书籍，时长：360 分钟

<!-- ZH_UI -->
1. 理解直方图桶（histogram buckets）代表什么以及如何配置它们
2. 在服务中为请求持续时间（request duration）埋点直方图
3. 使用 histogram_quantile() 从直方图计算 p50、p95、p99 延迟
4. 理解桶数量与准确性之间的权衡
5. 我已经有了一个直方图，但我不理解桶的含义，也不明白为什么大家都在讨论 p99 而不是只看平均延迟。
6. 直方图就在那里，但我不知道怎么读它。有各种“le”标签和桶计数，我完全不知道它们是什么意思。我的平均延迟看起来没问题，但用户抱怨应用很慢——我觉得自己在如何解读这些数据上漏掉了什么重要的东西。
