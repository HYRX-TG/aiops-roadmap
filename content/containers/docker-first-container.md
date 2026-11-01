---
id: docker-first-container
title: Running Your First Container
zone: containers
edges:
  to:
    - id: writing-a-dockerfile
      question: I can run containers. Now how do I build one for my own app?
      detail: >-
        I've pulled and run existing images but all of those were someone else's
        app. I need to package my own code into a container — where do I start?
    - id: container-logs-and-exec
      question: Something's broken inside a container. How do I figure out what's going on?
      detail: >-
        The container is running but the app isn't behaving right. I don't have
        a terminal open inside it and I'm not sure how to look at what it's doing
        or what went wrong.
difficulty: 1
tags:
  - docker
  - containers
  - getting-started
category: practice
milestones:
  - Pull and run an existing image with docker run
  - Map a container port to your host with -p
  - Pass environment variables into a container with -e
  - Run a container in the background with -d and check it with docker ps
  - Stop and remove containers with docker stop and docker rm
  - Understand the difference between docker run and docker start
title_zh: "运行你的第一个容器"

---


The fastest way to develop an intuition for containers is to run one before you touch a Dockerfile. There are thousands of production-quality images on Docker Hub — databases, web servers, language runtimes — and you can have any of them running locally in seconds. Getting comfortable with `docker run` and its flags first means you'll understand what a Dockerfile is actually producing when you get to building your own.

This node covers the commands you'll use constantly: running containers, mapping ports, injecting config, checking what's running, and cleaning up. These are the primitives everything else is built on.

<!-- DEEP_DIVE -->

## Your first docker run

```bash
docker run nginx
```

This pulls the official nginx image from Docker Hub if it isn't cached locally, then starts a container from it. The process runs in the **foreground** — you'll see nginx's access logs streaming to your terminal, and pressing Ctrl-C stops the container.

That's useful for experimenting, but most of the time you want the container running in the background. The `-d` flag (detached) does that:

```bash
docker run -d nginx
```

Docker prints a container ID and returns you to the prompt. To confirm it's running:

```bash
docker ps
```

This lists all running containers with their IDs, image names, status, and ports. To stop it:

```bash
docker stop <container-id>
```

You only need enough characters of the ID to make it unambiguous — usually 3-4 is enough.

## Port mapping

A container has its own network namespace — its ports are completely invisible to your host by default. If nginx inside the container listens on port 80, you can't reach it at `localhost:80` without explicitly mapping it.

The `-p` flag maps a host port to a container port:

```bash
docker run -d -p 8080:80 nginx
```

The format is `host:container`. After this, `localhost:8080` on your machine hits port 80 inside the container.

This also means you can run **multiple containers from the same image** simultaneously as long as they map to different host ports:

```bash
docker run -d -p 8080:80 nginx
docker run -d -p 8081:80 nginx
```

Both containers listen on port 80 internally. They're routed to different host ports, so there's no conflict.

## Environment variables

Most container images are configured via environment variables rather than config files. This is by design — it's how you run the same image in dev and production with different settings without modifying the image.

The `-e` flag injects a variable:

```bash
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=myapp postgres
```

Pass multiple variables with multiple `-e` flags. The image's entrypoint reads these at startup and configures the application accordingly.

This pattern extends to Compose files and Kubernetes — they all use environment variables as the primary mechanism for injecting config into containers. Understanding it now makes everything else click.

## Managing containers

**Listing containers:**

```bash
docker ps          # running containers only
docker ps -a       # all containers, including stopped ones
```

Stopped containers still exist on disk until you remove them. `docker ps -a` is how you find them.

**Stopping containers:**

```bash
docker stop <id>   # sends SIGTERM, waits for graceful shutdown (default: 10s), then SIGKILL
docker kill <id>   # sends SIGKILL immediately — no graceful shutdown
```

Prefer `docker stop` — it gives the process a chance to flush buffers and close connections cleanly. Use `docker kill` when something is unresponsive.

**Removing containers:**

```bash
docker rm <id>          # remove a stopped container
docker rm -f <id>       # force stop and remove a running container
```

Two shortcuts worth knowing:

```bash
docker run --rm nginx        # container is automatically removed when it stops
docker run --name myapp nginx  # give the container a name instead of a random one
```

`--rm` is useful for one-off tasks and experiments so you don't accumulate stopped containers. `--name` makes subsequent commands like `docker stop myapp` more readable.

## docker run vs docker start

These do different things and it's worth being clear on the distinction.

`docker run` **creates a new container** from an image every time. Each invocation produces a fresh container with a new writable layer and a new ID.

`docker start` **resumes an existing stopped container** — the one that already exists from a previous `docker run`. Its writable layer and state are preserved.

In practice, treat containers as **disposable**. If something needs updating, stop the old container, remove it, and run a new one from the updated image. Don't reach for `docker start` to resume a specific container's state — that's what volumes are for. The workflow is almost always: run, not start.

<!-- RESOURCES -->

- [docker run reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/run/)
- [docker ps reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/ls/)

<!-- ZH_SUMMARY -->
建立对容器直觉的最快方式，是在接触 Dockerfile 之前先运行一个容器。Docker Hub 上有数千个生产级镜像——数据库、Web 服务器、语言运行时——你可以在几秒内让其中任何一个在本地运行起来。先熟悉 `docker run` 及其标志，意味着当你开始构建自己的镜像时，你会理解 Dockerfile 实际在产出什么。

