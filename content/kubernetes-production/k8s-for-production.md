---
id: k8s-for-production
title: Taking Kubernetes to Production
zone: kubernetes-production
edges:
  to:
    - id: managed-vs-self-managed
      question: >-
        Do I even need to run the cluster control plane myself, or is there a
        better way?
      detail: >-
        Setting up the control plane myself sounds like a full-time job — etcd,
        the API server, controller manager. Surely there's a way to just get a
        cluster without having to operate all of that infrastructure?
    - id: managing-k8s-manifests
      question: >-
        My YAML files are getting messy across environments. How do I manage
        this properly?
      detail: >-
        I have staging and production and I've been copying and editing YAML
        between them. It's already drifting and I'm only two environments in.
        There has to be a better approach than copy-paste.
    - id: rbac-k8s
      question: >-
        How do I control who can actually do what in my cluster — without giving
        everyone admin access?
      detail: >-
        Right now anyone with the kubeconfig can do anything — delete namespaces,
        read secrets, scale down production. I need a way to give developers just
        enough access without handing them the keys to everything.
difficulty: 2
tags:
  - kubernetes
  - production
  - k8s
  - concept
category: concept
milestones:
  - Understand what changes between local K8s and production K8s
  - >-
    Know what 'production-grade' means: HA control plane, node pools, storage
    classes
  - Understand why raw YAML manifests don't scale for real workloads
title_zh: "将 Kubernetes 投入生产环境"

---


Running Kubernetes locally is not the same as running it in production. A local cluster has one node, no real storage, no access control, and nobody cares if it dies. Production means real users, real data, and real consequences when things go wrong. The gap between the two is where most of the hard lessons live.

<!-- DEEP_DIVE -->

## What actually changes in production

In a local cluster you can skip almost everything: no RBAC, no resource limits, no health checks, no autoscaling. It works because nothing important depends on it.

In production, each of those skipped pieces becomes a failure mode:

- **No resource limits** — one misbehaving pod starves everything else on the node
- **No health checks** — Kubernetes routes traffic to pods that are starting up or broken
- **No graceful shutdown** — in-flight requests die when pods are replaced
- **No access control** — any CI token can delete production namespaces
- **Manifests managed by hand** — environments drift, changes are unreproducible, rollback is manual

Production Kubernetes is really a set of operational disciplines layered on top of the basics you already know.

## The production checklist (conceptually)

