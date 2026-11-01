---
id: critical-user-journeys
title: Critical User Journeys
zone: sre
edges:
  to:
    - id: service-level-objectives
      question: >-
        I've mapped the user journeys. Now how do I turn them into concrete
        reliability targets?
      detail: >-
        I can describe what a user does: opens the app, searches, adds to cart,
        checks out. But I don't know how to translate that into a measurable
        number. Do I measure each step separately? What counts as a failure —
        an error response, or just being slow? And how do I know what target
        to set for each one?
difficulty: 2
tags:
  - cuj
  - critical-user-journeys
  - slo
  - sre
  - user-experience
  - reliability
category: concept
milestones:
  - Identify the top three critical user journeys for a service you own
  - Explain why "server uptime" is a poor proxy for user experience reliability
  - Map a complete user journey end-to-end including all service dependencies
  - Understand why you need separate SLOs for different user journeys
title_zh: "关键用户旅程"

---


Your infrastructure metrics are all green, but users are filing support tickets. This happens because there's a gap between what you're measuring and what users are actually doing. A Critical User Journey (CUJ) is the sequence of steps a real user takes to accomplish something meaningful — search for a product, complete a checkout, send a message, upload a file. Reliability measured against those journeys is reliability that users actually experience.

<!-- DEEP_DIVE -->

## Why per-service metrics miss the point

Modern applications are composed of many services, each with its own dashboards and SLOs. The auth service is 99.9% available. The product catalogue is 99.9% available. The payment service is 99.9% available. So why are users unable to complete checkouts?

The problem: a user completing a checkout touches all three services sequentially. If any one of them fails, the checkout fails. Three services each at 99.9% availability combine to 99.7% availability for the checkout journey — which means users can't complete purchases 0.3% of the time. That's 3x worse than any individual service suggests.

Per-service metrics are internally coherent but externally misleading. CUJs reveal what the user actually experiences by measuring across the full dependency chain.

## Identifying your CUJs

A CUJ is typically 3-10 steps that represent a complete unit of user value. For an e-commerce site:

- **Purchase journey**: search → view product → add to cart → checkout → payment → confirmation
- **Account journey**: register → verify email → log in → manage profile
- **Return journey**: request return → print label → track status

Not all journeys are equally critical. The right question is: if this journey fails completely, what happens to the business? Payment failures lose revenue directly. Return failures create support escalations. Both matter, but the priority and SLO target should reflect the business impact.

## Measuring CUJ reliability

You have two main approaches:

**Synthetic monitoring** — write automated tests that simulate user journeys end-to-end, run them continuously from outside your infrastructure, and alert when they fail. This gives you a continuous signal independent of real traffic, and works even at low traffic volumes. Tools: Playwright, Datadog Synthetic Tests, Pingdom.

**Real user traffic analysis** — instrument each step of the journey and track the proportion that complete successfully. This reflects actual user experience but requires sufficient traffic volume to be statistically meaningful, and requires tracing across services. Tools: distributed tracing (Jaeger, Tempo), analytics events.

## Separate SLOs for separate journeys

Different journeys have different expectations and different tolerances. Search results appearing in 500ms might be a reasonable SLO. Payment confirmation appearing within 5 seconds might be fine — users expect it to take a moment. Internal admin actions might have much more forgiving targets.

Once you've defined your CUJs and how to measure them, you have the right inputs for setting SLOs. The objective should reflect user expectations for that specific journey — not an arbitrary number or an industry benchmark.

<!-- RESOURCES -->

