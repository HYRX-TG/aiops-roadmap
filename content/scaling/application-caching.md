---
id: application-caching
title: Application Caching with Memcache
zone: scaling
edges:
  to:
    - id: cache-aside-pattern
      question: How exactly does my app code use Memcache? What's the pattern?
      detail: >-
        I have Memcache running but I'm not confident my code is using it
        correctly. Do I check the cache before every query? What happens on a
        miss? How long should I keep things cached before they go stale? I feel
        like I'm winging it and I'll regret it later.
    - id: cache-invalidation
      question: >-
        What happens when the underlying data changes? How do I keep the cache
        consistent?
      detail: >-
        We updated a product price and users were still seeing the old one for
        minutes. I flushed the cache to fix it, but that tanked the database
        immediately. I don't have a good mental model for how to keep cached
        data in sync when the source changes — and I'm worried it's going to
        bite us again.
    - id: reverse-proxy-caching
      question: Object caching requires instrumenting every query in my code. But a lot of traffic is for the exact same pages — can I cache full HTTP responses without touching application code?
      detail: >-
        Memcache requires me to touch every database call manually — it's not
        a small refactor, I have to instrument every query I want cached. But
        the homepage and top category pages are almost identical for every
        visitor and get hit thousands of times a minute. It feels wrong to run
        all of that through my Python processes when the response barely ever
        changes.
    - id: browser-caching
      question: My servers are still sending the same images, CSS, and JS on every single request. Can the browser just keep those?
      detail: >-
        Every page load fetches the same logo, stylesheet, and JavaScript bundle
        — even if nothing has changed since yesterday. There has to be a way to
        tell the browser it already has these and doesn't need to download them
        again.
difficulty: 2
tags:
  - memcache
  - memcached
  - caching
  - elasticache
  - memorystore
  - gcp
  - aws
  - object-cache
  - performance
category: practice
milestones:
  - Set up ElastiCache Memcached (AWS) or Memorystore Memcached (GCP)
  - Implement cache-aside for product listing and product detail pages
  - Measure the latency difference between a cache hit and a cache miss
  - Set appropriate TTLs for different types of data
  - Understand when to use Memcache vs Redis for object caching
title_zh: "使用 Memcache 进行应用缓存"

---


The database is where most web applications hit their first serious performance wall. Every product listing page runs a query. Every product detail page runs a query. If the same 100 products appear on the homepage and are requested by thousands of users per minute, the database answers the same query thousands of times with the same result. Application caching breaks this pattern by keeping hot data in memory so the database never gets asked the same question twice.

<!-- DEEP_DIVE -->

## What Memcache is

Memcache (specifically the Memcached daemon) is a simple, extremely fast in-memory key-value store. It stores arbitrary data keyed by a string — product listings, user profiles, rendered HTML fragments, whatever you want — entirely in RAM. A Memcache read is typically under 1 millisecond versus tens of milliseconds for a database query. It has no persistence and no disk I/O — everything lives in memory.

AWS offers Memcached as ElastiCache for Memcached. GCP has Memorystore for Memcached. Both are managed: you pick a node type, click create, and get a host:port to connect to.

## Object caching in practice

The pattern is: check cache first, fall back to the database on a miss, populate the cache for next time. For a product listing:

```python
cache_key = "product_list_page_1"
result = memcache_client.get(cache_key)

if result is None:
    result = db.query("SELECT * FROM products ORDER BY id LIMIT 20")
    memcache_client.set(cache_key, result, expire=300)  # cache for 5 minutes

return result
```

This is the cache-aside pattern, covered in its own node. The main decision here is how long to cache things (the TTL — time-to-live). Product listings that change infrequently can be cached for minutes. User-specific data like cart contents should not be cached this way at all.

## What to cache and what not to

Good candidates for object caching:
- Product listings and detail pages (same data for all users, changes infrequently)
- Category trees, navigation menus
- Expensive aggregation queries (total orders by day, top products)
- External API responses you don't want to hammer

Bad candidates:
- User-specific data (cart, order history) — each user needs different data, cache hit rate will be low
- Frequently mutating data — you'll spend as much time invalidating as you save
- Data that must be real-time (live inventory, auction prices)

## Measuring the impact

Before adding caching, measure your database query latency and throughput. After adding caching, look at:
- **Hit rate**: percentage of cache lookups that find data. Below 80% usually means you're caching the wrong things or TTLs are too short.
- **Database query rate**: should drop significantly for cached queries
- **p99 response time for cached endpoints**: should drop from tens of ms to single-digit ms

ElastiCache provides CloudWatch metrics for cache hits and misses out of the box.

## Memcache vs Redis for object caching

Memcache is simpler and faster for pure object caching. Redis supports richer data structures (sorted sets, hashes, pub/sub) and has persistence options. If you're already running Redis for sessions, using Redis for caching too reduces operational complexity. If you want maximum caching throughput and simplicity, dedicated Memcache nodes are slightly faster.

<!-- RESOURCES -->

