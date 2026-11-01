---
id: structured-logging
title: Structured Logging
zone: observability
edges:
  to:
    - id: log-aggregation
      question: >-
        My services emit structured logs. How do I collect and search them all
        in one place?
      detail: >-
        My logs are structured now but they're spread across 10 different
        containers and 3 services. When something breaks I have to SSH into
        each one separately and grep. There must be a way to search everything
        from one place.
difficulty: 1
tags:
  - logging
  - structured-logging
  - json
  - correlation-id
  - request-tracing
  - observability
category: practice
milestones:
  - Switch your application from print/printf to a structured logging library
  - 'Emit logs as JSON with consistent fields: timestamp, level, service, message'
  - >-
    Add a correlation ID to every log line so you can trace a request across
    services
  - >-
    Understand what log levels are for and why DEBUG logs shouldn't run in
    production
title_zh: "结构化日志记录"

---


Plain text logs work fine when you have one small service. When you have three services, a database, a message queue, and traffic from thousands of users, plain text stops scaling. The problem isn't the format itself — it's that text logs can only be searched with text search. You can grep for "error" but you can't ask "show me all requests for user 12345 that took longer than 500ms and returned an error." For that, your log lines need to be machine-parseable, not just human-readable.

Structured logging solves this by emitting logs as key-value pairs — usually JSON — rather than free-form strings. Instead of writing "Payment failed for user 9912 after 3 retries", you write a log event where `level`, `message`, `user_id`, `attempt_count`, and `duration_ms` are all separate, queryable fields. The message is still there and still readable, but now it lives alongside a set of structured fields that a log query tool can filter, aggregate, and join on.

The shift to structured logging is one of the highest-leverage things you can do early in a service's life. It costs very little upfront — swap your print statements for a logging library call — and it unlocks the ability to actually use your logs at scale rather than just grep through them.

<!-- DEEP_DIVE -->

## Plain text vs. structured: a concrete comparison

Imagine a payment service. Here's what the same event looks like as plain text versus structured JSON.

**Plain text:**
```
[2024-01-15 14:32:01] ERROR: Payment processing failed for user 9912 (order 4821): card declined after 2 attempts, took 1842ms
```

This is readable. But to find all failed payments in the last hour, you'd have to grep for "Payment processing failed" and parse the rest by hand. To find failures for a specific user, you'd grep for "user 9912". There's no reliable way to filter by duration or attempt count.

**Structured JSON:**
```json
{
  "timestamp": "2024-01-15T14:32:01Z",
  "level": "error",
  "service": "payment-service",
  "message": "Payment processing failed",
  "user_id": 9912,
  "order_id": 4821,
  "reason": "card_declined",
  "attempt_count": 2,
  "duration_ms": 1842,
  "request_id": "req_a8f3d2c1"
}
```

Now every field is independently queryable. In a log query tool you can write: `service="payment-service" level="error" duration_ms > 1000` and get exactly the results you want. You can group by `reason` to see the breakdown of failure causes. You can filter by `user_id` to see everything that happened for one specific user.

## The standard fields

Every log line your services emit should have a consistent set of base fields. Consistency is what makes logs queryable at scale — if `user_id` is called `userId` in one service and `user` in another, joining on user becomes a manual mess.

These fields should be on every log line:

| Field | Format | Example |
|-------|--------|---------|
| `timestamp` | ISO 8601, UTC | `"2024-01-15T14:32:01.412Z"` |
| `level` | lowercase string | `"error"` |
| `service` | service name | `"payment-service"` |
| `message` | human-readable string | `"Payment processing failed"` |
| `request_id` | UUID or similar | `"req_a8f3d2c1"` |

Beyond that, add context fields relevant to what's being logged: `user_id`, `order_id`, `duration_ms`, `http_status`, `error`, whatever is meaningful for the operation.

## The correlation ID pattern

One of the most valuable uses of structured logging is tracing a single request through multiple services. If a user's request hits your API, which calls a payment service, which calls a database — that single user action generates log lines in at least three places. Without a way to tie them together, debugging a failure means trying to correlate logs from different places by timestamp alone, which is imprecise and painful.

The solution is a correlation ID (also called a request ID or trace ID). At the entry point of a request, generate a unique ID and attach it to every log line for the duration of that request. When your API calls the payment service, pass the correlation ID in a header. The payment service picks it up and includes it in its own logs.

```python
import uuid
import logging

def handle_request(request):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    logger = logging.LoggerAdapter(base_logger, {"request_id": request_id})

    logger.info("Request received", extra={"path": request.path, "method": request.method})
    # ... handle the request
    # Pass request_id to downstream services via header
```

Now when something goes wrong, you take the `request_id` from the user's error report, search your log aggregation system for all lines with that ID, and see the complete story of that request across every service — in chronological order.

## Logging libraries

