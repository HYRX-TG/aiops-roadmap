---
id: storage-planning
title: Where Does All This Data Go?
zone: self-hosting
edges:
  to:
    - id: build-a-nas
      question: I want to build my own storage server from spare parts
      detail: >-
        I have an old PC sitting around and some drives. Can I turn that into
        a proper storage box? What software do I put on it, and how do I make
        sure I don't lose data if a drive dies?
    - id: buy-a-nas
      question: I'd rather just buy something that works out of the box
      detail: >-
        I don't want another project — I want to plug something in, put drives
        in it, and have it work. What should I be looking at and how much is
        this going to cost me?
difficulty: 1
tags:
  - self-hosting
  - storage
  - nas
  - data
category: concept
milestones:
  - Understand why separating storage from compute matters
  - Know the difference between DAS, NAS, and just using local disks
  - Decide whether to build, buy, or keep it simple
title_zh: "所有这些数据都去了哪里？"

---


Right now your data lives on the same disk your server boots from. Docker volumes, photos, media files, databases — all sharing space with the OS. This works fine when you're starting out, but it has problems that show up over time.

The disk fills up. You can't easily move data to a bigger drive. If the disk fails, you lose everything — the OS and your data. And if you want a second server, there's no shared storage between them.

Separating storage from compute solves all of these. Your server runs services, your storage holds data, and they talk over the network.

<!-- DEEP_DIVE -->

## Do you actually need a NAS?

Not everyone does. If you have a single server with a few small services (Vaultwarden, Pi-hole, a small Nextcloud), the boot disk is fine. Add a second internal drive if you need more space and mount it for your Docker volumes. That's perfectly valid and much simpler than a NAS.

A dedicated storage device starts making sense when:

- You have more data than fits on one or two drives
- You want redundancy (a drive can fail without losing data)
- Multiple machines need access to the same files
- You're running a media server with a large library

## How NAS storage works

A NAS (Network Attached Storage) is a dedicated machine — purpose-built or repurposed — that serves files over the network. Your server mounts a network share (NFS or SMB) and reads/writes to it as if it were a local directory.

From your Docker containers' perspective, nothing changes. You point a volume at the mounted share instead of a local directory. The data lives on the NAS, which has its own redundancy and can be backed up independently.

## RAID: redundancy, not backup

Most NAS setups use some form of RAID — multiple disks working together so that one (or more) can fail without data loss. Common options:

- **Mirror (RAID 1)** — two disks, identical copies. One fails, the other has everything. You lose half your total capacity.
- **RAID 5 / RAIDZ1** — three or more disks, one can fail. Better capacity efficiency than mirroring.
- **RAID 6 / RAIDZ2** — four or more disks, two can fail. More protection, more overhead.

**RAID is not a backup.** It protects against a single disk failing. It does not protect against accidental deletion, ransomware, fire, or the RAID controller itself failing. You still need backups.

## The two paths

**Build a NAS** — Take an old PC, add drives, install TrueNAS or OpenMediaVault. More work, more control, cheaper if you already have spare hardware. You learn a lot in the process.

**Buy a NAS** — Synology, QNAP, or similar. Pop in drives, follow the setup wizard, done. Costs more upfront but saves time and comes with polished software for file sharing, photo management, and more.

Neither is objectively better. It depends on whether you want another project or just want storage that works.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
目前你的数据与服务器启动盘存放在同一块磁盘上。Docker 卷、照片、媒体文件、数据库——全都与操作系统共享空间。刚开始时这没问题，但随着时间推移会暴露出一些问题。

磁盘会被占满。你无法轻松将数据迁移到更大的硬盘。如果磁盘故障，你会丢失一切——操作系统和你的数据。而且如果你想要第二台服务器，它们之间没有共享存储。

将存储与计算分离可以解决所有这些问题。服务器运行服务，存储保存数据，二者通过网络通信。

<!-- ZH_DEEP_DIVE -->
## 你真的需要 NAS 吗？

并非所有人都需要。如果你只有一台服务器运行几个小服务（Vaultwarden、Pi-hole、一个小型 Nextcloud），启动盘就足够了。如果需要更多空间，加一块内置硬盘并挂载给 Docker 卷使用即可。这完全可行，而且比 NAS 简单得多。

专用存储设备在以下情况下才开始有意义：

- 你的数据量超过一两块硬盘的容量
- 你需要冗余（一块硬盘故障时数据不丢失）
- 多台机器需要访问相同的文件
- 你运行着媒体库庞大的媒体服务器

## NAS 存储的工作原理

NAS（Network Attached Storage，网络附加存储）是一台专用机器——无论是专门打造的还是旧设备改造的——通过网络提供文件服务。你的服务器挂载一个网络共享（NFS 或 SMB），然后像访问本地目录一样读写它。

从 Docker 容器的角度看，一切都没有变化。你把卷指向挂载的共享，而不是本地目录。数据存放在 NAS 上，NAS 自带冗余，可以独立备份。

## RAID：冗余，而非备份

大多数 NAS 配置都使用某种形式的 RAID——多块硬盘协同工作，使得一块（或多块）硬盘故障时数据不丢失。常见选项：

- **镜像（RAID 1）**——两块硬盘，内容完全相同。一块故障，另一块拥有全部数据。你损失一半的总容量。
- **RAID 5 / RAIDZ1**——三块或更多硬盘，允许一块故障。容量效率优于镜像。
- **RAID 6 / RAIDZ2**——四块或更多硬盘，允许两块故障。保护更强，开销更大。

**RAID 不是备份。** 它能防止单块硬盘故障，但无法防止误删除、勒索软件、火灾，或 RAID 控制器本身故障。你仍然需要备份。

## 两条路径

**自建 NAS**——拿一台旧 PC，加上硬盘，安装 TrueNAS 或 OpenMediaVault。工作量更大，控制力更强，如果你已有闲置硬件则更便宜。过程中能学到很多东西。

**购买 NAS**——Synology、QNAP 或类似产品。装上硬盘，跟着设置向导走，搞定。前期成本更高，但节省时间，并附带打磨完善的软件，用于文件共享、照片管理等。

两者没有客观上的优劣。取决于你是想再做一个项目，还是只想要能用的存储。

<!-- ZH_UI -->
1. 理解存储与计算分离为何重要
2. 了解 DAS、NAS 与直接使用本地磁盘的区别
3. 决定是自建、购买还是保持简单
4. 我想用 spare parts 自建存储服务器
5. 我有一台闲置的旧 PC 和一些硬盘。我能把它变成一台像样的存储设备吗？该装什么软件，以及如何确保硬盘坏了也不丢数据？
6. 我更愿意直接买开箱即用的产品
7. 我不想再折腾一个项目——我只想插上电、装上硬盘就能用。我该看哪些产品，大概要花多少钱？
