---
id: measuring-reliability
title: Measuring Reliability
zone: sre
edges:
  to:
    - id: service-level-agreements
      question: >-
        I keep seeing 'SLA' in contracts and dashboards — what does it actually
        commit us to, and who holds us to it?
      detail: >-
        Our enterprise customers keep asking about our SLA. Legal drafted some
        numbers but I'm not sure we can actually meet them, and I don't know how
        they relate to what I measure internally. And when internal teams promise
        each other things — is that also an SLA?
    - id: service-level-indicators
      question: >-
        How do I decide what to actually measure? My dashboards have a hundred
        graphs but none of them clearly answer 'is the service OK?'
      detail: >-
        I have CPU, memory, request count, error rate, database connections — but
        when someone asks 'is the service healthy?' I'm still guessing. I want to
        find the handful of measurements that actually reflect whether users are
        having a good experience, not just whether the machines are running.
    - id: critical-user-journeys
      question: >-
        I want to measure reliability from my users' perspective, not just
        whether my servers are up.
      detail: >-
        My pods are all green but users are complaining. I think I'm measuring
        the wrong things — infrastructure health instead of whether users can
        actually complete what they came to do. How do I define and measure
        reliability from their point of view?
difficulty: 1
tags:
  - reliability
  - sre
  - sli
  - slo
  - observability
  - measurement
category: concept
milestones:
  - Explain why raw infrastructure metrics are poor proxies for user experience
  - Understand what SLAs, SLIs, and SLOs are and how they relate to each other
  - Know the difference between availability, reliability, and durability
  - Calculate allowed downtime for common SLO targets (99%, 99.9%, 99.99%)
title_zh: "衡量可靠性"

---


You have alerts. You have dashboards. But when someone asks "how reliable is this service?", the honest answer is "I'm not sure." You know when it's obviously broken. You don't know if it's trending better or worse. There's no shared definition of "working well enough" that developers, ops, and product stakeholders all agree on. Before you can improve reliability, you need a way to measure it that everyone understands — and that actually reflects what users experience.

<!-- DEEP_DIVE -->

## Why uptime isn't enough

"Five nines" sounds impressive until you ask: five nines of what, exactly? Uptime means the service is responding to something. It doesn't tell you whether users are actually getting what they need. A service can be "up" while half of all requests fail with 500 errors. A service can be "up" while every response takes 30 seconds to arrive. From a monitoring dashboard perspective: green. From a user perspective: completely broken.

The problem with uptime as a metric is that it's measured from the inside — "is the process running?" — not from the outside — "are users successfully completing what they came to do?" A service that's 100% up but 50% slow isn't 100% reliable.

## The SRE measurement model

SRE introduces three concepts that work together:

**Service Level Indicators (SLIs)** are the metrics you actually measure. Not "is the service up?" but "what fraction of requests succeeded in under 200ms?" SLIs are chosen to reflect what users actually care about.

**Service Level Objectives (SLOs)** are the targets you set for those indicators. "99.9% of requests should succeed" or "95% of requests should complete in under 200ms." These are internal targets — the standard you hold yourself to.

**Service Level Agreements (SLAs)** are contracts with customers about what happens when you miss those targets. SLAs have consequences: refunds, credits, contract penalties. Not every service needs an SLA, but every service should have SLOs.

## The math that makes it concrete

Some quick numbers that are worth having in your head:

| SLO target | Allowed downtime per month |
|-----------|--------------------------|
| 99% | ~7.3 hours |
| 99.5% | ~3.6 hours |
| 99.9% | ~43 minutes |
| 99.99% | ~4.3 minutes |

The difference between 99.9% and 99.99% is enormous operationally. Achieving that extra 9 requires fundamentally different architecture: no single points of failure, automated failover, zero-downtime deployments. That's why picking your SLO matters — it defines what you need to build.

## Three branches from here

SLAs, SLIs, and Critical User Journeys are distinct enough that each deserves separate attention. SLAs connect to your relationship with customers and what you're contractually committing to. SLIs connect to what you measure and how. CUJs reveal which user actions matter most — and often show you've been measuring the wrong things entirely. All three paths converge on setting objectives that actually guide engineering decisions.

<!-- RESOURCES -->

