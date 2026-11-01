---
id: trace-sampling
title: Trace Sampling
zone: observability
edges:
  to:
    - id: correlating-signals
      question: >-
        Sampling is configured. Now how do I actually use the traces I have
        alongside my logs and metrics?
      detail: >-
        I'm keeping a sensible subset of traces now. But when I'm debugging I
        still have to jump between my trace tool, my log tool, and Grafana
        separately. I'm copy-pasting timestamps and hoping the right data lines
        up. There has to be a way to actually connect them.
difficulty: 2
tags:
  - tracing
  - sampling
  - head-sampling
  - tail-sampling
  - observability
  - cost
category: concept
milestones:
  - Understand why tracing 100% of requests is impractical at scale
  - Know the difference between head-based and tail-based sampling
  - Configure a sampling rate in your tracing setup
  - Understand why tail sampling is better for catching errors but harder to implement
title_zh: "追踪采样"

---


A service handling 1,000 requests per second generates 1,000 traces per second. If each trace is 10KB of data, that's 10MB per second, 864GB per day — for a single service. Add more services, more spans per trace, and you're looking at terabytes of trace data daily. Storing all of it is impractical and, honestly, unnecessary: the 999th request that looked exactly like the first 998 doesn't teach you anything new.

Sampling means keeping only a representative subset of traces. Done right, you keep enough traces to diagnose problems without drowning in data. Done poorly, you might discard the exact trace that would have explained your 3am incident. The challenge is that you don't always know which traces are interesting until after they're complete — and by then, the decision about whether to keep them might already have been made.

There are two fundamentally different approaches to this problem, and understanding the tradeoff between them is important before you configure anything.

<!-- DEEP_DIVE -->

## Head-based sampling

In head-based sampling, the decision to keep or discard a trace is made at the very beginning — when the root span starts. Your API gateway or first service flips a coin and decides "yes, trace this request" or "no, skip it." That decision is propagated to every downstream service as part of the trace context, so the whole system either traces the request or doesn't.

