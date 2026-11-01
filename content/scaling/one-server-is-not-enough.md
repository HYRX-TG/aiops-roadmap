---
id: one-server-is-not-enough
title: One Server Is Not Enough
zone: scaling
edges:
  to:
    - id: horizontal-vs-vertical-scaling
      question: >-
        My server can't keep up. Do I just make it bigger, or is that the
        wrong approach?
      detail: >-
        I've been bumping up CPU and RAM every few months but I feel like I'm
        running out of road — and if this server goes down, everything goes
        down. I don't know if I should keep scaling up or start thinking about
        this completely differently.
difficulty: 1
tags:
  - scaling
  - reliability
  - single-point-of-failure
  - availability
  - capacity
category: concept
milestones:
  - Identify the failure modes of a single-server deployment
  - Explain what a single point of failure is
  - Understand the difference between performance headroom and high availability
title_zh: "一台服务器不够用"

---


A single server is the simplest possible deployment. It's also the most fragile. When the store gets featured in a newsletter or hits the front page of a social media site and thousands of users arrive at once, the server hits its limits fast. This node is about understanding exactly what those limits are and why they matter before you start solving them.

<!-- DEEP_DIVE -->

## What actually breaks under load

When a server gets more traffic than it can handle, it doesn't gracefully slow down — it degrades unpredictably. CPU climbs toward 100%. The process queue backs up. MySQL starts queuing queries. Gunicorn workers exhaust their pool. Requests that would normally take 50ms start taking 5 seconds. Eventually the server starts dropping connections entirely or the OOM killer starts killing processes.

The particularly bad version: a traffic spike hits at 3 AM, crashes the server, and the store is down until someone wakes up and notices. With a single server there's no automatic recovery, no redundancy, and no graceful degradation.

## Two separate problems: performance headroom and availability

These are often confused but they're different problems with different solutions.

**Performance headroom** is about having enough capacity for expected traffic. A bigger server (more CPU, more RAM) can handle more concurrent users. But you're always chasing a ceiling — there's a maximum size for any single machine, and it's expensive.

**High availability** is about surviving failures. Even a server with infinite CPU will go down eventually: hardware fails, kernels crash, you need to apply security patches. If there's only one server, every failure is an outage.

Scaling up (a bigger server) helps with headroom but does nothing for availability. You need multiple servers to have real redundancy — and once you have multiple servers, you need a way to distribute traffic between them.

## Single points of failure

Every component in a single-server deployment is a single point of failure:
- The server itself (hardware, kernel, network interface)
- The MySQL process running on that server
- The Python app process
- Nginx
- The disk

Any one of these failing takes down the whole store simultaneously. The more components on one machine, the more ways that machine can fail.

## What you actually need

To handle more traffic *and* be resilient to failures, you need:
1. Multiple application servers that can each handle requests independently
2. Something in front to distribute traffic across them
3. Data stores (database, sessions) that are shared and accessible from any server

This is what the rest of the zone builds toward.

<!-- RESOURCES -->

- [The Architecture of Open Source Applications - Scalability](https://aosabook.org/en/v2/distsys.html) -- type: article, time: 30m
- [AWS EC2 Instance Types - Understanding vertical limits](https://aws.amazon.com/ec2/instance-types/) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
单台服务器是最简单的部署方式，也是最脆弱的。当商店被新闻简报推荐，或登上社交媒体首页，成千上万的用户同时涌入时，服务器很快就会达到极限。本节旨在让你在着手解决这些限制之前，先准确理解这些限制究竟是什么，以及它们为何重要。

<!-- ZH_DEEP_DIVE -->
## 负载下真正会崩溃的是什么

当服务器收到的流量超过其处理能力时，它不会优雅地减速——而是会不可预测地降级。CPU 攀升至 100%。进程队列积压。MySQL 开始排队查询。Gunicorn worker 耗尽连接池。原本只需 50ms 的请求开始耗时 5 秒。最终服务器开始完全丢弃连接，或者 OOM killer 开始杀死进程。

特别糟糕的情况是：凌晨 3 点流量高峰袭来，服务器崩溃，商店下线，直到有人醒来发现。单台服务器没有自动恢复、没有冗余、也没有优雅降级。

## 两个独立的问题：性能余量与可用性

这两个问题经常被混淆，但它们是不同的问题，需要不同的解决方案。

**性能余量**关乎为预期流量提供足够容量。更大的服务器（更多 CPU、更多内存）可以处理更多并发用户。但你总是在追逐天花板——任何单台机器都有最大规格，而且成本高昂。

**高可用性**关乎在故障中存活。即使一台拥有无限 CPU 的服务器最终也会宕机：硬件故障、内核崩溃、需要打安全补丁。如果只有一台服务器，每次故障都是停机。

纵向扩展（更大的服务器）有助于提升余量，但对可用性毫无帮助。你需要多台服务器才能实现真正的冗余——而一旦有了多台服务器，你就需要一种在它们之间分配流量的方式。

## 单点故障

单服务器部署中的每个组件都是单点故障：
- 服务器本身（硬件、内核、网络接口）
- 运行在该服务器上的 MySQL 进程
- Python 应用进程
- Nginx
- 磁盘

其中任何一个发生故障，都会同时拖垮整个商店。一台机器上的组件越多，这台机器可能故障的方式就越多。

## 你真正需要的东西

要处理更多流量*并且*具备故障韧性，你需要：
1. 多台能够各自独立处理请求的应用服务器
2. 前面有东西将流量分发到这些服务器
3. 共享的、可从任何服务器访问的数据存储（数据库、会话）

这就是本区域后续内容要构建的目标。

<!-- ZH_RESOURCES -->
- [开源应用架构 - 可扩展性](https://aosabook.org/en/v2/distsys.html) -- 类型: 文章, 时间: 30分钟
- [AWS EC2 实例类型 - 理解纵向扩展限制](https://aws.amazon.com/ec2/instance-types/) -- 类型: 文档, 时间: 10分钟

<!-- ZH_UI -->
1. 识别单服务器部署的故障模式
2. 解释什么是单点故障
3. 理解性能余量与高可用性的区别
4. 我的服务器跟不上了。是直接扩容就行，还是这个思路本身就不对？
5. 我每隔几个月就加 CPU 和内存，但感觉快到头了——而且这台服务器一挂，所有东西都挂。我不知道该继续纵向扩容，还是该彻底换个思路。
