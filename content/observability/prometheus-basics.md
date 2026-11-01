---
id: prometheus-basics
title: Prometheus Basics
zone: observability
edges:
  to:
    - id: dashboards
      question: >-
        I've got Prometheus scraping my metrics. Now I want to actually look at
        them visually — not just run queries in a terminal.
      detail: >-
        PromQL queries in a terminal are fine for one-off checks but useless
        during an incident. I want a screen I can pull up that shows me at a
        glance whether things are getting worse or better — something I can
        share with the team.
difficulty: 2
tags:
  - prometheus
  - promql
  - scraping
  - metrics
  - observability
category: practice
milestones:
  - Run Prometheus locally and configure it to scrape a service
  - Instrument an application with the Prometheus client library
  - Write basic PromQL queries (rate, sum, histogram_quantile)
  - Understand the pull model and why it differs from a push-based approach
  - Configure scrape intervals and understand their effect on data resolution
title_zh: "Prometheus 基础"

---


Prometheus is the de facto standard for metrics collection in cloud-native environments. It works on a pull model: rather than having your service push metrics to a central server, Prometheus periodically fetches metrics from your services on a schedule — every 15 seconds by default. Your service exposes a plain-text HTTP endpoint at `/metrics`, and Prometheus scrapes it, parses the output, and stores the values in its built-in time-series database.

The pull model has real advantages. If a service stops responding, Prometheus knows it immediately — the scrape fails. With a push model, a dead service just stops sending data and you have to detect the silence. The pull model also means Prometheus controls the scrape interval, so you get consistent timing across all your services without coordinating anything on the service side. The downside is that services behind firewalls or in short-lived environments (like batch jobs) need special treatment — Prometheus has a Pushgateway for those cases.

Every metric in Prometheus is a combination of a name, a set of labels (key-value pairs), and a value. The same metric can have many time series if it has multiple label combinations — `http_requests_total{method="GET", status="200"}` is a different time series from `http_requests_total{method="POST", status="500"}`. This label system is what makes Prometheus so flexible for slicing and dicing data during an investigation.

<!-- DEEP_DIVE -->

## The data model

Prometheus stores time series identified by a metric name and a set of labels:

```
<metric_name>{<label_name>=<label_value>, ...} <value> [<timestamp>]
```

For example:
```
http_requests_total{method="GET", endpoint="/api/users", status="200"} 14832
http_requests_total{method="POST", endpoint="/api/users", status="201"} 3241
http_requests_total{method="GET", endpoint="/api/users", status="500"} 47
```

Each unique combination of labels is a separate time series. Prometheus appends (timestamp, value) pairs to each series as it scrapes.

## Exposing a /metrics endpoint

Your service needs to expose metrics at an HTTP endpoint. The Prometheus client libraries handle all of this — you just register metrics and call them in your code:

```python
# Python — minimal Flask service with Prometheus metrics
from flask import Flask
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration',
                              buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])

@app.route('/api/hello')
def hello():
    start = time.time()
    REQUEST_COUNT.labels(method='GET', status='200').inc()
    REQUEST_DURATION.observe(time.time() - start)
    return 'Hello, world!'

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

```go
// Go — minimal HTTP server with Prometheus metrics
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
    // Your own metrics registration happens here (see Counter/Gauge/Histogram nodes)

    // Expose /metrics endpoint — promhttp handles everything
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}
```

The `/metrics` output is plain text that Prometheus parses:

```
# HELP http_requests_total Total requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1432
http_requests_total{method="GET",status="500"} 7
# HELP http_request_duration_seconds Request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005"} 342
http_request_duration_seconds_bucket{le="0.01"} 891
...
```

## Configuring Prometheus to scrape your service

Prometheus is configured via a YAML file:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s      # How often to scrape — default is 15s
  evaluation_interval: 15s  # How often to evaluate alerting rules

scrape_configs:
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape your service
  - job_name: 'my-api'
    static_configs:
      - targets: ['my-api-host:8080']
    metrics_path: '/metrics'  # Default — can omit if you use /metrics

  # Scrape host metrics via node_exporter
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

Run Prometheus with Docker for local development:

```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Then open `http://localhost:9090` to access the Prometheus UI and run PromQL queries.

## Essential PromQL queries

PromQL is the query language for Prometheus. A few patterns you'll use constantly:

```promql
# Instant vector — current value of a metric
http_requests_total

# Filter by label
http_requests_total{method="GET", status=~"2.."}  # regex match on status

# Rate — per-second rate of a counter over 5 minutes
rate(http_requests_total[5m])

# Sum across all label combinations
sum(rate(http_requests_total[5m]))

# Sum, grouped by a label
sum by (method) (rate(http_requests_total[5m]))

# Error rate as a percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))
* 100

# p99 latency from a histogram
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)

# Current memory usage across all instances
process_resident_memory_bytes
```

