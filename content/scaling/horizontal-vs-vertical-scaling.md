---
id: horizontal-vs-vertical-scaling
title: Vertical vs Horizontal Scaling
zone: scaling
edges:
  to:
    - id: load-balancers
      question: >-
        Horizontal scaling sounds right. What do I need before I can add more
        servers?
      detail: >-
        If I add more servers, how does traffic actually get to them? I can't
        point my domain at ten IPs and hope it works out. Something has to sit
        in front and distribute requests. I don't really understand what that
        thing is or how it works.
difficulty: 1
tags:
  - scaling
  - vertical-scaling
  - horizontal-scaling
  - capacity-planning
  - architecture
category: concept
milestones:
  - Explain the ceiling problem with vertical scaling
  - Describe why horizontal scaling requires stateless application design
  - >-
    Give an example of a workload better suited to vertical vs horizontal
    scaling
title_zh: "纵向扩展与横向扩展"

---


When a server can't handle the load, you have two options: make the server bigger, or add more servers. These are called vertical scaling (scale up) and horizontal scaling (scale out). They have different costs, different limits, and different implications for how you design your application.

<!-- DEEP_DIVE -->

## Vertical scaling: make it bigger

Vertical scaling means upgrading the machine — more CPU cores, more RAM, faster disk. If you're on AWS, this means stopping the instance and changing to a larger instance type. This is the path of least resistance. You don't change any code, you don't change your architecture, you just pay more for a bigger box.

The problem is the ceiling. There is a largest VM in any cloud provider's catalog. You will hit it. And even before you hit the absolute limit, you run into diminishing returns: doubling CPU doesn't double throughput if your bottleneck is database queries, network I/O, or something else.

Vertical scaling also doesn't solve availability. A very powerful server that goes down is still down.

## Horizontal scaling: add more servers

Horizontal scaling means running the same application on multiple identical servers simultaneously and distributing traffic across them. This is the architecture that can theoretically scale to any load — you just keep adding servers.

But horizontal scaling has a prerequisite that vertical scaling doesn't: **your application must be stateless**.

If each server stores any local state — session data in files, user-uploaded images on disk, cached computation results in memory — then routing the same user to a different server breaks things. Two servers can't share local state. The application has to be written so that any server can handle any request at any time, because with a load balancer you can't control which server handles which request.

## What stateless means in practice

A stateless application stores all persistent state in shared, external systems:
- **Sessions** in Redis or a database (not in a file on the server's filesystem)
- **Uploaded files** in object storage (S3, GCS) (not on the server's local disk)
- **Application configuration** via environment variables or a config service (not hardcoded per-instance)

The server itself becomes disposable. You can start it, kill it, replace it, and it doesn't matter — it has no unique state that would be lost.

## When to use which

Vertical scaling is appropriate for stateful workloads that are hard to distribute: databases, certain caches, memory-intensive batch jobs. You can't just add another Postgres primary — distributed databases require significant application changes. Vertical scaling buys you time.

Horizontal scaling is appropriate for stateless web application tiers. Once you've made your app stateless, running three servers instead of one is straightforward and gives you both more capacity and automatic redundancy.

Most production systems use both: vertical scaling for databases (within limits), horizontal scaling for application servers.

<!-- RESOURCES -->

- [Scaling Up vs Scaling Out - Digital Ocean](https://www.digitalocean.com/community/tutorials/5-common-server-setups-for-your-web-application) -- type: article, time: 15m
- [The Twelve-Factor App - Processes](https://12factor.net/processes) -- type: article, time: 10m
- [Designing Data-Intensive Applications - Chapter 1 (Reliability, Scalability, Maintainability)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- type: book, time: 45m

<!-- ZH_SUMMARY -->
当服务器无法承受负载时，你有两种选择：升级服务器配置，或增加更多服务器。这分别称为垂直扩展（纵向扩展）和水平扩展（横向扩展）。它们在成本、限制以及对应用设计的影响上各不相同。

<!-- ZH_DEEP_DIVE -->
## 垂直扩展：让它更大

垂直扩展意味着升级机器——更多 CPU 核心、更多内存、更快的磁盘。如果你在 AWS 上，这意味着停止实例并更换为更大的实例类型。这是阻力最小的路径。你不需要改任何代码，不需要改架构，只需为更大的机器付更多钱。

问题在于天花板。任何云厂商的目录中都有最大的 VM。你终将触及它。而且即使在你触及绝对上限之前，你也会遇到收益递减：如果你的瓶颈是数据库查询、网络 I/O 或其他因素，CPU 翻倍并不会让吞吐量翻倍。

垂直扩展也无法解决可用性。一台非常强大的服务器宕机了仍然是宕机。

## 水平扩展：增加更多服务器

水平扩展意味着在多台相同的服务器上同时运行同一个应用，并在它们之间分配流量。这种架构理论上可以扩展到任意负载——你只需不断添加服务器。

但水平扩展有一个垂直扩展没有的前提条件：**你的应用必须是无状态的**。

如果每台服务器存储任何本地状态——文件中的会话数据、磁盘上的用户上传图片、内存中的缓存计算结果——那么将同一用户路由到不同服务器就会出问题。两台服务器无法共享本地状态。应用必须被编写成任何服务器都能在任何时候处理任何请求，因为使用负载均衡器时你无法控制哪台服务器处理哪个请求。

## 无状态在实践中意味着什么

无状态应用将所有持久状态存储在共享的外部系统中：
- **会话**存储在 Redis 或数据库中（而不是服务器文件系统上的文件里）
- **上传的文件**存储在对象存储中（S3、GCS）（而不是服务器的本地磁盘上）
- **应用配置**通过环境变量或配置服务提供（而不是按实例硬编码）

服务器本身变得可丢弃。你可以启动它、杀掉它、替换它，都无所谓——它没有会丢失的唯一状态。

## 何时使用哪种

垂直扩展适用于难以分布的有状态工作负载：数据库、某些缓存、内存密集型批处理任务。你不能随便再加一个 Postgres 主库——分布式数据库需要大量的应用改动。垂直扩展为你争取时间。

水平扩展适用于无状态的 Web 应用层。一旦你让应用变为无状态，运行三台服务器而不是一台就很简单，并且同时给你更多容量和自动冗余。

大多数生产系统两者都用：数据库用垂直扩展（在限制范围内），应用服务器用水平扩展。

<!-- ZH_RESOURCES -->
- [纵向扩展与横向扩展 - Digital Ocean](https://www.digitalocean.com/community/tutorials/5-common-server-setups-for-your-web-application) -- 类型: 文章, 时长: 15m
- [十二要素应用 - 进程](https://12factor.net/processes) -- 类型: 文章, 时长: 10m
- [设计数据密集型应用 - 第 1 章（可靠性、可扩展性、可维护性）](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- 类型: 书籍, 时长: 45m

<!-- ZH_UI -->
1. 解释垂直扩展的天花板问题
2. 描述为什么水平扩展需要无状态应用设计
3. 举例说明更适合垂直扩展而非水平扩展的工作负载
4. 水平扩展听起来是对的。在增加更多服务器之前我需要什么？
5. 如果我增加更多服务器，流量实际上如何到达它们？我不能把域名指向十个 IP 然后指望它能正常工作。必须有东西坐在前面分发请求。我不太理解那个东西是什么或它如何工作。
