---
id: shared-sessions-redis
title: Shared Sessions with Redis
zone: scaling
edges:
  to:
    - id: auto-scaling-groups
      question: >-
        Sessions are in Redis. My app servers are now truly stateless. How do I
        auto-scale them?
      detail: >-
        With sessions out of the app servers, every server is identical and
        replaceable. AWS can spin up new instances and tear down old ones
        without losing user state. That's the prerequisite for Auto Scaling
        Groups to actually work.
    - id: jwt-and-cookie-sessions
      question: >-
        Wait — do I even need server-side sessions? What about JWT or signed
        cookies?
      detail: >-
        I've been assuming I need a session store, but I've seen other apps use
        tokens that just live in the browser with no server involved. How is
        that different, and should I be doing that instead?
difficulty: 2
tags:
  - redis
  - sessions
  - stateless
  - elasticache
  - memorystore
  - scaling
  - gcp
  - aws
category: practice
milestones:
  - 'Add Redis to your stack (ElastiCache on AWS, Memorystore on GCP)'
  - Configure your Python app to store sessions in Redis instead of on disk
  - Verify that two app servers share the same sessions correctly
  - Confirm the app works when one server is killed mid-session
title_zh: "与 Redis 共享会话"

---


The session problem goes away completely when session data lives outside the application servers. Any server can handle any request, because the session data isn't on the server — it's in a shared Redis instance that all servers can reach. This is the standard solution for horizontally scaled web applications.

<!-- DEEP_DIVE -->

## Why Redis for sessions

Redis is a fast, in-memory key-value store. Sessions are a natural fit: a session is a key (the session ID from the cookie) mapping to a value (the session data). Redis reads and writes are typically sub-millisecond, so adding a Redis lookup on every request doesn't noticeably add latency. Redis also supports TTL on keys, so sessions automatically expire without any cleanup logic in your app.

