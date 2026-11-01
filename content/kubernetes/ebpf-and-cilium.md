---
id: ebpf-and-cilium
title: eBPF and Why It Changes Kubernetes Networking
zone: kubernetes
edges:
  to:
    - id: network-policies
      zone: kubernetes-production
      question: >-
        I understand how the network works now — I want to actually lock down
        which pods can talk to which.
      detail: >-
        My cluster has a flat network where any pod can reach any other pod. Now
        that I understand CNI, eBPF, and how traffic flows, I want to put up
        walls. A compromised pod in one namespace shouldn't be able to reach the
        database in another.
difficulty: 3
tags:
  - kubernetes
  - ebpf
  - cilium
  - hubble
  - networking
  - k8s
category: concept
milestones:
  - >-
    Understand what eBPF is: small programs that run inside the Linux kernel,
    attached to hooks like network events
  - >-
    Know why eBPF matters for networking: make routing decisions at the kernel
    level, skip iptables entirely
  - >-
    Understand Cilium's model: eBPF programs handle pod networking, service
    routing, network policies, and observability in a single layer
  - >-
    Know what Hubble is: Cilium's observability layer that shows every network
    flow without needing tcpdump
  - >-
    Understand how Cilium replaces kube-proxy: eBPF handles ClusterIP routing
    instead of iptables rules
  - >-
    Know when eBPF is overkill (small clusters, simple needs) vs when it's
    essential (scale, visibility, performance)
title_zh: "eBPF 及其为何改变 Kubernetes 网络"

---


eBPF (extended Berkeley Packet Filter) lets you run small programs directly inside the Linux kernel, attached to events like network packets arriving or leaving. Cilium uses eBPF to handle Kubernetes networking at the kernel level — bypassing iptables entirely. This isn't just a different CNI; it's a fundamentally different approach to how the cluster processes network traffic, and it unlocks things that iptables-based networking can't do.

<!-- DEEP_DIVE -->

## What is eBPF?

Traditionally, if you wanted to change how the Linux kernel handles network packets, you had two options: modify the kernel source code (impractical) or use iptables rules (limited). eBPF introduces a third option: load small, verified programs into the kernel that run when specific events happen.

An eBPF program can:
- Inspect every packet entering or leaving a network interface
- Make routing decisions (forward, drop, redirect)
- Collect metrics about traffic patterns
- Modify packet headers

The kernel verifies every eBPF program before loading it — it checks that the program terminates, doesn't access invalid memory, and can't crash the kernel. This safety guarantee is what makes it practical for production use.

## Why iptables is the bottleneck

Traditional Kubernetes networking relies heavily on iptables. kube-proxy programs iptables rules for every Service, and CNIs like Calico use iptables for network policy enforcement. The problem:

- **Linear scanning** — iptables evaluates rules one by one. With thousands of Services, every packet traverses thousands of rules.
- **Full table replacement** — updating a single Service requires rewriting all iptables rules atomically. With 10,000 Services, this gets slow.
- **No awareness** — iptables operates at L3/L4 (IPs and ports). It can't make decisions based on HTTP headers, gRPC methods, or DNS names.

eBPF replaces this with hash-table lookups. Instead of scanning a chain of rules, the eBPF program does an O(1) lookup in a map: "traffic to ClusterIP X → redirect to Pod Y." This is dramatically faster at scale.

## How Cilium uses eBPF

Cilium attaches eBPF programs to the network interfaces of every pod and node. These programs handle:

### Pod networking
When a pod sends a packet, an eBPF program on the pod's virtual interface decides where to route it — directly to another pod on the same node (shortcutting the bridge entirely), to another node, or to a Service.

### Service routing (replacing kube-proxy)
Instead of iptables DNAT rules, Cilium's eBPF programs intercept traffic to ClusterIPs and redirect it to backend pods. This is faster and uses hash maps instead of chain scanning. When you install Cilium with `kubeProxyReplacement=true`, kube-proxy is no longer needed.

### Network policies
Cilium enforces network policies in eBPF. But unlike Calico's iptables-based enforcement, Cilium's policies can operate at L7 — you can allow HTTP GET but block HTTP DELETE, or restrict which Kafka topics a pod can consume from. Standard Kubernetes NetworkPolicy resources work unchanged, but Cilium also supports its own `CiliumNetworkPolicy` CRD for L7 rules.

### Transparent encryption
Cilium can encrypt all pod-to-pod traffic using WireGuard or IPsec, configured at the CNI level. No changes to your applications — the eBPF programs handle encryption and decryption transparently.

## Hubble: seeing the network

Hubble is Cilium's observability layer. Because eBPF programs see every packet, Cilium can expose rich visibility without any additional instrumentation:

```bash
# Watch all network flows in real time
hubble observe

# See flows for a specific pod
hubble observe --pod my-namespace/my-app

# Filter by verdict (dropped traffic = policy violations)
hubble observe --verdict DROPPED

# See HTTP-level detail
hubble observe --protocol http
```

Hubble shows you:
- Which pods are talking to which (source → destination)
- Whether traffic was forwarded or dropped (and by which policy)
- HTTP request/response details (method, path, status code)
- DNS queries and responses

This is enormously useful for debugging. Instead of guessing why a pod can't reach another pod, you can see exactly what's happening — "traffic from pod A to pod B was dropped by CiliumNetworkPolicy `deny-cross-namespace`."

Hubble also has a UI dashboard and can export metrics to Prometheus and Grafana.

## When Cilium is overkill

Cilium has a learning curve. For a small dev cluster with 10 pods, the setup complexity isn't worth the observability and performance gains. Flannel or basic Calico will work fine.

Cilium starts making a real difference when:
- You have hundreds of Services (eBPF routing is measurably faster)
- You need visibility into traffic flows without deploying separate monitoring
- You want to enforce L7 network policies (allow specific HTTP paths)
- You're running in a security-sensitive environment that needs encrypted pod-to-pod traffic
- You want to consolidate — one tool for CNI, service routing, network policies, and observability

## Installing Cilium

Cilium is typically installed via Helm:

```bash
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true
```

On managed clusters (EKS, AKS), Cilium can replace the default CNI. GKE Autopilot uses Cilium's eBPF data plane under the hood (called "Dataplane V2"), though it's a slimmed-down integration — not a full Cilium install with Hubble and CiliumNetworkPolicy CRDs. On GKE Standard clusters, you opt into it explicitly.

<!-- RESOURCES -->

