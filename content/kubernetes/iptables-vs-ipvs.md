---
id: iptables-vs-ipvs
title: "Service Routing at Scale: iptables vs IPVS"
zone: kubernetes
edges:
  to:
    - id: service-mesh-problems
      zone: kubernetes-production
      question: >-
        Traffic routing works, but everything between my services is unencrypted
        and I have zero visibility into what's calling what.
      detail: >-
        I can see that traffic reaches the right pods, but that's it. I don't
        know which service is calling which, I can't tell when requests between
        services fail, and none of it is encrypted — every pod talks plain HTTP
        to every other pod. I need observability and security between services,
        not just basic routing.
difficulty: 3
tags:
  - kubernetes
  - iptables
  - ipvs
  - kube-proxy
  - scaling
  - k8s
category: concept
milestones:
  - >-
    Understand the iptables scaling problem: every Service adds 8–15 rules
    across multiple chains, thousands of Services means tens of thousands of
    rules with O(n) chain scanning
  - >-
    Know what IPVS mode is: a real L4 load balancer in the kernel with
    hash-based O(1) lookup instead of linear chain scanning
  - >-
    Understand the load balancing algorithms IPVS supports: round-robin, least
    connections, weighted — compared to iptables random probability
  - >-
    Know the connection tracking differences between iptables and IPVS
  - >-
    Understand that eBPF (via Cilium) is the next evolution: skip kube-proxy
    entirely and handle service routing in eBPF programs
  - >-
    Know when to switch: hundreds of Services, need smarter load balancing, or
    want to eliminate kube-proxy
title_zh: "大规模服务路由：iptables 与 IPVS 对比"

---


kube-proxy's default iptables mode works fine for small clusters. But iptables was never designed for thousands of dynamically changing rules. At scale — hundreds or thousands of Services — every packet traverses a long chain of rules, updates require rewriting the entire table, and latency starts creeping up. IPVS and eBPF are the two alternatives that solve this differently.

<!-- DEEP_DIVE -->

## The iptables scaling problem

Every Kubernetes Service creates roughly 8–15 iptables rules (entries across KUBE-SERVICES, KUBE-SVC, and KUBE-SEP chains — more with additional endpoints and ports). With 1,000 Services, that's easily 10,000+ rules. With 5,000 Services, you're looking at 50,000–100,000+ rules.

The problem is how iptables processes packets:

- **Linear chain scanning** — when a packet arrives, the kernel evaluates rules one by one until it finds a match. With 5,000 Service rules, the worst case is scanning all 5,000 for every packet.
- **Full table replacement** — when kube-proxy needs to update a single Service (a pod was added or removed), it can't surgically update one rule. It rewrites the entire iptables table atomically. With tens of thousands of rules, this operation takes seconds and briefly blocks all rule evaluation.
- **Connection tracking pressure** — iptables uses conntrack to track connections. Under heavy load with many Services, the conntrack table fills up and starts dropping packets.

For a cluster with 50 Services, none of this matters. At 500+ Services with high traffic, you'll start seeing measurable latency from rule processing.

## IPVS mode

IPVS (IP Virtual Server) is a load balancer built into the Linux kernel. It was designed specifically for this — routing traffic to backend servers at high scale.

Instead of a chain of iptables rules, IPVS uses hash tables. When a packet arrives for a ClusterIP, IPVS does an O(1) hash table lookup to find the backend — no scanning, no matter how many Services exist.

### Switching to IPVS

To use IPVS mode, configure kube-proxy:

```yaml
# kube-proxy ConfigMap
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
ipvs:
  scheduler: "rr"    # round-robin (default)
```

On managed clusters, this is often a cluster setting or flag when creating the cluster.

### Load balancing algorithms

This is one of IPVS's biggest advantages over iptables. Instead of random probability, IPVS supports real load balancing algorithms:

- **rr** (round-robin) — requests go to backends in order. Simple, predictable.
- **lc** (least connections) — send to the backend with the fewest active connections. Better for uneven request durations.
- **wrr** (weighted round-robin) — backends with higher weights get more traffic. Useful for heterogeneous pod sizes.
- **sh** (source hashing) — consistent mapping from client IP to backend. Similar to sessionAffinity but at the IPVS level.

iptables can't do any of this — it only supports random probability-based distribution.

### IPVS performance

At scale, the difference is significant:

