---
id: overlay-vs-native-routing
title: Overlay Networks vs Native Routing
zone: kubernetes
edges:
  to:
    - id: choosing-a-cni
      question: >-
        I get how overlay and native routing differ. But there are a dozen CNI
        plugins — which one should I actually use?
      detail: >-
        Routing mode is just one piece of the puzzle. Some CNIs support network
        policies, some don't. Some have built-in observability. Some can replace
        other cluster components entirely. I need to pick one and I don't want
        to find out I chose wrong after I'm already in production.
difficulty: 3
tags:
  - kubernetes
  - overlay
  - vxlan
  - bgp
  - routing
  - networking
  - k8s
category: concept
milestones:
  - >-
    Understand overlay networking: pod packets are encapsulated inside
    node-to-node UDP packets (VXLAN) — works on any infrastructure
  - >-
    Understand native/BGP routing: pod CIDRs are advertised as real routes on
    the network — no encapsulation overhead, but requires network cooperation
  - >-
    Know the AWS VPC CNI model as a third approach: pods get real VPC IPs with
    no overlay, but IP address consumption is a real constraint
  - >-
    Know when to pick overlay (any environment, simple, just works) vs native
    (performance-sensitive, you control the underlying network)
title_zh: "Overlay 网络与原生路由"

---


When pods on different nodes need to talk, the traffic has to cross the physical network. CNI plugins handle this in two fundamentally different ways: overlay networking wraps pod traffic inside regular node-to-node packets, while native routing makes the physical network aware of pod IPs directly. Each has real trade-offs in simplicity, performance, and where you can run it.

<!-- DEEP_DIVE -->

## Overlay networking

An overlay network works by encapsulating pod packets inside regular node-to-node packets. The most common protocol is VXLAN (Virtual Extensible LAN).

Here's what happens when Pod A on Node 1 sends a packet to Pod B on Node 2:

1. Pod A sends a packet addressed to Pod B's IP (`10.244.2.3`)
2. Node 1's CNI intercepts the packet before it hits the physical network
3. The CNI wraps the entire original packet inside a new UDP packet, addressed from Node 1's IP to Node 2's IP
4. The outer packet travels across the physical network like any other traffic between machines
5. Node 2 receives the UDP packet, strips the outer headers, and delivers the inner packet to Pod B

```
Original:  [Pod A IP → Pod B IP] [payload]
On wire:   [Node 1 IP → Node 2 IP] [UDP] [Pod A IP → Pod B IP] [payload]
```

The physical network only sees traffic between node IPs. It has no idea that pod IPs exist. This is the key advantage of overlays: **they work on any network**, because the underlying infrastructure doesn't need to know anything about Kubernetes.

### The cost

Encapsulation isn't free:
- **Overhead per packet** — each packet gets an extra header (~50 bytes), reducing the effective MTU
- **CPU cost** — wrapping and unwrapping packets takes CPU cycles on every node
- **Troubleshooting** — when you capture packets on the physical network, you see VXLAN-encapsulated traffic, not the actual pod-to-pod communication

For most workloads, the overhead is negligible. For high-throughput, latency-sensitive applications (think: databases doing thousands of queries per second between pods), it can matter.

## Native routing

Native routing means pod CIDRs are real routes on the network. No wrapping — the physical network knows how to reach pod IPs directly.

The most common way to do this is BGP (Border Gateway Protocol). Each node runs a BGP agent that announces its pod CIDR to the network's routers: "I own `10.244.1.0/24`, send traffic for those IPs to me."

The routers add these as entries in their routing tables, and traffic flows directly:

1. Pod A sends a packet to Pod B's IP (`10.244.2.3`)
2. The packet hits the network router
3. The router has a route: `10.244.2.0/24 → Node 2`
4. The packet goes straight to Node 2, which delivers it to Pod B

No encapsulation, no overhead, no extra headers. The packet on the wire is exactly what the pod sent.

### The requirement

Native routing only works if your network infrastructure cooperates. The routers need to:
- Accept BGP peering from your nodes (or support some other route advertisement mechanism)
- Have the capacity in their routing tables for pod CIDRs

