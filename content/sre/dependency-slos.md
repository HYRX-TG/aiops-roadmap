---
id: dependency-slos
title: Dependency SLOs
zone: sre
edges:
  to:
    - id: error-budgets
      question: >-
        My SLO now accounts for my dependencies. How does this translate into
        a budget for reliability work?
      detail: >-
        I've set a composite SLO that factors in what my dependencies can
        deliver. Now I have a target that's actually achievable. But I'm still
        not sure how this target guides day-to-day engineering decisions — how
        does it change what I work on next?
difficulty: 2
tags:
  - slo
  - dependency-slos
  - composite-slo
  - sre
  - reliability
  - service-dependencies
category: concept
milestones:
  - Explain why your service SLO cannot exceed the weakest SLO in your dependency chain
  - Calculate a composite availability given three services each at 99.9%
  - Identify all direct dependencies for a service and find their published SLOs
  - Understand what to do when a dependency's SLO is worse than yours needs to be
title_zh: "依赖 SLO"

---


You cannot be more reliable than your dependencies. This sounds obvious, but it has a concrete mathematical implication: if your service calls five other services to process a request, and each has 99.9% availability, your composite availability is approximately 99.5%. Not 99.9%. Not even close. Your SLO needs to account for this reality — otherwise you're committing to a target that's physically impossible to hit.

<!-- DEEP_DIVE -->

## The math of dependency chains

Availability compounds multiplicatively. If service A depends on services B and C, and a request to A requires both B and C to succeed:

```
P(A succeeds) = P(B succeeds) × P(C succeeds)
              = 0.999 × 0.999
              = 0.998 (99.8%)
```

Add a third dependency at 99.9% and you're at 99.7%. Add a fourth and you're at 99.6%. Five dependencies each at 99.9% gives you approximately 99.5% — barely. If any of your dependencies is at 99% availability, the math gets painful fast.

This isn't hypothetical. A checkout service that calls auth, product catalogue, inventory, payments, and notifications has five single points of failure before it even talks to its own database. Setting a 99.9% SLO for that service without understanding the dependency chain is committing to an engineering miracle.

## What to do with this information

First, **catalog your dependencies**. For every service you own, map every outbound call. Include databases, caches, message queues, third-party APIs, internal microservices. Everything. Most engineers are surprised by how long the list is.

Second, **find the published SLOs for each dependency**. If they don't have SLOs, that's information too — they're implicitly promising nothing. Treat undocumented dependencies as lower reliability than you'd like.

Third, **set your SLO at or below the composite availability**. If your dependencies give you a ceiling of 99.5%, your SLO cannot exceed 99.5%. You can aspire to exceed your own SLO, but you can't commit to it.

## Breaking the dependency problem

If the math doesn't work — if your dependencies limit your availability to something lower than what users need — you have engineering options:

**Caching** — store dependency responses locally. Availability now depends on cache hit rate + dependency availability × cache miss rate. Caching is most effective for read-heavy dependencies with data that can tolerate some staleness.

**Graceful degradation** — when a dependency is unavailable, return a degraded response rather than failing entirely. Recommendations go away, notifications queue, non-critical features are disabled. The core flow continues.

**Circuit breakers** — detect when a dependency is failing and stop sending requests to it, instead returning errors immediately rather than waiting for timeouts. This bounds the blast radius of a flaky dependency.

**SLO negotiation with dependency teams** — if a dependency's SLO is incompatible with yours, that's a conversation to have. Sometimes the dependency team doesn't know their SLO is a blocker for yours.

## Cascade failures

The dependency problem has a nastier version: cascading failures. A slow dependency is often worse than an unavailable one. When the database is down, requests fail fast and users get errors. When the database is slow, requests queue up, connections exhaust, memory fills, and the caller goes down too — even though the original problem wasn't with the caller at all.

This is why dependency SLOs should include latency targets, not just availability. A dependency that's technically "available" but responding in 10 seconds for P99 requests is a reliability hazard for anyone who calls it.

<!-- RESOURCES -->

