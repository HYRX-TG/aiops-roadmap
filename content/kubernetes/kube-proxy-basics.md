---
id: kube-proxy-basics
title: kube-proxy and How Services Route Traffic
zone: kubernetes
edges:
  to:
    - id: iptables-vs-ipvs
      question: >-
        We keep adding Services and networking latency keeps creeping up — are
        all those iptables rules the problem?
      detail: >-
        With a handful of Services everything was snappy. But we've scaled to
        hundreds and I'm seeing latency I can't explain. Every Service adds a
        bunch of iptables rules and the kernel scans them one by one. That
        can't scale forever. Is there a better way to do this?
difficulty: 2
tags:
  - kubernetes
  - kube-proxy
  - iptables
  - services
  - routing
  - k8s
category: concept
milestones:
  - >-
    Know that kube-proxy runs on every node and watches the API server for
    Service and Endpoint changes
  - >-
    Understand iptables mode: kube-proxy creates DNAT rules that intercept
    traffic to ClusterIPs and redirect to a randomly chosen backend pod
  - >-
    Be able to inspect the rules kube-proxy creates with iptables -t nat -L
  - >-
    Understand what happens when a pod dies: the endpoint is removed, but
    in-flight connections may still break during the transition
  - >-
    Know what session affinity does (sessionAffinity: ClientIP) and its
    limitations
title_zh: "kube-proxy 与 Service 如何路由流量"

---


When you create a Kubernetes Service, it gets a ClusterIP — a virtual IP that doesn't exist on any network interface. Yet you can curl it from any pod in the cluster and traffic reaches the right place. The component responsible is kube-proxy: it runs on every node, watches for Service changes, and programs iptables rules that intercept traffic to ClusterIPs and redirect it to real pod IPs.

<!-- DEEP_DIVE -->

## What kube-proxy does

kube-proxy runs as a DaemonSet on every node in the cluster. It watches the Kubernetes API server for two things:

1. **Services** — their ClusterIPs and ports
2. **EndpointSlices** — which pods are currently backing each Service

When a Service is created or updated, kube-proxy translates that information into networking rules on the node. In its default mode, those rules are iptables entries.

## How iptables mode works

When you create a Service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

kube-proxy creates iptables rules on every node that say:

1. If traffic is destined for `10.96.0.15:80` (the ClusterIP), intercept it
2. Pick one of the backend pods randomly
3. DNAT (Destination NAT) the packet — rewrite the destination from `10.96.0.15:80` to `10.244.1.5:8080` (a real pod IP)
4. The packet now flows through normal pod-to-pod routing to reach the selected pod

The ClusterIP itself is never assigned to any interface. It's a "virtual" IP that only exists as an iptables rule target. The kernel intercepts packets heading for it before they ever hit the network.

## Seeing the rules

You can inspect the iptables rules kube-proxy creates:

```bash
# SSH to a node or use kubectl debug
iptables -t nat -L -n | grep my-app
```

For a Service with three backends, you'll see rules that look roughly like this (simplified):

```
KUBE-SVC-XXXXX  ->  statistic mode random probability 0.333 -> KUBE-SEP-AAAA (pod 1)
KUBE-SVC-XXXXX  ->  statistic mode random probability 0.500 -> KUBE-SEP-BBBB (pod 2)
KUBE-SVC-XXXXX  ->  remaining                               -> KUBE-SEP-CCCC (pod 3)
```

kube-proxy uses probability-based random selection. With 3 pods: the first rule matches 33% of traffic, the second matches 50% of the remaining (= 33% total), and the third catches everything else (= 33% total). Equal distribution, but using sequential probability rather than actual load balancing.

## What happens when a pod dies

When a pod is deleted:

1. The API server removes the pod from the EndpointSlice
2. kube-proxy detects the change and removes the iptables rules for that pod
3. New connections stop going to the dead pod

