---
id: network-protocols
title: What Are Protocols?
zone: networking
edges:
  to:
    - id: tcp-udp-basics
      question: >-
        I get why protocols exist. Now what are the actual protocols that move
        data around?
      detail: >-
        I get that protocols are rules computers agree to follow. But what are
        the actual rules that move data between my machine and a server? There
        must be specific protocols doing the heavy lifting — what are they and
        what does each one do?
    - id: ip-addresses
      question: >-
        Protocols have layers, and one layer handles addressing. How do IP
        addresses actually work?
      detail: >-
        I understand that networking has layers and each layer has a job. The
        network layer handles addressing — but what does that actually mean in
        practice? Every device must have some kind of address for packets to
        find it. What are those addresses and how do they actually work?
difficulty: 1
tags:
  - protocols
  - networking
  - layers
  - osi
  - tcp-ip
  - communication
category: concept
milestones:
  - Explain what a protocol is and why networked computers need them
  - Describe the purpose of different networking layers
  - 'Identify which layer common protocols belong to (HTTP, TCP, IP, Ethernet)'
title_zh: "什么是协议？"

---


Two computers are connected. You can ping one from the other. But ping just says "yes, I can reach you." How do you actually send meaningful data? If your laptop sends a stream of bytes to your phone, how does the phone know if it is a web page, an email, a video, or garbage? The answer: both sides agree on rules ahead of time. Those rules are **protocols**.

<!-- DEEP_DIVE -->

A **protocol** is just an agreement about how to communicate. Humans do this too. When you call someone on the phone, there is an unspoken protocol: one person says hello, the other responds, they take turns talking, and one of them eventually says goodbye. If one person just started shouting random words without waiting for a response, communication would break down. Computers are the same — they need structure.

**Why not just one protocol?** Because communication has different problems at different levels. Consider sending a letter:

1. You **write the letter** in English (the language you both understand)
2. You **put it in an envelope** with the recipient's address
3. The **postal service** figures out which trucks and planes to use
4. The **truck driver** follows roads to physically move it

Each step has its own rules. The language rules do not care about which truck carries the letter. The truck driver does not need to read English. Each layer does one job and trusts the others to do theirs.

Networking works the same way, organized into **layers**:

```
┌─────────────────────────────────────────────┐
│  Application Layer (HTTP, DNS, SMTP, SSH)   │ ← What the data means
├─────────────────────────────────────────────┤
│  Transport Layer (TCP, UDP)                 │ ← Reliable or fast delivery
├─────────────────────────────────────────────┤
│  Network Layer (IP)                         │ ← Addressing and routing
├─────────────────────────────────────────────┤
│  Link Layer (Ethernet, WiFi)                │ ← Physical transmission
└─────────────────────────────────────────────┘
```

When you load a web page, here is what happens at each layer:

1. **Your browser** creates an HTTP request — "GET me the page at /products" (Application)
2. **TCP** wraps that request in a segment, adds sequence numbers for reliability (Transport)
3. **IP** wraps the segment in a packet, adds source and destination IP addresses (Network)
4. **Ethernet/WiFi** wraps the packet in a frame, adds MAC addresses, sends it as electrical signals or radio waves (Link)

On the other end, the process reverses — each layer peels off its wrapper and passes the contents up to the next layer, until the web server gets the original HTTP request.

Think of it as an **envelope inside an envelope inside an envelope**:

```
┌─────────────────────────────────────────────┐
│ Ethernet Frame                              │
│  ┌──────────────────────────────────────┐   │
│  │ IP Packet                            │   │
│  │  ┌───────────────────────────────┐   │   │
│  │  │ TCP Segment                   │   │   │
│  │  │  ┌────────────────────────┐   │   │   │
│  │  │  │ HTTP Request           │   │   │   │
│  │  │  │ "GET /products"        │   │   │   │
│  │  │  └────────────────────────┘   │   │   │
│  │  └───────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**This layering is why the internet works.** HTTP does not care whether you are on WiFi or Ethernet. TCP does not care whether you are loading a web page or sending an email. IP does not care what the data is — it just routes packets to the right address. Each protocol does one job well and does not worry about the rest.

You have already seen some of these protocols without realizing it:

- When you typed `http://192.168.1.42:5000` in your phone's browser — that is **HTTP** (application layer) over **TCP** (transport) over **IP** (network) over **WiFi** (link)
- When you used `ping` — that uses **ICMP** (a network layer protocol), which rides directly on **IP**
- Your router assigning IP addresses — that is **DHCP**, an application layer protocol
- Your devices finding each other's hardware addresses — that is **ARP**, a link layer protocol

