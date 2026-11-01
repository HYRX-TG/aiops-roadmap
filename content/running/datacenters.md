---
id: datacenters
title: Datacenters
zone: running
edges:
  to:
    - id: linux-server-basics
      question: I know where servers live. How do I actually use one?
      detail: >-
        I understand what a datacenter is. But now I have actual hardware (or a
        VM) sitting somewhere I need to use. I've never managed a Linux server
        remotely before — I don't know where to start or what the basics even
        are.
    - id: what-is-a-vps
      question: >-
        Servers live in datacenters. How do I actually get one without going
        there?
      detail: >-
        Okay, so servers live in datacenters. But I'm not flying to a datacenter
        to plug in a machine. Clearly there's a way to get a server without
        physically going anywhere. How does that actually work — what am I
        renting, and what does it run on?
difficulty: 1
tags:
  - datacenter
  - colocation
  - infrastructure
  - power
  - cooling
  - redundancy
category: concept
milestones:
  - Understand what a datacenter is and why servers live there
  - 'Explain the role of redundant power, cooling, and networking'
  - Know the difference between colocation and cloud hosting
title_zh: "数据中心"

---


A server needs power, cooling, and a fast network connection — 24 hours a day, 365 days a year. Your apartment does not offer any of that reliably. A **datacenter** is a building purpose-built to keep servers running. Every website you visit, every app you use, every API you call — the servers behind them live in datacenters.

<!-- DEEP_DIVE -->

A **datacenter** is a facility designed to house computer systems and their associated components — servers, storage, networking equipment. The building itself is engineered for one thing: keeping those machines running without interruption.

**What is inside a datacenter:**

Walk into a datacenter and you will see rows and rows of **server racks** — tall metal cabinets, each holding dozens of servers stacked on top of each other. The racks are arranged in rows with alternating **hot aisles** and **cold aisles** — cold air blows in from the front of the servers, hot exhaust goes out the back. Containment systems keep the hot and cold air separated so cooling is efficient.

```
  [Cold Aisle]     [Hot Aisle]     [Cold Aisle]
  ┌─────────┐     ┌─────────┐     ┌─────────┐
  │ ═══════ │ ←── │ ═══════ │ ──→ │ ═══════ │
  │ ═══════ │     │ ═══════ │     │ ═══════ │
  │ ═══════ │     │ ═══════ │     │ ═══════ │
  │  Rack   │     │  Rack   │     │  Rack   │
  └─────────┘     └─────────┘     └─────────┘
    Cold air        Hot air         Cold air
    flows IN        flows OUT       flows IN
```

**Power** is the most critical system. Datacenters have multiple layers of redundancy:

1. **Utility power** — the main electrical feed from the power grid
2. **UPS (Uninterruptible Power Supply)** — batteries that kick in instantly if utility power drops, keeping servers running for minutes
3. **Generators** — diesel or natural gas generators that start within seconds and can run for days. They take over from the UPS while utility power is restored

A well-designed datacenter loses zero seconds of operation during a power outage. The UPS bridges the gap while generators spin up.

**Cooling** is the second biggest challenge. Servers generate enormous amounts of heat. A single server rack can draw 5-20 kW of power, and almost all of that energy becomes heat. Without cooling, temperatures would reach dangerous levels in minutes.

Cooling approaches:
- **CRAC units** (Computer Room Air Conditioning) — industrial air conditioning, the traditional approach
- **Evaporative cooling** — uses water evaporation, more energy-efficient in dry climates
- **Liquid cooling** — circulates coolant directly to server components, used in high-density deployments
- **Free cooling** — uses outside air when the climate allows it (datacenters in cold regions love this)

**Networking** in a datacenter is fast. Servers connect to **top-of-rack switches** at 10-25 Gbps. Those switches connect to **aggregation switches** and then to **core routers** that connect to the internet. The datacenter itself connects to the internet backbone through multiple independent connections from different providers — so if one ISP has an outage, traffic flows through another.

**Datacenter tiers** (defined by the Uptime Institute) describe levels of redundancy:

| Tier | Uptime | Downtime/Year | Key Feature |
|------|--------|---------------|-------------|
| Tier I | 99.671% | 28.8 hours | Single path for power and cooling |
| Tier II | 99.741% | 22 hours | Redundant components |
| Tier III | 99.982% | 1.6 hours | Maintainable without downtime |
| Tier IV | 99.995% | 26 minutes | Fault-tolerant, survives any single failure |

