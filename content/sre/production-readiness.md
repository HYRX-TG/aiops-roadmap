---
id: production-readiness
title: Production Readiness
zone: sre
edges:
  to: []
difficulty: 2
tags:
  - production-readiness
  - prd
  - service-maturity
  - launch-checklist
  - sre
  - reliability
category: practice
milestones:
  - Write a production readiness checklist for your organisation
  - Review a real service against the checklist and identify gaps
  - >-
    Define service maturity levels (e.g. alpha, beta, production) and what each
    requires
  - Run a production readiness review before a major launch
title_zh: "生产就绪"

---


A new service is ready for production when it meets a defined set of criteria — not when it passes its first deployment, not when it "looks good," but when it can be demonstrably shown to satisfy a standard that your organization has agreed on. Production readiness is the practice of making that standard explicit, reviewing services against it before they launch, and using it to continuously improve existing services. It's the organizational answer to "how do we know we're ready?"

<!-- DEEP_DIVE -->

## Why production readiness reviews exist

Without a standard, "production ready" means whatever the deploying engineer decided it means on the day they shipped. Some services launch with comprehensive monitoring and runbooks. Others go live with no alerting and no clear owner. The difference isn't malice — it's the absence of a defined bar.

A Production Readiness Review (PRR) is a structured assessment of whether a service meets that bar before it handles real user traffic. Google SRE introduced the practice as a way for SRE teams to decide whether to accept support responsibility for a new service. But the practice has value even without a dedicated SRE function: it forces teams to think through operational concerns before deployment rather than after the first incident.

## What a production readiness checklist covers

A good PRR checklist covers the key failure modes and operational requirements:

**Observability**
- Are there dashboards showing the key SLIs (latency, error rate, availability)?
- Are logs structured and searchable?
- Is distributed tracing instrumented?
- Are metrics labeled with enough context to diagnose issues?

**Alerting and on-call**
- Is there an on-call rotation assigned to this service?
- Are alerts defined for the SLOs?
- Do all alerts have associated runbooks?
- Has the on-call team been briefed on the service?

**SLOs**
- Is there a defined SLO for the service?
- Is it being measured and dashboarded?
- Is there an error budget policy in place?

**Reliability**
- Is the service deployed with redundancy (multi-instance)?
- Does the service handle dependency failures gracefully (timeouts, circuit breakers)?
- Has a load test validated capacity assumptions?
- Is there a rollback procedure documented and tested?

**Operations**
- Are there runbooks for the most common failure modes?
- Is the deployment process automated and reproducible?
- Is there an incident response playbook?

**Security**
- Are secrets managed through a secrets manager (not hardcoded or in environment variables)?
- Is authentication and authorization implemented correctly?
- Has the service been reviewed for OWASP top 10 vulnerabilities?

## Service maturity levels

Rather than a binary ready/not-ready, some organizations define maturity levels:

**Alpha / Internal**: service is functional, being used internally, observability and alerting are incomplete. Not customer-facing.

**Beta**: service is customer-facing but with explicit limitations. SLOs are defined but commitments are relaxed. On-call exists but may be shared.

**Production**: full PRR passed. SLOs are enforced. On-call is dedicated. All checklist items are met.

**Mature**: the service has operated in production for enough time to have well-calibrated SLOs, tested runbooks, and demonstrated reliability.

## Making it stick

A PRR only works if it has organizational teeth. If teams can skip it or if the bar is never enforced, it becomes a checkbox exercise. Two practices that help:

**Gate deployment or customer access**: services don't become customer-facing until they've passed the PRR. This can be enforced via feature flags, deployment approvals, or explicit sign-off.

**Make it a collaboration, not an audit**: the PRR should be a conversation between the service team and the SRE or platform team. The goal is to help the service team meet the bar, not catch them failing. Framed correctly, teams want to do PRRs because they've seen what happens to services that skip them.

<!-- RESOURCES -->

