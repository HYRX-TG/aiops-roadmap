---
id: dns-debugging-k8s
title: Debugging Kubernetes DNS
zone: kubernetes
edges:
  to: []
difficulty: 3
tags:
  - kubernetes
  - dns
  - debugging
  - ndots
  - coredns
  - k8s
category: practice
milestones:
  - >-
    Understand the ndots:5 problem: why a lookup for `api.stripe.com` generates
    multiple failed queries across search domains before the real one succeeds
  - >-
    Know how search domains in /etc/resolv.conf work and how Kubernetes
    configures them
  - >-
    Diagnose common DNS failures: CoreDNS crash-looping, DNS timeouts vs
    NXDOMAIN, pods resolving external but not internal names
  - >-
    Use debugging tools: nslookup and dig from inside a pod, reading CoreDNS
    logs, the dnsutils debug pod
  - >-
    Understand DNS caching options: why it matters at scale, NodeLocal DNSCache
    for node-level caching
  - >-
    Know the dnsPolicy options on pods: ClusterFirst vs Default vs None and when
    you'd change them
title_zh: "调试 Kubernetes DNS"

---


DNS problems are the most common networking issue in Kubernetes clusters. Lookups time out, external domains resolve slowly, internal names return NXDOMAIN for no apparent reason. Most of these problems trace back to a few well-known causes — the ndots:5 default, CoreDNS resource issues, or misconfigured resolv.conf. Knowing how to systematically debug DNS saves hours of guesswork.

<!-- DEEP_DIVE -->

## The ndots:5 problem

This is the single most common Kubernetes DNS performance issue, and almost nobody explains it well.

Look at a pod's `/etc/resolv.conf`:

```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`ndots:5` means: if the name you're looking up has fewer than 5 dots, try appending each search domain first before trying the name as-is.

When your app looks up `api.stripe.com` (2 dots, less than 5):

1. Try `api.stripe.com.default.svc.cluster.local` → NXDOMAIN
2. Try `api.stripe.com.svc.cluster.local` → NXDOMAIN
3. Try `api.stripe.com.cluster.local` → NXDOMAIN
4. Try `api.stripe.com` → success

That's **four DNS queries** before the real one succeeds. Every single external domain lookup generates this burst. Under load, this multiplies and hammers CoreDNS.

### Fixing ndots

Option 1: Add a trailing dot to external names (makes it fully qualified, skips search domains):

```bash
# In application code or config
curl api.stripe.com.    # trailing dot = absolute name, no search domains
```

Option 2: Set ndots lower in the pod spec:

```yaml
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"
```

With `ndots:2`, names with 2+ dots (like `api.stripe.com`) are tried as-is first. Internal names like `my-service` (0 dots) still go through search domains.

Option 3: Deploy NodeLocal DNSCache (see below).

## The debugging toolkit

Start with a debug pod that has DNS tools:

```bash
# Run a pod with DNS utilities
kubectl run dnstest --image=registry.k8s.io/e2e-test-images/agnhost:2.39 \
  --restart=Never -- /bin/sh -c "sleep 3600"

# Or use kubectl debug to attach to an existing pod
kubectl debug -it my-pod --image=nicolaka/netshoot
```

### Test internal DNS

```bash
# Resolve a service name
kubectl exec dnstest -- nslookup my-service.default.svc.cluster.local

# Verbose lookup with dig
kubectl exec dnstest -- dig my-service.default.svc.cluster.local

# Check what nameserver the pod uses
kubectl exec dnstest -- cat /etc/resolv.conf
```

### Test external DNS

```bash
# This should work if CoreDNS forwards external queries correctly
kubectl exec dnstest -- nslookup google.com

# If external works but internal doesn't (or vice versa), that narrows the problem
```

## Common failures and what causes them

### Internal names fail, external names work

CoreDNS's Kubernetes plugin can't reach the API server, or the Service/Endpoints aren't registered. Check:

```bash
# Is the service you're looking up real?
kubectl get svc my-service -n default

# Is CoreDNS healthy?
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Everything fails — all DNS is broken

CoreDNS pods are likely down or unreachable:

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check if the kube-dns Service has endpoints
kubectl get endpoints -n kube-system kube-dns
```

If CoreDNS pods are running but the Service has no endpoints, the labels don't match.

### DNS is slow but not broken

Usually the ndots:5 problem. Verify by timing a lookup with a trailing dot:

```bash
# Slow (search domain iteration)
time kubectl exec dnstest -- nslookup api.stripe.com

