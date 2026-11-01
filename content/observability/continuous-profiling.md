---
id: continuous-profiling
title: Continuous Profiling
zone: observability
edges:
  to:
    - id: observability-cardinality
      question: >-
        I found the performance problem and fixed it. But my observability bill
        is still growing every month. What's driving that?
      detail: >-
        Great — I tracked down the slow function. But now I'm noticing that the
        infrastructure cost for metrics and traces is growing faster than my
        traffic is. Something about how I've set things up is generating way
        more data than I actually need, and I don't know where to look.
difficulty: 3
tags:
  - profiling
  - continuous-profiling
  - pprof
  - pyroscope
  - flame-graphs
  - observability
  - performance
category: practice
milestones:
  - Understand what a CPU flame graph shows and how to read it
  - Set up continuous profiling for a service using Pyroscope or pprof
  - Identify a hot function from a flame graph and fix it
  - Know when to reach for profiling vs. tracing vs. metrics to diagnose slowness
title_zh: "持续性能分析"

---


Metrics tell you that your service is using 80% CPU. Traces tell you that the `processPayment` function is slow. Neither tells you which specific line of code inside `processPayment` is burning all that CPU. That's the gap profiling fills — it samples your running program thousands of times per second, recording exactly what each thread was executing at each sample, and aggregates that into a picture of where your code spends its time.

Traditional profiling means running a profiler against a local copy of your code for a specific benchmark. That's useful for known performance problems, but it misses the cases that matter most: the ones that only appear under real production load, with real data, at 2am when traffic is at its peak. Continuous profiling keeps a low-overhead profiler running all the time in production, stores the profiles over time, and lets you compare them across deployments. You can ask: "Did this deploy make the CPU usage worse?" and get an actual code-level answer.

The visualization that makes all of this legible is the flame graph. Once you can read a flame graph, a lot of performance investigations that used to take days take an hour.

<!-- DEEP_DIVE -->

## How profiling works

A CPU profiler works by interrupting your program at regular intervals (typically thousands of times per second) and recording the call stack at that moment. After enough samples, a clear picture emerges: if `parseJSON` appears in 30% of your samples, it's consuming roughly 30% of your CPU time.

This sampling approach is lightweight enough to run in production — typical overhead is 1–3% CPU, which is acceptable for the value it provides. It's different from instrumented profiling, which adds code around every function call and can have 20–50% overhead.

## Reading a flame graph

A flame graph is the standard way to visualize profile data. Before you can use it, you need to understand what it's showing:

- **The x-axis is not time** — it's the proportion of CPU samples. Functions that appear in more samples are wider. Width = CPU time.
- **The y-axis is the call stack** — the bottom is the entry point (main function, thread start, event loop), and stacks grow upward. A bar sitting on top of another bar means "this function was called by the one below it."
- **The top of each stack is where time is actually being spent** — a wide bar at the top that has nothing above it is a leaf function consuming CPU.

Here's how to read one:

```
┌──────────────────────────────────────────────────────────────────────┐
│ http.Server.Serve (80% of samples)                                   │
├──────────────────────────────────────────┬───────────────────────────┤
│ handleRequest (70%)                      │ TLS handshake (10%)        │
├────────────────────┬─────────────────────┤                           │
│ parseRequest (5%)  │ processOrder (65%)  │                           │
│                    ├───────┬─────────────┤                           │
│                    │ DB    │ validateCart│                           │
│                    │ query │ (45%)       │                           │
│                    │ (20%) ├─────────────┤                           │
│                    │       │ priceCalc   │                           │
│                    │       │ (45%)  ◄────┼── THIS is your problem    │
└────────────────────┴───────┴─────────────┴───────────────────────────┘
```

In this example, `priceCalc` is at the top of the widest stack and takes 45% of CPU time. That's your hot function. The DB query at 20% is the next candidate. The TLS handshake at 10% is probably not worth touching unless you can terminate TLS at the load balancer.

The key technique: find the widest bar that isn't a language runtime or framework call. That's where you should focus.

## Tools by language

**Go — pprof (built-in)**

Go has profiling built into the standard library. Add the pprof HTTP handler and you can pull profiles on demand:

```go
import _ "net/http/pprof"

// In your main function:
go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()
```

Collect a 30-second CPU profile:

```bash
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
```

View the flame graph in your browser:

```bash
go tool pprof -http=:8080 profile.pb.gz
```

**Python — py-spy**

py-spy attaches to a running Python process without modifying your code:

```bash
pip install py-spy

# Profile a running process for 30 seconds
py-spy record -o profile.svg --pid 12345 --duration 30

# Or a subprocess
py-spy record -o profile.svg -- python myapp.py
```

**JVM — async-profiler**

```bash
# Download async-profiler
curl -L https://github.com/async-profiler/async-profiler/releases/latest/download/async-profiler-linux-x64.tar.gz | tar xz

# Profile a running JVM process
./asprof -d 30 -f profile.html <pid>
```

## Continuous profiling with Pyroscope

For continuous profiling (always-on, stored historically), Pyroscope is the main open-source option. You run the Pyroscope server, and integrate the Pyroscope SDK into your application:

