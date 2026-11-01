---
id: reverse-proxy
title: What Is a Reverse Proxy?
zone: self-hosting
edges:
  to:
    - id: traefik
      question: Makes sense — show me how to set one up with Docker
      detail: >-
        How complex is this to actually set up? I don't want to break what's
        already running, and I've never configured something that sits in front
        of all my other services before.
    - id: getting-a-domain
      question: How do I get a domain name to route to my services?
      detail: >-
        Do I have to buy a real domain for this to work? Or can I use something
        free — or set up names that only work on my home network?
difficulty: 2
tags:
  - self-hosting
  - networking
  - reverse-proxy
  - traefik
category: concept
milestones:
  - Understand what a reverse proxy does and why it's useful
  - 'Understand the difference between accessing by IP:port vs by domain name'
title_zh: "什么是反向代理？"

---


You have three services running. Vaultwarden on port 8080. Immich on port 2283. Jellyfin on port 8096. To use them, you type `192.168.1.100:8080`, `192.168.1.100:2283`, `192.168.1.100:8096`. You'll inevitably mix them up, type the wrong port, or just get tired of it.

A reverse proxy fixes this. You access everything by name instead of port.

```
passwords.home  →  reverse proxy  →  Vaultwarden (:8080)
photos.home     →  reverse proxy  →  Immich (:2283)
media.home      →  reverse proxy  →  Jellyfin (:8096)
```

<!-- DEEP_DIVE -->

**How it works**

A reverse proxy sits in front of all your services. It listens on port 80 (HTTP) and 443 (HTTPS). When a request comes in, it reads the hostname from the request header and forwards it to the right container.

For this to work, your browser needs to resolve `passwords.home` to your server's IP. That's a DNS question — which is why you'll set up a domain name alongside this.

Your services no longer need to publish ports to the host at all. Only the reverse proxy has open ports. Everything else is internal.

**The options**

Three reverse proxies dominate the self-hosting world:

| Tool | Strength | Interface |
|---|---|---|
| **Nginx Proxy Manager** | Easiest setup, GUI-based | Web UI |
| **Caddy** | Clean config syntax, auto-HTTPS | Config file |
| **Traefik** | Docker-native, auto-discovers containers | Docker labels |

For a Docker-based homelab, **Traefik** is the right choice. It watches Docker for running containers, reads their labels, and automatically creates routing rules. Add a label to your Compose service and Traefik picks it up — no proxy config to edit, no restart required.

It also handles TLS certificates from Let's Encrypt automatically, including renewal. Once configured, you never think about certificates again.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你有三个服务在运行。Vaultwarden 在 8080 端口。Immich 在 2283 端口。Jellyfin 在 8096 端口。要使用它们，你需要输入 `192.168.1.100:8080`、`192.168.1.100:2283`、`192.168.1.100:8096`。你难免会把它们搞混、输错端口，或者干脆厌倦了这样。

反向代理可以解决这个问题。你通过名称而不是端口来访问所有服务。

```
passwords.home  →  reverse proxy  →  Vaultwarden (:8080)
photos.home     →  reverse proxy  →  Immich (:2283)
media.home      →  reverse proxy  →  Jellyfin (:8096)
```

<!-- ZH_DEEP_DIVE -->
**工作原理**

反向代理位于所有服务的前端。它监听 80（HTTP）和 443（HTTPS）端口。当请求到达时，它从请求头中读取主机名，并将其转发到正确的容器。

要让这一机制生效，你的浏览器需要将 `passwords.home` 解析到服务器的 IP。这是一个 DNS 问题——因此你需要同时配置一个域名。

你的服务不再需要向宿主机发布端口。只有反向代理开放端口。其他一切都在内部。

**可选方案**

自助托管领域有三款主流反向代理：

| 工具 | 优势 | 接口 |
|---|---|---|
| **Nginx Proxy Manager** | 设置最简单，基于 GUI | Web UI |
| **Caddy** | 配置语法简洁，自动 HTTPS | 配置文件 |
| **Traefik** | Docker 原生，自动发现容器 | Docker 标签 |

对于基于 Docker 的 homelab，**Traefik** 是正确选择。它会监视 Docker 中运行的容器，读取其标签，并自动创建路由规则。为你的 Compose 服务添加一个标签，Traefik 就会识别它——无需编辑代理配置，也无需重启。

它还会自动处理来自 Let's Encrypt 的 TLS 证书，包括续期。配置完成后，你再也无需操心证书。

<!-- ZH_UI -->
1. 理解反向代理的作用及其价值
2. 理解通过 IP:端口 访问与通过域名访问的区别
3. 有道理——演示如何用 Docker 搭建一个
4. 实际搭建有多复杂？我不想破坏已在运行的服务，而且我从没配置过位于所有其他服务前面的东西。
5. 如何让域名路由到我的服务？
6. 必须购买真实域名才能用吗？还是可以用免费的——或者设置仅在家用网络内有效的名称？