# Fast (fully qualified, skips search domains)
time kubectl exec dnstest -- nslookup api.stripe.com.
```

If the second is significantly faster, ndots is the issue.

### Intermittent timeouts under load

CoreDNS is getting overwhelmed. Check resource usage:

```bash
kubectl top pods -n kube-system -l k8s-app=kube-dns
```

If CoreDNS is hitting memory or CPU limits, scale it up (more replicas) or deploy NodeLocal DNSCache.

## NodeLocal DNSCache

NodeLocal DNSCache runs a DNS caching agent on every node as a DaemonSet. Pods send DNS queries to the local cache first, which handles repeated lookups without going to CoreDNS. This dramatically reduces load on CoreDNS and avoids conntrack race conditions that cause intermittent DNS failures on Linux.

It's especially valuable in large clusters or environments with heavy DNS traffic. Most managed Kubernetes services (GKE, EKS, AKS) offer it as a one-click or one-flag option.

## dnsPolicy options

The `dnsPolicy` field on a pod controls how its `/etc/resolv.conf` is configured:

- **ClusterFirst** (default) — use CoreDNS for everything, fall back to node DNS for external names
- **Default** — inherit the node's DNS config (skip CoreDNS entirely)
- **None** — empty resolv.conf; you must provide everything via `dnsConfig`
- **ClusterFirstWithHostNet** — like ClusterFirst but for pods using host networking

You'd change this if a pod needs to use external DNS directly (e.g., a monitoring pod that should resolve names the way the node does, not through CoreDNS).

<!-- RESOURCES -->

- [Kubernetes Docs - Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) -- type: docs, time: 15m
- [Kubernetes DNS ndots Explained](https://pracucci.com/kubernetes-dns-resolution-ndots-options-and-why-it-may-affect-application-performances.html) -- type: article, time: 10m
- [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
DNS 问题是 Kubernetes 集群中最常见的网络问题。查询超时、外部域名解析缓慢、内部名称无缘无故返回 NXDOMAIN。大多数这类问题都可以追溯到几个众所周知的成因——ndots:5 默认值、CoreDNS 资源问题，或 resolv.conf 配置错误。掌握系统化调试 DNS 的方法，可以节省数小时的猜测时间。

<!-- ZH_DEEP_DIVE -->
## ndots:5 问题

这是 Kubernetes 中最常见的 DNS 性能问题，但几乎没有人能把它解释清楚。

看看一个 Pod 的 `/etc/resolv.conf`：

```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`ndots:5` 的意思是：如果你要查询的域名中点的数量少于 5 个，就先依次追加每个搜索域进行尝试，最后才按原样查询该域名。

当你的应用查询 `api.stripe.com`（2 个点，少于 5 个）时：

1. 尝试 `api.stripe.com.default.svc.cluster.local` → NXDOMAIN
2. 尝试 `api.stripe.com.svc.cluster.local` → NXDOMAIN
3. 尝试 `api.stripe.com.cluster.local` → NXDOMAIN
4. 尝试 `api.stripe.com` → 成功

在真正成功的那次查询之前，已经产生了 **四次 DNS 查询**。每一次外部域名查询都会产生这样一串查询。在高负载下，这会成倍放大并冲击 CoreDNS。

### 修复 ndots

方案 1：为外部域名添加末尾的点（使其成为完全限定域名，跳过搜索域）：

```bash
# 在应用代码或配置中
curl api.stripe.com.    # 末尾的点 = 绝对域名，不使用搜索域
```

方案 2：在 Pod spec 中把 ndots 调低：

```yaml
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"
```

使用 `ndots:2` 时，包含 2 个及以上点的域名（如 `api.stripe.com`）会先按原样尝试。像 `my-service`（0 个点）这样的内部名称仍会走搜索域。

方案 3：部署 NodeLocal DNSCache（见下文）。

## 调试工具集

先启动一个带有 DNS 工具的调试 Pod：

```bash
# 运行一个带 DNS 工具的 Pod
kubectl run dnstest --image=registry.k8s.io/e2e-test-images/agnhost:2.39 \
  --restart=Never -- /bin/sh -c "sleep 3600"

# 或者使用 kubectl debug 附加到现有 Pod
kubectl debug -it my-pod --image=nicolaka/netshoot
```

### 测试内部 DNS

