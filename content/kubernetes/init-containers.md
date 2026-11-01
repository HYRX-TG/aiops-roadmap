---
id: init-containers
title: Init Containers
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - init-containers
  - pods
  - k8s
  - startup
category: concept
milestones:
  - >-
    Understand what init containers are: containers that run to completion
    before any main container in the Pod starts
  - >-
    Know that multiple init containers run sequentially — each must succeed
    before the next starts; if one fails, Kubernetes restarts it
  - Write an init container that waits for a dependency to become available
  - >-
    Know what init containers can do that main containers can't: run as a
    different image, have different permissions, access secrets the app
    container doesn't need
  - >-
    Understand when NOT to use init containers for dependency waiting — health
    checks and readiness probes are usually the better answer
title_zh: "初始化容器"

---


Init containers are containers that run inside a Pod before the main application container starts. They run sequentially, each must exit with success before the next begins, and the Pod's main containers don't start until all init containers have completed.

<!-- DEEP_DIVE -->

## Why init containers exist

Sometimes a container needs something to be true before it can start usefully:

- A config file fetched from a remote source
- Directory permissions set correctly
- A database migration applied
- A dependency service that needs to be reachable

You could put all of this logic inside your application container, but that mixes setup concerns with application code, requires your app image to contain tools it shouldn't need at runtime, and makes the startup logic harder to test independently.

Init containers let you separate that pre-start work into dedicated containers with their own images and permissions.

## Writing an init container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.35
      command:
        - sh
        - -c
        - |
          until nc -z postgres-service 5432; do
            echo "waiting for postgres..."
            sleep 2
          done
    - name: run-migrations
      image: my-app:1.2.3
      command: ["./migrate", "--up"]
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
  containers:
    - name: app
      image: my-app:1.2.3
      ports:
        - containerPort: 8080
```

The two init containers run in order: `wait-for-db` runs until it exits 0, then `run-migrations` runs until it exits 0, then the main `app` container starts.

## Key differences from regular containers

**Init containers run to completion.** They're not long-running processes — they do their job and exit. A non-zero exit code is treated as failure, and Kubernetes will restart the init container according to the Pod's `restartPolicy`.

**They run sequentially.** Unlike main containers (which all start in parallel), init containers run one after another. Order matters and is guaranteed.

**They can use a different image.** The `wait-for-db` container above uses `busybox` — a tiny image with basic Unix tools — while the main app uses `my-app`. You don't need to bundle `nc` or `curl` into your production image just for startup checks.

**They can have different permissions.** An init container can run as root to set up file permissions, while the main container runs as a non-root user.

**They can access secrets the main container doesn't need.** A init container that fetches a bootstrap token from Vault doesn't need to share that secret with the running application.

## The dependency-waiting pattern

Waiting for a service to be ready is the most common init container use case:

```yaml
initContainers:
  - name: wait-for-redis
    image: busybox:1.35
    command:
      - sh
      - -c
      - until nc -z redis-service 6379; do sleep 1; done
```

This loops until `redis-service:6379` accepts a TCP connection. The main container won't start until Redis is reachable.

## When init containers aren't the right answer

If your app crashes because a dependency isn't ready, the instinct is to add a wait loop in an init container. But Kubernetes already has a mechanism for this: readiness probes and the Pod restart policy.

If your app fails to start, Kubernetes will restart it with exponential backoff (CrashLoopBackOff). For many services, building retry logic into the app itself — or just letting Kubernetes restart it — is simpler than adding an init container. The restart backoff eventually gives dependencies time to come up.

Use init containers when:
- You need to run a different image (tool that isn't in your app image)
- You need elevated permissions briefly that you don't want in the running app
- The setup step is a one-time task with a clear success/failure (migrations, cert fetching)

Prefer readiness probes and app-level retries when:
- You're just waiting for a service to be ready
- The dependency might go away temporarily during the app's lifetime (in which case you need runtime retry logic anyway)

<!-- RESOURCES -->

- [Kubernetes Docs - Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) -- type: docs, time: 15m
- [Kubernetes Docs - Configure Pod Initialization](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-initialization/) -- type: tutorial, time: 15m

<!-- ZH_SUMMARY -->
Init 容器是在 Pod 内、主应用容器启动之前运行的容器。它们按顺序依次运行，每个都必须成功退出后下一个才会开始，并且只有当所有 init 容器都完成后，Pod 的主容器才会启动。

<!-- ZH_DEEP_DIVE -->
## 为什么需要 init 容器

有时容器需要先满足某些条件才能正常启动并发挥作用：

- 从远程源获取的配置文件
- 正确设置目录权限
- 应用数据库迁移
- 需要可访问的依赖服务

你可以把所有这些逻辑都放进应用容器里，但这样会把初始化关注点与应用程序代码混在一起，要求应用镜像包含运行时本不需要的工具，并且使启动逻辑难以独立测试。

Init 容器让你可以把这些启动前的工作分离到专用容器中，这些容器拥有自己的镜像和权限。

## 编写 init 容器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.35
      command:
        - sh
        - -c
        - |
          until nc -z postgres-service 5432; do
            echo "waiting for postgres..."
            sleep 2
          done
    - name: run-migrations
      image: my-app:1.2.3
      command: ["./migrate", "--up"]
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
  containers:
    - name: app
      image: my-app:1.2.3
      ports:
        - containerPort: 8080
```

