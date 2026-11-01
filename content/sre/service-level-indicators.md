---
id: service-level-indicators
title: Service Level Indicators
zone: sre
edges:
  to:
    - id: service-level-objectives
      question: >-
        I've got my SLIs defined. Now how do I set a target that's actually
        meaningful — not just a number I made up?
      detail: >-
        I know I should measure error rate and latency. But what's the right
        threshold — 99%? 99.9%? 99.99%? I could just pick a high number to
        look good, but that feels dishonest. I want to understand how to arrive
        at something defensible.
difficulty: 1
tags:
  - sli
  - sre
  - reliability
  - metrics
  - user-experience
category: concept
milestones:
  - Define what makes a metric a good SLI vs. a bad one
  - List three SLIs for a typical web service (latency, error rate, availability)
  - Explain why internal metrics like CPU utilization are bad SLIs
  - Write SLIs for a real service you own
title_zh: "服务等级指标"

---


An SLI is the actual measurement — the number that tells you whether users are having a good experience right now. Not "is the server running?" but "are requests succeeding?" The hardest part of choosing SLIs isn't the measurement itself — it's resisting the temptation to measure what's easy to collect rather than what actually matters to users.

<!-- DEEP_DIVE -->

## What makes a good SLI

A good SLI has three properties:

1. **It reflects user experience directly.** If the SLI is good, users are having a good experience. If it degrades, users notice. CPU utilization fails this test — it can spike while users experience nothing, and can be low while users are getting errors.

2. **It's measurable at the right point.** You want to measure as close to the user as possible. Server-side latency is better than process CPU. Client-side latency measured from actual requests is better still. The further from the user you measure, the more disconnected the metric is from their actual experience.

3. **It's aggregable into a ratio.** SLIs are usually expressed as "X% of events were good." This makes them comparable across time periods and services.

## The four golden signals

Google SRE introduced the concept of the four golden signals: latency, traffic, errors, and saturation. These aren't SLIs by themselves — they're a framework for thinking about what to measure.

**Latency** — how long requests take. Critically, you care about the distribution, not just the average. A system where 50% of requests take 10ms and 50% take 10 seconds has a wonderful average and a terrible user experience. Use percentiles: P50, P95, P99.

**Traffic** — how much demand the system is handling. Requests per second, queries per second, active connections. This contextualizes everything else — a high error rate matters differently at 100 RPS vs 100,000 RPS.

**Errors** — the rate of failed requests. Both explicit failures (HTTP 500) and implicit ones (HTTP 200 with wrong data, timeouts, partial responses) count.

**Saturation** — how full the system is. Memory utilization, connection pool exhaustion, queue depth. Saturation is often a leading indicator: it degrades before errors start.

## What to avoid as SLIs

**CPU and memory utilization** — these are implementation details, not user experience signals. High CPU might mean high load and happy users. Low CPU might mean the service is completely broken and handling no traffic at all.

**Synthetic health check endpoints** — a `/health` endpoint returning 200 tells you the service can process requests to that specific endpoint. It tells you nothing about whether real user traffic is succeeding.

**Internal queue depths** — unless the queue directly backs user requests, this is an internal signal that doesn't reflect user experience.

## Writing your SLIs

For a typical web service, start with these three:

- **Availability SLI**: `count(successful_requests) / count(total_requests)` — a request is successful if the status code is 2xx or 3xx
- **Latency SLI**: `count(requests_under_threshold_ms) / count(total_requests)` — pick a threshold that reflects actual user expectations (200ms for interactive, 1s for async)
- **Error rate SLI**: `1 - count(5xx_requests) / count(total_requests)` — explicit server errors

Once you have these, you have the raw material for setting objectives.

<!-- RESOURCES -->

