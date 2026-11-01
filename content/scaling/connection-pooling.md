---
id: connection-pooling
title: Connection Pooling
zone: scaling
edges:
  to:
    - id: managed-database
      question: Connection pooling is handling the pressure. But I'm still managing MySQL on a VM myself — backups, patching, failover. It is a lot of work and we don't even have any database admins. Is there something easier?
      detail: >-
        PgBouncer is absorbing the connection spikes. But I'm still on call for
        the database itself — schema migrations at 2 AM, manual backups I keep
        forgetting to test, no automatic failover. Database stores the most important
        data but it also feel like the most fragile. I am willing to pay to not have to manage it
difficulty: 2
tags:
  - connection-pooling
  - pgbouncer
  - rds-proxy
  - database
  - postgres
  - mysql
  - scaling
category: practice
milestones:
  - Explain why each app server maintaining its own connection pool is a problem at scale
  - Know what PgBouncer does and how connection multiplexing works
  - Explain the difference between transaction mode and session mode pooling
  - Know what max_connections is in Postgres and why it is a hard limit
title_zh: "连接池"

---


Each application server maintains a pool of persistent database connections. With one app server, this is fine. With ten app servers, each holding twenty connections open, you're at two hundred connections — and when the ASG scales out during a spike, you can hit Postgres's connection ceiling before the new servers have handled a single user request. Connection pooling solves this by multiplexing many application connections through far fewer actual database connections.

<!-- DEEP_DIVE -->

## Why connections are expensive

A Postgres connection is not a cheap resource. Each connection spawns a backend process (forked from the postmaster), consuming roughly 5-10 MB of memory per connection. Postgres has a hard `max_connections` limit, defaulting to 100 on small instances and configurable up to a few hundred on larger ones. Beyond that limit, new connection attempts fail with `FATAL: sorry, too many clients already`.

The naïve scaling math is brutal: 10 app servers × 20 connections each = 200 connections, and that's before considering database monitoring tools, migrations, read replicas, and admin sessions that also need connections.

## What a connection pool does

A connection pool like PgBouncer sits between your application servers and the database. Applications connect to PgBouncer (which looks like a normal Postgres endpoint). PgBouncer maintains a small, fixed pool of actual connections to the database. When an application "connection" needs to run a query, PgBouncer assigns it one of the real database connections, runs the query, and returns the connection to the pool.

The result: 500 application-level connections multiplexed through 20 real database connections. The database sees 20 connections; your application servers see their own private-looking connection pools.

## PgBouncer pooling modes

**Session mode**: a real database connection is assigned to an application connection for its entire lifetime. Least disruptive but least efficient — no real multiplexing, just limits the max connections.

**Transaction mode**: a real database connection is only held for the duration of a transaction. Between transactions, the real connection is returned to the pool and can be reused by other application connections. This is the most efficient mode — one real connection can serve many application connections as long as they're not all in transactions simultaneously.

**Statement mode**: connections are returned to the pool between every statement. Most efficient but breaks any application that uses transactions, session-level settings, or prepared statements. Generally not usable for production applications.

Transaction mode is the standard choice for web applications. The caveat: features that are tied to a specific connection — `LISTEN/NOTIFY`, prepared statements, session-level `SET` commands — either break or need special handling.

## RDS Proxy

AWS offers a managed connection pooler: **RDS Proxy**. It serves the same function as PgBouncer (connection multiplexing) but is fully managed, supports IAM authentication, integrates with Secrets Manager for credential rotation, and has native multi-AZ support. It's more expensive than self-hosting PgBouncer but removes the operational burden.

For Lambda functions that make burst database connections (Lambdas can scale to thousands of instances, each opening connections), RDS Proxy is the standard solution.

## Measuring the impact

Before and after adding a connection pool, measure:
- `SELECT count(*) FROM pg_stat_activity` — the number of actual connections to the database
- Connection error rate in your application logs (`too many clients`)
- Response time for database-bound requests under load

A well-configured PgBouncer should let you run 10× more application server capacity without changing the database's connection count.

## Configuration example

A minimal PgBouncer config:

```ini
[databases]
mydb = host=rds-endpoint.us-east-1.rds.amazonaws.com port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
listen_addr = 0.0.0.0
listen_port = 5432
```

Your application connects to PgBouncer (`pgbouncer-host:5432`) instead of the RDS endpoint directly. PgBouncer maintains 20 real database connections and multiplexes up to 1000 application connections through them.

<!-- RESOURCES -->

