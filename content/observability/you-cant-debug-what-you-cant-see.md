---
id: you-cant-debug-what-you-cant-see
title: You Can't Debug What You Can't See
zone: observability
edges:
  to:
    - id: what-is-observability
      question: What does "observability" even mean? I just know my service breaks and I can't see why.
      detail: >-
        I keep hearing logs, metrics, and traces but I don't really understand
        how they're different or why I'd need all three. I just want to be able
        to tell what my service is doing when something goes wrong.
difficulty: 1
tags:
  - observability
  - logging
  - metrics
  - tracing
  - three-pillars
  - debugging
category: concept
milestones:
  - 'Explain the three pillars of observability: logs, metrics, and traces'
  - >-
    Describe what each pillar answers: what happened, how is it performing, why
    is it slow
  - Understand why you need all three — no single signal tells the full story
title_zh: "无法调试你看不见的东西"

---


Picture this: it's 2am, your phone is buzzing, users are reporting that your service is down. You SSH into your server, stare at a process that appears to be running, and have absolutely no idea what is happening inside it. Is it crashing and restarting? Is it hanging on a database query? Is it throwing errors for every user or just some? You have no way to answer any of those questions. That feeling — of being completely blind to a system you're supposed to be responsible for — is what the observability problem is about.

This happens more often than people admit. Services get built, they work in development, they get deployed, and then the question of "how do I know what this thing is doing in production?" gets kicked down the road indefinitely. Until something breaks. The hard truth is that debugging a system you can't see is just guessing. You try things, restart processes, roll back deploys, and hope something changes — without ever knowing what actually fixed it or whether it'll happen again.

The goal of observability is simple: make your systems legible. Give yourself the ability to look inside a running system and answer real questions — not just "is it up?" but "which users are affected?", "when did this start?", "which part of the code is responsible?", and "has this happened before?" Those questions are unanswerable without the right signals in place.

<!-- DEEP_DIVE -->

## What happens when something breaks and you have no visibility

Let's walk through a realistic scenario. A user opens a support ticket: "The checkout page is broken." You check your monitoring dashboard — if you have one — and the uptime check is green. The process is running. Nothing looks obviously wrong.

So you start guessing:

- Did a recent deploy break something? You check the deploy history. Nothing deployed in the last 6 hours.
- Is the database down? You try connecting manually. It connects fine.
- Is it broken for everyone? You don't know. You have no request logs, no error rate, nothing.
- When did it start? You have no idea. The user says "about an hour ago" but you can't verify.

This is the flying-blind problem. Every step of the investigation is a guess. You're not debugging — you're fumbling.

Now contrast that with having basic observability in place. The user files a ticket. You open your log viewer, filter to `service=checkout level=error`, and immediately see a wall of errors that started 73 minutes ago. The error message says `payment_gateway: connection timeout`. You didn't need to guess at all — the system told you.

## The questions you can't answer without observability

The absence of observability means you can't answer the most basic operational questions:

**Is it down?** An uptime check tells you if a port is open. It doesn't tell you if requests are failing. You can have a service that accepts connections but returns 500 for every single request — and a simple ping-based uptime check will say it's healthy.

**Which users are affected?** Without logging, you have no idea if the problem is hitting everyone or just a subset. Maybe it's only users who signed up before a certain date. Maybe it's only users in a specific region. Without logs that record who made each request, you can't even begin to answer this.

**For how long?** If you don't have timestamped logs or metrics with history, you're relying on user reports to tell you when something started. Users don't report problems the moment they happen. You might have been broken for hours before anyone noticed.

**Is it getting worse or better?** Without a time series of error rates or request counts, you can't tell if a problem is stable, trending up, or resolving on its own. A restart might have fixed it — or it might have fixed it temporarily and it's about to break again.

**Which part is broken?** Modern applications aren't a single process. They're APIs calling other APIs, background workers, database queries, external services. Without tracing, a "slow request" could be caused by any one of a dozen things, and you're left timing things manually and guessing.

## Knowing it's broken vs. knowing why

There's an important distinction between knowing your service is broken and knowing why it's broken.

Traditional monitoring systems — uptime checks, process monitors, basic health endpoints — are good at the first part. They can tell you something is wrong. But they stop there. The moment you need to understand *why* something is wrong, you need to look inside the system.

That's the difference between monitoring and observability. Monitoring is about alerting on known failure modes. Observability is about being able to answer questions you didn't know to ask in advance. You can't write an uptime check for "the payment gateway is timing out specifically for users with European billing addresses" — but if you have good logs and traces, you can discover that on your own once an alert fires.

The practical takeaway: monitoring gets you woken up. Observability gets you back to sleep.

<!-- RESOURCES -->