Don't use raw print statements or `fmt.Println` for production logging. A proper logging library handles timestamp generation, level filtering, output formatting, and structured field attachment without you having to build it yourself.

**Python — structlog:**
```python
import structlog

log = structlog.get_logger()

log.info("payment_processed",
    order_id=4821,
    user_id=9912,
    amount=49.99,
    duration_ms=312
)
```

**Go — zap or zerolog:**
```go
// zerolog
log.Info().
    Int("order_id", 4821).
    Int("user_id", 9912).
    Float64("amount", 49.99).
    Int64("duration_ms", 312).
    Msg("payment processed")
```

**Node.js — pino:**
```javascript
const logger = require('pino')()

logger.info({
  order_id: 4821,
  user_id: 9912,
  amount: 49.99,
  duration_ms: 312
}, 'payment processed')
```

Each of these outputs a JSON line per event with consistent structure. The tradeoff for readability during local development — JSON is noisy to read in a terminal — is usually handled with a pretty-printer script or a development mode that formats output differently.

## Practical tips

**Add context once, not on every call.** Most logging libraries support "bound loggers" — a logger with certain fields already attached. Bind `request_id` and `user_id` at the start of a request, then use that bound logger throughout. You won't forget to include them on individual log calls.

**Log errors with their full context, not just the message.** `log.Error("failed")` is useless. Include the error object, relevant IDs, and whatever the system was doing when it failed.

**Keep message strings static.** Put dynamic values in fields, not embedded in the message string. `log.Info("user logged in", user_id=9912)` is better than `log.Info(f"user {9912} logged in")` — the latter makes it impossible to group or search by message text.

<!-- RESOURCES -->

