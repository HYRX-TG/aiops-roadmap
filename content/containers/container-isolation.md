---
id: container-isolation
title: How Containers Isolate Processes
zone: containers
edges:
  to:
    - id: container-resources
      question: Okay, so processes are isolated — but what stops a container from using all the CPU and RAM?
      detail: >-
        I get that containers have their own process tree and network stack, but
        isolation alone doesn't stop a runaway container from starving everything
        else on the host. How does Docker limit what a container can actually consume?
difficulty: 2
tags:
  - containers
  - linux
  - namespaces
  - internals
category: concept
milestones:
  - Understand what Linux namespaces are and why they exist
  - "Know the six namespace types: PID, net, mnt, user, UTS, IPC"
  - Understand how PID namespaces make process 1 inside a container
  - Know what network namespace isolation means for container networking
  - Be able to explain why containers aren't VMs
title_zh: "容器如何隔离进程"

---


When people say "containers aren't VMs," they mean something specific about the kernel. A VM runs its own OS kernel on a hypervisor, completely separated from the host. A container is just a process — or a group of processes — running on the host kernel, but wrapped in a set of Linux kernel features that give it a private view of the system. That mechanism is **namespaces**.

Namespaces don't create a new kernel or a new OS. They partition existing global resources — process IDs, network interfaces, mount points — so that each container sees only its own slice. Understanding the six namespace types is understanding exactly what "isolated" means and, equally importantly, what it doesn't mean.

<!-- DEEP_DIVE -->

## The problem isolation solves

Without isolation, every process on a system shares the same global resources. Every process can see every other process in `ps`. Every process shares the same network stack, which means two processes trying to listen on port 80 conflict directly. Every process has access to the same filesystem tree from `/`.

This makes running multiple applications on a shared host messy. Port conflicts are common. A misconfigured process can see — and potentially interfere with — another application's processes. Dependency versions collide at the system level.

VMs solve this completely by running separate kernels: each VM has its own isolated OS, its own network stack, its own filesystem. The tradeoff is cost — each VM needs its own kernel, its own init system, its own copy of every shared library. Containers solve the same problem more efficiently by partitioning the existing kernel's resources rather than duplicating them.

## Linux namespaces

A **namespace** wraps a global system resource and gives a process its own private instance of it. Processes inside the namespace see the namespaced resource as if it were theirs alone; processes outside see their own separate instance.

Namespaces are a kernel feature, entirely independent of Docker. The `unshare` command lets you create namespaces manually from the command line. Docker's main job, at the process level, is to call the right kernel APIs to create a set of namespaces for each container and then start the container process inside them.

## The six namespace types

**PID** — Each container gets its own process ID tree. The first process inside the container gets PID 1, regardless of what PID it holds on the host. From inside the container, `ps aux` shows only the container's processes. From the host, the same process has a regular host PID and is visible alongside everything else. This is why a container can have its own init process at PID 1 without conflicting with the host's init.

**net** — Each container gets its own network stack: its own virtual network interfaces, its own IP address, its own routing table, and its own port space. Port 80 inside the container is completely separate from port 80 inside a different container or on the host. This is why port mapping (`-p 8080:80`) is necessary — it creates a rule connecting a host port to a container's private port.

**mnt** — Each container gets its own set of mount points. The container sees its image layers as its root filesystem (`/`), completely separate from the host's `/`. Bind mounts and volumes punch deliberate holes through this boundary.

**UTS** — Each container can have its own hostname. This is why `hostname` inside a container returns the container ID by default rather than the host's hostname.

**user** — Allows mapping container UIDs/GIDs to different UIDs/GIDs on the host. This enables "rootless containers" where a process that appears to be root inside the container maps to an unprivileged user on the host. This namespace is **not enabled by default** in standard Docker configurations and requires additional setup.

**IPC** — Each container gets its own inter-process communication namespace — its own shared memory segments and POSIX message queues. This prevents containers from accidentally communicating or interfering through IPC mechanisms.

## Why containers aren't VMs

The key difference is the kernel. A VM runs a **full guest OS kernel** on top of a hypervisor (VMware, KVM, Hyper-V). The guest kernel is completely separate — it handles its own system calls, its own scheduling, its own memory management. Even if two VMs run the same Linux distribution, their kernels don't interact.

