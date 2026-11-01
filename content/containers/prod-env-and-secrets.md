---
id: prod-env-and-secrets
title: Environment Config and Secrets in Production
zone: containers
edges:
  to:
    - id: healthchecks-and-monitoring
      question: Config is sorted. How do I know if the containers are actually healthy?
      detail: >-
        Everything seems to be running, but "seems to" isn't good enough in
        production. I want to know if a container is actually serving traffic
        correctly, not just that the process is alive.
difficulty: 2
tags:
  - docker
  - production
  - secrets
  - environment
  - configuration
category: practice
milestones:
  - Understand why you must never bake secrets into Docker images
  - Use env_file in Compose to inject config from a file not committed to git
  - Understand the difference between build-time ARG and runtime ENV
  - Know the options for secrets in production (env vars, mounted files, secret managers)
  - Use a mounted secrets file as a step up from plain env vars
  - Know what to do when a secret rotates — how to update without downtime
title_zh: "生产环境中的环境配置与密钥管理"

---


Config and secrets are different things that get treated the same way and shouldn't be. Config — log level, port, feature flags — is environment-specific but not sensitive. Secrets — database passwords, API keys, signing keys — are sensitive. If they're ever in an image layer, a commit, or a process listing, you have a problem. Neither belongs in the image. Both need to get into the container at runtime.

The good news is that the mechanics are simple. The discipline is harder: it requires understanding where values end up and who can read them at each stage of the build and deploy pipeline.

<!-- DEEP_DIVE -->

## Why secrets can't live in images

An image is an artifact pushed to a registry — accessible to anyone with pull access. Once a secret is written to a layer, it's permanently in that layer. Even if you delete it in a subsequent `RUN` step, the original layer still contains it and is still in the image.

You can extract any layer from an image:

```bash
docker save myapp:latest | tar x
# layers are now directories — find and unpack them to read their contents
```

If credentials are in those layers, anyone who can pull the image can read them. That includes developers who shouldn't have production access, CI systems with registry pull permissions, and anyone who gains access to the registry.

A secondary problem: when a secret rotates, you'd need to rebuild and push a new image just to change a credential. That's the wrong coupling — the image should represent a version of your code, not a version of your secrets.

**Rule: images contain code. Secrets are injected at runtime.**

## env_file in Compose

The straightforward way to inject environment variables from a file:

```yaml
services:
  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    env_file:
      - .env.prod
```

`.env.prod` lives on the server, not in the repository:

```
DATABASE_URL=postgres://appuser:secret@db:5432/myapp
API_KEY=sk-prod-abc123
APP_ENV=production
LOG_LEVEL=info
```

Keep a `.env.example` in the repo with placeholder values documenting what variables are needed:

```
DATABASE_URL=postgres://user:password@localhost:5432/myapp
API_KEY=your-api-key-here
APP_ENV=development
LOG_LEVEL=debug
```

`.env.prod` must be in `.gitignore`. If it ever lands in git history — even briefly, even in a commit you intend to revert — assume those credentials are compromised and rotate every one of them immediately. Git history is permanent and widely cached.

## ARG vs ENV

These two Dockerfile instructions look similar but behave very differently:

**`ARG`** — build-time only. Available during `docker build`, not in the running container, and not persisted in image layers in the same way.

```dockerfile
ARG BUILD_VERSION
RUN echo "Building version $BUILD_VERSION"
# BUILD_VERSION is not available at runtime
```

Use `ARG` for things that vary between builds but aren't sensitive: version strings, registry URLs, build timestamps.

**`ENV`** — persisted in the image. Available at runtime, visible in `docker inspect`, and readable from `docker history`.

```dockerfile
ENV APP_PORT=8000
ENV LOG_FORMAT=json
```

`ENV` is fine for non-sensitive runtime defaults that you want baked into the image. **Do not use `ENV` for secrets** — the value is in the image metadata and readable by anyone who can inspect it.

Override `ENV` defaults at runtime without rebuilding the image:

```bash
docker run -e APP_PORT=9000 myapp
# or in compose:
environment:
  - APP_PORT=9000
```

## The spectrum of secret management

Options in order of simplicity to robustness:

**1. Plain environment variables**

`docker run -e SECRET=value` or Compose `environment:` block. Simple, but secrets appear in `docker inspect`, in `/proc/<pid>/environ` on the host, and in any logging that dumps environment variables. Avoid for anything sensitive.

**2. env_file**

Keeps secrets out of the compose file and run commands. The secrets live on disk on the server. Anyone with SSH access can read them, but they're not in docker inspect output by default. This is the practical baseline for most single-server setups.

**3. Mounted secret files**

Mount a file containing the secret into the container:

```yaml
services:
  app:
    volumes:
      - /run/secrets/db_password:/run/secrets/db_password:ro
```

The application reads the secret from the file rather than from an environment variable:

```python
with open("/run/secrets/db_password") as f:
    db_password = f.read().strip()
```

The secret doesn't appear in `docker inspect` environment output or in process listings. The file can have tight permissions (`chmod 400`). This is a meaningful step up from env vars for sensitive credentials.

**4. External secret manager**

HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager. Secrets live in a dedicated, audited system. The application (or a sidecar) fetches secrets at startup using short-lived credentials. Secret rotation doesn't require touching individual servers. Access is logged and auditable.

This is the right level for large teams, compliance requirements (SOC 2, HIPAA), or any situation where you need to know who accessed what and when.

For most teams running on a single server, `env_file` or mounted secret files is sufficient. Don't add external secret management complexity until you have a clear reason.

## Secret rotation

When a secret changes, the container needs to pick up the new value. The approach depends on how the secret is delivered.

**env_file approach** — update the file, restart the container:

```bash
# edit .env.prod with the new value, then:
docker compose -f docker-compose.prod.yml restart app
```

**Mounted file approach** — update the file on the host; whether the app picks it up depends on whether it re-reads the file:

```bash
# update the file
echo "new-password" | sudo tee /run/secrets/db_password > /dev/null
sudo chmod 400 /run/secrets/db_password

# if the app doesn't watch for file changes, restart it
docker compose -f docker-compose.prod.yml restart app
```

**Zero-downtime rotation** requires either:
- Applications designed to re-read secrets on a signal (SIGHUP) — possible but requires code support
- A manual blue-green swap: start a new container with the new secret, shift traffic, stop the old one
- An external secret manager where the application fetches credentials dynamically and handles rotation in code

For most deployments, a brief restart during rotation is acceptable. If it isn't, design for it from the start — retrofitting zero-downtime secret rotation is significantly harder.

<!-- RESOURCES -->