- [PgBouncer Documentation](https://www.pgbouncer.org/config.html) -- type: docs, time: 20m
- [AWS RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html) -- type: docs, time: 15m
- [Postgres max_connections and Why It Matters](https://www.postgresql.org/docs/current/runtime-config-connection.html) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
每个应用服务器都维护一个持久数据库连接池。只有一台应用服务器时，这没问题。但有十台应用服务器，每台保持二十个连接打开，你就达到了两百个连接——而当 ASG 在流量高峰期间扩容时，新服务器还没处理任何一个用户请求，你就可能触及 Postgres 的连接上限。连接池通过将许多应用连接多路复用到远少于实际数量的数据库连接上，解决了这个问题。

<!-- ZH_DEEP_DIVE -->
## 为什么连接是昂贵的

Postgres 连接不是一种廉价的资源。每个连接都会派生一个后端进程（从 postmaster fork 而来），每个连接大约消耗 5-10 MB 内存。Postgres 有一个硬性的 `max_connections` 限制，在小型实例上默认为 100，在较大的实例上可配置到几百。超过该限制后，新的连接尝试会失败，并报错 `FATAL: sorry, too many clients already`。

朴素的扩展计算很残酷：10 台应用服务器 × 每台 20 个连接 = 200 个连接，而这还没算上同样需要连接的数据库监控工具、迁移、只读副本和管理会话。

## 连接池的作用

像 PgBouncer 这样的连接池位于应用服务器和数据库之间。应用程序连接到 PgBouncer（它看起来就像一个普通的 Postgres 端点）。PgBouncer 维护一个小的、固定的到数据库的真实连接池。当某个应用“连接”需要执行查询时，PgBouncer 为它分配一个真实的数据库连接，执行查询，然后把连接归还到池中。

结果：500 个应用层连接通过 20 个真实数据库连接进行多路复用。数据库看到的是 20 个连接；你的应用服务器看到的是各自看似私有的连接池。

## PgBouncer 池化模式

**会话模式（Session mode）**：一个真实数据库连接在整个生命周期内分配给一个应用连接。干扰最小但效率最低——没有真正的多路复用，只是限制了最大连接数。

**事务模式（Transaction mode）**：一个真实数据库连接仅在事务持续期间被持有。事务之间，真实连接被归还到池中，可被其他应用连接复用。这是最高效的模式——只要不是所有应用连接同时处于事务中，一个真实连接就能服务许多应用连接。

**语句模式（Statement mode）**：连接在每条语句之间归还到池中。效率最高，但会破坏任何使用事务、会话级设置或预处理语句的应用。通常不适用于生产应用。

事务模式是 Web 应用的标准选择。注意事项：与特定连接绑定的特性——`LISTEN/NOTIFY`、预处理语句、会话级 `SET` 命令——要么会失效，要么需要特殊处理。

## RDS Proxy

AWS 提供了一种托管的连接池：**RDS Proxy**。它的功能与 PgBouncer 相同（连接多路复用），但完全托管，支持 IAM 认证，与 Secrets Manager 集成以实现凭证轮换，并原生支持多可用区。它比自托管 PgBouncer 更贵，但免除了运维负担。

对于会产生突发数据库连接的 Lambda 函数（Lambda 可扩展到数千个实例，每个实例都会打开连接），RDS Proxy 是标准解决方案。

## 衡量影响

在添加连接池之前和之后，测量：
- `SELECT count(*) FROM pg_stat_activity` —— 到数据库的真实连接数
- 应用日志中的连接错误率（`too many clients`）
- 负载下数据库相关请求的响应时间

配置良好的 PgBouncer 应该能让你在不改变数据库连接数的情况下，运行 10 倍以上的应用服务器容量。

## 配置示例

一个最小的 PgBouncer 配置：

```ini
[databases]
mydb = host=rds-endpoint.us-east-1.rds.amazonaws.com port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
listen_addr = 0.0.0.0
listen_port = 5432
```

你的应用连接到 PgBouncer（`pgbouncer-host:5432`），而不是直接连接 RDS 端点。PgBouncer 维护 20 个真实数据库连接，并通过它们多路复用最多 1000 个应用连接。

<!-- ZH_RESOURCES -->
- [PgBouncer 文档](https://www.pgbouncer.org/config.html) -- 类型：文档，时长：20 分钟
- [AWS RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html) -- 类型：文档，时长：15 分钟
- [Postgres max_connections 及其重要性](https://www.postgresql.org/docs/current/runtime-config-connection.html) -- 类型：文档，时长：10 分钟

<!-- ZH_UI -->
1. 解释为什么每个应用服务器维护自己的连接池在规模化时会成为问题
2. 了解 PgBouncer 的作用以及连接多路复用如何工作
3. 解释事务模式与会话模式连接池的区别
4. 了解 Postgres 中的 max_connections 是什么，以及为什么它是硬性限制
5. 连接池解决了压力问题。但我仍然自己在虚拟机上管理 MySQL——备份、打补丁、故障转移。工作量很大，而且我们甚至没有数据库管理员。有没有更简单的方法？
6. PgBouncer 正在吸收连接峰值。但我仍然要为数据库本身随时待命——凌晨 2 点做 schema 迁移、总是忘记测试的手动备份、没有自动故障转移。数据库存储着最重要的数据，但也感觉是最脆弱的。我愿意花钱来免于管理它
