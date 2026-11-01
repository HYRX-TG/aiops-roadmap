---
id: healthchecks-and-monitoring
title: Healthchecks and Monitoring Containers
zone: containers
edges:
  to:
    - id: why-kubernetes
      zone: kubernetes
      question: Single-server Docker is getting limiting. How do I run this at scale?
      detail: >-
        I've got one server working well but I need more resilience — if the
        server goes down, everything goes down. I also can't scale horizontally
        without a lot of manual work. Is there something better?
difficulty: 2
tags:
  - docker
  - monitoring
  - healthchecks
  - production
  - observability
category: practice
milestones:
  - Add a HEALTHCHECK instruction to a Dockerfile
  - Understand the three container health states (starting, healthy, unhealthy)
  - Use docker inspect to read a container's health status and history
  - Configure depends_on health conditions so services wait for dependencies to be ready
  - Use docker stats for basic resource monitoring
  - Know the limits of docker stats and when to reach for a proper monitoring stack
title_zh: "健康检查与监控容器"

---


A container showing "Up" in `docker ps` means the process is alive. It doesn't mean the application is serving traffic, hasn't deadlocked, or can reach its database. Healthchecks let you define what "healthy" actually means for your specific application — and Docker, Compose, and Kubernetes all use that definition to make operational decisions automatically.

Without a healthcheck, you're flying blind. The runtime knows the process is running. It has no idea whether the process is doing anything useful.

<!-- DEEP_DIVE -->

## What a healthcheck does

A healthcheck is a command Docker runs periodically inside the running container. The semantics are simple: **exit 0 means healthy, exit 1 means unhealthy**. Docker tracks the results over time and transitions the container through three health states.

Those states are used by:
- Compose `depends_on` conditions — to hold dependent services until this one is ready
- Kubernetes readiness and liveness probes — to control traffic routing and restart decisions
- Docker itself — to trigger a restart when combined with an appropriate restart policy

Without a healthcheck, these systems can only see process state. With one, they can see application state.

## Adding a HEALTHCHECK in a Dockerfile

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

The parameters:

| Flag | Default | Meaning |
|---|---|---|
| `--interval` | 30s | How often to run the check |
| `--timeout` | 30s | How long before the check is considered failed |
| `--start-period` | 0s | Grace period after start — failures during this window don't count |
| `--retries` | 3 | Consecutive failures before marking unhealthy |

**`--start-period` is important.** Applications that take time to initialize — warming caches, running migrations, establishing connection pools — will fail health checks during startup. Without a start period, those failures count toward the retry limit and the container gets marked unhealthy before it ever finishes starting. Set it to slightly longer than your p95 startup time.

### What the health endpoint should check

Don't just check that the port is open. Check that the application is actually functional:

```python
@app.get("/health")
def health():
    # verify database connection is alive
    db.execute("SELECT 1")
    # verify any other critical dependency
    cache.ping()
    return {"status": "ok"}
```

A health endpoint that only returns 200 without checking dependencies will pass the check while the application fails every real request because the database is down. The check is only useful if it reflects actual application health.

## The three health states

- **starting** — the container has just started and is within the `--start-period` grace window. Failures during this period don't count toward the retry limit.
- **healthy** — the last N consecutive checks passed (where N is `--retries`).
- **unhealthy** — the last N consecutive checks failed. With `restart: unless-stopped`, Docker will restart the container automatically.

The transition from starting → healthy requires passing checks. The transition from healthy → unhealthy requires failing `--retries` consecutive checks, which provides protection against transient blips.

## Reading health status

```bash
# current health status (starting / healthy / unhealthy)
docker inspect <container> --format '{{.State.Health.Status}}'

# full health object with recent check results
docker inspect <container> --format '{{json .State.Health}}' | jq .
```

The full health object includes the output and exit code of each recent check. When a healthcheck is failing and you can't tell why, this is where you look:

```bash
docker inspect <container> --format '{{json .State.Health.Log}}' | jq '.[0]'
```

The `Output` field shows exactly what the check command printed before exiting — the actual error message from `curl`, `pg_isready`, or whatever command you're using. This is the fastest way to debug a container stuck in "unhealthy".

## Compose and health conditions

By default, `depends_on` only waits for the container to start — not for the service inside it to be ready. This causes flapping on startup: the app container starts, tries to connect to the database before Postgres has finished initializing, crashes, and restarts in a loop.

With a healthcheck defined, you can tell Compose to actually wait:

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env.prod
```

`condition: service_healthy` tells Compose to hold the `app` container until `db` passes its healthcheck. The app no longer starts before the database is ready.

Available conditions:
- `service_started` — default, container is running (does not check health)
- `service_healthy` — container has passed its healthcheck
- `service_completed_successfully` — for one-shot containers like migrations

## docker stats for resource monitoring

```bash
# live stats for all running containers
docker stats

