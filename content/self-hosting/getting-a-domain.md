---
id: getting-a-domain
title: Getting a Domain Name for Your Services
zone: self-hosting
edges:
  to:
    - id: tls-with-traefik
      question: I have a domain — now I want HTTPS on everything
      detail: >-
        My browser still shows a security warning even though everything routes
        correctly. Do I need to buy a certificate? And how do I actually get it
        installed?
difficulty: 1
tags:
  - self-hosting
  - dns
  - domain
  - cloudflare
  - networking
category: concept
milestones:
  - Understand the difference between a public domain and a local hostname
  - Register a domain or set up a free subdomain
  - Point your domain's DNS to Cloudflare
  - >-
    Understand how split-horizon DNS works (resolving to a local IP from inside
    your home)
title_zh: "为你的服务获取域名"

---


Your reverse proxy routes traffic by hostname — `passwords.yourdomain.com` to Vaultwarden, `photos.yourdomain.com` to Immich. For that to work, you need a domain name and you need DNS to resolve it.

You have three paths: use a subdomain of a domain you already own (best), buy a new domain, or use a free subdomain service.

<!-- DEEP_DIVE -->

## Option 1: Use a subdomain of a domain you already own (best)

If you already own a domain — for your blog, portfolio, side project, anything — you can carve out a subdomain for your homelab and never touch DNS again.

The pattern: pick a subdomain like `home.yourdomain.com` and create a single wildcard DNS record pointing to your server's local IP:

```
Type: A
Name: *.home
Content: 192.168.1.100
Proxy status: DNS only
```

Now `vaultwarden.home.yourdomain.com`, `immich.home.yourdomain.com`, `jellyfin.home.yourdomain.com` — all of them resolve to your server automatically. Add a new service in Traefik, and it just works with no DNS changes needed.

For example, `*.home.esc.sh` pointing to a local IP is a perfectly valid setup. The DNS record is public — anyone can look it up — but all they learn is that it resolves to `192.168.1.x`, a private address they can't reach from outside your network. No security concern.

The only requirement: your domain's DNS needs to be managed somewhere that supports wildcard records and the DNS challenge for TLS (Cloudflare is the easiest choice).

## Option 2: Buy a new domain

A `.com` domain costs around $10–12/year. That's less than a single month of most cloud services. It's worth it if you don't already own one.

Register one at [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) — they charge at-cost with no markup, and using Cloudflare for both registration and DNS simplifies the TLS setup that comes next.

## Option 3: Free subdomain services

If you don't want to pay for a domain yet, [DuckDNS](https://www.duckdns.org/) gives you a free `something.duckdns.org` subdomain. It works, and Traefik supports it for TLS. The downside is you're sharing a domain with everyone else on the service, and some features (like wildcard certs) require more config.

For this guide, we'll assume you have a real domain on Cloudflare. The setup is cleaner and the skills transfer directly to production work.

## Setting up DNS

Once your domain is on Cloudflare, create DNS records pointing your subdomains to your server's local IP:

```
Type: A
Name: passwords
Content: 192.168.1.100   ← your server's local IP
Proxy status: DNS only (grey cloud, not orange)
```

Do the same for each service. Or set up a wildcard:

```
Type: A
Name: *
Content: 192.168.1.100
Proxy status: DNS only
```

The wildcard means `anything.yourdomain.com` resolves to your server — you don't need a new DNS record for every new service.

## Why "DNS only" (not proxied)?

Cloudflare can proxy your traffic through their network (the orange cloud). For internal services you're not exposing publicly, set it to DNS only. The orange cloud is for publicly-accessible services and adds Cloudflare's WAF and CDN — overkill for a homelab.

## Split-horizon DNS

Here's something that trips people up: your laptop inside your home asks "what's the IP of passwords.yourdomain.com?" — the DNS answer points to `192.168.1.100`. It connects to your server directly.

Your phone on mobile data asks the same question — it gets the same DNS answer, but `192.168.1.100` is a private IP, unreachable from the internet. The connection fails. That's expected behavior for an internal service. To access your services from outside, you'd use Tailscale (a future topic) rather than exposing them directly.

<!-- RESOURCES -->

