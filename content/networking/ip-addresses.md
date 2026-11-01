---
id: ip-addresses
title: IP Addresses
zone: networking
edges:
  to:
    - id: subnets-and-cidr
      question: >-
        Every device has an IP address. But how are those addresses organized
        into groups?
      detail: >-
        I understand what my IP address is. But the numbers don't seem random —
        my home devices are all 192.168.1.something. I'm wondering how those
        address blocks are organized and what the structure actually means.
    - id: dhcp
      question: >-
        Every device needs an IP. But how does your device actually get one
        assigned to it?
      detail: >-
        When I connected to WiFi this morning I didn't type any IP — my device
        just got one automatically. How does that work? And what happens when
        something goes wrong with that process?
difficulty: 1
tags:
  - ip
  - ipv4
  - ipv6
  - addressing
  - network
category: concept
milestones:
  - Find your own IP address using a terminal command
  - Explain what each of the four octets in an IPv4 address represents
  - Describe why every networked device needs an IP address
title_zh: "IP 地址"

---


Every device on a network needs an address — a number other devices use to find it. Your laptop has one, your phone has one, Google's servers have one. When your laptop sends a request to `google.com`, the response needs to come back somewhere. That somewhere is your laptop's **IP address**. Without it, packets would have nowhere to go.

<!-- DEEP_DIVE -->

An **IPv4 address** is a 32-bit number written as four groups of digits separated by dots: `192.168.1.42`. Each group is called an **octet** — 8 bits, so each ranges from 0 to 255. Four octets, 32 bits total — giving you 2³² possible addresses, about 4.3 billion.

```bash
# Find your IP address on Linux
ip addr show
# Look for lines starting with "inet" — that's your IP
# Example: inet 192.168.1.42/24 brd 192.168.1.255 scope global eth0

# On macOS
ifconfig en0
# Look for the "inet" line
# Example: inet 192.168.1.42 netmask 0xffffff00 broadcast 192.168.1.255
```

A few special addresses worth knowing:

| Address | What it means |
|---------|--------------|
| `127.0.0.1` | **Loopback** — "this machine itself". `localhost` points here. |
| `0.0.0.0` | "Any interface" — used when configuring a server to listen on all network interfaces |
| `255.255.255.255` | **Broadcast** — sends to all devices on the local network |

**A device can have multiple IP addresses.** Your laptop might have:

```
en0 (WiFi):     192.168.1.42   ← your home network
lo0 (loopback): 127.0.0.1      ← always present, "this machine"
utun0 (VPN):    10.0.0.5       ← when connected to a VPN
```

Each network interface gets its own IP. This becomes important when you configure servers — binding to `0.0.0.0` means "accept traffic on any interface", while binding to `127.0.0.1` means "only accept local connections".

**Why 4.3 billion ran out:** In the 1980s, that seemed like plenty. Today there are around 20 billion internet-connected devices. The practical fix — which you'll learn about soon — is that most devices share a small pool of addresses using a trick called NAT, so the same addresses get reused in millions of private networks simultaneously.

**IPv6** is the long-term solution. It uses 128 bits instead of 32, written in hexadecimal: `2001:0db8:85a3::8a2e:0370:7334`. That is 2¹²⁸ addresses — more than enough for every grain of sand on Earth to have millions of its own. IPv6 adoption is growing but IPv4 still runs the majority of the internet today.

**The key thing to take away:** An IP address is just a number. It identifies a network interface, not a physical device. Your phone gets a new IP address every time it connects to a different WiFi network. Your web server has a fixed IP so people can always find it. IP addresses are not permanent — they are assigned as needed.

<!-- RESOURCES -->

