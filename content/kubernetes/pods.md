---
id: pods
title: Pods
zone: kubernetes
edges:
  to:
    - id: services
      question: My Pod is running. How do I access it reliably?
      detail: >-
        My Pod has an IP, but I've already seen how Pods get deleted and
        recreated. Every time that happens the IP changes — which means anything
        trying to reach my Pod would break. I need something more stable than a
        Pod IP to point other services or users at.
    - id: port-forward
      question: >-
        My Pod is running. I just want to quickly access it to see if it works —
        what's the simplest way?
      detail: >-
        I just want to hit my Pod in a browser to see if it's actually serving
        anything — but I haven't set up any networking yet. Is there a quick way
        to just peek at it directly without having to wire up a whole load
        balancer first?
    - id: health-checks
      question: >-
        My Pod is running — but how does Kubernetes know if it's actually
        healthy and ready to serve traffic?
      detail: >-
        I've seen my pod show as Running in kubectl, but requests were still
        failing because the app wasn't actually ready yet. How does Kubernetes
        know when my app is genuinely ready to take traffic — not just
        technically started?
    - id: deployments
      question: >-
        Managing individual Pods by hand seems wrong. How do I actually run my
        app reliably?
      detail: >-
        I've been creating Pods directly but they don't restart when they crash,
        I can't run multiple copies easily, and there's no way to roll out a
        new version without downtime. There has to be a better way to run a
        real service.
    - id: init-containers
      question: >-
        My app keeps crashing on startup because the database isn't ready yet.
        Is there a way to run a setup step before my main container starts?
      detail: >-
        I've added retry loops inside my app code but it feels like the wrong
        place to put that logic. Other things too — I need to download some
        config files, set up directory permissions — before the app can actually
        start. Can I define pre-start steps at the Kubernetes level?
    - id: debugging-pods
      question: >-
        My pod is stuck in CrashLoopBackOff and I have no idea what's happening
        inside it.
      detail: >-
        kubectl get pods shows CrashLoopBackOff but that tells me nothing about
        why. I don't even know how to see the logs or get inside the container
        to poke around. Where do I even start?
difficulty: 1
tags:
  - kubernetes
  - pods
  - containers
  - k8s
  - kubectl
  - multi-container
category: concept
milestones:
  - Write a Pod manifest and apply it with kubectl apply
  - Exec into a running Pod with kubectl exec
  - Read Pod logs with kubectl logs
  - Explain why a Pod can run multiple containers and when you'd want that
  - Understand why you shouldn't run naked Pods in production
title_zh: "Pod"

---


In Kubernetes, the smallest deployable unit is not a container — it's a Pod. A Pod wraps one or more containers that share a network stack and storage, and runs together on a single node. Understanding the Pod abstraction is the foundation for everything else in Kubernetes.

<!-- DEEP_DIVE -->

## Why not just "a container"?

The most natural question: why invent the "Pod" concept at all? Why not just schedule containers?

The short answer: sometimes two containers are so tightly coupled that they need to share a local network or filesystem. The Pod models that relationship. Two containers in the same Pod communicate over `localhost`, share a network interface, and can mount the same volumes.

The most common case is a Pod with exactly one container, and that's fine. The Pod is just a thin wrapper around it. But the abstraction exists for when you need that tight coupling.

## Writing a Pod manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  namespace: default
spec:
  containers:
    - name: app
      image: nginx:1.25
      ports:
        - containerPort: 80
