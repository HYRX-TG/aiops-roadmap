---
id: docker-compose
title: Docker Compose
zone: self-hosting
edges:
  to:
    - id: reverse-proxy
      question: Services are running but I'm tired of remembering port numbers
      detail: >-
        I have to remember which port maps to which service, and when I add a
        new one I have to pick a free port and hope nothing conflicts. Typing
        192.168.1.33:8083 every time is not how I want to use this.
    - id: backup-strategy
      question: If my server dies right now, I lose everything — how do I prevent that?
      detail: >-
        I've been setting up services and not once thought about what happens
        if the disk fails. All my configs, all my data — just gone. That
        can't be the plan.
    - id: monitoring-your-server
      question: Everything works... until it doesn't. How do I know when something breaks?
      detail: >-
        I found out Vaultwarden was down because I couldn't log into a
        website. That was three days after it crashed. There has to be a
        better way to know when things go wrong.
    - id: storage-planning
      question: All my data is on one disk — what happens when it fills up or fails?
      detail: >-
        I'm running everything off the boot drive. Photos, media, databases —
        all on the same disk. That feels like a ticking time bomb but I don't
        know what the alternative looks like.
difficulty: 1
tags:
  - self-hosting
  - docker
  - docker-compose
  - containers
category: tool
milestones:
  - Write a docker-compose.yml for Vaultwarden
  - Start it with `docker compose up -d`
  - Stop and restart it without losing data
  - Add a second service to the same compose file
  - Understand named volumes vs bind mounts
title_zh: "Docker Compose"

---


Docker Compose lets you define your entire service — image, ports, volumes, environment variables, restart policy — in a single YAML file. Instead of a long `docker run` command you have to remember, you have a file you can commit to git and reproduce anywhere.

Two commands run your entire stack. Two commands tear it down.

<!-- DEEP_DIVE -->

**The compose file**

Create a directory for your service and a `docker-compose.yml` inside it:

```bash
mkdir -p ~/apps/vaultwarden
nano ~/apps/vaultwarden/docker-compose.yml
```

```yaml
services:
  vaultwarden:
    image: vaultwarden/server:latest
    container_name: vaultwarden
    volumes:
      - ./data:/data
    ports:
      - "8080:80"
    environment:
      - DOMAIN=https://passwords.yourdomain.com  # set this when you have a domain
    restart: unless-stopped
```

**Key fields:**

- `image`: the Docker image to run
- `container_name`: a fixed name so you can reference it in logs and commands
- `volumes`: `./data:/data` is a bind mount — the `data/` directory next to your compose file, mounted as `/data` in the container. Docker creates `data/` automatically.
- `ports`: `host:container` mapping, same as `-p` in `docker run`
- `environment`: environment variables passed into the container — service-specific config
- `restart: unless-stopped`: restart automatically after reboot or crash, but not if you manually stop it

**Starting and stopping**

```bash
cd ~/apps/vaultwarden

docker compose up -d        # start everything in the background
docker compose down         # stop and remove containers (data is preserved)
docker compose logs -f      # follow logs from all containers
docker compose ps           # show running containers in this stack
```

**Updating a service**

Pull the new image and restart:

```bash
docker compose pull         # pull latest images
docker compose up -d        # recreate containers with new images
```

That's the entire update process. Your data is in bind mounts — it's untouched by the update.

**A service with a database**

Many services need a database. Here's what a two-container compose file looks like:

```yaml
services:
  app:
    image: someapp:latest
    volumes:
      - ./data:/data
    ports:
      - "8080:80"
    environment:
      - DB_HOST=db
      - DB_NAME=appdb
      - DB_USER=appuser
      - DB_PASS=changeme
    restart: unless-stopped
    depends_on:
      - db

  db:
    image: postgres:16
    volumes:
      - ./postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=appdb
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=changeme
    restart: unless-stopped
```

Notice `DB_HOST=db` — the app connects to the database using the service name `db`. Compose automatically creates a shared network for all services in the file, so service name DNS resolution just works.

`depends_on: db` tells Compose to start the database before the app.

**Where to store your stacks**

Use `~/apps/<service-name>/` for everything. Each service gets its own directory with its own `docker-compose.yml` and its own `data/` subdirectory. It lives in your home directory — no sudo, no root, just your files.

```
~/apps/
├── vaultwarden/
│   ├── docker-compose.yml
│   └── data/
├── immich/
│   ├── docker-compose.yml
│   └── data/
└── jellyfin/
    ├── docker-compose.yml
    ├── config/
    └── media -> /mnt/nas/media   # symlink to wherever media lives
```

<!-- RESOURCES -->