- [Cloudflare - What is an IP address?](https://www.cloudflare.com/learning/dns/glossary/what-is-my-ip-address/) -- type: article, time: 5m
- [Khan Academy - IP Addresses](https://www.khanacademy.org/computing/computers-and-internet/xcae6f4a7ff015e7d:the-internet/xcae6f4a7ff015e7d:web-protocols/a/ip-addresses-and-dns) -- type: interactive, time: 10m
- [Julia Evans - Networking Zine](https://wizardzines.com/zines/networking/) -- type: zine, time: 15m

<!-- ZH_SUMMARY -->
网络上的每台设备都需要一个地址——一个其他设备用来找到它的数字。你的笔记本电脑有一个，你的手机有一个，Google 的服务器也有一个。当你的笔记本电脑向 `google.com` 发送请求时，响应需要回到某个地方。那个地方就是你的笔记本电脑的 **IP 地址**。没有它，数据包将无处可去。

<!-- ZH_DEEP_DIVE -->
**IPv4 地址**是一个 32 位数字，写成四组用点分隔的数字：`192.168.1.42`。每组称为一个**八位组**（octet）——8 位，因此每组范围是 0 到 255。四个八位组，总共 32 位——给你 2³² 个可能的地址，大约 43 亿个。

```bash
# Find your IP address on Linux
ip addr show
# Look for lines starting with "inet" — that's your IP
# Example: inet 192.168.1.42/24 brd 192.168.1.255 scope global eth0

# On macOS
ifconfig en0
# Look for the "inet" line
# Example: inet 192.168.1.42 netmask 0xffffff00 broadcast 192.168.1.255
```

几个值得了解的特殊地址：

| 地址 | 含义 |
|---------|--------------|
| `127.0.0.1` | **回环**（Loopback）——"本机自身"。`localhost` 指向这里。 |
| `0.0.0.0` | "任意接口"——用于配置服务器监听所有网络接口 |
| `255.255.255.255` | **广播**（Broadcast）——发送到本地网络上的所有设备 |

**一个设备可以有多个 IP 地址。** 你的笔记本电脑可能有：

```
en0 (WiFi):     192.168.1.42   ← your home network
lo0 (loopback): 127.0.0.1      ← always present, "this machine"
utun0 (VPN):    10.0.0.5       ← when connected to a VPN
```

每个网络接口都有自己的 IP。这在配置服务器时很重要——绑定到 `0.0.0.0` 意味着"接受任意接口上的流量"，而绑定到 `127.0.0.1` 意味着"只接受本地连接"。

**为什么 43 亿会用完：** 在 1980 年代，这看起来绰绰有余。如今大约有 200 亿台联网设备。实际的解决办法——你很快就会学到——是大多数设备通过一种叫 NAT 的技巧共享一小池地址，因此同样的地址会在数百万个私有网络中同时被复用。

**IPv6** 是长期的解决方案。它使用 128 位而不是 32 位，用十六进制书写：`2001:0db8:85a3::8a2e:0370:7334`。那是 2¹²⁸ 个地址——足以让地球上的每一粒沙子都拥有数百万个自己的地址。IPv6 的采用率在增长，但 IPv4 今天仍然承载着互联网的大部分流量。

**要记住的关键点：** IP 地址只是一个数字。它标识的是一个网络接口，而不是一台物理设备。你的手机每次连接到不同的 WiFi 网络时都会获得一个新的 IP 地址。你的 Web 服务器有一个固定的 IP，这样人们总能找到它。IP 地址不是永久的——它们按需分配。

<!-- ZH_RESOURCES -->
- [Cloudflare - 什么是 IP 地址？](https://www.cloudflare.com/learning/dns/glossary/what-is-my-ip-address/) -- 类型：文章，时间：5 分钟
- [Khan Academy - IP 地址](https://www.khanacademy.org/computing/computers-and-internet/xcae6f4a7ff015e7d:the-internet/xcae6f4a7ff015e7d:web-protocols/a/ip-addresses-and-dns) -- 类型：互动，时间：10 分钟
- [Julia Evans - 网络小志](https://wizardzines.com/zines/networking/) -- 类型：小志，时间：15 分钟

<!-- ZH_UI -->
1. 使用终端命令查找你自己的 IP 地址
2. 解释 IPv4 地址中四个八位组各自代表什么
3. 描述为什么每台联网设备都需要一个 IP 地址
4. 每台设备都有一个 IP 地址。但这些地址是如何分组组织的？
5. 我知道我的 IP 地址是什么。但这些数字似乎不是随机的——我家的设备都是 192.168.1.something。我想知道这些地址块是如何组织的，以及这种结构实际意味着什么。
6. 每台设备都需要一个 IP。但你的设备实际上是如何被分配到一个 IP 的？
7. 今天早上连接 WiFi 时我没有输入任何 IP——我的设备就自动获得了一个。这是怎么工作的？如果这个过程出问题会发生什么？
