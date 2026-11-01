---
id: platform-engineering
title: Platform Engineering
zone: sre
edges:
  to:
    - id: golden-paths
      question: >-
        How do I make the right way to build a service the default — not
        something teams have to discover for themselves?
      detail: >-
        Teams are still starting from scratch and making the same mistakes. I
        want something where if you follow the path we've laid out, you
        automatically get CI/CD, observability, secrets management, and a
        proper on-call setup — without having to figure it all out yourself.
    - id: service-ownership
      question: >-
        All these tools are great. But when something breaks at 3am, who's
        actually responsible?
      detail: >-
        We have great tooling now, but when something goes wrong it's still
        unclear whose problem it is. The platform team gets pulled in, the
        product team says it's infra, infra says it's the app. Nobody has clear
        ownership and it slows everything down.
difficulty: 2
tags:
  - platform-engineering
  - idp
  - internal-developer-platform
  - developer-experience
  - self-service
  - dx
category: concept
milestones:
  - >-
    Explain the difference between a platform team and a traditional ops/infra
    team
  - Identify the top three things your engineers repeatedly set up from scratch
  - >-
    Understand what an Internal Developer Platform (IDP) is and what Backstage
    provides
  - >-
    Describe why the platform should be treated as a product with internal
    customers
title_zh: "平台工程"

---


Every time a developer joins your organization, they spend weeks figuring out how to set up CI/CD, how to wire up metrics, how to configure secrets, and how to get a service into production. Every team reinvents the same boilerplate. Every new service has a slightly different observability setup. Platform engineering is the practice of building an Internal Developer Platform — the shared infrastructure, tooling, and workflows that make all of this self-service. The platform team's job is to make the right way to build a service the easy way.

<!-- DEEP_DIVE -->

## The platform team's mandate

A platform team is fundamentally different from a traditional operations or infrastructure team. Traditional infra teams are service teams: developers submit requests, infra teams fulfill them. Platform teams build products: self-service capabilities that developers use without filing tickets.

The platform team's customers are internal developers. Their product is the infrastructure that developers use to build and run services. Like any product, it needs to be designed for its users, measured by adoption and developer satisfaction, and improved continuously.

The shift in mindset: from "we manage infrastructure for teams" to "we build tools that let teams manage their own infrastructure."

## What an IDP provides

An Internal Developer Platform (IDP) is the collection of tools, workflows, and standards that a platform team builds and maintains. It typically includes:

**Service scaffolding**: a way to create a new service that comes pre-configured with CI/CD, logging, metrics, tracing, secrets management, and an on-call setup. Developers don't configure these from scratch — they inherit them by using the service template.

**Self-service environments**: developers can provision staging environments, run integration tests, and deploy to production without needing platform team involvement.

**Deployment workflows**: standardized CI/CD pipelines that handle testing, building container images, security scanning, and deploying to Kubernetes. Developers write code; the pipeline handles everything else.

**Observability out of the box**: metrics, logs, and traces automatically collected and available in a shared dashboard without any developer configuration.

**Secret management**: a standard way to store and access secrets (API keys, database passwords) that's secure, auditable, and doesn't require developers to figure out Vault configuration from scratch.

## Backstage and catalog-based platforms

Backstage (originally developed by Spotify, now CNCF) has become the dominant open-source foundation for IDPs. It provides:

**Software catalog**: a searchable inventory of all services in the organization — who owns them, what their SLOs are, where their docs live, what's their deployment status. Solves the "who owns this service?" question permanently.

**Templates (Software Templates)**: scaffolding for new services, pre-configured with organizational standards. Click through a wizard, enter service name and owner, get a fully configured repository pushed to GitHub.

**TechDocs**: documentation living with the service code, rendered in the catalog. Keeps docs and code in sync.

**Plugins**: extensible ecosystem for integrating with PagerDuty, Datadog, ArgoCD, GitHub Actions, and dozens of other tools.

## The product mindset

The failure mode of platform teams is building for themselves rather than for their users. A platform that platform engineers understand perfectly but that developers find confusing has failed. Treat your internal platform like a product:

- Talk to developers about what slows them down
- Measure time-to-first-deployment for new services
- Run developer satisfaction surveys (NPS for internal tools is real)
- Prioritize improvements based on what developers actually struggle with, not what seems technically interesting

<!-- RESOURCES -->