**The key takeaway:** You do not need to memorize the layers or know every protocol. What matters is the concept: networking is built in layers, each layer solves one problem, and protocols are just the rules for each layer. Once you understand this, every new protocol you encounter — TCP, UDP, HTTP, DNS, TLS — slots into place naturally.

The next step is to learn the specific protocols that matter most. At the transport layer, there are really only two: **TCP** (reliable, careful, connection-oriented) and **UDP** (fast, fire-and-forget). Everything on the internet uses one of them, and understanding the difference is fundamental.

<!-- RESOURCES -->

- [Khan Academy - Internet Protocols](https://www.khanacademy.org/computing/computers-and-internet/xcae6f4a7ff015e7d:the-internet/xcae6f4a7ff015e7d:the-internet-protocol-suite/a/the-internet-protocols) -- type: interactive, time: 15m
- [How Does the Internet Work? (Stanford)](https://web.stanford.edu/class/msande91si/www-spr04/readings/week1/InternetWhitepaper.htm) -- type: article, time: 30m
- [Cloudflare - What is a network protocol?](https://www.cloudflare.com/learning/network-layer/what-is-a-network-protocol/) -- type: article, time: 10m
- [Julia Evans - Networking Zine](https://wizardzines.com/zines/networking/) -- type: zine, time: 15m

<!-- ZH_SUMMARY -->
两台计算机已连接。你可以从一台 ping 通另一台。但 ping 只说明“是的，我能到达你”。你实际上如何发送有意义的数据？如果你的笔记本电脑向手机发送一串字节流，手机如何知道它是网页、电子邮件、视频，还是垃圾数据？答案：双方事先就规则达成一致。这些规则就是**协议**。

<!-- ZH_DEEP_DIVE -->
**协议**不过是一种关于如何通信的约定。人类也是如此。当你打电话给某人时，存在一种不成文的协议：一个人说你好，另一个人回应，他们轮流说话，最终其中一人说再见。如果一个人不等回应就开始大喊随机词语，沟通就会崩溃。计算机也一样——它们需要结构。

**为什么不能只用一种协议？** 因为通信在不同层次上有不同的问题。考虑寄一封信：

1. 你用英语**写信**（你们都能理解的语言）
2. 你把信**装进信封**，写上收件人地址
3. **邮政服务**决定使用哪些卡车和飞机
4. **卡车司机**沿着道路实际运送它

每一步都有自己的规则。语言规则不关心哪辆卡车运送信件。卡车司机不需要读英语。每一层只做一件事，并信任其他层做好它们的事。

网络的工作原理相同，被组织成**层**：

```
┌─────────────────────────────────────────────┐
│  应用层 (HTTP, DNS, SMTP, SSH)              │ ← 数据的含义
├─────────────────────────────────────────────┤
│  传输层 (TCP, UDP)                          │ ← 可靠或快速交付
├─────────────────────────────────────────────┤
│  网络层 (IP)                                │ ← 寻址和路由
├─────────────────────────────────────────────┤
│  链路层 (Ethernet, WiFi)                    │ ← 物理传输
└─────────────────────────────────────────────┘
```

当你加载一个网页时，每一层会发生以下事情：

1. **你的浏览器**创建一个 HTTP 请求——"GET 给我 /products 页面"（应用层）
2. **TCP** 将该请求包装成一个段，添加序列号以保证可靠性（传输层）
3. **IP** 将该段包装成一个包，添加源 IP 地址和目的 IP 地址（网络层）
4. **Ethernet/WiFi** 将该包包装成一个帧，添加 MAC 地址，以电信号或无线电波的形式发送（链路层）

在另一端，过程相反——每一层剥掉自己的包装，将内容向上传递给下一层，直到 Web 服务器收到原始的 HTTP 请求。

可以把它想象成**信封套信封再套信封**：

```
┌─────────────────────────────────────────────┐
│ Ethernet 帧                                 │
│  ┌──────────────────────────────────────┐   │
│  │ IP 包                                │   │
│  │  ┌───────────────────────────────┐   │   │
│  │  │ TCP 段                        │   │   │
│  │  │  ┌────────────────────────┐   │   │   │
│  │  │  │ HTTP 请求              │   │   │   │
│  │  │  │ "GET /products"        │   │   │   │
│  │  │  └────────────────────────┘   │   │   │
│  │  └───────────────────────────────┘   │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**这种分层正是互联网运作的原因。** HTTP 不关心你是在 WiFi 还是 Ethernet 上。TCP 不关心你是在加载网页还是发送电子邮件。IP 不关心数据是什么——它只是将包路由到正确的地址。每个协议做好一件事，不操心其余的事。

你其实已经见过其中一些协议，只是没有意识到：

- 当你在手机浏览器中输入 `http://192.168.1.42:5000` 时——那是 **HTTP**（应用层）运行在 **TCP**（传输层）之上，再运行在 **IP**（网络层）之上，再运行在 **WiFi**（链路层）之上
- 当你使用 `ping` 时——那使用的是 **ICMP**（一种网络层协议），它直接运行在 **IP** 之上
- 你的路由器分配 IP 地址——那是 **DHCP**，一种应用层协议
- 你的设备互相发现硬件地址——那是 **ARP**，一种链路层协议

**关键要点：** 你不需要记住这些层或了解每一个协议。重要的是这个概念：网络是分层构建的，每一层解决一个问题，协议只是每一层的规则。一旦你理解了这一点，你遇到的每一个新协议——TCP、UDP、HTTP、DNS、TLS——都会自然地各就各位。

下一步是学习最重要的具体协议。在传输层，实际上只有两个：**TCP**（可靠、谨慎、面向连接）和 **UDP**（快速、发后不管）。互联网上的一切都使用其中之一，理解它们的区别是基础。

<!-- ZH_RESOURCES -->
- [Khan Academy - 互联网协议](https://www.khanacademy.org/computing/computers-and-internet/xcae6f4a7ff015e7d:the-internet/xcae6f4a7ff015e7d:the-internet-protocol-suite/a/the-internet-protocols) -- 类型：互动式，时长：15 分钟
- [互联网是如何运作的？（斯坦福）](https://web.stanford.edu/class/msande91si/www-spr04/readings/week1/InternetWhitepaper.htm) -- 类型：文章，时长：30 分钟
- [Cloudflare - 什么是网络协议？](https://www.cloudflare.com/learning/network-layer/what-is-a-network-protocol/) -- 类型：文章，时长：10 分钟
- [Julia Evans - 网络小志](https://wizardzines.com/zines/networking/) -- 类型：小志，时长：15 分钟

<!-- ZH_UI -->
1. 解释什么是协议，以及为什么联网计算机需要协议
2. 描述不同网络分层的作用
3. 识别常见协议属于哪一层（HTTP、TCP、IP、Ethernet）
4. 我明白协议为什么存在。那么实际负责传输数据的协议有哪些？
5. 我明白协议是计算机约定遵循的规则。但在我机器和服务器之间传输数据的具体规则是什么？肯定有特定协议在承担主要工作——它们是什么，各自做什么？
6. 协议是分层的，其中一层负责寻址。IP 地址实际上是如何工作的？
7. 我理解网络是分层的，每一层都有各自的职责。网络层负责寻址——但这在实践中到底意味着什么？每个设备都必须有某种地址，数据包才能找到它。这些地址是什么，它们实际上如何工作？
