---
id: opentelemetry
title: OpenTelemetry
zone: observability
edges:
  to:
    - id: correlating-signals
      question: >-
        I've instrumented with OTel. Now how do I actually use traces alongside
        my logs and metrics when debugging?
      detail: >-
        I can see traces in Jaeger but when I want to find the logs that
        correspond to a specific trace, I'm manually guessing based on
        timestamps. And getting from a metric spike to the trace for requests
        that happened then feels impossible. Shouldn't these tools talk to each
        other?
difficulty: 2
tags:
  - opentelemetry
  - otel
  - tracing
  - instrumentation
  - observability
  - vendor-neutral
category: practice
milestones:
  - Instrument a service with the OpenTelemetry SDK to emit traces
  - Understand what auto-instrumentation does and when manual spans are needed
  - Configure an OTel collector to export to a backend (Jaeger, Tempo, etc.)
  - Understand why OTel matters for avoiding vendor lock-in
title_zh: "OpenTelemetry"

---


Before OpenTelemetry, every observability vendor shipped their own instrumentation SDK. If you wanted traces, you'd install Jaeger's library, wrap your code in Jaeger-specific calls, and configure Jaeger-specific exporters. If you later wanted to switch to Datadog or Honeycomb, you'd have to rip out every trace call in your entire codebase and replace it with the new vendor's API. For a large application, that could be weeks of work.

OpenTelemetry (usually called OTel) solves this by separating the instrumentation from the backend. You write your tracing code once against the OTel API, and then you configure where the data goes — Jaeger, Tempo, Datadog, Honeycomb, or anything else — without touching your application code. OTel is vendor-neutral and backed by the CNCF, which means it's not going away, and all the major observability vendors support it natively.

OTel also covers all three observability signals — traces, metrics, and logs — under a single unified standard. You don't need three different SDKs from three different vendors. One instrumentation library, one collector, one configuration, and you get all your telemetry flowing to wherever you want it.

<!-- DEEP_DIVE -->

## The three components of OpenTelemetry

OTel is built from three distinct parts that are worth understanding separately:

**The API** is what you call in your application code. It defines the interfaces for creating spans, recording metrics, and emitting logs. The key property of the API is that it's a no-op by default — if you don't attach an SDK, calling the API does nothing and has zero overhead. This means libraries can instrument themselves with OTel without forcing a dependency on any specific SDK.

**The SDK** is the implementation of the API. It's what actually creates spans, samples traces, and hands data to exporters. You install the SDK in your application and configure it at startup. The SDK is where you set things like the service name, the sampling rate, and which exporter to use.

**The Collector** is an optional but highly recommended standalone process that receives telemetry from your services, optionally processes it (filtering, batching, enriching), and exports it to your backend. Instead of having each service talk directly to your backend, services send to the Collector, and the Collector manages the backend connection. This is important for production: it decouples your application from your observability infrastructure and lets you change backends without redeploying your services.

## Auto-instrumentation

The fastest way to get traces is auto-instrumentation. OTel provides agents for most languages that instrument common frameworks automatically — HTTP servers, HTTP clients, database drivers, message queue clients — without you writing a single line of tracing code.

For Python, you install the agent and run your app through it:

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install

# Run your Flask/Django/FastAPI app with auto-instrumentation
opentelemetry-instrument python app.py
```

For Java, you attach a Java agent:

```bash
java -javaagent:opentelemetry-javaagent.jar \
     -Dotel.service.name=my-service \
     -Dotel.exporter.otlp.endpoint=http://collector:4317 \
     -jar myapp.jar
```

Auto-instrumentation gives you spans for every HTTP request your service handles, every outbound HTTP call it makes, and every database query it executes. For many applications, this is enough to get useful traces immediately.

## Manual spans

Auto-instrumentation covers the edges of your service — requests in and out, database calls. But it can't instrument your business logic. If you want to see how long it takes to process an order or validate a payment, you need manual spans.

Here's an example in Python:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        # validate the order
        with tracer.start_as_current_span("validate_order"):
            result = validate(order_id)

        if not result.valid:
            span.set_status(trace.StatusCode.ERROR, "Validation failed")
            return

        # charge the customer
        with tracer.start_as_current_span("charge_customer"):
            charge(order_id)
```

This creates a parent `process_order` span with two child spans: `validate_order` and `charge_customer`. In your trace viewer, you'll see exactly how long each step takes, and if any step errors, it'll be flagged.

Good candidates for manual spans:
- Any significant business logic operation
- External API calls not covered by auto-instrumentation
- Expensive computations you want to track
- Cache hits/misses

