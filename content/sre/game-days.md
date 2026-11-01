---
id: game-days
title: Game Days
zone: sre
edges:
  to:
    - id: capacity-planning
      question: >-
        The team knows how to respond under pressure. What's the next proactive
        reliability concern?
      detail: >-
        GameDays have been great — people know the playbooks, roles, and
        escalation paths now. But I'm starting to think about whether we're
        actually sized correctly for what's coming. Recovery is covered. I want
        to make sure we don't hit a wall on the growth side.
difficulty: 3
tags:
  - game-days
  - chaos-engineering
  - incident-response
  - drills
  - resilience
  - sre
category: practice
milestones:
  - Design a game day scenario based on a real historical failure mode
  - Run the game day without telling all participants what failure will be injected
  - Measure response time and decision accuracy against runbooks
  - Capture follow-up items and update runbooks based on what broke down
title_zh: "游戏日"

---


Chaos engineering finds technical weaknesses. Game days practice the human response. A game day is a scheduled, facilitated exercise where the team faces a realistic failure scenario — either injected into a real system or simulated in a tabletop format — and responds as they would in a real incident. The goal is to find out how your response process actually works under pressure, rather than finding out during a genuine emergency at 3 AM.

<!-- DEEP_DIVE -->

## Why practice matters

Incident response is a perishable skill. Reading the runbook is not the same as using it. Knowing who the IC is supposed to be is not the same as actually functioning in that role under stress. Teams that have practiced incident response — who have made mistakes in a safe environment and learned from them — handle real incidents dramatically better than teams that haven't.

This is why organizations like the US military and emergency services spend so much time on drills. The muscle memory matters. The procedures need to be practiced until they're automatic, not just documented until they're familiar.

## Game day formats

**Live failure injection** (chaos-assisted): inject an actual failure into a real environment (production or staging) and run a real incident response. The team must detect, diagnose, and resolve the failure. The facilitator observes, notes what breaks down, and may introduce complications.

**Tabletop exercise**: no actual system changes. The facilitator describes a failure scenario and the team talks through their response: "The database just went read-only. What's the first thing you do?" "You've confirmed it's a disk issue. Who do you escalate to?" This is lower-risk and can cover more failure scenarios per hour.

**Hybrid**: inject a real failure but with a facilitator who can stop it if things go badly. The real alert fires, real tools are used, but there's a safety net.

For teams new to game days, start with tabletop exercises. They're lower-stakes, require no setup, and can be run in a single meeting. Once the process is familiar, move to live injection.

## Designing a game day scenario

A good scenario has three properties:

**Based on plausible failure modes**: ideally adapted from a real historical incident or a chaos experiment that revealed a weakness. Theoretical failures are less motivating than failures that have actually happened.

**Multi-step**: simple "database is down" scenarios are too easy. The best scenarios require diagnosis across multiple systems: "Users are reporting slow checkouts, but the checkout service looks healthy, and the database latency looks normal. What now?"

**Unknown to most participants**: if everyone knows the scenario, the exercise tests knowledge of the specific failure, not the diagnostic process. At minimum, the responders shouldn't know what failure will be injected.

## Running the game day

**Before**: define the scenario, confirm the scope, brief any stakeholders who might see alerts fire, ensure you have a rollback plan.

**During**: the facilitator observes without intervening (unless things are genuinely going badly). Note: How long until detection? Was the alert accurate? Was the IC role clear? Were the runbooks used? What caused confusion?

**After**: facilitate a debrief. What worked? What was confusing? Which runbooks were incomplete? Who didn't know what to do? Capture action items while they're fresh.

## Measuring the exercise

Compare the response to your defined criteria:

- Time from failure injection to detection
- Time from detection to accurate diagnosis
- Adherence to incident roles
- Runbook usefulness (did it help, or was it ignored?)
- Communication quality (internal and simulated external)

These measurements make the next game day comparable, and they show whether you're improving over time.

<!-- RESOURCES -->

