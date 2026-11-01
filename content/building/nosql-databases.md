---
id: nosql-databases
title: NoSQL Databases
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: >-
        I understand my data layer options. How do I get this whole thing
        running for real?
      detail: >-
        Everything works on my laptop — app, database, cache. But running it for
        real means all of these pieces have to live somewhere on an actual
        server, talking to each other over a network I don't fully understand
        yet. How does any of this connect?
difficulty: 2
tags:
  - nosql
  - mongodb
  - dynamodb
  - document-store
  - key-value
category: concept
milestones:
  - >-
    Understand the difference between document, key-value, column-family, and
    graph databases
  - Set up MongoDB and perform basic CRUD operations
  - Identify scenarios where NoSQL is a better fit than SQL
title_zh: "NoSQL 数据库"

---


You are building a content platform where every post can have completely different metadata — blog posts have word counts and categories, videos have duration and resolution, podcasts have episode numbers and guest lists. Trying to cram all of this into rigid SQL tables means dozens of nullable columns or ugly workarounds. NoSQL databases let each record have its own shape, and for certain problems, that flexibility is exactly what you need.

<!-- DEEP_DIVE -->

**NoSQL** is a broad category meaning "not only SQL." These databases sacrifice some of the guarantees that relational databases provide (like strict schemas and complex joins) in exchange for flexibility, scalability, or performance in specific use cases. There are four main types:

**Document Stores** (MongoDB, CouchDB) store data as JSON-like documents. Each document can have a different structure. This maps naturally to how applications already work with data — as objects and dictionaries:

```python
# MongoDB example with pymongo
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["myapp"]

# Each document can have different fields
db.posts.insert_one({
    "type": "blog",
    "title": "Understanding NoSQL",
    "author": "Alice",
    "word_count": 1500,
    "tags": ["databases", "nosql"]
})

db.posts.insert_one({
    "type": "video",
    "title": "NoSQL Explained",
    "author": "Bob",
    "duration_seconds": 600,
    "resolution": "1080p"
})

# Query across different shapes
for post in db.posts.find({"author": "Alice"}):
    print(post["title"])
```

No schema to define upfront. No migrations when you add a new field. Just store the data. This is incredibly convenient during rapid development — but it also means the database will not stop you from storing garbage.

**Key-Value Stores** (Redis, DynamoDB, etcd) are the simplest model: a key maps to a value. Think of it as a giant dictionary. Lightning fast for lookups by key, but you cannot query by value easily. DynamoDB is AWS's managed key-value/document store and is ubiquitous in AWS-heavy environments:

```python
# DynamoDB-style thinking
# Key: "user:alice@example.com"
# Value: {"name": "Alice", "plan": "premium", "last_login": "2024-01-15"}
```

**Column-Family Stores** (Cassandra, HBase) organize data into columns rather than rows. They excel at handling massive amounts of data distributed across many servers — think billions of rows of time-series data, event logs, or IoT sensor readings. You will encounter Cassandra in large-scale infrastructure.

**Graph Databases** (Neo4j, Amazon Neptune) model data as nodes and relationships. They are perfect for social networks, recommendation engines, and fraud detection — anywhere the connections between things matter more than the things themselves.

**When to use NoSQL vs SQL:**

| Use SQL when... | Use NoSQL when... |
|-----------------|-------------------|
| Data has clear, stable relationships | Data shape varies or evolves rapidly |
| You need complex queries with joins | You mostly query by key or simple filters |
| Data integrity is critical (financial) | You need horizontal scalability |
| Your schema is well-defined | You need flexible schemas |

**The CAP theorem** is worth knowing: in a distributed database, you can only guarantee two of three properties — **Consistency** (every read gets the latest write), **Availability** (every request gets a response), and **Partition tolerance** (the system works even if network links between nodes fail). Since network partitions are unavoidable in distributed systems, you are really choosing between consistency and availability. SQL databases traditionally favor consistency. Many NoSQL databases favor availability.

**Why SREs care:** NoSQL databases show up everywhere in modern infrastructure. etcd stores Kubernetes cluster state. DynamoDB backs serverless architectures. MongoDB powers content platforms. Cassandra handles time-series metrics. Understanding the trade-offs — when NoSQL shines and when it creates headaches — helps you make better architectural decisions and debug production issues faster.

<!-- RESOURCES -->

