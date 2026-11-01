---
id: debugging-deployments
title: Debugging Deployments
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - debugging
  - deployments
  - rollout
  - kubectl
  - k8s
category: practice
milestones:
  - >-
    Use kubectl rollout status to see whether a rollout is progressing or stuck
  - >-
    Identify why new pods are failing during a rollout — image errors, bad
    config, failing readiness probes
  - Roll back a broken deployment with kubectl rollout undo
  - >-
    Understand why a readiness probe failure stalls a rollout rather than
    completing it
title_zh: "调试部署"

---


A stuck rollout almost always means the new pods are failing — either they're crashing immediately, or they're running but failing their readiness probe. Kubernetes deliberately holds the old pods until new ones are healthy, so a stuck rollout is a safety mechanism, not a bug.

<!-- DEEP_DIVE -->

## Check rollout status first

```bash
kubectl rollout status deployment/my-app
```

If this is stuck, Kubernetes is waiting for new pods to become ready. It won't remove old pods until new ones pass their readiness probe.

See the full rollout history:

```bash
kubectl rollout history deployment/my-app
```

## Find the failing pods

During a rollout, there will be a mix of old and new pods. Identify which generation is which:

```bash
kubectl get pods -l app=my-app
```

Look for pods in `CrashLoopBackOff`, `Error`, or stuck in `0/1 Running` (container running but not passing readiness). The pods with a newer creation timestamp are the new ones.

Check what the new pods are doing:

```bash
kubectl logs my-app-<new-pod-hash> --previous
kubectl describe pod my-app-<new-pod-hash>
```

The Events section in `describe` will tell you whether it's an image pull failure, a crash, or a readiness probe timeout.

## Common causes

**Wrong image tag** — the image doesn't exist in the registry. `kubectl describe pod` will show `ImagePullBackOff` in Events with the exact registry error.

**Bad environment variable or secret** — the app starts, tries to connect somewhere using a misconfigured URL or credential, and crashes. The error will be in `kubectl logs --previous`.

**Readiness probe failing** — the container is running but not passing the readiness check. The pod shows `0/1 Running`. `kubectl describe pod` will show repeated probe failures in Events. The pod is alive but Kubernetes won't count it as ready, so the rollout stalls. Check whether the probe path, port, or timing is wrong.

**Resource limits too low** — if the container hits its memory limit during startup, it gets OOMKilled before it can become ready. Exit code 137. Increase the memory limit.

## Roll back immediately

If you need to restore the previous version right now:

```bash
kubectl rollout undo deployment/my-app
```

To go back to a specific revision:

```bash
kubectl rollout undo deployment/my-app --to-revision=3
```

The rollback triggers a new rollout — it scales up the previous ReplicaSet and scales down the broken one. Watch it with `kubectl rollout status`.

## Pause a rollout while you investigate

If you want to stop the rollout without rolling back (to preserve the partially-deployed state while you debug):

```bash
kubectl rollout pause deployment/my-app
# ... investigate ...
kubectl rollout resume deployment/my-app
```

## A systematic approach

1. `kubectl rollout status deployment/my-app` — is it stuck?
2. `kubectl get pods` — which new pods exist and what state are they in?
3. `kubectl logs <new-pod> --previous` — what did it print before crashing?
4. `kubectl describe pod <new-pod>` — Events section: image pull? probe failures? OOMKilled?
5. Fix the underlying cause (image, config, probe, limits) then re-apply
6. If you need to restore immediately: `kubectl rollout undo`

<!-- RESOURCES -->

- [Kubernetes Docs - Performing a Rollback](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
卡住的 rollout 几乎总是意味着新的 pod 正在失败——要么它们立即崩溃，要么它们正在运行但未通过 readiness probe。Kubernetes 会刻意保留旧的 pod，直到新的 pod 健康为止，因此卡住的 rollout 是一种安全机制，而不是 bug。

<!-- ZH_DEEP_DIVE -->
## 先检查 rollout 状态

```bash
kubectl rollout status deployment/my-app
```

如果该命令卡住，说明 Kubernetes 正在等待新 Pod 变为就绪状态。在新 Pod 通过就绪探针之前，它不会移除旧 Pod。

查看完整的 rollout 历史：

```bash
kubectl rollout history deployment/my-app
```

## 找到出问题的 Pod

在 rollout 期间，会同时存在新旧 Pod。先确认哪些属于新版本：

```bash
kubectl get pods -l app=my-app
```

查找处于 `CrashLoopBackOff`、`Error` 状态，或卡在 `0/1 Running`（容器已运行但未通过就绪检查）的 Pod。创建时间戳较新的就是新 Pod。

检查新 Pod 在做什么：

```bash
kubectl logs my-app-<new-pod-hash> --previous
kubectl describe pod my-app-<new-pod-hash>
```

`describe` 中的 Events 部分会告诉你问题出在镜像拉取失败、崩溃，还是就绪探针超时。

## 常见原因

**镜像 tag 错误** — 镜像在 registry 中不存在。`kubectl describe pod` 的 Events 中会显示 `ImagePullBackOff`，并附带具体的 registry 错误。

**环境变量或 secret 配置错误** — 应用启动后，尝试使用配置错误的 URL 或凭据连接某处，然后崩溃。错误信息会出现在 `kubectl logs --previous` 中。

**就绪探针失败** — 容器正在运行但未通过就绪检查。Pod 显示为 `0/1 Running`。`kubectl describe pod` 的 Events 中会显示反复的探针失败。Pod 是活的，但 Kubernetes 不会将其计为就绪，因此 rollout 停滞。检查探针的路径、端口或时间配置是否有误。

**资源限制过低** — 如果容器在启动期间达到内存限制，它会在变为就绪之前被 OOMKilled。退出码为 137。请提高内存限制。

## 立即回滚

如果你需要立刻恢复上一版本：

```bash
kubectl rollout undo deployment/my-app
```

回滚到指定修订版本：

```bash
kubectl rollout undo deployment/my-app --to-revision=3
```

回滚会触发一次新的 rollout —— 它会扩容之前的 ReplicaSet 并缩容出问题的那个。用 `kubectl rollout status` 观察进度。

## 排查期间暂停 rollout

如果你想停止 rollout 但不回滚（在调试时保留部分部署的状态）：

```bash
kubectl rollout pause deployment/my-app
# ... 排查 ...
kubectl rollout resume deployment/my-app
```

## 系统性排查方法

1. `kubectl rollout status deployment/my-app` — 是否卡住？
2. `kubectl get pods` — 有哪些新 Pod，它们处于什么状态？
3. `kubectl logs <new-pod> --previous` — 崩溃前输出了什么？
4. `kubectl describe pod <new-pod>` — Events 部分：镜像拉取？探针失败？OOMKilled？
5. 修复根本原因（镜像、配置、探针、资源限制），然后重新 apply
6. 如果需要立即恢复：`kubectl rollout undo`

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 执行回滚](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment) -- 类型：文档，时长：15分钟

<!-- ZH_UI -->
1. 使用 kubectl rollout status 查看发布是在进行中还是卡住了
2. 找出发布期间新 pod 失败的原因——镜像错误、配置错误、就绪探针失败
3. 用 kubectl rollout undo 回滚损坏的部署
4. 理解为什么就绪探针失败会让发布停滞而不是完成