- [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) -- type: tool, time: 15min
- [DuckDNS (free subdomain)](https://www.duckdns.org/) -- type: tool, time: 5min

<!-- ZH_SUMMARY -->
你的反向代理按主机名路由流量——`passwords.yourdomain.com` 指向 Vaultwarden，`photos.yourdomain.com` 指向 Immich。要让这套机制生效，你需要一个域名，并且需要 DNS 能解析它。

你有三条路径：使用你已拥有域名的子域名（最佳）、购买新域名，或使用免费子域名服务。

<!-- ZH_DEEP_DIVE -->
## 方案 1：使用你已拥有域名的子域名（最佳）

如果你已经拥有一个域名——用于博客、作品集、副业项目或其他任何用途——你可以为你的 homelab 划出一个子域名，从此再也不用碰 DNS。

模式是这样的：选择一个类似 `home.yourdomain.com` 的子域名，并创建一条指向服务器本地 IP 的通配符 DNS 记录：

```
Type: A
Name: *.home
Content: 192.168.1.100
Proxy status: DNS only
```

现在 `vaultwarden.home.yourdomain.com`、`immich.home.yourdomain.com`、`jellyfin.home.yourdomain.com`——它们全都会自动解析到你的服务器。在 Traefik 中添加一个新服务，它就能直接工作，无需任何 DNS 变更。

例如，`*.home.esc.sh` 指向一个本地 IP 是完全有效的配置。这条 DNS 记录是公开的——任何人都可以查询它——但他们所能了解到的只是它解析到 `192.168.1.x`，这是一个私有地址，他们无法从你的网络外部访问。没有安全问题。

唯一的要求：你的域名的 DNS 需要托管在支持通配符记录和 TLS 的 DNS challenge 的地方（Cloudflare 是最简单的选择）。

## 方案 2：购买一个新域名

一个 `.com` 域名每年大约花费 10–12 美元。这比大多数云服务一个月的费用还少。如果你还没有域名，这是值得的。

在 [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) 注册一个——他们按成本价收费，不加价，并且同时使用 Cloudflare 进行注册和 DNS 可以简化接下来要进行的 TLS 设置。

## 方案 3：免费子域名服务

如果你还不想为域名付费，[DuckDNS](https://www.duckdns.org/) 会给你一个免费的 `something.duckdns.org` 子域名。它可以用，并且 Traefik 支持它为 TLS 提供服务。缺点是你要与该服务上的其他所有人共享一个域名，而且某些功能（如通配符证书）需要更多配置。

在本指南中，我们假设你在 Cloudflare 上拥有一个真实域名。这样设置更简洁，而且这些技能可以直接迁移到生产工作中。

## 设置 DNS

一旦你的域名在 Cloudflare 上，创建 DNS 记录，将你的子域名指向服务器的本地 IP：

```
Type: A
Name: passwords
Content: 192.168.1.100   ← 你服务器的本地 IP
Proxy status: DNS only（灰色云朵，不是橙色）
```

为每个服务做同样的操作。或者设置一个通配符：

```
Type: A
Name: *
Content: 192.168.1.100
Proxy status: DNS only
```

通配符意味着 `anything.yourdomain.com` 会解析到你的服务器——你不需要为每个新服务创建新的 DNS 记录。

## 为什么选择“仅 DNS”（而非代理）？

Cloudflare 可以通过他们的网络代理你的流量（橙色云朵）。对于你不公开暴露的内部服务，将其设置为仅 DNS。橙色云朵适用于可公开访问的服务，并会增加 Cloudflare 的 WAF 和 CDN——对于 homelab 来说是大材小用。

## 分离解析 DNS（Split-horizon DNS）

这里有一点会让人们困惑：你家里的笔记本电脑询问“passwords.yourdomain.com 的 IP 是什么？”——DNS 应答指向 `192.168.1.100`。它直接连接到你的服务器。

你的手机在使用移动数据时问同样的问题——它得到相同的 DNS 应答，但 `192.168.1.100` 是一个私有 IP，无法从互联网访问。连接失败。对于内部服务来说，这是预期行为。要从外部访问你的服务，你会使用 Tailscale（未来的主题），而不是直接暴露它们。

<!-- ZH_RESOURCES -->
- [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) -- 类型：工具，时间：15 分钟
- [DuckDNS（免费子域名）](https://www.duckdns.org/) -- 类型：工具，时间：5 分钟

<!-- ZH_UI -->
1. 理解公共域名与本地主机名之间的区别
2. 注册一个域名或设置一个免费子域名
3. 将你的域名 DNS 指向 Cloudflare
4. 理解分域 DNS 的工作原理（从家庭内部解析到本地 IP）
5. 我已经有了一个域名——现在我想让所有服务都启用 HTTPS
6. 尽管所有路由都正确，我的浏览器仍然显示安全警告。我需要购买证书吗？我该如何实际安装它？
