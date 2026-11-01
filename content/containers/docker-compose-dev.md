---
id: docker-compose-dev
title: Docker Compose for Local Development
zone: containers
edges:
  to:
    - id: building-images-in-ci
      question: Local setup works. How do I build images automatically in CI?
      detail: >-
        I'm running docker build manually on my laptop every time I make a
        change. That's not sustainable — I need this to happen automatically
        when I push code, not something I have to remember to do.
    - id: container-networking
      question: My services talk to each other in Compose, but I don't understand how. What's actually happening?
      detail: >-
        I just wrote `db` in my app's connection string and it worked. But I
        have no idea why. What if I need to connect containers that aren't in
        the same Compose file? Or debug a networking issue between services?
    - id: debugging-compose
      question: Something's wrong with my Compose setup and I can't figure out what.
      detail: >-
        One service keeps restarting, another can't reach the database even though
        they're in the same Compose file. I'm not sure how to read the logs across
        multiple services or tell whether it's a config issue or a networking issue.
difficulty: 1
tags:
  - docker
  - docker-compose
  - local-dev
  - containers
category: practice
milestones:
  - Write a docker-compose.yml that runs your app and its dependencies
  - Start and stop the full stack with docker compose up/down
  - Use volumes to persist data across container restarts
  - Use environment variables to configure services per environment
title_zh: "用于本地开发的 Docker Compose"

---


Most applications aren't a single process. They need a database, maybe a cache, maybe a queue. Running each one separately with `docker run` commands you have to remember — and then tearing them down in the right order — gets tedious fast. Docker Compose lets you describe the entire local stack in one YAML file and manage it with a single command.

The mental model is straightforward: you define services, and each service is a container. Compose handles creating a shared network so services can reach each other by name, manages named volumes so database data survives restarts, and gives you a consistent set of commands to start, stop, and inspect everything at once.

<!-- DEEP_DIVE -->

## What Compose gives you

A `docker-compose.yml` file (or `compose.yaml` — both are valid) describes your full local environment: what images to use or build, which ports to expose, what volumes to mount, what environment variables to set, and which services need to start before others.

The core workflow:

```bash
docker compose up -d      # start everything in the background
docker compose down       # stop and remove containers and networks
```

All services in a Compose project are placed on a shared network automatically. A service named `db` is reachable from other containers at the hostname `db` — no manual networking configuration required.

## The compose file structure

Here's a realistic example: a web app, a Postgres database, and Redis.

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgres://postgres:secret@db:5432/myapp
      REDIS_URL: redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

A few things to notice: `build: .` tells Compose to build the image from the Dockerfile in the current directory. The service name (`db`, `cache`) becomes the DNS hostname that other services use in connection strings. Named volumes (`postgres-data`, `redis-data`) are declared at the bottom and persist across `docker compose down` / `up` cycles.

## Services and builds

Each service either builds from source or pulls an existing image.

For your own application code, use `build`:

```yaml
services:
  app:
    build: .                          # Dockerfile in current directory
```

For more control over the build context or a different Dockerfile:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev      # Use a dev-specific Dockerfile
```

For external dependencies (databases, caches, queues), use `image`:

```yaml
services:
  db:
    image: postgres:16
```

The general pattern: `build` for code you own, `image` for everything else.

## Volumes for persistence

Without a volume, a container's filesystem disappears when the container is removed. That's fine for your application, but not for a database.

**Named volumes** are managed by Docker and persist across `down` / `up` cycles:

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

**Bind mounts** map a directory on your host into the container. This is the standard pattern for live code reloading in development — changes to your local files are immediately visible inside the container:

```yaml
services:
  app:
    build: .
    volumes:
      - .:/app                        # current directory → /app in container
```

One important command to know: `docker compose down -v` removes both containers and named volumes. This is what you want when you need a clean slate — but it also deletes all your local database data. Use it intentionally.

## Environment variables

Services are configured through environment variables. There are two ways to set them in a Compose file:

Inline in the service definition:

```yaml
services:
  app:
    environment:
      APP_ENV: development
      LOG_LEVEL: debug
