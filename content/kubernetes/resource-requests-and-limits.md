---
id: resource-requests-and-limits
title: Resource Requests and Limits
zone: kubernetes
edges:
  to:
    - id: autoscaling
      question: >-
        Resources are defined. Now I want Kubernetes to scale my Pods
        automatically based on those metrics.
      detail: >-
        I've set requests and limits so Kubernetes knows what each Pod needs.
        But when traffic spikes I'd still have to manually bump the replica
        count. Is there a way for the cluster to just figure out 'there's more
        load, spin up more Pods' on its own — without me having to watch it?
difficulty: 2
tags:
  - kubernetes
  - resource-requests
  - resource-limits
  - qos
  - scheduling
  - hpa
  - k8s
category: practice
milestones:
  - >-
    Set CPU and memory requests and limits on a Pod and observe where the
    scheduler places it
  - >-
    Understand the three QoS classes: Guaranteed, Burstable, BestEffort — and
    which gets evicted first
  - >-
    Deliberately exhaust a node's memory and watch BestEffort Pods get evicted
    first
  - Explain why requests affect scheduling while limits affect runtime behaviour
  - 'Know the rule of thumb: always set requests, set limits carefully'
title_zh: "资源请求与限制"

---


Resource requests tell the Kubernetes scheduler how much CPU and memory a Pod needs — the scheduler uses this to decide which node to place it on. Limits cap what a Pod can actually consume at runtime. Getting this right is a prerequisite for both reliable scheduling and for autoscaling to work correctly.

<!-- DEEP_DIVE -->

## Requests vs limits

**Requests** — what the Pod is *guaranteed*. The scheduler only places a Pod on a node that has enough unallocated capacity to satisfy the request. The Pod always gets at least what it requests.

**Limits** — the maximum the Pod can use at runtime. If a container tries to exceed its CPU limit, it's throttled. If it tries to exceed its memory limit, it's killed with an OOMKill.

```yaml
resources:
  requests:
    cpu: "250m"      # 250 millicores = 0.25 CPUs
    memory: "256Mi"
  limits:
    cpu: "1"         # 1 full CPU
    memory: "512Mi"
```

CPU is expressed in cores or millicores (`1000m` = 1 core). Memory uses binary SI suffixes: `Ki`, `Mi`, `Gi`.

## How scheduling uses requests

When you create a Pod, the scheduler looks at every node and finds one where:

- The sum of all Pod CPU requests doesn't exceed the node's allocatable CPU capacity
- The sum of all Pod memory requests doesn't exceed the node's allocatable memory capacity

It ignores actual current usage — only committed requests matter for scheduling decisions. A node that's physically "busy" but has unallocated request headroom will happily accept more Pods. A node with plenty of actual headroom but fully committed requests will refuse them.

This is why accurate requests matter. Set them too low and your Pods get scheduled onto already-overloaded nodes. Set them too high and your nodes are under-utilized while Pods sit in `Pending`.

## QoS classes

Kubernetes assigns each Pod a Quality of Service class based on how requests and limits are configured. This determines eviction order when a node runs out of memory:

**Guaranteed** — requests equal limits for every container in the Pod. These Pods have the highest priority and are evicted last. Good for latency-sensitive production workloads.

**Burstable** — at least one container has a request set, but requests don't equal limits. Most Pods land here. They can burst above their requests when capacity is available.

**BestEffort** — no requests or limits set at all. These Pods are the first to be evicted when a node runs out of memory. Never run production workloads without resource requests.

## The CPU limits debate

Setting CPU limits is controversial in the Kubernetes community. The problem: a container that hits its CPU limit gets throttled by the Linux kernel's CFS scheduler — even if the node has spare CPU capacity available. This causes latency spikes that aren't visible from CPU utilization metrics.

Many teams set CPU requests but not CPU limits, accepting the risk of "noisy neighbor" effects in exchange for avoiding unnecessary throttling. If you do set CPU limits, set them well above the request and monitor for throttling with `container_cpu_cfs_throttled_seconds_total` in Prometheus.

Memory limits are different and should always be set — a container that exceeds its memory limit is killed immediately (OOMKill), which is a hard failure you want to scope and control.

## Practical rule of thumb

- **Always set memory requests and limits** — required for scheduling, prevents OOM cascades
- **Always set CPU requests** — required for autoscaling, affects where Pods land
- **Set CPU limits cautiously** — test under real load and watch for throttling before enforcing them

<!-- RESOURCES -->

