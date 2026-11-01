---
id: port-forwarding
title: 'Port Forwarding: The Direct Approach'
zone: self-hosting
edges:
  to: []
difficulty: 2
tags:
  - self-hosting
  - networking
  - port-forwarding
  - public
  - router
category: concept
milestones:
  - Understand what port forwarding does and what it exposes
  - 'Know the limitations (ISP blocking, dynamic IP, exposed home IP)'
title_zh: "端口转发：直接方式"

---


Port forwarding tells your router: "when traffic arrives on port X from the internet, send it to this local machine." No VPS, no tunnel, no third party. It's the original way to expose a home service, and it works.

But it comes with trade-offs the other options don't. Know what you're getting into.

<!-- DEEP_DIVE -->

## What port forwarding actually does

Your home router has one public IP (assigned by your ISP) and manages a private LAN behind it. Normally, inbound traffic from the internet is dropped — there's no route to your internal machines.

Port forwarding punches a hole: traffic arriving on a specific port gets forwarded to a specific internal IP and port. From the internet, it looks like your router is serving the traffic. In reality, your home server is.

## Your home IP is now public

Unlike Cloudflare Tunnel or a VPS setup, anyone connecting to your service can see your real home IP address. This isn't necessarily a dealbreaker, but it's worth knowing. If you'd prefer to keep your home IP private, use one of the tunnel-based approaches instead.

## ISP restrictions

Many ISPs block inbound traffic on ports 80 (HTTP) and 443 (HTTPS) — the standard web ports. If yours does, you'll have to use non-standard ports like 8080 or 8443, which means URLs like `https://example.com:8443`. Fine for personal use, awkward for anything you're sharing widely.

Some ISPs also use **Carrier Grade NAT (CGNAT)** — they give you a private IP (like `100.x.x.x`) rather than a real public one, and you share a public IP with many other customers. In this case, port forwarding simply doesn't work. You can't forward ports you don't own. If you're behind CGNAT, a tunnel-based approach is your only option.

Check your router's WAN IP. If it looks like `100.x.x.x` or `10.x.x.x`, you're likely behind CGNAT.

## Dynamic DNS

Your ISP changes your home IP periodically — sometimes daily. If you're sharing a URL with anyone, you need it to stay working when the IP changes.