Most cloud providers operate at Tier III or IV. When AWS promises 99.99% availability for a service, this infrastructure is part of how they deliver it.

**Colocation** is when you own the servers but rent the space. You buy your hardware, ship it to a colocation facility, and they provide the rack space, power, cooling, and network connectivity. You are responsible for your own servers — if a disk fails at 3 AM, you drive to the datacenter (or send someone) to replace it.

**Managed hosting** is the middle ground — you rent both the space and the hardware, and the provider handles hardware maintenance.

**Cloud hosting** (AWS, GCP, Azure) is the highest level of abstraction — you do not touch hardware at all. The cloud provider owns the datacenters, the servers, the networking. You rent virtual slices of their infrastructure. When you create an EC2 instance, you are getting a virtual machine running on a physical server in one of Amazon's datacenters. You never see or touch that server.

**Physical security** is surprisingly strict. Datacenters have:
- Perimeter fencing, security cameras, 24/7 guards
- Biometric access (fingerprint, retina scan)
- Mantrap entries (two doors — the first must close before the second opens)
- Individual rack locks
- Visitor logs and escort requirements

This matters because physical access to a server means game over for security. If someone can touch your server, they can steal data, install malware, or simply unplug it.

**Why SREs care:** Understanding datacenters helps you understand cloud regions and availability zones, why network latency varies, what happens during "hardware failures," and why cloud providers charge for data transfer. When AWS says your instance is in `us-east-1a`, that is a specific datacenter (or section of one) in Northern Virginia. When you design for multi-AZ redundancy, you are putting servers in physically separate datacenters.

<!-- RESOURCES -->

