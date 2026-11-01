---
id: local-network
title: Connecting Two Computers
zone: networking
edges:
  to:
    - id: network-protocols
      question: >-
        My computers are connected. But how do they actually understand each
        other?
      detail: >-
        My laptop and phone can ping each other. But when I think about what's
        actually happening when they communicate — not the wires, but the actual
        data exchange — I realize I don't understand how they agree on what the
        bytes mean. How do computers speak the same language?
    - id: dhcp
      question: >-
        You connected to WiFi and got an IP address automatically. How does that
        work?
      detail: >-
        I connected to WiFi and my device just had an IP address. I never typed
        anything in. Something must have noticed I joined and handed me an
        address — but what? And what happens when that breaks and my device
        can't get an IP?
difficulty: 1
tags:
  - networking
  - lan
  - wifi
  - router
  - local-network
  - ethernet
category: concept
milestones:
  - Understand how devices physically connect via Ethernet and WiFi
  - Find your machine's local IP address and your router's IP
  - Ping another device on your local network
title_zh: "连接两台计算机"

---


Before the internet, before web servers, before any of that — there is a simpler question: **how do you connect two computers?** Take your laptop and your phone. They are both sitting in the same room, connected to the same WiFi. How are they actually connected, and what does that connection even look like?

<!-- DEEP_DIVE -->

At the most basic level, connecting two computers requires a physical medium — something for data to travel through. There are two ways:

**Wired (Ethernet):** You plug a cable into both machines. Literally. An Ethernet cable carries electrical signals between two network cards. This is how servers in data centers are connected, how your desktop connects to your router, and how the backbone of most networks works. It is simple, fast, and reliable.

**Wireless (WiFi):** Instead of a cable, your device uses radio waves to communicate with a WiFi access point (usually built into your router). The data is the same — just transmitted through the air instead of through copper. Convenient, but slower and less reliable than a cable.

Either way, the result is the same: your device can send bits to another device.

**Your home network** is called a **LAN (Local Area Network)** — a small group of devices connected together. Your router is the hub of this network. It does two things: it lets your local devices talk to each other, and it connects your entire network to the internet.

When your laptop connects to WiFi, the router gives it an **IP address** — a number that identifies your device on the network. Your laptop might be `192.168.1.42`, your phone `192.168.1.43`, and the router itself is usually `192.168.1.1`:

```bash
# Find your local IP address
# macOS
ipconfig getifaddr en0

# Linux
ip addr show | grep "inet 192"

# Windows
ipconfig
```

You can check if another device is reachable with **ping** — one of the simplest networking tools. It sends a tiny message and waits for a reply:

```bash
# Ping your router
ping 192.168.1.1

# Ping your phone (if you know its IP)
ping 192.168.1.43

# You should see responses like:
# 64 bytes from 192.168.1.1: icmp_seq=0 ttl=64 time=2.3 ms
```

If you get a response, the two machines can reach each other. They are connected.

**The practical test:** Your Flask app is running on `localhost:5000`. Change it to listen on `0.0.0.0:5000`, grab your phone (on the same WiFi), and visit `http://192.168.1.42:5000`. Your phone loads the page. Two devices, communicating over a network.

```python
# Listen on all network interfaces, not just localhost
app.run(host="0.0.0.0", port=5000)
```

**But here is the thing.** Your phone loaded the page — great. But how? What actually happened between "your phone sent a request" and "the page appeared"? Your phone sent some bytes over WiFi, and your laptop received them and sent some bytes back. But how did both sides know what those bytes meant? How did they agree on the format, the order, the rules?

That is where protocols come in. The physical connection is step one — but without agreed-upon rules for communication, two connected computers are just two machines shouting into the void.

**Switches** are worth mentioning because they are the physical infrastructure of wired networks. A switch connects multiple devices via Ethernet cables. When your laptop sends data to another device, the switch figures out which port that device is on and sends the data only there — not to every device. In a data center, switches connect hundreds of servers. At home, your router has a small switch built in (those Ethernet ports on the back).

<!-- RESOURCES -->