## Configuring the OTel Collector

The Collector is configured with a YAML file that defines three things: receivers (how data comes in), processors (what to do with it), and exporters (where it goes).

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

Your services send to `otel-collector:4317` (gRPC) or `otel-collector:4318` (HTTP). The Collector batches the data and forwards it to Jaeger for traces and Prometheus for metrics. If you later decide to switch from Jaeger to Grafana Tempo, you change the exporter config in one place — your application code doesn't change at all.

## The vendor lock-in argument in practice

Here's a concrete example of what OTel saves you from. Without OTel, you might instrument your Go service with the Jaeger client:

```go
// Jaeger-specific code — tied to Jaeger forever
tracer, closer, err := jaeger.NewTracer("my-service", sampler, reporter)
defer closer.Close()

span := tracer.StartSpan("my-operation")
defer span.Finish()
```

With OTel, the same code uses the vendor-neutral API:

```go
// OTel code — works with any backend
tracer := otel.Tracer("my-service")
ctx, span := tracer.Start(ctx, "my-operation")
defer span.End()
```

The OTel version doesn't know or care whether data goes to Jaeger, Tempo, Datadog, or anywhere else. That decision lives entirely in the Collector configuration, outside your application.

<!-- RESOURCES -->

- [OpenTelemetry Getting Started](https://opentelemetry.io/docs/getting-started/) -- type: tutorial, time: 30m
- [OpenTelemetry Collector documentation](https://opentelemetry.io/docs/collector/) -- type: article, time: 20m
- [Auto-instrumentation in OpenTelemetry (Python)](https://opentelemetry.io/docs/zero-code/python/) -- type: tutorial, time: 15m
- [OpenTelemetry Demo Application](https://opentelemetry.io/docs/demo/) -- type: tutorial, time: 45m
- [Why OpenTelemetry? — CNCF blog](https://www.cncf.io/blog/2021/08/06/what-is-opentelemetry-and-why-is-it-the-future-of-instrumentation/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
在 OpenTelemetry 出现之前，每个可观测性厂商都提供自己的埋点 SDK。如果你想要追踪数据，就得安装 Jaeger 的库，用 Jaeger 特有的调用包裹你的代码，并配置 Jaeger 特有的 exporter。如果之后你想切换到 Datadog 或 Honeycomb，就必须把整个代码库中每一处追踪调用都删掉，替换成新厂商的 API。对于一个大型应用来说，这可能需要数周的工作量。

OpenTelemetry（通常简称 OTel）通过将埋点与后端分离来解决这个问题。你只需针对 OTel API 编写一次追踪代码，然后配置数据流向何处——Jaeger、Tempo、Datadog、Honeycomb 或其他任何地方——而无需改动应用代码。OTel 是厂商中立的，并由 CNCF 支持，这意味着它不会消失，而且所有主流可观测性厂商都原生支持它。

OTel 还在单一统一标准下覆盖了全部三种可观测性信号——追踪、指标和日志。你不需要来自三个不同厂商的三个不同 SDK。一个埋点库、一个 collector、一份配置，就能让你所有的遥测数据流向任何你想要的地方。

<!-- ZH_DEEP_DIVE -->
## OpenTelemetry 的三个组成部分

OTel 由三个不同的部分组成，值得分别理解：

**API** 是你在应用代码中调用的部分。它定义了用于创建 span、记录指标和输出日志的接口。API 的关键特性是默认情况下它是空操作（no-op）——如果你没有附加 SDK，调用 API 不会做任何事情，也没有任何开销。这意味着库可以用 OTel 进行自我埋点，而不必强制依赖任何特定的 SDK。

**SDK** 是 API 的实现。它真正负责创建 span、对 trace 进行采样，并将数据交给 exporter。你在应用中安装 SDK，并在启动时进行配置。SDK 是你设置服务名称、采样率以及使用哪个 exporter 等配置的地方。

**Collector** 是一个可选但强烈推荐的独立进程，它从你的服务接收遥测数据，可选地进行处理（过滤、批处理、丰富），然后导出到你的后端。与其让每个服务直接与后端通信，不如让服务发送到 Collector，由 Collector 管理后端连接。这对生产环境很重要：它将你的应用与可观测性基础设施解耦，让你无需重新部署服务就能更换后端。

## 自动埋点

获取 trace 最快的方式是自动埋点。OTel 为大多数语言提供了 agent，可以自动对常见框架进行埋点——HTTP 服务器、HTTP 客户端、数据库驱动、消息队列客户端——而你无需编写任何一行追踪代码。

对于 Python，你安装 agent 并通过它运行你的应用：

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install

# Run your Flask/Django/FastAPI app with auto-instrumentation
opentelemetry-instrument python app.py
```

对于 Java，你附加一个 Java agent：

```bash
java -javaagent:opentelemetry-javaagent.jar \
     -Dotel.service.name=my-service \
     -Dotel.exporter.otlp.endpoint=http://collector:4317 \
     -jar myapp.jar
```

自动埋点会为你的服务处理的每个 HTTP 请求、发起的每个出站 HTTP 调用以及执行的每个数据库查询生成 span。对于许多应用来说，这足以立即获得有用的 trace。

## 手动 span

自动埋点覆盖了服务的边界——请求的进出、数据库调用。但它无法对你的业务逻辑进行埋点。如果你想查看处理订单或验证支付需要多长时间，就需要手动 span。

以下是一个 Python 示例：

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        # validate the order
        with tracer.start_as_current_span("validate_order"):
            result = validate(order_id)

        if not result.valid:
            span.set_status(trace.StatusCode.ERROR, "Validation failed")
            return

        # charge the customer
        with tracer.start_as_current_span("charge_customer"):
            charge(order_id)
```

这会创建一个父 span `process_order`，以及两个子 span：`validate_order` 和 `charge_customer`。在你的 trace 查看器中，你将确切看到每个步骤花费的时间，如果任何步骤出错，它会被标记出来。

适合使用手动 span 的场景：
- 任何重要的业务逻辑操作
- 自动埋点未覆盖的外部 API 调用
- 你想追踪的昂贵计算
- 缓存命中/未命中

## 配置 OTel Collector

Collector 通过一个 YAML 文件进行配置，该文件定义了三个部分：receivers（数据如何进入）、processors（如何处理数据）和 exporters（数据去向何处）。

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

你的服务发送到 `otel-collector:4317`（gRPC）或 `otel-collector:4318`（HTTP）。Collector 对数据进行批处理，并将其转发到 Jaeger 用于 trace、Prometheus 用于指标。如果你之后决定从 Jaeger 切换到 Grafana Tempo，只需在一个地方更改 exporter 配置——你的应用代码完全不需要改动。

## 供应商锁定问题的实践

以下是一个具体示例，说明 OTel 能帮你避免什么。没有 OTel 时，你可能会用 Jaeger 客户端对你的 Go 服务进行埋点：

```go
// Jaeger-specific code — tied to Jaeger forever
tracer, closer, err := jaeger.NewTracer("my-service", sampler, reporter)
defer closer.Close()

span := tracer.StartSpan("my-operation")
defer span.Finish()
```

使用 OTel 时，同样的代码使用供应商中立的 API：

```go
// OTel code — works with any backend
tracer := otel.Tracer("my-service")
ctx, span := tracer.Start(ctx, "my-operation")
defer span.End()
```

OTel 版本不知道也不关心数据是发往 Jaeger、Tempo、Datadog 还是其他地方。这个决定完全存在于 Collector 配置中，在你的应用之外。

<!-- ZH_RESOURCES -->
- [OpenTelemetry 入门](https://opentelemetry.io/docs/getting-started/) -- 类型：教程，时长：30m
- [OpenTelemetry Collector 文档](https://opentelemetry.io/docs/collector/) -- 类型：文章，时长：20m
- [OpenTelemetry 中的自动插桩（Python）](https://opentelemetry.io/docs/zero-code/python/) -- 类型：教程，时长：15m
- [OpenTelemetry 演示应用](https://opentelemetry.io/docs/demo/) -- 类型：教程，时长：45m
- [为什么选择 OpenTelemetry？—— CNCF 博客](https://www.cncf.io/blog/2021/08/06/what-is-opentelemetry-and-why-is-it-the-future-of-instrumentation/) -- 类型：文章，时长：10m

<!-- ZH_UI -->
1. 使用 OpenTelemetry SDK 为服务埋点以生成 trace
2. 理解自动埋点的作用以及何时需要手动 span
3. 配置 OTel collector 导出到后端（Jaeger、Tempo 等）
4. 理解 OTel 为何对避免供应商锁定很重要
5. 我已经用 OTel 埋点了。调试时我究竟该如何把 trace 与日志和指标结合使用？
6. 我能在 Jaeger 中看到 trace，但当我想找到与某个特定 trace 对应的日志时，只能根据时间戳手动猜测。而从指标尖峰找到当时请求对应的 trace 感觉根本不可能。这些工具难道不应该互相通信吗？
