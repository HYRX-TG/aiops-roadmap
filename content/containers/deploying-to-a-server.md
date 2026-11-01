---
id: deploying-to-a-server
title: Running Containers on a Real Server
zone: containers
edges:
  to:
    - id: prod-env-and-secrets
      question: The app is running. How do I handle config and secrets properly in production?
      detail: >-
        I've got the container running on the server but I've been hardcoding
        values and I know that's wrong. Database passwords, API keys — I need
        a proper way to inject these without putting them in the image or
        committing them to git.
difficulty: 2
tags:
  - docker
  - production
  - deployment
  - docker-compose
  - containers
category: practice
milestones:
  - SSH into a server and pull a versioned image from a registry
  - Run the app with docker compose up -d using a production compose file
  - Set restart policies (unless-stopped) so the app survives reboots
  - Verify the deployment with docker ps and docker logs
  - Understand the difference between a local docker-compose.yml and a production override file
  - Know when single-server Compose is enough and when it isn't
title_zh: "在真实服务器上运行容器"

---


Getting a containerized application onto a real server is simpler than it sounds: pull the image, run it with Compose, and make sure it restarts if the process dies or the server reboots. The commands themselves are nearly identical to running Compose locally — the difference is discipline about what goes in the file.

The operational model diverges from local development in a few specific ways: no bind mounts to your source code, no dev database passwords, no exposed debug ports, and restart policies that actually mean something when the server reboots at 3am. Once those habits are in place, single-server Compose is a capable production setup for a wide range of services.

<!-- DEEP_DIVE -->

## Pulling an image on a server

Before you can run anything, the server needs the image. Authenticate once, then pull by a specific tag:

```bash
# authenticate to the registry — credentials stored in ~/.docker/config.json
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# pull a specific versioned image
docker pull ghcr.io/myorg/myapp:a1b2c3d
```

The critical habit here is **never deploying `latest` in production**. `latest` is a moving target — you can't tell what code is running, you can't roll back to a specific version, and a broken push silently replaces your working deployment. Use a git SHA or a semantic version tag. Your CI pipeline should build and tag the image on every merge to main.

## Production Compose file

Your local `docker-compose.yml` is built for development: bind mounts to your source code, dev database credentials, ports exposed for debugging tools. None of that belongs on a production server.

Keep a separate `docker-compose.prod.yml` for production:

```yaml
services:
  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    restart: unless-stopped
    env_file:
      - .env.prod
    ports:
      - "8000:8000"
    depends_on:
      - db

  db:
    image: postgres:16
    restart: unless-stopped
    env_file:
      - .env.prod
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

Key differences from a dev file:
- `image:` instead of `build:` — the image was already built and pushed by CI
- `restart: unless-stopped` on every service
- `env_file:` pointing to a file that lives on the server, not in the repo
- Named volume for database data — not a bind mount to a host directory
- No source code bind mounts

Pass the image tag at deploy time without editing the file:

```bash
IMAGE_TAG=a1b2c3d docker compose -f docker-compose.prod.yml up -d
```

The `${IMAGE_TAG}` in the compose file picks up the environment variable automatically. This is the key to repeatable, scriptable deploys.

## Restart policies

Without a restart policy, a process crash or server reboot leaves your container stopped until someone manually runs it again.

| Policy | Behavior |
|---|---|
| `no` | Never restart (default) |
| `always` | Always restart, including after `docker stop` — inconvenient during maintenance |
| `on-failure` | Only on non-zero exit; accepts optional retry limit: `on-failure:3` |
| `unless-stopped` | Restart unless explicitly stopped; survives Docker daemon restarts and server reboots |

**`unless-stopped` is the right choice for production services.** It means your app comes back automatically after a crash or reboot, but `docker compose stop` actually stops it and keeps it stopped — which is what you want when deploying or doing maintenance.

`always` sounds safer but isn't: it ignores explicit stop commands, which makes controlled restarts and zero-downtime deploys harder to reason about.

## Compose overrides

Compose supports merging multiple files. The second file overrides values from the first:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

A common pattern: `docker-compose.yml` defines the service structure (image, ports, volumes), and `docker-compose.prod.yml` adds or overrides the production-specific values (restart policies, prod env file, resource limits). This keeps you from duplicating service definitions.

An alternative: maintain entirely separate files for dev and prod. This is simpler to reason about if your dev and prod environments differ significantly — no mental model needed for which file overrides which. The tradeoff is that changes to service structure have to be made in both files.

Either approach works. Pick the one that matches how different your environments actually are.

## Verifying after deploy

```bash
# are services running?
docker compose -f docker-compose.prod.yml ps

