---
id: service-ownership
title: Service Ownership
zone: sre
edges:
  to:
    - id: production-readiness
      question: >-
        Ownership is assigned. But how do I make sure 'owning' a service means
        something consistent across teams?
      detail: >-
        Every team says they own their service, but what that means varies
        wildly. Some have runbooks and a real on-call rotation. Others just have
        a name in a spreadsheet. I need a standard for what being
        production-ready actually requires.
difficulty: 2
tags:
  - service-ownership
  - platform-engineering
  - on-call
  - team-topologies
  - sre
  - responsibility
category: concept
milestones:
  - Define what service ownership means in your organization
  - Assign clear on-call owners to all production services
  - Understand the "you build it, you run it" model and its tradeoffs
  - Establish an ownership transfer process for when teams hand off services
title_zh: "服务所有权"

---


When something breaks at 3 AM, who's responsible? In many organizations, the honest answer is "unclear." The platform team blames the product team. The product team blames infrastructure. Nobody has definitive ownership. Service ownership is the practice of assigning clear, named accountability for every production service — not just for on-call response, but for reliability, SLOs, operational health, and long-term maintenance. Without it, accountability is diffuse and nothing gets fixed properly.

<!-- DEEP_DIVE -->

## "You build it, you run it"

The most influential ownership model in modern software development came from Werner Vogels, Amazon's CTO: "You build it, you run it." Developers who build a service are responsible for running it in production. They carry the pager. They respond to incidents. They feel the pain of the operational decisions they made during development.

This model produces better software because the people making architectural decisions experience the consequences. A developer who has been paged at 3 AM because a connection pool wasn't sized correctly will never misconfigure that pool again. A team that deploys bad code and deals with the incident learns much faster than one that hands code over the wall.

The "you build it, you run it" model requires platform teams to make this possible without crushing developers. If every developer has to be a database expert and a Kubernetes expert and an observability expert, the model fails. The platform team exists to absorb that complexity.

## What ownership means in practice

Service ownership is more than having a name in a spreadsheet. A team that "owns" a service should be accountable for:

**Reliability**: the service meets its SLO. When it doesn't, the owning team is responsible for fixing the underlying cause, not just patching the symptom.

**On-call**: there's a functioning rotation for the service. When an alert fires, someone from the team responds within the defined SLA. Not the platform team, not whoever happens to be online — the owning team.

**Runbooks**: documentation exists for common failure modes. The on-call engineer can handle incidents using the runbook without needing to call the person who built the service.

**Capacity**: the owning team monitors and manages the service's capacity. They know when it will need to scale and take action before it hits limits.

**Dependencies**: the team knows what the service depends on, what happens when those dependencies fail, and has notified the dependency teams of their SLO requirements.

## Service catalog as the foundation

You can't manage service ownership without a service catalog — a central, authoritative list of every production service, its owner, and key metadata. This is the first thing to build.

Minimum catalog fields:
- Service name and ID
- Owning team
- Primary and secondary on-call contacts
- Links to: runbook, SLO dashboard, deployment pipeline, repository
- Criticality (used to prioritize during incidents)

Many organizations use Backstage for this. Others use a simple spreadsheet or Notion database. The format matters less than the discipline of keeping it current.

## Ownership transfers

Services outlive team assignments. Teams restructure, responsibilities shift, projects are handed off. Without an explicit transfer process, ownership becomes ambiguous: the old team thinks they've handed it off; the new team thinks the old team still owns it.

A service ownership transfer requires:
- An explicit handoff meeting where the new team is briefed on the service
- Updated catalog entry (new team, new contacts)
- On-call rotation updated in the alerting system
- Runbooks reviewed and updated
- A defined period of parallel coverage where both teams are available for questions

<!-- RESOURCES -->

