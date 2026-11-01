---
id: dashboards
title: Dashboards and Grafana
zone: observability
edges:
  to:
    - id: what-makes-a-good-dashboard
      question: >-
        My dashboard has 40 panels and I still can't tell at a glance whether
        the system is healthy. What am I doing wrong?
      detail: >-
        I just kept adding panels whenever I thought of something useful to
        track. Now it's a wall of graphs and during incidents I'm scanning
        through all of them trying to find the one that shows the problem.
        This doesn't feel like it's helping.
    - id: alerting
      question: >-
        My dashboards look great. But I can't stare at them 24/7. How do I get
        notified when something's wrong?
      detail: >-
        Even a good dashboard is useless if nobody is looking at it. We've had
        incidents where the problem was visible the whole time — we just didn't
        happen to have the dashboard open. I need the system to come to me.
difficulty: 1
tags:
  - grafana
  - dashboards
  - visualisation
  - prometheus
  - cloudwatch
  - observability
category: practice
milestones:
  - Set up Grafana connected to your metrics source (Prometheus or CloudWatch)
  - Build a service dashboard showing the four golden signals
  - Understand when to use a time series panel vs a stat panel vs a table
  - Know what makes a dashboard useful vs noisy
title_zh: "仪表盘与 Grafana"

---


Once you have metrics flowing into Prometheus (or CloudWatch, or any other backend), you need a way to look at them. That's where Grafana comes in. Grafana is the de facto standard for visualizing time-series metrics — it's open source, it connects to almost any data source, and it gives you a flexible panel-based canvas for building dashboards. Most teams running Prometheus use Grafana alongside it almost automatically.

A dashboard is just a collection of panels, each one running a query and rendering the result as a chart, number, or table. The value isn't in having a lot of panels — it's in having the right ones. A well-built dashboard lets you answer "is this service healthy right now?" in a few seconds, without scrolling or hunting. That's the bar to aim for.

The four golden signals — latency, traffic, errors, and saturation — are the foundation every service dashboard should start from. They were coined by Google's SRE book and they hold up because they represent the four things users actually feel. If those four signals look healthy, your service is almost certainly healthy. If one of them looks wrong, you know exactly which dimension to investigate.

<!-- DEEP_DIVE -->

## Connecting Grafana to Prometheus

After installing Grafana (it runs as a standalone server, usually on port 3000), the first thing you do is add a data source. Go to **Configuration → Data Sources → Add data source**, choose Prometheus, and point it at your Prometheus URL (e.g. `http://localhost:9090`). Grafana will test the connection and confirm it can reach Prometheus.

From that point on, every panel you create can run PromQL queries and render the results. You write the query, Grafana handles the visualization.

## Panel Types

Grafana has many panel types but you'll use four of them the vast majority of the time.

**Time series** is the standard line chart. Use it for anything that changes over time and where you care about the shape of the curve — request rate, latency percentiles, error count, CPU usage. This should be your default.

**Stat** shows a single current value, big and readable. Use it for things where the current state matters more than the history — current error rate, number of active connections, uptime. You can add color thresholds so the number turns red when it exceeds a limit.

**Gauge** is a visual fill indicator, like a fuel gauge. Use it for saturation metrics where "how full is this?" is the right mental model — disk usage percentage, memory utilization, connection pool saturation. Avoid it for metrics that can spike suddenly; the animated fill is misleading for fast-changing values.

**Table** shows multiple time series as rows with columns for different computed values (last, average, max). Use it when you want a breakdown by label — request rate per service, error count per endpoint, latency by region. Tables are great for comparing across many instances at once.

## The Four Golden Signals

Every service dashboard should start with these four panels before you add anything else.