- [Google SRE Book - Production Readiness Review](https://sre.google/workbook/service-introduction/) -- type: book, time: 20m
- [Production Readiness Checklist - GitHub Awesome Lists](https://github.com/mtdvio/going-to-production) -- type: reference, time: 30m

<!-- ZH_SUMMARY -->
一个新服务达到生产就绪状态，是当它满足一组已定义的标准时——不是当它通过首次部署时，不是当它“看起来不错”时，而是当能够明确证明它满足你组织已达成一致的标准时。生产就绪是这样一种实践：把该标准明确表达出来，在服务上线前依据它进行评审，并用它持续改进现有服务。这是组织层面对“我们怎么知道已经准备好了？”这一问题的回答。

<!-- ZH_DEEP_DIVE -->
## 为什么需要生产就绪评审

没有标准时，“生产就绪”的含义就取决于部署工程师在发布当天怎么想。有些服务上线时配备了完善的监控和运行手册，另一些则在没有告警、没有明确负责人的情况下直接上线。这种差异并非出于恶意——而是因为缺少一条明确的门槛。

生产就绪评审（Production Readiness Review，PRR）是一种结构化评估，用于判断服务在处理真实用户流量之前是否达到该门槛。Google SRE 引入这一实践，是为了让 SRE 团队决定是否接受为新服务承担支持责任。但即使没有专职的 SRE 职能，这一实践也有价值：它迫使团队在部署之前而非第一次故障之后，就把运维层面的问题想清楚。

## 生产就绪检查清单涵盖的内容

一份好的 PRR 检查清单应覆盖关键故障模式和运维要求：

**可观测性**
- 是否有展示关键 SLI（延迟、错误率、可用性）的仪表盘？
- 日志是否结构化且可搜索？
- 是否接入了分布式追踪？
- 指标是否带有足够的上下文标签以便诊断问题？

**告警与值班**
- 是否为该服务分配了值班轮换？
- 是否针对 SLO 定义了告警？
- 所有告警是否都配有对应的运行手册？
- 值班团队是否已了解该服务？

**SLO**
- 是否为该服务定义了 SLO？
- 是否在测量并通过仪表盘展示？
- 是否制定了错误预算策略？

**可靠性**
- 服务是否以冗余方式部署（多实例）？
- 服务是否能优雅地处理依赖故障（超时、熔断）？
- 是否通过负载测试验证了容量假设？
- 是否有记录在案并经过测试的回滚流程？

**运维**
- 是否为最常见的故障模式准备了运行手册？
- 部署流程是否自动化且可复现？
- 是否有事件响应手册？

**安全**
- 密钥是否通过密钥管理器管理（而非硬编码或放在环境变量中）？
- 身份认证与授权是否实现正确？
- 服务是否针对 OWASP Top 10 漏洞做过评审？

## 服务成熟度等级

有些组织不采用就绪/未就绪的二元判断，而是定义成熟度等级：

**Alpha / 内部**：服务可用，正在内部使用，可观测性和告警尚不完善。不面向客户。

**Beta**：服务面向客户，但有明确的限制。已定义 SLO，但承诺较为宽松。有值班安排，但可能是共享的。

**生产**：通过完整的 PRR。SLO 被强制执行。有专职值班。所有检查清单项均已满足。

**成熟**：服务已在生产环境运行足够长时间，SLO 经过良好校准，运行手册经过验证，可靠性得到证明。

## 如何让它真正落地

PRR 只有在组织层面具有约束力时才有效。如果团队可以跳过，或者门槛从未被强制执行，它就会沦为走过场。有两个做法有帮助：

**把部署或客户访问作为关卡**：服务在通过 PRR 之前不得面向客户。这可以通过功能开关、部署审批或明确的签字确认来强制执行。

**把它做成协作，而不是审计**：PRR 应该是服务团队与 SRE 或平台团队之间的对话。目标是帮助服务团队达到门槛，而不是抓他们的错。只要定位正确，团队会愿意做 PRR，因为他们见过跳过 PRR 的服务后来是什么下场。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 生产就绪评审](https://sre.google/workbook/service-introduction/) -- 类型: 书籍, 时长: 20m
- [生产就绪检查清单 - GitHub Awesome Lists](https://github.com/mtdvio/going-to-production) -- 类型: 参考, 时长: 30m

<!-- ZH_UI -->
1. 为你的组织编写一份生产就绪检查清单
2. 对照检查清单审查一个真实服务并找出差距
3. 定义服务成熟度级别（如 alpha、beta、production）及各自的要求
4. 在重大发布前进行生产就绪评审
