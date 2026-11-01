---
id: what-is-a-vps
title: What Is a VPS?
zone: running
edges:
  to:
    - id: ssh
      question: I have a VPS. How do I connect to it and run commands?
      detail: >-
        My VPS is running in some datacenter — but I have no monitor, no
        keyboard, no way to touch it. How do I actually get inside it and run
        commands? There must be a way to connect to it remotely, but I don't
        know what that involves.
difficulty: 1
tags:
  - vps
  - virtualization
  - cloud
  - vm
  - hypervisor
category: concept
milestones:
  - Explain what a hypervisor does and how a VPS differs from a dedicated server
  - >-
    Understand what resources a VPS has and why they are shared with other
    tenants
  - Know what a disk image / snapshot is and why it matters
title_zh: "什么是 VPS？"

---


When you click "Create Droplet" on DigitalOcean or "Launch Instance" on AWS, you get a VPS — a Virtual Private Server. It looks and behaves like a real computer: it has a CPU, RAM, disk, and a public IP address. But it is not a physical machine. It is a software-defined slice of a much larger physical server, running alongside dozens of other virtual machines owned by other customers.

Understanding what a VPS actually is helps you reason about performance, limits, cost, and why the server behaves the way it does.

<!-- DEEP_DIVE -->

**Virtualization and hypervisors**

The physical servers in a datacenter are powerful machines — 64 cores, 512 GB of RAM, multiple terabytes of disk. Running a single customer's workload on that hardware would be massively wasteful. Instead, a piece of software called a **hypervisor** runs directly on the hardware and carves it up into isolated virtual machines.

Each VM gets a guaranteed slice: "this VM has 2 CPU cores, 4 GB of RAM, 80 GB of disk." The hypervisor enforces this isolation. Your VM cannot use more RAM than it was allocated, and it cannot see the other VMs' memory or disk.

Common hypervisors: KVM (used by DigitalOcean, Linode), Xen (used by AWS EC2 originally), VMware ESXi (enterprise).

```
Physical Server (64 cores, 512 GB RAM)
┌─────────────────────────────────────────────┐
│  Hypervisor (KVM)                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Your VPS  │ │ Someone   │ │ Someone   │  │
│  │ 2 cores   │ │ else's VM │ │ else's VM │  │
│  │ 4 GB RAM  │ │ 4 cores   │ │ 1 core    │  │
│  │ 80 GB SSD │ │ 8 GB RAM  │ │ 2 GB RAM  │  │
│  └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────┘
```

**What you actually get**

When you provision a VPS, you choose:
- **CPU** — number of virtual cores (vCPUs). These map to threads on the host's physical CPU.
- **RAM** — dedicated memory. If your app leaks memory and uses it all, only your VM is affected.
- **Disk** — a virtual disk, usually backed by SSDs in a SAN (storage area network) or local NVMe drives.
- **Network** — a virtual network interface with a public IPv4 address (and often IPv6). Bandwidth is throttled per plan.
- **OS image** — you pick an operating system (Ubuntu 22.04 LTS is the most common choice). The hypervisor installs it from a pre-built image.

**VPS vs. dedicated server vs. shared hosting**

| | Shared Hosting | VPS | Dedicated Server |
|--|--|--|--|
| Hardware | Shared with hundreds | Shared (virtualized) | Yours alone |
| Root access | No | Yes | Yes |
| Isolation | Weak | Strong (VM boundary) | Complete |
| Cost | $5–15/mo | $5–100/mo | $100–500+/mo |
| Control | Almost none | Full | Full |

A VPS is the sweet spot: you get root access and full control, at a fraction of the cost of dedicated hardware.

**The ephemeral nature of a VPS**

Unlike your laptop, a VPS is designed to be disposable. You can:
- **Destroy it** — delete the VM and all its data permanently
- **Snapshot it** — take a point-in-time image of the entire disk. If you break something, you can restore to a known-good state.
- **Resize it** — many providers let you upgrade to a bigger plan (more RAM, more CPU) with minimal downtime
- **Rebuild it** — wipe the disk and reinstall a fresh OS image

This means you should treat your server's **configuration as code** — not something you type once and hope you remember. If your server is destroyed and you cannot recreate it from scratch in an hour, something is wrong.

**Practical implications**

- **You have root** — you are the administrator. You can install anything, break anything, and no one will stop you.
- **CPU and RAM limits are real** — if your app uses more RAM than you have, the kernel will start killing processes (OOM killer). If you max out CPU, everything slows down.
- **Disk is not infinite** — a typical entry-level VPS has 25–80 GB. Logs, uploaded files, and database growth can fill it.
- **The public IP is yours** — until you destroy the VM. After that, someone else gets it. Don't hardcode your server's IP anywhere important.
- **Nothing is backed up by default** — most providers offer optional backup services. If you do not enable them and your disk fails, your data is gone.

<!-- RESOURCES -->

