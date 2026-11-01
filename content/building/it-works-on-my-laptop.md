---
id: it-works-on-my-laptop
title: It Works on My Laptop
zone: building
edges:
  to:
    - id: local-network
      zone: networking
      question: Why can't anyone else reach my app? What even is a network?
      detail: >-
        I bound to 0.0.0.0 and my phone can reach the app when we're on the same
        WiFi — but my friend across town still can't. I don't understand why.
        There must be something about how networks are structured that explains
        this, but I don't know what I'm missing.
    - id: where-do-i-run-this
      zone: running
      question: My app works locally. Where do I actually run this for real?
      detail: >-
        I can't run a production service from my laptop — it goes to sleep, I
        carry it around, the IP changes. I need something that's always on and
        always reachable. But I have no idea what that actually means or what my
        options are.
difficulty: 1
tags:
  - localhost
  - networking
  - deployment
  - ports
  - development-environment
category: concept
milestones:
  - Understand why localhost is only accessible from your own machine
  - Try to access your app from another device on the same network
  - Identify what you would need to make your app publicly accessible
title_zh: "在我的笔记本电脑上能运行"

---


You built an online store. It has products, users, a shopping cart, checkout — the works. You run `python app.py`, open `http://localhost:5000` in your browser, and everything works perfectly. Then you try to share it with a friend. You send them the URL. They cannot connect. You text them "just go to localhost:5000" and they tell you it does not work. Of course it does not — localhost means your machine, and your machine only.

<!-- DEEP_DIVE -->

**localhost** (or `127.0.0.1`) is a special address that always points to the computer you are currently on. When your Flask app listens on `localhost:5000`, it is only accepting connections from your own machine. It is like having a shop with the door locked from the inside — you can walk around inside, but nobody else can get in.

This is actually a good thing for development. You do not want random people on the internet hitting your half-finished app. But at some point, you need to open that door.

The first thing you might try is binding to `0.0.0.0` instead of `localhost`:

```python
app.run(host="0.0.0.0", port=5000)
```

This tells your app to listen on all network interfaces, not just the loopback. Now other devices on your local network (your phone on the same WiFi, another computer in your house) can reach your app by going to your computer's local IP address, something like `http://192.168.1.42:5000`.

But this still does not work for people outside your network. Your friend across town, a customer in another country — they cannot reach `192.168.1.42` because that is a **private IP address**. It only exists within your home network. The internet does not know how to route to it.

To understand why, you need to understand how networks actually work:

- **Your app** listens on a port (5000) on your machine
- **Your machine** has a private IP (192.168.1.42) on your home network
- **Your router** has a public IP (say, 73.42.100.15) assigned by your ISP
- **The internet** can only see your router's public IP, not your machine

For someone on the internet to reach your app, the request has to travel from their computer → through the internet → to your router's public IP → somehow get forwarded to your machine → and hit port 5000. Every step in that chain has requirements: DNS to translate a domain name to an IP, routing to move packets across networks, port forwarding or a public server to bridge the gap between the internet and your local machine.

This is the "it works on my laptop" wall. Almost every developer hits it. And solving it requires understanding networking — how data actually travels between computers, what TCP and ports really are, how web servers work, and how to expose an application to the world. It is a big topic, but it is the bridge between "I can build software" and "I can run software that people actually use."

The typical solutions, in order of complexity:

1. **Tunneling services** (ngrok, Cloudflare Tunnel) — punch a temporary hole from the internet to your laptop. Great for demos, terrible for production.
2. **Cloud VM** (AWS EC2, DigitalOcean Droplet) — rent a server with a public IP, deploy your app there. This is real deployment.
3. **Platform as a Service** (Heroku, Railway, Render) — push your code and they handle the server. Convenient but less educational.

Each of these requires networking knowledge to understand and debug. When something goes wrong — and it will — you need to know what a port is, how TCP works, what a reverse proxy does, and how DNS translates a name to an address.

<!-- RESOURCES -->

