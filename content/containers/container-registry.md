---
id: container-registry
title: Container Registries
zone: containers
edges:
  to:
    - id: deploying-to-a-server
      question: >-
        My image is stored and versioned. How do I get it running on a real
        server?
      detail: >-
        I've pushed my image to a registry but I'm not sure how my server
        actually gets it and keeps it running. Do I ssh in and run docker pull
        every time? And what happens if the container crashes?
difficulty: 1
tags:
  - docker
  - container-registry
  - ghcr
  - ecr
  - images
  - containers
category: concept
milestones:
  - Push a Docker image to GitHub Container Registry (GHCR)
  - Pull a specific image version by tag on your server
  - Understand what image tags are for and why 'latest' is dangerous
  - Set up registry authentication in your CI pipeline
title_zh: "容器镜像仓库"

---


A container registry is where images live between being built and being run. It's the distribution layer — CI pushes to it, servers pull from it, and the tag on the image is how you know exactly which version you're running. Without a registry, an image exists only on the machine that built it, and there's no way to get it anywhere else without exporting and copying files manually.

The registry also enforces immutability through content-addressable storage. Every image has a digest — a SHA256 hash of its contents — that never changes. Tags are human-readable pointers to digests, and understanding the difference between the two is what separates a working deployment strategy from one that will eventually surprise you.

<!-- DEEP_DIVE -->

## What a registry is