Dynamic DNS (DDNS) solves this: a small client runs on your server (or router), detects when your IP changes, and updates a DNS record automatically. Services like [DuckDNS](https://www.duckdns.org/) (free) or Cloudflare DDNS handle this. Your domain always points to your current home IP.

## Direct internet exposure

With port forwarding, your server is directly reachable from the internet. There's no Cloudflare layer, no VPS in between. Bots will find you and probe for vulnerabilities.

A few things help:
- **Keep software updated** — the most important thing
- **[Fail2ban](https://github.com/fail2ban/fail2ban)** or **[CrowdSec](https://www.crowdsec.net/)** — automatically ban IPs that repeatedly fail authentication
- **Don't expose anything without authentication**

## When this actually makes sense

Port forwarding is a perfectly valid approach when:
- Your ISP doesn't block ports and you're not behind CGNAT
- You're running something personal and IP exposure isn't a concern
- You want zero ongoing cost (no VPS)
- You're comfortable with the security trade-offs

We won't go deeper on the full setup here — this is a signpost. If you go this route, the pieces are: port forward rule in your router settings + DDNS + Traefik is already handling your reverse proxy + keep things patched.

<!-- RESOURCES -->

- [DuckDNS — free dynamic DNS](https://www.duckdns.org/) -- type: tool, time: 10min
- [Fail2ban](https://github.com/fail2ban/fail2ban) -- type: tool, time: 20min
- [CrowdSec](https://www.crowdsec.net/) -- type: tool, time: 20min

<!-- ZH_SUMMARY -->
端口转发是告诉你的路由器：“当来自互联网的流量到达端口 X 时，把它发送到这台本地机器。”不需要 VPS，不需要隧道，也不需要第三方。这是暴露家庭服务的最原始方式，而且它确实有效。

但它带来的权衡是其他方案所没有的。要清楚自己将面对什么。

<!-- ZH_DEEP_DIVE -->
## 端口转发实际做了什么

你的家用路由器有一个公网 IP（由 ISP 分配），并管理其后的私有局域网。通常，来自互联网的入站流量会被丢弃——没有通往你内部机器的路由。

端口转发打了一个洞：到达特定端口的流量会被转发到特定的内部 IP 和端口。从互联网看，像是你的路由器在提供这些流量。实际上，是你的家用服务器在提供。

## 你的家庭 IP 现在是公开的

与 Cloudflare Tunnel 或 VPS 方案不同，任何连接到你的服务的人都能看到你真实的家庭 IP 地址。这不一定是个致命问题，但值得了解。如果你希望保持家庭 IP 私密，请改用基于隧道的方案之一。

## ISP 限制

许多 ISP 会封锁 80（HTTP）和 443（HTTPS）端口的入站流量——这两个是标准 Web 端口。如果你的 ISP 也这样做，你就得使用 8080 或 8443 之类的非标准端口，这意味着 URL 会变成 `https://example.com:8443` 这样。个人使用没问题，但广泛分享时就显得别扭了。

有些 ISP 还使用 **Carrier Grade NAT（CGNAT）**——他们给你一个私有 IP（如 `100.x.x.x`）而不是真正的公网 IP，你与许多其他客户共享一个公网 IP。在这种情况下，端口转发根本无法工作。你无法转发你不拥有的端口。如果你处于 CGNAT 之后，基于隧道的方案是你唯一的选择。

检查你路由器的 WAN IP。如果它看起来像 `100.x.x.x` 或 `10.x.x.x`，你很可能处于 CGNAT 之后。

## 动态 DNS

你的 ISP 会定期更换你的家庭 IP——有时每天都会变。如果你要与任何人分享 URL，你需要它在 IP 变化时仍能正常工作。

动态 DNS（DDNS）解决了这个问题：一个小客户端在你的服务器（或路由器）上运行，检测你的 IP 何时变化，并自动更新 DNS 记录。[DuckDNS](https://www.duckdns.org/)（免费）或 Cloudflare DDNS 等服务可以处理这件事。你的域名始终指向你当前的家庭 IP。

## 直接暴露于互联网

使用端口转发时，你的服务器可以从互联网直接访问。没有 Cloudflare 层，中间也没有 VPS。机器人会找到你并探测漏洞。

以下几件事有帮助：
- **保持软件更新**——最重要的一点
- **[Fail2ban](https://github.com/fail2ban/fail2ban)** 或 **[CrowdSec](https://www.crowdsec.net/)**——自动封禁反复认证失败的 IP
- **不要暴露任何没有认证的东西**

## 什么时候这确实合理

端口转发在以下情况下是完全合理的方法：
- 你的 ISP 不封锁端口，且你不在 CGNAT 之后
- 你运行的是个人用途的东西，IP 暴露不是问题
- 你想要零持续成本（没有 VPS）
- 你能接受这些安全权衡

我们不会在这里深入完整的设置——这只是一个路标。如果你走这条路，需要的组件是：路由器设置中的端口转发规则 + DDNS + Traefik 已经在处理你的反向代理 + 保持补丁更新。

<!-- ZH_RESOURCES -->
- [DuckDNS — 免费动态 DNS](https://www.duckdns.org/) -- 类型: 工具, 时间: 10min
- [Fail2ban](https://github.com/fail2ban/fail2ban) -- 类型: 工具, 时间: 20min
- [CrowdSec](https://www.crowdsec.net/) -- 类型: 工具, 时间: 20min

<!-- ZH_UI -->
1. 理解端口转发的作用及其暴露的内容
2. 了解其局限性（ISP 封锁、动态 IP、暴露家庭 IP）
