---
id: managed-vs-self-managed
title: Managed vs Self-Managed Kubernetes
zone: kubernetes-production
edges:
  to:
    - id: cluster-topology
      question: >-
        I know I'm using a managed cluster. Now — should I have one cluster or
        many?
      detail: >-
        I've got my managed cluster running but staging and production are in
        the same cluster separated by namespaces. I keep wondering whether
        that's actually good enough isolation or if I need separate clusters
        entirely.
    - id: cluster-upgrades
      question: >-
        New Kubernetes versions keep dropping. How do I actually upgrade without
        taking everything down?
      detail: >-
        My cluster is running 1.28 and I'm already two minor versions behind. I
        have no idea what the upgrade process looks like — whether my workloads
        survive it or whether there's a window of downtime I need to plan around.
difficulty: 2
tags:
  - kubernetes
  - eks
  - gke
  - aks
  - managed
  - control-plane
  - k8s
  - production
category: concept
milestones:
  - Understand what a control plane is and why running it yourself is hard
  - 'Know what EKS, GKE, and AKS handle for you vs what you still own'
  - >-
    Understand the real costs: managed isn't free, but operator time has a cost
    too
  - 'Know when self-managed (kubeadm, k3s) is actually the right call'
title_zh: "托管 vs 自管理 Kubernetes"

---


The Kubernetes control plane — the API server, etcd, the scheduler, the controller manager — is the most operationally demanding part of the system. Managed Kubernetes services like EKS, GKE, and AKS run the control plane for you. Self-managed means you own all of it. The choice determines how much of your time goes to Kubernetes infrastructure versus the workloads running on it.

<!-- DEEP_DIVE -->

## What the control plane actually is

The control plane is the brain of the cluster. When you run `kubectl apply`, the request goes to the API server. The scheduler decides which node gets the pod. The controller manager reconciles the desired state (3 replicas) against reality (2 running). etcd is the distributed key-value store that holds all cluster state.

Running this yourself means:
- Provisioning and maintaining multiple API server instances for HA
- Operating an etcd cluster (etcd has its own failure modes and backup requirements)
- Handling control plane upgrades without dropping the API surface
- Monitoring the control plane health separately from your workloads

None of these are insurmountable, but they're a full-time concern. etcd especially — a corrupted or lost etcd cluster is a total cluster loss.

## What managed clusters give you

EKS (AWS), GKE (Google Cloud), and AKS (Azure) all:
- Run and maintain the control plane in their infrastructure
- Handle HA across availability zones automatically
- Manage etcd backups
- Handle control plane version upgrades (to varying degrees)
- Integrate with cloud IAM, load balancers, and storage

You still own: your nodes, your workloads, add-on components (CNI, ingress controllers, monitoring), and node version upgrades. But the hardest operational piece is off your plate.

## EKS vs GKE vs AKS

These three are not equivalent in UX or features.

**GKE** is the most polished. Autopilot mode abstracts node management entirely. Built-in integration with Cloud Logging, Cloud Monitoring, and Google's networking stack. Generally considered the easiest experience.

**EKS** is the most widely deployed. AWS ecosystem integration is strong (IAM, ALB, EFS, Fargate). The experience is more DIY than GKE — more decisions left to you. Node group management is more manual.

**AKS** is strong if you're already in Azure. Azure AD integration, Windows node support. Generally considered between GKE and EKS in operational simplicity.

If you're cloud-agnostic, GKE. If you're already on AWS, EKS. If you're on Azure, AKS. The choice is usually determined by where the rest of your infrastructure lives.

## When self-managed makes sense

Self-managed Kubernetes (kubeadm, k3s, RKE2) makes sense when:
- You're on-premises with no managed option
- You're running at a scale where the per-cluster control plane cost matters ($150–$300/month for managed control planes adds up at hundreds of clusters)
- You have very specific Kubernetes API customization requirements
- You're at a large org with a dedicated platform team that wants full control

For most teams, managed is correct. The time cost of running a control plane yourself exceeds the money saved unless you have specific reasons to go self-managed.

## The real cost calculation

Managed isn't free — GKE, EKS, and AKS charge for the control plane even if it's just one cluster. But engineer time is expensive. Spending 20% of a senior engineer's time managing Kubernetes infrastructure instead of working on product quickly exceeds the cost of a managed cluster.

The honest rule: if you don't have someone who wants to specialize in Kubernetes operations, use a managed cluster.

<!-- RESOURCES -->

