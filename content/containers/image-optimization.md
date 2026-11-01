---
id: image-optimization
title: Optimizing Docker Images
zone: containers
edges:
  to:
    - id: container-security-basics
      question: My images are lean. What should I know about making them secure?
      detail: >-
        I've got the size down and builds are fast. But I'm realizing I don't
        really know if what's running inside my containers is safe — am I
        exposing things I shouldn't be?
difficulty: 2
tags:
  - docker
  - dockerfile
  - images
  - optimization
  - multi-stage
category: practice
milestones:
  - Use multi-stage builds to separate build dependencies from the final image
  - Understand how Docker layer caching works and why instruction order matters
  - Use .dockerignore to exclude files from the build context
  - Choose minimal base images (alpine, distroless, slim variants)
  - Combine RUN commands and clean up package manager caches in a single layer
  - Measure image size with docker image ls and inspect layers with docker history
title_zh: "优化 Docker 镜像"

---


A working Dockerfile gets your app running. An optimized one gets it running fast, in a small image, with a cache that actually helps. The gap between a naive Dockerfile and a well-structured one is often 10x in image size and 5x in build time — and neither improvement is complicated once you understand the mechanics.

The two tools that matter most are multi-stage builds and layer caching. Multi-stage builds let you use a fat image full of compilers and dev tools to produce your artifact, then throw all of that away and ship only what the runtime actually needs. Layer caching lets you skip rebuilding dependencies on every code change — but only if your Dockerfile is written in the right order. These two things together turn a 1.5GB image with a two-minute rebuild into a 50MB image that rebuilds in seconds.

<!-- DEEP_DIVE -->

## Why image size matters

Image size shows up in more places than you'd expect. In CI, every build pushes an image and every deployment pulls one — the bigger the image, the longer every step takes. On a new node joining your cluster, a 1.5GB image means 1.5GB of data over the wire before the first container starts. And in terms of security, every extra package in your image is a potential CVE. A Node app that ships its full `node_modules`, build tools, and a Debian base with all its utilities has an enormous attack surface compared to one that ships only the compiled output and a handful of runtime packages.

A common example: a default Node.js app image built with `node:20` and a naive `COPY . .` will include every devDependency, TypeScript, ts-node, testing libraries, and whatever else is in your `node_modules`. Ship that to production and you're pushing half a gigabyte of code that never runs.

## Multi-stage builds

Multi-stage builds let you use multiple `FROM` instructions in a single Dockerfile. Each stage starts with a fresh filesystem. The key insight is that you can `COPY --from=<stage>` to pull specific files from an earlier stage into a later one — and only those files end up in the final image.

A Node.js example:

```dockerfile
# Stage 1: build
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: runtime
FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

The `build` stage has TypeScript, ts-node, all devDependencies. None of that makes it into `runtime` — only the compiled `dist` directory and production `node_modules` do.

For Go, this is even more dramatic since the compiled binary has no runtime dependencies at all:

```dockerfile
FROM golang:1.22 AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

FROM gcr.io/distroless/static-debian12
COPY --from=build /app/server /server
ENTRYPOINT ["/server"]
```

The final image is `gcr.io/distroless/static-debian12` — no shell, no package manager, just a minimal set of C libraries. The only thing in it is your binary.

## Layer caching and instruction order

Every instruction in a Dockerfile creates a layer. Docker caches each layer and reuses it on the next build if two things are true: the instruction itself hasn't changed, and none of the layers before it have been invalidated. Once a layer is invalidated, every layer after it rebuilds from scratch.

This makes instruction order critical. The wrong order:

```dockerfile
# Rebuilds npm ci on every code change
COPY . .
RUN npm ci
```

Every time you change a single source file, `COPY . .` invalidates its layer, and `npm ci` runs again from scratch. With a large dependency tree, that's easily a minute of wasted time per build.

The right order:

```dockerfile
# npm ci is cached unless package.json or package-lock.json changes
COPY package*.json ./
RUN npm ci
COPY . .
```

Now `npm ci` only re-runs when your actual dependencies change. Day-to-day development only rebuilds the `COPY . .` layer and anything after it.

The general rule: put instructions that change rarely near the top, instructions that change on every commit near the bottom.

For `apt-get`, combine the install and cleanup in a single `RUN` instruction — if you split them across two instructions, the cached install layer retains the package manager cache even after you try to clean it:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

## .dockerignore

When you run `docker build .`, Docker sends the entire build context — everything in the directory — to the daemon before executing a single instruction. On a large project with a `node_modules` directory, this can mean hundreds of megabytes transferred before anything happens. Even files you never `COPY` into the image are still sent.

A `.dockerignore` file works like `.gitignore` and lives in the same directory as your Dockerfile:

```
.git
node_modules
.env
*.log
dist
coverage
.DS_Store
.pytest_cache
__pycache__
```

There are two benefits: builds start faster because the context is smaller, and `COPY . .` won't unnecessarily invalidate the cache when files in ignored directories change.

## Choosing base images

The base image you choose is the foundation of everything else in the image — its size, its packages, its vulnerabilities.

**`python:3.11`** — the full official image. Debian-based, includes everything. Fine for development, unnecessarily large for production. Typical size: 900MB+.

**`python:3.11-slim`** — a minimal Debian image with Python installed. Removes most of the standard Debian packages. Good default for production. Typical size: 130MB.

**`python:3.11-alpine`** — based on Alpine Linux with musl libc instead of glibc. Very small (around 50MB) but causes compatibility issues with Python packages that have C extensions (numpy, cryptography, psycopg2). If your packages compile without issues on Alpine, it's worth it. If they don't, you'll waste hours debugging.

**`gcr.io/distroless/python3`** — no shell, no package manager, no utilities. Maximum security posture, minimum attack surface. Hard to debug because you can't get a shell inside the container.

For most production services, **`-slim` variants are the right default**. They're small enough, broadly compatible, and debuggable when something goes wrong.

Always pin to a specific version tag. `FROM python:3.11-slim` will pull different images over time as the tag is updated. `FROM python:3.11.9-slim-bookworm` is reproducible.

## Measuring image size

```bash
# List images with sizes
docker image ls

