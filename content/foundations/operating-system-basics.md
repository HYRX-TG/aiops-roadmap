---
id: operating-system-basics
title: Operating System Basics
zone: foundations
edges:
  to:
    - id: linux-and-distros
      question: I know what an OS does. Which one matters for SRE?
      detail: >-
        I get what an OS does in abstract terms. But in practice, which one am I
        actually going to be using? I know most servers don't run Windows, but beyond
        that I'm fuzzy — is Linux one thing? Are there different versions? What
        am I actually going to encounter when I SSH into a server?
    - id: files-and-filesystems
      question: The OS manages files. How does that work?
      detail: >-
        I keep running into paths like /etc/nginx/nginx.conf and /var/log/syslog
        but I don't really understand how any of this is organized. Why are there
        so many folders? What does it even mean that "everything is a file"? When
        I try to read a log or edit a config I feel like I'm just guessing at
        where things live.
difficulty: 1
tags:
  - operating-system
  - linux
  - kernel
  - user-space
category: concept
milestones:
  - Explain what a kernel does
  - Understand why most servers run Linux
title_zh: "操作系统基础"

---


Your CPU can run code, but something needs to decide *which* code runs, *when* it runs, and *how* it shares resources like memory and disk with everything else happening on the machine. That something is the operating system. It is the layer between your programs and the bare metal hardware, and understanding it is absolutely essential for anyone working in SRE or DevOps.

<!-- DEEP_DIVE -->

An operating system has one core job: manage hardware resources and provide a stable, consistent interface for programs to use them. Without an OS, every program would need to know how to talk directly to your specific hard drive, your specific network card, your specific display. The OS abstracts all of that away. Your program says "write this to a file" and the OS figures out the specific disk commands to make it happen, regardless of whether you are using an SSD, an NVMe drive, or a network-attached storage device.

The heart of the OS is the **kernel**. The kernel runs with special privileges -- it has direct access to hardware and memory. It handles the most critical jobs: scheduling which processes get CPU time, managing physical memory, handling device drivers, and enforcing security boundaries between programs. When people say "Linux," they technically mean the Linux kernel. Everything else -- the shell, the file manager, the desktop environment -- is "user space" software that runs on top of the kernel.

**User space** is where your applications live. Programs in user space cannot directly touch hardware; they have to ask the kernel through **system calls** (syscalls). When your Python script opens a file, it triggers the `open()` system call. When it sends data over the network, it uses the `send()` syscall. This separation is crucial for security and stability -- a buggy application cannot crash the entire system because it never has direct hardware access. The kernel acts as a bouncer, validating every request.

Now, why Linux? In the SRE/DevOps world, Linux dominates server infrastructure. The overwhelming majority of servers on the internet run Linux -- from tiny containers to massive cloud instances. The reasons are practical: Linux is free and open source, it is incredibly stable, it is highly configurable, and it runs efficiently without a graphical interface (which servers do not need). AWS, Google Cloud, and Azure all default to Linux. Kubernetes runs on Linux. Docker containers are built on Linux kernel features. If you are going into SRE, Linux is not optional -- it is your primary working environment.

You do not need to switch your personal computer to Linux right away (though it helps). macOS is Unix-based and shares many concepts with Linux, so most terminal commands work the same way. Windows users can use WSL (Windows Subsystem for Linux) to get a full Linux environment. The important thing is to start getting comfortable with the concepts: processes, file permissions, system services, and the command line. These are the building blocks for everything that follows.

<!-- RESOURCES -->

