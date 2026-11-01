---
id: linux-and-distros
title: Linux & Distributions
zone: foundations
edges:
  to:
    - id: the-terminal
      question: I understand Linux. How do I actually use it?
      detail: >-
        I've been reading about Linux and I get the theory. But reading about it
        isn't the same as actually using it. Where do I even start — there's no
        GUI, no icons, just a blinking cursor and no idea what to type.
    - id: users-and-permissions
      question: Linux is multi-user. Who controls what?
      detail: >-
        I've already hit "permission denied" and just slapped sudo in front of
        things to make them go away. But I don't really know what's happening —
        why am I being blocked? Is it about who I am, or what the file is? And
        if I'm the only one on this server, why does any of it matter?
difficulty: 1
tags:
  - linux
  - distributions
  - ubuntu
  - debian
  - rhel
  - server-os
  - desktop-os
category: concept
milestones:
  - Explain the difference between the Linux kernel and a distribution
  - Name three server-focused distributions and when you would use each
  - Explain why servers do not run desktop operating systems
title_zh: "Linux 与发行版"

---


You know that an operating system sits between your programs and the hardware. But which operating system? If you are going into SRE or DevOps, the answer is Linux. Not sometimes, not mostly — almost always. The overwhelming majority of servers, containers, and cloud instances on the internet run Linux. Understanding what Linux actually is, why it won, and how its ecosystem of distributions works is essential context for everything that follows.

<!-- DEEP_DIVE -->

First, let us clear up a common confusion: **Linux is a kernel, not an operating system**. The kernel is the core piece — it manages CPU scheduling, memory, devices, and system calls. What people casually call "Linux" is actually a **distribution** (or "distro") — a complete operating system built around the Linux kernel, bundled with a package manager, system utilities, default configurations, and sometimes a desktop environment. Ubuntu, Debian, Red Hat Enterprise Linux (RHEL), CentOS, Fedora, Arch, Alpine — these are all distributions. They all use the same Linux kernel but differ in how they package software, how often they update, and what they prioritize.

**Why Linux dominates servers.** Three reasons. First, it is free and open source — you can run it on a thousand servers without paying a licensing fee. Second, it is incredibly stable and efficient. A Linux server can run for years without a reboot. It does not need a graphical interface, so it uses minimal resources — all the CPU and RAM go to actually running your applications. Third, the entire cloud ecosystem is built around it. AWS, GCP, and Azure all default to Linux. Docker containers are Linux containers — they use Linux kernel features (namespaces and cgroups) to work. Kubernetes runs on Linux. The tools you will use daily (Nginx, PostgreSQL, Redis, Prometheus) are all Linux-first.

**Server OS vs Desktop OS.** A desktop operating system (Windows, macOS, Ubuntu Desktop) is built for a human sitting in front of a screen — it has a GUI, a window manager, audio, Bluetooth, and a bunch of software you will never need on a server. A server OS strips all of that away. No GUI, no desktop environment, no wasted resources. You interact with it entirely through a text-based terminal over SSH. Server distributions like Ubuntu Server, Debian, RHEL, and Amazon Linux are optimized for this — small footprint, long-term stability, security updates without reboots when possible.

**The major distributions you will encounter as an SRE:**

- **Ubuntu Server** — the most popular choice for getting started and for many production environments. Based on Debian, huge community, excellent documentation. LTS (Long Term Support) releases get five years of updates.
- **Debian** — the upstream of Ubuntu. Known for rock-solid stability. Slower release cycle, which is a feature when you want predictability in production.
- **RHEL / CentOS Stream / Rocky Linux / AlmaLinux** — the Red Hat ecosystem. RHEL is the enterprise standard with paid support. CentOS used to be the free clone; after Red Hat changed its model, Rocky Linux and AlmaLinux filled that gap. You will encounter these in enterprise environments constantly.
- **Amazon Linux** — AWS's own distribution, optimized for running on EC2. If you are in an AWS shop, you will likely see this.
- **Alpine Linux** — tiny (5 MB base image), used heavily in Docker containers where image size matters. Uses `musl` instead of `glibc` and `apk` instead of `apt` — you will run into compatibility quirks.

You do not need to master all of these. Pick one (Ubuntu Server is the best starting point) and get comfortable. The core concepts — the filesystem layout, process management, networking, package management — are the same across all of them. The differences are mostly in package managers (`apt` vs `yum`/`dnf` vs `apk`) and default configurations.

**A note on Windows and macOS servers.** They exist, but they are niche. Windows Server is used in enterprises with heavy Microsoft dependencies (Active Directory, .NET, SQL Server). macOS Server is effectively dead. As an SRE, you might occasionally deal with a Windows server, but your bread and butter will be Linux. If you are on a Mac, the good news is that macOS is Unix-based and shares many concepts with Linux — most terminal commands work the same way.

<!-- RESOURCES -->

