---
id: debugging-dockerfile-builds
title: Debugging Dockerfile Builds
zone: containers
edges:
  to:
    - id: docker-compose-dev
      question: Builds are working. How do I run my app alongside its dependencies locally?
      detail: >-
        I can build and debug images now. But I'm still starting Postgres and
        Redis separately by hand every time I work on the app — that's getting old.
difficulty: 2
tags:
  - docker
  - dockerfile
  - debugging
  - builds
category: practice
milestones:
  - Read docker build output and understand which step failed
  - Use docker build --no-cache to rule out stale cache as the cause
  - Inspect intermediate layers by running a shell at a failed build step
  - Understand what goes into the build context and why large contexts slow builds down
  - Use docker history to see what each layer in an image actually contains
  - Debug ENTRYPOINT/CMD mismatches by overriding them at run time
title_zh: "调试 Dockerfile 构建"

---


A failed or misbehaving build usually comes down to one of a few things: a RUN command that errors out, stale cache serving content that's no longer valid, a build context that's pulling in things it shouldn't, or a wrong ENTRYPOINT or CMD that makes the container exit as soon as it starts. Each of these has a specific diagnostic approach, and once you know the patterns they're quick to resolve.

The trickier case is when the build succeeds but the container doesn't behave correctly. That's usually an ENTRYPOINT or CMD problem — the image was built right but it starts the wrong thing, or signals don't propagate correctly. Getting comfortable with overriding the entrypoint at runtime is the main tool for that class of issue.

<!-- DEEP_DIVE -->

## Reading build output

Each line in `docker build` output corresponds to one instruction in the Dockerfile, executed in order. When a step fails, the error appears inline with that step's output — not at the end.

```
Step 5/9 : RUN pip install -r requirements.txt
 ---> Running in a3f91c2b88d4
Collecting flask
...
ERROR: Could not find a version that satisfies the requirement flakk==2.0 (from versions: ...)
```

The long hash after "Running in" is the ID of the intermediate container Docker created for that step. If you need to inspect the state right before the failure, that hash is useful (more on that below).

Common causes by error type:

- **"command not found"** — the base image doesn't have the tool you're trying to run; wrong base image, or you need to install it first
- **"no such file or directory" in a COPY** — the source path is wrong relative to the build context, or the file is excluded by `.dockerignore`
- **permission denied** — you're trying to write somewhere the current user can't, or a script doesn't have execute permission
- **network failure during package download** — transient; retry or pin to a specific package version

## Cache issues

Docker caches each layer. If the instruction and its inputs haven't changed since the last build, Docker reuses the cached result and skips the step. This is usually what you want, but it can produce stale results:

```bash
# bypass the cache entirely
docker build --no-cache -t myapp .
```

If a build was succeeding but producing a wrong result — an outdated package version, a missing file that was added recently — the cache is often the culprit. `--no-cache` forces a full rebuild from scratch.

Understanding **when cache invalidates** is also important for structuring Dockerfiles efficiently. Once any layer's instruction or its inputs change, Docker rebuilds that layer and every layer after it. This is why instruction order matters:

- If you change a `RUN apt-get install` near the top of a Dockerfile, everything below it rebuilds
- If you `COPY . .` early, every code change triggers a full rebuild of all subsequent layers
- The correct pattern (covered in the COPY section of writing-a-dockerfile) is to copy dependency manifests first, install dependencies, then copy source code

## Build context problems

When you run `docker build . `, the `.` is the **build context** — the directory Docker sends to the daemon before the build starts. The entire directory is uploaded, even files that are never referenced in the Dockerfile.

The first line of build output tells you how large it is:

```
Sending build context to Docker daemon  1.23GB
```

If that number is large, the build will be slow even before the first step runs. Common culprits:

- `node_modules/` — often hundreds of MB, never needed in the build context
- `.git/` — the full git history adds up
- Build artifacts, compiled binaries, or local `.env` files
- Large test fixtures or data files

Fix this with a `.dockerignore` file in the same directory as the Dockerfile:

```
.git
node_modules
*.log
.env
.env.*
dist
__pycache__
*.pyc
.DS_Store
```

`.dockerignore` uses the same syntax as `.gitignore`. Adding it to a project with a large context can cut build times dramatically — not because the build steps get faster, but because the upload step disappears.

## Inspecting intermediate layers

When a build fails partway through, Docker prints the ID of the last successfully built layer. You can start a container from that exact layer to inspect the filesystem state right before the failing step:

```bash
docker run --rm -it <layer-id> sh
```

From that shell, you can see exactly what files exist, what paths are available, what environment variables are set, and what the working directory looks like. This is the most direct way to debug a complex build failure — you're standing at the exact point in the build where things went wrong.