- [structlog Documentation (Python)](https://www.structlog.org/en/stable/) -- type: article, time: 20m
- [zerolog — Zero Allocation JSON Logger (Go)](https://github.com/rs/zerolog) -- type: article, time: 10m
- [pino — Node.js Logger](https://getpino.io/) -- type: article, time: 10m
- [Structured Logging Best Practices (Datadog)](https://www.datadoghq.com/blog/engineering/logs-performance-best-practices/) -- type: article, time: 12m

<!-- ZH_SUMMARY -->
当你只有一个小型服务时，纯文本日志完全够用。但当你拥有三个服务、一个数据库、一个消息队列，以及来自数千名用户的流量时，纯文本就无法扩展了。问题不在于格式本身——而在于文本日志只能通过文本搜索来检索。你可以用 grep 搜索“error”，但你无法查询“显示用户 12345 所有耗时超过 500ms 且返回错误的请求”。要做到这一点，你的日志行必须是机器可解析的，而不仅仅是人类可读的。

结构化日志通过将日志输出为键值对——通常是 JSON——而非自由格式的字符串来解决这个问题。与其写“Payment failed for user 9912 after 3 retries”，你写的是一个日志事件，其中 `level`、`message`、`user_id`、`attempt_count` 和 `duration_ms` 都是独立的、可查询的字段。消息仍然存在，仍然可读，但现在它与一组结构化字段并存，日志查询工具可以对这些字段进行过滤、聚合和关联。

向结构化日志的转变是你在服务生命周期早期所能做的最具杠杆效应的事情之一。它的前期成本非常低——把 print 语句换成日志库调用——却能解锁在规模化场景下真正利用日志的能力，而不仅仅是 grep 翻阅它们。

<!-- ZH_DEEP_DIVE -->
## 纯文本与结构化：具体对比

设想一个支付服务。下面展示的是同一个事件在纯文本和结构化 JSON 下的样子。

**纯文本：**
```
[2024-01-15 14:32:01] ERROR: Payment processing failed for user 9912 (order 4821): card declined after 2 attempts, took 1842ms
```

这段内容可读。但要找出过去一小时内所有失败的支付，你得用 grep 搜索 “Payment processing failed”，再手动解析其余部分。要查找某个特定用户的失败，你得 grep “user 9912”。没有可靠的方式按耗时或尝试次数进行过滤。

**结构化 JSON：**
```json
{
  "timestamp": "2024-01-15T14:32:01Z",
  "level": "error",
  "service": "payment-service",
  "message": "Payment processing failed",
  "user_id": 9912,
  "order_id": 4821,
  "reason": "card_declined",
  "attempt_count": 2,
  "duration_ms": 1842,
  "request_id": "req_a8f3d2c1"
}
```

现在每个字段都可以独立查询。在日志查询工具中你可以写：`service="payment-service" level="error" duration_ms > 1000`，精确得到你想要的结果。你可以按 `reason` 分组，查看失败原因的分布。你可以按 `user_id` 过滤，查看某个特定用户发生的所有事情。

## 标准字段

你的服务输出的每一行日志都应有一组一致的基础字段。一致性是日志能够大规模可查询的关键——如果 `user_id` 在一个服务中叫 `userId`，在另一个服务中叫 `user`，那么按用户关联就会变成手工处理的烂摊子。

这些字段应出现在每一行日志中：

| 字段 | 格式 | 示例 |
|-------|--------|---------|
| `timestamp` | ISO 8601，UTC | `"2024-01-15T14:32:01.412Z"` |
| `level` | 小写字符串 | `"error"` |
| `service` | 服务名称 | `"payment-service"` |
| `message` | 人类可读字符串 | `"Payment processing failed"` |
| `request_id` | UUID 或类似 | `"req_a8f3d2c1"` |

除此之外，添加与所记录内容相关的上下文字段：`user_id`、`order_id`、`duration_ms`、`http_status`、`error`，任何对操作有意义的字段。

## 关联 ID 模式

结构化日志最有价值的用途之一，是追踪单个请求穿过多个服务的过程。如果用户的请求到达你的 API，API 调用支付服务，支付服务又调用数据库——这一个用户操作至少会在三个地方产生日志行。如果没有办法把它们关联起来，调试故障就意味着只能靠时间戳去关联不同地方的日志，这既不精确又痛苦。

解决方案是关联 ID（也称为请求 ID 或追踪 ID）。在请求的入口点生成一个唯一 ID，并在该请求的持续时间内将其附加到每一行日志。当你的 API 调用支付服务时，在请求头中传递关联 ID。支付服务接收它，并将其包含在自己的日志中。

```python
import uuid
import logging

def handle_request(request):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    logger = logging.LoggerAdapter(base_logger, {"request_id": request_id})

    logger.info("Request received", extra={"path": request.path, "method": request.method})
    # ... handle the request
    # Pass request_id to downstream services via header
```

现在出问题时，你从用户的错误报告中拿到 `request_id`，在日志聚合系统中搜索所有带有该 ID 的日志行，就能按时间顺序看到该请求在每个服务中的完整过程。

## 日志库

不要用裸 print 语句或 `fmt.Println` 做生产日志。一个合适的日志库会处理时间戳生成、级别过滤、输出格式化和结构化字段附加，无需你自己构建。

**Python — structlog：**
```python
import structlog

log = structlog.get_logger()

log.info("payment_processed",
    order_id=4821,
    user_id=9912,
    amount=49.99,
    duration_ms=312
)
```

**Go — zap 或 zerolog：**
```go
// zerolog
log.Info().
    Int("order_id", 4821).
    Int("user_id", 9912).
    Float64("amount", 49.99).
    Int64("duration_ms", 312).
    Msg("payment processed")
```

**Node.js — pino：**
```javascript
const logger = require('pino')()

logger.info({
  order_id: 4821,
  user_id: 9912,
  amount: 49.99,
  duration_ms: 312
}, 'payment processed')
```

这些库每个事件输出一行结构一致的 JSON。本地开发时可读性方面的代价——在终端里读 JSON 很嘈杂——通常通过美化打印脚本或采用不同输出格式的开发模式来处理。

## 实用技巧

**上下文只添加一次，而不是每次调用都加。** 大多数日志库支持“绑定日志器”——即已经附加了某些字段的日志器。在请求开始时绑定 `request_id` 和 `user_id`，然后全程使用该绑定日志器。你就不会忘记在单次日志调用中包含它们。

**记录错误时要带上完整上下文，而不只是消息。** `log.Error("failed")` 毫无用处。要包含错误对象、相关 ID，以及系统失败时正在做什么。

**保持消息字符串静态。** 把动态值放在字段中，而不是嵌入消息字符串。`log.Info("user logged in", user_id=9912)` 比 `log.Info(f"user {9912} logged in")` 更好——后者使得无法按消息文本进行分组或搜索。

<!-- ZH_RESOURCES -->
- [structlog 文档 (Python)](https://www.structlog.org/en/stable/) -- 类型: 文章, 时间: 20m
- [zerolog — 零分配 JSON 日志库 (Go)](https://github.com/rs/zerolog) -- 类型: 文章, 时间: 10m
- [pino — Node.js 日志库](https://getpino.io/) -- 类型: 文章, 时间: 10m
- [结构化日志最佳实践 (Datadog)](https://www.datadoghq.com/blog/engineering/logs-performance-best-practices/) -- 类型: 文章, 时间: 12m

<!-- ZH_UI -->
1. 将应用从 print/printf 切换到结构化日志库
2. 以 JSON 格式输出日志，字段保持一致：timestamp、level、service、message
3. 为每行日志添加关联 ID，以便跨服务追踪请求
4. 理解日志级别的用途，以及为什么生产环境不应运行 DEBUG 日志
5. 我的服务输出结构化日志。如何在一处集中收集并搜索所有日志？
6. 我的日志现在已是结构化的，但分散在 10 个不同容器和 3 个服务中。出问题时我得逐个 SSH 登录并 grep。总该有一种方式能在一处搜索全部内容。
