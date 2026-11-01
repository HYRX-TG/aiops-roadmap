---
id: container-security-basics
title: Container Security Basics
zone: containers
edges:
  to:
    - id: docker-compose-dev
      question: My images are optimized and reasonably secure. How do I run multiple services together locally?
      detail: >-
        I've got my app containerized properly. Now I need Postgres and Redis
        running alongside it — I'm starting everything separately and it's
        getting messy.
difficulty: 2
tags:
  - docker
  - containers
  - security
  - dockerfile
category: practice
milestones:
  - Add a USER instruction to run the container process as a non-root user
  - Understand why running as root inside a container is a real risk even with namespace isolation
  - Never bake secrets or credentials into an image layer
  - Use read-only filesystems with --read-only where possible
  - Scan images for known CVEs with docker scout or trivy
  - Understand what --cap-drop and --cap-add do and why dropping capabilities matters
title_zh: "容器安全基础"

---


Most container security problems aren't sophisticated exploits — they're basic misconfigurations that make a bad situation worse if something else goes wrong. Running processes as root, baking API keys into image layers, shipping fat images full of outdated packages. None of these things are immediately exploitable on their own, but each one turns a minor vulnerability into a major incident.

The security model for containers is defense in depth. The namespace and cgroup isolation Docker provides is real, but it's not a hard boundary the way a VM is. A container escape vulnerability in the container runtime — and they have happened — means your process's privileges matter. A non-root process with dropped capabilities in a read-only container is a much harder target than a root process with full privileges.

<!-- DEEP_DIVE -->

## The root problem

By default, container processes run as root (UID 0). This is the same UID 0 as the host. The container namespace creates isolation at the process and filesystem level, but the user identity is shared.

This matters most in a container escape scenario. CVE-2019-5736 was a real vulnerability in `runc` (the container runtime Docker uses) that allowed a malicious container to overwrite the host's `runc` binary. An attacker who could run arbitrary code inside the container could escape and execute code on the host with root privileges — because the container process was already running as root.

With a non-root container process, the same escape gives the attacker a shell on the host as an unprivileged user. That's still bad, but the blast radius is dramatically smaller. They can't read `/etc/shadow`, can't install kernel modules, can't bind to privileged ports.

Running as non-root is the single highest-leverage security change you can make to a Dockerfile.

## Running as non-root

Add a `USER` instruction at the end of your Dockerfile, after creating a dedicated user:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `--chown` flag on `COPY` matters. If you copy files as root and then switch to `appuser`, the non-root user may not be able to read them. Own files as the user that needs to read them.

Many official images already provide a non-root user. The official `node` image has a `node` user, `nginx` has `nginx`. Check the image's documentation or Dockerfile before creating your own:

```dockerfile
FROM node:20-slim
# The 'node' user already exists — use it
USER node
```

## Secrets don't belong in images

Every layer in a Docker image is permanent and addressable. If you add a secret in one layer and try to delete it in the next, the original layer still contains it — it's visible to anyone who can pull the image and inspect the layer directly.

```dockerfile
# Wrong: secret is in the image history forever
COPY .npmrc /root/.npmrc
RUN npm install
RUN rm /root/.npmrc

# Also wrong: visible in docker inspect and docker history
ENV NPM_TOKEN=secret_token_here
RUN npm install
```

For runtime secrets, pass them at runtime, not build time:

```bash
docker run -e DATABASE_URL="postgres://user:pass@host/db" myapp
```

For build-time secrets — like a `.npmrc` with a private registry token — use Docker BuildKit's `--secret` flag. The secret is mounted as a file during that `RUN` instruction and is never written to any layer:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-slim AS build

WORKDIR /app
COPY package*.json ./

RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci

COPY . .
RUN npm run build
```

Build with:

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc -t myapp .
```

The `.npmrc` is available during `npm ci` and gone afterward — it never appears in any layer.

## Read-only filesystems

Most application containers don't need to write to their filesystem at runtime. If yours doesn't, make that explicit:

```bash
docker run --read-only myapp
```

If the app tries to write somewhere unexpected, it fails loudly with a permission error rather than silently. That's useful both as a security control and as a way to discover unintended write behavior.

Apps that need scratch space (temp files, caches) can get a writable tmpfs mount for specific directories:

```bash
docker run --read-only --tmpfs /tmp myapp
```

Or in a Compose file:

```yaml
services:
  app:
    image: myapp
    read_only: true
    tmpfs:
      - /tmp
```

## Linux capabilities

Linux capabilities break root's privileges into discrete units. Docker grants containers a default subset — enough for most apps, but more than most apps actually need.

```bash
# Drop everything, add back only what you need
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp
```

Common capabilities and what they allow:

