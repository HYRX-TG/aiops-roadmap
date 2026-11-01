---
id: statefulsets
title: StatefulSets
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - statefulsets
  - storage
  - databases
  - headless-service
  - k8s
category: practice
milestones:
  - >-
    Understand the three StatefulSet guarantees: stable pod identity, stable
    network hostname, and stable per-replica storage
  - >-
    Create a StatefulSet with a volumeClaimTemplate and verify each pod gets
    its own PVC
  - >-
    Understand how headless Services give each pod a stable DNS name like
    my-app-0.my-app.default.svc.cluster.local
  - >-
    Know the ordering guarantees: pods start in order (0, 1, 2) and terminate
    in reverse — and when that matters vs when it doesn't
  - >-
    Know when NOT to use StatefulSets: managed databases outside the cluster
    are usually less operational pain
title_zh: "有状态副本集（StatefulSets）"

---


A StatefulSet is the right workload type when your pods cannot be interchangeable. Unlike a Deployment (where replicas are identical and disposable), a StatefulSet gives each pod a stable name, a stable DNS hostname, and its own PersistentVolumeClaim that follows it across rescheduling.

The classic use case is a database cluster: each replica needs to know its own identity, communicate with specific peers by name, and write to its own storage — none of which works with a Deployment.

<!-- DEEP_DIVE -->

## The three guarantees

StatefulSets provide three things that Deployments don't:

**Stable pod identity** — pods are named `<statefulset>-0`, `<statefulset>-1`, etc. The name is consistent across restarts. Pod `my-db-0` is always `my-db-0`, not some randomly generated name.

**Stable network hostname** — when paired with a headless Service, each pod gets a DNS record like `my-db-0.my-db.default.svc.cluster.local`. Other pods can address a specific replica directly, not just the service's load-balanced endpoint.

**Stable per-replica storage** — each pod gets its own PVC, created from a `volumeClaimTemplate`. The PVC is named `<template>-<pod>` (e.g. `data-my-db-0`) and is never deleted when the pod is rescheduled. The replacement pod finds the same data waiting.

## Writing a StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: my-db
spec:
  serviceName: my-db        # must match the headless Service name
  replicas: 3
  selector:
    matchLabels:
      app: my-db
  template:
    metadata:
      labels:
        app: my-db
    spec:
      containers:
        - name: db
          image: postgres:15
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3
        resources:
          requests:
            storage: 20Gi
```

When you apply this, Kubernetes creates three pods (`my-db-0`, `my-db-1`, `my-db-2`) and three PVCs (`data-my-db-0`, `data-my-db-1`, `data-my-db-2`). Each pod mounts only its own PVC.

## The headless Service

A StatefulSet requires a headless Service — a Service with `clusterIP: None`. Without a headless Service you don't get per-pod DNS records.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-db
spec:
  clusterIP: None           # headless
  selector:
    app: my-db
  ports:
    - port: 5432
```

With this in place, `my-db-0.my-db.default.svc.cluster.local` resolves directly to pod `my-db-0`. This is how database clustering software (Postgres, Cassandra, Redis Sentinel) knows how to reach specific peers.

## Ordering guarantees

StatefulSets start pods in order and wait for each to be Ready before starting the next:

- `my-db-0` starts, becomes Ready
- `my-db-1` starts, becomes Ready
- `my-db-2` starts

Scale-down is the reverse: `my-db-2` terminates first, then `my-db-1`, then `my-db-0`.

This ordering matters for databases that elect a leader or require a primary to be up before replicas join. For workloads that don't need it, you can set `podManagementPolicy: Parallel` to start all pods simultaneously.

## What doesn't get cleaned up automatically

Deleting a StatefulSet does **not** delete its PVCs. This is intentional — you don't want to lose database state just because you reapplied a manifest. PVCs must be deleted manually. Be deliberate about this in CI environments where you're tearing things down.

## When not to use StatefulSets

Running a database inside Kubernetes is operationally harder than it looks. You're responsible for backups, replication configuration, failover, and upgrades — on top of running Kubernetes itself.

For most teams, the right answer is a managed database (RDS, Cloud SQL, PlanetScale) outside the cluster, accessed over the network. You lose nothing architecturally and gain a lot of operational simplicity.

StatefulSets are appropriate when:
- You're running infrastructure software that needs to be self-contained (message queues, caches, search engines)
- You're operating at a scale where a managed service is prohibitively expensive
- You have the platform team capacity to own the operational burden

<!-- RESOURCES -->

