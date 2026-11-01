---
id: what-makes-a-good-dashboard
title: What Makes a Good Dashboard
zone: observability
edges:
  to:
    - id: alerting
      question: >-
        My dashboards are clean now. But I still need someone to be watching
        them to catch a problem. How do I make the system tell me?
      detail: >-
        Even a perfect dashboard is useless if nobody is looking at it. We've
        had incidents where the problem was visible in the dashboard the whole
        time — we just didn't happen to have it open. I need the system to come
        to me when something is wrong, not the other way around.
difficulty: 1
tags:
  - dashboards
  - grafana
  - observability
  - golden-signals
  - visualisation
category: practice
milestones:
  - Build a service dashboard that answers "is this healthy?" in under 5 seconds
  - Understand the four golden signals and why they belong on every service dashboard
  - Know when to use time series vs stat panels vs tables
  - Identify and remove panels that look useful but don't drive decisions
title_zh: "什么造就了优秀的仪表盘"

---


Most dashboards get built the same way: someone opens Grafana, starts adding panels, and doesn't stop until they feel covered. The result is a 40-panel wall of graphs that's technically comprehensive and practically useless. During an incident, you're scanning through it hoping something jumps out. That's the opposite of what a dashboard should do.

A good dashboard answers a specific question. "Is this service healthy right now?" or "What's happening during this deployment?" are good questions. "Show me everything I might ever want to know about this service" is not. When you start with a question, you know exactly which panels belong and which ones are noise. When you don't, you keep adding panels until it feels like enough — and it never does.

The test for whether a dashboard is good is simple: hand it to someone who didn't build it and hasn't been staring at it all week. Can they tell in five seconds whether things are OK? If they have to scroll, read panel titles carefully, and cross-reference multiple graphs to form an opinion, the dashboard has failed. Good dashboards make the answer obvious.

<!-- DEEP_DIVE -->

## Start With the Four Golden Signals

Before you add any service-specific panels, put the four golden signals on the dashboard: latency, traffic, errors, saturation. These four metrics cover the vast majority of ways a service can fail from a user's perspective. If all four look normal, your service is almost certainly fine. If one looks wrong, you know which dimension to investigate.

Put them at the top where they're the first thing you see. Three stat panels (current error rate, current request rate, current p99 latency) in a row give you an instant status check without reading a single graph. Below those, time series panels for each signal give you the trend and the history.

This structure means someone can open the dashboard, look at the top row, and immediately know whether they need to keep reading. That's the five-second test passing.

## The Five-Second Test

A useful practice before publishing any dashboard: close your eyes, open the dashboard, and time how long it takes to answer your core question. If it takes more than five seconds — if you find yourself reading labels, adjusting time ranges, or hunting through panels — something needs to change.

Common reasons a dashboard fails the five-second test:

- **No visual hierarchy.** Everything is the same size and importance. The most important signals should be the biggest and highest on the page.
- **Too many panels.** When everything is shown, nothing stands out. Ten panels that cover the right things beats forty panels that cover everything.
- **No color thresholds.** If a number is bad, it should look bad. Configure stat panels to turn red above a threshold so bad values are immediately visible without reading the number carefully.
- **Inconsistent time ranges.** If one panel shows the last hour and another shows the last day, you can't visually compare them. Set a dashboard-level default time range and leave it there.

## Organizing Panels

Group related panels together using Grafana rows. A row creates a collapsible section with a label. A typical service dashboard might have:

- **Health** — the four golden signals at a glance
- **Latency** — p50, p95, p99, broken down by endpoint
- **Traffic** — request rate by endpoint, broken down by status code
- **Infrastructure** — CPU, memory, disk for the underlying hosts or pods

This way someone doing a quick health check reads the top section and stops. Someone debugging a latency issue expands the Latency row. The dashboard serves multiple purposes without being overwhelming at first glance.

## Choosing the Right Panel Type

The panel type should match how you think about the metric.

Use a **time series** (line chart) when the shape of the curve matters — you want to see spikes, gradual trends, the moment something changed. Latency percentiles, request rate over time, error count per minute.

Use a **stat panel** (single big number) when the current value is what matters, not the history. The current error rate, current number of connections, whether a health check is passing. Add color thresholds so the number changes color at bad values.

Use a **gauge** when "how full is this?" is the right mental model. Disk usage percentage, memory utilization, connection pool capacity. Good for saturation metrics.

Use a **table** when you want to compare the same metric across many instances at once. Request rate per service, error count per endpoint. Tables let you spot which one is the outlier.

## What to Cut

