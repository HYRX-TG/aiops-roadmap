---
id: redis-scaling
title: Scaling Redis
zone: scaling
edges:
  to:
    - id: connection-pooling
      question: Redis is clustered and stable. Now the database is complaining — every app server is maintaining its own connection pool and I'm hitting the connection limit.
      detail: >-
        Fixing Redis took the session pressure off. But now I have a fleet of
        app servers and each one maintains its own persistent connection pool
        to the database. The connection count grows faster than the load, and
        I keep hitting Postgres's hard max_connections ceiling.
difficulty: 2
tags:
  - redis
  - redis-cluster
  - elasticache
  - memorystore
  - gcp
  - aws
  - high-availability
  - scaling
category: practice
milestones:
  - Understand why a single Redis node has memory and throughput limits
  - Set up an ElastiCache Redis Cluster (AWS) or Memorystore cluster (GCP)
  - Understand how Redis Cluster shards data across nodes
  - Understand what happens to sessions when a Redis node fails
  - Know the difference between Redis Cluster and Redis Sentinel
title_zh: "扩展 Redis"

---


A single Redis node handles millions of operations per second and stores data entirely in memory. For most applications, a single node with a replica is sufficient for years. But Redis is in-memory — there's a hard memory ceiling on any single machine. And a single Redis node with no replica is a single point of failure. When your session store or cache goes down, every user on the site is affected immediately.

<!-- DEEP_DIVE -->

## Why a single Redis node is eventually not enough

**Memory**: Redis is bounded by the RAM of the instance. A single `cache.r7g.large` ElastiCache node has 13 GB of memory. If your session store and application cache together need more than that — or if you want memory headroom to avoid eviction — you need to either upgrade to a larger instance or distribute data across multiple nodes.

**Throughput**: a single Redis node can handle hundreds of thousands of operations per second. This is a very high ceiling — most applications never hit it. But if you're caching every database result and handling millions of requests per minute, you can get there.

**Availability**: a single Redis node with no replica is a single point of failure. When it restarts (for maintenance, a crash, or an AZ event), your session store disappears. Every user on the site is logged out simultaneously. Your cache is empty, flooding the database.

## Redis replication: primary + replica

The simplest reliability improvement is a single replica with automatic failover. ElastiCache calls this "cluster mode disabled with replication" — one primary plus one or more read replicas in different AZs, with automatic failover.

If the primary fails, ElastiCache promotes a replica to primary and updates the configuration endpoint within minutes. Sessions that were active during the failover are lost (the primary's recent writes that hadn't replicated yet), but the store recovers automatically.

This is the right starting point for most production workloads.

## Redis Cluster: sharding across nodes

When you need more memory than one node provides, Redis Cluster distributes data across multiple primary nodes. Each primary owns a range of hash slots (Redis divides the keyspace into 16,384 slots). A key is deterministically assigned to a slot based on its name, and thus to a specific primary.

ElastiCache cluster mode enabled supports Redis Cluster. You specify how many shards (primaries) you want and how many replicas per shard. Data is automatically distributed. If one shard fails, its replica takes over.

The trade-off: Redis Cluster doesn't support multi-key operations across shards. Commands like `MGET` with keys on different shards fail. Lua scripts and transactions that touch multiple keys work only if all the keys hash to the same slot (use hash tags: `{user:123}:session` and `{user:123}:cart` both hash to the slot for `user:123`).

## Redis Sentinel

Redis Sentinel is an alternative high-availability approach for non-clustered Redis: a set of Sentinel processes monitors the primary and replicas, detects failures, and performs automatic failover without the application needing Redis Cluster. Sentinel is useful for self-managed Redis deployments. With ElastiCache, the managed service handles this — you don't configure Sentinel yourself.

## When to start worrying about scaling Redis

For session storage: the memory footprint per session is small (a few hundred bytes to a few KB). An `r7g.medium` with 6 GB can hold millions of sessions. You need to scale before you hit memory, not after — watch the `BytesUsedForCache` CloudWatch metric.

For application caching: monitor `CacheHits`, `CacheMisses`, and `Evictions`. When evictions start occurring frequently, Redis is running low on memory and evicting old keys to make room for new ones. Increase the instance size or add shards before this degrades your database hit rate.

<!-- RESOURCES -->