| Signal | What it measures | Example PromQL |
|---|---|---|
| Latency | How long requests take | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| Traffic | How many requests you're handling | `rate(http_requests_total[5m])` |
| Errors | What fraction of requests are failing | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` |
| Saturation | How full your system is | `1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))` |

If latency is high, users are experiencing slowness. If traffic dropped suddenly, something may have broken upstream (or you're no longer receiving requests for some other reason). If errors are elevated, users are seeing failures. If saturation is high, you're approaching a limit and things will get worse. These four signals cover most of what goes wrong with a service.

## Dashboard Variables

Static dashboards that only show one service or one environment get old fast. Grafana's variable system lets you add drop-downs at the top of a dashboard so you can filter all panels at once.

In **Dashboard Settings → Variables**, you can define a variable like `$service` that queries Prometheus for all label values: `label_values(http_requests_total, service)`. Grafana populates the drop-down automatically. Then in your panel queries you use `{service="$service"}` and every panel updates when you pick a different service from the drop-down.

Common variables to add:

- `$service` — filter by service name
- `$env` — filter by environment (production, staging)
- `$instance` — filter by individual host or pod
- `$interval` — control the step size for rate calculations

Variables are what transform a single hardcoded dashboard into something your whole team can use across every service.

## A Practical Starting Template

When building a new service dashboard, start with this layout:

1. A row of three stat panels at the top: current request rate, current error rate, p99 latency. These give instant status at a glance.
2. Below that, a time series panel for each golden signal — traffic, errors, latency (p50, p95, p99 on the same chart), and saturation.
3. Add variables for service and environment.
4. Stop there until you have a reason to add more.

Resist the urge to add more panels "just in case." A dashboard with six well-chosen panels that answer one clear question is more valuable than forty panels that might theoretically be useful. You can always add more later when you discover you actually need them during an incident.

<!-- RESOURCES -->

- [Grafana Dashboards Getting Started](https://grafana.com/docs/grafana/latest/getting-started/build-first-dashboard/) -- type: tutorial, time: 20m
- [The Four Golden Signals (Google SRE Book)](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- type: article, time: 15m
- [Grafana Dashboard Variables](https://grafana.com/docs/grafana/latest/dashboards/variables/) -- type: article, time: 15m
- [Grafana Panel Types Overview](https://grafana.com/docs/grafana/latest/panels-visualizations/) -- type: article, time: 10m
- [Practical Monitoring (O'Reilly)](https://www.oreilly.com/library/view/practical-monitoring/9781491957349/) -- type: book, time: 300m

<!-- ZH_SUMMARY -->
一旦指标流入 Prometheus（或 CloudWatch，或任何其他后端），你需要一种方式来查看它们。这就是 Grafana 的用武之地。Grafana 是时序指标可视化的事实标准——它开源、几乎可以连接任何数据源，并为你提供灵活的基于面板的画布来构建仪表盘。大多数运行 Prometheus 的团队几乎都会自然而然地搭配使用 Grafana。

仪表盘不过是一组面板的集合，每个面板运行一个查询，并将结果渲染为图表、数字或表格。其价值不在于拥有大量面板——而在于拥有正确的面板。一个构建良好的仪表盘能让你在几秒内回答“这个服务现在健康吗？”，而无需滚动或翻找。这就是你应该追求的标准。

四大黄金信号——延迟、流量、错误和饱和度——是每个服务仪表盘都应作为起点的基石。它们由 Google 的 SRE 书籍提出，之所以经久不衰，是因为它们代表了用户真正能感受到的四件事。如果这四个信号看起来健康，你的服务几乎肯定是健康的。如果其中某个信号看起来不对，你就确切知道该调查哪个维度。

<!-- ZH_DEEP_DIVE -->
## 将 Grafana 连接到 Prometheus

安装 Grafana 后（它作为独立服务器运行，通常监听 3000 端口），你要做的第一件事就是添加数据源。进入 **Configuration → Data Sources → Add data source**，选择 Prometheus，然后将其指向你的 Prometheus URL（例如 `http://localhost:9090`）。Grafana 会测试连接并确认它能够访问 Prometheus。

从那时起，你创建的每个面板都可以运行 PromQL 查询并渲染结果。你编写查询，Grafana 负责可视化。

## 面板类型

Grafana 有很多面板类型，但绝大多数情况下你只会用到其中四种。

**Time series** 是标准的折线图。凡是随时间变化、且你关心曲线形状的指标都用它——请求速率、延迟分位数、错误数、CPU 使用率。这应该是你的默认选择。

**Stat** 显示单个当前值，大而醒目。凡是当前状态比历史更重要的情况都用它——当前错误率、活跃连接数、运行时长。你可以添加颜色阈值，让数字在超过限制时变红。

**Gauge** 是一种可视化的填充指示器，就像油量表。凡是“这个有多满？”是正确心智模型的饱和度指标都用它——磁盘使用率、内存利用率、连接池饱和度。避免将它用于可能突然飙升的指标；动画填充对于快速变化的值会产生误导。