- [Kubernetes Docs - Production Environment](https://kubernetes.io/docs/setup/production-environment/) -- type: docs, time: 15m
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) -- type: docs, time: 20m
- [GKE Overview](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Kubernetes 控制平面——API server、etcd、调度器、控制器管理器——是系统运维要求最高的部分。EKS、GKE 和 AKS 等托管 Kubernetes 服务会为你运行控制平面。自管理则意味着这一切都由你负责。这一选择决定了你花在 Kubernetes 基础设施上的时间与花在其上运行的工作负载上的时间各占多少。

<!-- ZH_DEEP_DIVE -->
## 控制平面到底是什么

控制平面是集群的大脑。当你执行 `kubectl apply` 时，请求会发送到 API server。调度器决定哪个节点获得该 Pod。controller manager 将期望状态（3 个副本）与实际状态（2 个正在运行）进行调和。etcd 是保存所有集群状态的分布式键值存储。

自行运行控制平面意味着：
- 为高可用而预置并维护多个 API server 实例
- 运维 etcd 集群（etcd 有其自身的故障模式和备份要求）
- 在不中断 API 表面的情况下处理控制平面升级
- 将控制平面健康监控与工作负载监控分开进行

这些都不是无法克服的，但它们是全职关注的事项。尤其是 etcd——etcd 集群损坏或丢失就意味着整个集群丢失。

## 托管集群为你提供了什么

EKS（AWS）、GKE（Google Cloud）和 AKS（Azure）都会：
- 在其基础设施中运行并维护控制平面
- 自动处理跨可用区的高可用
- 管理 etcd 备份
- 处理控制平面版本升级（程度各不相同）
- 与云 IAM、负载均衡器和存储集成

你仍然拥有：你的节点、你的工作负载、附加组件（CNI、ingress controller、监控）以及节点版本升级。但最困难的那部分运维工作已经不在你身上了。

## EKS vs GKE vs AKS

这三者在用户体验或功能上并不等同。

**GKE** 是最精致的。Autopilot 模式完全抽象了节点管理。与 Cloud Logging、Cloud Monitoring 和 Google 网络栈内置集成。通常被认为体验最轻松。

**EKS** 是部署最广泛的。AWS 生态集成很强（IAM、ALB、EFS、Fargate）。体验比 GKE 更偏 DIY——更多决策留给你。节点组管理更手动。

**AKS** 如果你已经在 Azure 上，则很强。Azure AD 集成、Windows 节点支持。在运维简便性上通常被认为介于 GKE 和 EKS 之间。

如果你云无关，选 GKE。如果你已经在 AWS 上，选 EKS。如果你在 Azure 上，选 AKS。选择通常由你其余基础设施所在的位置决定。

## 自管理何时有意义

自管理 Kubernetes（kubeadm、k3s、RKE2）在以下情况下有意义：
- 你在本地部署，没有托管选项
- 你的规模大到每集群控制平面成本变得重要（托管控制平面每月 $150–$300，在数百个集群时会累积起来）
- 你有非常特定的 Kubernetes API 定制需求
- 你在一家大型组织，拥有想要完全控制的专职平台团队

对大多数团队来说，托管是正确的。自行运行控制平面的时间成本超过节省的金钱，除非你有特定理由选择自管理。

## 真实的成本计算

托管并非免费——GKE、EKS 和 AKS 即使只有一个集群也会对控制平面收费。但工程师时间很昂贵。把一位高级工程师 20% 的时间花在管理 Kubernetes 基础设施而不是产品工作上，很快就会超过托管集群的成本。

诚实的规则：如果你没有想要专攻 Kubernetes 运维的人，就使用托管集群。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 生产环境](https://kubernetes.io/docs/setup/production-environment/) -- 类型: 文档, 时间: 15m
- [AWS EKS 文档](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) -- 类型: 文档, 时间: 20m
- [GKE 概览](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 理解什么是控制平面，以及为什么自行运行控制平面很困难
2. 了解 EKS、GKE 和 AKS 为你处理了什么，以及你仍然需要负责什么
3. 理解真实成本：托管并非免费，但运维人员的时间也有成本
4. 知道什么时候自管理（kubeadm、k3s）才是真正正确的选择
5. 我知道我在使用托管集群。那么——我应该用一个集群还是多个集群？
6. 我的托管集群已经运行起来了，但预发和生产在同一个集群里，用命名空间隔开。我一直在想，这算不算足够好的隔离，还是说我需要完全独立的集群。
7. 新的 Kubernetes 版本不断发布。我怎样才能真正完成升级而不让一切宕机？
8. 我的集群运行的是 1.28，我已经落后两个小版本了。我完全不知道升级流程是什么样的——我的工作负载能否挺过去，还是说有一段停机窗口需要我提前规划。