```bash
# 解析一个 Service 名称
kubectl exec dnstest -- nslookup my-service.default.svc.cluster.local

# 使用 dig 进行详细查询
kubectl exec dnstest -- dig my-service.default.svc.cluster.local

# 检查 Pod 使用的 nameserver
kubectl exec dnstest -- cat /etc/resolv.conf
```

### 测试外部 DNS

```bash
# 如果 CoreDNS 正确转发外部查询，这应该能成功
kubectl exec dnstest -- nslookup google.com

# 如果外部正常但内部不正常（或反之），就能缩小问题范围
```

## 常见故障及其原因

### 内部名称失败，外部名称正常

CoreDNS 的 Kubernetes 插件无法访问 API server，或者 Service/Endpoints 未注册。检查：

```bash
# 你要查询的 Service 是否真实存在？
kubectl get svc my-service -n default

# CoreDNS 是否健康？
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### 全部失败——所有 DNS 都不可用

CoreDNS Pod 很可能已宕机或不可达：

```bash
# 检查 CoreDNS Pod
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 检查 kube-dns Service 是否有 endpoints
kubectl get endpoints -n kube-system kube-dns
```

如果 CoreDNS Pod 正在运行但 Service 没有 endpoints，说明标签不匹配。

### DNS 慢但未中断

通常是 ndots:5 问题。通过对比带末尾点的查询耗时来验证：

```bash
# 慢（遍历搜索域）
time kubectl exec dnstest -- nslookup api.stripe.com

# 快（完全限定域名，跳过搜索域）
time kubectl exec dnstest -- nslookup api.stripe.com.
```

如果第二个明显更快，那就是 ndots 的问题。

### 高负载下间歇性超时

CoreDNS 不堪重负。检查资源使用情况：

```bash
kubectl top pods -n kube-system -l k8s-app=kube-dns
```

如果 CoreDNS 达到内存或 CPU 限制，就扩容（增加副本数）或部署 NodeLocal DNSCache。

## NodeLocal DNSCache

NodeLocal DNSCache 以 DaemonSet 形式在每个节点上运行一个 DNS 缓存代理。Pod 首先将 DNS 查询发送到本地缓存，由本地缓存处理重复查询，而无需访问 CoreDNS。这大幅降低 CoreDNS 的负载，并避免 conntrack 竞态条件——该条件会导致 Linux 上出现间歇性 DNS 故障。

它在大型集群或 DNS 流量繁重的环境中尤其有价值。大多数托管 Kubernetes 服务（GKE、EKS、AKS）都提供一键或一个参数即可启用的选项。

## dnsPolicy 选项

Pod 上的 `dnsPolicy` 字段控制其 `/etc/resolv.conf` 的配置方式：

- **ClusterFirst**（默认）——所有查询都使用 CoreDNS，外部名称回退到节点 DNS
- **Default**——继承节点的 DNS 配置（完全跳过 CoreDNS）
- **None**——空的 resolv.conf；你必须通过 `dnsConfig` 提供所有配置
- **ClusterFirstWithHostNet**——与 ClusterFirst 类似，但适用于使用 host 网络的 Pod

如果某个 Pod 需要直接使用外部 DNS（例如，一个监控 Pod 需要像节点那样解析名称，而不是通过 CoreDNS），你就需要修改这个字段。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 调试 DNS 解析](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) -- 类型：文档，时长：15 分钟
- [Kubernetes DNS ndots 详解](https://pracucci.com/kubernetes-dns-resolution-ndots-options-and-why-it-may-affect-application-performances.html) -- 类型：文章，时长：10 分钟
- [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 理解 ndots:5 问题：为什么查询 `api.stripe.com` 会在真正成功之前，跨搜索域产生多次失败查询
2. 了解 /etc/resolv.conf 中搜索域的工作方式，以及 Kubernetes 如何配置它们
3. 诊断常见 DNS 故障：CoreDNS 崩溃循环、DNS 超时与 NXDOMAIN 的区别、Pod 能解析外部名称但无法解析内部名称
4. 使用调试工具：在 Pod 内使用 nslookup 和 dig、读取 CoreDNS 日志、dnsutils 调试 Pod
5. 理解 DNS 缓存方案：为什么在大规模场景下很重要、用于节点级缓存的 NodeLocal DNSCache
6. 了解 Pod 上的 dnsPolicy 选项：ClusterFirst 与 Default 与 None，以及何时需要更改它们
