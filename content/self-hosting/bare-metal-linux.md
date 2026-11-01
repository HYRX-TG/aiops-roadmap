---
id: bare-metal-linux
title: Installing Linux Directly (Bare Metal)
zone: self-hosting
edges:
  to:
    - id: ssh-into-your-server
      question: Debian is installed — now what?
      detail: >-
        The installer finished and the machine rebooted. I'm looking at a login
        prompt with no idea what to do next. I don't plan to keep a monitor
        plugged in — how am I supposed to actually use this thing?
difficulty: 1
tags:
  - self-hosting
  - linux
  - debian
  - bare-metal
category: practice
milestones:
  - Download and flash the Debian ISO
  - 'Complete the Debian installer (minimal, no desktop)'
  - Note the machine's IP address
  - SSH in successfully
title_zh: "直接安装 Linux（裸金属）"

---


We're installing **Debian 13 (Trixie)**. Not Ubuntu, not Fedora, not Arch. Debian. It's stable, boring, extremely well-documented, and has rock-solid Docker support. Ubuntu is a fine choice too — it's built on Debian — but we're making an opinionated call here and sticking with it.

Follow the [official Debian installation guide](https://www.debian.org/releases/trixie/amd64/) for complete documentation. This is the practical walkthrough.

<!-- DEEP_DIVE -->

**Step 1: Download and flash the ISO**

Get the **netinstall** ISO from [debian.org/distrib/netinst](https://www.debian.org/distrib/netinst). This is a small image that downloads packages over the network during install — it always gives you the latest package versions.

Flash it to a USB drive with [Balena Etcher](https://www.balena.io/etcher/) or `dd`:

```bash
dd if=debian-*-amd64-netinst.iso of=/dev/sdX bs=4M status=progress
```

**Step 2: Boot and install**

Plug the USB into your machine and boot from it (F2, F12, or Del to get the boot menu). Use the **graphical installer** — it's easier to navigate.

Key choices during install:

- **Hostname**: something simple like `homelab` or `server`
- **User account**: create a non-root user (e.g., your name). You'll use this to log in and `sudo` for admin commands.
- **Disk partitioning**: "Guided - use entire disk" with a single partition is fine for a server
- **Software selection**: this is important — **uncheck everything** except:
  - ☑ SSH server
  - ☑ standard system utilities
  - Everything else (desktop environments, web server, etc.) — leave unchecked

A server with no GUI uses less RAM and has fewer moving parts. You'll access it via SSH.

**Step 3: First boot and setup**

After install, the machine reboots into a bare Debian system. Log in with the user you created.

Run the first update:

```bash
sudo apt update && sudo apt upgrade -y
```

Note the machine's IP address:

```bash
ip a
```

Look for something like `192.168.1.x` on your main network interface. Write it down.

**Static IP vs DHCP reservation**

Your router assigns IPs via DHCP. By default, your server might get a different IP after each reboot. That's annoying — you need to know where to SSH.

The recommended approach is a **DHCP reservation** (sometimes called "static DHCP" or "address reservation") in your router settings. You tell the router "always give this MAC address this IP". The machine still uses DHCP, but always gets the same address. It's cleaner than configuring a static IP inside Linux.

Find this in your router's web interface under something like DHCP settings → Static leases / Address reservations. You'll need the machine's MAC address:

```bash
ip link show
```

Look for the `link/ether` line — that's the MAC address.

<!-- RESOURCES -->

- [Debian 13 Installation Guide](https://www.debian.org/releases/trixie/amd64/) -- type: guide, time: 30min
- [Balena Etcher](https://www.balena.io/etcher/) -- type: tool, time: 5min

<!-- ZH_SUMMARY -->
我们要安装的是 **Debian 13 (Trixie)**。不是 Ubuntu，不是 Fedora，也不是 Arch。就是 Debian。它稳定、朴实无华、文档极其完善，并且对 Docker 的支持坚如磐石。Ubuntu 也是个不错的选择——它基于 Debian 构建——但我们在这里做一个有主见的决定，并坚持到底。

完整的文档请参阅 [Debian 官方安装指南](https://www.debian.org/releases/trixie/amd64/)。以下是实用操作指南。

<!-- ZH_DEEP_DIVE -->
**步骤 1：下载并刷写 ISO**

从 [debian.org/distrib/netinst](https://www.debian.org/distrib/netinst) 获取 **netinstall** ISO。这是一个小型镜像，安装过程中会通过网络下载软件包——它始终能为你提供最新的软件包版本。

使用 [Balena Etcher](https://www.balena.io/etcher/) 或 `dd` 将其刷写到 USB 驱动器：

```bash
dd if=debian-*-amd64-netinst.iso of=/dev/sdX bs=4M status=progress
```

**步骤 2：启动并安装**

将 USB 插入你的机器并从它启动（按 F2、F12 或 Del 进入启动菜单）。使用**图形化安装程序**——它更易于操作。

安装过程中的关键选择：

- **主机名**：使用简单的名称，如 `homelab` 或 `server`
- **用户账户**：创建一个非 root 用户（例如你的名字）。你将使用它登录，并通过 `sudo` 执行管理命令。
- **磁盘分区**："Guided - use entire disk"（引导 - 使用整个磁盘）配合单一分区对服务器来说就足够了
- **软件选择**：这一点很重要——**取消勾选所有选项**，只保留：
  - ☑ SSH server
  - ☑ standard system utilities
  - 其他所有选项（桌面环境、Web 服务器等）——保持不勾选

没有 GUI 的服务器占用更少内存，活动部件也更少。你将通过 SSH 访问它。

**步骤 3：首次启动与设置**

安装完成后，机器会重启进入一个基础的 Debian 系统。使用你创建的用户登录。

运行首次更新：

```bash
sudo apt update && sudo apt upgrade -y
```

记下机器的 IP 地址：

```bash
ip a
```

在主网络接口上寻找类似 `192.168.1.x` 的地址。把它记下来。

**静态 IP 与 DHCP 保留**

你的路由器通过 DHCP 分配 IP。默认情况下，服务器每次重启后可能会获得不同的 IP。这很烦人——你需要知道该 SSH 到哪里。

推荐的方法是在路由器设置中配置 **DHCP 保留**（有时称为 "static DHCP" 或 "address reservation"）。你告诉路由器"始终将这个 IP 分配给这个 MAC 地址"。机器仍然使用 DHCP，但总是获得相同的地址。这比在 Linux 内部配置静态 IP 更简洁。

在路由器的 Web 界面中找到类似 DHCP 设置 → Static leases / Address reservations 的位置。你需要机器的 MAC 地址：

```bash
ip link show
```

寻找 `link/ether` 那一行——那就是 MAC 地址。

<!-- ZH_RESOURCES -->
- [Debian 13 安装指南](https://www.debian.org/releases/trixie/amd64/) -- 类型：指南，时长：30 分钟
- [Balena Etcher](https://www.balena.io/etcher/) -- 类型：工具，时长：5 分钟

<!-- ZH_UI -->
1. 下载并刷写 Debian ISO
2. 完成 Debian 安装程序（最小化，无桌面）
3. 记录机器的 IP 地址
4. 成功通过 SSH 登录
5. Debian 已安装——接下来做什么？
6. 安装程序已完成，机器已重启。我正看着登录提示符，完全不知道下一步该做什么。我不打算一直插着显示器——我到底该怎么使用这台机器？
