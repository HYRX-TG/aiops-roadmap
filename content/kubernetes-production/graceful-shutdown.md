---
id: graceful-shutdown
title: Graceful Pod Shutdown
zone: kubernetes-production
edges:
  to:
    - id: pod-scheduling-spread
      question: >-
        My app shuts down cleanly, but I just realized all my replicas might be
        running on the same node.
      detail: >-
        I handle SIGTERM properly so my app drains. But if all my replicas land
        on the same node and that node goes away — hardware failure, maintenance
        drain, whatever — there's nothing left to serve traffic. How do I
        actually guarantee they end up on different nodes?
difficulty: 3
tags:
  - kubernetes
  - sigterm
  - sigkill
  - graceful
  - shutdown
  - prestop
  - k8s
  - production
category: practice
milestones:
  - >-
    Understand the shutdown sequence: SIGTERM → terminationGracePeriodSeconds →
    SIGKILL
  - >-
    Know why endpoints are removed asynchronously and what that means for
    in-flight requests
  - Understand the preStop hook sleep trick and why it exists
  - >-
    Know what your application needs to do: handle SIGTERM, drain connections,
    close DB pools
title_zh: "优雅关闭 Pod"

---


When Kubernetes kills a pod — during a rolling update, a node drain, or a scale-down — in-flight requests can fail unless the application handles shutdown correctly. This isn't just about catching SIGTERM; there's a timing issue built into how Kubernetes removes pods from the load balancer that you need to work around explicitly.

<!-- DEEP_DIVE -->

## The shutdown sequence

When a pod is deleted, several things happen:

1. Kubernetes sets the pod's status to `Terminating`
2. If a `preStop` hook is defined, it runs first
3. SIGTERM is sent to the container
4. Simultaneously, the pod's IP is removed from Service endpoints (stops new traffic from routing to it)
5. The `terminationGracePeriodSeconds` countdown begins (default: 30 seconds)
6. If the container is still running when the grace period expires, SIGKILL is sent

Your application's job: catch SIGTERM, finish in-flight requests, close connections cleanly, exit.

## The race condition you must work around

Step 3 (SIGTERM) and step 4 (removing endpoints) happen simultaneously — but they're handled by different Kubernetes controllers that don't coordinate with each other. The endpoint update propagates through the cluster asynchronously: it goes to kube-proxy, which updates iptables on every node, which takes some amount of time.

During that propagation window (typically 1–5 seconds), traffic is still being routed to your pod even though it has received SIGTERM. If your application stops accepting connections immediately on SIGTERM, those requests fail.

## The preStop sleep trick

The most practical solution is a preStop hook that sleeps for a few seconds before SIGTERM is sent:

```yaml
lifecycle:
  preStop:
    exec:
      command: [sh, -c, "sleep 5"]
```

This gives the endpoint removal time to propagate through kube-proxy before the container starts shutting down. The preStop hook runs, the process sleeps for 5 seconds, SIGTERM fires, the application drains its connections and exits. By the time SIGTERM fires, no new traffic is being routed to the pod.

The 5 second delay does increase the time a pod takes to shut down. It's worth it.

## What your application must do

The preStop trick buys time, but your application still needs to handle shutdown correctly:

**Stop accepting new connections** — when you receive SIGTERM, stop listening for new connections.

**Finish in-flight requests** — allow currently running request handlers to complete. Don't kill them mid-way.

**Close database connection pools** — return connections to the pool cleanly. An abrupt exit leaves connections open on the server side until they time out.

**Exit cleanly** — call `os.Exit(0)` or equivalent after draining. If you don't exit, Kubernetes waits until `terminationGracePeriodSeconds` and then SIGKILLs the process.

Most web frameworks have built-in graceful shutdown support. In Go, `http.Server.Shutdown`. In Node.js, close the server with `server.close()`. In Java (Spring Boot), the `server.shutdown=graceful` property. Use it.

## Setting terminationGracePeriodSeconds

The default is 30 seconds. If your application can take longer to drain (long-running requests, slow connection draining), set it higher:

```yaml
spec:
  terminationGracePeriodSeconds: 60
```

If your application exits faster (most stateless web apps), keeping it at 30 is fine. Don't set it lower than 10 — you need time for both the preStop delay and the actual drain.

For batch jobs or long-running processes, you may need minutes or more. Set it to match the maximum time the job needs to complete a unit of work.

<!-- RESOURCES -->

