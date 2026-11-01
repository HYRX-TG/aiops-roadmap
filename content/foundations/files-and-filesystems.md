---
id: files-and-filesystems
title: Files & Filesystems
zone: foundations
edges:
  to:
    - id: processes-and-memory
      question: Files exist on disk. But what about things running in memory?
      detail: >-
        I understand how files sit on disk. But when a program is actually
        running, where does it live? I've heard of RAM and memory but I don't
        understand what a 'process' is or how the OS actually handles the thing
        I just started running. What happens between 'I ran this program' and
        'it's doing something'?
    - id: log-files
      question: I understand files. Where do systems keep their logs?
      detail: >-
        I know where config files live and how permissions work. But where does
        all the logging go? Every service must be writing something somewhere —
        I just have no idea how to find it or make sense of it when something
        goes wrong.
difficulty: 1
tags:
  - filesystem
  - permissions
  - inodes
  - linux
  - ext4
  - directory-structure
category: concept
milestones:
  - 'Explain the Linux directory structure (/etc, /var, /home, etc.)'
  - Change file permissions using chmod
title_zh: "文件与文件系统"

---


Everything on a Linux system is a file -- or at least, it pretends to be. Regular files, directories, hardware devices, running processes -- they all show up as entries in a unified file hierarchy. Understanding how this hierarchy is organized, how permissions control who can do what, and how the filesystem actually stores data on disk will save you from countless headaches when managing servers.

<!-- DEEP_DIVE -->