- [Platform Engineering on Kubernetes - O'Reilly](https://www.oreilly.com/library/view/platform-engineering-on/9781617299322/) -- type: book, time: varies
- [Backstage Documentation](https://backstage.io/docs) -- type: tool, time: 2h
- [Team Topologies - Matthew Skelton and Manuel Pais](https://teamtopologies.com/book) -- type: book, time: varies
- [Internal Developer Platform - internaldeveloperplatform.org](https://internaldeveloperplatform.org/) -- type: guide, time: 30m

<!-- ZH_SUMMARY -->
每当有开发者加入你的组织，他们都要花上数周时间弄清楚如何搭建 CI/CD、如何接入指标、如何配置密钥，以及如何让服务进入生产环境。每个团队都在重复造同样的样板。每个新服务的可观测性配置都略有不同。平台工程就是构建内部开发者平台（Internal Developer Platform）的实践——即那些让这一切实现自助化的共享基础设施、工具和工作流。平台团队的职责，就是让构建服务的正确方式成为最省力的方式。

<!-- ZH_DEEP_DIVE -->
## 平台团队的使命

平台团队与传统的运维或基础设施团队有着本质区别。传统基础设施团队是服务型团队：开发者提交请求，基础设施团队负责满足。平台团队则构建产品：开发者无需提交工单即可使用的自助服务能力。

平台团队的客户是内部开发者。他们的产品是开发者用来构建和运行服务的基础设施。与任何产品一样，它需要为用户而设计，以采用率和开发者满意度来衡量，并持续改进。

思维方式的转变：从“我们为团队管理基础设施”到“我们构建工具，让团队管理自己的基础设施”。

## IDP 提供什么

内部开发者平台（IDP）是平台团队构建和维护的工具、工作流和标准的集合。它通常包括：

**服务脚手架**：一种创建新服务的方式，预配置了 CI/CD、日志、指标、追踪、密钥管理和 on-call 设置。开发者无需从零配置这些内容——他们通过使用服务模板来继承这些配置。

**自助式环境**：开发者可以自行开通预发布环境、运行集成测试并部署到生产环境，无需平台团队介入。

**部署工作流**：标准化的 CI/CD 流水线，负责处理测试、构建容器镜像、安全扫描以及部署到 Kubernetes。开发者编写代码；流水线处理其余一切。

**开箱即用的可观测性**：指标、日志和追踪自动收集，并在共享仪表板中可用，开发者无需任何配置。

**密钥管理**：一种存储和访问密钥（API 密钥、数据库密码）的标准方式，安全、可审计，且无需开发者从零摸索 Vault 配置。

## Backstage 与基于目录的平台

Backstage（最初由 Spotify 开发，现为 CNCF 项目）已成为 IDP 的主流开源基础。它提供：

**软件目录**：组织中所有服务的可搜索清单——谁负责、SLO 是什么、文档在哪里、部署状态如何。永久解决“这个服务归谁管？”的问题。

**模板（软件模板）**：新服务的脚手架，预配置了组织标准。通过向导点击操作，输入服务名称和负责人，即可获得一个完整配置的仓库并推送到 GitHub。

**TechDocs**：文档与服务代码放在一起，在目录中渲染。保持文档与代码同步。

**插件**：可扩展的生态系统，用于集成 PagerDuty、Datadog、ArgoCD、GitHub Actions 以及数十种其他工具。

## 产品思维

平台团队的失败模式是为自己而构建，而非为用户而构建。一个平台工程师完全理解、但开发者觉得困惑的平台是失败的。像对待产品一样对待你的内部平台：

- 与开发者交流是什么拖慢了他们的工作
- 衡量新服务从创建到首次部署的时间
- 开展开发者满意度调查（内部工具的 NPS 是真实有效的）
- 根据开发者实际遇到的困难来排定改进优先级，而非根据技术上看起来有趣的内容

<!-- ZH_RESOURCES -->
- [Platform Engineering on Kubernetes - O'Reilly](https://www.oreilly.com/library/view/platform-engineering-on/9781617299322/) -- 类型：书籍，时长：不定
- [Backstage Documentation](https://backstage.io/docs) -- 类型：工具，时长：2小时
- [Team Topologies - Matthew Skelton and Manuel Pais](https://teamtopologies.com/book) -- 类型：书籍，时长：不定
- [Internal Developer Platform - internaldeveloperplatform.org](https://internaldeveloperplatform.org/) -- 类型：指南，时长：30分钟

<!-- ZH_UI -->
1. 解释平台团队与传统运维/基础设施团队的区别
2. 找出工程师反复从零搭建的前三件事
3. 理解什么是内部开发者平台（IDP）以及 Backstage 提供了什么
4. 说明为什么平台应被视为面向内部客户的产品
5. 如何让正确的服务构建方式成为默认路径——而不是让团队自己去摸索？
6. 团队仍在从零开始并重复同样的错误。我希望有这样的东西：只要遵循我们铺好的路径，就能自动获得 CI/CD、可观测性、密钥管理和完善的值班安排——无需自己从头摸索。
7. 这些工具都很好。但凌晨三点出问题时，到底谁负责？
8. 我们现在有很好的工具，但出问题时仍然不清楚是谁的问题。平台团队被拉进来，产品团队说是基础设施的问题，基础设施团队说是应用的问题。没有人有明确的归属，一切都变慢了。
