---
id: dora-metrics
title: DORA Metrics
zone: sre
edges:
  to:
    - id: chaos-engineering
      question: >-
        I can measure that we're improving. But I still want to proactively
        find the weaknesses before users do.
      detail: >-
        DORA metrics tell me we're deploying more frequently and recovering
        faster. But every incident is still a surprise. I want to go beyond
        measuring improvement and start actively hunting for what's going to
        break next — before it breaks in production.
difficulty: 2
tags:
  - dora
  - metrics
  - devops
  - sre
  - deployment-frequency
  - mttr
  - change-failure-rate
category: concept
milestones:
  - Define the four DORA metrics and what each measures
  - Instrument your delivery pipeline to collect deployment frequency and lead time
  - Know what "elite" vs "low" DORA performance looks like and what drives each
  - Understand why change failure rate and MTTR are the reliability-facing DORA metrics
title_zh: "DORA 指标"

---


DORA metrics are four measurements that tell you whether your engineering organization is performing well — not just individual services, but the whole delivery system. They came from the DevOps Research and Assessment team's research across thousands of organizations, and they've held up: these four metrics strongly predict organizational performance, both reliability and velocity. If you want to know whether your org is improving, these are the numbers to watch.

<!-- DEEP_DIVE -->

## The four DORA metrics

**Deployment Frequency** — How often does your organization successfully release to production? Elite organizations deploy on demand — multiple times per day. Low performers deploy once a month or less. This measures the health of your delivery pipeline: can you ship changes quickly when you need to?

**Lead Time for Changes** — How long does it take from code committed to code in production? Elite: less than one hour. Low performers: one to six months. This captures everything between commit and deploy: code review time, CI duration, manual approvals, deployment processes.

**Change Failure Rate** — What percentage of deployments cause a production incident requiring a rollback or hotfix? Elite performers: 0–15%. Low performers: 46–60%. This is the reliability-facing deployment metric. High change failure rate means your development and testing practices aren't catching problems before production.

**Time to Restore Service (MTTR)** — When a service incident occurs, how long does it take to recover? Elite: less than one hour. Low performers: one to six months (for the longest incidents). This captures the effectiveness of your incident detection, response, and resolution processes.

## Which metrics are reliability-facing

All four DORA metrics relate to reliability, but change failure rate and MTTR are the most directly connected.

**Change failure rate** tells you how often your deployments break things. Improving it requires: better automated testing, staged rollouts (canary, blue/green), feature flags that let you decouple deploy from release, and code review practices that catch defects earlier.

**MTTR** tells you how effective your incident response is. Improving it requires: better alerting that detects problems sooner, runbooks that enable faster diagnosis, and post-mortems that address root causes so the same incident doesn't recur.

## The tension between deployment frequency and change failure rate

High deployment frequency is good, but only if the change failure rate stays low. Organizations that ship frequently but break things constantly are trading velocity for stability. The goal is to increase deployment frequency without increasing change failure rate — and the key to that is progressive delivery (canary deployments, feature flags) and comprehensive automated testing.

Elite organizations achieve both: they deploy frequently and have low failure rates. This is not a coincidence — the practices that enable frequent deployment (automation, small changes, CI/CD) also reduce the blast radius of failures.

## Measuring DORA in practice

**Deployment Frequency**: count deployments to production per time period. Your CI/CD pipeline already has this data — the number of successful deployments to production.

**Lead Time**: timestamp of first commit to a branch vs. timestamp of merge to main. Requires integration with your version control system. Most CI/CD platforms or DORA-specific tools (LinearB, Sleuth, Faros) can calculate this.

**Change Failure Rate**: count deployments that caused an incident (defined as: required a rollback, hotfix, or incident declaration within some window, typically 1 hour of deployment). Manual tagging in your incident tracker, or automated correlation between deployments and incidents.

**MTTR**: timestamp of incident declaration to timestamp of resolution. Pull from your incident management tool (PagerDuty, OpsGenie).

<!-- RESOURCES -->

