---
id: load-testing
title: Load Testing
zone: sre
edges:
  to:
    - id: platform-engineering
      question: >-
        Load tests are passing. How do I make sure every new service our teams
        build starts with this level of rigour?
      detail: >-
        I've validated our capacity assumptions — I know where we break and
        I've fixed the bottlenecks. But there are fifteen other services that
        have never been load tested. I can't do this for every team manually.
        How do I make it a default rather than something I have to chase people
        to do?
difficulty: 2
tags:
  - load-testing
  - performance
  - capacity
  - sre
  - reliability
  - k6
  - locust
category: practice
milestones:
  - Write a load test that simulates realistic traffic patterns for a service you own
  - Identify the bottleneck — which resource hits its limit first under load
  - Run a soak test to find memory leaks or resource exhaustion over time
  - Know the difference between load testing, stress testing, and spike testing
title_zh: "负载测试"

---


The only way to know how your system behaves under load is to put it under load. Capacity estimates made from reading code or doing back-of-the-envelope math are invariably wrong in ways you don't expect. Load testing generates synthetic traffic against your system and lets you observe exactly what breaks, at what scale, and why — before real users discover the answer for you.

<!-- DEEP_DIVE -->

## Types of load tests

**Load test**: ramp traffic up to your expected peak and hold it there. Confirm the system handles normal high-traffic operation without degradation. This is the most common starting point.

**Stress test**: keep increasing traffic beyond normal peak until something breaks. This identifies your system's actual ceiling and which resource hits it first. The goal is to find the limit, not to prove the system handles expected load.

**Spike test**: jump from baseline traffic to peak instantly, rather than ramping gradually. Real traffic often has this shape — a marketing email goes out and traffic doubles in 60 seconds. This tests your auto-scaling and your cold-start latency.

**Soak test**: run at moderate load for many hours. This finds problems that only manifest over time: memory leaks, connection pool exhaustion, log accumulation, cache eviction issues, database fragmentation.

## Choosing a tool

**k6** — the current industry-standard choice for most teams. Scripts are written in JavaScript. Excellent for API and HTTP load testing. Has cloud execution (k6 Cloud) for running large tests from distributed locations. Open-source, widely documented.

**Locust** — Python-based. Good if your team is more comfortable with Python. Easy to express complex, stateful user journeys. Requires more setup for distributed execution.

**Artillery** — YAML-based configuration with JavaScript extensions. Good for quick tests. Excellent documentation.

**Gatling** — Scala-based (can be configured in Java/Kotlin). Excellent reporting. Popular in JVM shops.

For most teams starting out, k6 is the right choice: low barrier to entry, great documentation, active community, and it scales from simple smoke tests to complex production simulations.

## Writing a realistic test

The hardest part of load testing is making the traffic realistic. Blasting your homepage with 1,000 concurrent requests is not the same as 1,000 concurrent users doing what real users do.

Realistic test characteristics:
- **Realistic traffic distribution**: most requests should be the most common user actions, not just the most interesting ones
- **Realistic user behavior**: include think time (pauses between actions), not just back-to-back requests
- **Realistic data variety**: use realistic data, not the same test credentials on every request
- **Realistic request size**: POST requests with real payloads, not empty bodies

```javascript
// k6 example: basic load test
import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // ramp up
    { duration: '5m', target: 100 },  // hold
    { duration: '2m', target: 0 },    // ramp down
  ],
};

export default function () {
  const response = http.get('https://your-service/api/products');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1); // think time
}
```

## What to observe during a test

Monitor these during the load test:
- **Error rate**: does it increase as load increases? At what traffic level?
- **Latency percentiles (P50, P95, P99)**: not just average — the tail matters
- **Resource utilization**: which resource hits its limit first (CPU, memory, DB connections)?
- **Auto-scaling events**: are new instances launching fast enough to handle the ramp?
- **Downstream dependencies**: are you pushing a bottleneck into a dependency?

<!-- RESOURCES -->