- [Google SRE Book - Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) -- type: book, time: 30m
- [The Art of SLOs - Google SRE Workbook](https://sre.google/workbook/art-of-slos/) -- type: book, time: 45m
- [SLO vs SLA vs SLI - Atlassian](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
你有告警，也有仪表盘。但当有人问“这个服务有多可靠？”时，诚实的回答是“我不确定。”你知道它明显出故障的时候。你不知道它是在变好还是变差。对于“足够好地运行”没有一个开发者、运维和产品相关方都认同的共享定义。在你能提升可靠性之前，你需要一种所有人都能理解、并且真正反映用户体验的衡量方式。

<!-- ZH_DEEP_DIVE -->
## 为什么仅靠正常运行时间还不够

“五个九”听起来很厉害，直到你问一句：到底是什么的五个九？正常运行时间意味着服务对某些请求有响应。它并不能告诉你用户是否真正得到了他们需要的东西。一个服务可以处于“运行中”状态，而一半的请求都以 500 错误失败。一个服务可以处于“运行中”状态，而每个响应都要等 30 秒才到达。从监控仪表盘的视角看：绿色。从用户的视角看：彻底坏了。

把正常运行时间当作指标的问题在于，它是从内部测量的——“进程还在跑吗？”——而不是从外部测量的——“用户是否成功完成了他们想做的事？”一个 100% 在线但 50% 缓慢的服务，并不是 100% 可靠的。

## SRE 的度量模型

SRE 引入了三个协同工作的概念：

**服务等级指标（SLI）** 是你实际测量的指标。不是“服务是否在线？”，而是“有多大比例的请求在 200ms 内成功？”选择 SLI 时，要反映用户真正关心的事情。

**服务等级目标（SLO）** 是你为这些指标设定的目标。“99.9% 的请求应当成功”或“95% 的请求应当在 200ms 内完成”。这些是内部目标——你对自己要求的标准。

**服务等级协议（SLA）** 是与客户签订的合同，规定当你未达成这些目标时会发生什么。SLA 带有后果：退款、抵扣、合同处罚。并非每个服务都需要 SLA，但每个服务都应该有 SLO。

## 让一切具体化的数学

一些值得记在脑子里的快速数字：

| SLO 目标 | 每月允许的停机时间 |
|-----------|--------------------------|
| 99% | ~7.3 小时 |
| 99.5% | ~3.6 小时 |
| 99.9% | ~43 分钟 |
| 99.99% | ~4.3 分钟 |

99.9% 和 99.99% 之间的差异在运维上是巨大的。要实现多出来的那个 9，需要根本不同的架构：没有单点故障、自动故障转移、零停机部署。这就是为什么选择 SLO 很重要——它定义了你需要构建什么。

## 从这里分出的三条分支

SLA、SLI 和关键用户旅程（CUJ）彼此区别足够大，每一条都值得单独关注。SLA 关联到你与客户的关系以及你在合同上承诺的内容。SLI 关联到你测量什么以及如何测量。CUJ 揭示哪些用户操作最重要——而且常常让你发现，你一直在测量完全错误的东西。这三条路径最终都汇聚到设定真正能指导工程决策的目标上。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 服务等级目标](https://sre.google/sre-book/service-level-objectives/) -- 类型: 书籍, 时长: 30m
- [SLO 的艺术 - Google SRE 工作手册](https://sre.google/workbook/art-of-slos/) -- 类型: 书籍, 时长: 45m
- [SLO vs SLA vs SLI - Atlassian](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) -- 类型: 文章, 时长: 10m

<!-- ZH_UI -->
1. 解释为什么原始基础设施指标不能很好地代表用户体验
2. 理解 SLA、SLI 和 SLO 是什么，以及它们之间如何关联
3. 了解可用性、可靠性和持久性之间的区别
4. 计算常见 SLO 目标（99%、99.9%、99.99%）允许的停机时间
5. 我不断在合同和仪表盘中看到“SLA”——它到底承诺了什么，谁用它来约束我们？
6. 我们的企业客户一直询问我们的 SLA。法务起草了一些数字，但我不确定我们是否真能达到，也不知道它们与我在内部衡量的内容有何关系。还有，内部团队之间互相承诺的东西——那也是 SLA 吗？
7. 我该如何决定实际要衡量什么？我的仪表盘有一百张图，但没有一张能清楚回答“服务是否正常？”
8. 我有 CPU、内存、请求数、错误率、数据库连接——但当有人问“服务是否健康？”时，我仍然只能猜。我想找出少数几个真正反映用户是否获得良好体验的衡量指标，而不只是机器是否在运行。
9. 我想从用户视角衡量可靠性，而不只是服务器是否在线。
10. 我的 Pod 全是绿的，但用户在抱怨。我觉得我衡量错了东西——衡量的是基础设施健康，而不是用户是否真能完成他们来做的事。我该如何从他们的角度定义并衡量可靠性？