Every panel on a dashboard has a cost: it takes up space, it adds visual noise, and it gives the eye one more thing to process. Before adding a panel, ask: when would I use this? If the honest answer is "I'd look at it if I happened to notice it looked weird," that's not a panel that should exist on this dashboard — that's a panel that belongs in a separate exploratory dashboard or not at all.

When auditing existing dashboards, look for panels that:

- Show a metric that's never been the deciding factor in an incident
- Show information already visible in a different panel
- Have no threshold or baseline, so you can't tell what "bad" looks like
- Are checked during deployments but never at any other time (move them to a deployment dashboard)

The goal isn't minimalism for its own sake. It's clarity. Every panel that stays should have a clear reason to exist: it's part of the health check, or it's part of debugging a specific known failure mode.

## Annotations for Context

Grafana can overlay deployment markers on your time series charts as vertical lines. These are called annotations. Connect Grafana to your CI/CD pipeline to emit an annotation event every time a deployment happens, and suddenly your time series charts show you exactly when deployments occurred relative to any spike or drop.

This is one of the highest-leverage things you can add to a dashboard. The most common question during an incident is "did this correlate with a deployment?" Annotations answer it instantly without checking multiple systems.

<!-- RESOURCES -->

- [The Four Golden Signals (Google SRE Book)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: article, time: 15m
- [Grafana Best Practices for Dashboards](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/) -- type: article, time: 15m
- [Grafana Annotations](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/annotate-visualizations/) -- type: article, time: 10m
- [Practical Monitoring (O'Reilly)](https://www.oreilly.com/library/view/practical-monitoring/9781491957349/) -- type: book, time: 300m
- [How to Design Useful Dashboards (Grafana Labs blog)](https://grafana.com/blog/2022/06/06/grafana-dashboards-a-complete-guide-to-all-the-different-types-you-might-need/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
大多数仪表盘的构建方式如出一辙：有人打开 Grafana，开始添加面板，一直加到觉得覆盖得差不多了才停手。结果就是一面由 40 个面板组成的图表墙，技术上全面，实际上毫无用处。故障发生时，你只能扫来扫去，指望有什么东西能跳出来引起注意。这恰恰与仪表盘应有的作用背道而驰。

好的仪表盘回答一个具体的问题。“这个服务现在健康吗？”或者“这次部署期间发生了什么？”都是好问题。“把关于这个服务我可能想知道的全部展示给我”则不是。当你从一个问题出发时，你清楚地知道哪些面板该留、哪些是噪音。当你不是这样开始时，你就会不断添加面板，直到感觉差不多了为止——而它永远都不够。

判断一个仪表盘好不好，测试方法很简单：把它交给一个不是它的构建者、也没有盯着它看了一整周的人。他们能在五秒内判断出情况是否正常吗？如果他们必须滚动、仔细阅读面板标题、并交叉比对多个图表才能形成判断，那这个仪表盘就是失败的。好的仪表盘让答案一目了然。

<!-- ZH_DEEP_DIVE -->
## 从四大黄金信号开始

在添加任何服务特定的面板之前，先把四大黄金信号放到仪表盘上：延迟、流量、错误、饱和度。从用户视角来看，这四项指标覆盖了服务可能失败的绝大多数方式。如果这四项看起来都正常，你的服务几乎可以肯定没问题。如果某一项看起来不对，你就知道该往哪个维度去排查。

把它们放在顶部，让你第一眼就能看到。一行三个 stat 面板（当前错误率、当前请求速率、当前 p99 延迟）让你无需阅读任何图表就能即时检查状态。在这些面板下方，为每个信号放置时间序列面板，展示趋势和历史。

这种结构意味着，任何人打开仪表盘、看一眼顶部那一行，就能立刻知道是否还需要继续往下读。这就是通过了五秒测试。

## 五秒测试

在发布任何仪表盘之前，有一个有用的做法：闭上眼睛，打开仪表盘，计时回答你的核心问题需要多久。如果超过五秒——如果你发现自己在读标签、调整时间范围，或者在面板之间翻找——那就需要做出改变。

仪表盘无法通过五秒测试的常见原因：

- **没有视觉层次。** 所有东西的大小和重要性都一样。最重要的信号应该是最大的，并且位于页面最上方。
- **面板太多。** 当所有东西都展示出来时，就没有任何东西能脱颖而出。十个覆盖正确内容的面板，胜过四十个覆盖一切的面板。
- **没有颜色阈值。** 如果一个数值很糟糕，它看起来就应该很糟糕。配置 stat 面板，让它在超过阈值时变红，这样糟糕的数值无需仔细阅读数字就能立刻被发现。
- **时间范围不一致。** 如果一个面板显示最近一小时，另一个显示最近一天，你就无法在视觉上比较它们。设置一个仪表盘级别的默认时间范围，并保持不动。

## 组织面板

使用 Grafana 的行（row）将相关的面板分组在一起。一个行会创建一个带标签的可折叠区域。一个典型的服务仪表盘可能包含：

- **健康** — 四大黄金信号一览
- **延迟** — p50、p95、p99，按端点细分
- **流量** — 按端点划分的请求速率，按状态码细分
- **基础设施** — 底层主机或 Pod 的 CPU、内存、磁盘

这样一来，做快速健康检查的人读完顶部区域就可以停下。排查延迟问题的人则展开延迟行。仪表盘服务于多种用途，同时第一眼看上去又不会让人不知所措。

## 选择正确的面板类型

面板类型应该与你看待该指标的方式相匹配。

当你关心曲线的形状时——你想看到尖峰、渐变趋势、某个东西发生变化的时刻——使用**时间序列**（折线图）。延迟百分位数、随时间变化的请求速率、每分钟错误数。

当当前值才是关键、历史不重要时，使用 **stat 面板**（单个大数字）。当前错误率、当前连接数、健康检查是否通过。添加颜色阈值，让数字在糟糕的数值下改变颜色。

当“这个有多满？”是正确的思维模型时，使用**仪表盘（gauge）**。磁盘使用百分比、内存利用率、连接池容量。适合饱和度指标。

当你想一次性比较多个实例上的同一指标时，使用**表格**。每个服务的请求速率、每个端点的错误数。表格让你能找出哪个是异常值。

## 该删掉什么

仪表盘上的每个面板都有成本：它占用空间、增加视觉噪音，并让眼睛多处理一样东西。在添加面板之前，问自己：我什么时候会用到它？如果诚实的答案是“如果我碰巧注意到它看起来奇怪，我就会看一眼”，那这不是一个应该存在于这个仪表盘上的面板——那是一个属于单独的探索性仪表盘的面板，或者根本不该存在。

在审计现有仪表盘时，寻找符合以下情况的面板：

- 展示的指标从未在事故中成为决定性因素
- 展示的信息已经在另一个面板中可见
- 没有阈值或基线，因此你无法判断“糟糕”是什么样子
- 在部署期间会被查看，但其他任何时候都不会（把它们移到部署仪表盘）

目标不是为极简而极简。而是清晰。每一个保留下来的面板都应该有明确的存续理由：它要么是健康检查的一部分，要么是排查某个已知特定故障模式的一部分。

## 用注解提供上下文

Grafana 可以将部署标记作为垂直线叠加到你的时间序列图表上。这些被称为注解（annotation）。将 Grafana 连接到你的 CI/CD 流水线，在每次部署发生时发出一个注解事件，突然间你的时间序列图表就能准确显示部署相对于任何尖峰或下降发生的时间。

这是你能添加到仪表盘上的最高杠杆的事情之一。事故期间最常见的问题是“这和某次部署有关吗？”注解能瞬间回答这个问题，而无需检查多个系统。

<!-- ZH_RESOURCES -->
- [四大黄金信号（Google SRE 手册）](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型：文章，时长：15 分钟
- [Grafana 仪表盘最佳实践](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/) -- 类型：文章，时长：15 分钟
- [Grafana 注解](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/annotate-visualizations/) -- 类型：文章，时长：10 分钟
- [实用监控（O'Reilly）](https://www.oreilly.com/library/view/practical-monitoring/9781491957349/) -- 类型：书籍，时长：300 分钟
- [如何设计有用的仪表盘（Grafana Labs 博客）](https://grafana.com/blog/2022/06/06/grafana-dashboards-a-complete-guide-to-all-the-different-types-you-might-need/) -- 类型：文章，时长：15 分钟

<!-- ZH_UI -->
1. 构建一个能在5秒内回答“这个服务健康吗？”的服务仪表盘
2. 理解四大黄金信号，以及为什么它们应该出现在每个服务仪表盘上
3. 知道何时使用时间序列、统计面板或表格
4. 识别并移除那些看起来有用但不能驱动决策的面板
5. 我的仪表盘现在很干净了。但我仍然需要有人盯着它们来发现问题。如何让系统主动告诉我？
6. 即使仪表盘再完美，如果没人看也毫无用处。我们遇到过问题一直显示在仪表盘上、只是我们碰巧没打开的情况。我需要系统在出问题时主动通知我，而不是反过来。
