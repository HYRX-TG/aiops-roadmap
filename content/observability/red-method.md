---
id: red-method
title: The RED Method
zone: observability
edges:
  to:
    - id: prometheus-basics
      question: >-
        RED gives me a clear framework. Now I need to actually instrument my
        service and start collecting these metrics.
      detail: >-
        I know I should track Rate, Errors, and Duration. But I've never added
        metrics to a service before. I don't know what library to use, where
        the data goes, or how anything gets from my app into a place I can
        query it.
difficulty: 1
tags:
  - metrics
  - red-method
  - rate
  - errors
  - duration
  - observability
category: concept
milestones:
  - Define Rate, Errors, and Duration and instrument all three for a service
  - Understand why these three signals are the minimum useful set for any service
  - Use RED metrics to answer "is my service healthy?" in under 30 seconds
  - Know the difference between RED (for services) and USE (for infrastructure)
title_zh: "RED 方法"

---


When you're first adding observability to a service, the hardest question is: what should I actually measure? You could instrument hundreds of things. The RED method cuts through that by giving you the minimum viable set of metrics for any request-driven service: Rate, Errors, and Duration. These three signals answer the only question that matters in the first 30 seconds of an incident: is my service healthy?

Rate tells you how much traffic the service is handling — requests per second. Errors tells you how often those requests are failing — the error rate as a percentage of total requests. Duration tells you how long requests are taking, specifically the latency distribution (p99 is the most actionable). Together, they answer whether the service is busy, broken, or slow. If all three look normal, the problem is probably not in this service. If any of them is abnormal, you know where to look next.

The RED method was coined by Tom Wilkie at Grafana Labs, drawing on the Google SRE "four golden signals" (which adds Saturation as a fourth). RED is deliberately minimal — it's the floor, not the ceiling. Once you have Rate, Errors, and Duration instrumented, you can add more signals. But these three come first, and many teams find they cover the majority of their alerting needs.

<!-- DEEP_DIVE -->

## The three signals

### Rate: how busy is the service?

Rate is requests per second. It tells you how much demand the service is currently handling and lets you spot sudden drops or spikes in traffic that might indicate a problem (either in the service itself or in whatever is calling it).

In PromQL, Rate comes from a Counter:

```promql
# Total request rate across all endpoints
rate(http_requests_total[5m])

# Request rate, broken down by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))
```

A sudden drop in rate when traffic should be steady often means requests are being dropped or failing before they're counted. A sudden spike might mean a retry storm or a traffic flood.

### Errors: is the service broken?

Errors is the rate of failed requests, usually expressed as a percentage of total requests. What counts as an error depends on your service — for an HTTP API, it's typically 5xx status codes. For a gRPC service, it's non-OK status codes. For a queue consumer, it might be processing failures.

```promql
# Error rate as a percentage of total requests
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))
* 100

# Absolute error rate (errors per second)
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

An error rate above 1% is generally worth investigating. Above 5% is an incident. The right thresholds depend on your service and your SLOs.

### Duration: is the service slow?

Duration is the latency distribution — specifically what percentile of requests complete within an acceptable time. Query the p99 for alerting; graph p50, p95, and p99 together for dashboards.

```promql
# p99 request duration
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)

# p50, p95, p99 in one graph (use multiple queries)
histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

Duration requires a Histogram metric type — you can't compute percentiles from a counter or gauge.

## Instrumenting RED metrics in practice

For an HTTP service, you typically need two metrics:

1. **A Counter** for requests, labelled by method, endpoint, and status code — gives you Rate and Errors
2. **A Histogram** for request duration, labelled by method and endpoint — gives you Duration

```python
# Python example — both metrics for a Flask service
from prometheus_client import Counter, Histogram
import time

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Wrap your handler
def handle_request(method, endpoint, handler):
    start = time.time()
    status_code = "200"
    try:
        result = handler()
        status_code = str(result.status_code)
        return result
    except Exception as e:
        status_code = "500"
        raise
    finally:
        duration = time.time() - start
        REQUEST_COUNT.labels(method, endpoint, status_code).inc()
        REQUEST_DURATION.labels(method, endpoint).observe(duration)
```