- [DigitalOcean - What is a VPS?](https://www.digitalocean.com/community/tutorials/what-is-a-vps-virtual-private-server) -- type: article, time: 10m
- [How Virtualization Works (KVM)](https://www.linux-kvm.org/page/FAQ) -- type: reference, time: 15m

<!-- ZH_SUMMARY -->
当你在 DigitalOcean 上点击“Create Droplet”，或在 AWS 上点击“Launch Instance”时，你得到的就是一台 VPS——虚拟专用服务器。它看起来、用起来都像一台真实的计算机：有 CPU、内存、磁盘和一个公网 IP 地址。但它并不是一台物理机，而是从一台大得多的物理服务器上划分出来的、由软件定义的资源切片，与数十台属于其他客户的虚拟机一同运行。

理解 VPS 究竟是什么，有助于你分析性能、限制、成本，以及服务器为何会表现出当前的行为。

<!-- ZH_DEEP_DIVE -->
**虚拟化与 Hypervisor**

数据中心里的物理服务器都是性能强劲的机器——64 核、512 GB 内存、数 TB 磁盘。在这套硬件上只运行单个客户的工作负载会造成极大的浪费。因此，一种称为 **hypervisor** 的软件直接运行在硬件之上，将硬件切分为多个相互隔离的虚拟机。

每个 VM 都获得一份有保障的资源配额：“这个 VM 有 2 个 CPU 核心、4 GB 内存、80 GB 磁盘。”hypervisor 负责强制执行这种隔离。你的 VM 无法使用超过分配给它的内存，也无法看到其他 VM 的内存或磁盘。

常见的 hypervisor：KVM（DigitalOcean、Linode 使用）、Xen（AWS EC2 最初使用）、VMware ESXi（企业级）。

```
Physical Server (64 cores, 512 GB RAM)
┌─────────────────────────────────────────────┐
│  Hypervisor (KVM)                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Your VPS  │ │ Someone   │ │ Someone   │  │
│  │ 2 cores   │ │ else's VM │ │ else's VM │  │
│  │ 4 GB RAM  │ │ 4 cores   │ │ 1 core    │  │
│  │ 80 GB SSD │ │ 8 GB RAM  │ │ 2 GB RAM  │  │
│  └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────┘
```

**你实际得到的东西**

当你开通一台 VPS 时，你需要选择：
- **CPU**——虚拟核心（vCPU）数量。这些核心映射到宿主机物理 CPU 的线程上。
- **内存**——专用内存。如果你的应用发生内存泄漏并耗尽内存，只有你的 VM 会受到影响。
- **磁盘**——一块虚拟磁盘，通常由 SAN（存储区域网络）中的 SSD 或本地 NVMe 盘提供支持。
- **网络**——一个虚拟网络接口，带有公网 IPv4 地址（通常还有 IPv6）。带宽按套餐进行限速。
- **操作系统镜像**——你选择一个操作系统（Ubuntu 22.04 LTS 是最常见的选择）。hypervisor 会从预构建的镜像安装它。

**VPS vs. 独立服务器 vs. 共享主机**

| | 共享主机 | VPS | 独立服务器 |
|--|--|--|--|
| 硬件 | 与数百个用户共享 | 共享（虚拟化） | 独享 |
| Root 权限 | 无 | 有 | 有 |
| 隔离性 | 弱 | 强（VM 边界） | 完全隔离 |
| 成本 | $5–15/月 | $5–100/月 | $100–500+/月 |
| 控制权 | 几乎没有 | 完全 | 完全 |

VPS 是最佳平衡点：你获得 root 权限和完全控制权，而成本只是独立硬件的一小部分。

**VPS 的临时性本质**

与你的笔记本电脑不同，VPS 在设计上就是可随时丢弃的。你可以：
- **销毁它**——删除 VM 及其所有数据，永久不可恢复
- **创建快照**——对整个磁盘做一份时间点镜像。如果你把某些东西弄坏了，可以恢复到已知良好的状态。
- **调整规格**——许多提供商允许你升级到更大的套餐（更多内存、更多 CPU），且停机时间极短
- **重装系统**——清空磁盘并重新安装全新的操作系统镜像

这意味着你应当把服务器的**配置当作代码**来管理——而不是敲一遍然后指望自己还记得。如果你的服务器被销毁后，你无法在一小时内从零重建它，那就说明有问题。

**实际影响**

- **你拥有 root 权限**——你就是管理员。你可以安装任何东西、弄坏任何东西，没有人会阻止你。
- **CPU 和内存限制是真实存在的**——如果你的应用使用的内存超过可用内存，内核会开始杀死进程（OOM killer）。如果你把 CPU 跑满，一切都会变慢。
- **磁盘不是无限的**——典型的入门级 VPS 有 25–80 GB。日志、上传的文件和数据库增长都可能把它填满。
- **公网 IP 属于你**——直到你销毁 VM 为止。之后，它会分配给其他人。不要把服务器的 IP 硬编码在任何重要的地方。
- **默认没有任何备份**——大多数提供商提供可选的备份服务。如果你不启用它们，而你的磁盘发生故障，你的数据就没了。

<!-- ZH_RESOURCES -->
- [DigitalOcean - 什么是 VPS？](https://www.digitalocean.com/community/tutorials/what-is-a-vps-virtual-private-server) -- 类型: 文章, 时间: 10m
- [虚拟化是如何工作的 (KVM)](https://www.linux-kvm.org/page/FAQ) -- 类型: 参考, 时间: 15m

<!-- ZH_UI -->
1. 解释 hypervisor 的作用，以及 VPS 与独立服务器的区别
2. 了解 VPS 拥有哪些资源，以及为什么这些资源与其他租户共享
3. 了解什么是磁盘镜像/快照，以及它为什么重要
4. 我有一台 VPS。如何连接它并运行命令？
5. 我的 VPS 运行在某个数据中心里——但我没有显示器、没有键盘，也无法接触到它。我究竟怎样才能进入其中并运行命令？一定有办法远程连接它，但我不知道这涉及什么。
