---
id: docker-volumes
title: 'Docker Volumes: Where Does My Data Live?'
zone: self-hosting
edges:
  to:
    - id: docker-networking
      question: Data is safe. Now how do multiple containers talk to each other?
      detail: >-
        I tried using localhost in my app's database connection string but it
        couldn't connect. Both containers are on the same machine — why can't
        they see each other?
difficulty: 1
tags:
  - self-hosting
  - docker
  - volumes
  - storage
  - data
category: concept
milestones:
  - Understand why containers are ephemeral by default
  - Run a container with a bind mount and verify data persists after restart
  - Know the difference between bind mounts and named volumes
  - Know where to put your data on the host (e.g. ~/apps/vaultwarden/)
title_zh: "Docker 卷：我的数据究竟存放在哪里？"

---


Containers are ephemeral. Every file written inside a container lives only as long as the container exists. Delete the container to update it, and everything written inside is gone.

This is by design — containers are supposed to be disposable. Your data shouldn't live inside them.

<!-- DEEP_DIVE -->

**The problem, made concrete**

Run Vaultwarden, create some passwords. Now update Vaultwarden (the standard way: delete the old container, start a new one with the new image). Without a volume, all your passwords are gone.

Volumes solve this by storing data *outside* the container, on your server's filesystem. The container reads and writes to that location — when you delete and recreate the container, the data is still there.

**Two kinds of volumes**

**1. Bind mounts** — you specify a directory on your host:

```bash
-v ~/apps/vaultwarden/data:/data
```

The directory `~/apps/vaultwarden/data` on your server is mounted as `/data` inside the container. The container writes to `/data`, the files appear on your server at the host path.

This is what we recommend for self-hosting. You can see exactly where your data is, back it up with `rsync` or any backup tool, and inspect it directly if needed.

**2. Named volumes** — Docker manages the location:

```bash
-v vaultwarden_data:/data
```

Docker creates and manages a volume under `/var/lib/docker/volumes/vaultwarden_data/`. The data is just as persistent, but harder to find and back up. Fine for databases where you don't need to inspect the files, but less transparent.

**The recommended convention**

Keep all your self-hosted data under `~/apps/`:

```
~/apps/
├── vaultwarden/
│   └── data/          ← Vaultwarden's data
├── immich/
│   └── data/          ← Immich's photos and database
└── jellyfin/
    ├── config/        ← Jellyfin's config
    └── media/         ← Your media files (or a symlink to wherever they live)
```

Every service has its own directory. When you back up `~/apps/`, you back up everything.

**Verify that volumes work**

```bash
# Start Vaultwarden with a bind mount
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  vaultwarden/server:latest

# Open the UI, create an account, add a password

# Now delete the container
docker rm -f vaultwarden

# Look — your data is still on the host
ls ~/apps/vaultwarden/data/

# Start a new container pointing to the same directory
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  vaultwarden/server:latest

# Open the UI — your account and passwords are still there
```

The container is gone and recreated. The data never left your server.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
容器是临时的。容器内写入的每个文件，其生命周期仅与容器本身相同。删除容器以进行更新时，容器内写入的所有内容都会丢失。

这是设计使然——容器本就应该是一次性的。你的数据不应存放在容器内部。

<!-- ZH_DEEP_DIVE -->
**问题具体化**

运行 Vaultwarden，创建一些密码。现在更新 Vaultwarden（标准做法：删除旧容器，用新镜像启动一个新容器）。如果没有卷，你的所有密码都会丢失。

卷通过将数据存储在容器*之外*、即服务器的文件系统上，来解决这个问题。容器读写该位置——当你删除并重新创建容器时，数据仍然存在。

**两种卷**

**1. 绑定挂载（Bind mounts）**——你指定宿主机上的一个目录：

```bash
-v ~/apps/vaultwarden/data:/data
```

服务器上的目录 `~/apps/vaultwarden/data` 被挂载为容器内的 `/data`。容器写入 `/data`，文件就会出现在服务器上的宿主机路径下。

这是我们推荐用于自托管的方式。你可以确切看到数据在哪里，用 `rsync` 或任何备份工具进行备份，并在需要时直接检查。

**2. 命名卷（Named volumes）**——由 Docker 管理位置：

```bash
-v vaultwarden_data:/data
```

Docker 会在 `/var/lib/docker/volumes/vaultwarden_data/` 下创建并管理一个卷。数据同样持久，但更难找到和备份。对于不需要检查文件的数据库来说没问题，但透明度较低。

**推荐的约定**

将所有自托管数据放在 `~/apps/` 下：

```
~/apps/
├── vaultwarden/
│   └── data/          ← Vaultwarden 的数据
├── immich/
│   └── data/          ← Immich 的照片和数据库
└── jellyfin/
    ├── config/        ← Jellyfin 的配置
    └── media/         ← 你的媒体文件（或指向它们所在位置的符号链接）
```

每个服务都有自己的目录。当你备份 `~/apps/` 时，你就备份了一切。

**验证卷是否生效**

```bash
# 使用绑定挂载启动 Vaultwarden
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  vaultwarden/server:latest

# 打开 UI，创建账户，添加一个密码

# 现在删除容器
docker rm -f vaultwarden

# 看——你的数据仍在宿主机上
ls ~/apps/vaultwarden/data/

# 启动一个指向同一目录的新容器
docker run -d \
  --name vaultwarden \
  -v ~/apps/vaultwarden/data:/data \
  -p 8080:80 \
  vaultwarden/server:latest

# 打开 UI——你的账户和密码仍然在那里
```

容器被删除并重新创建。数据从未离开你的服务器。

<!-- ZH_UI -->
1. 理解容器默认为何是临时的
2. 使用绑定挂载运行容器，并验证重启后数据仍然保留
3. 了解绑定挂载与命名卷的区别
4. 知道在宿主机上把数据放在哪里（例如 ~/apps/vaultwarden/）
5. 数据安全了。那么多个容器之间如何通信？
6. 我在应用的数据库连接字符串中使用了 localhost，但无法连接。两个容器都在同一台机器上——为什么它们互相看不到？
