---
id: vps-pangolin
title: 'VPS + Pangolin: Self-Hosted Tunnel with a UI'
zone: self-hosting
edges:
  to: []
difficulty: 2
tags:
  - self-hosting
  - vps
  - pangolin
  - tunnel
  - reverse-proxy
  - public
category: tool
milestones:
  - Provision a VPS
  - Install Pangolin on the VPS
  - Connect your home server to Pangolin using the Newt agent
  - Configure a public hostname routing to a local service
  - Verify the service is reachable publicly
title_zh: "VPS + Pangolin：带 UI 的自托管隧道"

---


Pangolin is a self-hosted reverse proxy and tunnel manager. You run it on a cheap VPS, and it manages the tunnel from your home server to the VPS — similar in concept to Cloudflare Tunnel, but you own every piece of it. A web UI handles hostnames, routing, and access control without touching config files.

Works for websites, web apps, and media streaming — no TOS restrictions since you own the VPS.

<!-- DEEP_DIVE -->

## The architecture

```
Internet → VPS public IP → Pangolin → tunnel → Newt agent (home server) → service
```

Pangolin runs on the VPS. On your home server, you run **Newt** — a lightweight agent that connects out to Pangolin and registers your services. Traffic arrives at the VPS, Pangolin routes it through the tunnel to the appropriate service on your home server.

Like Cloudflare Tunnel, the tunnel is outbound-only from your home — no open ports on your router.

## Choosing a VPS

Almost any cheap VPS works. Popular choices:

- **Hetzner** (CAX11, ~€4/month) — excellent value, good bandwidth
- **Oracle Always Free** — genuinely free, limited but usable for light traffic
- **DigitalOcean / Vultr / Linode** — $5-6/month, widely used

For media streaming, prioritize bandwidth. Hetzner includes 20TB/month on most plans.

## Setup overview

**1. Provision the VPS** with a fresh Linux install (Ubuntu or Debian recommended).

**2. Install Pangolin on the VPS** following the [Pangolin documentation](https://docs.fossorial.io/). It runs as a set of Docker containers and includes a web UI, the tunnel server (Gerbil), and a reverse proxy (Traefik).

**3. Install Newt on your home server** — the lightweight agent that connects to Pangolin. It runs as a Docker container and registers with your Pangolin instance using a credential you create in the dashboard.

**4. Configure tunnels in the Pangolin UI** — add your services, configure public hostnames, and set access policies. Pangolin creates the necessary DNS records or gives you the records to add yourself.

**5. Access your service** at the configured public hostname. Pangolin handles HTTPS automatically.

## Access control

Pangolin includes built-in access control — you can lock tunnels behind email-based OTP, SSO, or a simple PIN, without needing to add a separate auth layer.

## Trade-offs vs VPS + WireGuard + nginx

Pangolin adds convenience: a UI, built-in auth, automatic certificate management. In exchange, you're running additional software (the Pangolin stack) on your VPS, which means more to maintain and more potential failure points.

If you're comfortable with nginx and WireGuard, the raw approach is often cleaner — fewer moving parts, standard tooling, simpler to debug. Pangolin is the better choice if you prefer a GUI and want auth and cert management handled for you.

<!-- RESOURCES -->

- [Pangolin Documentation](https://docs.fossorial.io/) -- type: reference, time: ongoing
- [Pangolin on GitHub](https://github.com/fosrl/pangolin) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
Pangolin 是一个自托管的反向代理和隧道管理器。你可以在廉价的 VPS 上运行它，由它管理从你的家庭服务器到 VPS 的隧道——概念上类似 Cloudflare Tunnel，但每一部分都由你自己掌控。Web UI 负责处理主机名、路由和访问控制，无需改动配置文件。

适用于网站、Web 应用和媒体流媒体——由于 VPS 归你所有，因此没有 TOS 限制。

<!-- ZH_DEEP_DIVE -->
## 架构

```
Internet → VPS public IP → Pangolin → tunnel → Newt agent (home server) → service
```

Pangolin 运行在 VPS 上。在你的家庭服务器上，你运行 **Newt** —— 一个轻量级 agent，它会向外连接到 Pangolin 并注册你的服务。流量到达 VPS，Pangolin 通过隧道将其路由到家庭服务器上相应的服务。

与 Cloudflare Tunnel 类似，隧道是从你的家庭网络向外发起的 —— 路由器上无需开放任何端口。

## 选择 VPS

几乎任何便宜的 VPS 都可以。常见选择：

- **Hetzner**（CAX11，约 €4/月）—— 性价比极高，带宽好
- **Oracle Always Free** —— 真正免费，有限制但足以应对轻量流量
- **DigitalOcean / Vultr / Linode** —— $5-6/月，使用广泛

对于媒体流传输，优先考虑带宽。Hetzner 的大多数套餐包含每月 20TB 流量。

## 设置概览

**1. 准备 VPS**，安装全新的 Linux 系统（推荐 Ubuntu 或 Debian）。

**2. 在 VPS 上安装 Pangolin**，参照 [Pangolin 文档](https://docs.fossorial.io/)。它以一组 Docker 容器运行，包含 Web UI、隧道服务器（Gerbil）和反向代理（Traefik）。

**3. 在家庭服务器上安装 Newt** —— 这是连接到 Pangolin 的轻量级 agent。它以 Docker 容器运行，使用你在仪表盘中创建的凭据注册到你的 Pangolin 实例。

**4. 在 Pangolin UI 中配置隧道** —— 添加你的服务、配置公共主机名、设置访问策略。Pangolin 会创建必要的 DNS 记录，或者提供记录让你自行添加。

**5. 通过配置的公共主机名访问你的服务**。Pangolin 自动处理 HTTPS。

## 访问控制

Pangolin 内置访问控制 —— 你可以将隧道锁定在基于邮箱的 OTP、SSO 或简单 PIN 之后，无需额外添加独立的认证层。

## 与 VPS + WireGuard + nginx 方案的权衡

Pangolin 带来了便利：UI、内置认证、自动证书管理。作为交换，你需要在 VPS 上运行额外的软件（Pangolin 栈），这意味着更多维护工作和更多潜在故障点。

如果你熟悉 nginx 和 WireGuard，原生方案通常更简洁 —— 更少的组件、标准工具、更易于调试。如果你偏好 GUI，并希望认证和证书管理由系统代劳，Pangolin 是更好的选择。

<!-- ZH_RESOURCES -->
- [Pangolin 文档](https://docs.fossorial.io/) -- 类型：参考，时间：持续
- [GitHub 上的 Pangolin](https://github.com/fosrl/pangolin) -- 类型：参考，时间：5 分钟

<!-- ZH_UI -->
1. 配置一台 VPS
2. 在 VPS 上安装 Pangolin
3. 使用 Newt agent 将家庭服务器连接到 Pangolin
4. 配置一个指向本地服务的公共主机名路由
5. 验证该服务可公开访问