- [Linux Journey - Getting Started](https://linuxjourney.com/) -- type: tutorial, time: 2h
- [DistroWatch - Compare Linux Distributions](https://distrowatch.com/) -- type: reference, time: 30m
- [The Linux Foundation - Introduction to Linux (free course)](https://training.linuxfoundation.org/training/introduction-to-linux/) -- type: course, time: 10h
- [Ubuntu Server Guide](https://ubuntu.com/server/docs) -- type: reference, time: varies
- [Red Hat vs Debian: A Comparison](https://www.redhat.com/en/topics/linux/whats-the-best-linux-distro-for-you) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
你知道操作系统位于程序和硬件之间。但究竟是哪个操作系统？如果你要从事 SRE 或 DevOps，答案是 Linux。不是有时，不是大多数时候——而是几乎总是。互联网上绝大多数服务器、容器和云实例都运行 Linux。理解 Linux 究竟是什么、它为何胜出，以及它的发行版生态如何运作，是后续一切内容必不可少的背景知识。

<!-- ZH_DEEP_DIVE -->
首先，让我们澄清一个常见的误解：**Linux 是内核，不是操作系统**。内核是核心部分——它管理 CPU 调度、内存、设备和系统调用。人们随口所说的“Linux”实际上是一个**发行版**（或“distro”）——一个围绕 Linux 内核构建的完整操作系统，捆绑了包管理器、系统工具、默认配置，有时还包括桌面环境。Ubuntu、Debian、Red Hat Enterprise Linux（RHEL）、CentOS、Fedora、Arch、Alpine——这些都是发行版。它们都使用相同的 Linux 内核，但在软件打包方式、更新频率和优先事项上有所不同。

**为什么 Linux 主导服务器领域。** 三个原因。第一，它免费且开源——你可以在上千台服务器上运行它而无需支付许可费。第二，它极其稳定和高效。一台 Linux 服务器可以运行数年而无需重启。它不需要图形界面，因此占用资源极少——所有 CPU 和内存都用于实际运行你的应用。第三，整个云生态都围绕它构建。AWS、GCP 和 Azure 都默认使用 Linux。Docker 容器就是 Linux 容器——它们利用 Linux 内核特性（namespaces 和 cgroups）来工作。Kubernetes 运行在 Linux 上。你日常使用的工具（Nginx、PostgreSQL、Redis、Prometheus）都是 Linux 优先的。

**服务器操作系统 vs 桌面操作系统。** 桌面操作系统（Windows、macOS、Ubuntu Desktop）是为坐在屏幕前的人构建的——它有 GUI、窗口管理器、音频、蓝牙，以及一堆你在服务器上永远用不到的软件。服务器操作系统把这一切都剥离掉。没有 GUI，没有桌面环境，没有浪费的资源。你完全通过 SSH 上的文本终端与它交互。像 Ubuntu Server、Debian、RHEL 和 Amazon Linux 这样的服务器发行版就是为此优化的——占用小、长期稳定、尽可能无需重启即可完成安全更新。

**作为 SRE 你会遇到的主要发行版：**

- **Ubuntu Server**——入门以及许多生产环境中最受欢迎的选择。基于 Debian，社区庞大，文档出色。LTS（长期支持）版本获得五年的更新。
- **Debian**——Ubuntu 的上游。以坚如磐石的稳定性著称。发布周期较慢，当你在生产环境中需要可预测性时，这是一个优点。
- **RHEL / CentOS Stream / Rocky Linux / AlmaLinux**——Red Hat 生态。RHEL 是带有付费支持的企业标准。CentOS 曾是免费的克隆版；在 Red Hat 改变其模式后，Rocky Linux 和 AlmaLinux 填补了这一空白。你在企业环境中会经常遇到这些。
- **Amazon Linux**——AWS 自己的发行版，针对在 EC2 上运行进行了优化。如果你在 AWS 环境中工作，你很可能会看到它。
- **Alpine Linux**——极小（5 MB 基础镜像），大量用于镜像大小至关重要的 Docker 容器中。使用 `musl` 而非 `glibc`，使用 `apk` 而非 `apt`——你会遇到兼容性上的小问题。

你不需要精通所有这些。选一个（Ubuntu Server 是最好的起点）并熟练掌握。核心概念——文件系统布局、进程管理、网络、包管理——在所有发行版中都是相同的。差异主要在于包管理器（`apt` vs `yum`/`dnf` vs `apk`）和默认配置。

**关于 Windows 和 macOS 服务器的一点说明。** 它们存在，但属于小众。Windows Server 用于严重依赖 Microsoft 技术的企业（Active Directory、.NET、SQL Server）。macOS Server 实际上已经消亡。作为 SRE，你偶尔可能会处理 Windows 服务器，但你的主要工作将是 Linux。如果你用的是 Mac，好消息是 macOS 基于 Unix，与 Linux 共享许多概念——大多数终端命令的工作方式相同。

<!-- ZH_RESOURCES -->
- [Linux Journey - 入门](https://linuxjourney.com/) -- 类型：教程，时长：2小时
- [DistroWatch - 比较 Linux 发行版](https://distrowatch.com/) -- 类型：参考，时长：30分钟
- [Linux 基金会 - Linux 入门（免费课程）](https://training.linuxfoundation.org/training/introduction-to-linux/) -- 类型：课程，时长：10小时
- [Ubuntu 服务器指南](https://ubuntu.com/server/docs) -- 类型：参考，时长：不定
- [Red Hat 与 Debian：对比](https://www.redhat.com/en/topics/linux/whats-the-best-linux-distro-for-you) -- 类型：文章，时长：15分钟

<!-- ZH_UI -->
1. 解释 Linux 内核与发行版之间的区别
2. 列举三个面向服务器的发行版，并说明各自适用场景
3. 解释为什么服务器不运行桌面操作系统
4. 我懂 Linux 了，但实际该怎么用？
5. 我一直在读 Linux 相关资料，理论是懂了，但读和实际用是两回事。到底该从哪开始——没有图形界面、没有图标，只有一个闪烁的光标，完全不知道敲什么。
6. Linux 是多用户的，谁控制什么？
7. 我已经碰到过“permission denied”，就直接在前面加 sudo 把问题糊弄过去。但我并不真正明白发生了什么——为什么我被拦住？是因为我的身份，还是文件本身？而且如果这台服务器上只有我一个人，这些又有什么关系？
