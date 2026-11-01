---
id: container-networking
title: Container Networking
zone: containers
edges:
  to:
    - id: building-images-in-ci
      question: I understand how containers talk to each other. How do I automate building images in CI?
      detail: >-
        The networking model makes sense now. The next thing I need is to stop
        building images manually — I want this to happen automatically when I push code.
difficulty: 2
tags:
  - docker
  - networking
  - containers
  - docker-compose
category: concept
milestones:
  - Understand Docker's default bridge network and its limitations
  - Know how user-defined bridge networks enable container DNS
  - Understand how Compose creates a network per project automatically
  - Know the difference between publishing a port (-p) and exposing one (EXPOSE)
  - Understand when to use host networking and why it's usually the wrong choice
  - Debug connectivity between containers with docker network inspect
title_zh: "容器网络"

---


When Docker Compose lets you use the service name `db` as a hostname, it works because Docker created a network with built-in DNS. The default `docker run` networking doesn't give you this — and understanding why explains a lot about how containers talk to each other and why they sometimes don't.

Networking is also where a lot of confusing behavior lives: a container binds to a port, the other container can't reach it, `curl localhost` works from your laptop but not from inside another container. These failures all have the same root cause — which network a container is on, and whether DNS resolution is available there.

<!-- DEEP_DIVE -->

## The default bridge network

Every Docker installation comes with a default network called `bridge`. When you run `docker run` without specifying a `--network` flag, that container attaches to it automatically.

The limitation is significant: containers on the default bridge network **can reach each other only by IP address, not by name**. Docker does not provide DNS resolution on the default bridge. You'd have to look up the container's IP with `docker inspect`, hardcode it, and hope it doesn't change when the container restarts.

```bash
# list all Docker networks on the host
docker network ls

# inspect the default bridge to see which containers are on it
docker network inspect bridge
```

This is mostly a historical artifact — the default bridge exists for backward compatibility. For anything beyond running a single container, you want a user-defined network.

## User-defined bridge networks

Creating your own network is the fix. User-defined bridge networks get an **embedded DNS server** that resolves container names as hostnames. Any container on the network can reach any other container on that network using its name.

```bash
# create a network
docker network create mynetwork

# attach containers to it at run time
docker run --network mynetwork --name api myapp:latest
docker run --network mynetwork --name db postgres:16

# now 'api' can reach 'db' by name
docker exec -it api curl http://db:5432
```

Isolation is also automatic: containers on different networks **cannot reach each other by default**. If you need two containers from different networks to communicate, you can connect a container to multiple networks with `docker network connect`.

## How Compose networking works

Docker Compose automates the user-defined network setup for you. When you run `docker compose up`, Compose creates a bridge network named `<project>_default` and attaches every service in the file to it. That's the entire reason service names resolve as hostnames — there's nothing magic about Compose itself, it just creates the right network automatically.

```bash
# inspect the network Compose created
docker network inspect myproject_default
```

The project name defaults to the directory name, or can be set explicitly with `--project-name` or the `COMPOSE_PROJECT_NAME` environment variable. If you have two Compose projects running on the same host, their services are on separate networks and cannot reach each other unless you explicitly connect them or use an external network.

## Publishing ports vs exposing them

These two things are often confused because they sound related:

**Publishing a port** (`-p 8080:80` on the command line, or `ports:` in a Compose file) binds a port on the host to a port inside the container. Traffic hitting `host:8080` gets forwarded to `container:80`. This is what makes a service accessible from outside Docker — from your browser, from another machine, from the internet.

**Exposing a port** (`EXPOSE 80` in a Dockerfile, or `expose:` in a Compose file) does nothing at runtime. It's documentation — a signal to operators about which ports the application listens on. It does not publish anything, and it has no effect on whether other containers can reach the service.

The important implication: **containers on the same network can reach each other on any port without any port publishing**. If your `api` service and `db` service are both on `myproject_default`, the API can connect to port 5432 on `db` with no `ports:` declaration on the database service. Port publishing is only needed to make something reachable from outside the Docker network.

## Host and none networking

These are special-purpose modes you'll rarely need in normal application development.