- [MongoDB University (free courses)](https://learn.mongodb.com/) -- type: course, time: varies
- [DynamoDB Guide](https://www.dynamodbguide.com/) -- type: guide, time: 2h
- [Visual Guide to NoSQL Systems](https://blog.nahurst.com/visual-guide-to-nosql-systems) -- type: article, time: 15m
- [CAP Theorem Explained](https://www.ibm.com/topics/cap-theorem) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
你正在构建一个内容平台，其中每篇帖子都可以拥有完全不同的元数据——博客文章有字数和分类，视频有时长和分辨率，播客有集数和嘉宾名单。试图把所有这些都塞进僵化的 SQL 表中，意味着要设置几十个可空列，或者采用丑陋的变通方案。NoSQL 数据库让每条记录都能拥有自己的结构，而对于某些问题，这种灵活性正是你所需要的。

<!-- ZH_DEEP_DIVE -->
**NoSQL** 是一个宽泛的类别，意为“不仅仅是 SQL”。这类数据库牺牲了关系型数据库提供的一些保证（如严格的模式和复杂的连接），以换取特定用例下的灵活性、可扩展性或性能。主要有四种类型：

**文档存储**（MongoDB、CouchDB）将数据存储为类似 JSON 的文档。每个文档可以有不同的结构。这自然地映射了应用程序处理数据的方式——作为对象和字典：

```python
# MongoDB example with pymongo
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["myapp"]

# Each document can have different fields
db.posts.insert_one({
    "type": "blog",
    "title": "Understanding NoSQL",
    "author": "Alice",
    "word_count": 1500,
    "tags": ["databases", "nosql"]
})

db.posts.insert_one({
    "type": "video",
    "title": "NoSQL Explained",
    "author": "Bob",
    "duration_seconds": 600,
    "resolution": "1080p"
})

# Query across different shapes
for post in db.posts.find({"author": "Alice"}):
    print(post["title"])
```

无需预先定义模式。添加新字段时无需迁移。直接存储数据即可。这在快速开发期间极其方便——但这也意味着数据库不会阻止你存储垃圾数据。

**键值存储**（Redis、DynamoDB、etcd）是最简单的模型：键映射到值。可以把它想象成一个巨大的字典。按键查找快如闪电，但无法轻松地按值查询。DynamoDB 是 AWS 的托管键值/文档存储，在重度使用 AWS 的环境中无处不在：

```python
# DynamoDB-style thinking
# Key: "user:alice@example.com"
# Value: {"name": "Alice", "plan": "premium", "last_login": "2024-01-15"}
```

**列族存储**（Cassandra、HBase）将数据组织为列而非行。它们擅长处理分布在多台服务器上的海量数据——想想数十亿行的时间序列数据、事件日志或 IoT 传感器读数。你会在大规模基础设施中遇到 Cassandra。

**图数据库**（Neo4j、Amazon Neptune）将数据建模为节点和关系。它们非常适合社交网络、推荐引擎和欺诈检测——任何事物之间的连接比事物本身更重要的场景。

**何时使用 NoSQL 与 SQL：**

| 在以下情况使用 SQL... | 在以下情况使用 NoSQL... |
|-----------------|-------------------|
| 数据具有清晰、稳定的关系 | 数据形态多变或快速演变 |
| 你需要带连接的复杂查询 | 你主要按键或简单过滤条件查询 |
| 数据完整性至关重要（金融） | 你需要水平可扩展性 |
| 你的模式定义明确 | 你需要灵活的模式 |

**CAP 定理**值得了解：在分布式数据库中，你只能保证三个属性中的两个——**一致性**（每次读取都能获得最新的写入）、**可用性**（每个请求都能得到响应）和**分区容错性**（即使节点之间的网络链路故障，系统仍能工作）。由于网络分区在分布式系统中不可避免，你实际上是在一致性和可用性之间做选择。SQL 数据库传统上偏向一致性。许多 NoSQL 数据库偏向可用性。

**为什么 SRE 关心：** NoSQL 数据库在现代基础设施中随处可见。etcd 存储 Kubernetes 集群状态。DynamoDB 支撑无服务器架构。MongoDB 驱动内容平台。Cassandra 处理时间序列指标。理解这些权衡——NoSQL 何时大放异彩、何时带来麻烦——有助于你做出更好的架构决策，并更快地调试生产问题。

<!-- ZH_RESOURCES -->
- [MongoDB University（免费课程）](https://learn.mongodb.com/) -- 类型：课程，时长：不定
- [DynamoDB 指南](https://www.dynamodbguide.com/) -- 类型：指南，时长：2 小时
- [NoSQL 系统可视化指南](https://blog.nahurst.com/visual-guide-to-nosql-systems) -- 类型：文章，时长：15 分钟
- [CAP 定理详解](https://www.ibm.com/topics/cap-theorem) -- 类型：文章，时长：15 分钟

<!-- ZH_UI -->
1. 理解文档型、键值型、列族型和图数据库之间的区别
2. 搭建 MongoDB 并执行基本 CRUD 操作
3. 识别 NoSQL 比 SQL 更适用的场景
4. 我已了解数据层可选方案。如何真正把整套系统跑起来？
5. 在我的笔记本电脑上一切正常——应用、数据库、缓存。但真正运行意味着所有这些组件都必须部署在实际服务器上，并通过我尚未完全理解的网络相互通信。这一切究竟是如何连接的？