| Metric | iptables | IPVS |
|--------|----------|------|
| Rule lookup | O(n) linear scan | O(1) hash lookup |
| Updating one Service | Rewrite all rules | Update one entry |
| 10,000 Services | Noticeable latency | No measurable impact |
| Load balancing | Random probability | rr, lc, wrr, sh |

IPVS still uses iptables for some things (NodePort handling, masquerading), but the hot path — routing packets to the right pod — uses the much faster IPVS data path.

## eBPF: skipping kube-proxy entirely

Both iptables and IPVS rely on kube-proxy to program the rules. Cilium takes a different approach: it replaces kube-proxy entirely and handles service routing with eBPF programs attached directly to network interfaces.

The eBPF approach bypasses iptables/IPVS completely. When a pod sends a packet to a ClusterIP, a Cilium eBPF program on the pod's virtual interface rewrites the destination immediately — before the packet even reaches the kernel's networking stack. No rule chains, no hash tables in a separate subsystem — just an inline eBPF map lookup.

This is the fastest option at any scale, but it requires running Cilium as your CNI. You can't mix kube-proxy IPVS with Cilium eBPF service routing — it's one or the other.

## When to switch

**Stick with iptables if:** You have fewer than a few hundred Services and aren't seeing latency issues. It's the simplest and most battle-tested option.

**Switch to IPVS if:** You have hundreds of Services, want real load balancing algorithms, or are seeing iptables-related latency. IPVS is a drop-in replacement — just change the kube-proxy mode.

**Use Cilium eBPF if:** You're already running Cilium (or evaluating it as your CNI) and want to simplify the stack by removing kube-proxy entirely. This is the most performant option but comes with the commitment to Cilium as your CNI.

<!-- RESOURCES -->

