---
id: ports-and-listening
title: Ports and How Apps Listen for Traffic
zone: running
edges:
  to:
    - id: firewall-basics
      question: >-
        My app is listening on a port. Who can actually connect to it from the
        internet?
      detail: >-
        My app is listening on port 5000 but I still can't reach it from outside
        the server. I've heard there's a firewall that might be blocking it —
        but I don't know how to check or fix that.
difficulty: 1
tags:
  - ports
  - tcp
  - sockets
  - listening
  - 0.0.0.0
  - 127.0.0.1
  - netstat
  - ss
category: concept
milestones:
  - Explain the difference between 0.0.0.0 and 127.0.0.1 and when to use each
  - Use ss -tlnp to see what processes are listening on which ports
  - Understand why non-root users cannot bind to ports below 1024
title_zh: "端口与应用如何监听流量"

---


When your web app starts, it opens a socket and listens on a port — waiting for incoming connections. HTTP traffic goes to port 80. HTTPS to 443. SSH to 22. Your Flask or Express app probably listens on 3000 or 5000. A port is just a number that tells the operating system which process should receive a given packet.

Understanding ports — what they are, which address your app binds to, and how to inspect what is running — is essential for debugging the inevitable "why can't I reach my app?" problems.

<!-- DEEP_DIVE -->

**What is a port?**

A server has one IP address (say, `143.198.100.50`) but can run many services at once: a web server, an SSH server, a database, your app. Ports are how the OS tells them apart.

When a packet arrives at the server with `destination port 80`, the OS delivers it to whichever process is listening on port 80. When a packet arrives for port 5000, it goes to your Flask app.

Ports range from 0 to 65535:
- **0–1023**: Well-known ports. Require root to bind. HTTP=80, HTTPS=443, SSH=22, DNS=53.
- **1024–49151**: Registered ports. Common apps: Redis=6379, Postgres=5432, MySQL=3306, Node apps typically use 3000–9000.
- **49152–65535**: Ephemeral ports. Used temporarily for outgoing connections.

**The address your app binds to**

When your app listens, it binds to an IP address AND a port. This matters a lot:

```
0.0.0.0:5000   → listen on ALL network interfaces — reachable from the internet
127.0.0.1:5000 → listen on loopback only — only reachable from the server itself
```

For security, your app should bind to `127.0.0.1`, and Nginx (your reverse proxy) should handle traffic from the internet on port 80/443. Nginx then forwards requests to `127.0.0.1:5000` internally. This way, your app is never directly exposed to the internet.

```python
# Flask — bind to localhost only (correct for production)
app.run(host='127.0.0.1', port=5000)

# Flask — bind to all interfaces (only do this for testing)
app.run(host='0.0.0.0', port=5000)
```

```javascript
// Express
app.listen(3000, '127.0.0.1', () => {
  console.log('Listening on 127.0.0.1:3000');
});
```

**Why non-root users cannot bind to ports below 1024**

Ports 1–1023 are privileged. The kernel requires root (or the `CAP_NET_BIND_SERVICE` capability) to bind to them. This is why:

- Your app should NOT run as root just to use port 80
- Instead: run your app on port 5000 (or 3000, 8000, etc.) as a normal user
- Run Nginx as root briefly to bind port 80/443, then drop to a lower-privilege worker

Trying to bind a privileged port as a non-root user gives you:
```
Error: listen EACCES: permission denied 0.0.0.0:80
```

The fix is not to run your app as root. The fix is to use Nginx as a reverse proxy.

**Checking what is listening**

`ss` (socket statistics) is the modern replacement for `netstat`:

```bash
# Show all TCP ports that are listening, with the process name
sudo ss -tlnp

# Output looks like:
# State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
# LISTEN  0       128     127.0.0.1:5000      0.0.0.0:*          users:(("python3",pid=12345))
# LISTEN  0       511     0.0.0.0:80          0.0.0.0:*          users:(("nginx",pid=1001))
# LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=892))

# Flags:
# -t  TCP only
# -l  listening sockets only
# -n  show port numbers, not service names
# -p  show which process owns the socket (requires sudo)
```

