---
id: debugging-pods
title: Debugging Pods
zone: kubernetes
edges:
  to: []
difficulty: 1
tags:
  - kubernetes
  - debugging
  - pods
  - crashloopbackoff
  - kubectl
  - logs
  - k8s
category: practice
milestones:
  - Use kubectl logs to see what a container printed before it crashed
  - >-
    Use kubectl describe pod to read the Events section — this is where
    Kubernetes explains what it tried and what went wrong
  - Use kubectl exec to get a shell inside a running container
  - >-
    Recognize the common failure states: CrashLoopBackOff, Pending,
    ImagePullBackOff, OOMKilled — and know what each one means
  - >-
    Use kubectl get events to see a timeline of what happened to a pod
title_zh: "调试 Pod"

---


When a pod isn't behaving, Kubernetes gives you several tools to understand why. The hard part for new users is knowing which tool to reach for first and how to read what it tells you.

<!-- DEEP_DIVE -->

## Start with kubectl logs

The first thing to check when a pod is crashing is what the container printed before it died:

```bash
kubectl logs my-pod
```

If the container has already exited, add `--previous` to see the logs from the last run:

```bash
kubectl logs my-pod --previous
```

If your pod has multiple containers (or init containers), specify which one:

```bash
kubectl logs my-pod -c my-container
kubectl logs my-pod -c my-init-container
```

Logs tell you what your application reported. If it crashed with a stack trace, a missing environment variable, a connection refused error — it's in here.

## kubectl describe pod — the Events section

When logs aren't enough (or the container never started at all), `kubectl describe pod` is your next stop:

```bash
kubectl describe pod my-pod
```

The most useful part is at the bottom — the **Events** section. It shows what Kubernetes itself has been doing:

```
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  2m                default-scheduler  Successfully assigned default/my-pod to node-1
  Normal   Pulling    2m                kubelet            Pulling image "my-app:latest"
  Warning  Failed     2m                kubelet            Failed to pull image: rpc error: ...
  Warning  BackOff    90s (x3 over 2m)  kubelet            Back-off pulling image
```

Events tell you about scheduling, image pulls, volume mounts, probe failures — things that happen at the Kubernetes level before your app even starts.

## kubectl exec — get inside a running container

If the pod is running but behaving unexpectedly, you can open a shell inside it:

```bash
kubectl exec -it my-pod -- /bin/sh
```

Use `/bin/bash` if the image has it. From inside, you can check environment variables, test network connections, look at filesystem paths, or manually run commands your app would run.

```bash
# Check env vars are what you expect
env | grep DATABASE

# Test if a dependency is reachable
curl http://postgres-service:5432

# Inspect the filesystem
ls -la /app/config/
```

## Common failure states and what they mean

**CrashLoopBackOff** — the container starts, crashes, and Kubernetes keeps restarting it with increasing delays. The container is running long enough to exit with a non-zero code. Check `kubectl logs --previous` to see what it printed before exiting.

**Pending** — the pod hasn't been scheduled to a node yet. This means the scheduler can't find a suitable node. Common causes:
- Not enough CPU or memory available on any node
- A node selector or affinity rule that no node satisfies
- A PVC that hasn't bound yet (the pod waits for its volumes)

Check `kubectl describe pod` — the Events section will say why it can't schedule.

**ImagePullBackOff** — Kubernetes can't pull the container image. Either the image name is wrong, the tag doesn't exist, or the registry requires credentials that aren't configured. The Events section will show the exact error message from the registry.

**OOMKilled** — the container exceeded its memory limit and was killed by the kernel. The exit code is 137. Either the memory limit is too low, or the application has a memory leak. Increase the limit or investigate the leak.

**Error** (exit code non-zero) — the container started and exited with a failure. Check logs.

## kubectl get events

For a broader picture of what's happening across the namespace:

```bash
kubectl get events --sort-by='.lastTimestamp'
```

To filter events for a specific pod:

```bash
kubectl get events --field-selector involvedObject.name=my-pod
```

Events are namespace-scoped and expire after an hour by default, so check them while things are still fresh.

## A systematic approach

When a pod isn't working:

1. `kubectl get pods` — what state is it in?
2. `kubectl describe pod my-pod` — read the Events section
3. `kubectl logs my-pod --previous` — what did the container print?
4. `kubectl exec -it my-pod -- /bin/sh` — if it's running, get inside
5. `kubectl get events --field-selector involvedObject.name=my-pod` — broader timeline

Most pod problems are one of: wrong image, missing environment variable, missing secret, failing readiness probe, or not enough resources. The tools above will surface whichever one it is.

<!-- RESOURCES -->

