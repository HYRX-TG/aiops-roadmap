---
id: tailscale
title: 'Tailscale: Private Network, Zero Configuration'
zone: self-hosting
edges:
  to: []
difficulty: 1
tags:
  - self-hosting
  - tailscale
  - vpn
  - wireguard
  - remote-access
category: tool
milestones:
  - Install Tailscale on your home server
  - Install Tailscale on your phone or laptop
  - >-
    Access a home service by its Tailscale IP or MagicDNS name from outside your
    home
  - Share access with at least one other person (if applicable)
title_zh: "Tailscale：私有网络，零配置"

---


Tailscale connects your devices into a private mesh network that works everywhere — no port forwarding, no dynamic DNS, no firewall rules. Install it, log in, and your devices find each other as if they were on the same LAN, regardless of where they are.

Under the hood it's WireGuard, managed for you.

<!-- DEEP_DIVE -->

## How it works

Every device you install Tailscale on gets a stable IP in the `100.x.x.x` range (the Tailscale network), plus a MagicDNS name like `my-server.tail1234.ts.net`. These are stable — they don't change when your home IP changes or when the device reboots.

Tailscale handles NAT traversal automatically. It tries to establish a direct peer-to-peer connection between your devices using WireGuard. If that's blocked (some networks are restrictive), it falls back to routing traffic through Tailscale's relay servers. Either way, the traffic is WireGuard-encrypted end-to-end — Tailscale as a company cannot see it.

## Installation

On your Linux home server:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Then install the Tailscale app on your phone or laptop and log in with the same account. Both devices will appear in your Tailscale admin console and can immediately reach each other.

## Accessing your services

Once connected, use the device's Tailscale IP or MagicDNS name to reach your services:

```
http://100.x.x.x:8096       # Jellyfin by Tailscale IP
https://my-server.tail1234.ts.net  # via MagicDNS
```

If you've set up Traefik with local DNS (as in the previous sections), that works too — you just need to be on your Tailscale network for the DNS to resolve.

## Sharing access with others

Tailscale lets you share individual devices with other Tailscale accounts — they get access to just that device, not your whole network. Great for giving a family member access to your Jellyfin server.

Alternatively, you can enable **subnet routing**: your Tailscale node advertises your whole home network (`192.168.1.0/24`), and other devices can reach anything on that subnet. Useful if you have non-Tailscale devices (a NAS, a printer) you want to reach remotely.

## Free tier

The free plan allows up to 100 devices and 3 users, which is plenty for personal and family use. If you hit the limits, self-hosting the coordination server with [Headscale](https://headscale.net/) is an open-source alternative.

<!-- RESOURCES -->

- [Tailscale Quickstart](https://tailscale.com/kb/1017/install) -- type: guide, time: 10min
- [MagicDNS](https://tailscale.com/kb/1081/magicdns) -- type: reference, time: 5min
- [Subnet Routing](https://tailscale.com/kb/1019/subnets) -- type: guide, time: 10min
- [Sharing Nodes](https://tailscale.com/kb/1084/sharing) -- type: guide, time: 5min
- [Headscale (self-hosted coordination)](https://headscale.net/) -- type: reference, time: ongoing

<!-- ZH_SUMMARY -->
Tailscale 将你的设备连接成一个私有网状网络，随处可用——无需端口转发、无需动态 DNS、无需防火墙规则。安装并登录后，你的设备就能像在同一局域网内一样互相发现，无论它们身处何地。

其底层是 WireGuard，由 Tailscale 为你托管管理。

<!-- ZH_DEEP_DIVE -->
## 工作原理

你在每台设备上安装 Tailscale 后，该设备都会获得一个 `100.x.x.x` 网段内的稳定 IP（即 Tailscale 网络），以及一个形如 `my-server.tail1234.ts.net` 的 MagicDNS 名称。这些标识是稳定的——不会因为你的家庭 IP 变化或设备重启而改变。

Tailscale 会自动处理 NAT 穿透。它会尝试使用 WireGuard 在你的设备之间建立点对点直连。如果直连被阻断（有些网络限制较严），它会回退为通过 Tailscale 的中继服务器转发流量。无论哪种方式，流量都经过 WireGuard 端到端加密——Tailscale 公司本身也无法看到。

## 安装

在你的 Linux 家庭服务器上：
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

然后在手机或笔记本电脑上安装 Tailscale 应用，并使用同一账号登录。两台设备都会出现在你的 Tailscale 管理控制台中，并且可以立即互相访问。

## 访问你的服务

连接成功后，使用设备的 Tailscale IP 或 MagicDNS 名称来访问你的服务：

```
http://100.x.x.x:8096       # Jellyfin by Tailscale IP
https://my-server.tail1234.ts.net  # via MagicDNS
```

如果你已经按照前面章节所述配置了带本地 DNS 的 Traefik，那也可以正常工作——你只需处于你的 Tailscale 网络中，DNS 就能解析。

## 与他人共享访问

Tailscale 允许你将单个设备共享给其他 Tailscale 账号——对方只能访问该设备，而不是你的整个网络。这非常适合让家庭成员访问你的 Jellyfin 服务器。

或者，你可以启用**子网路由**：让你的 Tailscale 节点通告你的整个家庭网络（`192.168.1.0/24`），其他设备就能访问该子网上的任何设备。如果你有非 Tailscale 设备（如 NAS、打印机）需要远程访问，这会很有用。

## 免费套餐

免费计划最多支持 100 台设备和 3 个用户，对个人和家庭使用来说绰绰有余。如果达到限制，使用 [Headscale](https://headscale.net/) 自托管协调服务器是一个开源替代方案。

<!-- ZH_RESOURCES -->
- [Tailscale 快速入门](https://tailscale.com/kb/1017/install) -- 类型：指南，时长：10 分钟
- [MagicDNS](https://tailscale.com/kb/1081/magicdns) -- 类型：参考，时长：5 分钟
- [子网路由](https://tailscale.com/kb/1019/subnets) -- 类型：指南，时长：10 分钟
- [共享节点](https://tailscale.com/kb/1084/sharing) -- 类型：指南，时长：5 分钟
- [Headscale（自托管协调服务器）](https://headscale.net/) -- 类型：参考，时长：持续更新

<!-- ZH_UI -->
1. 在家用服务器上安装 Tailscale
2. 在手机或笔记本电脑上安装 Tailscale
3. 从家外通过 Tailscale IP 或 MagicDNS 名称访问家庭服务
4. 与至少一位其他人共享访问权限（如适用）