- [AWS ElastiCache for Memcached](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/WhatIs.html) -- type: docs, time: 15m
- [pymemcache Python Client](https://pymemcache.readthedocs.io/) -- type: docs, time: 10m
- [Caching Best Practices - AWS](https://aws.amazon.com/caching/best-practices/) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
数据库是大多数 Web 应用首次遭遇严重性能瓶颈的地方。每个商品列表页都会执行一次查询。每个商品详情页也会执行一次查询。如果同样的 100 个商品出现在首页，并且每分钟有数千名用户请求它们，数据库就会用相同的结果回答相同的查询数千次。应用层缓存通过将热数据保留在内存中打破了这一模式，使数据库永远不会被问到同一个问题两次。

<!-- ZH_DEEP_DIVE -->
## Memcache 是什么

Memcache（具体来说是 Memcached 守护进程）是一个简单、极快的内存键值存储。它以字符串为键存储任意数据——商品列表、用户资料、渲染好的 HTML 片段，你想存什么都可以——全部放在 RAM 中。一次 Memcache 读取通常低于 1 毫秒，而数据库查询需要几十毫秒。它没有持久化，也没有磁盘 I/O——一切都在内存中。

AWS 以 ElastiCache for Memcached 的形式提供 Memcached。GCP 有 Memorystore for Memcached。两者都是托管服务：你选择节点类型，点击创建，然后得到一个可连接的 host:port。

## 实践中的对象缓存

模式是：先查缓存，未命中时回退到数据库，并为下次填充缓存。对于商品列表：

```python
cache_key = "product_list_page_1"
result = memcache_client.get(cache_key)

if result is None:
    result = db.query("SELECT * FROM products ORDER BY id LIMIT 20")
    memcache_client.set(cache_key, result, expire=300)  # cache for 5 minutes

return result
```

这就是 cache-aside 模式，在它自己的节点中有介绍。这里的主要决策是缓存多长时间（TTL——time-to-live）。变化不频繁的商品列表可以缓存几分钟。像购物车内容这样的用户特定数据则完全不应以这种方式缓存。

## 该缓存什么、不该缓存什么

适合对象缓存的候选：
- 商品列表和详情页（所有用户看到相同数据，变化不频繁）
- 分类树、导航菜单
- 昂贵的聚合查询（每日总订单数、热门商品）
- 你不想频繁请求的外部 API 响应

不适合的候选：
- 用户特定数据（购物车、订单历史）——每个用户需要不同的数据，缓存命中率会很低
- 频繁变更的数据——你在失效上花的时间会和节省的时间一样多
- 必须实时的数据（实时库存、拍卖价格）

## 衡量影响

在添加缓存之前，测量你的数据库查询延迟和吞吐量。添加缓存之后，关注：
- **命中率**：找到数据的缓存查找所占的百分比。低于 80% 通常意味着你缓存了错误的内容，或者 TTL 太短。
- **数据库查询速率**：对于被缓存的查询应显著下降
- **被缓存端点的 p99 响应时间**：应从几十毫秒降至个位数毫秒

ElastiCache 开箱即提供缓存命中和未命中的 CloudWatch 指标。

## 对象缓存：Memcache vs Redis

对于纯对象缓存，Memcache 更简单、更快。Redis 支持更丰富的数据结构（有序集合、哈希、pub/sub），并且有持久化选项。如果你已经为会话运行 Redis，那么也用 Redis 做缓存可以减少运维复杂性。如果你想要最大的缓存吞吐量和简单性，专用的 Memcache 节点会稍快一些。

<!-- ZH_RESOURCES -->
- [AWS ElastiCache for Memcached](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/WhatIs.html) -- 类型：文档，时长：15m
- [pymemcache Python 客户端](https://pymemcache.readthedocs.io/) -- 类型：文档，时长：10m
- [缓存最佳实践 - AWS](https://aws.amazon.com/caching/best-practices/) -- 类型：文章，时长：20m

<!-- ZH_UI -->
1. 搭建 ElastiCache Memcached（AWS）或 Memorystore Memcached（GCP）
2. 为商品列表页和商品详情页实现 cache-aside 模式
3. 测量缓存命中与缓存未命中之间的延迟差异
4. 为不同类型的数据设置合适的 TTL
5. 理解何时使用 Memcache 与 Redis 进行对象缓存
6. 我的应用代码究竟如何使用 Memcache？采用的是什么模式？
7. 我的 Memcache 已经在运行，但我不确定代码是否正确使用了它。我是否需要在每次查询前检查缓存？未命中时会发生什么？缓存数据在过期前应该保留多久？我感觉自己是在凭感觉做，以后会后悔。
8. 当底层数据发生变化时会发生什么？我如何保持缓存一致性？
9. 我们更新了商品价格，但用户仍然在几分钟内看到旧价格。我清空了缓存来修复，但这立刻压垮了数据库。对于源数据变化时如何保持缓存数据同步，我没有一个好的心智模型——我担心它还会再次给我们带来麻烦。
10. 对象缓存需要在代码中为每个查询埋点。但大量流量都指向完全相同的页面——我能否在不改动应用代码的情况下缓存完整的 HTTP 响应？
11. Memcache 要求我手动处理每一个数据库调用——这不是小规模重构，我必须为每个想要缓存的查询埋点。但首页和热门分类页对每个访客几乎完全相同，每分钟被访问数千次。把这些请求都跑一遍我的 Python 进程感觉不对，因为响应几乎从不变化。
12. 我的服务器仍然在每次请求时发送相同的图片、CSS 和 JS。浏览器能不能直接保留这些？
13. 每次页面加载都会获取相同的 logo、样式表和 JavaScript 包——即使从昨天起没有任何变化。一定有办法告诉浏览器它已经拥有这些内容，不需要再次下载。
