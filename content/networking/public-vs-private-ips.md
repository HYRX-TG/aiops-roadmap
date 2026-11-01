---
id: public-vs-private-ips
title: Public vs Private IPs
zone: networking
edges:
  to:
    - id: where-do-i-run-this
      zone: running
      question: >-
        I understand addressing — private networks, public IPs, NAT. But where
        do I actually run something that serves content?
      detail: >-
        I understand private vs public IPs and NAT now. But my laptop is behind
        NAT — so where do I actually put something if I want real users to reach
        it? I need a machine that has its own public IP and is always reachable.
        What even is that, and how do I get one?
    - id: dns
      question: >-
        I understand public IPs. But nobody types IP addresses — they type
        domain names. How does that translation work?
      detail: >-
        I understand that servers have public IPs. But nobody types an IP
        address — they type google.com, or my-app.example.com. My computer must
        be translating that name to an IP somehow, but I have no idea how. That
        translation happens before every single request I make, and I've never
        thought about it.
    - id: how-packets-travel
      question: >-
        I know about public IPs. But how does a packet actually travel across
        the internet to reach one?
      detail: >-
        I understand that public IPs are reachable from anywhere on the
        internet. But what does 'anywhere' actually mean? When I send a packet
        to Tokyo, it doesn't teleport there — it has to physically travel
        through routers and cables. I don't understand what that journey looks
        like or who's making decisions along the way.
difficulty: 2
tags:
  - ip
  - nat
  - private
  - public
  - ipv4
  - network
category: concept
milestones:
  - Identify the three private IP ranges and what each is typically used for
  - Explain how NAT lets many devices share one public IP
  - >-
    Describe why you can browse any website but can't easily receive incoming
    connections at home
title_zh: "公有 IP 与私有 IP"

---


Your laptop's IP is `192.168.1.42`. But if you asked a friend across the country to connect to your laptop at that address, it would not work. That address does not exist on the public internet — it only exists on your home network. There are two completely separate worlds of IP addresses: **private** (inside a network) and **public** (routable everywhere on the internet). Understanding the difference explains NAT, cloud networking, and why hosting from home is complicated.

<!-- DEEP_DIVE -->

**Private IP ranges** are reserved address blocks defined in RFC 1918. They can be freely used inside any private network. Crucially, routers on the public internet will never forward packets to these addresses — they exist only within local networks:

| Range | CIDR | Typically used for |
|-------|------|--------------------|
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | Cloud VPCs, corporate networks |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | Docker default bridge network |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | Home routers |

Your router assigns addresses from one of these ranges to your devices. Your neighbor's router does the same. You might both have a `192.168.1.42` on your respective networks, and that is perfectly fine — because neither of those addresses is visible on the internet.

**Public IP addresses** are globally unique, allocated by IANA and distributed through ISPs. Every packet on the internet has a public source and destination IP. When your web server is reachable at `104.21.4.56` — that is a public IP. Routers worldwide know how to forward packets to it.

**NAT (Network Address Translation)** is what lets your entire home share a single public IP. Your ISP gives your router one public IP. Your router gives your devices private addresses. NAT bridges them:

```
Request from your laptop:
  Source:      192.168.1.42:54321   (private, invisible to internet)
  Destination: 142.250.80.100:443   (google.com)

Router (NAT) rewrites the packet:
  Source:      73.42.100.15:60000   (your public IP)
  Destination: 142.250.80.100:443

NAT table entry: 73.42.100.15:60000 ↔ 192.168.1.42:54321

Response comes back to 73.42.100.15:60000
  → Router looks up NAT table
  → Rewrites destination to 192.168.1.42:54321
  → Delivers to your laptop
```

Your router tracks each outgoing connection and knows where to send incoming replies. This works great for browsing — your devices initiate the connections. It breaks down for hosting: nobody on the internet can initiate a connection to `192.168.1.42` because:
1. They don't know that address exists
2. Even if they tried, packets sent to `192.168.1.42` on the internet would be dropped

This is why running a server at home requires port forwarding — you configure your router to forward incoming connections on a specific port to a specific internal device. It works, but it is manual, fragile, and only one device can use each port.

**Cloud infrastructure makes this pattern explicit and intentional:**

```
Internet
    ↓
Load Balancer  ← public IP (104.21.4.56) — this is what the internet talks to
    ↓
App Servers    ← private IPs (10.0.1.5, 10.0.1.6) — only reachable inside the VPC
    ↓
Database       ← private IP (10.0.20.10) — no public IP at all
```

Your database has no public IP. It is only reachable from inside the VPC, from trusted services. Your load balancer has a public IP — it's the one entry point from the internet. This is deliberate security design: minimize what's exposed, protect everything else behind private addresses.

When you see `0.0.0.0/0` in a firewall rule or route table, it means "all addresses" — shorthand for "the entire internet."

```bash
# See your public IP (what the internet sees)
curl https://api.ipify.org

# See your private IP (what your local network sees)
ip addr show       # Linux
ifconfig en0       # macOS

# These will be different — that gap is NAT
```

<!-- RESOURCES -->

