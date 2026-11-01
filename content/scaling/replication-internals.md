---
id: replication-internals
title: How Database Replication Actually Works
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - replication
  - binlog
  - mysql
  - replication-lag
  - consistency
  - eventual-consistency
  - database
category: concept
milestones:
  - Explain what a binary log (binlog) is and what it contains
  - Describe the difference between synchronous and asynchronous replication
  - Explain what replication lag is and when it matters to your application
  - >-
    Know why you cannot use an asynchronous replica as a direct failover target
    without promotion
  - Understand what 'reading your own writes' means and how lag can break it
title_zh: "数据库复制实际上是如何工作的"

---


Database replication is not magic — it's a stream of changes from one node applied to another. Understanding the mechanism (binary logs, replication threads, async vs sync modes) lets you reason about what replication guarantees and what it doesn't, when lag matters, and why you can't use an async replica as a zero-downtime failover target.

<!-- DEEP_DIVE -->

## The binary log (binlog)

MySQL and Postgres both implement replication through a persistent log of all changes made to the database. In MySQL, this is the **binary log (binlog)**. Every `INSERT`, `UPDATE`, and `DELETE` that commits successfully is written to the binlog as an event. The binlog is the authoritative record of what happened and in what order.

A replica works by reading these events from the primary's binlog and applying them in order. The replica has two threads:
- **I/O thread**: connects to the primary, reads binlog events, writes them to the replica's local relay log
- **SQL thread**: reads events from the relay log and applies them (executes the SQL) on the replica's data

Replication lag is the difference in time between when an event is written to the primary's binlog and when the SQL thread finishes applying it on the replica.

## Asynchronous replication

The default replication mode for MySQL read replicas (and Postgres streaming replication) is **asynchronous**. The primary writes to the binlog, acknowledges the write to the client, and separately sends the events to replicas. The primary doesn't wait for replicas to confirm they received anything.

Implications:
- **Low write latency**: no replica round-trip in the write path
- **Data loss risk on failover**: if the primary crashes after writing to the binlog but before the replica received those events, those writes are lost when the replica is promoted

This is why you cannot safely promote an async replica to primary during a crash without potentially losing the last few transactions. You're accepting that replicas might be slightly behind.

## Synchronous replication

**Synchronous replication** means the primary waits for at least one replica to confirm it has received (and optionally written to its relay log) the event before acknowledging the write to the client.

MySQL's **semi-synchronous replication** (a middle ground) requires at least one replica to acknowledge receipt of the event before the primary commits. This eliminates the data loss window but adds latency to every write — the primary must wait for a replica round-trip.

AWS RDS Multi-AZ uses synchronous replication. The standby must confirm every write before RDS acknowledges it. This is why Multi-AZ has no data loss on failover — the standby has every committed transaction.

## Replication lag in practice

Lag accumulates when:
- The primary is handling large transactions (an UPDATE touching 10 million rows generates a lot of binlog events that take time to apply on the replica)
- The replica's SQL thread can't keep up with the I/O thread (the replica instance is undersized)
- Network congestion between primary and replica

**Reading your own writes**: the classic lag problem. A user writes data and then immediately reads it from a replica that hasn't received the write yet. They see stale data — their write appears missing. Solutions:
- After writes, read from the primary for a brief window
- Route users to a replica only after confirming the replica is caught up to the point of their last write (track the binlog position)
- For anything where freshness is critical, always read from the primary

## The promotion cost