# tail logs from all services
docker compose -f docker-compose.prod.yml logs -f --tail 100

# is the app actually responding?
curl http://localhost:8000/health
```

"Up" in `docker ps` means the process is alive — the kernel sees the PID running. It does **not** mean the application has finished starting, can connect to its database, or is serving valid responses. A crashed-but-restarting app cycles through "Up" states continuously.

A healthcheck (covered in the next node) gives you an actual signal about whether the application is functional — and lets Compose and Kubernetes act on that signal automatically.

## The ceiling of single-server Compose

Single-server Compose is a legitimate production setup. It handles real traffic for teams shipping real products. But it has hard ceilings you'll eventually hit:

- **Availability**: the server is a single point of failure. It goes down, everything goes down — no redundancy, no automatic failover.
- **Scale**: you're bound to one machine's CPU and RAM. Scaling up means resizing the server and accepting downtime.
- **Zero-downtime deploys**: possible but manual — requires nginx reload tricks, Traefik configuration, or scripted blue-green swaps. Nothing orchestrates it for you.
- **Many services**: as the number of services grows, resource allocation, dependency ordering, and port management become manual coordination problems.

These aren't Compose's failures — they're exactly the problems that container orchestrators were designed to solve. When you hit them, that's the signal to look at Kubernetes or a managed container platform, not to find workarounds.

<!-- RESOURCES -->

- [Docker Compose restart policies reference](https://docs.docker.com/compose/compose-file/05-services/#restart)
- [docker compose up reference](https://docs.docker.com/reference/cli/docker/compose/up/)

<!-- ZH_SUMMARY -->
将容器化应用部署到真实服务器上比听起来简单：拉取镜像，用 Compose 运行它，并确保进程崩溃或服务器重启时能自动重启。这些命令本身与在本地运行 Compose 几乎完全相同——区别在于对文件中该放什么内容的严格把控。

运维模型在几个具体方面与本地开发不同：不绑定挂载源代码，不使用开发数据库密码，不暴露调试端口，以及使用在凌晨 3 点服务器重启时真正有意义的重启策略。一旦养成这些习惯，单服务器 Compose 对于广泛的服务而言就是一种能力足够的生产环境方案。

<!-- ZH_DEEP_DIVE -->
## 在服务器上拉取镜像

在运行任何东西之前，服务器需要先有镜像。先认证一次，然后按特定标签拉取：

```bash
# authenticate to the registry — credentials stored in ~/.docker/config.json
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# pull a specific versioned image
docker pull ghcr.io/myorg/myapp:a1b2c3d
```

这里最关键的习惯是**绝不在生产环境部署 `latest`**。`latest` 是一个移动的目标——你无法知道正在运行的是哪份代码，无法回滚到特定版本，而且一次有问题的推送会悄无声息地替换掉你正常工作的部署。请使用 git SHA 或语义化版本标签。你的 CI 流水线应当在每次合并到 main 时构建并打标签。

## 生产环境 Compose 文件

你本地的 `docker-compose.yml` 是为开发而构建的：绑定挂载到源代码、开发数据库凭据、为调试工具暴露的端口。这些都不应出现在生产服务器上。

为生产环境单独保留一个 `docker-compose.prod.yml`：

```yaml
services:
  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    restart: unless-stopped
    env_file:
      - .env.prod
    ports:
      - "8000:8000"
    depends_on:
      - db

  db:
    image: postgres:16
    restart: unless-stopped
    env_file:
      - .env.prod
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

与开发文件的关键区别：
- 使用 `image:` 而非 `build:`——镜像已由 CI 构建并推送
- 每个服务都设置 `restart: unless-stopped`
- `env_file:` 指向位于服务器上、而非仓库中的文件
- 数据库数据使用命名卷——而不是绑定挂载到宿主机目录
- 没有源代码绑定挂载

部署时传入镜像标签，无需编辑文件：

```bash
IMAGE_TAG=a1b2c3d docker compose -f docker-compose.prod.yml up -d
```

