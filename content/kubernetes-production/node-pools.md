---
id: node-pools
title: Node Pools and Sizing
zone: kubernetes-production
edges:
  to:
    - id: node-autoscaling
      question: >-
        I have my node pools set up — but do I really need to manually decide
        how many nodes to run?
      detail: >-
        Right now I have a fixed number of nodes and I'm constantly either
        over-provisioned and wasting money, or under-provisioned and pods are
        pending. Surely the cluster can figure out how many nodes it needs on
        its own?
    - id: managing-k8s-manifests
      question: >-
        I understand my cluster hardware setup. Now how do I manage the
        workloads that run on it?
      detail: >-
        I've got my node pools sorted out. Now I need to actually define and
        manage all the Kubernetes resources for my apps. I'm not sure how to
        keep deployments, services, and configmaps organized as things get more
        complex.
difficulty: 2
tags:
  - kubernetes
  - node-pools
  - spot
  - on-demand
  - sizing
  - gpu
  - k8s
  - production
category: concept
milestones:
  - Understand what a node pool is and why you'd have more than one
  - Know the tradeoff between spot and on-demand nodes
  - Understand what workloads belong on spot and which must not
  - 'Have a mental model for node sizing: many small vs few large'
title_zh: "节点池与容量规划"

---


A node pool is a group of nodes with the same configuration — same instance type, same OS, same labels. Running all workloads on one pool of identical nodes is simple but wasteful: a CPU-intensive batch job sitting next to a latency-sensitive API on the same node degrades both. Node pools let you match hardware to workload.

<!-- DEEP_DIVE -->

## Why you'd have more than one pool

Different workloads have different resource profiles:

- **Web servers and APIs** — moderate CPU, low memory, many small instances work fine
- **ML training / GPU workloads** — require GPU instances, which cost 10–100x more per hour than CPU instances. You want exactly zero GPU nodes sitting idle.
- **Data processing / Spark** — high memory nodes. Need 128GB+ RAM per node, which isn't available in standard instance families.
- **Spot/preemptible workloads** — batch jobs, CI workers, anything stateless and retryable that can run on 60% cheaper instances that may disappear with 2 minutes' notice

A single pool forces you to choose: provision for your heaviest workload (waste money most of the time) or provision for average (fail during spikes). Multiple pools let you right-size each category.

## Spot and preemptible nodes

Cloud providers offer spare compute at a significant discount — 60–80% off on-demand prices. The catch: they can reclaim the instance with 2 minutes' warning.

**What's safe on spot:**
- Batch jobs with checkpointing
- CI build runners
- Stateless workers that can be restarted
- Dev/staging workloads

**What must not run on spot:**
- Production databases (StatefulSets with persistent data — a sudden node loss = potential data corruption)
- Any stateful workload where restart is disruptive
- Applications that take several minutes to start (they'll be evicted before they're useful)

In practice: mix on-demand nodes for your core production workloads, and spot nodes for everything that can tolerate interruption.

## Node sizing: many small vs few large

**Many small nodes (e.g., 4 vCPU / 16GB RAM):**
- Better blast radius isolation — a node failure takes down fewer pods
- Easier to schedule many small pods
- More nodes means more flexibility in scheduling constraints

**Few large nodes (e.g., 32 vCPU / 128GB RAM):**
- Better bin-packing efficiency — larger scheduling surface per node reduces wasted fractional resources
- Fewer nodes means fewer node management operations (upgrades, drains)
- Some workloads need more resources than a small node can provide

There's no universal answer. Many teams use medium-sized nodes (8–16 vCPU) as a default and add specialized pools for outlier workloads.

## Taints and tolerations

When you add a GPU node pool, you don't want random workloads landing on it (those GPU instances are expensive). Use taints to mark the pool as reserved:

```yaml
# Applied to GPU nodes
kubectl taint nodes <node-name> gpu=true:NoSchedule
```

Only pods with the matching toleration will schedule there:

```yaml
tolerations:
  - key: gpu
    operator: Equal
    value: "true"
    effect: NoSchedule
```

Combined with node affinity (requiring specific node labels), this ensures GPU workloads land on GPU nodes and nothing else does.

<!-- RESOURCES -->