In a data center you control, this is often straightforward. In a cloud VPC or a managed corporate network where you don't control the routers, it might not be an option.

## Cloud-native networking: the third approach

Cloud providers offer a third model that doesn't fit neatly into overlay vs native. The AWS VPC CNI is the clearest example:

- Pods get IP addresses from the VPC's own IP space — the same address range as EC2 instances
- No overlay, no BGP — the VPC network treats pod IPs as first-class citizens
- Traffic between pods on different nodes travels through the VPC fabric like normal EC2-to-EC2 traffic

The trade-off: IP address consumption. Each EC2 instance can only hold a limited number of secondary IPs (based on instance type). A small instance might support 10-15 pod IPs. Run more pods than that and you're out of IPs. Larger instance types support more, but you're always constrained by VPC CIDR sizing and ENI limits.

Azure CNI and GKE's native networking work similarly — they integrate pod networking with the cloud network layer, trading IP flexibility for seamless cloud integration.

## When to pick which

| Approach | Use when | Avoid when |
|----------|----------|------------|
| **Overlay (VXLAN)** | Cloud, on-prem, any network you don't control. Simplest setup. | Ultra-low-latency workloads, very high network throughput |
| **Native (BGP)** | You control the network, need best performance, on-prem data center | Cloud VPCs (routers often don't support BGP peering) |
| **Cloud-native** | Running on AWS/Azure/GKE and want tight integration | Multi-cloud, on-prem, or if you're burning through IP addresses |

Most clusters start with overlay because it works everywhere. Switch to native routing if you hit performance limits and your network supports it. Use cloud-native CNI if you're all-in on one cloud provider and want the simplest integration.

<!-- RESOURCES -->

- [Calico Networking Options](https://docs.tigera.io/calico/latest/networking/) -- type: docs, time: 20m
- [VXLAN Explained](https://www.tkng.io/cni/vxlan/) -- type: guide, time: 15m
- [AWS VPC CNI - How It Works](https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当不同节点上的 Pod 需要通信时，流量必须跨越物理网络。CNI 插件以两种根本不同的方式处理这一问题：overlay 网络将 Pod 流量封装在常规的节点间数据包内，而原生路由则让物理网络直接感知 Pod IP。两者在简单性、性能以及可运行环境方面各有实际的权衡。

<!-- ZH_DEEP_DIVE -->
## Overlay 网络

Overlay 网络的工作原理是将 Pod 数据包封装在常规的节点间数据包中。最常见的协议是 VXLAN（Virtual Extensible LAN）。

以下是 Node 1 上的 Pod A 向 Node 2 上的 Pod B 发送数据包时发生的过程：

1. Pod A 发送一个目标地址为 Pod B IP（`10.244.2.3`）的数据包
2. Node 1 的 CNI 在数据包到达物理网络之前将其拦截
3. CNI 将整个原始数据包封装在一个新的 UDP 数据包中，外层地址为 Node 1 的 IP 到 Node 2 的 IP
4. 外层数据包像机器之间的任何其他流量一样穿越物理网络
5. Node 2 接收 UDP 数据包，剥离外层头部，将内层数据包投递给 Pod B

```
原始:     [Pod A IP → Pod B IP] [payload]
线路上:   [Node 1 IP → Node 2 IP] [UDP] [Pod A IP → Pod B IP] [payload]
```

物理网络只能看到节点 IP 之间的流量。它完全不知道 Pod IP 的存在。这是 overlay 的关键优势：**它们可以在任何网络上工作**，因为底层基础设施不需要了解任何关于 Kubernetes 的信息。

### 代价

封装并非没有成本：
- **每包开销** — 每个数据包都会增加一个额外的头部（约 50 字节），降低有效 MTU
- **CPU 成本** — 封装和解封装数据包会在每个节点上消耗 CPU 周期
- **故障排查** — 当你在物理网络上抓包时，看到的是 VXLAN 封装后的流量，而非实际的 Pod 到 Pod 通信

对于大多数工作负载，开销可以忽略不计。但对于高吞吐、延迟敏感的应用（比如：Pod 之间每秒执行数千次查询的数据库），这可能会有影响。

## 原生路由

原生路由意味着 Pod CIDR 是网络上的真实路由。无需封装——物理网络知道如何直接到达 Pod IP。

最常见的实现方式是 BGP（Border Gateway Protocol）。每个节点运行一个 BGP agent，向其网络路由器宣告自己的 Pod CIDR：“我拥有 `10.244.1.0/24`，将这些 IP 的流量发送给我。”

路由器将这些作为条目添加到路由表中，流量直接流动：

1. Pod A 向 Pod B 的 IP（`10.244.2.3`）发送数据包
2. 数据包到达网络路由器
3. 路由器有一条路由：`10.244.2.0/24 → Node 2`
4. 数据包直接到达 Node 2，由 Node 2 投递给 Pod B

无封装、无开销、无额外头部。线路上的数据包就是 Pod 发送的原始数据包。

### 前提条件

原生路由只有在你的网络基础设施配合的情况下才能工作。路由器需要：
- 接受来自节点的 BGP peering（或支持其他路由宣告机制）
- 在路由表中有足够的容量来存储 Pod CIDR

在你控制的数据中心中，这通常很直接。在云 VPC 或你不控制路由器的托管企业网络中，这可能不是一个选项。

## 云原生网络：第三种方案

云提供商提供了第三种模式，它不能简单地归入 overlay 或原生路由。AWS VPC CNI 是最清晰的例子：

- Pod 从 VPC 自身的 IP 空间获取 IP 地址——与 EC2 实例相同的地址范围
- 无 overlay、无 BGP——VPC 网络将 Pod IP 视为一等公民
- 不同节点上的 Pod 之间的流量通过 VPC 网络结构传输，就像正常的 EC2 到 EC2 流量一样

权衡：IP 地址消耗。每个 EC2 实例只能持有有限数量的辅助 IP（取决于实例类型）。小型实例可能支持 10-15 个 Pod IP。运行超过这个数量的 Pod 就会耗尽 IP。更大的实例类型支持更多，但你始终受限于 VPC CIDR 大小和 ENI 限制。

Azure CNI 和 GKE 的原生网络工作原理类似——它们将 Pod 网络与云网络层集成，以 IP 灵活性换取无缝的云集成。

## 如何选择

| 方案 | 适用场景 | 避免场景 |
|----------|----------|------------|
| **Overlay (VXLAN)** | 云环境、本地部署、任何你不控制的网络。设置最简单。 | 超低延迟工作负载、极高网络吞吐 |
| **原生路由 (BGP)** | 你控制网络、需要最佳性能、本地数据中心 | 云 VPC（路由器通常不支持 BGP peering） |
| **云原生** | 运行在 AWS/Azure/GKE 上并希望紧密集成 | 多云、本地部署，或者 IP 地址消耗过快 |

大多数集群从 overlay 开始，因为它到处都能用。如果你遇到性能瓶颈且网络支持，可以切换到原生路由。如果你完全投入某一家云提供商并希望最简单的集成，可以使用云原生 CNI。

<!-- ZH_RESOURCES -->
- [Calico 网络选项](https://docs.tigera.io/calico/latest/networking/) -- type: docs, time: 20m
- [VXLAN 详解](https://www.tkng.io/cni/vxlan/) -- type: guide, time: 15m
- [AWS VPC CNI - 工作原理](https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html) -- type: docs, time: 15m

<!-- ZH_UI -->
1. 理解 overlay 网络：pod 数据包被封装在节点间的 UDP 包（VXLAN）中——可在任何基础设施上运行
2. 理解原生/BGP 路由：pod CIDR 作为真实路由在网络中通告——无封装开销，但需要网络配合
3. 了解 AWS VPC CNI 模型作为第三种方案：pod 获得真实 VPC IP，无 overlay，但 IP 地址消耗是实际约束
4. 了解何时选择 overlay（任何环境、简单、开箱即用）与原生（性能敏感、可控制底层网络）
5. 我理解 overlay 和原生路由的区别。但有十多个 CNI 插件——我到底该用哪个？
6. 路由模式只是其中一环。有些 CNI 支持网络策略，有些不支持。有些内置可观测性。有些能完全替代其他集群组件。我需要选一个，而且不想在上生产之后才发现选错了。