- [Kubernetes Docs - StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) -- type: docs, time: 25m
- [Kubernetes Docs - Running a Replicated Stateful Application](https://kubernetes.io/docs/tasks/run-application/run-replicated-stateful-application/) -- type: tutorial, time: 30m

<!-- ZH_SUMMARY -->
当你的 Pod 无法互换时，StatefulSet 就是正确的工作负载类型。与 Deployment（副本完全相同且可随时丢弃）不同，StatefulSet 为每个 Pod 提供稳定的名称、稳定的 DNS 主机名，以及跟随其跨重新调度迁移的专属 PersistentVolumeClaim。

经典用例是数据库集群：每个副本都需要知道自己的身份、按名称与特定对等节点通信，并写入自己的存储——这些在 Deployment 上都无法实现。

<!-- ZH_DEEP_DIVE -->
## 三大保证

StatefulSet 提供了 Deployment 所不具备的三项能力：

**稳定的 Pod 标识** —— Pod 命名为 `<statefulset>-0`、`<statefulset>-1` 等。该名称在重启后保持一致。Pod `my-db-0` 始终是 `my-db-0`，而不是某个随机生成的名字。

**稳定的网络主机名** —— 与 headless Service 配合使用时，每个 Pod 都会获得一条 DNS 记录，例如 `my-db-0.my-db.default.svc.cluster.local`。其他 Pod 可以直接寻址某个特定的副本，而不仅仅是 Service 的负载均衡端点。

**稳定的每副本存储** —— 每个 Pod 都会获得自己的 PVC，由 `volumeClaimTemplate` 创建。PVC 命名为 `<template>-<pod>`（例如 `data-my-db-0`），并且当 Pod 被重新调度时永远不会被删除。替换后的 Pod 会发现同样的数据仍在等待它。

## 编写 StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: my-db
spec:
  serviceName: my-db        # must match the headless Service name
  replicas: 3
  selector:
    matchLabels:
      app: my-db
  template:
    metadata:
      labels:
        app: my-db
    spec:
      containers:
        - name: db
          image: postgres:15
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3
        resources:
          requests:
            storage: 20Gi
```

应用此配置后，Kubernetes 会创建三个 Pod（`my-db-0`、`my-db-1`、`my-db-2`）和三个 PVC（`data-my-db-0`、`data-my-db-1`、`data-my-db-2`）。每个 Pod 只挂载自己的 PVC。

## headless Service

StatefulSet 需要一个 headless Service —— 即 `clusterIP: None` 的 Service。没有 headless Service，就无法获得每 Pod 的 DNS 记录。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-db
spec:
  clusterIP: None           # headless
  selector:
    app: my-db
  ports:
    - port: 5432
```

配置好之后，`my-db-0.my-db.default.svc.cluster.local` 会直接解析到 Pod `my-db-0`。数据库集群软件（Postgres、Cassandra、Redis Sentinel）正是通过这种方式知道如何访问特定的对等节点。

## 顺序保证

StatefulSet 按顺序启动 Pod，并等待每个 Pod 就绪后再启动下一个：

- `my-db-0` 启动，变为 Ready
- `my-db-1` 启动，变为 Ready
- `my-db-2` 启动

缩容则相反：`my-db-2` 先终止，然后是 `my-db-1`，最后是 `my-db-0`。

这种顺序对于需要选举 leader 或要求主节点先于副本加入的数据库至关重要。对于不需要此顺序的工作负载，可以设置 `podManagementPolicy: Parallel` 来同时启动所有 Pod。

## 不会自动清理的内容

删除 StatefulSet **不会**删除其 PVC。这是有意为之 —— 你不会希望仅仅因为重新应用了一次 manifest 就丢失数据库状态。PVC 必须手动删除。在需要拆除环境的 CI 环境中，务必谨慎对待这一点。

## 何时不应使用 StatefulSet

在 Kubernetes 中运行数据库，其运维难度比看起来要大。除了运行 Kubernetes 本身之外，你还要负责备份、复制配置、故障转移和升级。

对大多数团队而言，正确的答案是在集群之外使用托管数据库（RDS、Cloud SQL、PlanetScale），通过网络访问。在架构上你没有任何损失，却能获得大量的运维简化。

StatefulSet 适用于以下情况：
- 你运行的基础设施软件需要自包含（消息队列、缓存、搜索引擎）
- 你的规模使得托管服务成本过高
- 你有平台团队的能力来承担运维负担

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) -- 类型：文档，时长：25 分钟
- [Kubernetes 文档 - 运行有状态副本应用](https://kubernetes.io/docs/tasks/run-application/run-replicated-stateful-application/) -- 类型：教程，时长：30 分钟

<!-- ZH_UI -->
1. 理解 StatefulSet 的三项保证：稳定的 Pod 身份、稳定的网络主机名，以及每个副本稳定的存储
2. 创建一个带 volumeClaimTemplate 的 StatefulSet，并验证每个 Pod 都获得自己的 PVC
3. 理解 headless Service 如何为每个 Pod 提供稳定的 DNS 名称，如 my-app-0.my-app.default.svc.cluster.local
4. 了解顺序保证：Pod 按顺序启动（0、1、2），并按相反顺序终止——以及何时重要、何时不重要
5. 了解何时不应使用 StatefulSet：集群外的托管数据库通常运维负担更小