`--network host` removes the network namespace entirely. The container shares the host's network stack directly — no virtual interface, no NAT, no port mapping. Port 8080 inside the container is literally port 8080 on the host. This is occasionally useful for performance-sensitive applications or for tools that need to observe host-level network traffic.

The reason to avoid it in production: the container has unrestricted access to every interface on the host, and any service it opens is immediately exposed on the host's network with no isolation.

`--network none` gives the container no network interface at all. Useful for batch jobs or data processing tasks that should have zero network access as a security constraint.

## Debugging connectivity

When containers can't reach each other, the failure is almost always one of three things: wrong network, DNS not working, or the application binding to the wrong address.

```bash
# which containers are on this network?
docker network inspect <network-name>

# from inside a container — test DNS resolution
docker exec -it <container> nslookup <other-service>

# test HTTP connectivity once DNS resolves
docker exec -it <container> curl http://<other-service>:<port>

# list all networks a container is connected to
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```

**If DNS fails**: the two containers are on different networks. Check `docker network inspect` on both and verify they share one.

**If DNS resolves but connection is refused**: the application isn't listening on that port, or the process crashed. Check `docker logs <container>`.

**If the application binds to `127.0.0.1`**: it will not be reachable from other containers even on the same network. The application must bind to `0.0.0.0` (all interfaces) to accept traffic from the Docker network. This is a common gotcha with development servers that default to loopback-only.

<!-- RESOURCES -->