You can also use `docker history` to see what each layer in a finished image actually contains:

```bash
docker history myapp:latest
```

The output shows each layer, its size, and the command that created it. This is useful for understanding where image size is coming from, and for verifying that a layer-caching strategy is working the way you expect.

## ENTRYPOINT and CMD problems

The container builds successfully but exits immediately when you run it — often with exit code 0 or 1 and nothing useful in the logs. This is almost always an ENTRYPOINT or CMD problem.

First, check what the image declares:

```bash
docker inspect <image> --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'
```

Then test it interactively by overriding the entrypoint:

```bash
docker run --rm -it --entrypoint sh <image>
```

From that shell, run the intended command manually and watch what happens. If the command errors out, you'll see the error. If it exits immediately, you can check file permissions and paths.

A few specific things to check:

**Shell form vs JSON array form.** There are two ways to write CMD and ENTRYPOINT:

```dockerfile
# shell form — runs via sh -c
CMD python app.py

# JSON array form — runs the executable directly
CMD ["python", "app.py"]
```

Shell form wraps the command in `sh -c`, which means the shell process is PID 1, not your application. When Docker sends SIGTERM to stop the container, the shell may or may not forward it to the child process — often it doesn't, and the container gets forcibly killed after the timeout. **Always use JSON array form** for CMD and ENTRYPOINT in production images.

**Entrypoint scripts.** If your ENTRYPOINT is a shell script, check two things: the file must have execute permission (`chmod +x`), and it must have a correct shebang line (`#!/bin/sh` or `#!/bin/bash`). A script without a shebang may work on some systems and fail silently on others.

<!-- RESOURCES -->

