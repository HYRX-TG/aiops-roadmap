---
id: building-images-in-ci
title: Building Docker Images in CI
zone: containers
edges:
  to:
    - id: container-registry
      question: I built an image in CI. Where does it go?
      detail: >-
        The build finishes and the image just disappears when the CI runner
        shuts down. I need somewhere to actually store it so my server can pull
        it later — but I'm not sure what that looks like.
difficulty: 2
tags:
  - docker
  - ci-cd
  - dockerfile
  - images
  - github-actions
  - containers
category: practice
milestones:
  - Build a Docker image in a GitHub Actions workflow
  - Tag the image with the git commit SHA
  - Use multi-stage builds to keep production images small
  - Cache Docker layers in CI to speed up builds
title_zh: "在 CI 中构建 Docker 镜像"

---


Building images manually on a laptop doesn't scale — the image depends on your local state, there's no audit trail, and you have to remember to rebuild before deploying. Building in CI means every image comes from a clean checkout of a known commit, is stored in a registry, and can be reproduced. The image tag becomes the deployment artifact.

The commit SHA is the link that makes the whole chain traceable: you can look at a running container, read its tag, and find the exact commit, the diff, the PR, and the engineer who merged it. That's the operational value of CI-built images beyond just "automation."

<!-- DEEP_DIVE -->

## Why build in CI

A locally-built image carries invisible risk. It includes whatever is in your working directory — uncommitted changes, local config files, a `node_modules` that differs from what `npm ci` would produce on a clean machine. You also have to remember to build before you deploy, and if you forget or build from the wrong branch, you've deployed something you can't reproduce.

CI builds solve this by construction: the runner starts from a clean git checkout, builds deterministically, tags the image with the commit SHA, and pushes to a registry. The SHA tag is immutable — it maps to exactly one commit. Anyone can look at a running container's image tag and trace it back to source.

## A basic GitHub Actions workflow

This workflow builds and pushes to GitHub Container Registry (GHCR) on every push to `main`. `GITHUB_TOKEN` is provided automatically — no manual secrets needed for GHCR.

```yaml
name: Build and push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

`github.sha` is the full 40-character commit SHA. It's immutable — it will never point to a different image once pushed. `github.repository` expands to `org/repo`, which is the correct path format for GHCR.

The `permissions` block is required. Without `packages: write`, the token won't have permission to push to GHCR even though it's the same GitHub token.

## Tagging strategy

Tags serve different audiences and purposes. A typical setup uses two tags per build:

**SHA tags** (`ghcr.io/myorg/myapp:a1b2c3d`) are immutable and traceable. Use these for deployments — they pin you to an exact version. If something goes wrong, you can roll back by pinning to a previous SHA.

**Branch tags** (`ghcr.io/myorg/myapp:main`) are mutable pointers to the latest build from that branch. Useful for development environments that should always run the latest version, but **never use these for production** — you lose traceability and safe rollback.

**Semantic version tags** (`ghcr.io/myorg/myapp:1.4.2`) make sense for libraries or images that external teams depend on. They provide a stable, human-readable contract.

**`latest`** should be avoided in production. It's mutable, gives no information about what version is actually running, and makes rollback ambiguous.

To push both SHA and branch tags in one build step:

```yaml
tags: |
  ghcr.io/${{ github.repository }}:${{ github.sha }}
  ghcr.io/${{ github.repository }}:main
```

## Layer caching in CI

CI runners are ephemeral — every run starts from a blank slate with no cached Docker layers. Without caching, every build reinstalls all dependencies from scratch, which can add several minutes to a build that would be fast locally.

The fix is registry-based layer caching: store the layer cache in the registry itself, pull it at the start of each build, and only rebuild layers that have changed.

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache
    cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache,mode=max
```

`mode=max` caches all layers, including intermediate ones from multi-stage builds. The `buildcache` tag is a separate image in your registry that holds only layer data — it won't be confused with your application images.

With a well-structured Dockerfile (dependencies installed before application code is copied), a code-only change will hit the cache for the dependency install layer and only rebuild from the `COPY . .` line onward.

## Build secrets in CI

If your build needs credentials — a private npm registry token, a PyPI token, an SSH key for a private git dependency — don't pass them as build args. Build args are baked into the image and visible in `docker history`. Anyone with access to the image can read them.

BuildKit's secret mounting is the correct approach: the secret is available as a file during a specific build step and is **never written to any image layer**.

In the workflow, pass the secret using the `secrets` input:

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: |
      NPM_TOKEN=${{ secrets.NPM_TOKEN }}
```

In the Dockerfile, mount the secret at the step that needs it:

```dockerfile
RUN --mount=type=secret,id=NPM_TOKEN \
    NPM_TOKEN=$(cat /run/secrets/NPM_TOKEN) npm install
