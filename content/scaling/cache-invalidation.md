---
id: cache-invalidation
title: 'Cache Invalidation: The Hard Problem'
zone: scaling
edges:
  to: []
difficulty: 3
tags:
  - cache-invalidation
  - ttl
  - consistency
  - memcache
  - redis
  - stale-data
  - caching
category: concept
milestones:
  - Understand the difference between TTL-based expiry and active invalidation
  - Explain what 'stale data' means and when it's acceptable vs a real problem
  - 'Implement event-driven cache invalidation: clear the cache key on write'
  - Understand the cache stampede problem and one way to mitigate it
  - Know the trade-off between consistency and cache effectiveness
title_zh: "缓存失效：难题"

---


Phil Karlton's famous quote — "there are only two hard things in computer science: cache invalidation and naming things" — is overused but accurate. Keeping a cache consistent with its source of truth is genuinely difficult. When do you update it? What if the update fails? What if ten servers all miss the cache at once? This node covers the main strategies and the failure modes.

<!-- DEEP_DIVE -->

## The consistency problem

A cache is a copy of data. The source of truth is the database. The moment you cache something, the copy and the source can diverge: someone updates the product price in the database, but the old price is still in the cache. Users see stale data.

TTL-based expiry handles this eventually: after the TTL expires, the cache fetches fresh data. But "eventually" might be 5 minutes, or an hour, depending on your TTL. For a price update, 5 minutes of incorrect prices could mean real money.

## Strategy 1: TTL-only (passive invalidation)

Set a TTL and let data expire naturally. The simplest approach. Suitable for data where being slightly stale is acceptable — product descriptions, category trees, marketing content.

The problem: staleness windows are fixed. If your TTL is 10 minutes and someone updates a price, some users see the wrong price for up to 10 minutes. You can't shorten this without increasing database load.

## Strategy 2: Write-through invalidation (active invalidation)

When data changes, immediately delete or update the cache entry.

```python
def update_product_price(product_id, new_price):
    db.execute("UPDATE products SET price = %s WHERE id = %s", [new_price, product_id])
    cache.delete(f"product:{product_id}")  # invalidate immediately
```

The next request for that product is a cache miss, fetches fresh data from the database, and repopulates the cache. This keeps the cache much more consistent.

**The problem: cache stampede.** If you have a very popular item — say the homepage featured product — and you invalidate it, hundreds of simultaneous requests all miss the cache at once. They all go to the database simultaneously to fetch the same row. This can spike database load dramatically right at the moment when a popular item was just updated (which is often a high-traffic moment).

## Mitigating cache stampedes

**Probabilistic early expiration**: before the TTL actually expires, start occasionally fetching a fresh value. When a cache hit occurs, with some small probability, treat it as a miss and refresh in the background. This staggers refreshes instead of having them all happen simultaneously.

**Mutex/lock on cache miss**: when a cache miss occurs, only one process fetches from the database. Others wait briefly and retry. If the cache is populated by the time they retry, they get a cache hit. If not, they fall through to the database too.

```python
def get_product(product_id):
    key = f"product:{product_id}"
    cached = cache.get(key)
    if cached:
        return cached

    # Try to acquire a lock
    lock_key = f"lock:{key}"
    if cache.add(lock_key, "1", ttl=5):  # atomic: only one writer wins
        product = db.query(...)
        cache.set(key, product, ttl=300)
        cache.delete(lock_key)
    else:
        # Another process is fetching, wait and retry
        time.sleep(0.05)
        product = cache.get(key) or db.query(...)

    return product
```

## Strategy 3: event-driven invalidation

For complex applications, a write to the database publishes an event (to a queue, a pub/sub system, or a webhook). Cache invalidation logic subscribes to these events and clears the relevant cache keys. This decouples invalidation from the write path and works well when the same data is cached in multiple keys or across multiple cache instances.

## The consistency trade-off

No caching strategy achieves perfect consistency at zero cost. The choice is always: how stale is acceptable, and how much database load can you afford on invalidation? Most production systems use TTL-based invalidation for data that can be slightly stale, combined with active invalidation for data where freshness matters (prices, inventory counts, user-specific data).

<!-- RESOURCES -->

