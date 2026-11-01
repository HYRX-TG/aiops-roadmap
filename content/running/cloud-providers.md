---
id: cloud-providers
title: Cloud Providers
zone: running
edges:
  to:
    - id: linux-server-basics
      question: I have a cloud VM. How do I actually use it?
      detail: >-
        I've got a cloud VM with a public IP but I have no idea what to do with
        it. I've never remotely managed a Linux server before — how do I even
        connect, and what do I actually need to learn?
    - id: what-is-a-vps
      question: What am I actually renting when I create a cloud server?
      detail: >-
        I clicked a button and now I have a 'server' — but it doesn't feel like
        a real machine. It's somewhere in the cloud, I have no idea what
        hardware it's running on, and it seems like other people's VMs are on
        the same physical box. What did I actually just create?
difficulty: 1
tags:
  - cloud
  - aws
  - gcp
  - azure
  - digitalocean
  - vm
  - iaas
category: concept
milestones:
  - Understand what IaaS is and how cloud VMs work
  - Create a virtual machine on a cloud provider
  - 'Explain regions, availability zones, and why they matter'
title_zh: "云服务提供商"

---


You could buy a server, find a datacenter, and set everything up yourself. Or you could open a browser, click a few buttons, and have a server running in under a minute — with a public IP, a fresh operating system, and pay-by-the-hour pricing. That is what **cloud providers** offer, and it is how the vast majority of applications run today.

<!-- DEEP_DIVE -->

**Cloud computing** means renting computing resources instead of owning them. Instead of buying a $2,000 server, you rent a virtual one for $5-20/month. Instead of signing a 3-year datacenter contract, you pay by the hour and shut it down when you are done. The cloud provider owns and operates the physical infrastructure — you just use it.

**IaaS (Infrastructure as a Service)** is the cloud model most relevant right now. The provider gives you virtual machines, storage, and networking. You control the operating system and everything above it. This is what services like AWS EC2, DigitalOcean Droplets, and GCP Compute Engine provide.

The major cloud providers:

| Provider | VM Service | Best For | Pricing Model |
|----------|-----------|----------|---------------|
| **AWS** | EC2 | Industry standard, widest service range | Complex, per-second billing |
| **GCP** | Compute Engine | Data/ML workloads, good networking | Per-second, sustained discounts |
| **Azure** | Virtual Machines | Microsoft ecosystem, enterprise | Per-second billing |
| **DigitalOcean** | Droplets | Simplicity, learning, small projects | Fixed monthly, simple pricing |
| **Hetzner** | Cloud Servers | European hosting, excellent price/perf | Fixed monthly, very affordable |
| **Linode (Akamai)** | Linodes | Simple, developer-friendly | Fixed monthly |

**Creating your first VM** on DigitalOcean (the simplest to start with):

1. Create an account at digitalocean.com
2. Click "Create" → "Droplets"
3. Choose a region (pick one close to your users)
4. Choose an image: **Ubuntu 24.04 LTS**
5. Choose a plan: **Basic, $6/month** (1 vCPU, 1 GB RAM, 25 GB SSD)
6. Add your SSH key (so you can log in securely)
7. Click "Create Droplet"

In about 30 seconds, you have a server with a public IP address. You can SSH in immediately:

```bash
# Your droplet's IP appears in the dashboard
ssh root@143.198.100.50

# You are now on a server in a datacenter, running Ubuntu
```

**Virtual Machines (VMs)** are how cloud providers fit many customers on one physical server. A single physical server with 64 CPU cores and 256 GB RAM can run dozens of small VMs simultaneously. Each VM thinks it is a real computer — it has its own operating system, its own CPU allocation, its own memory. The **hypervisor** (software like KVM or Xen) manages the sharing.

```
Physical Server (64 cores, 256 GB RAM)
├── VM 1: 2 vCPU, 4 GB RAM  (Customer A - web server)
├── VM 2: 4 vCPU, 8 GB RAM  (Customer B - database)
├── VM 3: 1 vCPU, 1 GB RAM  (Customer C - small app)
├── VM 4: 2 vCPU, 4 GB RAM  (Customer D - API server)
└── ... more VMs
```

**Regions and Availability Zones** are how cloud providers organize their infrastructure geographically:

- A **region** is a geographic area — `us-east-1` (N. Virginia), `eu-west-1` (Ireland), `ap-southeast-1` (Singapore)
- An **availability zone (AZ)** is an isolated datacenter (or cluster of datacenters) within a region — `us-east-1a`, `us-east-1b`, `us-east-1c`
- AZs within a region have low-latency connections to each other but are physically separate — different buildings, different power feeds, different flood zones