But there's a race condition: between the pod starting to shut down and kube-proxy updating the rules, some traffic may still be routed to the dying pod. This is why graceful shutdown and proper readiness probes matter — the pod should stop accepting new connections before it starts tearing down.

Existing TCP connections to the dying pod may also break if the pod exits before the connections drain. Kubernetes doesn't automatically wait for in-flight requests to complete — that's the application's responsibility via `preStop` hooks and graceful shutdown handling.

## Session affinity

By default, kube-proxy's random selection means each request from the same client could hit a different pod. If your application needs sticky sessions:

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800   # 3 hours
```

This makes kube-proxy route all traffic from the same client IP to the same pod. It's useful for applications that store session state in memory, but it undermines load balancing — one very active client sends all its traffic to a single pod.

Better approach: store session state externally (Redis, a database) and let traffic distribute evenly.

## The kube-proxy modes

kube-proxy supports different backends for implementing service routing:

- **iptables** (default) — the approach described above. Simple, works everywhere, but scales poorly with thousands of Services.
- **IPVS** — uses the kernel's built-in L4 load balancer instead of iptables rules. Better performance at scale.
- **nftables** — newer iptables replacement, available in recent Kubernetes versions.
- **None** — don't run kube-proxy at all. Used when the CNI (like Cilium) handles service routing via eBPF.

For most clusters with a reasonable number of Services (up to a few hundred), iptables mode works fine. The performance difference only becomes visible at scale.

<!-- RESOURCES -->

- [Kubernetes Docs - Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/) -- type: docs, time: 20m
- [Kubernetes Docs - kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) -- type: docs, time: 10m
- [A Deep Dive into Kubernetes Service Routing](https://www.tkng.io/services/) -- type: guide, time: 25m

<!-- ZH_SUMMARY -->
当你创建一个 Kubernetes Service 时，它会获得一个 ClusterIP——一个不存在于任何网络接口上的虚拟 IP。然而，你可以在集群中的任意 pod 中 curl 它，流量就能到达正确的位置。负责这一功能的组件是 kube-proxy：它运行在每个节点上，监听 Service 的变化，并编写 iptables 规则，拦截发往 ClusterIP 的流量并将其重定向到真实的 pod IP。

<!-- ZH_DEEP_DIVE -->
## kube-proxy 的作用

kube-proxy 以 DaemonSet 的形式运行在集群中的每个节点上。它监听 Kubernetes API server 的两类资源：

1. **Services** —— 它们的 ClusterIP 和端口
2. **EndpointSlices** —— 当前为每个 Service 提供后端的 Pod

当 Service 被创建或更新时，kube-proxy 会将这些信息转换为节点上的网络规则。在其默认模式下，这些规则就是 iptables 条目。

## iptables 模式的工作原理

当你创建一个 Service 时：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

kube-proxy 会在每个节点上创建如下 iptables 规则：

1. 如果流量的目标是 `10.96.0.15:80`（该 ClusterIP），则拦截它
2. 随机选择一个后端 Pod
3. 对数据包执行 DNAT（目标 NAT）—— 将目标从 `10.96.0.15:80` 改写为 `10.244.1.5:8080`（一个真实的 Pod IP）
4. 数据包随后通过正常的 Pod 到 Pod 路由到达所选中的 Pod

ClusterIP 本身从未被分配给任何网络接口。它是一个“虚拟”IP，仅作为 iptables 规则的目标存在。内核在数据包真正进入网络之前就拦截了发往它的流量。

## 查看规则

你可以检查 kube-proxy 创建的 iptables 规则：

```bash
# SSH 到某个节点，或使用 kubectl debug
iptables -t nat -L -n | grep my-app
```

对于一个有三个后端的 Service，你会看到大致如下所示的规则（已简化）：

```
KUBE-SVC-XXXXX  ->  statistic mode random probability 0.333 -> KUBE-SEP-AAAA (pod 1)
KUBE-SVC-XXXXX  ->  statistic mode random probability 0.500 -> KUBE-SEP-BBBB (pod 2)
KUBE-SVC-XXXXX  ->  remaining                               -> KUBE-SEP-CCCC (pod 3)
```

kube-proxy 使用基于概率的随机选择。对于 3 个 Pod：第一条规则匹配 33% 的流量，第二条匹配剩余流量的 50%（= 总量的 33%），第三条捕获其余所有流量（= 总量的 33%）。分布是均匀的，但使用的是顺序概率而非真正的负载均衡。

## Pod 挂掉时会发生什么

当 Pod 被删除时：

1. API server 将该 Pod 从 EndpointSlice 中移除
2. kube-proxy 检测到变化，并移除该 Pod 对应的 iptables 规则
3. 新连接不再流向已死亡的 Pod

但存在竞态条件：从 Pod 开始关闭到 kube-proxy 更新规则之间，部分流量仍可能被路由到正在终止的 Pod。这就是优雅关闭和正确的就绪探针很重要的原因 —— Pod 应当在开始拆除之前停止接受新连接。

如果 Pod 在连接排空之前退出，发往该 Pod 的现有 TCP 连接也可能中断。Kubernetes 不会自动等待进行中的请求完成 —— 这是应用的责任，需要通过 `preStop` 钩子和优雅关闭处理来实现。

## 会话亲和性

默认情况下，kube-proxy 的随机选择意味着来自同一客户端的每个请求都可能命中不同的 Pod。如果你的应用需要粘性会话：

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800   # 3 小时
```

