---
id: correlating-signals
title: Correlating Logs, Metrics, and Traces
zone: observability
edges:
  to:
    - id: continuous-profiling
      question: >-
        The trace shows my service is slow, the logs are clean, the metrics
        look normal — but something is eating CPU. I have no idea what code is
        causing it.
      detail: >-
        I've gone through all three signals and none of them tell me WHY it's
        slow. I can see THAT it's slow and roughly WHERE in the call graph it
        happens, but I can't see what specific function or line of code is
        actually the problem. Is there a deeper level of visibility I'm missing?
    - id: observability-cardinality
      question: >-
        My observability stack is working but it's getting really expensive. I
        added one new label and my metric count exploded. What's happening?
      detail: >-
        I added user_id as a label to a counter metric and Prometheus slowed to
        a crawl and my storage costs went through the roof. I don't understand
        how one label could do that. I feel like I'm doing observability wrong
        and I don't know what the right constraints are.
difficulty: 2
tags:
  - observability
  - correlation
  - logs
  - metrics
  - tracing
  - exemplars
category: practice
milestones:
  - Add trace IDs to structured log lines so you can jump from trace to logs
  - Use exemplars in Prometheus to link a metric data point to a specific trace
  - Navigate from a metric spike to a trace to the relevant logs in a single flow
  - Understand what trace context propagation is and why it enables correlation
title_zh: "关联日志、指标和追踪"

---


Metrics, logs, and traces are all describing the same system, but without correlation they're three isolated islands of information. During an incident you see a latency spike in Grafana, you want to find a trace from one of those slow requests, and then you want to find the logs for that specific trace — and each step requires you to guess. You copy a timestamp, switch tabs, filter by that timestamp, and hope something lines up. It works, but it's slow and fragile.

The key to fixing this is the trace ID. Every request that gets traced has a unique trace ID. If you embed that trace ID in every log line your service emits while processing that request, you can jump from trace to logs in one click. If you attach trace IDs to specific metric data points (called exemplars), you can jump from a spike on a Grafana graph directly to a trace from that exact moment. The signals stay separate, but they're connected by a common key.

This isn't just a nice-to-have for debugging. During a high-pressure incident, the difference between "I can navigate from alert to trace to logs in 30 seconds" and "I'm manually searching for relevant data" is often the difference between a 10-minute outage and a 2-hour one.

<!-- DEEP_DIVE -->

## Trace IDs in logs: the foundation

The first and most important correlation to set up is trace ID in logs. When your service handles a request, it has a trace context (from incoming headers or one it created itself). You want that trace ID included on every log line emitted during that request.

With OpenTelemetry and structured logging, you can pull the trace context and inject it automatically. Here's an example in Python using structlog:

```python
import structlog
from opentelemetry import trace

def add_trace_context(logger, method, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

structlog.configure(
    processors=[
        add_trace_context,
        structlog.processors.JSONRenderer(),
    ]
)
```

Now every log line looks like this:

```json
{
  "timestamp": "2024-01-15T14:32:01.234Z",
  "level": "info",
  "message": "Order created",
  "order_id": "ord_abc123",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

When you're looking at a trace in Jaeger and you want the logs for that request, you copy the trace ID and search your log tool (Loki, Elasticsearch, CloudWatch) for `trace_id = "4bf92f3577..."`. You get exactly the log lines from that request.

## Exemplars: from metrics to traces

Exemplars solve a different problem. A metric like `http_request_duration_seconds` is an aggregate — it summarizes thousands of requests into a histogram. When you see a p99 spike at 14:32, you know something was slow, but you don't know which request, and the metric itself has no pointer to any trace.

An exemplar is a specific data point attached to a metric sample that says "this particular observation came from this trace." In Prometheus, exemplars look like this in the metrics endpoint:

```
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.5"} 24054 # {trace_id="4bf92f3577b34da6a3ce929d0e0e4736"} 0.32 1705324321.234
http_request_duration_seconds_bucket{le="1.0"} 33444 # {trace_id="4bf92f3577b34da6a3ce929d0e0e4736"} 0.32 1705324321.234
```

The `# {...}` part is the exemplar: it records that one specific observation of 0.32 seconds was associated with trace ID `4bf92f3577...`. In Grafana, when you view a histogram panel, you can enable exemplar display and see dots on the graph. Clicking a dot opens the corresponding trace directly.

