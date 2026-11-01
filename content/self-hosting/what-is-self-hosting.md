---
id: what-is-self-hosting
title: What Is Self-Hosting?
zone: self-hosting
edges:
  to:
    - id: i-need-hardware
      question: 'OK, I want to try this. Where do I actually run it?'
      detail: >-
        Can I just use my laptop, or do I need dedicated hardware? I don't have
        a server room — I'm not even sure what 'server' means in this context.
difficulty: 1
tags:
  - self-hosting
  - homelab
  - docker
  - privacy
  - open-source
category: concept
milestones:
  - List 3 services you want to run and why
  - Understand why Docker Compose is the standard tool for self-hosting
  - >-
    Know the difference between running a service locally vs. exposing it to the
    internet
title_zh: "什么是自托管？"

---


You have a Linux machine. You know how to SSH into it. Now what?

Self-hosting means running services on hardware you control — your own Dropbox, your own Netflix, your own photo library, your own password manager. The software exists. The communities around it are huge. And the skills you're building on this roadmap are exactly what you need to run it all.

<!-- DEEP_DIVE -->

**What can you actually self-host?**

The short answer: almost anything. The longer answer is a list that keeps growing:

| Category | Cloud service it replaces | Self-hosted alternative |
|---|---|---|
| **File sync** | Dropbox, Google Drive | Nextcloud, Seafile |
| **Photos** | Google Photos, iCloud | Immich |
| **Media streaming** | Netflix, Spotify | Jellyfin, Plex, Navidrome |
| **Password manager** | 1Password, LastPass | Vaultwarden (Bitwarden-compatible) |
| **Home automation** | Google Home, Amazon Alexa | Home Assistant |
| **RSS / reading** | Feedly | Miniflux, FreshRSS |
| **Note-taking** | Notion, Evernote | Joplin, Obsidian sync |
| **Git hosting** | GitHub | Gitea, Forgejo |
| **Bookmarks** | Pocket, Pinboard | Linkding, Wallabag |
| **Ad blocking** | Browser extensions | Pi-hole, AdGuard Home |
| **VPN** | Commercial VPN | WireGuard, Tailscale |