- [Docker Compose documentation](https://docs.docker.com/compose/) -- type: reference, time: ongoing

<!-- ZH_SUMMARY -->
Docker Compose 让你可以在单个 YAML 文件中定义整个服务——镜像、端口、卷、环境变量、重启策略。你不再需要记住冗长的 `docker run` 命令，而是拥有一个可以提交到 git 并在任何地方复现的文件。

两条命令即可运行你的整个技术栈。两条命令即可将其拆除。

<!-- ZH_DEEP_DIVE -->
**Compose 文件**

为你的服务创建一个目录，并在其中创建 `docker-compose.yml`：

```bash
mkdir -p ~/apps/vaultwarden
nano ~/apps/vaultwarden/docker-compose.yml
```

```yaml
services:
  vaultwarden:
    image: vaultwarden/server:latest
    container_name: vaultwarden
    volumes:
      - ./data:/data
    ports:
      - "8080:80"
    environment:
      - DOMAIN=https://passwords.yourdomain.com  # set this when you have a domain
    restart: unless-stopped
```

**关键字段：**

- `image`：要运行的 Docker 镜像
- `container_name`：固定名称，便于在日志和命令中引用
- `volumes`：`./data:/data` 是绑定挂载——compose 文件旁的 `data/` 目录，挂载为容器内的 `/data`。Docker 会自动创建 `data/`。
- `ports`：`host:container` 映射，与 `docker run` 中的 `-p` 相同
- `environment`：传入容器的环境变量——服务特定的配置
- `restart: unless-stopped`：重启或崩溃后自动重启，但手动停止后不会重启

**启动与停止**

```bash
cd ~/apps/vaultwarden

docker compose up -d        # start everything in the background
docker compose down         # stop and remove containers (data is preserved)
docker compose logs -f      # follow logs from all containers
docker compose ps           # show running containers in this stack
```

**更新服务**

拉取新镜像并重启：

```bash
docker compose pull         # pull latest images
docker compose up -d        # recreate containers with new images
```

这就是整个更新过程。你的数据位于绑定挂载中——更新不会触碰它。

**带数据库的服务**

许多服务需要数据库。下面是一个双容器 compose 文件的样子：

```yaml
services:
  app:
    image: someapp:latest
    volumes:
      - ./data:/data
    ports:
      - "8080:80"
    environment:
      - DB_HOST=db
      - DB_NAME=appdb
      - DB_USER=appuser
      - DB_PASS=changeme
    restart: unless-stopped
    depends_on:
      - db

  db:
    image: postgres:16
    volumes:
      - ./postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=appdb
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=changeme
    restart: unless-stopped
```

注意 `DB_HOST=db`——应用使用服务名 `db` 连接数据库。Compose 会自动为该文件中的所有服务创建一个共享网络，因此服务名 DNS 解析可以直接工作。

`depends_on: db` 告诉 Compose 先启动数据库，再启动应用。

**在哪里存放你的 stack**

所有内容都放在 `~/apps/<service-name>/` 下。每个服务都有自己的目录，包含自己的 `docker-compose.yml` 和自己的 `data/` 子目录。它位于你的主目录中——无需 sudo，无需 root，只是你的文件。

```
~/apps/
├── vaultwarden/
│   ├── docker-compose.yml
│   └── data/
├── immich/
│   ├── docker-compose.yml
│   └── data/
└── jellyfin/
    ├── docker-compose.yml
    ├── config/
    └── media -> /mnt/nas/media   # symlink to wherever media lives
```

<!-- ZH_RESOURCES -->
- [Docker Compose 文档](https://docs.docker.com/compose/) -- 类型：参考，时间：持续

<!-- ZH_UI -->
1. 为 Vaultwarden 编写 docker-compose.yml
2. 用 `docker compose up -d` 启动它
3. 停止并重启它而不丢失数据
4. 向同一个 compose 文件添加第二个服务
5. 理解命名卷与绑定挂载的区别
6. 服务都在运行，但我厌倦了记端口号
7. 我得记住哪个端口对应哪个服务，添加新服务时还得挑一个空闲端口并祈祷不冲突。每次都输入 192.168.1.33:8083 可不是我想用的方式。
8. 如果我的服务器现在挂了，我会失去一切——我该怎么防止这种情况？
9. 我一直在搭建服务，却从没想过磁盘故障会发生什么。所有配置、所有数据——全都没了。这不能是计划。
10. 一切正常……直到它不正常。我怎么知道什么时候出了问题？
11. 我发现 Vaultwarden 挂了是因为我登录不上一个网站。那已经是它崩溃三天后了。一定有更好的办法知道出问题时的情况。
12. 我的所有数据都在一块磁盘上——当它满了或坏了会发生什么？
13. 我把所有东西都跑在启动盘上。照片、媒体、数据库——全在同一块磁盘上。这感觉像一颗定时炸弹，但我不知道替代方案是什么样。
