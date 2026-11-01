---
id: persistent-volumes
title: Persistent Volumes
zone: kubernetes
edges:
  to:
    - id: persistent-volume-claims
      question: >-
        I understand PersistentVolumes exist as cluster resources. How does my
        Pod actually claim and use one?
      detail: >-
        So I've got a PV sitting there as a cluster resource — but how does my
        Pod actually get to use it? Do I reference it by name in the Pod spec?
        Is there some request mechanism? I want my Pod to be able to say 'give
        me 10GB of storage' without me having to wire up the specific underlying
        volume manually.
    - id: storage-classes
      question: >-
        Creating PersistentVolumes manually one by one sounds painful. Is there
        a way to provision storage automatically?
      detail: >-
        Every time an app needs storage I'd have to manually create a PV
        pointing at a specific EBS volume or NFS share? That's going to get
        tedious fast — and it means I need to know in advance exactly what
        storage each workload needs. Surely there's a way for the cluster to
        just create the underlying storage on demand when something requests it.
difficulty: 2
tags:
  - kubernetes
  - persistent-volumes
  - pv
  - storage
  - stateful
  - k8s
category: concept
milestones:
  - Explain why Pod storage is ephemeral by default
  - Create a PersistentVolume manually (static provisioning)
  - 'Understand the PV lifecycle: Available, Bound, Released, Failed'
  - 'Know the access modes: ReadWriteOnce, ReadOnlyMany, ReadWriteMany'
title_zh: "持久卷"

---


A Pod's filesystem is ephemeral by default — when the Pod is deleted, everything it wrote is gone. PersistentVolumes are cluster-level storage resources that exist independently of Pods, allowing data to survive Pod restarts, rescheduling, and replacements.

<!-- DEEP_DIVE -->

## Why Pod storage is ephemeral

When a container starts in Kubernetes, it gets a writable layer on top of its container image (using a union filesystem like OverlayFS). Everything the container writes goes into this writable layer. When the container or Pod is deleted, that writable layer is discarded.

This is a feature for stateless workloads — you never accidentally carry stale state from one run to the next. But for anything that needs persistence — databases, file uploads, caches that are expensive to rebuild — you need storage that exists outside the Pod.

## PersistentVolumes

A PersistentVolume (PV) is a cluster-level resource that represents a piece of storage. It could be:

- An AWS EBS volume
- A GCP Persistent Disk
- An Azure Disk or Azure File share
- An NFS mount
- A local disk on a node
- Any other backend that has a CSI driver

A manually created (statically provisioned) PV looks like this:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-nfs-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  nfs:
    path: /exports/data
    server: 10.0.0.5
```

## Access modes

Access modes describe how a volume can be mounted across nodes:

- **ReadWriteOnce (RWO)** — mounted read-write by a single node. Most cloud block storage (EBS, GCP PD, Azure Disk) only supports this. Multiple Pods on the same node can share it, but Pods on different nodes cannot.
- **ReadOnlyMany (ROX)** — mounted read-only by many nodes simultaneously. Good for distributing static content or config data.
- **ReadWriteMany (RWX)** — mounted read-write by many nodes simultaneously. Requires a network filesystem like NFS, CephFS, or AWS EFS. More expensive to set up correctly.

The access mode you request in a PVC must be supported by the underlying storage type.

## PV lifecycle states

A PV moves through these states:

- **Available** — created and not yet claimed by any PVC
- **Bound** — matched to a PVC and in use
- **Released** — the PVC was deleted, but the volume hasn't been reclaimed yet (its data still exists)
- **Failed** — automatic reclamation failed

## Static vs dynamic provisioning

Creating PVs manually (static provisioning) doesn't scale. Every new workload needs a new PV, and a human has to provision the underlying storage before the workload can start.

Dynamic provisioning via **StorageClasses** solves this: when a PVC is created referencing a StorageClass, Kubernetes automatically provisions the underlying storage and creates the PV. No human in the loop. This is how most production Kubernetes storage works.

<!-- RESOURCES -->

- [Kubernetes Docs - Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) -- type: docs, time: 30m
- [Container Storage Interface (CSI) Docs](https://kubernetes-csi.github.io/docs/) -- type: docs, time: 20m
- [Kubernetes Storage Explained - TechWorld with Nana (YouTube)](https://www.youtube.com/watch?v=0swOh5C3OVM) -- type: video, time: 20m

<!-- ZH_SUMMARY -->
Pod 的文件系统默认是临时的——Pod 被删除时，它写入的所有内容都会丢失。PersistentVolume 是集群级存储资源，独立于 Pod 存在，使数据能够在 Pod 重启、重新调度和替换后依然保留。

<!-- ZH_DEEP_DIVE -->
## 为什么 Pod 存储是临时的

当容器在 Kubernetes 中启动时，它会在容器镜像之上获得一个可写层（使用 OverlayFS 等联合文件系统）。容器写入的所有内容都会进入这个可写层。当容器或 Pod 被删除时，该可写层会被丢弃。

对于无状态工作负载来说，这是一个特性——你永远不会意外地将上一次运行的陈旧状态带到下一次运行。但对于任何需要持久化的东西——数据库、文件上传、重建成本高昂的缓存——你需要存在于 Pod 之外的存储。

## PersistentVolume

PersistentVolume（PV）是一个集群级资源，代表一块存储。它可以是：

- 一个 AWS EBS 卷
- 一个 GCP Persistent Disk
- 一个 Azure Disk 或 Azure File 共享
- 一个 NFS 挂载
- 节点上的本地磁盘
- 任何其他具有 CSI 驱动的后端

手动创建（静态制备）的 PV 如下所示：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-nfs-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  nfs:
    path: /exports/data
    server: 10.0.0.5
```

