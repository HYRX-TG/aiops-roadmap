---
id: log-levels
title: Log Levels
zone: observability
edges:
  to:
    - id: structured-logging
      question: >-
        I've got log levels set up. But searching through plain text is still
        painful. Is there a better format?
      detail: >-
        I'm using debug and error now but even filtered to just errors, each
        line is just a sentence — I can't filter by field or join on a request
        ID. The right level is there but the message itself is impossible to
        parse programmatically.
difficulty: 1
tags:
  - logging
  - log-levels
  - observability
category: practice
milestones:
  - Understand what each log level means and when to use it
  - Configure your service to log at info by default and debug only when needed
  - Understand why debug-everywhere destroys signal-to-noise ratio
  - Know which level should cause an alert vs which is just informational
title_zh: "日志级别"

---


Every logging library gives you levels — DEBUG, INFO, WARN, ERROR — but most people either ignore them (logging everything at the same level) or misuse them (calling everything an ERROR). Getting this right is one of the cheapest observability improvements you can make, because log levels are the primary mechanism for controlling signal-to-noise ratio. When everything is at the same level, your logs are noise. When levels are used correctly, you can filter to just errors and see exactly what's broken.

The mental model is simple: the level tells you how much attention this event deserves. DEBUG is for detailed internal state you'd only want when actively diagnosing a specific problem. INFO is for normal, noteworthy events. WARN is for unexpected things that were handled gracefully. ERROR is for things that went wrong and shouldn't have. Anything you'd want to be woken up about at 2am belongs at ERROR, possibly higher.

The rule of thumb for production is: run at INFO, flip to DEBUG only when actively investigating. DEBUG in production all the time means your real errors are buried under thousands of lines of normal operation detail. A spike of ERRORs should jump out immediately when you look at your logs — and it can't, if the errors are swimming in a sea of DEBUG output.

<!-- DEEP_DIVE -->

## The four main levels

### DEBUG

Debug logs are internal, verbose, for developers. They record the kind of detail you'd want when you're sitting at your desk trying to understand why something is misbehaving: function arguments, loop iteration counts, intermediate variable values, database query parameters.

```
DEBUG: Fetching user from cache key=user:9912
DEBUG: Cache miss, querying database user_id=9912
DEBUG: Query returned in 4ms rows=1
DEBUG: Building user object from row id=9912 email=alice@example.com
```

This is useful when you're debugging a problem. It's noise when you're not. The rule: never leave DEBUG logging on in production continuously. The volume will bury your real signals and the storage costs add up fast.

### INFO

Info logs record normal, noteworthy events — things that are worth knowing happened, but not alarming. Request received, job started, job completed, user logged in, payment processed.

```
INFO: Payment processed order_id=4821 user_id=9912 amount=49.99 duration_ms=312
INFO: User session created user_id=9912 ip=203.0.113.45
INFO: Scheduled job started job=daily-report
INFO: Scheduled job completed job=daily-report records_processed=14291 duration_ms=8420
```

INFO is your default production log level. It gives you an audit trail of what your system was doing without overwhelming you with detail.

### WARN

WARN is the most commonly misused level. People either never use it or use it for things that are genuinely errors. The correct definition: WARN is for something unexpected that happened, but the system handled it and continued operating normally.

