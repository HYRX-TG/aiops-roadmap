---
id: docker-networking
title: 'Docker Networking: How Do Containers Talk to Each Other?'
zone: self-hosting
edges:
  to:
    - id: docker-compose
      question: I understand how it all fits together — now how do I manage it properly?
      detail: >-
        Right now I'm running everything with separate docker run commands. If
        the server restarts I have to retype all of it from memory. And adding a
        new service means more commands to keep track of.
difficulty: 1
tags:
  - self-hosting
  - docker
  - networking
  - containers
category: concept
milestones:
  - >-
    Understand why containers on the default bridge network can't resolve each
    other by name
  - Create a user-defined Docker network
  - Run two containers on the same network and have one reach the other by name
  - Understand that Docker Compose handles this automatically
title_zh: "Docker 网络：容器之间如何通信？"

---


When you run multiple containers — say, an app and its database — they need to communicate. The app needs to reach the database. But containers are isolated. They're not just processes on the same machine sharing a network; each has its own network namespace.

Docker networks are how containers find each other.

<!-- DEEP_DIVE -->

**The default bridge network: bad for multi-container setups**

By default, all containers join Docker's `bridge` network. Containers on this network can reach each other — but only by IP address. And container IPs change every time you stop and start a container.

So the app can reach the database at `172.17.0.3` — until the database container restarts and gets a new IP. Then the connection breaks. This is unusable for production workloads.

**User-defined networks: containers find each other by name**

Create your own network:

```bash
docker network create myapp
```

Start containers on it:

```bash
docker run -d --name postgres --network myapp postgres:16
docker run -d --name myapp --network myapp myapp:latest
```

Now the `myapp` container can reach the database at hostname `postgres` — the container name. Docker's internal DNS resolves `postgres` to the right IP automatically, even after restarts. No hardcoded IPs.

This is how real multi-container apps work. The app connects to the database using its name, not an IP.

**Network isolation as a security feature**

Containers on different networks can't reach each other at all. This is useful:

- Your database containers don't need to be reachable from your reverse proxy network. Put them on a separate internal network.
- Your reverse proxy lives on a public-facing network. Only services that should be exposed are on that network.

You can attach a container to multiple networks:

```bash
docker network connect another-network myapp
```

**You won't do this manually much**

In practice, Docker Compose handles all of this for you. Every Compose stack gets its own user-defined network automatically. Containers in the same `docker-compose.yml` can reach each other by service name without any network configuration. It just works.

Understanding why it works — and what to do when it doesn't — is why this matters.

```bash
# Useful commands
docker network ls                    # list all networks
docker network inspect myapp         # see which containers are on a network
docker network connect net container # attach a container to a network
```

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
当你运行多个容器时——比如一个应用及其数据库——它们需要相互通信。应用需要访问数据库。但容器是相互隔离的。它们不仅仅是同一台机器上共享网络的进程；每个容器都有自己独立的网络命名空间。

Docker 网络就是容器相互发现的方式。

<!-- ZH_DEEP_DIVE -->
**默认 bridge 网络：不适合多容器场景**

默认情况下，所有容器都会加入 Docker 的 `bridge` 网络。该网络上的容器可以互相访问——但只能通过 IP 地址。而且每次停止并启动容器时，容器 IP 都会变化。

因此，应用可以通过 `172.17.0.3` 访问数据库——直到数据库容器重启并获得新 IP。然后连接就断了。这对生产工作负载来说不可用。

**用户自定义网络：容器通过名称互相发现**

创建你自己的网络：

```bash
docker network create myapp
```

在该网络上启动容器：

```bash
docker run -d --name postgres --network myapp postgres:16
docker run -d --name myapp --network myapp myapp:latest
```

现在 `myapp` 容器可以通过主机名 `postgres`（即容器名称）访问数据库。Docker 的内部 DNS 会自动将 `postgres` 解析为正确的 IP，即使容器重启后也是如此。无需硬编码 IP。

真实的多容器应用就是这样工作的。应用使用名称而不是 IP 来连接数据库。

**网络隔离作为安全特性**

不同网络上的容器完全无法互相访问。这很有用：

- 你的数据库容器不需要从反向代理网络可达。将它们放在单独的内部网络上。
- 你的反向代理位于面向公众的网络上。只有应当暴露的服务才在该网络上。

你可以将容器连接到多个网络：

```bash
docker network connect another-network myapp
```

**你很少需要手动做这些**

在实践中，Docker Compose 会为你处理所有这些事情。每个 Compose 栈都会自动获得自己的用户自定义网络。同一个 `docker-compose.yml` 中的容器可以通过服务名互相访问，无需任何网络配置。开箱即用。

理解它为什么能工作——以及当它不工作时该怎么做——正是这件事重要的原因。

```bash
# 常用命令
docker network ls                    # 列出所有网络
docker network inspect myapp         # 查看某个网络上有哪些容器
docker network connect net container # 将容器连接到网络
```

<!-- ZH_UI -->
1. 理解为什么默认桥接网络上的容器无法通过名称互相解析
2. 创建用户自定义的 Docker 网络
3. 在同一网络上运行两个容器，并让其中一个通过名称访问另一个
4. 理解 Docker Compose 会自动处理这一点
5. 我明白各部分如何协同工作了——那现在该如何正确管理它？
6. 目前我用单独的 docker run 命令运行所有东西。服务器重启后，我得凭记忆重新输入所有命令。而添加新服务意味着要跟踪更多命令。
