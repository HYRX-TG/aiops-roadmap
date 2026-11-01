---
id: gauge-metric
title: Gauges
zone: observability
edges:
  to:
    - id: prometheus-basics
      question: >-
        I get gauges. How do I actually instrument my service to expose all of
        these metrics?
      detail: >-
        I know what I want to measure now — counters for events, gauges for
        current state. But I've never actually added metrics to a real service.
        Where does the data even go and what reads it?
difficulty: 1
tags:
  - metrics
  - gauges
  - prometheus
  - observability
category: concept
milestones:
  - Understand that a gauge can go up and down and represents a current state
  - Know when to use a gauge vs a counter
  - Instrument a gauge for active connections, queue depth, and memory usage
  - Understand why averaging gauges over time can be misleading
title_zh: "仪表"

---


A gauge represents the current value of something. It can go up, go down, or stay the same — whatever the real value is right now. Memory usage, number of active HTTP connections, the depth of a job queue, the current temperature of a server, the number of goroutines running — anything where you want to know the present state is a gauge.

Unlike counters, you read gauge values directly. If a gauge reads 847, that means there are 847 of whatever you're measuring right now. You don't need to apply `rate()` or any other transformation to make the value meaningful. This makes gauges simpler to query but also simpler to misuse — because what you get back is a snapshot, and snapshots can mislead you.

The sampling problem is real: Prometheus scrapes your metrics every 15 seconds by default. If your memory usage spikes to 90% for 3 seconds between scrapes, you'll never see it. The gauge will show the values at each scrape point, and a brief spike between two scrapes is invisible. This matters most for values that change rapidly and where peaks are dangerous.

<!-- DEEP_DIVE -->

## How gauges work

A gauge can be set to an absolute value, incremented, or decremented. Your code updates it directly to reflect the current state:

```python
# Python — prometheus_client library
from prometheus_client import Gauge

MEMORY_USAGE = Gauge(
    'process_memory_bytes',
    'Current memory usage in bytes'
)

ACTIVE_CONNECTIONS = Gauge(
    'http_active_connections',
    'Number of currently active HTTP connections'
)

# Set to an absolute value
MEMORY_USAGE.set(process_memory_bytes())

# Increment when a connection opens
def on_connection_open():
    ACTIVE_CONNECTIONS.inc()

# Decrement when a connection closes
def on_connection_close():
    ACTIVE_CONNECTIONS.dec()
```

```go
// Go — prometheus/client_golang
var activeConnections = prometheus.NewGauge(prometheus.GaugeOpts{
    Name: "http_active_connections",
    Help: "Number of currently active HTTP connections",
})

func init() {
    prometheus.MustRegister(activeConnections)
}

func handleConnect() {
    activeConnections.Inc()
    defer activeConnections.Dec()
    // ... handle connection ...
}
```

## Querying gauges in PromQL

Gauge queries are simpler than counter queries because you're working with real values, not rates. You can query the current value, compute averages over time, find the maximum, or compare to a threshold:

```promql
# Current memory usage across all instances
process_memory_bytes

# Average memory usage over the last 5 minutes (smooths noise)
avg_over_time(process_memory_bytes[5m])

# Maximum memory across all instances of a service
max(process_memory_bytes{service="api"})

# Alert: queue depth has been above 100 for 10 minutes
job_queue_depth > 100

# Memory usage as a percentage of a 2GB limit
process_memory_bytes / (2 * 1024 * 1024 * 1024) * 100
```

## Common gauge use cases

| What to measure | Metric name pattern | Notes |
|----------------|---------------------|-------|
| Memory usage | `process_memory_bytes` | Set from OS stats periodically |
| Active HTTP connections | `http_active_connections` | Inc on connect, dec on close |
| Job queue depth | `queue_depth` | Set from queue API |
| Cache hit ratio | `cache_hit_ratio` | Recompute and set periodically |
| CPU temperature | `hardware_cpu_temp_celsius` | Set from host metrics exporter |
| Number of open file descriptors | `process_open_fds` | Often auto-exported by client libs |

Many infrastructure gauges — CPU usage, memory, disk — are collected by Prometheus exporters (like `node_exporter`) rather than instrumented in your application code. You don't need to write code to track host memory; you just run node_exporter on the host and Prometheus scrapes it.