compose 文件中的 `${IMAGE_TAG}` 会自动读取该环境变量。这是实现可重复、可脚本化部署的关键。

## 重启策略

如果没有重启策略，进程崩溃或服务器重启后，你的容器会一直处于停止状态，直到有人手动再次运行它。

| 策略 | 行为 |
|---|---|
| `no` | 从不重启（默认） |
| `always` | 总是重启，包括在 `docker stop` 之后——维护期间很不方便 |
| `on-failure` | 仅在非零退出时重启；接受可选的重试次数上限：`on-failure:3` |
| `unless-stopped` | 除非被显式停止，否则重启；可承受 Docker 守护进程重启和服务器重启 |

**`unless-stopped` 是生产服务的正确选择。** 它意味着你的应用在崩溃或重启后会自动恢复，但 `docker compose stop` 会真正停止它并保持停止——这正是你在部署或维护时想要的行为。

`always` 听起来更安全，但并非如此：它会忽略显式的停止命令，这使得受控重启和零停机部署更难推理。

## Compose 覆盖

Compose 支持合并多个文件。第二个文件会覆盖第一个文件中的值：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

一种常见模式：`docker-compose.yml` 定义服务结构（镜像、端口、卷），而 `docker-compose.prod.yml` 添加或覆盖生产环境特有的值（重启策略、生产环境变量文件、资源限制）。这样可以避免重复定义服务。

另一种选择：为开发和生产维护完全独立的文件。如果你的开发和生产环境差异很大，这种方式更容易理解——无需在脑中构建哪个文件覆盖哪个文件的模型。代价是服务结构的变更必须在两个文件中都进行。

两种方式都可行。选择与你环境实际差异程度相匹配的那一种。

## 部署后验证

```bash
# are services running?
docker compose -f docker-compose.prod.yml ps

# tail logs from all services
docker compose -f docker-compose.prod.yml logs -f --tail 100

# is the app actually responding?
curl http://localhost:8000/health
```

`docker ps` 中的 "Up" 表示进程存活——内核看到 PID 正在运行。它**并不**意味着应用已完成启动、能连接到数据库，或正在提供有效响应。一个崩溃但正在重启的应用会不断在 "Up" 状态之间循环。

健康检查（将在下一节介绍）能为你提供应用是否真正可用的实际信号——并让 Compose 和 Kubernetes 能基于该信号自动采取行动。

## 单服务器 Compose 的上限

单服务器 Compose 是一种合理的生产环境方案。它能承载团队交付真实产品所需的真实流量。但它存在你最终会触及的硬性上限：

- **可用性**：服务器是单点故障。它宕机，一切就都宕机——没有冗余，没有自动故障转移。
- **规模**：你受限于单台机器的 CPU 和内存。扩容意味着调整服务器规格并接受停机。
- **零停机部署**：可行但需手动操作——需要 nginx reload 技巧、Traefik 配置或脚本化的蓝绿切换。没有任何东西为你编排这些。
- **大量服务**：随着服务数量增长，资源分配、依赖排序和端口管理会变成手动协调问题。

这些并非 Compose 的失败——它们正是容器编排器被设计来解决的问题。当你触及这些上限时，这就是该考虑 Kubernetes 或托管容器平台的信号，而不是去寻找变通方案。

<!-- ZH_RESOURCES -->
- [Docker Compose 重启策略参考](https://docs.docker.com/compose/compose-file/05-services/#restart)
- [docker compose up 参考](https://docs.docker.com/reference/cli/docker/compose/up/)

<!-- ZH_UI -->
1. SSH 登录服务器，从镜像仓库拉取带版本号的镜像
2. 使用生产 compose 文件，通过 docker compose up -d 运行应用
3. 设置重启策略（unless-stopped），让应用在重启后仍能存活
4. 用 docker ps 和 docker logs 验证部署
5. 理解本地 docker-compose.yml 与生产 override 文件的区别
6. 知道单服务器 Compose 何时够用、何时不够用
7. 应用已在运行。生产环境中我该如何正确处理配置和密钥？
8. 容器已在服务器上跑起来了，但我一直在硬编码配置值，我知道这是错的。数据库密码、API key——我需要一种正确的方式注入它们，既不放进镜像，也不提交到 git。
