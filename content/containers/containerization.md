---
id: containerization
title: What Is Containerization?
zone: containers
edges:
  to:
    - id: writing-a-dockerfile
      question: I get it. How do I build a container for my app?
      detail: >-
        I understand what containers are in theory, but I have no idea where to
        start making one for my own code. What actually goes in that Dockerfile,
        and how do I know if I've got it right?
    - id: docker-first-container
      question: I've never actually used Docker before. Where do I start?
      detail: >-
        All of this makes sense conceptually but I haven't actually run a container
        yet. I don't know what commands to use or how any of it works in practice.
    - id: container-isolation
      question: How does Docker actually isolate containers from each other and from the host?
      detail: >-
        I keep hearing that containers aren't VMs but I don't really understand what
        that means. What's actually stopping one container from seeing another
        container's processes, or from accessing the host filesystem?
difficulty: 1
tags:
  - containers
  - docker
  - containerization
  - concept
category: concept
milestones:
  - Understand the problem containers solve
  - Know the difference between an image and a container
  - Understand why container images solve the 'works on my machine' problem
  - Know what a container runtime is
title_zh: "什么是容器化？"

---


Before containers, deploying software meant carefully recreating a specific environment on every machine it needed to run on — the right OS version, the right runtime, the right system libraries, all installed in the right order. A bug that only appeared on the staging server but not on anyone's laptop was often a missing library, a different Python version, or a subtly misconfigured dependency. This was called **dependency hell**, and it made deployments slow, brittle, and hard to reason about.

A container packages an application together with everything it needs to run: the runtime, libraries, config, and code. The resulting artifact is a **container image** — a self-contained, immutable snapshot. A **container** is what you get when you run that image: a live process with its own isolated view of the system. The image never changes; you can run dozens of containers from the same image simultaneously. This is why containers solve the "works on my machine" problem — the machine is shipped with the code.

<!-- DEEP_DIVE -->

## The problem before containers

The classic deployment workflow went something like this: a developer writes code on their laptop running macOS, tests it against a locally installed Postgres 14, and ships it. The staging server runs Ubuntu 20.04 with Postgres 13. Production runs CentOS with a slightly different glibc. Each environment was set up manually, months or years apart, by different people following slightly different runbooks.

This created a category of bugs that were infuriating precisely because they were environmental rather than logical — the code was correct, but the context around it differed. **Environment drift** compounds over time: the longer a server runs, the further it drifts from its original state and from every other server in the fleet.

The solution before containers was to invest heavily in configuration management (Chef, Puppet, Ansible) to keep environments in sync. That helped, but it was still specifying the environment separately from the code. Containers took a different approach: bundle the environment into the artifact itself.

## Images vs containers

A **container image** is a static, read-only artifact. It contains your application code, the language runtime it needs, system libraries, and any other files required to run. It's built once and can be stored in a registry (like Docker Hub or a private registry) and pulled anywhere.

A **container** is a running instance of an image. When you run an image, the container runtime creates a new process with an isolated view of the filesystem, network, and process tree. The container has a thin writable layer on top of the read-only image layers — writes go there, not into the image itself.

The relationship: one image → many containers. You can run ten instances of an nginx image simultaneously; each is an independent container sharing the same underlying image layers. When you stop and delete a container, the image is untouched and its writable layer is discarded.

Building and running are distinct operations: `docker build` produces an image, `docker run` instantiates a container from it.

## The container runtime

Docker is the most familiar name, but it's not the only option. Docker itself is built on **containerd**, a container runtime that handles the low-level work of pulling images, managing container lifecycles, and interfacing with the kernel. The **OCI (Open Container Initiative)** standard defines the image format and runtime interface — which means an image built with Docker will run on Kubernetes, Podman, or any OCI-compliant runtime without modification.

When you run `docker run nginx`, the runtime pulls the image if needed, creates a set of Linux **namespaces** (giving the container its own isolated process tree, network stack, and filesystem view) and **cgroups** (limiting what CPU and memory it can consume), and then starts the process. From the container's perspective, it has its own system. From the host's perspective, it's just a process with some kernel-enforced boundaries around it.

The isolation mechanisms (namespaces) and resource controls (cgroups) are covered in depth in later nodes — the important thing to understand here is that containers are a kernel feature that Docker exposes, not magic that Docker invented.

## What containers are not

Containers are often confused with virtual machines, but the underlying mechanics are very different. A **VM** runs a full OS kernel on top of a hypervisor. Each VM has its own kernel, its own device drivers, its own init system — which is why VMs take tens of seconds to boot and use gigabytes of disk per instance.

Containers share the host kernel. There is no second OS, no hypervisor. This makes containers start in milliseconds, use far less disk, and have near-zero overhead. The tradeoff is isolation: a VM's kernel is fully separate from the host; a container's process isolation relies on kernel namespaces, which have a larger attack surface.

A practical consequence: **you cannot run Windows containers on a Linux host**, because there is no Windows kernel. (Docker Desktop on macOS and Windows handles this by running a lightweight Linux VM under the hood.) Containers give you process isolation, not OS-level virtualization.

<!-- RESOURCES -->

