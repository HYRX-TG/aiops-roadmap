---
id: k8s-networking-model
title: How Kubernetes Networking Works
zone: kubernetes
edges:
  to:
    - id: pod-to-pod-networking
      question: >-
        Every pod gets its own IP and can reach every other pod — but how? My
        pods are on completely different machines.
      detail: >-
        I have pods on Node A and pods on Node B. They're on different machines
        with different network cables. But somehow a pod on one node can just
        curl a pod on another node by IP and it works. What is actually carrying
        that traffic between machines? I want to understand what's happening
        under the hood.
    - id: what-is-cni
      question: >-
        Every pod gets an IP and the network just works — but who sets it all up
        when a pod starts?
      detail: >-
        When I run a pod, it gets an IP address and can talk to other pods. But
        Kubernetes itself doesn't do networking — it says right in the docs that
        it delegates to a 'network plugin.' I've seen clusters break because
        this plugin was misconfigured, and I don't even know what it is.
    - id: coredns
      question: >-
        I curl `my-service.default.svc.cluster.local` and it resolves — who's
        running a DNS server in my cluster?
      detail: >-
        I've never set up a DNS server in this cluster, but every pod can
        resolve Service names. I don't know where it runs, what happens if it
        crashes, or why some DNS lookups take five seconds when they should be
        instant. It's a black box that everything depends on.
    - id: kube-proxy-basics
      question: >-
        A Service gives me a ClusterIP that I can reach from any pod — but that
        IP doesn't belong to anything. How does that work?
      detail: >-
        I ran `kubectl get svc` and got a ClusterIP like 10.96.0.1. I can curl
        it from any pod in the cluster and it reaches my app. But that IP isn't
        any pod's IP, and it's not any node's IP. It's a made-up address that
        somehow routes to the right place. What is doing that?
difficulty: 2
tags:
  - kubernetes
  - networking
  - pod-network
  - flat-network
  - k8s
category: concept
milestones:
  - >-
    Understand the Kubernetes networking contract: every pod gets a real routable
    IP, no NAT between pods, all pods can reach all other pods
  - >-
    Know how this differs from Docker's default bridge networking where
    containers share an IP and use port mapping
  - >-
    Identify the three networking problems Kubernetes solves: pod-to-pod,
    pod-to-service, and external-to-cluster
  - >-
    Understand that Kubernetes defines the networking rules but doesn't
    implement them — a network plugin handles the actual implementation
title_zh: "Kubernetes 网络的工作原理"

---


Kubernetes networking is built on one big promise: every pod gets its own real IP address, and every pod can talk to every other pod directly — no NAT, no port mapping. This is fundamentally different from Docker's default networking, and understanding this contract is the key to understanding everything else about how traffic moves inside a cluster.

<!-- DEEP_DIVE -->

## The networking contract

Kubernetes doesn't ship a networking implementation. Instead, it defines a set of rules that any networking solution must follow:

1. **Every pod gets its own IP address.** Not a port on the node's IP — its own unique IP, routable within the cluster.
2. **All pods can communicate with all other pods directly.** A pod on Node A can reach a pod on Node B by IP without any NAT or tunneling (from the pod's perspective).
3. **Agents on a node can communicate with all pods on that node.** Processes running directly on the node (like kubelet) can reach pod IPs on that node.

That's it. Kubernetes says "make these things true" and hands the actual work to a network plugin.

## How this differs from Docker

If you've used Docker without Kubernetes, you're used to a different model. Docker's default bridge networking gives every container a private IP on a virtual bridge (`docker0`), but those IPs aren't routable outside the host. To access a container from another machine, you map a container port to a host port with `-p 8080:80`.

Kubernetes throws that away entirely. There's no port mapping. Pod IPs are real within the cluster. If your pod is at `10.244.1.5`, any other pod in the cluster can `curl 10.244.1.5:8080` directly.

This is why you never see `-p` flags or port mapping in Kubernetes — every pod listens on whatever port it wants, and there are no collisions because every pod has its own IP.

## Three networking problems

Kubernetes networking solves three distinct problems, each at a different layer:

### Pod-to-pod

How does pod `10.244.1.5` on Node A reach pod `10.244.2.3` on Node B? Something has to move packets between nodes and deliver them to the right pod. This is where the CNI plugin does its work.

### Pod-to-service

Pods die and get recreated with new IPs. Services provide a stable virtual IP (ClusterIP) that load-balances across a changing set of pod IPs. Something has to intercept traffic to that virtual IP and route it to a real pod. This is what kube-proxy handles.

### External-to-cluster

Users outside the cluster need to reach your app. NodePort, LoadBalancer Services, and Ingress each solve this differently — from raw port exposure to cloud load balancers to HTTP routing.

## Who implements the contract?

Kubernetes delegates networking to external components:

- **CNI plugin** (Calico, Cilium, Flannel, etc.) — creates the pod network, assigns IPs, routes traffic between nodes
- **kube-proxy** — handles Service routing by programming iptables/IPVS rules on each node
- **CoreDNS** — provides DNS-based service discovery so pods can find Services by name

Each of these is a separate system. They work together but are independently swappable. You can replace your CNI without touching kube-proxy, or replace kube-proxy with Cilium's eBPF implementation without changing how DNS works.

## Seeing it in action

You can observe the networking model directly:

```bash
# Get a pod's IP
kubectl get pod my-app -o wide
# NAME     READY   IP           NODE
# my-app   1/1     10.244.1.5   node-1

# From another pod, you can reach it directly
kubectl exec other-pod -- curl 10.244.1.5:8080

# The node also has a different IP
kubectl get node node-1 -o wide
# NAME     INTERNAL-IP    ...
# node-1   192.168.1.10   ...
```

The pod IP (`10.244.1.5`) and the node IP (`192.168.1.10`) are on completely different subnets. The CNI plugin is responsible for making traffic to `10.244.x.x` reach the right pod on the right node.

<!-- RESOURCES -->

- [Kubernetes Docs - Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/) -- type: docs, time: 15m
- [A Guide to the Kubernetes Networking Model](https://sookocheff.com/post/kubernetes/understanding-kubernetes-networking-model/) -- type: article, time: 20m
- [Kubernetes Networking Demystified](https://www.tkng.io/) -- type: guide, time: 30m

<!-- ZH_SUMMARY -->
Kubernetes 网络建立在一个重要承诺之上：每个 Pod 都拥有自己真实的 IP 地址，并且每个 Pod 都能直接与其它所有 Pod 通信——无需 NAT，无需端口映射。这与 Docker 的默认网络有着根本性的不同，而理解这一约定，是理解集群内部流量如何流转及其它一切相关机制的关键。

<!-- ZH_DEEP_DIVE -->
## 网络契约

Kubernetes 本身并不提供网络实现。相反，它定义了一组任何网络方案都必须遵循的规则：

1. **每个 Pod 都拥有自己的 IP 地址。** 不是节点 IP 上的某个端口，而是自己独有的 IP，可在集群内路由。
2. **所有 Pod 都能直接与所有其他 Pod 通信。** Node A 上的 Pod 可以通过 IP 直接访问 Node B 上的 Pod，无需任何 NAT 或隧道（从 Pod 的视角来看）。
3. **节点上的代理进程能与该节点上的所有 Pod 通信。** 直接运行在节点上的进程（如 kubelet）可以访问该节点上的 Pod IP。

仅此而已。Kubernetes 只说“让这些条件成立”，然后把实际工作交给网络插件。

## 与 Docker 的区别

如果你用过没有 Kubernetes 的 Docker，那你习惯的是另一种模型。Docker 默认的 bridge 网络会给每个容器在虚拟网桥（`docker0`）上分配一个私有 IP，但这些 IP 在宿主机之外无法路由。要从另一台机器访问容器，需要用 `-p 8080:80` 把容器端口映射到宿主机端口。

Kubernetes 完全抛弃了这套做法。没有端口映射。Pod IP 在集群内是真实可路由的。如果你的 Pod 位于 `10.244.1.5`，集群中任何其他 Pod 都可以直接 `curl 10.244.1.5:8080`。

这就是为什么你在 Kubernetes 中从来看不到 `-p` 参数或端口映射——每个 Pod 想监听什么端口就监听什么端口，不存在冲突，因为每个 Pod 都有自己的 IP。

## 三个网络问题

Kubernetes 网络解决三个不同的问题，各自处于不同的层次：

### Pod 到 Pod

Node A 上的 Pod `10.244.1.5` 如何到达 Node B 上的 Pod `10.244.2.3`？必须有某种机制在节点之间搬运数据包，并将其投递到正确的 Pod。这正是 CNI 插件发挥作用的地方。

### Pod 到 Service

Pod 会消亡并以新 IP 重建。Service 提供一个稳定的虚拟 IP（ClusterIP），在一组不断变化的 Pod IP 之上做负载均衡。必须有某种机制拦截发往该虚拟 IP 的流量，并将其路由到真实的 Pod。这就是 kube-proxy 负责的事情。

### 外部到集群

集群之外的用户需要访问你的应用。NodePort、LoadBalancer Service 和 Ingress 各自以不同方式解决这个问题——从直接暴露端口，到云负载均衡器，再到 HTTP 路由。

## 谁来履行契约？

Kubernetes 将网络委托给外部组件：

- **CNI 插件**（Calico、Cilium、Flannel 等）——创建 Pod 网络、分配 IP、在节点之间路由流量
- **kube-proxy**——通过在每个节点上编写 iptables/IPVS 规则来处理 Service 路由
- **CoreDNS**——提供基于 DNS 的服务发现，使 Pod 能按名称找到 Service

每一个都是独立的系统。它们协同工作，但可以独立替换。你可以在不动 kube-proxy 的情况下替换 CNI，也可以用 Cilium 的 eBPF 实现替换 kube-proxy，而无需改变 DNS 的工作方式。

## 实际观察

你可以直接观察网络模型：

```bash
# Get a pod's IP
kubectl get pod my-app -o wide
# NAME     READY   IP           NODE
# my-app   1/1     10.244.1.5   node-1

# From another pod, you can reach it directly
kubectl exec other-pod -- curl 10.244.1.5:8080

# The node also has a different IP
kubectl get node node-1 -o wide
# NAME     INTERNAL-IP    ...
# node-1   192.168.1.10   ...
```

Pod IP（`10.244.1.5`）和节点 IP（`192.168.1.10`）处于完全不同的子网。CNI 插件负责让发往 `10.244.x.x` 的流量到达正确节点上的正确 Pod。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 集群网络](https://kubernetes.io/docs/concepts/cluster-administration/networking/) -- 类型: 文档, 时间: 15m
- [Kubernetes 网络模型指南](https://sookocheff.com/post/kubernetes/understanding-kubernetes-networking-model/) -- 类型: 文章, 时间: 20m
- [Kubernetes 网络揭秘](https://www.tkng.io/) -- 类型: 指南, 时间: 30m

<!-- ZH_UI -->
1. 理解 Kubernetes 网络契约：每个 pod 获得一个真实可路由的 IP，pod 之间没有 NAT，所有 pod 都能访问所有其他 pod
2. 了解这与 Docker 默认桥接网络的区别——后者中容器共享一个 IP 并使用端口映射
3. 识别 Kubernetes 解决的三个网络问题：pod 到 pod、pod 到 service、外部到集群
4. 理解 Kubernetes 定义网络规则但不实现它们——网络插件负责实际实现
5. 每个 pod 都有自己的 IP，并且能访问其他所有 pod——但这是怎么做到的？我的 pod 在完全不同的机器上。
6. 我在节点 A 上有 pod，在节点 B 上也有 pod。它们在不同的机器上，使用不同的网线。但不知何故，一个节点上的 pod 可以直接用 IP curl 另一个节点上的 pod，而且能通。到底是什么在机器之间承载这些流量？我想理解底层发生了什么。
7. 每个 pod 都获得一个 IP，网络就能正常工作——但 pod 启动时是谁把这一切设置好的？
8. 当我运行一个 pod 时，它获得一个 IP 地址并能与其他 pod 通信。但 Kubernetes 本身不做网络——文档里明确说它委托给“网络插件”。我见过集群因为插件配置错误而崩溃，而我甚至不知道它是什么。
9. 我 curl `my-service.default.svc.cluster.local`，它能解析——是谁在我的集群里运行 DNS 服务器？
10. 我从未在这个集群里设置过 DNS 服务器，但每个 pod 都能解析 Service 名称。我不知道它运行在哪里、如果它崩溃了会发生什么，或者为什么有些 DNS 查询需要五秒而本应瞬间完成。它是一个所有东西都依赖的黑盒。
11. 一个 Service 给我一个 ClusterIP，我可以从任何 pod 访问它——但那个 IP 不属于任何东西。这是怎么工作的？
12. 我运行了 `kubectl get svc`，得到了一个类似 10.96.0.1 的 ClusterIP。我可以从集群中任何 pod curl 它，并且能到达我的应用。但那个 IP 不是任何 pod 的 IP，也不是任何节点的 IP。它是一个凭空编造的地址，却不知何故路由到了正确的地方。是什么在做这件事？
