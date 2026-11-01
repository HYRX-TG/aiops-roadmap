---
id: databases-and-sql
title: Databases & SQL
zone: building
edges:
  to:
    - id: nosql-databases
      question: What if my data doesn't fit neatly into rows and columns?
      detail: >-
        My product table works perfectly. But then I need to store user activity
        logs — each event has totally different fields. Or I want to store JSON
        from an API that's shaped differently every time. SQL starts to feel
        like the wrong tool, but I don't know what the alternative actually is.
    - id: caching-and-redis
      question: >-
        My app keeps hitting the database for the same data over and over. How
        do I speed things up?
      detail: >-
        My database is getting hammered with the same queries over and over —
        the same product list, the same category page, fetched fresh on every
        single request. It works, but it's slow and I'm worried about what
        happens when traffic picks up. There must be a way to avoid repeating
        that work constantly.
    - id: file-and-object-storage
      question: >-
        Users upload images and PDFs. I can't shove binary files into a SQL
        table, can I?
      detail: >-
        Users want to upload profile photos and PDFs. I tried storing them in
        the database but it felt wrong — the database slowed down and the column
        was just a blob of bytes I couldn't do anything with. There must be a
        proper way to handle files that isn't shoehorning them into SQL.
difficulty: 1
tags:
  - database
  - sql
  - postgresql
  - mysql
  - sqlite
  - relational
category: concept
milestones:
  - >-
    Create a SQLite database and write basic SQL queries (SELECT, INSERT,
    UPDATE, DELETE)
  - Design a schema with multiple related tables and foreign keys
  - Connect a database to a web application and perform CRUD operations
title_zh: "数据库与 SQL"

---


Your Flask app stores a list of products in a Python list. You add a product, it shows up. You restart the app, it is gone. Every piece of data lives in memory, and memory is wiped the moment the process stops. You need somewhere for data to live permanently — somewhere that survives restarts, handles multiple users reading and writing at the same time, and lets you ask complex questions about your data. That is what a database does.

<!-- DEEP_DIVE -->

A **relational database** stores data in tables — rows and columns, like a spreadsheet but with superpowers. Each table represents a type of thing (users, products, orders), each row is one instance, and each column is an attribute. The "relational" part means tables can reference each other through **foreign keys**.

**SQL** (Structured Query Language) is how you talk to relational databases. It is not a programming language in the traditional sense — it is a query language designed specifically for asking questions about data:

```sql
-- Create a table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert data
INSERT INTO users (email, name) VALUES ('alice@example.com', 'Alice');

-- Query data
SELECT * FROM users WHERE email = 'alice@example.com';

-- Update data
UPDATE users SET name = 'Alice Smith' WHERE id = 1;

-- Delete data
DELETE FROM users WHERE id = 1;
```

These four operations — **Create, Read, Update, Delete** — are called **CRUD**, and they are the backbone of almost every application.

**Relationships** are what make relational databases powerful. An order belongs to a user. An order contains multiple products. These connections are expressed with foreign keys:

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Join tables to get related data
SELECT users.name, orders.total, orders.created_at
FROM orders
JOIN users ON orders.user_id = users.id
WHERE users.email = 'alice@example.com';
```

**Choosing a database** matters. The three you will encounter most:

- **SQLite** — a database in a single file. No server to install, built into Python. Perfect for learning, prototyping, and small applications. Not great for high concurrency.
- **PostgreSQL** — the industry standard for production. Robust, feature-rich, handles complex queries and high concurrency. This is what most serious applications use.
- **MySQL** — widely used, especially in web hosting (WordPress, PHP apps). Solid but historically less feature-rich than PostgreSQL.

```python
# SQLite with Python — no setup needed
import sqlite3