- [Implementing SLOs - Dependency Section](https://sre.google/workbook/implementing-slos/) -- type: book, time: 20m
- [Cascading Failures - Google SRE Book](https://sre.google/sre-book/addressing-cascading-failures/) -- type: book, time: 30m

<!-- ZH_SUMMARY -->
你的可靠性不可能超过你所依赖的组件。这听起来显而易见，但它有一个具体的数学含义：如果你的服务在处理一个请求时调用了另外五个服务，而每个服务的可用性都是 99.9%，那么你的复合可用性大约是 99.5%。不是 99.9%，甚至差得远。你的 SLO 需要考虑到这一现实——否则你就是在承诺一个物理上不可能达成的目标。

<!-- ZH_DEEP_DIVE -->
## 依赖链的数学

可用性以乘法方式复合。如果服务 A 依赖服务 B 和 C，且对 A 的请求需要 B 和 C 都成功：

```
P(A succeeds) = P(B succeeds) × P(C succeeds)
              = 0.999 × 0.999
              = 0.998 (99.8%)
```

再加入第三个依赖，每个 99.9%，你就到了 99.7%。加入第四个，你就到了 99.6%。五个依赖各 99.9% 大约给你 99.5%——勉强。如果你的任何一个依赖是 99% 可用性，数学很快就会变得痛苦。

这不是假设。一个结账服务调用 auth、商品目录、库存、支付和通知，在它甚至还没和自己的数据库通信之前，就已经有五个单点故障。在不理解依赖链的情况下为该服务设定 99.9% 的 SLO，等于承诺一个工程奇迹。

## 如何利用这些信息

第一，**编目你的依赖**。对于你拥有的每个服务，映射每一个出站调用。包括数据库、缓存、消息队列、第三方 API、内部微服务。一切。大多数工程师会对列表之长感到惊讶。

第二，**找到每个依赖已发布的 SLO**。如果它们没有 SLO，那也是信息——它们隐含地没有承诺任何东西。将未文档化的依赖视为比你期望的更低的可靠性。

第三，**将你的 SLO 设定在复合可用性处或以下**。如果你的依赖给你 99.5% 的上限，你的 SLO 不能超过 99.5%。你可以期望超越自己的 SLO，但你不能承诺它。

## 打破依赖问题

如果数学不成立——如果你的依赖将你的可用性限制在低于用户需要的水平——你有工程选项：

**缓存**——在本地存储依赖响应。可用性现在取决于缓存命中率 + 依赖可用性 × 缓存未命中率。缓存对于读密集且数据能容忍一定陈旧性的依赖最有效。

**优雅降级**——当依赖不可用时，返回降级响应而不是完全失败。推荐消失，通知排队，非关键功能被禁用。核心流程继续。

**断路器**——检测依赖何时失败并停止向其发送请求，而是立即返回错误而不是等待超时。这限制了不稳定依赖的爆炸半径。

**与依赖团队协商 SLO**——如果依赖的 SLO 与你的不兼容，那是一场需要进行的对话。有时依赖团队不知道他们的 SLO 是你的阻塞项。

## 级联故障

依赖问题有一个更棘手的版本：级联故障。慢依赖通常比不可用依赖更糟。当数据库宕机时，请求快速失败，用户得到错误。当数据库变慢时，请求排队，连接耗尽，内存填满，调用方也宕机——即使原始问题根本不在调用方。

这就是为什么依赖 SLO 应该包括延迟目标，而不仅仅是可用性。一个技术上“可用”但对 P99 请求响应 10 秒的依赖，对任何调用它的人都是可靠性危害。

<!-- ZH_RESOURCES -->
- [实施 SLO - 依赖关系部分](https://sre.google/workbook/implementing-slos/) -- 类型: 书籍, 时长: 20m
- [级联故障 - Google SRE 手册](https://sre.google/sre-book/addressing-cascading-failures/) -- 类型: 书籍, 时长: 30m

<!-- ZH_UI -->
1. 解释为什么你的服务 SLO 不能超过依赖链中最弱的 SLO
2. 计算三个各为 99.9% 的服务的复合可用性
3. 找出一个服务的所有直接依赖，并找到它们公布的 SLO
4. 理解当依赖的 SLO 低于你所需水平时该怎么做
5. 我的 SLO 现在已考虑我的依赖。这如何转化为可靠性工作的预算？
6. 我已设定一个复合 SLO，把依赖能交付的能力纳入考量。现在我有了一个实际可达的目标。但我仍不确定这个目标如何指导日常工程决策——它如何改变我接下来要做的工作？