- [Google SRE Workbook - Incident Management](https://sre.google/workbook/incident-management/) -- type: book, time: 30m
- [PagerDuty Game Day Guide](https://response.pagerduty.com/training/gameday/) -- type: guide, time: 20m
- [How Stripe Runs Game Days](https://stripe.com/blog/game-day-exercises-at-stripe) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
混沌工程发现技术弱点，Game day 则演练人的响应能力。Game day 是一场有计划、有引导的演练，团队在其中面对一个逼真的故障场景——可以注入真实系统，也可以采用桌面推演的形式模拟——并像真实事故中那样做出响应。其目的是弄清你的响应流程在压力下究竟如何运作，而不是等到凌晨 3 点真正发生紧急情况时才发现问题。

<!-- ZH_DEEP_DIVE -->
## 为什么演练很重要

事件响应是一项容易生疏的技能。阅读 runbook 和使用 runbook 是两回事。知道 IC 应该由谁担任，和在压力下真正履行该角色的职责，也是两回事。进行过事件响应演练的团队——在安全环境中犯过错并从中学习——处理真实事件的能力远胜于没有演练过的团队。

这就是为什么美国军方和应急服务等组织会花大量时间进行演练。肌肉记忆很重要。流程需要反复练习直到成为自动反应，而不只是记录下来直到大家熟悉。

## 演练形式

**实时故障注入**（混沌辅助）：向真实环境（生产或预发布）注入实际故障，并运行真实的事件响应。团队必须检测、诊断并解决故障。引导者观察、记录出现问题的环节，并可能引入复杂情况。

**桌面演练**：不实际更改系统。引导者描述一个故障场景，团队讨论他们的响应方式：“数据库刚刚变成只读了。你做的第一件事是什么？”“你已经确认是磁盘问题。你向谁上报？”这种方式风险更低，每小时可以覆盖更多故障场景。

**混合式**：注入真实故障，但由引导者在情况恶化时中止。真实告警会触发，使用真实工具，但有安全网。

对于刚接触演练的团队，从桌面演练开始。它们风险更低、无需准备，且可以在一次会议内完成。一旦流程熟悉，再转向实时注入。

## 设计演练场景

好的场景具备三个特性：

**基于合理的故障模式**：最好改编自真实历史事件或揭示弱点的混沌实验。理论上的故障不如实际发生过的故障有说服力。

**多步骤**：简单的“数据库宕机”场景太容易。最好的场景需要跨多个系统进行诊断：“用户报告结账缓慢，但结账服务看起来健康，数据库延迟看起来也正常。接下来怎么办？”

**对大多数参与者未知**：如果所有人都知道场景，演练测试的是对特定故障的了解，而不是诊断过程。至少，响应者不应知道将注入什么故障。

## 运行演练

**演练前**：定义场景、确认范围、向可能看到告警触发的相关方做简要说明、确保有回滚计划。

**演练中**：引导者观察而不干预（除非情况确实在恶化）。记录：检测用了多长时间？告警是否准确？IC 角色是否清晰？是否使用了 runbook？什么导致了混乱？

**演练后**：组织复盘。哪些做得好？哪些令人困惑？哪些 runbook 不完整？谁不知道该做什么？趁记忆新鲜时记录行动项。

## 衡量演练

将响应情况与你定义的标准进行对比：

- 从故障注入到检测的时间
- 从检测到准确诊断的时间
- 对事件角色的遵守情况
- runbook 的有用性（它有帮助，还是被忽略了？）
- 沟通质量（内部及模拟外部）

这些度量使下一次演练具有可比性，并能显示你是否在随时间改进。

<!-- ZH_RESOURCES -->
- [Google SRE Workbook - 事件管理](https://sre.google/workbook/incident-management/) -- 类型: 书籍, 时长: 30m
- [PagerDuty Game Day 指南](https://response.pagerduty.com/training/gameday/) -- 类型: 指南, 时长: 20m
- [Stripe 如何开展 Game Day](https://stripe.com/blog/game-day-exercises-at-stripe) -- 类型: 文章, 时长: 15m

<!-- ZH_UI -->
1. 基于真实历史故障模式设计游戏日场景
2. 在不告知所有参与者将注入何种故障的情况下运行游戏日
3. 对照运行手册衡量响应时间和决策准确性
4. 记录后续事项，并根据失效环节更新运行手册
5. 团队已掌握压力下的响应方法。下一个主动可靠性关注点是什么？
6. 游戏日效果很好——现在大家已熟悉操作手册、角色和升级路径。但我开始思考我们的人员配置是否真的能匹配即将到来的需求。恢复能力已有保障。我想确保我们不会在增长方面撞墙。
