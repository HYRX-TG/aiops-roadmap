---
id: subnets-and-cidr
title: Subnets & CIDR
zone: networking
edges:
  to:
    - id: public-vs-private-ips
      question: >-
        I understand how addresses are organized. But why do some IPs only work
        at home while others work anywhere on the internet?
      detail: >-
        I understand how subnets carve up address space into groups. But I've
        noticed that my home IP is always 192.168.something, while servers have
        completely different addresses — and I can't reach my home machine from
        outside. There seems to be a fundamental split between addresses that
        work anywhere and ones that only work locally. What's going on there?
    - id: how-packets-travel
      question: >-
        Traffic between subnets needs a router. But how does a router know where
        to send a packet?
      detail: >-
        I get that my routing table says 'local subnet: direct, everything else:
        send to my gateway.' But then what? My router gets the packet — and it
        somehow ends up at a server on the other side of the world. How does any
        router along the way know where to send something? There must be routers
        in between that are making decisions I don't understand.
difficulty: 2
tags:
  - subnets
  - cidr
  - ipv4
  - routing
  - network
category: concept
milestones:
  - Explain what a subnet mask tells you about an IP address
  - Read CIDR notation and calculate how many hosts fit in a subnet
  - Describe why subnets are used to organize networks
title_zh: "子网与 CIDR"

---


Your laptop is `192.168.1.42`. Your phone is `192.168.1.43`. Your router is `192.168.1.1`. These aren't random — they all belong to the same **subnet**: a chunk of IP addresses that form one logical network. Devices on the same subnet can talk directly to each other. Devices on different subnets need a router to forward traffic between them.

<!-- DEEP_DIVE -->

Every IP address has two parts: the **network portion** (which subnet is this?) and the **host portion** (which device on that subnet?). The **subnet mask** tells you where the split is.

```
IP Address:    192.168.1.42
Subnet Mask:   255.255.255.0
               ────────────  ──
               Network part  Host part

Network:       192.168.1.0    (the subnet — all addresses that share this prefix)
Host:          .42            (this specific device within the subnet)
Broadcast:     192.168.1.255  (special address: sends to ALL devices on this subnet)
```

**CIDR notation** is the modern shorthand. Instead of writing out `255.255.255.0`, you write `/24` — meaning the first 24 bits are the network portion. So `192.168.1.0/24` means "the network where the first 24 bits are fixed, leaving 8 bits (2⁸ = 256 addresses) for devices."

```
192.168.1.42/24
│           │└─ /24 means: first 24 bits are the network
│           └── .42 is the host — this specific device
└────────────── 192.168.1.0 is the network (the subnet itself)
```

Common subnet sizes:

| CIDR | Subnet Mask | Usable Hosts | Typical use |
|------|-------------|-------------|-------------|
| /24 | 255.255.255.0 | 254 | Home network, small office |
| /16 | 255.255.0.0 | 65,534 | Large corporate network |
| /8 | 255.0.0.0 | 16.7 million | The entire `10.x.x.x` range |
| /32 | 255.255.255.255 | 1 | A single specific host (used in firewall rules) |
| /30 | 255.255.255.252 | 2 | Point-to-point links between routers |

Note: each subnet loses 2 addresses — one for the network address (`.0`) and one for broadcast (`.255`) — so a /24 has 256 total but only 254 usable for devices.

**Why subnets exist:** Subnets let you divide a large address space into isolated segments. A company might structure their network like this:

```
10.0.1.0/24   — engineering team    (up to 254 devices)
10.0.2.0/24   — marketing team      (up to 254 devices)
10.0.10.0/24  — production servers
10.0.20.0/24  — database servers
```

Traffic within `10.0.10.0/24` (between app servers) flows directly, without hitting a router. Traffic from `10.0.1.x` (engineering) to `10.0.20.x` (databases) must pass through a router — and that's where you apply firewall rules that say "engineers' laptops cannot connect directly to production databases."

**Your routing table makes this concrete:**

```bash
# View your routing table on Linux
ip route

# On macOS
netstat -rn

# Typical output:
# 192.168.1.0/24 dev eth0         ← this subnet: send directly to the interface
# default via 192.168.1.1 dev eth0  ← everything else: send to the router
```

Your machine sees `192.168.1.x`? Send it directly. Anything else? Forward to `192.168.1.1` (your router) and let it figure it out.

**In the cloud, this is explicit.** When you create an AWS VPC, you pick a CIDR block (`10.0.0.0/16`). Then you carve it into subnets (`10.0.1.0/24` for web servers, `10.0.2.0/24` for databases). This is the same concept — just managed by cloud infrastructure instead of physical switches. When a pod can't reach a database, or a security group is blocking traffic, you're almost always debugging subnet and routing problems. CIDR notation is daily vocabulary for anyone working in cloud infrastructure.

<!-- RESOURCES -->

