---
id: resource-requests-limits
title: Resource Requests and Limits
zone: kubernetes-production
edges:
  to:
    - id: hpa-vpa
      question: >-
        Setting static requests worked. But what if my traffic spikes — can the
        cluster adjust automatically?
      detail: >-
        My requests and limits are set and scheduling is working. But my traffic
        is unpredictable — sometimes I need 2 replicas, sometimes 20. I don't
        want to pre-provision for peak if I'm paying for idle capacity most of
        the time.
    - id: health-checks-k8s
      question: >-
        Resources are set. But how does Kubernetes actually know if my app is
        healthy and ready to serve traffic?
      detail: >-
        I've set my resource requests so the scheduler can place pods. But a pod
        could be Running while my app is still initializing or silently broken.
        How does Kubernetes know the difference between a pod that's started and
        one that's actually ready?
difficulty: 3
tags:
  - kubernetes
  - resources
  - requests
  - limits
  - qos
  - oom
  - cpu-throttling
  - k8s
  - production
category: concept
milestones:
  - >-
    Understand the difference: requests are for scheduling, limits are for
    runtime enforcement
  - Know why CPU throttling and memory OOM kill are different failure modes
  - >-
    Understand QoS classes: Guaranteed, Burstable, BestEffort — and which gets
    evicted first
  - >-
    Know why 'no limits' is dangerous and why limits set too tight are also
    dangerous
  - >-
    Understand how resource requests feed directly into node autoscaling
    decisions
title_zh: "资源请求与限制"

---


Resource requests and limits are two separate things that solve two separate problems. Requests tell the scheduler where a pod can fit. Limits enforce a ceiling at runtime. Getting either wrong causes subtle failures that are hard to debug under load.

<!-- DEEP_DIVE -->

## Requests vs limits

**Requests** — what the scheduler uses to decide which node can host the pod. If a node has 2 vCPU of unallocated capacity and your pod requests 3 vCPU, the pod won't schedule there, even if the node's actual CPU usage is 0.5 vCPU. Requests are guarantees from the cluster to the pod.

**Limits** — the hard ceiling enforced at runtime. The container cannot use more than the limit. What happens when it hits the limit is different for CPU vs memory.

## CPU throttling vs OOM kill — a critical difference

**CPU** — when a container exceeds its CPU limit, it gets throttled. The kernel slows it down. The process keeps running, but slower. You'll see increased latency without knowing why. This is especially painful for latency-sensitive applications.

**Memory** — when a container exceeds its memory limit, the kernel kills the process immediately with OOMKill. The pod restarts. You'll see `OOMKilled` in `kubectl describe pod`.

This asymmetry matters for how you set limits:
- CPU limits set too tight → invisible latency degradation
- Memory limits set too tight → pod crashes under load

The controversial opinion: some teams don't set CPU limits at all (to avoid throttling) and rely only on requests for scheduling. This is defensible on dedicated node pools where noisy neighbor isn't a concern.

## QoS classes

Kubernetes assigns one of three QoS classes based on how requests and limits are configured:

**Guaranteed** — requests = limits for both CPU and memory. The pod gets exactly what it asked for, never less. Last to be evicted when a node runs low on resources.

**Burstable** — requests set but limits either not set or different from requests. Can burst above requests if capacity is available. Evicted after BestEffort pods when nodes are under pressure.

**BestEffort** — no requests or limits set at all. Gets whatever's left over. First to be evicted when the node needs resources.

For production workloads: aim for Guaranteed or Burstable. BestEffort pods are unpredictable under node resource pressure.

## Common mistakes

**No limits at all** — a pod that leaks memory or has a bug can consume the entire node's memory and start evicting everything else. Always set memory limits.

**Requests = 0** — the scheduler thinks the pod needs nothing. It packs pods onto nodes until they're starved. Everything slows down together and you don't know why.

**Limits set dramatically higher than requests** — the scheduler sees light load but nodes are actually saturated. The autoscaler won't provision new nodes because it thinks capacity is fine.

**Copy-pasted requests from examples** — "512m CPU, 256Mi memory" is in every tutorial. Whether it's right for your app requires measurement, not guessing.

## Finding the right values

You need to measure, not guess. Ways to do it:

- Run your app under realistic load and watch `kubectl top pods`
- Use VPA in `Off` mode — it observes resource usage and produces recommendations without changing anything
- Check `container_memory_working_set_bytes` in Prometheus to see actual memory consumption

Set requests to roughly your app's average usage, and limits to your app's expected peak. Leave some headroom so you're not right at the limit under normal load.

## How requests feed autoscaling

The node autoscaler provisions nodes based on pending pods whose requests don't fit. If you set requests too low, the autoscaler underestimates load and won't provision nodes until CPUs are already saturated at the kernel level. If you set requests too high, nodes are underutilized and autoscaling is sluggish.

Accurate requests = accurate autoscaling.

<!-- RESOURCES -->

