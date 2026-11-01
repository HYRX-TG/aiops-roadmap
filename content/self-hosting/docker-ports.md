---
id: docker-ports
title: 'Docker Ports: How Do I Access My Container?'
zone: self-hosting
edges:
  to:
    - id: docker-volumes
      question: I can access the service. But where is my data stored?
      detail: >-
        If the container is what's running the service, is my data inside it?
        What happens when I delete the container to update it — do I lose
        everything I've set up?
difficulty: 1
tags:
  - self-hosting
  - docker
  - networking
  - ports
category: concept
milestones:
  - 'Understand the host:container port syntax'
  - Know what port a service listens on inside its container (check Docker Hub)
  - Access a running container from your browser using the host port
  - Understand why binding to 0.0.0.0 vs 127.0.0.1 matters
title_zh: "Docker 端口：如何访问我的容器？"

---


A container has its own isolated network. When a service inside it listens on port 80, that's port 80 *inside the container* — not port 80 on your server. To reach the service from your browser, you have to tell Docker to forward a port from your server into the container.

That's what `-p 8080:80` does.

<!-- DEEP_DIVE -->

**The syntax: host:container**

`-p 8080:80` means:

> "Take port **8080** on my server (host), and connect it to port **80** inside the container."

So you open `http://your-server:8080` in a browser. Docker receives the connection on port 8080 and passes it to port 80 inside the container.

You can use any available port on the host side. Convention: many people use ports in the 8000–9000 range for homelab services. The container port is fixed — it's whatever the application listens on.

**How do you know what port the container uses?**

Check Docker Hub. Every official image has a documentation page that tells you what port the application listens on. For Vaultwarden: port 80. For Jellyfin: port 8096. For Immich: port 2283. You don't choose this — it's baked into the image.

The Dockerfile typically has an `EXPOSE` instruction listing the container's port. Docker Hub shows this on the image page.

**What happens if you don't publish a port?**

The container runs, the service starts, but nothing can reach it. The port is only accessible from inside the container itself. For a web service, this means the browser gets a connection refused error.

**0.0.0.0 vs 127.0.0.1**

By default, `-p 8080:80` binds to `0.0.0.0` — meaning the port is accessible from any network interface on your server, including the local network. Anyone on your WiFi can reach it.

If you want a service only reachable from the server itself (e.g., a database that only your other containers need), bind to localhost:

```bash
-p 127.0.0.1:5432:5432
```

This is a useful security practice for anything that shouldn't be accessed directly. For services you want to access from your laptop or phone on the home network, `0.0.0.0` (the default) is correct.

**Check running containers and their ports**

```bash
docker ps
```

The `PORTS` column shows all published ports — the host:container mapping for each running container.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
容器拥有自己隔离的网络。当容器内的服务监听 80 端口时，那是*容器内部*的 80 端口——而不是你服务器上的 80 端口。要从浏览器访问该服务，你必须让 Docker 将服务器上的某个端口转发到容器内。

这就是 `-p 8080:80` 的作用。

<!-- ZH_DEEP_DIVE -->
**语法：host:container**

`-p 8080:80` 的意思是：

> “把我服务器（主机）上的端口 **8080** 连接到容器内部的端口 **80**。”

这样你在浏览器中打开 `http://your-server:8080`。Docker 在 8080 端口接收连接，并将其转发到容器内部的 80 端口。

主机侧可以使用任意可用端口。惯例：很多人在家庭实验室服务中使用 8000–9000 范围内的端口。容器端口是固定的——它就是应用程序监听的端口。

**如何知道容器使用哪个端口？**

查看 Docker Hub。每个官方镜像都有一个文档页面，告诉你应用程序监听的端口。对于 Vaultwarden：端口 80。对于 Jellyfin：端口 8096。对于 Immich：端口 2283。这个端口不是你选择的——它已经固化在镜像里。

Dockerfile 通常有一个 `EXPOSE` 指令，列出容器的端口。Docker Hub 会在镜像页面上显示这一点。

**如果不发布端口会发生什么？**

容器会运行，服务会启动，但没有任何东西能访问它。该端口只能从容器内部访问。对于 Web 服务来说，这意味着浏览器会收到连接被拒绝的错误。

**0.0.0.0 与 127.0.0.1**

默认情况下，`-p 8080:80` 绑定到 `0.0.0.0`——意味着该端口可从服务器上的任意网络接口访问，包括本地网络。你 WiFi 上的任何人都能访问它。

如果你希望某个服务只能从服务器本身访问（例如，只有你的其他容器需要的数据库），请绑定到 localhost：

```bash
-p 127.0.0.1:5432:5432
```

对于任何不应被直接访问的服务来说，这是一个有用的安全实践。对于你想从家庭网络中的笔记本电脑或手机访问的服务，`0.0.0.0`（默认值）是正确的。

**检查正在运行的容器及其端口**

```bash
docker ps
```

`PORTS` 列显示所有已发布的端口——每个正在运行的容器的 host:container 映射。

<!-- ZH_UI -->
1. 理解主机端口与容器端口的语法
2. 了解服务在容器内监听的端口（查看 Docker Hub）
3. 通过主机端口从浏览器访问运行中的容器
4. 理解为什么绑定到 0.0.0.0 与 127.0.0.1 很重要
5. 我能访问服务了。但我的数据存储在哪里？
6. 如果容器是运行服务的东西，我的数据在它里面吗？当我删除容器以更新它时会发生什么——我会丢失所有已设置的内容吗？
