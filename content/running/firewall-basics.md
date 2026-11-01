---
id: firewall-basics
title: Firewall Basics
zone: running
edges:
  to:
    - id: deploying-your-code
      question: My server is set up and secured. Now how do I get my code onto it?
      detail: >-
        The server is locked down and my runtime is installed. But my code is
        still sitting on my laptop. How do I actually get it onto the server?
difficulty: 1
tags:
  - firewall
  - ufw
  - security-groups
  - ports
  - iptables
  - network-security
category: practice
milestones:
  - 'Configure ufw to allow only SSH, HTTP, and HTTPS and deny everything else'
  - >-
    Explain the difference between a host-based firewall (ufw) and a cloud
    security group
  - Safely change firewall rules without locking yourself out of SSH
title_zh: "防火墙基础"

---


A firewall controls which network traffic is allowed into and out of your server. Without one, every port your server has open — your app, any database, any internal service — is potentially reachable from anywhere on the internet. Bots and scanners probe servers constantly looking for exposed services to exploit.

A basic firewall rule is simple: deny everything by default, then explicitly allow only what you need.

<!-- DEEP_DIVE -->

**ufw — the Uncomplicated Firewall**

Ubuntu ships with `ufw`, a friendly wrapper around `iptables` (the kernel's low-level firewall). Most of the time, `ufw` is all you need.

```bash
# Set defaults: block all incoming, allow all outgoing
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH — do this BEFORE enabling ufw or you will lock yourself out
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS for your web server
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable the firewall
sudo ufw enable

# Check the current rules
sudo ufw status verbose
```

Output looks like:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
```

**The critical rule: allow SSH before you enable ufw**

If you enable ufw without first allowing port 22, you will immediately lock yourself out of the server. The firewall will block your SSH connection and you will have no way to get back in (unless your cloud provider has an out-of-band console).

Always:
1. `sudo ufw allow 22/tcp`
2. `sudo ufw enable`

Never do it in the other order.

**Managing rules**

```bash
# Allow a specific port
sudo ufw allow 5432/tcp      # PostgreSQL (only do this if you need remote DB access)

# Deny a port explicitly
sudo ufw deny 3306/tcp       # MySQL

# Allow from a specific IP only
sudo ufw allow from 203.0.113.5 to any port 22

# Delete a rule
sudo ufw delete allow 5432/tcp

# Reset everything (start over)
sudo ufw reset
```

**Cloud security groups — the second layer**

Most cloud providers have their own firewall at the network level, before traffic even reaches your server. DigitalOcean calls these "Cloud Firewalls." AWS calls them "Security Groups." They work the same way as `ufw` but are managed through the provider's control panel or API.

You should use both:

```
Internet
    ↓
Cloud Security Group (DigitalOcean/AWS firewall — network level)
    ↓ Only allowed traffic reaches the server
Server's network interface
    ↓
ufw (host-based firewall — kernel level)
    ↓ Second check before reaching the process
Your app / Nginx / SSH daemon
```

Cloud security groups are the outer gate. `ufw` is the inner gate. Using both is defense in depth — if one is misconfigured, the other still protects you.

**What ports to open**

For a typical web app on a VPS:

| Port | Service | Open? |
|------|---------|-------|
| 22 | SSH | Yes — your only way in |
| 80 | HTTP | Yes — Nginx listens here |
| 443 | HTTPS | Yes — Nginx listens here |
| 5000/3000 | Your app | No — Nginx proxies to it internally |
| 5432 | PostgreSQL | No — only accessible locally |
| 6379 | Redis | No — only accessible locally |

The rule: if a service is only used internally (your app talking to its own database), do not open a firewall port for it. It should only be reachable on `127.0.0.1`, not from the internet.

**Checking your work**

```bash
# See current status and rules
sudo ufw status verbose

# Test from your laptop that a port is open (replace with your server IP)
nc -zv 143.198.100.50 80
# Connection to 143.198.100.50 80 port [tcp/http] succeeded!

# Test that a port is correctly blocked
nc -zv 143.198.100.50 5000
# nc: connectx to 143.198.100.50 port 5000 (tcp) failed: Connection refused
```

**Logging**

```bash
# Enable logging to see blocked traffic
sudo ufw logging on

# Logs appear in /var/log/ufw.log
sudo tail -f /var/log/ufw.log
# UFW BLOCK IN=eth0 ... SRC=1.2.3.4 DST=143.198.100.50 ... DPT=3306
# (someone was trying to reach MySQL from the internet)
```

<!-- RESOURCES -->

- [DigitalOcean - ufw Essentials](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands) -- type: tutorial, time: 20m
- [ufw man page](https://manpages.ubuntu.com/manpages/focal/en/man8/ufw.8.html) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
防火墙控制允许进出服务器的网络流量。没有防火墙，服务器上开放的每个端口——你的应用、任何数据库、任何内部服务——都可能从互联网上的任何位置被访问到。机器人和扫描器会不断探测服务器，寻找可被利用的暴露服务。

基本的防火墙规则很简单：默认拒绝所有流量，然后只显式允许你需要的流量。

<!-- ZH_DEEP_DIVE -->
**ufw —— 简单的防火墙**

Ubuntu 自带 `ufw`，它是对 `iptables`（内核的低层防火墙）的友好封装。大多数情况下，`ufw` 就足够用了。

```bash
# 设置默认策略：阻止所有入站，允许所有出站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许 SSH —— 在启用 ufw 之前务必先执行此操作，否则你会把自己锁在外面
sudo ufw allow 22/tcp

# 为你的 Web 服务器允许 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看当前规则
sudo ufw status verbose
```

输出类似如下：
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
```

**关键规则：在启用 ufw 之前先允许 SSH**

如果你在未先允许 22 端口的情况下启用了 ufw，你会立即把自己锁在服务器之外。防火墙会阻断你的 SSH 连接，你将无法再重新进入（除非你的云服务商提供带外控制台）。

始终按以下顺序操作：
1. `sudo ufw allow 22/tcp`
2. `sudo ufw enable`

绝不要颠倒顺序。

**管理规则**

```bash
# 允许特定端口
sudo ufw allow 5432/tcp      # PostgreSQL（仅在你需要远程访问数据库时才这样做）

# 显式拒绝某个端口
sudo ufw deny 3306/tcp       # MySQL

# 仅允许来自特定 IP 的访问
sudo ufw allow from 203.0.113.5 to any port 22

# 删除一条规则
sudo ufw delete allow 5432/tcp

# 重置所有内容（从头开始）
sudo ufw reset
```

**云安全组 —— 第二层防护**

大多数云服务商在网络层面都有自己的防火墙，在流量到达你的服务器之前就进行过滤。DigitalOcean 称之为“Cloud Firewalls”，AWS 称之为“Security Groups”。它们的工作方式与 `ufw` 相同，但通过服务商的控制面板或 API 进行管理。

你应该同时使用两者：

```
Internet
    ↓
Cloud Security Group (DigitalOcean/AWS firewall — network level)
    ↓ Only allowed traffic reaches the server
Server's network interface
    ↓
ufw (host-based firewall — kernel level)
    ↓ Second check before reaching the process
Your app / Nginx / SSH daemon
```

云安全组是外层大门，`ufw` 是内层大门。同时使用两者即为纵深防御——如果其中一层配置错误，另一层仍能保护你。

**应开放哪些端口**

对于 VPS 上的典型 Web 应用：

| 端口 | 服务 | 是否开放？ |
|------|---------|-------|
| 22 | SSH | 是 —— 你唯一的进入方式 |
| 80 | HTTP | 是 —— Nginx 在此监听 |
| 443 | HTTPS | 是 —— Nginx 在此监听 |
| 5000/3000 | 你的应用 | 否 —— Nginx 在内部代理到它 |
| 5432 | PostgreSQL | 否 —— 仅本地可访问 |
| 6379 | Redis | 否 —— 仅本地可访问 |

规则是：如果某个服务仅在内部使用（你的应用与自己的数据库通信），就不要为它开放防火墙端口。它应该只能通过 `127.0.0.1` 访问，而不能从互联网访问。

**检查你的配置**

```bash
# 查看当前状态和规则
sudo ufw status verbose

# 从你的笔记本电脑测试某个端口是否开放（替换为你的服务器 IP）
nc -zv 143.198.100.50 80
# Connection to 143.198.100.50 80 port [tcp/http] succeeded!

# 测试某个端口是否被正确阻止
nc -zv 143.198.100.50 5000
# nc: connectx to 143.198.100.50 port 5000 (tcp) failed: Connection refused
```

**日志记录**

```bash
# 启用日志记录以查看被阻止的流量
sudo ufw logging on

# 日志出现在 /var/log/ufw.log
sudo tail -f /var/log/ufw.log
# UFW BLOCK IN=eth0 ... SRC=1.2.3.4 DST=143.198.100.50 ... DPT=3306
# (有人正试图从互联网访问 MySQL)
```

<!-- ZH_RESOURCES -->
- [DigitalOcean - ufw 基础](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands) -- 类型：教程，时长：20分钟
- [ufw 手册页](https://manpages.ubuntu.com/manpages/focal/en/man8/ufw.8.html) -- 类型：参考，时长：10分钟

<!-- ZH_UI -->
1. 配置 ufw 仅允许 SSH、HTTP 和 HTTPS，拒绝其他所有流量
2. 解释基于主机的防火墙（ufw）与云安全组之间的区别
3. 安全地更改防火墙规则，避免把自己锁在 SSH 之外
4. 服务器已配置并加固完成。现在如何把代码部署到服务器上？
5. 服务器已锁定加固，运行时也已安装。但代码还在我的笔记本电脑上。我究竟该如何把它传到服务器上？