本节点涵盖你会不断使用的命令：运行容器、映射端口、注入配置、检查正在运行的内容，以及清理。这些是其他一切所构建于其上的原语。

<!-- ZH_DEEP_DIVE -->
## 你的第一次 docker run

```bash
docker run nginx
```

如果本地没有缓存，这条命令会从 Docker Hub 拉取官方 nginx 镜像，然后基于它启动一个容器。进程运行在**前台**——你会看到 nginx 的访问日志实时输出到终端，按 Ctrl-C 即可停止容器。

这对实验很有用，但大多数时候你希望容器在后台运行。`-d` 标志（detached，分离模式）就是做这个的：

```bash
docker run -d nginx
```

Docker 会打印一个容器 ID 并返回提示符。要确认它正在运行：

```bash
docker ps
```

这会列出所有正在运行的容器，包括它们的 ID、镜像名、状态和端口。要停止它：

```bash
docker stop <container-id>
```

你只需要提供足够多的 ID 字符来保证唯一即可——通常 3-4 个就够了。

## 端口映射

容器有自己独立的网络命名空间——默认情况下，它的端口对宿主机完全不可见。如果容器内的 nginx 监听 80 端口，不显式映射的话，你无法通过 `localhost:80` 访问它。

`-p` 标志把宿主机端口映射到容器端口：

```bash
docker run -d -p 8080:80 nginx
```

格式是 `host:container`。执行之后，你机器上的 `localhost:8080` 就会命中容器内的 80 端口。

这也意味着你可以**同时运行多个来自同一镜像的容器**，只要它们映射到不同的宿主机端口：

```bash
docker run -d -p 8080:80 nginx
docker run -d -p 8081:80 nginx
```

两个容器内部都监听 80 端口。它们被路由到不同的宿主机端口，所以没有冲突。

## 环境变量

大多数容器镜像通过环境变量而非配置文件来配置。这是有意为之——这样你就能在开发和生产环境中运行同一个镜像，使用不同的设置，而无需修改镜像。

`-e` 标志注入一个变量：

```bash
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=myapp postgres
```

用多个 `-e` 标志传入多个变量。镜像的 entrypoint 会在启动时读取这些变量，并据此配置应用程序。

这种模式延伸到 Compose 文件和 Kubernetes——它们都把环境变量作为向容器注入配置的主要机制。现在理解了它，其他一切就都通了。

## 管理容器

**列出容器：**

```bash
docker ps          # 仅正在运行的容器
docker ps -a       # 所有容器，包括已停止的
```

已停止的容器在你删除之前仍然存在于磁盘上。`docker ps -a` 就是用来找到它们的。

**停止容器：**

```bash
docker stop <id>   # 发送 SIGTERM，等待优雅关闭（默认：10s），然后发送 SIGKILL
docker kill <id>   # 立即发送 SIGKILL——没有优雅关闭
```

优先使用 `docker stop`——它给进程机会刷新缓冲区并干净地关闭连接。当某个进程无响应时，再用 `docker kill`。

**删除容器：**

```bash
docker rm <id>          # 删除一个已停止的容器
docker rm -f <id>       # 强制停止并删除一个正在运行的容器
```

两个值得知道的快捷方式：

```bash
docker run --rm nginx        # 容器停止时自动删除
docker run --name myapp nginx  # 给容器起个名字，而不是随机名字
```

`--rm` 对一次性任务和实验很有用，这样你就不会积累一堆已停止的容器。`--name` 让后续命令如 `docker stop myapp` 更具可读性。

## docker run 与 docker start

它们做的事情不同，值得把区别讲清楚。

`docker run` 每次都会**从镜像创建一个新容器**。每次调用都会产生一个带有新可写层和新 ID 的全新容器。

`docker start` **恢复一个已存在的停止容器**——也就是之前某次 `docker run` 已经创建的那个。它的可写层和状态会被保留。

在实践中，把容器视为**一次性**的。如果需要更新，就停止旧容器、删除它，然后从更新后的镜像运行一个新容器。不要用 `docker start` 去恢复某个特定容器的状态——那是卷（volume）的用途。工作流几乎总是：run，而不是 start。

<!-- ZH_RESOURCES -->
- [docker run 参考 — Docker Docs](https://docs.docker.com/reference/cli/docker/container/run/)
- [docker ps 参考 — Docker Docs](https://docs.docker.com/reference/cli/docker/container/ls/)

<!-- ZH_UI -->
1. 使用 docker run 拉取并运行现有镜像
2. 使用 -p 将容器端口映射到主机
3. 使用 -e 向容器传入环境变量
4. 使用 -d 在后台运行容器，并用 docker ps 查看
5. 使用 docker stop 和 docker rm 停止并删除容器
6. 理解 docker run 与 docker start 的区别
7. 我会运行容器了。现在如何为自己的应用构建一个容器？
8. 我已经拉取并运行了现有镜像，但那些都是别人的应用。我需要把自己的代码打包进容器——从哪里开始？
9. 容器内部出问题了。我该如何排查发生了什么？
10. 容器在运行，但应用行为不正常。我没有在容器内打开终端，也不确定如何查看它在做什么或哪里出了问题。
