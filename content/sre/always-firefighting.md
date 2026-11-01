---
id: always-firefighting
title: Always Firefighting
zone: sre
edges:
  to:
    - id: what-is-sre
      question: >-
        Is there a more systematic way to handle this than just hiring more
        people and hoping it gets better?
      detail: >-
        Every incident we patch something, add another alert, write a note
        somewhere. But we're back in the same cycle two weeks later. It feels
        like we're treating symptoms, not the root cause. There has to be a
        fundamentally better way to think about running software in production.
difficulty: 1
tags:
  - sre
  - reliability
  - ops
  - incidents
  - firefighting
  - culture
category: concept
milestones:
  - Identify the patterns that lead to permanent firefighting mode
  - Understand why adding more ops headcount doesn't solve the root problem
  - Recognize the dev/ops divide and its consequences for reliability
  - Know the cost of poor reliability — churn, trust erosion, engineering morale
title_zh: "永远在救火"

---


Every ops team hits this wall eventually. You're not building anymore — you're just surviving. Something breaks, you fix it, something else breaks. The cycle repeats. Your backlog is a graveyard of intentions: projects you meant to do, improvements you planned to make, the automation you keep promising yourself you'll write next week. Next week never comes. This isn't bad luck or a staffing problem. It's the predictable outcome of scaling complexity without scaling the systems for managing it.

<!-- DEEP_DIVE -->

## Why the fires never stop

The firefighting trap has a specific shape. Early on, the team is small and the system is simple. Everyone knows everything. When something breaks, the right person fixes it fast. Then the system grows. New services, new dependencies, new failure modes. But the team's operating model doesn't change — you still rely on heroics, institutional knowledge, and whoever is available. The fires start taking longer to put out. Then they start overlapping.

Adding more people is the instinctive response, but it doesn't solve the underlying problem. More people means more services to own, more alerts to triage, more incidents to manage. The workload expands to fill the headcount. You end up with a bigger team that's just as overwhelmed, plus the coordination overhead of a bigger team.

## The dev/ops divide

In most organizations, the team that builds software and the team that runs it are different people. Developers optimize for shipping features fast. Operations optimizes for keeping things stable. These incentives conflict by design. Developers throw code over the wall; operations catches whatever breaks. Neither team has the full picture. Developers don't feel the pain of running bad code in production. Operations doesn't have the context to fix the underlying problems. So both teams are stuck: developers keep shipping things that break, operations keeps fixing the same classes of problems over and over.

The result: operations is reactive by nature. You respond to what happened. You don't have the time, context, or authority to prevent the next thing.

## What reliability actually costs

Poor reliability isn't just an operational headache — it's a business cost that's easy to underestimate. Every major incident erodes trust. Customers who get burned once start looking for alternatives. Support tickets spike, which costs money. Engineers who spend their nights and weekends on-call burn out and leave. The knowledge walks out the door with them, which makes the next incident worse.

There's also the hidden cost of interruptions. An engineer who gets paged at 2 AM loses not just two hours — they lose the next day's focus too. Studies on cognitive interruption show that context-switching between deep work and incident response has a compounding cost that doesn't show up in any on-call report.

## The pattern that escapes this

The escape isn't working harder or hiring faster. It's changing the model. Organizations that stop firefighting permanently share a few traits: they measure reliability in terms that connect to user impact, they have a shared understanding between development and operations about what "working well enough" means, and they treat operational work as engineering work — something to be systematically reduced, not just staffed.

That's the discipline this zone is about. Not more firefighting, but fewer fires — and a systematic way to make that happen.

<!-- RESOURCES -->

- [Google SRE Book - Introduction](https://sre.google/sre-book/introduction/) -- type: book, time: 30m
- [The Calculus of Service Availability - Google](https://queue.acm.org/detail.cfm?id=3096459) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
每个运维团队最终都会撞上这堵墙。你不再是在建设，只是在勉强维持。某个东西坏了，你修好它，另一个东西又坏了。循环往复。你的待办事项列表成了一片意图的坟场：你想做的项目、你计划做的改进、你一直承诺下周要写的自动化。下周永远不会到来。这不是运气不好，也不是人手问题。这是在扩展复杂度的同时没有扩展管理复杂度的系统所导致的必然结果。

<!-- ZH_DEEP_DIVE -->
## 为什么火永远扑不完

救火陷阱有其特定的形态。早期，团队规模小，系统简单，每个人都了解所有事情。出问题时，合适的人能迅速修复。然后系统开始增长：新服务、新依赖、新故障模式。但团队的运作模式没有改变——你仍然依赖英雄主义、机构知识和谁有空谁上。灭火开始耗时更长，然后开始重叠。

增加人手是本能反应，但并不能解决根本问题。更多人意味着更多服务要负责、更多告警要分诊、更多事件要管理。工作量会膨胀到填满人头数。最终你得到一个更大的团队，同样不堪重负，还要加上更大团队带来的协调开销。

## 开发/运维的割裂

在大多数组织中，构建软件的团队和运行软件的团队是不同的人。开发者优化的是快速交付功能。运维优化的是保持稳定。这些激励在设计上就是冲突的。开发者把代码扔过墙；运维接住任何出问题的地方。两个团队都没有全貌。开发者感受不到在生产环境运行糟糕代码的痛苦。运维没有上下文去修复根本问题。于是两个团队都卡住了：开发者不断交付会出问题的东西，运维不断一遍又一遍地修复同一类问题。

结果：运维本质上是反应式的。你响应已经发生的事情。你没有时间、上下文或权限去预防下一件事。

## 可靠性真正的代价

可靠性差不仅仅是运维上的头疼——它是一项容易被低估的业务成本。每一次重大事故都会侵蚀信任。被伤害过一次的客户开始寻找替代方案。支持工单激增，这要花钱。花夜晚和周末值班的工程师会倦怠并离开。知识随他们一起走出门，这让下一次事故更糟。

还有中断的隐性成本。凌晨2点被呼叫的工程师失去的不只是两个小时——他们还失去了第二天的专注力。关于认知中断的研究表明，在深度工作和事件响应之间切换上下文有一种复合成本，这不会出现在任何值班报告里。

## 逃离这一切的模式

出路不是更努力地工作或更快地招人。而是改变模式。永久停止救火的组织有几个共同特征：他们用与用户影响相关联的方式来衡量可靠性，开发和运维之间对“足够好地运行”意味着什么有共同理解，他们把运维工作当作工程工作——系统性地减少它，而不仅仅是给它配人。

这就是本专区所讲的纪律。不是更多的救火，而是更少的火灾——以及一种系统化的方式来实现它。

<!-- ZH_RESOURCES -->
- [Google SRE 手册 - 简介](https://sre.google/sre-book/introduction/) -- 类型：书籍，时长：30分钟
- [服务可用性的计算 - Google](https://queue.acm.org/detail.cfm?id=3096459) -- 类型：文章，时长：20分钟

<!-- ZH_UI -->
1. 识别导致永久救火模式的模式
2. 理解为什么增加运维人员不能解决根本问题
3. 认识开发/运维鸿沟及其对可靠性的影响
4. 了解可靠性差的代价——人员流失、信任侵蚀、工程士气
5. 有没有比单纯增加人手并寄希望于情况好转更系统化的处理方式？
6. 每次事故我们都打补丁、加告警、在某处写备注。但两周后又回到同样的循环。感觉我们在治标不治本。必须有一种从根本上更好的方式来思考生产环境中的软件运行。
