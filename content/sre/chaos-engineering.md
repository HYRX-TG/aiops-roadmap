---
id: chaos-engineering
title: Chaos Engineering
zone: sre
edges:
  to:
    - id: graceful-degradation
      question: >-
        Chaos tests keep revealing that my services fall over completely instead
        of degrading gracefully.
      detail: >-
        Every fault injection test ends the same way — the whole service goes
        down instead of shedding load or serving partial results. Users get a
        hard error instead of something degraded but functional. I want to
        design for partial failure, not just crash-and-recover.
    - id: game-days
      question: >-
        We're finding failures with chaos tests. But I'm not sure the team
        actually knows how to respond when they happen.
      detail: >-
        The last drill revealed that people didn't know what to do, who to
        call, or how to use the runbooks under pressure. The technical systems
        are getting more resilient but the human response is still unreliable.
        I want to practice the response, not just find the failure.
    - id: capacity-planning
      question: >-
        I've stress-tested the failure modes. Now I'm worried about what
        happens when traffic just keeps growing.
      detail: >-
        Chaos tests have found a bunch of weaknesses that I've fixed. But
        they're all about fault tolerance — not about growth. I don't know if
        the system can handle 3x current traffic, and I'd rather find out
        before users do.
difficulty: 3
tags:
  - chaos-engineering
  - resilience
  - game-days
  - fault-injection
  - reliability
  - netflix
  - chaos-monkey
category: practice
milestones:
  - 'Run a game day: define a failure scenario, inject it, observe and recover'
  - >-
    Verify your auto-scaling and self-healing actually work by terminating
    instances
  - >-
    Test your failover path: does Multi-AZ failover work in practice, not just
    in theory?
  - >-
    Understand the difference between chaos experiments and breaking production
    carelessly
title_zh: "混沌工程"

---


Every system has failure modes that haven't been discovered yet. Post-mortems and monitoring find failures after they happen. Chaos engineering finds them before. The discipline is straightforward in principle: inject controlled failures into your system to observe how it behaves, identify unexpected weaknesses, and fix them before users find them. Netflix's Chaos Monkey — which randomly terminates production instances — made this famous, but the practice applies at every scale.

<!-- DEEP_DIVE -->

## The hypothesis-driven approach

Chaos engineering is not random destruction. It's a scientific practice with a specific structure:

1. **Form a hypothesis**: "If we terminate one of the three checkout service instances, the load balancer will route traffic to the other two and response time will increase by less than 50ms."

2. **Define success criteria**: what outcome confirms the hypothesis? What outcome refutes it?

3. **Inject the failure**: terminate the instance, introduce latency on a network call, exhaust a connection pool, fill a disk.

4. **Observe the system**: what actually happened? Did the load balancer behave as expected? Were there unexpected cascading effects?

5. **Analyze and act**: if the hypothesis was confirmed, the system is more resilient than you thought. If it was refuted, you've found a weakness — fix it before it becomes a production incident.

The difference between chaos engineering and breaking production carelessly: the hypothesis, the criteria, and the plan for what to do if things go wrong.

## Start with simple experiments

Before Chaos Monkey, there are simpler experiments that reveal a lot:

**Instance termination**: can your service handle losing one instance? Most properly configured auto-scaling groups handle this, but it's worth confirming. The failure reveals whether your health checks work, whether the load balancer routes correctly, and whether your instance startup is fast enough.

**Network partition**: what happens if your service can't reach its primary database? Does it fail fast with a clear error, or does it hang indefinitely? Does it try the replica? Does it serve stale cached data?

**Slow dependencies**: what happens if a downstream API takes 10 seconds to respond instead of 100ms? Does your service time out correctly? Does it circuit-break? Or does it hold connections open until it runs out of threads?

**Resource exhaustion**: what happens when the connection pool is full? When memory is at 95%? When the disk is full? These are often the most revealing experiments — the system behavior is usually worse than expected.

## Blast radius control

The cardinal rule: every chaos experiment has a defined blast radius — the maximum user impact if the experiment goes wrong. In early experiments, keep the blast radius small:

- Test in staging first
- Test a single instance, not the whole cluster
- Test non-peak traffic times
- Have a prepared rollback (stop the failure injection immediately if things go badly)
- Monitor SLOs during the experiment and abort if error budget starts burning faster than expected

As you build confidence in your system's resilience, you can run experiments with larger blast radii — and eventually, in production during peak traffic, which is where Netflix and Google run theirs.

## From experiments to game days

Individual chaos experiments validate specific failure modes. Game days combine multiple failure scenarios with a focus on the human response: does the team detect the failure? Do they follow the right runbook? Do incident roles work under pressure? Do escalation policies fire correctly?

Game days are intentional, scheduled events. They combine technical fault injection with incident response practice.

<!-- RESOURCES -->