- [Cloudflare - What is NAT?](https://www.cloudflare.com/learning/network-layer/what-is-nat/) -- type: article, time: 10m
- [RFC 1918 - Private Address Space](https://datatracker.ietf.org/doc/html/rfc1918) -- type: reference, time: 10m
- [Julia Evans - Networking Zine](https://wizardzines.com/zines/networking/) -- type: zine, time: 15m

<!-- ZH_SUMMARY -->
你笔记本电脑的 IP 是 `192.168.1.42`。但如果你让远在另一个城市的朋友通过这个地址连接你的笔记本，是连不上的。这个地址在公共互联网上并不存在——它只存在于你的家庭网络中。IP 地址分为两个完全独立的世界：**私有**（网络内部）和**公共**（可在互联网上处处路由）。理解这一区别，就能解释 NAT、云网络，以及为什么从家里托管服务会很复杂。

<!-- ZH_DEEP_DIVE -->
**私有 IP 范围**是 RFC 1918 中定义的保留地址块。它们可以在任何私有网络内部自由使用。关键在于，公共互联网上的路由器永远不会将数据包转发到这些地址——它们只存在于本地网络内部：

| 范围 | CIDR | 典型用途 |
|-------|------|--------------------|
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | 云 VPC、企业网络 |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | Docker 默认桥接网络 |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | 家用路由器 |

你的路由器从这些范围之一为你的设备分配地址。你邻居的路由器也是如此。你们各自的网络上可能都有一个 `192.168.1.42`，这完全没问题——因为这两个地址在互联网上都不可见。

**公共 IP 地址**是全球唯一的，由 IANA 分配，并通过 ISP 分发。互联网上的每个数据包都有公共源 IP 和目的 IP。当你的 Web 服务器可通过 `104.21.4.56` 访问时——那就是一个公共 IP。全世界的路由器都知道如何将数据包转发到它。

**NAT（网络地址转换）**让你的整个家庭共享一个公共 IP。你的 ISP 给你的路由器一个公共 IP。你的路由器给你的设备分配私有地址。NAT 在两者之间架起桥梁：

```
Request from your laptop:
  Source:      192.168.1.42:54321   (private, invisible to internet)
  Destination: 142.250.80.100:443   (google.com)

Router (NAT) rewrites the packet:
  Source:      73.42.100.15:60000   (your public IP)
  Destination: 142.250.80.100:443

NAT table entry: 73.42.100.15:60000 ↔ 192.168.1.42:54321

Response comes back to 73.42.100.15:60000
  → Router looks up NAT table
  → Rewrites destination to 192.168.1.42:54321
  → Delivers to your laptop
```

你的路由器跟踪每个出站连接，并知道将传入的回复发送到哪里。这对于浏览网页非常有效——你的设备发起连接。但对于托管服务就行不通了：互联网上没有人能主动向 `192.168.1.42` 发起连接，因为：
1. 他们不知道那个地址存在
2. 即使他们尝试，在互联网上发送到 `192.168.1.42` 的数据包也会被丢弃

这就是为什么在家运行服务器需要端口转发——你配置路由器将特定端口上的传入连接转发到特定的内部设备。这可行，但它是手动的、脆弱的，而且每个端口只能供一个设备使用。

**云基础设施让这种模式变得明确且有意图：**

```
Internet
    ↓
Load Balancer  ← public IP (104.21.4.56) — this is what the internet talks to
    ↓
App Servers    ← private IPs (10.0.1.5, 10.0.1.6) — only reachable inside the VPC
    ↓
Database       ← private IP (10.0.20.10) — no public IP at all
```

你的数据库没有公共 IP。它只能从 VPC 内部、从受信任的服务访问。你的负载均衡器有一个公共 IP——它是来自互联网的唯一入口点。这是刻意的安全设计：最小化暴露面，将其他一切保护在私有地址之后。

当你在防火墙规则或路由表中看到 `0.0.0.0/0` 时，它表示“所有地址”——是“整个互联网”的简写。

```bash
# See your public IP (what the internet sees)
curl https://api.ipify.org

# See your private IP (what your local network sees)
ip addr show       # Linux
ifconfig en0       # macOS

# These will be different — that gap is NAT
```

<!-- ZH_RESOURCES -->
- [Cloudflare - 什么是 NAT？](https://www.cloudflare.com/learning/network-layer/what-is-nat/) -- 类型: 文章, 时长: 10m
- [RFC 1918 - 私有地址空间](https://datatracker.ietf.org/doc/html/rfc1918) -- 类型: 参考, 时长: 10m
- [Julia Evans - 网络小志](https://wizardzines.com/zines/networking/) -- 类型: 小志, 时长: 15m

<!-- ZH_UI -->
1. 识别三个私有 IP 地址段及其各自的典型用途
2. 解释 NAT 如何让多台设备共享一个公网 IP
3. 描述为什么你可以浏览任何网站，但在家里却不容易接收传入连接
4. 我理解了地址——私有网络、公网 IP、NAT。但我到底在哪里运行提供内容的东西？
5. 我现在理解了私有 IP 与公网 IP 以及 NAT。但我的笔记本在 NAT 后面——那如果我想让真实用户访问，我到底该把东西放在哪里？我需要一台拥有自己公网 IP 且始终可达的机器。那到底是什么，我又怎么获得一台？
6. 我理解了公网 IP。但没人会输入 IP 地址——他们输入域名。那个转换是怎么工作的？
7. 我理解了服务器有公网 IP。但没人会输入 IP 地址——他们输入 google.com 或 my-app.example.com。我的电脑一定在以某种方式把这个名字转换成 IP，但我完全不知道是怎么做到的。这个转换发生在我发出的每一个请求之前，而我从未想过它。
8. 我了解公网 IP。但一个数据包实际上是如何穿越互联网到达它的？
9. 我理解了公网 IP 可以从互联网上的任何地方访问。但“任何地方”到底是什么意思？当我向东京发送一个数据包时，它并不会瞬移过去——它必须物理地经过路由器和线缆。我不理解那段旅程是什么样子，也不理解沿途是谁在做决定。
