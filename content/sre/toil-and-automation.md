---
id: toil-and-automation
title: Toil and Automation
zone: sre
edges:
  to:
    - id: runbooks-and-playbooks
      question: >-
        Before I can automate any of this, I feel like I need to write down how
        we actually handle things. Where do I start?
      detail: >-
        Half of our operational knowledge lives in people's heads. When
        something breaks, whoever's on call figures it out from scratch every
        time. I want to capture that, but I've seen runbooks that are out of
        date the moment they're written — so what makes one actually useful?
difficulty: 2
tags:
  - toil
  - automation
  - sre
  - operational-work
  - on-call
  - efficiency
category: concept
milestones:
  - >-
    Define toil using the SRE definition: manual, repetitive, automatable,
    scales with traffic
  - Audit your current operational work and classify it as toil or not toil
  - Identify your top three sources of toil and pick one to automate
  - Understand the 50% toil cap and why exceeding it is unsustainable
title_zh: "繁琐工作与自动化"

---


Toil is the operational work that keeps systems running today but doesn't make them better tomorrow. Restarting services. Processing manual deployment requests. Running the same diagnostic script every week. Answering tickets that ask the same question. Every hour spent on toil is an hour not spent on engineering work that would reduce toil. Left unchecked, toil grows with scale — more services, more traffic, more toil — until it consumes the entire team.

<!-- DEEP_DIVE -->

## The SRE definition of toil

The Google SRE book gives toil a precise definition with six characteristics:

**Manual** — it requires a human to do it. Not automated, not running by itself.

**Repetitive** — you've done it before and will do it again. Not a one-off.

**Automatable** — a machine could do it with sufficient engineering investment.

**Reactive** — triggered by external events, not by the team's own planned work. Pages, tickets, customer requests.

**Scales with service growth** — more users or traffic means more toil, not the same amount. This is the key sign that toil is structural, not incidental.

**Low value** — toil keeps the lights on but doesn't improve the system. It has no cumulative benefit. Doing it today doesn't make tomorrow better.

Not all operational work is toil. Building a new monitoring dashboard is not toil — it has lasting value. Writing a runbook that will be used for years is not toil. Responding to a novel incident that teaches you something new is not toil. Toil is specifically the repetitive, low-value work that scales with the system.

## The 50% toil cap

Google SRE sets a firm limit: SREs should spend no more than 50% of their time on toil. The rest goes to engineering work — projects that reduce toil, improve reliability, or build new capabilities. This isn't a suggestion. If an SRE regularly exceeds 50% toil, that's a management problem — the team is being used as operational staff rather than engineers.

Why 50%? Below that threshold, toil is manageable and the team has time to invest in reducing it. Above it, toil crowds out the engineering work that would reduce toil, creating a death spiral: more toil → less time for automation → toil continues to grow → even less time for automation.

## Identifying and measuring toil

You can't manage what you don't measure. Start by auditing the operational work your team does over a two-week period:

1. List every recurring task — weekly, daily, or per-incident
2. Estimate the time per occurrence and frequency
3. Classify each as toil or legitimate engineering work
4. Calculate the total toil burden as a percentage of team capacity

Once you have the list, prioritize by impact: which toil takes the most time? Which is growing fastest? Which is most automatable? Pick one. Build the automation. Measure the reduction.

## What automation means in practice

Automation isn't always a sophisticated system. Sometimes it's:

- A script that runs the 15-step diagnostic process automatically
- A Kubernetes operator that handles the restart logic that on-call engineers do manually
- A runbook converted into a self-service form that developers can fill out without filing a ticket
- A pre-built dashboard that answers the three questions people always ask during incidents

The automation spectrum runs from "manual" to "fully automated with no human in the loop." You don't have to reach full automation to get value. A script that does 80% of the work and prompts a human for the last decision is dramatically better than 100% manual.

<!-- RESOURCES -->

