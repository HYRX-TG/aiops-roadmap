---
id: storage-classes
title: StorageClasses and Dynamic Provisioning
zone: kubernetes
edges:
  to:
    - id: persistent-volume-claims
      question: >-
        StorageClasses are configured. How do workloads actually request and use
        storage?
      detail: >-
        So the StorageClass defines how storage gets created — but I still need
        to wire this up to my Pod. Does the Pod reference the StorageClass
        directly? Is there some intermediate resource where I say 'give me 20GB
        of this type of storage'? And how does that volume actually get mounted
        inside my container?
difficulty: 2
tags:
  - kubernetes
  - storageclass
  - dynamic-provisioning
  - ebs
  - gcp-pd
  - csi
  - k8s
category: concept
milestones:
  - Inspect the default StorageClass in your cluster
  - >-
    Create a PVC without a pre-existing PV and watch dynamic provisioning create
    the underlying disk
  - Understand what a CSI driver is and why cloud providers ship them
  - >-
    Know the reclaim policies: Retain, Delete, Recycle — and when each is
    appropriate
title_zh: "存储类与动态供应"

---


StorageClasses tell Kubernetes how to dynamically provision storage on demand. Instead of a human creating a PersistentVolume before a workload starts, the StorageClass defines a provisioner that creates the underlying storage automatically when a PVC is submitted.

<!-- DEEP_DIVE -->

## Static vs dynamic provisioning

With static provisioning, someone pre-creates PersistentVolume objects. A PVC then binds to a matching PV. The problem: a human has to provision storage before the workload needs it, and you're left with either unused pre-created volumes or deployment delays.

Dynamic provisioning inverts this. When a PVC is submitted referencing a StorageClass:

1. Kubernetes calls the StorageClass's provisioner
2. The provisioner creates the underlying storage (an EBS volume, a GCP Persistent Disk, an NFS share)
3. Kubernetes creates a PV automatically to represent it
4. The PV is bound to the PVC

The workload gets storage without anyone manually provisioning it.

## Inspecting your cluster's StorageClasses

```bash
kubectl get storageclass
```

On EKS you'll typically see `gp2` or `gp3` (EBS volumes). On GKE, `standard` and `premium-rwo`. One is usually marked `(default)` — PVCs without an explicit StorageClass reference use this one.

## Writing a StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com     # the CSI driver that creates the volume
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

## Reclaim policies

When the PVC using a PV is deleted, what happens to the PV and its underlying storage?

- **Delete** — delete the PV and the underlying storage automatically. This is the common default for cloud volumes — you don't want orphaned EBS volumes accumulating.
- **Retain** — keep the PV (and the data) after the PVC is deleted. A human must manually clean up. Use this for important data where accidental deletion would be catastrophic.
- **Recycle** — deprecated. Don't use.

## VolumeBindingMode

- **Immediate** — provision the volume as soon as the PVC is created, regardless of where the Pod will be scheduled. Problem in cloud environments: the volume ends up in a random availability zone and may not be in the same AZ as the node the Pod gets scheduled to.
- **WaitForFirstConsumer** — provision the volume only when a Pod that uses the PVC is actually scheduled. The provisioner creates the volume in the same AZ as the scheduled node. This is the recommended mode for cloud environments.

## CSI drivers

CSI (Container Storage Interface) is the standard interface between Kubernetes and storage backends. Cloud providers ship CSI drivers for their storage services:

- `ebs.csi.aws.com` — AWS EBS
- `pd.csi.storage.gke.io` — GCP Persistent Disk
- `disk.csi.azure.com` — Azure Disk
- `nfs.csi.k8s.io` — NFS (community driver)

Managed Kubernetes services (EKS, GKE, AKS) install the appropriate CSI driver automatically. On self-managed clusters, you install the driver as a Helm chart or manifest.

<!-- RESOURCES -->

