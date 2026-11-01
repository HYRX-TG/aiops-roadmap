---
id: service-level-objectives
title: Service Level Objectives
zone: sre
edges:
  to:
    - id: dependency-slos
      question: >-
        My service depends on five others. If any of them are slow, my SLO
        fails. How do I account for that?
      detail: >-
        I'm setting an SLO for my checkout service, but it calls auth, payments,
        inventory, and notifications. If any of those are failing, I fail. Should
        my SLO be based on the sum of all their failure rates? I feel like I'm
        missing something fundamental here.
    - id: error-budgets
      question: >-
        I've got an SLO set. What does that actually give me beyond a number
        on a dashboard?
      detail: >-
        I have a target on paper. But I'm not sure what to do with it. Is it
        just something I monitor and feel bad about when I miss? How does having
        an SLO actually change how my team works or what we prioritise?
difficulty: 2
tags:
  - slo
  - sre
  - reliability
  - targets
  - objectives
category: practice
milestones:
  - Write an SLO for a service you own, including the SLI and target percentage
  - Explain why SLOs should be set below 100% and what that communicates
  - Understand the difference between a customer-facing SLO and an internal SLO
  - Know what it means to negotiate an SLO with a product stakeholder
title_zh: "服务等级目标"

---


An SLO is the target you hold yourself to. Not what you promise customers — that's the SLA. Not the raw metric — that's the SLI. The SLO is the decision: "99.5% of requests will succeed." Simple to state, harder to pick correctly. The number you choose has real engineering consequences: it determines what architecture you need, what on-call burden you accept, and how much risk you can take when shipping.

<!-- DEEP_DIVE -->

## Why 100% is the wrong answer

The first instinct is to set the highest possible target. Maximum reliability sounds like the right goal. But 100% availability is impossible — hardware fails, networks partition, deployments go wrong. If you set 100% as your SLO, you're setting yourself up to permanently miss it, which makes the metric meaningless.

More importantly, chasing near-100% reliability is extraordinarily expensive. The difference between 99.9% and 99.99% availability isn't incremental — it requires eliminating single points of failure, implementing automated failover, achieving zero-downtime deployments, building full geographic redundancy. All of that costs engineering time that could otherwise go to features.

The right SLO is the minimum reliability that keeps users happy and the business healthy. Set it lower than your instinct says — you can always tighten it later if you're comfortably exceeding it.

## How to pick a target

There are two useful inputs:

**Historical performance** — What availability are you actually delivering today? If you've been running at 99.7% for the past six months, committing to 99.95% is aspirational fantasy. Start at or slightly above your current baseline, then improve from there.

**User expectations** — What does a user experience when the service is at various reliability levels? For an internal admin tool, users might tolerate 99% — that's 7 hours of downtime per month during working hours, which is annoying but manageable. For a checkout flow, users might churn if availability drops below 99.9%. For a payment processor, anything below 99.99% is commercially unacceptable. Different services, different users, different SLOs.

## Writing an SLO

A complete SLO has four parts:

- **The indicator**: what you're measuring ("fraction of HTTP requests returning 2xx")
- **The target**: the percentage ("99.5%")
- **The window**: over what time period ("rolling 30 days")
- **The measurement method**: how you compute it ("from ingress controller access logs, excluding health check endpoints")

The window matters. A 30-day rolling window is the standard, but it means you carry the cost of a bad week for a month. Some teams use quarterly SLOs for strategic decisions and monthly SLOs for operational alerting.

## SLOs need negotiation, not just calculation

An SLO you pick in isolation has no teeth. The product team will push back when reliability work competes with feature work, and without buy-in, the SLO becomes a number on a dashboard that nobody acts on.

The right process: propose an SLO based on data, explain what it costs to achieve it, and explicitly negotiate with product management. When both sides agree, the SLO carries weight. When the budget runs out, both sides are committed to the policy.

<!-- RESOURCES -->

