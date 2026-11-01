---
id: pod-scheduling-spread
title: 'Pod Affinity, Anti-Affinity, and Spread'
zone: kubernetes-production
edges:
  to:
    - id: pod-disruption-budgets
      question: >-
        My pods are spread across nodes. But can Kubernetes still drain all of
        them at once during an upgrade and cause an outage anyway?
      detail: >-
        I've set up topology spread so replicas land on different nodes. But if
        Kubernetes decides to drain three nodes simultaneously for a version
        upgrade, I'd still lose everything. Is there a way to tell it how many
        pods it's allowed to take down at a time?
difficulty: 3
tags:
  - kubernetes
  - affinity
  - anti-affinity
  - topology
  - spread
  - scheduling
  - k8s
  - production
category: practice
milestones:
  - >-
    Understand why two replicas on the same node gives you false confidence in
    availability
  - >-
    Know how anti-affinity rules prevent replicas from co-locating on the same
    node or zone
  - >-
    Use topologySpreadConstraints as the modern, flexible approach to spreading
    pods
  - >-
    Use node affinity to pin workloads to specific pools (e.g. GPU jobs to GPU
    nodes)
  - >-
    Know the difference between required (hard) and preferred (best-effort)
    constraints
title_zh: "Pod 亲和性、反亲和性与分布"

---


Running three replicas of your app is false confidence if all three are on the same node. One node failure — hardware failure, node drain, cloud provider maintenance — takes all three down at once. You need the scheduler to actively spread pods across failure domains: different nodes, different availability zones.

<!-- DEEP_DIVE -->

## The false safety illusion

A Deployment with 3 replicas gives you redundancy — unless the scheduler decides to place all three on the same node, which it can do by default. The scheduler optimizes for bin-packing efficiency, not fault tolerance. Without explicit constraints, replicas frequently co-locate.

## Pod anti-affinity

Pod anti-affinity tells the scheduler to avoid placing a pod on a node that already has a pod matching a given selector.

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: my-api
        topologyKey: kubernetes.io/hostname
```

`requiredDuringScheduling` means this is a hard requirement. If no node exists that satisfies the anti-affinity rule, the pod will not schedule. This can cause pods to be unschedulable if your cluster is small — if you have 3 replicas required to be on 3 different nodes but only have 2 nodes, one pod will remain pending.

`preferredDuringScheduling` is a soft requirement: the scheduler tries to satisfy it but will co-locate if there's no other option.

## topologySpreadConstraints

The modern, more flexible approach. Instead of "don't put pods together," it says "distribute pods evenly across this topology key":

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: my-api
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: my-api
```

`maxSkew: 1` means the difference between the most-loaded and least-loaded topology domain is at most 1. This ensures balanced distribution rather than just co-location avoidance.