## The gotcha: gauges and missed peaks

Imagine your job queue spikes to 10,000 items and drains back to 0 in 8 seconds. With a 15-second scrape interval, it's possible Prometheus captured 0 items at scrape N, and 0 items at scrape N+1, completely missing the spike. The gauge would show a flat line.

This isn't unique to Prometheus — any polling-based monitoring system has this property. A few ways to deal with it:

- **Reduce the scrape interval** for critical gauges (but this increases storage cost)
- **Track the maximum with a separate metric**: keep a gauge that records the max value seen since last scrape and reset it after each scrape
- **Accept the limitation**: for most gauges, the scrape interval is fine. A 15-second peak in queue depth that then drains might not be actionable anyway

For truly latency-sensitive detection (sub-second anomalies), you generally need a different approach than scrape-based metrics entirely.

## Gauge vs counter: the decision

If you're unsure which to use:

- Can the value decrease? → **Gauge**
- Does the value represent a current state or level? → **Gauge**
- Are you counting events that accumulate over time? → **Counter**
- Would it make sense to ask "how fast is this changing per second"? → **Counter**

Active connections is a gauge (it goes down when connections close). Total connections ever made is a counter (it only ever goes up). Both metrics are useful and they answer different questions.

<!-- RESOURCES -->

- [Prometheus Gauge type (official docs)](https://prometheus.io/docs/concepts/metric_types/#gauge) -- type: article, time: 5m
- [Prometheus: Up & Running (O'Reilly)](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- type: book, time: 360m
- [Choosing the right Prometheus metric type](https://prometheus.io/docs/practices/instrumentation/#counter-vs-gauge-summary-vs-histogram) -- type: article, time: 10m
- [node_exporter — host and OS metrics for Prometheus](https://github.com/prometheus/node_exporter) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
Gauge 表示某个事物的当前值。它可以上升、下降或保持不变——即当下的真实值是什么就是什么。内存使用量、活跃 HTTP 连接数、任务队列深度、服务器当前温度、正在运行的 goroutine 数量——任何你想了解当前状态的事物都是 gauge。

与 counter 不同，gauge 的值可以直接读取。如果某个 gauge 读数为 847，就意味着你正在测量的对象此刻有 847 个。你不需要应用 `rate()` 或任何其他变换来让这个值有意义。这让 gauge 查询起来更简单，但也更容易被误用——因为你得到的是一个快照，而快照可能会误导你。

采样问题确实存在：Prometheus 默认每 15 秒抓取一次指标。如果你的内存使用量在两次抓取之间飙升到 90% 并持续 3 秒，你永远不会看到它。gauge 只会显示每个抓取点的值，而两次抓取之间的短暂峰值是不可见的。这对于变化迅速且峰值具有危险性的值来说最为重要。

<!-- ZH_DEEP_DIVE -->
## Gauge 的工作原理

Gauge 可以被设置为绝对值、递增或递减。你的代码直接更新它以反映当前状态：

```python
# Python — prometheus_client library
from prometheus_client import Gauge

MEMORY_USAGE = Gauge(
    'process_memory_bytes',
    'Current memory usage in bytes'
)

ACTIVE_CONNECTIONS = Gauge(
    'http_active_connections',
    'Number of currently active HTTP connections'
)

# Set to an absolute value
MEMORY_USAGE.set(process_memory_bytes())

# Increment when a connection opens
def on_connection_open():
    ACTIVE_CONNECTIONS.inc()

# Decrement when a connection closes
def on_connection_close():
    ACTIVE_CONNECTIONS.dec()
```

```go
// Go — prometheus/client_golang
var activeConnections = prometheus.NewGauge(prometheus.GaugeOpts{
    Name: "http_active_connections",
    Help: "Number of currently active HTTP connections",
})

func init() {
    prometheus.MustRegister(activeConnections)
}

func handleConnect() {
    activeConnections.Inc()
    defer activeConnections.Dec()
    // ... handle connection ...
}
```

## 在 PromQL 中查询 gauge

Gauge 查询比 counter 查询更简单，因为你处理的是真实值，而不是速率。你可以查询当前值、计算一段时间内的平均值、求最大值，或与阈值进行比较：

```promql
# Current memory usage across all instances
process_memory_bytes

# Average memory usage over the last 5 minutes (smooths noise)
avg_over_time(process_memory_bytes[5m])

# Maximum memory across all instances of a service
max(process_memory_bytes{service="api"})

# Alert: queue depth has been above 100 for 10 minutes
job_queue_depth > 100

# Memory usage as a percentage of a 2GB limit
process_memory_bytes / (2 * 1024 * 1024 * 1024) * 100
```

## 常见的 gauge 使用场景

| 要测量的内容 | 指标名称模式 | 说明 |
|----------------|---------------------|-------|
| 内存使用量 | `process_memory_bytes` | 定期从操作系统统计信息中设置 |
| 活跃 HTTP 连接数 | `http_active_connections` | 连接建立时 inc，关闭时 dec |
| 任务队列深度 | `queue_depth` | 从队列 API 设置 |
| 缓存命中率 | `cache_hit_ratio` | 定期重新计算并设置 |
| CPU 温度 | `hardware_cpu_temp_celsius` | 从主机指标 exporter 设置 |
| 打开的文件描述符数量 | `process_open_fds` | 通常由客户端库自动导出 |

许多基础设施 gauge——CPU 使用率、内存、磁盘——是由 Prometheus exporter（如 `node_exporter`）采集的，而不是在你的应用代码中进行埋点。你不需要编写代码来跟踪主机内存；只需在主机上运行 node_exporter，Prometheus 就会抓取它。

## 陷阱：gauge 与错过的峰值

想象一下，你的任务队列在 8 秒内飙升到 10,000 个条目，然后又回落到 0。在 15 秒的抓取间隔下，Prometheus 可能在第 N 次抓取时捕获到 0 个条目，在第 N+1 次抓取时也捕获到 0 个条目，从而完全错过了这次峰值。gauge 会显示为一条平线。

这并不是 Prometheus 独有的问题——任何基于轮询的监控系统都有这个特性。有几种应对方法：

- **缩短关键 gauge 的抓取间隔**（但这会增加存储成本）
- **用单独的指标跟踪最大值**：维护一个 gauge，记录自上次抓取以来看到的最大值，并在每次抓取后重置它
- **接受这一限制**：对大多数 gauge 来说，抓取间隔是足够的。队列深度出现 15 秒的峰值然后回落，可能本来也不具备可操作性

对于真正对延迟敏感的检测（亚秒级异常），你通常需要完全不同的方法，而不是基于抓取的指标。

## Gauge 与 counter：如何抉择

如果你不确定该用哪个：

- 值会减少吗？→ **Gauge**
- 值代表当前状态或水平吗？→ **Gauge**
- 你是在统计随时间累积的事件吗？→ **Counter**
- 问“它每秒变化多快”是否合理？→ **Counter**

活跃连接数是一个 gauge（连接关闭时它会下降）。曾经建立的总连接数是一个 counter（它只会上升）。两个指标都有用，它们回答的是不同的问题。

<!-- ZH_RESOURCES -->
- [Prometheus Gauge 类型（官方文档）](https://prometheus.io/docs/concepts/metric_types/#gauge) -- 类型：文章，时长：5 分钟
- [Prometheus: Up & Running（O'Reilly）](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- 类型：书籍，时长：360 分钟
- [选择合适的 Prometheus 指标类型](https://prometheus.io/docs/practices/instrumentation/#counter-vs-gauge-summary-vs-histogram) -- 类型：文章，时长：10 分钟
- [node_exporter — 用于 Prometheus 的主机与操作系统指标](https://github.com/prometheus/node_exporter) -- 类型：文章，时长：10 分钟

<!-- ZH_UI -->
1. 理解 gauge 可以上升和下降，表示当前状态
2. 知道何时使用 gauge 与 counter
3. 为活跃连接、队列深度和内存使用量埋点 gauge
4. 理解为什么对 gauge 随时间取平均值可能产生误导
5. 我懂了 gauge。我该如何实际为服务埋点以暴露所有这些指标？
6. 我现在知道要测量什么了——事件用 counter，当前状态用 gauge。但我从未真正给真实服务添加过指标。数据到底去了哪里，又是什么在读取它？
