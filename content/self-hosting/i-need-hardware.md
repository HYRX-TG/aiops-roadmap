---
id: i-need-hardware
title: I Need Somewhere to Run This
zone: self-hosting
edges:
  to:
    - id: buying-homelab-hardware
      question: I don't have any hardware — what should I buy?
      detail: >-
        Do I need something powerful? And what about electricity — if this thing
        runs 24/7, is that going to cost me? I don't want to overspend on
        something I'm just experimenting with.
    - id: bare-machine-now-what
      question: I have an old PC or laptop sitting around
      detail: >-
        It's a few years old and pretty slow. Is that going to be a problem? And
        I'm not sure I want to dedicate the whole machine — I still use it
        sometimes.
difficulty: 1
tags:
  - self-hosting
  - hardware
  - homelab
category: concept
milestones:
  - Decide whether you're using existing hardware or buying something
  - 'Know what specs matter (CPU, RAM, storage, power draw)'
title_zh: "我需要一个地方来运行这个"

---


The machine you run your services on doesn't need to be new, powerful, or expensive. That old laptop under your bed? That PC you replaced two years ago? Both are fine. Self-hosting workloads are not demanding — you're running a password manager or a file sync, not training neural networks.

The first question is simply: do you already have something, or do you need to buy?

<!-- DEEP_DIVE -->

**If you already have hardware**

Almost anything made in the last 15 years can run a self-hosted service. An old dual-core Intel laptop from 2012 can run Vaultwarden, Pi-hole, and a few other services simultaneously without breaking a sweat.

The things that actually matter:

- **RAM is the most important spec.** Aim for at least 8GB. If you have 4GB, you can still get started — run one or two lightweight services. If you have 4GB and a RAM slot free, a cheap upgrade is worth it. Most services use 100–500MB each; Jellyfin with hardware transcoding or Nextcloud with a lot of users use more.

- **An SSD is worth having.** Not for performance (services aren't that write-heavy), but for reliability. Spinning hard drives fail over time, especially in machines that run 24/7. If your old PC has an HDD, a cheap 240GB SSD is a worthwhile $20 upgrade.

- **The CPU barely matters.** Even a 4th-gen Intel Core i3 is overkill for most self-hosting. The exception is media transcoding (Jellyfin/Plex) — if you want to transcode video, you want a CPU with Intel Quick Sync (Intel 7th gen or later iGPU). But for everything else, age doesn't matter.

- **Think about power draw.** This machine will run 24/7. An old gaming PC might draw 150W idle. At $0.15/kWh, that's $200/year in electricity. A modern mini PC draws 6–15W idle. It's worth checking your machine's idle power consumption with a [Kill A Watt](https://www.amazon.com/dp/B00009MDBU) or similar meter before committing to running it full-time.

**If you need to buy**

See the next node — we cover exactly what to buy and where to find it.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
运行服务的机器不必是全新的、高性能的或昂贵的。你床底下那台旧笔记本？两年前换掉的那台 PC？都可以。自托管的工作负载要求并不高——你运行的是密码管理器或文件同步，而不是训练神经网络。

第一个问题很简单：你已经有现成的设备，还是需要购买？

<!-- ZH_DEEP_DIVE -->
**如果你已经有硬件**

过去 15 年内生产的几乎任何设备都能运行自托管服务。一台 2012 年的旧双核 Intel 笔记本可以同时运行 Vaultwarden、Pi-hole 和其他几个服务，毫不费力。

真正重要的几点：

- **RAM 是最重要的规格。** 目标至少 8GB。如果你只有 4GB，仍然可以起步——运行一两个轻量级服务。如果你有 4GB 且还有一个空闲内存插槽，那么便宜的升级是值得的。大多数服务每个占用 100–500MB；带硬件转码的 Jellyfin 或用户较多的 Nextcloud 会占用更多。

- **SSD 值得拥有。** 不是为了性能（服务并没有那么重的写入负载），而是为了可靠性。机械硬盘会随着时间推移而故障，尤其是在 24/7 运行的机器中。如果你的旧 PC 用的是 HDD，一块便宜的 240GB SSD 是值得的 20 美元升级。

- **CPU 几乎不重要。** 即便是第 4 代 Intel Core i3 对大多数自托管来说也绰绰有余。例外是媒体转码（Jellyfin/Plex）——如果你想转码视频，你需要一块带 Intel Quick Sync 的 CPU（第 7 代或更新 iGPU 的 Intel）。但除此之外，年代并不重要。

- **考虑功耗。** 这台机器将 24/7 运行。一台旧游戏 PC 空闲时可能消耗 150W。按 $0.15/kWh 计算，一年就是 $200 电费。现代迷你 PC 空闲时消耗 6–15W。在决定让它全天候运行之前，值得用 [Kill A Watt](https://www.amazon.com/dp/B00009MDBU) 或类似仪表检查一下你机器的空闲功耗。

**如果你需要购买**

参见下一个节点——我们会详细介绍该买什么以及在哪里找到它。

<!-- ZH_UI -->
1. 决定是使用现有硬件还是购买新设备
2. 了解哪些规格重要（CPU、RAM、存储、功耗）
3. 我没有任何硬件——应该买什么？
4. 我需要性能强劲的设备吗？电费方面呢——如果这台设备24/7运行，会不会很费钱？我不想在只是实验用的东西上过度花费。
5. 我有一台闲置的旧PC或笔记本
6. 它已经用了几年，速度相当慢。这会有问题吗？而且我不确定是否要专用整台机器——我有时还会用它。