# single container
docker stats <container-name>
```

The output:

```
CONTAINER ID   NAME    CPU %   MEM USAGE / LIMIT   MEM %   NET I/O       BLOCK I/O
a1b2c3d4e5f6   app     2.3%    128MiB / 512MiB     25%     1.2MB / 800kB 0B / 4MB
```

What to watch for:
- **Steady memory growth** over hours or days — likely a memory leak; the container will eventually get OOM killed
- **CPU consistently near 100%** — the container is saturated; check if it's doing something unexpected or needs a resource limit increase
- **Memory limit column showing total host RAM** — you haven't set a `mem_limit` in Compose. Set one before going to production, or a runaway process can take down the entire server

Set limits in your Compose file:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          memory: 256M
```

## The limits of docker stats

`docker stats` shows current snapshots only. It has no memory — "what was memory doing three hours ago?" is not a question it can answer. It provides no alerting, no dashboards, and no trend analysis.

For production monitoring with history and alerting, you need an external stack:

**Self-hosted:**
- **cAdvisor** — exports container resource metrics (CPU, memory, network, disk I/O) to Prometheus
- **Prometheus** — stores metrics with retention
- **Grafana** — dashboards and alerting on top of Prometheus

The stack is a few compose services and a standard configuration. cAdvisor runs as a privileged container with access to Docker's cgroups and emits per-container metrics on a `/metrics` endpoint.

**Managed:**
- AWS CloudWatch Container Insights, Google Cloud Monitoring, Datadog — all support Docker metric collection with minimal configuration

For a single-server Docker deployment, `docker stats` combined with healthchecks that trigger automatic restarts covers most operational needs. The gap is history and alerting — if you want to know about a problem before users report it, or diagnose what happened after the fact, you need a real monitoring stack.

<!-- RESOURCES -->

