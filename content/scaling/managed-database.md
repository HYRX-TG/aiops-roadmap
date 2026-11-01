---
id: managed-database
title: Managed Databases
zone: scaling
edges:
  to:
    - id: database-replication
      question: >-
        We're on RDS/Cloud SQL. Now how do we scale reads and add high
        availability?
      detail: >-
        We're on RDS now and it's much better than self-managing MySQL. But
        the database is still a single point of failure — if it goes down,
        everything goes down. And reads are starting to pile up. I don't know
        if I need replicas, Multi-AZ, both, or something else entirely.
difficulty: 2
tags:
  - rds
  - aws
  - database
  - managed-database
  - multi-az
  - read-replicas
  - postgresql
  - mysql
category: practice
milestones:
  - Create an RDS instance and connect to it from an EC2 instance
  - Understand what Multi-AZ deployment does (and what it doesn't do)
  - Create a read replica and configure your app to use it for reads
  - Understand the shared responsibility model for managed databases
title_zh: "托管数据库"

---


Running your own database on a VM works, but it means you're responsible for everything: installing MySQL or Postgres, configuring it, taking backups, testing restores, patching CVEs, tuning replication, handling failover. Managed databases (RDS on AWS, Cloud SQL on GCP) hand most of this operational burden back to the cloud provider in exchange for a monthly fee and somewhat less control.

<!-- DEEP_DIVE -->

## What a managed database gives you

**Automated backups**: RDS takes daily snapshots and archives transaction logs continuously, giving you point-in-time restore to any second in your retention window (up to 35 days). Testing restores is a one-click operation.

**Automated patching**: Minor version patches and security updates are applied automatically during your maintenance window. You control when, but not whether.

**Multi-AZ deployments**: RDS can maintain a synchronous replica in a second availability zone. If the primary fails, RDS detects it and fails over to the replica — typically in 60-120 seconds — automatically. You don't need to write any failover logic; your connection string points to an endpoint that always resolves to the current primary.

**Monitoring built-in**: CPU, disk I/O, connection count, replication lag, and dozens of other metrics are available in CloudWatch without configuring anything.

**Storage auto-scaling**: RDS can automatically grow your storage when it's running low. No waking up at 3 AM because the disk filled up.

## What you still own

Managed doesn't mean zero responsibility. The **shared responsibility model** means:

- **You own**: schema design, index selection, query optimization, connection management, access control, deciding which parameter group settings to change
- **AWS owns**: the hardware, OS patching, daemon health, hardware failure replacement, backup infrastructure

Performance problems caused by missing indexes, N+1 queries, or poor schema design are still your problem. RDS will faithfully run your slow queries very reliably.

## RDS vs self-managed: the cost question

RDS is more expensive than running MySQL on an EC2 instance of equivalent size. An `r7g.large` RDS instance costs roughly 2x a self-managed MySQL on an equivalent EC2 instance. Whether that's worth it depends on how much you value your time and how much operational risk you want to carry. For most teams: the operational overhead of self-managed databases costs more in engineer time than the RDS premium.

## Multi-AZ vs read replicas

These are often confused because they both involve a second database:

- **Multi-AZ**: synchronous replication to a standby in another AZ, used only for failover. You cannot read from the standby — it exists purely to take over if the primary fails.
- **Read replicas**: asynchronous replication to one or more replicas. You can and should point read-heavy queries at these. They reduce read load on the primary. They are not hot standbys — promoting a replica to primary requires a manual step.

Multi-AZ is for availability. Read replicas are for read scaling. You often want both.

## Creating an RDS instance

Key decisions when creating:
- **Engine and version**: use the latest minor version of your engine. Postgres 16, MySQL 8.0, etc.
- **Instance class**: start smaller than you think you need (you can scale up with a short restart); `db.t3.medium` is a reasonable starting point for dev/staging
- **Storage type**: `gp3` (general purpose SSD) is fine for most workloads; `io1` for IOPS-intensive workloads
- **Multi-AZ**: enable it from the start in production; retrofitting it later causes a storage conversion
- **Parameter group**: start with the default; tune specific settings only when you have evidence they matter
- **Security group**: restrict database access to only your application servers — the database should never be publicly accessible

<!-- RESOURCES -->

- [AWS RDS Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) -- type: docs, time: 30m
- [AWS RDS Multi-AZ Deployments](https://aws.amazon.com/rds/features/multi-az/) -- type: article, time: 10m
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
在虚拟机上运行自己的数据库是可行的，但这意味着你需要对一切负责：安装 MySQL 或 Postgres、配置、备份、测试恢复、修补 CVE、调优复制、处理故障转移。托管数据库（AWS 上的 RDS、GCP 上的 Cloud SQL）将大部分运维负担交还给云服务提供商，代价是支付月费，并牺牲一定的控制权。

<!-- ZH_DEEP_DIVE -->
## 托管数据库为你提供了什么

**自动备份**：RDS 每天创建快照，并持续归档事务日志，让你可以在保留窗口内（最长 35 天）恢复到任意一秒的时间点。测试恢复只需一键操作。

**自动打补丁**：小版本补丁和安全更新会在你的维护窗口内自动应用。你控制何时打补丁，但无法控制是否打补丁。

**多可用区部署**：RDS 可以在第二个可用区维护一个同步副本。如果主实例发生故障，RDS 会检测到并自动故障转移到副本——通常在 60-120 秒内完成。你不需要编写任何故障转移逻辑；你的连接字符串指向一个端点，该端点始终解析到当前的主实例。

**内置监控**：CPU、磁盘 I/O、连接数、复制延迟以及数十种其他指标都可以在 CloudWatch 中查看，无需任何配置。

**存储自动扩展**：RDS 可以在存储空间不足时自动扩容。不用再因为磁盘写满而在凌晨 3 点被叫醒。

## 你仍然需要负责的部分

托管并不意味着零责任。**共享责任模型**意味着：

- **你负责**：schema 设计、索引选择、查询优化、连接管理、访问控制、决定更改哪些参数组设置
- **AWS 负责**：硬件、操作系统补丁、守护进程健康、硬件故障更换、备份基础设施

由缺失索引、N+1 查询或糟糕的 schema 设计导致的性能问题仍然是你的问题。RDS 会非常可靠地忠实执行你的慢查询。

## RDS 与自管理：成本问题

RDS 比在同等规格的 EC2 实例上运行 MySQL 更贵。一个 `r7g.large` 的 RDS 实例成本大约是同等 EC2 实例上自管理 MySQL 的 2 倍。这是否值得，取决于你有多看重自己的时间，以及你愿意承担多少运维风险。对大多数团队来说：自管理数据库的运维开销在工程师时间上的成本，超过了 RDS 的溢价。

## 多可用区与只读副本

这两者经常被混淆，因为它们都涉及第二个数据库：

- **多可用区**：同步复制到另一个可用区的备用实例，仅用于故障转移。你无法从备用实例读取——它的存在纯粹是为了在主实例故障时接管。
- **只读副本**：异步复制到一个或多个副本。你可以并且应该将读密集型查询指向这些副本。它们减轻主实例的读负载。它们不是热备用——将副本提升为主实例需要手动操作。

多可用区用于可用性。只读副本用于读扩展。你通常两者都需要。

## 创建 RDS 实例

创建时的关键决策：
- **引擎和版本**：使用引擎的最新小版本。Postgres 16、MySQL 8.0 等。
- **实例类**：从比你认为需要的更小的规格开始（你可以通过短暂重启来扩容）；`db.t3.medium` 是开发/预发环境的合理起点
- **存储类型**：`gp3`（通用 SSD）适合大多数工作负载；`io1` 适合 IOPS 密集型工作负载
- **多可用区**：在生产环境中从一开始就启用；之后再改造会触发存储转换
- **参数组**：从默认值开始；只有在有证据表明某些设置确实重要时才调整它们
- **安全组**：将数据库访问限制为仅你的应用服务器——数据库永远不应可公开访问

<!-- ZH_RESOURCES -->
- [AWS RDS 文档](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) -- 类型：文档，时长：30m
- [AWS RDS 多可用区部署](https://aws.amazon.com/rds/features/multi-az/) -- 类型：文章，时长：10m
- [AWS 责任共担模型](https://aws.amazon.com/compliance/shared-responsibility-model/) -- 类型：文章，时长：10m

<!-- ZH_UI -->
1. 创建一个 RDS 实例，并从 EC2 实例连接到它
2. 理解多可用区部署的作用（以及它不能做什么）
3. 创建一个只读副本，并配置应用将读请求交给它
4. 理解托管数据库的责任共担模型
5. 我们用的是 RDS/Cloud SQL。现在如何扩展读能力并增加高可用性？
6. 我们现在用 RDS，比自管理 MySQL 好多了。但数据库仍是单点故障——一旦它宕机，所有服务都会中断。而且读请求开始堆积。我不确定自己需要只读副本、多可用区、两者都要，还是完全不同的方案。