- **`NET_BIND_SERVICE`**: bind to ports below 1024. Most apps should use ports above 1024 instead and not need this at all.
- **`SYS_PTRACE`**: attach a debugger to a process. Never needed in production.
- **`SYS_ADMIN`**: a broad capability covering many privileged operations. Almost never needed.
- **`CHOWN`**, **`SETUID`**, **`SETGID`**: manipulate file ownership and user identity. Needed by some apps during startup, not at runtime.

Never use `--privileged` in production. It disables all capability restrictions, all seccomp profiles, and gives the container nearly full access to the host kernel. It exists for specific use cases (running Docker inside Docker, certain system tooling) and is frequently misused as a quick fix when something doesn't work.

## Image scanning

A lean, non-root image that was built six months ago may still have dozens of known CVEs in its base image packages. Scanning catches these.

```bash
# Docker's built-in scanner (requires Docker Desktop or Docker Hub login)
docker scout cves myapp:latest

# trivy — open source, no login required, widely used in CI
trivy image myapp:latest

# Fail the build if HIGH or CRITICAL vulnerabilities are found
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest
```

In a CI pipeline, run `trivy` as part of the image build step. Set a severity threshold that fails the build — `HIGH` and `CRITICAL` is a reasonable starting point. Lower severity findings are often too noisy to gate on initially.

One important caveat: new CVEs are published against packages that haven't changed. An image that passed scanning when it was built may fail a week later. Running scans in CI on every build helps, but also consider periodic re-scans of images already deployed to production.

<!-- RESOURCES -->

