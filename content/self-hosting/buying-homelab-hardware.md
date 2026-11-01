---
id: buying-homelab-hardware
title: Buying Homelab Hardware
zone: self-hosting
edges:
  to:
    - id: bare-machine-now-what
      question: I got something — now what do I do with it?
      detail: >-
        I have the machine. Do I just download an ISO and put it on a USB? Is
        there anything I need to configure first? I've never set up a server
        from scratch before.
difficulty: 1
tags:
  - self-hosting
  - hardware
  - homelab
  - raspberry-pi
  - mini-pc
category: concept
milestones:
  - >-
    Understand the tradeoffs between Raspberry Pi, mini PCs, and used enterprise
    hardware
  - Know what to look for on eBay (tiny/mini/micro form factor PCs)
  - Have a machine in hand and ready to set up
title_zh: "购买家庭实验室硬件"

---


The best homelab hardware is cheap, quiet, and sips power. You're running services 24/7 — the electricity cost matters more than the purchase price over time. A machine that draws 100W idle costs more in electricity in a year than a used mini PC costs to buy.

The sweet spot: **a used mini PC from eBay**, in the $50–150 range.

<!-- DEEP_DIVE -->

**The Tiny/Mini/Micro category**

The homelab community has a name for the ideal hardware: "tiny/mini/micro" — referring to the small form-factor PCs sold by Lenovo, HP, and Dell for enterprise desktops. These machines were designed to sit under a monitor in an office, run all day, and draw minimal power. They're now available in large quantities on eBay as businesses refresh their fleets.

The best options:

| Brand | Model series | Notes |
|---|---|---|
| **Lenovo** | ThinkCentre M series (M710q, M720q, M920q) | Most popular, excellent Linux support |
| **HP** | EliteDesk 800 G3/G4/G5 mini | Very similar to Lenovo, also excellent |
| **Dell** | OptiPlex Micro 3070, 5070 | Slightly larger, same idea |

What to look for:
- **Intel 7th gen (Kaby Lake) or later CPU.** Intel Quick Sync (the iGPU) enables hardware-accelerated video transcoding in Jellyfin. If you ever want to stream media, this matters. Skip AMD for now — Quick Sync support is significantly better.
- **16GB RAM.** Costs very little on a used machine and gives you room to run multiple services without thinking about it.
- **NVMe or SSD storage.** Not the spinning drive it probably ships with.
- **Expected power draw: 6–15W idle.** This is the big win over any desktop or laptop.

A Lenovo M720q with an i5-8500T, 16GB RAM, and a 256GB SSD typically sells for $80–120 on eBay. That's exceptional value.

**Raspberry Pi**

A Raspberry Pi 4 (4GB or 8GB) or Pi 5 is a perfectly valid choice, especially if you want something small and low-power from new. Caveats:
- ARM architecture means a small number of Docker images don't have ARM builds. Most popular self-hosted apps do.
- The Pi 4 draws about 3–5W idle — even lower than mini PCs.
- Storage lives on an SD card or USB SSD. Use an SSD via USB, not an SD card — SD cards die under constant writes.
- The Pi 5 is significantly faster than the Pi 4 and worth the extra $20 if you're buying new.

**What NOT to buy**

Avoid old enterprise rack servers (Dell PowerEdge, HP ProLiant, etc.). They're tempting because they're cheap and have lots of RAM, but their idle power draw is 100–300W. At typical electricity rates, one of these costs $150–450/year to run idle. That's not a homelab, that's a heating system.

**Where to buy**

- **eBay**: Best selection and prices. Search "Lenovo M720q", "HP EliteDesk 800 G4 mini". Sort by "Buy It Now" and filter to your budget.
- **Facebook Marketplace**: Often cheaper than eBay, local pickup means no shipping. IT equipment from local businesses refreshing their hardware shows up regularly.
- **r/homelabsales**: Community marketplace. Good deals, trustworthy sellers.

<!-- RESOURCES -->