- [Docker HEALTHCHECK reference](https://docs.docker.com/reference/dockerfile/#healthcheck)
- [cAdvisor — Container Advisor](https://github.com/google/cadvisor)
- [Prometheus getting started](https://prometheus.io/docs/prometheus/latest/getting_started/)

<!-- ZH_SUMMARY -->
在 `docker ps` 中显示为 "Up" 的容器只表示进程还活着。它并不意味着应用正在处理流量、没有发生死锁，或者能够连接到数据库。健康检查让你可以为自己的特定应用定义"健康"的实际含义——Docker、Compose 和 Kubernetes 都会使用这个定义来自动做出运维决策。

没有健康检查，你就是在盲飞。运行时知道进程在运行，却完全不知道这个进程是否在做任何有用的事。

<!-- ZH_DEEP_DIVE -->
## 健康检查的作用

健康检查是 Docker 在运行中的容器内定期执行的命令。其语义很简单：**退出码 0 表示健康，退出码 1 表示不健康**。Docker 会持续跟踪检查结果，并让容器在三种健康状态之间转换。

这些状态被以下系统使用：
- Compose 的 `depends_on` 条件——用于阻塞依赖服务，直到本服务就绪
- Kubernetes 的就绪探针和存活探针——用于控制流量路由和重启决策
- Docker 自身——配合适当的重启策略时触发重启

没有健康检查时，这些系统只能看到进程状态。有了健康检查，它们就能看到应用状态。

## 在 Dockerfile 中添加 HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

参数说明：

| 参数 | 默认值 | 含义 |
|---|---|---|
| `--interval` | 30s | 检查的执行频率 |
| `--timeout` | 30s | 超过多久视为检查失败 |
| `--start-period` | 0s | 启动后的宽限期——此窗口内的失败不计入 |
| `--retries` | 3 | 标记为不健康前允许的连续失败次数 |

**`--start-period` 很重要。** 需要时间初始化的应用——预热缓存、执行迁移、建立连接池——在启动期间会健康检查失败。如果没有启动宽限期，这些失败会计入重试次数，容器在还没完成启动时就被标记为不健康。应将其设置为略长于你的 p95 启动时间。

### 健康端点应该检查什么

不要只检查端口是否开放。要检查应用是否真正可用：

```python
@app.get("/health")
def health():
    # verify database connection is alive
    db.execute("SELECT 1")
    # verify any other critical dependency
    cache.ping()
    return {"status": "ok"}
```

如果健康端点只返回 200 而不检查依赖，那么当数据库宕机、应用所有真实请求都失败时，该检查仍会通过。只有当检查能反映应用的真实健康状况时，它才有用。

## 三种健康状态

- **starting**——容器刚启动，处于 `--start-period` 宽限窗口内。此期间的失败不计入重试次数。
- **healthy**——最近 N 次连续检查通过（N 即 `--retries`）。
- **unhealthy**——最近 N 次连续检查失败。配合 `restart: unless-stopped`，Docker 会自动重启容器。

从 starting → healthy 的转换需要检查通过。从 healthy → unhealthy 的转换需要连续 `--retries` 次检查失败，这提供了对瞬时抖动的保护。

## 读取健康状态

```bash
# current health status (starting / healthy / unhealthy)
docker inspect <container> --format '{{.State.Health.Status}}'

# full health object with recent check results
docker inspect <container> --format '{{json .State.Health}}' | jq .
```

完整的健康对象包含每次近期检查的输出和退出码。当健康检查失败却找不到原因时，这里就是你要看的地方：

```bash
docker inspect <container> --format '{{json .State.Health.Log}}' | jq '.[0]'
```

`Output` 字段会准确显示检查命令退出前打印的内容——来自 `curl`、`pg_isready` 或你所用命令的实际错误信息。这是调试卡在“unhealthy”状态的容器最快的方法。

## Compose 与健康条件

默认情况下，`depends_on` 只等待容器启动——而不等待其中的服务就绪。这会导致启动时反复抖动：应用容器启动，在 Postgres 完成初始化之前尝试连接数据库，崩溃，然后循环重启。

定义了健康检查后，你可以让 Compose 真正等待：

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env.prod
```

`condition: service_healthy` 告诉 Compose 阻塞 `app` 容器，直到 `db` 通过其健康检查。应用不再会在数据库就绪之前启动。

可用的条件：
- `service_started`——默认值，容器正在运行（不检查健康状态）
- `service_healthy`——容器已通过健康检查
- `service_completed_successfully`——用于迁移等一次性容器

## 用 docker stats 监控资源

```bash
# live stats for all running containers
docker stats

# single container
docker stats <container-name>
```

输出：

```
CONTAINER ID   NAME    CPU %   MEM USAGE / LIMIT   MEM %   NET I/O       BLOCK I/O
a1b2c3d4e5f6   app     2.3%    128MiB / 512MiB     25%     1.2MB / 800kB 0B / 4MB
```

需要关注的情况：
- **内存持续增长**，持续数小时或数天——很可能是内存泄漏；容器最终会被 OOM 杀死
- **CPU 持续接近 100%**——容器已饱和；检查它是否在做预期之外的事情，或者是否需要提高资源限制
- **内存限制列显示的是宿主机总内存**——说明你没有在 Compose 中设置 `mem_limit`。上生产前务必设置，否则失控进程可能拖垮整台服务器

在 Compose 文件中设置限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          memory: 256M
```

## docker stats 的局限

`docker stats` 只显示当前快照。它没有记忆——“三小时前内存在做什么？”不是它能回答的问题。它不提供告警、仪表盘或趋势分析。

对于需要历史记录和告警的生产监控，你需要外部技术栈：

**自托管：**
- **cAdvisor**——将容器资源指标（CPU、内存、网络、磁盘 I/O）导出到 Prometheus
- **Prometheus**——带保留期地存储指标
- **Grafana**——在 Prometheus 之上提供仪表盘和告警

该技术栈只需几个 compose 服务和一份标准配置。cAdvisor 以特权容器运行，访问 Docker 的 cgroups，并在 `/metrics` 端点上输出每个容器的指标。

**托管方案：**
- AWS CloudWatch Container Insights、Google Cloud Monitoring、Datadog——均支持以极简配置采集 Docker 指标

对于单服务器 Docker 部署，`docker stats` 配合能触发自动重启的健康检查，已能覆盖大多数运维需求。缺口在于历史记录和告警——如果你想在用户报告之前发现问题，或在事后诊断发生了什么，就需要一套真正的监控技术栈。

<!-- ZH_RESOURCES -->
- [Docker HEALTHCHECK 参考文档](https://docs.docker.com/reference/dockerfile/#healthcheck)
- [cAdvisor — 容器顾问](https://github.com/google/cadvisor)
- [Prometheus 入门指南](https://prometheus.io/docs/prometheus/latest/getting_started/)

<!-- ZH_UI -->
1. 在 Dockerfile 中添加 HEALTHCHECK 指令
2. 理解容器的三种健康状态（starting、healthy、unhealthy）
3. 使用 docker inspect 读取容器的健康状态和历史记录
4. 配置 depends_on 健康条件，让服务等待依赖就绪
5. 使用 docker stats 进行基础资源监控
6. 了解 docker stats 的局限，知道何时该用专业监控栈
7. 单服务器 Docker 越来越受限。如何大规模运行？
8. 我有一台服务器运行良好，但需要更高韧性——服务器一旦宕机，所有服务都会挂掉。不做大量手动工作也无法横向扩展。有更好的方案吗？
