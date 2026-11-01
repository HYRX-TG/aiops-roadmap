---
id: proxmox-backup-server
title: Proxmox Backup Server
zone: self-hosting
edges:
  to:
    - id: cloud-backups
      question: This covers local backups — but what about offsite?
      detail: >-
        PBS backs up my VMs to another machine on my network, but that's
        still in my house. If I want a copy somewhere else entirely, how
        do I do that?
difficulty: 2
tags:
  - self-hosting
  - backups
  - proxmox
  - pbs
category: tool
milestones:
  - Understand what Proxmox Backup Server does and how it integrates with Proxmox VE
  - Install PBS (on a separate machine or VM)
  - Configure a backup job for your VMs and containers
  - Test restoring a VM from backup
title_zh: "Proxmox 备份服务器"

---


Proxmox Backup Server (PBS) is Proxmox's dedicated backup solution. It integrates directly with Proxmox VE — you add it as a storage target and schedule backup jobs from the same web UI you already use to manage your VMs. Backups are incremental and deduplicated, so after the first full backup, subsequent runs are fast and space-efficient.

If you're running Proxmox, this is the most natural way to back up your entire setup.

<!-- DEEP_DIVE -->

## What PBS actually does

PBS backs up at the VM/container level. When you back up a VM, it captures the entire disk image — the OS, your Docker setup, your volumes, everything. When you restore, you get the whole VM back exactly as it was. No need to figure out which files to back up or worry about database consistency — the snapshot is atomic.

It's also smart about storage. After the initial full backup, PBS uses changed-block tracking to only transfer what's different. Deduplication means identical blocks across multiple VMs are stored only once. A typical homelab with a few VMs might use surprisingly little backup space.

## Where to install PBS

PBS needs to run somewhere separate from what it's backing up. Options:

**A separate physical machine** — Ideal. An old laptop or mini PC with a large disk works perfectly. If your main Proxmox host dies, your backups are on a completely independent machine.

**A VM on the same Proxmox host** — Works, but understand the limitation: if the host's disk fails, you lose both the VMs and the backups. This is still useful for protecting against accidental deletions and botched upgrades, just not hardware failure. Pair it with offsite backups to cover that gap.

**On your NAS** — If you have a NAS that can run PBS (TrueNAS can run it in a VM or jail), this gives you both separation and redundant storage. I personally do this. I run PBS on a VM in my Synology NAS

## Setting it up

