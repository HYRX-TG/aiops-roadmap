---
id: unraid
title: 'Unraid: Storage, VMs, and Docker in One Box'
zone: self-hosting
edges:
  to:
    - id: ssh-into-your-server
      question: Unraid is running — how do I get into it and start setting things up?
      detail: >-
        The web UI is up and I can see my drives. But I want to SSH in and
        start running services. How does that work on Unraid — is it just
        Linux underneath?
difficulty: 2
tags:
  - self-hosting
  - unraid
  - storage
  - virtualization
  - docker
category: tool
milestones:
  - Understand how Unraid's storage model differs from traditional RAID
  - Know when Unraid makes sense vs Proxmox + separate NAS
  - Install Unraid and configure your array
  - Run your first Docker container through the Unraid UI
title_zh: "Unraid：存储、虚拟机和 Docker 一体化"

---


Unraid is an operating system for your server that combines storage management, Docker containers, and virtual machines in a single package. You install it on a USB drive, boot from it, and manage everything through a web UI.

What makes it different from Proxmox or bare-metal Linux is the storage model. Unraid lets you mix and match drives of different sizes — no matching pairs required — and adds parity protection so you can survive drive failures. It's particularly popular with media server builders and people who want one box that does everything.

<!-- DEEP_DIVE -->

## How Unraid storage works

Traditional RAID requires identical (or similar) drives and stripes data across all of them. Unraid takes a different approach:

**The array** — Your data drives don't form a stripe. Each file lives on exactly one drive, written as a normal filesystem (XFS or BTRFS). You can pull any single drive from the array and read its files on another Linux machine. This is fundamentally different from RAID, where no single drive is readable on its own.

**Parity drives** — One or two drives are designated as parity. They store calculated data that lets Unraid reconstruct any single failed drive's contents. One parity drive protects against one drive failure. Two parity drives protect against two simultaneous failures.

**Mix and match** — Your data drives can be different sizes and brands. A 4TB, an 8TB, and a 12TB can all coexist in the same array. The only rule: each parity drive must be as large as the biggest data drive.

**The cache pool** — A fast SSD (or pool of SSDs) that acts as a write buffer. New files land on the cache first, then get moved to the array on a schedule ("mover"). This means writes are fast (SSD speed) even though the array uses slower spinning drives. Docker containers and VMs typically run on the cache pool for performance.

## Unraid vs Proxmox

They solve different problems and have different strengths:

| | Unraid | Proxmox |
|---|---|---|
| **Primary strength** | Storage management | Virtualization |
| **Storage model** | Mix-and-match drives with parity | Uses whatever the OS underneath uses |
| **Docker** | Built-in, GUI-managed | Run inside VMs |
| **VMs** | Supported via KVM/libvirt | First-class, full-featured |
| **Price** | $59–$129 license (one-time) | Free (open source) |
| **Best for** | All-in-one server (storage + services) | Multi-VM environments, clustering |

**Choose Unraid if:** You want one machine that handles storage and runs your Docker services, and you have a bunch of mismatched drives. Unraid excels as the single-box homelab.

**Choose Proxmox if:** You want proper VM isolation, might add more physical nodes later, or already have dedicated storage (NAS). Proxmox excels at managing compute.

## Installing Unraid

