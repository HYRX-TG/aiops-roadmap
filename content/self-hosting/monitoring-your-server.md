---
id: monitoring-your-server
title: How Do I Know If Something Breaks?
zone: self-hosting
edges:
  to:
    - id: beszel
      question: I just want something simple that tells me when things are down
      detail: >-
        I don't need fancy dashboards or historical data. I want to open one
        page and see green or red — are my services up, is my disk getting
        full, is the CPU pegged. That's it.
    - id: prometheus-grafana
      question: I want real dashboards, metrics history, and alerting
      detail: >-
        I want to see graphs over time — when did memory usage spike, how has
        disk space trended over the last month, which container is eating all
        the CPU. And I want alerts when things go wrong, not just a status page.
difficulty: 1
tags:
  - self-hosting
  - monitoring
  - observability
  - uptime
category: concept
milestones:
  - Understand what server monitoring actually means (uptime, resources, logs)
  - Know the difference between simple monitoring and full observability
  - Decide which approach fits your needs
title_zh: "我如何知道是否有东西出故障了？"

---


You find out Jellyfin is down because someone texts you "the stream isn't working." You discover your disk is full because a new container won't start. You realize the server rebooted three days ago because the uptime counter reset.

This is monitoring by accident. It works until it doesn't — and when it doesn't, it's usually at the worst time.

<!-- DEEP_DIVE -->

## What monitoring actually means

At its simplest, monitoring answers three questions:

1. **Is it up?** — Are my services responding? Did something crash?
2. **Is it healthy?** — CPU, memory, disk — are any of them maxed out or trending toward trouble?
3. **What happened?** — When did the problem start? What changed?

You can answer these at different levels of depth, from "just tell me if something's down" to "show me every metric over the last 90 days with alerting rules."

## Simple monitoring vs full observability

**Simple monitoring** is a lightweight dashboard that shows you the current state of your server: CPU usage, memory, disk space, network, and whether your services are responding. You check it when you want, or it pings you when something's wrong. Beszel is a great example — one Docker container, minimal configuration, covers the basics.

**Full observability** means collecting metrics over time, storing them, querying them, building dashboards, and setting up alerts. Prometheus scrapes metrics from your services on a schedule, stores them in a time-series database, and Grafana turns that data into dashboards and alerts. It's more work to set up but gives you historical data and much more flexibility.

## Which do you need?

Be honest about this. If you have one server running a handful of services, Beszel or something similar is probably all you need. You'll know if something's down, you'll see if disk space is getting tight, and you won't spend a weekend configuring dashboards.

If you have multiple servers, want to track specific application metrics, or just enjoy building dashboards (no judgment), Prometheus + Grafana is the way to go. It's also what you'll encounter in professional environments, so there's learning value beyond the homelab.

Both are free, both run in Docker, and you can always start simple and upgrade later.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你发现 Jellyfin 挂了，是因为有人发短信告诉你“直播流用不了”。你发现磁盘满了，是因为一个新容器起不来。你意识到服务器三天前重启过，是因为 uptime 计数器被重置了。

这是靠偶然的监控。它能撑到撑不住为止——而一旦撑不住，通常都是最糟糕的时刻。

<!-- ZH_DEEP_DIVE -->
## 监控的真正含义

最简单的说，监控回答三个问题：

1. **它还在运行吗？** —— 我的服务有响应吗？有什么东西崩溃了吗？
2. **它健康吗？** —— CPU、内存、磁盘 —— 有哪个已经满载或正趋向出问题吗？
3. **发生了什么？** —— 问题是什么时候开始的？有什么变动？

你可以按不同的深度来回答这些问题，从“只要告诉我有没有东西挂了”到“给我看过去 90 天的每一项指标，并配上告警规则”。

## 简单监控 vs 完整可观测性

**简单监控**是一个轻量级仪表盘，展示服务器的当前状态：CPU 使用率、内存、磁盘空间、网络，以及你的服务是否有响应。你想看的时候就看一眼，或者出问题时它主动通知你。Beszel 就是一个很好的例子 —— 一个 Docker 容器、极少配置，覆盖基础需求。

**完整可观测性**意味着随时间采集指标、存储它们、查询它们、构建仪表盘并设置告警。Prometheus 按计划从你的服务抓取指标，存入时序数据库，Grafana 再把数据变成仪表盘和告警。搭建起来更费功夫，但能给你历史数据和更大的灵活性。

## 你需要哪一种？

对此要诚实。如果你只有一台服务器跑着几个服务，Beszel 或类似工具大概就够了。东西挂了你会知道，磁盘空间紧张了你会看到，而且不用花一个周末去配置仪表盘。

如果你有多台服务器、想追踪特定的应用指标，或者就是喜欢搭仪表盘（不做评判），那就选 Prometheus + Grafana。这也是你在专业环境中会遇到的东西，所以除了家庭实验室之外还有学习价值。

两者都免费，都能跑在 Docker 里，你随时可以先从简单的开始，之后再升级。

<!-- ZH_UI -->
1. 理解服务器监控的真正含义（正常运行时间、资源、日志）
2. 了解简单监控与完整可观测性之间的区别
3. 决定哪种方案适合你的需求
4. 我只想要一个简单的东西，在出问题时告诉我
5. 我不需要花哨的仪表盘或历史数据。我只想打开一个页面看到绿色或红色——我的服务是否在线、磁盘是否快满了、CPU 是否满载。仅此而已。
6. 我想要真正的仪表盘、指标历史和告警
7. 我想看到随时间变化的图表——内存使用何时飙升、磁盘空间在过去一个月如何变化、哪个容器占用了所有 CPU。而且我希望在出问题时收到告警，而不只是一个状态页面。