- [k6 Documentation](https://k6.io/docs/) -- type: tool, time: 1h
- [Load Testing Guide - k6 Blog](https://k6.io/blog/load-testing-guide/) -- type: article, time: 20m
- [Google SRE Book - Testing for Reliability](https://sre.google/sre-book/testing-reliability/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
要了解系统在负载下的行为，唯一的方法就是给它施加负载。通过阅读代码或做粗略估算得出的容量估计，总会以你意想不到的方式出错。负载测试会向你的系统生成合成流量，让你在真实用户替你发现答案之前，准确观察到底是什么在什么规模下、因为什么原因而崩溃。

<!-- ZH_DEEP_DIVE -->
## 负载测试的类型

**负载测试**：将流量逐步提升至预期峰值并保持在该水平。确认系统在正常运行的高流量下不会出现性能退化。这是最常见的起点。

**压力测试**：持续增加流量，超过正常峰值，直到某个环节崩溃。这可以识别出系统的实际上限，以及哪个资源最先触及瓶颈。目标是找到极限，而不是证明系统能承受预期负载。

**尖峰测试**：从基线流量瞬间跃升至峰值，而不是逐步爬升。真实流量经常呈现这种形态——一封营销邮件发出后，流量在 60 秒内翻倍。这可以测试你的自动扩缩容能力和冷启动延迟。

**浸泡测试**：在中等负载下持续运行数小时。这可以发现只在长时间运行后才显现的问题：内存泄漏、连接池耗尽、日志堆积、缓存淘汰问题、数据库碎片化。

## 选择工具

**k6** —— 目前大多数团队采用的行业标准选择。脚本使用 JavaScript 编写。非常适合 API 和 HTTP 负载测试。支持云端执行（k6 Cloud），可从分布式位置运行大规模测试。开源，文档完善。

**Locust** —— 基于 Python。如果你的团队更熟悉 Python，这是不错的选择。易于表达复杂、有状态的用户旅程。分布式执行需要更多配置。

**Artillery** —— 基于 YAML 配置，支持 JavaScript 扩展。适合快速测试。文档优秀。

**Gatling** —— 基于 Scala（可通过 Java/Kotlin 配置）。报告功能出色。在 JVM 技术栈的团队中很流行。

对于大多数刚起步的团队，k6 是正确选择：入门门槛低、文档出色、社区活跃，并且可以从简单的冒烟测试扩展到复杂的生产模拟。

## 编写贴近真实的测试

负载测试最难的部分是让流量贴近真实。用 1,000 个并发请求轰炸你的首页，与 1,000 个并发用户执行真实用户行为，是完全不同的。

真实测试的特征：
- **真实的流量分布**：大多数请求应该是用户最常见的操作，而不仅仅是最有趣的操作
- **真实的用户行为**：包含思考时间（操作之间的停顿），而不仅仅是连续不断的请求
- **真实的数据多样性**：使用真实数据，而不是每个请求都使用相同的测试凭证
- **真实的请求大小**：POST 请求携带真实负载，而不是空请求体

```javascript
// k6 示例：基础负载测试
import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // 爬升
    { duration: '5m', target: 100 },  // 保持
    { duration: '2m', target: 0 },    // 回落
  ],
};

export default function () {
  const response = http.get('https://your-service/api/products');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1); // 思考时间
}
```

## 测试期间需要观察什么

在负载测试期间监控以下指标：
- **错误率**：是否随负载增加而上升？在什么流量水平下开始上升？
- **延迟百分位数（P50、P95、P99）**：不仅仅是平均值——尾部延迟很重要
- **资源利用率**：哪个资源最先触及上限（CPU、内存、数据库连接）？
- **自动扩缩容事件**：新实例的启动速度是否足以应对流量爬升？
- **下游依赖**：你是否将瓶颈推给了某个依赖服务？

<!-- ZH_RESOURCES -->
- [k6 文档](https://k6.io/docs/) -- type: tool, time: 1h
- [负载测试指南 - k6 博客](https://k6.io/blog/load-testing-guide/) -- type: article, time: 20m
- [Google SRE 手册 - 可靠性测试](https://sre.google/sre-book/testing-reliability/) -- type: book, time: 20m

<!-- ZH_UI -->
1. 为你负责的服务编写一个模拟真实流量模式的负载测试
2. 找出瓶颈——在负载下哪个资源最先达到极限
3. 运行浸泡测试，发现随时间推移出现的内存泄漏或资源耗尽
4. 了解负载测试、压力测试和尖峰测试之间的区别
5. 负载测试已通过。我如何确保团队构建的每个新服务都从这种严谨程度开始？
6. 我已经验证了容量假设——我知道我们在哪里会崩溃，也已经修复了瓶颈。但还有十五个其他服务从未做过负载测试。我无法为每个团队手动做这件事。如何让它成为默认做法，而不是我得追着别人去做？