Why this matters: if a single datacenter has a power failure, only one AZ goes down. If your app runs in multiple AZs, it survives. This is the foundation of high-availability architecture.

**What you get with a cloud VM:**

- A public IPv4 address (and usually IPv6)
- A fresh operating system (your choice — Ubuntu, Debian, CentOS, etc.)
- Root access — you can install anything
- Persistent storage (SSD-based)
- Network connectivity (usually 1-10 Gbps)
- A firewall you can configure (security groups, firewall rules)
- A web console for emergency access if SSH breaks

**What you are responsible for:**

- Operating system updates and security patches
- Software installation and configuration
- Backups (cloud VMs are not automatically backed up unless you set it up)
- Monitoring and alerting
- Security hardening

**Pricing** is straightforward for simple VMs but can get complex for larger deployments:

```
DigitalOcean Basic Droplet:
  1 vCPU, 1 GB RAM, 25 GB SSD, 1 TB transfer
  $6/month ($0.009/hour)

AWS EC2 t3.micro:
  2 vCPU, 1 GB RAM
  ~$7.50/month on-demand
  Free tier: 750 hours/month for 12 months

Data transfer (egress) is the hidden cost:
  DigitalOcean: 1 TB included, then $0.01/GB
  AWS: first 100 GB free, then $0.09/GB
```

The key insight: **compute is cheap, bandwidth is expensive.** A small server costs pocket change. But if your app serves large files or handles millions of requests, data transfer costs add up fast.

**Why SREs care:** Cloud providers are where your infrastructure lives. Understanding VM types, regions, availability zones, and pricing is fundamental. When someone says "spin up an EC2 instance in us-west-2," you need to know what that means. When designing for reliability, you need to understand AZs. When optimizing costs, you need to understand pricing models.

<!-- RESOURCES -->

