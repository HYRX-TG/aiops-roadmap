---
id: pod-to-pod-networking
title: How Pods Talk Across Nodes
zone: kubernetes
edges:
  to:
    - id: what-is-cni
      question: >-
        All this networking gets set up automatically every time a pod starts —
        what's doing it?
      detail: >-
        Every time a pod launches, it gets an IP, gets wired into the network,
        and can immediately talk to other pods. That's a lot of setup happening
        behind the scenes. Kubernetes doesn't do it directly — so what does? And
        why are there so many different options for it?
    - id: network-debugging-k8s
      question: >-
        I understand how packets are supposed to flow — but right now something
        is broken and traffic between my pods is just dropping.
      detail: >-
        My pod can't reach a pod on another node. I know the path should be: pod
        → veth → bridge → node routing → other node → bridge → veth → pod. But
        something in that chain is failing and I don't know how to figure out
        where.
difficulty: 3
tags:
  - kubernetes
  - networking
  - veth
  - bridge
  - routing
  - packets
  - k8s
category: concept
milestones:
  - >-
    Understand veth pairs: every pod gets a virtual ethernet interface paired to
    the node's network namespace
  - >-
    Know how a node's network bridge connects all local pod veth interfaces so
    pods on the same node can talk directly
  - >-
    Trace the path of a packet from a pod on Node A to a pod on Node B — through
    the veth, bridge, node routing table, and into the destination node
  - >-
    Understand that cross-node routing is where CNI plugins differ — some
    encapsulate (overlay), some use real routes (BGP)
title_zh: "Pod 如何跨节点通信"

---


When a pod on one node sends traffic to a pod on another node, something has to carry that traffic across the physical network. Kubernetes doesn't handle this itself — it relies on a combination of virtual network interfaces, bridges, and routing that gets set up for each pod. Understanding this path is what lets you debug networking problems instead of guessing.

<!-- DEEP_DIVE -->

## Inside a single node

Every pod gets its own network namespace — an isolated copy of the network stack with its own interfaces, routing table, and IP address. The pod doesn't share the node's network directly.

To connect the pod's isolated network to the node, Kubernetes (via the CNI plugin) creates a **veth pair** — a virtual ethernet cable with two ends. One end goes inside the pod's network namespace and becomes the pod's `eth0`. The other end stays in the node's root network namespace.

```
┌─────────────────────────────┐
│          Node               │
│                             │
│  ┌─────────┐  ┌─────────┐  │
│  │  Pod A  │  │  Pod B  │  │
│  │  eth0   │  │  eth0   │  │
│  └──┬──────┘  └──┬──────┘  │
│     │veth        │veth     │
│  ┌──┴────────────┴──────┐  │
│  │    bridge (cbr0)     │  │
│  └──────────┬───────────┘  │
│             │              │
│         eth0 (node)        │
└─────────────┴──────────────┘
```

The node-side ends of the veth pairs are typically connected to a **bridge** (like `cbr0` or `cni0`). A bridge is a virtual network switch — it lets all pods on the same node talk to each other directly. Pod A sends a packet, it arrives at the bridge via the veth pair, and the bridge forwards it to Pod B's veth pair.

This is fast — same-node pod-to-pod traffic never leaves the machine.

## Across nodes

When Pod A on Node 1 needs to reach Pod C on Node 2, the packet has to leave Node 1 and arrive at Node 2. This is where things get interesting and where different CNI plugins take different approaches.

The basic path:

1. Pod A sends a packet to Pod C's IP (e.g., `10.244.2.3`)
2. The packet reaches the bridge on Node 1
3. The bridge doesn't know that IP locally, so the packet goes to the node's routing table
4. The routing table has an entry saying "10.244.2.0/24 is reachable via Node 2"
5. The packet travels over the physical network to Node 2
6. Node 2's routing table delivers it to the local bridge
7. The bridge forwards it to Pod C's veth pair

Step 4 is where the CNI plugin's approach matters. There are two fundamental strategies:

### Overlay approach