- [Cloudflare - What is a LAN?](https://www.cloudflare.com/learning/network-layer/what-is-a-lan/) -- type: article, time: 10m
- [Wireless Internet - Explain That Stuff](https://www.explainthatstuff.com/wirelessinternet.html) -- type: article, time: 15m
- [Practical Networking - Networking Fundamentals](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) -- type: series, time: 1h
- [Cloudflare - What is Ethernet?](https://www.cloudflare.com/learning/network-layer/what-is-ethernet/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
在互联网之前，在 Web 服务器之前，在这一切之前——有一个更简单的问题：**你如何连接两台计算机？** 拿你的笔记本电脑和手机来说。它们都坐在同一个房间里，连接着同一个 WiFi。它们实际上是如何连接的，而这种连接又是什么样子的？

<!-- ZH_DEEP_DIVE -->
在最基础的层面上，连接两台计算机需要一个物理介质——让数据能够传输的通道。有两种方式：

**有线（以太网）：** 你把一根网线插到两台机器上。字面意义上的插。以太网线在两张网卡之间传输电信号。数据中心里的服务器就是这样连接的，你的台式机连接路由器也是这样，大多数网络的骨干也是这样工作的。它简单、快速、可靠。

**无线（WiFi）：** 不用网线，你的设备使用无线电波与 WiFi 接入点（通常内置在你的路由器中）通信。数据是一样的——只是通过空气传输而不是通过铜线。方便，但比有线慢，也不如有线可靠。

无论哪种方式，结果都一样：你的设备可以向另一台设备发送比特。

**你的家庭网络**被称为 **LAN（局域网）**——一小群连接在一起的设备。你的路由器是这个网络的枢纽。它做两件事：让你的本地设备互相通信，以及把你的整个网络连接到互联网。

当你的笔记本电脑连接 WiFi 时，路由器会给它分配一个 **IP 地址**——一个在网络中标识你设备的数字。你的笔记本电脑可能是 `192.168.1.42`，你的手机是 `192.168.1.43`，而路由器本身通常是 `192.168.1.1`：

```bash
# Find your local IP address
# macOS
ipconfig getifaddr en0

# Linux
ip addr show | grep "inet 192"

# Windows
ipconfig
```

你可以用 **ping** 检查另一台设备是否可达——这是最简单的网络工具之一。它发送一条很小的消息并等待回复：

```bash
# Ping your router
ping 192.168.1.1

# Ping your phone (if you know its IP)
ping 192.168.1.43

# You should see responses like:
# 64 bytes from 192.168.1.1: icmp_seq=0 ttl=64 time=2.3 ms
```

如果你收到回复，说明两台机器可以互相到达。它们是连通的。

**实际测试：** 你的 Flask 应用运行在 `localhost:5000` 上。把它改成监听 `0.0.0.0:5000`，拿起你的手机（连接同一个 WiFi），访问 `http://192.168.1.42:5000`。你的手机加载了页面。两台设备，通过网络通信。

```python
# Listen on all network interfaces, not just localhost
app.run(host="0.0.0.0", port=5000)
```

**但问题在这里。** 你的手机加载了页面——很好。但它是怎么做到的？从“你的手机发送了一个请求”到“页面出现”之间，到底发生了什么？你的手机通过 WiFi 发送了一些字节，你的笔记本电脑收到了它们并回发了一些字节。但双方怎么知道这些字节是什么意思？它们如何就格式、顺序、规则达成一致？

这就是协议发挥作用的地方。物理连接是第一步——但如果没有约定好的通信规则，两台连通的计算机就只是两台对着虚空喊话的机器。

**交换机**值得一提，因为它们是有线网络的物理基础设施。交换机通过以太网线连接多台设备。当你的笔记本电脑向另一台设备发送数据时，交换机会判断那台设备在哪个端口上，并只把数据发送到那里——而不是发给每台设备。在数据中心，交换机连接数百台服务器。在家里，你的路由器内置了一个小型交换机（背面那些以太网端口）。

<!-- ZH_RESOURCES -->
- [Cloudflare - 什么是 LAN？](https://www.cloudflare.com/learning/network-layer/what-is-a-lan/) -- 类型: 文章, 时间: 10m
- [Wireless Internet - Explain That Stuff](https://www.explainthatstuff.com/wirelessinternet.html) -- 类型: 文章, 时间: 15m
- [Practical Networking - 网络基础](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) -- 类型: 系列, 时间: 1h
- [Cloudflare - 什么是以太网？](https://www.cloudflare.com/learning/network-layer/what-is-ethernet/) -- 类型: 文章, 时间: 10m

<!-- ZH_UI -->
1. 理解设备如何通过以太网和 WiFi 进行物理连接
2. 找到你机器的本地 IP 地址和路由器的 IP
3. 在本地网络中 ping 另一台设备
4. 我的计算机已经连接了。但它们实际上是如何相互理解的？
5. 我的笔记本电脑和手机可以互相 ping 通。但当我思考它们通信时实际发生了什么——不是网线，而是真正的数据交换——我意识到我不理解它们如何就字节的含义达成一致。计算机是如何说同一种语言的？
6. 你连接了 WiFi 并自动获得了一个 IP 地址。这是如何工作的？
7. 我连接了 WiFi，我的设备就有了一个 IP 地址。我从未输入任何内容。一定有某个东西注意到我加入了并给了我一个地址——但那是什么？当它出故障、我的设备无法获得 IP 时会发生什么？
