---
id: tls-with-traefik
title: TLS / HTTPS with Traefik
zone: self-hosting
edges:
  to:
    - id: expose-to-internet
      question: Works locally — now how do I access it when I'm not home?
      detail: >-
        Everything is perfect on my home network. But the moment I'm on my phone
        elsewhere, none of it is reachable. I can't keep being forced to be at
        home to use my own stuff.
difficulty: 2
tags:
  - self-hosting
  - tls
  - https
  - traefik
  - letsencrypt
  - cloudflare
category: practice
milestones:
  - Understand why HTTPS matters even on a home network
  - Configure Traefik with a Let's Encrypt certificate resolver
  - Use Cloudflare DNS challenge (no port forwarding needed)
  - Access all your services over HTTPS with real trusted certificates
title_zh: "使用 Traefik 的 TLS / HTTPS"

---


Vaultwarden won't let you use its browser extension without HTTPS. Many modern browser APIs require a secure context. And plain HTTP means your passwords travel unencrypted over your local network.

HTTPS matters even for internal services. With Traefik and Cloudflare, getting it is nearly automatic — and once configured, you never think about certificates again.

For the full setup walkthrough, follow this guide: **[Traefik with Docker — blog.esc.sh](https://blog.esc.sh/traefik-docker/)**

<!-- DEEP_DIVE -->

## How it works

[Let's Encrypt](https://letsencrypt.org/) issues free, trusted TLS certificates that browsers recognise without warnings. Traefik has built-in support for requesting and renewing them automatically.

The key is using the **DNS challenge** instead of the HTTP challenge. Normally, Let's Encrypt verifies you own a domain by making an HTTP request to it — which requires your server to be reachable from the internet. The DNS challenge proves ownership differently: Traefik creates a temporary DNS TXT record via the Cloudflare API. Let's Encrypt checks for that record. Certificate issued. Your server never needs to be publicly reachable.

## What you need

- A domain on Cloudflare DNS (covered in the previous node)
- A Cloudflare API token with permission to edit DNS records for your zone
- Traefik already running from the previous step

## The end state

Once configured, every service you add gets HTTPS automatically:

1. Add a `docker-compose.yml` with Traefik labels
2. `docker compose up -d`
3. Access at `https://servicename.yourdomain.com` — real trusted cert, no warnings

Traefik stores certificates in a local file and renews them before expiry. You set this up once and forget it exists.

<!-- RESOURCES -->

- [Traefik with Docker — full setup guide](https://blog.esc.sh/traefik-docker/) -- type: guide, time: 30min
- [Cloudflare API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) -- type: guide, time: 5min
- [Let's Encrypt](https://letsencrypt.org/) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
Vaultwarden 不允许在未启用 HTTPS 的情况下使用其浏览器扩展。许多现代浏览器 API 要求安全上下文。而明文 HTTP 意味着你的密码会在本地网络中未经加密地传输。

即便是内部服务，HTTPS 也很重要。借助 Traefik 和 Cloudflare，获取 HTTPS 几乎是自动完成的——而且一旦配置好，你就再也不用操心证书了。

完整的配置步骤，请参阅本指南：**[Traefik with Docker — blog.esc.sh](https://blog.esc.sh/traefik-docker/)**

<!-- ZH_DEEP_DIVE -->
## 工作原理

[Let's Encrypt](https://letsencrypt.org/) 签发免费、受信任的 TLS 证书，浏览器可识别且不会发出警告。Traefik 内置支持自动申请和续期这些证书。

关键在于使用 **DNS challenge** 而非 HTTP challenge。通常，Let's Encrypt 通过向你的域名发起 HTTP 请求来验证你拥有该域名——这要求你的服务器可从互联网访问。DNS challenge 则以不同方式证明所有权：Traefik 通过 Cloudflare API 创建一条临时 DNS TXT 记录。Let's Encrypt 检查该记录。证书签发。你的服务器永远无需公开可访问。

## 你需要什么

- 一个托管在 Cloudflare DNS 上的域名（已在上一节点中介绍）
- 一个具有编辑你所在区域 DNS 记录权限的 Cloudflare API token
- 已从上一步骤运行起来的 Traefik

## 最终状态

配置完成后，你添加的每个服务都会自动获得 HTTPS：

1. 添加一个带有 Traefik labels 的 `docker-compose.yml`
2. `docker compose up -d`
3. 通过 `https://servicename.yourdomain.com` 访问——真实受信任的证书，无警告

Traefik 将证书存储在本地文件中，并在到期前续期。你只需设置一次，之后便可置之不理。

<!-- ZH_RESOURCES -->
- [Traefik 与 Docker — 完整搭建指南](https://blog.esc.sh/traefik-docker/) -- 类型：指南，时长：30 分钟
- [Cloudflare API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) -- 类型：指南，时长：5 分钟
- [Let's Encrypt](https://letsencrypt.org/) -- 类型：参考，时长：5 分钟

<!-- ZH_UI -->
1. 理解为什么即使在家庭网络中 HTTPS 也很重要
2. 为 Traefik 配置 Let's Encrypt 证书解析器
3. 使用 Cloudflare DNS challenge（无需端口转发）
4. 通过 HTTPS 使用真实可信证书访问所有服务
5. 本地运行正常——那我不在家时该如何访问？
6. 在我的家庭网络上一切都很完美。但一旦我在外面用手机，就什么都访问不到。我不能总是被迫待在家里才能使用自己的东西。
