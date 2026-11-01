---
id: how-packets-travel
title: How Packets Travel the Internet
zone: networking
edges:
  to:
    - id: bgp
      question: >-
        I understand how routers forward packets. But how do they know about all
        the routes on the internet?
      detail: >-
        My home router just has 'send everything to my ISP' — but somehow ISPs
        and major networks know about every IP block on the internet. Nobody
        manually configured millions of routes on millions of routers. Something
        must be letting them share and update that knowledge automatically. How
        does a router on one continent know how to reach a network it's never
        directly connected to?
difficulty: 2
tags:
  - routing
  - packets
  - ttl
  - traceroute
  - hops
  - gateway
  - internet
category: concept
milestones:
  - Describe what happens at each hop as a packet travels to its destination
  - Run traceroute and interpret the output
  - Explain what TTL is and why it exists
title_zh: "数据包如何穿越互联网"

---


Your laptop sends a packet to a server on the other side of the world. Between you and it: a dozen routers across multiple countries, owned by different companies. Your packet didn't teleport — it **hopped**. Each router received the packet, looked at the destination IP, made a decision about where to forward it next, and sent it on its way. Understanding those decisions is understanding how the internet actually works.

<!-- DEEP_DIVE -->

**The journey of a packet:**

```
Your laptop (192.168.1.42)
    ↓  "I need to reach 142.250.80.100 — not on my subnet, send to default gateway"
Your home router (192.168.1.1 / 73.42.100.15)
    ↓  "142.250.80.100 — not mine, forward to my ISP"
Your ISP's router
    ↓  "That's a Google IP — forward toward Google's network"
Peering point / transit router
    ↓  "Getting closer — forward to Google's AS"
Google's edge router
    ↓  "That's our IP — deliver to the data center"
Google's server (142.250.80.100)
```

Each router only needs to know the *next hop*, not the full path. Like giving directions one intersection at a time.

**TTL (Time to Live):** Every IP packet carries a TTL — a counter that starts at 64 or 128 and decrements by 1 at each router. If it hits zero, the router drops the packet and sends an "ICMP Time Exceeded" message back. This prevents packets from looping forever when routing goes wrong.

**traceroute** exploits TTL to map the path:

```bash
traceroute google.com
# or on macOS
traceroute google.com

# Windows
tracert google.com

# Example output:
#  1  192.168.1.1 (your router)       1ms
#  2  10.0.0.1 (ISP first hop)        8ms
#  3  72.14.232.1 (ISP backbone)      12ms
#  4  142.250.80.100 (Google)         15ms
```

Each line is one hop. The IP is that router's address. The time is the round-trip latency to that point. `* * *` means the router didn't respond (common — many routers silently drop TTL-expired packets).

**How routers build their tables:** Your home router knows two things: your local subnet (direct) and everything else (send to ISP). Your ISP's routers know far more — they've learned routes from other ISPs and large networks through a routing protocol. That protocol — how the internet's routers collectively figure out paths to every network — is BGP.

<!-- RESOURCES -->

- [How Routing Works - Cloudflare](https://www.cloudflare.com/learning/network-layer/what-is-routing/) -- type: article, time: 10m
- [Traceroute Explained](https://www.cloudflare.com/learning/network-layer/what-is-traceroute/) -- type: article, time: 10m
- [Packet Traveling - Practical Networking](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) -- type: series, time: 1h

<!-- ZH_SUMMARY -->
你的笔记本电脑向世界另一端的服务器发送一个数据包。在你和它之间：跨越多个国家、由不同公司拥有的十几台路由器。你的数据包并没有瞬移——它是**逐跳**前进的。每台路由器接收数据包，查看目的 IP，决定下一步将其转发到哪里，然后把它发送出去。理解这些决策，就是理解互联网实际如何运作。

<!-- ZH_DEEP_DIVE -->
**一个数据包的旅程：**

```
你的笔记本电脑 (192.168.1.42)
    ↓  “我需要到达 142.250.80.100 —— 不在我的子网内，发送到默认网关”
你的家庭路由器 (192.168.1.1 / 73.42.100.15)
    ↓  “142.250.80.100 —— 不是我的，转发给我的 ISP”
你的 ISP 的路由器
    ↓  “那是 Google 的 IP —— 向 Google 的网络转发”
对等点 / 中转路由器
    ↓  “越来越近了 —— 转发到 Google 的 AS”
Google 的边缘路由器
    ↓  “那是我们的 IP —— 投递到数据中心”
Google 的服务器 (142.250.80.100)
```

每个路由器只需要知道*下一跳*，而不是完整路径。就像每次只在一个路口给出方向指引。

**TTL（Time to Live，生存时间）：** 每个 IP 数据包都携带一个 TTL —— 一个从 64 或 128 开始的计数器，每经过一个路由器就减 1。如果它减到零，路由器就会丢弃该数据包，并回送一条“ICMP Time Exceeded”消息。这可以防止在路由出错时数据包永远循环。

**traceroute** 利用 TTL 来绘制路径：

```bash
traceroute google.com
# 或在 macOS 上
traceroute google.com

# Windows
tracert google.com

# 示例输出：
#  1  192.168.1.1 (你的路由器)       1ms
#  2  10.0.0.1 (ISP 第一跳)        8ms
#  3  72.14.232.1 (ISP 骨干网)      12ms
#  4  142.250.80.100 (Google)         15ms
```

每一行是一跳。IP 是该路由器的地址。时间则是到该点的往返延迟。`* * *` 表示该路由器没有响应（很常见 —— 许多路由器会静默丢弃 TTL 过期的数据包）。

**路由器如何构建它们的表：** 你的家庭路由器知道两件事：你的本地子网（直连）和其他所有内容（发送给 ISP）。你的 ISP 的路由器知道得多得多 —— 它们通过路由协议从其他 ISP 和大型网络那里学习路由。那个协议 —— 即互联网的路由器如何共同找出通往每个网络的路径 —— 就是 BGP。

<!-- ZH_RESOURCES -->
- [路由是如何工作的 - Cloudflare](https://www.cloudflare.com/learning/network-layer/what-is-routing/) -- 类型: 文章, 时间: 10m
- [Traceroute 详解](https://www.cloudflare.com/learning/network-layer/what-is-traceroute/) -- 类型: 文章, 时间: 10m
- [数据包之旅 - Practical Networking](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) -- 类型: 系列, 时间: 1h

<!-- ZH_UI -->
1. 描述数据包在前往目的地途中每一跳发生的情况
2. 运行 traceroute 并解读输出
3. 解释什么是 TTL 以及它为何存在
4. 我理解路由器如何转发数据包。但它们如何知道互联网上的所有路由？
5. 我的家用路由器只有“把所有流量发给我的 ISP”——但不知何故，ISP 和主要网络知道互联网上的每一个 IP 块。没有人手动在数百万台路由器上配置数百万条路由。一定有某种机制让它们自动共享和更新这些知识。一个大陆上的路由器如何知道如何到达一个它从未直接连接的网络？