- [Observability Engineering (book overview)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) -- type: book, time: 360m
- [What is Observability? (Honeycomb)](https://www.honeycomb.io/blog/so-you-want-to-build-an-observable-system) -- type: article, time: 12m
- [The Three Pillars of Observability (Splunk)](https://www.splunk.com/en_us/blog/learn/observability-pillars-logs-metrics-traces.html) -- type: article, time: 8m

<!-- ZH_SUMMARY -->
想象一下：凌晨两点，你的手机嗡嗡作响，用户反馈你的服务宕机了。你 SSH 登录到服务器，盯着一个看起来还在运行的进程，却完全不知道它内部发生了什么。它是在崩溃后重启吗？是卡在某个数据库查询上吗？是给每个用户都报错，还是只对部分用户报错？你无从回答这些问题中的任何一个。那种感觉——对自己本应负责的系统完全一无所知——正是可观测性问题所关注的。

这种情况发生的频率比人们愿意承认的要高。服务被构建出来，在开发环境中运行正常，然后被部署上线，接着“我怎么知道这东西在生产环境中在做什么？”这个问题就被无限期地往后推。直到某天出了问题。残酷的事实是：调试一个你看不见的系统，本质上就是在猜。你尝试各种操作、重启进程、回滚部署，指望某个改动能起作用——却始终不知道究竟是什么修好了它，也不知道它会不会再次发生。

可观测性的目标很简单：让你的系统变得可读。让自己有能力窥视一个正在运行的系统内部，回答真正的问题——不只是“它还在运行吗？”，而是“哪些用户受到了影响？”、“这个问题是什么时候开始的？”、“哪部分代码该负责？”以及“以前发生过吗？”如果没有正确的信号就位，这些问题都无从回答。

<!-- ZH_DEEP_DIVE -->
## 当系统出问题而你毫无可见性时会发生什么

让我们走一遍一个真实的场景。用户提交了一个支持工单：“结账页面坏了。”你查看监控仪表盘——如果你有的话——可用性检查是绿色的。进程正在运行。没有什么看起来明显不对。

于是你开始猜测：

- 最近的部署是不是弄坏了什么？你查看部署历史。过去 6 小时内没有任何部署。
- 数据库是不是挂了？你尝试手动连接。连接正常。
- 是所有用户都受影响吗？你不知道。你没有请求日志，没有错误率，什么都没有。
- 什么时候开始的？你完全不知道。用户说“大约一小时前”，但你无法验证。

这就是盲飞问题。调查的每一步都是猜测。你不是在调试——你是在瞎摸。

现在对比一下已经具备基本可观测性的情况。用户提交工单。你打开日志查看器，过滤 `service=checkout level=error`，立刻看到一大片错误，从 73 分钟前开始出现。错误信息写着 `payment_gateway: connection timeout`。你根本不需要猜——系统直接告诉了你。

## 没有可观测性就无法回答的问题

缺乏可观测性意味着你无法回答最基本的运维问题：

**服务是不是挂了？** 可用性检查只能告诉你端口是否开放。它不会告诉你请求是否在失败。你的服务可能接受连接但对每一个请求都返回 500——而一个简单的基于 ping 的可用性检查会说它是健康的。

**哪些用户受影响？** 没有日志，你完全不知道问题是影响所有人还是只影响一部分人。也许只有某个日期之前注册的用户受影响。也许只有特定地区的用户受影响。如果没有记录每个请求发起者的日志，你甚至无从下手。

**持续了多久？** 如果你没有带时间戳的日志或带历史数据的指标，你就只能依赖用户报告来告诉你问题何时开始。用户不会在问题发生的那一刻就报告。你可能已经坏了几个小时才有人注意到。

**是在恶化还是在好转？** 没有错误率或请求数的时间序列，你无法判断问题是稳定的、在上升，还是在自行恢复。一次重启可能已经修复了它——也可能只是暂时修复，马上又会坏。

**哪个部分坏了？** 现代应用不是单个进程。它们是调用其他 API 的 API、后台 worker、数据库查询、外部服务。没有追踪，一个“慢请求”可能由十几种原因中的任何一种引起，而你只能手动计时并猜测。

## 知道它坏了 vs. 知道为什么坏

知道服务坏了和知道为什么坏之间有一个重要的区别。

传统监控系统——可用性检查、进程监控、基础健康端点——擅长第一部分。它们能告诉你出了问题。但也就到此为止。当你需要理解*为什么*出问题时，你需要看到系统内部。

这就是监控和可观测性之间的区别。监控是对已知故障模式进行告警。可观测性是能够回答你事先不知道要问的问题。你没法写一个可用性检查来检测“支付网关专门对欧洲账单地址的用户超时”——但如果你有好的日志和追踪，一旦告警触发，你可以自己发现这一点。

实际结论：监控让你被叫醒。可观测性让你能回去接着睡。

<!-- ZH_RESOURCES -->
- [Observability Engineering（书籍概览）](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) -- 类型：书籍，时长：360m
- [What is Observability?（Honeycomb）](https://www.honeycomb.io/blog/so-you-want-to-build-an-observable-system) -- 类型：文章，时长：12m
- [The Three Pillars of Observability（Splunk）](https://www.splunk.com/en_us/blog/learn/observability-pillars-logs-metrics-traces.html) -- 类型：文章，时长：8m

<!-- ZH_UI -->
1. 解释可观测性的三大支柱：日志、指标和追踪
2. 描述每个支柱回答的问题：发生了什么、性能如何、为什么慢
3. 理解为什么三者都需要——没有任何单一信号能讲述完整的故事
4. “可观测性”到底是什么意思？我只知道我的服务坏了，却看不出原因。
5. 我总听到日志、指标和追踪，但不太理解它们有何不同，也不明白为什么三者都需要。我只想在出问题时能看清服务在做什么。
