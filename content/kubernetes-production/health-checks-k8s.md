---
id: health-checks-k8s
title: 'Health Checks: Liveness, Readiness, Startup'
zone: kubernetes-production
edges:
  to:
    - id: graceful-shutdown
      question: >-
        Kubernetes knows when my app is sick. But what happens when it decides
        to restart or move a pod — does traffic just get dropped?
      detail: >-
        My liveness probe works and unhealthy pods get restarted. But what
        happens to requests that are in-flight when the pod gets killed? Do they
        just fail, or is there something that drains them first?
difficulty: 2
tags:
  - kubernetes
  - liveness
  - readiness
  - startup
  - probes
  - health
  - k8s
  - production
category: practice
milestones:
  - Understand the three probe types and when each fires
  - >-
    Know the critical mistake: an aggressive liveness probe that causes restart
    loops
  - >-
    Know the readiness probe problem: no probe means traffic hits pods that
    aren't ready
  - >-
    Understand when startup probes save JVM and heavy-framework apps from being
    killed during boot
  - 'Write HTTP, TCP, and exec probe configurations'
title_zh: "健康检查：存活探针、就绪探针、启动探针"

---


Kubernetes has three probe types for checking container health, and each one does a fundamentally different thing. Configuring the wrong probe type for the wrong purpose is one of the most common causes of self-inflicted production incidents — including restart loops that take your service down entirely.

<!-- DEEP_DIVE -->

## The three probe types

**Liveness probe** — answers the question: "Is this container in a state it can never recover from?" If the liveness probe fails, Kubernetes kills the container and restarts it.

**Readiness probe** — answers the question: "Is this container ready to receive traffic?" If the readiness probe fails, Kubernetes removes the pod from the Service endpoints. Traffic stops going to it. The pod isn't killed — it stays running but receives no traffic until the probe passes again.

**Startup probe** — answers the question: "Has this container finished starting up?" Used to protect slow-starting containers from the liveness probe firing too early. While the startup probe hasn't passed, the liveness probe is disabled.

## The dangerous liveness probe mistake

This is the most consequential misconfiguration: using the liveness probe to check things the container has no control over.

Example of what not to do: checking that your database is reachable in the liveness probe. If the database goes down, all your pods fail their liveness probe and Kubernetes starts killing and restarting them — over and over, in a loop. The restarts don't fix the database. You've now made the situation worse: your app goes from degraded (slow queries, errors) to completely unavailable (restart loop).

The liveness probe should only check things that indicate the process itself is stuck and needs to be killed. An HTTP endpoint that returns 200 as long as the application's event loop is responsive. A simple check that the process hasn't deadlocked.

**Readiness** is the right probe for dependency failures. If the database is unreachable, fail the readiness probe. Traffic stops hitting the pod. The pod stays running and ready to serve as soon as the database comes back — no restart needed.

## No readiness probe is also a problem

Without a readiness probe, Kubernetes adds a pod to the Service endpoints as soon as it's Running. Your application might take 10 seconds to load configuration, warm caches, or establish connection pools. During those 10 seconds, live traffic is hitting an unready pod and failing.

Always configure a readiness probe for services that receive traffic.

## Startup probe for slow applications

JVM applications, Rails, and other heavy frameworks can take 30–90 seconds to start. Without a startup probe:
- Set liveness `initialDelaySeconds` too short → liveness fires during startup → restart loop
- Set it too long → a genuinely crashed pod isn't detected for a long time

The startup probe is a clean solution: it fires repeatedly during startup until the app is ready. Once it passes, it hands off to the liveness probe for the rest of the container's life.

## Probe configuration

All three probes support the same probe types:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10    # wait this long before starting
  periodSeconds: 10          # check every N seconds
  failureThreshold: 3        # fail this many times before action
  successThreshold: 1        # pass this many times before healthy

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30       # 30 * 10s = 5 minutes to start
  periodSeconds: 10
