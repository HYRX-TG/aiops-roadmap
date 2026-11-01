---
id: golden-paths
title: Golden Paths and Templates
zone: sre
edges:
  to:
    - id: production-readiness
      question: >-
        Golden paths make it easy to start correctly. How do I ensure services
        stay correct as they evolve?
      detail: >-
        Golden paths set you up right at day zero. Production readiness reviews
        and service maturity models enforce standards at launch and as services
        grow. Together, they're the carrot (easy to do the right thing) and the
        stick (can't ship without meeting the bar).
difficulty: 2
tags:
  - golden-paths
  - templates
  - scaffolding
  - developer-experience
  - platform-engineering
  - backstage
category: practice
milestones:
  - Identify the golden path for creating a new service in your organisation
  - 'Build or adopt a service template with CI/CD, logging, and metrics pre-wired'
  - 'Measure adoption: what percentage of new services follow the golden path?'
  - Understand the tension between opinionated defaults and team autonomy
title_zh: "黄金路径与模板"

---


A golden path is the paved road through your infrastructure — the set of defaults, templates, and workflows that let a developer create a new service correctly without having to figure out CI/CD, observability, secrets management, and Kubernetes configuration from scratch. The term comes from the idea of the "path of least resistance": if you make the right way to do something easy, most people will do it the right way. Golden paths are how platform teams scale their influence across the entire engineering organization.

<!-- DEEP_DIVE -->

## The problem golden paths solve

Without golden paths, every team builds from scratch. Team A sets up CI/CD using their own YAML. Team B copies what they remember from a previous job. Team C asks someone from Team A to help them. Three months later: three different CI/CD configurations, three different approaches to secrets management, three different log formats, three different alert setups — none of them talking to each other in a unified dashboard.

The platform team can't maintain consistency by reviewing every team's work. They don't have the capacity. Golden paths are the alternative: build the infrastructure once, package it into a template, and let every team benefit from it.

## What a golden path includes

A good golden path gives you, for the price of filling out a form or running a CLI command:

**A repository structure**: with the right directory layout, README template, `.gitignore`, and initial code structure for your organization's primary language.

**CI/CD pipeline**: pre-configured to run tests, build a container image, scan for vulnerabilities, and deploy through your organization's deployment process. Developers don't write CI/CD — they get it.

**Observability wiring**: the application sends metrics to Prometheus (or Datadog, or CloudWatch), logs in structured JSON to the central logging system, and traces are collected by the tracing agent. This is wired in at the framework level — developers get it without configuring it.

**A Kubernetes deployment manifest**: with sensible defaults for resource limits, liveness and readiness probes, and pod disruption budgets. Developers adjust the values; they don't build the structure.

**Secrets management integration**: the service is pre-wired to read secrets from Vault (or AWS Secrets Manager, or GCP Secret Manager). Developers don't write the integration code.

**An SLO dashboard**: pre-built for the service's standard SLIs, visible in the catalog from day one.

## Opinionated defaults vs flexibility

Golden paths are opinionated. They make choices — which logging library, which tracing framework, which Kubernetes patterns — so that developers don't have to. This is both the value and the tension.

Teams that want to deviate from the golden path should be able to, but they should have to make an active choice to do so. The default is the path. The path is optimized for the platform team's ability to support it, not for maximum flexibility. A service that's on the golden path can be debugged, monitored, and operated by anyone. A service that's custom all the way down can only be operated by the people who built it.

## Measuring adoption

A golden path that nobody uses hasn't solved anything. Track adoption explicitly:
- What percentage of new services are created using the golden path template?
- What's the time-to-first-deployment for new services on the path vs off it?
- How many support tickets do teams that use the path generate vs teams that don't?

When a team goes off-path and struggles, understand why. Sometimes the golden path is missing a capability that teams need. Sometimes the path is poorly documented. Sometimes the team has a legitimate specialized requirement. The feedback loop between teams and the golden path improves the path.

<!-- RESOURCES -->

- [Spotify's Engineering Blog on Golden Paths](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem/) -- type: article, time: 15m
- [Backstage Software Templates](https://backstage.io/docs/features/software-templates/) -- type: tool, time: 30m
- [Platform Engineering on Kubernetes - O'Reilly](https://www.oreilly.com/library/view/platform-engineering-on/9781617299322/) -- type: book, time: varies

<!-- ZH_SUMMARY -->
黄金路径是贯穿基础设施的铺就之路——一套默认配置、模板和工作流，让开发者无需从零摸索 CI/CD、可观测性、密钥管理和 Kubernetes 配置，就能正确地创建新服务。这个术语源自"最小阻力路径"的理念：如果你把做某件事的正确方式变得简单，大多数人就会用正确的方式去做。黄金路径正是平台团队将其影响力扩展到整个工程组织的方式。

<!-- ZH_DEEP_DIVE -->
## 黄金路径解决的问题

没有黄金路径，每个团队都从零开始构建。团队 A 用自己写的 YAML 搭建 CI/CD。团队 B 照搬自己记得的上份工作的做法。团队 C 请团队 A 的人来帮忙。三个月后：三套不同的 CI/CD 配置、三种不同的密钥管理方式、三种不同的日志格式、三套不同的告警设置——它们没有一个能在统一仪表盘里互相对接。

平台团队无法通过审查每个团队的工作来维持一致性。他们没有这个精力。黄金路径是替代方案：把基础设施构建一次，打包成模板，让每个团队从中受益。

## 黄金路径包含什么

一条好的黄金路径，只需填一张表单或运行一条 CLI 命令，就能为你提供：

**仓库结构**：包含正确的目录布局、README 模板、`.gitignore`，以及针对你组织主要语言的初始代码结构。

**CI/CD 流水线**：预先配置好运行测试、构建容器镜像、扫描漏洞，并通过你组织的部署流程进行部署。开发者不用写 CI/CD——他们直接获得。

**可观测性接入**：应用将指标发送到 Prometheus（或 Datadog、或 CloudWatch），日志以结构化 JSON 发送到中央日志系统，链路追踪由追踪代理收集。这些在框架层面就已接好——开发者无需配置即可获得。

**Kubernetes 部署清单**：带有资源限制、存活探针和就绪探针、Pod 中断预算的合理默认值。开发者调整数值；他们不用构建结构。

**密钥管理集成**：服务已预先接好，可从 Vault（或 AWS Secrets Manager、或 GCP Secret Manager）读取密钥。开发者不用写集成代码。

**SLO 仪表盘**：针对服务的标准 SLI 预先构建，从第一天起就在目录中可见。

## 有主见的默认值与灵活性

黄金路径是有主见的。它们做出选择——用哪个日志库、哪个追踪框架、哪些 Kubernetes 模式——这样开发者就不必做这些选择。这既是价值所在，也是张力所在。

想要偏离黄金路径的团队应该能够这样做，但他们必须主动做出这个选择。默认就是走这条路径。这条路径的优化目标是平台团队支持它的能力，而不是最大灵活性。走黄金路径的服务，任何人都能调试、监控和运维。一个从头到尾都是定制的服务，只有构建它的人才能运维。

## 衡量采用情况

没人使用的黄金路径没有解决任何问题。要明确跟踪采用情况：
- 新服务中使用黄金路径模板创建的比例是多少？
- 走路径与不走路径的新服务，首次部署时间分别是多少？
- 使用路径的团队与不使用的团队，各自产生多少支持工单？

当一个团队偏离路径并陷入困境时，要理解原因。有时是黄金路径缺少团队需要的能力。有时是路径文档写得不好。有时是团队有合理的特殊需求。团队与黄金路径之间的反馈回路会改进这条路径。

<!-- ZH_RESOURCES -->
- [Spotify 工程博客：Golden Paths](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem/) -- 类型：文章，时长：15m
- [Backstage 软件模板](https://backstage.io/docs/features/software-templates/) -- 类型：工具，时长：30m
- [Kubernetes 上的平台工程 - O'Reilly](https://www.oreilly.com/library/view/platform-engineering-on/9781617299322/) -- 类型：书籍，时长：不定

<!-- ZH_UI -->
1. 识别组织中创建新服务的黄金路径
2. 构建或采用预置 CI/CD、日志和指标的服务模板
3. 衡量采用率：新服务遵循黄金路径的比例是多少？
4. 理解有主见的默认配置与团队自主权之间的张力
5. 黄金路径让正确起步变得容易。如何确保服务在演进过程中保持正确？
6. 黄金路径在第零天就让你走上正轨。生产就绪评审和服务成熟度模型在发布时及服务成长过程中强制执行标准。二者结合，就是胡萝卜（容易做正确的事）和大棒（不达标就不能发布）。
