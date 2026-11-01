---
id: build-a-nas
title: Building a NAS from Scratch
zone: self-hosting
difficulty: 2
tags:
  - self-hosting
  - storage
  - nas
  - truenas
  - zfs
category: practice
milestones:
  - Understand RAID levels and why RAID is not a backup
  - Know the difference between TrueNAS and OpenMediaVault
  - Set up a basic NAS with redundant storage
  - Mount a network share from your server
title_zh: "从零构建 NAS"

---


Building your own NAS means taking a machine — an old PC, a mini server, or purpose-built hardware — adding drives to it, and installing NAS software that manages the storage, shares it over the network, and handles redundancy.

It's more hands-on than buying a Synology, but it's cheaper, more flexible, and you end up understanding exactly how your storage works.

<!-- DEEP_DIVE -->

## What hardware do you need?

**The machine** — Any PC with enough SATA ports for your drives works. An old desktop is fine. If you're buying specifically for this, a used mini server or a case with many drive bays is ideal. You don't need a powerful CPU — NAS workloads are mostly I/O, not compute.

**RAM** — 8GB minimum. If you're using ZFS (which you should consider), more RAM helps — ZFS uses RAM for caching (ARC). 16GB is comfortable for a homelab NAS.

**The ECC debate** — ECC (Error-Correcting Code) RAM catches and fixes memory bit flips. ZFS purists will tell you it's mandatory. In practice, non-ECC RAM works fine for a homelab. ECC is nice to have, not a dealbreaker. I personally don't have any ECC RAM.

**Drives** — NAS-rated drives (WD Red Plus, Seagate IronWolf) are designed for 24/7 operation and vibration tolerance in multi-drive setups. They cost a bit more than desktop drives but last longer in NAS use. For a homelab, regular drives work too — just keep backups.

**HBA cards** — If your motherboard doesn't have enough SATA ports, a Host Bus Adapter adds more. Look for cards based on the LSI SAS2008 chipset (commonly Dell H200, H310 flashed to IT mode). They're cheap on eBay and well-supported.

## TrueNAS vs OpenMediaVault

**TrueNAS (SCALE)** — Based on Debian Linux with ZFS as the filesystem. ZFS gives you data integrity verification, snapshots, compression, and flexible RAID (RAIDZ). TrueNAS has a polished web UI for managing pools, shares, snapshots, and even Docker containers and VMs. The downside: ZFS wants more RAM and has a learning curve.

**OpenMediaVault (OMV)** — Debian-based, lighter weight, works with traditional Linux filesystems (ext4, XFS) and mdadm software RAID. Simpler to set up, lower resource requirements, plugin-based. A good choice if you want a straightforward NAS without the ZFS complexity.

**The recommendation:** If you have 16GB+ RAM and want the best data protection, TrueNAS with ZFS. If you have limited hardware or just want simple network shares, OpenMediaVault.

## Setting up TrueNAS SCALE

