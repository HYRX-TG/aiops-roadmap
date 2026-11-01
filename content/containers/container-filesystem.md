---
id: container-filesystem
title: Image Layers and the Union Filesystem
zone: containers
edges:
  to:
    - id: docker-first-container
      question: I get how Docker works internally. Let me actually start using it.
      detail: >-
        I understand namespaces, cgroups, and how image layers are stored. Now
        I want to put that into practice — pull an image and run my first container.
difficulty: 2
tags:
  - containers
  - linux
  - overlayfs
  - internals
  - images
category: concept
milestones:
  - Understand what a union filesystem is and why Docker uses one
  - Know how image layers are stacked (read-only layers + writable layer on top)
  - Understand copy-on-write and what it means for container filesystem changes
  - Know where Docker stores layers on disk (/var/lib/docker)
  - Understand why layer sharing makes pulling images efficient
title_zh: "镜像层与联合文件系统"

---


A container image isn't a single file or a disk snapshot. It's a stack of **layers**, each containing only the filesystem changes from the step before it. A **union filesystem** (Docker uses OverlayFS on most Linux hosts) merges these read-only layers into a single coherent filesystem that the container sees as its root. On top of that stack sits a thin writable layer, unique to each running container, where all writes go.

This design is why `docker pull` shows "Already exists" for layers your system has already seen, why builds that change one line don't re-download the world, and why ten containers running the same image don't consume ten times the disk. The layers are stored once and referenced by every container that needs them.

<!-- DEEP_DIVE -->

## The problem union filesystems solve

Without layer sharing, each image would be a complete, standalone copy of every file it contains. Two images both based on `ubuntu:22.04` would each store a separate full copy of the Ubuntu filesystem — roughly 80 MB each, duplicated on disk. At scale this becomes significant: a host pulling hundreds of images accumulates enormous redundancy.

**OverlayFS** solves this by stacking multiple directory trees as a single unified view. Each layer is a directory on the host. OverlayFS merges them top-to-bottom: files in higher layers shadow files with the same path in lower layers. The result looks like one filesystem but the data is stored separately per layer.

Layers are identified by a content hash. If two images share a base layer — even if they have completely different names and purposes — they reference the same content-addressed layer on disk. Docker stores it once.

## How image layers work

Each Dockerfile instruction that modifies the filesystem produces a new layer containing only the diff from the previous state. Instructions that don't touch the filesystem (like `ENV` or `EXPOSE`) don't produce a filesystem layer.

```dockerfile
FROM ubuntu:22.04                          # Layer 1: base Ubuntu filesystem
RUN apt-get install -y python3             # Layer 2: python3 and its dependencies added
COPY . /app                                # Layer 3: your application code
RUN pip install -r /app/requirements.txt  # Layer 4: Python packages installed
```

Layer 1 is the full Ubuntu base. Layer 2 contains only the files that `apt-get` added or modified — nothing else. Layer 3 contains only your application files. Layer 4 contains only the installed packages.

All four layers are read-only once built. They're immutable — a layer's content never changes after creation, which is how Docker can safely identify and deduplicate them by hash.

## The writable container layer

When Docker starts a container, it assembles the image layers into a merged view using OverlayFS and adds one additional **writable layer** on top. This writable layer is where all container filesystem writes go — log files written to disk, config files modified at runtime, anything created or changed during the container's lifetime.

**Copy-on-write** is the mechanism that makes this work for writes to existing files. If a container modifies a file that exists in one of the read-only image layers, OverlayFS first copies that file up into the writable layer, then applies the modification there. The original in the read-only layer is untouched. From the container's perspective, it sees the modified version in its unified filesystem view.

Consequences:

- When a container is deleted, its writable layer is discarded. The image layers are untouched.
- Ten containers from the same image share all the read-only image layers but each has its own independent writable layer.
- Writes that modify large files from the base layers are expensive the first time (the full file is copied up before the modification), but subsequent writes to that file are cheap.
- Data you need to persist beyond a container's lifetime must go into a **volume** or a **bind mount**, which bypass the writable layer entirely.

## Where layers live on disk