- [DigitalOcean - How to Create a Droplet](https://docs.digitalocean.com/products/droplets/how-to/create/) -- type: tutorial, time: 15m
- [AWS EC2 Getting Started](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html) -- type: tutorial, time: 30m
- [Cloudflare - What is cloud computing?](https://www.cloudflare.com/learning/cloud/what-is-cloud-computing/) -- type: article, time: 10m
- [Cloud Provider Comparison - DigitalOcean vs AWS vs GCP](https://www.digitalocean.com/pricing) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
你可以买一台服务器，找一个数据中心，然后自己把一切搭建起来。或者，你可以打开浏览器，点几下按钮，不到一分钟就能让一台服务器运行起来——拥有公网 IP、全新的操作系统，以及按小时计费的价格。这就是**云服务商**所提供的东西，也是当今绝大多数应用的运行方式。

<!-- ZH_DEEP_DIVE -->
**云计算**指的是租用计算资源，而不是拥有它们。与其花 2,000 美元买一台服务器，不如每月花 5-20 美元租一台虚拟服务器。与其签一份 3 年的数据中心合同，不如按小时付费，用完就关掉。云提供商拥有并运营物理基础设施——你只是使用它。

**IaaS（基础设施即服务）**是当下最相关的云模型。提供商为你提供虚拟机、存储和网络。你控制操作系统及其上的一切。AWS EC2、DigitalOcean Droplets 和 GCP Compute Engine 等服务提供的正是这些。

主要的云提供商：

| 提供商 | 虚拟机服务 | 最适合 | 定价模式 |
|----------|-----------|----------|---------------|
| **AWS** | EC2 | 行业标准，服务范围最广 | 复杂，按秒计费 |
| **GCP** | Compute Engine | 数据/ML 工作负载，网络良好 | 按秒计费，持续使用折扣 |
| **Azure** | Virtual Machines | 微软生态，企业级 | 按秒计费 |
| **DigitalOcean** | Droplets | 简单、学习、小型项目 | 固定月费，定价简单 |
| **Hetzner** | Cloud Servers | 欧洲托管，性价比极佳 | 固定月费，非常实惠 |
| **Linode (Akamai)** | Linodes | 简单，对开发者友好 | 固定月费 |

**创建你的第一台虚拟机**（在 DigitalOcean 上，最容易上手）：

1. 在 digitalocean.com 创建账户
2. 点击“Create” → “Droplets”
3. 选择一个区域（选一个靠近你用户的）
4. 选择一个镜像：**Ubuntu 24.04 LTS**
5. 选择一个套餐：**Basic，$6/月**（1 vCPU、1 GB RAM、25 GB SSD）
6. 添加你的 SSH 密钥（这样你可以安全登录）
7. 点击“Create Droplet”

大约 30 秒后，你就拥有了一台带公网 IP 地址的服务器。你可以立即通过 SSH 登录：

```bash
# Your droplet's IP appears in the dashboard
ssh root@143.198.100.50

# You are now on a server in a datacenter, running Ubuntu
```

**虚拟机（VM）**是云提供商将众多客户装到一台物理服务器上的方式。一台拥有 64 个 CPU 核心和 256 GB RAM 的物理服务器可以同时运行几十台小型虚拟机。每台虚拟机都认为自己是一台真实的计算机——它有自己的操作系统、自己的 CPU 分配、自己的内存。**hypervisor**（如 KVM 或 Xen 之类的软件）负责管理这种共享。

```
Physical Server (64 cores, 256 GB RAM)
├── VM 1: 2 vCPU, 4 GB RAM  (Customer A - web server)
├── VM 2: 4 vCPU, 8 GB RAM  (Customer B - database)
├── VM 3: 1 vCPU, 1 GB RAM  (Customer C - small app)
├── VM 4: 2 vCPU, 4 GB RAM  (Customer D - API server)
└── ... more VMs
```

**区域和可用区**是云提供商在地理上组织其基础设施的方式：

- **区域（region）**是一个地理区域——`us-east-1`（北弗吉尼亚）、`eu-west-1`（爱尔兰）、`ap-southeast-1`（新加坡）
- **可用区（AZ）**是区域内一个隔离的数据中心（或数据中心集群）——`us-east-1a`、`us-east-1b`、`us-east-1c`
- 同一区域内的可用区之间具有低延迟连接，但物理上是分离的——不同的建筑、不同的供电线路、不同的洪水风险区

为什么这很重要：如果单个数据中心发生断电，只有一个可用区会宕机。如果你的应用运行在多个可用区，它就能存活。这是高可用架构的基础。

**云虚拟机为你提供：**

- 一个公网 IPv4 地址（通常还有 IPv6）
- 一个全新的操作系统（由你选择——Ubuntu、Debian、CentOS 等）
- root 访问权限——你可以安装任何东西
- 持久存储（基于 SSD）
- 网络连接（通常 1-10 Gbps）
- 一个你可以配置的防火墙（安全组、防火墙规则）
- 一个 Web 控制台，用于在 SSH 断开时进行紧急访问

**你需要负责：**

- 操作系统更新和安全补丁
- 软件安装和配置
- 备份（除非你自行设置，否则云虚拟机不会自动备份）
- 监控和告警
- 安全加固

**定价**对于简单的虚拟机来说很直接，但对于更大的部署可能会变得复杂：

```
DigitalOcean Basic Droplet:
  1 vCPU, 1 GB RAM, 25 GB SSD, 1 TB transfer
  $6/month ($0.009/hour)

AWS EC2 t3.micro:
  2 vCPU, 1 GB RAM
  ~$7.50/month on-demand
  Free tier: 750 hours/month for 12 months

Data transfer (egress) is the hidden cost:
  DigitalOcean: 1 TB included, then $0.01/GB
  AWS: first 100 GB free, then $0.09/GB
```

关键洞察：**计算很便宜，带宽很昂贵。** 一台小型服务器花不了几个钱。但如果你的应用提供大文件服务或处理数百万请求，数据传输成本会迅速累积。

**为什么 SRE 关心这些：** 云提供商是你的基础设施所在之处。理解虚拟机类型、区域、可用区和定价是基础。当有人说“在 us-west-2 启动一台 EC2 实例”时，你需要知道那是什么意思。在设计可靠性时，你需要理解可用区。在优化成本时，你需要理解定价模型。

<!-- ZH_RESOURCES -->
- [DigitalOcean - 如何创建 Droplet](https://docs.digitalocean.com/products/droplets/how-to/create/) -- 类型：教程，时长：15m
- [AWS EC2 入门](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html) -- 类型：教程，时长：30m
- [Cloudflare - 什么是云计算？](https://www.cloudflare.com/learning/cloud/what-is-cloud-computing/) -- 类型：文章，时长：10m
- [云服务商对比 - DigitalOcean vs AWS vs GCP](https://www.digitalocean.com/pricing) -- 类型：参考，时长：10m

<!-- ZH_UI -->
1. 理解什么是 IaaS 以及云虚拟机如何运作
2. 在云服务商上创建一台虚拟机
3. 解释区域、可用区以及它们为何重要
4. 我有一台云虚拟机，我该如何实际使用它？
5. 我有一台带公网 IP 的云虚拟机，但我完全不知道该怎么用它。我以前从未远程管理过 Linux 服务器——我该怎么连接，我实际需要学些什么？
6. 我创建云服务器时，实际租用的是什么？
7. 我点了个按钮，现在就有了一个“服务器”——但它感觉不像一台真实的机器。它在云端的某个地方，我不知道它运行在什么硬件上，而且似乎别人的虚拟机也在同一台物理机上。我到底创建了什么？