- [Kubernetes Docs - Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) -- type: docs, time: 25m
- [Kubernetes Docs - Pod Quality of Service](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) -- type: docs, time: 15m
- [For the Love of God, Stop Using CPU Limits on Kubernetes](https://home.robusta.dev/blog/stop-using-cpu-limits) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
资源请求（requests）告诉 Kubernetes 调度器一个 Pod 需要多少 CPU 和内存——调度器据此决定将 Pod 放置在哪个节点上。限制（limits）则限定 Pod 在运行时实际可以消耗的资源上限。正确设置这两者是实现可靠调度以及让自动扩缩容正常工作的前提条件。

<!-- ZH_DEEP_DIVE -->
## Requests 与 limits

**Requests** — Pod 被*保证*获得的资源量。调度器只会把 Pod 放到未分配容量足以满足其 request 的节点上。Pod 至少能获得它所请求的资源量。

**Limits** — Pod 在运行时可以使用的最大资源量。如果容器试图超过其 CPU limit，就会被限流(throttled)。如果试图超过其内存 limit，就会被 OOMKill 杀死。

```yaml
resources:
  requests:
    cpu: "250m"      # 250 millicores = 0.25 CPUs
    memory: "256Mi"
  limits:
    cpu: "1"         # 1 full CPU
    memory: "512Mi"
```

CPU 以核(core)或毫核(millicore)表示(`1000m` = 1 核)。内存使用二进制 SI 后缀:`Ki`、`Mi`、`Gi`。

## 调度如何使用 requests

创建 Pod 时,调度器会检查每个节点,找到一个满足以下条件的节点:

- 所有 Pod 的 CPU request 之和不超过该节点的可分配 CPU 容量
- 所有 Pod 的内存 request 之和不超过该节点的可分配内存容量

它忽略当前的实际使用量 — 只有已承诺的 request 才影响调度决策。一个物理上"繁忙"但仍有未分配 request 余量的节点会欣然接受更多 Pod。一个实际余量充足但 request 已完全承诺的节点则会拒绝它们。

这就是准确的 requests 很重要的原因。设置得太低,Pod 会被调度到已经过载的节点上。设置得太高,节点利用率不足,而 Pod 却停留在 `Pending` 状态。

## QoS 类别

Kubernetes 会根据 requests 和 limits 的配置方式,为每个 Pod 分配一个服务质量(QoS)类别。这决定了节点内存耗尽时的驱逐顺序:

**Guaranteed** — Pod 中每个容器的 requests 都等于 limits。这些 Pod 优先级最高,最后被驱逐。适合对延迟敏感的生产工作负载。

**Burstable** — 至少有一个容器设置了 request,但 requests 不等于 limits。大多数 Pod 属于这一类。当有可用容量时,它们可以突发到超过其 requests。

**BestEffort** — 完全没有设置 requests 或 limits。当节点内存耗尽时,这些 Pod 最先被驱逐。绝不要在没有资源 requests 的情况下运行生产工作负载。

## CPU limits 之争

设置 CPU limits 在 Kubernetes 社区中存在争议。问题在于:达到 CPU limit 的容器会被 Linux 内核的 CFS 调度器限流 — 即使节点还有空闲的 CPU 容量可用。这会导致延迟尖峰,而这些尖峰从 CPU 利用率指标中看不出来。

许多团队只设置 CPU requests 而不设置 CPU limits,接受"吵闹邻居"效应的风险,以换取避免不必要的限流。如果你确实要设置 CPU limits,请将它们设置得远高于 request,并用 Prometheus 中的 `container_cpu_cfs_throttled_seconds_total` 监控限流情况。

内存 limits 则不同,应当始终设置 — 超过内存 limit 的容器会被立即杀死(OOMKill),这是一种硬失败,你需要界定并控制其影响范围。

## 实用经验法则

- **始终设置内存 requests 和 limits** — 调度所必需,可防止 OOM 级联
- **始终设置 CPU requests** — 自动扩缩容所必需,影响 Pod 的落点
- **谨慎设置 CPU limits** — 在真实负载下测试并观察限流情况后再启用

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Pod 与容器的资源管理](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) -- 类型：文档，时长：25 分钟
- [Kubernetes 文档 - Pod 服务质量](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) -- 类型：文档，时长：15 分钟
- [看在上帝的份上，别再在 Kubernetes 上使用 CPU Limits 了](https://home.robusta.dev/blog/stop-using-cpu-limits) -- 类型：文章，时长：10 分钟

<!-- ZH_UI -->
1. 为 Pod 设置 CPU 和内存的 requests 与 limits，并观察调度器将其调度到何处
2. 理解三种 QoS 类别：Guaranteed、Burstable、BestEffort——以及哪种会最先被驱逐
3. 故意耗尽节点内存，观察 BestEffort Pod 最先被驱逐
4. 解释为什么 requests 影响调度，而 limits 影响运行时行为
5. 掌握经验法则：始终设置 requests，谨慎设置 limits
6. 资源已定义。现在我希望 Kubernetes 基于这些指标自动扩缩我的 Pod。
7. 我已设置 requests 和 limits，让 Kubernetes 知道每个 Pod 需要什么。但流量激增时我仍得手动调高副本数。有没有办法让集群自己判断“负载增加了，多启动一些 Pod”——而无需我盯着它？
