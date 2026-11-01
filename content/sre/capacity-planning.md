---
id: capacity-planning
title: Capacity Planning
zone: sre
edges:
  to:
    - id: load-testing
      question: >-
        I have capacity estimates on paper. How do I actually verify them before
        real traffic hits?
      detail: >-
        I've done the maths and we should handle 3x current traffic. But the
        last time I said that, I was wrong. I want to actually simulate the load
        and find the bottlenecks myself before users find them for me.
    - id: platform-engineering
      question: >-
        My systems are reliable and well-provisioned. How do I make the
        infrastructure accessible and productive for the rest of my engineering
        organisation?
      detail: >-
        I can run reliable infrastructure. But now the question is: how do I
        make this accessible to the rest of the engineering org? Every team
        reinventing infra from scratch, every new hire spending weeks on
        Kubernetes setup — that's not sustainable. There must be a better way to
        share what I've built.
difficulty: 2
tags:
  - capacity-planning
  - load-testing
  - forecasting
  - scaling
  - resource-management
  - sre
category: practice
milestones:
  - >-
    Run a load test that simulates your expected traffic at 2x and 5x current
    volume
  - >-
    Identify which resource hits its limit first: CPU, memory, database
    connections, or network
  - Build a traffic forecast from historical data and planned growth
  - >-
    Set up proactive alerts that fire when you have weeks of runway left, not
    hours
title_zh: "容量规划"

---


Traffic keeps growing. New features increase per-request resource usage. Marketing plans a campaign that will double traffic overnight. At some point, the system you have won't be enough for the system you need. Capacity planning is the practice of understanding how your systems scale and making sure you don't find the limits in production. The goal isn't unlimited resources — it's knowing where the ceiling is, how much headroom you have, and how to get ahead of it.

<!-- DEEP_DIVE -->

## What capacity planning answers

Capacity planning addresses three questions:

1. **Where will we hit a wall?** Which resource — CPU, memory, database connections, network throughput, storage — hits its limit first as traffic grows?

2. **When will we hit it?** Based on current growth trends and planned demand, how many weeks or months until that resource is exhausted?

3. **What do we need to do about it?** Scale horizontally, optimize code, add caching, renegotiate a dependency SLO, increase infrastructure?

These questions can't be answered theoretically. They require measurements of how the system currently behaves under load.

## The four resource constraints

Most capacity problems live in one of these four places:

**CPU**: request processing is too compute-intensive for the available cores. Manifests as increased latency at high traffic, eventually timeouts. Solved by horizontal scaling (more instances) or profiling and optimizing hot code paths.

**Memory**: each request uses significant memory (object allocation, caching, session state) and the system runs out. Manifests as GC pauses, OOM kills, increasingly long memory cleanup cycles. Solved by reducing per-request memory footprint or adding RAM/instances.

**Database connections**: connection pools have a fixed size. At high concurrency, requests queue waiting for a connection. Manifests as latency spikes proportional to traffic. Solved by connection pool sizing, connection multiplexing (PgBouncer), or reducing database calls per request.

**Throughput / network**: the volume of data transferred hits the limits of the network interface, load balancer, or upstream provider. Manifests as packet loss, retransmits, and latency. Solved by caching, reducing response sizes, or upgrading network capacity.

## Traffic forecasting

Historical traffic data has patterns: daily cycles, weekly patterns, seasonal spikes, growth trends. Extract these:

**Daily/weekly baseline**: what's the typical traffic curve? When is peak? What's the ratio of peak to average?

**Growth trend**: fit a trend line to your historical traffic data. At the current growth rate, when does traffic reach 2x? 5x? This gives you a timeline.

**Known demand events**: product launches, marketing campaigns, seasonal events. These require separate analysis — a campaign that promises 10x traffic for 48 hours is a different problem from gradual growth.

Most capacity planning tools (CloudWatch, Datadog, Google Cloud Monitoring) can project forward from historical trends. The projection is an estimate, not a guarantee, but it gives you a defensible number to plan against.

## The headroom principle

Don't plan to run at 100% of capacity. Plan to run at a defined maximum utilization — typically 60-70% for most resources — and treat anything above that as the trigger for capacity action.

Running at 70% CPU on average means you have 30% headroom for traffic spikes and load variability. Running at 95% CPU means any spike causes latency degradation, and any traffic variability causes incidents.

The headroom percentage depends on the volatility of your traffic and the cost of going over. For databases (where connection pool exhaustion cascades badly), maintain more headroom. For stateless compute (where scaling is fast), less headroom is acceptable.

<!-- RESOURCES -->

