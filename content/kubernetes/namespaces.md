---
id: namespaces
title: Namespaces
zone: kubernetes
edges:
  to:
    - id: pods
      question: >-
        I understand how namespaces organise the cluster. Now — how do I
        actually run something in one?
      detail: >-
        I've set up my namespaces, but now I'm staring at kubectl not sure what
        to actually put in them. What's the first real thing I deploy, and how
        do I make sure it ends up in the right namespace?
difficulty: 1
tags:
  - kubernetes
  - namespaces
  - multi-tenancy
  - resource-quotas
  - organisation
  - k8s
category: concept
milestones:
  - Create a namespace and deploy a Pod into it
  - Use -n flag with kubectl to target a specific namespace
  - Set a ResourceQuota on a namespace to limit CPU and memory
  - >-
    Understand why cluster-scoped resources (Nodes, PersistentVolumes) don't
    belong to namespaces
  - Explain the difference between namespace-scoped and cluster-scoped resources
title_zh: "命名空间"

---


A Kubernetes cluster is shared infrastructure — by default, everything lands in the `default` namespace and all workloads can see each other. Namespaces carve a cluster into isolated virtual spaces, each with its own resources, access controls, and limits. Getting this right from the start is much easier than retrofitting it later.

<!-- DEEP_DIVE -->

## What a namespace actually is

Namespaces are a virtual partition inside a Kubernetes cluster. Think of them like directories in a filesystem — except these directories also carry access controls and resource limits. Two Services named `api` in different namespaces are completely separate resources. A ResourceQuota on the `staging` namespace doesn't affect `production`.

Kubernetes ships with a few built-in namespaces:

- `default` — where your resources go when you don't specify a namespace
- `kube-system` — where Kubernetes's own components run (scheduler, controller manager, CoreDNS)
- `kube-public` — readable by all users, rarely used in practice
- `kube-node-lease` — used for node heartbeats, not for user workloads

## How to use namespaces

Creating a namespace is trivial:

```bash
kubectl create namespace staging
```

