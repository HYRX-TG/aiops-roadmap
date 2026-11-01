---
id: deployments
title: Deployments
zone: kubernetes
edges:
  to:
    - id: services
      question: >-
        I have a Deployment running three replicas. How do I send traffic to all
        of them instead of hitting one pod at a time?
      detail: >-
        I can reach a single pod with port-forward, but now I have three
        replicas. How does a real request actually get to any of them — and if
        one pod goes down, does traffic automatically stop going to it?
    - id: deployment-strategies
      question: >-
        Rolling updates are the default. What other strategies exist for
        zero-downtime deployments?
      detail: >-
        Rolling update works — but it just swaps everything out gradually, and
        if something is wrong I don't find out until users are hitting the
        broken pods. Is there a way to test a new version with a small slice of
        real traffic before rolling it out to everyone?
    - id: jobs-and-cronjobs
      question: >-
        Deployments keep services running forever. What about tasks that just
        need to run once and finish?
      detail: >-
        My app is a long-running service — it just keeps going. But I also need
        to run database migrations, generate reports, process a queue of
        uploads. These aren't services, they have a start and an end. How does
        Kubernetes handle tasks that are supposed to finish?
    - id: daemonsets
      question: >-
        I need something running on every single node — like a log collector. A
        Deployment with a fixed replica count won't cut it.
      detail: >-
        I need a monitoring agent on every node. If I set replicas to 5 and a
        new node joins the cluster, the agent won't be there. Is there a
        workload type that automatically keeps exactly one pod running per node?
    - id: configmaps
      question: >-
        My app needs different config for dev and production — database URLs,
        feature flags, settings. Where do those go in Kubernetes?
      detail: >-
        Right now I'm baking config into the container image, which means I
        need a different image for every environment. That can't be right —
        the image should be the same everywhere and just pick up the right
        config at runtime. How does Kubernetes handle that?
    - id: debugging-deployments
      question: >-
        I deployed a new version and the rollout is stuck — new pods keep
        crashing while old ones are still running.
      detail: >-
        I updated the image and ran kubectl apply, but the new pods are in
        CrashLoopBackOff and the old pods are still serving traffic. The rollout
        never finishes. I can't tell if it's a bad image, a wrong environment
        variable, or something else.
difficulty: 2
tags:
  - kubernetes
  - deployments
  - rolling-update
  - replicaset
  - kubectl
  - k8s
  - zero-downtime
category: practice
milestones:
  - Create a Deployment and understand its relationship to ReplicaSets and Pods
  - Update the container image and watch the rolling update proceed
  - Roll back to a previous version with kubectl rollout undo
  - Set resource requests and limits on the Deployment's Pod template
  - Explain what happens to running traffic during a rolling update
title_zh: "部署"

---


A Deployment is the standard way to run a long-lived application on Kubernetes. It manages a ReplicaSet (which manages Pods), declares the desired state — image, replicas, resources — and handles rolling updates and rollbacks automatically when you change the spec.

<!-- DEEP_DIVE -->

## Deployments, ReplicaSets, and Pods

Kubernetes has three layers here:

- **Pod** — runs your containers on a single node
- **ReplicaSet** — ensures N copies of a Pod spec are running at all times; replaces Pods that fail or get deleted
- **Deployment** — manages the ReplicaSet and handles transitions between versions

You almost never create ReplicaSets directly. You create Deployments, and the Deployment controller creates and manages ReplicaSets for you. Each time you update a Deployment's Pod template (new image, new env var, new resource limits), a new ReplicaSet is created and the old one is scaled down gradually.

## Writing a Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:1.2.3
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```

## Rolling updates

When you change `spec.template` — typically by updating the container image — Kubernetes performs a rolling update:

1. Creates a new ReplicaSet with the new Pod template
2. Scales up the new ReplicaSet one Pod at a time
3. As new Pods pass their readiness probe, scales down the old ReplicaSet by one
4. Repeats until all Pods are on the new version

The rolling update is controlled by two fields in `spec.strategy.rollingUpdate`:

- `maxSurge` — how many extra Pods can exist above the desired count during the update (default: 25%)
- `maxUnavailable` — how many Pods can be below the desired count during the update (default: 25%)

With `replicas: 4`, `maxSurge: 1`, `maxUnavailable: 0`: Kubernetes creates one new Pod, waits for it to pass readiness, then terminates one old Pod, repeating until done. Zero Pods are ever removed before a replacement is ready — true zero-downtime deployment.

## Checking rollout status

```bash
kubectl rollout status deployment/my-app
```

This blocks until the rollout completes. If the new Pods fail their readiness probe, the rollout pauses here — you won't accidentally mark a broken deployment as done.

## Rolling back

If something goes wrong:

```bash
kubectl rollout undo deployment/my-app
```

This scales up the previous ReplicaSet and scales down the current one. Kubernetes keeps a configurable history of old ReplicaSets (default: 10), so you can roll back multiple versions:

```bash
kubectl rollout history deployment/my-app
kubectl rollout undo deployment/my-app --to-revision=3
```

## Updating the image imperatively

```bash
kubectl set image deployment/my-app app=my-app:1.3.0
```

This works in a pinch, but it's not tracked in Git, it's not reproducible, and it bypasses any review process. In practice, update the Deployment manifest and apply it through GitOps — that way the change has an audit trail and can be reverted with `git revert`.

<!-- RESOURCES -->

- [Kubernetes Docs - Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) -- type: docs, time: 30m
- [kubectl rollout command reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/) -- type: docs, time: 10m
- [Kubernetes Deployment Strategies - Container Solutions](https://blog.container-solutions.com/kubernetes-deployment-strategies) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
Deployment 是在 Kubernetes 上运行长期存活应用的标准方式。它管理 ReplicaSet（后者管理 Pod），声明期望状态——镜像、副本数、资源——并在你修改 spec 时自动处理滚动更新和回滚。

<!-- ZH_DEEP_DIVE -->
## Deployment、ReplicaSet 与 Pod

Kubernetes 在这里分为三层：

- **Pod** —— 在单个节点上运行你的容器
- **ReplicaSet** —— 确保始终运行 N 个 Pod 规格的副本；替换失败或被删除的 Pod
- **Deployment** —— 管理 ReplicaSet 并处理版本之间的过渡

你几乎从不直接创建 ReplicaSet。你创建 Deployment，由 Deployment 控制器为你创建和管理 ReplicaSet。每次更新 Deployment 的 Pod 模板（新镜像、新环境变量、新资源限制）时，都会创建一个新的 ReplicaSet，旧的 ReplicaSet 会被逐步缩容。

## 编写 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:1.2.3
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```