- [Google SRE Book - Handling Overload](https://sre.google/sre-book/handling-overload/) -- type: book, time: 20m
- [Capacity Planning for SREs - Google SRE Workbook](https://sre.google/workbook/capacity-planning/) -- type: book, time: 30m

<!-- ZH_SUMMARY -->
流量持续增长。新功能增加了每个请求的资源消耗。市场部门计划开展一场活动，一夜之间让流量翻倍。到了某个时刻，你现有的系统将无法满足你所需的系统。容量规划就是理解系统如何扩展、并确保你不会在生产环境中触碰到极限的实践。目标不是拥有无限资源——而是知道天花板在哪里、你还有多少余量，以及如何提前应对。

<!-- ZH_DEEP_DIVE -->
## 容量规划要回答的问题

容量规划要解决三个问题：

1. **我们会在哪里遇到瓶颈？** 随着流量增长，哪种资源——CPU、内存、数据库连接、网络吞吐量、存储——会最先达到上限？

2. **我们什么时候会遇到瓶颈？** 根据当前的 growth 趋势和计划中的需求，距离该资源耗尽还有多少周或多少个月？

3. **我们需要对此做什么？** 水平扩展、优化代码、增加缓存、重新协商依赖的 SLO、增加基础设施？

这些问题无法通过理论推导来回答。它们需要对系统当前在负载下的行为进行测量。

## 四种资源约束

大多数容量问题都出在以下四个地方之一：

**CPU**：请求处理对可用核心来说计算过于密集。表现为高流量下延迟增加，最终超时。通过水平扩展（更多实例）或对热点代码路径进行性能分析和优化来解决。

**内存**：每个请求占用大量内存（对象分配、缓存、会话状态），系统内存耗尽。表现为 GC 暂停、OOM kill、内存清理周期越来越长。通过减少每请求内存占用或增加 RAM/实例来解决。

**数据库连接**：连接池大小固定。在高并发下，请求排队等待连接。表现为延迟尖峰与流量成正比。通过连接池大小调整、连接多路复用（PgBouncer）或减少每请求的数据库调用次数来解决。

**吞吐量 / 网络**：传输的数据量触及网络接口、负载均衡器或上游提供商的限制。表现为丢包、重传和延迟。通过缓存、减小响应大小或升级网络容量来解决。

## 流量预测

历史流量数据有规律：日周期、周模式、季节性尖峰、增长趋势。提取这些规律：

**日/周基线**：典型的流量曲线是什么样？峰值在什么时候？峰值与平均值的比率是多少？

**增长趋势**：对历史流量数据拟合一条趋势线。按当前增长率，流量何时达到 2 倍？5 倍？这给你一个时间线。

**已知需求事件**：产品发布、营销活动、季节性事件。这些需要单独分析——一个承诺 48 小时内带来 10 倍流量的活动，与渐进式增长是不同的问题。

大多数容量规划工具（CloudWatch、Datadog、Google Cloud Monitoring）可以根据历史趋势向前预测。预测是估计值，不是保证，但它给你一个可辩护的数字来作为规划依据。

## 余量原则

不要计划以 100% 的容量运行。计划以定义好的最大利用率运行——大多数资源通常为 60-70%——并将超过该值视为触发容量行动的信号。

平均 CPU 运行在 70% 意味着你有 30% 的余量来应对流量尖峰和负载波动。CPU 运行在 95% 意味着任何尖峰都会导致延迟下降，任何流量波动都会导致事故。

余量百分比取决于流量的波动性和超限的代价。对于数据库（连接池耗尽会严重级联），保持更多余量。对于无状态计算（扩展速度快），较少的余量是可以接受的。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 处理过载](https://sre.google/sre-book/handling-overload/) -- 类型：书籍，时长：20分钟
- [SRE 容量规划 - Google SRE 工作手册](https://sre.google/workbook/capacity-planning/) -- 类型：书籍，时长：30分钟

<!-- ZH_UI -->
1. 运行负载测试，模拟当前流量 2 倍和 5 倍的预期流量
2. 确定哪个资源最先达到极限：CPU、内存、数据库连接还是网络
3. 基于历史数据和计划增长构建流量预测
4. 设置主动告警，在还剩数周余量时触发，而不是只剩数小时
5. 我纸面上有容量估算。如何在真实流量到来前实际验证它们？
6. 我算过了，我们应该能承受当前流量的 3 倍。但上次我这么说时，我错了。我想实际模拟负载，自己找出瓶颈，而不是让用户替我找出来。
7. 我的系统可靠且资源充足。如何让基础设施对整个工程组织可访问且高效？
8. 我能运行可靠的基础设施。但现在的问题是：如何让整个工程组织都能使用它？每个团队都在从头重新造基础设施，每个新员工都要花数周搭建 Kubernetes——这不可持续。一定有更好的方式来共享我构建的东西。
