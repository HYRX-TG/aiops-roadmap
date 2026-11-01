---
id: observability-cardinality
title: Observability Cardinality
zone: observability
edges:
  to:
    - id: always-firefighting
      zone: sre
      question: >-
        I can see everything now — dashboards, alerts, traces. But when
        an incident hits, it's still chaos. We keep having the same problems
        over and over.
      detail: >-
        The observability is solid. I can find the problem. But the response
        is a mess — everyone scrambling, nobody knows who's in charge, no
        process for what happens after. And the same types of failures keep
        recurring because nothing changes. How do teams actually get ahead
        of this instead of just reacting?
difficulty: 3
tags:
  - metrics
  - cardinality
  - prometheus
  - cost
  - observability
  - labels
category: concept
milestones:
  - Understand what metric cardinality means and what drives it
  - Identify which labels in your current setup create high-cardinality problems
  - Know which label values are safe (service, method) vs dangerous (user_id, request_id)
  - Use Prometheus TSDB analysis tools to find cardinality offenders
title_zh: "可观测性基数"

---


In Prometheus, every unique combination of metric name and label values creates a separate time series. A metric called `http_requests_total` with labels `method` and `status_code` might have series for `{method="GET", status_code="200"}`, `{method="GET", status_code="404"}`, `{method="POST", status_code="200"}`, and so on. With a few bounded values per label, this is manageable — maybe a dozen series. But labels with high cardinality multiply that count explosively.

Cardinality is the number of unique values a label can take. Adding a label with 10 possible values multiplies your series count by 10. Adding `user_id` as a label on a counter metric, with 500,000 active users, creates 500,000 time series for that one metric. Prometheus has to keep all active time series in memory. At high enough cardinality, Prometheus runs out of memory, scraping falls behind, queries time out, and your entire observability stack grinds to a halt.

This is one of the most common ways people accidentally break their own observability infrastructure. The good news is the rules are simple once you know them, and the fix is usually removing the offending label — not deleting the metric entirely.

<!-- DEEP_DIVE -->

## How time series multiply

Start with a single metric: `http_requests_total`. No labels. That's one time series.

Add a `method` label with 4 values (GET, POST, PUT, DELETE): 4 time series.

Add a `status_code` label with 10 common values (200, 201, 301, 400, 401, 403, 404, 500, 502, 503): 40 time series.

Add a `service` label for your 8 microservices: 320 time series.

Still fine. 320 time series is nothing to Prometheus.

Now add `user_id` with 100,000 active users: 32,000,000 time series. Prometheus is on fire.

Each time series is an independent stream of data that Prometheus must track: store in memory, write to disk, index, and query. The math compounds fast because it's multiplicative, not additive.

## Safe labels vs dangerous labels

The rule is simple: a label is safe if its possible values are **bounded and small**. A label is dangerous if its values can grow without limit.

**Safe labels (bounded values):**

| Label | Why it's safe |
|-------|---------------|
| `service` | You have tens of services, not millions |
| `method` | HTTP methods are a fixed set |
| `status_code` | HTTP status codes are a fixed set |
| `environment` | `production`, `staging`, `dev` — handful of values |
| `region` | `us-east-1`, `eu-west-1` — handful of values |
| `error_type` | Bounded error classifications |

**Dangerous labels (unbounded values):**

| Label | Why it's dangerous |
|-------|-------------------|
| `user_id` | Grows with your user base |
| `request_id` | Unique per request — infinite |
| `session_id` | Unique per session — infinite |
| `IP address` | Unbounded |
| `URL path` | If it includes IDs (e.g., `/users/12345`) |
| `SQL query` | Unique per query text |

The canonical example that catches people: tracking latency per endpoint and including the dynamic part of the path in the label. `/api/users/{id}` becomes `/api/users/12345`, `/api/users/67890`, etc. Each unique ID creates a new time series. You want the label to be `/api/users/{id}` (the route pattern), not `/api/users/12345` (the actual path).

