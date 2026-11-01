---
id: cluster-topology
title: One Cluster or Many?
zone: kubernetes-production
edges:
  to:
    - id: node-pools
      question: >-
        I've decided on my cluster structure. Now how do I actually carve up the
        machines inside it?
      detail: >-
        I know whether I want one cluster or many. But now I need to figure out
        what the actual machines look like — different sizes, different roles.
        My GPU workloads and my web servers probably shouldn't run on the same
        nodes.
difficulty: 2
tags:
  - kubernetes
  - cluster
  - multi-cluster
  - namespaces
  - isolation
  - blast-radius
  - k8s
  - production
category: concept
milestones:
  - >-
    Understand the tradeoffs between per-environment clusters vs namespaces in
    one cluster
  - Know what 'blast radius' means and why isolation matters
  - Understand the operational cost of running multiple clusters
  - Know when a single cluster with namespaces is good enough
title_zh: "一个集群还是多个？"

---


One cluster with namespaces, or separate clusters per environment? This is one of the first architectural decisions in production Kubernetes and there's no universal right answer — only trade-offs that depend on your team size, compliance requirements, and operational appetite.

<!-- DEEP_DIVE -->

## What namespaces actually give you

Namespaces provide:
- **Name isolation** — two deployments named `api` can coexist in `staging` and `production` namespaces
- **RBAC scope** — Role bindings can be scoped to a namespace
- **Resource quota scope** — ResourceQuotas apply per namespace
- **Logical grouping** — `kubectl get pods -n staging` filters to just that namespace

Namespaces do *not* provide:
- **Network isolation** — a pod in `staging` can by default reach a pod in `production` over the cluster network
- **Node isolation** — staging and production pods land on the same nodes
- **Cluster-scoped resource isolation** — CRDs, ClusterRoles, StorageClasses are cluster-wide
- **Blast radius isolation** — a bug in the API server or etcd affects all namespaces simultaneously

Namespaces are a soft boundary. They work well for team organization. They're not a security perimeter.

## The case for separate clusters per environment

**Blast radius containment** — a botched production deploy, a cluster-level misconfiguration, or a control plane incident is scoped to that cluster. Staging problems cannot take down production.

**Independent upgrade schedules** — you can run Kubernetes 1.30 in production and 1.31 in staging to validate the upgrade before committing to production.

**Compliance and audit requirements** — some regulations require production data to be isolated from non-production environments. Namespaces don't satisfy this; separate clusters do.

**Different node sizing** — production might need beefy nodes with specific instance types; staging can run on cheap spot instances.

The cost: every cluster is an operational artifact. Secrets, ingress, monitoring, cluster add-ons — all duplicated. Upgrading five clusters is five times the work of upgrading one.

## The case for namespaces in one cluster

**Operational simplicity** — one cluster to monitor, upgrade, and maintain. Cluster add-ons (cert-manager, ingress controller, monitoring) installed once.

**Cost** — managed control planes charge per cluster. One cluster is cheaper.

**Developer experience** — easier to give developers access to a namespace than to manage kubeconfig files for multiple clusters.

The cost: weaker isolation. If you care about staging pods being on different nodes than production pods, or about network-level separation, you need more configuration (NetworkPolicies, PodAntiAffinity, taints) to compensate.

## The most common pattern in practice

Most teams land here: **production is its own cluster; staging and development share a second cluster** (sometimes separated by namespace, sometimes together).

This gives you:
- Strong isolation for production (the thing that matters most)
- One cluster to manage for non-production (acceptable risk; shared cost)

Teams with strong compliance requirements, regulated data, or multiple internal teams often move to a cluster-per-environment model as they grow.

## Multi-cluster complexity

If you go multi-cluster, be prepared for:
- Managing separate kubeconfig contexts and auth for each cluster
- Deploying the same workloads to multiple clusters (GitOps helps here significantly)
- Service discovery across clusters (no built-in solution — needs extra tooling)
- Multiple ingress configurations and certificates

Multi-cluster management is a real operational cost. Don't add clusters you don't need.

<!-- RESOURCES -->