这会让 kube-proxy 将来自同一客户端 IP 的所有流量路由到同一个 Pod。这对于将会话状态存储在内存中的应用很有用，但它会破坏负载均衡 —— 一个非常活跃的客户端会将其所有流量发送到单个 Pod。

更好的做法：将会话状态存储在外部（Redis、数据库），让流量均匀分布。

## kube-proxy 的模式

kube-proxy 支持不同的后端来实现 Service 路由：

- **iptables**（默认）—— 上述方式。简单、处处可用，但在数千个 Service 的场景下扩展性较差。
- **IPVS** —— 使用内核内置的 L4 负载均衡器而非 iptables 规则。大规模场景下性能更好。
- **nftables** —— 较新的 iptables 替代品，在较新的 Kubernetes 版本中可用。
- **None** —— 完全不运行 kube-proxy。当 CNI（如 Cilium）通过 eBPF 处理 Service 路由时使用。

对于 Service 数量合理（最多几百个）的大多数集群，iptables 模式运行良好。性能差异只有在规模化时才会显现。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 虚拟 IP 与 Service 代理](https://kubernetes.io/docs/reference/networking/virtual-ips/) -- 类型：文档，时长：20 分钟
- [Kubernetes 文档 - kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) -- 类型：文档，时长：10 分钟
- [深入解析 Kubernetes Service 路由](https://www.tkng.io/services/) -- 类型：指南，时长：25 分钟

<!-- ZH_UI -->
1. 了解 kube-proxy 在每个节点上运行，并监听 API server 以获取 Service 和 Endpoint 的变化
2. 理解 iptables 模式：kube-proxy 创建 DNAT 规则，拦截发往 ClusterIP 的流量并重定向到随机选择的后端 pod
3. 能够使用 iptables -t nat -L 检查 kube-proxy 创建的规则
4. 理解 pod 死亡时会发生什么：endpoint 被移除，但过渡期间进行中的连接仍可能中断
5. 了解会话亲和性（sessionAffinity: ClientIP）的作用及其局限性
6. 我们不断添加 Service，网络延迟持续攀升——是那些 iptables 规则导致的问题吗？
7. 只有少量 Service 时一切都很流畅。但我们已经扩展到数百个，我看到了无法解释的延迟。每个 Service 都会添加一堆 iptables 规则，内核逐条扫描它们。这不可能无限扩展。有没有更好的办法？
