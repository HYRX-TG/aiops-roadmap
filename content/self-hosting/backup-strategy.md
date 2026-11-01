---
id: backup-strategy
title: You Need Backups — Here's How to Think About It
zone: self-hosting
edges:
  to:
    - id: proxmox-backup-server
      question: I'm running Proxmox — can I back up my entire VMs?
      detail: >-
        I have everything in VMs and containers on Proxmox. If I could just
        snapshot the whole thing and restore it if something goes wrong, that
        would be way easier than backing up individual files inside each VM.
    - id: rsync-backups
      question: I just want to copy my important files to another machine
      detail: >-
        I know which folders matter — my Docker volumes, my configs, my
        databases. I just need a reliable way to copy them somewhere else
        on a schedule. What's the simplest way to do that?
    - id: cloud-backups
      question: What if something happens to my house? I need a copy somewhere else
      detail: >-
        A backup on another drive in the same room doesn't help if there's a
        fire or a break-in. How do I get a copy of my data somewhere offsite
        without it costing a fortune?
difficulty: 1
tags:
  - self-hosting
  - backups
  - data-protection
  - 3-2-1
category: concept
milestones:
  - Understand the 3-2-1 backup rule
  - Know what to back up (configs, volumes, databases — not the containers themselves)
  - Think about how much data loss you can tolerate
  - Pick a backup approach that fits your setup
title_zh: "你需要备份——以下是如何看待它"

---


You've been building your self-hosted setup — Vaultwarden, maybe Immich, maybe Jellyfin. Your passwords are in there. Your photos are in there. And right now, all of it lives on one disk in one machine. If that disk dies tonight, it's all gone.

Backups are the thing everyone knows they should do and nobody does until they lose something. Let's fix that before it happens.

<!-- DEEP_DIVE -->

## The 3-2-1 rule

The simplest backup strategy that actually works:

- **3** copies of your data (the original + 2 backups)
- **2** different types of storage (e.g., your server's SSD + an external drive or NAS)
- **1** copy offsite (somewhere physically different — a cloud provider, a friend's house)

You don't need all three on day one. A single backup to another machine in your house is already infinitely better than nothing. But the goal is to get to 3-2-1 over time.

## What to back up

Not everything on your server is equally important, and you don't need to back up the entire filesystem.

**Always back up:**
- Docker volumes (your actual data — Vaultwarden's `/data`, Immich's library, database files)
- Docker Compose files and `.env` files (your service configuration)
- Any config files you've customized (`traefik.yml`, `prometheus.yml`, etc.)

**Don't bother backing up:**
- Docker images — they're pulled from registries, not unique to you
- The OS itself — reinstalling Debian takes 10 minutes
- Log files — nice to have but rarely critical

**Special case — databases:**
Don't just copy a running database's files. A SQLite file might be fine, but PostgreSQL or MariaDB files copied mid-write can be corrupted. Dump the database first (`pg_dump`, `mysqldump`), then back up the dump.

## How much can you afford to lose?

Think about this honestly. If your backup runs once a day at midnight, and your server dies at 11pm, you lose almost 24 hours of data. For a password manager, that might be one or two new entries. For a photo library, it could be a day's worth of photos.

For most self-hosters, daily backups are fine. If you're running something where losing even an hour matters, you need more frequent backups — but that's rare for home use.

## The approaches

There are three main paths, and they're not mutually exclusive — most solid setups combine two or three:

**Proxmox Backup Server** — If you're running Proxmox, PBS backs up entire VMs and containers at the hypervisor level. Incremental, deduplicated, and restores the whole machine state. The easiest "back up everything" approach if you're in the Proxmox ecosystem.

**rsync** — The universal file-level backup tool. Copy specific directories to another machine on your network, a NAS, or an external drive. Simple, scriptable, works everywhere. This is the right tool when you know exactly what files matter.

**Cloud/offsite backups** — Get a copy out of your house entirely. Backblaze B2, rsync.net, Hetzner Storage Box — all cheap for the amount of data most self-hosters have. Tools like restic and rclone make this straightforward and encrypted.

Pick the one that matches where you are right now. You can always add the others later.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你一直在搭建自己的自托管环境——Vaultwarden，也许还有 Immich，也许还有 Jellyfin。你的密码在里面。你的照片在里面。而现在，这一切都存放在一台机器的一块磁盘上。如果那块磁盘今晚坏了，一切就都没了。

备份是每个人都知道应该做、却没人去做的事，直到他们丢了东西才后悔。让我们在事情发生之前把它解决掉。

<!-- ZH_DEEP_DIVE -->
## 3-2-1 原则

真正有效的最简单备份策略：

- 数据的 **3** 份副本（原始数据 + 2 份备份）
- **2** 种不同类型的存储（例如，服务器的 SSD + 外置硬盘或 NAS）
- **1** 份异地副本（物理位置不同的地方——云服务商、朋友家）

你不需要在第一天就做到全部三点。仅仅把数据备份到家里的另一台机器上，就已经比什么都不做强无数倍。但目标是在时间推移中逐步达到 3-2-1。

## 需要备份什么

服务器上的东西并非同等重要，你也不需要备份整个文件系统。

**始终备份：**
- Docker 卷（你的实际数据——Vaultwarden 的 `/data`、Immich 的图库、数据库文件）
- Docker Compose 文件和 `.env` 文件（你的服务配置）
- 你自定义过的任何配置文件（`traefik.yml`、`prometheus.yml` 等）

**不必费心备份：**
- Docker 镜像——它们从镜像仓库拉取，并非你独有
- 操作系统本身——重装 Debian 只需 10 分钟
- 日志文件——有则更好，但很少是关键

**特殊情况——数据库：**
不要直接复制正在运行的数据库文件。SQLite 文件可能没问题，但 PostgreSQL 或 MariaDB 的文件在写入过程中被复制可能会损坏。先导出数据库（`pg_dump`、`mysqldump`），然后备份导出文件。

## 你能承受丢失多少数据？

诚实地想一想。如果你的备份每天午夜运行一次，而服务器在晚上 11 点宕机，你会丢失近 24 小时的数据。对于密码管理器，这可能是一两条新条目。对于照片库，可能是一整天的照片。

对大多数自托管用户来说，每日备份就够了。如果你运行的东西哪怕丢失一小时都很要紧，那就需要更频繁的备份——但这在家庭使用中很少见。

## 可选方案

主要有三条路径，它们并不互斥——大多数可靠的方案会结合两到三种：

**Proxmox Backup Server**——如果你运行 Proxmox，PBS 在 hypervisor 层面备份整个虚拟机和容器。增量、去重，并能恢复整台机器的状态。如果你身处 Proxmox 生态，这是最简单的“备份一切”方案。

**rsync**——通用的文件级备份工具。把特定目录复制到网络上的另一台机器、NAS 或外置硬盘。简单、可脚本化、随处可用。当你确切知道哪些文件重要时，这就是正确的工具。

**云/异地备份**——把副本完全放到家外。Backblaze B2、rsync.net、Hetzner Storage Box——对于大多数自托管用户的数据量来说都很便宜。restic 和 rclone 这类工具让这件事变得简单且加密。

选择与你当前情况相符的那一个。你随时可以之后再添加其他方案。

<!-- ZH_UI -->
1. 理解 3-2-1 备份原则
2. 明确要备份什么（配置、卷、数据库——而不是容器本身）
3. 考虑你能容忍多少数据丢失
4. 选择适合你环境的备份方案
5. 我在用 Proxmox——能备份整个虚拟机吗？
6. 我在 Proxmox 上的虚拟机和容器里放了一切。如果我能对整个东西做快照，出问题时再恢复，那会比备份每个虚拟机里的单个文件简单得多。
7. 我只想把重要文件复制到另一台机器
8. 我知道哪些文件夹重要——我的 Docker 卷、配置、数据库。我只需要一种可靠的方式，按计划把它们复制到别处。最简单的方法是什么？
9. 如果我家出事了怎么办？我需要一份放在别处的副本
10. 同一房间另一块硬盘上的备份，遇到火灾或入室盗窃就没用了。怎样才能把数据副本放到异地，又不用花大钱？