- [Redis Cluster Specification](https://redis.io/docs/reference/cluster-spec/) -- type: docs, time: 30m
- [AWS ElastiCache - Choosing Between Cluster Mode On and Off](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Replication.Redis-RedisCluster.html) -- type: docs, time: 15m
- [Redis Sentinel Documentation](https://redis.io/docs/management/sentinel/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
单个 Redis 节点每秒可处理数百万次操作，并将数据完全存储在内存中。对大多数应用而言，一个主节点加一个副本就足以支撑数年。但 Redis 是基于内存的——任何单机都有硬性的内存上限。而单个没有副本的 Redis 节点就是单点故障。当你的会话存储或缓存宕机时，站点上的每个用户都会立即受到影响。

<!-- ZH_DEEP_DIVE -->
## 为什么单个 Redis 节点最终会不够用

**内存**：Redis 受限于实例的 RAM。单个 `cache.r7g.large` ElastiCache 节点拥有 13 GB 内存。如果你的会话存储和应用缓存加起来需要超过这个量——或者你希望留出内存余量以避免淘汰——你需要么升级到更大的实例，要么将数据分布到多个节点上。

**吞吐量**：单个 Redis 节点每秒可以处理数十万次操作。这是一个非常高的上限——大多数应用永远达不到。但如果你缓存每一个数据库结果并每分钟处理数百万请求，你就有可能触及它。

**可用性**：没有副本的单个 Redis 节点是单点故障。当它重启时（因维护、崩溃或可用区事件），你的会话存储就消失了。网站上的每个用户会同时被登出。你的缓存为空，请求会涌向数据库。

## Redis 复制：主节点 + 副本

最简单的可靠性改进是使用带自动故障转移的单个副本。ElastiCache 称之为“禁用集群模式并启用复制”——一个主节点加上一个或多个位于不同可用区的只读副本，并支持自动故障转移。

如果主节点发生故障，ElastiCache 会将一个副本提升为主节点，并在几分钟内更新配置端点。故障转移期间活跃的会话会丢失（主节点尚未复制的最新写入），但存储会自动恢复。

对于大多数生产工作负载，这是正确的起点。

## Redis Cluster：跨节点分片

当你需要的内存超过单个节点所能提供的量时，Redis Cluster 会将数据分布到多个主节点上。每个主节点拥有一段哈希槽（Redis 将键空间划分为 16,384 个槽）。一个键会根据其名称被确定性地分配到一个槽，从而分配到特定的主节点。

ElastiCache 集群模式启用后支持 Redis Cluster。你可以指定想要多少个分片（主节点）以及每个分片有多少个副本。数据会自动分布。如果一个分片发生故障，它的副本会接管。

权衡之处：Redis Cluster 不支持跨分片的多键操作。像 `MGET` 这样键位于不同分片的命令会失败。涉及多个键的 Lua 脚本和事务只有在所有键都哈希到同一个槽时才能工作（使用哈希标签：`{user:123}:session` 和 `{user:123}:cart` 都会哈希到 `user:123` 对应的槽）。

## Redis Sentinel

Redis Sentinel 是非集群 Redis 的另一种高可用方案：一组 Sentinel 进程监控主节点和副本，检测故障，并执行自动故障转移，而应用无需使用 Redis Cluster。Sentinel 适用于自管理的 Redis 部署。使用 ElastiCache 时，托管服务会处理这些——你不需要自己配置 Sentinel。

## 何时开始担心 Redis 的扩展问题

对于会话存储：每个会话的内存占用很小（几百字节到几 KB）。一个拥有 6 GB 内存的 `r7g.medium` 可以容纳数百万个会话。你需要在触及内存上限之前进行扩展，而不是之后——请关注 `BytesUsedForCache` CloudWatch 指标。

对于应用缓存：监控 `CacheHits`、`CacheMisses` 和 `Evictions`。当淘汰开始频繁发生时，说明 Redis 内存不足，正在淘汰旧键以为新键腾出空间。在这一点降低你的数据库命中率之前，请增加实例大小或添加分片。

<!-- ZH_RESOURCES -->
- [Redis Cluster 规范](https://redis.io/docs/reference/cluster-spec/) -- 类型：文档，时长：30m
- [AWS ElastiCache - 在集群模式开启与关闭之间做选择](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Replication.Redis-RedisCluster.html) -- 类型：文档，时长：15m
- [Redis Sentinel 文档](https://redis.io/docs/management/sentinel/) -- 类型：文档，时长：20m

<!-- ZH_UI -->
1. 理解为什么单个 Redis 节点存在内存和吞吐量限制
2. 搭建 ElastiCache Redis Cluster（AWS）或 Memorystore 集群（GCP）
3. 理解 Redis Cluster 如何跨节点分片数据
4. 理解 Redis 节点故障时会话会发生什么
5. 了解 Redis Cluster 与 Redis Sentinel 的区别
6. Redis 已完成集群化并稳定运行。现在数据库开始告警——每个应用服务器都维护自己的连接池，我正触及连接数上限。
7. 修复 Redis 缓解了会话压力。但现在我有一批应用服务器，每台都维护自己到数据库的持久连接池。连接数增长快于负载，我不断触及 Postgres 的 max_connections 硬上限。
