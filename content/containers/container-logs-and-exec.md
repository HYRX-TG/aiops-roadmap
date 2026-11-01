---
id: container-logs-and-exec
title: Logs, Exec, and Inspecting Containers
zone: containers
edges:
  to:
    - id: writing-a-dockerfile
      question: I've got enough to debug basics. Now I want to build my own image.
      detail: >-
        I can run containers and poke around inside them. Time to stop using
        other people's images and package my own app.
    - id: container-debugging
      question: Logs aren't enough — the container keeps crashing and I can't tell why.
      detail: >-
        I can see the logs but they don't explain what's happening. The container
        exits with code 137 or just disappears. I need to get inside it or figure
        out how to debug something I can't directly observe.
difficulty: 1
tags:
  - docker
  - containers
  - debugging
  - logs
  - operations
category: practice
milestones:
  - Stream container logs with docker logs -f
  - Filter logs with --tail and --since
  - Open a shell inside a running container with docker exec -it
  - Inspect container metadata and config with docker inspect
  - Check resource usage in real time with docker stats
  - Use docker top to see processes running inside a container
title_zh: "日志、Exec 与容器检查"

---


A container isn't a VM with a persistent terminal — it's a process (or a small group of processes) running in isolation. There's no SSH daemon waiting for you to log in. Docker provides a set of commands to observe and interact with a running container: reading its output, opening a shell inside it, inspecting its configuration, and watching its resource usage in real time.

These tools are your first line of investigation. Getting comfortable with them means you can tell the difference between a container that's working correctly, one that's struggling, and one that's about to fall over.

<!-- DEEP_DIVE -->

## docker logs

Containers write their output to stdout and stderr, and Docker captures that stream automatically. `docker logs` is how you read it.

```bash
# all logs since the container started
docker logs <container>

# follow in real time (like tail -f)
docker logs -f <container>

# last 50 lines only
docker logs --tail 50 <container>

# everything since 10 minutes ago
docker logs --since 10m <container>

# since a specific timestamp
docker logs --since "2024-01-15T10:00:00" <container>
```

The most important thing to understand: **Docker only captures what the process writes to stdout and stderr.** If your application writes logs to a file inside the container (e.g., `/var/log/app.log`), `docker logs` will show nothing useful. This is why the standard practice is to always log to stdout — it works automatically with Docker, Kubernetes, and every log aggregation system.

If you're dealing with an application that insists on writing to files, you can either configure it to use stdout, or use `docker exec` to open a shell and read the file directly.

## docker exec

`docker exec` runs a command inside an already-running container. The most common use is opening an interactive shell:

```bash
# if the image has bash
docker exec -it <container> bash

# for minimal images (alpine, slim variants) that only have sh
docker exec -it <container> sh
```

The `-i` flag keeps stdin open so you can type input. The `-t` flag allocates a pseudo-TTY so the terminal behaves correctly — you get line editing, colors, and proper cursor behavior. Almost always use both together.

You're not just getting a shell on a remote machine — you're inside the container's **filesystem**, **network namespace**, and **environment variables**. The hostname resolves as the container sees it, `/etc/hosts` is the container's version, and the env vars are whatever was set in the image or at `docker run` time.

For non-interactive use, you can run a single command and get the output:

```bash
# print all environment variables
docker exec <container> env

# check a specific file
docker exec <container> cat /etc/nginx/nginx.conf

# run a database query
docker exec <container> psql -U postgres -c "SELECT version();"
```

## docker inspect

`docker inspect` gives you the complete configuration and state of a container as JSON. It covers everything: image, network settings, mounted volumes, environment variables, resource limits, and current state.

```bash
docker inspect <container>
```

The raw output is verbose. Use `--format` with Go template syntax to extract specific fields:

```bash
# container's IP address on the default bridge network
docker inspect <container> --format '{{.NetworkSettings.IPAddress}}'

# all environment variables
docker inspect <container> --format '{{.Config.Env}}'

# exit code (useful for stopped containers)
docker inspect <container> --format '{{.State.ExitCode}}'

# whether the container was OOM-killed
docker inspect <container> --format '{{.State.OOMKilled}}'

# the image the container is running from
docker inspect <container> --format '{{.Config.Image}}'
```