The other common options are storing sessions in the database (works fine, but slower than Redis and adds more query load) or in Memcached (also works, but Memcached doesn't persist to disk, so sessions are lost if the cache restarts).

## Setting it up

On AWS, use ElastiCache (managed Redis). On GCP, use Memorystore. On a bare VM or in Docker, run `redis-server` directly.

The application change is small. In Python with Flask-Session:

```python
from flask import Flask
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis.from_url("redis://your-redis-host:6379")
Session(app)
```

After this change, every call to `session["user_id"] = 123` writes to Redis, and every session read fetches from Redis. The server itself stores nothing about individual users.

## What this gives you

With sessions in Redis, your app servers are now genuinely stateless. Any server can handle any request, because they all read from and write to the same session store. The load balancer can route requests anywhere — round robin, least connections, it doesn't matter. You can spin up new servers at any time and they immediately serve traffic including existing sessions. You can kill any server without logging out any users.

This is the prerequisite for Auto Scaling Groups to work correctly. An ASG can spin up new instances during a traffic spike and kill them when traffic drops — but this only works if those instances can pick up sessions that started on other instances.

## Redis availability

One Redis instance is now a single point of failure for all your sessions. If it goes down, every user is logged out simultaneously. In production, run Redis with replication:

- **ElastiCache cluster mode disabled with replica**: one primary + one or more read replicas, automatic failover in minutes
- **ElastiCache cluster mode enabled**: data sharded across multiple primaries, each with replicas — more complex but needed for very large session stores

For most apps, a single ElastiCache instance with one replica (Multi-AZ enabled) is the right starting point. Sessions that were in-flight during a failover will be lost, but automatic failover takes 1-2 minutes and only loses sessions that were active at that moment.

<!-- RESOURCES -->

- [Flask-Session Documentation](https://flask-session.readthedocs.io/) -- type: docs, time: 15m
- [AWS ElastiCache for Redis](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html) -- type: docs, time: 20m
- [Redis Persistence and High Availability](https://redis.io/docs/management/replication/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当会话数据存储在应用服务器之外时，会话问题就完全消失了。任何服务器都能处理任何请求，因为会话数据不在服务器上——它位于所有服务器都能访问的共享 Redis 实例中。这是横向扩展 Web 应用的标准解决方案。

<!-- ZH_DEEP_DIVE -->
## 为什么用 Redis 存储会话

Redis 是一个快速的内存键值存储。会话天然适合用它：一个会话就是一个键（来自 cookie 的会话 ID）映射到一个值（会话数据）。Redis 的读写通常是亚毫秒级的，因此对每个请求增加一次 Redis 查询不会明显增加延迟。Redis 还支持键的 TTL，因此会话会自动过期，无需在应用中编写任何清理逻辑。

其他常见方案是将会话存储在数据库中（可行，但比 Redis 慢，且会增加更多查询负载），或存储在 Memcached 中（也可行，但 Memcached 不会持久化到磁盘，因此缓存重启时会丢失会话）。

## 配置

在 AWS 上，使用 ElastiCache（托管的 Redis）。在 GCP 上，使用 Memorystore。在裸 VM 或 Docker 中，直接运行 `redis-server`。

应用侧的改动很小。在 Python 中使用 Flask-Session：

```python
from flask import Flask
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis.from_url("redis://your-redis-host:6379")
Session(app)
```

完成此改动后，每次调用 `session["user_id"] = 123` 都会写入 Redis，每次读取会话都会从 Redis 获取。服务器本身不存储任何关于单个用户的信息。

## 这带来了什么

将会话存储在 Redis 中后，你的应用服务器现在真正做到了无状态。任何服务器都可以处理任何请求，因为它们都读写同一个会话存储。负载均衡器可以将请求路由到任何地方——轮询、最少连接，都无所谓。你可以随时启动新服务器，它们会立即开始处理流量，包括已有的会话。你可以杀掉任何服务器而不会让任何用户登出。

这是 Auto Scaling Groups 正常工作的前提条件。ASG 可以在流量高峰期间启动新实例，并在流量下降时杀掉它们——但这只有在这些实例能够接管在其他实例上开始的会话时才有效。

## Redis 的可用性

现在，一个 Redis 实例是所有会话的单点故障。如果它宕机，每个用户都会同时被登出。在生产环境中，应使用复制来运行 Redis：

- **ElastiCache 集群模式禁用并带副本**：一个主节点 + 一个或多个只读副本，几分钟内自动故障转移
- **ElastiCache 集群模式启用**：数据分片到多个主节点，每个主节点都有副本——更复杂，但对于非常大的会话存储是必要的

对于大多数应用，一个启用了 Multi-AZ 的 ElastiCache 实例加一个副本是合适的起点。故障转移期间正在处理的会话会丢失，但自动故障转移只需 1-2 分钟，且只会丢失那一刻活跃的会话。

<!-- ZH_RESOURCES -->
- [Flask-Session 文档](https://flask-session.readthedocs.io/) -- 类型：文档，时长：15m
- [AWS ElastiCache for Redis](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html) -- 类型：文档，时长：20m
- [Redis 持久化与高可用性](https://redis.io/docs/management/replication/) -- 类型：文档，时长：15m

<!-- ZH_UI -->
1. 将 Redis 加入你的技术栈（AWS 上用 ElastiCache，GCP 上用 Memorystore）
2. 配置你的 Python 应用，将会话存储在 Redis 中而不是磁盘上
3. 验证两台应用服务器能正确共享同一批会话
4. 确认当一台服务器在会话中途被杀死时应用仍能正常工作
5. 会话已存入 Redis。我的应用服务器现在真正无状态了。我该如何对它们做自动扩缩容？
6. 会话已从应用服务器中剥离，每台服务器都完全相同且可替换。AWS 可以启动新实例并销毁旧实例而不丢失用户状态。这正是 Auto Scaling Groups 能真正生效的前提。
7. 等等——我到底需不需要服务端会话？JWT 或签名 Cookie 怎么样？
8. 我一直假设自己需要一个会话存储，但我见过其他应用使用只存在于浏览器、不涉及服务器的令牌。这有什么不同，我是否应该改用那种方式？
