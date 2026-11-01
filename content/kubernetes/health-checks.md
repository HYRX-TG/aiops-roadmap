---
id: health-checks
title: 'Health Checks: Liveness, Readiness, and Startup Probes'
zone: kubernetes
edges:
  to:
    - id: services
      question: >-
        Probes are configured. Now how do I expose my Pod with a stable
        endpoint?
      detail: >-
        My probes are configured and Kubernetes knows when my pod is healthy.
        But how does traffic actually reach my pods? They have IPs that change
        every time they restart — I need something stable that I can point DNS
        at, something that finds the healthy pods automatically.
difficulty: 2
tags:
  - kubernetes
  - liveness-probe
  - readiness-probe
  - startup-probe
  - health-checks
  - reliability
  - k8s
category: practice
milestones:
  - >-
    Add a readiness probe to a Pod and verify it's removed from Service
    endpoints during startup
  - >-
    Add a liveness probe and watch Kubernetes restart a Pod that stops
    responding
  - Understand when to use a startup probe instead of a long initialDelaySeconds
  - >-
    Explain the difference: liveness (is it broken?) vs readiness (is it ready
    for traffic?)
  - >-
    See what happens to a rolling update when the new Pod fails its readiness
    probe
title_zh: "健康检查：存活探针、就绪探针与启动探针"

---


Kubernetes has three types of probes for monitoring container health: liveness (is it broken and needs restarting?), readiness (is it ready to receive traffic?), and startup (has it finished initializing?). Configuring them correctly is the difference between self-healing infrastructure and a service that silently fails under load.

<!-- DEEP_DIVE -->

## The three probes

**Liveness probe** — answers "is this container broken in a way that warrants a restart?" If a liveness probe fails repeatedly, Kubernetes kills the container and restarts it. Use this for detecting deadlocks, memory leaks that make the app unresponsive, or any state where "restart it" is the right fix.

**Readiness probe** — answers "is this container ready to serve traffic?" A failing readiness probe removes the Pod from the Service's endpoint list. Traffic stops being routed to it. This is not a restart — the Pod keeps running, it just receives no traffic until it recovers. Use this to signal "I'm still initializing" or "I'm under too much load, back off."

**Startup probe** — answers "has this container finished starting up?" It blocks the liveness and readiness probes from running until it passes. Use this for slow-starting apps (JVM services, anything loading large datasets on boot) — it prevents the liveness probe from killing the container before it's had time to start.

## Probe types

All three probes support the same check mechanisms:

**HTTP GET** — the most common. Kubernetes makes an HTTP request; any 2xx or 3xx response counts as healthy:

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

**TCP Socket** — opens a TCP connection; success means the port is accepting connections. Good for non-HTTP services:

```yaml
readinessProbe:
  tcpSocket:
    port: 5432
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Exec** — runs a command inside the container; exit code 0 is healthy:

```yaml
livenessProbe:
  exec:
    command: ["redis-cli", "ping"]
  periodSeconds: 10