- [docker build reference](https://docs.docker.com/reference/cli/docker/buildx/build/)
- [docker history reference](https://docs.docker.com/reference/cli/docker/image/history/)
- [BuildKit documentation](https://docs.docker.com/build/buildkit/)
- [.dockerignore file reference](https://docs.docker.com/reference/dockerfile/#dockerignore-file)

<!-- ZH_SUMMARY -->
构建失败或行为异常通常可归结为以下几种情况之一：RUN 命令报错、陈旧缓存提供了已失效的内容、构建上下文引入了不该引入的内容，或者 ENTRYPOINT 或 CMD 设置错误导致容器一启动就退出。每种情况都有特定的诊断方法，一旦掌握了这些模式，解决起来都很快。

更棘手的情况是构建成功但容器行为不正确。这通常是 ENTRYPOINT 或 CMD 的问题——镜像构建正确，但启动的是错误的东西，或者信号无法正确传递。熟练掌握在运行时覆盖 entrypoint 是应对这类问题的主要手段。

<!-- ZH_DEEP_DIVE -->
## 阅读构建输出

`docker build` 输出中的每一行对应 Dockerfile 中的一条指令，按顺序执行。当某一步失败时，错误会内联显示在该步骤的输出中——而不是在末尾。

```
Step 5/9 : RUN pip install -r requirements.txt
 ---> Running in a3f91c2b88d4
Collecting flask
...
ERROR: Could not find a version that satisfies the requirement flakk==2.0 (from versions: ...)
```

"Running in" 后面的长哈希是 Docker 为该步骤创建的中间容器的 ID。如果你需要检查失败前的状态，这个哈希很有用（详见下文）。

按错误类型划分的常见原因：

- **"command not found"** —— 基础镜像中没有你要运行的工具；基础镜像选错了，或者你需要先安装它
- **COPY 中的 "no such file or directory"** —— 源路径相对于构建上下文是错误的，或者文件被 `.dockerignore` 排除了
- **permission denied** —— 你试图写入当前用户无权访问的位置，或者脚本没有执行权限
- **包下载期间的网络故障** —— 暂时性的；重试或固定到特定包版本

## 缓存问题

Docker 会缓存每一层。如果自上次构建以来指令及其输入没有变化，Docker 会复用缓存结果并跳过该步骤。这通常是你想要的行为，但它可能产生过时的结果：

```bash
# bypass the cache entirely
docker build --no-cache -t myapp .
```

如果构建一直成功但产生了错误的结果——过时的包版本、最近添加的文件缺失——缓存往往是罪魁祸首。`--no-cache` 会强制从头完整重建。

理解**缓存何时失效**对于高效地组织 Dockerfile 也很重要。一旦任何一层的指令或其输入发生变化，Docker 就会重建该层及其后的每一层。这就是指令顺序很重要的原因：

- 如果你更改了 Dockerfile 顶部的 `RUN apt-get install`，它下面的所有内容都会重建
- 如果你过早地 `COPY . .`，每次代码更改都会触发所有后续层的完整重建
- 正确的模式（在 writing-a-dockerfile 的 COPY 部分有介绍）是先复制依赖清单，安装依赖，然后复制源代码

## 构建上下文问题

当你运行 `docker build .` 时，`.` 就是**构建上下文**——Docker 在构建开始前发送给守护进程的目录。整个目录都会被上传，即使是从未在 Dockerfile 中引用的文件。

构建输出的第一行会告诉你它有多大：

```
Sending build context to Docker daemon  1.23GB
```

如果这个数字很大，那么即使在第一步运行之前，构建也会很慢。常见的罪魁祸首：

- `node_modules/` —— 通常有数百 MB，构建上下文中从不需要
- `.git/` —— 完整的 git 历史会累积起来
- 构建产物、编译后的二进制文件或本地 `.env` 文件
- 大型测试夹具或数据文件

在 Dockerfile 所在目录中放置一个 `.dockerignore` 文件来解决这个问题：

```
.git
node_modules
*.log
.env
.env.*
dist
__pycache__
*.pyc
.DS_Store
```

`.dockerignore` 使用与 `.gitignore` 相同的语法。将其添加到具有大上下文的项目中可以大幅缩短构建时间——不是因为构建步骤变快了，而是因为上传步骤消失了。

## 检查中间层

当构建中途失败时，Docker 会打印最后一个成功构建的层的 ID。你可以从该层启动一个容器，以检查失败步骤之前的文件系统状态：

```bash
docker run --rm -it <layer-id> sh
```

在那个 shell 中，你可以确切地看到存在哪些文件、哪些路径可用、设置了哪些环境变量，以及工作目录是什么样子。这是调试复杂构建失败最直接的方法——你正站在构建中出问题的确切位置。

你还可以使用 `docker history` 查看已完成镜像中每一层实际包含的内容：

```bash
docker history myapp:latest
```

输出会显示每一层、其大小以及创建它的命令。这对于理解镜像大小来自哪里，以及验证层缓存策略是否按预期工作很有用。

## ENTRYPOINT 和 CMD 问题

容器构建成功，但运行时立即退出——通常退出码为 0 或 1，日志中没有任何有用信息。这几乎总是 ENTRYPOINT 或 CMD 的问题。

首先，检查镜像声明了什么：

```bash
docker inspect <image> --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'
```

然后通过覆盖 entrypoint 以交互方式测试它：

```bash
docker run --rm -it --entrypoint sh <image>
```

在那个 shell 中，手动运行预期的命令并观察会发生什么。如果命令出错，你会看到错误。如果它立即退出，你可以检查文件权限和路径。

需要检查的几个具体事项：

**Shell 形式 vs JSON 数组形式。** 有两种方式编写 CMD 和 ENTRYPOINT：

```dockerfile
# shell form — runs via sh -c
CMD python app.py

# JSON array form — runs the executable directly
CMD ["python", "app.py"]
```

Shell 形式将命令包装在 `sh -c` 中，这意味着 shell 进程是 PID 1，而不是你的应用程序。当 Docker 发送 SIGTERM 来停止容器时，shell 可能会也可能不会将其转发给子进程——通常不会，容器会在超时后被强制杀死。**在生产镜像中，始终为 CMD 和 ENTRYPOINT 使用 JSON 数组形式。**

**Entrypoint 脚本。** 如果你的 ENTRYPOINT 是一个 shell 脚本，检查两件事：文件必须具有执行权限（`chmod +x`），并且必须有正确的 shebang 行（`#!/bin/sh` 或 `#!/bin/bash`）。没有 shebang 的脚本在某些系统上可能工作，而在其他系统上静默失败。

<!-- ZH_RESOURCES -->
- [docker build 参考](https://docs.docker.com/reference/cli/docker/buildx/build/)
- [docker history 参考](https://docs.docker.com/reference/cli/docker/image/history/)
- [BuildKit 文档](https://docs.docker.com/build/buildkit/)
- [.dockerignore 文件参考](https://docs.docker.com/reference/dockerfile/#dockerignore-file)

<!-- ZH_UI -->
1. 阅读 docker build 输出，理解哪一步失败了
2. 使用 docker build --no-cache 排除过期缓存这一原因
3. 在失败的构建步骤处启动 shell，检查中间层
4. 理解构建上下文包含什么，以及为什么大上下文会拖慢构建
5. 使用 docker history 查看镜像中每一层实际包含的内容
6. 通过在运行时覆盖 ENTRYPOINT/CMD 来调试二者不匹配的问题
7. 构建已经能正常工作。如何在本地让应用与其依赖一起运行？
8. 我现在能构建和调试镜像了。但每次开发这个应用时，我仍然要手动分别启动 Postgres 和 Redis——这越来越烦人了。