- [Kubernetes Docs - Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/) -- type: docs, time: 20m
- [Kubernetes Docs - Determine the Reason for Pod Failure](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
当 Pod 表现异常时，Kubernetes 提供了多种工具来帮助你理解原因。对新手来说，难点在于知道该先使用哪个工具，以及如何解读它给出的信息。

<!-- ZH_DEEP_DIVE -->
## 从 kubectl logs 开始

当 pod 崩溃时，首先要检查的是容器在退出前打印了什么：

```bash
kubectl logs my-pod
```

如果容器已经退出，加上 `--previous` 查看上一次运行的日志：

```bash
kubectl logs my-pod --previous
```

如果你的 pod 有多个容器（或 init 容器），指定要查看哪一个：

```bash
kubectl logs my-pod -c my-container
kubectl logs my-pod -c my-init-container
```

日志会告诉你应用报告了什么。如果它崩溃时带有堆栈跟踪、缺少环境变量、连接被拒绝错误——都在这里。

## kubectl describe pod —— Events 部分

当日志不够用时（或者容器根本没有启动），`kubectl describe pod` 是你的下一站：

```bash
kubectl describe pod my-pod
```

最有用的部分在底部——**Events** 部分。它展示了 Kubernetes 本身一直在做什么：

```
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  2m                default-scheduler  Successfully assigned default/my-pod to node-1
  Normal   Pulling    2m                kubelet            Pulling image "my-app:latest"
  Warning  Failed     2m                kubelet            Failed to pull image: rpc error: ...
  Warning  BackOff    90s (x3 over 2m)  kubelet            Back-off pulling image
```

Events 会告诉你关于调度、镜像拉取、卷挂载、探针失败的信息——这些都是在你的应用启动之前发生在 Kubernetes 层面的事情。

## kubectl exec —— 进入运行中的容器

如果 pod 正在运行但行为异常，你可以在其中打开一个 shell：

```bash
kubectl exec -it my-pod -- /bin/sh
```

如果镜像中有 `/bin/bash`，就用它。进入容器后，你可以检查环境变量、测试网络连接、查看文件系统路径，或手动运行你的应用会运行的命令。

```bash
# Check env vars are what you expect
env | grep DATABASE

# Test if a dependency is reachable
curl http://postgres-service:5432

# Inspect the filesystem
ls -la /app/config/
```

## 常见故障状态及其含义

**CrashLoopBackOff** —— 容器启动、崩溃，Kubernetes 以递增的延迟不断重启它。容器运行的时间足够长，以非零代码退出。检查 `kubectl logs --previous` 查看它在退出前打印了什么。

**Pending** —— pod 尚未被调度到节点。这意味着调度器找不到合适的节点。常见原因：
- 任何节点上都没有足够的 CPU 或内存可用
- 节点选择器或亲和性规则没有任何节点能满足
- PVC 尚未绑定（pod 在等待其卷）

检查 `kubectl describe pod` —— Events 部分会说明为什么无法调度。

**ImagePullBackOff** —— Kubernetes 无法拉取容器镜像。要么镜像名称错误，要么 tag 不存在，要么仓库需要未配置的凭据。Events 部分会显示来自仓库的确切错误消息。

**OOMKilled** —— 容器超出了其内存限制，被内核杀死。退出代码是 137。要么内存限制太低，要么应用存在内存泄漏。增加限制或调查泄漏。

**Error**（退出代码非零）—— 容器启动后以失败退出。检查日志。

## kubectl get events

要了解整个命名空间中正在发生的事情的更全面情况：

```bash
kubectl get events --sort-by='.lastTimestamp'
```

要过滤特定 pod 的事件：

```bash
kubectl get events --field-selector involvedObject.name=my-pod
```

Events 是命名空间范围的，默认一小时后过期，所以在事情还新鲜时检查它们。

## 系统化的方法

当 pod 不工作时：

1. `kubectl get pods` —— 它处于什么状态？
2. `kubectl describe pod my-pod` —— 阅读 Events 部分
3. `kubectl logs my-pod --previous` —— 容器打印了什么？
4. `kubectl exec -it my-pod -- /bin/sh` —— 如果它在运行，进入其中
5. `kubectl get events --field-selector involvedObject.name=my-pod` —— 更广泛的时间线

大多数 pod 问题都是以下之一：镜像错误、缺少环境变量、缺少 secret、就绪探针失败，或资源不足。上述工具会揭示到底是哪一个。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 调试运行中的 Pod](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/) -- 类型：文档，时间：20分钟
- [Kubernetes 文档 - 确定 Pod 失败的原因](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/) -- 类型：文档，时间：10分钟

<!-- ZH_UI -->
1. 使用 kubectl logs 查看容器崩溃前打印的内容
2. 使用 kubectl describe pod 查看 Events 部分——Kubernetes 会在这里说明它尝试了什么、出了什么问题
3. 使用 kubectl exec 进入运行中的容器获取 shell
4. 识别常见故障状态：CrashLoopBackOff、Pending、ImagePullBackOff、OOMKilled——并了解每种状态的含义
5. 使用 kubectl get events 查看 Pod 发生了什么的时间线
