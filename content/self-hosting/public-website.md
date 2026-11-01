---
id: public-website
title: Public Website or Web App
zone: self-hosting
edges:
  to:
    - id: cloudflare-tunnel
      question: I want the simplest managed option
      detail: >-
        I don't want to think about VPS setup or manual configuration. I just
        want to run a command and have my site be reachable. Does that exist?
    - id: vps-pangolin
      question: I want a self-hosted VPS solution with a UI
      detail: >-
        I'm fine renting a cheap VPS, but I want a web interface to manage the
        connection — not raw config files and commands every time something
        changes.
    - id: vps-wireguard-expose
      question: I want full control — VPS with manual setup
      detail: >-
        I want to understand exactly how traffic gets from the internet to my
        home server, and I'm comfortable doing the configuration myself. What
        does that actually look like?
    - id: port-forwarding
      question: What about just forwarding a port on my router?
      detail: >-
        Isn't opening a port directly simpler than renting a VPS or signing up
        for a tunnel service? Why isn't this what everyone does?
difficulty: 1
tags:
  - self-hosting
  - public
  - website
  - web-app
category: concept
milestones:
  - Know the approaches for exposing a public web service and their trade-offs
title_zh: "公共网站或 Web 应用"

---


You're running a website, blog, or web app that anyone should be able to reach. HTTP and HTTPS traffic — no raw TCP, no media streaming with large files.

You have a few paths, ranging from "it just works" to "full control over every piece."

<!-- DEEP_DIVE -->

## Your options

### Cloudflare Tunnel — easiest, free, hides your home IP

An outbound connection from your server to Cloudflare's network. No open ports, no exposed home IP. Cloudflare handles HTTPS. You configure hostnames in their dashboard and traffic flows in through Cloudflare.

Best for: websites, APIs, anything HTTP. Not allowed for video streaming (Cloudflare's TOS).

### VPS + Pangolin — self-hosted, with a UI

You rent a cheap VPS (~$5/month), run Pangolin on it, and it creates a tunnel back to your home server. Similar concept to Cloudflare Tunnel but you own the VPS. Pangolin gives you a web UI to manage tunnels and hostnames.

Best for: people who want to avoid Cloudflare dependency and prefer a managed UI over manual config.

### VPS + WireGuard + nginx — full control, no extra software

A WireGuard tunnel from your home server to the VPS, then nginx on the VPS proxies public traffic through the tunnel. No special software — just WireGuard and a reverse proxy you almost certainly already know. Works for websites, media, any protocol.

Best for: advanced users who are comfortable with Linux and want the cleanest, most portable setup without adding Pangolin as a dependency.

### Port forwarding — the direct approach

Open a port on your router, traffic goes straight to your home server. No VPS cost, works for anything. Your home IP is exposed, ISP may block standard ports, dynamic DNS required.

Best for: personal projects where IP exposure isn't a concern and you want the simplest possible setup.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你正在运行一个网站、博客或 Web 应用，任何人都应该能够访问它。流量是 HTTP 和 HTTPS——没有原始 TCP，也没有大文件媒体流。

你有几种方案可选，从“开箱即用”到“完全掌控每一个细节”。

<!-- ZH_DEEP_DIVE -->
## 你的可选方案

### Cloudflare Tunnel — 最简单、免费、隐藏你的家庭 IP

从你的服务器到 Cloudflare 网络的出站连接。无需开放端口，不暴露家庭 IP。Cloudflare 负责处理 HTTPS。你在他们的仪表盘中配置主机名，流量通过 Cloudflare 流入。

最适合：网站、API、任何 HTTP 服务。不允许用于视频流媒体（Cloudflare 的服务条款）。

### VPS + Pangolin — 自托管，带 UI

你租一台便宜的 VPS（约 $5/月），在上面运行 Pangolin，它会创建一条回到你家庭服务器的隧道。概念与 Cloudflare Tunnel 类似，但 VPS 归你所有。Pangolin 提供 Web UI 来管理隧道和主机名。

最适合：希望避免依赖 Cloudflare、并且偏好托管式 UI 而非手动配置的人。

### VPS + WireGuard + nginx — 完全掌控，无需额外软件

从你的家庭服务器到 VPS 建立一条 WireGuard 隧道，然后 VPS 上的 nginx 通过该隧道代理公网流量。无需特殊软件——只需 WireGuard 和一个你几乎肯定已经熟悉的反向代理。适用于网站、媒体、任何协议。

最适合：熟悉 Linux、希望获得最干净、最可移植的设置、且不想引入 Pangolin 作为依赖的高级用户。

### 端口转发 — 直接方式

在路由器上开放一个端口，流量直接到达你的家庭服务器。无 VPS 成本，适用于任何服务。你的家庭 IP 会暴露，ISP 可能封锁标准端口，需要动态 DNS。

最适合：不担心 IP 暴露、并且希望尽可能简单设置的个人项目。

<!-- ZH_UI -->
1. 了解暴露公共 Web 服务的方法及其权衡
2. 我想要最简单的托管方案
3. 我不想考虑 VPS 搭建或手动配置。我只想运行一条命令就能让我的站点可访问。有这样的方案吗？
4. 我想要一个带 UI 的自托管 VPS 方案
5. 我可以租一台便宜的 VPS，但我想要一个 Web 界面来管理连接——而不是每次有变更都要改原始配置文件和敲命令。
6. 我想要完全控制——手动搭建 VPS
7. 我想确切了解流量是如何从互联网到达我家服务器的，而且我自己配置也没问题。这实际上是什么样子？
8. 那直接在路由器上转发端口呢？
9. 直接开放端口不是比租 VPS 或注册隧道服务更简单吗？为什么不是所有人都这么做？
