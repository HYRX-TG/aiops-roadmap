---
id: what-is-virtualization
title: What Is Virtualization?
zone: self-hosting
edges:
  to:
    - id: install-proxmox
      question: Proxmox sounds good — I'll use that
      detail: >-
        Will it wipe what's currently on the machine? And after it's installed,
        how do I actually get a working Linux system I can SSH into and run
        things on?
    - id: bare-metal-linux
      question: I don't want virtualization — just Linux directly on the hardware
      detail: >-
        I don't need VMs for what I'm doing right now. But am I going to regret
        this later? What am I actually giving up by skipping virtualization?
    - id: unraid
      question: I want storage, VMs, and Docker all in one — is there something for that?
      detail: >-
        I keep hearing about Unraid. It sounds like it handles storage and
        runs containers and VMs too. Is it an alternative to Proxmox or
        something different entirely?
difficulty: 1
tags:
  - self-hosting
  - virtualization
  - proxmox
  - vms
  - hypervisor
category: concept
milestones:
  - Understand what a hypervisor does
  - Know why Proxmox is recommended over bare metal for homelabs
  - 'Make the call: Proxmox or bare metal'
title_zh: "什么是虚拟化？"

---


Virtualization means running multiple isolated operating systems on a single physical machine. Instead of installing Linux directly on your hardware, you install a **hypervisor** — software that manages the hardware and runs virtual machines (VMs) on top of it.

Each VM is a fully isolated system: its own kernel, its own processes, its own network interface. From inside the VM, it looks and behaves exactly like a real machine. From the hypervisor's perspective, it's just a process it controls.

<!-- DEEP_DIVE -->

## Why would you want this for a homelab?

You might be thinking: "I'm running everything in Docker anyway, doesn't that already isolate my services?" It does — but that's not why Virtualization (Example: Proxmox) is worth it. The real reasons are about what happens to the machine itself.

### Snapshots and backups

This is the biggest one. Before you do anything risky — try a new configuration, mess with networking — you take a snapshot. If something breaks, you restore. The whole VM state, including the OS and all your Docker volumes, is back exactly as it was. On bare metal, "backup" means figuring out your own rsync scripts. In Proxmox, it's one click.

### Safe experimentation

Want to try something new — a different service, a beta version, a config change you're unsure about? Spin up a new VM. Break it, learn from it, delete it. Your running services on other VMs are completely untouched. On bare metal, experimenting on your production server means you're gambling with your uptime.

### Logical grouping, not one-VM-per-service

You don't run one VM per Docker container — that defeats the purpose. A realistic setup: one VM for your stable, always-on services (Vaultwarden, Immich, Jellyfin), and a separate VM for things you're actively tinkering with. Or one VM you leave alone for months at a time, another you upgrade aggressively. The boundary is between groups of services that have different risk profiles, not individual apps.

### Resource limits and flexibility

You can cap how much CPU and RAM each VM can use. If one service starts misbehaving — a runaway process, a Jellyfin transcode job eating everything — it can't starve the rest of your server.

You can also resize on the fly: give a VM more RAM when a service needs it, shrink it back when you're done. And when you outgrow a single machine, clustering lets you add another node and live-migrate VMs to it — no downtime, no reinstalling anything.

## The performance question

The most common concern: "won't VMs be slower?"

For self-hosting workloads, the overhead is negligible. Modern hypervisors use hardware virtualization (Intel VT-x/AMD-V) which means the CPU runs VM instructions at near-native speed. Memory overhead is a few percent. For Vaultwarden, Nextcloud, Jellyfin — you will not notice.

## Proxmox: the homelab standard

