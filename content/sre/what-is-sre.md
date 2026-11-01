---
id: what-is-sre
title: What Is SRE?
zone: sre
edges:
  to:
    - id: measuring-reliability
      question: >-
        We have alerts everywhere but things still feel unpredictable. How do
        I actually measure reliability properly?
      detail: >-
        We get paged when things are obviously broken. But I have no idea if
        we're trending better or worse over time. There's no shared definition
        of 'working well enough.' I feel like we're flying blind between
        incidents.
    - id: toil-and-automation
      question: >-
        Operations is drowning in manual work and it's not getting better. How
        do I fix that systematically?
      detail: >-
        Half the team's time goes to repetitive manual tasks — restarting
        services, running the same scripts, processing the same tickets every
        week. It's not making anything more reliable. I want a principled way
        to get this under control.
    - id: too-many-incidents
      question: >-
        We keep having incidents and I don't think we're handling them well.
        Where do I even start?
      detail: >-
        Something goes wrong and it's chaos every time — no clear process, no
        clear owner, everyone talking over each other. Then we patch it and move
        on. A week later it happens again. I want a real process, not just
        winging it every time.
difficulty: 1
tags:
  - sre
  - devops
  - site-reliability-engineering
  - toil
  - philosophy
  - culture
category: concept
milestones:
  - Explain the difference between SRE and traditional operations
  - Describe what Google meant by 'hire software engineers to do operations'
  - Understand why SRE is not just DevOps with a different name
  - 'Explain the core tension SRE manages: reliability vs feature velocity'
title_zh: "什么是 SRE？"

---


Site Reliability Engineering is the discipline Google invented when they realized that hiring traditional sysadmins to run internet-scale systems wasn't going to work. The core idea: software engineers should run software. Only people who can write code can automate away the operational work that would otherwise crush a team. SRE isn't just a job title or a team structure — it's a set of principles for how software-driven organizations should think about reliability as a product requirement, not an afterthought.

<!-- DEEP_DIVE -->

## The Google origin story

In 2003, Google VP of Engineering Ben Treynor Sloss was handed a production team and told to run it. He gave it to a group of software engineers with one mandate: you are responsible for the availability, latency, performance, efficiency, change management, monitoring, emergency response, and capacity planning of the products you run. That mandate became Site Reliability Engineering.

The insight was simple: if you hire software engineers to do operations, they will automate themselves out of the jobs they hate. They'll build tooling to eliminate repetitive work. They'll write code that makes the system more observable. They'll treat operational problems as engineering problems. This is fundamentally different from hiring people whose job is to operate the system — those people will keep operating it manually forever.

## SRE vs DevOps

DevOps and SRE are often compared because they're solving the same underlying problem: the dev/ops divide. But they approach it differently.

DevOps is a philosophy and culture change: tear down the wall between development and operations, make developers responsible for what they ship, create shared ownership. It deliberately doesn't prescribe how to implement that culture change.

SRE is a prescriptive implementation: here's a specific set of practices (SLOs, error budgets, toil reduction, blameless post-mortems) that Google found effective. Ben Treynor Sloss's own description: "SRE is what happens when you ask a software engineer to design an operations function."

The two are compatible. Many organizations describe their approach as "DevOps culture with SRE practices."

## The core tension SRE manages

The fundamental tension in software organizations is between reliability and velocity. More frequent deployments mean more opportunities to break things. More reliability work means fewer features shipped. Left unmanaged, this tension becomes a political fight: operations wants a feature freeze, product wants to ship faster, and no one is making principled decisions — just fighting.

SRE resolves this tension with a concrete mechanism: the **error budget**. If you define how unreliable your service is allowed to be (say, 0.1% of requests can fail), everything above 99.9% success is a budget you can spend on risk. Deploy fast and burn through it? Slow down until it recovers. Deploy conservatively and have budget left over? Ship more aggressively. The budget converts a political argument into an engineering decision.

## What SRE is not

SRE is not a rebrand of sysadmin. The SRE model explicitly expects engineers to spend at most 50% of their time on operational work — the rest goes to engineering projects that reduce that operational load. An SRE who spends 80% of their time on tickets and incidents is doing it wrong, and that's a management failure, not a personal one.

SRE is also not a silver bullet. The practices only work if there's organizational buy-in — particularly from product management, who needs to understand what error budgets mean for feature velocity. SRE without that relationship is just rebranded ops.

<!-- RESOURCES -->

