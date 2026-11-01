---
id: file-and-object-storage
title: File & Object Storage
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: I can handle files and data. Now how do I deploy all of this?
      detail: >-
        My app handles uploads and stores them on my local filesystem — but that
        only works on my machine. If I deploy to a server and users upload
        files, where do those actually go? I can't count on the server's disk
        for everything. I need to figure out how file storage works in a real
        deployment.
difficulty: 2
tags:
  - storage
  - s3
  - object-storage
  - files
  - blob
  - cdn
category: concept
milestones:
  - >-
    Understand the difference between file storage, block storage, and object
    storage
  - Handle file uploads in a web application and store them on disk
  - Use an S3-compatible API to store and retrieve objects
title_zh: "文件与对象存储"

---


Your app lets users upload profile pictures. Where do those images go? You could base64-encode them and store them in a database column — but your database will balloon in size, queries will slow to a crawl, and your DBA will cry. Files and databases are different kinds of data, and they need different kinds of storage.

<!-- DEEP_DIVE -->

**File storage** is what you already know — directories and files on a filesystem. `/home/user/photos/vacation.jpg`. It is hierarchical (folders within folders), supports permissions, and every operating system understands it. For a small app running on a single server, storing uploads on the local filesystem is perfectly fine:

```python
import os
from flask import Flask, request

app = Flask(__name__)
UPLOAD_DIR = "/var/uploads"

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["avatar"]
    filename = f"{user_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    return {"path": filepath}
```

This works on your laptop. But what happens when you have two servers behind a load balancer? A user uploads to server A, and their next request hits server B — which does not have the file. Local filesystem storage does not scale.

**Object storage** (Amazon S3, Google Cloud Storage, Azure Blob Storage) solves this. Instead of files in directories, you have **objects** in **buckets**. Each object has a key (like a filepath), the data itself, and metadata. There is no real directory hierarchy — the "folders" you see in S3 are just key prefixes.

```python
import boto3

s3 = boto3.client("s3")

# Upload a file
s3.upload_file("local_photo.jpg", "my-app-uploads", "avatars/user_123.jpg")

# Generate a URL anyone can use to download it
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": "my-app-uploads", "Key": "avatars/user_123.jpg"},
    ExpiresIn=3600  # URL valid for 1 hour
)
```

Object storage is fundamentally different from a filesystem:

- **Virtually unlimited capacity** — you do not manage disks, S3 scales for you
- **Built-in redundancy** — your data is replicated across multiple data centers automatically
- **HTTP accessible** — every object has a URL, making it easy to serve to users
- **Flat namespace** — no real directories, just keys like `avatars/user_123.jpg`
- **No append or partial update** — you replace the whole object or nothing

**Block storage** (AWS EBS, GCP Persistent Disks) is the third type. It provides raw disk volumes that you attach to a server and format with a filesystem. It is what your cloud VM's hard drive actually is. You rarely interact with it directly unless you are doing database administration or need high-performance disk I/O.

**When to use what:**

| Type | Use case | Example |
|------|----------|---------|
| Object storage (S3) | User uploads, static assets, backups, logs | Profile pictures, PDF reports, log archives |
| File storage (EFS/NFS) | Shared filesystem across servers | Legacy apps that need POSIX filesystem |
| Block storage (EBS) | Database storage, high-performance I/O | PostgreSQL data directory, application state |
| Database | Structured, queryable data | User records, orders, relationships |

**CDNs (Content Delivery Networks)** sit in front of your object storage and cache files at edge locations around the world. When a user in Tokyo requests an image, they get it from a nearby CDN node instead of your S3 bucket in Virginia. CloudFront, Cloudflare, and Fastly are the big names. For any app serving static content globally, a CDN is essential.

**Why SREs care:** Storage is one of the three fundamental infrastructure resources (compute, storage, networking). Understanding storage tiers, costs, durability guarantees, and performance characteristics is core to infrastructure design. S3 in particular is everywhere — application data, infrastructure backups, Terraform state, CloudTrail logs, and more.

<!-- RESOURCES -->

- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/) -- type: reference, time: varies
- [Cloud Storage Explained (AWS vs GCP vs Azure)](https://cloud.google.com/learn/what-is-object-storage) -- type: article, time: 15m
- [MinIO - Self-hosted S3-compatible Storage](https://min.io/docs/minio/linux/index.html) -- type: tool, time: 30m
- [Cloudflare CDN Docs](https://developers.cloudflare.com/cache/) -- type: reference, time: 20m

<!-- ZH_SUMMARY -->
你的应用允许用户上传头像。这些图片去了哪里？你可以对它们进行 base64 编码并存储到数据库的某一列中——但你的数据库体积会膨胀，查询会慢如蜗牛，你的 DBA 会哭的。文件和数据库是不同类型的数据，它们需要不同类型的存储。

<!-- ZH_DEEP_DIVE -->
**文件存储**是你已经熟悉的东西——文件系统上的目录和文件。`/home/user/photos/vacation.jpg`。它是分层的（文件夹中嵌套文件夹），支持权限，并且每个操作系统都能理解它。对于运行在单台服务器上的小型应用来说，将上传文件存储在本地文件系统上完全没问题：

```python
import os
from flask import Flask, request

app = Flask(__name__)
UPLOAD_DIR = "/var/uploads"

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["avatar"]
    filename = f"{user_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    return {"path": filepath}
```

这在你的笔记本电脑上可以正常工作。但当你有两台服务器位于负载均衡器后面时会发生什么？用户上传到服务器 A，而他们的下一个请求打到了服务器 B——服务器 B 上没有这个文件。本地文件系统存储无法扩展。

**对象存储**（Amazon S3、Google Cloud Storage、Azure Blob Storage）解决了这个问题。不再是目录中的文件，而是**桶**中的**对象**。每个对象都有一个键（类似文件路径）、数据本身以及元数据。没有真正的目录层级——你在 S3 中看到的“文件夹”只是键前缀。

```python
import boto3

s3 = boto3.client("s3")

# Upload a file
s3.upload_file("local_photo.jpg", "my-app-uploads", "avatars/user_123.jpg")

# Generate a URL anyone can use to download it
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": "my-app-uploads", "Key": "avatars/user_123.jpg"},
    ExpiresIn=3600  # URL valid for 1 hour
)
```

对象存储与文件系统有着根本性的不同：

- **几乎无限的容量**——你无需管理磁盘，S3 会为你扩展
- **内置冗余**——你的数据会自动复制到多个数据中心
- **可通过 HTTP 访问**——每个对象都有一个 URL，便于提供给用户
- **扁平命名空间**——没有真正的目录，只有像 `avatars/user_123.jpg` 这样的键
- **不支持追加或部分更新**——你要么替换整个对象，要么什么都不做

**块存储**（AWS EBS、GCP Persistent Disks）是第三种类型。它提供原始磁盘卷，你将其挂载到服务器上并用文件系统格式化。它实际上就是你的云虚拟机硬盘。除非你在做数据库管理或需要高性能磁盘 I/O，否则很少直接与它交互。

**何时使用哪种：**

| 类型 | 使用场景 | 示例 |
|------|----------|---------|
| 对象存储（S3） | 用户上传、静态资源、备份、日志 | 头像、PDF 报告、日志归档 |
| 文件存储（EFS/NFS） | 跨服务器共享文件系统 | 需要 POSIX 文件系统的遗留应用 |
| 块存储（EBS） | 数据库存储、高性能 I/O | PostgreSQL 数据目录、应用状态 |
| 数据库 | 结构化、可查询的数据 | 用户记录、订单、关系 |

**CDN（内容分发网络）**位于你的对象存储之前，并在世界各地的边缘位置缓存文件。当东京的用户请求一张图片时，他们会从附近的 CDN 节点获取，而不是从你位于弗吉尼亚的 S3 桶获取。CloudFront、Cloudflare 和 Fastly 是其中的大牌。对于任何向全球提供静态内容的应用来说，CDN 都是必不可少的。

**为什么 SRE 关心：**存储是三大基础基础设施资源之一（计算、存储、网络）。理解存储层级、成本、持久性保证和性能特征是基础设施设计的核心。S3 尤其无处不在——应用数据、基础设施备份、Terraform 状态、CloudTrail 日志等等。

<!-- ZH_RESOURCES -->
- [Amazon S3 文档](https://docs.aws.amazon.com/s3/) -- 类型：参考，时间：不定
- [云存储解析（AWS vs GCP vs Azure）](https://cloud.google.com/learn/what-is-object-storage) -- 类型：文章，时间：15分钟
- [MinIO - 自托管 S3 兼容存储](https://min.io/docs/minio/linux/index.html) -- 类型：工具，时间：30分钟
- [Cloudflare CDN 文档](https://developers.cloudflare.com/cache/) -- 类型：参考，时间：20分钟

<!-- ZH_UI -->
1. 理解文件存储、块存储和对象存储之间的区别
2. 在 Web 应用中处理文件上传并将其存储到磁盘上
3. 使用兼容 S3 的 API 存储和检索对象
4. 我能处理文件和数据了。现在该如何部署这一切？
5. 我的应用处理上传并将它们存储到本地文件系统上——但这只在我自己的机器上有效。如果我部署到服务器上，用户上传文件后，这些文件实际会去哪里？我不能完全依赖服务器的磁盘。我需要弄清楚在真实部署中文件存储是如何工作的。
