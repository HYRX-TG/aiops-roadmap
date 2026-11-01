---
id: own-hardware
title: Running on Your Own Hardware
zone: running
edges:
  to:
    - id: ssh
      question: I have a Linux machine running at home. How do I connect to it?
      detail: >-
        Whether your server is in a datacenter or under your desk, the interface
        is the same: SSH. You get a terminal that runs on the remote machine,
        and every command you type executes there. The only difference is where
        the hardware lives.
    - id: what-is-self-hosting
      zone: self-hosting
      question: I have my own hardware. What can I actually run on it?
      detail: >-
        A Linux box at home is the foundation for self-hosting — running your
        own file sync, media server, home automation hub, and more. You own the
        hardware, you own the data, and there are no monthly fees. The rabbit
        hole goes deep.
difficulty: 1
tags:
  - self-hosting
  - home-server
  - raspberry-pi
  - bare-metal
  - homelab
  - linux
category: concept
milestones:
  - >-
    Choose hardware suitable for a home server (Pi, mini PC, old laptop or
    desktop)
  - Install Linux on bare metal (not just picking a cloud image)
  - Assign a static local IP to your machine from your router
  - SSH into your home server from another machine on the same network
title_zh: "在自己的硬件上运行"

---


You don't have to rent a server. You can take an old PC, a Raspberry Pi, a used mini PC you found for $80 on eBay, and turn it into a Linux server that runs 24/7 in your home. This is the other answer to "where do I run this?" — and it's a completely valid one.

The skills are the same as a VPS. The hardware is yours.

<!-- DEEP_DIVE -->

**What hardware should you use?**

Almost anything running Linux works. Here are the most common choices:

| Hardware | Cost | Power | Use case |
|---|---|---|---|
| **Raspberry Pi 4/5** | $60–90 | ~5W | Light workloads, learning, IoT |
| **Mini PC** (Beelink, Intel NUC, used ThinkCentre) | $80–250 | 10–35W | The sweet spot for most home servers |
| **Old laptop** | Free (you may already have one) | 15–45W | Gets you started immediately |
| **Old desktop** | Free–$100 | 65–150W | Lots of storage, noisier, more power |
| **Used rackmount server** | $100–500 | 150–400W | Serious homelab, loud, hot |

For most people starting out: **a used mini PC is the best choice**. They're quiet, energy-efficient, have enough CPU and RAM for most home services, and cost less than two months of a VPS.

**Installing Linux on bare metal**

With a VPS, you pick an OS from a dropdown and the hypervisor handles the rest. With your own hardware, you do it yourself:

1. Download an Ubuntu Server ISO from ubuntu.com
2. Flash it to a USB drive with a tool like Balena Etcher or `dd`
3. Boot your machine from the USB (change boot order in BIOS/UEFI)
4. Walk through the installer — set a username, configure disk, enable SSH server
5. Pull out the USB, reboot, and you have a headless Linux machine

```bash
# Flash the ISO to a USB drive (on macOS/Linux)
# Replace /dev/sdX with your USB device — double check with lsblk
sudo dd if=ubuntu-24.04-server.iso of=/dev/sdX bs=4M status=progress
```

After install, you never need a monitor plugged in again. SSH is your interface.

**Setting a static local IP**

By default, your router assigns IP addresses dynamically via DHCP. Every time your server reboots, it might get a different IP, which means your SSH commands break. Fix this by reserving a static IP.

The easiest way is a **DHCP reservation** in your router settings (sometimes called "static IP" or "address binding"). Find your server's MAC address, and tell the router to always give it the same IP:

```bash
# Find your server's MAC address
ip link show
# Look for your ethernet interface (eth0, enp3s0, etc.)
# The MAC address looks like: aa:bb:cc:dd:ee:ff
```

Go into your router admin panel (usually `192.168.1.1` or `192.168.0.1`), find DHCP settings, and add a reservation. Now your server always gets, say, `192.168.1.100`.

**How your home server differs from a VPS**

This is the important part. Your home server has some real constraints compared to a cloud VM:

| | VPS | Home Server |
|---|---|---|
| **Public IP** | Static, assigned to you | Dynamic — changes when your ISP feels like it |
| **Network** | Direct, no NAT | Behind your home router (NAT) |
| **Uptime** | Datacenter-grade power + cooling | Your home electricity + internet |
| **Access from outside** | Direct via public IP | Requires extra setup (port forwarding or VPN) |
| **Cost** | Monthly fee forever | Hardware cost once, electricity ongoing |
| **Data** | Provider's disks | Your disks, your responsibility |

