---
id: tcp-udp-basics
title: 'TCP, UDP & How Data Travels'
zone: networking
edges:
  to:
    - id: http-protocol
      question: >-
        I understand TCP and ports. But what is my browser actually saying to
        the server?
      detail: >-
        TCP gets bytes from A to B reliably — I get that. But what are the
        actual bytes my browser sends when I load a webpage? It can't just be a
        raw stream of random data. The server must understand exactly what's
        being asked for. What language are they actually speaking to each other?
difficulty: 1
tags:
  - tcp
  - udp
  - networking
  - ports
  - ip-addresses
  - protocols
category: concept
milestones:
  - Explain the difference between TCP and UDP
  - Use netcat to send data between two machines
  - Identify what port a service is listening on using ss or lsof
title_zh: "TCP、UDP 与数据传输原理"

---


Your app works on localhost, but when you try to share it, nothing happens. To understand why, you need to understand how data actually moves between computers. Every time you load a webpage, send a message, or make an API call, data is being broken into packets and routed across networks using protocols — primarily TCP and UDP. These are the fundamental building blocks of all network communication.

<!-- DEEP_DIVE -->

**IP addresses** identify machines on a network. Think of them as street addresses — if you want to send a letter, you need to know where it is going. IPv4 addresses look like `192.168.1.42` (four numbers, 0-255 each). Every device on a network has one. Your home network uses private IPs (192.168.x.x, 10.x.x.x), while servers on the internet have public IPs that anyone can route to.

**Ports** identify specific services on a machine. If the IP address is the street address, the port is the apartment number. A single machine can run dozens of services — a web server on port 80, your Flask app on port 5000, a database on port 5432, SSH on port 22. When you type `http://localhost:5000`, you are telling your browser to connect to your own machine (localhost), specifically to whatever is listening on port 5000.

**TCP** (Transmission Control Protocol) is the reliable protocol. When your browser loads a webpage, it uses TCP. Here is what happens:

1. **Three-way handshake** — Your computer sends a SYN (synchronize) packet, the server responds with SYN-ACK, your computer sends ACK. Connection established. This takes milliseconds but it happens every time.
2. **Data transfer** — Your HTTP request is broken into segments, each one numbered. The server acknowledges each segment it receives.
3. **Reliability** — If a segment is lost, TCP detects it (no acknowledgment arrived) and retransmits. It guarantees that data arrives complete and in order.
4. **Connection teardown** — When done, both sides exchange FIN packets to close cleanly.

TCP is used for HTTP/HTTPS, SSH, email, database connections — anything where you cannot afford to lose data. If a packet containing part of your checkout form gets lost, TCP makes sure it gets retransmitted.

**UDP** (User Datagram Protocol) is the fast protocol. It does not do handshakes, does not guarantee delivery, does not ensure ordering. You just fire packets and hope they arrive. Why would anyone want this? Speed. UDP has less overhead, lower latency, and is perfect for cases where a few lost packets do not matter — video streaming, online gaming, DNS queries, voice calls. If one frame of a video call is lost, you do not want to pause and retransmit — you just skip it and move on.

You can see TCP in action with **netcat** (`nc`), a simple networking tool:

```bash
# Terminal 1 - start a listener on port 9000
nc -l 9000

# Terminal 2 - connect to it
nc localhost 9000
```

Type in Terminal 2, and the text appears in Terminal 1. You just sent data over TCP. This is exactly what your web app does, just with more structure (HTTP) on top.

To see what ports are in use on your machine:

```bash
# Show all listening ports
ss -tlnp

# Or on macOS
lsof -iTCP -sTCP:LISTEN -n -P
```

You will see your Flask app on port 5000, maybe a database on 5432, SSH on 22. Each one is a service waiting for TCP connections.

**The key insight**: when your app listens on `localhost:5000`, it is listening for TCP connections on port 5000, but only from the loopback interface (your own machine). When you change to `0.0.0.0:5000`, it listens on all interfaces, including your network card — so other machines that can reach your IP can connect. But getting traffic from the internet to your machine requires more: routing, possibly port forwarding, and typically a web server sitting in front of your app.

<!-- RESOURCES -->

- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/) -- type: book, time: varies
- [TCP/IP Illustrated - Kevin Fall & W. Richard Stevens](https://www.oreilly.com/library/view/tcpip-illustrated-volume/9780132808200/) -- type: book, time: varies
- [Cloudflare - What is TCP?](https://www.cloudflare.com/learning/ddos/glossary/tcp-ip/) -- type: article, time: 10m
- [Julia Evans - Networking Zine](https://jvns.ca/blog/2019/06/23/a-few-things-about-computer-networking/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
你的应用在 localhost 上运行正常，但当你尝试分享它时，却没有任何反应。要理解其中的原因，你需要了解数据实际上是如何在计算机之间传输的。每次你加载网页、发送消息或发起 API 调用时，数据都会被拆分成数据包，并通过协议在网络中路由——主要是 TCP 和 UDP。这些是所有网络通信的基本构建块。

<!-- ZH_DEEP_DIVE -->
**IP 地址**用于标识网络上的机器。可以把它们想象成街道地址——如果你想寄信，就需要知道寄往哪里。IPv4 地址看起来像 `192.168.1.42`（四个数字，每个在 0-255 之间）。网络上的每台设备都有一个 IP 地址。你的家庭网络使用私有 IP（192.168.x.x、10.x.x.x），而互联网上的服务器拥有任何人都能路由到的公网 IP。

**端口**用于标识机器上的特定服务。如果 IP 地址是街道地址，那么端口就是公寓门牌号。一台机器可以运行数十个服务——端口 80 上的 Web 服务器、端口 5000 上的 Flask 应用、端口 5432 上的数据库、端口 22 上的 SSH。当你输入 `http://localhost:5000` 时，你是在告诉浏览器连接到你自己的机器（localhost），具体来说，是连接到监听端口 5000 的那个服务。

**TCP**（传输控制协议）是可靠协议。当你的浏览器加载网页时，它使用的就是 TCP。下面是发生的过程：

1. **三次握手** —— 你的计算机发送一个 SYN（同步）包，服务器以 SYN-ACK 响应，你的计算机再发送 ACK。连接建立。这只需几毫秒，但每次都会发生。
2. **数据传输** —— 你的 HTTP 请求被拆分成多个段，每个段都有编号。服务器会确认它收到的每个段。
3. **可靠性** —— 如果某个段丢失，TCP 会检测到（没有收到确认）并重传。它保证数据完整且按序到达。
4. **连接拆除** —— 完成后，双方交换 FIN 包以干净地关闭连接。

TCP 用于 HTTP/HTTPS、SSH、电子邮件、数据库连接——任何你无法承受数据丢失的场景。如果包含你结账表单一部分的包丢失了，TCP 会确保它被重传。

**UDP**（用户数据报协议）是快速协议。它不做握手，不保证送达，也不确保顺序。你只管把包发出去，然后希望它们能到达。为什么有人会想要这个？为了速度。UDP 开销更小、延迟更低，非常适合少数丢包无关紧要的场景——视频流、在线游戏、DNS 查询、语音通话。如果视频通话中的一帧丢失了，你不会希望暂停并重传——你只需跳过它继续。

你可以用 **netcat**（`nc`）这个简单的网络工具来观察 TCP 的实际运行：

```bash
# Terminal 1 - start a listener on port 9000
nc -l 9000

# Terminal 2 - connect to it
nc localhost 9000
```

在终端 2 中输入，文本就会出现在终端 1 中。你刚刚通过 TCP 发送了数据。这正是你的 Web 应用所做的事情，只不过在上面多了更多结构（HTTP）。

要查看你机器上正在使用的端口：

```bash
# Show all listening ports
ss -tlnp

# Or on macOS
lsof -iTCP -sTCP:LISTEN -n -P
```

你会看到你的 Flask 应用在端口 5000 上，可能还有端口 5432 上的数据库、端口 22 上的 SSH。每一个都是等待 TCP 连接的服务。

**关键洞察**：当你的应用监听 `localhost:5000` 时，它是在端口 5000 上监听 TCP 连接，但只接受来自回环接口（你自己的机器）的连接。当你改为 `0.0.0.0:5000` 时，它会在所有接口上监听，包括你的网卡——因此，能够访问到你 IP 的其他机器就可以连接。但要让流量从互联网到达你的机器，还需要更多东西：路由、可能的端口转发，以及通常位于你的应用前面的一个 Web 服务器。

<!-- ZH_RESOURCES -->
- [Beej 的网络编程指南](https://beej.us/guide/bgnet/) -- 类型：书籍，时长：不定
- [TCP/IP 详解 - Kevin Fall & W. Richard Stevens](https://www.oreilly.com/library/view/tcpip-illustrated-volume/9780132808200/) -- 类型：书籍，时长：不定
- [Cloudflare - 什么是 TCP？](https://www.cloudflare.com/learning/ddos/glossary/tcp-ip/) -- 类型：文章，时长：10 分钟
- [Julia Evans - 网络小志](https://jvns.ca/blog/2019/06/23/a-few-things-about-computer-networking/) -- 类型：文章，时长：15 分钟

<!-- ZH_UI -->
1. 解释 TCP 与 UDP 的区别
2. 使用 netcat 在两台机器之间发送数据
3. 使用 ss 或 lsof 识别服务正在监听的端口
4. 我理解 TCP 和端口。但我的浏览器实际上在对服务器说什么？
5. TCP 能可靠地把字节从 A 传到 B——这我明白。但当我加载网页时，浏览器实际发送的字节是什么？它不可能只是随机的原始数据流。服务器必须准确理解请求的内容。它们之间实际使用的是什么语言？