Docker stores layer data under `/var/lib/docker/overlay2/` on systems using OverlayFS (the default on most modern Linux distributions). Each subdirectory corresponds to a layer. You'll find `diff/` (the layer's filesystem content), `link` (a short identifier), and `lower` (a reference to the parent layers).

```bash
docker pull ubuntu:22.04
ls /var/lib/docker/overlay2/
```

You can inspect the layers for a specific image:

```bash
docker image inspect ubuntu:22.04 --format '{{json .GraphDriver}}'
```

When you pull a second image based on the same Ubuntu base, Docker checks whether each layer's hash already exists locally. The layers that match print "Already exists" and are not re-downloaded. Only new layers transfer.

## What this means for builds

Layer caching is the most practical consequence of this architecture. Docker checks each build step: if the instruction is identical **and** its inputs are unchanged (for `COPY`, the files being copied), it reuses the cached layer and skips re-executing the instruction. The moment any step's inputs change, that layer is **invalidated** — and so are all subsequent layers, because they were built on top of it.

This has a direct implication for how you order Dockerfile instructions:

```dockerfile
# Good: dependencies installed before code is copied
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY . /app                        # changing app code only invalidates from here

# Bad: copying all code first
COPY . /app
RUN pip install -r /app/requirements.txt  # reinstalls on every code change
```

Put instructions that change infrequently (system package installs, dependency installations) near the top. Put instructions whose inputs change frequently (copying your application code) near the bottom. This maximizes cache hits and keeps builds fast.

Inspect the layers of any image to see what each instruction produced and how large each layer is:

```bash
docker history <image>
```

This prints each layer, the command that created it, and its size. Large unexpected layers usually mean a `RUN` instruction left behind build artifacts or temporary files that should have been cleaned up in the same layer.

<!-- RESOURCES -->