The **NAT problem** is the big one: your home router has a single public IP, and your server sits behind it with a private IP (`192.168.x.x`). The internet can't reach your server directly. If you want services accessible from outside your home, you need to deal with this — either through port forwarding, a VPN tunnel (Tailscale is the easiest modern solution), or a reverse proxy in the cloud.

The **dynamic IP problem** compounds this: your ISP can change your home's public IP at any time (usually every few days or on router restart). Services like DuckDNS or Cloudflare's free DNS can automatically update a domain name to point at your current IP (Dynamic DNS / DDNS).

These sound like blockers. They're not — they're just things you learn to handle. The self-hosting community has solved all of them, and the solutions are well-documented.

**Why do this at all?**

- **You own the data.** Your files on your server are on your hardware. No company can read them, sell them, or delete your account.
- **No subscriptions.** Run Nextcloud instead of Google Drive, Jellyfin instead of Netflix, Immich instead of Google Photos — for the cost of electricity.
- **Real learning.** You will break things, fix them, understand why. No managed service insulates you from the interesting parts.
- **It's fun.** The homelab community is massive and enthusiastic. There's always another service to run, another thing to optimize.

The path from here is the same as any other Linux server: SSH in, learn the basics, start running services. The difference is what those services are — and who they're for.

<!-- RESOURCES -->