- [What is localhost? - MDN](https://developer.mozilla.org/en-US/docs/Glossary/Localhost) -- type: reference, time: 5m
- [Private vs Public IP Addresses](https://www.cloudflare.com/learning/network-layer/what-is-a-private-ip-address/) -- type: article, time: 10m
- [How the Internet Works - Stanford](https://web.stanford.edu/class/msande91si/www-spr04/readings/week1/InternetWhitepaper.htm) -- type: article, time: 30m
- [ngrok Documentation](https://ngrok.com/docs) -- type: tool, time: 15m

<!-- ZH_SUMMARY -->
你构建了一个在线商店。它有商品、用户、购物车、结账——一应俱全。你运行 `python app.py`，在浏览器中打开 `http://localhost:5000`，一切运行完美。然后你试着把它分享给朋友。你把 URL 发给他们。他们却连不上。你发消息说“直接访问 localhost:5000 就行”，他们告诉你不行。当然不行——localhost 指的是你的机器，而且只是你的机器。

<!-- ZH_DEEP_DIVE -->
**localhost**（或 `127.0.0.1`）是一个特殊地址，它始终指向你当前所在的计算机。当你的 Flask 应用监听 `localhost:5000` 时，它只接受来自你自己机器的连接。这就像一家从里面锁了门的商店——你可以在里面走动，但其他人进不来。

这对开发来说其实是件好事。你不希望互联网上的陌生人访问你半成品状态的应用。但到了某个时候，你需要打开那扇门。

你可能首先尝试的是绑定到 `0.0.0.0` 而不是 `localhost`：

```python
app.run(host="0.0.0.0", port=5000)
```

这会告诉你的应用监听所有网络接口，而不仅仅是回环接口。现在你本地网络上的其他设备（同一 WiFi 上的手机、你家里的另一台电脑）可以通过你电脑的本地 IP 地址访问你的应用，类似 `http://192.168.1.42:5000`。

但这仍然无法让网络外的人访问。你城市另一头的朋友、另一个国家的客户——他们无法访问 `192.168.1.42`，因为那是一个**私有 IP 地址**。它只存在于你的家庭网络内。互联网不知道如何路由到它。

要理解原因，你需要理解网络实际上是如何工作的：

- **你的应用**监听你机器上的一个端口（5000）
- **你的机器**在你的家庭网络上有一个私有 IP（192.168.1.42）
- **你的路由器**有一个由 ISP 分配的公网 IP（比如 73.42.100.15）
- **互联网**只能看到你路由器的公网 IP，看不到你的机器

要让互联网上的人访问你的应用，请求必须从他们的电脑 → 穿过互联网 → 到达你路由器的公网 IP → 以某种方式转发到你的机器 → 并命中端口 5000。这条链上的每一步都有要求：DNS 将域名转换为 IP，路由将数据包跨网络移动，端口转发或公网服务器来弥合互联网与你本地机器之间的鸿沟。

这就是“在我笔记本上能跑”的墙。几乎每个开发者都会撞上它。而解决它需要理解网络——数据实际上如何在计算机之间传输、TCP 和端口到底是什么、Web 服务器如何工作，以及如何将应用暴露给世界。这是一个很大的话题，但它是“我能构建软件”和“我能运行人们真正使用的软件”之间的桥梁。

典型的解决方案，按复杂度排序：

1. **隧道服务**（ngrok、Cloudflare Tunnel）——从互联网到你的笔记本打一个临时洞。非常适合演示，非常不适合生产。
2. **云虚拟机**（AWS EC2、DigitalOcean Droplet）——租一台有公网 IP 的服务器，在那里部署你的应用。这才是真正的部署。
3. **平台即服务**（Heroku、Railway、Render）——推送你的代码，他们来处理服务器。方便但教育意义较小。

这些方案中的每一个都需要网络知识来理解和调试。当出问题时——而且一定会出问题——你需要知道什么是端口、TCP 如何工作、反向代理做什么，以及 DNS 如何将名称转换为地址。

<!-- ZH_RESOURCES -->
- [什么是 localhost？ - MDN](https://developer.mozilla.org/en-US/docs/Glossary/Localhost) -- 类型：参考，时间：5分钟
- [私有 IP 地址与公共 IP 地址](https://www.cloudflare.com/learning/network-layer/what-is-a-private-ip-address/) -- 类型：文章，时间：10分钟
- [互联网如何运作 - 斯坦福](https://web.stanford.edu/class/msande91si/www-spr04/readings/week1/InternetWhitepaper.htm) -- 类型：文章，时间：30分钟
- [ngrok 文档](https://ngrok.com/docs) -- 类型：工具，时间：15分钟

<!-- ZH_UI -->
1. 理解为什么 localhost 只能从你自己的机器访问
2. 尝试从同一网络上的另一台设备访问你的应用
3. 找出让你的应用可公开访问需要什么
4. 为什么其他人都无法访问我的应用？网络到底是什么？
5. 我绑定到 0.0.0.0，手机在同一 WiFi 下能访问应用——但城市另一头的朋友仍然访问不了。我不明白为什么。网络的结构方式肯定能解释这一点，但我不知道我漏掉了什么。
6. 我的应用在本地能跑。我到底该在哪里真正运行它？
7. 我无法用笔记本电脑运行生产服务——它会休眠、我会带着它到处走、IP 会变。我需要一个始终在线、始终可达的东西。但我完全不知道这意味着什么，也不知道我有哪些选择。