- [Docker storage drivers — Docker Docs](https://docs.docker.com/storage/storagedriver/)
- [Use the OverlayFS storage driver — Docker Docs](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)
- [OverlayFS — kernel.org documentation](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html)

<!-- ZH_SUMMARY -->
容器镜像不是单个文件，也不是磁盘快照。它是由**层**（layer）堆叠而成的，每一层只包含相对于前一步的文件系统变更。**联合文件系统**（union filesystem，Docker 在大多数 Linux 主机上使用 OverlayFS）将这些只读层合并为一个连贯的文件系统，容器将其视为自己的根文件系统。在这个堆栈之上，还有一个薄薄的可写层，每个运行中的容器独有，所有写入操作都发生在这里。

正是这种设计，使得 `docker pull` 对你系统已经见过的层显示“Already exists”，使得只改一行的构建不会重新下载整个世界，也使得运行同一镜像的十个容器不会消耗十倍的磁盘空间。这些层只存储一次，并被每个需要它们的容器引用。

<!-- ZH_DEEP_DIVE -->
## 联合文件系统解决的问题

如果没有层共享，每个镜像都会是其包含的每个文件的完整、独立副本。两个都基于 `ubuntu:22.04` 的镜像会各自存储一份完整的 Ubuntu 文件系统副本——每个大约 80 MB，在磁盘上重复存储。在大规模场景下这会变得非常显著：一台拉取了数百个镜像的主机会累积巨大的冗余。

**OverlayFS** 通过将多个目录树叠加为单一统一视图来解决这个问题。每一层都是主机上的一个目录。OverlayFS 自上而下合并它们：较高层中的文件会遮蔽较低层中相同路径的文件。结果看起来像一个文件系统，但数据是按层分别存储的。

层通过内容哈希来标识。如果两个镜像共享一个基础层——即使它们的名称和用途完全不同——它们也会引用磁盘上同一个内容寻址的层。Docker 只存储一次。

## 镜像层的工作原理

每条修改文件系统的 Dockerfile 指令都会产生一个新层，其中只包含与前一状态的差异。不触及文件系统的指令（如 `ENV` 或 `EXPOSE`）不会产生文件系统层。

```dockerfile
FROM ubuntu:22.04                          # Layer 1: base Ubuntu filesystem
RUN apt-get install -y python3             # Layer 2: python3 and its dependencies added
COPY . /app                                # Layer 3: your application code
RUN pip install -r /app/requirements.txt  # Layer 4: Python packages installed
```

第 1 层是完整的 Ubuntu 基础。第 2 层只包含 `apt-get` 添加或修改的文件——没有其他内容。第 3 层只包含你的应用程序文件。第 4 层只包含已安装的软件包。

所有四个层在构建后都是只读的。它们是不可变的——层的内容在创建后永远不会改变，这正是 Docker 能够安全地通过哈希识别和去重它们的原因。

## 可写容器层

当 Docker 启动容器时，它使用 OverlayFS 将镜像层组装成合并视图，并在顶部添加一个额外的**可写层**。这个可写层是所有容器文件系统写入的去处——写入磁盘的日志文件、运行时修改的配置文件、容器生命周期内创建或更改的任何内容。

**写时复制**是使对现有文件的写入得以工作的机制。如果容器修改了只读镜像层中存在的文件，OverlayFS 会先将该文件复制到可写层，然后在那里应用修改。只读层中的原始文件保持不变。从容器的角度来看，它在统一文件系统视图中看到的是修改后的版本。

后果：

- 当容器被删除时，其可写层会被丢弃。镜像层不受影响。
- 来自同一镜像的十个容器共享所有只读镜像层，但每个容器都有自己独立的可写层。
- 修改基础层中大文件的写入在第一次时开销较大（修改前会复制完整文件），但之后对该文件的写入开销较小。
- 需要在容器生命周期之后持久化的数据必须放入**卷**或**绑定挂载**，它们完全绕过可写层。

## 层在磁盘上的位置

在使用 OverlayFS 的系统上（大多数现代 Linux 发行版的默认配置），Docker 将层数据存储在 `/var/lib/docker/overlay2/` 下。每个子目录对应一个层。你会找到 `diff/`（层的文件系统内容）、`link`（一个短标识符）和 `lower`（对父层的引用）。

```bash
docker pull ubuntu:22.04
ls /var/lib/docker/overlay2/
```

你可以检查特定镜像的层：

```bash
docker image inspect ubuntu:22.04 --format '{{json .GraphDriver}}'
```

当你拉取第二个基于相同 Ubuntu 基础的镜像时，Docker 会检查每个层的哈希是否已存在于本地。匹配的层会打印 "Already exists"，不会被重新下载。只有新层会传输。

## 这对构建意味着什么

层缓存是这种架构最实际的后果。Docker 检查每个构建步骤：如果指令完全相同**并且**其输入未改变（对于 `COPY`，即被复制的文件），它会复用缓存的层并跳过重新执行该指令。一旦任何步骤的输入发生变化，该层就会**失效**——所有后续层也会失效，因为它们构建在其之上。

这对你如何排列 Dockerfile 指令有直接影响：

```dockerfile
# Good: dependencies installed before code is copied
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY . /app                        # changing app code only invalidates from here

# Bad: copying all code first
COPY . /app
RUN pip install -r /app/requirements.txt  # reinstalls on every code change
```

将不常变化的指令（系统软件包安装、依赖安装）放在靠近顶部的位置。将输入频繁变化的指令（复制应用程序代码）放在靠近底部的位置。这能最大化缓存命中并保持构建快速。

检查任何镜像的层，以查看每条指令产生了什么以及每个层有多大：

```bash
docker history <image>
```

这会打印每个层、创建它的命令及其大小。意外的大层通常意味着某条 `RUN` 指令留下了构建产物或临时文件，而这些本应在同一层中清理掉。

<!-- ZH_RESOURCES -->
- [Docker 存储驱动 — Docker 文档](https://docs.docker.com/storage/storagedriver/)
- [使用 OverlayFS 存储驱动 — Docker 文档](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)
- [OverlayFS — kernel.org 文档](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html)

<!-- ZH_UI -->
1. 理解联合文件系统是什么，以及 Docker 为什么使用它
2. 了解镜像层如何堆叠（只读层 + 顶层可写层）
3. 理解写时复制及其对容器文件系统更改的意义
4. 了解 Docker 在磁盘上存储层的位置（/var/lib/docker）
5. 理解层共享为何使拉取镜像更高效
6. 我已了解 Docker 的内部工作原理，现在要真正开始使用它。
7. 我理解了命名空间、cgroups 以及镜像层的存储方式。现在我想付诸实践——拉取一个镜像并运行我的第一个容器。
