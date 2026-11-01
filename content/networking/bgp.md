---
id: bgp
title: 'BGP: How the Internet Shares Routes'
zone: networking
difficulty: 3
tags:
  - bgp
  - routing
  - autonomous-system
  - internet
  - peering
  - as
category: concept
milestones:
  - Explain what an Autonomous System is and give examples
  - Describe how BGP lets ISPs and networks exchange routing information
  - Understand why a BGP misconfiguration can cause widespread internet outages
title_zh: "BGP：互联网如何共享路由"

---


There are roughly 900,000 routes on the internet. Every major router knows how to reach every network in the world. No one typed those routes in manually — they were learned automatically through **BGP**, the Border Gateway Protocol. BGP is the protocol that lets the internet's networks tell each other "I can reach these IP ranges — send traffic my way." It is the glue that holds the internet together, and when it breaks, large parts of the internet break with it.

<!-- DEEP_DIVE -->

**Autonomous Systems (AS):** The internet is divided into Autonomous Systems — independently operated networks, each with a unique **AS number (ASN)**. Your ISP is an AS. AWS is an AS. Google is an AS. Each AS controls its own IP ranges and its own internal routing. BGP is what happens *between* ASes.

```
AS15169 (Google)     — owns 142.250.0.0/15, 8.8.8.0/24, etc.
AS16509 (Amazon)     — owns 54.0.0.0/8, 52.0.0.0/8, etc.
AS7922  (Comcast)    — your ISP, owns large residential IP blocks
```

**How BGP works:** Each AS announces the IP prefixes it owns to its neighbors. Those neighbors pass the announcements along. Within minutes, every BGP router on the internet knows "to reach 142.250.0.0/15, go toward Google's AS."

```
Google announces: "I own 142.250.0.0/15"
    → Google's peers hear it
    → They tell their peers
    → It propagates globally in minutes
```

When you send a packet to `142.250.80.100`, each router along the way is following a BGP-learned route.

**Why BGP outages are catastrophic:** BGP trusts its neighbors. If an AS accidentally (or maliciously) announces routes it doesn't own — called a **route hijack** — traffic for those IP ranges starts flowing the wrong way. In 2021, Facebook accidentally withdrew their own BGP routes, making Facebook, Instagram, and WhatsApp unreachable globally for 6 hours. In 2010, a Chinese ISP accidentally announced 50,000 incorrect routes, briefly rerouting traffic through China.

BGP is powerful, old, and built on trust. Understanding it explains why "the internet is down" sometimes means a routing misconfiguration thousands of miles away.

<!-- RESOURCES -->

- [BGP Explained - Cloudflare](https://www.cloudflare.com/learning/security/glossary/what-is-bgp/) -- type: article, time: 15m
- [The Internet's Most Fragile System - BGP](https://www.youtube.com/watch?v=wIa_lPBONxE) -- type: video, time: 20m
- [BGP Route Hijacking Explained](https://www.cloudflare.com/learning/security/glossary/bgp-hijacking/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
互联网上大约有 90 万条路由。每一台主要路由器都知道如何到达世界上的每一个网络。没有人手动输入这些路由——它们是通过 **BGP**（边界网关协议）自动学习到的。BGP 是让互联网中的各个网络相互告知“我能到达这些 IP 段——把流量发给我”的协议。它是把互联网粘合在一起的粘合剂，一旦它出问题，互联网的大片区域也会随之瘫痪。

<!-- ZH_DEEP_DIVE -->
**自治系统（AS）：** 互联网被划分为多个自治系统——即独立运营的网络，每个网络都有一个唯一的 **AS 号（ASN）**。你的 ISP 是一个 AS。AWS 是一个 AS。Google 是一个 AS。每个 AS 控制自己的 IP 地址段和内部路由。BGP 发生在 AS *之间*。

```
AS15169 (Google)     — owns 142.250.0.0/15, 8.8.8.0/24, etc.
AS16509 (Amazon)     — owns 54.0.0.0/8, 52.0.0.0/8, etc.
AS7922  (Comcast)    — your ISP, owns large residential IP blocks
```

**BGP 的工作原理：** 每个 AS 向它的邻居通告自己拥有的 IP 前缀。邻居再把这些通告继续传递下去。几分钟之内，互联网上的每台 BGP 路由器都会知道“要到达 142.250.0.0/15，就朝 Google 的 AS 方向走”。

```
Google announces: "I own 142.250.0.0/15"
    → Google's peers hear it
    → They tell their peers
    → It propagates globally in minutes
```

当你向 `142.250.80.100` 发送数据包时，沿途的每台路由器都在遵循一条通过 BGP 学到的路由。

**为什么 BGP 故障是灾难性的：** BGP 信任它的邻居。如果一个 AS 意外地（或恶意地）通告了它并不拥有的路由——这被称为**路由劫持**——那么发往这些 IP 地址段的流量就会开始流向错误的方向。2021 年，Facebook 意外撤销了自己的 BGP 路由，导致 Facebook、Instagram 和 WhatsApp 在全球范围内无法访问长达 6 小时。2010 年，一家中国 ISP 意外通告了 50,000 条错误路由，短暂地将流量改道经过中国。

BGP 强大、古老，且建立在信任之上。理解它就能明白，为什么有时“互联网挂了”意味着数千英里之外的一处路由配置错误。

<!-- ZH_RESOURCES -->
- [BGP 详解 - Cloudflare](https://www.cloudflare.com/learning/security/glossary/what-is-bgp/) -- 类型：文章，时长：15 分钟
- [互联网最脆弱的系统 - BGP](https://www.youtube.com/watch?v=wIa_lPBONxE) -- 类型：视频，时长：20 分钟
- [BGP 路由劫持详解](https://www.cloudflare.com/learning/security/glossary/bgp-hijacking/) -- 类型：文章，时长：10 分钟

<!-- ZH_UI -->
1. 解释什么是自治系统，并举例说明
2. 描述 BGP 如何让 ISP 和网络交换路由信息
3. 理解为什么 BGP 配置错误会导致大范围互联网中断
