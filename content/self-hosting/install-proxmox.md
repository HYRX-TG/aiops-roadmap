---
id: install-proxmox
title: Installing Proxmox and Creating Your First VM
zone: self-hosting
edges:
  to:
    - id: ssh-into-your-server
      question: Proxmox is running and I have a Debian VM — now what?
      detail: >-
        The VM shows as running in the Proxmox UI. How do I actually get into
        it? Do I use that console in the web interface, set up SSH, or something
        else?
difficulty: 1
tags:
  - self-hosting
  - proxmox
  - virtualization
  - homelab
  - vm
category: practice
milestones:
  - Download and flash the Proxmox ISO
  - Complete the Proxmox installer
  - Access the Proxmox web UI
  - Create a Debian VM and boot it
  - SSH into the VM successfully
title_zh: "安装 Proxmox 并创建你的第一台虚拟机"

---


Proxmox installs directly onto your hardware like any operating system — you boot from a USB drive, run through the installer, and the machine becomes a hypervisor. After that, you manage everything from a web browser.

Follow the [official Proxmox installation guide](https://pve.proxmox.com/wiki/Installation) for the full walkthrough. What follows here is the practical overview.

<!-- DEEP_DIVE -->

**Step 1: Create a bootable USB**

Download the Proxmox VE ISO from [proxmox.com/downloads](https://www.proxmox.com/en/downloads). Flash it to a USB drive using [Balena Etcher](https://www.balena.io/etcher/) (Windows/Mac) or `dd` on Linux:

```bash
dd if=proxmox-ve_*.iso of=/dev/sdX bs=4M status=progress
```

Replace `/dev/sdX` with your USB device (use `lsblk` to find it).

**Step 2: Install**

Boot from the USB (usually F2, F12, or Del at startup to get the boot menu). The installer is straightforward:

- Select target disk — this erases everything on it
- Set country, timezone, keyboard layout
- Set a root password and email (the email is for alerts; any valid address works)
- **Network config**: set a static IP that's outside your router's DHCP range (e.g., `192.168.1.10`). Proxmox needs a fixed IP.
- Hostname: something like `pve.local` works fine

After install, the machine reboots and you're done.

**Step 3: Access the web UI**

Open a browser and go to `https://YOUR-IP:8006`. You'll get a certificate warning (expected — it's using a self-signed cert). Proceed anyway.

Log in with username `root` and the password you set.

**The "no valid subscription" warning**

Proxmox is free and open-source. When you log in, it shows a popup saying you have no active subscription. Click OK and ignore it. This is their enterprise support upsell — it does not affect any functionality. The community edition you're running is fully featured.

If the popup annoys you, there are scripts to remove it, but it really doesn't matter.

**Step 4: Upload a Debian ISO**

You need a Debian ISO to create a VM. In the web UI:

1. Click your node name in the left panel (e.g., "pve")
2. Go to **local** → **ISO Images** → **Download from URL**
3. Paste the Debian netinstall ISO URL from [debian.org/distrib/netinst](https://www.debian.org/distrib/netinst) (grab the amd64 netinst link)
4. Click **Query URL** then **Download**

**Step 5: Create a VM**

Click **Create VM** in the top right. Reasonable defaults for a self-hosting VM:

| Setting | Value |
|---|---|
| OS | Choose the Debian ISO you uploaded |
| Disk | 32GB is plenty for most services |
| CPU | 2 cores |
| RAM | 2048MB (2GB) — add more if needed later |
| Network | Default (VirtIO, on the bridge) |

Start the VM and open its console (the **Console** button in the sidebar). You'll see the Debian installer boot up.

**Step 6: Install Debian in the VM**

The Debian installer is text-based. Key choices:
- **No graphical desktop** — just a server. When it asks about software, uncheck everything except **SSH server** and **standard system utilities**
- Set a hostname, create a user with a password
- Let it partition the disk automatically

After install, the VM reboots into a running Debian system.

**A note on LXC containers**

Proxmox also supports LXC containers — lighter than VMs because they share the host kernel. Many homelabbers prefer LXC for simple services like Pi-hole or small databases. For now, VMs are simpler to reason about. You can explore LXC later once you're comfortable with the basics.

<!-- RESOURCES -->

- [Proxmox VE Installation Guide](https://pve.proxmox.com/wiki/Installation) -- type: guide, time: 30min
- [Balena Etcher](https://www.balena.io/etcher/) -- type: tool, time: 5min
- [tteck's Proxmox Helper Scripts](https://tteck.github.io/Proxmox/) -- type: tool, time: ongoing

<!-- ZH_SUMMARY -->
Proxmox 像任何操作系统一样直接安装到你的硬件上——从 USB 驱动器启动，运行安装程序，这台机器就变成了一个 hypervisor。之后，你通过 Web 浏览器管理一切。

完整的操作步骤请遵循 [Proxmox 官方安装指南](https://pve.proxmox.com/wiki/Installation)。下面给出的是实用概览。

<!-- ZH_DEEP_DIVE -->
**步骤 1：创建可启动 USB**

从 [proxmox.com/downloads](https://www.proxmox.com/en/downloads) 下载 Proxmox VE ISO。使用 [Balena Etcher](https://www.balena.io/etcher/)（Windows/Mac）或 Linux 上的 `dd` 将其写入 USB 驱动器：

```bash
dd if=proxmox-ve_*.iso of=/dev/sdX bs=4M status=progress
```

将 `/dev/sdX` 替换为你的 USB 设备（使用 `lsblk` 查找）。

**步骤 2：安装**

从 USB 启动（通常在启动时按 F2、F12 或 Del 进入启动菜单）。安装程序很直观：

- 选择目标磁盘——这会擦除磁盘上的所有内容
- 设置国家、时区、键盘布局
- 设置 root 密码和邮箱（邮箱用于接收告警；任何有效地址均可）
- **网络配置**：设置一个位于路由器 DHCP 范围之外的静态 IP（例如 `192.168.1.10`）。Proxmox 需要固定 IP。
- 主机名：类似 `pve.local` 即可

安装完成后，机器重启，一切就绪。

**步骤 3：访问 Web UI**

打开浏览器并访问 `https://YOUR-IP:8006`。你会看到证书警告（这是预期内的——它使用的是自签名证书）。继续访问即可。

使用用户名 `root` 和你设置的密码登录。

**“无有效订阅”警告**

Proxmox 是免费且开源的。登录时，它会弹出一个提示，说你没有有效订阅。点击 OK 并忽略它。这是他们的企业支持推销——不影响任何功能。你运行的社区版功能完整。

如果这个弹窗让你烦，有脚本可以移除它，但这真的无所谓。

**步骤 4：上传 Debian ISO**

你需要一个 Debian ISO 来创建 VM。在 Web UI 中：

1. 点击左侧面板中的节点名称（例如 “pve”）
2. 转到 **local** → **ISO Images** → **Download from URL**
3. 粘贴来自 [debian.org/distrib/netinst](https://www.debian.org/distrib/netinst) 的 Debian netinstall ISO URL（获取 amd64 netinst 链接）
4. 点击 **Query URL**，然后点击 **Download**

**步骤 5：创建 VM**

点击右上角的 **Create VM**。对于自托管 VM，合理的默认值如下：

| 设置 | 值 |
|---|---|
| OS | 选择你上传的 Debian ISO |
| Disk | 32GB 对大多数服务来说足够 |
| CPU | 2 核 |
| RAM | 2048MB（2GB）——之后如需更多可增加 |
| Network | 默认（VirtIO，位于网桥上） |

启动 VM 并打开其控制台（侧边栏中的 **Console** 按钮）。你会看到 Debian 安装程序启动。

**步骤 6：在 VM 中安装 Debian**

Debian 安装程序是基于文本的。关键选择：
- **无图形桌面**——仅服务器。当它询问软件时，取消勾选除 **SSH server** 和 **standard system utilities** 之外的所有选项
- 设置主机名，创建一个带密码的用户
- 让它自动分区磁盘

安装完成后，VM 重启进入运行中的 Debian 系统。

**关于 LXC 容器的说明**

Proxmox 也支持 LXC 容器——比 VM 更轻量，因为它们共享宿主内核。许多 homelab 爱好者更喜欢用 LXC 运行 Pi-hole 或小型数据库等简单服务。目前来说，VM 更容易理解。等你熟悉基础之后，可以再探索 LXC。

<!-- ZH_RESOURCES -->
- [Proxmox VE 安装指南](https://pve.proxmox.com/wiki/Installation) -- 类型：指南，时间：30 分钟
- [Balena Etcher](https://www.balena.io/etcher/) -- 类型：工具，时间：5 分钟
- [tteck 的 Proxmox 辅助脚本](https://tteck.github.io/Proxmox/) -- 类型：工具，时间：持续进行

<!-- ZH_UI -->
1. 下载并刷写 Proxmox ISO
2. 完成 Proxmox 安装程序
3. 访问 Proxmox Web UI
4. 创建 Debian 虚拟机并启动
5. 成功通过 SSH 登录虚拟机
6. Proxmox 已运行，我也有一台 Debian 虚拟机——接下来做什么？
7. 虚拟机在 Proxmox UI 中显示为运行中。我实际该如何进入它？是用 Web 界面里的那个控制台、配置 SSH，还是其他方式？