```

The secret is exposed as a file at `/run/secrets/<id>` for the duration of that `RUN` instruction only. It is not present in the final image, not visible in the layer history, and not accessible to subsequent build steps unless explicitly mounted again.

<!-- RESOURCES -->

- [docker/build-push-action documentation](https://github.com/docker/build-push-action)
- [GitHub Container Registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker BuildKit secrets documentation](https://docs.docker.com/build/building/secrets/)
- [GitHub Actions: automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

<!-- ZH_SUMMARY -->
在笔记本电脑上手动构建镜像无法规模化——镜像依赖于你的本地状态，没有审计追踪，而且你必须记得在部署前重新构建。在 CI 中构建意味着每个镜像都来自已知提交的干净检出，存储在镜像仓库中，并且可以复现。镜像 tag 成为部署产物。

commit SHA 是使整条链路可追溯的纽带：你可以查看正在运行的容器，读取它的 tag，并找到确切的提交、diff、PR，以及合并它的工程师。这就是 CI 构建镜像超越单纯“自动化”的运维价值。

<!-- ZH_DEEP_DIVE -->
## 为什么要在 CI 中构建

本地构建的镜像带有不可见的风险。它包含你工作目录中的任何内容——未提交的更改、本地配置文件、与在干净机器上运行 `npm ci` 所生成的不同的 `node_modules`。你还必须记得在部署前进行构建，如果忘记或从错误的分支构建，你部署的东西将无法复现。

CI 构建从机制上解决了这个问题：runner 从干净的 git checkout 开始，确定性地构建，用 commit SHA 为镜像打标签，并推送到 registry。SHA 标签是不可变的——它精确映射到一个 commit。任何人都可以查看运行中容器的镜像标签，并追溯回源代码。

## 一个基础的 GitHub Actions workflow

这个 workflow 在每次推送到 `main` 时构建并推送到 GitHub Container Registry (GHCR)。`GITHUB_TOKEN` 是自动提供的——GHCR 不需要手动配置 secrets。

```yaml
name: Build and push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

`github.sha` 是完整的 40 字符 commit SHA。它是不可变的——一旦推送，它永远不会指向不同的镜像。`github.repository` 展开为 `org/repo`，这是 GHCR 的正确路径格式。

`permissions` 块是必需的。没有 `packages: write`，即使使用的是同一个 GitHub token，该 token 也没有权限推送到 GHCR。

## 标签策略

标签服务于不同的受众和目的。一个典型的设置会为每次构建使用两个标签：

**SHA 标签**（`ghcr.io/myorg/myapp:a1b2c3d`）是不可变且可追溯的。将它们用于部署——它们将你固定到确切的版本。如果出现问题，你可以通过固定到之前的 SHA 来回滚。

**分支标签**（`ghcr.io/myorg/myapp:main`）是指向该分支最新构建的可变指针。对于应始终运行最新版本的开发环境很有用，但**绝不要在生产环境中使用这些标签**——你会失去可追溯性和安全回滚能力。

**语义化版本标签**（`ghcr.io/myorg/myapp:1.4.2`）对于外部团队依赖的库或镜像是有意义的。它们提供了一个稳定、人类可读的契约。

**`latest`** 在生产环境中应避免使用。它是可变的，不提供关于实际运行版本的任何信息，并使回滚变得模糊。

要在一次构建步骤中同时推送 SHA 和分支标签：

```yaml
tags: |
  ghcr.io/${{ github.repository }}:${{ github.sha }}
  ghcr.io/${{ github.repository }}:main
```

## CI 中的层缓存

CI runner 是临时的——每次运行都从空白状态开始，没有缓存的 Docker 层。没有缓存，每次构建都会从头重新安装所有依赖，这可能会给一个在本地本来很快的构建增加几分钟时间。

解决方案是基于 registry 的层缓存：将层缓存存储在 registry 本身中，在每次构建开始时拉取它，并且只重建已更改的层。

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache
    cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache,mode=max
```

`mode=max` 缓存所有层，包括多阶段构建中的中间层。`buildcache` 标签是你 registry 中的一个单独镜像，只保存层数据——它不会与你的应用镜像混淆。

使用结构良好的 Dockerfile（在复制应用代码之前安装依赖），仅代码更改会命中依赖安装层的缓存，并且只从 `COPY . .` 行开始重建。

## CI 中的构建 secrets

如果你的构建需要凭据——私有 npm registry token、PyPI token、用于私有 git 依赖的 SSH 密钥——不要将它们作为 build args 传递。Build args 会被烘焙到镜像中，并在 `docker history` 中可见。任何有权访问该镜像的人都可以读取它们。

BuildKit 的 secret 挂载是正确的方法：secret 在特定构建步骤期间作为文件可用，并且**永远不会写入任何镜像层**。

在 workflow 中，使用 `secrets` 输入传递 secret：

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: |
      NPM_TOKEN=${{ secrets.NPM_TOKEN }}
```

在 Dockerfile 中，在需要它的步骤挂载 secret：

```dockerfile
RUN --mount=type=secret,id=NPM_TOKEN \
    NPM_TOKEN=$(cat /run/secrets/NPM_TOKEN) npm install
```

secret 仅在该 `RUN` 指令执行期间作为文件暴露在 `/run/secrets/<id>`。它不存在于最终镜像中，在层历史中不可见，并且除非再次显式挂载，否则后续构建步骤无法访问它。

<!-- ZH_RESOURCES -->
- [docker/build-push-action 文档](https://github.com/docker/build-push-action)
- [GitHub Container Registry 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker BuildKit secrets 文档](https://docs.docker.com/build/building/secrets/)
- [GitHub Actions：自动令牌认证](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

<!-- ZH_UI -->
1. 在 GitHub Actions 工作流中构建 Docker 镜像
2. 用 git commit SHA 给镜像打标签
3. 使用多阶段构建保持生产镜像精简
4. 在 CI 中缓存 Docker 层以加速构建
5. 我在 CI 中构建了镜像。它会被送到哪里？
6. 构建完成后，CI runner 关闭时镜像就消失了。我需要一个地方真正存储它，以便我的服务器之后能拉取——但我不确定这该是什么样子。
