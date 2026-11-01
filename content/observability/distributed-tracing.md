---
id: distributed-tracing
title: Distributed Tracing
zone: observability
edges:
  to:
    - id: opentelemetry
      question: >-
        I want to add tracing but I don't want to be locked into one vendor's
        SDK forever. Is there a standard way to instrument my code?
      detail: >-
        I've looked at Jaeger, Datadog, and Honeycomb and they all have
        different instrumentation libraries. If I pick one and later want to
        switch, I'd have to re-instrument everything. Surely there's a
        vendor-neutral way to add tracing.
    - id: trace-sampling
      question: >-
        I turned on tracing and my storage costs tripled. I can't keep a trace
        for every single request — how do I decide what to keep?
      detail: >-
        Tracing 100% of requests at any real traffic volume is clearly not
        sustainable. But if I sample randomly I might miss the slow requests
        I actually care about. How do people solve this?
    - id: correlating-signals
      question: >-
        I have logs, metrics, and traces. But during an incident I'm jumping
        between three different tools. Shouldn't these connect somehow?
      detail: >-
        I see a latency spike in Grafana, I want to find the trace for one of
        those slow requests, I want to find the logs for that trace — but each
        step requires me to manually guess. I'm copy-pasting timestamps between
        tabs. This can't be how it's supposed to work.
difficulty: 2
tags:
  - tracing
  - opentelemetry
  - jaeger
  - tempo
  - distributed-systems
  - observability
  - spans
category: practice
milestones:
  - Instrument an application with OpenTelemetry to emit spans
  - View a trace in Jaeger or Grafana Tempo
  - Identify the slowest span in a trace and the service responsible
  - 'Understand what a trace, span, and context propagation are'
title_zh: "分布式追踪"

---


When a request hits your API, it might touch five different services before a response comes back. If that request is slow, logs from any single service won't tell you which service caused the problem — they only show what happened inside that service. Distributed tracing solves this by following a single request across every service it touches, recording timing information for each step, and stitching them into a single timeline you can read at a glance.

The core idea is simple: a trace is the complete story of one request, end-to-end. It's made up of spans — each span represents one unit of work. A service receiving an HTTP call is a span. A database query inside that service is another span. A downstream API call is another. Spans have parent-child relationships, so you end up with a tree that mirrors the path the request actually took through your system.

When you look at that tree in a tool like Jaeger or Grafana Tempo, the view is called a waterfall. Time flows left to right, and each span appears as a horizontal bar. Narrow bars mean fast. Wide bars mean slow. If you see one bar that stretches halfway across the screen, you've found your problem. This is something logs alone can never give you — the visual, immediate answer to "which service is the bottleneck?"

<!-- DEEP_DIVE -->

## Traces and spans

A **trace** represents the full lifecycle of a single request, from the moment it enters your system to the moment the response is sent. Every trace has a unique trace ID — a random hex string like `4bf92f3577b34da6a3ce929d0e0e4736`. That ID gets passed along as the request moves through your services, connecting all the work together.

A **span** is one unit of work within a trace. Every span records:
- A name (e.g., `HTTP POST /orders`, `db.query`, `payment-service.charge`)
- A start time and duration
- A status (OK or Error)
- Optional attributes (metadata like `http.status_code`, `db.statement`, `user.id`)
- The trace ID it belongs to
- The ID of its parent span (if it has one)

Here's what a simple three-service trace looks like conceptually:

```
Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736

[api-gateway]           POST /checkout          0ms → 320ms
  [order-service]         createOrder           12ms → 180ms
    [postgres]              INSERT orders        15ms → 42ms
    [payment-service]       chargeCard          50ms → 175ms
      [stripe-api]            POST /charges     55ms → 170ms
```

The api-gateway span is the root span — it has no parent. The order-service span is a child of api-gateway. The postgres and payment-service spans are children of order-service. Reading it this way, you can see immediately that `stripe-api` took 115ms, which is the bulk of the total latency.

## Parent-child relationships and the waterfall view

In a trace viewer, this tree becomes a waterfall diagram. Each span is a horizontal bar, indented to show its depth in the tree. Time is the x-axis. The widest bar is the slowest span.

```
|-- api-gateway (320ms) -----------------------------------|
    |-- order-service (168ms) -------------------|
        |-- postgres (27ms) ----|
        |-- payment-service (125ms) --------------|
            |-- stripe-api (115ms) --------------|
```