To emit exemplars from your service, you need to add trace context when recording metrics. With the Prometheus Python client:

```python
from prometheus_client import Histogram
from opentelemetry import trace

REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')

def handle_request(request):
    start = time.time()
    response = process(request)
    duration = time.time() - start

    # Get current trace context
    span = trace.get_current_span()
    ctx = span.get_span_context()
    exemplar = {"trace_id": format(ctx.trace_id, "032x")}

    REQUEST_LATENCY.observe(duration, exemplar=exemplar)
    return response
```

Prometheus must be configured to accept and store exemplars (`--enable-feature=exemplar-storage`), and Grafana needs to be told which Tempo/Jaeger datasource to use for trace lookups.

## The full correlated workflow

With both pieces in place, your incident investigation flow becomes:

1. **Alert fires** — p99 latency above 2 seconds for the past 5 minutes.
2. **Open Grafana dashboard** — you see the spike on the latency histogram. Exemplars are enabled, so you see orange dots at the peak of the spike.
3. **Click an exemplar dot** — Grafana opens the trace for that specific slow request in Tempo/Jaeger.
4. **Read the trace** — you see the `payment-service` span took 1.8 seconds. You want to know why.
5. **Click "Logs for this trace"** — Grafana Explore opens Loki filtered by that trace ID. You see a log line: `"Payment gateway timeout after 1800ms"` with the gateway's error response.
6. **Root cause found** — the payment gateway had elevated latency. Total investigation time: under 2 minutes.

Compare this to the same investigation without correlation: you'd be guessing timestamps, searching for relevant logs, trying to identify which request among thousands was the slow one, and probably ending up at the same answer 20 minutes later.

## Grafana's derived fields

If you're using Grafana with Loki for logs, derived fields let you turn the trace ID in a log line into a clickable link to Tempo or Jaeger. Configure them in the Loki datasource settings:

```
Name:     traceID
Regex:    "trace_id":"(\w+)"
URL:      http://tempo:3200/trace/$${__value.raw}
```

Now whenever Grafana renders a log line with a `trace_id` field, the value becomes a hyperlink. Click it and the trace opens in Tempo. No copy-pasting required.

## What you need in your stack

| Component | What it provides |
|-----------|-----------------|
| Structured logging with trace ID | Logs → Trace lookup |
| OTel trace context propagation | Trace IDs flow through all services |
| Prometheus exemplars | Metric spike → Trace |
| Grafana derived fields | Log line → Trace (clickable) |
| Grafana datasource linking | All signals navigable from Explore |

You don't need all of this on day one. Start with trace IDs in logs — it's one function and it immediately makes debugging faster. Add exemplars later when your dashboards are mature enough to use them.

<!-- RESOURCES -->

