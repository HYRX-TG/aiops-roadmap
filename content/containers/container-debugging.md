---
id: container-debugging
title: Debugging Containers That Crash or Misbehave
zone: containers
edges:
  to:
    - id: writing-a-dockerfile
      question: I can debug running containers. Now I want to build my own image.
      detail: >-
        I've got the debugging tools down. Time to stop using other people's
        images and package my own app.
difficulty: 2
tags:
  - docker
  - containers
  - debugging
  - operations
category: practice
milestones:
  - Understand common exit codes (0, 1, 137, 139) and what they mean
  - Debug a container that exits immediately by overriding the entrypoint
  - Use docker run --rm -it <image> sh to explore an image interactively
  - Debug networking issues between containers with docker network inspect
  - Understand why you can't exec into a stopped container and what to do instead
  - Use a temporary debug sidecar to inspect a broken container's filesystem
title_zh: "调试崩溃或行为异常的容器"

---


`docker logs` gets you far when something is failing noisily. But some failures leave almost nothing to look at: a container that exits before you can exec in, a crash with no error message, a network issue where two containers simply can't reach each other. These situations require a different set of techniques — not just reading output, but reshaping how the container starts so you can get inside and look around.

The core idea behind most container debugging is this: if you can't observe the failure directly, change what the container runs so you can. Override the entrypoint, attach a sidecar, or start a fresh shell from the same image. The container's isolation is the problem, but it's also the tool.

<!-- DEEP_DIVE -->

## Reading exit codes

When a container stops, Docker records the exit code. This is often the first and most useful signal:

```bash
docker inspect <container> --format '{{.State.ExitCode}}'
```

The common ones:

- **exit 0** — the process exited cleanly on its own (not always good — if a server exits with 0, something told it to stop)
- **exit 1** — general application error; check the logs for the actual message
- **exit 137** — the process received SIGKILL; most commonly an out-of-memory kill, but also happens from `docker kill` or a host-level OOM event
- **exit 139** — segfault (SIGSEGV); unusual in interpreted languages, more common with native code or bad memory access in C extensions
- **exit 143** — received SIGTERM; this is the normal signal from `docker stop`, so exit 143 usually means clean shutdown

**Exit 137 is the most commonly misread.** People assume it means "application crashed," but it usually means the kernel or Docker killed it due to memory pressure. Always check:

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

If that's `true`, the container hit its memory limit (or the host ran out of memory) and was killed. The fix is increasing the limit or fixing a memory leak — not debugging the application code.

## Debugging a container that exits immediately

The hardest case: the container starts and exits before you can exec into it. You can't attach to something that's already gone.

The solution is to **override the entrypoint** to get a shell instead of running the application:

```bash
docker run --rm -it --entrypoint sh <image>
# or, if bash is available
docker run --rm -it --entrypoint bash <image>
```

Now you have a shell inside the exact same filesystem environment the application would have run in. From here you can:

- Check that all expected files exist at the right paths
- Inspect environment variables with `env`
- Run the application command manually and watch what happens:
  ```bash
  # run whatever the original CMD was
  python app.py
  # or
  node server.js
  ```
- Check file permissions on the entrypoint script
- Verify the working directory is what the Dockerfile declared

This technique works even if you don't have the Dockerfile — you're exploring the image as-built.

## You can't exec into a stopped container

`docker exec` only works on **running** containers. If the container has exited, exec will refuse:

```
Error response from daemon: container is not running
```

Your options:

1. **Restart and exec quickly** — works if the crash takes a few seconds to manifest, not if it exits in milliseconds
2. **Start with an overridden entrypoint** — `docker run --rm -it --entrypoint sh <image>`, as above. If the container uses specific volumes, mount them the same way: `docker run --rm -it -v mydata:/data --entrypoint sh <image>`
3. **Commit the stopped container to an image** — `docker commit <stopped-container> debug-image`, then `docker run --rm -it --entrypoint sh debug-image`. This captures the filesystem state at the time of the crash, including any files written at runtime.

The commit approach is especially useful when you need to see exactly what was on disk when the crash happened — not just what the original image contained.

## Network debugging between containers

When containers can't reach each other, `docker network inspect` shows the full state of a network:

```bash
docker network inspect <network-name>
```

This shows every container attached to the network, their assigned IP addresses, and their DNS aliases. If a container you expect to find isn't listed, it's on a different network and DNS resolution between them won't work.