- [What is a container? — Docker Docs](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)
- [OCI Image Format Specification](https://specs.opencontainers.org/image-spec/)
- [OCI Runtime Specification](https://specs.opencontainers.org/runtime-spec/)

<!-- ZH_SUMMARY -->
在容器出现之前，部署软件意味着要在每一台需要运行它的机器上小心翼翼地重建特定环境——正确的操作系统版本、正确的运行时、正确的系统库，并且全部按正确的顺序安装。一个只在预发布服务器上出现、却不在任何人的笔记本电脑上出现的 bug，往往是因为缺少某个库、Python 版本不同，或者某个依赖被微妙地配置错了。这被称为**依赖地狱**，它让部署变得缓慢、脆弱且难以推理。

容器将应用程序与其运行所需的一切打包在一起：运行时、库、配置和代码。由此产生的产物就是**容器镜像**——一个自包含、不可变的快照。**容器**则是你运行该镜像时得到的东西：一个拥有自己隔离的系统视图的活进程。镜像永远不会改变；你可以从同一个镜像同时运行几十个容器。这就是容器能解决“在我机器上能跑”问题的原因——机器是随代码一起交付的。

<!-- ZH_DEEP_DIVE -->
## 容器出现之前的问题

经典的部署工作流程大致是这样的：开发者在运行 macOS 的笔记本电脑上编写代码，针对本地安装的 Postgres 14 进行测试，然后发布。预发布服务器运行 Ubuntu 20.04 和 Postgres 13。生产环境运行 CentOS，glibc 版本略有不同。每个环境都是手动搭建的，时间相隔数月甚至数年，由不同的人按照略有不同的操作手册完成。

这催生了一类令人恼火的 bug，原因恰恰在于它们是环境问题而非逻辑问题——代码本身是正确的，但代码所处的上下文不同。**环境漂移**会随时间不断累积：服务器运行得越久，它偏离初始状态以及偏离集群中其他服务器的程度就越大。

容器出现之前的解决方案是大量投入配置管理（Chef、Puppet、Ansible）来保持环境同步。这确实有帮助，但仍然是在代码之外单独描述环境。容器采取了不同的思路：把环境打包进制品本身。

## 镜像与容器

**容器镜像**是一个静态的、只读的制品。它包含你的应用代码、所需的语言运行时、系统库，以及运行所需的任何其他文件。它只构建一次，可以存储在镜像仓库（如 Docker Hub 或私有仓库）中，并在任何地方拉取。

**容器**是镜像的运行实例。当你运行一个镜像时，容器运行时会创建一个新进程，该进程拥有隔离的文件系统、网络和进程树视图。容器在只读镜像层之上有一个薄薄的可写层——写入操作发生在这里，而不是写入镜像本身。

两者的关系是：一个镜像 → 多个容器。你可以同时运行十个 nginx 镜像的实例；每个都是独立的容器，共享相同的底层镜像层。当你停止并删除一个容器时，镜像不受影响，其可写层被丢弃。

构建和运行是不同的操作：`docker build` 生成镜像，`docker run` 从镜像实例化容器。

## 容器运行时

Docker 是最为人熟知的名字，但它并非唯一选择。Docker 本身构建在 **containerd** 之上，后者是一个容器运行时，负责拉取镜像、管理容器生命周期以及与内核交互等底层工作。**OCI（Open Container Initiative）** 标准定义了镜像格式和运行时接口——这意味着用 Docker 构建的镜像无需修改即可在 Kubernetes、Podman 或任何符合 OCI 的运行时上运行。

当你运行 `docker run nginx` 时，运行时会按需拉取镜像，创建一组 Linux **命名空间**（为容器提供自己独立的进程树、网络栈和文件系统视图）和 **cgroups**（限制其可消耗的 CPU 和内存），然后启动进程。从容器的视角看，它拥有自己的系统。从宿主机的视角看，它只是一个被内核强制划定边界的进程。

隔离机制（命名空间）和资源控制（cgroups）将在后续节点中深入介绍——这里需要理解的重点是：容器是 Docker 所暴露的一项内核特性，而不是 Docker 发明的魔法。

## 容器不是什么

容器常被与虚拟机混淆，但底层机制截然不同。**VM** 在 hypervisor 之上运行完整的操作系统内核。每个 VM 都有自己的内核、自己的设备驱动、自己的 init 系统——这就是为什么 VM 启动需要数十秒，且每个实例占用数 GB 磁盘空间。

容器共享宿主机内核。没有第二个操作系统，没有 hypervisor。这使得容器能在毫秒级启动，占用磁盘少得多，开销几乎为零。代价是隔离性：VM 的内核与宿主机完全分离；容器的进程隔离依赖内核命名空间，其攻击面更大。

一个实际后果是：**你无法在 Linux 宿主机上运行 Windows 容器**，因为不存在 Windows 内核。（macOS 和 Windows 上的 Docker Desktop 通过在底层运行一个轻量级 Linux VM 来处理这个问题。）容器提供的是进程隔离，而非操作系统级虚拟化。

<!-- ZH_RESOURCES -->
- [什么是容器？ — Docker 文档](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)
- [OCI 镜像格式规范](https://specs.opencontainers.org/image-spec/)
- [OCI 运行时规范](https://specs.opencontainers.org/runtime-spec/)

<!-- ZH_UI -->
1. 理解容器所解决的问题
2. 了解镜像与容器的区别
3. 理解容器镜像为何能解决“在我机器上能跑”的问题
4. 了解什么是容器运行时
5. 我明白了。如何为我的应用构建容器？
6. 我理论上理解什么是容器，但完全不知道从哪里开始为自己的代码做一个。Dockerfile 里到底写什么，我怎么知道写得对不对？
7. 我以前从没用过 Docker。该从哪里开始？
8. 这些概念上都说得通，但我还没真正运行过容器。我不知道该用什么命令，也不知道实际怎么运作。
9. Docker 究竟如何将容器彼此隔离、并与宿主机隔离？
10. 我总听说容器不是虚拟机，但不太理解这意味着什么。究竟是什么阻止一个容器看到另一个容器的进程，或访问宿主机文件系统？
