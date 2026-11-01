---
id: bare-machine-now-what
title: I Have a Bare Machine — Now What?
zone: self-hosting
edges:
  to:
    - id: what-is-virtualization
      question: What OS should I install? What's all this Proxmox stuff?
      detail: >-
        I keep seeing Proxmox mentioned everywhere but I don't know what it is.
        Is it an OS? Something that runs on top of one? And why does it matter
        which one I pick?
difficulty: 1
tags:
  - self-hosting
  - hardware
  - linux
  - os
category: concept
milestones:
  - 'Understand the decision you''re about to make: virtualized vs bare metal'
title_zh: "我有一台裸机——接下来怎么办？"

---


You have a machine. It probably has Windows on it, or nothing at all. The instinct is to Google "how to install Linux" and get started. That's not wrong — but there's one question worth asking first, because it changes what you install.

**Do you want to run one thing on this machine, or many things?**

If you plug in a USB and install Linux directly, you get a Linux server. Simple, straightforward, and perfectly fine. But if you ever want to run a second service that needs its own isolated environment — or experiment without breaking what's working — you'll wish you had virtualization.

Before you reach for an ISO, read the next section on what virtualization is. It takes five minutes to understand, and it'll shape every decision you make about this machine.

<!-- DEEP_DIVE -->

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你有一台机器。它上面可能装着 Windows，或者什么都没有。你的本能是去 Google“如何安装 Linux”，然后开始动手。这并没有错——但有一个问题值得先问清楚，因为它会改变你要安装的东西。

**你想在这台机器上运行一个东西，还是许多个东西？**

如果你插上 U 盘直接安装 Linux，你会得到一个 Linux 服务器。简单、直接，完全没问题。但如果你以后想运行第二个需要自己隔离环境的服务——或者想在不破坏现有正常服务的前提下做实验——你就会希望自己当初用了虚拟化。

在你去拿 ISO 之前，先读下一节关于虚拟化是什么的内容。理解它只需要五分钟，而它会塑造你关于这台机器所做的每一个决定。

<!-- ZH_UI -->
1. 理解你即将做出的决定：虚拟化还是裸金属
2. 我应该安装什么操作系统？这些 Proxmox 相关的东西是什么？
3. 我到处都看到有人提到 Proxmox，但我不知道它是什么。它是一个操作系统吗？还是运行在操作系统之上的东西？为什么我选择哪一个很重要？
