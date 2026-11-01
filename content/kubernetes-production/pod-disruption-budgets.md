---
id: pod-disruption-budgets
title: Pod Disruption Budgets
zone: kubernetes-production
edges:
  to:
    - id: you-cant-debug-what-you-cant-see
      zone: observability
      question: >-
        My cluster handles disruptions gracefully now. But when something
        does go wrong, I'm still flying blind — I have no idea what's
        happening inside my services.
      detail: >-
        The infrastructure is solid. Pods survive node drains, autoscaling
        works, deploys are safe. But last week a service started returning
        errors and I had nothing — no logs I could search, no metrics to
        look at, no way to tell which request was failing or why. I need
        to actually see what's going on inside these things.
difficulty: 3
tags:
  - kubernetes
  - pdb
  - disruption
  - availability
  - draining
  - autoscaler
  - k8s
  - production
category: concept
milestones:
  - Understand voluntary vs involuntary disruptions
  - Know what a PDB tells the cluster and why it matters during node drains
  - >-
    Understand the danger: Cluster Autoscaler + no PDB = all pods evicted
    simultaneously
  - Know the difference between minAvailable and maxUnavailable
title_zh: "Pod 中断预算"

---


A PodDisruptionBudget tells Kubernetes how many pods of a given workload it's allowed to evict at once during voluntary operations. Without one, a node drain or cluster autoscaler scale-down can evict all your pods simultaneously — turning a routine maintenance operation into an outage.

<!-- DEEP_DIVE -->

## Voluntary vs involuntary disruptions

**Involuntary disruptions** are things Kubernetes can't prevent: hardware failure, kernel panic, the cloud provider deleting your node. PDBs don't help with these — there's nothing to coordinate.

**Voluntary disruptions** are controlled operations: `kubectl drain` for node maintenance, the cluster autoscaler consolidating underutilized nodes, rolling updates, and cluster upgrades. These are operations that *ask* the cluster to evict pods, and the cluster can honor a PDB before proceeding.

PDBs protect against voluntary disruptions. They're the mechanism that turns "drain this node immediately" into "drain this node, but respect my availability guarantees."

## What a PDB looks like

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-api
```

This says: when any voluntary disruption targets pods matching `app: my-api`, ensure at least 2 are available at all times. If evicting a pod would drop below 2, the drain pauses and waits until the pod is replaced and healthy before evicting another.

## minAvailable vs maxUnavailable

**minAvailable** — the minimum number (or percentage) of pods that must be available.

```yaml
minAvailable: 2     # absolute number
minAvailable: "50%" # at least half must be available
```

**maxUnavailable** — the maximum number (or percentage) of pods that can be unavailable simultaneously.

```yaml
maxUnavailable: 1     # at most one down at a time
maxUnavailable: "25%" # at most a quarter unavailable
```

Use `minAvailable` when you care about a hard floor. Use `maxUnavailable` when you're thinking about how much disruption you can absorb as a fraction of your fleet.

## The Cluster Autoscaler problem

Without a PDB, when the cluster autoscaler decides to consolidate nodes, it evicts all pods on those nodes in parallel. If your 3 replicas happen to be on 2 nodes being consolidated simultaneously, all 3 evictions can fire at once.

With a PDB of `minAvailable: 2`, the autoscaler evicts one pod, waits for a replacement to become available and healthy, then evicts another. The autoscaler is a well-behaved voluntary disruptor that respects PDBs.

This is the single most important reason to set PDBs: it makes your service immune to autoscaler-driven consolidation causing availability gaps.

## The trap with single replicas

A PDB of `minAvailable: 1` with only 1 replica means the PDB *blocks all drains*. You can't drain the node the pod is on because evicting the pod would drop below `minAvailable: 1`. The node drain will hang indefinitely waiting for a pod that will never be replaced while the original is still there.

If you run a single replica and need drains to succeed, either:
- Remove the PDB (accept the downtime)
- Use `maxUnavailable: 1` instead of `minAvailable` — this allows eviction even for single-replica workloads
- Increase replicas to at least 2

## Pairing with topologySpreadConstraints

A PDB ensures Kubernetes evicts pods gradually. topologySpreadConstraints ensure those pods are spread across nodes and zones so they're not all on the same node to begin with. Together they're the complete answer to "how do I survive a node going away?"

PDB alone: your 3 pods are all on node A, node A is drained, PDB allows 1 eviction at a time — but there's nowhere to move them until the drain is done and a new node is provisioned.

PDB + spread: your pods are on nodes A, B, and C. Node A is drained. The pod on A is evicted (PDB allows it; 2 remain available). A new pod schedules on node D. Nothing went down.

<!-- RESOURCES -->

- [Kubernetes Docs - Pod Disruption Budgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) -- type: docs, time: 20m
- [Kubernetes Docs - Specifying a Disruption Budget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
PodDisruptionBudget 告诉 Kubernetes 在自愿操作期间，允许一次性驱逐某个工作负载的多少个 Pod。如果没有 PDB，节点排空或集群自动扩缩容缩容可能会同时驱逐你的所有 Pod——把一次例行维护操作变成一次故障。

<!-- ZH_DEEP_DIVE -->
## 自愿中断与非自愿中断

**非自愿中断**是 Kubernetes 无法阻止的情况：硬件故障、内核 panic、云提供商删除你的节点。PDB 对这些情况无能为力——没有什么可协调的。

**自愿中断**是受控操作：节点维护时的 `kubectl drain`、集群自动扩缩器合并利用率不足的节点、滚动更新以及集群升级。这些操作会*请求*集群驱逐 Pod，而集群可以在继续之前遵守 PDB。

PDB 用于防范自愿中断。它们是将“立即 drain 此节点”转变为“drain 此节点，但请遵守我的可用性保证”的机制。

## PDB 的样子

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-api
```

