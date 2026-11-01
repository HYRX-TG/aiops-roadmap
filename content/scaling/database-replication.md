---
id: database-replication
title: Database Replication
zone: scaling
edges:
  to:
    - id: replication-internals
      question: >-
        How does the replica actually stay in sync? What's happening under the
        hood?
      detail: >-
        When you add a read replica, the database engine streams every write
        from the primary using a binary log. Understanding this mechanism —
        replication lag, async vs sync, what 'eventually consistent' really
        means — helps you reason about what you can and can't do with replicas.
    - id: database-write-scaling
      question: Read replicas handle my reads. But write traffic is growing and the primary is showing CPU pressure. Adding more replicas doesn't help writes at all. What are my options?
      detail: >-
        All writes still go to one primary. I've offloaded reads to replicas
        but the primary is now the bottleneck — CPU is climbing, replication
        lag is growing. I can't just add another primary the way I added
        replicas. What does horizontal write scaling actually look like?
difficulty: 2
tags:
  - replication
  - database
  - read-replicas
  - multi-az
  - failover
  - lag
  - consistency
category: concept
milestones:
  - Explain the difference between synchronous and asynchronous replication
  - Describe what replication lag is and when it matters
  - Understand what happens to in-flight writes during a Multi-AZ failover
  - >-
    Know why you can't use a read replica as a direct failover target without
    promotion
title_zh: "数据库复制"

---


Database replication creates additional copies of your database that stay in sync with the primary. Read replicas let you distribute read-heavy queries across multiple database servers — product listings, search queries, reporting — while all writes still go to the primary. Multi-AZ deployments create a standby in another availability zone that can take over if the primary fails. Understanding the difference between these and how they interact is essential for building a database tier that handles real traffic.

<!-- DEEP_DIVE -->

## Read replicas

A read replica receives a continuous stream of changes from the primary and applies them, maintaining a copy of the data that is slightly behind the primary (replication lag). You configure your application to send reads to one or more replicas and writes to the primary.

```python
# Write to primary
primary_db.execute("INSERT INTO orders ...")

# Read from replica for non-critical reads
replica_db.execute("SELECT * FROM products WHERE ...")
```

On RDS, creating a read replica is a few clicks. RDS gives the replica its own endpoint (different hostname from the primary). You configure this in your application's database settings.

The key property: read replicas are **asynchronous**. Data written to the primary doesn't immediately appear on the replica — there's a delay (usually milliseconds, sometimes seconds under load). This is called **replication lag**.

## Multi-AZ

Multi-AZ is different from a read replica. With Multi-AZ enabled:
- RDS maintains a **standby** in a second availability zone
- Replication to the standby is **synchronous** — a write isn't acknowledged to your application until it's confirmed on both the primary and standby
- You **cannot** read from the standby — it exists only for failover
- If the primary fails (hardware failure, AZ outage), RDS automatically promotes the standby and updates the DNS endpoint — typically in 60-120 seconds

Multi-AZ increases write latency slightly (the synchronous replication adds a small amount of time for each write), but gives you automatic failover without data loss.

## The critical distinction

**Multi-AZ is for availability (surviving failures). Read replicas are for performance (distributing read load).** They're different features addressing different problems. In production, you typically want both:
- Multi-AZ for the primary: so a failure doesn't take you offline
- Read replicas for read scaling: so your product listing queries don't compete with your checkout queries

## Replication lag matters

Replication lag means replicas can serve slightly stale data. For most read patterns — browsing product listings, searching — this is acceptable. For others, it can cause bugs:

**The "read your own writes" problem**: a user submits a review, you confirm it and redirect them to the product page. If the product page reads from a replica that hasn't received the insert yet, the review isn't there. The user thinks their submission was lost.

Solutions:
- After a write, read from the primary for a brief window (1-2 seconds)
- Track which replica is "caught up enough" using `Seconds_Behind_Master`
- For critical reads after writes, always go to the primary

## Monitoring replication lag

Watch `ReplicaLag` (RDS CloudWatch metric) for your read replicas. It should normally be under 1 second. Spikes indicate the replica is falling behind — usually because a large write transaction hit the primary, or the replica instance is undersized. Sustained high lag means your replica is not safe to read from for any data that changes frequently.

<!-- RESOURCES -->

