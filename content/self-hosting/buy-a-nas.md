---
id: buy-a-nas
title: Buying a Pre-Built NAS
zone: self-hosting
difficulty: 1
tags:
  - self-hosting
  - storage
  - nas
  - synology
  - qnap
category: concept
milestones:
  - Know what to look for in a pre-built NAS (bays, CPU, RAM)
  - Understand the Synology vs QNAP landscape
  - Set up a NAS and create a shared folder
  - Mount a network share from your server
title_zh: "购买预装 NAS"

---


A pre-built NAS is a small, purpose-built box. You buy the unit, slide in your own hard drives, and follow a setup wizard. Within an hour you have redundant, networked storage with a web UI, mobile apps, and often built-in features like photo management and backup scheduling.

You pay more upfront than building your own, but you get polished software and less tinkering.

<!-- DEEP_DIVE -->

## Synology vs QNAP vs Others

These two dominate the consumer/prosumer NAS market. Both are solid, but the communities lean heavily toward Synology for home use.

**Synology** — Known for DiskStation Manager (DSM), their operating system. It's clean, reliable, and has a large ecosystem of first-party apps (Synology Photos, Hyper Backup, Surveillance Station). The community is huge, which means more guides and troubleshooting help. Downsides: hardware is often underpowered for the price, and they've been pushing their own branded drives.

**QNAP** — Generally better hardware specs per dollar. More flexible for power users — better Docker support, more RAM options, PCIe expansion slots on some models. The software (QTS) is less polished than DSM and has had more security vulnerabilities historically. If you plan to do more than just file sharing, QNAP gives you more room to grow.

**For most people:** If you are unsure, I would say, Synology. The software experience is smoother and you'll spend less time troubleshooting. I personally use Synology and never had a single issue (anecdot, so don't hold me accountable)

## What to look for

**Number of bays** — How many drives it holds. A 2-bay NAS with mirroring gives you the capacity of one drive with redundancy. A 4-bay NAS with RAID 5 gives you three drives of usable space. Start with what you need now; getting a bay or two extra is wise if you think you'll grow.

**CPU** — Matters if you plan to run Docker containers, transcode video (Plex/Jellyfin), or use resource-intensive apps. Intel/AMD CPUs are better for transcoding than ARM-based models. For pure file storage, even an ARM chip is fine.

**RAM** — 2GB works for basic file sharing. If you want to run Docker containers or VMs on the NAS, 4GB minimum, 8GB+ preferred. Some models let you upgrade RAM later, some don't — check before buying.

**Network** — Most NAS devices come with 1GbE. If you're transferring large files regularly (video editing, large media libraries), look for 2.5GbE or 10GbE. For typical homelab use, 1GbE is fine.


## Initial setup

The setup process is similar across brands:

1. Install drives (tool-less trays on most models)
2. Power on and find the NAS on your network (Synology: `find.synology.com`, QNAP: `install.qnap.com`)
3. Follow the web-based wizard — it installs the OS, creates your storage pool, and sets up an admin account
4. Create a shared folder and set permissions
5. Mount the share on your server:

```bash
# NFS mount from Synology/QNAP
sudo apt install nfs-common
sudo mkdir -p /mnt/nas
sudo mount nas-ip:/volume1/shared /mnt/nas

# Add to /etc/fstab for persistence
echo "nas-ip:/volume1/shared /mnt/nas nfs defaults 0 0" | sudo tee -a /etc/fstab
```

## Running Docker on the NAS?

Both Synology and QNAP support Docker containers natively. This can be tempting — run everything on one box. It works for lightweight services, but NAS hardware is usually underpowered compared to a dedicated server. The NAS is best at what it's built for: storing and serving files. Let your server handle the compute.

The exception: if you have a higher-end NAS with a decent CPU and enough RAM, running a few containers (like Plex or a download client) directly on the NAS is perfectly fine and simplifies your setup.

<!-- RESOURCES -->