- [Kubernetes Docs - Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) -- type: docs, time: 25m
- [AWS EBS CSI Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver) -- type: tool, time: 20m
- [Container Storage Interface (CSI) Overview](https://kubernetes-csi.github.io/docs/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
StorageClass 告诉 Kubernetes 如何按需动态供应存储。无需在负载启动前由人工创建 PersistentVolume，StorageClass 定义了一个 provisioner，当 PVC 提交时会自动创建底层存储。

<!-- ZH_DEEP_DIVE -->
## 静态供应与动态供应

在静态供应模式下，需要有人预先创建 PersistentVolume 对象。然后 PVC 会绑定到匹配的 PV。问题在于：必须有人在工作负载需要存储之前就完成存储的供应，结果要么是预先创建但未被使用的卷，要么是部署延迟。

动态供应则相反。当提交引用某个 StorageClass 的 PVC 时：

1. Kubernetes 调用该 StorageClass 的 provisioner
2. provisioner 创建底层存储（EBS 卷、GCP Persistent Disk、NFS 共享）
3. Kubernetes 自动创建一个 PV 来表示该存储
4. 该 PV 绑定到 PVC

工作负载无需任何人手动供应即可获得存储。

## 检查集群的 StorageClass

```bash
kubectl get storageclass
```

在 EKS 上，你通常会看到 `gp2` 或 `gp3`（EBS 卷）。在 GKE 上，则是 `standard` 和 `premium-rwo`。其中一个通常会被标记为 `(default)`——未显式引用 StorageClass 的 PVC 会使用这个默认的 StorageClass。

## 编写 StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com     # the CSI driver that creates the volume
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

## 回收策略

当使用某个 PV 的 PVC 被删除时，该 PV 及其底层存储会怎样？

- **Delete** — 自动删除 PV 和底层存储。这是云卷的常见默认值——你不会希望孤立的 EBS 卷不断累积。
- **Retain** — 在 PVC 被删除后保留 PV（以及数据）。必须由人工手动清理。对于误删除会造成灾难性后果的重要数据，请使用此策略。
- **Recycle** — 已弃用。不要使用。

## VolumeBindingMode

- **Immediate** — 在 PVC 创建后立即供应卷，而不考虑 Pod 将被调度到哪里。在云环境中会有问题：卷最终会位于随机的可用区，可能与该 Pod 被调度到的节点不在同一 AZ。
- **WaitForFirstConsumer** — 仅当使用该 PVC 的 Pod 实际被调度时才供应卷。provisioner 会在与已调度节点相同的 AZ 中创建卷。这是云环境推荐使用的模式。

## CSI 驱动

CSI（Container Storage Interface）是 Kubernetes 与存储后端之间的标准接口。云提供商为其存储服务提供 CSI 驱动：

- `ebs.csi.aws.com` — AWS EBS
- `pd.csi.storage.gke.io` — GCP Persistent Disk
- `disk.csi.azure.com` — Azure Disk
- `nfs.csi.k8s.io` — NFS（社区驱动）

托管 Kubernetes 服务（EKS、GKE、AKS）会自动安装相应的 CSI 驱动。在自管理集群上，你需要以 Helm chart 或 manifest 的形式安装驱动。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) -- type: docs, time: 25m
- [AWS EBS CSI Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver) -- type: tool, time: 20m
- [Container Storage Interface (CSI) 概述](https://kubernetes-csi.github.io/docs/) -- type: docs, time: 15m

<!-- ZH_UI -->
1. 检查集群中的默认 StorageClass
2. 创建一个没有预先存在的 PV 的 PVC，观察动态供给如何创建底层磁盘
3. 理解什么是 CSI 驱动，以及云厂商为何提供它们
4. 了解回收策略：Retain、Delete、Recycle——以及各自适用的场景
5. StorageClass 已配置好。工作负载实际上如何请求和使用存储？
6. 所以 StorageClass 定义了存储如何创建——但我还需要把它接到我的 Pod 上。Pod 是直接引用 StorageClass 吗？是否存在某个中间资源，让我声明“给我 20GB 这种类型的存储”？这个卷实际上又是如何挂载到我的容器里的？