这表示：当任何自愿中断针对匹配 `app: my-api` 的 Pod 时，确保始终至少有 2 个可用。如果驱逐某个 Pod 会导致可用数量低于 2，drain 就会暂停，等待该 Pod 被替换并恢复健康后，再驱逐下一个。

## minAvailable 与 maxUnavailable

**minAvailable** —— 必须保持可用的 Pod 最小数量（或百分比）。

```yaml
minAvailable: 2     # 绝对数量
minAvailable: "50%" # 至少一半必须可用
```

**maxUnavailable** —— 可以同时不可用的 Pod 最大数量（或百分比）。

```yaml
maxUnavailable: 1     # 同一时间最多一个不可用
maxUnavailable: "25%" # 最多四分之一不可用
```

当你关心硬性下限时使用 `minAvailable`。当你考虑的是以集群规模的比例来衡量能承受多少中断时，使用 `maxUnavailable`。

## Cluster Autoscaler 的问题

没有 PDB 时，当集群自动扩缩器决定合并节点，它会并行驱逐这些节点上的所有 Pod。如果你的 3 个副本恰好位于同时被合并的 2 个节点上，3 次驱逐可能同时触发。

使用 `minAvailable: 2` 的 PDB 时，自动扩缩器会驱逐一个 Pod，等待替换 Pod 变为可用且健康，然后再驱逐另一个。自动扩缩器是一个行为良好的自愿中断发起者，会遵守 PDB。

这是设置 PDB 最重要的单一原因：它让你的服务免受自动扩缩器驱动的节点合并所导致的可用性缺口影响。

## 单副本的陷阱

`minAvailable: 1` 的 PDB 配合仅 1 个副本，意味着该 PDB *会阻止所有 drain*。你无法 drain 该 Pod 所在的节点，因为驱逐该 Pod 会使可用数量低于 `minAvailable: 1`。节点 drain 将无限期挂起，等待一个永远不会被替换的 Pod（因为原 Pod 仍然存在）。

如果你运行单副本且需要 drain 成功，可以：
- 移除 PDB（接受停机）
- 使用 `maxUnavailable: 1` 代替 `minAvailable` —— 这允许即使是单副本工作负载也能被驱逐
- 将副本数增加到至少 2

## 与 topologySpreadConstraints 配合

PDB 确保 Kubernetes 逐步驱逐 Pod。topologySpreadConstraints 确保这些 Pod 从一开始就分散在不同节点和可用区，而不是全部位于同一节点。两者结合，才是“如何在一个节点消失时存活下来”的完整答案。

仅有 PDB：你的 3 个 Pod 全在节点 A 上，节点 A 被 drain，PDB 允许一次驱逐 1 个——但在 drain 完成且新节点被配置出来之前，它们无处可去。

PDB + 分散：你的 Pod 位于节点 A、B 和 C 上。节点 A 被 drain。A 上的 Pod 被驱逐（PDB 允许；仍有 2 个可用）。新 Pod 调度到节点 D 上。没有任何服务中断。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Pod 中断预算](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) -- 类型: 文档, 时间: 20m
- [Kubernetes 文档 - 指定中断预算](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 理解自愿中断与非自愿中断的区别
2. 了解 PDB 向集群传达了什么，以及为何在节点排空时至关重要
3. 理解危险：Cluster Autoscaler + 无 PDB = 所有 Pod 同时被驱逐
4. 了解 minAvailable 与 maxUnavailable 的区别
5. 我的集群现在能优雅地处理中断。但一旦真的出问题，我仍然两眼一抹黑——完全不知道服务内部发生了什么。
6. 基础设施很稳固。Pod 能扛过节点排空，自动扩缩容正常，部署也安全。但上周有个服务开始返回错误，我却束手无策——没有可搜索的日志，没有可查看的指标，无法判断哪个请求在失败、为什么失败。我需要真正看清这些服务内部到底在发生什么。