- [Google SRE Book - Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) -- type: book, time: 30m
- [The Four Golden Signals - Google SRE Book](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: book, time: 15m
- [Implementing SLOs - Google SRE Workbook](https://sre.google/workbook/implementing-slos/) -- type: book, time: 45m

<!-- ZH_SUMMARY -->
SLI 是实际的度量值——这个数字告诉你用户当前是否拥有良好的体验。它衡量的不是“服务器是否在运行？”，而是“请求是否成功？”。选择 SLI 最难的部分不在于度量本身——而在于抵制住诱惑，不去度量那些容易采集的指标，而是去度量真正对用户重要的指标。

<!-- ZH_DEEP_DIVE -->
## 什么造就了优秀的 SLI

一个优秀的 SLI 具备三个特性：

1. **它直接反映用户体验。** 如果 SLI 表现良好，用户就在获得良好体验。如果 SLI 劣化，用户就能感知到。CPU 利用率无法通过这一检验——它可能在用户毫无感知时飙升，也可能在用户不断遇到错误时保持低位。

2. **它能在正确的观测点被测量。** 你希望尽可能贴近用户进行测量。服务端延迟优于进程 CPU。从真实请求测得的客户端延迟则更佳。测量点离用户越远，指标与其实际体验的脱节就越大。

3. **它可以聚合成一个比率。** SLI 通常表述为“X% 的事件是好的”。这使得它们能够跨时间段和服务进行比较。

## 四大黄金信号

Google SRE 提出了四大黄金信号的概念：延迟、流量、错误和饱和度。它们本身并不是 SLI——而是一个用于思考“该测量什么”的框架。

**延迟**——请求耗时多久。关键在于，你关心的是分布，而不仅仅是平均值。一个 50% 的请求耗时 10ms、50% 的请求耗时 10 秒的系统，平均值很漂亮，用户体验却很糟糕。使用百分位数：P50、P95、P99。

**流量**——系统正在处理多少需求。每秒请求数、每秒查询数、活跃连接数。这为其他一切提供了背景——高错误率在 100 RPS 与 100,000 RPS 下的意义截然不同。

**错误**——失败请求的比率。显式失败（HTTP 500）和隐式失败（HTTP 200 但数据错误、超时、部分响应）都计入其中。

**饱和度**——系统的满载程度。内存利用率、连接池耗尽、队列深度。饱和度通常是先行指标：它在错误开始出现之前就已劣化。

## 应避免用作 SLI 的指标

**CPU 和内存利用率**——这些是实现细节，而非用户体验信号。高 CPU 可能意味着高负载和满意的用户。低 CPU 可能意味着服务已完全崩溃、根本没有处理任何流量。

**合成的健康检查端点**——一个返回 200 的 `/health` 端点只能告诉你服务能够处理发往该特定端点的请求。它完全无法告诉你真实用户流量是否成功。

**内部队列深度**——除非队列直接支撑用户请求，否则这是一个不反映用户体验的内部信号。

## 编写你的 SLI

对于典型的 Web 服务，从以下三个开始：

- **可用性 SLI**：`count(successful_requests) / count(total_requests)`——如果状态码为 2xx 或 3xx，则请求成功
- **延迟 SLI**：`count(requests_under_threshold_ms) / count(total_requests)`——选择一个反映实际用户预期的阈值（交互式 200ms，异步 1s）
- **错误率 SLI**：`1 - count(5xx_requests) / count(total_requests)`——显式服务端错误

一旦拥有这些，你就有了设定目标的原始素材。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 服务等级目标](https://sre.google/sre-book/service-level-objectives/) -- 类型: 书籍, 时间: 30分钟
- [四大黄金信号 - Google SRE 手册](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型: 书籍, 时间: 15分钟
- [实施 SLO - Google SRE 工作手册](https://sre.google/workbook/implementing-slos/) -- 类型: 书籍, 时间: 45分钟

<!-- ZH_UI -->
1. 定义什么样的指标是好的 SLI，什么是差的 SLI
2. 列出一个典型 Web 服务的三个 SLI（延迟、错误率、可用性）
3. 解释为什么 CPU 利用率等内部指标是差的 SLI
4. 为你实际负责的服务编写 SLI
5. 我已经定义好了 SLI。现在如何设定一个真正有意义的目标——而不只是我随便编的数字？
6. 我知道应该衡量错误率和延迟。但正确的阈值是什么——99%？99.9%？99.99%？我可以直接选一个高数字让自己好看，但那感觉不诚实。我想理解如何得出一个站得住脚的结论。