A container has no guest kernel. Its processes make system calls directly to the **host kernel**, which enforces the namespace boundaries. There is no hypervisor, no kernel boot sequence, no duplicate OS. This is why containers start in milliseconds (no kernel boot) and are much smaller on disk (no OS image).

The isolation tradeoff: namespace isolation is a feature of the host kernel, which means it's only as strong as the kernel's implementation. A kernel vulnerability can potentially allow a container to escape its namespaces. VMs have a larger boundary — escaping a VM means compromising the hypervisor, which is a much harder target. For most workloads the practical difference doesn't matter; for high-security multi-tenant environments (running untrusted code), the distinction is significant.

A practical consequence: you cannot mix kernels. A container that requires a Linux kernel cannot run on a Windows host without a Linux VM underneath it. Docker Desktop on macOS and Windows handles this transparently by running a lightweight Linux VM, which is why Docker works on those platforms — but the containers are still running on a Linux kernel inside that VM.

## Seeing it yourself

You can inspect the namespace files that Docker creates for a running container:

```bash
docker run -d --name test nginx
docker inspect test --format '{{.State.Pid}}'
# outputs something like: 12345
ls -la /proc/12345/ns/
```

Each file in `/proc/<pid>/ns/` is a handle to a namespace. You'll see entries for `net`, `pid`, `mnt`, `uts`, `user`, and `ipc`. Two containers that share a namespace (which you can configure explicitly) will have symlinks pointing to the same inode. Two containers with separate namespaces will have different inodes.

This makes the abstraction concrete: namespaces are real kernel objects, and Docker's job is to create and manage them.

<!-- RESOURCES -->