The packet gets wrapped inside another packet. Node 1 takes Pod A's original packet and puts it inside a UDP packet addressed to Node 2's real IP. Node 2 unwraps it and delivers the inner packet to Pod C. The physical network only sees normal traffic between node IPs — it doesn't need to know about pod IPs at all.

### Native routing approach

The nodes' routing tables (or the physical network's routers) know about pod subnets directly. Node 1 says "10.244.2.0/24 → Node 2's IP" as a real route. No wrapping, no overhead — but the network infrastructure needs to cooperate.

## What the node's routing table looks like

On a node in a typical cluster, you'd see something like:

```
10.244.0.0/24  via node-0  # pods on node-0
10.244.1.0/24  dev cni0    # local pods (this node)
10.244.2.0/24  via node-2  # pods on node-2
```

Each node gets a slice of the pod IP range (a /24 by default), and the routing table maps each slice to the node that owns it. How these routes get installed — whether by VXLAN tunnels, BGP advertisements, or cloud-specific APIs — depends entirely on the CNI plugin.

## Why this matters for debugging

When pod-to-pod traffic breaks, it's almost always a problem in this chain: the veth pair, the bridge, the routing table, or the cross-node transport. Knowing the path lets you ask the right questions:

- Can the pod reach its own gateway? (veth pair issue)
- Can pods on the same node talk to each other? (bridge issue)
- Can pods on different nodes talk? (routing or overlay issue)
- Can the nodes themselves ping each other? (physical network issue)

<!-- RESOURCES -->

