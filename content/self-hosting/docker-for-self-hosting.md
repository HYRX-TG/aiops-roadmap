---
id: docker-for-self-hosting
title: Docker for Self-Hosting
zone: self-hosting
edges:
  to:
    - id: docker-compose
      question: I know Docker — let's skip to managing services properly
      detail: >-
        I've been running containers with docker run commands but it's already
        getting messy. If I restart the server I have to remember all the flags.
        There has to be a better way.
    - id: docker-ports
      question: Wait — I don't really understand how Docker works yet
      detail: >-
        I got a container running but I honestly have no idea what's happening.
        What are all those flags doing? If I delete the container, do I lose my
        data? And how do I get two services to talk to each other?
difficulty: 1
tags:
  - self-hosting
  - docker
  - containers
  - linux
category: tool
milestones:
  - Install Docker on your server
  - Pull and run a container (e.g. `docker run hello-world`)
  - Run Vaultwarden with `docker run` and access it from your browser
  - 'Understand images, containers, volumes, and ports'
title_zh: "用于自托管的 Docker"

---


Docker is a tool for running applications in isolated containers. For self-hosting, it means you can run any service — Vaultwarden, Immich, Jellyfin — without installing its dependencies directly on your server. You just run the container.

Let's install Docker and run your first service.

<!-- DEEP_DIVE -->

**Installing Docker**

Don't use the Docker package from the Debian apt repository — it's often outdated. Use the official Docker repository:

```bash
# Add Docker's official GPG key
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Add your user to the `docker` group so you can run Docker commands without `sudo`:

```bash
sudo usermod -aG docker $USER
```

Log out and back in, then verify:

```bash
docker run hello-world
```

**Four things Docker works with**

- **Image**: a packaged application, read-only. Think of it as the blueprint. `vaultwarden/server:latest` is an image.
- **Container**: a running instance of an image. You can run multiple containers from the same image.
- **Volume**: persistent storage attached to a container. Data here survives container restarts and updates.
- **Port**: a network port exposed from the container to your host machine.

**Run Vaultwarden with a single command**

```bash
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  --restart unless-stopped \
  vaultwarden/server:latest
```

What each flag does:
- `-d`: run in the background (detached)
- `--name vaultwarden`: give the container a name
- `-v ~/apps/vaultwarden/data:/data`: mount a host directory into the container for persistent storage
- `-p 8080:80`: map port 8080 on the host to port 80 in the container
- `--restart unless-stopped`: restart automatically if the server reboots

Open your browser: `http://YOUR-SERVER-IP:8080`. Vaultwarden is running.

**The problem with `docker run`**

That command is long and hard to remember. If you ever need to stop and restart the container, you have to type it all again — or hope you saved it somewhere. It doesn't version-control well. And when you have multiple services with multiple containers, managing them all with `docker run` becomes a nightmare.

Docker Compose solves this. It lets you define your entire setup in a single YAML file and manage it with two commands.

<!-- RESOURCES -->

- [Docker Installation for Debian](https://docs.docker.com/engine/install/debian/) -- type: guide, time: 15min
- [Vaultwarden on Docker Hub](https://hub.docker.com/r/vaultwarden/server) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
Docker 是一个用于在隔离容器中运行应用的工具。对于自托管而言，这意味着你可以运行任何服务——Vaultwarden、Immich、Jellyfin——而无需直接在服务器上安装它们的依赖项。你只需运行容器即可。

让我们安装 Docker 并运行你的第一个服务。

<!-- ZH_DEEP_DIVE -->
**安装 Docker**

不要使用 Debian apt 仓库中的 Docker 包——它通常已经过时。请使用 Docker 官方仓库：

```bash
# Add Docker's official GPG key
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

将你的用户添加到 `docker` 组，这样你就可以在不使用 `sudo` 的情况下运行 Docker 命令：

```bash
sudo usermod -aG docker $USER
```

注销并重新登录，然后验证：

```bash
docker run hello-world
```

**Docker 涉及的四个概念**

- **镜像（Image）**：打包好的应用程序，只读。可以把它看作蓝图。`vaultwarden/server:latest` 就是一个镜像。
- **容器（Container）**：镜像的运行实例。你可以从同一个镜像运行多个容器。
- **卷（Volume）**：附加到容器的持久化存储。这里的数据在容器重启和更新后依然存在。
- **端口（Port）**：从容器暴露到宿主机的一个网络端口。

**用一条命令运行 Vaultwarden**

```bash
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  --restart unless-stopped \
  vaultwarden/server:latest
```

各参数的作用：
- `-d`：在后台运行（分离模式）
- `--name vaultwarden`：为容器指定一个名称
- `-v ~/apps/vaultwarden/data:/data`：将宿主机目录挂载到容器中，用于持久化存储
- `-p 8080:80`：将宿主机的 8080 端口映射到容器内的 80 端口
- `--restart unless-stopped`：如果服务器重启，自动重启容器

打开浏览器访问：`http://YOUR-SERVER-IP:8080`。Vaultwarden 已在运行。

**`docker run` 的问题**

那条命令又长又难记。如果你需要停止并重启容器，就必须把整条命令重新输入一遍——或者指望自己把它保存在了某个地方。它也不便于版本控制。而且当你拥有多个服务、多个容器时，用 `docker run` 管理它们会变成一场噩梦。

Docker Compose 解决了这个问题。它让你可以在单个 YAML 文件中定义整套配置，并用两条命令进行管理。

<!-- ZH_RESOURCES -->
- [Debian 上的 Docker 安装](https://docs.docker.com/engine/install/debian/) -- 类型：指南，时间：15 分钟
- [Docker Hub 上的 Vaultwarden](https://hub.docker.com/r/vaultwarden/server) -- 类型：参考，时间：5 分钟

<!-- ZH_UI -->
1. 在你的服务器上安装 Docker
2. 拉取并运行一个容器（例如 `docker run hello-world`）
3. 用 `docker run` 运行 Vaultwarden 并从浏览器访问它
4. 理解镜像、容器、卷和端口
5. 我懂 Docker——直接跳到正确管理服务
6. 我一直用 docker run 命令运行容器，但已经变得很乱。如果重启服务器，我得记住所有参数。一定有更好的办法。
7. 等等——我其实还不太懂 Docker 是怎么工作的
8. 我跑起来了一个容器，但我完全不知道发生了什么。那些参数都是干什么的？如果我删除容器，会丢失数据吗？还有怎么让两个服务互相通信？
