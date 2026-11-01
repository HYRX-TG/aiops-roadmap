---
id: remote-access-public
title: 'Goal: Public Access — Open to the Internet'
zone: self-hosting
edges:
  to:
    - id: public-access-security
      question: >-
        What are the risks? I want to understand what I'm getting into before I
        open anything up.
      detail: >-
        I've heard bots scan everything constantly. Does my home IP get exposed?
        What am I actually signing up for in terms of attack surface?
difficulty: 2
tags:
  - self-hosting
  - public
  - networking
  - security
category: concept
milestones:
  - 'Identify your use case: genuinely public-facing service'
title_zh: "目标：公共访问 — 对互联网开放"

---


You're running something that legitimately needs to be reachable by anyone — a personal website, a public API, a blog, or a media server for people you can't set up a VPN for.

This is a fundamentally different problem from private access. You're not extending a private network to trusted devices — you're putting something on the open internet.

<!-- DEEP_DIVE -->

## What "public" actually means

When you make a service publicly accessible, anyone with the URL can attempt to reach it. That includes people you want, and bots you don't. Port scanners, credential stuffers, vulnerability probes — they're automated and they hit everything they can find.

This doesn't mean don't do it. It means go in with a clear picture of what you're exposing, and take the right precautions.

## The options

There are a few approaches, each with different trade-offs:

- **Cloudflare Tunnel** — outbound tunnel from your server to Cloudflare, no open ports, your home IP stays hidden. Great for websites and web apps. Not suitable for media streaming.
- **VPS + Pangolin** — rent a cheap VPS, run a reverse proxy manager on it, tunnel from home. Works for websites and media alike. You own the VPS.
- **VPS + WireGuard + nginx** — the same VPS approach but fully manual. WireGuard for the tunnel, nginx to proxy publicly. No extra software layer, full control, works for everything.
- **Port forwarding** — open a port on your router directly. Works, but your home IP is exposed and your server is directly on the internet.

Before you pick one, there's an important security conversation to have.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你运行的服务确实需要任何人都能访问——个人网站、公共 API、博客，或是为那些你无法为其配置 VPN 的人提供的媒体服务器。

这与私有访问是一个根本不同的问题。你不是在把私有网络扩展到受信任的设备上——你是在把某个东西放到开放的互联网上。

<!-- ZH_DEEP_DIVE -->
## “公开”到底意味着什么

当你让一个服务可以被公开访问时，任何拿到 URL 的人都能尝试访问它。这既包括你希望其访问的人，也包括你不希望其访问的机器人。端口扫描器、凭据填充工具、漏洞探测程序——它们都是自动化的，会攻击它们能找到的一切目标。

这并不意味着不要这么做，而是意味着在动手之前，要清楚自己到底暴露了什么，并采取正确的预防措施。

## 可选方案

有几种做法，各有不同的取舍：

- **Cloudflare Tunnel** —— 从你的服务器向 Cloudflare 建立出站隧道，不开放端口，你的家庭 IP 保持隐藏。非常适合网站和 Web 应用，但不适合媒体流传输。
- **VPS + Pangolin** —— 租一台便宜的 VPS，在上面运行反向代理管理器，从家里建立隧道。网站和媒体都适用。VPS 归你所有。
- **VPS + WireGuard + nginx** —— 同样是 VPS 方案，但完全手动。用 WireGuard 建立隧道，用 nginx 对外代理。没有额外的软件层，完全可控，适用于一切场景。
- **端口转发** —— 直接在路由器上开放一个端口。能用，但你的家庭 IP 会暴露，服务器也直接暴露在互联网上。

在选择之前，有一个重要的安全话题需要先讨论。

<!-- ZH_UI -->
1. 明确你的使用场景：真正面向公众的服务
2. 有哪些风险？我想在开放任何东西之前先了解自己将面对什么。
3. 我听说机器人会不断扫描一切。我的家庭 IP 会暴露吗？就攻击面而言，我实际上要面对什么？
