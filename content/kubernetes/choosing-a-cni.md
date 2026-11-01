---
id: choosing-a-cni
title: Choosing a CNI Plugin
zone: kubernetes
edges:
  to:
    - id: ebpf-and-cilium
      question: >-
        Cilium keeps coming up as the answer to everything — networking,
        security, observability. What makes it so different from the others?
      detail: >-
        Every comparison ends with 'or just use Cilium.' It apparently uses
        something called eBPF to handle networking directly in the kernel, can
        replace kube-proxy, enforces network policies, and gives you visibility
        into every network flow. That sounds too good to be true. What's the
        catch, and what even is eBPF?
difficulty: 2
tags:
  - kubernetes
  - cni
  - flannel
  - calico
  - cilium
  - networking
  - k8s
category: concept
milestones:
  - >-
    Know Flannel: simplest CNI, overlay-only, no network policy enforcement —
    fine for learning and dev clusters
  - >-
    Know Calico: supports BGP and overlay, enforces network policies, mature and
    widely deployed in production
  - >-
    Know Cilium: eBPF-based, network policies, can replace kube-proxy, built-in
    observability with Hubble
  - >-
    Understand cloud provider CNIs (AWS VPC CNI, Azure CNI, GKE native): tight
    integration with cloud networking, limited portability
  - >-
    Know what Canal is: Flannel's networking with Calico's network policy
    enforcement — a common combination
  - >-
    Be able to pick a CNI based on actual needs: do you need network policies?
    eBPF? Cloud-native IPs? Performance? Start there.
title_zh: "选择 CNI 插件"

---


Your CNI plugin is one of the most consequential decisions in a Kubernetes cluster — it determines how traffic moves, whether network policies work, what observability you get, and how the cluster performs at scale. The bad news: there are a lot of options. The good news: for most clusters, the decision comes down to a few key questions about what features you actually need.

<!-- DEEP_DIVE -->

## Flannel

Flannel is the simplest CNI. It creates an overlay network using VXLAN and assigns each node a subnet from the cluster's pod CIDR. That's it — it does the minimum to make pod-to-pod networking work.

**Good for:** Learning, development clusters, simple environments where you don't need network policies.

**Limitations:** No network policy enforcement at all. If you apply a NetworkPolicy resource with Flannel, nothing happens — the policy exists in the API but nobody enforces it. Overlay-only (no BGP mode). Minimal features.

## Calico

Calico is the most widely deployed production CNI. It supports both overlay (VXLAN) and native routing (BGP), enforces network policies, and is mature and battle-tested.

**Good for:** Production clusters that need network policies. On-prem environments where you want BGP for performance. Any cluster where you want a proven, well-documented option.