## 访问模式

访问模式描述卷如何跨节点挂载：

- **ReadWriteOnce (RWO)** — 由单个节点以读写方式挂载。大多数云块存储（EBS、GCP PD、Azure Disk）仅支持此模式。同一节点上的多个 Pod 可以共享它，但不同节点上的 Pod 不能。
- **ReadOnlyMany (ROX)** — 由多个节点同时以只读方式挂载。适合分发静态内容或配置数据。
- **ReadWriteMany (RWX)** — 由多个节点同时以读写方式挂载。需要 NFS、CephFS 或 AWS EFS 等网络文件系统。正确设置的代价更高。

你在 PVC 中请求的访问模式必须得到底层存储类型的支持。

## PV 生命周期状态

PV 会经历以下状态：

- **Available** — 已创建，尚未被任何 PVC 认领
- **Bound** — 已匹配到 PVC 并正在使用
- **Released** — PVC 已被删除，但卷尚未被回收（其数据仍然存在）
- **Failed** — 自动回收失败

## 静态制备与动态制备

手动创建 PV（静态制备）无法扩展。每个新工作负载都需要一个新的 PV，并且必须有人先制备底层存储，工作负载才能启动。

通过 **StorageClass** 进行动态制备解决了这个问题：当创建引用 StorageClass 的 PVC 时，Kubernetes 会自动制备底层存储并创建 PV。无需人工介入。这就是大多数生产环境 Kubernetes 存储的工作方式。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 持久卷](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) -- 类型：文档，时长：30 分钟
- [容器存储接口（CSI）文档](https://kubernetes-csi.github.io/docs/) -- 类型：文档，时长：20 分钟
- [Kubernetes 存储详解 - TechWorld with Nana（YouTube）](https://www.youtube.com/watch?v=0swOh5C3OVM) -- 类型：视频，时长：20 分钟

<!-- ZH_UI -->
1. 解释为什么 Pod 存储默认是临时的
2. 手动创建 PersistentVolume（静态供应）
3. 理解 PV 生命周期：Available、Bound、Released、Failed
4. 了解访问模式：ReadWriteOnce、ReadOnlyMany、ReadWriteMany
5. 我理解 PersistentVolume 是集群资源。我的 Pod 实际如何申请并使用一个 PV？
6. 那么 PV 作为集群资源已经在那里了——但我的 Pod 实际怎么用上它？是在 Pod spec 里按名字引用吗？还是有某种请求机制？我希望我的 Pod 能直接说“给我 10GB 存储”，而不用我手动接上具体的底层卷。
7. 手动逐个创建 PersistentVolume 听起来很麻烦。有没有办法自动供应存储？
8. 每次应用需要存储，我都得手动创建一个指向特定 EBS 卷或 NFS 共享的 PV？这很快就会变得很繁琐——而且这意味着我得提前确切知道每个工作负载需要什么存储。肯定有办法让集群在有请求时按需创建底层存储吧。