- [Correlate logs and traces with Grafana](https://grafana.com/docs/grafana/latest/explore/logs-integration/) -- type: tutorial, time: 20m
- [Exemplars in Prometheus](https://prometheus.io/docs/prometheus/latest/feature_flags/#exemplars-storage) -- type: article, time: 10m
- [Trace context in logs — OpenTelemetry docs](https://opentelemetry.io/docs/specs/otel/logs/data-model/#trace-context-fields) -- type: article, time: 8m
- [Grafana Tempo: Linking with Loki](https://grafana.com/docs/tempo/latest/getting-started/tempo-in-grafana/) -- type: tutorial, time: 25m
- [Three Pillars of Observability — Charity Majors](https://charity.wtf/2019/02/05/logs-vs-structured-events/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
指标、日志和链路追踪都在描述同一个系统，但如果没有关联，它们就是三座孤立的信息孤岛。在故障排查时，你在 Grafana 上看到延迟飙升，想找到某个慢请求对应的 trace，然后再找到该 trace 对应的日志——而每一步都需要你去猜。你复制时间戳、切换标签页、按该时间戳过滤，然后祈祷能对上。这样做能行，但既慢又脆弱。

解决这个问题的关键在于 trace ID。每个被追踪的请求都有一个唯一的 trace ID。如果你在处理该请求期间，把该 trace ID 嵌入到服务输出的每一行日志中，就能一键从 trace 跳转到日志。如果你把 trace ID 附加到特定的指标数据点上（称为 exemplars），就能从 Grafana 图表上的一个尖峰直接跳转到那个确切时刻的 trace。这些信号仍然彼此独立，但通过一个共同的键连接了起来。

这不仅仅是调试时的一个锦上添花的功能。在高压的故障处理过程中，“我能在 30 秒内从告警导航到 trace 再到日志”与“我正在手动搜索相关数据”之间的差别，往往就是 10 分钟故障和 2 小时故障之间的差别。

<!-- ZH_DEEP_DIVE -->
## 日志中的 Trace ID：基础

首先要建立、也是最重要的关联，是日志中的 trace ID。当你的服务处理一个请求时，它拥有一个 trace 上下文（来自传入的 header，或由它自己创建）。你希望在该请求期间输出的每一行日志中都包含这个 trace ID。

借助 OpenTelemetry 和结构化日志，你可以提取 trace 上下文并自动注入。以下是一个使用 structlog 的 Python 示例：

```python
import structlog
from opentelemetry import trace

def add_trace_context(logger, method, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

structlog.configure(
    processors=[
        add_trace_context,
        structlog.processors.JSONRenderer(),
    ]
)
```

现在每一行日志都长这样：

```json
{
  "timestamp": "2024-01-15T14:32:01.234Z",
  "level": "info",
  "message": "Order created",
  "order_id": "ord_abc123",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

当你在 Jaeger 中查看某个 trace，并想获取该请求的日志时，你复制 trace ID，然后在日志工具（Loki、Elasticsearch、CloudWatch）中搜索 `trace_id = "4bf92f3577..."`。你就能精确得到该请求产生的日志行。

## Exemplars：从指标到 trace

Exemplars 解决的是另一个问题。像 `http_request_duration_seconds` 这样的指标是一个聚合值——它把成千上万个请求汇总成一个直方图。当你在 14:32 看到 p99 出现尖峰时，你知道有东西变慢了，但不知道是哪个请求，而且指标本身也没有指向任何 trace 的指针。

Exemplar 是附加在某个指标样本上的一个具体数据点，它表示“这个特定的观测值来自这个 trace”。在 Prometheus 中，exemplars 在 metrics 端点里长这样：

```
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.5"} 24054 # {trace_id="4bf92f3577b34da6a3ce929d0e0e4736"} 0.32 1705324321.234
http_request_duration_seconds_bucket{le="1.0"} 33444 # {trace_id="4bf92f3577b34da6a3ce929d0e0e4736"} 0.32 1705324321.234
```

`# {...}` 部分就是 exemplar：它记录了某个 0.32 秒的具体观测值与 trace ID `4bf92f3577...` 相关联。在 Grafana 中，当你查看直方图面板时，可以启用 exemplar 显示，并在图上看到圆点。点击某个圆点即可直接打开对应的 trace。

要从你的服务中输出 exemplars，你需要在记录指标时添加 trace 上下文。使用 Prometheus Python 客户端：

```python
from prometheus_client import Histogram
from opentelemetry import trace

REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')

def handle_request(request):
    start = time.time()
    response = process(request)
    duration = time.time() - start

    # Get current trace context
    span = trace.get_current_span()
    ctx = span.get_span_context()
    exemplar = {"trace_id": format(ctx.trace_id, "032x")}

    REQUEST_LATENCY.observe(duration, exemplar=exemplar)
    return response
```

Prometheus 必须配置为接受并存储 exemplars（`--enable-feature=exemplar-storage`），并且需要告诉 Grafana 使用哪个 Tempo/Jaeger 数据源来进行 trace 查询。

## 完整的关联工作流

两部分都就位后，你的故障排查流程就变成：

1. **告警触发** —— 过去 5 分钟 p99 延迟超过 2 秒。
2. **打开 Grafana 仪表盘** —— 你在延迟直方图上看到尖峰。Exemplars 已启用，因此你能在尖峰顶部看到橙色圆点。
3. **点击一个 exemplar 圆点** —— Grafana 在 Tempo/Jaeger 中打开那个特定慢请求的 trace。
4. **阅读 trace** —— 你看到 `payment-service` 的 span 耗时 1.8 秒。你想知道原因。
5. **点击“Logs for this trace”** —— Grafana Explore 打开按该 trace ID 过滤的 Loki。你看到一行日志：`"Payment gateway timeout after 1800ms"`，以及网关的错误响应。
6. **找到根因** —— 支付网关的延迟升高了。总排查时间：不到 2 分钟。

对比一下没有关联时的同样排查过程：你得猜测时间戳、搜索相关日志、试图从成千上万个请求中找出哪个是慢请求，大概 20 分钟后才得到同样的答案。

## Grafana 的派生字段

如果你使用 Grafana 搭配 Loki 来管理日志，派生字段可以让你把日志行中的 trace ID 变成指向 Tempo 或 Jaeger 的可点击链接。在 Loki 数据源设置中配置它们：

```
Name:     traceID
Regex:    "trace_id":"(\w+)"
URL:      http://tempo:3200/trace/$${__value.raw}
```

现在，只要 Grafana 渲染出带有 `trace_id` 字段的日志行，该值就会变成一个超链接。点击它，trace 就会在 Tempo 中打开。无需复制粘贴。

## 你的技术栈需要什么

| 组件 | 它提供的能力 |
|-----------|-----------------|
| 带 trace ID 的结构化日志 | 日志 → Trace 查询 |
| OTel trace 上下文传播 | Trace ID 流经所有服务 |
| Prometheus exemplars | 指标尖峰 → Trace |
| Grafana 派生字段 | 日志行 → Trace（可点击） |
| Grafana 数据源链接 | 所有信号均可从 Explore 导航 |

你不需要在第一天就全部具备。从日志中的 trace ID 开始——它只是一个函数，却能立即让调试更快。等你的仪表盘足够成熟、能够使用 exemplars 时，再添加它们。

<!-- ZH_RESOURCES -->
- [使用 Grafana 关联日志与追踪](https://grafana.com/docs/grafana/latest/explore/logs-integration/) -- 类型：教程，时长：20m
- [Prometheus 中的 Exemplars](https://prometheus.io/docs/prometheus/latest/feature_flags/#exemplars-storage) -- 类型：文章，时长：10m
- [日志中的追踪上下文 — OpenTelemetry 文档](https://opentelemetry.io/docs/specs/otel/logs/data-model/#trace-context-fields) -- 类型：文章，时长：8m
- [Grafana Tempo：与 Loki 关联](https://grafana.com/docs/tempo/latest/getting-started/tempo-in-grafana/) -- 类型：教程，时长：25m
- [可观测性的三大支柱 — Charity Majors](https://charity.wtf/2019/02/05/logs-vs-structured-events/) -- 类型：文章，时长：15m

<!-- ZH_UI -->
1. 将 trace ID 添加到结构化日志行中，以便从 trace 跳转到日志
2. 在 Prometheus 中使用 exemplars 将指标数据点关联到特定 trace
3. 在单一流程中从指标尖峰导航到 trace，再到相关日志
4. 理解什么是 trace 上下文传播，以及为什么它能实现关联
5. trace 显示我的服务很慢，日志干净，指标看起来正常——但有东西在消耗 CPU。我不知道是哪段代码导致的。
6. 我已经检查了所有三种信号，但它们都没有告诉我为什么慢。我能看到它慢，也能大致看出在调用图中的哪个位置发生，但我看不到具体是哪个函数或哪行代码是问题所在。我是否遗漏了更深层次的可见性？
7. 我的可观测性栈在运行，但变得非常昂贵。我添加了一个新标签，指标数量就爆炸了。发生了什么？
8. 我将 user_id 作为标签添加到一个计数器指标上，Prometheus 变得极其缓慢，存储成本飙升。我不理解一个标签怎么能造成这种情况。我觉得我在可观测性方面做错了，我不知道正确的约束是什么。