# Show each layer, the instruction that created it, and its size
docker history myapp:latest

# Show uncompressed layer sizes in a more readable format
docker history --no-trunc myapp:latest
```

`docker history` is where you find the problem layers. If you see a large `RUN` layer, it usually means you're leaving a package manager cache in that layer. Fix it by cleaning up in the same `RUN` instruction.

For a more interactive exploration, `dive` is a third-party tool that lets you navigate layers and see exactly which files are in each one:

```bash
# Install dive (macOS)
brew install dive

# Run against an image
dive myapp:latest
```

`dive` shows you the file tree diff for each layer and flags wasted space — files added in one layer and deleted in another, which still take up space in the image.

<!-- RESOURCES -->

- [Docker multi-stage builds documentation](https://docs.docker.com/build/building/multi-stage/)
- [Dockerfile best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [dive — image layer explorer](https://github.com/wagoodman/dive)
- [distroless base images](https://github.com/GoogleContainerTools/distroless)

<!-- ZH_SUMMARY -->
一个能用的 Dockerfile 能让你的应用跑起来。一个经过优化的 Dockerfile 能让它跑得快、镜像小，并且缓存真正发挥作用。一个朴素的 Dockerfile 和一个结构良好的 Dockerfile 之间的差距，往往在镜像大小上是 10 倍，在构建时间上是 5 倍——而一旦你理解了其中的机制，这两项改进都不复杂。

最重要的两个工具是多阶段构建和层缓存。多阶段构建让你可以用一个塞满编译器和开发工具的臃肿镜像来产出构建产物，然后把这些统统丢掉，只交付运行时真正需要的东西。层缓存让你在每次代码变更时跳过重新构建依赖——但前提是你的 Dockerfile 以正确的顺序编写。这两者结合起来，能把一个 1.5GB、重新构建需要两分钟的镜像，变成一个 50MB、几秒钟就能重新构建的镜像。

<!-- ZH_DEEP_DIVE -->
## 为什么镜像大小很重要

镜像大小出现的地方比你想象的要多。在 CI 中，每次构建都会推送一个镜像，每次部署都会拉取一个镜像——镜像越大，每一步耗时越长。在加入集群的新节点上，一个 1.5GB 的镜像意味着在第一个容器启动之前，需要通过网络传输 1.5GB 的数据。从安全角度来看，镜像中每一个额外的软件包都是一个潜在的 CVE。一个 Node 应用如果打包了完整的 `node_modules`、构建工具，以及带有全部工具的 Debian 基础镜像，其攻击面远大于只打包编译产物和少量运行时软件包的镜像。

一个常见的例子：用 `node:20` 和简单的 `COPY . .` 构建的默认 Node.js 应用镜像，会包含所有 devDependency、TypeScript、ts-node、测试库，以及 `node_modules` 中的其他所有内容。把它推送到生产环境，你推送的是半千兆字节永远不会运行的代码。

## 多阶段构建

多阶段构建允许你在单个 Dockerfile 中使用多个 `FROM` 指令。每个阶段都从全新的文件系统开始。关键点在于，你可以使用 `COPY --from=<stage>` 将特定文件从较早的阶段拉取到较晚的阶段——只有这些文件会进入最终镜像。

一个 Node.js 示例：

```dockerfile
# Stage 1: build
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: runtime
FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

`build` 阶段包含 TypeScript、ts-node、所有 devDependency。这些都不会进入 `runtime`——只有编译后的 `dist` 目录和生产环境的 `node_modules` 会进入。

对于 Go，这一点更加显著，因为编译后的二进制文件完全没有运行时依赖：

```dockerfile
FROM golang:1.22 AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

FROM gcr.io/distroless/static-debian12
COPY --from=build /app/server /server
ENTRYPOINT ["/server"]
```

最终镜像是 `gcr.io/distroless/static-debian12`——没有 shell，没有包管理器，只有一组最小的 C 库。其中唯一的内容就是你的二进制文件。

## 层缓存与指令顺序