```

## Common configuration fields

- `initialDelaySeconds` — how long to wait after container start before running the first probe
- `periodSeconds` — how often to run the probe (default: 10s)
- `timeoutSeconds` — how long to wait for a response before counting it as a failure
- `failureThreshold` — how many consecutive failures before acting (restarting for liveness, removing from Service endpoints for readiness)
- `successThreshold` — how many consecutive successes to be considered healthy again after a failure (always 1 for liveness and startup)

## How readiness integrates with rolling updates

During a rolling update, Kubernetes replaces Pods one by one. A new Pod only starts receiving traffic after its readiness probe passes. If the new Pod never passes readiness, the rolling update pauses — it stops replacing old Pods, and your old version keeps serving traffic.

This is the safety net that makes rolling updates safe: a broken new version can't take over the Deployment because it never becomes "ready." The update stalls rather than silently failing.

## What not to probe

Don't wire your readiness probe to an external database. If your database goes down, all your Pods fail readiness simultaneously, all traffic drops — even though the Pods themselves are fine. Your app should handle database outages (return errors, use circuit breakers), not respond by refusing to serve traffic.

Probes should check your app's internal health, not the health of its dependencies.

<!-- RESOURCES -->

- [Kubernetes Docs - Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) -- type: docs, time: 25m
- [Liveness Probes are Dangerous](https://srcco.de/posts/kubernetes-liveness-probes-are-dangerous.html) -- type: article, time: 10m
- [Kubernetes Docs - Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Kubernetes 有三种探针用于监控容器健康状态：liveness（是否已损坏、需要重启？）、readiness（是否已准备好接收流量？）和 startup（是否已完成初始化？）。正确配置它们，决定了基础设施是能自愈，还是会在负载下悄然失效。

<!-- ZH_DEEP_DIVE -->
## 三种探针

**存活探针（Liveness probe）** — 回答“这个容器是否已经损坏到需要重启的程度？”如果存活探针连续失败，Kubernetes 会杀死容器并重启它。适用于检测死锁、导致应用无响应的内存泄漏，以及任何“重启就能解决”的状态。

**就绪探针（Readiness probe）** — 回答“这个容器是否已准备好接收流量？”就绪探针失败会将 Pod 从 Service 的端点列表中移除，流量随之停止路由到它。这不是重启——Pod 继续运行，只是在恢复之前收不到流量。适用于表达“我还在初始化”或“我负载过高，请退避”。

**启动探针（Startup probe）** — 回答“这个容器是否已完成启动？”在它通过之前，会阻止存活探针和就绪探针运行。适用于启动缓慢的应用（JVM 服务、启动时加载大型数据集的任何应用）——它能防止存活探针在容器还没来得及启动时就将其杀死。

## 探针类型

三种探针都支持相同的检查机制：

**HTTP GET** — 最常见。Kubernetes 发起 HTTP 请求；任何 2xx 或 3xx 响应都视为健康：

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

**TCP Socket** — 打开一个 TCP 连接；成功意味着端口正在接受连接。适用于非 HTTP 服务：

```yaml
readinessProbe:
  tcpSocket:
    port: 5432
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Exec** — 在容器内运行命令；退出码为 0 即健康：

```yaml
livenessProbe:
  exec:
    command: ["redis-cli", "ping"]
  periodSeconds: 10
```

## 常用配置字段

- `initialDelaySeconds` — 容器启动后等待多久再运行第一次探针
- `periodSeconds` — 探针运行频率（默认：10s）
- `timeoutSeconds` — 等待响应多久后计为失败
- `failureThreshold` — 连续失败多少次后采取行动（存活探针为重启，就绪探针为从 Service 端点移除）
- `successThreshold` — 失败后连续成功多少次才重新视为健康（存活探针和启动探针始终为 1）

## 就绪探针如何与滚动更新集成

在滚动更新期间，Kubernetes 会逐个替换 Pod。新 Pod 只有在就绪探针通过后才开始接收流量。如果新 Pod 始终无法通过就绪检查，滚动更新会暂停——它停止替换旧 Pod，旧版本继续提供流量。

这就是让滚动更新安全的安全网：损坏的新版本无法接管 Deployment，因为它永远不会变为“就绪”。更新会停滞，而不是悄无声息地失败。

## 不要探测什么

不要将就绪探针绑定到外部数据库。如果数据库宕机，所有 Pod 会同时就绪失败，所有流量都会中断——即使 Pod 本身完好无损。你的应用应该处理数据库故障（返回错误、使用熔断器），而不是以拒绝提供流量的方式响应。

探针应检查应用的内部健康状况，而不是其依赖项的健康状况。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 配置 Liveness、Readiness 和 Startup 探针](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) -- 类型: 文档, 时间: 25m
- [Liveness 探针很危险](https://srcco.de/posts/kubernetes-liveness-probes-are-dangerous.html) -- 类型: 文章, 时间: 10m
- [Kubernetes 文档 - Pod 生命周期](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 为 Pod 添加就绪探针，并验证启动期间该 Pod 会从 Service 端点中移除
2. 添加存活探针，观察 Kubernetes 重启停止响应的 Pod
3. 理解何时应使用启动探针而非较长的 initialDelaySeconds
4. 解释区别：存活探针（是否已故障？）与就绪探针（是否已准备好接收流量？）
5. 观察当新 Pod 未通过就绪探针时，滚动更新会发生什么
6. 探针已配置好。现在如何用稳定端点暴露我的 Pod？
7. 我的探针已配置好，Kubernetes 知道我的 Pod 何时健康。但流量实际如何到达我的 Pod？它们每次重启 IP 都会变——我需要一个稳定、可指向 DNS 的东西，能自动找到健康的 Pod。
