---
id: traefik
title: Traefik as Your Reverse Proxy
zone: self-hosting
edges:
  to:
    - id: tls-with-traefik
      question: Routing works — now I want HTTPS on everything
      detail: >-
        My browser keeps showing a 'not secure' warning. I know I need a
        certificate but I don't know how that works — do I have to buy one,
        generate one, or what?
difficulty: 2
tags:
  - self-hosting
  - traefik
  - reverse-proxy
  - docker
  - networking
category: tool
milestones:
  - Run Traefik as a Docker container with a compose file
  - Expose Vaultwarden through Traefik using Docker labels
  - 'Access Vaultwarden by hostname instead of IP:port'
  - Access the Traefik dashboard
title_zh: "Traefik 作为你的反向代理"

---


Traefik runs as a Docker container alongside your other services. It watches the Docker socket for running containers, reads their labels, and automatically creates routing rules — no config file to edit every time you add a service.

The mental model: you add a few labels to any container telling Traefik "route `passwords.yourdomain.com` to me on port 80", and it picks that up immediately.

For the full setup walkthrough, follow this guide: **[Traefik with Docker — blog.esc.sh](https://blog.esc.sh/traefik-docker/)**

<!-- DEEP_DIVE -->

## How Traefik works

Traefik needs access to the Docker socket (`/var/run/docker.sock`) so it can watch what containers are running. When a container starts with `traefik.enable=true` in its labels, Traefik reads the rest of the labels and creates a router automatically.

The key labels on any service you want to expose:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myservice.rule=Host(`myservice.yourdomain.com`)"
  - "traefik.http.services.myservice.loadbalancer.server.port=80"
```

That's the core of it. Traefik handles the rest.

## The shared Docker network

Traefik needs to be on the same Docker network as the containers it routes to. The standard approach is a single shared network — create it once:

```bash
docker network create proxy
```

Then attach both Traefik and your services to it. The detailed setup in the blog post above covers this end to end.

## Local DNS

For `myservice.yourdomain.com` to resolve to your server on your home network, set up a wildcard DNS record pointing to your server's local IP — either in your router, in Pi-hole/AdGuard, or directly in Cloudflare (recommended, since Cloudflare is already managing your domain for TLS).

<!-- RESOURCES -->

- [Traefik with Docker — full setup guide](https://blog.esc.sh/traefik-docker/) -- type: guide, time: 30min
- [Traefik Documentation](https://doc.traefik.io/traefik/) -- type: reference, time: ongoing

<!-- ZH_SUMMARY -->
Traefik 作为 Docker 容器与其他服务一起运行。它会监听 Docker socket 以发现正在运行的容器，读取它们的标签，并自动创建路由规则——每次添加服务时都无需编辑配置文件。

心智模型：你给任意容器添加几个标签，告诉 Traefik“把 `passwords.yourdomain.com` 路由到我这里的 80 端口”，它就会立即识别并生效。

完整的搭建步骤，请参阅本指南：**[Traefik with Docker — blog.esc.sh](https://blog.esc.sh/traefik-docker/)**

<!-- ZH_DEEP_DIVE -->
## Traefik 的工作原理

Traefik 需要访问 Docker socket（`/var/run/docker.sock`），以便监控正在运行的容器。当某个容器在其标签中设置了 `traefik.enable=true` 启动时，Traefik 会读取其余标签并自动创建一个路由器。

要暴露的任何服务上的关键标签：

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myservice.rule=Host(`myservice.yourdomain.com`)"
  - "traefik.http.services.myservice.loadbalancer.server.port=80"
```

这就是核心部分。其余工作由 Traefik 处理。

## 共享的 Docker 网络

Traefik 需要与其路由到的容器位于同一个 Docker 网络上。标准做法是使用一个共享网络——创建一次即可：

```bash
docker network create proxy
```

然后将 Traefik 和你的服务都接入该网络。上面博客文章中的详细设置完整涵盖了这一过程。

## 本地 DNS

要让 `myservice.yourdomain.com` 在你的家庭网络上解析到你的服务器，请设置一条指向服务器本地 IP 的通配符 DNS 记录——可以在路由器中设置，也可以在 Pi-hole/AdGuard 中设置，或直接在 Cloudflare 中设置（推荐，因为 Cloudflare 已经在为你的域名管理 TLS）。

<!-- ZH_RESOURCES -->
- [Traefik 与 Docker 配合使用——完整配置指南](https://blog.esc.sh/traefik-docker/) -- 类型：指南，时长：30 分钟
- [Traefik 文档](https://doc.traefik.io/traefik/) -- 类型：参考，时长：持续更新

<!-- ZH_UI -->
1. 使用 compose 文件将 Traefik 作为 Docker 容器运行
2. 通过 Docker 标签经 Traefik 暴露 Vaultwarden
3. 通过主机名而非 IP:端口访问 Vaultwarden
4. 访问 Traefik 仪表盘
5. 路由已生效——现在我想让所有服务都启用 HTTPS
6. 我的浏览器一直显示“不安全”警告。我知道需要证书，但不知道它如何运作——是必须购买、自行生成，还是怎样？