This is not an exhaustive list. The [r/selfhosted](https://www.reddit.com/r/selfhosted/) community adds new ones every week.

If you want an overwhelming list of apps you could self-host, check this out - [Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted)

**Why do people self-host?**

Different people have different reasons. The most common ones:

- **Privacy.** Your data lives on your hardware, not a company's servers. No one is scanning your files or selling your usage patterns.
- **Cost.** After the hardware cost, most services are free. No Dropbox subscription, no Google One storage tier, no Netflix fee.
- **Control.** You decide when to update, what version to run, and what features to enable. You're not subject to a company changing their pricing or shutting down.
- **Learning.** Running real services teaches you things no tutorial can. You'll debug networking issues, manage disk space, set up backups, write cron jobs. It's infrastructure work in miniature.
- **It's fun.** Genuinely. The homelab community is large, welcoming, and enthusiastic.

**How self-hosting actually works**

Most self-hosted services run as Docker containers. A tool called **Docker Compose** lets you define an entire service — its image, ports, volumes, environment variables — in a single YAML file:

```yaml
# docker-compose.yml for Nextcloud (simplified)
services:
  nextcloud:
    image: nextcloud:latest
    ports:
      - "8080:80"
    volumes:
      - ./data:/var/www/html/data
    environment:
      - MYSQL_HOST=db
      - MYSQL_DATABASE=nextcloud
  db:
    image: mariadb:latest
    volumes:
      - ./db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=nextcloud
```

```bash
docker compose up -d   # start everything in the background
docker compose down    # stop everything
docker compose logs -f # watch the logs
```

That's it. Two commands and you have a running service. The container handles dependencies — you don't install PHP, Apache, MariaDB directly on your server. Each service lives in its own isolated environment.

**The three things you'll learn here**

Self-hosting has its own set of practical skills that sit alongside (and reinforce) what the professional SRE path teaches:

1. **Docker Compose** — how to define, run, and manage containerized services. This is the same Docker used in production, just simpler config.

2. **Reverse proxies** — running multiple services means multiple ports. A reverse proxy (Nginx, Caddy, or Traefik) routes traffic by domain name to the right service: `photos.yourdomain.com` → Immich on port 2283, `files.yourdomain.com` → Nextcloud on port 8080.

3. **Access from outside your home** — services on your home network aren't reachable from the internet by default (NAT). Tailscale is the modern answer: a free, easy VPN that connects your devices without port forwarding. For truly public services, you'll learn about port forwarding and dynamic DNS.

**Start small**

Pick one service. Something you'd actually use. Run it locally first — just on your home network, no external access. Get comfortable with Docker Compose, understand how the service works, and make sure it survives a reboot.

Then, when you're ready, expose it to the internet if you want. Or don't — plenty of people run their entire homelab on Tailscale and never open a port to the public internet. Both are valid.

The learning compounds. Every service you add teaches you something. Your second service is easier than your first. Your tenth is almost automatic.

<!-- RESOURCES -->

- [Awesome Self-Hosted (GitHub)](https://github.com/awesome-selfhosted/awesome-selfhosted) -- type: reference, time: ongoing
- [List of Apps to self host - Cleaner Look](https://selfh.st/apps/)
- [r/selfhosted](https://www.reddit.com/r/selfhosted/) -- type: community, time: ongoing

<!-- ZH_SUMMARY -->
你有一台 Linux 机器。你知道如何通过 SSH 登录它。接下来呢？

自托管意味着在你掌控的硬件上运行服务——你自己的 Dropbox、你自己的 Netflix、你自己的照片库、你自己的密码管理器。软件已经存在。围绕它们的社区非常庞大。而你在这条路线图上培养的技能，正是运行这一切所需要的。

<!-- ZH_DEEP_DIVE -->
**你实际上可以自托管什么？**

简短的回答：几乎任何东西。更长的回答是一份不断增长的清单：

| 类别 | 它所替代的云服务 | 自托管替代方案 |
|---|---|---|
| **文件同步** | Dropbox、Google Drive | Nextcloud、Seafile |
| **照片** | Google Photos、iCloud | Immich |
| **媒体流** | Netflix、Spotify | Jellyfin、Plex、Navidrome |
| **密码管理器** | 1Password、LastPass | Vaultwarden（兼容 Bitwarden） |
| **家庭自动化** | Google Home、Amazon Alexa | Home Assistant |
| **RSS / 阅读** | Feedly | Miniflux、FreshRSS |
| **笔记** | Notion、Evernote | Joplin、Obsidian sync |
| **Git 托管** | GitHub | Gitea、Forgejo |
| **书签** | Pocket、Pinboard | Linkding、Wallabag |
| **广告拦截** | 浏览器扩展 | Pi-hole、AdGuard Home |
| **VPN** | 商业 VPN | WireGuard、Tailscale |

这不是一份详尽的清单。[r/selfhosted](https://www.reddit.com/r/selfhosted/) 社区每周都会新增一些。

如果你想看一份令人眼花缭乱的可自托管应用清单，看看这个——[Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted)

**人们为什么自托管？**

不同的人有不同的理由。最常见的几个：

- **隐私。** 你的数据存放在你自己的硬件上，而不是公司的服务器上。没有人会扫描你的文件或出售你的使用模式。
- **成本。** 在硬件成本之后，大多数服务都是免费的。没有 Dropbox 订阅、没有 Google One 存储套餐、没有 Netflix 费用。
- **控制权。** 你决定何时更新、运行哪个版本、启用哪些功能。你不会受制于公司更改定价或关停服务。
- **学习。** 运行真实服务能教给你任何教程都教不了的东西。你会调试网络问题、管理磁盘空间、设置备份、编写 cron 任务。这是微缩版的基础设施工作。
- **它很有趣。** 真的。homelab 社区庞大、友好且充满热情。

**自托管实际上是如何运作的**

大多数自托管服务以 Docker 容器方式运行。一个名为 **Docker Compose** 的工具让你可以在单个 YAML 文件中定义一个完整的服务——它的镜像、端口、卷、环境变量：

```yaml
# docker-compose.yml for Nextcloud (simplified)
services:
  nextcloud:
    image: nextcloud:latest
    ports:
      - "8080:80"
    volumes:
      - ./data:/var/www/html/data
    environment:
      - MYSQL_HOST=db
      - MYSQL_DATABASE=nextcloud
  db:
    image: mariadb:latest
    volumes:
      - ./db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=nextcloud
```

```bash
docker compose up -d   # start everything in the background
docker compose down    # stop everything
docker compose logs -f # watch the logs
```

就这样。两条命令，你就有了一个运行中的服务。容器会处理依赖——你不需要在服务器上直接安装 PHP、Apache、MariaDB。每个服务都运行在自己隔离的环境中。

**你在这里会学到的三件事**

自托管有自己的一套实用技能，它们与专业 SRE 路径所教授的内容并存（并相互强化）：

1. **Docker Compose** ——如何定义、运行和管理容器化服务。这与生产环境中使用的 Docker 相同，只是配置更简单。

2. **反向代理** ——运行多个服务意味着多个端口。反向代理（Nginx、Caddy 或 Traefik）按域名将流量路由到正确的服务：`photos.yourdomain.com` → 端口 2283 上的 Immich，`files.yourdomain.com` → 端口 8080 上的 Nextcloud。

3. **从家庭网络外部访问** ——家庭网络上的服务默认无法从互联网访问（NAT）。Tailscale 是现代答案：一个免费、易用的 VPN，无需端口转发即可连接你的设备。对于真正公开的服务，你会了解端口转发和动态 DNS。

**从小处开始**

选择一个服务。一个你实际会用的服务。先在本地运行它——只在你家庭网络上，不对外访问。熟悉 Docker Compose，理解该服务如何运作，并确保它能在重启后存活。

然后，当你准备好时，如果你愿意，就把它暴露到互联网上。或者不——很多人把整个 homelab 都运行在 Tailscale 上，从不向公共互联网开放端口。两者都是可行的。

学习会不断累积。你添加的每个服务都会教给你一些东西。你的第二个服务比第一个更容易。你的第十个几乎就是自动的。

<!-- ZH_RESOURCES -->
- [Awesome Self-Hosted (GitHub)](https://github.com/awesome-selfhosted/awesome-selfhosted) -- 类型：参考资料，时间：持续更新
- [自托管应用列表 - 更清爽的界面](https://selfh.st/apps/)
- [r/selfhosted](https://www.reddit.com/r/selfhosted/) -- 类型：社区，时间：持续更新

<!-- ZH_UI -->
1. 列出你想运行的 3 个服务及原因
2. 理解为什么 Docker Compose 是自托管的标准工具
3. 了解本地运行服务与将其暴露到互联网的区别
4. 好，我想试试。我到底该在哪里运行它？
5. 我可以直接用笔记本电脑，还是需要专用硬件？我没有机房——甚至不确定这里的“服务器”指什么。