## 滚动更新

当你修改 `spec.template` 时——通常是通过更新容器镜像——Kubernetes 会执行滚动更新：

1. 使用新的 Pod 模板创建一个新的 ReplicaSet
2. 逐个 Pod 地扩容新的 ReplicaSet
3. 当新 Pod 通过其就绪探针后，将旧的 ReplicaSet 缩容一个
4. 重复此过程，直到所有 Pod 都运行新版本

滚动更新由 `spec.strategy.rollingUpdate` 中的两个字段控制：

- `maxSurge` —— 更新期间可以超出期望数量的额外 Pod 数（默认：25%）
- `maxUnavailable` —— 更新期间可以低于期望数量的 Pod 数（默认：25%）

当 `replicas: 4`、`maxSurge: 1`、`maxUnavailable: 0` 时：Kubernetes 创建一个新 Pod，等待其通过就绪探针，然后终止一个旧 Pod，如此重复直到完成。在替代 Pod 就绪之前，绝不会移除任何 Pod——真正的零停机部署。

## 检查滚动更新状态

```bash
kubectl rollout status deployment/my-app
```

此命令会阻塞直到滚动更新完成。如果新 Pod 未通过就绪探针，滚动更新会在此处暂停——你不会意外地将损坏的部署标记为完成。

## 回滚

如果出现问题：

```bash
kubectl rollout undo deployment/my-app
```

这会扩容之前的 ReplicaSet 并缩容当前的 ReplicaSet。Kubernetes 会保留可配置的旧 ReplicaSet 历史记录（默认：10），因此你可以回滚多个版本：

```bash
kubectl rollout history deployment/my-app
kubectl rollout undo deployment/my-app --to-revision=3
```

## 以命令式方式更新镜像

```bash
kubectl set image deployment/my-app app=my-app:1.3.0
```

这在紧急情况下可行，但它不会被 Git 跟踪，不可复现，并且绕过了任何审查流程。在实践中，应更新 Deployment 清单并通过 GitOps 应用它——这样变更就有审计轨迹，并且可以通过 `git revert` 回退。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) -- 类型: 文档, 时间: 30m
- [kubectl rollout 命令参考](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/) -- 类型: 文档, 时间: 10m
- [Kubernetes 部署策略 - Container Solutions](https://blog.container-solutions.com/kubernetes-deployment-strategies) -- 类型: 文章, 时间: 10m

<!-- ZH_UI -->
1. 创建一个 Deployment，并理解它与 ReplicaSet 和 Pod 的关系
2. 更新容器镜像，观察滚动更新过程
3. 使用 kubectl rollout undo 回滚到之前的版本
4. 为 Deployment 的 Pod 模板设置资源请求和限制
5. 解释滚动更新期间运行中的流量会发生什么
6. 我有一个运行三个副本的 Deployment。如何将流量发送到所有副本，而不是一次只命中一个 Pod？
7. 我可以用 port-forward 访问单个 Pod，但现在有三个副本。真实请求实际上是如何到达其中任意一个的？如果某个 Pod 挂了，流量会自动停止发往它吗？
8. 滚动更新是默认方式。还有哪些策略可以实现零停机部署？
9. 滚动更新能用——但它只是逐步替换所有内容，如果出了问题，直到用户访问到有问题的 Pod 我才会发现。有没有办法在向所有人推出之前，先用一小部分真实流量测试新版本？
10. Deployment 让服务永远运行。那些只需要运行一次就结束的任务呢？
11. 我的应用是一个长期运行的服务——它一直在跑。但我还需要运行数据库迁移、生成报告、处理上传队列。这些不是服务，它们有开始也有结束。Kubernetes 如何处理那些本应完成的任务？
12. 我需要每个节点上都运行某些东西——比如日志收集器。固定副本数的 Deployment 做不到。
13. 我需要在每个节点上运行监控代理。如果我把副本数设为 5，然后一个新节点加入集群，代理就不会在那里。有没有一种工作负载类型能自动保持每个节点上恰好运行一个 Pod？
14. 我的应用在开发和生产环境需要不同的配置——数据库 URL、功能开关、设置。这些在 Kubernetes 中放在哪里？
15. 目前我把配置烘焙进容器镜像，这意味着每个环境都需要不同的镜像。这不对——镜像应该在所有环境中都一样，只在运行时获取正确的配置。Kubernetes 如何处理这个？
16. 我部署了一个新版本，但 rollout 卡住了——新 Pod 不断崩溃，而旧 Pod 仍在运行。
17. 我更新了镜像并运行了 kubectl apply，但新 Pod 处于 CrashLoopBackOff，旧 Pod 仍在处理流量。rollout 永远完不成。我分不清是镜像有问题、环境变量错了，还是其他原因。