`docker inspect` works on both **running and stopped containers** — which is critical for debugging crashes. The container may be gone from your terminal, but Docker still holds its metadata until you `docker rm` it.

## docker stats

`docker stats` shows a live table of resource usage across your running containers:

```bash
# all running containers
docker stats

# a specific container
docker stats <container>
```

The output updates every second and shows CPU percentage, memory usage vs limit, network I/O, and block I/O. The memory column is particularly useful: `256MiB / 512MiB` means the container is using 256MB of its 512MB limit.

Watch for **steady memory growth** — a container that starts at 50MB and climbs to 450MB over a few hours without ever coming back down is almost certainly leaking memory. `docker stats` is usually how you first notice this.

If you haven't set a memory limit with `docker run -m`, the limit column will show the total RAM on the host. That's not a container limit — it just means you haven't set one.

## docker top

`docker top` lists the processes running inside a container, as seen from the host:

```bash
docker top <container>
```

The output looks like `ps aux` — PIDs, CPU and memory percentages, start time, and the command. Because containers share the host kernel, these are real host PIDs (just namespaced), so they show up here as well as in a regular `ps` on the host.

This is useful for a few things: confirming your application actually started (as opposed to an init process waiting for it), spotting unexpected processes that shouldn't be there, and identifying zombie processes that have accumulated because a parent isn't reaping them.

<!-- RESOURCES -->