- [Kubernetes Networking Demystified - Pod Networking](https://www.tkng.io/cni/) -- type: guide, time: 25m
- [Kubernetes Docs - Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/) -- type: docs, time: 15m
- [Container Networking From Scratch](https://www.youtube.com/watch?v=6v_BDHIgOY8) -- type: video, time: 35m

<!-- ZH_SUMMARY -->
当一个节点上的 Pod 向另一个节点上的 Pod 发送流量时，必须有某种机制将这些流量通过物理网络传输过去。Kubernetes 本身并不处理这件事——它依赖于为每个 Pod 设置的虚拟网络接口、网桥和路由的组合。理解这条路径，才能让你调试网络问题，而不是靠猜测。

<!-- ZH_DEEP_DIVE -->
## 单节点内部

每个 Pod 都有自己独立的网络命名空间——这是网络栈的一份隔离副本，拥有自己的网络接口、路由表和 IP 地址。Pod 并不直接共享节点的网络。

为了将 Pod 的隔离网络连接到节点，Kubernetes（通过 CNI 插件）会创建一对 **veth pair**——一根两端相连的虚拟以太网线缆。一端进入 Pod 的网络命名空间，成为 Pod 的 `eth0`；另一端则留在节点的根网络命名空间中。

```
┌─────────────────────────────┐
│          Node               │
│                             │
│  ┌─────────┐  ┌─────────┐  │
│  │  Pod A  │  │  Pod B  │  │
│  │  eth0   │  │  eth0   │  │
│  └──┬──────┘  └──┬──────┘  │
│     │veth        │veth     │
│  ┌──┴────────────┴──────┐  │
│  │    bridge (cbr0)     │  │
│  └──────────┬───────────┘  │
│             │              │
│         eth0 (node)        │
└─────────────┴──────────────┘
```

veth pair 位于节点侧的一端通常会连接到一个**网桥**（如 `cbr0` 或 `cni0`）。网桥是一台虚拟网络交换机——它让同一节点上的所有 Pod 能够直接相互通信。Pod A 发出一个数据包，经由 veth pair 到达网桥，网桥再将其转发到 Pod B 的 veth pair。

这个过程很快——同节点 Pod 之间的流量永远不会离开本机。

## 跨节点通信

当 Node 1 上的 Pod A 需要访问 Node 2 上的 Pod C 时，数据包必须离开 Node 1 并到达 Node 2。这正是有趣之处，也是不同 CNI 插件采取不同方案的地方。

基本路径如下：

1. Pod A 向 Pod C 的 IP（例如 `10.244.2.3`）发送数据包
2. 数据包到达 Node 1 上的网桥
3. 网桥在本地不认识该 IP，因此数据包进入节点的路由表
4. 路由表中有一条记录：“10.244.2.0/24 可通过 Node 2 到达”
5. 数据包经由物理网络传输到 Node 2
6. Node 2 的路由表将其投递到本地网桥
7. 网桥将其转发到 Pod C 的 veth pair

第 4 步正是 CNI 插件方案发挥作用的地方。这里有两种基本策略：

### Overlay 方案

数据包会被封装进另一个数据包中。Node 1 取来 Pod A 的原始数据包，将其放入一个发往 Node 2 真实 IP 的 UDP 数据包中。Node 2 将其解封装，并把内层数据包投递给 Pod C。物理网络只能看到节点 IP 之间的普通流量——它完全不需要知道 Pod IP。

### 原生路由方案

节点的路由表（或物理网络中的路由器）直接知晓 Pod 子网。Node 1 将“10.244.2.0/24 → Node 2 的 IP”作为一条真实路由。没有封装，没有额外开销——但网络基础设施需要配合。

## 节点的路由表长什么样

在典型集群的一个节点上，你会看到类似这样的内容：

```
10.244.0.0/24  via node-0  # pods on node-0
10.244.1.0/24  dev cni0    # local pods (this node)
10.244.2.0/24  via node-2  # pods on node-2
```

每个节点分得 Pod IP 范围中的一片（默认是一个 /24），路由表将每一片映射到拥有它的节点。这些路由如何安装——是通过 VXLAN 隧道、BGP 通告，还是云厂商特定的 API——完全取决于 CNI 插件。

## 为什么这对调试很重要

当 Pod 之间的流量中断时，问题几乎总是出在这条链路上：veth pair、网桥、路由表或跨节点传输。了解这条路径能让你提出正确的问题：

- Pod 能否到达自己的网关？（veth pair 问题）
- 同一节点上的 Pod 能否相互通信？（网桥问题）
- 不同节点上的 Pod 能否通信？（路由或 overlay 问题）
- 节点之间能否互相 ping 通？（物理网络问题）

<!-- ZH_RESOURCES -->
- [Kubernetes 网络揭秘 - Pod 网络](https://www.tkng.io/cni/) -- 类型: 指南, 时长: 25m
- [Kubernetes 文档 - 集群网络](https://kubernetes.io/docs/concepts/cluster-administration/networking/) -- 类型: 文档, 时长: 15m
- [从零开始理解容器网络](https://www.youtube.com/watch?v=6v_BDHIgOY8) -- 类型: 视频, 时长: 35m

<!-- ZH_UI -->
1. 理解 veth 对：每个 pod 都会获得一个虚拟以太网接口，并与节点的网络命名空间配对
2. 了解节点的网络桥如何连接所有本地 pod 的 veth 接口，使同一节点上的 pod 可以直接通信
3. 追踪数据包从节点 A 上的 pod 到节点 B 上的 pod 的路径——经过 veth、网桥、节点路由表，进入目标节点
4. 理解跨节点路由正是 CNI 插件差异所在——有些进行封装（overlay），有些使用真实路由（BGP）
5. 所有这些网络配置在每次 pod 启动时都会自动设置——是什么在完成这些工作？
6. 每次 pod 启动时，它都会获得一个 IP、接入网络，并能立即与其他 pod 通信。这背后有大量设置工作在进行。Kubernetes 并不直接完成这些——那么是什么在完成？为什么会有这么多不同的选项？
7. 我理解数据包应该如何流动——但现在出了问题，我的 pod 之间的流量正在被丢弃。
8. 我的 pod 无法访问另一个节点上的 pod。我知道路径应该是：pod → veth → 网桥 → 节点路由 → 另一个节点 → 网桥 → veth → pod。但这条链路中某个环节失败了，我不知道如何找出问题所在。