```

Or loaded from a file with `env_file`:

```yaml
services:
  app:
    env_file:
      - .env
```

The standard practice for team projects: commit a `.env.example` with placeholder values showing what variables are needed, and keep `.env` (with real values) in `.gitignore`. Anyone cloning the repo copies `.env.example` to `.env` and fills in their local values.

```bash
# .env.example (committed)
DATABASE_URL=postgres://postgres:changeme@db:5432/myapp
SECRET_KEY=change-me-in-production

# .env (gitignored — real local values)
DATABASE_URL=postgres://postgres:mypassword@db:5432/myapp
SECRET_KEY=dev-key-abc123
```

## Useful Compose commands

```bash
# Start all services in the background
docker compose up -d

# Stop and remove containers and networks (keeps volumes)
docker compose down

# Also remove named volumes
docker compose down -v

# Follow logs from all services
docker compose logs -f

# Follow logs from a specific service
docker compose logs -f app

# Open a shell in a running container
docker compose exec app bash

# Run a one-off command (e.g., a database migration)
docker compose run --rm app python manage.py migrate

# Show status of all services
docker compose ps

# Rebuild images without starting containers
docker compose build

# Pull latest versions of all images
docker compose pull
```

`docker compose run` starts a new container for a one-off command. It's the right tool for migrations, seed scripts, and anything you want to run inside the container environment without leaving a long-running process. The `--rm` flag removes the container after it exits.

<!-- RESOURCES -->

- [Docker Compose file reference](https://docs.docker.com/compose/compose-file/)
- [Docker Compose CLI reference](https://docs.docker.com/compose/reference/)

<!-- ZH_SUMMARY -->
大多数应用并不是单一进程。它们需要数据库，可能还需要缓存，可能还需要队列。用 `docker run` 命令逐个运行每个组件——还得记住这些命令，然后按正确顺序拆除——很快就会变得繁琐。Docker Compose 让你在一个 YAML 文件中描述整个本地栈，并用一条命令管理它。

心智模型很直接：你定义服务，每个服务就是一个容器。Compose 负责创建一个共享网络，使服务可以通过名称相互访问；管理命名卷，使数据库数据在重启后依然保留；并提供一套一致的命令，让你一次性启动、停止和检查所有内容。

<!-- ZH_DEEP_DIVE -->
## Compose 能为你提供什么

一个 `docker-compose.yml` 文件（或 `compose.yaml`——两者都有效）描述了你完整的本地环境：使用或构建哪些镜像、暴露哪些端口、挂载哪些卷、设置哪些环境变量，以及哪些服务需要先于其他服务启动。

核心工作流：

```bash
docker compose up -d      # start everything in the background
docker compose down       # stop and remove containers and networks
```

Compose 项目中的所有服务会自动放置在一个共享网络上。名为 `db` 的服务可以从其他容器通过主机名 `db` 访问——无需手动配置网络。

## compose 文件结构

下面是一个贴近实际的示例：一个 Web 应用、一个 Postgres 数据库和一个 Redis。

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgres://postgres:secret@db:5432/myapp
      REDIS_URL: redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

有几点需要注意：`build: .` 告诉 Compose 从当前目录的 Dockerfile 构建镜像。服务名（`db`、`cache`）会成为其他服务在连接字符串中使用的 DNS 主机名。命名卷（`postgres-data`、`redis-data`）在文件底部声明，并在 `docker compose down` / `up` 循环之间持久保留。

## 服务与构建

每个服务要么从源码构建，要么拉取现有镜像。

对于你自己的应用代码，使用 `build`：

```yaml
services:
  app:
    build: .                          # Dockerfile in current directory
```

如需对构建上下文或使用不同的 Dockerfile 进行更多控制：

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev      # Use a dev-specific Dockerfile
```

