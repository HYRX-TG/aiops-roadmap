---
id: namespace-strategy
title: Namespace Strategy for Production
zone: kubernetes-production
edges:
  to:
    - id: rbac-k8s
      question: >-
        Now that I have namespaces organized, how do I control who can deploy
        to each one?
      detail: >-
        I've got my namespace structure figured out. But I need to make sure
        developers can only touch the namespaces they own — not accidentally
        deploy to production or read secrets from another team's namespace.
difficulty: 3
tags:
  - kubernetes
  - namespaces
  - multi-tenancy
  - environments
  - isolation
  - k8s
  - production
  - organization
category: concept
milestones:
  - >-
    Understand what namespaces actually isolate — and what they don't: network
    traffic, node scheduling, and cluster-scoped resources are not namespace-isolated
  - >-
    Know the two main models: namespace-per-environment (dev/staging/prod in
    one cluster) vs cluster-per-environment, and the trade-offs of each
  - >-
    Understand namespace-per-team as a multi-tenancy pattern: each team owns
    their namespace(s) with scoped RBAC and ResourceQuotas
  - >-
    Know how ResourceQuotas and LimitRanges enforce resource boundaries at the
    namespace level — preventing one team from starving another
  - >-
    Understand when shared-cluster multi-tenancy breaks down and separate
    clusters become the right answer (hard compliance, noisy-neighbor problems)
title_zh: "生产环境的命名空间策略"

---


Namespaces are Kubernetes's primary mechanism for logical organization. But they're often misunderstood as security boundaries — they're not. Understanding what namespaces actually give you (and what they don't) determines whether your namespace structure is genuinely protective or just visually reassuring.

<!-- DEEP_DIVE -->

## What namespaces provide

**Name isolation** — two resources with the same name can coexist in different namespaces. `api` deployment in `team-a` and `api` deployment in `team-b` don't conflict.

**RBAC scope** — Role and RoleBinding objects are namespace-scoped. You can grant a service account read access to secrets in `team-a` without granting access to `team-b`.

**Resource quota scope** — ResourceQuotas apply per namespace. You can limit how much CPU, memory, and storage a namespace's workloads can consume in aggregate.

**Grouping for operations** — `kubectl get pods -n team-a` shows only that team's pods. Network policies, monitoring filters, and audit logs can all be scoped by namespace.

## What namespaces do NOT provide

**Network isolation** — a pod in namespace `staging` can make HTTP requests to a pod in namespace `production` using its ClusterIP. Namespaces have no network firewall effect by default. You need NetworkPolicies for that (and a CNI that enforces them).

**Node isolation** — pods from different namespaces can land on the same node and share its CPU, memory, and kernel. A runaway pod in staging can starve production pods on the same node if resource limits aren't enforced.

**Cluster-scoped resource isolation** — CRDs, ClusterRoles, StorageClasses, and PersistentVolumes are not namespace-scoped. Namespaces don't protect against cluster-level misconfiguration.

## Common namespace patterns

**Namespace per environment:**
```
production/
staging/
development/
```
Simple. Works for small teams. The risk: staging and production share the cluster; a production incident takes both down.

**Namespace per team:**
```
team-payments/
team-search/
team-platform/
```
Good for multi-team isolation. Each team owns their namespace(s). RBAC is straightforward. Resource quotas prevent noisy-neighbor problems.

**Namespace per team per environment:**
```
payments-prod/
payments-staging/
search-prod/
search-staging/
```
More granular but higher operational overhead. Makes sense for large organizations with strong team ownership.

## ResourceQuotas: limiting namespace consumption

Without quotas, one namespace can consume all cluster resources. ResourceQuotas prevent this:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-payments
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
```

The team's workloads can't exceed these limits in aggregate. If they try, new pods fail to schedule.

## LimitRanges: defaults and caps per pod

Without LimitRanges, pods without resource specifications run with no requests or limits (BestEffort QoS — first evicted under pressure). LimitRanges fix this:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: team-payments
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
      max:
        cpu: "4"
        memory: 4Gi
```

Pods that don't specify resource requests/limits get the defaults. Pods that request more than `max` are rejected. This enforces hygiene without requiring developers to know the exact values.

## When namespaces aren't enough

Namespace-level isolation breaks down for:

- **Hard multi-tenancy** — external customers or untrusted workloads sharing a cluster. Namespaces alone don't prevent a malicious pod from escaping to the host or accessing other tenants' data.
- **Compliance requirements** — PCI, HIPAA, and similar standards often require physical separation of production data. Namespaces in a shared cluster typically don't satisfy these.
- **Persistent noisy-neighbor problems** — a team consuming excessive node I/O or network bandwidth affects other namespaces on the same node. ResourceQuotas limit scheduling but don't control runtime resource consumption at the node level.

When you hit these limits, the answer is separate clusters — not more namespace configuration.

<!-- RESOURCES -->