- [Kubernetes Docs - Pod Termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) -- type: docs, time: 20m
- [Kubernetes Docs - Container Lifecycle Hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当 Kubernetes 终止一个 pod 时——无论是在滚动更新、节点排空还是缩容期间——除非应用程序正确处理关闭流程，否则正在处理中的请求可能会失败。这不仅仅是捕获 SIGTERM 的问题；Kubernetes 将 pod 从负载均衡器中移除的方式本身存在一个时序问题，你需要显式地规避它。

<!-- ZH_DEEP_DIVE -->
## 关闭流程

当 Pod 被删除时，会发生以下几件事：

1. Kubernetes 将 Pod 的状态设置为 `Terminating`
2. 如果定义了 `preStop` 钩子，它会首先运行
3. 向容器发送 SIGTERM
4. 同时，Pod 的 IP 从 Service endpoints 中移除（停止新流量路由到它）
5. `terminationGracePeriodSeconds` 倒计时开始（默认：30 秒）
6. 如果宽限期到期时容器仍在运行，则发送 SIGKILL

你的应用程序的职责：捕获 SIGTERM，完成正在处理的请求，干净地关闭连接，然后退出。

## 你必须应对的竞态条件

步骤 3（SIGTERM）和步骤 4（移除 endpoints）同时发生——但它们由不同的 Kubernetes 控制器处理，这些控制器之间并不协调。endpoint 更新在集群中异步传播：它传到 kube-proxy，kube-proxy 再更新每个节点上的 iptables，这需要一定时间。

在这个传播窗口期间（通常为 1–5 秒），即使你的 Pod 已经收到 SIGTERM，流量仍在被路由到它。如果你的应用程序在收到 SIGTERM 时立即停止接受连接，那些请求就会失败。

## preStop sleep 技巧

最实用的解决方案是使用 preStop 钩子，在发送 SIGTERM 之前先 sleep 几秒钟：

```yaml
lifecycle:
  preStop:
    exec:
      command: [sh, -c, "sleep 5"]
```

这为 endpoint 移除留出了通过 kube-proxy 传播的时间，之后容器才开始关闭。preStop 钩子运行，进程 sleep 5 秒，SIGTERM 触发，应用程序排空连接并退出。等到 SIGTERM 触发时，已经没有新流量被路由到该 Pod 了。

5 秒的延迟确实会增加 Pod 关闭所需的时间。但这是值得的。

## 你的应用程序必须做什么

preStop 技巧争取了时间，但你的应用程序仍然需要正确处理关闭：

**停止接受新连接**——收到 SIGTERM 时，停止监听新连接。

**完成正在处理的请求**——允许当前正在运行的请求处理器完成。不要中途杀死它们。

**关闭数据库连接池**——干净地将连接归还到池中。突然退出会导致连接在服务器端保持打开状态，直到超时。

**干净退出**——在排空后调用 `os.Exit(0)` 或等效操作。如果你不退出，Kubernetes 会等到 `terminationGracePeriodSeconds` 到期，然后 SIGKILL 该进程。

大多数 Web 框架都内置了优雅关闭支持。在 Go 中，使用 `http.Server.Shutdown`。在 Node.js 中，使用 `server.close()` 关闭服务器。在 Java（Spring Boot）中，使用 `server.shutdown=graceful` 属性。请使用它。

## 设置 terminationGracePeriodSeconds

默认值为 30 秒。如果你的应用程序排空需要更长时间（长时间运行的请求、缓慢的连接排空），请将其设置得更高：

```yaml
spec:
  terminationGracePeriodSeconds: 60
```

如果你的应用程序退出更快（大多数无状态 Web 应用），保持 30 秒即可。不要将其设置低于 10——你需要时间用于 preStop 延迟和实际排空。

对于批处理作业或长时间运行的进程，你可能需要几分钟甚至更长时间。将其设置为与作业完成一个工作单元所需的最大时间相匹配。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Pod 终止](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) -- 类型：文档，时长：20 分钟
- [Kubernetes 文档 - 容器生命周期钩子](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 理解关闭序列：SIGTERM → terminationGracePeriodSeconds → SIGKILL
2. 了解端点为何被异步移除，以及这对进行中请求意味着什么
3. 理解 preStop hook 的 sleep 技巧及其存在的原因
4. 了解你的应用需要做什么：处理 SIGTERM、排空连接、关闭数据库连接池
5. 我的应用能干净地关闭，但我刚意识到所有副本可能都运行在同一个节点上。
6. 我正确处理了 SIGTERM，所以应用能排空。但如果所有副本都落在同一个节点上，而该节点消失——硬件故障、维护排空，或其他原因——就没有任何实例能继续服务流量。我该如何真正保证它们落在不同节点上？