- [Defining SLOs for User Journeys - Google SRE Workbook](https://sre.google/workbook/art-of-slos/) -- type: book, time: 45m
- [Critical User Journeys - Google Web DevRel](https://web.dev/articles/user-centric-performance-metrics) -- type: article, time: 20m
- [Synthetic Monitoring with Playwright](https://playwright.dev/docs/intro) -- type: tool, time: 30m

<!-- ZH_SUMMARY -->
你的基础设施指标全部显示正常，但用户却在提交支持工单。出现这种情况，是因为你所测量的内容与用户实际执行的操作之间存在差距。关键用户旅程（Critical User Journey，CUJ）是真实用户为完成某项有意义的事情所经历的一系列步骤——搜索商品、完成结账、发送消息、上传文件。以这些旅程为基准衡量的可靠性，才是用户真正体验到的可靠性。

<!-- ZH_DEEP_DIVE -->
## 为什么按服务划分的指标没有抓住重点

现代应用由许多服务组成，每个服务都有自己的仪表盘和 SLO。认证服务可用性 99.9%。商品目录可用性 99.9%。支付服务可用性 99.9%。那为什么用户还是无法完成结账？

问题在于：用户完成一次结账会依次经过这三个服务。其中任何一个失败，结账就会失败。三个各自 99.9% 可用性的服务组合起来，结账旅程的可用性只有 99.7%——这意味着用户有 0.3% 的概率无法完成购买。这比任何单个服务所暗示的情况都要差 3 倍。

按服务划分的指标在内部是自洽的，但对外部却具有误导性。CUJ 通过衡量整条依赖链，揭示用户实际体验到的状况。

## 识别你的 CUJ

一个 CUJ 通常由 3-10 个步骤组成，代表一个完整的用户价值单元。对于一个电商网站来说：

- **购买旅程**：搜索 → 查看商品 → 加入购物车 → 结账 → 支付 → 确认
- **账户旅程**：注册 → 验证邮箱 → 登录 → 管理个人资料
- **退货旅程**：申请退货 → 打印标签 → 跟踪状态

并非所有旅程都同等关键。正确的问题是：如果这个旅程完全失败，业务会怎样？支付失败会直接损失收入。退货失败会导致支持工单升级。两者都重要，但优先级和 SLO 目标应反映业务影响。

## 衡量 CUJ 可靠性

你有两种主要方法：

**合成监控**——编写模拟用户旅程端到端流程的自动化测试，从基础设施外部持续运行它们，并在失败时告警。这为你提供了一个独立于真实流量的持续信号，即使在低流量下也能工作。工具：Playwright、Datadog Synthetic Tests、Pingdom。

**真实用户流量分析**——对旅程的每个步骤进行埋点，并跟踪成功完成的比例。这反映了实际用户体验，但需要足够的流量才能在统计上有意义，并且需要跨服务的追踪。工具：分布式追踪（Jaeger、Tempo）、分析事件。

## 为不同旅程设置独立的 SLO

不同旅程有不同的期望和不同的容忍度。搜索结果在 500ms 内出现可能是一个合理的 SLO。支付确认在 5 秒内出现可能没问题——用户预期它需要一点时间。内部管理操作的目标可能宽松得多。

一旦你定义了 CUJ 以及如何衡量它们，你就有了设置 SLO 的正确输入。目标应反映用户对该特定旅程的期望——而不是一个随意的数字或行业基准。

<!-- ZH_RESOURCES -->
- [为用户旅程定义 SLO - Google SRE 工作手册](https://sre.google/workbook/art-of-slos/) -- 类型: 书籍, 时间: 45分钟
- [关键用户旅程 - Google Web DevRel](https://web.dev/articles/user-centric-performance-metrics) -- 类型: 文章, 时间: 20分钟
- [使用 Playwright 进行合成监控](https://playwright.dev/docs/intro) -- 类型: 工具, 时间: 30分钟

<!-- ZH_UI -->
1. 为你负责的服务识别出前三个关键用户旅程
2. 解释为什么“服务器正常运行时间”不能很好地代表用户体验可靠性
3. 端到端梳理完整用户旅程，包括所有服务依赖
4. 理解为什么不同用户旅程需要不同的 SLO
5. 我已经梳理了用户旅程。现在如何把它们转化为具体的可靠性目标？
6. 我能描述用户做了什么：打开应用、搜索、加入购物车、结账。但我不知道如何把它转化为可衡量的数字。我是要分别衡量每一步吗？什么算作失败——错误响应，还是仅仅变慢？我又怎么知道每一步该设定什么目标？