1. Download the [Unraid USB Creator](https://unraid.net/download) and flash it to a USB drive (the USB drive becomes the boot device permanently — use a quality one)
2. Boot from the USB — Unraid loads entirely into RAM
3. Access the web UI at `http://tower.local` or the machine's IP
4. Enter your license key (you can start a free trial)
5. Assign drives: select parity drive(s) and data drive(s)
6. Start the array — Unraid formats and initializes the drives

## Running Docker on Unraid

Unraid has a built-in Docker management UI. The Community Applications (CA) plugin is essentially an app store — search for an app (Vaultwarden, Jellyfin, Nextcloud), click install, fill in a few fields, and it pulls and runs the container.

For custom containers, you can add them manually through the UI or use Docker Compose via a plugin. Under the hood it's standard Docker — you can SSH in and use the CLI if you prefer.

## The catch

Unraid is not free. The license costs $59 (Basic, up to 6 drives), $89 (Plus, up to 12), or $129 (Pro, unlimited). It's a one-time purchase with lifetime updates. For what you get — a polished all-in-one OS with excellent community support — most users find it worth the cost.

The other consideration: because Unraid writes each file to a single drive (not striped), read speeds are limited to the speed of that one drive. For media streaming this is fine. For workloads that need high sequential read throughput across large files, traditional RAID or ZFS might be better.

<!-- RESOURCES -->

- [Unraid Documentation](https://docs.unraid.net/) -- type: reference, time: ongoing
- [Unraid Community Forums](https://forums.unraid.net/) -- type: reference, time: ongoing
- [SpaceInvader One YouTube Channel](https://www.youtube.com/@SpaceinvaderOne) -- type: video, time: ongoing

<!-- ZH_SUMMARY -->
Unraid 是一款服务器操作系统，将存储管理、Docker 容器和虚拟机整合在同一个软件包中。你把它安装到 U 盘上，从 U 盘启动，然后通过 Web UI 管理一切。

它与 Proxmox 或裸机 Linux 的不同之处在于存储模型。Unraid 允许你混用不同容量的硬盘——无需成对匹配——并加入奇偶校验保护，让你能在硬盘故障中存活下来。它在媒体服务器搭建者和希望一台机器搞定所有事情的人群中尤其受欢迎。

<!-- ZH_DEEP_DIVE -->
## Unraid 存储的工作原理

传统 RAID 要求使用相同（或相似）的硬盘，并将数据条带化分布到所有硬盘上。Unraid 采用了不同的方式：

**阵列** —— 你的数据盘不会组成条带。每个文件只存放在一块硬盘上，以普通文件系统（XFS 或 BTRFS）写入。你可以从阵列中拔出任意一块硬盘，在另一台 Linux 机器上读取其中的文件。这与 RAID 有本质区别——在 RAID 中，没有任何一块硬盘可以单独读取。

**校验盘** —— 一块或两块硬盘被指定为校验盘。它们存储经过计算的数据，使 Unraid 能够重建任意一块故障硬盘的内容。一块校验盘可防范一块硬盘故障。两块校验盘可防范两块硬盘同时故障。

**混搭** —— 你的数据盘可以容量不同、品牌各异。一块 4TB、一块 8TB 和一块 12TB 可以共存于同一阵列。唯一的规则：每块校验盘的容量必须不小于最大的数据盘。

**缓存池** —— 一块快速 SSD（或 SSD 池）充当写入缓冲区。新文件先写入缓存，然后按计划（“mover”）迁移到阵列。这意味着尽管阵列使用的是较慢的机械硬盘，写入速度依然很快（SSD 速度）。Docker 容器和虚拟机通常运行在缓存池上以获得性能。

## Unraid 与 Proxmox 对比

它们解决不同的问题，各有优势：

| | Unraid | Proxmox |
|---|---|---|
| **主要优势** | 存储管理 | 虚拟化 |
| **存储模型** | 混搭硬盘 + 校验 | 使用底层操作系统所支持的存储 |
| **Docker** | 内置，GUI 管理 | 在虚拟机内运行 |
| **虚拟机** | 通过 KVM/libvirt 支持 | 一等公民，功能完整 |
| **价格** | $59–$129 许可证（一次性） | 免费（开源） |
| **最适合** | 一体化服务器（存储 + 服务） | 多虚拟机环境、集群 |

**选择 Unraid 如果：** 你想要一台机器同时处理存储并运行 Docker 服务，而且你手头有一堆容量不一的硬盘。Unraid 作为单机 homelab 表现出色。

**选择 Proxmox 如果：** 你想要真正的虚拟机隔离，以后可能增加更多物理节点，或者已经有专用存储（NAS）。Proxmox 擅长管理计算资源。

## 安装 Unraid

1. 下载 [Unraid USB Creator](https://unraid.net/download) 并将其刷写到 USB 驱动器（该 USB 驱动器将永久作为启动设备——请使用质量好的）
2. 从 USB 启动——Unraid 完全加载到内存中
3. 通过 `http://tower.local` 或机器 IP 访问 Web UI
4. 输入你的许可证密钥（可以开始免费试用）
5. 分配硬盘：选择校验盘和数据盘
6. 启动阵列——Unraid 会格式化并初始化硬盘

## 在 Unraid 上运行 Docker

Unraid 内置 Docker 管理 UI。Community Applications (CA) 插件本质上是一个应用商店——搜索应用（Vaultwarden、Jellyfin、Nextcloud），点击安装，填写几个字段，它就会拉取并运行容器。

对于自定义容器，你可以通过 UI 手动添加，或通过插件使用 Docker Compose。底层就是标准 Docker——如果你愿意，可以 SSH 登录并使用 CLI。

## 需要注意的地方

Unraid 并非免费。许可证价格为 $59（Basic，最多 6 块硬盘）、$89（Plus，最多 12 块）或 $129（Pro，无限制）。这是一次性购买，包含终身更新。考虑到你得到的东西——一个打磨完善的一体化操作系统，加上出色的社区支持——大多数用户认为物有所值。

另一个考虑因素：由于 Unraid 将每个文件写入单块硬盘（而非条带化），读取速度受限于该单块硬盘的速度。对于媒体流播放来说这没问题。对于需要跨大文件高顺序读取吞吐量的工作负载，传统 RAID 或 ZFS 可能更合适。

<!-- ZH_RESOURCES -->
- [Unraid 文档](https://docs.unraid.net/) -- 类型：参考，时间：持续
- [Unraid 社区论坛](https://forums.unraid.net/) -- 类型：参考，时间：持续
- [SpaceInvader One YouTube 频道](https://www.youtube.com/@SpaceinvaderOne) -- 类型：视频，时间：持续

<!-- ZH_UI -->
1. 理解 Unraid 的存储模型与传统 RAID 的区别
2. 了解何时选择 Unraid 而非 Proxmox + 独立 NAS
3. 安装 Unraid 并配置阵列
4. 通过 Unraid UI 运行第一个 Docker 容器
5. Unraid 已运行——我该如何进入并开始配置？
6. Web UI 已启动，我能看到硬盘。但我想通过 SSH 登录并开始运行服务。Unraid 上如何操作——底层就是 Linux 吗？