- [Google SRE Book (free online)](https://sre.google/sre-book/table-of-contents/) -- type: book, time: varies
- [Google SRE Workbook (free online)](https://sre.google/workbook/table-of-contents/) -- type: book, time: varies
- [What is SRE? - Ben Treynor Sloss](https://landing.google.com/sre/interview/ben-treynor-sloss/) -- type: article, time: 15m
- [SRE vs DevOps - Google Cloud Blog](https://cloud.google.com/blog/products/gcp/sre-vs-devops-competing-standards-or-close-friends) -- type: article, time: 10m
- [The SRE Book Chapter 1 - Introduction](https://sre.google/sre-book/introduction/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
站点可靠性工程（Site Reliability Engineering）是 Google 发明的一门学科，当时他们意识到，雇佣传统系统管理员来运行互联网规模的系统行不通。核心理念是：软件工程师应当运行软件。只有能写代码的人，才能将那些原本会压垮团队的操作性工作自动化掉。SRE 不仅仅是一个职位名称或一种团队结构——它是一套原则，指导以软件驱动的组织如何将可靠性视为产品需求，而非事后补救。

<!-- ZH_DEEP_DIVE -->
## Google 的起源故事

2003 年，Google 工程副总裁 Ben Treynor Sloss 接手了一个生产团队，并被告知要负责运营它。他把这个团队交给了一群软件工程师，并下达了一条指令：你们要对自己所运行产品的可用性、延迟、性能、效率、变更管理、监控、应急响应和容量规划负责。这条指令后来成为了站点可靠性工程（Site Reliability Engineering）。

这个洞见很简单：如果你雇佣软件工程师来做运维，他们会把自己讨厌的工作自动化掉。他们会构建工具来消除重复性工作。他们会编写代码让系统更具可观测性。他们会把运维问题当作工程问题来处理。这与雇佣那些本职工作就是操作系统的人有着根本区别——那些人会永远手动操作下去。

## SRE 与 DevOps

DevOps 和 SRE 经常被拿来比较，因为它们解决的是同一个底层问题：开发与运维之间的鸿沟。但它们的切入方式不同。

DevOps 是一种理念和文化变革：推倒开发与运维之间的墙，让开发者对自己交付的东西负责，建立共同担责的文化。它刻意不规定如何实现这种文化变革。

SRE 则是一种规定性的实现方式：这里有一套具体的实践（SLO、错误预算、减少琐事、无指责事后复盘），是 Google 发现行之有效的。Ben Treynor Sloss 自己的描述是：“SRE 就是当你让一位软件工程师去设计运维职能时会发生的事情。”

两者是兼容的。许多组织将他们的做法描述为“DevOps 文化加 SRE 实践”。

## SRE 所管理的核心张力

软件组织中的根本张力在于可靠性（reliability）与速度（velocity）之间。更频繁的部署意味着更多出错的机会。更多的可靠性工作意味着更少的功能交付。如果放任不管，这种张力就会演变成政治斗争：运维想要功能冻结，产品想要更快交付，而没有人做出有原则的决策——只是在争吵。

SRE 用一种具体机制化解了这种张力：**错误预算**。如果你定义了服务被允许有多不可靠（比如，0.1% 的请求可以失败），那么高于 99.9% 成功率的部分就是你可以花在风险上的预算。快速部署把预算烧光了？那就放慢速度直到恢复。保守部署还有预算剩余？那就更激进地交付。预算把一场政治争论转化为了一个工程决策。

## SRE 不是什么

SRE 不是系统管理员的改头换面。SRE 模式明确期望工程师最多把 50% 的时间花在运维工作上——其余时间用于减少运维负载的工程项目。一个把 80% 时间花在工单和事故上的 SRE 是做错了，而这是管理层的失职，不是个人的问题。

SRE 也不是万能灵药。这些实践只有在组织上下都认同的情况下才有效——尤其是产品管理层，他们需要理解错误预算对功能交付速度意味着什么。没有这层关系的 SRE，不过是换了包装的运维。

<!-- ZH_RESOURCES -->
- [Google SRE 书（免费在线）](https://sre.google/sre-book/table-of-contents/) -- 类型：书籍，时长：不定
- [Google SRE 工作手册（免费在线）](https://sre.google/workbook/table-of-contents/) -- 类型：书籍，时长：不定
- [什么是 SRE？ - Ben Treynor Sloss](https://landing.google.com/sre/interview/ben-treynor-sloss/) -- 类型：文章，时长：15 分钟
- [SRE 与 DevOps - Google Cloud 博客](https://cloud.google.com/blog/products/gcp/sre-vs-devops-competing-standards-or-close-friends) -- 类型：文章，时长：10 分钟
- [SRE 书第 1 章 - 简介](https://sre.google/sre-book/introduction/) -- 类型：书籍，时长：20 分钟

<!-- ZH_UI -->
1. 解释 SRE 与传统运维的区别
2. 描述 Google 所说的“雇佣软件工程师来做运维”是什么意思
3. 理解为什么 SRE 不只是换了个名字的 DevOps
4. 解释 SRE 管理的核心矛盾：可靠性与功能迭代速度
5. 我们到处都是告警，但事情仍然感觉不可预测。我该如何真正正确地衡量可靠性？
6. 当事情明显出问题时我们会被呼叫。但我不知道我们的趋势是在变好还是变差。对“足够好地运行”没有共同的定义。我觉得我们在事件之间是在盲目飞行。
7. 运维淹没在手工工作中，而且情况没有好转。我该如何系统性地解决这个问题？
8. 团队一半的时间花在重复性手工任务上——重启服务、运行相同的脚本、每周处理相同的工单。这并没有让任何东西变得更可靠。我想要一种有原则的方式来控制这件事。
9. 我们不断发生事件，我认为我们处理得不好。我该从哪里开始？
10. 出问题时每次都一片混乱——没有清晰的流程，没有明确的负责人，大家互相抢话。然后我们打个补丁就继续。一周后又发生同样的事。我想要一个真正的流程，而不是每次都临时应付。