Reading a waterfall:
1. Start at the top — the root span shows total request time
2. Look for the widest bars, especially deep in the tree (they're the ones you can optimize)
3. Look for gaps — time where nothing is happening might indicate a lock, a queue wait, or unnecessary serialization
4. Look for spans that run sequentially when they could run in parallel

## Context propagation

For a trace to work, every service needs to know which trace it belongs to. This is done via **context propagation** — the trace ID is passed from service to service as an HTTP header.

The standard header is `traceparent`, defined by the W3C Trace Context specification. It looks like this:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

The fields are: `version-traceId-parentSpanId-flags`. When your order-service calls payment-service, it includes this header in the outgoing HTTP request. Payment-service reads it, creates a new span as a child of the parent span ID, and continues the trace.

Most tracing libraries handle this automatically for common HTTP clients. You declare that you want to propagate context, and the library injects and extracts the header for you.

## Tracing vs logs: what each is for

Logs and traces are complementary, not competing. They answer different questions:

| Question | Use |
|----------|-----|
| Which service caused the slowdown? | Trace (waterfall view) |
| What path did this request take? | Trace (span tree) |
| Was this an error? Where exactly did it fail? | Trace (error status + attributes) |
| What SQL query ran? What did it return? | Log (from the service) |
| What was the user's input that caused this? | Log (structured log line) |
| Did this error happen before or after a deploy? | Log + metric |

A good rule of thumb: traces show you the structure and timing of what happened. Logs show you the details of what happened inside each service. When you're debugging, you typically start with a trace to identify which service and which span is the problem, then look at logs from that service during that time window to understand why.

## A real debugging workflow

1. You get a p99 latency alert — 95th percentile response time is above your SLO.
2. You open Jaeger or Tempo and filter for traces with duration above 2 seconds.
3. You pick one slow trace and open the waterfall. The `payment-service` span is 1.8 seconds wide.
4. You expand the payment-service span and see `stripe-api` is 1.75 seconds — a timeout, probably.
5. You look at the span attributes: `http.status_code: 504`. The Stripe API timed out.
6. You check whether Stripe had an incident at that time. They did.

Without tracing, step 4 might have taken hours of log-digging across multiple services. With tracing, it took about two minutes.

<!-- RESOURCES -->

- [Distributed Tracing — OpenTelemetry docs](https://opentelemetry.io/docs/concepts/observability-primer/#distributed-traces) -- type: article, time: 10m
- [Jaeger: Getting Started](https://www.jaegertracing.io/docs/latest/getting-started/) -- type: tutorial, time: 20m
- [W3C Trace Context specification](https://www.w3.org/TR/trace-context/) -- type: article, time: 15m
- [Grafana Tempo: Getting Started](https://grafana.com/docs/tempo/latest/getting-started/) -- type: tutorial, time: 20m
- [Life of a Span — Lightstep blog](https://lightstep.com/blog/life-of-a-span) -- type: article, time: 8m

<!-- ZH_SUMMARY -->
当一个请求到达你的 API 时，它可能在返回响应之前经过五个不同的服务。如果这个请求很慢，任何单个服务的日志都无法告诉你究竟是哪个服务导致了问题——它们只显示该服务内部发生了什么。分布式追踪通过跟踪单个请求经过它触及的每一个服务、记录每一步的耗时信息，并将它们拼接成一条一眼就能读懂的时间线，从而解决了这个问题。

核心思想很简单：一个 trace 就是一个请求端到端的完整故事。它由 span 组成——每个 span 代表一个工作单元。一个服务接收到 HTTP 调用是一个 span。该服务内部的一次数据库查询是另一个 span。一次下游 API 调用又是一个。span 之间具有父子关系，因此你最终会得到一棵树，它映射出请求在你的系统中实际经过的路径。

当你在 Jaeger 或 Grafana Tempo 这类工具中查看这棵树时，这种视图被称为瀑布图（waterfall）。时间从左向右流动，每个 span 显示为一条水平条。窄条表示快。宽条表示慢。如果你看到某一条横跨半个屏幕，你就找到问题了。这是仅靠日志永远无法给你的东西——对“哪个服务是瓶颈？”这个问题的直观、即时的答案。

<!-- ZH_DEEP_DIVE -->
## Trace 与 Span

一个 **trace** 代表单个请求的完整生命周期，从它进入你的系统的那一刻起，到响应被发送的那一刻止。每个 trace 都有一个唯一的 trace ID——一个随机的十六进制字符串，例如 `4bf92f3577b34da6a3ce929d0e0e4736`。当请求在你的各个服务之间流转时，这个 ID 会被一路传递，把所有工作串联在一起。

一个 **span** 是 trace 中的一个工作单元。每个 span 记录：
- 一个名称（例如 `HTTP POST /orders`、`db.query`、`payment-service.charge`）
- 开始时间和持续时间
- 一个状态（OK 或 Error）
- 可选属性（元数据，如 `http.status_code`、`db.statement`、`user.id`）
- 它所属的 trace ID
- 其父 span 的 ID（如果有的话）

下面是一个简单的三服务 trace 在概念上的样子：

```
Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736

[api-gateway]           POST /checkout          0ms → 320ms
  [order-service]         createOrder           12ms → 180ms
    [postgres]              INSERT orders        15ms → 42ms
    [payment-service]       chargeCard          50ms → 175ms
      [stripe-api]            POST /charges     55ms → 170ms
```

api-gateway 这个 span 是根 span——它没有父 span。order-service 这个 span 是 api-gateway 的子 span。postgres 和 payment-service 这两个 span 是 order-service 的子 span。这样读下来，你可以立刻看出 `stripe-api` 耗时 115ms，占了总延迟的大部分。

## 父子关系与瀑布图视图

在 trace 查看器中，这棵树会变成一张瀑布图。每个 span 是一根水平条，通过缩进来表示它在树中的深度。时间作为 x 轴。最宽的条就是最慢的 span。

```
|-- api-gateway (320ms) -----------------------------------|
    |-- order-service (168ms) -------------------|
        |-- postgres (27ms) ----|
        |-- payment-service (125ms) --------------|
            |-- stripe-api (115ms) --------------|
```

阅读瀑布图的方法：
1. 从顶部开始——根 span 显示总请求时间
2. 寻找最宽的条，尤其是树中较深位置的条（它们才是你可以优化的对象）
3. 寻找空隙——什么都没发生的时间可能意味着锁、队列等待或不必要的串行化
4. 寻找那些本可以并行执行、却串行执行的 span

## 上下文传播

要让 trace 正常工作，每个服务都需要知道它属于哪个 trace。这通过 **上下文传播** 来实现——trace ID 作为 HTTP 头在服务之间传递。

标准头是 `traceparent`，由 W3C Trace Context 规范定义。它看起来像这样：

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

各字段依次为：`version-traceId-parentSpanId-flags`。当你的 order-service 调用 payment-service 时，它会在发出的 HTTP 请求中包含这个头。payment-service 读取它，以父 span ID 为父创建一个新的 span，并继续这个 trace。

大多数追踪库会为常见的 HTTP 客户端自动处理这一点。你只需声明希望传播上下文，库就会为你注入和提取该头。

## 追踪与日志：各自的用途

日志和 trace 是互补的，而非相互竞争的。它们回答不同的问题：

| 问题 | 使用 |
|----------|-----|
| 是哪个服务导致了变慢？ | Trace（瀑布图视图） |
| 这个请求走了什么路径？ | Trace（span 树） |
| 这是不是一次错误？具体在哪里失败的？ | Trace（错误状态 + 属性） |
| 执行了什么 SQL 查询？返回了什么？ | 日志（来自该服务） |
| 导致此问题的用户输入是什么？ | 日志（结构化日志行） |
| 这个错误发生在部署之前还是之后？ | 日志 + 指标 |

一个很好的经验法则：trace 向你展示发生了什么的结构和时序。日志向你展示每个服务内部发生的细节。调试时，你通常先从 trace 入手，确定是哪个服务、哪个 span 出了问题，然后查看该服务在那个时间窗口内的日志，以理解原因。

## 一个真实的调试工作流

1. 你收到一个 p99 延迟告警——第 95 百分位响应时间超过了你的 SLO。
2. 你打开 Jaeger 或 Tempo，筛选持续时间超过 2 秒的 trace。
3. 你挑一个慢 trace 并打开瀑布图。`payment-service` 这个 span 宽达 1.8 秒。
4. 你展开 payment-service 这个 span，看到 `stripe-api` 是 1.75 秒——很可能是一次超时。
5. 你查看 span 属性：`http.status_code: 504`。Stripe API 超时了。
6. 你检查 Stripe 在那个时间是否发生了故障。确实发生了。

如果没有追踪，第 4 步可能需要在多个服务之间翻日志，耗费数小时。有了追踪，只花了大约两分钟。

<!-- ZH_RESOURCES -->
- [分布式追踪 — OpenTelemetry 文档](https://opentelemetry.io/docs/concepts/observability-primer/#distributed-traces) -- 类型: 文章, 时间: 10m
- [Jaeger: 入门指南](https://www.jaegertracing.io/docs/latest/getting-started/) -- 类型: 教程, 时间: 20m
- [W3C Trace Context 规范](https://www.w3.org/TR/trace-context/) -- 类型: 文章, 时间: 15m
- [Grafana Tempo: 入门指南](https://grafana.com/docs/tempo/latest/getting-started/) -- 类型: 教程, 时间: 20m
- [Span 的一生 — Lightstep 博客](https://lightstep.com/blog/life-of-a-span) -- 类型: 文章, 时间: 8m

<!-- ZH_UI -->
1. 使用 OpenTelemetry 为应用埋点以生成 span
2. 在 Jaeger 或 Grafana Tempo 中查看 trace
3. 找出 trace 中最慢的 span 及负责的服务
4. 理解什么是 trace、span 和上下文传播
5. 我想加 tracing，但不想永远被绑定在某家厂商的 SDK 上。有没有标准的方式来为代码埋点？
6. 我看过 Jaeger、Datadog 和 Honeycomb，它们的埋点库各不相同。如果我选了一个以后想换，就得重新埋点所有东西。肯定有厂商中立的方式来加 tracing 吧。
7. 我开了 tracing 后存储成本翻了三倍。我不能为每个请求都保留 trace——该怎么决定保留哪些？
8. 在任何真实流量下 100% 采样所有请求显然不可持续。但如果随机采样，可能会漏掉我真正关心的慢请求。大家是怎么解决的？
9. 我有日志、指标和 trace。但出故障时我得在三个不同工具之间来回跳。它们不应该能关联起来吗？
10. 我在 Grafana 看到延迟飙升，想找到某个慢请求的 trace，再找到那个 trace 的日志——但每一步都得手动猜。我在标签页之间复制粘贴时间戳。这不该是它应有的工作方式。