Head-based sampling is simple to implement and has essentially zero overhead for discarded requests — you're not collecting data you're going to throw away. The standard way to configure it in OTel is a `TraceIdRatioBased` sampler:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.10)
```

The fatal flaw: the decision happens before anything has gone wrong. If you sample 10% of requests and 1% of those requests hit an error, you're keeping 10% of your errors — meaning you miss 90% of error traces. The one request that took 5 seconds and failed in a confusing way? There's a 90% chance you dropped it.

## Tail-based sampling

In tail-based sampling, you buffer all spans from a trace until the trace is complete, then decide whether to keep it based on what actually happened. This means you can apply intelligent rules: keep 100% of traces that contain an error, keep 100% of traces over 2 seconds, and sample 5% of everything else.

The result is far better signal. You never miss an error trace. You never miss a slow trace. You shed volume from the boring, fast, successful requests that don't need investigating.

The cost is complexity. You need a component that can buffer and hold all spans, correlate them by trace ID, wait for the trace to complete, and then make the sampling decision. The OTel Collector's `tail_sampling` processor does this:

```yaml
processors:
  tail_sampling:
    decision_wait: 10s       # wait up to 10s for all spans to arrive
    num_traces: 50000        # max traces to hold in memory at once
    policies:
      - name: errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: everything-else
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
```

This config keeps all errors, all traces over 1 second, and 5% of everything else. In practice this reduces volume dramatically while preserving almost all the traces that matter.

The catch: tail sampling requires all spans for a given trace to arrive at the same Collector instance, because the Collector needs to see the complete trace to make the decision. In a horizontally scaled Collector deployment, you need to route spans by trace ID to ensure they land in the same place. The `loadbalancingexporter` in OTel handles this.

## A practical starting point

If you're just getting started with sampling:

1. **Start with head-based sampling at 10%** — it's easy to configure and immediately reduces your storage costs by 10x. You'll miss some errors, but you'll understand your baseline.

2. **Add 100% error sampling as soon as you can** — even with head-based sampling, many SDKs let you override the sampling decision after the fact if the trace completed with an error.

3. **Move to tail-based sampling when you have the infrastructure for it** — this is the approach production systems with meaningful traffic use.

A common production setup:

| Scenario | Keep |
|----------|------|
| Request returned 5xx | 100% |
| Request duration > 2s | 100% |
| Request returned 4xx | 20% |
| Everything else | 5% |

## The trade-off you're always making

Sampling is a compression of reality. A 5% sample rate means 1-in-20 requests appears in your tracing tool. If you're debugging a bug that affects 0.1% of requests, you might need to trigger hundreds of requests before a trace from the affected path lands in your 5% sample.

The way to think about this: sampling is appropriate for understanding patterns (what does normal look like? where is the p99 hotspot?). For debugging specific bugs, especially rare ones, you sometimes need to temporarily increase your sample rate or add targeted 100% sampling for specific endpoints.

Tail-based sampling with intelligent policies mostly solves this for errors and slowness — the cases you care most about. But for debugging a subtle correctness bug (not an error, not slow, just wrong output for certain inputs), you may still need to trace 100% of requests temporarily.

<!-- RESOURCES -->

- [Sampling — OpenTelemetry docs](https://opentelemetry.io/docs/concepts/sampling/) -- type: article, time: 10m
- [OTel Collector tail_sampling processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor) -- type: article, time: 15m
- [Trace Sampling Strategies — Honeycomb](https://www.honeycomb.io/blog/trace-sampling-strategies/) -- type: article, time: 12m
- [Head vs Tail Sampling — Grafana docs](https://grafana.com/docs/tempo/latest/operations/tempo_cli/#tail-sampling) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
一个每秒处理 1,000 个请求的服务，每秒会产生 1,000 条 trace。如果每条 trace 的数据量为 10KB，那就是每秒 10MB、每天 864GB——而这还只是一个服务。再加上更多服务、每条 trace 中更多的 span，你每天面对的将是数 TB 的 trace 数据。把全部数据都存下来既不现实，说实话也没必要：第 999 个请求和第 1 到第 998 个请求看起来一模一样，它不会教给你任何新东西。

采样意味着只保留一个有代表性的 trace 子集。做得好，你能保留足够多的 trace 来诊断问题，而不至于被数据淹没。做得不好，你可能恰好丢弃了那条本可以解释你凌晨 3 点故障的 trace。挑战在于，你并不总能事先知道哪些 trace 值得关注，直到它们完整结束——而到那时，关于是否保留它们的决定可能早已做出。

解决这个问题有两种根本不同的方法，在配置任何东西之前，理解它们之间的权衡很重要。

<!-- ZH_DEEP_DIVE -->
## 头部采样（Head-based sampling）

在头部采样中，保留或丢弃 trace 的决策在最初就做出——即根 span 启动时。你的 API 网关或第一个服务抛硬币决定“是，追踪这个请求”或“否，跳过它”。该决策作为 trace 上下文的一部分传播到每个下游服务，因此整个系统要么追踪该请求，要么不追踪。

头部采样实现简单，且对丢弃的请求基本零开销——你不会收集将要丢弃的数据。在 OTel 中配置它的标准方式是使用 `TraceIdRatioBased` 采样器：

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.10)
```

致命缺陷：决策发生在任何问题出现之前。如果你采样 10% 的请求，而这些请求中有 1% 命中错误，那么你只保留了 10% 的错误——意味着你错过了 90% 的错误 trace。那个耗时 5 秒并以令人困惑的方式失败的请求？有 90% 的概率被你丢弃了。

## 尾部采样（Tail-based sampling）

在尾部采样中，你缓冲一个 trace 的所有 span，直到该 trace 完成，然后根据实际发生的情况决定是否保留它。这意味着你可以应用智能规则：保留 100% 包含错误的 trace，保留 100% 超过 2 秒的 trace，并对其余所有内容采样 5%。