Good candidates for WARN:
- A retry succeeded on the second attempt (the first attempt failed, but we recovered)
- Falling back to a slower path because the faster one is unavailable
- A deprecated API endpoint is being called (it works, but it shouldn't be)
- A request took longer than expected but succeeded

```
WARN: Payment gateway timed out, retrying order_id=4821 attempt=1
INFO: Payment gateway retry succeeded order_id=4821 attempt=2
WARN: Deprecated endpoint called /api/v1/users client_ip=203.0.113.45
```

WARN says: "I noticed something, dealt with it, and you should probably know." It's not necessarily a problem right now, but it might be a sign of something worth looking into.

### ERROR

ERROR means something went wrong that shouldn't have. A request failed. An operation that was expected to succeed didn't. Data that should be valid isn't. An external dependency returned an unexpected response.

```
ERROR: Payment failed order_id=4821 user_id=9912 reason="card_declined" error="stripe: card was declined"
ERROR: Database query failed query="SELECT * FROM orders WHERE id=?" error="connection refused" duration_ms=5001
ERROR: Unhandled exception in request handler path=/api/checkout method=POST error="NullPointerException at PaymentService.java:142"
```

ERRORs should be relatively rare in a healthy system. If you're generating hundreds of ERRORs per minute during normal operation, either something is actually broken, or things that should be WARN or INFO are being logged at ERROR. Both problems are worth fixing.

## The signal-to-noise problem in practice

Imagine your service is emitting 10,000 log lines per minute: 9,900 at DEBUG and 100 at INFO. Buried somewhere in those 10,000 lines are 3 ERROR lines. Someone has to find those 3 lines.

Now flip to INFO level (suppress DEBUG), and you're emitting 103 lines per minute — 100 INFO and 3 ERROR. The errors are immediately visible.

This is why "log everything at DEBUG in production" is such a bad practice. It doesn't add safety — it removes it. The errors are there, they're just invisible.

## Configuring log levels

Most logging libraries read the log level from an environment variable or config file at startup. You never want to hardcode a level in your application — that would require a redeploy to change it.

**Python (standard library):**
```python
import logging
import os

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
```

**Go (with slog):**
```go
level := slog.LevelInfo
if os.Getenv("LOG_LEVEL") == "DEBUG" {
    level = slog.LevelDebug
}
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level}))
```

**Node.js (with pino):**
```javascript
const pino = require('pino')
const logger = pino({ level: process.env.LOG_LEVEL || 'info' })
```

The pattern is the same everywhere: default to INFO, allow override via environment variable. When you need to debug a production issue, set `LOG_LEVEL=DEBUG` for a specific service instance, capture what you need, then set it back.

## Which level should trigger an alert?

Not all levels are equally alertworthy. A general rule:

| Level | Alert? | Why |
|-------|--------|-----|
| DEBUG | No | Never in production; pure noise |
| INFO | No | Normal operation |
| WARN | Maybe | Worth a dashboard, alert only if rate spikes significantly |
| ERROR | Yes | Failures shouldn't be happening; alert when error rate exceeds threshold |

Alerts on raw ERROR counts are often noisy. A better approach is to alert on error rate — ERRORs as a percentage of total requests. A single error in 10,000 requests is very different from 500 errors in 1,000 requests.

<!-- RESOURCES -->

- [Log Levels Explained (Loggly)](https://www.loggly.com/blog/logging-levels/) -- type: article, time: 8m
- [Python Logging HOWTO (official docs)](https://docs.python.org/3/howto/logging.html) -- type: article, time: 15m
- [Structured Logging with Go slog](https://pkg.go.dev/log/slog) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
每个日志库都提供日志级别——DEBUG、INFO、WARN、ERROR——但大多数人要么忽略它们（把所有日志都记录在同一级别），要么误用它们（把所有事情都标为 ERROR）。把这一点做对，是你能做出的成本最低的可观测性改进之一，因为日志级别是控制信噪比的主要机制。当所有日志都处于同一级别时，你的日志就是噪声。当级别被正确使用时，你可以只筛选出错误，准确看到哪里出了问题。

心智模型很简单：级别告诉你这个事件值得多少关注。DEBUG 用于详细的内部状态，只有在你主动诊断特定问题时才会需要。INFO 用于正常的、值得注意的事件。WARN 用于那些被妥善处理的意外情况。ERROR 用于出了错且本不该出错的事情。任何你希望在凌晨 2 点被叫醒来处理的事情都应归为 ERROR，甚至更高。

生产环境的经验法则是：以 INFO 级别运行，只在主动调查时才切换到 DEBUG。在生产环境一直开着 DEBUG，意味着你真正的错误会被埋没在数千行正常运行的细节之下。当你查看日志时，ERROR 的激增应该立刻跳出来——但如果错误淹没在 DEBUG 输出的海洋里，就做不到这一点。

<!-- ZH_DEEP_DIVE -->
## 四个主要级别

### DEBUG

Debug 日志是内部的、详细的，面向开发者。它们记录的是当你坐在桌前试图弄清楚某件事为何出问题时想要的那种细节：函数参数、循环迭代次数、中间变量值、数据库查询参数。

```
DEBUG: Fetching user from cache key=user:9912
DEBUG: Cache miss, querying database user_id=9912
DEBUG: Query returned in 4ms rows=1
DEBUG: Building user object from row id=9912 email=alice@example.com
```

这在调试问题时很有用。不调试时它就是噪音。规则是：绝不要在生产环境持续开启 DEBUG 日志。其数据量会淹没你真正的信号，存储成本也会迅速累积。

### INFO

Info 日志记录正常的、值得注意的事件——值得知道已经发生、但并不令人警觉的事情。收到请求、任务开始、任务完成、用户登录、支付处理完成。

```
INFO: Payment processed order_id=4821 user_id=9912 amount=49.99 duration_ms=312
INFO: User session created user_id=9912 ip=203.0.113.45
INFO: Scheduled job started job=daily-report
INFO: Scheduled job completed job=daily-report records_processed=14291 duration_ms=8420
```

INFO 是你默认的生产日志级别。它为你提供系统正在做什么的审计轨迹，又不会用过多细节淹没你。

### WARN

WARN 是最常被误用的级别。人们要么从不使用它，要么把它用于真正的错误。正确定义是：WARN 用于发生了意外情况，但系统已处理并继续正常运行。

适合使用 WARN 的场景：
- 重试在第二次尝试时成功（第一次尝试失败，但我们恢复了）
- 因为更快的路径不可用而回退到较慢的路径
- 调用了已弃用的 API 端点（它能工作，但不应该被调用）
- 请求耗时超过预期但成功了

```
WARN: Payment gateway timed out, retrying order_id=4821 attempt=1
INFO: Payment gateway retry succeeded order_id=4821 attempt=2
WARN: Deprecated endpoint called /api/v1/users client_ip=203.0.113.45
```

WARN 表达的是：“我注意到了某件事，处理了它，你可能应该知道。”它当下不一定是问题，但可能是值得调查的迹象。

### ERROR

ERROR 意味着发生了本不该发生的错误。请求失败了。本应成功的操作没有成功。本应有效的数据无效。外部依赖返回了意外响应。

```
ERROR: Payment failed order_id=4821 user_id=9912 reason="card_declined" error="stripe: card was declined"
ERROR: Database query failed query="SELECT * FROM orders WHERE id=?" error="connection refused" duration_ms=5001
ERROR: Unhandled exception in request handler path=/api/checkout method=POST error="NullPointerException at PaymentService.java:142"
```

在健康的系统中，ERROR 应该相对少见。如果你在正常运行期间每分钟产生数百条 ERROR，要么确实有东西坏了，要么本应记为 WARN 或 INFO 的内容被记录成了 ERROR。这两个问题都值得修复。

## 实践中的信噪比问题

想象你的服务每分钟产生 10,000 行日志：9,900 行是 DEBUG，100 行是 INFO。在这 10,000 行中的某处埋着 3 行 ERROR。必须有人找出这 3 行。

现在切换到 INFO 级别（抑制 DEBUG），你每分钟产生 103 行——100 行 INFO 和 3 行 ERROR。错误立刻可见。

这就是为什么“在生产环境把所有内容都按 DEBUG 记录”是如此糟糕的做法。它不会增加安全性——反而会消除安全性。错误就在那里，只是不可见。

## 配置日志级别

大多数日志库在启动时从环境变量或配置文件读取日志级别。你绝不应该在应用程序中硬编码级别——那将需要重新部署才能更改。

**Python（标准库）：**
```python
import logging
import os

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
```

**Go（使用 slog）：**
```go
level := slog.LevelInfo
if os.Getenv("LOG_LEVEL") == "DEBUG" {
    level = slog.LevelDebug
}
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level}))
```

**Node.js（使用 pino）：**
```javascript
const pino = require('pino')
const logger = pino({ level: process.env.LOG_LEVEL || 'info' })
```

各处的模式都一样：默认 INFO，允许通过环境变量覆盖。当你需要调试生产问题时，为特定服务实例设置 `LOG_LEVEL=DEBUG`，捕获你需要的信息，然后改回去。

## 哪个级别应该触发告警？

并非所有级别都同样值得告警。一般规则：

| 级别 | 告警？ | 原因 |
|-------|--------|-----|
| DEBUG | 否 | 绝不在生产环境；纯噪音 |
| INFO | 否 | 正常运行 |
| WARN | 也许 | 值得放到仪表盘，仅在速率显著飙升时告警 |
| ERROR | 是 | 失败不应发生；错误率超过阈值时告警 |

基于原始 ERROR 计数的告警通常噪音很大。更好的方法是基于错误率告警——ERROR 占总请求数的百分比。10,000 个请求中的 1 个错误与 1,000 个请求中的 500 个错误截然不同。

<!-- ZH_RESOURCES -->
- [日志级别详解 (Loggly)](https://www.loggly.com/blog/logging-levels/) -- 类型: 文章, 时长: 8分钟
- [Python 日志记录指南 (官方文档)](https://docs.python.org/3/howto/logging.html) -- 类型: 文章, 时长: 15分钟
- [使用 Go slog 进行结构化日志记录](https://pkg.go.dev/log/slog) -- 类型: 文章, 时长: 10分钟

<!-- ZH_UI -->
1. 理解每个日志级别的含义以及何时使用
2. 将服务配置为默认以 info 级别记录日志，仅在需要时使用 debug
3. 理解为什么到处开 debug 会破坏信噪比
4. 知道哪个级别应触发告警，哪个只是信息性记录
5. 我已经设置好日志级别了。但搜索纯文本仍然很痛苦。有没有更好的格式？
6. 我现在用 debug 和 error，但即使只过滤到 error，每一行也只是一句话——我无法按字段过滤，也无法按请求 ID 关联。级别是对的，但消息本身无法以编程方式解析。
