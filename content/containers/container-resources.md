---
id: container-resources
title: Limiting Container Resources with cgroups
zone: containers
edges:
  to:
    - id: container-filesystem
      question: Namespaces and cgroups explain isolation and limits — but how do image layers actually work on disk?
      detail: >-
        I understand processes are isolated and resources are capped. But I'm
        curious how Docker stores images — every image seems to share layers with
        others and I don't understand how that works or what it means for my disk.
difficulty: 2
tags:
  - containers
  - linux
  - cgroups
  - internals
  - resources
category: concept
milestones:
  - Understand what cgroups are and what problem they solve
  - Know how Docker uses cgroups to enforce --memory and --cpus limits
  - Understand what happens when a container hits its memory limit (OOM kill)
  - Know how to inspect a container's resource usage with docker stats
  - Understand why resource limits matter in shared environments
title_zh: "使用 cgroups 限制容器资源"

---


Namespaces give each container an isolated view of the system, but isolation alone doesn't prevent a container from consuming everything the host has. A container with no limits is just a process — it can allocate as much memory as it wants, and if it leaks or spikes, it can take down the entire host. The kernel feature that solves this is **cgroups** (control groups), and Docker uses them to enforce every `--memory` and `--cpus` limit you set.

Understanding cgroups isn't about memorizing kernel internals — it's about knowing what the limits actually do, what happens when they're hit, and why running containers without them in shared environments is asking for trouble.

<!-- DEEP_DIVE -->

## The problem without limits

On a server running multiple containers, all processes compete for the same physical CPU and RAM. A container with a memory leak will keep allocating until the kernel's out-of-memory killer steps in — at which point it starts killing processes across the host, not just inside the offending container. A CPU-heavy container can consume all available cores and starve everything else, including health checks, monitoring agents, and the container runtime itself.

This is a real operational risk. A single misbehaving container can cascade into the rest of the workload. In a production environment running dozens of containers on a host, limits aren't optional — they're what makes the system predictable.

## What cgroups are

A **cgroup** is a kernel mechanism for grouping processes together and applying resource constraints to the group. The kernel tracks resource consumption per cgroup and enforces configured limits.

When Docker starts a container, it creates a cgroup for that container's processes. Every process spawned inside the container belongs to the same cgroup. The kernel enforces the limits you set against that group as a whole.

Cgroups control more than just CPU and memory: they also handle disk I/O bandwidth, network priority, and device access. Docker exposes the most commonly needed controls through standard flags.

## Setting limits with Docker

```bash
docker run -m 512m --cpus 0.5 nginx
```

**Memory** (`-m` or `--memory`): a hard limit. If the container's processes collectively try to allocate more than 512 MB, the kernel's OOM killer fires and terminates a process inside the container. The container may exit or restart depending on its restart policy.

**CPU** (`--cpus`): a soft limit expressed as a number of CPU cores. `--cpus 0.5` means the container can use at most half a core on average. Unlike the memory limit, this isn't a hard cap — the container can **burst** above the limit when the host has idle CPU capacity, but it will be throttled back under contention. This makes it suitable for bursty workloads without wasting resources when the host is quiet.

You can also set `--memory-swap` to control how much swap a container can use, and `--cpu-shares` for relative priority weighting between containers rather than a fixed limit.

**Always set memory limits in production.** Unbounded memory growth is one of the most common causes of host-level incidents in containerized environments.

## OOM kills

When a container exceeds its memory limit, the kernel sends **SIGKILL** to a process in the cgroup. The container exits with **exit code 137** (128 + 9, where 9 is the signal number for SIGKILL).

Exit code 137 doesn't always mean OOM — it can also be a manual `docker kill` — but it's the first thing to check. Confirm it:

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

If this returns `true`, the container was OOM killed. The causes are either:

1. The memory limit is set too low for the workload.
2. There's a memory leak in the application.

In both cases, `docker stats` (below) is the right starting point for investigation.

## Inspecting resource usage

```bash
docker stats
```