[Proxmox VE](https://www.proxmox.com/en/proxmox-ve) is a free, open-source hypervisor that runs on your hardware. You install it like an OS, then manage everything through a web UI. It's what the majority of homelabbers run, and for good reason:

- **Web UI**: create VMs, manage resources, view console — all from your browser
- **Snapshots**: one click to save state, one click to restore
- **LXC containers**: lightweight Linux containers (like VMs but sharing the host kernel) — less resource-intensive for simple services
- **Clustering**: add more physical machines later and Proxmox ties them into a single cluster — move VMs between nodes, balance load across machines, or add capacity without rebuilding anything
- **Community**: enormous amount of tutorials, scripts (like [tteck's Proxmox scripts](https://tteck.github.io/Proxmox/)), and documentation

## When to skip Proxmox

Bare metal Linux is simpler and perfectly valid if:
- You have a Raspberry Pi (Proxmox has limited Pi support)
- You want to run exactly one thing and don't care about isolation
- You want the simplest possible setup and don't anticipate expanding

For everyone else: the recommendation here is Proxmox.

<!-- RESOURCES -->

- [Proxmox VE Documentation](https://pve.proxmox.com/pve-docs/) -- type: reference, time: ongoing
- [tteck's Proxmox Helper Scripts](https://tteck.github.io/Proxmox/) -- type: tool, time: ongoing

<!-- ZH_SUMMARY -->
虚拟化是指在单台物理机上运行多个相互隔离的操作系统。与其直接在硬件上安装 Linux，不如安装一个 **hypervisor**——一种管理硬件并在其上运行虚拟机（VM）的软件。

每个 VM 都是一个完全隔离的系统：拥有自己的内核、自己的进程、自己的网络接口。从 VM 内部看，它的外观和行为与真实机器完全一致。从 hypervisor 的视角看，它只是自己控制的一个进程。

<!-- ZH_DEEP_DIVE -->
## 为什么家庭实验室需要虚拟化？

你可能会想：“反正我所有东西都跑在 Docker 里，这不已经隔离了我的服务吗？”确实如此——但这并不是虚拟化（例如 Proxmox）值得拥有的原因。真正的理由在于机器本身会发生什么。

### 快照与备份

这是最重要的一点。在做任何有风险的操作之前——尝试新配置、折腾网络——你先打一个快照。如果出了问题，你直接恢复。整个 VM 状态，包括操作系统和所有 Docker 卷，都会精确恢复到原来的样子。在裸机上，“备份”意味着你得自己写 rsync 脚本。在 Proxmox 里，只需一键。

### 安全的实验环境

想尝试新东西——一个不同的服务、一个 beta 版本、一个你拿不准的配置改动？开一台新 VM。搞坏它、从中学到东西、删掉它。你在其他 VM 上运行的服务完全不受影响。在裸机上，拿生产服务器做实验，就是在拿你的正常运行时间赌博。

### 逻辑分组，而非一服务一 VM

你不会为每个 Docker 容器跑一台 VM——那违背了初衷。一个现实的方案是：一台 VM 跑你稳定的、常驻的服务（Vaultwarden、Immich、Jellyfin），另一台 VM 跑你正在积极折腾的东西。或者一台 VM 你几个月都不碰，另一台你频繁升级。边界划在风险特征不同的服务组之间，而不是单个应用之间。

### 资源限制与灵活性

你可以限制每台 VM 能使用的 CPU 和内存上限。如果某个服务开始行为异常——一个失控的进程、一个吃光一切的 Jellyfin 转码任务——它无法饿死你服务器上的其他部分。

你还可以动态调整：服务需要时给 VM 加内存，用完了再缩回去。当单台机器不够用时，集群让你可以再加一个节点并把 VM 热迁移过去——无需停机，无需重装任何东西。

## 性能问题

最常见的担忧：“VM 会不会更慢？”

对于自托管工作负载，开销可以忽略不计。现代 hypervisor 使用硬件虚拟化（Intel VT-x/AMD-V），这意味着 CPU 以接近原生的速度执行 VM 指令。内存开销只有几个百分点。对于 Vaultwarden、Nextcloud、Jellyfin——你根本感觉不到。

## Proxmox：家庭实验室的标准

[Proxmox VE](https://www.proxmox.com/en/proxmox-ve) 是一个免费、开源的 hypervisor，直接跑在你的硬件上。你像装操作系统一样安装它，然后通过 Web UI 管理一切。大多数家庭实验室玩家都在用它，而且理由充分：

- **Web UI**：创建 VM、管理资源、查看控制台——全部在浏览器里完成
- **快照**：一键保存状态，一键恢复
- **LXC 容器**：轻量级 Linux 容器（类似 VM 但共享宿主机内核）——对简单服务来说资源开销更小
- **集群**：以后添加更多物理机，Proxmox 会把它们绑成单一集群——在节点间迁移 VM、跨机器负载均衡，或者不重建任何东西就扩容
- **社区**：海量的教程、脚本（比如 [tteck 的 Proxmox 脚本](https://tteck.github.io/Proxmox/)）和文档

## 什么时候不该用 Proxmox

裸机 Linux 更简单，而且在以下情况下完全合理：
- 你有一台 Raspberry Pi（Proxmox 对 Pi 的支持有限）
- 你只想跑一样东西，不在乎隔离
- 你想要尽可能最简单的配置，且不打算扩展

对于其他人：这里的建议是 Proxmox。

<!-- ZH_RESOURCES -->
- [Proxmox VE 文档](https://pve.proxmox.com/pve-docs/) -- 类型：参考，时间：持续
- [tteck 的 Proxmox 辅助脚本](https://tteck.github.io/Proxmox/) -- 类型：工具，时间：持续

<!-- ZH_UI -->
1. 了解 hypervisor 的作用
2. 了解为什么在家庭实验室中推荐 Proxmox 而非裸机
3. 做出决定：Proxmox 还是裸机
4. Proxmox 听起来不错——我就用这个
5. 它会清空机器上现有的内容吗？安装完成后，我怎样才能真正得到一个可以 SSH 登录并运行各种东西的可用 Linux 系统？
6. 我不想要虚拟化——直接在硬件上装 Linux
7. 我目前做的事情不需要虚拟机。但以后会后悔吗？跳过虚拟化到底放弃了什么？
8. 我想要存储、虚拟机和 Docker 全都集成在一起——有这种东西吗？
9. 我总听说 Unraid。它似乎能处理存储，还能运行容器和虚拟机。它是 Proxmox 的替代品，还是完全不同的东西？
