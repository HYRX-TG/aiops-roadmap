---
id: what-is-cni
title: "CNI: The Plugin That Builds the Network"
zone: kubernetes
edges:
  to:
    - id: overlay-vs-native-routing
      question: >-
        My CNI has different modes for how it moves traffic between nodes — one
        wraps packets, another uses real routes. What's the difference?
      detail: >-
        I'm setting up my CNI and it's asking me to choose between 'overlay' and
        'native routing.' One apparently wraps each pod's traffic inside another
        layer to send it across nodes. The other makes the real network aware of
        pod IPs. I don't know which one I want or what the trade-offs are.
    - id: choosing-a-cni
      question: >-
        Flannel, Calico, Cilium, Weave, AWS VPC CNI — there are a dozen
        options. How do I pick?
      detail: >-
        My cluster came with a default CNI and I never questioned it. But now I
        need network policies and someone said my CNI doesn't support them.
        Another person says I should use Cilium for everything. I have no idea
        what the actual differences are.
difficulty: 2
tags:
  - kubernetes
  - cni
  - networking
  - kubelet
  - ipam
  - k8s
category: concept
milestones:
  - >-
    Understand that CNI (Container Network Interface) is a spec — it defines the
    interface between container runtimes and network plugins
  - >-
    Know the lifecycle: when kubelet starts a pod, the container runtime
    (containerd/CRI-O) calls the CNI plugin to assign an IP and wire up the
    network
  - >-
    Understand what IPAM (IP Address Management) does: allocates pod IPs from a
    configured range, tracks which IPs are in use
  - >-
    Know that CNI plugin chaining lets you stack plugins — e.g., a main network
    plugin plus a bandwidth-limiting plugin
  - >-
    Recognize the symptom of a broken CNI: pods stuck in ContainerCreating with
    network setup errors
title_zh: "CNI：构建网络的插件"

---


CNI stands for Container Network Interface. It's not a product — it's a specification that defines how container runtimes (like containerd) should talk to network plugins. When kubelet starts a pod, it calls the CNI plugin to do the actual networking work: assign an IP, create the virtual interfaces, and set up routes. The CNI plugin is what makes the Kubernetes networking contract a reality.

<!-- DEEP_DIVE -->

## What CNI actually is

CNI is a spec maintained by the CNCF. It defines a simple interface: when a container is created, the runtime calls the CNI plugin with "add this container to the network." When the container is deleted, it calls "remove this container from the network."

The plugin is just a binary on the node, stored in `/opt/cni/bin/`. When kubelet needs to create a pod, it tells the container runtime (containerd or CRI-O) to set up a pod sandbox. The container runtime then calls the CNI plugin with the container's network namespace as an argument. The plugin does whatever it needs to — create a veth pair, assign an IP, program routes — and returns the assigned IP address.

```
Pod starts → kubelet → containerd (CRI) → calls CNI plugin binary → plugin assigns IP, creates veth, configures routes → pod has networking
```

This distinction matters for debugging: CNI errors show up in the container runtime's logs (containerd), not just kubelet's.

## How IP addresses get assigned

CNI plugins use an IPAM (IP Address Management) module to assign IP addresses. The most common approach:

- Each node gets a slice of the cluster's pod CIDR (e.g., Node 1 gets `10.244.1.0/24`, Node 2 gets `10.244.2.0/24`)
- When a pod starts on Node 1, the IPAM module picks the next available IP from `10.244.1.0/24`
- The assignment is tracked so two pods never get the same IP

In cloud environments, the IPAM approach can be different. AWS VPC CNI, for example, assigns real VPC IP addresses to pods by requesting secondary IPs from the EC2 API.

## The CNI configuration

The CNI config lives on each node, typically at `/etc/cni/net.d/`. It tells kubelet which plugin to use and how to configure it:

```json
{
  "cniVersion": "1.0.0",
  "name": "my-network",
  "type": "calico",
  "ipam": {
    "type": "calico-ipam"
  }
}
```

The `type` field maps to a binary in `/opt/cni/bin/`. When you install a CNI like Calico or Cilium, it drops its binary there and writes this config file.

## Plugin chaining

CNI supports chaining multiple plugins together. The first plugin does the main networking (assign IP, create veth), and subsequent plugins add features on top:

```json
{
  "cniVersion": "1.0.0",
  "name": "my-network",
  "plugins": [
    { "type": "calico" },
    { "type": "bandwidth", "ingressRate": 1000000 },
    { "type": "portmap", "capabilities": { "portMappings": true } }
  ]
}
```

This runs Calico for the main network setup, then applies bandwidth limiting, then sets up port mappings. Each plugin in the chain gets called in order.

## When the CNI breaks

If the CNI plugin is misconfigured, missing, or crashing, pods get stuck in `ContainerCreating`. You'll see events like:

```
Warning  FailedCreatePodSandBox  network: failed to setup sandbox
```

Common causes:
- The CNI plugin binary is missing from `/opt/cni/bin/`
- The config in `/etc/cni/net.d/` is invalid or points to the wrong plugin
- The CNI pod itself (Calico, Cilium, etc.) is crash-looping on that node
- IP address exhaustion — the node's CIDR range is full

Check the CNI pods first:

```bash
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"
```

If those pods aren't healthy, no new pods on that node can get networking.

## Why the CNI choice matters

Your CNI plugin determines:
- **How traffic crosses nodes** — overlay (VXLAN) or native routing (BGP)
- **Whether network policies work** — Flannel doesn't enforce them, Calico and Cilium do
- **Performance characteristics** — overlay adds latency, eBPF-based CNIs skip iptables
- **Available features** — some CNIs provide encryption, observability, or can replace kube-proxy

This isn't something you can easily swap later. Changing CNIs in a running cluster means draining all nodes and reconfiguring networking — effectively a cluster rebuild. Pick carefully up front.

<!-- RESOURCES -->

