---
id: cache-aside-pattern
title: The Cache-Aside Pattern
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - cache-aside
  - lazy-loading
  - memcache
  - redis
  - caching-patterns
  - ttl
category: concept
milestones:
  - 'Implement cache-aside in Python: check cache → DB fallback → populate cache'
  - Understand what a cache hit and a cache miss look like in practice
  - Explain what TTL (time-to-live) is and how to choose an appropriate value
  - Know what happens to stale data when the source changes before TTL expires
title_zh: "旁路缓存模式"

---


Cache-aside (also called lazy loading) is the most common pattern for using a cache in application code. The cache doesn't do anything automatically — the application checks the cache, falls back to the database on a miss, and populates the cache itself. Understanding this pattern and getting the details right (key design, TTL, error handling) is most of what "using a cache correctly" means in practice.

<!-- DEEP_DIVE -->

## The pattern

Three steps, every time:

1. **Check the cache**: look up the cache key. If data is there (cache hit), return it immediately.
2. **Database fallback**: if the cache key is missing or expired (cache miss), fetch from the database.
3. **Populate the cache**: store the database result in the cache with a TTL, so the next request finds it.

```python
def get_product(product_id):
    key = f"product:{product_id}"

    # Step 1: check cache
    cached = cache.get(key)
    if cached is not None:
        return cached

    # Step 2: database fallback
    product = db.query("SELECT * FROM products WHERE id = %s", [product_id])

    # Step 3: populate cache
    cache.set(key, product, ttl=300)
    return product
```

## Cache key design

Cache keys need to be unique for each distinct result. Good key patterns:
- `product:{id}` — one entry per product
- `product_list:page:{page}:sort:{sort_by}` — one entry per distinct listing query
- `user:{id}:cart` — one entry per user's cart

Bad key patterns:
- `products` — too broad; maps to the whole table, hard to invalidate when one product changes
- `query:{raw_sql}` — keys become too long and include user-specific data that pollutes the cache

Namespace your keys (prefix with a category) to make batch invalidation easier and to avoid collisions when different parts of the app share a cache instance.

## Choosing a TTL

TTL is how long cached data is considered fresh before it expires and must be re-fetched. There's no universally right answer — it's a trade-off between freshness and cache effectiveness.

General guidelines:
- **High TTL (hours to days)**: data that rarely changes — product descriptions, category trees, static reference data
- **Medium TTL (minutes)**: product listings, prices (acceptable to be slightly stale)
- **Short TTL (seconds)**: anything you're not comfortable being stale but still want some caching benefit
- **No caching**: real-time data, user-specific highly mutable data (cart totals, live inventory)

When in doubt, start with a shorter TTL and increase it as you gain confidence in the data's stability.

## What cache misses cost

Every cache miss goes to the database. If your hit rate drops (e.g., after a cache restart, or because TTLs are too short), database load spikes. For a site that was previously getting 90% cache hits and seeing 10% of traffic hit the database, a cold cache suddenly means 10x more database queries. Design for this: keep TTLs long enough that most traffic hits cache, and be ready for cold-start load when you restart the cache or deploy a new version.

## Error handling

If the cache is unavailable, the application should fall back to the database and continue working (with degraded performance, not failure). Never let a cache outage become a site outage. Most cache client libraries have timeout settings — configure them to be short (50-100ms) so a slow cache doesn't block requests.

```python
try:
    cached = cache.get(key)
except CacheConnectionError:
    cached = None  # fall through to database
```

<!-- RESOURCES -->

- [Caching Patterns - AWS](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html) -- type: article, time: 15m
- [Redis - Caching Patterns](https://redis.io/docs/manual/patterns/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Cache-aside（也称为懒加载）是应用代码中使用缓存最常见的模式。缓存本身不会自动做任何事情——应用程序先检查缓存，未命中时回退到数据库，并由应用自身填充缓存。理解这一模式并把握其中的细节（键设计、TTL、错误处理），在实践中基本就等同于“正确使用缓存”。

<!-- ZH_DEEP_DIVE -->
## 模式

每次都是三个步骤：

1. **检查缓存**：查找缓存键。如果数据存在（缓存命中），立即返回。
2. **回退到数据库**：如果缓存键缺失或已过期（缓存未命中），从数据库获取。
3. **填充缓存**：将数据库结果以 TTL 存入缓存，以便下一次请求能够找到它。

```python
def get_product(product_id):
    key = f"product:{product_id}"

    # Step 1: check cache
    cached = cache.get(key)
    if cached is not None:
        return cached

    # Step 2: database fallback
    product = db.query("SELECT * FROM products WHERE id = %s", [product_id])

    # Step 3: populate cache
    cache.set(key, product, ttl=300)
    return product
```

## 缓存键设计

缓存键需要对每个不同的结果保持唯一。良好的键模式：
- `product:{id}` — 每个产品一个条目
- `product_list:page:{page}:sort:{sort_by}` — 每个不同的列表查询一个条目
- `user:{id}:cart` — 每个用户的购物车一个条目

糟糕的键模式：
- `products` — 过于宽泛；映射到整张表，当某个产品发生变化时难以失效
- `query:{raw_sql}` — 键会变得过长，并且包含用户特定的数据，会污染缓存

为键添加命名空间（用类别作为前缀），以便更容易进行批量失效，并避免应用的不同部分共享同一缓存实例时发生冲突。

## 选择 TTL

TTL 是缓存数据在被视为新鲜、直到过期并必须重新获取之前的时长。没有普遍正确的答案——这是在新鲜度与缓存有效性之间的权衡。

一般准则：
- **高 TTL（小时到天）**：很少变化的数据——产品描述、分类树、静态参考数据
- **中等 TTL（分钟）**：产品列表、价格（可以接受略微陈旧）
- **短 TTL（秒）**：任何你不希望陈旧但仍想获得一定缓存收益的数据
- **不缓存**：实时数据、用户特定的高度可变数据（购物车总计、实时库存）

拿不准时，先从较短的 TTL 开始，随着对数据稳定性的信心增加再逐步提高。

## 缓存未命中的代价

每次缓存未命中都会访问数据库。如果命中率下降（例如缓存重启后，或因为 TTL 太短），数据库负载就会激增。对于一个此前缓存命中率为 90%、只有 10% 的流量访问数据库的站点，冷缓存会突然意味着数据库查询量增加 10 倍。为此做好设计：保持 TTL 足够长，使大部分流量命中缓存，并为重启缓存或部署新版本时的冷启动负载做好准备。

## 错误处理

如果缓存不可用，应用应回退到数据库并继续工作（性能下降，而非失败）。绝不要让缓存故障变成站点故障。大多数缓存客户端库都有超时设置——将其配置得较短（50-100ms），这样缓慢的缓存不会阻塞请求。

```python
try:
    cached = cache.get(key)
except CacheConnectionError:
    cached = None  # fall through to database
```

<!-- ZH_RESOURCES -->
- [缓存模式 - AWS](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html) -- 类型: 文章, 时间: 15m
- [Redis - 缓存模式](https://redis.io/docs/manual/patterns/) -- 类型: 文档, 时间: 20m

<!-- ZH_UI -->
1. 在 Python 中实现 cache-aside：检查缓存 → 回退到数据库 → 填充缓存
2. 理解实践中缓存命中与缓存未命中的表现
3. 解释什么是 TTL（time-to-live）以及如何选择合适的值
4. 了解在 TTL 过期前源数据发生变化时，陈旧数据会怎样
