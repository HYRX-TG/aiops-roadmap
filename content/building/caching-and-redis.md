---
id: caching-and-redis
title: Caching & Redis
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: My app is fast and data-aware. Time to get it off my laptop.
      detail: >-
        My app works locally with the database and cache all running on my
        machine. But I have no idea how to make those three separate services
        work together on a real server. How do they find each other, and how do
        I actually get this running somewhere else?
difficulty: 2
tags:
  - caching
  - redis
  - memcached
  - performance
  - in-memory
category: concept
milestones:
  - 'Understand cache hit, cache miss, and TTL'
  - Set up Redis locally and use it to cache database queries
  - Identify what data in your application is worth caching
title_zh: "缓存与 Redis"

---


Your app has a product catalog page. Every time someone visits it, the app queries the database, fetches the same 200 products, serializes them to JSON, and sends them to the browser. The products barely change — maybe once a day. But the database does all that work for every single visitor, every single page load. Caching means storing that result somewhere fast (memory) so you only do the expensive work once.

<!-- DEEP_DIVE -->

**Caching** is storing the result of an expensive operation so you can reuse it. Instead of querying the database every time, you check the cache first. If the data is there (a **cache hit**), you return it instantly. If not (a **cache miss**), you query the database, store the result in the cache, and return it. Future requests get the cached version.

```python
import redis
import json

r = redis.Redis(host="localhost", port=6379)

def get_products():
    # Check cache first
    cached = r.get("products")
    if cached:
        print("Cache hit!")
        return json.loads(cached)

    # Cache miss — query database
    print("Cache miss, querying database...")
    products = db.query("SELECT * FROM products")

    # Store in cache for 5 minutes (300 seconds)
    r.setex("products", 300, json.dumps(products))
    return products
```

**Redis** is the most popular caching tool. It is an in-memory data store — all data lives in RAM, which is why it is fast. A database query might take 5-50 milliseconds. A Redis lookup takes 0.1-0.5 milliseconds. That difference adds up fast when you have thousands of users.

Redis is more than just a key-value cache. It supports multiple data structures:

```bash
# Strings — basic key-value
SET user:1:name "Alice"
GET user:1:name

# Hashes — like a mini dictionary per key
HSET user:1 name "Alice" email "alice@example.com" plan "premium"
HGET user:1 name

# Lists — ordered collections
LPUSH notifications:user:1 "New order received"
LRANGE notifications:user:1 0 -1

# Sets — unique collections
SADD online_users "alice" "bob" "charlie"
SISMEMBER online_users "alice"  # returns 1 (true)

# Sorted sets — ranked data
ZADD leaderboard 100 "alice" 85 "bob" 92 "charlie"
ZREVRANGE leaderboard 0 2  # top 3 scores
```

**TTL (Time To Live)** controls how long cached data stays valid. Set it too short and you hit the database too often. Set it too long and users see stale data. The right TTL depends on how often the data changes and how much staleness is acceptable:

- Product catalog: 5-15 minutes (changes rarely)
- User session data: 30 minutes (moderate)
- Real-time stock prices: 1-5 seconds (changes constantly)

**Cache invalidation** is famously one of the two hard problems in computer science. When the underlying data changes, you need to update or delete the cached version. The simplest approach: when you write to the database, delete the relevant cache key. The next read will trigger a cache miss and refresh the data.

```python
def update_product(product_id, new_data):
    db.execute("UPDATE products SET ... WHERE id = ?", product_id)
    # Invalidate the cache
    r.delete("products")
    r.delete(f"product:{product_id}")
```

**Memcached** is the other major caching tool. It is simpler than Redis — just key-value strings with TTL. No fancy data structures, no persistence, no clustering built-in. It is slightly faster than Redis for simple get/set operations, but Redis has largely taken over because of its versatility.

**What to cache** (and what not to):

- **Cache:** Data that is read often and written rarely (product listings, user profiles, configuration)
- **Cache:** Results of expensive computations (aggregated reports, search results)
- **Don't cache:** Data that must always be fresh (account balances, inventory counts for checkout)
- **Don't cache:** Data that is unique per request (personalized content with no shared patterns)

**Why SREs care:** Caching is one of the most common performance optimization tools. Redis going down can cascade into a thundering herd — every request suddenly hits the database, overwhelming it. Understanding cache behavior, monitoring hit rates, and planning for cache failures is core SRE work.

<!-- RESOURCES -->