- [Docker networking overview](https://docs.docker.com/network/)
- [docker network reference](https://docs.docker.com/reference/cli/docker/network/)
- [Networking in Compose](https://docs.docker.com/compose/how-tos/networking/)

<!-- ZH_SUMMARY -->
当 Docker Compose 允许你将服务名 `db` 用作主机名时，它能正常工作是因为 Docker 创建了一个内置 DNS 的网络。默认的 `docker run` 网络不会提供这一能力——理解其中的原因，就能解释很多关于容器之间如何通信、以及为什么有时无法通信的问题。

网络也是许多令人困惑的行为的根源：一个容器绑定了端口，另一个容器却无法访问它；`curl localhost` 在你的笔记本电脑上能正常工作，但从另一个容器内部却不行。这些故障都有相同的根本原因——容器位于哪个网络上，以及该网络上是否可用 DNS 解析。

<!-- ZH_DEEP_DIVE -->
## 默认 bridge 网络

每个 Docker 安装都会自带一个名为 `bridge` 的默认网络。当你运行 `docker run` 且未指定 `--network` 参数时，容器会自动接入该网络。

这一限制影响很大：默认 bridge 网络上的容器**只能通过 IP 地址互相访问，不能通过名称访问**。Docker 在默认 bridge 上不提供 DNS 解析。你只能用 `docker inspect` 查出容器的 IP，把它硬编码进去，然后祈祷容器重启后这个 IP 不会变。

```bash
# list all Docker networks on the host
docker network ls

# inspect the default bridge to see which containers are on it
docker network inspect bridge
```

这主要是历史遗留问题——默认 bridge 的存在是为了向后兼容。除了运行单个容器之外，任何场景都应该使用用户自定义网络。

## 用户自定义 bridge 网络

创建自己的网络就是解决办法。用户自定义 bridge 网络自带一个**内嵌 DNS 服务器**，可以把容器名称解析为主机名。该网络上的任何容器都可以用名称访问同一网络上的其他容器。

```bash
# create a network
docker network create mynetwork

# attach containers to it at run time
docker run --network mynetwork --name api myapp:latest
docker run --network mynetwork --name db postgres:16

# now 'api' can reach 'db' by name
docker exec -it api curl http://db:5432
```

隔离也是自动的：不同网络上的容器**默认无法互相访问**。如果你需要让来自不同网络的两个容器通信，可以用 `docker network connect` 把一个容器接入多个网络。

## Compose 网络的工作原理

Docker Compose 会替你自动完成用户自定义网络的设置。当你运行 `docker compose up` 时，Compose 会创建一个名为 `<project>_default` 的 bridge 网络，并把文件中的每个服务都接入该网络。服务名之所以能解析为主机名，原因全在于此——Compose 本身并没有什么魔法，它只是自动创建了正确的网络。

```bash
# inspect the network Compose created
docker network inspect myproject_default
```

项目名默认取目录名，也可以通过 `--project-name` 或 `COMPOSE_PROJECT_NAME` 环境变量显式设置。如果同一台主机上运行着两个 Compose 项目，它们的服务位于不同的网络上，除非你显式连接它们或使用外部网络，否则无法互相访问。

## 发布端口与暴露端口的区别

这两件事经常被混淆，因为听起来很相关：

**发布端口**（命令行上的 `-p 8080:80`，或 Compose 文件中的 `ports:`）把主机上的一个端口绑定到容器内的一个端口。访问 `host:8080` 的流量会被转发到 `container:80`。正是它让服务可以从 Docker 外部访问——从浏览器、从另一台机器、从互联网。

**暴露端口**（Dockerfile 中的 `EXPOSE 80`，或 Compose 文件中的 `expose:`）在运行时什么都不做。它只是文档——向运维人员说明应用监听哪些端口。它不发布任何东西，也不影响其他容器能否访问该服务。

重要推论：**同一网络上的容器可以在任意端口上互相访问，无需任何端口发布**。如果你的 `api` 服务和 `db` 服务都在 `myproject_default` 上，API 可以直接连接 `db` 的 5432 端口，数据库服务上不需要任何 `ports:` 声明。只有在需要让某个服务从 Docker 网络外部可达时，才需要发布端口。

## host 和 none 网络模式

这些是特殊用途模式，在常规应用开发中很少需要用到。

`--network host` 会完全移除网络命名空间。容器直接共享主机的网络栈——没有虚拟接口、没有 NAT、没有端口映射。容器内的 8080 端口就是主机上的 8080 端口。这对性能敏感的应用，或需要观测主机级网络流量的工具，偶尔有用。

在生产环境中应避免使用它的原因：容器可以不受限制地访问主机上的每一个网络接口，它打开的任何服务都会立即暴露在主机网络上，没有任何隔离。

`--network none` 让容器完全没有网络接口。适用于批处理作业或数据处理任务，作为安全约束要求零网络访问。

## 排查连通性问题

当容器之间无法互相访问时，故障几乎总是以下三种之一：网络不对、DNS 不工作，或应用绑定到了错误的地址。

```bash
# which containers are on this network?
docker network inspect <network-name>

# from inside a container — test DNS resolution
docker exec -it <container> nslookup <other-service>

# test HTTP connectivity once DNS resolves
docker exec -it <container> curl http://<other-service>:<port>

# list all networks a container is connected to
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```

**如果 DNS 解析失败**：两个容器在不同的网络上。对两者分别执行 `docker network inspect`，确认它们共享同一个网络。

**如果 DNS 能解析但连接被拒绝**：应用没有监听该端口，或者进程已经崩溃。检查 `docker logs <container>`。

**如果应用绑定到 `127.0.0.1`**：即使在同一网络上，其他容器也无法访问它。应用必须绑定到 `0.0.0.0`（所有接口）才能接受来自 Docker 网络的流量。这是开发服务器默认只监听回环地址时常见的坑。

<!-- ZH_RESOURCES -->
- [Docker 网络概述](https://docs.docker.com/network/)
- [docker network 参考](https://docs.docker.com/reference/cli/docker/network/)
- [Compose 中的网络](https://docs.docker.com/compose/how-tos/networking/)

<!-- ZH_UI -->
1. 理解 Docker 默认 bridge 网络及其局限性
2. 了解用户自定义 bridge 网络如何实现容器 DNS
3. 理解 Compose 如何自动为每个项目创建网络
4. 了解发布端口（-p）与暴露端口（EXPOSE）的区别
5. 理解何时使用 host 网络，以及为什么它通常是错误选择
6. 使用 docker network inspect 调试容器间的连通性
7. 我理解了容器之间如何通信。如何在 CI 中自动化构建镜像？
8. 网络模型现在清楚了。接下来我需要停止手动构建镜像——我希望在推送代码时自动完成。