Or declaratively (the preferred way for anything you'd commit to Git):

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging
```

Every subsequent `kubectl` command accepts a `-n` flag to target a specific namespace:

```bash
kubectl get pods -n staging
kubectl apply -f my-app.yaml -n staging
kubectl logs my-pod -n staging
```

If you work in one namespace constantly, set it as the default for your current context with `kubens` (part of the `kubectx` tool) rather than typing `-n` on every command.

## Namespace-scoped vs cluster-scoped resources

Not everything in Kubernetes lives inside a namespace. Namespaces contain workload-level resources: Pods, Services, Deployments, ConfigMaps, Secrets, PersistentVolumeClaims. But some resources are cluster-scoped and exist outside any namespace:

- **Nodes** — the machines themselves
- **PersistentVolumes** — cluster-level storage pools
- **StorageClasses** — how to provision storage
- **ClusterRoles** and **ClusterRoleBindings** — cluster-wide permissions
- **Namespaces** themselves

This distinction matters: when you grant RBAC permissions scoped to a namespace, they only apply to namespace-scoped resources within that namespace. Cluster-scoped resources require ClusterRoleBindings.

## Resource quotas

One of the main reasons to use namespaces in a shared cluster is to prevent one team or environment from consuming all available compute. A `ResourceQuota` caps what a namespace can collectively use:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-quota
  namespace: staging
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
```

With this quota, the staging namespace can never collectively request more than 4 CPUs or 8GB of memory. If a Deployment update would push past the limit, Kubernetes rejects it — the quota acts as a ceiling.

## Namespace patterns in practice

Three common strategies:

- **Per-environment** — `dev`, `staging`, `production` in the same cluster. Simple, but production and dev are co-located, which makes some teams nervous.
- **Per-team** — `payments`, `auth`, `notifications`, each team owns their namespace. Works well with GitOps where each team manages their own manifests.
- **Per-application** — fine-grained isolation, each application gets its own namespace. Common in larger organizations with many services.

For strong isolation between tenants who shouldn't see each other's secrets — true multi-tenancy — namespaces alone aren't enough. You also need NetworkPolicies (to limit cross-namespace network traffic) and strict RBAC (to prevent namespace hopping). For single-team clusters with multiple environments, namespace-per-environment is simple and usually sufficient.

<!-- RESOURCES -->

- [Kubernetes Docs - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- type: docs, time: 15m
- [Kubernetes Docs - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- type: docs, time: 20m
- [kubectx + kubens - Switch contexts and namespaces fast](https://github.com/ahmetb/kubectx) -- type: tool, time: 5m

<!-- ZH_SUMMARY -->
Kubernetes 集群是共享基础设施——默认情况下，所有内容都落在 `default` 命名空间中，所有工作负载彼此可见。命名空间将集群划分为相互隔离的虚拟空间，每个空间都有自己的资源、访问控制和限制。从一开始就正确规划，远比事后改造要容易得多。

<!-- ZH_DEEP_DIVE -->
## namespace 究竟是什么

namespace 是 Kubernetes 集群内部的虚拟分区。可以把它想象成文件系统中的目录——只不过这些“目录”还带有访问控制和资源限制。不同 namespace 中两个同名为 `api` 的 Service 是完全独立的资源。`staging` namespace 上的 ResourceQuota 不会影响 `production`。

Kubernetes 自带几个内置 namespace：

- `default` — 未指定 namespace 时资源的默认去处
- `kube-system` — Kubernetes 自身组件运行的地方（scheduler、controller manager、CoreDNS）
- `kube-public` — 所有用户可读，实践中很少使用
- `kube-node-lease` — 用于节点心跳，不用于用户工作负载

## 如何使用 namespace

创建 namespace 非常简单：

```bash
kubectl create namespace staging
```

或以声明式方式（对于要提交到 Git 的内容，这是首选方式）：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging
```

之后每条 `kubectl` 命令都接受 `-n` 标志来指定目标 namespace：

```bash
kubectl get pods -n staging
kubectl apply -f my-app.yaml -n staging
kubectl logs my-pod -n staging
```

如果你长期在同一个 namespace 中工作，可以用 `kubens`（`kubectx` 工具的一部分）将其设为当前 context 的默认 namespace，而不必在每条命令上都输入 `-n`。

## namespace 级资源与集群级资源

Kubernetes 中并非所有东西都位于 namespace 内。namespace 包含工作负载级资源：Pod、Service、Deployment、ConfigMap、Secret、PersistentVolumeClaim。但有些资源是集群级的，存在于任何 namespace 之外：

- **Node** — 机器本身
- **PersistentVolume** — 集群级存储池
- **StorageClass** — 如何供应存储
- **ClusterRole** 和 **ClusterRoleBinding** — 集群范围的权限
- **Namespace** 本身

这一区别很重要：当你授予限定在某个 namespace 的 RBAC 权限时，它们只作用于该 namespace 内的 namespace 级资源。集群级资源需要 ClusterRoleBinding。

## 资源配额

在共享集群中使用 namespace 的主要原因之一，是防止某个团队或环境耗尽所有可用算力。`ResourceQuota` 限制一个 namespace 可以集体使用的资源上限：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-quota
  namespace: staging
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
```

有了这个配额，staging namespace 集体请求的 CPU 永远不能超过 4 个，内存不能超过 8GB。如果某次 Deployment 更新会超出限制，Kubernetes 会拒绝它——配额起到上限的作用。

## 实践中的 namespace 模式

三种常见策略：

- **按环境划分** — 同一集群中的 `dev`、`staging`、`production`。简单，但生产与开发共处一地，这让一些团队感到不安。
- **按团队划分** — `payments`、`auth`、`notifications`，每个团队拥有自己的 namespace。与 GitOps 配合良好，每个团队管理自己的 manifest。
- **按应用划分** — 细粒度隔离，每个应用拥有自己的 namespace。在拥有众多服务的大型组织中很常见。

对于租户之间不应看到彼此 secret 的强隔离——真正的多租户——仅靠 namespace 是不够的。你还需要 NetworkPolicy（限制跨 namespace 的网络流量）和严格的 RBAC（防止 namespace 越权访问）。对于单团队、多环境的集群，按环境划分 namespace 简单且通常足够。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- 类型: 文档, 时间: 15m
- [Kubernetes 文档 - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- 类型: 文档, 时间: 20m
- [kubectx + kubens - 快速切换上下文和命名空间](https://github.com/ahmetb/kubectx) -- 类型: 工具, 时间: 5m

<!-- ZH_UI -->
1. 创建一个命名空间并在其中部署一个 Pod
2. 使用 kubectl 的 -n 标志指定特定命名空间
3. 在命名空间上设置 ResourceQuota 以限制 CPU 和内存
4. 理解为什么集群级资源（Nodes、PersistentVolumes）不属于命名空间
5. 解释命名空间级资源与集群级资源的区别
6. 我理解了命名空间如何组织集群。那么——我究竟该如何在其中运行东西？
7. 我已经建好了命名空间，但现在盯着 kubectl 不知道该往里面放什么。我第一个真正要部署的是什么，又该如何确保它落到正确的命名空间里？