```python
import pyroscope

pyroscope.configure(
    application_name = "my-service",
    server_address   = "http://pyroscope:4040",
    tags             = {
        "region": "us-east-1",
        "version": os.environ.get("APP_VERSION", "unknown"),
    }
)
```

The SDK profiles your application every 10 seconds and ships the data to Pyroscope. In the Pyroscope UI you can:
- View a flame graph for any time range
- Compare flame graphs across two time windows (e.g., before vs. after a deploy)
- Filter profiles by tag (e.g., compare profile between v1.2 and v1.3)

The "diff flame graph" feature is particularly useful after deploys. New red regions are code paths that got slower. Green regions got faster.

## When to reach for profiling

Profiling is the last resort, not the first. Use it when:

- Metrics show CPU or memory usage is high, but traces don't explain why
- A trace shows a span is slow, but there are no obvious external calls inside it (the work is happening inside your code)
- You've deployed a change and CPU usage went up, but nothing obvious changed
- You suspect a library you're using is doing something inefficient

You don't need profiling when:
- A trace shows a database query is slow — optimize the query
- An external API is slow — that's network and the external service, not your code
- You can see from metrics that a specific endpoint is slow — traces give you enough detail

The rough debugging hierarchy: **metrics → traces → logs → profiles**. Most problems are solved before you get to profiling.

<!-- RESOURCES -->