Many web frameworks have middleware that does this automatically — you don't always have to write it yourself. Look for Prometheus middleware for your framework (Flask-Prometheus, gin-prometheus, express-prom-bundle, etc.).

## RED vs USE: choosing the right method

RED is for **services** — anything that handles requests. Use it for your API servers, microservices, databases, and queues.

USE is for **resources** — CPU, memory, disk, network. Use it when you're asking about the health of the infrastructure running those services.

They're complementary. A typical workflow: RED metrics alert you that the service is slow (high p99 latency). USE metrics tell you why — the CPU on the host is saturated, or the disk I/O is at capacity.

| Question | Method |
|---------|--------|
| Is my API service healthy? | RED |
| Is my database healthy? | RED (for queries) + USE (for the database host) |
| Is my Kubernetes node healthy? | USE |
| Is my caching layer working? | RED |
| Is my network card overloaded? | USE |

## Building a minimal RED dashboard

A useful starting point for any service dashboard:

1. **Rate**: `sum(rate(http_requests_total[5m]))` — single stat + graph over time
2. **Error rate**: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100` — percentage, alert at 1%
3. **p50 / p95 / p99 latency**: Three lines on one graph

These three panels, visible at a glance, are enough to answer "is the service OK?" in seconds.

<!-- RESOURCES -->

- [RED Method — Tom Wilkie, Grafana Labs](https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/) -- type: article, time: 10m
- [The Four Golden Signals (Google SRE Book)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: article, time: 15m
- [Monitoring Microservices: RED, USE, and the four golden signals](https://thenewstack.io/monitoring-microservices-red-method/) -- type: article, time: 12m
- [Building a Grafana dashboard from RED metrics](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
当你第一次为一个服务添加可观测性时，最难的问题是：我到底应该测量什么？你可以埋点上数百个指标。RED 方法直击这一难题，为任何请求驱动的服务给出了最小可行的指标集：Rate（速率）、Errors（错误）和 Duration（持续时间）。这三个信号回答了故障发生最初 30 秒内唯一重要的问题：我的服务健康吗？

Rate 告诉你服务正在处理多少流量——每秒请求数。Errors 告诉你这些请求失败的频率——错误率占总请求数的百分比。Duration 告诉你请求需要多长时间，具体来说是延迟分布（p99 最具可操作性）。三者结合起来，回答了服务是繁忙、故障还是缓慢。如果三者看起来都正常，问题很可能不在这个服务里。如果其中任何一个异常，你就知道下一步该往哪里查。

RED 方法由 Grafana Labs 的 Tom Wilkie 提出，借鉴了 Google SRE 的“四个黄金信号”（后者将 Saturation 作为第四个信号加入）。RED 刻意保持极简——它是下限，而非上限。一旦你埋点了 Rate、Errors 和 Duration，就可以添加更多信号。但这三个是首要的，许多团队发现它们已经覆盖了大部分的告警需求。

<!-- ZH_DEEP_DIVE -->
## 三大信号

### Rate：服务有多繁忙？

Rate 是每秒请求数。它告诉你服务当前正在处理多少需求，并让你能够发现流量中可能表明问题的突然下降或激增（问题可能出在服务本身，也可能出在调用它的任何东西上）。

在 PromQL 中，Rate 来自 Counter：

```promql
# Total request rate across all endpoints
rate(http_requests_total[5m])

# Request rate, broken down by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))
```

当流量本应稳定时，Rate 突然下降通常意味着请求在被计数之前就被丢弃或失败了。突然激增可能意味着重试风暴或流量洪峰。

### Errors：服务是否出故障了？

Errors 是失败请求的速率，通常表示为总请求数的百分比。什么算作错误取决于你的服务——对于 HTTP API，通常是 5xx 状态码。对于 gRPC 服务，是非 OK 状态码。对于队列消费者，可能是处理失败。

```promql
# Error rate as a percentage of total requests
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))
* 100

# Absolute error rate (errors per second)
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

错误率超过 1% 通常就值得调查。超过 5% 就是事故了。合适的阈值取决于你的服务和你的 SLO。

