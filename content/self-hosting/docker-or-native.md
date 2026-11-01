---
id: docker-or-native
title: Docker or Install Natively?
zone: self-hosting
edges:
  to:
    - id: docker-for-self-hosting
      question: Docker it is — how do I get started?
      detail: >-
        I've heard people talk about images and containers but I'm not sure
        where to start. Do I need to build anything, or can I just use what's
        already out there? And how do I actually run something?
    - id: i-want-pain
      question: I want to install everything manually from source
      detail: >-
        I want to know what's actually running, not just trust someone else's
        image. But where do I even start — apt, compiling from source, something
        else? I've never set up a service on bare Linux before.
difficulty: 1
tags:
  - self-hosting
  - docker
  - linux
  - package-management
category: concept
milestones:
  - Understand why Docker is the standard for self-hosting
  - 'Make the call: Docker (recommended) or native install'
title_zh: "Docker 还是原生安装？"

---


You have two options for running self-hosted services: install them natively on the OS (using `apt`, compiling from source, or following each project's install guide), or run them in Docker containers.

Use Docker. This guide only covers Docker.

<!-- DEEP_DIVE -->

**Why not native installs?**

The native path works — for the first service. You install PHP, configure Apache, set up a database, edit config files in `/etc`, write a systemd unit. An hour later, Nextcloud is running.

Then you want to install Vaultwarden. Different language (Rust), different database setup, different config system. Another hour. Then you want Immich — Python dependencies, Redis, microservices. Things start conflicting. You upgrade one package and something else breaks. You can't easily tell which files belong to which service. Rolling back an update means manual work.

This is why Docker was invented.

**What Docker gives you**

Every service runs in an isolated container. The container has its own filesystem, its own dependencies, its own runtime. Services can't conflict with each other. To upgrade Vaultwarden, you pull a new image and restart the container — 30 seconds. To roll back, pull the previous image. To remove a service completely, delete its container and its data directory.

The other thing Docker gives you: a standard format. Every self-hosted service that supports Docker publishes an image on Docker Hub with a ready-to-run configuration. You don't figure out how to install it — you just run the image.

**The self-hosting ecosystem has standardized on Docker**

Browse any self-hosted app's documentation — Immich, Vaultwarden, Jellyfin, Nextcloud, Home Assistant. The installation guide starts with Docker Compose. The community support forums assume Docker. The update instructions are `docker compose pull && docker compose up -d`.

If you install natively, you're going off the beaten path. You'll spend more time on infrastructure and less time actually using your services.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
运行自托管服务有两种选择：直接在操作系统上原生安装（使用 `apt`、从源码编译，或按照各项目的安装指南操作），或者在 Docker 容器中运行。

请使用 Docker。本指南仅涵盖 Docker 方式。

<!-- ZH_DEEP_DIVE -->
**为什么不采用原生安装？**

原生安装路径确实可行——对第一个服务而言。你安装 PHP、配置 Apache、设置数据库、编辑 `/etc` 下的配置文件、编写 systemd 单元。一小时后，Nextcloud 跑起来了。

然后你想安装 Vaultwarden。不同的语言（Rust）、不同的数据库设置、不同的配置系统。又花一小时。接着你想装 Immich——Python 依赖、Redis、微服务。各种冲突开始出现。你升级一个软件包，别的东西就坏了。你很难分辨哪些文件属于哪个服务。回滚一次更新意味着手工操作。

这就是 Docker 被发明出来的原因。

**Docker 为你提供了什么**

每个服务都运行在隔离的容器中。容器有自己的文件系统、自己的依赖、自己的运行时。服务之间不会相互冲突。要升级 Vaultwarden，你拉取新镜像并重启容器——30 秒。要回滚，拉取之前的镜像。要彻底移除一个服务，删除它的容器和数据目录即可。

Docker 给你的另一样东西：一种标准格式。每个支持 Docker 的自托管服务都会在 Docker Hub 上发布一个镜像，附带可直接运行的配置。你不需要研究怎么安装——直接运行镜像就行。

**自托管生态已统一到 Docker 上**

随便浏览任何一个自托管应用的文档——Immich、Vaultwarden、Jellyfin、Nextcloud、Home Assistant。安装指南都以 Docker Compose 开头。社区支持论坛默认你用的是 Docker。更新说明就是 `docker compose pull && docker compose up -d`。

如果你采用原生安装，你就偏离了主流路径。你会花更多时间在基础设施上，而真正使用服务的时间反而更少。

<!-- ZH_UI -->
1. 理解为什么 Docker 是自托管的标准
2. 做出选择：Docker（推荐）还是原生安装
3. 就用 Docker——我该如何开始？
4. 我听过人们谈论镜像和容器，但不确定从哪里开始。我需要自己构建什么吗，还是可以直接用现成的？以及我实际该怎么运行？
5. 我想从源码手动安装一切
6. 我想知道实际在运行什么，而不是盲目信任别人的镜像。但我该从哪里开始——apt、从源码编译，还是别的？我以前从未在裸 Linux 上设置过服务。