- [LinuxServer.io](https://www.linuxserver.io/) -- type: reference, time: ongoing
- [r/selfhosted](https://www.reddit.com/r/selfhosted/) -- type: community, time: ongoing
- [Perfect Media Server](https://perfectmediaserver.com/) -- type: guide, time: 60m
- [Raspberry Pi Official Docs](https://www.raspberrypi.com/documentation/) -- type: reference, time: varies

<!-- ZH_SUMMARY -->
你不必租用服务器。你可以拿一台旧电脑、一个树莓派，或是在 eBay 上花 80 美元淘来的二手迷你主机，把它变成一台在家里 7×24 小时运行的 Linux 服务器。这就是“我该在哪里运行这个？”的另一个答案——而且它完全成立。

所需的技能和用 VPS 时一样。硬件是你自己的。

<!-- ZH_DEEP_DIVE -->
**应该使用什么硬件？**

几乎任何运行 Linux 的设备都可以。以下是最常见的选择：

| 硬件 | 成本 | 功耗 | 使用场景 |
|---|---|---|---|
| **Raspberry Pi 4/5** | $60–90 | ~5W | 轻负载、学习、IoT |
| **Mini PC**（Beelink、Intel NUC、二手 ThinkCentre） | $80–250 | 10–35W | 大多数家庭服务器的最佳选择 |
| **旧笔记本电脑** | 免费（你可能已经有一台） | 15–45W | 让你立即上手 |
| **旧台式机** | 免费–$100 | 65–150W | 存储空间大、噪音更大、功耗更高 |
| **二手机架式服务器** | $100–500 | 150–400W | 认真的 homelab、噪音大、发热高 |

对于大多数刚起步的人来说：**二手 Mini PC 是最佳选择**。它们安静、节能，拥有足够的 CPU 和 RAM 来运行大多数家庭服务，而且成本不到两个月 VPS 的费用。

**在裸机上安装 Linux**

使用 VPS 时，你从下拉菜单中选择一个操作系统，hypervisor 会处理其余的事情。使用自己的硬件时，你需要自己动手：

1. 从 ubuntu.com 下载 Ubuntu Server ISO
2. 使用 Balena Etcher 或 `dd` 等工具将其刷写到 USB 驱动器
3. 从 USB 启动你的机器（在 BIOS/UEFI 中更改启动顺序）
4. 按照安装程序操作——设置用户名、配置磁盘、启用 SSH 服务器
5. 拔出 USB，重启，你就拥有了一台无头 Linux 机器

```bash
# Flash the ISO to a USB drive (on macOS/Linux)
# Replace /dev/sdX with your USB device — double check with lsblk
sudo dd if=ubuntu-24.04-server.iso of=/dev/sdX bs=4M status=progress
```

安装完成后，你再也不需要插显示器了。SSH 就是你的接口。

**设置静态本地 IP**

默认情况下，你的路由器通过 DHCP 动态分配 IP 地址。每次服务器重启时，它可能会获得不同的 IP，这意味着你的 SSH 命令会失效。通过保留静态 IP 来解决这个问题。

最简单的方法是在路由器设置中进行 **DHCP 保留**（有时称为“静态 IP”或“地址绑定”）。找到你服务器的 MAC 地址，然后告诉路由器始终给它相同的 IP：

```bash
# Find your server's MAC address
ip link show
# Look for your ethernet interface (eth0, enp3s0, etc.)
# The MAC address looks like: aa:bb:cc:dd:ee:ff
```

进入你的路由器管理面板（通常是 `192.168.1.1` 或 `192.168.0.1`），找到 DHCP 设置，然后添加一个保留。现在你的服务器始终获得，比如说，`192.168.1.100`。

**你的家庭服务器与 VPS 有何不同**

这是重要的部分。与云 VM 相比，你的家庭服务器有一些实际的限制：

| | VPS | 家庭服务器 |
|---|---|---|
| **公网 IP** | 静态，分配给你 | 动态——你的 ISP 想变就变 |
| **网络** | 直接，无 NAT | 位于你的家庭路由器之后（NAT） |
| **正常运行时间** | 数据中心级供电 + 冷却 | 你家的电力和互联网 |
| **从外部访问** | 通过公网 IP 直接访问 | 需要额外设置（端口转发或 VPN） |
| **成本** | 永久每月付费 | 一次性硬件成本，持续电费 |
| **数据** | 提供商的磁盘 | 你的磁盘，你的责任 |

**NAT 问题**是大问题：你的家庭路由器只有一个公网 IP，而你的服务器位于其后，使用私有 IP（`192.168.x.x`）。互联网无法直接访问你的服务器。如果你希望服务能从家外访问，你需要处理这个问题——要么通过端口转发、VPN 隧道（Tailscale 是最简单的现代解决方案），要么在云中使用反向代理。

**动态 IP 问题**使情况更加复杂：你的 ISP 可以随时更改你家的公网 IP（通常每隔几天或在路由器重启时）。DuckDNS 或 Cloudflare 的免费 DNS 等服务可以自动更新域名以指向你当前的 IP（动态 DNS / DDNS）。

这些听起来像是障碍。它们不是——它们只是你学会处理的事情。自托管社区已经解决了所有这些问题，而且解决方案有充分的文档记录。

**为什么要这样做？**

- **你拥有数据。** 你服务器上的文件在你的硬件上。没有公司可以读取它们、出售它们或删除你的账户。
- **没有订阅。** 运行 Nextcloud 而不是 Google Drive，Jellyfin 而不是 Netflix，Immich 而不是 Google Photos——只需电费。
- **真正的学习。** 你会弄坏东西、修复它们、理解原因。没有托管服务会让你远离有趣的部分。
- **这很有趣。** homelab 社区庞大而热情。总有另一个服务要运行，另一件事要优化。

从这里开始的路径与任何其他 Linux 服务器相同：SSH 登录，学习基础知识，开始运行服务。不同之处在于这些服务是什么——以及它们为谁服务。

<!-- ZH_RESOURCES -->
- [LinuxServer.io](https://www.linuxserver.io/) -- 类型：参考，时间：持续
- [r/selfhosted](https://www.reddit.com/r/selfhosted/) -- 类型：社区，时间：持续
- [Perfect Media Server](https://perfectmediaserver.com/) -- 类型：指南，时间：60 分钟
- [Raspberry Pi 官方文档](https://www.raspberrypi.com/documentation/) -- 类型：参考，时间：不定

<!-- ZH_UI -->
1. 选择适合家庭服务器的硬件（树莓派、迷你主机、旧笔记本或台式机）
2. 在裸机上安装 Linux（而不只是选个云镜像）
3. 从路由器为你的机器分配静态局域网 IP
4. 从同一网络中的另一台机器 SSH 登录你的家庭服务器
5. 我家里有一台运行 Linux 的机器，如何连接到它？
6. 无论你的服务器在数据中心还是在你的桌下，接口都一样：SSH。你会得到一个运行在远程机器上的终端，你输入的每条命令都在那里执行。唯一的区别是硬件放在哪里。
7. 我有自己的硬件，实际能在上面运行什么？
8. 家里的 Linux 机器是自托管的基础——运行你自己的文件同步、媒体服务器、家庭自动化中枢等等。你拥有硬件，你拥有数据，而且没有月费。这个坑可以挖得很深。
