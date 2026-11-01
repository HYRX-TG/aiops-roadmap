---
id: persistent-volume-claims
title: Persistent Volume Claims
zone: kubernetes
edges:
  to:
    - id: configmaps
      question: >-
        Storage sorted. My app also needs configuration — database URLs, feature
        flags, settings. Where do those go?
      detail: >-
        Storage is sorted. But now my app needs to know its database URL, which
        environment it's in, which feature flags are on. Right now that's all
        baked into the container image — which means a rebuild every time
        something changes. There must be a way to inject configuration at
        runtime without rebuilding.
    - id: statefulsets
      question: >-
        I want to run a database in Kubernetes. A Deployment doesn't feel right
        — all the replicas would share the same PVC and fight over the same data.
      detail: >-
        With a Deployment, every pod is interchangeable and shares one PVC. But
        a database replica needs its own storage, its own stable name so other
        replicas know how to reach it, and it needs to come up in order. Is
        there a different workload type built for this?
    - id: debugging-storage
      question: >-
        My pod is stuck in Pending and the PVC won't bind — nothing is
        provisioning.
      detail: >-
        kubectl get pods shows Pending, but the container itself hasn't even
        started trying. kubectl get pvc shows the claim is also Pending. I don't
        know why the storage isn't provisioning or what I'm supposed to look at.
difficulty: 1
tags:
  - kubernetes
  - pvc
  - persistent-volume-claims
  - storage
  - volumes
  - k8s
category: practice
milestones:
  - Create a PVC and mount it into a Pod as a volume
  - >-
    Write data to the mounted path, delete the Pod, recreate it, and verify the
    data persists
  - >-
    Understand why StatefulSets are used instead of Deployments for stateful
    workloads
  - Explain what happens to a PVC when the Pod that uses it is deleted
title_zh: "持久卷声明"

---


A PersistentVolumeClaim (PVC) is how a Pod requests durable storage from the cluster. You declare the size and access mode you need; Kubernetes finds or creates a matching PersistentVolume and binds it. The Pod mounts the PVC as a directory and is abstracted from the underlying storage details entirely.

<!-- DEEP_DIVE -->

## Writing a PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data
  namespace: default
spec:
  storageClassName: gp3      # which StorageClass to use for dynamic provisioning
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

Apply this and Kubernetes will either bind it to a matching pre-existing PV (static provisioning), or trigger the StorageClass's provisioner to create the underlying storage automatically (dynamic provisioning).

## Mounting a PVC into a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
    - name: app
      image: postgres:15
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: my-data
```

The Pod sees `/var/lib/postgresql/data` as a regular directory. Whether it's backed by an EBS volume, an NFS share, or a local disk is invisible to the application.

## What happens when you delete the Pod

Deleting the Pod does not delete the PVC or the underlying storage. The volume outlives the Pod — that's the whole point. A new Pod mounting the same PVC finds the same data waiting for it.

What happens when you delete the PVC itself depends on the StorageClass's reclaim policy:
- `Delete` — the underlying storage is destroyed
- `Retain` — the storage persists and must be manually cleaned up

## PVCs and Deployments — the multi-replica problem

Using a PVC with a Deployment works, but with an important constraint: the access mode must be `ReadWriteMany` if you want multiple Pod replicas mounting the same PVC simultaneously. `ReadWriteOnce` volumes can only be mounted by Pods on the same node — if your Deployment scales to multiple nodes, extra Pods will fail to mount the volume.

For stateful workloads where each replica needs its own persistent storage (databases, message queues, stateful services), use a **StatefulSet** instead of a Deployment. StatefulSets use `volumeClaimTemplates` — Kubernetes automatically creates a separate PVC per Pod replica, named predictably (`data-my-app-0`, `data-my-app-1`, etc.), and each Pod always reconnects to its own PVC when rescheduled.

## Verifying persistence hands-on

The best way to understand PVCs is to experience them directly:

1. Create a PVC and mount it into a Pod
2. Write files to the mounted path (`echo "hello" > /data/test.txt`)
3. Delete the Pod
4. Create a new Pod using the same PVC
5. Verify the files are still there

This makes the abstraction concrete: the Pod is gone but the data survived.

<!-- RESOURCES -->

- [Kubernetes Docs - Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims) -- type: docs, time: 20m
- [Kubernetes Docs - StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) -- type: docs, time: 25m
- [Kubernetes Docs - Configure a Pod to Use a PersistentVolume](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/) -- type: tutorial, time: 20m

<!-- ZH_SUMMARY -->
PersistentVolumeClaim（PVC）是 Pod 向集群请求持久化存储的方式。你声明所需的大小和访问模式；Kubernetes 会找到或创建一个匹配的 PersistentVolume 并将其绑定。Pod 将 PVC 挂载为一个目录，从而完全与底层存储细节解耦。

<!-- ZH_DEEP_DIVE -->
## 编写 PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data
  namespace: default
spec:
  storageClassName: gp3      # 用于动态供应的 StorageClass
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

应用此配置后，Kubernetes 会将其绑定到匹配的已有 PV（静态供应），或者触发 StorageClass 的供应器自动创建底层存储（动态供应）。

## 将 PVC 挂载到 Pod 中

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
    - name: app
      image: postgres:15
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: my-data
```

