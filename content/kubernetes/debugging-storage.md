---
id: debugging-storage
title: Debugging Storage and PVCs
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - debugging
  - pvc
  - storage
  - persistent-volumes
  - storage-class
  - k8s
category: practice
milestones:
  - >-
    Use kubectl describe pvc to find why a claim isn't binding — wrong storage
    class, no provisioner, or access mode mismatch
  - >-
    Understand the difference between a PVC stuck in Pending (provisioning
    failed) and a pod stuck in Pending waiting for a PVC to bind
  - >-
    Know how to find and check the CSI driver or provisioner that's responsible
    for creating the actual storage
title_zh: "调试存储与 PVC"

---


A pod stuck in Pending because of storage is usually either a PVC that won't bind, or a PVC that bound to the wrong kind of volume. Almost all PVC problems come down to the storage class, the access mode, or a provisioner that isn't running.

<!-- DEEP_DIVE -->

## Check the PVC first

When a pod is pending because of storage, start with the PVC:

```bash
kubectl get pvc
kubectl describe pvc my-claim
```

Look at the **Status** field. A PVC can be:

- **Pending** — waiting to be bound. Either no matching PV exists (static provisioning), or the StorageClass provisioner hasn't created one yet, or it failed to.
- **Bound** — successfully bound to a PV. If the pod is still pending, the problem is something else (node resources, scheduling constraints).
- **Lost** — was bound to a PV that no longer exists. The PV was deleted while the PVC was still using it.

The **Events** section in `describe pvc` tells you what the provisioner tried and what went wrong.

## StorageClass problems

The most common root cause: the StorageClass doesn't exist, or its provisioner isn't running.

```bash
kubectl get storageclass
```

Check that the StorageClass your PVC requests actually exists. If you wrote `storageClassName: gp3` but the cluster has `gp2`, the PVC will sit in Pending forever.

Check whether the provisioner is working:

```bash
kubectl get pods -n kube-system | grep -i csi
```

If the CSI driver pods are crashing or missing, no PVCs can be provisioned. Check their logs:

```bash
kubectl logs -n kube-system <csi-provisioner-pod>
```

## Access mode mismatch

A PVC requests an access mode (`ReadWriteOnce`, `ReadWriteMany`, `ReadOnlyMany`). The PV it binds to must support that mode.

`ReadWriteOnce` (RWO) is the most common — one pod can mount the volume at a time, and only on one node. If your Deployment has multiple replicas trying to mount the same RWO PVC from different nodes, only one will succeed and the others will be stuck.

If you need multiple pods to mount the same volume simultaneously, you need `ReadWriteMany` (RWX) — but most cloud block storage (EBS, GCP PD) doesn't support RWX. You need a network filesystem (NFS, EFS, Azure Files) for that.

## Pod stuck waiting for PVC

If the pod is pending with this in its Events:

```
Warning  FailedScheduling  persistentvolumeclaim "my-claim" not found
```

or:

```
Warning  FailedMount  Unable to attach or mount volumes
```

The PVC itself might be bound, but the volume can't be attached to the node the pod landed on. This happens with zone-specific storage: if your PVC bound to a volume in `us-east-1a` and the pod scheduled to a node in `us-east-1b`, the attach will fail.

Fix: use `volumeBindingMode: WaitForFirstConsumer` on the StorageClass — this delays volume creation until a pod is scheduled, so the volume gets created in the right zone.

## A systematic approach

1. `kubectl get pvc` — is the PVC Bound or Pending?
2. `kubectl describe pvc my-claim` — Events section: what did the provisioner say?
3. `kubectl get storageclass` — does the requested StorageClass exist?
4. `kubectl get pods -n kube-system | grep csi` — is the provisioner running?
5. `kubectl describe pod my-pod` — Events: is the pod pending because of PVC or something else?
6. Check access mode: is this RWO being mounted by multiple pods on different nodes?

<!-- RESOURCES -->

