---
id: public-media-streaming
title: Public Media Streaming
zone: self-hosting
edges:
  to:
    - id: vps-pangolin
      question: I want a managed solution with a UI
      detail: >-
        I'm okay with a VPS, but I want a UI to manage things — not raw config
        files and commands every time. Is there something that handles the hard
        parts?
    - id: vps-wireguard-expose
      question: I want full control — VPS with manual setup
      detail: >-
        I want to understand exactly how traffic flows from the internet to my
        home server. I'm comfortable with manual setup — what does that actually
        involve?
    - id: port-forwarding
      question: What about just forwarding a port on my router?
      detail: >-
        Can't I just open a port on my router and skip renting a VPS entirely?
        What's the catch for media streaming specifically?
difficulty: 2
tags:
  - self-hosting
  - public
  - media
  - streaming
  - jellyfin
category: concept
milestones:
  - Understand why Cloudflare Tunnel is not suitable for media streaming
  - Know the options for public media access
title_zh: "公共媒体流"

---


You want to publicly expose a media server like Jellyfin so anyone can stream video or audio from a browser — no VPN required.

Cloudflare Tunnel is ruled out immediately: their Terms of Service explicitly prohibit proxying large media files, and they will terminate tunnels that violate this. For public media streaming, you need infrastructure you control.

<!-- DEEP_DIVE -->

## Why Cloudflare Tunnel doesn't work here

Cloudflare provides its CDN and tunnel service for free (or cheap) by restricting what you can push through it. Video and audio streaming generates enormous bandwidth. Their TOS explicitly forbids using the service "to serve video or a disproportionate amount of non-HTML content." If they detect it, the tunnel gets shut down.

## Your options

### VPS + Pangolin — managed, with a UI

Rent a cheap VPS, run Pangolin on it, configure a tunnel from your home server. Traffic comes in on the VPS's public IP and is forwarded through the tunnel to Jellyfin at home. Pangolin gives you a web UI to manage everything.

You own the VPS — no TOS restrictions, you control the bandwidth. For streaming you'll want a VPS with a generous bandwidth allowance. Hetzner and Oracle Free Tier are popular choices.

### VPS + WireGuard + nginx — full control

WireGuard tunnel from your home to the VPS, nginx proxying public traffic through it. No Pangolin, no extra software layer — just two tools you already understand. More setup, but the result is cleaner and easier to reason about long-term.

This is the approach to choose if you're comfortable with Linux and want to avoid managing additional software on your VPS. Run nginx however you like, add Caddy for automatic HTTPS, tune it for streaming — it's all standard tooling.

### Port forwarding — simplest, if your ISP allows it

If your ISP doesn't block the ports you need and you're okay with your home IP being public, port forwarding is the simplest path. No VPS cost. Works for any protocol. The trade-off is direct internet exposure and potential ISP port blocks.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你想公开暴露一个像 Jellyfin 这样的媒体服务器，让任何人都能从浏览器串流视频或音频——无需 VPN。

Cloudflare Tunnel 立刻被排除：其服务条款明确禁止代理大型媒体文件，违反者会被终止隧道。对于公开媒体串流，你需要自己掌控的基础设施。

<!-- ZH_DEEP_DIVE -->
## 为什么 Cloudflare Tunnel 在这里不适用

Cloudflare 通过限制你可以推送的内容，免费（或廉价）提供其 CDN 和隧道服务。视频和音频流媒体会产生巨大的带宽。其服务条款明确禁止使用该服务“提供视频或不成比例的非 HTML 内容”。一旦被检测到，隧道就会被关闭。

## 你的选择

### VPS + Pangolin —— 托管式，带 UI

租一台便宜的 VPS，在上面运行 Pangolin，配置一条从你家服务器出发的隧道。流量从 VPS 的公网 IP 进入，并通过隧道转发到家里的 Jellyfin。Pangolin 提供一个 Web UI 来管理一切。

VPS 归你所有——没有服务条款限制，带宽由你掌控。对于流媒体，你需要一台带宽配额充裕的 VPS。Hetzner 和 Oracle Free Tier 是热门选择。

### VPS + WireGuard + nginx —— 完全掌控

从你家到 VPS 建立 WireGuard 隧道，由 nginx 将公网流量通过隧道代理。没有 Pangolin，没有额外的软件层——只有两个你已经理解的工具。配置更多，但结果更干净，长期来看也更容易推理。

如果你熟悉 Linux，并且希望避免在 VPS 上管理额外软件，就选这个方案。你可以按自己喜欢的方式运行 nginx，加上 Caddy 实现自动 HTTPS，针对流媒体进行调优——全都是标准工具。

### 端口转发 —— 最简单，前提是你的 ISP 允许

如果你的 ISP 没有封锁你需要的端口，并且你不介意家庭 IP 公开，端口转发是最简单的路径。没有 VPS 成本。适用于任何协议。代价是直接暴露在互联网上，以及可能遭遇 ISP 端口封锁。

<!-- ZH_UI -->
1. 理解为什么 Cloudflare Tunnel 不适合媒体流传输
2. 了解公网媒体访问的几种方案
3. 我想要一个有 UI 的托管方案
4. 我不介意用 VPS，但我想要一个 UI 来管理，而不是每次都改原始配置文件和敲命令。有没有能处理复杂部分的方案？
5. 我想要完全掌控——用 VPS 手动搭建
6. 我想弄清楚流量从互联网到我家服务器的确切路径。我接受手动配置——这具体要做什么？
7. 那直接在路由器上做端口转发呢？
8. 我不能直接在路由器上开个端口、完全跳过租 VPS 吗？对媒体流传输来说具体有什么坑？
