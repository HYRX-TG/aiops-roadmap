---
id: what-is-ci-cd
title: What Is CI/CD?
zone: delivery
edges:
  to:
    - id: github-actions
      question: I get it. How do I actually build a pipeline?
      detail: >-
        GitHub Actions is the most approachable place to start. It's free for
        public repos, built into GitHub, and uses a simple YAML syntax to define
        what runs when you push code.
difficulty: 1
tags:
  - ci-cd
  - continuous-integration
  - continuous-delivery
  - pipelines
  - automation
category: concept
milestones:
  - >-
    Explain the difference between Continuous Integration and Continuous
    Delivery
  - Describe what a pipeline stage is
  - Understand why fast feedback loops matter
title_zh: "什么是 CI/CD？"

---


CI/CD stands for Continuous Integration and Continuous Delivery. CI means every code commit automatically triggers a build and test run. CD means passing code automatically gets delivered to production (or staged there, ready to deploy with one click).

Together they replace the manual deploy ritual with a pipeline: push to Git, tests run, image builds, deployment happens — no one SSHes into anything.

<!-- DEEP_DIVE -->

## Continuous Integration

The "integration" problem is old: multiple engineers working on the same codebase tend to diverge. Their branches work individually but break when merged. CI solves this by integrating constantly — every push triggers an automated build and test run.

If it passes: the code is good, move on.
If it fails: you know immediately, while the context is fresh, not three weeks later.

The discipline is: **the main branch is always green.** Small, frequent commits. Tests run on every push. Broken builds get fixed before anything else.

## Continuous Delivery

Delivery is getting that tested code to production. CD means the pipeline doesn't stop at "tests pass" — it keeps going. Build the artifact, push it to a registry, deploy to staging, run smoke tests, promote to production.

There's a distinction between Continuous Delivery and Continuous Deployment:
- **Continuous Delivery** — the pipeline prepares a deployment, but a human approves the final push to production.
- **Continuous Deployment** — everything is automatic, no human in the loop. Every green commit reaches production.

Most organizations start with Continuous Delivery (human approval for production) and move toward Continuous Deployment as they build confidence in their test coverage and rollback mechanisms.

## The pipeline

A pipeline is a sequence of automated stages. Each stage can fail, which stops the pipeline and notifies the team. A typical pipeline:

```
push → install deps → run tests → build image → push to registry → deploy to staging → smoke test → deploy to production
```

Each arrow represents a stage. If tests fail, nothing after that runs. You never push a broken image to production.

## Why fast feedback loops matter

The further a bug travels from where it was written, the more expensive it is to fix. A failing test in CI costs five minutes. The same bug discovered by a user costs an incident, a rollback, and a post-mortem.

Fast feedback — tests that run in seconds, pipelines that complete in minutes — keeps bugs cheap. Slow feedback keeps bugs expensive.

<!-- RESOURCES -->

- [CI/CD Overview (Atlassian)](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment) -- type: reference, time: 10min
- [The Twelve-Factor App: Build, Release, Run](https://12factor.net/build-release-run) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
CI/CD 代表持续集成与持续交付。CI 意味着每次代码提交都会自动触发构建和测试运行。CD 意味着通过测试的代码会自动交付到生产环境（或暂存到那里，一键即可部署）。

二者共同用流水线取代了手动部署仪式：推送到 Git、运行测试、构建镜像、执行部署——无需任何人 SSH 登录到任何机器。

<!-- ZH_DEEP_DIVE -->
## 持续集成

“集成”问题由来已久：多个工程师在同一个代码库上工作时，往往会产生分歧。他们的分支各自能正常工作，但合并时就会出问题。CI 通过持续集成来解决这个问题——每次推送都会触发自动化的构建和测试运行。

如果通过：代码没问题，继续推进。
如果失败：你能立刻知道，此时上下文还新鲜，而不是三周之后才发现。

这条纪律是：**主分支始终保持绿色。** 小而频繁的提交。每次推送都运行测试。构建一旦失败，优先修复它，其他事情都往后排。

## 持续交付

交付是把经过测试的代码送到生产环境。CD 意味着流水线不会停在“测试通过”这一步——它会继续往下走。构建产物、推送到镜像仓库、部署到预发布环境、运行冒烟测试、晋级到生产环境。

持续交付与持续部署之间有一个区别：
- **持续交付**——流水线准备好一次部署，但由人工批准最终推送到生产环境。
- **持续部署**——一切自动化，没有人工介入。每一个绿色的提交都会到达生产环境。

大多数组织从持续交付（生产环境需人工批准）起步，随着对测试覆盖率和回滚机制建立起信心，逐步转向持续部署。

## 流水线

流水线是一系列自动化阶段。每个阶段都可能失败，失败会中止流水线并通知团队。一条典型的流水线：

```
push → install deps → run tests → build image → push to registry → deploy to staging → smoke test → deploy to production
```

每个箭头代表一个阶段。如果测试失败，后面的阶段都不会运行。你永远不会把有问题的镜像推送到生产环境。

## 为什么快速反馈循环很重要

缺陷离它被写下的地方越远，修复成本就越高。CI 中一个失败的测试只花五分钟。同一个缺陷被用户发现，则要付出一次事故、一次回滚和一次复盘的成本。

快速反馈——几秒内跑完的测试、几分钟内完成的流水线——让缺陷保持廉价。缓慢的反馈则让缺陷变得昂贵。

<!-- ZH_RESOURCES -->
- [CI/CD 概述（Atlassian）](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment) -- 类型：参考，时间：10 分钟
- [十二要素应用：构建、发布、运行](https://12factor.net/build-release-run) -- 类型：参考，时间：5 分钟

<!-- ZH_UI -->
1. 解释持续集成与持续交付的区别
2. 描述什么是流水线阶段
3. 理解为什么快速反馈循环很重要
4. 我明白了。那我实际该怎么构建流水线？
5. GitHub Actions 是最容易上手的起点。它对公开仓库免费，内置于 GitHub，并使用简单的 YAML 语法来定义推送代码时运行什么。