- [CNI Specification](https://www.cni.dev/docs/spec/) -- type: docs, time: 15m
- [Kubernetes Docs - Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) -- type: docs, time: 10m
- [Understanding CNI](https://www.tkng.io/cni/) -- type: guide, time: 20m

<!-- ZH_SUMMARY -->
CNI 代表容器网络接口(Container Network Interface)。它不是一个产品——而是一个规范，定义了容器运行时（如 containerd）应如何与网络插件通信。当 kubelet 启动一个 pod 时，它会调用 CNI 插件来执行实际的网络工作：分配 IP、创建虚拟接口并设置路由。CNI 插件正是让 Kubernetes 网络契约得以实现的关键。

<!-- ZH_DEEP_DIVE -->
## CNI 究竟是什么

CNI 是由 CNCF 维护的一项规范。它定义了一个简单的接口：当容器被创建时，运行时调用 CNI 插件，传入“将此容器加入网络”；当容器被删除时，调用“将此容器从网络中移除”。

插件只是节点上的一个二进制文件，存放在 `/opt/cni/bin/` 中。当 kubelet 需要创建 pod 时，它会告诉容器运行时（containerd 或 CRI-O）去建立 pod sandbox。容器运行时随后以容器的网络命名空间作为参数调用 CNI 插件。插件执行它需要做的操作——创建 veth pair、分配 IP、配置路由——并返回所分配的 IP 地址。

```
Pod starts → kubelet → containerd (CRI) → calls CNI plugin binary → plugin assigns IP, creates veth, configures routes → pod has networking
```

这一区别对调试很重要：CNI 错误会出现在容器运行时的日志（containerd）中，而不仅仅是 kubelet 的日志里。

## IP 地址是如何分配的

CNI 插件使用 IPAM（IP 地址管理）模块来分配 IP 地址。最常见的做法是：

- 每个节点分得集群 pod CIDR 中的一段（例如，Node 1 分得 `10.244.1.0/24`，Node 2 分得 `10.244.2.0/24`）
- 当 Node 1 上启动一个 pod 时，IPAM 模块从 `10.244.1.0/24` 中选取下一个可用 IP
- 分配情况会被跟踪记录，因此两个 pod 永远不会拿到同一个 IP

在云环境中，IPAM 的方式可能有所不同。例如，AWS VPC CNI 通过向 EC2 API 申请辅助 IP，为 pod 分配真实的 VPC IP 地址。

## CNI 配置

CNI 配置存放在每个节点上，通常位于 `/etc/cni/net.d/`。它告诉 kubelet 使用哪个插件以及如何配置该插件：

```json
{
  "cniVersion": "1.0.0",
  "name": "my-network",
  "type": "calico",
  "ipam": {
    "type": "calico-ipam"
  }
}
```

`type` 字段对应 `/opt/cni/bin/` 中的一个二进制文件。当你安装 Calico 或 Cilium 这类 CNI 时，它会将自己的二进制文件放到那里，并写入这个配置文件。

## 插件链式调用

CNI 支持将多个插件串联起来。第一个插件负责主要的网络设置（分配 IP、创建 veth），后续插件在此基础上叠加功能：

```json
{
  "cniVersion": "1.0.0",
  "name": "my-network",
  "plugins": [
    { "type": "calico" },
    { "type": "bandwidth", "ingressRate": 1000000 },
    { "type": "portmap", "capabilities": { "portMappings": true } }
  ]
}
```

这会先运行 Calico 完成主要网络设置，然后应用带宽限制，再设置端口映射。链中的每个插件按顺序被调用。

## 当 CNI 出故障时

如果 CNI 插件配置错误、缺失或崩溃，pod 会卡在 `ContainerCreating` 状态。你会看到类似这样的事件：

```
Warning  FailedCreatePodSandBox  network: failed to setup sandbox
```

常见原因：
- `/opt/cni/bin/` 中缺少 CNI 插件二进制文件
- `/etc/cni/net.d/` 中的配置无效，或指向了错误的插件
- CNI 自身的 pod（Calico、Cilium 等）在该节点上反复崩溃重启
- IP 地址耗尽——节点的 CIDR 范围已满

先检查 CNI pod：

```bash
kubectl get pods -n kube-system | grep -E "calico|cilium|flannel"
```

如果这些 pod 不健康，该节点上任何新 pod 都无法获得网络。

## 为什么 CNI 的选择很重要

你的 CNI 插件决定了：
- **流量如何跨节点传输**——overlay（VXLAN）还是原生路由（BGP）
- **网络策略是否生效**——Flannel 不强制执行，Calico 和 Cilium 会
- **性能特征**——overlay 会增加延迟，基于 eBPF 的 CNI 会跳过 iptables
- **可用功能**——某些 CNI 提供加密、可观测性，或可替代 kube-proxy

这不是一件日后可以轻易更换的事。在运行中的集群里更换 CNI 意味着要排空所有节点并重新配置网络——实际上等同于重建集群。一开始就要谨慎选择。

<!-- ZH_RESOURCES -->
- [CNI 规范](https://www.cni.dev/docs/spec/) -- 类型：文档，时长：15 分钟
- [Kubernetes 文档 - 网络插件](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/) -- 类型：文档，时长：10 分钟
- [理解 CNI](https://www.tkng.io/cni/) -- 类型：指南，时长：20 分钟

<!-- ZH_UI -->
1. 理解 CNI（容器网络接口）是一个规范——它定义了容器运行时与网络插件之间的接口
2. 了解生命周期：当 kubelet 启动 Pod 时，容器运行时（containerd/CRI-O）调用 CNI 插件来分配 IP 并配置网络
3. 理解 IPAM（IP 地址管理）的作用：从配置的地址范围中分配 Pod IP，并跟踪哪些 IP 正在使用
4. 了解 CNI 插件链式调用可以叠加插件——例如一个主网络插件加一个带宽限制插件
5. 识别 CNI 故障的症状：Pod 卡在 ContainerCreating 状态并报网络配置错误
6. 我的 CNI 有不同的模式来在节点间传输流量——一种封装数据包，另一种使用真实路由。两者有什么区别？
7. 我在配置 CNI，它让我在“overlay”和“native routing”之间选择。一种是把每个 Pod 的流量封装在另一层里跨节点发送，另一种是让真实网络感知 Pod IP。我不知道该选哪个，也不知道权衡是什么。
8. Flannel、Calico、Cilium、Weave、AWS VPC CNI——有十几种选择。我该怎么选？
9. 我的集群自带默认 CNI，我从未质疑过。但现在我需要网络策略，有人说我的 CNI 不支持。另一个人说我应该全部用 Cilium。我完全不知道实际差异是什么。