A registry is an HTTP server implementing the [OCI Distribution Specification](https://github.com/opencontainers/distribution-spec). The spec defines how clients push and pull image layers, manifests, and tags. Because it's a standard, any OCI-compliant tool works against any compliant registry.

The main options:

- **Docker Hub** — the default. `docker pull nginx` implicitly pulls from `registry-1.docker.io`. Rate-limited for unauthenticated pulls.
- **GHCR** (GitHub Container Registry) — good default for GitHub projects. Auth uses GitHub credentials and tokens. Free for public images, included in GitHub plans for private.
- **ECR** (AWS Elastic Container Registry) — natural choice when deploying to AWS. Auth integrates with IAM.
- **Artifact Registry** (GCP) — GCP equivalent. Replaces the older Google Container Registry.
- **ACR** (Azure Container Registry) — Azure equivalent.

GHCR is usually the right choice for projects already on GitHub. Authentication uses the same `GITHUB_TOKEN` that CI already has, so there's no extra credential management.

## Pushing to GHCR

The workflow is: authenticate, tag your local image with the full registry path, push.

```bash
# authenticate — pipe the token to avoid it appearing in shell history
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# tag your local image with the full registry path
docker tag myapp:latest ghcr.io/<org>/<repo>:latest

# push
docker push ghcr.io/<org>/<repo>:latest

# on any other machine with credentials, pull it
docker pull ghcr.io/<org>/<repo>:latest
```

The image name must match the registry path exactly. `ghcr.io/<org>/<repo>` is the standard format — `org` is your GitHub username or organization, `repo` is the repository name.

By default, newly pushed packages on GHCR are private. You can change visibility in the package settings on GitHub, or link the package to a repository.

## Image tags

A tag is a **mutable pointer** — it's a name that points to an image manifest, and that name can be repointed to a different manifest at any time. `nginx:1.25.3` is relatively stable because that version was released once, but in principle anyone with push access could retag it.

An image **digest** is immutable. It's a SHA256 hash of the image manifest, and it identifies the exact bytes of that image forever. If you pull the same digest six months from now, you get exactly the same image.

```bash
# see the digest of a local image
docker inspect --format='{{index .RepoDigests 0}}' nginx:1.25.3

# pull by digest — will always be the same image
docker pull nginx@sha256:a484819eb60efa9577...
```

For most practical purposes, a git SHA tag (e.g., `myapp:a1b2c3d`) gives you the traceability you need without managing digests manually. It's semantically immutable — you'd never retag a git SHA — and it ties the image directly to its source commit.

## Why `latest` is dangerous in production

`latest` is not special. It's just a tag, and like any tag it's mutable. The problems it causes in production are consistent:

**Silent updates on restart.** If your deployment spec says `image: myapp:latest` and you push a new `latest` to the registry, the next time the container restarts — whether from a crash, a deploy, or a node reboot — it will pull the new version. You didn't explicitly deploy anything; the version changed beneath you.

**No traceability.** You can't look at a running container with tag `latest` and know what version it's running. You can't correlate it to a commit, a PR, or a point in time.

**Rollback is unclear.** To roll back, you need to know what the previous version was and retag `latest` to point at it. If you had been using SHA tags, rollback is just changing the tag in your deployment spec.

The rule is simple: in production, always deploy with a specific tag. Git SHA tags are the most traceable option.

## Registry authentication in CI

For GitHub Actions pushing to GHCR, the `GITHUB_TOKEN` that Actions provides automatically has sufficient permissions — no manual secret setup needed:

```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

The `permissions` block in the workflow job must include `packages: write` for the token to be allowed to push:

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
```

For other registries, the pattern is the same — authenticate, then push. AWS ECR requires generating a temporary token via the AWS CLI; there are Actions for this. Docker Hub uses repository secrets to store the username and access token.

## Pulling on a server

On the server, authenticate once and Docker will reuse the stored credentials for all subsequent pulls:

```bash
# authenticate
echo $TOKEN | docker login ghcr.io -u <username> --password-stdin

# pull a specific version by tag
docker pull ghcr.io/<org>/<repo>:<sha>
```

Credentials are stored in `~/.docker/config.json` for the user that ran `docker login`. Docker Compose reads them automatically when pulling images. This means if you run `docker compose pull` or `docker compose up` as the same user that authenticated, it will work without any extra configuration.

One practical note: if you're running Docker operations as root on the server (e.g., via a deploy script that uses `sudo`), root's `~/.docker/config.json` needs to hold the credentials — not your regular user's. Authenticate with `sudo docker login` in that case, or use a credential helper that makes credentials available system-wide.

<!-- RESOURCES -->

- [GitHub Container Registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [OCI Distribution Specification](https://github.com/opencontainers/distribution-spec)
- [docker login reference](https://docs.docker.com/reference/cli/docker/login/)
- [Image tags vs digests](https://docs.docker.com/reference/cli/docker/image/pull/#pull-an-image-by-digest-immutable-identifier)

<!-- ZH_SUMMARY -->
容器镜像仓库是镜像从构建到运行之间的存放之处。它是分发层——CI 向其推送镜像，服务器从中拉取镜像，而镜像上的标签则让你确切知道正在运行的是哪个版本。没有镜像仓库，镜像只存在于构建它的那台机器上，若不手动导出并复制文件，就无法将其传到其他地方。

镜像仓库还通过内容寻址存储来保证不可变性。每个镜像都有一个摘要（digest）——即其内容的 SHA256 哈希值——它永不改变。标签是指向摘要的人类可读指针，理解这两者之间的区别，正是区分一套可靠的部署策略与一套终将让你措手不及的部署策略的关键所在。

<!-- ZH_DEEP_DIVE -->
## 什么是 registry

registry 是一个实现 [OCI Distribution Specification](https://github.com/opencontainers/distribution-spec) 的 HTTP 服务器。该规范定义了客户端如何推送和拉取镜像层、manifest 和 tag。由于它是一个标准，任何符合 OCI 规范的工具都能与任何符合规范的 registry 配合使用。

主要选项：

- **Docker Hub** — 默认选项。`docker pull nginx` 会隐式地从 `registry-1.docker.io` 拉取。未认证的拉取会受到速率限制。
- **GHCR**（GitHub Container Registry）— 对于 GitHub 项目来说是个不错的默认选择。认证使用 GitHub 凭据和 token。公开镜像免费，私有镜像包含在 GitHub 套餐中。
- **ECR**（AWS Elastic Container Registry）— 部署到 AWS 时的自然选择。认证与 IAM 集成。
- **Artifact Registry**（GCP）— GCP 的对应产品。取代了较旧的 Google Container Registry。
- **ACR**（Azure Container Registry）— Azure 的对应产品。

对于已经在 GitHub 上的项目，GHCR 通常是正确的选择。认证使用 CI 已经拥有的同一个 `GITHUB_TOKEN`，因此无需额外的凭据管理。

## 推送到 GHCR

工作流程是：认证、用完整的 registry 路径为本地镜像打 tag、推送。

```bash
# authenticate — pipe the token to avoid it appearing in shell history
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# tag your local image with the full registry path
docker tag myapp:latest ghcr.io/<org>/<repo>:latest

# push
docker push ghcr.io/<org>/<repo>:latest

# on any other machine with credentials, pull it
docker pull ghcr.io/<org>/<repo>:latest
```

镜像名称必须与 registry 路径完全匹配。`ghcr.io/<org>/<repo>` 是标准格式——`org` 是你的 GitHub 用户名或组织，`repo` 是仓库名称。

默认情况下，GHCR 上新推送的包是私有的。你可以在 GitHub 上的包设置中更改可见性，或将包链接到仓库。

## 镜像 tag

tag 是一个**可变指针**——它是一个指向镜像 manifest 的名称，而这个名称可以随时重新指向不同的 manifest。`nginx:1.25.3` 相对稳定，因为该版本只发布过一次，但原则上任何有推送权限的人都可以重新给它打 tag。

镜像 **digest** 是不可变的。它是镜像 manifest 的 SHA256 哈希，永久标识该镜像的确切字节。如果你六个月后拉取同一个 digest，你会得到完全相同的镜像。

```bash
# see the digest of a local image
docker inspect --format='{{index .RepoDigests 0}}' nginx:1.25.3

# pull by digest — will always be the same image
docker pull nginx@sha256:a484819eb60efa9577...
```

在大多数实际场景中，git SHA tag（例如 `myapp:a1b2c3d`）能提供你所需的所有可追溯性，而无需手动管理 digest。它在语义上是不可变的——你永远不会重新给一个 git SHA 打 tag——并且它将镜像直接与其源提交关联起来。

## 为什么 `latest` 在生产环境中很危险

`latest` 并不特殊。它只是一个 tag，和任何 tag 一样是可变的。它在生产环境中导致的问题是一致的：

**重启时的静默更新。** 如果你的部署 spec 写的是 `image: myapp:latest`，而你向 registry 推送了新的 `latest`，那么下次容器重启时——无论是由于崩溃、部署还是节点重启——它都会拉取新版本。你并没有显式部署任何东西；版本在你不知情的情况下发生了变化。

**没有可追溯性。** 你无法通过查看一个 tag 为 `latest` 的运行中容器来知道它运行的是哪个版本。你无法将其关联到某个提交、某个 PR 或某个时间点。

**回滚不明确。** 要回滚，你需要知道之前的版本是什么，并重新将 `latest` 指向它。如果你一直使用 SHA tag，回滚只需在部署 spec 中更改 tag 即可。

规则很简单：在生产环境中，始终使用特定的 tag 进行部署。Git SHA tag 是最具可追溯性的选项。

## CI 中的 registry 认证

对于推送到 GHCR 的 GitHub Actions，Actions 自动提供的 `GITHUB_TOKEN` 具有足够的权限——无需手动设置 secret：

```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

工作流 job 中的 `permissions` 块必须包含 `packages: write`，token 才被允许推送：

```yaml
jobs:
  build:
    permissions:
      contents: read
      packages: write
```

对于其他 registry，模式相同——先认证，再推送。AWS ECR 需要通过 AWS CLI 生成临时 token；有相应的 Actions 可用于此。Docker Hub 使用仓库 secret 来存储用户名和访问 token。

## 在服务器上拉取

在服务器上，认证一次后，Docker 会在后续所有拉取中复用已存储的凭据：

```bash
# authenticate
echo $TOKEN | docker login ghcr.io -u <username> --password-stdin

# pull a specific version by tag
docker pull ghcr.io/<org>/<repo>:<sha>
```

凭据存储在运行 `docker login` 的用户的 `~/.docker/config.json` 中。Docker Compose 在拉取镜像时会自动读取它们。这意味着如果你以认证时所用的同一用户运行 `docker compose pull` 或 `docker compose up`，它无需任何额外配置即可工作。

一个实用提示：如果你在服务器上以 root 身份运行 Docker 操作（例如通过使用 `sudo` 的部署脚本），那么 root 的 `~/.docker/config.json` 需要保存凭据——而不是你普通用户的。在这种情况下，使用 `sudo docker login` 进行认证，或使用能让凭据在系统范围内可用的 credential helper。

<!-- ZH_RESOURCES -->
- [GitHub Container Registry 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [OCI Distribution 规范](https://github.com/opencontainers/distribution-spec)
- [docker login 参考](https://docs.docker.com/reference/cli/docker/login/)
- [镜像标签与摘要](https://docs.docker.com/reference/cli/docker/image/pull/#pull-an-image-by-digest-immutable-identifier)

<!-- ZH_UI -->
1. 将 Docker 镜像推送到 GitHub Container Registry (GHCR)
2. 在服务器上按 tag 拉取特定版本的镜像
3. 理解镜像 tag 的作用以及为什么 'latest' 很危险
4. 在 CI 流水线中配置镜像仓库认证
5. 我的镜像已存储并完成版本管理。如何让它在真实服务器上运行？
6. 我已将镜像推送到镜像仓库，但不确定服务器实际如何获取它并保持运行。是需要每次 ssh 登录执行 docker pull 吗？如果容器崩溃了会怎样？