- [Team Topologies - Matthew Skelton and Manuel Pais](https://teamtopologies.com/book) -- type: book, time: varies
- [You Build It, You Run It - Werner Vogels](https://queue.acm.org/detail.cfm?id=1142065) -- type: article, time: 15m
- [Service Ownership at Scale - Atlassian Blog](https://www.atlassian.com/incident-management/devops/you-build-it-you-run-it) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
凌晨3点出故障时，谁该负责？在许多组织中，诚实的答案是“不清楚”。平台团队怪产品团队，产品团队怪基础设施，没有人拥有明确的归属。服务所有权（Service ownership）是一种实践：为每一个生产服务指定清晰、具名的责任归属——不仅包括 on-call 响应，还包括可靠性、SLO、运行健康状况和长期维护。没有它，责任就会分散，什么问题都无法得到妥善解决。

<!-- ZH_DEEP_DIVE -->
## “你构建，你运行”

现代软件开发中最具影响力的归属模型来自 Amazon 的 CTO Werner Vogels：“你构建，你运行。”构建服务的开发者负责在生产环境中运行它。他们携带寻呼机。他们响应事故。他们感受自己在开发期间所做运维决策带来的痛苦。

这个模型能产出更好的软件，因为做架构决策的人会亲身体验后果。一个因为连接池配置不当而在凌晨 3 点被寻呼的开发者，再也不会把那个池配置错。一个部署了坏代码并处理事故的团队，比把代码甩手交给别人的团队学得快得多。

“你构建，你运行”模型要求平台团队在不压垮开发者的前提下让这一切成为可能。如果每个开发者都必须成为数据库专家、Kubernetes 专家和可观测性专家，这个模型就会失败。平台团队的存在就是为了吸收这种复杂性。

## 归属在实践中意味着什么

服务归属不仅仅是在电子表格里有个名字。一个“拥有”服务的团队应当对以下事项负责：

**可靠性**：服务满足其 SLO。当它不满足时，拥有团队负责修复根本原因，而不仅仅是修补症状。

**值班**：服务有正常运转的轮值机制。当告警触发时，团队中有人在定义的 SLA 内响应。不是平台团队，不是碰巧在线的人——而是拥有团队。

**运行手册**：针对常见故障模式存在文档。值班工程师可以使用运行手册处理事故，而无需打电话给构建该服务的人。

**容量**：拥有团队监控并管理服务的容量。他们知道何时需要扩容，并在触及限制之前采取行动。

**依赖**：团队知道服务依赖什么、这些依赖失败时会发生什么，并已将其 SLO 要求通知依赖团队。

## 服务目录作为基础

没有服务目录，就无法管理服务归属——服务目录是每个生产服务、其所有者及关键元数据的集中权威列表。这是首先要构建的东西。

最低限度的目录字段：
- 服务名称和 ID
- 拥有团队
- 主要和次要值班联系人
- 链接到：运行手册、SLO 仪表盘、部署流水线、代码仓库
- 关键性（用于在事故期间确定优先级）

许多组织为此使用 Backstage。其他组织使用简单的电子表格或 Notion 数据库。格式不如保持其最新的纪律重要。

## 归属转移

服务的生命周期长于团队分配。团队重组、职责转移、项目交接。没有明确的转移流程，归属就会变得模糊：旧团队以为他们已经交接了；新团队以为旧团队仍然拥有它。

服务归属转移需要：
- 一次明确的交接会议，向新团队介绍该服务
- 更新目录条目（新团队、新联系人）
- 在告警系统中更新值班轮值
- 审查并更新运行手册
- 一段定义的并行覆盖期，两个团队都可回答问题

<!-- ZH_RESOURCES -->
- [Team Topologies - Matthew Skelton and Manuel Pais](https://teamtopologies.com/book) -- 类型: 书籍, 时长: 不定
- [You Build It, You Run It - Werner Vogels](https://queue.acm.org/detail.cfm?id=1142065) -- 类型: 文章, 时长: 15分钟
- [Service Ownership at Scale - Atlassian Blog](https://www.atlassian.com/incident-management/devops/you-build-it-you-run-it) -- 类型: 文章, 时长: 10分钟

<!-- ZH_UI -->
1. 定义在你的组织中服务所有权意味着什么
2. 为所有生产服务分配明确的 on-call 负责人
3. 理解“you build it, you run it”模式及其权衡
4. 建立团队交接服务时的所有权转移流程
5. 所有权已分配。但如何确保“拥有”一个服务在各团队间含义一致？
6. 每个团队都说自己拥有服务，但含义千差万别。有些有 runbook 和真正的 on-call 轮值，另一些只是表格里的一个名字。我需要一个标准，明确达到生产就绪究竟需要什么。