This shows a live, refreshing table of all running containers with their current CPU usage, memory consumption vs. limit, network I/O, and block I/O. It's the fastest way to see what's happening across all containers on a host.

```bash
docker stats <container-name>
```

Scope it to a single container for a focused view.

Key things to watch:

- **MEM USAGE / LIMIT**: if a container is consistently using 80%+ of its memory limit, either the limit is too tight or there's a leak worth investigating before it becomes an OOM kill.
- **CPU %**: values over 100% on a multi-core host are normal (100% = 1 full core). A container pegged at exactly its `--cpus` limit under load is being actively throttled.
- `docker stats` shows instantaneous usage — for trends over time, you need a monitoring system (Prometheus + cAdvisor is the standard approach).

## cgroups v1 vs v2

Linux supports two versions of the cgroups interface. **cgroups v1** uses a separate hierarchy per resource type (memory, cpu, blkio each have their own tree under `/sys/fs/cgroup/`). **cgroups v2** uses a single unified hierarchy and fixes several edge cases in v1's behavior.

Most current Linux distributions (Ubuntu 22.04+, Fedora 31+, Debian 11+) default to cgroups v2. Docker supports both transparently — the flags (`-m`, `--cpus`) behave the same from the user's perspective regardless of which version the host uses.

If you ever need to inspect a container's cgroup directly:

```bash
# cgroups v2
cat /sys/fs/cgroup/system.slice/docker-<container-id>.scope/memory.current
```

This shows the container's current memory usage in bytes, directly from the kernel's accounting. Useful for debugging discrepancies between `docker stats` and what you expect.

<!-- RESOURCES -->

