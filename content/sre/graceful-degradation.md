---
id: graceful-degradation
title: Graceful Degradation
zone: sre
edges:
  to:
    - id: capacity-planning
      question: >-
        My services now degrade gracefully instead of falling over completely.
        How do I make sure we can actually handle real growth too?
      detail: >-
        Graceful degradation means we survive individual failures — a dependency
        goes down and we serve partial results instead of hard errors. But I'm
        now thinking about a different kind of stress: not a dependency failing,
        but traffic that just keeps growing. I need to know we can absorb that
        before it becomes an incident.
difficulty: 3
tags:
  - graceful-degradation
  - resilience
  - reliability
  - sre
  - circuit-breakers
  - fallbacks
  - partial-failure
category: practice
milestones:
  - Identify which of your service's features can be disabled without breaking core functionality
  - Implement circuit breakers for at least one external dependency
  - Test that your service serves degraded responses when a dependency is unavailable
  - Understand the difference between failing fast and gracefully degrading
title_zh: "优雅降级"

---


When a dependency fails, you have two choices: fail completely and serve users an error, or degrade gracefully and serve users something reduced but functional. The difference in user experience is enormous. Graceful degradation is the practice of designing services to handle partial failure — shedding features, serving cached data, returning reduced results — rather than crashing entirely when something in the dependency chain breaks.

<!-- DEEP_DIVE -->

## The failure modes that matter

There are two types of dependency failure that graceful degradation addresses:

**Hard failures**: the dependency is completely unavailable. HTTP connection refused. DNS doesn't resolve. No response at all.

**Soft failures**: the dependency is responding, but slowly. Timeouts. Elevated error rates. High latency. These are often worse than hard failures because they cause callers to queue up waiting, eventually exhausting their own connection pools and thread capacity.

Graceful degradation needs to handle both.

## Circuit breakers

A circuit breaker is the primary pattern for handling dependency failures. Named after electrical circuit breakers, the concept is the same: when failure is detected, "open" the circuit to stop requests flowing to the failing dependency, instead returning errors immediately.

The circuit breaker has three states:

**Closed** (normal): requests flow through normally. Failures are counted.

**Open** (failing): when failure rate exceeds a threshold, the circuit opens. Requests to the dependency are short-circuited — they fail immediately without attempting the call. This bounds the blast radius: a slow downstream doesn't cause callers to pile up.

**Half-open** (recovering): after a timeout, a small number of test requests are let through. If they succeed, the circuit closes. If they fail, it opens again.

Libraries: Resilience4j (Java/Kotlin), Hystrix (deprecated but influential), Polly (.NET), Python's circuit-breaker libraries, and most service meshes (Istio, Linkerd) implement circuit breaking at the infrastructure level.

## Timeouts everywhere

Every network call must have a timeout. Without a timeout, a slow dependency will hold your threads or goroutines indefinitely, eventually exhausting them. A service that can't reach its database should time out and fail after 500ms, not after 30 seconds.

The right timeout value depends on the SLO you're trying to meet and the expected response time of the dependency. For interactive user requests, timeouts should be aggressive — if a call hasn't returned in 1-2 seconds, your user is already frustrated. For async background work, timeouts can be more generous.

Always set timeouts at two levels: connection timeout (how long to wait to establish a connection) and read timeout (how long to wait for a response). Missing either one leaves a gap.

## Feature degradation

When a dependency is unavailable, the question is: what can the service still do without it?

- **Recommendation service down?** Show no recommendations rather than blocking the page load.
- **Search index degraded?** Fall back to basic SQL search or return cached recent results.
- **Notification service unavailable?** Queue notifications for later delivery rather than failing the user's action.
- **Personalization service down?** Show default content rather than a blank page.

This requires deliberately designing each dependency as optional or gracefully degradable, not treating all dependencies as required for all operations.

## Cache as a fallback

For read-heavy dependencies, a stale cache is often better than no data. If the product catalogue API is down, serving yesterday's product data is better than serving a 500 error to every user who visits a product page.

Implement "stale-while-revalidate" caching: serve the cached response immediately, then attempt to refresh in the background. If the refresh fails, keep serving the stale data until it's too old to be useful.

<!-- RESOURCES -->