对于外部依赖（数据库、缓存、队列），使用 `image`：

```yaml
services:
  db:
    image: postgres:16
```

通用模式：`build` 用于你自己拥有的代码，`image` 用于其他一切。

## 用于持久化的卷

没有卷时，容器被移除后其文件系统就会消失。这对你的应用来说没问题，但对数据库来说不行。

**命名卷**由 Docker 管理，并在 `down` / `up` 循环之间持久保留：

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

**绑定挂载**将宿主机上的目录映射到容器中。这是开发中实时重载代码的标准模式——对本地文件的更改会立即在容器内可见：

```yaml
services:
  app:
    build: .
    volumes:
      - .:/app                        # current directory → /app in container
```

有一个重要的命令需要了解：`docker compose down -v` 会同时移除容器和命名卷。当你需要干净的状态时，这正是你想要的——但它也会删除你所有的本地数据库数据。请有意识地使用它。

## 环境变量

服务通过环境变量进行配置。在 Compose 文件中有两种设置方式：

在服务定义中内联：

```yaml
services:
  app:
    environment:
      APP_ENV: development
      LOG_LEVEL: debug
```

或者通过 `env_file` 从文件加载：

```yaml
services:
  app:
    env_file:
      - .env
```

团队项目的标准做法：提交一个包含占位值的 `.env.example`，展示需要哪些变量，并将 `.env`（包含真实值）保留在 `.gitignore` 中。任何克隆仓库的人将 `.env.example` 复制为 `.env` 并填入自己的本地值。

```bash
# .env.example (committed)
DATABASE_URL=postgres://postgres:changeme@db:5432/myapp
SECRET_KEY=change-me-in-production

# .env (gitignored — real local values)
DATABASE_URL=postgres://postgres:mypassword@db:5432/myapp
SECRET_KEY=dev-key-abc123
```

## 有用的 Compose 命令

```bash
# Start all services in the background
docker compose up -d

# Stop and remove containers and networks (keeps volumes)
docker compose down

# Also remove named volumes
docker compose down -v

# Follow logs from all services
docker compose logs -f

# Follow logs from a specific service
docker compose logs -f app

# Open a shell in a running container
docker compose exec app bash

# Run a one-off command (e.g., a database migration)
docker compose run --rm app python manage.py migrate

# Show status of all services
docker compose ps

# Rebuild images without starting containers
docker compose build

# Pull latest versions of all images
docker compose pull
```

`docker compose run` 会为一次性命令启动一个新容器。它是执行迁移、种子脚本以及任何你想在容器环境中运行而不留下长期运行进程的操作的正确工具。`--rm` 标志会在容器退出后将其移除。

<!-- ZH_RESOURCES -->
- [Docker Compose 文件参考](https://docs.docker.com/compose/compose-file/)
- [Docker Compose CLI 参考](https://docs.docker.com/compose/reference/)

<!-- ZH_UI -->
1. 编写一个 docker-compose.yml，用于运行你的应用及其依赖项
2. 使用 docker compose up/down 启动和停止整个技术栈
3. 使用卷在容器重启之间持久化数据
4. 使用环境变量按环境配置服务
5. 本地环境已能正常工作。我如何在 CI 中自动构建镜像？
6. 我每次修改代码后都要在笔记本上手动运行 docker build。这不可持续——我需要它在推送代码时自动发生，而不是靠我记得去做。
7. 我的服务在 Compose 中能互相通信，但我不理解其原理。实际发生了什么？
8. 我在应用的连接字符串中只写了 `db` 就能正常工作。但我不知道为什么。如果我需要连接不在同一个 Compose 文件中的容器呢？或者调试服务之间的网络问题呢？
9. 我的 Compose 配置出了问题，但我找不出原因。
10. 一个服务不断重启，另一个服务无法访问数据库，尽管它们在同一个 Compose 文件中。我不知道如何跨多个服务阅读日志，也无法判断这是配置问题还是网络问题。