Dockerfile 中的每条指令都会创建一个层。Docker 会缓存每个层，并在下一次构建时复用，前提是两个条件都成立：指令本身没有改变，并且它之前的所有层都没有失效。一旦某个层失效，它之后的所有层都会从头重新构建。

这使得指令顺序至关重要。错误的顺序：

```dockerfile
# Rebuilds npm ci on every code change
COPY . .
RUN npm ci
```

每次你修改一个源文件，`COPY . .` 都会使其层失效，`npm ci` 就会从头重新运行。对于大型依赖树，每次构建很容易浪费一分钟。

正确的顺序：

```dockerfile
# npm ci is cached unless package.json or package-lock.json changes
COPY package*.json ./
RUN npm ci
COPY . .
```

现在 `npm ci` 只有在实际依赖发生变化时才会重新运行。日常开发只会重新构建 `COPY . .` 层及其之后的任何内容。

通用规则：将很少变化的指令放在靠近顶部的位置，将每次提交都会变化的指令放在靠近底部的位置。

对于 `apt-get`，将安装和清理合并到单个 `RUN` 指令中——如果你将它们拆分成两条指令，缓存的安装层会保留包管理器缓存，即使你尝试清理它：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

## .dockerignore

当你运行 `docker build .` 时，Docker 会在执行任何一条指令之前，将整个构建上下文——目录中的所有内容——发送给守护进程。在一个包含 `node_modules` 目录的大型项目中，这意味着在任何事情发生之前就要传输数百兆字节。即使是你从未 `COPY` 到镜像中的文件也会被发送。

`.dockerignore` 文件的工作方式类似于 `.gitignore`，位于与 Dockerfile 相同的目录中：

```
.git
node_modules
.env
*.log
dist
coverage
.DS_Store
.pytest_cache
__pycache__
```

有两个好处：构建启动更快，因为上下文更小；并且当被忽略目录中的文件发生变化时，`COPY . .` 不会不必要地使缓存失效。

## 选择基础镜像

你选择的基础镜像是镜像中其他一切的基础——它的大小、它的软件包、它的漏洞。

**`python:3.11`**——完整的官方镜像。基于 Debian，包含所有内容。适合开发，对于生产来说不必要地大。典型大小：900MB+。

**`python:3.11-slim`**——安装了 Python 的最小 Debian 镜像。移除了大部分标准 Debian 软件包。适合作为生产的良好默认选择。典型大小：130MB。

**`python:3.11-alpine`**——基于 Alpine Linux，使用 musl libc 而不是 glibc。非常小（约 50MB），但会导致带有 C 扩展的 Python 包（numpy、cryptography、psycopg2）出现兼容性问题。如果你的包在 Alpine 上编译没有问题，那它值得使用。如果不行，你会浪费数小时调试。

**`gcr.io/distroless/python3`**——没有 shell，没有包管理器，没有实用工具。最高安全态势，最小攻击面。难以调试，因为你无法在容器内获得 shell。

对于大多数生产服务，**`-slim` 变体是正确的默认选择**。它们足够小，广泛兼容，并且在出问题时可以调试。

始终固定到特定版本标签。`FROM python:3.11-slim` 会随着标签更新而拉取不同的镜像。`FROM python:3.11.9-slim-bookworm` 是可复现的。

## 测量镜像大小

```bash
# List images with sizes
docker image ls

# Show each layer, the instruction that created it, and its size
docker history myapp:latest

# Show uncompressed layer sizes in a more readable format
docker history --no-trunc myapp:latest
```

`docker history` 是你找到问题层的地方。如果你看到一个很大的 `RUN` 层，通常意味着你在该层中留下了包管理器缓存。通过在同一个 `RUN` 指令中清理来修复它。

对于更交互式的探索，`dive` 是一个第三方工具，可以让你浏览层并准确查看每一层中的文件：

```bash
# Install dive (macOS)
brew install dive

# Run against an image
dive myapp:latest
```

`dive` 会显示每一层的文件树差异，并标记浪费的空间——在一个层中添加并在另一个层中删除的文件，这些文件仍然占用镜像中的空间。

<!-- ZH_RESOURCES -->
- [Docker 多阶段构建文档](https://docs.docker.com/build/building/multi-stage/)
- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [dive — 镜像层浏览器](https://github.com/wagoodman/dive)
- [distroless 基础镜像](https://github.com/GoogleContainerTools/distroless)

<!-- ZH_UI -->
1. 使用多阶段构建将构建依赖与最终镜像分离
2. 理解 Docker 层缓存的工作原理以及指令顺序为何重要
3. 使用 .dockerignore 将文件排除在构建上下文之外
4. 选择最小化基础镜像（alpine、distroless、slim 变体）
5. 合并 RUN 命令并在单层中清理包管理器缓存
6. 使用 docker image ls 测量镜像大小，用 docker history 检查各层
7. 我的镜像很精简。关于如何让它们更安全，我应该了解什么？
8. 我已经缩小了体积，构建也很快。但我意识到我并不真正了解容器内运行的东西是否安全——我是否暴露了不该暴露的东西？