- [Kubernetes Docs - Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) -- type: docs, time: 15m
- [Kubernetes Docs - Assign Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
节点池是一组配置相同的节点——相同的实例类型、相同的操作系统、相同的标签。将所有工作负载运行在一个由相同节点组成的节点池上虽然简单，但会造成浪费：一个 CPU 密集型的批处理任务与一个对延迟敏感的 API 运行在同一节点上，会同时拖累两者。节点池让你能够将硬件与工作负载相匹配。

<!-- ZH_DEEP_DIVE -->
## 为什么需要多个节点池

不同的工作负载有不同的资源需求特征：

- **Web 服务器和 API** — 中等 CPU、低内存，多个小实例即可正常运行
- **ML 训练 / GPU 工作负载** — 需要 GPU 实例，每小时成本比 CPU 实例高 10–100 倍。你希望 GPU 节点空闲数量恰好为零。
- **数据处理 / Spark** — 高内存节点。每节点需要 128GB+ RAM，标准实例族无法提供。
- **Spot/可抢占工作负载** — 批处理任务、CI worker、任何无状态且可重试的任务，可以运行在便宜 60% 的实例上，但这些实例可能在提前 2 分钟通知后被回收

单一节点池会迫使你做出选择：为最重的工作负载预留资源（大多数时候浪费钱），或按平均水平预留（高峰期失败）。多个节点池让你可以为每个类别精确配置资源。

## Spot 和可抢占节点

云厂商以大幅折扣提供闲置算力——比按需价格低 60–80%。代价是：它们可以在提前 2 分钟通知的情况下回收实例。

**适合运行在 spot 上的：**
- 带检查点的批处理任务
- CI 构建 runner
- 可重启的无状态 worker
- 开发/预发工作负载

**绝不能运行在 spot 上的：**
- 生产数据库（带持久化数据的 StatefulSet——节点突然丢失 = 潜在数据损坏）
- 任何重启会造成中断的有状态工作负载
- 启动需要数分钟的应用（它们会在变得有用之前就被驱逐）

实践建议：核心生产工作负载使用按需节点，所有能容忍中断的工作负载使用 spot 节点。

## 节点规格：多个小节点 vs 少量大节点

**多个小节点（例如 4 vCPU / 16GB RAM）：**
- 故障影响范围隔离更好——节点故障影响的 pod 更少
- 更容易调度大量小 pod
- 节点更多意味着调度约束上有更大灵活性

**少量大节点（例如 32 vCPU / 128GB RAM）：**
- 装箱效率更好——每节点更大的调度空间减少碎片化资源浪费
- 节点更少意味着更少的节点管理操作（升级、驱逐）
- 某些工作负载需要的资源超过小节点能提供的量

没有通用答案。许多团队默认使用中等规格节点（8–16 vCPU），并为特殊工作负载添加专用节点池。

## 污点和容忍

当你添加 GPU 节点池时，你不希望随机工作负载落在上面（那些 GPU 实例很贵）。使用污点将该节点池标记为保留：

```yaml
# Applied to GPU nodes
kubectl taint nodes <node-name> gpu=true:NoSchedule
```

只有带有匹配容忍的 pod 才会调度到那里：

```yaml
tolerations:
  - key: gpu
    operator: Equal
    value: "true"
    effect: NoSchedule
```

结合节点亲和性（要求特定节点标签），这确保 GPU 工作负载落在 GPU 节点上，而其他工作负载不会。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 污点与容忍](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) -- 类型：文档，时长：15 分钟
- [Kubernetes 文档 - 将 Pod 分配到节点](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) -- 类型：文档，时长：20 分钟

<!-- ZH_UI -->
1. 理解什么是节点池，以及为什么需要多个节点池
2. 了解竞价节点与按需节点之间的权衡
3. 理解哪些工作负载适合放在竞价节点上，哪些绝对不能
4. 建立节点规格的心智模型：多个小节点 vs 少量大节点
5. 我已经配置好节点池了——但我真的需要手动决定运行多少个节点吗？
6. 目前我的节点数量是固定的，要么过度配置浪费钱，要么配置不足导致 Pod 一直处于 Pending 状态。集群难道不能自己算出需要多少个节点吗？
7. 我理解了集群的硬件配置。接下来该如何管理运行在其上的工作负载？
8. 节点池已经搞定了。现在我需要真正定义和管理应用的所有 Kubernetes 资源。随着复杂度增加，我不确定如何保持 Deployment、Service 和 ConfigMap 的组织有序。