- [Linux namespaces — man7.org](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [unshare(1) — man7.org](https://man7.org/linux/man-pages/man1/unshare.1.html)
- [Namespaces in operation — LWN.net series](https://lwn.net/Articles/531114/)

<!-- ZH_SUMMARY -->
当人们说“容器不是虚拟机”时，他们指的是内核层面的一些具体含义。虚拟机在 hypervisor 上运行自己的操作系统内核，与宿主机完全隔离。而容器只是一个进程——或一组进程——运行在宿主机内核上，但被一组 Linux 内核特性包裹，从而获得对系统的私有视图。这个机制就是 **namespaces**。

Namespaces 并不会创建新的内核或新的操作系统。它们对已有的全局资源——进程 ID、网络接口、挂载点——进行划分，使每个容器只能看到属于自己的那一部分。理解这六种 namespace 类型，就是准确理解“隔离”意味着什么，以及同样重要的是，它不意味着什么。

<!-- ZH_DEEP_DIVE -->
## 问题隔离所解决的问题

没有隔离，系统上的每个进程都共享相同的全局资源。每个进程都能在 `ps` 中看到其他所有进程。每个进程共享相同的网络栈，这意味着两个试图监听 80 端口的进程会直接冲突。每个进程都能访问从 `/` 开始的相同文件系统树。

这使得在共享主机上运行多个应用变得混乱。端口冲突很常见。一个配置错误的进程可以看到——并可能干扰——另一个应用的进程。依赖版本在系统层面发生冲突。

VM 通过运行独立的内核彻底解决了这个问题：每个 VM 都有自己的隔离操作系统、自己的网络栈、自己的文件系统。代价是成本——每个 VM 都需要自己的内核、自己的 init 系统、每个共享库的自己的副本。容器通过划分现有内核的资源而不是复制它们，更高效地解决了同样的问题。

## Linux 命名空间

**命名空间**封装一个全局系统资源，并为进程提供它自己的私有实例。命名空间内的进程看到的是属于它们自己的命名空间资源；外面的进程看到的是它们自己独立的实例。

命名空间是内核特性，完全独立于 Docker。`unshare` 命令让你可以从命令行手动创建命名空间。Docker 在进程层面的主要工作，就是调用正确的内核 API 为每个容器创建一组命名空间，然后在这些命名空间内启动容器进程。

## 六种命名空间类型

**PID** —— 每个容器都有自己的进程 ID 树。容器内的第一个进程获得 PID 1，无论它在主机上持有的是什么 PID。从容器内部看，`ps aux` 只显示容器的进程。从主机上看，同一个进程有一个常规的主机 PID，并与其他所有进程一起可见。这就是为什么容器可以在 PID 1 拥有自己的 init 进程，而不与主机的 init 冲突。

**net** —— 每个容器都有自己的网络栈：自己的虚拟网络接口、自己的 IP 地址、自己的路由表、自己的端口空间。容器内的 80 端口与另一个容器内或主机上的 80 端口完全分离。这就是为什么端口映射（`-p 8080:80`）是必要的——它创建了一条将主机端口连接到容器私有端口的规则。

**mnt** —— 每个容器都有自己的挂载点集合。容器将其镜像层视为自己的根文件系统（`/`），与主机的 `/` 完全分离。绑定挂载和卷有意在这个边界上打出孔洞。

**UTS** —— 每个容器可以有自己的主机名。这就是为什么容器内的 `hostname` 默认返回容器 ID 而不是主机的主机名。

**user** —— 允许将容器 UID/GID 映射到主机上不同的 UID/GID。这实现了“无根容器”，即容器内看起来是 root 的进程映射到主机上的非特权用户。在标准 Docker 配置中，此命名空间**默认未启用**，需要额外设置。

**IPC** —— 每个容器都有自己的进程间通信命名空间——自己的共享内存段和 POSIX 消息队列。这防止容器通过 IPC 机制意外通信或干扰。

## 为什么容器不是 VM

关键区别在于内核。VM 在 hypervisor（VMware、KVM、Hyper-V）之上运行**完整的客户机操作系统内核**。客户机内核完全独立——它处理自己的系统调用、自己的调度、自己的内存管理。即使两个 VM 运行相同的 Linux 发行版，它们的内核也不交互。

容器没有客户机内核。它的进程直接向**主机内核**发起系统调用，由主机内核强制执行命名空间边界。没有 hypervisor，没有内核启动序列，没有重复的操作系统。这就是为什么容器在毫秒内启动（没有内核启动），并且在磁盘上小得多（没有操作系统镜像）。

隔离的权衡：命名空间隔离是主机内核的特性，这意味着它的强度取决于内核的实现。内核漏洞可能允许容器逃逸其命名空间。VM 有更大的边界——逃逸 VM 意味着攻破 hypervisor，这是一个难得多的目标。对于大多数工作负载，实际差异无关紧要；对于高安全性的多租户环境（运行不受信任的代码），这一区别很重要。

一个实际后果：你不能混合内核。需要 Linux 内核的容器不能在 Windows 主机上运行，除非其下有一个 Linux VM。macOS 和 Windows 上的 Docker Desktop 通过运行一个轻量级 Linux VM 透明地处理这一点，这就是 Docker 在这些平台上工作的原因——但容器仍然在该 VM 内的 Linux 内核上运行。

## 自己动手看看

你可以检查 Docker 为运行中的容器创建的命名空间文件：

```bash
docker run -d --name test nginx
docker inspect test --format '{{.State.Pid}}'
# outputs something like: 12345
ls -la /proc/12345/ns/
```

`/proc/<pid>/ns/` 中的每个文件都是一个命名空间的句柄。你会看到 `net`、`pid`、`mnt`、`uts`、`user` 和 `ipc` 的条目。共享命名空间的两个容器（你可以显式配置）将拥有指向相同 inode 的符号链接。具有独立命名空间的两个容器将具有不同的 inode。

这使得抽象变得具体：命名空间是真实的内核对象，而 Docker 的工作就是创建和管理它们。

<!-- ZH_RESOURCES -->
- [Linux namespaces — man7.org](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [unshare(1) — man7.org](https://man7.org/linux/man-pages/man1/unshare.1.html)
- [Namespaces 实战 — LWN.net 系列](https://lwn.net/Articles/531114/)

<!-- ZH_UI -->
1. 理解 Linux 命名空间是什么以及它们为何存在
2. 了解六种命名空间类型：PID、net、mnt、user、UTS、IPC
3. 理解 PID 命名空间如何使容器内的进程成为 1 号进程
4. 了解网络命名空间隔离对容器网络意味着什么
5. 能够解释为什么容器不是虚拟机
6. 那么，进程是隔离的——但什么阻止容器用尽所有 CPU 和内存？
7. 我明白容器有自己的进程树和网络栈，但仅靠隔离并不能阻止失控的容器耗尽主机上的其他所有资源。Docker 如何限制容器实际能消耗的资源？