From inside a running container, you can test connectivity directly:

```bash
# by container name (Docker's built-in DNS)
ping other-container-name
curl http://other-container-name:8080/health

# by IP if DNS isn't resolving
curl http://172.18.0.3:8080/health
```

Common causes of network failures:
- **Different networks** — containers started without `--network` land on the default bridge, which has no automatic DNS. Containers on user-defined networks get DNS by name automatically.
- **Wrong port** — the application listens on a different port than the one being requested
- **Application not binding to 0.0.0.0** — if the app binds only to `127.0.0.1`, it's unreachable from other containers even on the same network

## Debug sidecars for minimal images

Distroless and scratch-based images contain no shell, no package manager, and often no standard utilities. You cannot exec into them with bash or sh — there's nothing to run.

The solution is a **debug sidecar**: a separate container that shares the target container's namespaces:

```bash
docker run --rm -it \
  --pid container:<target-container-name> \
  --network container:<target-container-name> \
  --volumes-from <target-container-name> \
  ubuntu bash
```

What each flag does:
- `--pid container:<target>` — shares the PID namespace; you can see the target's processes with `ps aux` and send signals to them
- `--network container:<target>` — shares the network namespace; `curl localhost:8080` hits the target's listening port, and `netstat` or `ss` shows the target's connections
- `--volumes-from <target>` — mounts all the same volumes; you can read and write the target's data files

This gives you a full Ubuntu environment with access to the target's runtime state, without modifying the target image at all. Use any debugging tool you need — `strace`, `tcpdump`, `lsof` — by installing it in the sidecar.

<!-- RESOURCES -->

