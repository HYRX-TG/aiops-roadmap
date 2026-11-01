---
id: dhcp
title: 'DHCP: How Devices Get Their IP'
zone: networking
difficulty: 1
tags:
  - dhcp
  - ip
  - network
  - automatic
  - lease
  - gateway
category: concept
milestones:
  - Explain the DHCP DORA process in plain terms
  - Identify what information DHCP assigns beyond just an IP address
  - Understand what a DHCP lease is and why leases expire
title_zh: "DHCP：设备如何获取 IP 地址"

---


Every time you connect to WiFi, your device gets an IP address — and you didn't type anything. No configuration screen, no decision to make, it just works. That is **DHCP** — the Dynamic Host Configuration Protocol. It's the protocol that automatically assigns IP addresses (and a few other critical settings) to devices when they join a network. Every home router runs a DHCP server, and so does every corporate network and cloud environment.

<!-- DEEP_DIVE -->

**The DORA process** — four steps that happen in milliseconds when you connect:

```
1. DISCOVER  — Your device broadcasts: "Is there a DHCP server here? I need an IP."
2. OFFER     — The DHCP server responds: "I can offer you 192.168.1.42, valid for 24 hours."
3. REQUEST   — Your device says: "I'll take 192.168.1.42 please."
4. ACK       — The server confirms: "It's yours. Here are your full settings."
```

DHCP doesn't just assign an IP — it hands your device a full network configuration:

| Setting | Example | Purpose |
|---------|---------|---------|
| IP address | `192.168.1.42` | Your device's address on this network |
| Subnet mask | `255.255.255.0` | Which addresses are on the same subnet |
| Default gateway | `192.168.1.1` | Where to send traffic destined outside the subnet |
| DNS server | `8.8.8.8` | Who to ask when resolving domain names |
| Lease time | `86400` seconds | How long the IP is yours before you need to renew |

**Leases:** A DHCP lease is temporary. Your device gets an IP for a set duration and must renew it before it expires. This allows the server to reclaim addresses from devices that left the network without saying goodbye. On most home networks the lease time is 24 hours. In busy environments (like conference WiFi) it might be 1 hour so addresses cycle quickly.

```bash
# See your current DHCP lease on Linux
ip addr show
# or
cat /var/lib/dhcp/dhclient.leases

# Release and renew your IP (Linux)
sudo dhclient -r eth0   # release
sudo dhclient eth0      # request a new one
```

**Static vs dynamic:** DHCP assigns addresses dynamically from a pool. Servers and infrastructure usually get **static IPs** — either assigned manually, or via DHCP reservations (telling the DHCP server "always give this MAC address this specific IP"). This is how your home router knows to always give your NAS the same address.

<!-- RESOURCES -->

- [What is DHCP? - Cloudflare](https://www.cloudflare.com/learning/network-layer/what-is-dhcp/) -- type: article, time: 10m
- [DHCP Explained - PowerCert](https://www.youtube.com/watch?v=e6-TaH5bkjo) -- type: video, time: 10m

<!-- ZH_SUMMARY -->
每次连接 WiFi 时，你的设备都会获得一个 IP 地址——而你什么都没输入。没有配置界面，无需做任何决定，一切自动完成。这就是 **DHCP**——动态主机配置协议。它负责在设备加入网络时自动为其分配 IP 地址（以及一些其他关键设置）。每个家用路由器都运行着 DHCP 服务器，每个企业网络和云环境也是如此。

<!-- ZH_DEEP_DIVE -->
**DORA 过程**——连接时在几毫秒内发生的四个步骤：

```
1. DISCOVER  — 你的设备广播：“这里有 DHCP 服务器吗？我需要一个 IP。”
2. OFFER     — DHCP 服务器响应：“我可以提供 192.168.1.42，有效期 24 小时。”
3. REQUEST   — 你的设备说：“我要 192.168.1.42。”
4. ACK       — 服务器确认：“它是你的了。这是你的完整设置。”
```

DHCP 不只是分配一个 IP——它会给你的设备下发完整的网络配置：

| 设置 | 示例 | 用途 |
|---------|---------|---------|
| IP 地址 | `192.168.1.42` | 你的设备在此网络上的地址 |
| 子网掩码 | `255.255.255.0` | 哪些地址位于同一子网 |
| 默认网关 | `192.168.1.1` | 发往子网外流量的目的地 |
| DNS 服务器 | `8.8.8.8` | 解析域名时向谁查询 |
| 租约时间 | `86400` 秒 | IP 归你使用多久后需要续约 |

**租约：** DHCP 租约是临时的。你的设备在设定时长内获得一个 IP，并且必须在到期前续约。这使服务器能够从那些不告而别的设备上回收地址。在大多数家庭网络中，租约时间是 24 小时。在繁忙环境（如会议 WiFi）中可能是 1 小时，以便地址快速轮换。

```bash
# See your current DHCP lease on Linux
ip addr show
# or
cat /var/lib/dhcp/dhclient.leases

# Release and renew your IP (Linux)
sudo dhclient -r eth0   # release
sudo dhclient eth0      # request a new one
```

**静态与动态：** DHCP 从地址池中动态分配地址。服务器和基础设施通常使用**静态 IP**——要么手动分配，要么通过 DHCP 保留（告诉 DHCP 服务器“始终给这个 MAC 地址分配这个特定 IP”）。这就是你的家用路由器如何知道始终给你的 NAS 分配相同地址的方式。

<!-- ZH_RESOURCES -->
- [什么是 DHCP？ - Cloudflare](https://www.cloudflare.com/learning/network-layer/what-is-dhcp/) -- 类型：文章，时长：10 分钟
- [DHCP 详解 - PowerCert](https://www.youtube.com/watch?v=e6-TaH5bkjo) -- 类型：视频，时长：10 分钟

<!-- ZH_UI -->
1. 用通俗的语言解释 DHCP DORA 过程
2. 识别 DHCP 除 IP 地址外还分配哪些信息
3. 理解什么是 DHCP 租约以及租约为何会过期