这两个 init 容器按顺序运行：`wait-for-db` 运行直到以 0 退出，然后 `run-migrations` 运行直到以 0 退出，之后主 `app` 容器才会启动。

## 与常规容器的关键区别

**Init 容器运行至完成。** 它们不是长期运行的进程——它们完成自己的任务后就会退出。非零退出码会被视为失败，Kubernetes 会根据 Pod 的 `restartPolicy` 重启该 init 容器。

**它们按顺序运行。** 与主容器（全部并行启动）不同，init 容器一个接一个地运行。顺序很重要，并且是有保证的。

**它们可以使用不同的镜像。** 上面的 `wait-for-db` 容器使用 `busybox`——一个包含基本 Unix 工具的极小镜像——而主应用使用 `my-app`。你不需要仅仅为了启动检查就把 `nc` 或 `curl` 打包进生产镜像。

**它们可以拥有不同的权限。** Init 容器可以以 root 身份运行来设置文件权限，而主容器以非 root 用户运行。

**它们可以访问主容器不需要的 Secret。** 一个从 Vault 获取引导令牌的 init 容器，不需要把该 Secret 共享给正在运行的应用程序。

## 依赖等待模式

等待服务就绪是最常见的 init 容器用例：

```yaml
initContainers:
  - name: wait-for-redis
    image: busybox:1.35
    command:
      - sh
      - -c
      - until nc -z redis-service 6379; do sleep 1; done
```

这会循环直到 `redis-service:6379` 接受 TCP 连接。在 Redis 可达之前，主容器不会启动。

## 何时 init 容器不是正确答案

如果你的应用因为依赖未就绪而崩溃，本能反应是在 init 容器中添加等待循环。但 Kubernetes 已经有对应的机制：就绪探针和 Pod 重启策略。

如果你的应用启动失败，Kubernetes 会以指数退避方式重启它（CrashLoopBackOff）。对许多服务来说，在应用自身内置重试逻辑——或者直接让 Kubernetes 重启它——比添加 init 容器更简单。重启退避最终会给依赖留出启动时间。

在以下情况下使用 init 容器：
- 你需要运行不同的镜像（应用镜像中没有的工具）
- 你需要短暂使用提升的权限，而不希望运行中的应用拥有这些权限
- 初始化步骤是一次性任务，且有明确的成功/失败结果（迁移、证书获取）

在以下情况下优先使用就绪探针和应用级重试：
- 你只是在等待服务就绪
- 依赖可能在应用生命周期内暂时不可用（这种情况下你无论如何都需要运行时重试逻辑）

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Init 容器](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) -- 类型：文档，时长：15分钟
- [Kubernetes 文档 - 配置 Pod 初始化](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-initialization/) -- 类型：教程，时长：15分钟

<!-- ZH_UI -->
1. 理解什么是 init 容器：在主容器启动之前运行至完成的容器
2. 了解多个 init 容器按顺序运行——每个都必须成功才能启动下一个；如果其中一个失败，Kubernetes 会重启它
3. 编写一个等待依赖项可用的 init 容器
4. 了解 init 容器能做而主容器不能做的事：使用不同的镜像运行、拥有不同的权限、访问应用容器不需要的 Secret
5. 理解何时不应使用 init 容器等待依赖项——健康检查和就绪探针通常是更好的选择