- [Docker exit codes reference](https://docs.docker.com/reference/run/#exit-status)
- [docker network inspect reference](https://docs.docker.com/reference/cli/docker/network/inspect/)
- [docker commit reference](https://docs.docker.com/reference/cli/docker/container/commit/)

<!-- ZH_SUMMARY -->
当某个东西大声报错时，`docker logs` 能帮你解决很多问题。但有些故障几乎不留下任何可供查看的线索：容器在你来得及 exec 进入之前就退出了，崩溃时没有任何错误消息，或者两个容器就是无法互相访问的网络问题。这些情况需要另一套技巧——不只是读取输出，而是重塑容器的启动方式，以便你能进入其中查看周围情况。

大多数容器调试背后的核心思想是：如果你无法直接观察故障，就改变容器运行的内容，以便能够观察。覆盖 entrypoint、附加 sidecar，或者从同一镜像启动一个全新的 shell。容器的隔离是问题所在，但它同时也是工具。

<!-- ZH_DEEP_DIVE -->
## 读取退出码

当容器停止时，Docker 会记录退出码。这通常是最先出现、也最有用的信号：

```bash
docker inspect <container> --format '{{.State.ExitCode}}'
```

常见的退出码：

- **exit 0** — 进程自行正常退出（并不总是好事——如果服务器以 0 退出，说明有东西让它停止了）
- **exit 1** — 通用应用程序错误；查看日志获取实际错误信息
- **exit 137** — 进程收到 SIGKILL；最常见的是内存不足被杀，但也可能来自 `docker kill` 或宿主机级别的 OOM 事件
- **exit 139** — 段错误（SIGSEGV）；在解释型语言中不常见，在原生代码或 C 扩展中的错误内存访问更常见
- **exit 143** — 收到 SIGTERM；这是 `docker stop` 发出的正常信号，所以 exit 143 通常意味着干净关闭

**Exit 137 是最常被误读的。** 人们以为它意味着“应用程序崩溃了”，但它通常意味着内核或 Docker 因内存压力将其杀死。务必检查：

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

如果结果为 `true`，说明容器达到了内存限制（或宿主机内存耗尽）并被杀死。修复方法是提高限制或修复内存泄漏——而不是调试应用程序代码。

## 调试立即退出的容器

最难的情况：容器启动后在你来得及 exec 进入之前就退出了。你无法附加到一个已经消失的东西上。

解决方案是**覆盖 entrypoint**，获得一个 shell 而不是运行应用程序：

```bash
docker run --rm -it --entrypoint sh <image>
# 或者，如果有 bash
docker run --rm -it --entrypoint bash <image>
```

现在你有了一个 shell，位于应用程序原本会运行的完全相同的文件系统环境中。从这里你可以：

- 检查所有预期文件是否存在于正确的路径
- 用 `env` 检查环境变量
- 手动运行应用程序命令并观察发生了什么：
  ```bash
  # 运行原始 CMD 的内容
  python app.py
  # 或
  node server.js
  ```
- 检查 entrypoint 脚本的文件权限
- 验证工作目录是否与 Dockerfile 声明的一致

即使你没有 Dockerfile，这个技巧也有效——你是在探索构建后的镜像。

## 无法 exec 进入已停止的容器

`docker exec` 只对**运行中**的容器有效。如果容器已退出，exec 会拒绝：

```
Error response from daemon: container is not running
```

你的选择：

1. **重启并快速 exec** — 如果崩溃需要几秒钟才显现则有效，如果毫秒级退出则无效
2. **用覆盖的 entrypoint 启动** — `docker run --rm -it --entrypoint sh <image>`，如上所述。如果容器使用了特定卷，以相同方式挂载它们：`docker run --rm -it -v mydata:/data --entrypoint sh <image>`
3. **将停止的容器提交为镜像** — `docker commit <stopped-container> debug-image`，然后 `docker run --rm -it --entrypoint sh debug-image`。这会捕获崩溃时的文件系统状态，包括运行时写入的任何文件。

当你需要确切查看崩溃时磁盘上的内容——而不仅仅是原始镜像包含的内容——commit 方法特别有用。

## 容器之间的网络调试

当容器无法相互访问时，`docker network inspect` 显示网络的完整状态：

```bash
docker network inspect <network-name>
```

这会显示连接到网络的每个容器、分配的 IP 地址以及 DNS 别名。如果你期望找到的容器未列出，说明它在不同的网络上，它们之间的 DNS 解析将无法工作。

在运行中的容器内部，你可以直接测试连通性：

```bash
# 通过容器名（Docker 内置 DNS）
ping other-container-name
curl http://other-container-name:8080/health

# 如果 DNS 无法解析，通过 IP
curl http://172.18.0.3:8080/health
```

网络故障的常见原因：
- **不同的网络** — 未指定 `--network` 启动的容器落在默认 bridge 上，它没有自动 DNS。用户自定义网络上的容器自动获得按名称的 DNS。
- **端口错误** — 应用程序监听的端口与请求的端口不同
- **应用程序未绑定到 0.0.0.0** — 如果应用只绑定到 `127.0.0.1`，即使在同一网络上，其他容器也无法访问它

## 用于最小化镜像的调试 sidecar

Distroless 和基于 scratch 的镜像不包含 shell、包管理器，通常也没有标准工具。你无法用 bash 或 sh exec 进入它们——没有东西可运行。

解决方案是**调试 sidecar**：一个共享目标容器命名空间的独立容器：

```bash
docker run --rm -it \
  --pid container:<target-container-name> \
  --network container:<target-container-name> \
  --volumes-from <target-container-name> \
  ubuntu bash
```

每个标志的作用：
- `--pid container:<target>` — 共享 PID 命名空间；你可以用 `ps aux` 查看目标进程并向它们发送信号
- `--network container:<target>` — 共享网络命名空间；`curl localhost:8080` 会命中目标的监听端口，`netstat` 或 `ss` 显示目标的连接
- `--volumes-from <target>` — 挂载所有相同的卷；你可以读写目标的数据文件

这为你提供了一个完整的 Ubuntu 环境，可以访问目标的运行时状态，而完全不修改目标镜像。在 sidecar 中安装任何你需要的调试工具——`strace`、`tcpdump`、`lsof`。

<!-- ZH_RESOURCES -->
- [Docker 退出码参考](https://docs.docker.com/reference/run/#exit-status)
- [docker network inspect 参考](https://docs.docker.com/reference/cli/docker/network/inspect/)
- [docker commit 参考](https://docs.docker.com/reference/cli/docker/container/commit/)

<!-- ZH_UI -->
1. 理解常见退出码（0、1、137、139）及其含义
2. 通过覆盖 entrypoint 调试立即退出的容器
3. 使用 docker run --rm -it <image> sh 交互式探索镜像
4. 用 docker network inspect 调试容器间的网络问题
5. 理解为何无法 exec 进入已停止的容器以及替代做法
6. 使用临时调试 sidecar 检查损坏容器的文件系统
7. 我能调试运行中的容器了。现在我想构建自己的镜像。
8. 调试工具我已掌握。是时候不再用别人的镜像，打包自己的应用了。