### Duration：服务是否变慢了？

Duration 是延迟分布——具体来说，是请求在可接受时间内完成的百分位数。用 p99 做告警；在仪表盘上把 p50、p95 和 p99 画在一起。

```promql
# p99 request duration
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)

# p50, p95, p99 in one graph (use multiple queries)
histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

Duration 需要 Histogram 指标类型——你无法从 counter 或 gauge 计算百分位数。

## 在实践中埋点 RED 指标

对于一个 HTTP 服务，你通常需要两个指标：

1. **一个 Counter** 用于请求，按 method、endpoint 和 status code 打标签——为你提供 Rate 和 Errors
2. **一个 Histogram** 用于请求时长，按 method 和 endpoint 打标签——为你提供 Duration

```python
# Python example — both metrics for a Flask service
from prometheus_client import Counter, Histogram
import time

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Wrap your handler
def handle_request(method, endpoint, handler):
    start = time.time()
    status_code = "200"
    try:
        result = handler()
        status_code = str(result.status_code)
        return result
    except Exception as e:
        status_code = "500"
        raise
    finally:
        duration = time.time() - start
        REQUEST_COUNT.labels(method, endpoint, status_code).inc()
        REQUEST_DURATION.labels(method, endpoint).observe(duration)
```

许多 Web 框架都有自动完成这项工作的中间件——你不必总是自己写。寻找适用于你的框架的 Prometheus 中间件（Flask-Prometheus、gin-prometheus、express-prom-bundle 等）。

## RED vs USE：选择正确的方法

RED 用于**服务**——任何处理请求的东西。将它用于你的 API 服务器、微服务、数据库和队列。

USE 用于**资源**——CPU、内存、磁盘、网络。当你询问运行这些服务的基础设施的健康状况时使用它。

它们是互补的。一个典型的工作流程：RED 指标告警你服务变慢了（高 p99 延迟）。USE 指标告诉你原因——主机上的 CPU 饱和了，或者磁盘 I/O 达到上限了。

| 问题 | 方法 |
|---------|--------|
| 我的 API 服务健康吗？ | RED |
| 我的数据库健康吗？ | RED（用于查询）+ USE（用于数据库主机） |
| 我的 Kubernetes 节点健康吗？ | USE |
| 我的缓存层工作正常吗？ | RED |
| 我的网卡过载了吗？ | USE |

## 构建一个最小化的 RED 仪表盘

对于任何服务仪表盘来说，一个有用的起点：

1. **Rate**：`sum(rate(http_requests_total[5m]))`——单个统计值 + 随时间变化的图表
2. **错误率**：`sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`——百分比，在 1% 时告警
3. **p50 / p95 / p99 延迟**：一张图上的三条线

这三个面板，一眼可见，就足以在几秒钟内回答“服务是否正常？”

<!-- ZH_RESOURCES -->
- [RED 方法 — Tom Wilkie，Grafana Labs](https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/) -- 类型: 文章，时长: 10 分钟
- [四大黄金信号（Google SRE 手册）](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型: 文章，时长: 15 分钟
- [监控微服务：RED、USE 与四大黄金信号](https://thenewstack.io/monitoring-microservices-red-method/) -- 类型: 文章，时长: 12 分钟
- [基于 RED 指标构建 Grafana 仪表盘](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) -- 类型: 文章，时长: 15 分钟

<!-- ZH_UI -->
1. 定义 Rate、Errors 和 Duration，并为服务对这三项全部进行埋点
2. 理解为什么这三个信号是任何服务的最小有用集合
3. 使用 RED 指标在 30 秒内回答“我的服务健康吗？”
4. 了解 RED（用于服务）和 USE（用于基础设施）之间的区别
5. RED 给了我一个清晰的框架。现在我需要真正为我的服务埋点，并开始收集这些指标。
6. 我知道我应该跟踪 Rate、Errors 和 Duration。但我以前从未给服务添加过指标。我不知道该用哪个库、数据去哪里，也不知道任何东西如何从我的应用进入一个我可以查询的地方。