- [ServeTheHome Tiny/Mini/Micro Guide](https://www.servethehome.com/introducing-project-tinyminimicro-home-lab-revolution/) -- type: reference, time: 20min

<!-- ZH_SUMMARY -->
最好的 homelab 硬件是便宜、安静、省电的。你要 7×24 小时运行服务——长期来看，电费比购买价格更重要。一台空闲功耗 100W 的机器，一年下来的电费比买一台二手迷你主机还贵。

最佳选择：**eBay 上的二手迷你主机**，价格在 50–150 美元之间。

<!-- ZH_DEEP_DIVE -->
**Tiny/Mini/Micro 类别**

homelab 社区对理想硬件有个称呼：“tiny/mini/micro”——指的是联想、惠普和戴尔面向企业桌面出售的小型台式机。这些机器设计用来放在办公室的显示器下方，全天运行，功耗极低。随着企业更新设备，现在 eBay 上有大量此类机器在售。

最佳选择：

| 品牌 | 型号系列 | 备注 |
|---|---|---|
| **Lenovo** | ThinkCentre M 系列（M710q、M720q、M920q） | 最受欢迎，Linux 支持极佳 |
| **HP** | EliteDesk 800 G3/G4/G5 mini | 与联想非常相似，同样出色 |
| **Dell** | OptiPlex Micro 3070、5070 | 稍大一些，思路相同 |

选购要点：
- **Intel 第 7 代（Kaby Lake）或更新的 CPU。** Intel Quick Sync（核显）可在 Jellyfin 中实现硬件加速的视频转码。如果你有流媒体播放需求，这一点很重要。暂时跳过 AMD——Quick Sync 的支持明显更好。
- **16GB 内存。** 在二手机器上花费很少，能让你有充足余量运行多个服务而无需顾虑。
- **NVMe 或 SSD 存储。** 而不是它可能附带的机械硬盘。
- **预期功耗：空闲 6–15W。** 这是相比任何台式机或笔记本电脑的最大优势。

一台配备 i5-8500T、16GB 内存和 256GB SSD 的联想 M720q 在 eBay 上通常售价 $80–120。性价比极高。

**Raspberry Pi**

Raspberry Pi 4（4GB 或 8GB）或 Pi 5 是完全合理的选择，尤其是如果你想要全新购买的小巧低功耗设备。注意事项：
- ARM 架构意味着少数 Docker 镜像没有 ARM 构建版本。大多数流行的自托管应用都有。
- Pi 4 空闲功耗约 3–5W——比迷你主机还低。
- 存储位于 SD 卡或 USB SSD 上。请通过 USB 使用 SSD，不要用 SD 卡——SD 卡在持续写入下容易损坏。
- Pi 5 比 Pi 4 快得多，如果你买全新，多花 $20 值得。

**不要买什么**

避免老旧的企业机架服务器（Dell PowerEdge、HP ProLiant 等）。它们很诱人，因为便宜且内存大，但空闲功耗为 100–300W。按典型电价，其中一台空闲运行每年花费 $150–450。那不是 homelab，那是供暖系统。

**在哪里购买**

- **eBay**：选择最多、价格最优。搜索“Lenovo M720q”、“HP EliteDesk 800 G4 mini”。按“Buy It Now”排序并筛选到你的预算。
- **Facebook Marketplace**：通常比 eBay 便宜，本地自提意味着没有运费。当地企业更新硬件时产生的 IT 设备会定期出现。
- **r/homelabsales**：社区市场。好价，卖家可信。

<!-- ZH_RESOURCES -->
- [ServeTheHome Tiny/Mini/Micro 指南](https://www.servethehome.com/introducing-project-tinyminimicro-home-lab-revolution/) -- 类型：参考，时间：20分钟

<!-- ZH_UI -->
1. 理解 Raspberry Pi、迷你主机和二手企业级硬件之间的取舍
2. 了解在 eBay 上该关注什么（tiny/mini/micro 规格的迷你主机）
3. 手头已有一台机器并准备好开始设置
4. 我已经拿到设备了——接下来该怎么做？
5. 我已经有机器了。是不是只要下载 ISO 并写入 USB 就行？需要先配置什么吗？我以前从未从零搭建过服务器。