- [Cloudflare - What is a subnet?](https://www.cloudflare.com/learning/network-layer/what-is-a-subnet/) -- type: article, time: 10m
- [Subnet Calculator](https://www.subnet-calculator.com/) -- type: tool, time: 5m
- [CIDR Notation Explained](https://aws.amazon.com/what-is/cidr/) -- type: article, time: 10m
- [Practical Networking - Subnetting](https://www.practicalnetworking.net/stand-alone/subnetting-mastery/) -- type: series, time: 2h

<!-- ZH_SUMMARY -->
你的笔记本电脑是 `192.168.1.42`。你的手机是 `192.168.1.43`。你的路由器是 `192.168.1.1`。这些地址并非随机——它们都属于同一个**子网**：一组构成单一逻辑网络的 IP 地址。同一子网内的设备可以直接相互通信。不同子网内的设备则需要路由器在它们之间转发流量。

<!-- ZH_DEEP_DIVE -->
每个 IP 地址都由两部分组成：**网络部分**（属于哪个子网？）和**主机部分**（该子网上的哪台设备？）。**子网掩码**告诉你分界点在哪里。

```
IP Address:    192.168.1.42
Subnet Mask:   255.255.255.0
               ────────────  ──
               Network part  Host part

Network:       192.168.1.0    (the subnet — all addresses that share this prefix)
Host:          .42            (this specific device within the subnet)
Broadcast:     192.168.1.255  (special address: sends to ALL devices on this subnet)
```

**CIDR 表示法**是现代简写形式。不用写出 `255.255.255.0`，而是写 `/24`——表示前 24 位是网络部分。因此 `192.168.1.0/24` 的意思是“前 24 位固定不变、剩余 8 位（2⁸ = 256 个地址）留给设备的网络”。

```
192.168.1.42/24
│           │└─ /24 means: first 24 bits are the network
│           └── .42 is the host — this specific device
└────────────── 192.168.1.0 is the network (the subnet itself)
```

常见子网大小：

| CIDR | Subnet Mask | Usable Hosts | Typical use |
|------|-------------|-------------|-------------|
| /24 | 255.255.255.0 | 254 | Home network, small office |
| /16 | 255.255.0.0 | 65,534 | Large corporate network |
| /8 | 255.0.0.0 | 16.7 million | The entire `10.x.x.x` range |
| /32 | 255.255.255.255 | 1 | A single specific host (used in firewall rules) |
| /30 | 255.255.255.252 | 2 | Point-to-point links between routers |

注意：每个子网都会损失 2 个地址——一个用于网络地址（`.0`），一个用于广播地址（`.255`）——所以 /24 总共有 256 个地址，但只有 254 个可供设备使用。

**子网存在的意义：** 子网让你能把一个大的地址空间划分成相互隔离的网段。一家公司可能会这样组织自己的网络：

```
10.0.1.0/24   — engineering team    (up to 254 devices)
10.0.2.0/24   — marketing team      (up to 254 devices)
10.0.10.0/24  — production servers
10.0.20.0/24  — database servers
```

`10.0.10.0/24` 内部的流量（应用服务器之间）直接流动，不经过路由器。从 `10.0.1.x`（工程团队）到 `10.0.20.x`（数据库）的流量必须经过路由器——而正是在这里，你可以应用防火墙规则，规定“工程师的笔记本电脑不能直接连接生产数据库”。

**你的路由表让这一点变得具体：**

```bash
# View your routing table on Linux
ip route

# On macOS
netstat -rn

# Typical output:
# 192.168.1.0/24 dev eth0         ← this subnet: send directly to the interface
# default via 192.168.1.1 dev eth0  ← everything else: send to the router
```

你的机器看到 `192.168.1.x`？直接发送。其他任何地址？转发给 `192.168.1.1`（你的路由器），让它去处理。

**在云环境中，这一点是显式的。** 当你创建 AWS VPC 时，你会选择一个 CIDR 块（`10.0.0.0/16`）。然后把它切分成子网（`10.0.1.0/24` 用于 Web 服务器，`10.0.2.0/24` 用于数据库）。这是同一个概念——只不过由云基础设施管理，而不是物理交换机。当某个 pod 无法访问数据库，或者某个安全组阻断了流量时，你几乎总是在调试子网和路由问题。对于任何从事云基础设施工作的人来说，CIDR 表示法是日常词汇。

<!-- ZH_RESOURCES -->
- [Cloudflare - 什么是子网？](https://www.cloudflare.com/learning/network-layer/what-is-a-subnet/) -- 类型：文章，时长：10分钟
- [子网计算器](https://www.subnet-calculator.com/) -- 类型：工具，时长：5分钟
- [CIDR 表示法详解](https://aws.amazon.com/what-is/cidr/) -- 类型：文章，时长：10分钟
- [Practical Networking - 子网划分](https://www.practicalnetworking.net/stand-alone/subnetting-mastery/) -- 类型：系列，时长：2小时

<!-- ZH_UI -->
1. 解释子网掩码能告诉你关于 IP 地址的哪些信息
2. 读懂 CIDR 表示法并计算一个子网能容纳多少主机
3. 描述为什么用子网来组织网络
4. 我理解地址是如何组织的。但为什么有些 IP 只能在家用，而另一些在互联网上任何地方都能用？
5. 我理解子网如何把地址空间划分成组。但我注意到我家里的 IP 总是 192.168 开头，而服务器是完全不同的地址——而且我从外面访问不到家里的机器。似乎存在一种根本性的区分：有些地址在任何地方都能用，有些只能在本地用。这是怎么回事？
6. 子网之间的流量需要路由器。但路由器怎么知道把数据包发到哪里？
7. 我明白我的路由表写着“本地子网：直连，其他一切：发给我的网关”。但然后呢？我的路由器收到数据包——然后它不知怎么就到达了世界另一端的服务器。沿途的任何一个路由器怎么知道该把东西发到哪里？中间一定有路由器在做我不理解的决策。