Promoting a replica to primary is not instant:
1. Stop replication (so the replica stops being a follower)
2. Wait for all relay log events to be applied (if there's lag, this takes time)
3. Update the replica's role to primary
4. Update your connection configuration to point at the new primary

With async replication, step 2 might be impossible if the primary crashed — you may have to promote with acknowledged lag and accept losing those transactions. This is the unavoidable trade-off of async replication.

<!-- RESOURCES -->

- [MySQL Binary Log](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html) -- type: docs, time: 20m
- [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html) -- type: docs, time: 20m
- [Designing Data-Intensive Applications - Ch. 5 (Replication)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- type: book, time: 1h

<!-- ZH_SUMMARY -->
数据库复制并非魔法——它不过是从一个节点发出、在另一个节点上应用的一串变更流。理解其机制（二进制日志、复制线程、异步与同步模式），你就能推断出复制能保证什么、不能保证什么，延迟何时才真正要紧，以及为什么不能把异步副本当作零停机故障切换目标。

<!-- ZH_DEEP_DIVE -->
## 二进制日志（binlog）

MySQL 和 Postgres 都通过一份持久化的日志来实现复制，该日志记录了数据库上发生的所有变更。在 MySQL 中，这份日志就是**二进制日志（binlog）**。每一个成功提交的 `INSERT`、`UPDATE` 和 `DELETE` 都会作为一个事件写入 binlog。binlog 是记录发生了什么以及以什么顺序发生的权威依据。

副本的工作方式是：从主库的 binlog 中读取这些事件，并按顺序应用它们。副本有两个线程：
- **I/O 线程**：连接主库，读取 binlog 事件，并将其写入副本本地的中继日志（relay log）
- **SQL 线程**：从中继日志中读取事件，并在副本的数据上应用它们（执行 SQL）

复制延迟（replication lag）是指从事件写入主库 binlog 到 SQL 线程在副本上完成应用之间的时间差。

## 异步复制

MySQL 只读副本（以及 Postgres 流复制）的默认复制模式是**异步**的。主库写入 binlog，向客户端确认写入成功，然后单独将事件发送给副本。主库不会等待副本确认收到任何内容。

影响：
- **写入延迟低**：写入路径中没有副本的往返
- **故障切换时存在数据丢失风险**：如果主库在写入 binlog 之后、副本收到这些事件之前崩溃，那么当副本被提升为主库时，这些写入就会丢失

这就是为什么在崩溃期间不能安全地将异步副本提升为主库，否则可能会丢失最后几笔事务。你接受的是副本可能略微落后。

## 同步复制

**同步复制**意味着主库在向客户端确认写入之前，会等待至少一个副本确认它已收到（并可选地写入其中继日志）该事件。

MySQL 的**半同步复制**（一种折中方案）要求至少一个副本在主库提交之前确认收到该事件。这消除了数据丢失窗口，但会给每次写入增加延迟——主库必须等待一次副本往返。

AWS RDS Multi-AZ 使用同步复制。备用实例必须在 RDS 确认每次写入之前进行确认。这就是为什么 Multi-AZ 在故障切换时不会丢失数据——备用实例拥有每一笔已提交的事务。

## 实践中的复制延迟

延迟会在以下情况下累积：
- 主库正在处理大事务（一条影响 1000 万行的 UPDATE 会生成大量 binlog 事件，在副本上应用需要时间）
- 副本的 SQL 线程跟不上 I/O 线程（副本实例规格过小）
- 主库与副本之间的网络拥塞

**读取自己写入的数据**：经典的延迟问题。用户写入数据后立即从尚未收到该写入的副本读取。他们看到的是过期数据——他们的写入似乎丢失了。解决方案：
- 写入后，在短暂的时间窗口内从主库读取
- 仅在确认副本已追赶到其最后一次写入的位置（跟踪 binlog 位置）后，才将用户路由到副本
- 对于任何对新鲜度至关重要的场景，始终从主库读取

## 提升的代价

将副本提升为主库并非瞬时完成：
1. 停止复制（使副本不再作为从库）
2. 等待所有中继日志事件被应用（如果存在延迟，这需要时间）
3. 将副本的角色更新为主库
4. 更新你的连接配置以指向新的主库

在异步复制下，如果主库崩溃，第 2 步可能无法完成——你可能不得不在存在已确认延迟的情况下进行提升，并接受丢失那些事务。这是异步复制不可避免的权衡。

<!-- ZH_RESOURCES -->
- [MySQL Binary Log](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html) -- 类型: 文档, 时间: 20m
- [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html) -- 类型: 文档, 时间: 20m
- [Designing Data-Intensive Applications - Ch. 5 (Replication)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) -- 类型: 书籍, 时间: 1h

<!-- ZH_UI -->
1. 解释什么是二进制日志（binlog）及其包含的内容
2. 描述同步复制与异步复制的区别
3. 解释什么是复制延迟以及何时对应用有影响
4. 了解为什么不能将异步副本直接作为故障转移目标而不进行提升
5. 理解“读取自己的写入”的含义以及延迟如何破坏它