**Table** 将多个时间序列显示为行，并用列展示不同的计算值（last、average、max）。当你想要按标签细分时用它——每个服务的请求速率、每个端点的错误数、按区域的延迟。表格非常适合一次性对比多个实例。

## 四大黄金信号

每个服务仪表盘都应该先有这四个面板，然后再添加其他内容。

| 信号 | 衡量什么 | PromQL 示例 |
|---|---|---|
| Latency（延迟） | 请求耗时多久 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| Traffic（流量） | 你正在处理多少请求 | `rate(http_requests_total[5m])` |
| Errors（错误） | 失败请求所占比例 | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` |
| Saturation（饱和度） | 你的系统有多满 | `1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))` |

如果延迟高，用户正在经历变慢。如果流量突然下降，可能是上游出了问题（或者你因其他原因不再收到请求）。如果错误率升高，用户正在看到失败。如果饱和度高，你正在接近极限，情况会变得更糟。这四个信号覆盖了服务出问题时的大部分情况。

## 仪表盘变量

只显示一个服务或一个环境的静态仪表盘很快就会过时。Grafana 的变量系统让你可以在仪表盘顶部添加下拉菜单，从而一次性过滤所有面板。

在 **Dashboard Settings → Variables** 中，你可以定义一个类似 `$service` 的变量，它向 Prometheus 查询所有标签值：`label_values(http_requests_total, service)`。Grafana 会自动填充下拉菜单。然后在你的面板查询中使用 `{service="$service"}`，当你从下拉菜单中选择不同的服务时，每个面板都会更新。

常用的变量：

- `$service` — 按服务名过滤
- `$env` — 按环境过滤（production、staging）
- `$instance` — 按单个主机或 pod 过滤
- `$interval` — 控制速率计算的步长

变量正是将单个硬编码的仪表盘转变为整个团队可以跨所有服务使用的工具的关键。

## 一个实用的起始模板

构建新的服务仪表盘时，从这个布局开始：

1. 顶部一行三个 stat 面板：当前请求速率、当前错误率、p99 延迟。这些让你一眼就能看到即时状态。
2. 在其下方，为每个黄金信号各放一个 time series 面板——流量、错误、延迟（p50、p95、p99 放在同一张图上）和饱和度。
3. 添加 service 和 environment 变量。
4. 到此为止，直到你有理由添加更多。

抵制“以防万一”而添加更多面板的冲动。一个包含六个精心挑选、能回答一个明确问题的面板的仪表盘，比四十个理论上可能有用的面板更有价值。当你发现在事故处理中确实需要更多面板时，随时可以再添加。

<!-- ZH_RESOURCES -->
- [Grafana 仪表盘入门](https://grafana.com/docs/grafana/latest/getting-started/build-first-dashboard/) -- 类型：教程，时长：20 分钟
- [四大黄金信号（Google SRE 手册）](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals) -- 类型：文章，时长：15 分钟
- [Grafana 仪表盘变量](https://grafana.com/docs/grafana/latest/dashboards/variables/) -- 类型：文章，时长：15 分钟
- [Grafana 面板类型概览](https://grafana.com/docs/grafana/latest/panels-visualizations/) -- 类型：文章，时长：10 分钟
- [实用监控（O'Reilly）](https://www.oreilly.com/library/view/practical-monitoring/9781491957349/) -- 类型：书籍，时长：300 分钟

<!-- ZH_UI -->
1. 设置 Grafana 并连接到你的指标源（Prometheus 或 CloudWatch）
2. 构建一个展示四大黄金信号的服务仪表盘
3. 理解何时使用时序面板、统计面板和表格
4. 了解什么样的仪表盘有用、什么样的仪表盘嘈杂
5. 我的仪表盘有 40 个面板，但我仍然无法一眼看出系统是否健康。我做错了什么？
6. 我只是想到什么有用的指标就加一个面板。现在满屏都是图表，出故障时我得逐个扫过去找显示问题的那个。这感觉没什么用。
7. 我的仪表盘看起来很棒。但我没法 24/7 盯着它。出问题时怎么收到通知？
8. 再好的仪表盘，没人看也没用。我们遇到过问题一直可见的情况——只是碰巧没打开仪表盘。我需要让系统主动来找我。
