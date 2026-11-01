---
id: cloudflare-tunnel
title: Cloudflare Tunnel
zone: self-hosting
edges:
  to: []
difficulty: 1
tags:
  - self-hosting
  - cloudflare
  - tunnel
  - public
  - reverse-proxy
category: tool
milestones:
  - Create a Cloudflare Tunnel in the dashboard
  - Install and run cloudflared on your home server
  - Route a public hostname to a local service
  - Verify the service is reachable publicly over HTTPS
title_zh: "Cloudflare 隧道"

---


Cloudflare Tunnel runs a small daemon (`cloudflared`) on your server that makes an outbound-only connection to Cloudflare's network. Traffic comes in through Cloudflare and flows down that tunnel to your service. No open ports, no exposed home IP, no firewall or router changes.

For the full setup guide: **[Exposing a Self-Hosted Service Using Cloudflare Tunnel — blog.esc.sh](https://blog.esc.sh/cloudflare-tunnel/)**

<!-- DEEP_DIVE -->

## Prerequisites

- A domain managed by Cloudflare DNS (covered earlier)
- A running service to expose (e.g., your reverse proxy or a specific container)

## How to set it up

**1. Create the tunnel in the Cloudflare dashboard**

Go to: **Account Home → Zero Trust → Networks → Tunnels → Create tunnel → Cloudflared**

Give the tunnel a name, then Cloudflare generates an install command for you.

**2. Install cloudflared on your server**

Cloudflare provides the exact command for your OS. For Debian/Ubuntu it's something like:

```bash
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
  && sudo dpkg -i cloudflared.deb \
  && sudo cloudflared service install <your-tunnel-token>
```

This installs `cloudflared` as a systemd service that starts automatically. Check it's running:

```bash
sudo systemctl status cloudflared
```

**3. Configure routing in the dashboard**

Still in the Cloudflare dashboard, configure where the tunnel sends traffic:

- **Subdomain:** your chosen subdomain (or leave blank for root domain)
- **Domain:** your domain
- **Type:** `HTTP` — not HTTPS. Cloudflare terminates TLS at the edge, so traffic from Cloudflare to your local service is plain HTTP. That's fine; the connection from the user to Cloudflare is HTTPS.
- **URL:** `localhost:<port>` (or the local IP/port of your service)

Cloudflare creates the DNS record automatically. Your service is now publicly reachable at `https://subdomain.yourdomain.com`.

## Important caveats

**Cloudflare sees your traffic.** The SSL/TLS connection terminates at Cloudflare's edge — they decrypt your traffic before forwarding it. For a public website this is usually fine, but don't route sensitive private services through it.

**No video streaming.** Cloudflare's Terms of Service explicitly prohibit using the tunnel to serve video or a disproportionate amount of non-HTML content. If you need to stream media publicly, use the VPS-based approaches instead.

**Second-level subdomains cost money.** The free plan only supports root domain and one level of subdomains (`sub.yourdomain.com`). Two-level subdomains (`one.two.yourdomain.com`) require a paid Advanced Certificate.

**What you get for free:** DDoS protection, WAF, CDN, automatic HTTPS, and your home IP stays completely hidden.

<!-- RESOURCES -->

- [Exposing a Self-Hosted Service Using Cloudflare Tunnel](https://blog.esc.sh/cloudflare-tunnel/) -- type: guide, time: 20min
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) -- type: reference, time: ongoing
- [Cloudflare Access (optional auth layer)](https://developers.cloudflare.com/cloudflare-one/policies/access/) -- type: reference, time: 15min

<!-- ZH_SUMMARY -->
Cloudflare Tunnel 在你的服务器上运行一个小型守护进程（`cloudflared`），它只向 Cloudflare 网络发起出站连接。流量通过 Cloudflare 进入，并沿着该隧道流向你的服务。无需开放端口，不会暴露家庭 IP，也无需更改防火墙或路由器。

完整设置指南：**[使用 Cloudflare Tunnel 暴露自托管服务 — blog.esc.sh](https://blog.esc.sh/cloudflare-tunnel/)**

<!-- ZH_DEEP_DIVE -->
## 前置条件

- 一个由 Cloudflare DNS 管理的域名（前面已介绍）
- 一个正在运行、需要暴露的服务（例如你的反向代理或某个特定容器）

## 如何配置

**1. 在 Cloudflare 仪表盘中创建隧道**

前往：**Account Home → Zero Trust → Networks → Tunnels → Create tunnel → Cloudflared**

为隧道命名，然后 Cloudflare 会为你生成一条安装命令。

**2. 在服务器上安装 cloudflared**

Cloudflare 会提供适用于你操作系统的确切命令。对于 Debian/Ubuntu，大致如下：

```bash
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
  && sudo dpkg -i cloudflared.deb \
  && sudo cloudflared service install <your-tunnel-token>
```

这会将 `cloudflared` 安装为自动启动的 systemd 服务。检查它是否正在运行：

```bash
sudo systemctl status cloudflared
```

**3. 在仪表盘中配置路由**

仍在 Cloudflare 仪表盘中，配置隧道将流量发送到哪里：

- **Subdomain：** 你选择的子域名（若用于根域名则留空）
- **Domain：** 你的域名
- **Type：** `HTTP` —— 不是 HTTPS。Cloudflare 在边缘终止 TLS，因此从 Cloudflare 到你的本地服务的流量是纯 HTTP。这没问题；从用户到 Cloudflare 的连接是 HTTPS。
- **URL：** `localhost:<port>`（或你的服务的本地 IP/端口）

Cloudflare 会自动创建 DNS 记录。你的服务现在可通过 `https://subdomain.yourdomain.com` 公开访问。

## 重要注意事项

**Cloudflare 能看到你的流量。** SSL/TLS 连接在 Cloudflare 的边缘终止——他们在转发之前会解密你的流量。对于公开网站，这通常没问题，但不要通过它路由敏感的私有服务。

**不支持视频流。** Cloudflare 的服务条款明确禁止使用隧道来提供视频或比例过高的非 HTML 内容。如果你需要公开流媒体，请改用基于 VPS 的方案。

**二级子域名需要付费。** 免费计划仅支持根域名和一级子域名（`sub.yourdomain.com`）。二级子域名（`one.two.yourdomain.com`）需要付费的 Advanced Certificate。

**免费获得的内容：** DDoS 防护、WAF、CDN、自动 HTTPS，并且你的家庭 IP 完全隐藏。

<!-- ZH_RESOURCES -->
- [使用 Cloudflare Tunnel 暴露自托管服务](https://blog.esc.sh/cloudflare-tunnel/) -- 类型: 指南, 时间: 20分钟
- [Cloudflare Tunnel 文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) -- 类型: 参考, 时间: 持续
- [Cloudflare Access（可选认证层）](https://developers.cloudflare.com/cloudflare-one/policies/access/) -- 类型: 参考, 时间: 15分钟

<!-- ZH_UI -->
1. 在仪表板中创建 Cloudflare Tunnel
2. 在家用服务器上安装并运行 cloudflared
3. 将公共主机名路由到本地服务
4. 验证该服务可通过 HTTPS 公开访问