- [Kubernetes Docs - Troubleshoot Persistent Volumes](https://kubernetes.io/docs/tasks/debug/debug-cluster/debug-application/#my-persistent-volume-is-not-binding) -- type: docs, time: 15m
- [Kubernetes Docs - Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Pod 因存储问题卡在 Pending 状态，通常要么是 PVC 无法绑定，要么是 PVC 绑定到了错误类型的卷。几乎所有 PVC 问题都可归结为存储类、访问模式，或未运行的 provisioner。

<!-- ZH_DEEP_DIVE -->
## 先检查 PVC

当 Pod 因存储问题处于 Pending 状态时，先从 PVC 入手：

```bash
kubectl get pvc
kubectl describe pvc my-claim
```

查看 **Status** 字段。PVC 可能处于以下几种状态：

- **Pending** —— 等待绑定。要么没有匹配的 PV（静态供应），要么 StorageClass 的 provisioner 尚未创建 PV，要么创建失败。
- **Bound** —— 已成功绑定到 PV。如果 Pod 仍处于 Pending，问题出在别处（节点资源、调度约束）。
- **Lost** —— 曾绑定到某个 PV，但该 PV 已不存在。即 PVC 仍在使用时 PV 被删除了。

`describe pvc` 中的 **Events** 部分会告诉你 provisioner 尝试了什么、哪里出了问题。

## StorageClass 问题

最常见的根因：StorageClass 不存在，或其 provisioner 未运行。

```bash
kubectl get storageclass
```

确认 PVC 请求的 StorageClass 确实存在。如果你写的是 `storageClassName: gp3`，但集群里只有 `gp2`，PVC 会永远停留在 Pending。

检查 provisioner 是否正常工作：

```bash
kubectl get pods -n kube-system | grep -i csi
```

如果 CSI driver 的 Pod 崩溃或缺失，就无法供应任何 PVC。查看它们的日志：

```bash
kubectl logs -n kube-system <csi-provisioner-pod>
```

## 访问模式不匹配

PVC 会请求一种访问模式（`ReadWriteOnce`、`ReadWriteMany`、`ReadOnlyMany`）。它绑定的 PV 必须支持该模式。

`ReadWriteOnce`（RWO）最常见——同一时间只能有一个 Pod 挂载该卷，且只能在一个节点上。如果你的 Deployment 有多个副本，试图从不同节点挂载同一个 RWO PVC，只有一个会成功，其余会卡住。

如果你需要多个 Pod 同时挂载同一个卷，就需要 `ReadWriteMany`（RWX）——但大多数云块存储（EBS、GCP PD）不支持 RWX。你需要网络文件系统（NFS、EFS、Azure Files）才能做到。

## Pod 卡在等待 PVC

如果 Pod 处于 Pending，且其 Events 中有：

```
Warning  FailedScheduling  persistentvolumeclaim "my-claim" not found
```

或：

```
Warning  FailedMount  Unable to attach or mount volumes
```

PVC 本身可能已绑定，但卷无法挂载到 Pod 所在的节点。这在使用区域特定存储时会发生：如果你的 PVC 绑定到 `us-east-1a` 的卷，而 Pod 被调度到 `us-east-1b` 的节点，挂载就会失败。

修复方法：在 StorageClass 上使用 `volumeBindingMode: WaitForFirstConsumer`——这会延迟卷的创建，直到 Pod 被调度，从而让卷在正确的区域创建。

## 系统性排查方法

1. `kubectl get pvc` —— PVC 是 Bound 还是 Pending？
2. `kubectl describe pvc my-claim` —— Events 部分：provisioner 说了什么？
3. `kubectl get storageclass` —— 请求的 StorageClass 是否存在？
4. `kubectl get pods -n kube-system | grep csi` —— provisioner 是否在运行？
5. `kubectl describe pod my-pod` —— Events：Pod 处于 Pending 是因为 PVC 还是其他原因？
6. 检查访问模式：这个 RWO 是否正被不同节点上的多个 Pod 挂载？

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 排查持久卷问题](https://kubernetes.io/docs/tasks/debug/debug-cluster/debug-application/#my-persistent-volume-is-not-binding) -- 类型：文档，时长：15 分钟
- [Kubernetes 文档 - 存储类](https://kubernetes.io/docs/concepts/storage/storage-classes/) -- 类型：文档，时长：20 分钟

<!-- ZH_UI -->
1. 使用 kubectl describe pvc 查明 PVC 为何无法绑定——存储类错误、没有 provisioner 或访问模式不匹配
2. 理解卡在 Pending 的 PVC（provisioning 失败）与等待 PVC 绑定的 Pending Pod 之间的区别
3. 知道如何找到并检查负责创建实际存储的 CSI 驱动或 provisioner