- [Principles of Chaos Engineering](https://principlesofchaos.org/) -- type: article, time: 10m
- [Chaos Engineering - O'Reilly Book (free online)](https://www.oreilly.com/library/view/chaos-engineering/9781491988459/) -- type: book, time: varies
- [Gremlin - Chaos Engineering Platform](https://www.gremlin.com/) -- type: tool, time: 30m
- [Netflix Tech Blog - Chaos Monkey](https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
每个系统都有尚未被发现的失效模式。事后复盘和监控只能在故障发生后发现问题，而混沌工程则能在故障发生前找到它们。这门学科在原理上很直接：向系统注入受控的故障，观察其行为，识别出意料之外的薄弱环节，并在用户发现之前将其修复。Netflix 的 Chaos Monkey——随机终止生产环境实例——让这一做法广为人知，但这种实践适用于各种规模。

<!-- ZH_DEEP_DIVE -->
## 假设驱动的方法

混沌工程不是随机破坏。它是一门具有特定结构的科学实践：

1. **形成假设**：“如果我们终止三个 checkout 服务实例中的一个，负载均衡器会将流量路由到另外两个，响应时间的增加将小于 50ms。”

2. **定义成功标准**：什么结果能证实假设？什么结果能推翻假设？

3. **注入故障**：终止实例、在网络调用上引入延迟、耗尽连接池、填满磁盘。

4. **观察系统**：实际发生了什么？负载均衡器的行为是否符合预期？是否出现了意料之外的级联效应？

5. **分析并行动**：如果假设得到证实，说明系统的韧性比你想象的更强。如果假设被推翻，你就发现了一个弱点——在它演变成生产事故之前修复它。

混沌工程与粗心破坏生产环境之间的区别在于：假设、标准，以及事情出错时的应对计划。

## 从简单实验开始

在 Chaos Monkey 之前，有一些更简单的实验能揭示很多问题：

**实例终止**：你的服务能否承受丢失一个实例？大多数配置正确的自动伸缩组都能处理这种情况，但值得确认。这个故障能揭示你的健康检查是否有效、负载均衡器路由是否正确，以及实例启动是否足够快。

**网络分区**：如果你的服务无法访问主数据库会发生什么？它是快速失败并给出清晰的错误，还是无限期挂起？它会尝试副本吗？它会提供过期的缓存数据吗？

**慢依赖**：如果下游 API 的响应时间从 100ms 变成 10 秒会发生什么？你的服务是否正确超时？是否触发熔断？还是会一直保持连接打开，直到线程耗尽？

**资源耗尽**：连接池满了会发生什么？内存达到 95% 时呢？磁盘满了呢？这些往往是最能揭示问题的实验——系统行为通常比预期更糟。

## 爆炸半径控制

首要原则：每个混沌实验都有明确的爆炸半径——即实验出错时对用户的最大影响。在早期实验中，保持较小的爆炸半径：

- 先在 staging 环境测试
- 测试单个实例，而非整个集群
- 在非高峰流量时段测试
- 准备好回滚方案（情况恶化时立即停止故障注入）
- 在实验期间监控 SLO，如果错误预算消耗速度超出预期就中止

随着你对系统韧性的信心增强，可以运行爆炸半径更大的实验——最终在生产环境的高峰流量时段进行，Netflix 和 Google 就是在那里运行他们的实验的。

## 从实验到 Game Day

单个混沌实验验证特定的故障模式。Game Day 将多个故障场景组合起来，并聚焦于人的响应：团队能否检测到故障？他们是否遵循正确的 runbook？事故角色在压力下能否正常运作？升级策略是否正确触发？

Game Day 是有意安排的、计划好的活动。它们将技术故障注入与事故响应演练结合起来。

<!-- ZH_RESOURCES -->
- [混沌工程原则](https://principlesofchaos.org/) -- 类型: 文章, 时长: 10m
- [混沌工程 - O'Reilly 图书（免费在线）](https://www.oreilly.com/library/view/chaos-engineering/9781491988459/) -- 类型: 图书, 时长: 不定
- [Gremlin - 混沌工程平台](https://www.gremlin.com/) -- 类型: 工具, 时长: 30m
- [Netflix 技术博客 - Chaos Monkey](https://netflixtechblog.com/the-netflix-simian-army-16e57fbab116) -- 类型: 文章, 时长: 15m

<!-- ZH_UI -->
1. 运行一次故障演练日：定义故障场景，注入故障，观察并恢复
2. 通过终止实例来验证自动扩缩容和自愈机制是否真正有效
3. 测试故障转移路径：多可用区故障转移在实践中是否有效，而不仅仅是理论上？
4. 理解混沌实验与随意破坏生产环境之间的区别
5. 混沌测试不断揭示我的服务是完全崩溃，而不是优雅降级。
6. 每次故障注入测试都以同样的方式结束——整个服务宕机，而不是卸载负载或提供部分结果。用户得到的是硬错误，而不是降级但可用的功能。我想为部分故障设计，而不仅仅是崩溃后恢复。
7. 我们通过混沌测试发现了故障。但我不确定团队是否真的知道故障发生时该如何响应。
8. 上次演练暴露出人们在压力下不知道做什么、该联系谁、如何使用运行手册。技术系统越来越有韧性，但人的响应仍然不可靠。我想演练响应过程，而不仅仅是发现故障。
9. 我已经对故障模式做了压力测试。现在担心的是流量持续增长时会发生什么。
10. 混沌测试发现了一堆我已经修复的弱点。但这些都是关于容错的——不是关于增长的。我不知道系统能否承受当前流量的3倍，我宁愿在用户之前发现答案。
