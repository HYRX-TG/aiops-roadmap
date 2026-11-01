---
id: daemonsets
title: DaemonSets
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - daemonsets
  - nodes
  - logging
  - monitoring
  - k8s
category: concept
milestones:
  - >-
    Understand what a DaemonSet guarantees: exactly one pod per node,
    automatically added when nodes join and removed when nodes leave
  - >-
    Know the canonical use cases: log collectors, monitoring agents, network
    plugins, storage drivers
  - >-
    Use a node selector or affinity to run a DaemonSet only on a subset of
    nodes (e.g. only GPU nodes, only spot nodes)
  - >-
    Know the update strategies: RollingUpdate (replace pods one at a time) vs
    OnDelete (replace only when you manually delete the old pod)
title_zh: "DaemonSet"

---


A DaemonSet ensures that exactly one copy of a pod runs on every node in the cluster — or on a selected subset of nodes. When a new node joins the cluster, the DaemonSet pod is automatically scheduled there. When a node is removed, that pod is cleaned up. There's no replica count to manage.

<!-- DEEP_DIVE -->

## When to use a DaemonSet

DaemonSets are for node-level infrastructure concerns — software that needs to run everywhere because it's collecting from or providing something to the node itself:

- **Log collectors** (Fluent Bit, Fluentd) — tail container logs from every node and forward them to a central log store
- **Monitoring agents** (Prometheus node-exporter, Datadog agent) — collect node-level metrics: CPU, memory, disk, network
- **Network plugins** (Calico, Cilium, Weave) — implement pod networking and network policy at the kernel level on each node
- **Storage drivers** (CSI node plugins) — mount volumes on nodes where pods need them
- **Security agents** — host-level intrusion detection, vulnerability scanning

For application workloads (your API, your web server), use a Deployment. DaemonSets are for infrastructure that serves the node, not the application.

## Writing a DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:2.2
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
```

The `hostPath` volumes give the DaemonSet pod access to the node's filesystem — typical for log collectors that need to read files the container runtime writes.

## Tolerations and control plane nodes

By default, the Kubernetes control plane has a taint (`node-role.kubernetes.io/control-plane:NoSchedule`) that prevents regular pods from landing there. DaemonSets respect this taint too.

If you need your DaemonSet on control plane nodes as well (some networking plugins do), add a toleration:

```yaml
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

## Running on a subset of nodes

If you only want the DaemonSet on certain nodes — GPU nodes, spot nodes, nodes in a specific pool — use a node selector:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        cloud.google.com/gke-nodepool: gpu-pool
```

Or use node affinity for more expressive rules. The DaemonSet will only schedule pods on nodes whose labels match.

## Update strategy

DaemonSets support two update strategies:

**RollingUpdate** (default) — replaces DaemonSet pods one at a time across nodes, respecting `maxUnavailable`. Use this for most workloads.

**OnDelete** — Kubernetes only creates the new pod template on a node after you manually delete the existing DaemonSet pod on that node. Useful when you need explicit control over when each node gets updated (e.g., infrastructure components where you want to validate each node before proceeding).

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

## Difference from a Deployment

The key distinction: a Deployment manages a desired replica count across available nodes. A DaemonSet doesn't have a replica count — it has a desired state of "one pod per matching node." As your cluster grows or shrinks, the DaemonSet adjusts automatically without any configuration changes.

<!-- RESOURCES -->

- [Kubernetes Docs - DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
DaemonSet 确保集群中的每个节点上都运行且仅运行一个 Pod 副本——或者只在选定的节点子集上运行。当新节点加入集群时，DaemonSet Pod 会自动调度到该节点上。当节点被移除时，该 Pod 会被清理。无需管理副本数量。

<!-- ZH_DEEP_DIVE -->
## 何时使用 DaemonSet

DaemonSet 用于节点级的基础设施关注点——这类软件需要在每个节点上运行，因为它从节点本身收集数据或为节点本身提供能力：

- **日志采集器**（Fluent Bit、Fluentd）——从每个节点上 tail 容器日志，并将其转发到集中式日志存储
- **监控代理**（Prometheus node-exporter、Datadog agent）——采集节点级指标：CPU、内存、磁盘、网络
- **网络插件**（Calico、Cilium、Weave）——在每个节点上于内核层面实现 Pod 网络和网络策略
- **存储驱动**（CSI node 插件）——在 Pod 需要卷的节点上挂载卷
- **安全代理**——主机级入侵检测、漏洞扫描

对于应用工作负载（你的 API、你的 Web 服务器），请使用 Deployment。DaemonSet 用于为节点提供服务的基础设施，而不是为应用服务。

## 编写 DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:2.2
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
```

`hostPath` 卷让 DaemonSet 的 Pod 能够访问节点的文件系统——这对于需要读取容器运行时写入的文件的日志采集器来说很常见。

## 容忍度与控制平面节点

默认情况下，Kubernetes 控制平面带有一个污点（`node-role.kubernetes.io/control-plane:NoSchedule`），阻止普通 Pod 调度到那里。DaemonSet 同样会遵守这个污点。

如果你还需要让 DaemonSet 运行在控制平面节点上（某些网络插件会这样做），请添加一个容忍度：

```yaml
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

## 仅在部分节点上运行

如果你只希望 DaemonSet 运行在某些节点上——GPU 节点、spot 节点、特定节点池中的节点——请使用 node selector：

```yaml
spec:
  template:
    spec:
      nodeSelector:
        cloud.google.com/gke-nodepool: gpu-pool
```

或者使用 node affinity 来表达更丰富的规则。DaemonSet 只会将 Pod 调度到标签匹配的节点上。

## 更新策略

DaemonSet 支持两种更新策略：

**RollingUpdate**（默认）——在各节点上逐个替换 DaemonSet 的 Pod，并遵守 `maxUnavailable`。大多数工作负载请使用此策略。

**OnDelete**——只有在你手动删除某个节点上现有的 DaemonSet Pod 之后，Kubernetes 才会在该节点上创建新的 Pod 模板。当你需要显式控制每个节点何时更新时（例如，对于基础设施组件，你希望在继续之前先验证每个节点），这很有用。

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

## 与 Deployment 的区别

关键区别在于：Deployment 管理的是跨可用节点的期望副本数。DaemonSet 没有副本数——它的期望状态是“每个匹配的节点上一个 Pod”。随着集群的扩缩容，DaemonSet 会自动调整，无需任何配置变更。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) -- 类型：文档，时长：20m

<!-- ZH_UI -->
1. 理解 DaemonSet 的保证：每个节点恰好一个 pod，节点加入时自动添加，节点离开时自动移除
2. 了解典型用例：日志收集器、监控代理、网络插件、存储驱动
3. 使用节点选择器或亲和性让 DaemonSet 只在部分节点上运行（例如仅 GPU 节点、仅 spot 节点）
4. 了解更新策略：RollingUpdate（逐个替换 pod）与 OnDelete（仅在你手动删除旧 pod 时才替换）