- [Caching Strategies - AWS Database Blog](https://aws.amazon.com/blogs/database/database-caching-strategies-using-redis/) -- type: article, time: 20m
- [Cache Stampede Problem - Redis Documentation](https://redis.io/docs/manual/patterns/distributed-locks/) -- type: docs, time: 15m
- [Designing Data-Intensive Applications - Ch. 5 (Replication, eventual consistency)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- type: book, time: 45m

<!-- ZH_SUMMARY -->
Phil Karlton 有一句名言：“计算机科学中只有两件难事：缓存失效和命名。”这句话虽然被用滥了，但确实准确。让缓存与它的真实数据源保持一致，确实非常困难。什么时候更新缓存？如果更新失败怎么办？如果十台服务器同时缓存未命中怎么办？本节将介绍主要的策略和失效模式。

<!-- ZH_DEEP_DIVE -->
## 一致性问题

缓存是数据的副本。数据的真实来源是数据库。一旦你缓存了某些内容，副本和来源就可能出现分歧：有人在数据库中更新了商品价格，但缓存中仍然是旧价格。用户看到的是过期数据。

基于 TTL 的过期机制最终会处理这个问题：TTL 过期后，缓存会获取最新数据。但“最终”可能是 5 分钟，也可能是 1 小时，取决于你的 TTL。对于价格更新来说，5 分钟的错误价格可能意味着真金白银的损失。

## 策略 1：仅 TTL（被动失效）

设置一个 TTL，让数据自然过期。这是最简单的方法。适用于可以接受轻微过期的数据——商品描述、分类树、营销内容。

问题在于：过期窗口是固定的。如果你的 TTL 是 10 分钟，有人更新了价格，部分用户会在长达 10 分钟内看到错误的价格。你无法在不增加数据库负载的情况下缩短这个时间。

## 策略 2：写穿透失效（主动失效）

当数据发生变化时，立即删除或更新缓存条目。

```python
def update_product_price(product_id, new_price):
    db.execute("UPDATE products SET price = %s WHERE id = %s", [new_price, product_id])
    cache.delete(f"product:{product_id}")  # invalidate immediately
```

对该商品的下一次请求会缓存未命中，从数据库获取最新数据，并重新填充缓存。这使缓存的一致性大大提高。

**问题在于：缓存击穿。** 如果你有一个非常热门的商品——比如首页推荐商品——而你使其失效，数百个并发请求会同时缓存未命中。它们会同时涌向数据库获取同一行数据。这可能在热门商品刚被更新的时刻（这通常是高流量时刻）导致数据库负载急剧飙升。

## 缓解缓存击穿

**概率性提前过期**：在 TTL 真正过期之前，开始偶尔获取新值。当发生缓存命中时，以很小的概率将其视为未命中并在后台刷新。这将刷新操作分散开来，而不是让它们同时发生。

**缓存未命中时加互斥锁**：当发生缓存未命中时，只有一个进程从数据库获取数据。其他进程短暂等待后重试。如果它们重试时缓存已被填充，就会命中缓存。如果还没有，它们也会落到数据库。

```python
def get_product(product_id):
    key = f"product:{product_id}"
    cached = cache.get(key)
    if cached:
        return cached

    # Try to acquire a lock
    lock_key = f"lock:{key}"
    if cache.add(lock_key, "1", ttl=5):  # atomic: only one writer wins
        product = db.query(...)
        cache.set(key, product, ttl=300)
        cache.delete(lock_key)
    else:
        # Another process is fetching, wait and retry
        time.sleep(0.05)
        product = cache.get(key) or db.query(...)

    return product
```

## 策略 3：事件驱动的失效

对于复杂的应用，对数据库的写入会发布一个事件（到队列、发布/订阅系统或 webhook）。缓存失效逻辑订阅这些事件并清除相关的缓存键。这将失效与写入路径解耦，当同一数据被缓存在多个键中或跨多个缓存实例时效果很好。

## 一致性的权衡

没有任何缓存策略能以零成本实现完美的一致性。选择始终是：多大的过期程度可以接受，以及失效时你能承受多少数据库负载？大多数生产系统对可以轻微过期的数据使用基于 TTL 的失效，并结合对新鲜度重要的数据（价格、库存数量、用户特定数据）使用主动失效。

<!-- ZH_RESOURCES -->
- [缓存策略 - AWS 数据库博客](https://aws.amazon.com/blogs/database/database-caching-strategies-using-redis/) -- 类型: 文章, 时间: 20m
- [缓存踩踏问题 - Redis 文档](https://redis.io/docs/manual/patterns/distributed-locks/) -- 类型: 文档, 时间: 15m
- [设计数据密集型应用 - 第 5 章（复制、最终一致性）](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- 类型: 书籍, 时间: 45m

<!-- ZH_UI -->
1. 理解基于 TTL 的过期与主动失效之间的区别
2. 解释“陈旧数据”的含义，以及何时可接受、何时是真正的问题
3. 实现事件驱动的缓存失效：写入时清除缓存键
4. 理解缓存击穿问题及其一种缓解方式
5. 了解一致性与缓存有效性之间的权衡