Pod 将 `/var/lib/postgresql/data` 视为一个普通目录。它背后是 EBS 卷、NFS 共享还是本地磁盘，对应用来说是不可见的。

## 删除 Pod 时会发生什么

删除 Pod 不会删除 PVC 或底层存储。卷的生命周期长于 Pod——这正是它的意义所在。挂载同一 PVC 的新 Pod 会发现相同的数据仍在等待它。

删除 PVC 本身时会发生什么，取决于 StorageClass 的回收策略：
- `Delete`——底层存储被销毁
- `Retain`——存储保留，必须手动清理

## PVC 与 Deployment——多副本问题

将 PVC 与 Deployment 一起使用是可行的，但有一个重要限制：如果希望多个 Pod 副本同时挂载同一 PVC，访问模式必须是 `ReadWriteMany`。`ReadWriteOnce` 卷只能被同一节点上的 Pod 挂载——如果 Deployment 扩展到多个节点，额外的 Pod 将无法挂载该卷。

对于每个副本都需要自己持久存储的有状态工作负载（数据库、消息队列、有状态服务），应使用 **StatefulSet** 而不是 Deployment。StatefulSet 使用 `volumeClaimTemplates`——Kubernetes 会自动为每个 Pod 副本创建单独的 PVC，命名可预测（`data-my-app-0`、`data-my-app-1` 等），并且每个 Pod 在重新调度时始终重新连接到自己的 PVC。

## 动手验证持久性

理解 PVC 的最佳方式是直接体验：

1. 创建一个 PVC 并将其挂载到 Pod 中
2. 向挂载路径写入文件（`echo "hello" > /data/test.txt`）
3. 删除 Pod
4. 使用同一 PVC 创建新 Pod
5. 验证文件仍然存在

这让抽象变得具体：Pod 消失了，但数据存活了下来。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims) -- 类型：文档，时长：20m
- [Kubernetes 文档 - StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) -- 类型：文档，时长：25m
- [Kubernetes 文档 - 配置 Pod 使用 PersistentVolume](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/) -- 类型：教程，时长：20m

<!-- ZH_UI -->
1. 创建 PVC 并将其作为卷挂载到 Pod 中
2. 向挂载路径写入数据，删除 Pod，重新创建它，并验证数据仍然存在
3. 理解为什么有状态工作负载使用 StatefulSet 而不是 Deployment
4. 解释当使用 PVC 的 Pod 被删除时，PVC 会发生什么
5. 存储问题已解决。我的应用还需要配置——数据库 URL、功能开关、设置。这些应该放在哪里？
6. 存储问题已解决。但现在我的应用需要知道它的数据库 URL、它处于哪个环境、哪些功能开关是开启的。目前这些都被固化在容器镜像里——这意味着每次有变更都要重新构建。一定有一种方法可以在运行时注入配置而无需重新构建。
7. 我想在 Kubernetes 中运行数据库。Deployment 感觉不合适——所有副本会共享同一个 PVC 并争抢同一份数据。
8. 使用 Deployment 时，每个 Pod 都是可互换的，并且共享一个 PVC。但数据库副本需要自己的存储、自己的稳定名称（以便其他副本知道如何访问它），并且需要按顺序启动。有没有为此设计的其他工作负载类型？
9. 我的 Pod 卡在 Pending 状态，PVC 无法绑定——没有任何东西在进行供应。
10. kubectl get pods 显示 Pending，但容器本身甚至还没有开始尝试。kubectl get pvc 显示声明也处于 Pending。我不知道为什么存储没有被供应，也不知道该看什么。