## The per-request data problem

The instinct to add `user_id` as a metric label comes from a real need: you want to know how a specific user's requests are performing. The mistake is reaching for metrics to answer that question.

Metrics are aggregate data — they summarize across many requests. The right tool for per-request data is **traces and logs**:

- "How many requests did user 12345 make?" — metrics, but with `user_id` on a counter (this will explode)
- "Which requests by user 12345 were slow, and why?" — traces and logs
- "What is the p99 latency for user 12345 over the last hour?" — traces (query trace data for that user)

When you find yourself wanting to add a high-cardinality label, it's almost always a signal that you should be looking at a trace or log, not a metric.

## Finding the offenders: TSDB analysis

If your Prometheus is already struggling with high cardinality, you can use the built-in TSDB analysis tool to find which metrics and labels are responsible.

**Via the HTTP API:**

```bash
# List the top metrics by series count
curl http://prometheus:9090/api/v1/status/tsdb | \
  jq '.data.seriesCountByMetricName | sort_by(.count) | reverse | .[0:20]'
```

**Via the CLI (on the Prometheus server):**

```bash
prometheus-tsdb analyze --db /prometheus/data
```

This outputs something like:

```
Block (2h):
  Highest cardinality labels:
    user_id       4,823,441 series
    request_id    1,293,882 series
    trace_id        842,193 series
  Highest cardinality metric names:
    http_requests_total{user_id=...}   4,823,441
    rpc_calls_total{request_id=...}    1,293,882
```

This immediately tells you which label is the culprit. In most cases the fix is to remove that label from the metric. The data you wanted from that label should come from traces or logs instead.

## Keeping URL labels safe

If you're labeling metrics with endpoint paths, make sure you're using the route pattern, not the actual URL. Most HTTP frameworks provide a route pattern variable.

In Python with FastAPI and the Prometheus client:

```python
# Dangerous — uses the actual request path
# path = request.url.path  # → "/users/12345", "/users/67890", etc.

# Safe — uses the route pattern
# In FastAPI, request.scope["path"] after routing gives the pattern
path = request.scope.get("route").path  # → "/users/{user_id}"

REQUEST_COUNT.labels(method=request.method, path=path, status=response.status_code).inc()
```

The middleware approach is usually easier — most Prometheus instrumentation libraries for web frameworks do this correctly by default if you use them properly.

## Practical cardinality budget

A rough guideline for a healthy Prometheus setup:

- Under 1 million active time series: comfortable
- 1–10 million: manageable with adequate memory (plan for ~2–3 bytes per sample, ~thousands of bytes per series)
- Over 10 million: you need to fix the cardinality or shard Prometheus

Before adding any new label to an existing metric, ask: "How many unique values can this label take? In 6 months? In 2 years?" If the answer isn't bounded and small, put that data in traces or logs instead.

<!-- RESOURCES -->