结果是信号质量好得多。你永远不会错过错误 trace。你永远不会错过慢 trace。你从那些无聊、快速、成功、无需调查的请求中削减了数据量。

代价是复杂性。你需要一个组件来缓冲并持有所有 span，按 trace ID 关联它们，等待 trace 完成，然后做出采样决策。OTel Collector 的 `tail_sampling` 处理器正是做这件事的：

```yaml
processors:
  tail_sampling:
    decision_wait: 10s       # wait up to 10s for all spans to arrive
    num_traces: 50000        # max traces to hold in memory at once
    policies:
      - name: errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: everything-else
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
```

此配置保留所有错误、所有超过 1 秒的 trace，以及其余所有内容的 5%。在实践中，这大幅减少了数据量，同时保留了几乎所有重要的 trace。

问题在于：尾部采样要求给定 trace 的所有 span 到达同一个 Collector 实例，因为 Collector 需要看到完整的 trace 才能做出决策。在水平扩展的 Collector 部署中，你需要按 trace ID 路由 span，以确保它们落在同一个地方。OTel 中的 `loadbalancingexporter` 负责处理这一点。

## 一个实用的起点

如果你刚开始使用采样：

1. **从 10% 的头部采样开始**——它易于配置，并立即将存储成本降低 10 倍。你会错过一些错误，但你会了解你的基线。

2. **尽快添加 100% 错误采样**——即使使用头部采样，许多 SDK 也允许你在 trace 以错误完成后覆盖采样决策。

3. **当你具备相应基础设施时，转向尾部采样**——这是有实际流量的生产系统所采用的方法。

一个常见的生产配置：

| 场景 | 保留比例 |
|----------|------|
| 请求返回 5xx | 100% |
| 请求持续时间 > 2s | 100% |
| 请求返回 4xx | 20% |
| 其他所有情况 | 5% |

## 你始终在做的权衡

采样是对现实的压缩。5% 的采样率意味着每 20 个请求中有 1 个出现在你的追踪工具中。如果你正在调试一个影响 0.1% 请求的 bug，你可能需要触发数百个请求，才能让受影响路径的 trace 落入你的 5% 样本中。

这样思考：采样适合理解模式（正常情况是什么样？p99 热点在哪里？）。对于调试特定 bug，尤其是罕见的 bug，你有时需要临时提高采样率，或为特定端点添加针对性的 100% 采样。

带有智能策略的尾部采样主要解决了错误和慢速的情况——这些是你最关心的场景。但对于调试微妙的正确性 bug（不是错误，不是慢速，只是对某些输入输出错误），你可能仍然需要临时追踪 100% 的请求。

<!-- ZH_RESOURCES -->
- [采样 — OpenTelemetry 文档](https://opentelemetry.io/docs/concepts/sampling/) -- 类型: 文章, 时长: 10m
- [OTel Collector tail_sampling 处理器](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor) -- 类型: 文章, 时长: 15m
- [追踪采样策略 — Honeycomb](https://www.honeycomb.io/blog/trace-sampling-strategies/) -- 类型: 文章, 时长: 12m
- [头部采样 vs 尾部采样 — Grafana 文档](https://grafana.com/docs/tempo/latest/operations/tempo_cli/#tail-sampling) -- 类型: 文章, 时长: 10m

<!-- ZH_UI -->
1. 理解为什么在全量规模下对 100% 请求进行追踪不切实际
2. 了解头部采样与尾部采样的区别
3. 在追踪配置中设置采样率
4. 理解为什么尾部采样更擅长捕获错误但更难实现
5. 采样已配置好。那么我该如何实际结合日志和指标来使用已有的追踪数据？
6. 我现在保留了合理的追踪子集。但调试时我仍要在追踪工具、日志工具和 Grafana 之间来回切换。我在复制粘贴时间戳，指望数据能对上。总得有一种真正把它们关联起来的方法。