The Prometheus UI at `:9090/graph` lets you run and visualise these queries immediately.

## Storage and retention

Prometheus stores all data locally in a built-in time-series database (TSDB). Default retention is 15 days. You can increase this with `--storage.tsdb.retention.time=30d`, but local storage isn't designed for multi-year retention.

For longer-term storage, Prometheus supports **remote write** — shipping data to an external system as it's collected:

```yaml
# prometheus.yml
remote_write:
  - url: "https://your-thanos-or-mimir-endpoint/api/v1/push"
```

Common remote storage systems:
- **Thanos** — open source, adds object storage (S3, GCS) for cheap long-term retention
- **Grafana Mimir** — horizontally scalable, managed or self-hosted
- **Cortex** — original open-source scalable Prometheus backend

For most teams starting out, local storage with 30–90 days of retention is fine. Add remote write when you need longer retention or when you have more data than a single Prometheus instance can handle.

## The client libraries

| Language | Library |
|----------|---------|
| Go | `github.com/prometheus/client_golang` |
| Python | `prometheus_client` (pip) |
| Node.js | `prom-client` (npm) |
| Java | `io.prometheus:simpleclient` |
| Ruby | `prometheus-client` |
| Rust | `prometheus` crate |

All of these expose the same concepts — Counter, Gauge, Histogram — and handle the `/metrics` endpoint formatting automatically. The Go library is the most complete and closest to the Prometheus internals.

<!-- RESOURCES -->