- [Cardinality is Key — Prometheus blog](https://www.robustperception.io/cardinality-is-key/) -- type: article, time: 10m
- [Prometheus TSDB: Understanding the storage](https://prometheus.io/docs/prometheus/latest/storage/) -- type: article, time: 15m
- [High Cardinality in Prometheus — Grafana blog](https://grafana.com/blog/2022/02/15/what-are-cardinality-spikes-and-why-do-they-matter/) -- type: article, time: 12m
- [Prometheus Best Practices: Labels](https://prometheus.io/docs/practices/instrumentation/#labels) -- type: article, time: 8m
- [Thanos and VictoriaMetrics for scaling Prometheus](https://victoriametrics.com/blog/cardinality-explorer/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
在 Prometheus 中，指标名称和标签值的每一种唯一组合都会创建一个独立的时间序列。一个名为 `http_requests_total` 的指标，带有 `method` 和 `status_code` 标签，可能会产生 `{method="GET", status_code="200"}`、`{method="GET", status_code="404"}`、`{method="POST", status_code="200"}` 等时间序列。如果每个标签只有少量有限取值，这还可控——大概也就十几个序列。但高基数标签会让这个数量爆炸式增长。

基数是指某个标签可以取的不同值的数量。添加一个具有 10 个可能取值的标签，就会让时间序列数量乘以 10。在一个计数器指标上添加 `user_id` 作为标签，如果有 50 万活跃用户，就会为这一个指标创建 50 万个时间序列。Prometheus 必须将所有活跃时间序列保存在内存中。当基数高到一定程度时，Prometheus 会耗尽内存，抓取开始滞后，查询超时，整个可观测性栈都会陷入停滞。

这是人们意外破坏自身可观测性基础设施的最常见方式之一。好消息是，一旦你了解了规则，它们其实很简单，而修复方法通常是移除有问题的标签——而不是完全删除该指标。

<!-- ZH_DEEP_DIVE -->
## 时间序列如何成倍增长

从一个指标开始：`http_requests_total`。没有标签。这就是一条时间序列。

添加一个 `method` 标签，有 4 个值（GET、POST、PUT、DELETE）：4 条时间序列。

添加一个 `status_code` 标签，有 10 个常见值（200、201、301、400、401、403、404、500、502、503）：40 条时间序列。

为你的 8 个微服务添加一个 `service` 标签：320 条时间序列。

仍然没问题。320 条时间序列对 Prometheus 来说不算什么。

现在添加 `user_id`，有 100,000 个活跃用户：32,000,000 条时间序列。Prometheus 要炸了。

每条时间序列都是 Prometheus 必须跟踪的独立数据流：存入内存、写入磁盘、建立索引并支持查询。这个数学增长得很快，因为它是乘法，不是加法。

## 安全标签 vs 危险标签

规则很简单：如果一个标签的可能取值是**有界且小**的，它就是安全的。如果一个标签的取值可以无限增长，它就是危险的。

**安全标签（有界取值）：**

| 标签 | 为什么安全 |
|-------|---------------|
| `service` | 你有几十个服务，不是几百万个 |
| `method` | HTTP 方法是固定集合 |
| `status_code` | HTTP 状态码是固定集合 |
| `environment` | `production`、`staging`、`dev` —— 少数几个值 |
| `region` | `us-east-1`、`eu-west-1` —— 少数几个值 |
| `error_type` | 有界的错误分类 |

**危险标签（无界取值）：**

| 标签 | 为什么危险 |
|-------|-------------------|
| `user_id` | 随用户基数增长 |
| `request_id` | 每个请求唯一 —— 无限 |
| `session_id` | 每个会话唯一 —— 无限 |
| `IP address` | 无界 |
| `URL path` | 如果包含 ID（例如 `/users/12345`） |
| `SQL query` | 每个查询文本唯一 |

最容易让人踩坑的典型例子：按端点跟踪延迟，并把路径中的动态部分放进标签。`/api/users/{id}` 变成了 `/api/users/12345`、`/api/users/67890` 等等。每个唯一 ID 都会创建一条新的时间序列。你希望标签是 `/api/users/{id}`（路由模式），而不是 `/api/users/12345`（实际路径）。

## 每请求数据的问题

把 `user_id` 添加为指标标签的冲动来自一个真实需求：你想知道某个特定用户的请求表现如何。错误在于用指标来回答这个问题。

指标是聚合数据 —— 它们跨许多请求进行汇总。每请求数据的正确工具是**追踪和日志**：

- “用户 12345 发出了多少请求？” —— 指标，但在计数器上带 `user_id`（这会爆炸）
- “用户 12345 的哪些请求慢，为什么？” —— 追踪和日志
- “用户 12345 在过去一小时的 p99 延迟是多少？” —— 追踪（查询该用户的追踪数据）

当你发现自己想添加高基数标签时，这几乎总是表明你应该查看追踪或日志，而不是指标。

## 找出罪魁祸首：TSDB 分析

如果你的 Prometheus 已经因高基数而吃力，你可以使用内置的 TSDB 分析工具来找出哪些指标和标签是罪魁祸首。

**通过 HTTP API：**

```bash
# List the top metrics by series count
curl http://prometheus:9090/api/v1/status/tsdb | \
  jq '.data.seriesCountByMetricName | sort_by(.count) | reverse | .[0:20]'
```

**通过 CLI（在 Prometheus 服务器上）：**

```bash
prometheus-tsdb analyze --db /prometheus/data
```

输出类似这样：

```
Block (2h):
  Highest cardinality labels:
    user_id       4,823,441 series
    request_id    1,293,882 series
    trace_id        842,193 series
  Highest cardinality metric names:
    http_requests_total{user_id=...}   4,823,441
    rpc_calls_total{request_id=...}    1,293,882
```

这会立即告诉你哪个标签是罪魁祸首。在大多数情况下，修复方法是从指标中移除该标签。你希望从该标签获得的数据应该来自追踪或日志。

## 保持 URL 标签安全

如果你用端点路径标记指标，请确保使用路由模式，而不是实际 URL。大多数 HTTP 框架都提供路由模式变量。

在 Python 中使用 FastAPI 和 Prometheus 客户端：

```python
# Dangerous — uses the actual request path
# path = request.url.path  # → "/users/12345", "/users/67890", etc.

# Safe — uses the route pattern
# In FastAPI, request.scope["path"] after routing gives the pattern
path = request.scope.get("route").path  # → "/users/{user_id}"

REQUEST_COUNT.labels(method=request.method, path=path, status=response.status_code).inc()
```

中间件方法通常更容易 —— 大多数 Web 框架的 Prometheus 插桩库如果你正确使用，默认就会正确处理这一点。

## 实用的基数预算

健康 Prometheus 设置的粗略指南：

- 低于 100 万活跃时间序列：舒适
- 100 万–1000 万：在内存充足的情况下可管理（按每个样本约 2–3 字节、每条序列约数千字节来规划）
- 超过 1000 万：你需要修复基数或对 Prometheus 进行分片

在向现有指标添加任何新标签之前，问自己：“这个标签可以取多少个唯一值？6 个月后？2 年后？”如果答案不是有界且小的，就把该数据放入追踪或日志中。

<!-- ZH_RESOURCES -->
- [基数至关重要 — Prometheus 博客](https://www.robustperception.io/cardinality-is-key/) -- 类型: 文章, 时间: 10m
- [Prometheus TSDB：理解存储](https://prometheus.io/docs/prometheus/latest/storage/) -- 类型: 文章, 时间: 15m
- [Prometheus 中的高基数 — Grafana 博客](https://grafana.com/blog/2022/02/15/what-are-cardinality-spikes-and-why-do-they-matter/) -- 类型: 文章, 时间: 12m
- [Prometheus 最佳实践：标签](https://prometheus.io/docs/practices/instrumentation/#labels) -- 类型: 文章, 时间: 8m
- [用于扩展 Prometheus 的 Thanos 与 VictoriaMetrics](https://victoriametrics.com/blog/cardinality-explorer/) -- 类型: 文章, 时间: 15m

<!-- ZH_UI -->
1. 理解指标基数（metric cardinality）的含义及其驱动因素
2. 识别当前配置中哪些标签会导致高基数问题
3. 了解哪些标签值是安全的（service、method），哪些是危险的（user_id、request_id）
4. 使用 Prometheus TSDB 分析工具找出基数问题的来源
5. 现在我能看到一切——仪表盘、告警、链路追踪。但故障来临时，依然一片混乱。同样的问题反复出现。
6. 可观测性已经很扎实，我能找到问题所在。但响应过程一团糟——所有人手忙脚乱，没人知道谁负责，事后也没有流程。同类故障反复发生，因为什么都没改变。团队究竟怎样才能真正走在问题前面，而不是一直被动应对？