- [Redis Documentation](https://redis.io/docs/) -- type: reference, time: varies
- [Try Redis (interactive tutorial)](https://try.redis.io/) -- type: interactive, time: 30m
- [Caching Strategies and How to Choose the Right One](https://codeahoy.com/2017/08/11/caching-strategies-and-how-to-choose-the-right-one/) -- type: article, time: 20m
- [Redis University (free)](https://university.redis.io/) -- type: course, time: varies

<!-- ZH_SUMMARY -->
你的应用有一个产品目录页面。每当有人访问它时，应用都会查询数据库、获取同样的 200 个产品、将它们序列化为 JSON，然后发送到浏览器。产品几乎不变——也许一天才变一次。但数据库却要为每一位访客、每一次页面加载都做所有这些工作。缓存意味着把这个结果存到某个快速的地方（内存）中，这样昂贵的工作就只需做一次。

<!-- ZH_DEEP_DIVE -->
**缓存（Caching）** 是指将开销较大的操作结果存储起来以便复用。与其每次都查询数据库，不如先检查缓存。如果数据存在（**缓存命中**），就立即返回。如果不存在（**缓存未命中**），则查询数据库，将结果存入缓存，然后返回。后续请求就会拿到缓存版本。

```python
import redis
import json

r = redis.Redis(host="localhost", port=6379)

def get_products():
    # Check cache first
    cached = r.get("products")
    if cached:
        print("Cache hit!")
        return json.loads(cached)

    # Cache miss — query database
    print("Cache miss, querying database...")
    products = db.query("SELECT * FROM products")

    # Store in cache for 5 minutes (300 seconds)
    r.setex("products", 300, json.dumps(products))
    return products
```

**Redis** 是最流行的缓存工具。它是一个内存数据存储——所有数据都存放在 RAM 中，这正是它速度快的原因。一次数据库查询可能需要 5-50 毫秒。一次 Redis 查找只需 0.1-0.5 毫秒。当你有成千上万的用户时，这种差异会迅速累积。

Redis 不仅仅是键值缓存。它支持多种数据结构：

```bash
# Strings — basic key-value
SET user:1:name "Alice"
GET user:1:name

# Hashes — like a mini dictionary per key
HSET user:1 name "Alice" email "alice@example.com" plan "premium"
HGET user:1 name

# Lists — ordered collections
LPUSH notifications:user:1 "New order received"
LRANGE notifications:user:1 0 -1

# Sets — unique collections
SADD online_users "alice" "bob" "charlie"
SISMEMBER online_users "alice"  # returns 1 (true)

# Sorted sets — ranked data
ZADD leaderboard 100 "alice" 85 "bob" 92 "charlie"
ZREVRANGE leaderboard 0 2  # top 3 scores
```

**TTL（Time To Live，生存时间）** 控制缓存数据的有效期。设置得太短，就会过于频繁地访问数据库。设置得太长，用户就会看到过期数据。合适的 TTL 取决于数据变化的频率以及可接受的过期程度：

- 产品目录：5-15 分钟（很少变化）
- 用户会话数据：30 分钟（中等）
- 实时股票价格：1-5 秒（持续变化）

**缓存失效（Cache invalidation）** 是计算机科学中著名的两大难题之一。当底层数据发生变化时，你需要更新或删除缓存版本。最简单的方法：写入数据库时，删除相关的缓存键。下一次读取将触发缓存未命中并刷新数据。

```python
def update_product(product_id, new_data):
    db.execute("UPDATE products SET ... WHERE id = ?", product_id)
    # Invalidate the cache
    r.delete("products")
    r.delete(f"product:{product_id}")
```

**Memcached** 是另一种主要的缓存工具。它比 Redis 更简单——只有带 TTL 的键值字符串。没有花哨的数据结构，没有持久化，没有内置集群。对于简单的 get/set 操作，它比 Redis 略快，但由于 Redis 的多功能性，Redis 已在很大程度上占据了主导地位。

**应该缓存什么**（以及不应该缓存什么）：

- **缓存：** 读多写少的数据（产品列表、用户资料、配置）
- **缓存：** 开销较大的计算结果（聚合报表、搜索结果）
- **不要缓存：** 必须始终保持最新的数据（账户余额、结账时的库存数量）
- **不要缓存：** 每个请求都唯一的数据（没有共享模式的个性化内容）

**为什么 SRE 关心：** 缓存是最常见的性能优化工具之一。Redis 宕机可能引发级联的惊群效应（thundering herd）——每个请求突然都打到数据库上，将其压垮。理解缓存行为、监控命中率、为缓存故障做规划，是 SRE 的核心工作。

<!-- ZH_RESOURCES -->
- [Redis 文档](https://redis.io/docs/) -- 类型：参考，时长：不定
- [试用 Redis（交互式教程）](https://try.redis.io/) -- 类型：交互式，时长：30 分钟
- [缓存策略以及如何选择正确的策略](https://codeahoy.com/2017/08/11/caching-strategies-and-how-to-choose-the-right-one/) -- 类型：文章，时长：20 分钟
- [Redis 大学（免费）](https://university.redis.io/) -- 类型：课程，时长：不定

<!-- ZH_UI -->
1. 理解缓存命中、缓存未命中和 TTL
2. 在本地搭建 Redis，并用它缓存数据库查询
3. 识别应用中哪些数据值得缓存
4. 我的应用运行快且能感知数据。是时候把它从我的笔记本上搬走了。
5. 我的应用在本地运行，数据库和缓存都在我的机器上。但我不知道如何让这三个独立服务在真实服务器上协同工作。它们如何找到彼此，我又该如何真正把它运行在别处？