- [Docker security best practices](https://docs.docker.com/develop/security-best-practices/)
- [trivy documentation](https://aquasecurity.github.io/trivy/)
- [Docker BuildKit secrets](https://docs.docker.com/build/building/secrets/)
- [Linux capabilities man page](https://man7.org/linux/man-pages/man7/capabilities.7.html)

<!-- ZH_SUMMARY -->
大多数容器安全问题并非复杂的漏洞利用——而是基础性的错误配置，一旦其他环节出问题，就会让糟糕的局面雪上加霜。以 root 身份运行进程、把 API 密钥烘焙进镜像层、发布塞满过时软件包的臃肿镜像。这些事情单独来看都不会立即被利用，但每一个都会把轻微的漏洞变成重大事故。

容器的安全模型是纵深防御。Docker 提供的 namespace 和 cgroup 隔离是真实有效的，但它不像 VM 那样是一道硬边界。容器运行时中的容器逃逸漏洞——而且这类漏洞确实发生过——意味着你进程的权限至关重要。在只读容器中、已丢弃 capabilities 的非 root 进程，比拥有完整权限的 root 进程要难攻击得多。

<!-- ZH_DEEP_DIVE -->
## 根本问题

默认情况下，容器进程以 root（UID 0）身份运行。这与宿主机上的 UID 0 是同一个。容器命名空间在进程和文件系统层面创建了隔离，但用户身份是共享的。

这在容器逃逸场景中影响最大。CVE-2019-5736 是 `runc`（Docker 使用的容器运行时）中的一个真实漏洞，它允许恶意容器覆盖宿主机的 `runc` 二进制文件。能够在容器内运行任意代码的攻击者可以逃逸，并以 root 权限在宿主机上执行代码——因为容器进程本身就已经以 root 身份运行。

如果容器进程以非 root 身份运行，同样的逃逸只会给攻击者一个宿主机上非特权用户的 shell。这仍然很糟糕，但影响范围会大幅缩小。他们无法读取 `/etc/shadow`，无法安装内核模块，无法绑定特权端口。

以非 root 身份运行是你能对 Dockerfile 做出的单点收益最高的安全变更。

## 以非 root 身份运行

在创建专用用户之后，在 Dockerfile 末尾添加 `USER` 指令：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`COPY` 上的 `--chown` 标志很重要。如果你以 root 身份复制文件然后切换到 `appuser`，非 root 用户可能无法读取这些文件。让文件归属于需要读取它们的用户。

许多官方镜像已经提供了非 root 用户。官方 `node` 镜像有 `node` 用户，`nginx` 有 `nginx` 用户。在创建自己的用户之前，先查看镜像的文档或 Dockerfile：

```dockerfile
FROM node:20-slim
# The 'node' user already exists — use it
USER node
```

## 密钥不应存在于镜像中

Docker 镜像中的每一层都是永久且可寻址的。如果你在一层中添加了密钥，并试图在下一层中删除它，原始层仍然包含它——任何能拉取镜像并直接检查该层的人都能看到。

```dockerfile
# Wrong: secret is in the image history forever
COPY .npmrc /root/.npmrc
RUN npm install
RUN rm /root/.npmrc

# Also wrong: visible in docker inspect and docker history
ENV NPM_TOKEN=secret_token_here
RUN npm install
```

对于运行时密钥，在运行时传递，而不是在构建时：

```bash
docker run -e DATABASE_URL="postgres://user:pass@host/db" myapp
```

对于构建时密钥——比如带有私有仓库令牌的 `.npmrc`——使用 Docker BuildKit 的 `--secret` 标志。密钥在该 `RUN` 指令期间以文件形式挂载，并且永远不会写入任何层：

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-slim AS build

WORKDIR /app
COPY package*.json ./

RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci

COPY . .
RUN npm run build
```

使用以下命令构建：

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc -t myapp .
```

`.npmrc` 在 `npm ci` 期间可用，之后便消失——它永远不会出现在任何层中。

## 只读文件系统

大多数应用容器在运行时不需要写入其文件系统。如果你的容器也不需要，请明确声明：

```bash
docker run --read-only myapp
```

如果应用试图写入意外位置，它会以权限错误大声失败，而不是静默失败。这既是一种安全控制，也是发现意外写入行为的有用方式。

需要暂存空间（临时文件、缓存）的应用可以为特定目录获得可写的 tmpfs 挂载：

```bash
docker run --read-only --tmpfs /tmp myapp
```

或者在 Compose 文件中：

```yaml
services:
  app:
    image: myapp
    read_only: true
    tmpfs:
      - /tmp
```

## Linux capabilities

Linux capabilities 将 root 的权限分解为离散的单元。Docker 授予容器一个默认子集——对大多数应用来说足够，但比大多数应用实际需要的要多。

```bash
# Drop everything, add back only what you need
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp
```

常见 capabilities 及其允许的操作：

- **`NET_BIND_SERVICE`**：绑定 1024 以下的端口。大多数应用应改用 1024 以上的端口，从而完全不需要此 capability。
- **`SYS_PTRACE`**：将调试器附加到进程。生产环境中永远不需要。
- **`SYS_ADMIN`**：一个涵盖许多特权操作的宽泛 capability。几乎永远不需要。
- **`CHOWN`**、**`SETUID`**、**`SETGID`**：操作文件所有权和用户身份。某些应用在启动时需要，运行时不需要。

永远不要在生产环境中使用 `--privileged`。它会禁用所有 capability 限制、所有 seccomp 配置文件，并给予容器对宿主机内核的几乎完全访问权限。它存在是为了特定用例（在 Docker 中运行 Docker、某些系统工具），并且经常在出现问题时被误用作快速修复手段。

## 镜像扫描

一个六个月前构建的精简、非 root 镜像，其基础镜像包中可能仍然存在数十个已知 CVE。扫描可以捕获这些。

```bash
# Docker's built-in scanner (requires Docker Desktop or Docker Hub login)
docker scout cves myapp:latest

# trivy — open source, no login required, widely used in CI
trivy image myapp:latest

# Fail the build if HIGH or CRITICAL vulnerabilities are found
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest
```

在 CI 流水线中，将 `trivy` 作为镜像构建步骤的一部分运行。设置一个使构建失败的严重性阈值——`HIGH` 和 `CRITICAL` 是一个合理的起点。较低严重性的发现通常噪音太大，初期不适合作为门禁条件。

一个重要注意事项：新的 CVE 会针对未发生变化的包发布。一个在构建时通过扫描的镜像可能在一周后无法通过。在 CI 中对每次构建运行扫描有帮助，但也应考虑对已部署到生产环境的镜像进行定期重新扫描。

<!-- ZH_RESOURCES -->
- [Docker 安全最佳实践](https://docs.docker.com/develop/security-best-practices/)
- [trivy 文档](https://aquasecurity.github.io/trivy/)
- [Docker BuildKit secrets](https://docs.docker.com/build/building/secrets/)
- [Linux capabilities 手册页](https://man7.org/linux/man-pages/man7/capabilities.7.html)

<!-- ZH_UI -->
1. 添加 USER 指令，以非 root 用户运行容器进程
2. 理解为什么即使有命名空间隔离，在容器内以 root 运行仍是真实风险
3. 绝不将密钥或凭据烘焙进镜像层
4. 尽可能使用只读文件系统，配合 --read-only
5. 用 docker scout 或 trivy 扫描镜像中的已知 CVE
6. 理解 --cap-drop 和 --cap-add 的作用，以及为什么丢弃能力很重要
7. 我的镜像已优化且相对安全。如何在本地一起运行多个服务？
8. 我的应用已正确容器化。现在需要 Postgres 和 Redis 与它一起运行——我正分别启动所有东西，越来越乱。