- [Kubernetes Docs - IPVS Mode](https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-ipvs) -- type: docs, time: 15m
- [IPVS-Based In-Cluster Load Balancing Deep Dive](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/) -- type: article, time: 20m
- [Cilium kube-proxy Replacement](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
kube-proxy 默认的 iptables 模式在小型集群中运行良好。但 iptables 从来就不是为成千上万条动态变化的规则而设计的。在大规模场景下——数百或数千个 Service——每个数据包都要穿越一长串规则链，更新时需要重写整张表，延迟也开始逐渐上升。IPVS 和 eBPF 是两种以不同方式解决这一问题的替代方案。

<!-- ZH_DEEP_DIVE -->
## iptables 的扩展性问题

每个 Kubernetes Service 大约会创建 8–15 条 iptables 规则（分布在 KUBE-SERVICES、KUBE-SVC 和 KUBE-SEP 链中的条目——随着 endpoint 和端口的增加，规则数量还会更多）。1,000 个 Service 就轻松达到 10,000+ 条规则。5,000 个 Service 则意味着 50,000–100,000+ 条规则。

问题在于 iptables 处理数据包的方式：

- **线性链扫描** —— 当数据包到达时，内核逐条评估规则，直到找到匹配项。有 5,000 条 Service 规则时，最坏情况是每个数据包都要扫描全部 5,000 条。
- **全表替换** —— 当 kube-proxy 需要更新单个 Service（有 pod 被添加或移除）时，它无法精准地只更新一条规则，而是原子性地重写整个 iptables 表。在数万条规则的情况下，这个操作需要数秒，并会短暂阻塞所有规则评估。
- **连接跟踪压力** —— iptables 使用 conntrack 跟踪连接。在大量 Service 的高负载下，conntrack 表会被填满并开始丢包。

对于只有 50 个 Service 的集群，这些都不是问题。当 Service 数量达到 500+ 且流量较高时，你就会开始看到规则处理带来的可测量延迟。

## IPVS 模式

IPVS（IP Virtual Server）是内置于 Linux 内核的负载均衡器。它正是为此而设计的——在大规模场景下将流量路由到后端服务器。

IPVS 不使用 iptables 规则链，而是使用哈希表。当数据包到达某个 ClusterIP 时，IPVS 通过 O(1) 的哈希表查找找到后端——无论存在多少 Service，都无需扫描。

### 切换到 IPVS

要使用 IPVS 模式，请配置 kube-proxy：

```yaml
# kube-proxy ConfigMap
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
ipvs:
  scheduler: "rr"    # round-robin (default)
```

在托管集群上，这通常是创建集群时的一个集群设置或参数。

### 负载均衡算法

这是 IPVS 相比 iptables 的最大优势之一。IPVS 不使用随机概率，而是支持真正的负载均衡算法：

- **rr**（round-robin，轮询）—— 请求按顺序发往后端。简单、可预测。
- **lc**（least connections，最少连接）—— 发往活跃连接数最少的后端。更适合请求时长不均的场景。
- **wrr**（weighted round-robin，加权轮询）—— 权重更高的后端获得更多流量。适用于 pod 规格异构的场景。
- **sh**（source hashing，源地址哈希）—— 从客户端 IP 到后端的稳定映射。类似于 sessionAffinity，但在 IPVS 层面实现。

iptables 无法做到这些——它只支持基于随机概率的分配。

### IPVS 性能

在大规模场景下，差异非常显著：

| 指标 | iptables | IPVS |
|--------|----------|------|
| 规则查找 | O(n) 线性扫描 | O(1) 哈希查找 |
| 更新单个 Service | 重写所有规则 | 更新一个条目 |
| 10,000 个 Service | 明显延迟 | 无可测量的影响 |
| 负载均衡 | 随机概率 | rr、lc、wrr、sh |

IPVS 在某些方面仍然使用 iptables（NodePort 处理、masquerading），但热路径——将数据包路由到正确的 pod——使用的是快得多的 IPVS 数据路径。

## eBPF：完全跳过 kube-proxy

iptables 和 IPVS 都依赖 kube-proxy 来编写规则。Cilium 采用了不同的方式：它完全取代 kube-proxy，通过直接挂载到网络接口上的 eBPF 程序来处理服务路由。

eBPF 方式完全绕过了 iptables/IPVS。当 pod 向某个 ClusterIP 发送数据包时，pod 虚拟接口上的 Cilium eBPF 程序会立即重写目标地址——甚至在数据包到达内核网络栈之前。没有规则链，没有独立子系统中的哈希表——只有一次内联的 eBPF map 查找。

这是任何规模下最快的选项，但它要求以 Cilium 作为你的 CNI。你不能将 kube-proxy IPVS 与 Cilium eBPF 服务路由混用——只能二选一。

## 何时切换

**继续使用 iptables，如果：** 你的 Service 数量少于几百个，且没有遇到延迟问题。它是最简单、经过最多实战检验的选项。

**切换到 IPVS，如果：** 你有数百个 Service，想要真正的负载均衡算法，或者遇到了与 iptables 相关的延迟。IPVS 是可直接替换的方案——只需更改 kube-proxy 模式。

**使用 Cilium eBPF，如果：** 你已经在运行 Cilium（或正在评估将其作为 CNI），并希望通过完全移除 kube-proxy 来简化技术栈。这是性能最高的选项，但需要承诺将 Cilium 作为你的 CNI。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - IPVS 模式](https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-ipvs) -- 类型: 文档, 时间: 15m
- [基于 IPVS 的集群内负载均衡深入解析](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/) -- 类型: 文章, 时间: 20m
- [Cilium kube-proxy 替换](https://docs.cilium.io/en/stable/network/kubernetes/kubeproxy-free/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 理解 iptables 的扩展性问题：每个 Service 会在多条链上添加 8–15 条规则，数千个 Service 意味着数万条规则，链扫描复杂度为 O(n)
2. 了解什么是 IPVS 模式：内核中的真正 L4 负载均衡器，使用基于哈希的 O(1) 查找，而非线性链扫描
3. 理解 IPVS 支持的负载均衡算法：轮询、最少连接、加权——与 iptables 的随机概率相比
4. 了解 iptables 与 IPVS 在连接跟踪上的差异
5. 理解 eBPF（通过 Cilium）是下一演进方向：完全跳过 kube-proxy，在 eBPF 程序中处理服务路由
6. 知道何时切换：数百个 Service、需要更智能的负载均衡，或希望消除 kube-proxy
7. 流量路由能正常工作，但我的服务之间一切都是未加密的，而且我完全无法看清谁在调用谁。
8. 我能看到流量到达了正确的 Pod，但仅此而已。我不知道哪个服务在调用哪个服务，无法判断服务间请求何时失败，而且这一切都未加密——每个 Pod 都用明文 HTTP 与其他 Pod 通信。我需要在服务之间实现可观测性和安全性，而不仅仅是基本路由。