- [Docker secrets documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker BuildKit --secret flag](https://docs.docker.com/build/building/secrets/)
- [The Twelve-Factor App: Config](https://12factor.net/config)

<!-- ZH_SUMMARY -->
配置和密钥是两种不同的东西，却常常被同等对待，这是不应该的。配置——日志级别、端口、功能开关——因环境而异，但并不敏感。密钥——数据库密码、API 密钥、签名密钥——则是敏感的。一旦它们出现在镜像层、提交记录或进程列表中，你就麻烦了。两者都不应放进镜像里。两者都需要在运行时注入容器。

好消息是，机制本身很简单。难的是纪律：它要求你理解在构建和部署流水线的每个阶段，这些值最终会落在哪里，以及谁能够读取它们。

<!-- ZH_DEEP_DIVE -->
## 为什么密钥不能存放在镜像中

镜像是一个推送到 registry 的制品——任何拥有拉取权限的人都可以访问。一旦密钥被写入某一层，它就会永久存在于该层中。即使在后续的 `RUN` 步骤中将其删除，原始层仍然包含它，并且仍然存在于镜像中。

你可以从镜像中提取任意层：

```bash
docker save myapp:latest | tar x
# layers are now directories — find and unpack them to read their contents
```

如果凭据存在于这些层中，任何能够拉取该镜像的人都可以读取它们。这包括不应拥有生产访问权限的开发者、拥有 registry 拉取权限的 CI 系统，以及任何获得 registry 访问权限的人。

第二个问题：当密钥轮换时，你仅仅为了更改一个凭据就需要重新构建并推送一个新镜像。这是一种错误的耦合——镜像应该代表代码的某个版本，而不是密钥的某个版本。

**规则：镜像包含代码。密钥在运行时注入。**

## Compose 中的 env_file

从文件注入环境变量的直接方式：

```yaml
services:
  app:
    image: ghcr.io/myorg/myapp:${IMAGE_TAG}
    env_file:
      - .env.prod
```

`.env.prod` 位于服务器上，而不是仓库中：

```
DATABASE_URL=postgres://appuser:secret@db:5432/myapp
API_KEY=sk-prod-abc123
APP_ENV=production
LOG_LEVEL=info
```

在仓库中保留一个 `.env.example`，其中包含占位值，记录需要哪些变量：

```
DATABASE_URL=postgres://user:password@localhost:5432/myapp
API_KEY=your-api-key-here
APP_ENV=development
LOG_LEVEL=debug
```

`.env.prod` 必须位于 `.gitignore` 中。如果它曾经进入 git 历史——即使是短暂的，即使是在你打算回滚的提交中——请假定这些凭据已泄露，并立即轮换其中的每一个。Git 历史是永久的，并且被广泛缓存。

## ARG 与 ENV

这两个 Dockerfile 指令看起来相似，但行为非常不同：

**`ARG`** —— 仅构建时。在 `docker build` 期间可用，在运行中的容器中不可用，并且不会以相同方式持久化到镜像层中。

```dockerfile
ARG BUILD_VERSION
RUN echo "Building version $BUILD_VERSION"
# BUILD_VERSION is not available at runtime
```

将 `ARG` 用于构建之间会变化但不敏感的内容：版本字符串、registry URL、构建时间戳。

**`ENV`** —— 持久化在镜像中。在运行时可用，在 `docker inspect` 中可见，并且可以从 `docker history` 中读取。

```dockerfile
ENV APP_PORT=8000
ENV LOG_FORMAT=json
```

`ENV` 适用于你希望烘焙到镜像中的非敏感运行时默认值。**不要将 `ENV` 用于密钥**——该值存在于镜像元数据中，任何能够检查它的人都可以读取。

在运行时覆盖 `ENV` 默认值而无需重新构建镜像：

```bash
docker run -e APP_PORT=9000 myapp
# or in compose:
environment:
  - APP_PORT=9000
```

## 密钥管理的谱系

按从简单到健壮的顺序排列的选项：

**1. 普通环境变量**

`docker run -e SECRET=value` 或 Compose 的 `environment:` 块。简单，但密钥会出现在 `docker inspect` 中、主机上的 `/proc/<pid>/environ` 中，以及任何转储环境变量的日志中。避免用于任何敏感内容。

**2. env_file**

将密钥排除在 compose 文件和运行命令之外。密钥存在于服务器磁盘上。任何拥有 SSH 访问权限的人都可以读取它们，但默认情况下它们不会出现在 docker inspect 输出中。对于大多数单服务器设置，这是实用的基线。

**3. 挂载的密钥文件**

将包含密钥的文件挂载到容器中：

```yaml
services:
  app:
    volumes:
      - /run/secrets/db_password:/run/secrets/db_password:ro
```

应用程序从文件而不是从环境变量读取密钥：

```python
with open("/run/secrets/db_password") as f:
    db_password = f.read().strip()
```

密钥不会出现在 `docker inspect` 的环境输出或进程列表中。文件可以具有严格的权限（`chmod 400`）。对于敏感凭据，这是相比环境变量的有意义的提升。

**4. 外部密钥管理器**

HashiCorp Vault、AWS Secrets Manager、GCP Secret Manager。密钥存在于专用的、经过审计的系统中。应用程序（或 sidecar）在启动时使用短期凭据获取密钥。密钥轮换不需要触及各个服务器。访问被记录并可审计。

对于大型团队、合规要求（SOC 2、HIPAA），或任何你需要知道谁在何时访问了什么的情况，这是正确的级别。

对于大多数在单台服务器上运行的团队，`env_file` 或挂载的密钥文件就足够了。在你有一个明确的理由之前，不要添加外部密钥管理的复杂性。

## 密钥轮换

当密钥更改时，容器需要获取新值。方法取决于密钥的传递方式。

**env_file 方式** —— 更新文件，重启容器：

```bash
# edit .env.prod with the new value, then:
docker compose -f docker-compose.prod.yml restart app
```

**挂载文件方式** —— 更新主机上的文件；应用程序是否获取它取决于它是否重新读取文件：

```bash
# update the file
echo "new-password" | sudo tee /run/secrets/db_password > /dev/null
sudo chmod 400 /run/secrets/db_password

# if the app doesn't watch for file changes, restart it
docker compose -f docker-compose.prod.yml restart app
```

**零停机轮换**需要以下之一：
- 设计为在信号（SIGHUP）上重新读取密钥的应用程序——可行但需要代码支持
- 手动蓝绿切换：使用新密钥启动一个新容器，切换流量，停止旧容器
- 一个外部密钥管理器，应用程序动态获取凭据并在代码中处理轮换

对于大多数部署，轮换期间的短暂重启是可以接受的。如果不可接受，请从一开始就为此设计——事后改造零停机密钥轮换要困难得多。

<!-- ZH_RESOURCES -->
- [Docker secrets 文档](https://docs.docker.com/engine/swarm/secrets/)
- [Docker BuildKit --secret 标志](https://docs.docker.com/build/building/secrets/)
- [十二要素应用：配置](https://12factor.net/config)

<!-- ZH_UI -->
1. 理解为什么绝不能将密钥烘焙进 Docker 镜像
2. 在 Compose 中使用 env_file 从不会提交到 git 的文件注入配置
3. 理解构建时 ARG 与运行时 ENV 的区别
4. 了解生产环境中密钥的几种方案（环境变量、挂载文件、密钥管理器）
5. 使用挂载的密钥文件，作为比纯环境变量更进一步的做法
6. 了解密钥轮换时该怎么做——如何在不中断服务的情况下更新
7. 配置已就绪。我怎么知道容器是否真的健康？
8. 一切看起来都在运行，但“看起来”在生产环境中还不够。我想知道容器是否真的在正确地处理流量，而不只是进程还活着。