- [Operating Systems: Three Easy Pieces (free online textbook)](https://pages.cs.wisc.edu/~remzi/OSTEP/) -- type: book, time: varies
- [Linux Journey - Getting Started](https://linuxjourney.com/) -- type: tutorial, time: 2h
- [How Linux Works by Brian Ward (book)](https://nostarch.com/howlinuxworks3) -- type: book, time: 10h
- [The Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/) -- type: reference, time: varies
- [WSL Installation Guide (for Windows users)](https://learn.microsoft.com/en-us/windows/wsl/install) -- type: tutorial, time: 30m

<!-- ZH_SUMMARY -->
你的 CPU 可以运行代码，但总得有东西来决定*哪段*代码运行、*何时*运行，以及它如何与机器上发生的其他一切共享内存和磁盘等资源。这个东西就是操作系统。它是你的程序与裸机硬件之间的那一层，理解它对于任何从事 SRE 或 DevOps 工作的人来说都绝对必不可少。

<!-- ZH_DEEP_DIVE -->
操作系统有一个核心职责：管理硬件资源，并为程序使用这些资源提供稳定、一致的接口。没有操作系统，每个程序都需要知道如何直接与你特定的硬盘、特定的网卡、特定的显示器通信。操作系统将所有这些抽象掉。你的程序说“把这个写入文件”，操作系统就会找出实现这一操作所需的具体磁盘命令，无论你使用的是 SSD、NVMe 驱动器还是网络附加存储设备。

操作系统的核心是**内核**。内核以特殊权限运行——它可以直接访问硬件和内存。它处理最关键的工作：调度哪些进程获得 CPU 时间、管理物理内存、处理设备驱动程序，以及强制执行程序之间的安全边界。当人们说“Linux”时，他们技术上指的是 Linux 内核。其他一切——shell、文件管理器、桌面环境——都是运行在内核之上的“用户空间”软件。

**用户空间**是你的应用程序所在的地方。用户空间中的程序不能直接接触硬件；它们必须通过**系统调用**（syscall）向内核请求。当你的 Python 脚本打开一个文件时，它会触发 `open()` 系统调用。当它通过网络发送数据时，它会使用 `send()` 系统调用。这种分离对安全性和稳定性至关重要——一个有缺陷的应用程序无法使整个系统崩溃，因为它永远没有直接的硬件访问权限。内核充当保安，验证每一个请求。

那么，为什么是 Linux？在 SRE/DevOps 世界中，Linux 主导着服务器基础设施。互联网上绝大多数服务器都运行 Linux——从微小的容器到大规模的云实例。原因很实际：Linux 免费且开源，它极其稳定，高度可配置，并且在没有图形界面（服务器不需要）的情况下高效运行。AWS、Google Cloud 和 Azure 都默认使用 Linux。Kubernetes 运行在 Linux 上。Docker 容器构建在 Linux 内核特性之上。如果你要进入 SRE 领域，Linux 不是可选项——它是你的主要工作环境。

你不需要立即将个人电脑切换到 Linux（尽管这有帮助）。macOS 基于 Unix，与 Linux 共享许多概念，因此大多数终端命令的工作方式相同。Windows 用户可以使用 WSL（Windows Subsystem for Linux）来获得完整的 Linux 环境。重要的是开始熟悉这些概念：进程、文件权限、系统服务和命令行。这些是后续一切内容的基础构建块。

<!-- ZH_RESOURCES -->
- [Operating Systems: Three Easy Pieces（免费在线教材）](https://pages.cs.wisc.edu/~remzi/OSTEP/) -- type: book, time: varies
- [Linux Journey - 入门](https://linuxjourney.com/) -- type: tutorial, time: 2h
- [How Linux Works，作者 Brian Ward（书籍）](https://nostarch.com/howlinuxworks3) -- type: book, time: 10h
- [Linux 内核文档](https://www.kernel.org/doc/html/latest/) -- type: reference, time: varies
- [WSL 安装指南（面向 Windows 用户）](https://learn.microsoft.com/en-us/windows/wsl/install) -- type: tutorial, time: 30m

<!-- ZH_UI -->
1. 解释内核的作用
2. 理解为什么大多数服务器运行 Linux
3. 我知道操作系统是做什么的。对 SRE 来说哪个操作系统重要？
4. 我抽象地理解操作系统是做什么的。但实践中我实际会用到哪个？我知道大多数服务器不运行 Windows，但除此之外我很模糊——Linux 是一个东西吗？有不同的版本吗？当我 SSH 登录服务器时实际会遇到什么？
5. 操作系统管理文件。这是如何工作的？
6. 我经常遇到像 /etc/nginx/nginx.conf 和 /var/log/syslog 这样的路径，但我并不真正理解这些是如何组织的。为什么有这么多文件夹？“一切皆文件”到底是什么意思？当我尝试读取日志或编辑配置时，我感觉自己只是在猜测东西在哪里。