```

Apply it:

```bash
kubectl apply -f pod.yaml
kubectl get pods
# NAME     READY   STATUS    RESTARTS   AGE
# my-app   1/1     Running   0          12s
```

Get logs: `kubectl logs my-app`

Exec into it: `kubectl exec -it my-app -- /bin/sh`

Describe it (events, status, container details): `kubectl describe pod my-app`

## The sidecar pattern

When would you run multiple containers in a Pod? The classic case is the **sidecar** — one container runs your application, a second runs a helper that doesn't belong in the app image.

Examples:

- A log shipper (Fluentd, Filebeat) that reads log files written by the app and forwards them to a central logging platform
- An Envoy proxy sidecar that handles mTLS and traffic management (how Istio works)
- A git-sync container that pulls config from a Git repository and writes it to a shared volume for the app to read

The key: sidecar containers need to run on the same node as the app, share its network interface, and often need access to the same files. The Pod provides exactly that.

## Why you shouldn't run naked Pods in production

A Pod by itself is not self-healing. If the node it's running on dies, the Pod is gone and doesn't come back. The container inside a Pod will be restarted if it crashes (based on `restartPolicy`), but the Pod itself is permanently tied to that one node.

For production workloads, you almost never create Pods directly. You create a **Deployment** instead. A Deployment manages a ReplicaSet, which manages Pods — and the Deployment controller ensures the right number of Pods are always running across the cluster. If a node dies, the affected Pods are rescheduled onto healthy nodes automatically.

Think of bare Pods as a learning and debugging tool. For anything that needs to stay alive, use a Deployment.

## Pod lifecycle phases

A Pod moves through these phases:

- **Pending** — scheduled but containers not yet started (pulling images, waiting for a node with enough resources)
- **Running** — at least one container is running
- **Succeeded** — all containers exited with code 0 (used for Jobs)
- **Failed** — at least one container exited non-zero and won't be restarted
- **Unknown** — the node isn't reporting back; usually a node connectivity problem

`kubectl describe pod <name>` shows the events log that explains why a Pod is stuck in any of these phases. It's the first thing to check when a Pod won't start.

<!-- RESOURCES -->

- [Kubernetes Docs - Pods](https://kubernetes.io/docs/concepts/workloads/pods/) -- type: docs, time: 20m
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) -- type: reference, time: 15m
- [Kubernetes Docs - Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
在 Kubernetes 中，最小的可部署单元不是容器，而是 Pod。Pod 封装了一个或多个共享网络栈和存储的容器，它们在同一节点上一起运行。理解 Pod 这一抽象概念是掌握 Kubernetes 中其他一切内容的基础。

<!-- ZH_DEEP_DIVE -->
## 为什么不直接使用“容器”？

最自然的问题：为什么要发明“Pod”这个概念？为什么不直接调度容器？

简短的回答：有时两个容器耦合得如此紧密，以至于它们需要共享本地网络或文件系统。Pod 对这种关系进行了建模。同一个 Pod 中的两个容器通过 `localhost` 通信，共享一个网络接口，并且可以挂载相同的卷。

最常见的情况是一个 Pod 中恰好只有一个容器，这没问题。Pod 只是它外面的一层薄封装。但当你需要那种紧密耦合时，这个抽象就存在了。

## 编写 Pod 清单

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  namespace: default
spec:
  containers:
    - name: app
      image: nginx:1.25
      ports:
        - containerPort: 80
```

应用它：

```bash
kubectl apply -f pod.yaml
kubectl get pods
# NAME     READY   STATUS    RESTARTS   AGE
# my-app   1/1     Running   0          12s
```

获取日志：`kubectl logs my-app`

进入容器：`kubectl exec -it my-app -- /bin/sh`

描述它（事件、状态、容器详情）：`kubectl describe pod my-app`

## Sidecar 模式

什么时候会在一个 Pod 中运行多个容器？经典的情况是 **sidecar** —— 一个容器运行你的应用，第二个容器运行一个不属于应用镜像的辅助程序。

示例：

- 一个日志转发器（Fluentd、Filebeat），读取应用写入的日志文件并将它们转发到中央日志平台
- 一个 Envoy 代理 sidecar，处理 mTLS 和流量管理（Istio 的工作方式）
- 一个 git-sync 容器，从 Git 仓库拉取配置并将其写入共享卷，供应用读取

关键点：sidecar 容器需要与应用运行在同一个节点上，共享其网络接口，并且通常需要访问相同的文件。Pod 恰好提供了这些。