- [Google Datacenter Tour (video)](https://www.youtube.com/watch?v=XZmGGAbHqa0) -- type: video, time: 5m
- [Cloudflare - What is a Data Center?](https://www.cloudflare.com/learning/cdn/glossary/data-center/) -- type: article, time: 10m
- [Uptime Institute Tier Standards](https://uptimeinstitute.com/tiers) -- type: reference, time: 10m
- [How AWS Builds Datacenters](https://aws.amazon.com/compliance/data-center/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
一台服务器需要电力、冷却和高速网络连接——全年 365 天、每天 24 小时不间断。你的公寓无法可靠地提供其中任何一项。**数据中心**是一栋专为维持服务器运行而建造的建筑。你访问的每个网站、使用的每个应用、调用的每个 API——其背后的服务器都位于数据中心里。

<!-- ZH_DEEP_DIVE -->
**数据中心**是专为容纳计算机系统及其相关组件——服务器、存储、网络设备——而设计的设施。建筑本身的设计目标只有一个：让这些机器不间断运行。

**数据中心内部有什么：**

走进数据中心，你会看到一排排的**服务器机架**——高大的金属机柜，每个机柜里堆叠着数十台服务器。机架按排排列，**热通道**和**冷通道**交替分布——冷空气从服务器正面吹入，热废气从背面排出。封闭系统将冷热空气隔离，以保证冷却效率。

```
  [Cold Aisle]     [Hot Aisle]     [Cold Aisle]
  ┌─────────┐     ┌─────────┐     ┌─────────┐
  │ ═══════ │ ←── │ ═══════ │ ──→ │ ═══════ │
  │ ═══════ │     │ ═══════ │     │ ═══════ │
  │ ═══════ │     │ ═══════ │     │ ═══════ │
  │  Rack   │     │  Rack   │     │  Rack   │
  └─────────┘     └─────────┘     └─────────┘
    Cold air        Hot air         Cold air
    flows IN        flows OUT       flows IN
```

**供电**是最关键的系统。数据中心有多层冗余：

1. **市电**——来自电网的主电源馈电
2. **UPS（不间断电源）**——电池组，在市电中断时瞬间接管，让服务器继续运行数分钟
3. **发电机**——柴油或天然气发电机，数秒内启动，可运行数天。在市电恢复期间，由发电机接管 UPS 的负载

设计良好的数据中心在停电期间零秒中断运行。UPS 在发电机启动期间填补空档。

**冷却**是第二大挑战。服务器产生大量热量。单个服务器机架可消耗 5-20 kW 电力，而几乎所有这些能量都转化为热量。没有冷却，温度会在几分钟内达到危险水平。

冷却方式：
- **CRAC 机组**（机房专用空调）——工业级空调，传统方案
- **蒸发冷却**——利用水蒸发，在干燥气候下更节能
- **液冷**——将冷却液直接循环到服务器组件，用于高密度部署
- **自然冷却**——在气候允许时利用室外空气（寒冷地区的数据中心非常青睐这种方式）

数据中心的**网络**速度很快。服务器以 10-25 Gbps 连接到**机架顶部交换机**。这些交换机连接到**汇聚交换机**，再连接到接入互联网的**核心路由器**。数据中心本身通过来自不同运营商的多个独立连接接入互联网骨干网——因此如果一家 ISP 发生故障，流量会走另一家。

**数据中心等级**（由 Uptime Institute 定义）描述了冗余级别：

| 等级 | 正常运行时间 | 每年停机时间 | 关键特性 |
|------|--------|---------------|-------------|
| Tier I | 99.671% | 28.8 小时 | 供电和冷却单路径 |
| Tier II | 99.741% | 22 小时 | 冗余组件 |
| Tier III | 99.982% | 1.6 小时 | 可维护而不停机 |
| Tier IV | 99.995% | 26 分钟 | 容错，可承受任何单点故障 |

大多数云提供商运营在 Tier III 或 IV 级别。当 AWS 承诺某项服务 99.99% 的可用性时，这套基础设施就是其实现方式的一部分。

**托管（Colocation）**是指你拥有服务器但租用空间。你购买硬件，运到托管设施，他们提供机架空间、电力、冷却和网络连接。你对自己的服务器负责——如果凌晨 3 点磁盘故障，你得开车去数据中心（或派人去）更换。

**管理型托管**是中间方案——你同时租用空间和硬件，提供商负责硬件维护。

**云托管**（AWS、GCP、Azure）是最高级别的抽象——你完全不接触硬件。云提供商拥有数据中心、服务器和网络。你租用其基础设施的虚拟切片。当你创建 EC2 实例时，你得到的是运行在亚马逊某个数据中心物理服务器上的虚拟机。你永远看不到也摸不到那台服务器。

**物理安全**严格得令人意外。数据中心有：
- 周界围栏、安全摄像头、24/7 保安
- 生物识别访问（指纹、视网膜扫描）
- 防尾随入口（两道门——第一道必须关闭后第二道才能打开）
- 独立机架锁
- 访客日志和陪同要求

这很重要，因为对服务器的物理访问意味着安全上的彻底失守。如果有人能接触到你的服务器，他们就能窃取数据、安装恶意软件，或者干脆拔掉电源。

**为什么 SRE 要关心：**理解数据中心有助于你理解云区域和可用区、网络延迟为何变化、“硬件故障”期间发生了什么，以及云提供商为何对数据传输收费。当 AWS 说你的实例在 `us-east-1a` 时，那是北弗吉尼亚的一个特定数据中心（或数据中心的一部分）。当你设计多可用区冗余时，你是在把服务器放在物理上独立的数据中心里。

<!-- ZH_RESOURCES -->
- [Google 数据中心参观（视频）](https://www.youtube.com/watch?v=XZmGGAbHqa0) -- 类型：视频，时长：5 分钟
- [Cloudflare - 什么是数据中心？](https://www.cloudflare.com/learning/cdn/glossary/data-center/) -- 类型：文章，时长：10 分钟
- [Uptime Institute 等级标准](https://uptimeinstitute.com/tiers) -- 类型：参考资料，时长：10 分钟
- [AWS 如何构建数据中心](https://aws.amazon.com/compliance/data-center/) -- 类型：文章，时长：15 分钟

<!-- ZH_UI -->
1. 了解什么是数据中心以及服务器为何部署在那里
2. 解释冗余电源、冷却和网络的作用
3. 了解托管与云托管的区别
4. 我知道服务器在哪里。我该如何实际使用一台？
5. 我明白什么是数据中心。但现在我有实际硬件（或虚拟机）放在某处需要使用。我以前从未远程管理过 Linux 服务器——我不知道从哪里开始，甚至不知道基础是什么。
6. 服务器在数据中心里。我如何实际获得一台而不用去那里？
7. 好吧，服务器在数据中心里。但我不会飞到数据中心去插一台机器。显然有一种方法可以不用亲自去任何地方就能获得服务器。这到底是怎么运作的——我在租什么，它运行在什么上？
