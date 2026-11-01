---
id: your-store-takes-off
title: Your Store Takes Off
zone: scaling
edges:
  to:
    - id: one-server-is-not-enough
      question: >-
        The store gets press coverage. Thousands of users show up at once. What
        breaks?
      detail: >-
        A single server has hard ceilings on CPU, memory, and connections. And
        if it crashes at 3 AM, the store is just down. Let's look at exactly
        what goes wrong — and why it goes wrong — before we talk about
        solutions.
difficulty: 1
tags:
  - example
  - python
  - mysql
  - single-vm
  - ecommerce
  - architecture
category: concept
milestones:
  - 'Understand the baseline stack: Python (Flask/FastAPI), MySQL, single VM'
  - Identify what each component does and why it exists
  - Understand why this setup works fine at small scale
title_zh: "你的商店起飞了"

---


You have a working e-commerce store. It runs on a single Linux VM: a Python web app (Flask or FastAPI), MySQL for the database, and Nginx in front. Everything is on one machine. Traffic is light, the app is fast, and life is good. This zone follows that store as it grows — and breaks — and gets rebuilt into something that can actually handle scale.

<!-- DEEP_DIVE -->

## The baseline stack

The store is a classic three-tier web application collapsed onto one box. Nginx receives incoming HTTP requests and proxies them to the Python app (running under Gunicorn or Uvicorn). The Python app does the business logic — looking up products, adding items to cart, processing checkouts. MySQL holds all the data: products, users, orders, inventory.

This setup works fine for hundreds of concurrent users. MySQL is fast for well-indexed relational queries. Python handles requests quickly enough. A single VM with 4 vCPUs and 8 GB of RAM can sustain surprising load if the app is reasonably efficient.

## Why single-server is fine — until it isn't

The fundamental problem with running everything on one machine is that it has hard limits. There's only so much CPU, memory, and network bandwidth. When you're at 10% utilization those limits feel irrelevant. When you're at 90% they feel very real, and you have no good options.

The second problem is reliability. If that one server has a bad disk, a kernel panic, a runaway process, or just needs an OS update — the store is down. There's no failover, no redundancy, no "the other server will take over." A single server is a single point of failure for every component simultaneously.

## What this zone covers

This zone works through the scaling problems you'd actually encounter as that store grows — adding a load balancer, solving the session problem, setting up auto-scaling, caching in multiple layers, scaling the database, handling background jobs, and protecting the API. Each node in the graph is a real problem you'll hit in roughly the order you'd hit it.

<!-- RESOURCES -->

- [AWS Well-Architected Framework - Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) -- type: docs, time: 30m
- [High Scalability - Real-world architecture case studies](http://highscalability.com/) -- type: article, time: varies
- [Designing Data-Intensive Applications (Kleppmann) - Chapter 1](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- type: book, time: 1h

<!-- ZH_SUMMARY -->
你有一个正常运营的电商店铺。它运行在一台 Linux 虚拟机上：一个 Python Web 应用（Flask 或 FastAPI）、MySQL 作为数据库，前面是 Nginx。所有东西都在一台机器上。流量不大，应用很快，一切都很顺利。本系列将跟随这家店铺一起成长、崩溃，并最终被重构成一个真正能够应对规模的东西。

<!-- ZH_DEEP_DIVE -->
## 基线架构

这个商店是一个经典的三层 Web 应用，全部折叠在一台机器上。Nginx 接收传入的 HTTP 请求，并将它们代理到 Python 应用（运行在 Gunicorn 或 Uvicorn 下）。Python 应用负责业务逻辑——查找商品、将商品加入购物车、处理结账。MySQL 保存所有数据：商品、用户、订单、库存。

这套配置对于数百个并发用户来说运行良好。MySQL 对于索引良好的关系型查询速度很快。Python 处理请求的速度足够快。如果应用效率合理，一台配备 4 个 vCPU 和 8 GB 内存的单一 VM 可以承受惊人的负载。

## 为什么单服务器没问题——直到它出问题

把所有东西都跑在一台机器上的根本问题在于它有硬性限制。CPU、内存和网络带宽都是有限的。当你处于 10% 利用率时，这些限制感觉无关紧要。当你处于 90% 时，它们就变得非常真实，而且你没有好的选择。

第二个问题是可靠性。如果那一台服务器出现坏盘、内核恐慌、失控进程，或者只是需要更新操作系统——商店就宕机了。没有故障转移，没有冗余，没有“另一台服务器会接管”。单台服务器同时是所有组件的单点故障。

## 本区域涵盖的内容

本区域将逐一处理随着商店增长你实际会遇到的扩展问题——添加负载均衡器、解决会话问题、设置自动扩缩容、多层缓存、扩展数据库、处理后台任务以及保护 API。图中的每个节点都是你会遇到的真实问题，大致按照你会遇到的顺序排列。

<!-- ZH_RESOURCES -->
- [AWS Well-Architected Framework - 可靠性支柱](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) -- 类型: 文档, 时间: 30分钟
- [High Scalability - 真实世界架构案例研究](http://highscalability.com/) -- 类型: 文章, 时间: 不定
- [Designing Data-Intensive Applications (Kleppmann) - 第1章](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- 类型: 书籍, 时间: 1小时

<!-- ZH_UI -->
1. 理解基线技术栈：Python（Flask/FastAPI）、MySQL、单台虚拟机
2. 明确每个组件的职责及其存在的原因
3. 理解为什么这套架构在小规模下运行良好
4. 商店获得媒体报道，成千上万的用户同时涌入。什么会崩溃？
5. 单台服务器在 CPU、内存和连接数上都有硬性上限。而且如果它在凌晨 3 点崩溃，商店就直接宕机了。在讨论解决方案之前，我们先看看究竟哪里会出问题——以及为什么会出问题。