- [Pyroscope: Getting Started](https://grafana.com/docs/pyroscope/latest/get-started/) -- type: tutorial, time: 20m
- [The Flame Graph — Brendan Gregg](https://www.brendangregg.com/flamegraphs.html) -- type: article, time: 15m
- [Go pprof documentation](https://pkg.go.dev/net/http/pprof) -- type: article, time: 10m
- [py-spy: Sampling profiler for Python](https://github.com/benfred/py-spy) -- type: article, time: 10m
- [Continuous Profiling in Production — Grafana blog](https://grafana.com/blog/2022/06/07/ask-us-anything-how-to-get-started-with-continuous-profiling/) -- type: article, time: 12m
- [async-profiler for JVM](https://github.com/async-profiler/async-profiler) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
指标告诉你服务正在使用 80% 的 CPU。链路追踪告诉你 `processPayment` 函数很慢。但两者都无法告诉你 `processPayment` 内部究竟是哪一行代码在消耗所有这些 CPU。这正是性能剖析（profiling）填补的空白——它以每秒数千次的频率对运行中的程序进行采样，精确记录每次采样时每个线程正在执行的代码，并将这些数据聚合起来，描绘出你的代码在何处花费时间。

传统性能剖析意味着针对特定基准测试，对本地代码副本运行剖析器。这对于已知的性能问题很有用，但它恰恰遗漏了最重要的场景：那些只在真实生产负载下、使用真实数据、在凌晨两点流量高峰期才会出现的问题。持续剖析（continuous profiling）在生产环境中始终运行一个低开销的剖析器，随时间存储剖析数据，并允许你跨部署进行比较。你可以问：“这次部署是否让 CPU 使用率变差了？”并得到一个代码级别的实际答案。

让这一切变得清晰可读的可视化工具就是火焰图（flame graph）。一旦你能读懂火焰图，许多过去需要数天的性能调查只需一小时就能完成。

<!-- ZH_DEEP_DIVE -->
## 性能分析的工作原理

CPU 性能分析器的工作原理是定期中断你的程序（通常每秒数千次），并记录中断那一刻的调用栈。在积累足够多的样本之后，一幅清晰的图景就会浮现出来：如果 `parseJSON` 出现在 30% 的样本中，那么它大约消耗了你 30% 的 CPU 时间。

这种采样方式足够轻量，可以在生产环境中运行——典型开销为 1–3% 的 CPU，相对于它带来的价值来说是可以接受的。它不同于插桩式性能分析（instrumented profiling），后者会在每次函数调用周围添加代码，开销可能高达 20–50%。

## 阅读火焰图

火焰图是可视化性能分析数据的标准方式。在使用它之前，你需要理解它展示的是什么：

- **x 轴不是时间**——它代表 CPU 样本的比例。出现在更多样本中的函数更宽。宽度 = CPU 时间。
- **y 轴是调用栈**——底部是入口点（main 函数、线程启动、事件循环），调用栈向上生长。一个条形位于另一个条形之上，意味着“这个函数是由它下面的函数调用的”。
- **每个调用栈的顶部才是时间实际花费的地方**——顶部一个很宽的条形，其上方没有任何东西，就是一个正在消耗 CPU 的叶子函数。

下面是如何阅读一张火焰图：

```
┌──────────────────────────────────────────────────────────────────────┐
│ http.Server.Serve (80% of samples)                                   │
├──────────────────────────────────────────┬───────────────────────────┤
│ handleRequest (70%)                      │ TLS handshake (10%)        │
├────────────────────┬─────────────────────┤                           │
│ parseRequest (5%)  │ processOrder (65%)  │                           │
│                    ├───────┬─────────────┤                           │
│                    │ DB    │ validateCart│                           │
│                    │ query │ (45%)       │                           │
│                    │ (20%) ├─────────────┤                           │
│                    │       │ priceCalc   │                           │
│                    │       │ (45%)  ◄────┼── THIS is your problem    │
└────────────────────┴───────┴─────────────┴───────────────────────────┘
```

在这个例子中，`priceCalc` 位于最宽的调用栈顶部，占用了 45% 的 CPU 时间。这就是你的热点函数。占 20% 的 DB 查询是下一个候选对象。占 10% 的 TLS 握手可能不值得处理，除非你能在负载均衡器上终止 TLS。

关键技巧：找到最宽的、且不是语言运行时或框架调用的条形。那才是你应该关注的地方。

## 各语言的工具

**Go —— pprof（内置）**

Go 在标准库中内置了性能分析功能。添加 pprof HTTP handler，你就可以按需拉取性能分析数据：

```go
import _ "net/http/pprof"

// In your main function:
go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()
```

采集 30 秒的 CPU 性能分析数据：

```bash
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
```

在浏览器中查看火焰图：

```bash
go tool pprof -http=:8080 profile.pb.gz
```

**Python —— py-spy**

py-spy 可以附加到正在运行的 Python 进程上，而无需修改你的代码：

```bash
pip install py-spy

# Profile a running process for 30 seconds
py-spy record -o profile.svg --pid 12345 --duration 30

# Or a subprocess
py-spy record -o profile.svg -- python myapp.py
```

**JVM —— async-profiler**

```bash
# Download async-profiler
curl -L https://github.com/async-profiler/async-profiler/releases/latest/download/async-profiler-linux-x64.tar.gz | tar xz

# Profile a running JVM process
./asprof -d 30 -f profile.html <pid>
```

## 使用 Pyroscope 进行持续性能分析

对于持续性能分析（始终开启、按历史存储），Pyroscope 是主要的开源选择。你运行 Pyroscope 服务器，并将 Pyroscope SDK 集成到你的应用中：

```python
import pyroscope

pyroscope.configure(
    application_name = "my-service",
    server_address   = "http://pyroscope:4040",
    tags             = {
        "region": "us-east-1",
        "version": os.environ.get("APP_VERSION", "unknown"),
    }
)
```

SDK 每 10 秒对你的应用进行一次性能分析，并将数据发送到 Pyroscope。在 Pyroscope UI 中，你可以：
- 查看任意时间范围的火焰图
- 对比两个时间窗口的火焰图（例如，部署前与部署后）
- 按标签过滤性能分析数据（例如，对比 v1.2 和 v1.3 之间的性能分析数据）

“差异火焰图”（diff flame graph）功能在部署之后特别有用。新的红色区域是变慢的代码路径。绿色区域则变快了。

## 何时使用性能分析

性能分析是最后的手段，而不是首选。在以下情况下使用它：

- 指标显示 CPU 或内存使用率很高，但 trace 无法解释原因
- trace 显示某个 span 很慢，但其内部没有明显的外部调用（工作发生在你的代码内部）
- 你部署了一项变更，CPU 使用率上升了，但没有什么明显的变化
- 你怀疑正在使用的某个库在做低效的事情

在以下情况下你不需要性能分析：
- trace 显示某个数据库查询很慢——优化该查询
- 某个外部 API 很慢——那是网络和外部服务的问题，不是你的代码
- 你可以从指标看出某个特定端点很慢——trace 已经提供了足够的细节

大致的调试层级：**指标 → trace → 日志 → 性能分析**。大多数问题在你走到性能分析这一步之前就已经解决了。

<!-- ZH_RESOURCES -->
- [Pyroscope：入门指南](https://grafana.com/docs/pyroscope/latest/get-started/) -- 类型：教程，时长：20m
- [火焰图 — Brendan Gregg](https://www.brendangregg.com/flamegraphs.html) -- 类型：文章，时长：15m
- [Go pprof 文档](https://pkg.go.dev/net/http/pprof) -- 类型：文章，时长：10m
- [py-spy：Python 采样分析器](https://github.com/benfred/py-spy) -- 类型：文章，时长：10m
- [生产环境中的持续性能分析 — Grafana 博客](https://grafana.com/blog/2022/06/07/ask-us-anything-how-to-get-started-with-continuous-profiling/) -- 类型：文章，时长：12m
- [用于 JVM 的 async-profiler](https://github.com/async-profiler/async-profiler) -- 类型：文章，时长：10m

<!-- ZH_UI -->
1. 理解 CPU 火焰图展示的内容以及如何阅读它
2. 使用 Pyroscope 或 pprof 为服务设置持续性能分析
3. 从火焰图中识别热点函数并修复它
4. 知道何时使用性能分析、追踪或指标来诊断变慢问题
5. 我找到了性能问题并修复了它。但我的可观测性账单仍在每月增长。是什么导致的？
6. 很好——我找到了慢函数。但现在我注意到指标和追踪的基础设施成本增长速度超过了我的流量增长速度。我的设置方式生成了远超实际需要的数据，而我不知道该从哪里排查。