**Key features:**
- Network policy enforcement (standard Kubernetes NetworkPolicy + Calico's own extended policies)
- BGP mode for native routing (no overlay overhead)
- VXLAN mode when BGP isn't possible
- Felix agent on each node handles policy enforcement and route programming
- Large community and extensive documentation

**Limitations:** Doesn't have Cilium's eBPF-based observability or kube-proxy replacement. Configuration can get complex in large environments.

## Cilium

Cilium uses eBPF to handle networking at the kernel level instead of relying on iptables. It's the newest of the major CNIs but has rapidly become the default choice for new production clusters — including being the default CNI for GKE.

**Good for:** Production clusters that want performance, observability, and advanced features. Teams that want to replace kube-proxy. Environments where network visibility matters.

**Key features:**
- eBPF-based data plane — no iptables for pod networking or service routing
- Can fully replace kube-proxy for service routing
- Hubble: built-in network observability (see every flow, protocol-aware)
- Network policy enforcement (Kubernetes policies + Cilium's L7-aware policies)
- Optional transparent encryption (WireGuard or IPsec)
- Can act as an ingress controller and even a service mesh

GKE Autopilot uses Cilium's eBPF data plane under the hood (called "Dataplane V2"), though it's not a full Cilium install — no Hubble or CiliumNetworkPolicy CRDs out of the box.

**Limitations:** Requires a relatively modern Linux kernel (5.4+). More complex to operate than Flannel or basic Calico. The breadth of features means more to learn.

## Canal

Canal is Flannel + Calico combined. It uses Flannel for the networking (VXLAN overlay) and Calico for network policy enforcement. It exists because people wanted Flannel's simplicity with network policies.

**Good for:** When you already use Flannel and want to add network policy support without a full migration.

**Honestly:** If you're starting fresh, just pick Calico or Cilium. Canal exists for historical reasons — it solves a problem that Calico already solves on its own.

## Cloud provider CNIs

Each major cloud has its own CNI that integrates pod networking with the cloud's virtual network:

- **AWS VPC CNI** — pods get real VPC IPs. No overlay. Tight integration with security groups and VPC networking. Limited by ENI IP capacity per instance type.
- **Azure CNI** — pods get IPs from the Azure VNet. Deep integration with Azure networking and Network Security Groups.
- **GKE** — GKE now defaults to Cilium (Dataplane V2). Previously used a custom CNI with native VPC routing.

Cloud CNIs give you the best integration with cloud networking (security groups apply to pods, native VPC routing), but they lock you into that cloud and have IP address constraints.

## How to decide

Start with these questions:

1. **Do you need network policies?** If yes, eliminate Flannel.
2. **Are you on a managed cloud service?** Consider the cloud's native CNI for simplest integration. GKE already defaults to Cilium.
3. **Do you want network observability out of the box?** Cilium with Hubble gives you visibility into every network flow without extra tooling.
4. **Is performance critical?** Cilium's eBPF path or Calico's BGP mode — both avoid overlay overhead.
5. **Do you want to simplify by replacing kube-proxy?** Only Cilium does this.
6. **Are you running on-prem with BGP routers?** Calico's BGP mode is the most mature option.

For a new production cluster today, Cilium is increasingly the default choice. For an established cluster that already runs Calico well, there's no urgent reason to switch.

<!-- RESOURCES -->

- [Calico Documentation](https://docs.tigera.io/calico/latest/about/) -- type: docs, time: 20m
- [Cilium Documentation](https://docs.cilium.io/) -- type: docs, time: 20m
- [Kubernetes CNI Benchmark](https://itnext.io/benchmark-results-of-kubernetes-network-plugins-cni-over-40gbit-s-network-2024-156f085a5e4e) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
你的 CNI 插件是 Kubernetes 集群中影响最深远的决策之一——它决定了流量的走向、网络策略是否生效、你能获得怎样的可观测性，以及集群在规模化时的性能表现。坏消息是：可选方案非常多。好消息是：对大多数集群而言，这个决策最终归结为几个关键问题，即你实际需要哪些功能。

<!-- ZH_DEEP_DIVE -->
## Flannel

Flannel 是最简单的 CNI。它使用 VXLAN 创建 overlay 网络，并从集群的 pod CIDR 中为每个节点分配一个子网。就是这样——它只做让 pod 到 pod 网络通信正常工作所需的最低限度工作。

**适用于：** 学习、开发集群、不需要网络策略的简单环境。

**限制：** 完全不执行网络策略。如果你用 Flannel 应用一个 NetworkPolicy 资源，什么也不会发生——策略存在于 API 中，但没有人执行它。仅支持 overlay（没有 BGP 模式）。功能极少。

## Calico

Calico 是部署最广泛的生产级 CNI。它同时支持 overlay（VXLAN）和原生路由（BGP），执行网络策略，并且成熟且经过实战检验。

**适用于：** 需要网络策略的生产集群。希望用 BGP 提升性能的本地环境。任何想要一个经过验证、文档完善的选项的集群。

**关键特性：**
- 网络策略执行（标准 Kubernetes NetworkPolicy + Calico 自有的扩展策略）
- BGP 模式用于原生路由（无 overlay 开销）
- 当 BGP 不可行时使用 VXLAN 模式
- 每个节点上的 Felix agent 负责策略执行和路由编程
- 庞大的社区和详尽的文档

**限制：** 没有 Cilium 基于 eBPF 的可观测性或 kube-proxy 替换能力。在大型环境中配置可能变得复杂。

## Cilium

Cilium 使用 eBPF 在内核层面处理网络，而不是依赖 iptables。它是主要 CNI 中最新的一个，但已迅速成为新生产集群的默认选择——包括成为 GKE 的默认 CNI。

**适用于：** 想要性能、可观测性和高级功能的生产集群。想要替换 kube-proxy 的团队。网络可见性很重要的环境。

**关键特性：**
- 基于 eBPF 的数据平面——pod 网络和服务路由不使用 iptables
- 可以完全替换 kube-proxy 进行服务路由
- Hubble：内置网络可观测性（查看每个流，协议感知）
- 网络策略执行（Kubernetes 策略 + Cilium 的 L7 感知策略）
- 可选的透明加密（WireGuard 或 IPsec）
- 可以充当 ingress controller，甚至 service mesh

GKE Autopilot 在底层使用 Cilium 的 eBPF 数据平面（称为 "Dataplane V2"），尽管它不是完整的 Cilium 安装——开箱即用没有 Hubble 或 CiliumNetworkPolicy CRD。

**限制：** 需要相对较新的 Linux 内核（5.4+）。运维比 Flannel 或基础 Calico 更复杂。功能广度意味着需要学习的东西更多。

## Canal

Canal 是 Flannel + Calico 的组合。它使用 Flannel 进行网络（VXLAN overlay），使用 Calico 执行网络策略。它存在是因为人们想要 Flannel 的简单性加上网络策略。

**适用于：** 当你已经使用 Flannel 并想在不完全迁移的情况下添加网络策略支持时。

**说实话：** 如果你是从零开始，直接选 Calico 或 Cilium。Canal 的存在有历史原因——它解决的问题 Calico 自己就能解决。

## 云厂商 CNI

每个主要云厂商都有自己的 CNI，将 pod 网络与云的虚拟网络集成：

- **AWS VPC CNI** — pod 获得真实的 VPC IP。无 overlay。与安全组和 VPC 网络紧密集成。受每种实例类型的 ENI IP 容量限制。
- **Azure CNI** — pod 从 Azure VNet 获得 IP。与 Azure 网络和网络安全组深度集成。
- **GKE** — GKE 现在默认使用 Cilium（Dataplane V2）。之前使用带原生 VPC 路由的自定义 CNI。

云 CNI 为你提供与云网络的最佳集成（安全组应用于 pod、原生 VPC 路由），但它们将你锁定在该云中，并且有 IP 地址约束。

## 如何决策

从这些问题开始：

1. **你需要网络策略吗？** 如果需要，排除 Flannel。
2. **你在托管云服务上吗？** 考虑云的原生 CNI 以获得最简单的集成。GKE 已经默认使用 Cilium。
3. **你想要开箱即用的网络可观测性吗？** Cilium 配合 Hubble 让你无需额外工具就能看到每个网络流。
4. **性能是否关键？** Cilium 的 eBPF 路径或 Calico 的 BGP 模式——两者都避免 overlay 开销。
5. **你想通过替换 kube-proxy 来简化吗？** 只有 Cilium 能做到这一点。
6. **你在本地运行且有 BGP 路由器吗？** Calico 的 BGP 模式是最成熟的选项。

对于今天的新生产集群，Cilium 正日益成为默认选择。对于已经良好运行 Calico 的现有集群，没有紧急理由去切换。

<!-- ZH_RESOURCES -->
- [Calico 文档](https://docs.tigera.io/calico/latest/about/) -- 类型：文档，时长：20m
- [Cilium 文档](https://docs.cilium.io/) -- 类型：文档，时长：20m
- [Kubernetes CNI 基准测试](https://itnext.io/benchmark-results-of-kubernetes-network-plugins-cni-over-40gbit-s-network-2024-156f085a5e4e) -- 类型：文章，时长：15m

<!-- ZH_UI -->
1. 了解 Flannel：最简单的 CNI，仅支持 overlay，不执行网络策略——适合学习和开发集群
2. 了解 Calico：支持 BGP 和 overlay，执行网络策略，成熟且在生产环境中广泛部署
3. 了解 Cilium：基于 eBPF，支持网络策略，可替代 kube-proxy，通过 Hubble 提供内置可观测性
4. 理解云厂商 CNI（AWS VPC CNI、Azure CNI、GKE 原生）：与云网络紧密集成，可移植性有限
5. 了解 Canal 是什么：Flannel 的网络加上 Calico 的网络策略执行——一种常见组合
6. 能根据实际需求选择 CNI：你需要网络策略吗？eBPF？云原生 IP？性能？从这里开始。
7. Cilium 总是作为一切问题的答案出现——网络、安全、可观测性。它与其他方案究竟有何不同？
8. 每次对比都以“或者直接用 Cilium”结尾。它显然用了叫 eBPF 的东西直接在内核中处理网络，可以替代 kube-proxy，执行网络策略，还能让你看清每一条网络流。听起来好得不像真的。有什么坑，eBPF 到底是什么？