Install PBS from the [official ISO](https://www.proxmox.com/en/downloads) the same way you installed Proxmox VE — flash to USB, boot, install. It gets its own web UI on port 8007.

Once PBS is running:

1. **Create a datastore** in the PBS web UI — this is where backups are stored. Point it at a directory with enough space.

2. **Add PBS as storage in Proxmox VE** — In your Proxmox VE web UI, go to Datacenter → Storage → Add → Proxmox Backup Server. Enter the PBS IP, credentials, and datastore name.

3. **Schedule backup jobs** — Datacenter → Backup → Add. Select which VMs/containers to back up, the schedule (daily is typical), and retention policy (how many backups to keep).

That's it. Backups run automatically on schedule.

## Retention and pruning

PBS lets you define retention policies: keep the last 7 daily backups, the last 4 weekly, the last 6 monthly — whatever makes sense for you. Old backups are pruned automatically. A reasonable starting point:

- Keep last 3 daily
- Keep last 2 weekly
- Keep last 1 monthly

You can always adjust once you see how much space you're using.

## Testing restores

A backup you've never tested is a backup you can't trust. After your first backup completes, try restoring a VM to verify it works. In Proxmox VE, go to the backup storage, select a backup, and click Restore. You can restore to a new VM ID so you don't overwrite the running one.

Do this once. It takes five minutes and saves you from finding out your backups are broken when you actually need them.

<!-- RESOURCES -->

- [Proxmox Backup Server Documentation](https://pbs.proxmox.com/docs/) -- type: reference, time: ongoing
- [PBS Installation Guide](https://pbs.proxmox.com/docs/installation.html) -- type: guide, time: 30min

<!-- ZH_SUMMARY -->
Proxmox Backup Server（PBS）是 Proxmox 的专用备份解决方案。它直接与 Proxmox VE 集成——你只需将其添加为存储目标，并在你原本用于管理虚拟机的同一个 Web UI 中安排备份任务。备份是增量式且去重的，因此在首次完整备份之后，后续运行既快速又节省空间。

如果你正在运行 Proxmox，这是备份整个环境最自然的方式。

<!-- ZH_DEEP_DIVE -->
## PBS 的实际作用

PBS 在 VM/容器层面进行备份。当你备份一台 VM 时，它会捕获整个磁盘镜像——操作系统、你的 Docker 环境、你的卷，所有内容。恢复时，你会得到与原来完全一致的整台 VM。无需费心确定要备份哪些文件，也不必担心数据库一致性——快照是原子性的。

它在存储方面也很智能。在首次完整备份之后，PBS 使用变更块跟踪，只传输有差异的部分。去重意味着多台 VM 之间的相同块只存储一次。一个拥有几台 VM 的典型家庭实验室可能只占用少得惊人的备份空间。

## PBS 安装在哪里

PBS 需要运行在与其所备份内容相互独立的地方。可选方案：

**一台独立的物理机** —— 理想选择。一台带大容量磁盘的旧笔记本或迷你主机就完全够用。如果你的主 Proxmox 主机挂了，你的备份在一台完全独立的机器上。

**同一台 Proxmox 主机上的 VM** —— 可行，但要理解其局限：如果主机的磁盘故障，你会同时失去 VM 和备份。这对于防范误删除和搞砸的升级仍然有用，只是无法应对硬件故障。搭配异地备份来弥补这一缺口。

**在你的 NAS 上** —— 如果你有一台能运行 PBS 的 NAS（TrueNAS 可以在 VM 或 jail 中运行它），这样既能实现隔离，又能获得冗余存储。我个人就是这么做的。我在 Synology NAS 上的一台 VM 中运行 PBS

## 进行设置

从[官方 ISO](https://www.proxmox.com/en/downloads) 安装 PBS，方式与你安装 Proxmox VE 相同——刷写到 USB、启动、安装。它会拥有自己的 Web UI，端口为 8007。

PBS 运行起来后：

1. **在 PBS Web UI 中创建一个 datastore** —— 这是存储备份的地方。将其指向一个空间充足的目录。

2. **在 Proxmox VE 中将 PBS 添加为存储** —— 在你的 Proxmox VE Web UI 中，进入 Datacenter → Storage → Add → Proxmox Backup Server。输入 PBS 的 IP、凭据和 datastore 名称。

3. **安排备份任务** —— Datacenter → Backup → Add。选择要备份的 VM/容器、计划（通常为每日）和保留策略（保留多少份备份）。

就这样。备份会按计划自动运行。

## 保留与清理

PBS 允许你定义保留策略：保留最近 7 份每日备份、最近 4 份每周备份、最近 6 份每月备份——随你合理设定。旧备份会被自动清理。一个合理的起点：

- 保留最近 3 份每日备份
- 保留最近 2 份每周备份
- 保留最近 1 份每月备份

等你看到实际占用了多少空间后，随时可以调整。

## 测试恢复

从未测试过的备份，是你无法信任的备份。首次备份完成后，尝试恢复一台 VM 以验证其可用。在 Proxmox VE 中，进入备份存储，选择一份备份，点击 Restore。你可以恢复到新的 VM ID，这样就不会覆盖正在运行的 VM。

做一次。只需五分钟，就能避免你在真正需要备份时才发现备份是坏的。

<!-- ZH_RESOURCES -->
- [Proxmox Backup Server 文档](https://pbs.proxmox.com/docs/) -- 类型：参考，时间：持续
- [PBS 安装指南](https://pbs.proxmox.com/docs/installation.html) -- 类型：指南，时间：30 分钟

<!-- ZH_UI -->
1. 了解 Proxmox Backup Server 的作用及其与 Proxmox VE 的集成方式
2. 安装 PBS（在独立机器或虚拟机上）
3. 为虚拟机和容器配置备份任务
4. 测试从备份恢复虚拟机
5. 这涵盖了本地备份——但异地备份怎么办？
6. PBS 将我的虚拟机备份到网络上的另一台机器，但那仍在我家里。如果我想在完全不同的地方保留一份副本，该怎么做？