- [What is eBPF?](https://ebpf.io/what-is-ebpf/) -- type: guide, time: 15m
- [Cilium Documentation](https://docs.cilium.io/) -- type: docs, time: 20m
- [Hubble Documentation](https://docs.cilium.io/en/stable/observability/hubble/) -- type: docs, time: 15m
- [eBPF and Kubernetes — Liz Rice talk](https://www.youtube.com/watch?v=99jUcLt3rSk) -- type: video, time: 30m

<!-- ZH_SUMMARY -->
eBPF（extended Berkeley Packet Filter）让你可以直接在 Linux 内核中运行小程序，并将它们挂载到网络数据包到达或离开等事件上。Cilium 使用 eBPF 在内核层面处理 Kubernetes 网络——完全绕过 iptables。这不仅仅是一个不同的 CNI；它是一种从根本上不同的集群网络流量处理方式，并且解锁了基于 iptables 的网络无法做到的事情。

<!-- ZH_DEEP_DIVE -->
## 什么是 eBPF？

传统上，如果你想改变 Linux 内核处理网络数据包的方式，有两种选择：修改内核源代码（不切实际）或使用 iptables 规则（能力有限）。eBPF 引入了第三种选择：将经过验证的小型程序加载到内核中，在特定事件发生时运行。

一个 eBPF 程序可以：
- 检查进出网络接口的每一个数据包
- 做出路由决策（转发、丢弃、重定向）
- 收集流量模式的指标
- 修改数据包头部

内核在加载每个 eBPF 程序之前都会对其进行验证——检查程序是否会终止、是否访问了无效内存、是否会导致内核崩溃。这种安全保障使其在生产环境中具有实用性。

## 为什么 iptables 是瓶颈

传统的 Kubernetes 网络严重依赖 iptables。kube-proxy 为每个 Service 编写 iptables 规则，而 Calico 等 CNI 使用 iptables 来实施网络策略。问题在于：

- **线性扫描** —— iptables 逐条评估规则。当有数千个 Service 时，每个数据包都要遍历数千条规则。
- **全表替换** —— 更新单个 Service 需要原子性地重写所有 iptables 规则。当有 10,000 个 Service 时，这会变得很慢。
- **缺乏感知能力** —— iptables 工作在 L3/L4 层（IP 和端口）。它无法基于 HTTP 头部、gRPC 方法或 DNS 名称做出决策。

eBPF 用哈希表查找取代了这一机制。eBPF 程序不再扫描规则链，而是在 map 中执行 O(1) 查找：“发往 ClusterIP X 的流量 → 重定向到 Pod Y。”在大规模场景下，这要快得多。

## Cilium 如何使用 eBPF

Cilium 将 eBPF 程序附加到每个 pod 和节点的网络接口上。这些程序负责：

### Pod 网络
当 pod 发送数据包时，pod 虚拟接口上的 eBPF 程序决定将其路由到何处——直接发送到同一节点上的另一个 pod（完全绕过网桥）、发送到另一个节点，或发送到某个 Service。

### Service 路由（替代 kube-proxy）
Cilium 的 eBPF 程序不再使用 iptables DNAT 规则，而是拦截发往 ClusterIP 的流量并将其重定向到后端 pod。这更快，并且使用哈希 map 而非链式扫描。当你使用 `kubeProxyReplacement=true` 安装 Cilium 时，就不再需要 kube-proxy 了。

### 网络策略
Cilium 在 eBPF 中实施网络策略。但与 Calico 基于 iptables 的实施方式不同，Cilium 的策略可以在 L7 层运作——你可以允许 HTTP GET 但阻止 HTTP DELETE，或者限制某个 pod 可以从哪些 Kafka topic 消费。标准的 Kubernetes NetworkPolicy 资源无需修改即可使用，但 Cilium 还支持自己的 `CiliumNetworkPolicy` CRD 来实现 L7 规则。

### 透明加密
Cilium 可以使用 WireGuard 或 IPsec 加密所有 pod 到 pod 的流量，并在 CNI 层面进行配置。你的应用无需任何改动——eBPF 程序会透明地处理加密和解密。

## Hubble：洞察网络

Hubble 是 Cilium 的可观测性层。由于 eBPF 程序能看到每一个数据包，Cilium 无需任何额外的埋点即可提供丰富的可见性：

```bash
# Watch all network flows in real time
hubble observe

# See flows for a specific pod
hubble observe --pod my-namespace/my-app

# Filter by verdict (dropped traffic = policy violations)
hubble observe --verdict DROPPED

# See HTTP-level detail
hubble observe --protocol http
```

Hubble 向你展示：
- 哪些 pod 在与哪些 pod 通信（源 → 目的地）
- 流量是被转发还是被丢弃（以及被哪条策略丢弃）
- HTTP 请求/响应详情（方法、路径、状态码）
- DNS 查询和响应

这对调试非常有用。与其猜测为什么一个 pod 无法访问另一个 pod，你可以确切地看到发生了什么——“从 pod A 到 pod B 的流量被 CiliumNetworkPolicy `deny-cross-namespace` 丢弃了。”

Hubble 还提供 UI 仪表盘，并可以将指标导出到 Prometheus 和 Grafana。

## 何时 Cilium 属于过度配置

Cilium 有学习曲线。对于一个只有 10 个 pod 的小型开发集群来说，搭建的复杂性不值得可观测性和性能上的收益。Flannel 或基础版 Calico 就足够了。

Cilium 开始真正发挥作用是在以下情况：
- 你有数百个 Service（eBPF 路由明显更快）
- 你需要在无需部署独立监控的情况下获得流量可见性
- 你想实施 L7 网络策略（允许特定 HTTP 路径）
- 你运行在对安全敏感的环境中，需要加密的 pod 到 pod 流量
- 你想整合——用一个工具搞定 CNI、Service 路由、网络策略和可观测性

## 安装 Cilium

Cilium 通常通过 Helm 安装：

```bash
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true
```

在托管集群（EKS、AKS）上，Cilium 可以替代默认的 CNI。GKE Autopilot 在底层使用 Cilium 的 eBPF 数据平面（称为“Dataplane V2”），不过这是一个精简版的集成——并非包含 Hubble 和 CiliumNetworkPolicy CRD 的完整 Cilium 安装。在 GKE Standard 集群上，你需要显式选择启用。

<!-- ZH_RESOURCES -->
- [什么是 eBPF？](https://ebpf.io/what-is-ebpf/) -- 类型：指南，时长：15m
- [Cilium 文档](https://docs.cilium.io/) -- 类型：文档，时长：20m
- [Hubble 文档](https://docs.cilium.io/en/stable/observability/hubble/) -- 类型：文档，时长：15m
- [eBPF 与 Kubernetes — Liz Rice 演讲](https://www.youtube.com/watch?v=99jUcLt3rSk) -- 类型：视频，时长：30m

<!-- ZH_UI -->
1. 理解什么是 eBPF：运行在 Linux 内核中的小型程序，挂载到网络事件等钩子上
2. 了解 eBPF 对网络的意义：在内核层面做路由决策，完全绕过 iptables
3. 理解 Cilium 的模型：eBPF 程序在单一层中处理 Pod 网络、服务路由、网络策略和可观测性
4. 了解什么是 Hubble：Cilium 的可观测性层，无需 tcpdump 即可展示每一条网络流
5. 理解 Cilium 如何替代 kube-proxy：由 eBPF 处理 ClusterIP 路由，而非 iptables 规则
6. 了解 eBPF 何时过度（小集群、简单需求），何时不可或缺（规模、可见性、性能）
7. 我现在理解网络是如何工作的了——我想真正锁定哪些 Pod 能与哪些 Pod 通信。
8. 我的集群是扁平网络，任意 Pod 都能访问任意其他 Pod。既然我已经理解了 CNI、eBPF 以及流量如何流转，我想筑起围墙。一个命名空间中被攻陷的 Pod 不应能访问另一个命名空间中的数据库。
