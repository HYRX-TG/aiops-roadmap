---
id: your-first-logs
title: Your First Logs
zone: observability
edges:
  to:
    - id: log-levels
      question: >-
        My app is printing messages everywhere. I can't tell what's important
        and what's noise. How do I control that?
      detail: >-
        I've got logs but they're all the same — every debug message, every
        request, every heartbeat, all mixed together. When something breaks I
        have to scroll through thousands of irrelevant lines to find anything
        useful.
    - id: structured-logging
      question: >-
        My logs are working but searching through plain text is painful. Is there
        a better way to format them?
      detail: >-
        Right now I'm grep-ing for things like "error" and hoping I find what I
        need. But if I want to find all errors for a specific user, or all slow
        requests over 500ms, I'm stuck manually scanning text. There has to be a
        better way.
difficulty: 1
tags:
  - logging
  - observability
  - getting-started
category: practice
milestones:
  - Add meaningful log output to a running service
  - Understand why logging to stdout is preferred over writing to files
  - Identify what information belongs in a log line
  - Recognise why unstructured text logs don't scale
title_zh: "你的第一批日志"

---


Logs are the first thing you reach for when something goes wrong. They're a timestamped record of what your application was doing — requests it received, decisions it made, errors it hit. Before you have metrics dashboards or distributed traces, you have logs, and for a lot of early-stage services, good logs are enough to get by.

The good news is that getting started is simple: just write to stdout. Not to a file, not to a database — stdout. Your runtime (Docker, systemd, Kubernetes, whatever runs your process) will capture stdout automatically, and from there it can be forwarded anywhere. Starting with stdout keeps logging infrastructure out of your application code and puts it where it belongs: in your deployment environment.

The trap most people fall into is either logging too much or logging too little. Too little and you're flying blind — you have no record of what happened. Too much and every meaningful event is buried in noise. The goal is to log meaningful events: things that you'd actually want to know about when something goes wrong, with enough context to understand them without needing to re-run the request.

<!-- DEEP_DIVE -->

## What belongs in a log line

A log line should answer four questions at minimum: when did this happen, how severe is it, what happened, and what was the context?

**When** — a timestamp. Always include one. Without a timestamp, logs are nearly useless for incident investigation. ISO 8601 format is standard (`2024-01-15T14:32:01Z`), and always use UTC so you're not dealing with timezone arithmetic during an outage.

**How severe** — a log level. Is this normal information, a warning, or an error? Log levels are covered in detail in the next node, but even just distinguishing INFO from ERROR immediately makes logs more useful.

**What happened** — the message. This should be human-readable and specific. "Error" tells you nothing. "Failed to process payment for order 4821: card declined" tells you a lot.

**Context** — the fields that let you find related events. At minimum: which service emitted this, which request ID caused it, and what user or entity was involved. These are what let you search for "all logs related to this one request" rather than scrolling.

## Bad log lines vs. useful log lines

Here's the difference in practice. Imagine a payment service:

**Bad:**
```
Error processing payment
Request failed
Retrying...
Success
```

These lines are nearly useless in an incident. You can't tell when they happened (no timestamp), what the error was (no detail), which user's payment failed (no context), or which request you should be investigating (no request ID).

**Better:**
```
2024-01-15T14:32:01Z INFO  payment-service: received payment request order_id=4821 user_id=9912 amount=49.99
2024-01-15T14:32:02Z ERROR payment-service: card charge failed order_id=4821 user_id=9912 error="card_declined" attempt=1
2024-01-15T14:32:03Z INFO  payment-service: retry attempt 2 order_id=4821 user_id=9912
2024-01-15T14:32:04Z INFO  payment-service: payment completed order_id=4821 user_id=9912 duration_ms=3021
```

Now you can see exactly what happened, in what order, for which order and user, and how long it took. If a user calls in saying their payment failed, you can search for their user ID and find the exact event instantly.

## Why stdout, not files

In a traditional single-server world, logging to a file made sense. You'd write to `/var/log/myapp.log`, set up logrotate to prevent the disk from filling up, and SSH in to read it when needed.

In containerised environments, this approach breaks down:

- Containers are ephemeral. When a container dies, its filesystem goes with it, including any log files inside it.
- You might have 20 container replicas running the same service. Logging to files means 20 separate places to look.
- The orchestrator (Kubernetes, ECS, whatever) has built-in mechanisms to capture stdout and forward it — but not for files inside containers.

When you log to stdout, the container runtime captures it automatically. Docker does it, Kubernetes does it, systemd does it. From there, a log shipping agent running on the host can pick it up and forward it to your central log store. Your application doesn't need to know or care about any of that.

The principle: your application's job is to emit log events. Where those events go is someone else's problem — the infrastructure layer's problem.

## The two failure modes

**Too little logging.** You deploy a service with no logging at all. The first time something goes wrong, you have nothing. You restart the process and the problem goes away temporarily, but you never find out what caused it. Two weeks later it happens again.

The fix: at minimum, log the start of every significant operation and its outcome — especially failures. Log every unhandled exception. Log every external call your service makes (database, API) and whether it succeeded. You don't need to log everything, but you need to log the decisions your service makes.

**Too much logging.** You log every function entry and exit, every variable assignment, every loop iteration. In production, this produces so much output that real errors are invisible. Even if you store all of it, the cost of storing and querying millions of irrelevant lines is significant.

The fix: be deliberate about what you log. Debug-level output can be verbose, but only emit it when you need it — not in production by default. Reserve most of your logging for meaningful events: requests, responses, errors, state transitions. The signal-to-noise ratio matters as much as the signal itself.

<!-- RESOURCES -->