**Cluster reliability:**
- Managed control plane (you don't run etcd yourself)
- Nodes in multiple availability zones
- Node pools sized for your actual workloads

**Workload reliability:**
- Resource requests and limits on every container
- Liveness, readiness, and startup probes configured correctly
- Graceful shutdown handled in application code
- Pods spread across nodes and zones
- PodDisruptionBudgets so upgrades don't take you down

**Scaling:**
- HPA for handling traffic spikes
- Node autoscaling so you're not paying for idle capacity

**Manifest management:**
- Kustomize or Helm — not copy-paste YAML
- GitOps — the cluster's desired state is in Git, not in someone's head

**Security:**
- RBAC — least privilege for humans and CI systems
- Secrets stored in a real secret store, not base64 in Git
- Network policies — pods can't reach everything by default

**Operations:**
- A safe upgrade process for Kubernetes versions
- Multi-environment promotion (staging before production)

None of these are optional if you're running something people depend on.

## The mindset shift

Local Kubernetes teaches you the API. Production Kubernetes teaches you what happens when the API is used by real workloads under real conditions.

The questions change. It's no longer "how do I deploy this?" It's "what happens when this pod gets evicted?" and "how does my app behave when it receives SIGTERM?" and "what happens if the node this pod is on disappears?"

Kubernetes gives you powerful primitives. The production work is configuring those primitives to match how you actually want your system to behave.

<!-- RESOURCES -->

- [Kubernetes Docs - Production Best Practices](https://kubernetes.io/docs/setup/production-environment/) -- type: docs, time: 20m
- [Kubernetes Docs - Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
在本地运行 Kubernetes 与在生产环境中运行并不相同。本地集群只有一个节点，没有真正的存储，没有访问控制，而且即使它挂了也没人在意。生产环境则意味着真实的用户、真实的数据，以及出问题时真实的后果。两者之间的差距，正是大多数深刻教训所在之处。

<!-- ZH_DEEP_DIVE -->
## 生产环境中实际会发生哪些变化

在本地集群中，你几乎可以跳过所有东西：没有 RBAC，没有资源限制，没有健康检查，没有自动扩缩容。它能正常工作，是因为没有什么重要的东西依赖它。

在生产环境中，每一个被跳过的部分都会变成一种故障模式：

- **没有资源限制** —— 一个行为异常的 Pod 会耗尽节点上其他所有 Pod 的资源
- **没有健康检查** —— Kubernetes 会把流量路由到正在启动或已经损坏的 Pod
- **没有优雅关闭** —— Pod 被替换时，正在处理的请求会直接失败
- **没有访问控制** —— 任何 CI token 都能删除生产命名空间
- **清单靠手工管理** —— 环境发生漂移，变更无法复现，回滚只能手动操作

生产级 Kubernetes 实际上是在你已经掌握的基础之上叠加的一整套运维规范。

## 生产环境检查清单（概念层面）

**集群可靠性：**
- 托管控制平面（你不自己运行 etcd）
- 节点分布在多个可用区
- 节点池按你的实际工作负载规模配置

**工作负载可靠性：**
- 每个容器都配置资源 requests 和 limits
- 正确配置 liveness、readiness 和 startup 探针
- 在应用代码中处理优雅关闭
- Pod 分散到不同节点和可用区
- 配置 PodDisruptionBudget，避免升级导致服务中断

**扩缩容：**
- 用 HPA 应对流量高峰
- 节点自动扩缩容，避免为闲置容量付费

**清单管理：**
- 使用 Kustomize 或 Helm —— 而不是复制粘贴 YAML
- GitOps —— 集群的期望状态在 Git 中，而不是在某个人的脑子里

**安全：**
- RBAC —— 对人和 CI 系统都遵循最小权限原则
- Secret 存储在真正的密钥存储中，而不是以 base64 形式放在 Git 里
- 网络策略 —— 默认情况下 Pod 不能访问所有东西

**运维：**
- 为 Kubernetes 版本制定安全的升级流程
- 多环境晋级（先 staging 再 production）

如果你运行的东西有人依赖，以上没有一项是可选的。

## 思维方式的转变

本地 Kubernetes 教你的是 API。生产 Kubernetes 教你的则是：当 API 被真实工作负载在真实条件下使用时会发生什么。

问题变了。不再是“我怎么部署这个？”，而是“这个 Pod 被驱逐时会发生什么？”、“我的应用收到 SIGTERM 时行为如何？”以及“如果这个 Pod 所在的节点消失了会怎样？”

Kubernetes 为你提供了强大的原语。生产环境的工作，就是把这些原语配置成你真正希望系统表现出的行为。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 生产环境最佳实践](https://kubernetes.io/docs/setup/production-environment/) -- 类型：文档，时长：20 分钟
- [Kubernetes 文档 - 配置最佳实践](https://kubernetes.io/docs/concepts/configuration/overview/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 理解本地 K8s 与生产环境 K8s 之间的差异
2. 了解“生产级”意味着什么：高可用控制平面、节点池、存储类
3. 理解为什么原始 YAML 清单无法支撑真实工作负载的规模
4. 我是否真的需要自己运行集群控制平面，还是有更好的方式？
5. 自己搭建控制平面听起来像是一份全职工作——etcd、API server、controller manager。肯定有办法直接获得一个集群，而无需运维所有这些基础设施吧？
6. 我的 YAML 文件跨环境变得越来越混乱。我该如何妥善管理？
7. 我有预发和生产环境，一直在它们之间复制和编辑 YAML。才两个环境就已经开始漂移了。肯定有比复制粘贴更好的办法。
8. 我如何控制谁能在集群里做什么——而不给每个人管理员权限？
9. 现在任何拿到 kubeconfig 的人都能做任何事——删除命名空间、读取密钥、缩容生产环境。我需要一种方式，只给开发者刚好够用的权限，而不是把一切都交给他们。