1. Download the [TrueNAS SCALE ISO](https://www.truenas.com/download-truenas-scale/) and flash it to USB
2. Install it — it takes over the boot drive (use a small SSD, not one of your data drives)
3. Access the web UI at the machine's IP address
4. Create a **storage pool** — select your data drives and choose a RAID level:
   - 2 drives → Mirror (RAIDZ is not an option with only 2 drives)
   - 3 drives → RAIDZ1 (one drive can fail)
   - 4+ drives → RAIDZ2 (two drives can fail) recommended

5. Create a **dataset** — a logical partition within the pool
6. Create an **NFS or SMB share** pointing to the dataset

## Mounting the share on your server

On your Docker server, mount the NAS share so containers can use it:

```bash
# Install NFS client
sudo apt install nfs-common

# Create a mount point
sudo mkdir -p /mnt/nas

# Mount the NFS share
sudo mount nas-ip:/mnt/pool/dataset /mnt/nas

# Make it permanent (add to /etc/fstab)
echo "nas-ip:/mnt/pool/dataset /mnt/nas nfs defaults 0 0" | sudo tee -a /etc/fstab
```

Now point your Docker volumes at `/mnt/nas/` subdirectories:

```yaml
services:
  jellyfin:
    volumes:
      - /mnt/nas/media:/media:ro
```

## ZFS snapshots

One of ZFS's best features: you can take instant, space-efficient snapshots of your data. Before a risky operation, snapshot. If something goes wrong, roll back in seconds. TrueNAS can schedule automatic snapshots — daily or hourly — as cheap insurance.

Snapshots are not backups (they're on the same disks), but they protect against accidental deletion and bad updates.

<!-- RESOURCES -->

- [TrueNAS SCALE Documentation](https://www.truenas.com/docs/scale/) -- type: reference, time: ongoing
- [OpenMediaVault Documentation](https://docs.openmediavault.org/) -- type: reference, time: ongoing

<!-- ZH_SUMMARY -->
搭建自己的 NAS 意味着拿一台机器——一台旧 PC、一台迷你服务器，或专用硬件——给它加上硬盘，并安装 NAS 软件来管理存储、通过网络共享存储并处理冗余。

这比买一台群晖更费手，但更便宜、更灵活，而且你最终会完全理解你的存储是如何工作的。

<!-- ZH_DEEP_DIVE -->
## 你需要什么硬件？

**机器** —— 任何有足够 SATA 端口连接硬盘的 PC 都可以。一台旧台式机就行。如果你是专门为此购买，二手迷你服务器或多盘位机箱是理想选择。你不需要强大的 CPU —— NAS 工作负载主要是 I/O，而不是计算。

**内存** —— 最低 8GB。如果你使用 ZFS（你应该考虑），更多内存会有帮助 —— ZFS 使用内存做缓存（ARC）。16GB 对于家庭实验室 NAS 来说比较舒适。

**ECC 之争** —— ECC（纠错码）内存可以捕获并修复内存位翻转。ZFS 纯粹主义者会告诉你这是必须的。实际上，非 ECC 内存对于家庭实验室完全够用。ECC 有更好，但不是决定性因素。我个人就没有任何 ECC 内存。

**硬盘** —— NAS 级硬盘（WD Red Plus、Seagate IronWolf）专为 24/7 运行和多盘位环境下的振动耐受性而设计。它们比台式机硬盘贵一些，但在 NAS 使用中寿命更长。对于家庭实验室，普通硬盘也可以 —— 只要做好备份。

**HBA 卡** —— 如果你的主板没有足够的 SATA 端口，主机总线适配器可以增加更多端口。寻找基于 LSI SAS2008 芯片组的卡（常见的有 Dell H200、H310 刷成 IT 模式）。它们在 eBay 上很便宜，且支持良好。

## TrueNAS vs OpenMediaVault

**TrueNAS (SCALE)** —— 基于 Debian Linux，使用 ZFS 作为文件系统。ZFS 为你提供数据完整性验证、快照、压缩和灵活的 RAID（RAIDZ）。TrueNAS 有精致的 Web UI，用于管理存储池、共享、快照，甚至 Docker 容器和虚拟机。缺点是：ZFS 需要更多内存，且有学习曲线。

**OpenMediaVault (OMV)** —— 基于 Debian，更轻量，支持传统 Linux 文件系统（ext4、XFS）和 mdadm 软件 RAID。设置更简单，资源需求更低，基于插件。如果你想要一个简单直接的 NAS 而不想面对 ZFS 的复杂性，这是个好选择。

**建议：** 如果你有 16GB+ 内存并且想要最好的数据保护，选择 TrueNAS 搭配 ZFS。如果你硬件有限或只想要简单的网络共享，选择 OpenMediaVault。

## 设置 TrueNAS SCALE

1. 下载 [TrueNAS SCALE ISO](https://www.truenas.com/download-truenas-scale/) 并将其刷入 USB
2. 安装它 —— 它会占用启动盘（使用一个小 SSD，不要用你的数据盘之一）
3. 通过机器的 IP 地址访问 Web UI
4. 创建**存储池** —— 选择你的数据盘并选择 RAID 级别：
   - 2 块盘 → Mirror（只有 2 块盘时 RAIDZ 不是选项）
   - 3 块盘 → RAIDZ1（允许一块盘故障）
   - 4+ 块盘 → 推荐 RAIDZ2（允许两块盘故障）

5. 创建**数据集** —— 存储池内的逻辑分区
6. 创建指向该数据集的 **NFS 或 SMB 共享**

## 在你的服务器上挂载共享

在你的 Docker 服务器上，挂载 NAS 共享以便容器可以使用它：

```bash
# Install NFS client
sudo apt install nfs-common

# Create a mount point
sudo mkdir -p /mnt/nas

# Mount the NFS share
sudo mount nas-ip:/mnt/pool/dataset /mnt/nas

# Make it permanent (add to /etc/fstab)
echo "nas-ip:/mnt/pool/dataset /mnt/nas nfs defaults 0 0" | sudo tee -a /etc/fstab
```

现在将你的 Docker 卷指向 `/mnt/nas/` 子目录：

```yaml
services:
  jellyfin:
    volumes:
      - /mnt/nas/media:/media:ro
```

## ZFS 快照

ZFS 最好的功能之一：你可以对数据拍摄即时、空间高效的快照。在进行有风险的操作之前，先拍快照。如果出了问题，几秒钟内就能回滚。TrueNAS 可以安排自动快照 —— 每天或每小时 —— 作为廉价的保险。

快照不是备份（它们在同一块磁盘上），但它们可以防止意外删除和糟糕的更新。

<!-- ZH_RESOURCES -->
- [TrueNAS SCALE 文档](https://www.truenas.com/docs/scale/) -- 类型：参考，时间：持续
- [OpenMediaVault 文档](https://docs.openmediavault.org/) -- 类型：参考，时间：持续

<!-- ZH_UI -->
1. 理解 RAID 级别以及为什么 RAID 不是备份
2. 了解 TrueNAS 与 OpenMediaVault 的区别
3. 用冗余存储搭建一个基础 NAS
4. 从你的服务器挂载网络共享