## 为什么不应该在生产环境运行裸 Pod

Pod 本身不具备自愈能力。如果它所在的节点宕机，Pod 就会消失且不会回来。Pod 内的容器如果崩溃会被重启（基于 `restartPolicy`），但 Pod 本身永久绑定在那一个节点上。

对于生产工作负载，你几乎从不直接创建 Pod。而是创建一个 **Deployment**。Deployment 管理 ReplicaSet，ReplicaSet 管理 Pod —— 并且 Deployment 控制器确保集群中始终运行正确数量的 Pod。如果某个节点宕机，受影响的 Pod 会自动重新调度到健康的节点上。

把裸 Pod 视为学习和调试工具。对于任何需要保持存活的东西，请使用 Deployment。

## Pod 生命周期阶段

Pod 会经历以下阶段：

- **Pending** —— 已调度但容器尚未启动（拉取镜像、等待有足够资源的节点）
- **Running** —— 至少有一个容器正在运行
- **Succeeded** —— 所有容器都以代码 0 退出（用于 Job）
- **Failed** —— 至少有一个容器以非零代码退出且不会被重启
- **Unknown** —— 节点没有回报状态；通常是节点连接问题

`kubectl describe pod <name>` 会显示事件日志，解释 Pod 为何卡在任何一个阶段。当 Pod 无法启动时，这是首先要检查的内容。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Pods](https://kubernetes.io/docs/concepts/workloads/pods/) -- 类型: 文档, 时间: 20m
- [kubectl 速查表](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) -- 类型: 参考, 时间: 15m
- [Kubernetes 文档 - Sidecar 容器](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) -- 类型: 文档, 时间: 10m

<!-- ZH_UI -->
1. 编写 Pod 清单并用 kubectl apply 应用它
2. 用 kubectl exec 进入运行中的 Pod
3. 用 kubectl logs 查看 Pod 日志
4. 解释为什么一个 Pod 可以运行多个容器，以及何时需要这样做
5. 理解为什么不应在生产环境运行裸 Pod
6. 我的 Pod 正在运行。如何可靠地访问它？
7. 我的 Pod 有 IP，但我已经见过 Pod 被删除并重建。每次发生这种情况 IP 都会变——这意味着任何试图访问我 Pod 的东西都会中断。我需要比 Pod IP 更稳定的东西来指向其他服务或用户。
8. 我的 Pod 正在运行。我只想快速访问它看看是否正常——最简单的方法是什么？
9. 我只想在浏览器里访问我的 Pod 看看它是否真的在提供服务——但我还没配置任何网络。有没有快速方法直接查看它，而不必先搭建整个负载均衡器？
10. 我的 Pod 正在运行——但 Kubernetes 如何知道它是否真的健康并准备好接收流量？
11. 我见过 Pod 在 kubectl 中显示为 Running，但请求仍然失败，因为应用实际上还没准备好。Kubernetes 如何知道我的应用何时真正准备好接收流量——而不仅仅是技术上已启动？
12. 手动管理单个 Pod 似乎不对。我该如何真正可靠地运行我的应用？
13. 我一直在直接创建 Pod，但它们崩溃时不会重启，我无法轻松运行多个副本，也没有办法在不中断的情况下推出新版本。运行真正的服务一定有更好的方法。
14. 我的应用启动时一直崩溃，因为数据库还没准备好。有没有办法在主容器启动前运行一个初始化步骤？
15. 我在应用代码里加了重试循环，但感觉把这种逻辑放在那里不对。还有其他事情——我需要下载一些配置文件、设置目录权限——然后应用才能真正启动。我能在 Kubernetes 层面定义启动前步骤吗？
16. 我的 Pod 卡在 CrashLoopBackOff，我完全不知道里面发生了什么。
17. kubectl get pods 显示 CrashLoopBackOff，但这没有告诉我原因。我甚至不知道如何查看日志或进入容器排查。我该从哪里开始？