- [Google SRE Book - Eliminating Toil](https://sre.google/sre-book/eliminating-toil/) -- type: book, time: 20m
- [Measuring and Reducing Toil - Google SRE Workbook](https://sre.google/workbook/toil-budgets/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
Toil 是维持系统当下运行、却无法让系统明天变得更好的运维工作。重启服务。处理手动部署请求。每周运行相同的诊断脚本。回答提出相同问题的工单。花在 toil 上的每一小时，都是没有花在能够减少 toil 的工程工作上的一小时。若不加以控制，toil 会随规模增长——更多服务、更多流量、更多 toil——直到它吞噬整个团队。

<!-- ZH_DEEP_DIVE -->
## SRE 对 toil 的定义

Google SRE 书籍为 toil 给出了精确的定义，包含六个特征：

**手动** —— 需要人来完成。不是自动化的，不能自行运行。

**重复** —— 你以前做过，以后还会再做。不是一次性的。

**可自动化** —— 只要有足够的工程投入，机器就能完成。

**被动响应** —— 由外部事件触发，而非团队自己计划的工作。告警、工单、客户请求。

**随服务增长而扩展** —— 更多用户或流量意味着更多 toil，而不是维持同样的量。这是 toil 属于结构性问题而非偶发问题的关键标志。

**低价值** —— toil 维持系统运转，但不改进系统。它没有累积收益。今天做了，明天不会更好。

并非所有运维工作都是 toil。构建新的监控仪表盘不是 toil——它具有持久价值。编写一份将使用多年的 runbook 不是 toil。响应一个让你学到新东西的新颖故障不是 toil。Toil 特指那些随系统扩展的、重复性的、低价值的工作。

## 50% 的 toil 上限

Google SRE 设定了一条硬性限制：SRE 花在 toil 上的时间不应超过 50%。其余时间用于工程工作——减少 toil、提升可靠性或构建新能力的项目。这不是建议。如果一名 SRE 经常超过 50% 的 toil，那就是管理问题——团队被当作运维人员而非工程师来使用。

为什么是 50%？低于这个阈值，toil 是可控的，团队有时间投入去减少它。高于这个阈值，toil 会挤占本可用于减少 toil 的工程工作，形成恶性循环：toil 越多 → 用于自动化的时间越少 → toil 持续增长 → 用于自动化的时间更少。

## 识别和度量 toil

你无法管理你没有度量的东西。首先审计团队在两周内所做的运维工作：

1. 列出每一项重复性任务——每周、每天或每次故障的
2. 估算每次发生的时间和频率
3. 将每项分类为 toil 或正当的工程工作
4. 计算 toil 总负担占团队容量的百分比

拿到清单后，按影响排序：哪项 toil 耗时最多？哪项增长最快？哪项最可自动化？选一个。构建自动化。度量减少量。

## 自动化在实践中意味着什么

自动化并不总是一套复杂的系统。有时它是：

- 一个自动运行 15 步诊断流程的脚本
- 一个处理 on-call 工程师手动执行的重启逻辑的 Kubernetes operator
- 一份转换为自助表单的 runbook，开发者无需提交工单即可填写
- 一个预构建的仪表盘，回答人们在故障期间总会问的三个问题

自动化光谱从“手动”延伸到“完全自动化、无需人工介入”。你不必达到完全自动化才能获得价值。一个完成 80% 工作并提示人做最后决策的脚本，远比 100% 手动要好得多。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 消除琐事](https://sre.google/sre-book/eliminating-toil/) -- 类型：书籍，时长：20分钟
- [衡量与减少琐事 - Google SRE 工作手册](https://sre.google/workbook/toil-budgets/) -- 类型：书籍，时长：20分钟

<!-- ZH_UI -->
1. 用 SRE 定义界定 toil：手动、重复、可自动化、随流量增长
2. 审计当前运维工作，将其分类为 toil 或非 toil
3. 找出 toil 的三大来源，并选一个进行自动化
4. 理解 50% toil 上限，以及为何超出后不可持续
5. 在自动化任何内容之前，我觉得需要先记录我们实际如何处理事情。该从哪里开始？
6. 我们一半的运维知识都在人们脑子里。出问题时，值班的人每次都要从头摸索。我想把这些知识沉淀下来，但我见过刚写完就过时的 runbook——那么什么才能让 runbook 真正有用？