- [Kubernetes Docs - Resource Requests and Limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) -- type: docs, time: 25m
- [Kubernetes Docs - Pod Quality of Service](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
资源请求和限制是两件独立的事情，解决两个独立的问题。请求告诉调度器 Pod 可以放在哪里。限制在运行时强制执行上限。任何一项设置错误都会导致微妙的故障，在高负载下很难调试。

<!-- ZH_DEEP_DIVE -->
## Requests 与 limits

**Requests** — 调度器用来决定哪个节点可以承载 Pod 的依据。如果节点有 2 vCPU 的未分配容量，而你的 Pod 请求 3 vCPU，那么该 Pod 不会被调度到那里，即使节点的实际 CPU 使用率只有 0.5 vCPU。Requests 是集群对 Pod 的保证。

**Limits** — 运行时强制执行的硬性上限。容器不能使用超过 limit 的资源。达到 limit 时会发生什么，CPU 和内存有所不同。

## CPU 限流 vs OOM kill —— 一个关键差异

**CPU** — 当容器超过其 CPU limit 时，会被限流。内核会减慢它的速度。进程继续运行，但变慢了。你会看到延迟增加却不知道原因。这对延迟敏感型应用尤其痛苦。

**内存** — 当容器超过其内存 limit 时，内核会立即通过 OOMKill 杀死进程。Pod 会重启。你会在 `kubectl describe pod` 中看到 `OOMKilled`。

这种不对称性对你如何设置 limit 很重要：
- CPU limit 设得太紧 → 不可见的延迟退化
- 内存 limit 设得太紧 → 负载下 Pod 崩溃

有争议的观点：一些团队完全不设置 CPU limit（以避免限流），仅依靠 requests 进行调度。在专用节点池上，如果不存在 noisy neighbor 问题，这是站得住脚的。

## QoS 类别

Kubernetes 根据 requests 和 limits 的配置方式分配三种 QoS 类别之一：

**Guaranteed** — CPU 和内存的 requests = limits。Pod 获得它请求的确切资源，绝不会更少。当节点资源不足时，最后被驱逐。

**Burstable** — 设置了 requests，但 limits 未设置或与 requests 不同。如果有可用容量，可以突发超过 requests。当节点承压时，在 BestEffort Pod 之后被驱逐。

**BestEffort** — 完全未设置 requests 或 limits。获得剩余的资源。当节点需要资源时，最先被驱逐。

对于生产工作负载：目标是 Guaranteed 或 Burstable。BestEffort Pod 在节点资源压力下不可预测。

## 常见错误

**完全不设 limits** — 一个内存泄漏或有 bug 的 Pod 可以消耗整个节点的内存，并开始驱逐其他所有东西。始终设置内存 limits。

**Requests = 0** — 调度器认为该 Pod 不需要任何资源。它把 Pod 塞到节点上，直到它们被耗尽。所有东西一起变慢，而你却不知道原因。

**Limits 设置得远高于 requests** — 调度器看到负载很轻，但节点实际上已经饱和。自动扩缩器不会配置新节点，因为它认为容量没问题。

**从示例中复制粘贴 requests** — “512m CPU, 256Mi memory” 出现在每个教程中。它是否适合你的应用需要测量，而不是猜测。

## 找到合适的值

你需要测量，而不是猜测。方法如下：

- 在真实负载下运行你的应用，并观察 `kubectl top pods`
- 以 `Off` 模式使用 VPA —— 它观察资源使用情况并生成建议，而不改变任何东西
- 在 Prometheus 中检查 `container_memory_working_set_bytes` 以查看实际内存消耗

将 requests 设置为你应用的大致平均使用量，将 limits 设置为应用的预期峰值。留一些余量，这样在正常负载下你不会正好处于 limit 上。

## Requests 如何影响自动扩缩

节点自动扩缩器根据 requests 无法容纳的待调度 Pod 来配置节点。如果你把 requests 设得太低，自动扩缩器会低估负载，直到 CPU 在内核层面已经饱和才会配置节点。如果你把 requests 设得太高，节点会利用不足，自动扩缩会变得迟缓。

准确的 requests = 准确的自动扩缩。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 资源请求与限制](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) -- 类型：文档，时长：25 分钟
- [Kubernetes 文档 - Pod 服务质量](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 理解区别：requests 用于调度，limits 用于运行时强制限制
2. 了解为什么 CPU 节流和内存 OOM kill 是不同的故障模式
3. 理解 QoS 类别：Guaranteed、Burstable、BestEffort——以及哪个会最先被驱逐
4. 了解为什么“不设 limits”很危险，以及 limits 设得太紧同样危险
5. 理解资源 requests 如何直接影响节点自动扩缩容决策
6. 设置静态 requests 可行。但如果流量激增——集群能自动调整吗？
7. 我的 requests 和 limits 已设置，调度也正常。但流量不可预测——有时需要 2 个副本，有时需要 20 个。大部分时间都在为闲置容量付费，我不想为峰值预置资源。
8. 资源已设置。但 Kubernetes 如何真正知道我的应用是否健康、是否已准备好接收流量？
9. 我已设置资源 requests，调度器可以放置 Pod。但 Pod 可能处于 Running 状态，而我的应用仍在初始化或已静默故障。Kubernetes 如何区分一个已启动的 Pod 和一个真正就绪的 Pod？