`whenUnsatisfiable: DoNotSchedule` makes it a hard requirement. `ScheduleAnyway` makes it a best-effort. Mix them: hard constraint on hostname (spread across nodes), soft constraint on zone (spread across zones when possible but don't block scheduling if you only have nodes in one zone).

## Spreading across availability zones

Spreading across nodes protects you against node failures. Spreading across availability zones protects you against AZ failures — which happen more often than you'd expect (cloud provider incidents frequently affect single AZs).

Use `topology.kubernetes.io/zone` as the topology key in a second spread constraint. Your cluster needs nodes in multiple zones for this to work.

## Node affinity for pool targeting

If you want a workload to land on a specific node pool (e.g., only on high-memory nodes, or only on spot nodes), use node affinity:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: cloud.google.com/gke-nodepool
              operator: In
              values:
                - memory-optimized
```

This pins the workload to nodes with that label. Use taints + tolerations alongside node affinity for strict targeting (node affinity selects; taints prevent other workloads from landing there).

## Required vs preferred

**Required** constraints block scheduling if they can't be satisfied. Use for true availability requirements: "I need replicas on different nodes" is a valid hard requirement.

**Preferred** constraints are best-effort. Use when you'd like spreading but don't want it to cause unschedulable pods in edge cases (small clusters, unusual topologies).

A good default: hard constraint on hostname spread, soft constraint on zone spread. This ensures you never co-locate on the same node, but handles the case where your cluster doesn't have nodes in all zones.

<!-- RESOURCES -->

- [Kubernetes Docs - Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) -- type: docs, time: 20m
- [Kubernetes Docs - Assign Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
如果你的应用运行三个副本，但它们都位于同一个节点上，那只是虚假的信心。一次节点故障——硬件故障、节点排空、云提供商维护——就会同时让这三个副本全部宕机。你需要调度器主动将 Pod 分散到不同的故障域：不同节点、不同可用区。

<!-- ZH_DEEP_DIVE -->
## 虚假的安全幻觉

一个拥有 3 个副本的 Deployment 看似提供了冗余——除非调度器决定将三个副本全部放在同一个节点上，而它在默认情况下确实可能这样做。调度器优化的是装箱效率，而非容错能力。在没有显式约束的情况下，副本经常会共置在同一节点上。

## Pod 反亲和性

Pod 反亲和性告诉调度器避免将 Pod 放置到已经存在匹配给定选择器的 Pod 的节点上。

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: my-api
        topologyKey: kubernetes.io/hostname
```

`requiredDuringScheduling` 表示这是硬性要求。如果不存在满足反亲和规则的节点，Pod 将无法调度。如果你的集群规模较小，这可能导致 Pod 无法调度——例如你需要 3 个副本分布在 3 个不同节点上，但只有 2 个节点，那么其中一个 Pod 将一直处于 Pending 状态。

`preferredDuringScheduling` 是软性要求：调度器会尽量满足，但如果没有其他选择，仍会允许共置。

## topologySpreadConstraints

这是更现代、更灵活的方式。它不表达"不要把 Pod 放在一起"，而是说"将 Pod 均匀分布到该拓扑键上"：

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: my-api
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: my-api
```

`maxSkew: 1` 表示负载最高与负载最低的拓扑域之间的差值最多为 1。这确保了均衡分布，而不仅仅是避免共置。

`whenUnsatisfiable: DoNotSchedule` 使其成为硬性要求。`ScheduleAnyway` 则使其成为尽力而为。可以将两者混用：对 hostname 使用硬约束（跨节点分布），对 zone 使用软约束（尽可能跨可用区分布，但如果只有一个可用区的节点，也不要阻塞调度）。

## 跨可用区分布

跨节点分布可以保护你免受节点故障的影响。跨可用区分布则可以保护你免受可用区故障的影响——而可用区故障发生的频率比你想象的要高（云厂商事故经常影响单个可用区）。

在第二个分布约束中使用 `topology.kubernetes.io/zone` 作为拓扑键。这需要你的集群在多个可用区中都有节点才能生效。

## 用于节点池定向的节点亲和性

如果你希望工作负载落在特定的节点池上（例如仅落在高内存节点上，或仅落在 spot 节点上），请使用节点亲和性：

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: cloud.google.com/gke-nodepool
              operator: In
              values:
                - memory-optimized
```

这将工作负载固定到具有该标签的节点上。将 taints + tolerations 与节点亲和性配合使用以实现严格的定向（节点亲和性负责选择；taints 防止其他工作负载落到那里）。

## Required 与 preferred

**Required** 约束在无法满足时会阻塞调度。用于真正的可用性需求："我需要副本分布在不同节点上"是一个合理的硬性要求。

**Preferred** 约束是尽力而为的。当你希望分布但又不希望在边缘情况（小集群、特殊拓扑）下导致 Pod 无法调度时使用。

一个好的默认配置：对 hostname 分布使用硬约束，对 zone 分布使用软约束。这确保你永远不会在同一节点上共置，同时也能处理集群并非在所有可用区都有节点的情况。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 拓扑分布约束](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) -- 类型：文档，时长：20m
- [Kubernetes 文档 - 将 Pod 分配到节点](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) -- 类型：文档，时长：20m

<!-- ZH_UI -->
1. 理解为什么同一节点上的两个副本会让你对可用性产生虚假信心
2. 了解反亲和性规则如何防止副本共置于同一节点或区域
3. 使用 topologySpreadConstraints 作为现代、灵活的 Pod 分布方式
4. 使用节点亲和性将工作负载固定到特定节点池（例如将 GPU 作业固定到 GPU 节点）
5. 了解 required（硬性）与 preferred（尽力而为）约束之间的区别
6. 我的 Pod 已分布到不同节点。但 Kubernetes 在升级期间仍可能一次性驱逐所有 Pod 并导致服务中断吗？
7. 我已配置拓扑分布，使副本落在不同节点上。但如果 Kubernetes 决定为版本升级同时驱逐三个节点，我仍会失去一切。有没有办法告诉它一次最多允许下线多少个 Pod？