- [Kubernetes Docs - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- type: docs, time: 15m
- [Kubernetes Docs - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
一个集群用命名空间划分，还是每个环境独立集群？这是生产 Kubernetes 的首批架构决策之一，没有放之四海而皆准的正确答案——只有取决于团队规模、合规要求和运维意愿的权衡取舍。

<!-- ZH_DEEP_DIVE -->
## Namespace 实际能提供什么

Namespace 提供：
- **名称隔离** —— 两个都叫 `api` 的 Deployment 可以分别存在于 `staging` 和 `production` namespace 中
- **RBAC 作用域** —— Role 绑定可以限定在某个 namespace 内
- **资源配额作用域** —— ResourceQuota 按 namespace 生效
- **逻辑分组** —— `kubectl get pods -n staging` 只筛选该 namespace 下的资源

Namespace *不* 提供：
- **网络隔离** —— 默认情况下，`staging` 中的 Pod 可以通过集群网络访问 `production` 中的 Pod
- **节点隔离** —— staging 和 production 的 Pod 会落在相同的节点上
- **集群级资源隔离** —— CRD、ClusterRole、StorageClass 都是集群范围的
- **爆炸半径隔离** —— API server 或 etcd 的故障会同时影响所有 namespace

Namespace 是软边界。它们很适合做团队组织。但它们不是安全边界。

## 每个环境使用独立集群的理由

**爆炸半径控制** —— 一次搞砸的生产部署、一次集群级错误配置、或一次控制平面事故，影响范围都被限制在该集群内。staging 的问题不会拖垮 production。

**独立的升级节奏** —— 你可以在 production 运行 Kubernetes 1.30，在 staging 运行 1.31，在正式升级 production 之前先验证升级。

**合规与审计要求** —— 某些法规要求生产数据与非生产环境隔离。Namespace 无法满足这一要求；独立集群可以。

**不同的节点规格** —— production 可能需要特定实例类型的强劲节点；staging 可以跑在便宜的 spot 实例上。

代价是：每个集群都是一个运维产物。Secret、ingress、监控、集群插件 —— 全都要重复部署。升级五个集群的工作量是升级一个集群的五倍。

## 单集群内使用 namespace 的理由

**运维简单** —— 只需监控、升级和维护一个集群。集群插件（cert-manager、ingress controller、监控）只安装一次。

**成本** —— 托管控制平面按集群收费。一个集群更便宜。

**开发者体验** —— 给开发者一个 namespace 的访问权限，比管理多个集群的 kubeconfig 文件更容易。

代价是：隔离更弱。如果你在意 staging Pod 与 production Pod 落在不同节点上，或者在意网络层面的隔离，就需要更多配置（NetworkPolicy、PodAntiAffinity、taint）来弥补。

## 实践中最常见的模式

大多数团队最终采用这个方案：**production 使用独立集群；staging 和 development 共享第二个集群**（有时用 namespace 分隔，有时混在一起）。

这给你带来：
- production 的强隔离（最重要的事）
- 非生产环境只需管理一个集群（风险可接受；成本共担）

有强合规要求、受监管数据、或多个内部团队的团队，随着规模增长，往往会转向每个环境一个集群的模式。

## 多集群的复杂性

如果你选择多集群，要做好准备应对：
- 为每个集群管理独立的 kubeconfig context 和认证
- 将相同的工作负载部署到多个集群（GitOps 在这方面帮助很大）
- 跨集群的服务发现（没有内置方案 —— 需要额外工具）
- 多套 ingress 配置和证书

多集群管理是实实在在的运维成本。不要添加你不需要的集群。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- 类型: 文档, 时间: 15m
- [Kubernetes 文档 - Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 理解按环境划分集群与在单一集群中使用命名空间之间的权衡
2. 了解“爆炸半径”的含义以及隔离为何重要
3. 理解运行多个集群的运维成本
4. 知道何时单一集群加命名空间就已足够
5. 我已确定集群结构。那么我究竟该如何划分集群内的机器？
6. 我知道自己想要一个集群还是多个集群。但现在我需要弄清楚实际机器该是什么样——不同规格、不同角色。我的 GPU 工作负载和 Web 服务器大概不应运行在同一批节点上。