Quick test — can you reach your app locally?

```bash
# If your app is on 127.0.0.1:5000, test it from the server itself
curl http://127.0.0.1:5000/

# If you get a response, the app is running and reachable locally
# If you get "Connection refused", the app is not listening on that port
```

**How traffic flows (the full picture)**

```
Browser on the internet
    ↓ TCP connection to 143.198.100.50:443
Server's network interface (public IP)
    ↓ Firewall checks: is port 443 allowed?
Nginx (listening on 0.0.0.0:443)
    ↓ TLS termination, then proxy_pass http://127.0.0.1:5000
Your Flask/Node app (listening on 127.0.0.1:5000)
    ↓ Processes the request, returns response
Back through Nginx to the browser
```

This is the standard architecture. Nginx is the only thing listening on the public IP for ports 80/443. Your app is only reachable internally via localhost.

**Common mistakes**

- **Binding to `0.0.0.0` in production** — your app is directly reachable from the internet, bypassing Nginx, TLS, and any rate limiting
- **Forgetting to check what is already on a port** — you try to start your app and it fails because something else already claimed that port. Check with `ss -tlnp`.
- **Running your app on port 80 as root** — root is not needed for your app. Use Nginx on 80 and your app on an unprivileged port.

<!-- RESOURCES -->

- [ss command reference](https://man7.org/linux/man-pages/man8/ss.8.html) -- type: reference, time: 10m
- [Linux Well-Known Ports (Wikipedia)](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers) -- type: reference, time: 5m

<!-- ZH_SUMMARY -->
当你的 Web 应用启动时，它会打开一个套接字并在某个端口上监听——等待传入的连接。HTTP 流量走 80 端口。HTTPS 走 443。SSH 走 22。你的 Flask 或 Express 应用可能监听在 3000 或 5000 端口。端口只是一个数字，用来告诉操作系统哪个进程应该接收某个给定的数据包。

理解端口——它们是什么、你的应用绑定到哪个地址、以及如何检查正在运行的内容——对于调试那些不可避免的“为什么我访问不到我的应用？”问题至关重要。

<!-- ZH_DEEP_DIVE -->
**什么是端口？**

一台服务器只有一个 IP 地址（比如 `143.198.100.50`），但可以同时运行多个服务：Web 服务器、SSH 服务器、数据库、你的应用。端口就是操作系统用来区分它们的方式。

当一个数据包到达服务器、其 `destination port 80` 时，操作系统会把它交给正在监听 80 端口的那个进程。当一个数据包到达 5000 端口时，它会被交给你的 Flask 应用。

端口范围是 0 到 65535：
- **0–1023**：知名端口。绑定需要 root 权限。HTTP=80、HTTPS=443、SSH=22、DNS=53。
- **1024–49151**：注册端口。常见应用：Redis=6379、Postgres=5432、MySQL=3306、Node 应用通常使用 3000–9000。
- **49152–65535**：临时端口。用于出站连接的临时分配。

**你的应用绑定的地址**

当你的应用监听时，它会绑定到一个 IP 地址和一个端口。这一点非常重要：

```
0.0.0.0:5000   → 监听所有网络接口 —— 可从互联网访问
127.0.0.1:5000 → 仅监听回环地址 —— 只能从服务器本身访问
```

出于安全考虑，你的应用应绑定到 `127.0.0.1`，由 Nginx（你的反向代理）在 80/443 端口上处理来自互联网的流量。然后 Nginx 在内部把请求转发到 `127.0.0.1:5000`。这样，你的应用就永远不会直接暴露在互联网上。

```python
# Flask —— 仅绑定到 localhost（生产环境的正确做法）
app.run(host='127.0.0.1', port=5000)

# Flask —— 绑定到所有接口（仅用于测试）
app.run(host='0.0.0.0', port=5000)
```

```javascript
// Express
app.listen(3000, '127.0.0.1', () => {
  console.log('Listening on 127.0.0.1:3000');
});
```

**为什么非 root 用户无法绑定 1024 以下的端口**

1–1023 端口是特权端口。内核要求 root（或 `CAP_NET_BIND_SERVICE` 能力）才能绑定它们。这就是为什么：

- 你的应用不应该仅仅为了使用 80 端口就以 root 身份运行
- 相反：以普通用户身份在 5000 端口（或 3000、8000 等）上运行你的应用
- 以 root 身份短暂运行 Nginx 以绑定 80/443 端口，然后降权到低权限的 worker 进程

以非 root 用户尝试绑定特权端口会得到：
```
Error: listen EACCES: permission denied 0.0.0.0:80
```

解决办法不是以 root 身份运行你的应用，而是使用 Nginx 作为反向代理。

**检查正在监听的内容**

`ss`（socket statistics）是 `netstat` 的现代替代品：

```bash
# 显示所有正在监听的 TCP 端口，以及进程名
sudo ss -tlnp

# 输出类似这样：
# State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
# LISTEN  0       128     127.0.0.1:5000      0.0.0.0:*          users:(("python3",pid=12345))
# LISTEN  0       511     0.0.0.0:80          0.0.0.0:*          users:(("nginx",pid=1001))
# LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=892))

# 参数说明：
# -t  仅 TCP
# -l  仅监听中的 socket
# -n  显示端口号，而非服务名
# -p  显示哪个进程拥有该 socket（需要 sudo）
```

快速测试 —— 你能在本地访问你的应用吗？

```bash
# 如果你的应用在 127.0.0.1:5000，从服务器本身测试它
curl http://127.0.0.1:5000/

# 如果得到响应，说明应用正在运行且可在本地访问
# 如果得到 "Connection refused"，说明应用没有在该端口上监听
```

**流量如何流动（完整图景）**

```
互联网上的浏览器
    ↓ TCP 连接到 143.198.100.50:443
服务器的网络接口（公网 IP）
    ↓ 防火墙检查：443 端口是否允许？
Nginx（监听 0.0.0.0:443）
    ↓ TLS 终止，然后 proxy_pass http://127.0.0.1:5000
你的 Flask/Node 应用（监听 127.0.0.1:5000）
    ↓ 处理请求，返回响应
经 Nginx 返回给浏览器
```

这是标准架构。Nginx 是唯一在公网 IP 的 80/443 端口上监听的东西。你的应用只能通过 localhost 在内部访问。

**常见错误**

- **在生产环境绑定到 `0.0.0.0`** —— 你的应用会直接从互联网可达，绕过 Nginx、TLS 以及任何限流
- **忘记检查端口上已有什么** —— 你尝试启动应用却失败了，因为别的进程已经占用了那个端口。用 `ss -tlnp` 检查。
- **以 root 身份在 80 端口上运行你的应用** —— 你的应用不需要 root。在 80 端口上用 Nginx，让你的应用使用非特权端口。

<!-- ZH_RESOURCES -->
- [ss 命令参考](https://man7.org/linux/man-pages/man8/ss.8.html) -- 类型：参考，时间：10m
- [Linux 知名端口（维基百科）](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers) -- 类型：参考，时间：5m

<!-- ZH_UI -->
1. 解释 0.0.0.0 与 127.0.0.1 的区别以及各自的使用场景
2. 使用 ss -tlnp 查看哪些进程在监听哪些端口
3. 理解为什么非 root 用户无法绑定 1024 以下的端口
4. 我的应用正在监听某个端口，实际谁能从互联网连接到它？
5. 我的应用监听在 5000 端口，但我仍然无法从服务器外部访问它。我听说可能有防火墙在拦截，但我不知道如何检查或修复。
