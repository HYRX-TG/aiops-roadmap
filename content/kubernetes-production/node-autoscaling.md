---
id: node-autoscaling
title: Node Autoscaling
zone: kubernetes-production
edges:
  to:
    - id: managing-k8s-manifests
      question: >-
        My cluster scales automatically. Now how do I manage all the manifests
        for everything I'm deploying on it?
      detail: >-
        The infrastructure takes care of itself, but my YAML files are still a
        mess — different copies for staging and prod, edited by hand. I need a
        proper way to manage and version all of this.
difficulty: 3
tags:
  - kubernetes
  - autoscaling
  - karpenter
  - cluster-autoscaler
  - nodes
  - k8s
  - production
category: concept
milestones:
  - >-
    Understand why accurate resource requests are critical — the autoscaler
    makes bin-packing decisions based on requests, not limits
  - >-
    Know Karpenter's advantages over Cluster Autoscaler: flexible node type
    selection, faster provisioning, bin-packing across instance families
  - >-
    Understand scale-down safety: how PDBs and do-not-evict annotations interact
    with the autoscaler's drain process
  - >-
    Know the overprovisioning pattern: placeholder pause pods that get evicted
    first, giving real workloads a pre-warmed node to land on
  - >-
    Understand spot/preemptible node handling: interruption notices, mixed node
    groups, and safe workload placement
title_zh: "节点自动扩缩容"

---


Node autoscaling watches for pods that can't be scheduled due to insufficient capacity and provisions new nodes automatically — and removes underutilized nodes when they're no longer needed. Without it, you're either over-provisioning (paying for idle nodes) or under-provisioning (pods stuck pending during traffic spikes).

<!-- DEEP_DIVE -->

## How it works