- [Synology Product Lineup](https://www.synology.com/en-us/products?bays=2,4) -- type: reference, time: 10min
- [QNAP Product Lineup](https://www.qnap.com/en/product?tab=702) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
成品 NAS 是一台小巧的专用设备。你买来整机，插入自己的硬盘，跟着设置向导走一遍。不到一小时，你就能拥有带冗余的网络存储，配有 Web UI、移动应用，通常还内置照片管理、备份计划等功能。

相比自己组装，前期投入更高，但你能得到打磨完善的软件，也省去不少折腾。

<!-- ZH_DEEP_DIVE -->
## Synology vs QNAP vs Others

这两个品牌主导着消费级/准专业级 NAS 市场。两者都很可靠，但社区在家用场景上明显更倾向于 Synology。

**Synology** — 以其操作系统 DiskStation Manager (DSM) 闻名。它简洁、可靠，并拥有庞大的第一方应用生态（Synology Photos、Hyper Backup、Surveillance Station）。社区规模庞大，这意味着有更多的指南和故障排查帮助。缺点：硬件在同价位下往往性能偏弱，而且他们一直在推自家品牌的硬盘。

**QNAP** — 通常每美元能买到更好的硬件规格。对高级用户更灵活——更好的 Docker 支持、更多内存选项、部分型号带 PCIe 扩展插槽。软件（QTS）不如 DSM 精致，历史上也出现过更多安全漏洞。如果你打算做的不仅仅是文件共享，QNAP 给你更多成长空间。

**对大多数人来说：** 如果你拿不准，我会说，选 Synology。软件体验更顺畅，你会花更少时间排查问题。我个人用 Synology，从未出过任何问题（个人经验，所以别拿这个来找我算账）

## 选购要点

**盘位数量** — 能装多少块硬盘。2 盘位 NAS 做镜像后，你得到的是单块硬盘的容量加冗余。4 盘位 NAS 做 RAID 5 后，你得到三块硬盘的可用空间。从你当前的需求起步；如果你觉得自己会扩展，多买一两个盘位是明智的。

**CPU** — 如果你打算运行 Docker 容器、转码视频（Plex/Jellyfin）或使用资源密集型应用，这一点很重要。Intel/AMD CPU 在转码方面优于基于 ARM 的型号。如果只是纯文件存储，即便是 ARM 芯片也够用。

**RAM** — 2GB 足以应付基础文件共享。如果你想在 NAS 上运行 Docker 容器或虚拟机，最低 4GB，最好 8GB 以上。有些型号允许你日后升级内存，有些则不行——购买前先确认。

**网络** — 大多数 NAS 设备配备 1GbE。如果你经常传输大文件（视频剪辑、大型媒体库），可以寻找 2.5GbE 或 10GbE。对于典型的 homelab 用途，1GbE 就足够了。


## 初始设置

各品牌的设置流程大同小异：

1. 安装硬盘（大多数型号为免工具托盘）
2. 开机并在网络上找到 NAS（Synology：`find.synology.com`，QNAP：`install.qnap.com`）
3. 按照基于 Web 的向导操作——它会安装操作系统、创建存储池并设置管理员账户
4. 创建共享文件夹并设置权限
5. 在你的服务器上挂载共享：

```bash
# NFS mount from Synology/QNAP
sudo apt install nfs-common
sudo mkdir -p /mnt/nas
sudo mount nas-ip:/volume1/shared /mnt/nas

# Add to /etc/fstab for persistence
echo "nas-ip:/volume1/shared /mnt/nas nfs defaults 0 0" | sudo tee -a /etc/fstab
```

## 在 NAS 上运行 Docker？

Synology 和 QNAP 都原生支持 Docker 容器。这很诱人——把所有东西都跑在一台机器上。对于轻量级服务可行，但 NAS 硬件通常比专用服务器性能弱。NAS 最擅长的是它被设计来做的事：存储和提供文件服务。让服务器来处理计算。

例外情况：如果你有一台更高端的 NAS，配备不错的 CPU 和足够的内存，直接在 NAS 上运行几个容器（比如 Plex 或下载客户端）完全没问题，还能简化你的设置。

<!-- ZH_RESOURCES -->
- [Synology 产品线](https://www.synology.com/en-us/products?bays=2,4) -- 类型：参考，时间：10 分钟
- [QNAP 产品线](https://www.qnap.com/en/product?tab=702) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 了解选购成品 NAS 时应关注哪些方面（盘位、CPU、内存）
2. 理解群晖与威联通的产品格局
3. 配置 NAS 并创建共享文件夹
4. 从服务器挂载网络共享