- [Accelerate: The Science of Lean Software and DevOps - Nicole Forsgren](https://itrevolution.com/accelerate-book/) -- type: book, time: varies
- [2023 State of DevOps Report - Google Cloud + DORA](https://dora.dev/research/2023/dora-report/) -- type: report, time: 1h
- [DORA Metrics - How to Measure - LinearB](https://linearb.io/blog/dora-metrics) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
DORA 指标是四项衡量标准，用于判断你的工程组织整体表现是否良好——不仅针对单个服务，而是整个交付系统。它们源自 DevOps Research and Assessment 团队对数千个组织的研究，并且经受住了检验：这四项指标能有力预测组织绩效，既包括可靠性也包括速度。如果你想知道你的组织是否在进步，这些就是值得关注的数字。

<!-- ZH_DEEP_DIVE -->
## 四个 DORA 指标

**部署频率** — 你的组织成功发布到生产环境的频率有多高？精英组织按需部署——每天多次。低绩效者每月部署一次或更少。这衡量的是你的交付流水线的健康度：当你需要时，你能快速发布变更吗？

**变更前置时间** — 从代码提交到代码进入生产环境需要多长时间？精英：少于一小时。低绩效者：一到六个月。这涵盖了从提交到部署之间的一切：代码审查时间、CI 持续时间、手动审批、部署流程。

**变更失败率** — 有多少比例的部署会导致需要回滚或热修复的生产事故？精英绩效者：0–15%。低绩效者：46–60%。这是面向可靠性的部署指标。高变更失败率意味着你的开发和测试实践未能在生产环境之前捕获问题。

**服务恢复时间（MTTR）** — 当服务事故发生时，恢复需要多长时间？精英：少于一小时。低绩效者：一到六个月（针对最长的事故）。这衡量的是你的事故检测、响应和解决流程的有效性。

## 哪些指标面向可靠性

所有四个 DORA 指标都与可靠性相关，但变更失败率和 MTTR 是最直接相关的。

**变更失败率**告诉你部署破坏事物的频率。改进它需要：更好的自动化测试、分阶段发布（金丝雀、蓝/绿）、让你将部署与发布解耦的功能开关，以及更早捕获缺陷的代码审查实践。

**MTTR**告诉你事故响应的有效性。改进它需要：更早检测问题的更好告警、支持更快诊断的运行手册，以及解决根本原因的事后复盘，使同一事故不再复发。

## 部署频率与变更失败率之间的张力

高部署频率是好的，但前提是变更失败率保持低位。频繁发布但不断破坏事物的组织是在用稳定性换取速度。目标是在不增加变更失败率的情况下提高部署频率——而关键在于渐进式交付（金丝雀部署、功能开关）和全面的自动化测试。

精英组织两者兼得：他们频繁部署且失败率低。这不是巧合——支持频繁部署的实践（自动化、小变更、CI/CD）也减少了故障的影响范围。

## 在实践中衡量 DORA

**部署频率**：统计每时间段内到生产环境的部署次数。你的 CI/CD 流水线已经有这些数据——成功部署到生产环境的次数。

**前置时间**：分支上首次提交的时间戳 vs. 合并到主分支的时间戳。需要与你的版本控制系统集成。大多数 CI/CD 平台或 DORA 专用工具（LinearB、Sleuth、Faros）可以计算这个。

**变更失败率**：统计导致事故的部署次数（定义为：在某个窗口内——通常是部署后 1 小时内——需要回滚、热修复或事故声明）。在你的事故跟踪器中手动打标签，或在部署与事故之间自动关联。

**MTTR**：事故声明的时间戳到解决的时间戳。从你的事故管理工具（PagerDuty、OpsGenie）中提取。

<!-- ZH_RESOURCES -->
- [Accelerate: The Science of Lean Software and DevOps - Nicole Forsgren](https://itrevolution.com/accelerate-book/) -- 类型: 书籍, 时长: 不定
- [2023 State of DevOps Report - Google Cloud + DORA](https://dora.dev/research/2023/dora-report/) -- 类型: 报告, 时长: 1小时
- [DORA Metrics - How to Measure - LinearB](https://linearb.io/blog/dora-metrics) -- 类型: 文章, 时长: 15分钟

<!-- ZH_UI -->
1. 定义四项 DORA 指标及其各自衡量的内容
2. 为你的交付流水线埋点，以采集部署频率和前置时间
3. 了解“精英”与“低”DORA 表现分别是什么样，以及各自由什么驱动
4. 理解为什么变更失败率和 MTTR 是面向可靠性的 DORA 指标
5. 我能衡量我们正在改进。但我仍想主动发现弱点，赶在用户之前。
6. DORA 指标告诉我，我们部署更频繁、恢复更快。但每次事故仍是意外。我想超越衡量改进，开始主动搜寻下一个会出问题的地方——在它在生产环境出问题之前。