- [Release It! - Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/) -- type: book, time: varies
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html) -- type: article, time: 15m
- [Resilience4j Documentation](https://resilience4j.readme.io/docs/circuitbreaker) -- type: tool, time: 30m

<!-- ZH_SUMMARY -->
当依赖项发生故障时，你有两种选择：要么彻底失败并向用户返回错误，要么优雅降级，为用户提供功能有所缩减但仍可用的服务。这两种方式在用户体验上的差异是巨大的。优雅降级是一种服务设计实践：当依赖链中的某个环节出现故障时，服务能够处理部分失败——削减功能、提供缓存数据、返回缩减后的结果——而不是彻底崩溃。

<!-- ZH_DEEP_DIVE -->
## 真正重要的故障模式

优雅降级所处理的依赖故障有两类：

**硬故障**：依赖完全不可用。HTTP 连接被拒绝。DNS 无法解析。完全没有响应。

**软故障**：依赖有响应，但很慢。超时。错误率升高。高延迟。这类故障往往比硬故障更糟，因为它们会让调用方排队等待，最终耗尽自身的连接池和线程容量。

优雅降级需要同时处理这两类故障。

## 熔断器

熔断器是处理依赖故障的主要模式。其命名源自电气断路器，概念相同：当检测到故障时，“断开”电路以阻止请求流向故障依赖，转而立即返回错误。

熔断器有三种状态：

**关闭**（正常）：请求正常通过。故障会被计数。

**打开**（故障中）：当故障率超过阈值时，电路打开。发往该依赖的请求被短路——立即失败，不再尝试调用。这限定了爆炸半径：缓慢的下游不会导致调用方堆积。

**半开**（恢复中）：超时之后，允许少量测试请求通过。如果成功，电路关闭。如果失败，电路再次打开。

相关库：Resilience4j（Java/Kotlin）、Hystrix（已废弃但影响深远）、Polly（.NET）、Python 的 circuit-breaker 库，以及大多数服务网格（Istio、Linkerd）在基础设施层面实现熔断。

## 处处设置超时

每次网络调用都必须有超时。没有超时，缓慢的依赖会无限期占用你的线程或 goroutine，最终将其耗尽。一个无法连接数据库的服务应该在 500ms 后超时失败，而不是 30 秒后。

正确的超时值取决于你要满足的 SLO 以及依赖的预期响应时间。对于交互式用户请求，超时应激进一些——如果调用在 1-2 秒内没有返回，用户已经不耐烦了。对于异步后台工作，超时可以更宽松。

始终在两个层面设置超时：连接超时（等待建立连接的时间）和读取超时（等待响应的时间）。缺少任何一个都会留下缺口。

## 功能降级

当某个依赖不可用时，问题是：没有它，服务还能做什么？

- **推荐服务宕机？** 不显示推荐，而不是阻塞页面加载。
- **搜索索引降级？** 回退到基础 SQL 搜索，或返回缓存的最新结果。
- **通知服务不可用？** 将通知排队以便稍后投递，而不是让用户操作失败。
- **个性化服务宕机？** 显示默认内容，而不是空白页面。

这需要有意识地将每个依赖设计为可选或可优雅降级，而不是把所有依赖都视为所有操作的必需项。

## 缓存作为回退

对于读密集型的依赖，过期的缓存往往好过没有数据。如果商品目录 API 宕机，提供昨天的商品数据也好过向每个访问商品页面的用户返回 500 错误。

实现“stale-while-revalidate”缓存：立即返回缓存响应，然后在后台尝试刷新。如果刷新失败，继续提供过期数据，直到它旧到不再有用。

<!-- ZH_RESOURCES -->
- [Release It! - Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/) -- 类型: 书籍, 时间: 不定
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html) -- 类型: 文章, 时间: 15分钟
- [Resilience4j Documentation](https://resilience4j.readme.io/docs/circuitbreaker) -- 类型: 工具, 时间: 30分钟

<!-- ZH_UI -->
1. 确定你的服务中哪些功能可以在不破坏核心功能的情况下被禁用
2. 为至少一个外部依赖实现熔断器
3. 测试当依赖不可用时，你的服务能提供降级响应
4. 理解快速失败与优雅降级之间的区别
5. 我的服务现在能优雅降级，而不是彻底崩溃。我如何确保我们也能真正应对真实的增长？
6. 优雅降级意味着我们能挺过单个故障——某个依赖宕机时，我们提供部分结果而不是硬错误。但我现在考虑的是另一种压力：不是依赖故障，而是流量持续增长。我需要知道在它变成事故之前我们能吸收这种增长。