- [Runtime options with Memory, CPUs, and GPUs — Docker Docs](https://docs.docker.com/config/containers/resource_constraints/)
- [Control Groups — kernel.org documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

<!-- ZH_SUMMARY -->
命名空间为每个容器提供了系统的隔离视图，但仅靠隔离并不能阻止容器耗尽宿主机的全部资源。一个没有限制的容器不过是一个普通进程——它可以随心所欲地分配内存，一旦发生内存泄漏或内存飙升，就可能拖垮整个宿主机。解决这一问题的内核特性是 **cgroups**（控制组），Docker 正是借助它来强制执行你设置的每一项 `--memory` 和 `--cpus` 限制。

理解 cgroups 并不在于死记硬背内核内部实现——而在于弄清楚这些限制实际起什么作用、触及限制时会发生什么，以及为什么在共享环境中不加限制地运行容器是在自找麻烦。

<!-- ZH_DEEP_DIVE -->
## 没有限制时的问题

在运行多个容器的服务器上，所有进程都在争抢相同的物理 CPU 和 RAM。存在内存泄漏的容器会持续分配内存，直到内核的 out-of-memory killer 介入——此时它开始在整个主机范围内终止进程，而不仅仅是在出问题的容器内部。一个 CPU 密集型的容器可能耗尽所有可用核心，使其他一切陷入饥饿，包括健康检查、监控 agent 以及容器运行时本身。

这是真实的运维风险。单个行为异常的容器可能级联影响到其余工作负载。在单台主机上运行数十个容器的生产环境中，限制不是可选项——正是它让系统变得可预测。

## cgroups 是什么

**cgroup** 是一种内核机制，用于将进程分组并对该组施加资源约束。内核按 cgroup 跟踪资源消耗，并强制执行配置的限制。

当 Docker 启动容器时，它会为该容器的进程创建一个 cgroup。容器内派生的每个进程都属于同一个 cgroup。内核针对整个组强制执行你设置的限制。

Cgroups 控制的不只是 CPU 和内存：它们还处理磁盘 I/O 带宽、网络优先级和设备访问。Docker 通过标准 flag 暴露了最常用的控制项。

## 使用 Docker 设置限制

```bash
docker run -m 512m --cpus 0.5 nginx
```

**内存**（`-m` 或 `--memory`）：硬限制。如果容器的进程合计尝试分配超过 512 MB，内核的 OOM killer 会触发并终止容器内的某个进程。容器可能退出或重启，取决于其重启策略。

**CPU**（`--cpus`）：以 CPU 核心数表示的软限制。`--cpus 0.5` 表示容器平均最多可使用半个核心。与内存限制不同，这不是硬上限——当主机有空闲 CPU 容量时，容器可以**突发**超过该限制，但在资源争用时会被限流回来。这使其适合突发型工作负载，在主机空闲时不会浪费资源。

你还可以设置 `--memory-swap` 来控制容器可使用的 swap 量，以及 `--cpu-shares` 用于容器之间的相对优先级权重，而非固定限制。

**在生产环境中始终设置内存限制。** 无界内存增长是容器化环境中主机级事故最常见的原因之一。

## OOM kill

当容器超过其内存限制时，内核向该 cgroup 中的某个进程发送 **SIGKILL**。容器以**退出码 137** 退出（128 + 9，其中 9 是 SIGKILL 的信号编号）。

退出码 137 并不总是意味着 OOM——它也可能是手动执行 `docker kill`——但这是首先要检查的。确认它：

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

如果返回 `true`，则容器是被 OOM kill 的。原因要么是：

1. 内存限制对该工作负载设置得过低。
2. 应用程序存在内存泄漏。

在这两种情况下，`docker stats`（见下文）都是调查的正确起点。

## 检查资源使用情况

```bash
docker stats
```

这会显示所有运行中容器的实时刷新表格，包含其当前 CPU 使用率、内存消耗与限制的对比、网络 I/O 和块 I/O。这是查看主机上所有容器正在发生什么的最快方式。

```bash
docker stats <container-name>
```

将其限定到单个容器以获得聚焦视图。

需要关注的关键项：

- **MEM USAGE / LIMIT**：如果容器持续使用其内存限制的 80% 以上，要么限制太紧，要么存在泄漏，值得在它变成 OOM kill 之前调查。
- **CPU %**：在多核主机上超过 100% 的值是正常的（100% = 1 个完整核心）。在负载下恰好卡在其 `--cpus` 限制上的容器正在被主动限流。
- `docker stats` 显示的是瞬时使用量——要查看随时间变化的趋势，你需要监控系统（Prometheus + cAdvisor 是标准方案）。

## cgroups v1 与 v2

Linux 支持两个版本的 cgroups 接口。**cgroups v1** 按资源类型使用独立的层级（memory、cpu、blkio 各自在 `/sys/fs/cgroup/` 下有自己的树）。**cgroups v2** 使用单一统一层级，并修复了 v1 行为中的若干边缘情况。

当前大多数 Linux 发行版（Ubuntu 22.04+、Fedora 31+、Debian 11+）默认使用 cgroups v2。Docker 透明地支持两者——无论主机使用哪个版本，从用户角度看 flag（`-m`、`--cpus`）的行为都相同。

如果你需要直接检查容器的 cgroup：

```bash
# cgroups v2
cat /sys/fs/cgroup/system.slice/docker-<container-id>.scope/memory.current
```

这会直接从内核的记账中显示容器当前的内存使用量（字节）。对于调试 `docker stats` 与你预期之间的差异很有用。

<!-- ZH_RESOURCES -->
- [Memory、CPU 和 GPU 的运行时选项 — Docker 文档](https://docs.docker.com/config/containers/resource_constraints/)
- [控制组 — kernel.org 文档](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

<!-- ZH_UI -->
1. 理解 cgroups 是什么以及它解决什么问题
2. 了解 Docker 如何使用 cgroups 强制执行 --memory 和 --cpus 限制
3. 理解容器达到内存限制时会发生什么（OOM kill）
4. 掌握如何用 docker stats 查看容器的资源使用情况
5. 理解为什么资源限制在共享环境中很重要
6. 命名空间和 cgroups 解释了隔离与限制——但镜像层在磁盘上究竟是如何工作的？
7. 我理解进程是隔离的、资源是受限的。但我很好奇 Docker 如何存储镜像——每个镜像似乎都与其他镜像共享层，我不明白这是如何实现的，也不明白这对我的磁盘意味着什么。