conn = sqlite3.connect("myapp.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
""")

cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)",
               ("alice@example.com", "Alice"))
conn.commit()

# Query
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
```

**Schemas and migrations** are how you manage the structure of your database over time. A schema defines what tables exist and what columns they have. As your app evolves, you need to add columns, create new tables, or change data types. Migration tools (like Alembic for Python) track these changes just like Git tracks code changes.

**Indexes** make queries fast. Without an index, the database has to scan every row to find what you want. With an index, it can jump straight to the right row — like looking up a word in a dictionary instead of reading every page. Always index columns you search or filter on frequently:

```sql
CREATE INDEX idx_users_email ON users(email);
```

**Why SREs care about databases:** Databases are the most common bottleneck in production systems. Slow queries, missing indexes, connection pool exhaustion, replication lag, disk space — these are the things that page you at 3 AM. Understanding how databases work is not optional for anyone operating production software.

<!-- RESOURCES -->

- [SQLBolt - Interactive SQL Tutorial](https://sqlbolt.com/) -- type: interactive, time: 2h
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/) -- type: tutorial, time: 4h
- [Use The Index, Luke](https://use-the-index-luke.com/) -- type: book, time: varies
- [SQLite Documentation](https://www.sqlite.org/docs.html) -- type: reference, time: 30m

<!-- ZH_SUMMARY -->
你的 Flask 应用把产品列表存在一个 Python 列表里。你添加一个产品，它就会出现。你重启应用，它就不见了。每一条数据都活在内存中，而进程一停止，内存就被清空。你需要一个能让数据永久驻留的地方——一个能经受重启、能处理多个用户同时读写、还能让你对数据提出复杂查询的地方。这就是数据库所做的事。

<!-- ZH_DEEP_DIVE -->
**关系型数据库**将数据存储在表中——行和列，就像电子表格但拥有超能力。每张表代表一类事物（用户、产品、订单），每一行是一个实例，每一列是一个属性。“关系型”意味着表之间可以通过**外键**相互引用。

**SQL**（Structured Query Language，结构化查询语言）是你与关系型数据库对话的方式。它不是传统意义上的编程语言——它是一种专门为查询数据而设计的查询语言：

```sql
-- Create a table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert data
INSERT INTO users (email, name) VALUES ('alice@example.com', 'Alice');

-- Query data
SELECT * FROM users WHERE email = 'alice@example.com';

-- Update data
UPDATE users SET name = 'Alice Smith' WHERE id = 1;

-- Delete data
DELETE FROM users WHERE id = 1;
```

这四种操作——**创建、读取、更新、删除**（Create、Read、Update、Delete）——被称为 **CRUD**，它们是几乎所有应用的支柱。

**关系**是关系型数据库强大的原因。一个订单属于一个用户。一个订单包含多个产品。这些关联通过外键来表达：

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Join tables to get related data
SELECT users.name, orders.total, orders.created_at
FROM orders
JOIN users ON orders.user_id = users.id
WHERE users.email = 'alice@example.com';
```

**选择数据库**很重要。你最常遇到的三种：

- **SQLite** —— 一个单文件中的数据库。无需安装服务器，内置于 Python。非常适合学习、原型开发和小型应用。不太适合高并发场景。
- **PostgreSQL** —— 生产环境的行业标准。健壮、功能丰富，能处理复杂查询和高并发。大多数严肃应用都使用它。
- **MySQL** —— 使用广泛，尤其在 Web 托管中（WordPress、PHP 应用）。可靠，但历史上功能不如 PostgreSQL 丰富。

```python
# SQLite with Python — no setup needed
import sqlite3

conn = sqlite3.connect("myapp.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
""")

cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)",
               ("alice@example.com", "Alice"))
conn.commit()

# Query
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
```

**Schema 与迁移**是你随时间管理数据库结构的方式。Schema 定义了存在哪些表以及它们有哪些列。随着应用演进，你需要添加列、创建新表或更改数据类型。迁移工具（如 Python 的 Alembic）像 Git 跟踪代码变更一样跟踪这些变更。

**索引**让查询变快。没有索引时，数据库必须扫描每一行才能找到你要的内容。有了索引，它可以直接跳到正确的行——就像查字典找单词，而不是逐页阅读。始终为你频繁搜索或过滤的列建立索引：

```sql
CREATE INDEX idx_users_email ON users(email);
```

**为什么 SRE 关心数据库：** 数据库是生产系统中最常见的瓶颈。慢查询、缺失索引、连接池耗尽、复制延迟、磁盘空间——这些就是凌晨 3 点把你叫醒的事情。对于任何运维生产软件的人来说，理解数据库如何工作不是可选项。

<!-- ZH_RESOURCES -->
- [SQLBolt - 交互式 SQL 教程](https://sqlbolt.com/) -- 类型：交互式，时长：2 小时
- [PostgreSQL 教程](https://www.postgresqltutorial.com/) -- 类型：教程，时长：4 小时
- [Use The Index, Luke](https://use-the-index-luke.com/) -- 类型：书籍，时长：不定
- [SQLite 文档](https://www.sqlite.org/docs.html) -- 类型：参考，时长：30 分钟

<!-- ZH_UI -->
1. 创建 SQLite 数据库并编写基础 SQL 查询（SELECT、INSERT、UPDATE、DELETE）
2. 设计包含多个关联表和 foreign key 的 schema
3. 将数据库连接到 Web 应用并执行 CRUD 操作
4. 如果我的数据无法整齐地放入行和列怎么办？
5. 我的 product 表运行完美。但接着我需要存储用户活动日志——每个事件的字段完全不同。或者我想存储来自 API 的 JSON，其结构每次都不同。SQL 开始感觉像是错误的工具，但我不知道替代方案究竟是什么。
6. 我的应用反复向数据库请求相同的数据。如何加快速度？
7. 我的数据库被相同的查询反复冲击——相同的产品列表、相同的分类页面，每个请求都重新获取。它能工作，但很慢，我担心流量增大后会发生什么。一定有办法避免不断重复这些工作。
8. 用户上传图片和 PDF。我不能把二进制文件塞进 SQL 表里，对吧？
9. 用户想上传头像照片和 PDF。我尝试将它们存储在数据库中，但感觉不对——数据库变慢了，列只是一堆我无法操作的字节。一定有处理文件的正确方式，而不是把它们硬塞进 SQL。
