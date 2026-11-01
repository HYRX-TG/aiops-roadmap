---
id: database-write-scaling
title: Scaling Database Writes
zone: scaling
edges:
  to:
    - id: application-caching
      question: Writes are distributed. But I'm still hitting the database on every request for the same product listings and user profiles. How do I stop that?
      detail: >-
        Sharding took the write pressure off any single node. But reads are
        still hammering the database on every request — the same product
        listing query, the same user profile fetch, over and over. The next
        lever is keeping hot data in memory so it never reaches the database
        at all.
difficulty: 3
tags:
  - sharding
  - partitioning
  - database
  - write-scaling
  - postgres
  - mysql
  - distributed-systems
category: concept
milestones:
  - Explain what a write bottleneck looks like (CPU on primary, growing replication lag)
  - Know the difference between horizontal partitioning (sharding) and vertical partitioning
  - Explain what a shard key is and why choosing it badly is a one-way door
  - Understand what cross-shard queries are and why they are expensive
  - Know what to try before sharding (connection pooling, read replicas, caching)
  - Know how managed databases (Aurora, CockroachDB, Spanner) abstract some of this
title_zh: "扩展数据库写入"

---


Read replicas address the read side of database scaling, but all writes still go to one primary. At some point — and this point comes much later than most people expect, usually after they've exhausted caching, connection pooling, and query optimization — the primary becomes a bottleneck. Write scaling is genuinely hard. The options involve significant trade-offs and architectural complexity.

<!-- DEEP_DIVE -->

## Before you shard: exhaust other options

Sharding is a one-way door with serious long-term costs. Before going there:

**Connection pooling** (PgBouncer): each application server maintains its own connection pool, but many connections from many servers quickly hit Postgres's max_connections. PgBouncer multiplexes many application connections onto far fewer database connections, dramatically reducing connection overhead on the primary.

**Query optimization**: a slow query that scans a table of 100M rows and takes 500ms on every request is a much bigger write bottleneck than the writes themselves. Profile your query patterns. Add indexes. Rewrite N+1 queries.

**Caching**: every read you serve from Memcache or Redis is a read that doesn't hit the database, freeing CPU on the primary for writes. High read-to-write ratios make caching the most effective scaling lever.

**Vertical scaling**: upgrading the primary to a larger instance (more CPU, faster disk, more RAM for buffer cache) is often the right short-term answer. Managed databases like Aurora can handle very large workloads on a single primary.

## Horizontal write scaling: partitioning

When the primary truly cannot keep up and vertical scaling has limits, horizontal write scaling means distributing data across multiple database nodes — each node owns a subset of the data.

**Vertical partitioning** (sometimes called functional partitioning): move different tables to different databases. User data on one cluster, product catalog on another, orders on a third. Each database handles a subset of the write workload. This is the least invasive approach — application code routes writes to the right database by domain, but each database is a standard, unsharded Postgres.

**Horizontal partitioning (sharding)**: split a single large table across multiple nodes by a shard key. Orders with user_id < 1,000,000 go to shard 1; orders with user_id >= 1,000,000 go to shard 2. Each shard is an independent database that knows nothing about the others.

## The shard key problem

Choosing a shard key is the most consequential decision in a sharded architecture. A bad shard key is nearly impossible to change later.

Good shard keys distribute writes evenly. Bad ones create hotspots: if you shard orders by `created_at` date, all writes today go to the "today" shard while old shards sit idle.

**Cross-shard queries**: sharding breaks any query that needs data from multiple shards. A `JOIN` between orders and users is trivial in a single database; in a sharded system it requires the application to query multiple shards and merge results. Reporting, aggregations, and analytics become dramatically harder.

## Managed alternatives to DIY sharding

**Amazon Aurora**: Postgres/MySQL-compatible with a custom distributed storage layer. Supports up to 128 TB and separates read/write scaling. Not true multi-primary sharding, but handles far larger workloads than standard RDS.

**CockroachDB / Google Spanner**: distributed SQL databases that handle sharding transparently. Writes scale across nodes; you still write standard SQL; cross-shard queries work. The trade-off is higher latency for strongly-consistent operations.

For most applications at realistic scale, exhausting caching and connection pooling, combined with Aurora for its extended storage ceiling, is the right path. Reserve manual sharding for the small number of workloads that genuinely need it.

<!-- RESOURCES -->