- [Kubernetes Docs - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- type: docs, time: 15m
- [Kubernetes Docs - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- type: docs, time: 15m
- [Kubernetes Docs - Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Namespace 是 Kubernetes 进行逻辑组织的主要机制。但人们常常误以为它是安全边界——其实并不是。理解 namespace 实际提供了什么（以及不提供什么），决定了你的 namespace 结构是真正具有保护作用，还是仅仅在视觉上让人安心。

<!-- ZH_DEEP_DIVE -->
## 命名空间提供了什么

**名称隔离** — 两个同名资源可以在不同命名空间中共存。`team-a` 中的 `api` deployment 和 `team-b` 中的 `api` deployment 不会冲突。

**RBAC 作用域** — Role 和 RoleBinding 对象是命名空间级别的。你可以授予某个 service account 对 `team-a` 中 secret 的读取权限，而不授予对 `team-b` 的访问权限。

**资源配额作用域** — ResourceQuota 按命名空间生效。你可以限制某个命名空间的工作负载总共可以消耗多少 CPU、内存和存储。

**运维分组** — `kubectl get pods -n team-a` 只显示该团队的 pod。网络策略、监控过滤器和审计日志都可以按命名空间划分作用域。

## 命名空间不提供什么

**网络隔离** — `staging` 命名空间中的 pod 可以使用其 ClusterIP 向 `production` 命名空间中的 pod 发起 HTTP 请求。默认情况下，命名空间没有网络防火墙效果。你需要 NetworkPolicy 来实现这一点（以及一个能强制执行它们的 CNI）。

**节点隔离** — 来自不同命名空间的 pod 可以落在同一个节点上，共享其 CPU、内存和内核。如果没有强制执行资源限制，staging 中一个失控的 pod 可能会耗尽同一节点上 production pod 的资源。

**集群级资源隔离** — CRD、ClusterRole、StorageClass 和 PersistentVolume 不是命名空间级别的。命名空间无法防止集群级别的错误配置。

## 常见的命名空间模式

**每个环境一个命名空间：**
```
production/
staging/
development/
```
简单。适用于小型团队。风险在于：staging 和 production 共享集群；一次 production 故障会同时拖垮两者。

**每个团队一个命名空间：**
```
team-payments/
team-search/
team-platform/
```
适合多团队隔离。每个团队拥有自己的命名空间。RBAC 简单直接。资源配额可以防止吵闹邻居问题。

**每个团队每个环境一个命名空间：**
```
payments-prod/
payments-staging/
search-prod/
search-staging/
```
更细粒度，但运维开销更高。适合具有强团队归属感的大型组织。

## ResourceQuota：限制命名空间消耗

没有配额时，一个命名空间可以消耗所有集群资源。ResourceQuota 可以防止这种情况：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-payments
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
```

该团队的工作负载总计不能超过这些限制。如果尝试超过，新 pod 将无法调度。

## LimitRange：每个 pod 的默认值和上限

没有 LimitRange 时，未指定资源规格的 pod 会在没有 requests 或 limits 的情况下运行（BestEffort QoS——在资源压力下最先被驱逐）。LimitRange 可以解决这个问题：

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: team-payments
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
      max:
        cpu: "4"
        memory: 4Gi
```

未指定资源 requests/limits 的 pod 会获得默认值。请求超过 `max` 的 pod 会被拒绝。这样可以在不要求开发者了解确切数值的情况下强制执行规范。

## 命名空间不够用的情况

命名空间级别的隔离在以下情况下会失效：

- **硬多租户** — 外部客户或不受信任的工作负载共享一个集群。仅靠命名空间无法阻止恶意 pod 逃逸到宿主机或访问其他租户的数据。
- **合规要求** — PCI、HIPAA 及类似标准通常要求生产数据物理隔离。共享集群中的命名空间通常无法满足这些要求。
- **持续存在的吵闹邻居问题** — 一个团队消耗过多的节点 I/O 或网络带宽会影响同一节点上的其他命名空间。ResourceQuota 限制调度，但不控制节点级别的运行时资源消耗。

当你遇到这些限制时，答案是使用独立集群——而不是更多的命名空间配置。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- 类型: 文档, 时间: 15m
- [Kubernetes 文档 - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- 类型: 文档, 时间: 15m
- [Kubernetes 文档 - Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 理解命名空间实际隔离了什么、又没有隔离什么：网络流量、节点调度和集群级资源并不受命名空间隔离
2. 了解两种主要模型：按环境划分命名空间（dev/staging/prod 在同一集群）与按环境划分集群，以及各自的权衡
3. 理解按团队划分命名空间作为多租户模式：每个团队拥有自己的命名空间，并配有作用域化的 RBAC 和 ResourceQuota
4. 了解 ResourceQuota 和 LimitRange 如何在命名空间层面强制资源边界——防止一个团队耗尽另一个团队的资源
5. 理解共享集群多租户何时会失效、独立集群何时成为正确答案（严格合规、吵闹邻居问题）
6. 现在命名空间已经组织好了，我该如何控制谁可以部署到每个命名空间？
7. 命名空间结构已经理清了。但我需要确保开发者只能操作自己拥有的命名空间——不会误部署到生产环境，也不会读取其他团队命名空间中的 Secret。