- [Prometheus Getting Started (official docs)](https://prometheus.io/docs/prometheus/latest/getting_started/) -- type: tutorial, time: 30m
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/) -- type: article, time: 20m
- [Prometheus: Up & Running (O'Reilly)](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- type: book, time: 360m
- [prom-client (Node.js)](https://github.com/siimon/prom-client) -- type: article, time: 10m
- [Practical introduction to PromQL](https://grafana.com/blog/2020/02/04/introduction-to-promql-the-prometheus-query-language/) -- type: article, time: 20m
- [Thanos — scalable, highly available Prometheus](https://thanos.io/tip/thanos/getting-started.md/) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
Prometheus 是云原生环境中指标收集的事实标准。它采用拉取模型：并非由你的服务将指标推送到中心服务器，而是 Prometheus 按计划定期从你的服务拉取指标——默认每 15 秒一次。你的服务在 `/metrics` 上暴露一个纯文本 HTTP 端点，Prometheus 抓取该端点、解析输出，并将数值存入其内置的时间序列数据库。

拉取模型有实实在在的优势。如果某个服务停止响应，Prometheus 会立即知晓——抓取失败。而在推送模型下，一个死掉的服务只是停止发送数据，你必须去检测这种沉默。拉取模型还意味着 Prometheus 掌控抓取间隔，因此你能在所有服务上获得一致的时序，而无需在服务侧做任何协调。缺点在于，位于防火墙之后或处于短生命周期环境（如批处理任务）中的服务需要特殊处理——针对这些情况，Prometheus 提供了 Pushgateway。

Prometheus 中的每个指标都是名称、一组标签（键值对）和数值的组合。同一个指标如果有多个标签组合，就可以拥有多条时间序列——`http_requests_total{method="GET", status="200"}` 与 `http_requests_total{method="POST", status="500"}` 是不同的时间序列。正是这套标签系统让 Prometheus 在排查问题时能够如此灵活地对数据进行切片和切块分析。

<!-- ZH_DEEP_DIVE -->
## 数据模型

Prometheus 存储的时间序列由指标名称和一组标签来标识：

```
<metric_name>{<label_name>=<label_value>, ...} <value> [<timestamp>]
```

例如：
```
http_requests_total{method="GET", endpoint="/api/users", status="200"} 14832
http_requests_total{method="POST", endpoint="/api/users", status="201"} 3241
http_requests_total{method="GET", endpoint="/api/users", status="500"} 47
```

每一种唯一的标签组合都是一个独立的时间序列。Prometheus 在抓取时会向每个序列追加 (timestamp, value) 对。

## 暴露 /metrics 端点

你的服务需要在一个 HTTP 端点上暴露指标。Prometheus 客户端库会处理所有这些工作——你只需注册指标并在代码中调用它们：

```python
# Python — minimal Flask service with Prometheus metrics
from flask import Flask
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration',
                              buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])

@app.route('/api/hello')
def hello():
    start = time.time()
    REQUEST_COUNT.labels(method='GET', status='200').inc()
    REQUEST_DURATION.observe(time.time() - start)
    return 'Hello, world!'

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

```go
// Go — minimal HTTP server with Prometheus metrics
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
    // Your own metrics registration happens here (see Counter/Gauge/Histogram nodes)

    // Expose /metrics endpoint — promhttp handles everything
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}
```

`/metrics` 的输出是纯文本，由 Prometheus 解析：

```
# HELP http_requests_total Total requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1432
http_requests_total{method="GET",status="500"} 7
# HELP http_request_duration_seconds Request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005"} 342
http_request_duration_seconds_bucket{le="0.01"} 891
...
```

## 配置 Prometheus 抓取你的服务

Prometheus 通过一个 YAML 文件进行配置：

```yaml
# prometheus.yml
global:
  scrape_interval: 15s      # How often to scrape — default is 15s
  evaluation_interval: 15s  # How often to evaluate alerting rules

scrape_configs:
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape your service
  - job_name: 'my-api'
    static_configs:
      - targets: ['my-api-host:8080']
    metrics_path: '/metrics'  # Default — can omit if you use /metrics

  # Scrape host metrics via node_exporter
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

使用 Docker 在本地开发环境中运行 Prometheus：

```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

然后打开 `http://localhost:9090` 访问 Prometheus UI 并运行 PromQL 查询。

## 必备的 PromQL 查询

PromQL 是 Prometheus 的查询语言。以下是你将会经常使用的几种模式：

```promql
# Instant vector — current value of a metric
http_requests_total

# Filter by label
http_requests_total{method="GET", status=~"2.."}  # regex match on status

# Rate — per-second rate of a counter over 5 minutes
rate(http_requests_total[5m])

# Sum across all label combinations
sum(rate(http_requests_total[5m]))

# Sum, grouped by a label
sum by (method) (rate(http_requests_total[5m]))

# Error rate as a percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))
* 100

# p99 latency from a histogram
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)

# Current memory usage across all instances
process_resident_memory_bytes
```

位于 `:9090/graph` 的 Prometheus UI 可以让你立即运行并可视化这些查询。

## 存储与保留

Prometheus 将所有数据存储在本地内置的时间序列数据库 (TSDB) 中。默认保留期为 15 天。你可以通过 `--storage.tsdb.retention.time=30d` 来延长保留期，但本地存储并非为多年保留而设计。

对于更长期的存储，Prometheus 支持 **remote write**——在采集数据的同时将其发送到外部系统：

```yaml
# prometheus.yml
remote_write:
  - url: "https://your-thanos-or-mimir-endpoint/api/v1/push"
```

常见的远程存储系统：
- **Thanos** — 开源，增加对象存储 (S3、GCS) 以实现低成本的长期保留
- **Grafana Mimir** — 水平可扩展，支持托管或自托管
- **Cortex** — 最初的开源可扩展 Prometheus 后端

对于大多数刚起步的团队来说，使用本地存储并保留 30–90 天就足够了。当你需要更长的保留期，或者数据量超过单个 Prometheus 实例所能处理的范围时，再添加 remote write。

## 客户端库

| 语言 | 库 |
|----------|---------|
| Go | `github.com/prometheus/client_golang` |
| Python | `prometheus_client` (pip) |
| Node.js | `prom-client` (npm) |
| Java | `io.prometheus:simpleclient` |
| Ruby | `prometheus-client` |
| Rust | `prometheus` crate |

所有这些库都暴露相同的概念——Counter、Gauge、Histogram——并自动处理 `/metrics` 端点的格式化。Go 库是最完整的，也最接近 Prometheus 的内部实现。

<!-- ZH_RESOURCES -->
- [Prometheus 入门（官方文档）](https://prometheus.io/docs/prometheus/latest/getting_started/) -- 类型：教程，时长：30m
- [PromQL 基础](https://prometheus.io/docs/prometheus/latest/querying/basics/) -- 类型：文章，时长：20m
- [Prometheus: Up & Running（O'Reilly）](https://www.oreilly.com/library/view/prometheus-up/9781492034131/) -- 类型：书籍，时长：360m
- [prom-client（Node.js）](https://github.com/siimon/prom-client) -- 类型：文章，时长：10m
- [PromQL 实践入门](https://grafana.com/blog/2020/02/04/introduction-to-promql-the-prometheus-query-language/) -- 类型：文章，时长：20m
- [Thanos — 可扩展、高可用的 Prometheus](https://thanos.io/tip/thanos/getting-started.md/) -- 类型：文章，时长：20m

<!-- ZH_UI -->
1. 在本地运行 Prometheus 并配置它抓取一个服务
2. 使用 Prometheus 客户端库为应用埋点
3. 编写基础 PromQL 查询（rate、sum、histogram_quantile）
4. 理解拉取模型及其与推送方式的差异
5. 配置抓取间隔并理解其对数据分辨率的影响
6. 我已经用 Prometheus 抓取指标了。现在我想真正可视化地查看它们——而不只是在终端里跑查询。
7. 在终端里跑 PromQL 查询适合一次性检查，但在事故处理时毫无用处。我想要一个能随时调出的界面，一眼看出情况是在变好还是变坏——还能分享给团队。