- [Designing Data-Intensive Applications - Ch. 6 (Partitioning)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- type: book, time: 1h
- [Amazon Aurora Overview](https://aws.amazon.com/rds/aurora/) -- type: article, time: 15m
- [CockroachDB - How It Works](https://www.cockroachlabs.com/docs/stable/architecture/overview.html) -- type: docs, time: 20m
- [Instagram Sharding at Scale (engineering blog)](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
读副本解决了数据库扩展中读操作的问题，但所有写操作仍然指向单一主库。在某个时刻——这个时刻比大多数人预期的要晚得多，通常是在他们已经用尽了缓存、连接池和查询优化之后——主库会成为瓶颈。写扩展确实很难。可选方案涉及重大的权衡和架构复杂性。

<!-- ZH_DEEP_DIVE -->
## 分片之前：先穷尽其他方案

分片是一扇单向门，会带来严重的长期成本。在走到那一步之前：

**连接池**（PgBouncer）：每个应用服务器维护自己的连接池，但来自多台服务器的大量连接会很快触及 Postgres 的 max_connections 上限。PgBouncer 将大量应用连接多路复用到远少于其数量的数据库连接上，大幅降低主库的连接开销。

**查询优化**：一条扫描 1 亿行表、每次请求耗时 500ms 的慢查询，造成的写入瓶颈远大于写入本身。分析你的查询模式。添加索引。重写 N+1 查询。

**缓存**：每一次从 Memcache 或 Redis 提供的读，都是一次不落到数据库的读，从而为主库腾出 CPU 用于写入。高读写比使缓存成为最有效的扩展杠杆。

**垂直扩展**：将主库升级到更大的实例（更多 CPU、更快的磁盘、更多用于缓冲缓存的 RAM）往往是正确的短期答案。像 Aurora 这样的托管数据库可以在单个主库上承载非常大的工作负载。

## 水平写入扩展：分区

当主库确实无法跟上、且垂直扩展已到极限时，水平写入扩展意味着将数据分布到多个数据库节点上——每个节点拥有数据的一个子集。

**垂直分区**（有时称为功能分区）：将不同的表迁移到不同的数据库。用户数据在一个集群，商品目录在另一个，订单在第三个。每个数据库处理写入工作负载的一个子集。这是侵入性最小的方式——应用代码按领域将写入路由到正确的数据库，但每个数据库都是标准的、未分片的 Postgres。

**水平分区（分片）**：按分片键将一张大表拆分到多个节点。user_id < 1,000,000 的订单进入分片 1；user_id >= 1,000,000 的订单进入分片 2。每个分片都是一个独立的数据库，对其他分片一无所知。

## 分片键问题

选择分片键是分片架构中影响最深远的决策。糟糕的分片键几乎不可能在事后更改。

好的分片键能均匀分布写入。糟糕的分片键会制造热点：如果按 `created_at` 日期对订单分片，今天的所有写入都会进入“今天”分片，而旧分片则闲置。

**跨分片查询**：分片会破坏任何需要从多个分片获取数据的查询。订单与用户之间的 `JOIN` 在单个数据库中轻而易举；在分片系统中，它需要应用查询多个分片并合并结果。报表、聚合和分析会变得极其困难。

## DIY 分片的托管替代方案

**Amazon Aurora**：兼容 Postgres/MySQL，采用定制的分布式存储层。支持高达 128 TB，并将读/写扩展分离。它不是真正的多主分片，但能承载比标准 RDS 大得多的工作负载。

**CockroachDB / Google Spanner**：透明处理分片的分布式 SQL 数据库。写入可跨节点扩展；你仍然编写标准 SQL；跨分片查询可以工作。代价是强一致性操作的延迟更高。

对于大多数处于现实规模的应用，穷尽缓存和连接池，再结合 Aurora 扩展后的存储上限，就是正确的路径。把手动分片留给极少数真正需要它的工作负载。

<!-- ZH_RESOURCES -->
- [Designing Data-Intensive Applications - 第 6 章（分区）](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- 类型: 书籍, 时间: 1h
- [Amazon Aurora 概述](https://aws.amazon.com/rds/aurora/) -- 类型: 文章, 时间: 15m
- [CockroachDB - 工作原理](https://www.cockroachlabs.com/docs/stable/architecture/overview.html) -- 类型: 文档, 时间: 20m
- [Instagram 大规模分片（工程博客）](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c) -- 类型: 文章, 时间: 10m

<!-- ZH_UI -->
1. 解释写瓶颈的表现（主库 CPU 高、复制延迟增长）
2. 了解水平分区（分片）与垂直分区的区别
3. 解释什么是分片键，以及为什么选错分片键是不可逆的
4. 理解什么是跨分片查询，以及为什么代价高昂
5. 了解分片前应先尝试什么（连接池、只读副本、缓存）
6. 了解托管数据库（Aurora、CockroachDB、Spanner）如何抽象掉其中一部分
7. 写入已经分散了。但我仍然在每个请求中为相同的商品列表和用户资料查询数据库。如何避免？
8. 分片减轻了单个节点的写入压力。但读取仍在每个请求中冲击数据库——相同的商品列表查询、相同的用户资料获取，反复发生。下一个手段是把热数据留在内存中，让它根本不会到达数据库。