- [Google SRE Book - Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) -- type: book, time: 30m
- [Implementing SLOs - Google SRE Workbook](https://sre.google/workbook/implementing-slos/) -- type: book, time: 45m
- [SLO Generator - Open Source Tool](https://github.com/google/slo-generator) -- type: tool, time: 30m

<!-- ZH_SUMMARY -->
SLO 是你对自己设定的目标。它不是你对客户的承诺——那是 SLA。也不是原始指标——那是 SLI。SLO 是一个决策：“99.5% 的请求将成功。”表述简单，但正确选择却更难。你选择的数字会带来实实在在的工程后果：它决定了你需要什么样的架构、你接受多大的 on-call 负担，以及你在发布时能承担多少风险。

<!-- ZH_DEEP_DIVE -->
## 为什么 100% 是错误的答案

第一反应是设定尽可能高的目标。最高可靠性听起来像是正确的目标。但 100% 可用性是不可能的——硬件会故障、网络会分区、部署会出错。如果你把 100% 设为 SLO，你就是在让自己永远无法达成它，这会让这个指标变得毫无意义。

更重要的是，追求接近 100% 的可靠性代价极其高昂。99.9% 和 99.99% 可用性之间的差距不是渐进的——它需要消除单点故障、实现自动故障转移、达成零停机部署、构建完整的地理冗余。所有这些都要消耗本可以用于功能开发的工程时间。

正确的 SLO 是能保持用户满意、业务健康的最低可靠性。把它设得比你的直觉更低——如果你能轻松超额完成，之后随时可以收紧。

## 如何选择目标

有两个有用的输入：

**历史表现**——你今天实际交付的可用性是多少？如果你过去六个月一直运行在 99.7%，承诺 99.95% 就是不切实际的幻想。从当前基线或略高于基线开始，然后在此基础上改进。

**用户期望**——当服务处于不同可靠性水平时，用户体验如何？对于内部管理工具，用户可能能容忍 99%——那是每月工作时间内 7 小时的停机，虽然烦人但可管理。对于结账流程，如果可用性降到 99.9% 以下，用户可能会流失。对于支付处理器，任何低于 99.99% 的可用性在商业上都是不可接受的。不同的服务、不同的用户、不同的 SLO。

## 编写 SLO

一个完整的 SLO 有四个部分：

- **指标**：你在测量什么（“返回 2xx 的 HTTP 请求比例”）
- **目标**：百分比（“99.5%”）
- **窗口**：在多长的时间段内（“滚动 30 天”）
- **测量方法**：你如何计算它（“来自 ingress controller 访问日志，排除健康检查端点”）

窗口很重要。30 天滚动窗口是标准做法，但这意味着你要为一个糟糕的一周背负一个月的代价。有些团队使用季度 SLO 做战略决策，使用月度 SLO 做运维告警。

## SLO 需要协商，而不仅仅是计算

孤立选出的 SLO 没有约束力。当可靠性工作与功能工作竞争时，产品团队会反对，而没有共识，SLO 就变成仪表盘上一个没人采取行动的数字。

正确的流程：基于数据提出 SLO，解释达成它的成本，并与产品管理方明确协商。当双方都同意时，SLO 才有分量。当预算耗尽时，双方都受该策略约束。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 服务等级目标](https://sre.google/sre-book/service-level-objectives/) -- 类型: 书籍, 时长: 30m
- [实施 SLO - Google SRE 工作手册](https://sre.google/workbook/implementing-slos/) -- 类型: 书籍, 时长: 45m
- [SLO Generator - 开源工具](https://github.com/google/slo-generator) -- 类型: 工具, 时长: 30m

<!-- ZH_UI -->
1. 为你负责的服务编写一个 SLO，包括 SLI 和目标百分比
2. 解释为什么 SLO 应设定在 100% 以下，以及这传达了什麼
3. 理解面向客户的 SLO 与内部 SLO 之间的区别
4. 了解与产品相关方协商 SLO 意味着什么
5. 我的服务依赖另外五个服务。如果其中任何一个变慢，我的 SLO 就会失败。我该如何考虑这一点？
6. 我正在为我的结账服务设定 SLO，但它会调用 auth、payments、inventory 和 notifications。如果其中任何一个失败，我就会失败。我的 SLO 是否应该基于它们所有失败率的总和？我觉得我在这里遗漏了一些根本性的东西。
7. 我已经设定了一个 SLO。除了仪表板上的一个数字之外，它实际上还能给我带来什么？
8. 我在纸面上有一个目标。但我不知道该拿它怎么办。它只是我监控的东西，并在未达标时感到难过吗？拥有 SLO 实际上如何改变我的团队的工作方式或我们优先处理的事项？