The node autoscaler doesn't watch CPU or memory usage. It watches the scheduler. When a pod can't be placed on any existing node (its resource requests don't fit), the autoscaler provisions a new node. When nodes are underutilized and their pods can be packed elsewhere, it drains and removes them.

This is why accurate resource requests are critical: the autoscaler makes decisions based on what pods *claim* they need, not what they actually use. A pod requesting 4 CPU will hold that scheduling space even if it's only using 0.1 CPU.

## Cluster Autoscaler vs Karpenter

**Cluster Autoscaler** (CA) is the original approach. It works with predefined node groups (AWS ASGs, GKE managed instance groups). When it needs a node, it scales up the appropriate group. It's well-tested and widely used.

Limitations: you configure node groups in advance, so you're picking instance types ahead of time. The autoscaler can only choose from what you've defined.

**Karpenter** (AWS-native, increasingly cross-cloud) takes a different approach: it provisions nodes directly, choosing the best instance type for the pending pods at the moment. If you have pending pods that need 7 vCPU, Karpenter can provision an 8 vCPU instance instead of wasting 8 vCPU because your node group only has 16 vCPU instances.

Karpenter advantages:
- Faster provisioning (doesn't wait for ASG to scale; provisions directly)
- Better bin-packing across many instance families
- Can mix spot and on-demand in a single provisioner configuration
- More flexible node lifecycle (terminates unused nodes faster)

For new AWS deployments, Karpenter is the preferred choice. For GKE and AKS, the managed autoscaler is tightly integrated and well-supported.

## Scale-down safety

The autoscaler will try to drain nodes it considers underutilized. A drain evicts all pods on that node, which means your pods must handle being killed gracefully.

Two mechanisms protect against eviction:

**PodDisruptionBudgets (PDBs)** — the autoscaler respects PDBs during drain. If draining a node would violate a PDB, the autoscaler skips that node. This is why PDBs matter even when you're not manually draining nodes.

**do-not-evict annotations** — `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` on a pod tells the autoscaler to never drain the node that pod is on. Use sparingly; it blocks scale-down.

## The overprovisioning pattern

Cold starts are a problem: the autoscaler provisions a node when pods are already pending. Provisioning a node takes 1–3 minutes. During a traffic spike, your new pods wait.

The overprovisioning pattern: run low-priority "placeholder" pods that consume capacity on fresh nodes. When a real workload pod needs to be scheduled and can't fit, it preempts the placeholder (which has lower priority). The real pod schedules immediately; the autoscaler then provisions a new node to replace the evicted placeholder.

This keeps one node of spare capacity warm, at the cost of paying for that spare capacity continuously.

## Spot node handling

If your node pool includes spot instances, nodes will be reclaimed with 2 minutes' warning. The autoscaler (and Karpenter) can respond to these interruption notices by preemptively migrating workloads.

Best practices for spot:
- Only run interruptible workloads on spot nodes
- Use taints + tolerations to segregate spot from on-demand
- Configure multiple instance types in your spot pool so AWS/GCP has more options to fulfill requests
- Use PDBs to limit how many pods can be evicted during an interruption

<!-- RESOURCES -->

- [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md) -- type: docs, time: 20m
- [Karpenter Documentation](https://karpenter.sh/docs/) -- type: docs, time: 30m
- [Kubernetes Docs - Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
节点自动伸缩会监控因容量不足而无法调度的 Pod，并自动创建新节点；当节点不再被需要时，还会移除利用率不足的节点。如果没有它，你要么过度配置（为闲置节点付费），要么配置不足（流量高峰时 Pod 卡在 pending 状态）。

<!-- ZH_DEEP_DIVE -->
## 工作原理

节点自动扩缩器并不监控 CPU 或内存使用率，而是监控调度器。当某个 Pod 无法被放置到任何现有节点上时（其资源请求无法满足），自动扩缩器就会创建新节点。当节点利用率不足、其上的 Pod 可以被打包到其他地方时，它会驱逐并移除这些节点。

这就是为什么准确的资源请求至关重要：自动扩缩器根据 Pod *声明* 所需的资源来做决策，而不是根据它们实际使用的资源。一个请求 4 CPU 的 Pod 即使只使用了 0.1 CPU，也会一直占用该调度空间。

## Cluster Autoscaler 与 Karpenter

**Cluster Autoscaler**（CA）是最初的方案。它基于预定义的节点组（AWS ASG、GKE 托管实例组）工作。当需要节点时，它会扩容相应的节点组。它经过充分测试并被广泛使用。

局限性：你需要预先配置节点组，因此要提前选定实例类型。自动扩缩器只能从你已定义的选项中选择。

**Karpenter**（AWS 原生，并日益跨云支持）采用了不同的方式：它直接创建节点，在当下为待调度的 Pod 选择最佳实例类型。如果你有待调度的 Pod 需要 7 vCPU，Karpenter 可以创建一个 8 vCPU 的实例，而不是因为你的节点组只有 16 vCPU 的实例而浪费 8 vCPU。

Karpenter 的优势：
- 更快的创建速度（无需等待 ASG 扩容，直接创建）
- 在众多实例族之间实现更好的装箱（bin-packing）
- 可以在单个 provisioner 配置中混合 spot 和 on-demand
- 更灵活的节点生命周期（更快地终止未使用的节点）

对于新的 AWS 部署，Karpenter 是首选。对于 GKE 和 AKS，托管自动扩缩器集成紧密且支持良好。

## 缩容安全性

自动扩缩器会尝试驱逐它认为利用率不足的节点。驱逐会移除该节点上的所有 Pod，这意味着你的 Pod 必须能够优雅地处理被终止的情况。

有两种机制可以防止驱逐：

**PodDisruptionBudgets（PDB）**——自动扩缩器在驱逐期间会遵守 PDB。如果驱逐某个节点会违反 PDB，自动扩缩器就会跳过该节点。这就是为什么即使你不手动驱逐节点，PDB 也很重要。

**do-not-evict 注解**——在 Pod 上设置 `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` 会告诉自动扩缩器永远不要驱逐该 Pod 所在的节点。请谨慎使用；它会阻止缩容。

## 超额配置模式

冷启动是一个问题：自动扩缩器在 Pod 已经处于待调度状态时才创建节点。创建一个节点需要 1–3 分钟。在流量高峰期间，你的新 Pod 需要等待。

超额配置模式：运行低优先级的“占位”Pod，在新节点上占用容量。当真实的工作负载 Pod 需要被调度且无法容纳时，它会抢占占位 Pod（占位 Pod 优先级较低）。真实 Pod 立即被调度；随后自动扩缩器创建一个新节点来替换被驱逐的占位 Pod。

这样可以让一个节点的备用容量保持热备状态，代价是需要持续为这部分备用容量付费。

## Spot 节点处理

如果你的节点池包含 spot 实例，节点会在收到 2 分钟警告后被回收。自动扩缩器（以及 Karpenter）可以响应这些中断通知，提前迁移工作负载。

Spot 的最佳实践：
- 只在 spot 节点上运行可中断的工作负载
- 使用 taints + tolerations 将 spot 与 on-demand 隔离
- 在 spot 池中配置多种实例类型，以便 AWS/GCP 有更多选项来满足请求
- 使用 PDB 限制中断期间可被驱逐的 Pod 数量

<!-- ZH_RESOURCES -->
- [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md) -- 类型：文档，时长：20m
- [Karpenter 文档](https://karpenter.sh/docs/) -- 类型：文档，时长：30m
- [Kubernetes 文档 - Pod 优先级与抢占](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) -- 类型：文档，时长：15m

<!-- ZH_UI -->
1. 理解为何准确的资源请求至关重要——自动扩缩器基于请求而非限制做出装箱决策
2. 了解 Karpenter 相较于 Cluster Autoscaler 的优势：灵活的节点类型选择、更快的供应速度、跨实例族的装箱
3. 理解缩容安全性：PDB 和 do-not-evict 注解如何与自动扩缩器的驱逐流程交互
4. 了解超额配置模式：占位 pause pod 会最先被驱逐，为真实工作负载提供预热好的节点
5. 理解 spot/preemptible 节点处理：中断通知、混合节点组以及安全的工作负载放置
6. 我的集群已能自动扩缩。现在我该如何管理部署在其上的所有清单文件？
7. 基础设施能自我管理，但我的 YAML 文件仍一团糟——staging 和 prod 有不同副本，靠手工编辑。我需要一种规范的方式来管理和版本化这一切。
