---
id: debugging-compose
title: Debugging Docker Compose Issues
zone: containers
edges:
  to:
    - id: building-images-in-ci
      question: Compose is working reliably. How do I automate building images in CI?
      detail: >-
        My local stack runs cleanly and I can debug it when things go wrong.
        The next problem is that I'm still building images by hand — I need
        this automated.
difficulty: 2
tags:
  - docker
  - docker-compose
  - debugging
  - networking
  - operations
category: practice
milestones:
  - Stream logs from all services at once with docker compose logs -f
  - Understand why a service keeps restarting by reading its exit code
  - Use depends_on health conditions to fix service startup ordering issues
  - Inspect the Compose-managed network with docker network inspect
  - Override a single service's command to debug it interactively
  - Use docker compose config to validate and view the resolved compose file
title_zh: "调试 Docker Compose 问题"

---


A Compose stack that's misbehaving falls into a few categories: a service crashing on startup, services that can't reach each other, or a startup ordering problem where the app starts before the database is ready. Each has a specific place to look, and the tools to diagnose them are all built into Docker.

The debugging workflow is almost always the same: check logs first, then check exit codes to understand why something died, then inspect the network or config if the problem is connectivity or misconfiguration rather than a crash.

<!-- DEEP_DIVE -->

## Following logs across services

Logs are where you start. `docker compose logs -f` streams output from all services simultaneously, with each line prefixed by the service name:

```bash
# All services
docker compose logs -f

# One specific service
docker compose logs -f app

# Start from the last 100 lines then follow
docker compose logs --tail 100 -f db

# Logs without following (useful for a service that already exited)
docker compose logs app
```

What you're looking for: error messages, unexpected output, a service that starts up and immediately goes silent (often means it exited), or a service that prints a startup message but never gets to "ready."

One thing that trips people up: if a service keeps restarting, `docker compose logs` still shows logs from previous runs. You don't lose the error output from a crashed container just because it restarted.

## Services that keep restarting

`docker compose ps` shows each service's current state. A service in a restart loop shows something like `Restarting (1) 2 seconds ago`. The exit code tells you why it died.

```bash
# Get the container ID
docker compose ps

# Inspect the exit code
docker inspect <container_name_or_id> --format '{{.State.ExitCode}}'
```

Common exit codes and what they mean:

- **Exit 0**: clean exit — the process ran to completion and stopped. If it shouldn't have stopped, the app's main process exited intentionally (e.g., a migration script that was left as the CMD).
- **Exit 1**: application error — the process crashed. Check logs for the stack trace or error message.
- **Exit 137**: the container was killed with SIGKILL. Most commonly an OOM kill (out of memory). Check your memory limits or look for a memory leak.
- **Exit 143**: received SIGTERM — the container was asked to stop gracefully. Usually expected during `docker compose down`.

For OOM kills, you can confirm with:

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

## Startup ordering problems

`depends_on` is the most commonly misunderstood Compose feature. By default, it only waits for the dependent container to **start** — not for the service running inside it to be ready. A Postgres container starts in under a second, but Postgres itself takes several seconds to initialize its data directory and begin accepting connections.

The result: your app starts, tries to connect to the database, gets "connection refused," and crashes — even though `depends_on: db` is set.

Fix it with a healthcheck and a `condition`:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
```

With `condition: service_healthy`, Compose waits until the `db` healthcheck passes before starting `app`. `pg_isready` is a Postgres utility that returns success only when the database is accepting connections.

For other services, use the appropriate readiness check:

```yaml
# Redis
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

Note that `condition: service_healthy` requires a healthcheck to be defined on the dependency. If there's no healthcheck, Compose will error rather than fall back to the default behavior.

## Network debugging

All services in a Compose project share a default network named `<project>_default` (where `<project>` is the directory name by default). Services are reachable by their service name as the hostname.

If a service can't reach another, start by getting a shell inside the failing container:

```bash
docker compose exec app sh
# or bash if the image has it
docker compose exec app bash
```

From inside, test connectivity:

```bash
# DNS resolution
ping db

# Port connectivity (requires curl or nc to be installed in the image)
curl -v http://db:5432
nc -zv db 5432
```

If `ping db` fails with a DNS error, the containers may be on different networks. Inspect the project network to see which containers are attached:

```bash
docker network inspect <project>_default
```

Look for the `Containers` section — it lists every container on that network. If a container is missing, check whether it belongs to a different Compose project or was started outside of Compose.

If you created additional named networks in your Compose file, make sure both services are listed under `networks` for the network they need to use.

## Overriding service command for debugging

Sometimes you need to poke around inside a container before the application starts — inspect environment variables, check whether a file is where you expect it, or run a command manually.

```bash
# Start the service with a shell instead of its normal CMD
docker compose run --entrypoint sh app

# Or for images that have bash
docker compose run --entrypoint bash app
```

This starts a fresh container using the same image, environment, and volumes as the `app` service, but drops you into a shell. The application itself doesn't start. From here you can:

```bash
# Check environment variables
env | grep DATABASE

# Verify a file exists
ls -la /app/config

# Try running the app manually to see its error output
python main.py
```

Use `docker compose run` (not `exec`) when the container isn't running or when you want a clean environment without the existing running process.

## Validating the compose file

Before spending time debugging what looks like a runtime issue, check whether the compose file itself is the problem:

```bash
docker compose config
```

This prints the fully resolved configuration: environment variable substitutions are applied, `env_file` entries are expanded, and any overrides from multiple Compose files are merged. If a variable you expected to be set shows as empty, it will be obvious here.

It also catches syntax errors and invalid keys before you try to run anything. Running `docker compose config` is a fast first check when you change the compose file and things stop working.

```bash
# Validate without printing the full config
docker compose config --quiet && echo "Config is valid"
```

<!-- RESOURCES -->