- [docker logs reference](https://docs.docker.com/reference/cli/docker/container/logs/)
- [docker exec reference](https://docs.docker.com/reference/cli/docker/container/exec/)
- [docker inspect reference](https://docs.docker.com/reference/cli/docker/inspect/)
- [docker stats reference](https://docs.docker.com/reference/cli/docker/container/stats/)

<!-- ZH_SUMMARY -->
容器不是带有持久终端的虚拟机——它是在隔离环境中运行的一个进程（或一小组进程）。没有 SSH 守护进程等着你登录。Docker 提供了一组命令来观察运行中的容器并与之交互：读取其输出、在其中打开 shell、检查其配置，以及实时查看其资源使用情况。

这些工具是你排查问题的第一道防线。熟练掌握它们，你就能区分出运行正常的容器、正在苦苦挣扎的容器，以及即将崩溃的容器。

<!-- ZH_DEEP_DIVE -->
## docker logs

容器将输出写入 stdout 和 stderr，Docker 会自动捕获这些流。`docker logs` 就是用来读取这些日志的。

```bash
# 自容器启动以来的所有日志
docker logs <container>

# 实时跟随（类似 tail -f）
docker logs -f <container>

# 仅显示最后 50 行
docker logs --tail 50 <container>

# 显示 10 分钟之前至今的全部日志
docker logs --since 10m <container>

# 从指定时间戳开始
docker logs --since "2024-01-15T10:00:00" <container>
```

最重要的一点是：**Docker 只捕获进程写入 stdout 和 stderr 的内容。** 如果你的应用把日志写入容器内的文件（例如 `/var/log/app.log`），`docker logs` 不会显示任何有用的信息。这就是为什么标准做法是始终将日志输出到 stdout——它能自动适配 Docker、Kubernetes 以及所有日志聚合系统。

如果你面对的应用坚持写入文件，你可以将其配置为使用 stdout，或者使用 `docker exec` 打开一个 shell 直接读取该文件。

## docker exec

`docker exec` 在已运行的容器内执行命令。最常见的用法是打开一个交互式 shell：

```bash
# 如果镜像包含 bash
docker exec -it <container> bash

# 对于仅包含 sh 的精简镜像（alpine、slim 变体）
docker exec -it <container> sh
```

`-i` 标志保持 stdin 打开，以便你可以输入内容。`-t` 标志分配一个伪 TTY，使终端行为正常——你可以获得行编辑、颜色和正确的光标行为。几乎总是将两者一起使用。

你不仅仅是在远程机器上获得一个 shell——你身处容器的**文件系统**、**网络命名空间**和**环境变量**之中。主机名按容器所看到的方式解析，`/etc/hosts` 是容器自己的版本，环境变量则是镜像中或 `docker run` 时设置的值。

对于非交互式用途，你可以运行单条命令并获取输出：

```bash
# 打印所有环境变量
docker exec <container> env

# 查看特定文件
docker exec <container> cat /etc/nginx/nginx.conf

# 执行数据库查询
docker exec <container> psql -U postgres -c "SELECT version();"
```

## docker inspect

`docker inspect` 以 JSON 形式提供容器的完整配置和状态。它涵盖一切：镜像、网络设置、挂载的卷、环境变量、资源限制以及当前状态。

```bash
docker inspect <container>
```

原始输出很冗长。使用 `--format` 配合 Go 模板语法来提取特定字段：

```bash
# 容器在默认 bridge 网络上的 IP 地址
docker inspect <container> --format '{{.NetworkSettings.IPAddress}}'

# 所有环境变量
docker inspect <container> --format '{{.Config.Env}}'

# 退出码（对已停止的容器很有用）
docker inspect <container> --format '{{.State.ExitCode}}'

# 容器是否被 OOM 杀死
docker inspect <container> --format '{{.State.OOMKilled}}'

# 容器运行所基于的镜像
docker inspect <container> --format '{{.Config.Image}}'
```

`docker inspect` 对**运行中和已停止的容器**都有效——这对于调试崩溃至关重要。容器可能已从你的终端中消失，但 Docker 仍会保留其元数据，直到你执行 `docker rm`。

## docker stats

`docker stats` 显示所有运行中容器的资源使用情况实时表格：

```bash
# 所有运行中的容器
docker stats

# 特定容器
docker stats <container>
```

输出每秒更新一次，显示 CPU 百分比、内存使用量与限制的对比、网络 I/O 和块 I/O。内存列特别有用：`256MiB / 512MiB` 表示容器正在使用其 512MB 限制中的 256MB。

留意**内存持续增长**——一个容器从 50MB 开始，在几个小时内攀升到 450MB 且从未回落，几乎可以肯定是在泄漏内存。`docker stats` 通常是你最先注意到这一点的方式。

如果你没有通过 `docker run -m` 设置内存限制，限制列将显示主机的总 RAM。那不是容器限制——只是意味着你还没有设置限制。

## docker top

`docker top` 列出容器内运行的进程，从主机视角查看：

```bash
docker top <container>
```

输出看起来像 `ps aux`——PID、CPU 和内存百分比、启动时间以及命令。由于容器共享主机内核，这些是真实的主机 PID（只是经过了命名空间隔离），因此它们既会出现在这里，也会出现在主机上常规的 `ps` 中。

这在几个方面很有用：确认你的应用确实启动了（而不是一个等待它的 init 进程），发现不应存在的意外进程，以及识别因父进程未回收而累积的僵尸进程。

<!-- ZH_RESOURCES -->
- [docker logs 参考](https://docs.docker.com/reference/cli/docker/container/logs/)
- [docker exec 参考](https://docs.docker.com/reference/cli/docker/container/exec/)
- [docker inspect 参考](https://docs.docker.com/reference/cli/docker/inspect/)
- [docker stats 参考](https://docs.docker.com/reference/cli/docker/container/stats/)

<!-- ZH_UI -->
1. 使用 docker logs -f 流式查看容器日志
2. 使用 --tail 和 --since 过滤日志
3. 使用 docker exec -it 在运行中的容器内打开 shell
4. 使用 docker inspect 查看容器元数据和配置
5. 使用 docker stats 实时检查资源使用情况
6. 使用 docker top 查看容器内运行的进程
7. 我已经能调试基础问题了。现在我想构建自己的镜像。
8. 我能运行容器并在里面探索了。是时候不再用别人的镜像，打包我自己的应用了。
9. 光看日志不够——容器一直崩溃，我搞不清原因。
10. 我能看到日志，但它们解释不了发生了什么。容器以退出码 137 退出，或者直接消失了。我需要进入容器内部，或者想办法调试我无法直接观察的东西。