```

Beyond `httpGet`, probes also support `tcpSocket` (checks if a port accepts connections) and `exec` (runs a command in the container; exit code 0 = healthy).

## Separate liveness and readiness endpoints

Expose two different HTTP endpoints: `/healthz` for liveness (always returns 200 as long as the process is alive), `/ready` for readiness (returns 200 only when dependencies are available and the app is ready to serve). Keep them separate — conflating them leads to the liveness-checking-dependencies mistake.

<!-- RESOURCES -->

- [Kubernetes Docs - Configure Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) -- type: docs, time: 25m

<!-- ZH_SUMMARY -->
Kubernetes 有三种用于检查容器健康状态的探针类型，每种探针做的事情在本质上各不相同。为错误的目的配置错误的探针类型，是导致自伤性生产事故最常见的原因之一——包括让服务彻底宕机的重启循环。

<!-- ZH_DEEP_DIVE -->
## 三种探针类型

**存活探针（Liveness probe）**——回答的问题是：“这个容器是否处于永远无法恢复的状态？”如果存活探针失败，Kubernetes 会杀死容器并重启它。

**就绪探针（Readiness probe）**——回答的问题是：“这个容器是否已准备好接收流量？”如果就绪探针失败，Kubernetes 会将 Pod 从 Service 的端点中移除。流量停止发往该 Pod。Pod 不会被杀死——它继续运行，但在探针再次通过之前不会接收任何流量。

**启动探针（Startup probe）**——回答的问题是：“这个容器是否已完成启动？”用于保护启动缓慢的容器，避免存活探针过早触发。在启动探针通过之前，存活探针处于禁用状态。

## 危险的存活探针误用

这是后果最严重的错误配置：使用存活探针检查容器无法控制的事项。

错误做法的示例：在存活探针中检查数据库是否可达。如果数据库宕机，所有 Pod 的存活探针都会失败，Kubernetes 会开始反复杀死并重启它们——陷入循环。重启并不能修复数据库。你反而让情况变得更糟：应用从降级状态（查询缓慢、报错）变成完全不可用（重启循环）。

存活探针只应检查那些表明进程本身已卡死、需要被杀死的事项。例如一个只要应用的事件循环有响应就返回 200 的 HTTP 端点。一个简单的检查，确认进程没有死锁。

**就绪探针**才是应对依赖故障的正确探针。如果数据库不可达，就让就绪探针失败。流量停止打到该 Pod。Pod 保持运行，一旦数据库恢复就能立即提供服务——无需重启。

## 没有就绪探针同样是个问题

如果没有就绪探针，Kubernetes 会在 Pod 进入 Running 状态后立即将其加入 Service 端点。你的应用可能需要 10 秒钟来加载配置、预热缓存或建立连接池。在这 10 秒内，实时流量会打到尚未就绪的 Pod 上并失败。

对于接收流量的服务，务必配置就绪探针。

## 为启动缓慢的应用配置启动探针

JVM 应用、Rails 以及其他重型框架可能需要 30–90 秒才能启动。如果没有启动探针：
- 将存活探针的 `initialDelaySeconds` 设得太短 → 存活探针在启动期间触发 → 重启循环
- 设得太长 → 真正崩溃的 Pod 长时间无法被检测到

启动探针是一个干净的解决方案：它在启动期间反复触发，直到应用就绪。一旦通过，它就将控制权交给存活探针，负责容器剩余生命周期的检查。

## 探针配置

三种探针都支持相同的探针类型：

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10    # wait this long before starting
  periodSeconds: 10          # check every N seconds
  failureThreshold: 3        # fail this many times before action
  successThreshold: 1        # pass this many times before healthy

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30       # 30 * 10s = 5 minutes to start
  periodSeconds: 10
```

除了 `httpGet`，探针还支持 `tcpSocket`（检查端口是否接受连接）和 `exec`（在容器中运行命令；退出码 0 = 健康）。

## 分离存活与就绪端点

暴露两个不同的 HTTP 端点：`/healthz` 用于存活检查（只要进程存活就始终返回 200），`/ready` 用于就绪检查（仅当依赖可用且应用已准备好提供服务时才返回 200）。保持它们分离——将二者混为一谈会导致存活探针检查依赖项的错误。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 配置 Liveness、Readiness 和 Startup 探针](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) -- 类型：docs，时间：25m

<!-- ZH_UI -->
1. 理解三种探针类型及其各自的触发时机
2. 了解关键错误：过于激进的存活探针会导致重启循环
3. 了解就绪探针的问题：没有探针意味着流量会打到尚未就绪的 Pod 上
4. 理解启动探针何时能避免 JVM 和重型框架应用在启动期间被杀掉
5. 编写 HTTP、TCP 和 exec 探针配置
6. Kubernetes 知道我的应用何时出问题。但当它决定重启或迁移 Pod 时会发生什么——流量就这样被丢弃了吗？
7. 我的存活探针工作正常，不健康的 Pod 会被重启。但 Pod 被杀掉时正在处理中的请求会怎样？它们会直接失败，还是有某种机制会先把它们排空？