Linux organizes everything into a single tree that starts at `/` (called "root," not to be confused with the root user). Unlike Windows, which has separate drive letters like `C:\` and `D:\`, Linux mounts everything under one unified hierarchy. The key directories you need to know: `/home` is where user home directories live (your stuff goes in `/home/yourusername`). `/etc` holds system-wide configuration files -- this is where you will find configs for SSH, Nginx, DNS, and nearly every service. `/var` stores variable data like logs (`/var/log`), databases, and mail. `/tmp` is for temporary files that get cleaned up on reboot. `/usr` holds user programs and libraries. `/bin` and `/sbin` contain essential system binaries.

**File permissions** are one of the most important concepts in Linux security. Every file has three sets of permissions: one for the owner, one for the group, and one for everyone else. Each set can allow reading (r), writing (w), and executing (x). When you run `ls -l`, you see something like `-rwxr-xr--`, which means the owner can read, write, and execute; the group can read and execute; and others can only read. The `chmod` command changes these permissions. You will use it in two ways: symbolic mode (`chmod u+x script.sh` adds execute permission for the owner) or numeric mode (`chmod 755 script.sh` sets rwx for owner, r-x for group and others). The numeric mode uses octal: 4=read, 2=write, 1=execute, and you add them up per group.

Under the hood, a filesystem like **ext4** (the most common Linux filesystem) or **XFS** stores data using a structure called **inodes**. An inode contains metadata about a file -- its size, permissions, timestamps, and pointers to the actual data blocks on disk. The filename itself is not stored in the inode; it is stored in the directory entry that points to the inode. This is why you can have hard links -- multiple filenames pointing to the same inode (and therefore the same data). It is also why deleting a file is technically "unlinking" it: you remove the directory entry, and when no more entries point to that inode, the data blocks are freed.

Why does this matter in practice? As an SRE, you will constantly deal with filesystem issues. A disk filling up with logs in `/var/log` can take down an entire service. Incorrect permissions on a config file can prevent a service from starting. Understanding inodes explains why you can sometimes run out of "disk space" even when `df` shows free space -- you might have run out of inodes (too many tiny files). Knowing the difference between ext4 and XFS matters when you are provisioning storage for databases versus log files, since they have different performance characteristics and limitations.

One more practical concept: **mount points**. In Linux, you can attach (mount) a separate disk or partition at any point in the directory tree. A common pattern on servers is to mount a separate disk at `/var/log` so that runaway logs cannot fill up the root filesystem and crash the machine. You will see this pattern constantly in cloud environments, where you attach EBS volumes or persistent disks and mount them where your application needs storage. The `mount` command and `/etc/fstab` file control this.

<!-- RESOURCES -->

- [Linux Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html) -- type: reference, time: 30m
- [Linux Journey - Filesystem](https://linuxjourney.com/lesson/filesystem-hierarchy) -- type: tutorial, time: 1h
- [chmod Calculator - Visual Permission Tool](https://chmod-calculator.com/) -- type: tool, time: 5m
- [Understanding Inodes - Linux Handbook](https://linuxhandbook.com/inode-linux/) -- type: article, time: 15m
- [How Linux Works, Chapter 4: Disks and Filesystems](https://nostarch.com/howlinuxworks3) -- type: book, time: 2h

<!-- ZH_SUMMARY -->
Linux 系统上的一切都是文件——至少，它们都伪装成文件。普通文件、目录、硬件设备、运行中的进程——它们都以条目的形式出现在统一的文件层次结构中。理解这个层次结构如何组织、权限如何控制谁能做什么，以及文件系统实际如何在磁盘上存储数据，将在你管理服务器时为你省去无数麻烦。

<!-- ZH_DEEP_DIVE -->
Linux 将所有内容组织成一棵以 `/` 为起点的单一树（称为“根”，不要与 root 用户混淆）。与 Windows 拥有 `C:\` 和 `D:\` 等独立盘符不同，Linux 将所有内容挂载在一个统一的层级之下。你需要了解的关键目录：`/home` 是用户主目录所在的位置（你的内容放在 `/home/yourusername`）。`/etc` 存放系统级配置文件——你将在这里找到 SSH、Nginx、DNS 以及几乎所有服务的配置。`/var` 存储可变数据，如日志（`/var/log`）、数据库和邮件。`/tmp` 用于存放重启时会被清理的临时文件。`/usr` 存放用户程序和库。`/bin` 和 `/sbin` 包含基本的系统二进制文件。

**文件权限**是 Linux 安全中最重要的概念之一。每个文件有三组权限：一组针对所有者，一组针对所属组，一组针对其他所有人。每组权限可以允许读取（r）、写入（w）和执行（x）。当你运行 `ls -l` 时，你会看到类似 `-rwxr-xr--` 的内容，这意味着所有者可以读、写、执行；所属组可以读、执行；其他人只能读。`chmod` 命令用于更改这些权限。你会以两种方式使用它：符号模式（`chmod u+x script.sh` 为所有者添加执行权限）或数字模式（`chmod 755 script.sh` 为所有者设置 rwx，为所属组和其他人设置 r-x）。数字模式使用八进制：4=读，2=写，1=执行，然后按组分别相加。

在底层，像 **ext4**（最常见的 Linux 文件系统）或 **XFS** 这样的文件系统使用一种称为 **inode** 的结构来存储数据。inode 包含关于文件的元数据——其大小、权限、时间戳以及指向磁盘上实际数据块的指针。文件名本身并不存储在 inode 中；它存储在指向该 inode 的目录项中。这就是为什么你可以拥有硬链接——多个文件名指向同一个 inode（因而指向同一份数据）。这也是为什么删除文件在技术上就是“解除链接”：你移除目录项，当没有更多目录项指向该 inode 时，数据块就会被释放。

为什么这在实践中很重要？作为 SRE，你会不断处理文件系统问题。`/var/log` 中日志写满磁盘可能导致整个服务宕机。配置文件上错误的权限可能阻止服务启动。理解 inode 可以解释为什么有时即使 `df` 显示有可用空间，你仍可能“磁盘空间”耗尽——你可能耗尽了 inode（太多小文件）。在为数据库与日志文件配置存储时，了解 ext4 与 XFS 的区别很重要，因为它们具有不同的性能特征和限制。

还有一个实用概念：**挂载点**。在 Linux 中，你可以在目录树的任意位置附加（挂载）单独的磁盘或分区。服务器上一种常见模式是在 `/var/log` 挂载单独的磁盘，这样失控的日志就无法填满根文件系统并导致机器崩溃。你会在云环境中经常看到这种模式，即你附加 EBS 卷或持久磁盘，并将它们挂载到应用程序需要存储的位置。`mount` 命令和 `/etc/fstab` 文件控制这一行为。

<!-- ZH_RESOURCES -->
- [Linux 文件系统层次结构标准](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html) -- 类型: 参考, 时间: 30m
- [Linux Journey - 文件系统](https://linuxjourney.com/lesson/filesystem-hierarchy) -- 类型: 教程, 时间: 1h
- [chmod 计算器 - 可视化权限工具](https://chmod-calculator.com/) -- 类型: 工具, 时间: 5m
- [理解 Inode - Linux Handbook](https://linuxhandbook.com/inode-linux/) -- 类型: 文章, 时间: 15m
- [How Linux Works，第 4 章：磁盘与文件系统](https://nostarch.com/howlinuxworks3) -- 类型: 书籍, 时间: 2h

<!-- ZH_UI -->
1. 解释 Linux 目录结构（/etc、/var、/home 等）
2. 使用 chmod 更改文件权限
3. 文件存在于磁盘上。但内存中运行的东西呢？
4. 我理解文件如何存放在磁盘上。但当程序实际运行时，它位于哪里？我听说过 RAM 和内存，但我不理解什么是“进程”，也不理解操作系统如何处理我刚启动运行的东西。从“我运行了这个程序”到“它在做某事”之间发生了什么？
5. 我理解文件。系统把日志放在哪里？
6. 我知道配置文件在哪里以及权限如何工作。但所有日志都去了哪里？每个服务一定都在某处写东西——我只是不知道如何找到它，也不知道出问题时如何理解它。