- [Docker Compose CLI reference](https://docs.docker.com/compose/reference/)
- [Docker Compose file reference: depends_on and healthcheck](https://docs.docker.com/compose/compose-file/05-services/#depends_on)

<!-- ZH_SUMMARY -->
一个行为异常的 Compose 栈通常可归为几类问题：服务在启动时崩溃、服务之间无法互相访问，或者启动顺序问题——应用在数据库就绪之前就启动了。每一类问题都有特定的排查位置，而诊断它们所需的工具都内置于 Docker 中。

调试流程几乎总是相同的：先检查日志，再检查退出码以了解某个服务为何终止，如果问题属于连接性或配置错误而非崩溃，则检查网络或配置。

<!-- ZH_DEEP_DIVE -->
## 跨服务跟踪日志

日志是你排查问题的起点。`docker compose logs -f` 会同时流式输出所有服务的日志，每一行都带有服务名前缀：

```bash
# 所有服务
docker compose logs -f

# 某个特定服务
docker compose logs -f app

# 从最后 100 行开始跟踪
docker compose logs --tail 100 -f db

# 不跟踪的日志（适用于已经退出的服务）
docker compose logs app
```

你要找的是：错误消息、意外输出、启动后立刻没了动静的服务（通常意味着它退出了），或者打印了启动消息却始终没有进入“就绪”状态的服务。

有一个容易让人困惑的地方：如果某个服务不断重启，`docker compose logs` 仍然会显示之前几次运行的日志。容器崩溃后即使重启了，你也不会丢失崩溃时的错误输出。

## 不断重启的服务

`docker compose ps` 会显示每个服务的当前状态。处于重启循环中的服务会显示类似 `Restarting (1) 2 seconds ago` 的信息。退出码会告诉你它为什么退出。

```bash
# 获取容器 ID
docker compose ps

# 查看退出码
docker inspect <container_name_or_id> --format '{{.State.ExitCode}}'
```

常见退出码及其含义：

- **退出码 0**：正常退出——进程运行完毕并停止。如果它本不该停止，说明应用的主进程是有意退出的（例如，一个迁移脚本被留作了 CMD）。
- **退出码 1**：应用错误——进程崩溃了。查看日志中的堆栈跟踪或错误消息。
- **退出码 137**：容器被 SIGKILL 杀死。最常见的是 OOM 杀死（内存不足）。检查你的内存限制，或查找内存泄漏。
- **退出码 143**：收到 SIGTERM——容器被要求优雅停止。通常在 `docker compose down` 期间是预期行为。

对于 OOM 杀死，你可以用以下命令确认：

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
```

## 启动顺序问题

`depends_on` 是 Compose 中最常被误解的功能。默认情况下，它只等待依赖容器**启动**——而不是等待其中运行的服务就绪。Postgres 容器不到一秒就能启动，但 Postgres 本身需要几秒钟来初始化数据目录并开始接受连接。

结果就是：你的应用启动，尝试连接数据库，得到“connection refused”，然后崩溃——即使已经设置了 `depends_on: db`。

用健康检查和 `condition` 来修复：

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
```

使用 `condition: service_healthy` 后，Compose 会等到 `db` 的健康检查通过后才启动 `app`。`pg_isready` 是 Postgres 的一个工具，只有在数据库接受连接时才返回成功。

对于其他服务，使用相应的就绪检查：

```yaml
# Redis
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

注意，`condition: service_healthy` 要求依赖服务上定义了健康检查。如果没有健康检查，Compose 会报错，而不是回退到默认行为。

## 网络调试

Compose 项目中的所有服务共享一个名为 `<project>_default` 的默认网络（其中 `<project>` 默认是目录名）。服务可以通过其服务名作为主机名来访问。

如果某个服务无法访问另一个服务，首先进入出故障的容器内部获取一个 shell：

```bash
docker compose exec app sh
# 或者如果镜像有 bash
docker compose exec app bash
```

从容器内部测试连通性：

```bash
# DNS 解析
ping db

# 端口连通性（需要镜像中安装了 curl 或 nc）
curl -v http://db:5432
nc -zv db 5432
```

如果 `ping db` 因 DNS 错误失败，容器可能位于不同的网络上。检查项目网络以查看哪些容器已连接：

```bash
docker network inspect <project>_default
```

查找 `Containers` 部分——它列出了该网络上的每个容器。如果某个容器不在其中，检查它是否属于不同的 Compose 项目，或者是在 Compose 之外启动的。

如果你在 Compose 文件中创建了额外的命名网络，确保两个服务都列在它们需要使用的网络的 `networks` 下。

## 覆盖服务命令以进行调试

有时你需要在应用启动之前进入容器内部查看——检查环境变量、确认文件是否在预期位置，或者手动运行命令。

```bash
# 用 shell 代替正常的 CMD 启动服务
docker compose run --entrypoint sh app

# 或者对于有 bash 的镜像
docker compose run --entrypoint bash app
```

这会使用与 `app` 服务相同的镜像、环境和卷启动一个新容器，但会把你带入一个 shell。应用本身不会启动。在这里你可以：

```bash
# 检查环境变量
env | grep DATABASE

# 验证文件是否存在
ls -la /app/config

# 尝试手动运行应用以查看其错误输出
python main.py
```

当容器未运行，或者你想要一个没有现有运行进程的干净环境时，使用 `docker compose run`（而不是 `exec`）。

## 验证 compose 文件

在花时间调试看起来像运行时问题之前，先检查 compose 文件本身是否有问题：

```bash
docker compose config
```

这会打印完全解析后的配置：环境变量替换已应用，`env_file` 条目已展开，来自多个 Compose 文件的任何覆盖已合并。如果你期望设置的变量显示为空，在这里会很明显。

它还会在你尝试运行任何东西之前捕获语法错误和无效的键。当你修改了 compose 文件后东西停止工作，运行 `docker compose config` 是一个快速的初步检查。

```bash
# 验证但不打印完整配置
docker compose config --quiet && echo "Config is valid"
```

<!-- ZH_RESOURCES -->
- [Docker Compose CLI 参考](https://docs.docker.com/compose/reference/)
- [Docker Compose 文件参考：depends_on 与 healthcheck](https://docs.docker.com/compose/compose-file/05-services/#depends_on)

<!-- ZH_UI -->
1. 使用 docker compose logs -f 一次性流式查看所有服务的日志
2. 通过读取退出码理解服务为何反复重启
3. 使用 depends_on 健康条件修复服务启动顺序问题
4. 用 docker network inspect 检查 Compose 管理的网络
5. 覆盖单个服务的 command 以交互方式调试它
6. 使用 docker compose config 验证并查看解析后的 compose 文件
7. Compose 已稳定运行。如何在 CI 中自动化构建镜像？
8. 我的本地栈运行正常，出问题时我也能调试。下一个问题是我仍在手动构建镜像——我需要将其自动化。