- [AWS RDS Read Replicas](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html) -- type: docs, time: 20m
- [AWS RDS Multi-AZ vs Read Replicas](https://aws.amazon.com/rds/features/multi-az/) -- type: article, time: 10m
- [Postgres Replication Lag - pganalyze](https://pganalyze.com/docs/log-insights/server/S10) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
数据库复制会创建数据库的额外副本，这些副本与主库保持同步。只读副本让你能够将读密集型查询（商品列表、搜索查询、报表）分散到多台数据库服务器上，而所有写入仍然发往主库。多可用区部署会在另一个可用区创建一个备用实例，在主库发生故障时可以接管。理解这两者的区别以及它们如何相互作用，对于构建能够应对真实流量的数据库层至关重要。

<!-- ZH_DEEP_DIVE -->
## 只读副本

只读副本从主库接收持续不断的变更流并应用这些变更，维护一份略微落后于主库的数据副本（复制延迟）。你需要配置应用程序，将读请求发送到一个或多个副本，将写请求发送到主库。

```python
# Write to primary
primary_db.execute("INSERT INTO orders ...")

# Read from replica for non-critical reads
replica_db.execute("SELECT * FROM products WHERE ...")
```

在 RDS 上，创建只读副本只需点击几下。RDS 会为副本分配独立的端点（主机名与主库不同）。你在应用程序的数据库设置中配置该端点。

关键特性：只读副本是**异步**的。写入主库的数据不会立即出现在副本上——存在延迟（通常是毫秒级，高负载时可能达到秒级）。这被称为**复制延迟**。

## 多可用区

多可用区与只读副本不同。启用多可用区后：
- RDS 会在第二个可用区维护一个**备用**实例
- 到备用实例的复制是**同步**的——只有当主库和备用实例都确认后，写入才会向应用程序返回成功
- 你**不能**从备用实例读取——它仅用于故障转移
- 如果主库发生故障（硬件故障、可用区中断），RDS 会自动将备用实例提升为主库并更新 DNS 端点——通常在 60-120 秒内完成

多可用区会略微增加写入延迟（同步复制会为每次写入增加少量时间），但能提供无数据丢失的自动故障转移。

## 关键区别

**多可用区用于可用性（承受故障）。只读副本用于性能（分散读负载）。** 它们是解决不同问题的不同特性。在生产环境中，你通常两者都需要：
- 为主库启用多可用区：这样故障不会导致服务离线
- 使用只读副本进行读扩展：这样商品列表查询不会与结账查询争抢资源

## 复制延迟很重要

复制延迟意味着副本可能提供略微陈旧的数据。对于大多数读取模式——浏览商品列表、搜索——这是可以接受的。对于其他场景，则可能导致 bug：

**“读己之写”问题**：用户提交了一条评论，你确认提交并将他们重定向到商品页面。如果商品页面从尚未收到该插入操作的副本读取，评论就不在那里。用户会认为他们的提交丢失了。

解决方案：
- 写入后，在短暂的时间窗口内（1-2 秒）从主库读取
- 使用 `Seconds_Behind_Master` 跟踪哪个副本“已足够追上”
- 对于写入后的关键读取，始终走主库

## 监控复制延迟

监控只读副本的 `ReplicaLag`（RDS CloudWatch 指标）。正常情况下应低于 1 秒。出现峰值表明副本正在落后——通常是因为主库上发生了大型写事务，或者副本实例规格不足。持续的高延迟意味着，对于任何频繁变更的数据，你的副本都不适合读取。

<!-- ZH_RESOURCES -->
- [AWS RDS 只读副本](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html) -- 类型: 文档, 时间: 20m
- [AWS RDS 多可用区 vs 只读副本](https://aws.amazon.com/rds/features/multi-az/) -- 类型: 文章, 时间: 10m
- [Postgres 复制延迟 - pganalyze](https://pganalyze.com/docs/log-insights/server/S10) -- 类型: 文章, 时间: 10m

<!-- ZH_UI -->
1. 解释同步复制与异步复制的区别
2. 描述什么是复制延迟以及何时需要关注
3. 理解多可用区故障转移期间进行中的写入会发生什么
4. 了解为什么不能将只读副本直接作为故障转移目标而不进行提升
5. 副本实际上如何保持同步？底层发生了什么？
6. 添加只读副本时，数据库引擎通过二进制日志流式传输主库的每次写入。理解这一机制——复制延迟、异步与同步、“最终一致”的真正含义——有助于你推断副本能做什么、不能做什么。
7. 只读副本处理我的读请求。但写入流量在增长，主库出现 CPU 压力。增加更多副本对写入毫无帮助。我有哪些选择？
8. 所有写入仍然流向一个主库。我已将读请求卸载到副本，但主库现在是瓶颈——CPU 持续攀升，复制延迟不断增大。我不能像添加副本那样直接再加一个主库。水平写入扩展实际上是什么样子？