- [The Twelve-Factor App: Logs](https://12factor.net/logs) -- type: article, time: 5m
- [Application Logging Best Practices (Datadog)](https://www.datadoghq.com/blog/python-logging-best-practices/) -- type: article, time: 10m
- [Logging in Python: A Guide](https://realpython.com/python-logging/) -- type: tutorial, time: 20m

<!-- ZH_SUMMARY -->
出问题时，你首先会去查看日志。日志是应用程序活动的带时间戳记录——收到的请求、做出的决策、遇到的错误。在拥有指标仪表盘或分布式追踪之前，你只有日志；对于许多早期阶段的服务来说，良好的日志足以应付。

好消息是，上手很简单：只需写入 stdout。不是写入文件，也不是写入数据库——而是 stdout。你的运行时（Docker、systemd、Kubernetes，或任何运行你进程的东西）会自动捕获 stdout，并可以从那里转发到任何地方。从 stdout 开始，可以把日志基础设施从应用代码中剥离出来，放到它该在的地方：你的部署环境里。

大多数人容易陷入的陷阱，要么是记录太多，要么是记录太少。记录太少，你就是在盲飞——对发生的事情毫无记录。记录太多，每个有意义的事件都被淹没在噪音中。目标是记录有意义的事件：那些出问题时你真正想知道的事情，并且带有足够的上下文，让你无需重新运行请求就能理解它们。

<!-- ZH_DEEP_DIVE -->
## 日志行应包含的内容

一条日志行至少应回答四个问题：这件事何时发生、严重程度如何、发生了什么、上下文是什么？

**何时** —— 时间戳。始终要包含一个。没有时间戳，日志在事故调查中几乎毫无用处。ISO 8601 格式是标准（`2024-01-15T14:32:01Z`），并且始终使用 UTC，这样在故障期间就不必处理时区换算。

**严重程度** —— 日志级别。这是普通信息、警告还是错误？日志级别将在下一个节点中详细介绍，但即使只是区分 INFO 和 ERROR，也能立刻让日志更有用。

**发生了什么** —— 消息。它应当是人类可读且具体的。“Error”什么也说明不了。“Failed to process payment for order 4821: card declined”则能告诉你很多。

**上下文** —— 让你能找到相关事件的字段。至少包括：哪个服务发出了这条日志、是哪个请求 ID 导致的、涉及哪个用户或实体。正是这些字段让你能搜索“与这一个请求相关的所有日志”，而不是靠滚动翻找。

## 糟糕的日志行 vs. 有用的日志行

下面是实践中的区别。想象一个支付服务：

**糟糕：**
```
Error processing payment
Request failed
Retrying...
Success
```

这些行在事故中几乎毫无用处。你无法判断它们何时发生（没有时间戳）、错误是什么（没有细节）、哪个用户的支付失败了（没有上下文），或者你应该调查哪个请求（没有请求 ID）。

**更好：**
```
2024-01-15T14:32:01Z INFO  payment-service: received payment request order_id=4821 user_id=9912 amount=49.99
2024-01-15T14:32:02Z ERROR payment-service: card charge failed order_id=4821 user_id=9912 error="card_declined" attempt=1
2024-01-15T14:32:03Z INFO  payment-service: retry attempt 2 order_id=4821 user_id=9912
2024-01-15T14:32:04Z INFO  payment-service: payment completed order_id=4821 user_id=9912 duration_ms=3021
```

现在你能确切看到发生了什么、以什么顺序发生、涉及哪个订单和用户，以及耗时多久。如果用户打电话说他们的支付失败了，你可以搜索他们的用户 ID，立刻找到确切的事件。

## 为什么用 stdout，而不是文件

在传统的单服务器世界里，记录到文件是合理的。你会写入 `/var/log/myapp.log`，设置 logrotate 防止磁盘被写满，需要时 SSH 登录进去读取。

在容器化环境中，这种做法就行不通了：

- 容器是短暂的。容器死亡时，它的文件系统也随之消失，包括其中的任何日志文件。
- 你可能运行着同一个服务的 20 个容器副本。记录到文件意味着有 20 个不同的地方需要查看。
- 编排器（Kubernetes、ECS 等）内置了捕获并转发 stdout 的机制——但不支持容器内的文件。

当你记录到 stdout 时，容器运行时会自动捕获它。Docker 会这样做，Kubernetes 会这样做，systemd 也会这样做。从那里开始，运行在宿主机上的日志转发代理可以接收它并转发到你的中央日志存储。你的应用不需要知道或关心这些。

原则是：应用的职责是发出日志事件。这些事件去哪里是别人的问题——基础设施层的问题。

## 两种失败模式

**日志太少。** 你部署了一个完全没有日志的服务。第一次出问题时，你什么也没有。你重启进程，问题暂时消失了，但你始终不知道原因。两周后它又发生了。

解决办法：至少记录每个重要操作的开始及其结果——尤其是失败。记录每个未处理的异常。记录你的服务发起的每次外部调用（数据库、API）以及是否成功。你不需要记录所有内容，但你需要记录你的服务所做的决策。

**日志太多。** 你记录每个函数的进入和退出、每次变量赋值、每次循环迭代。在生产环境中，这会产生如此多的输出，以至于真正的错误被淹没。即使你存储了全部内容，存储和查询数百万条无关日志行的成本也是可观的。

解决办法：有意识地决定记录什么。调试级别的输出可以很详细，但只在你需要时才发出——默认不要在生产环境中发出。把大部分日志留给有意义的事件：请求、响应、错误、状态转换。信噪比和信号本身同样重要。

<!-- ZH_RESOURCES -->
- [十二要素应用：日志](https://12factor.net/logs) -- 类型：文章，时长：5分钟
- [应用日志最佳实践 (Datadog)](https://www.datadoghq.com/blog/python-logging-best-practices/) -- 类型：文章，时长：10分钟
- [Python 日志记录：指南](https://realpython.com/python-logging/) -- 类型：教程，时长：20分钟

<!-- ZH_UI -->
1. 为运行中的服务添加有意义的日志输出
2. 理解为什么日志输出到 stdout 优于写入文件
3. 确定一行日志中应包含哪些信息
4. 认识为什么非结构化文本日志无法扩展
5. 我的应用到处在打印消息，分不清哪些重要、哪些是噪音。该如何控制？
6. 我有日志，但全都一样——每条调试消息、每个请求、每次心跳，全混在一起。出问题时得翻过成千上万条无关行才能找到有用的东西。
7. 日志能用，但在纯文本里搜索很痛苦。有没有更好的格式化方式？
8. 现在我只能 grep “error” 之类的内容，碰运气找需要的东西。但如果想找某个用户的全部错误，或所有超过 500ms 的慢请求，就只能手动扫文本。一定有更好的办法。
