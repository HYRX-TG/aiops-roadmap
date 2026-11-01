---
id: remote-access-just-me
title: 'Goal: Just Me — Personal Remote Access'
zone: self-hosting
edges:
  to:
    - id: tailscale
      question: What's the simplest option? I just want it to work
      detail: >-
        I don't want to deal with port forwarding, dynamic DNS, or certificates.
        Is there something I can just install that figures all of that out for
        me?
    - id: wireguard-vpn-home
      question: I'd rather set this up myself and understand exactly what's happening
      detail: >-
        I want to know what's actually encrypting my traffic and how my devices
        find each other. I'm okay with more work if it means I understand what
        I'm running.
difficulty: 1
tags:
  - self-hosting
  - remote-access
  - vpn
category: concept
milestones:
  - 'Identify your use case: personal remote access only'
title_zh: "目标：仅限本人 — 个人远程访问"

---


You want to reach your Jellyfin, Vaultwarden, or home assistant from your phone or laptop — anywhere in the world — without exposing anything to the public internet.

The right tool for this keeps everything private. Your services stay invisible to the internet; only your authorized devices can reach them.

<!-- DEEP_DIVE -->

## How private access works

Instead of opening a hole in your firewall for the world, you create a secure tunnel between your device and your home network. From your phone, it looks like you're on your home LAN. Your services don't need any changes — they just see local traffic.

## Your two options

**Tailscale** — installs in minutes, works through any firewall, no port forwarding needed, and just works. The right default for most people.

**WireGuard (self-hosted)** — you run the VPN server yourself. More moving parts (key generation, port forwarding on your router, dynamic DNS), but you own every piece of it and there's no third-party service involved.

Both give you the same end result. The difference is how much you want to manage.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你想从手机或笔记本电脑上访问你的 Jellyfin、Vaultwarden 或 Home Assistant——无论身处世界何地——同时不向公网暴露任何东西。

实现这一目标的合适工具能让一切保持私密。你的服务对互联网保持不可见；只有你授权的设备才能访问它们。

<!-- ZH_DEEP_DIVE -->
## 私有访问的工作原理

你无需在防火墙上为全世界开一个洞，而是在你的设备与家庭网络之间建立一条安全隧道。从手机上看，就像你连在家里的局域网上一样。你的服务无需任何改动——它们只会看到本地流量。

## 两种可选方案

**Tailscale** —— 几分钟即可安装完成，可穿透任何防火墙，无需端口转发，开箱即用。对大多数人来说是正确的默认选择。

**WireGuard（自托管）** —— 由你自己运行 VPN 服务器。涉及的环节更多（密钥生成、路由器上的端口转发、动态 DNS），但每一部分都由你掌控，且不涉及任何第三方服务。

两者最终效果相同。区别在于你愿意管理多少东西。

<!-- ZH_UI -->
1. 明确你的使用场景：仅限个人远程访问
2. 最简单的方案是什么？我只想它能直接可用
3. 我不想处理端口转发、动态 DNS 或证书。有没有那种装上就能自动搞定这一切的东西？
4. 我更愿意自己搭建，并清楚了解每一步在做什么
5. 我想知道究竟是什么在加密我的流量，以及我的设备如何互相发现。如果多花些功夫能让我理解自己在运行什么，我愿意这么做。
