---
id: network-debugging-k8s
title: Debugging Kubernetes Networking
zone: kubernetes
edges:
  to: []
difficulty: 3
tags:
  - kubernetes
  - debugging
  - networking
  - tcpdump
  - k8s
category: practice
milestones:
  - >-
    Follow a systematic approach: is it DNS? routing? the pod? the Service? the
    CNI?
  - >-
    Use kubectl exec with curl or wget to test connectivity from inside pods
  - >-
    Know how to use ephemeral debug containers with kubectl debug to attach to
    running pods
  - >-
    Capture packets with tcpdump inside pods or on nodes to trace actual network
    traffic
  - >-
    Diagnose common failures: pod can't reach external DNS, cross-node traffic
    drops, connection resets
  - >-
    Use CNI-specific tools: calicoctl for Calico, cilium status and hubble
    observe for Cilium
  - >-
    Debug network policy issues: applied a policy and broke everything — how to
    identify what's being blocked
title_zh: "调试 Kubernetes 网络"

---


When networking breaks in Kubernetes, the symptoms are vague — timeouts, connection refused, packets just disappearing. The key is to systematically narrow down which layer is broken: is it DNS? The Service? The CNI? A network policy? This node walks through a structured approach to debugging, with the tools to test each layer.

<!-- DEEP_DIVE -->

## Start with the right question

Before running commands, figure out which layer to investigate:

1. **Can the pod reach the internet?** If not → DNS or CNI issue
2. **Can the pod reach other pods on the same node?** If not → bridge or CNI issue
3. **Can the pod reach pods on other nodes?** If not → cross-node routing, overlay, or firewall issue
4. **Can the pod reach a Service by ClusterIP?** If not → kube-proxy or iptables issue
5. **Can the pod resolve Service names?** If not → CoreDNS issue
6. **Was everything working until you applied a NetworkPolicy?** → Policy issue

This ordering goes from the broadest scope to the narrowest. Start at the top and stop when you find the broken layer.

## The debugging toolkit

Most production container images are minimal — no curl, no dig, no ping. You need a way to get debugging tools into the picture.

### Ephemeral debug containers

The best approach — attach a debug container to a running pod without restarting it:

```bash
# Attach a debug container with networking tools
kubectl debug -it my-pod --image=nicolaka/netshoot --target=my-container

# Now you're inside a container that shares the pod's network namespace
# You can use curl, dig, tcpdump, ping, traceroute, etc.
```

The `netshoot` image is specifically built for this — it has every networking tool you'd want.

### Standalone debug pod

If you don't need to debug from a specific pod's perspective:

```bash
kubectl run debug --rm -it --image=nicolaka/netshoot -- bash
```

### Debug from the node

Sometimes the problem is at the node level, not inside a pod:

```bash
# On managed clusters, you can debug a node
kubectl debug node/my-node -it --image=ubuntu

# This gives you a shell on the node with access to the host network
# You can inspect iptables rules, routing tables, CNI config
chroot /host    # to access the node's filesystem
```

## Testing connectivity layer by layer

### Pod to pod (same node)

```bash
# Find two pods on the same node
kubectl get pods -o wide

# From pod A, curl pod B by IP
kubectl exec pod-a -- curl -s --max-time 3 <pod-b-ip>:8080
```

If this fails, the problem is local to the node — veth pairs, bridge, or CNI configuration.

### Pod to pod (cross-node)

```bash
# Find two pods on different nodes
kubectl get pods -o wide

# From pod on node-1, curl pod on node-2 by IP
kubectl exec pod-on-node1 -- curl -s --max-time 3 <pod-on-node2-ip>:8080
```

If same-node works but cross-node doesn't, the problem is in the overlay/routing between nodes. Check:
- Can the nodes themselves ping each other?
- Is the CNI pod healthy on both nodes?
- Are there firewall rules between nodes blocking the overlay port (VXLAN uses UDP 4789)?

### Pod to Service

```bash
# Test by ClusterIP
kubectl exec debug -- curl -s --max-time 3 <cluster-ip>:80

# Test by DNS name
kubectl exec debug -- curl -s --max-time 3 my-service.default.svc.cluster.local
```

If pod-to-pod works but pod-to-Service doesn't, the problem is in kube-proxy's iptables/IPVS rules. Check:
- Does the Service have endpoints? `kubectl get endpoints my-service`
- Are kube-proxy pods running? `kubectl get pods -n kube-system | grep kube-proxy`

### DNS resolution

```bash
# Test internal DNS
kubectl exec debug -- nslookup my-service.default.svc.cluster.local

# Test external DNS
kubectl exec debug -- nslookup google.com

# Check what the pod thinks the nameserver is
kubectl exec debug -- cat /etc/resolv.conf
```

If DNS fails, check CoreDNS health: `kubectl get pods -n kube-system -l k8s-app=kube-dns`

## Packet capture with tcpdump

When you need to see exactly what's on the wire:

```bash
# Capture inside a pod (using a debug container)
kubectl debug -it my-pod --image=nicolaka/netshoot --target=my-container
tcpdump -i eth0 -n port 8080

# Capture on a node (see all traffic, including encapsulated overlay)
kubectl debug node/my-node -it --image=nicolaka/netshoot
tcpdump -i any -n host <pod-ip>
```

Things to look for:
- **SYN packets going out but no SYN-ACK coming back** → the destination is unreachable (routing, firewall, or the destination pod isn't listening)
- **SYN-ACK coming back but RST immediately after** → the destination is rejecting the connection (wrong port, application not listening)
- **Packets flowing but no HTTP response** → application-level issue, not networking

## Network policy debugging

Network policies are the most common cause of "it was working, then it stopped." If you recently applied a NetworkPolicy:

```bash
# List all network policies in the namespace
kubectl get networkpolicies -n my-namespace

# Describe a specific policy to see what it allows/blocks
kubectl describe networkpolicy my-policy -n my-namespace
```

The key gotcha: a default-deny policy blocks ALL traffic unless explicit allow rules match. If you applied a deny-all policy and only allowed ingress on port 80, your pod can't reach DNS (port 53) or other services — you need to explicitly allow egress too.

With Cilium, debugging is easier:

```bash
# See dropped traffic (shows exactly which policy blocked it)
hubble observe --verdict DROPPED --namespace my-namespace

# See all flows for a specific pod
hubble observe --pod my-namespace/my-pod
```

## CNI-specific debugging

### Calico

```bash
# Check Calico node status
kubectl exec -n kube-system calico-node-xxxxx -- calico-node -bird-ready
calicoctl node status

# Check routes Calico programmed
calicoctl get workloadEndpoints -n my-namespace
```

### Cilium

```bash
# Check Cilium agent health
kubectl exec -n kube-system cilium-xxxxx -- cilium status

# Check endpoint (pod) connectivity
kubectl exec -n kube-system cilium-xxxxx -- cilium endpoint list

# Network flows via Hubble
hubble observe --namespace my-namespace
```

## The usual suspects

| Symptom | Most likely cause |
|---------|-------------------|
| Pods stuck in ContainerCreating | CNI pod crashed or CNI binary missing |
| Cross-node traffic fails | Overlay port (UDP 4789) blocked by firewall, or CNI pod unhealthy on one node |
| Service ClusterIP unreachable | kube-proxy not running, or endpoints empty (label mismatch) |
| DNS timeout | CoreDNS overloaded or crash-looping |
| Intermittent DNS failures | ndots:5 generating extra queries, or conntrack table full |
| Everything broke after applying a policy | Default-deny policy without sufficient allow rules |

<!-- RESOURCES -->

- [Kubernetes Docs - Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/) -- type: docs, time: 15m
- [netshoot - Container Networking Debugging](https://github.com/nicolaka/netshoot) -- type: tool, time: 10m
- [Kubernetes Docs - Ephemeral Debug Containers](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#ephemeral-container) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
当 Kubernetes 中的网络出现故障时，症状往往很模糊——超时、连接被拒绝、数据包凭空消失。关键在于系统性地缩小范围，确定是哪一层出了问题：是 DNS？Service？CNI？还是网络策略？本节将带你走一遍结构化的排查方法，并介绍用于测试每一层的工具。

<!-- ZH_DEEP_DIVE -->
## 从正确的问题开始

在运行命令之前，先弄清楚该排查哪一层：

1. **Pod 能访问互联网吗？** 如果不能 → DNS 或 CNI 问题
2. **Pod 能访问同一节点上的其他 Pod 吗？** 如果不能 → 网桥或 CNI 问题
3. **Pod 能访问其他节点上的 Pod 吗？** 如果不能 → 跨节点路由、overlay 或防火墙问题
4. **Pod 能通过 ClusterIP 访问 Service 吗？** 如果不能 → kube-proxy 或 iptables 问题
5. **Pod 能解析 Service 名称吗？** 如果不能 → CoreDNS 问题
6. **在应用 NetworkPolicy 之前一切正常吗？** → 策略问题

这个顺序从最广的范围到最窄的范围。从顶部开始，找到出问题的那一层就停下来。

## 调试工具包

大多数生产容器镜像都是精简的——没有 curl、没有 dig、没有 ping。你需要一种方式把调试工具引入进来。

### 临时调试容器

最佳方案——将一个调试容器附加到正在运行的 Pod 上，而无需重启它：

```bash
# Attach a debug container with networking tools
kubectl debug -it my-pod --image=nicolaka/netshoot --target=my-container

# Now you're inside a container that shares the pod's network namespace
# You can use curl, dig, tcpdump, ping, traceroute, etc.
```

`netshoot` 镜像就是专门为此构建的——它包含了你想要的所有网络工具。

### 独立调试 Pod

如果你不需要从特定 Pod 的视角进行调试：

```bash
kubectl run debug --rm -it --image=nicolaka/netshoot -- bash
```

### 从节点进行调试

有时问题出在节点层面，而不是 Pod 内部：

```bash
# On managed clusters, you can debug a node
kubectl debug node/my-node -it --image=ubuntu

# This gives you a shell on the node with access to the host network
# You can inspect iptables rules, routing tables, CNI config
chroot /host    # to access the node's filesystem
```

## 逐层测试连通性

### Pod 到 Pod（同一节点）

```bash
# Find two pods on the same node
kubectl get pods -o wide

# From pod A, curl pod B by IP
kubectl exec pod-a -- curl -s --max-time 3 <pod-b-ip>:8080
```

如果这一步失败，问题就局限在该节点本地——veth 对、网桥或 CNI 配置。

### Pod 到 Pod（跨节点）

```bash
# Find two pods on different nodes
kubectl get pods -o wide

# From pod on node-1, curl pod on node-2 by IP
kubectl exec pod-on-node1 -- curl -s --max-time 3 <pod-on-node2-ip>:8080
```

如果同节点正常但跨节点不正常，问题出在节点之间的 overlay/路由。检查：
- 节点之间本身能互相 ping 通吗？
- 两个节点上的 CNI Pod 都健康吗？
- 节点之间是否有防火墙规则阻止了 overlay 端口（VXLAN 使用 UDP 4789）？

### Pod 到 Service

```bash
# Test by ClusterIP
kubectl exec debug -- curl -s --max-time 3 <cluster-ip>:80

# Test by DNS name
kubectl exec debug -- curl -s --max-time 3 my-service.default.svc.cluster.local
```

如果 Pod 到 Pod 正常但 Pod 到 Service 不正常，问题出在 kube-proxy 的 iptables/IPVS 规则。检查：
- Service 有 endpoints 吗？`kubectl get endpoints my-service`
- kube-proxy Pod 在运行吗？`kubectl get pods -n kube-system | grep kube-proxy`

### DNS 解析

```bash
# Test internal DNS
kubectl exec debug -- nslookup my-service.default.svc.cluster.local

# Test external DNS
kubectl exec debug -- nslookup google.com

# Check what the pod thinks the nameserver is
kubectl exec debug -- cat /etc/resolv.conf
```

如果 DNS 失败，检查 CoreDNS 健康状态：`kubectl get pods -n kube-system -l k8s-app=kube-dns`

## 使用 tcpdump 抓包

当你需要确切看到网络上传输的内容时：

```bash
# Capture inside a pod (using a debug container)
kubectl debug -it my-pod --image=nicolaka/netshoot --target=my-container
tcpdump -i eth0 -n port 8080

# Capture on a node (see all traffic, including encapsulated overlay)
kubectl debug node/my-node -it --image=nicolaka/netshoot
tcpdump -i any -n host <pod-ip>
```

需要留意的现象：
- **SYN 包发出去了但没有 SYN-ACK 返回** → 目标不可达（路由、防火墙，或目标 Pod 没有在监听）
- **SYN-ACK 返回了但紧接着就是 RST** → 目标在拒绝连接（端口错误，应用没有在监听）
- **有数据包流动但没有 HTTP 响应** → 应用层问题，不是网络问题

## NetworkPolicy 调试

NetworkPolicy 是“本来好好的，然后突然就不行了”的最常见原因。如果你最近应用了 NetworkPolicy：

```bash
# List all network policies in the namespace
kubectl get networkpolicies -n my-namespace

# Describe a specific policy to see what it allows/blocks
kubectl describe networkpolicy my-policy -n my-namespace
```

关键的坑：default-deny 策略会阻止所有流量，除非有显式的 allow 规则匹配。如果你应用了一个 deny-all 策略，只允许了 80 端口的 ingress，那么你的 Pod 就无法访问 DNS（53 端口）或其他服务——你还需要显式允许 egress。

使用 Cilium 时，调试更容易：

```bash
# See dropped traffic (shows exactly which policy blocked it)
hubble observe --verdict DROPPED --namespace my-namespace

# See all flows for a specific pod
hubble observe --pod my-namespace/my-pod
```

## 特定 CNI 的调试

### Calico

```bash
# Check Calico node status
kubectl exec -n kube-system calico-node-xxxxx -- calico-node -bird-ready
calicoctl node status

# Check routes Calico programmed
calicoctl get workloadEndpoints -n my-namespace
```

### Cilium

```bash
# Check Cilium agent health
kubectl exec -n kube-system cilium-xxxxx -- cilium status

# Check endpoint (pod) connectivity
kubectl exec -n kube-system cilium-xxxxx -- cilium endpoint list

# Network flows via Hubble
hubble observe --namespace my-namespace
```

## 常见嫌疑对象

| 症状 | 最可能的原因 |
|---------|-------------------|
| Pod 卡在 ContainerCreating | CNI Pod 崩溃或 CNI 二进制文件缺失 |
| 跨节点流量失败 | Overlay 端口（UDP 4789）被防火墙阻止，或某个节点上的 CNI Pod 不健康 |
| Service ClusterIP 不可达 | kube-proxy 未运行，或 endpoints 为空（标签不匹配） |
| DNS 超时 | CoreDNS 过载或处于 crash-loop |
| 间歇性 DNS 失败 | ndots:5 产生额外查询，或 conntrack 表已满 |
| 应用策略后一切都不正常了 | Default-deny 策略没有足够的 allow 规则 |

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 调试 Service](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/) -- 类型: 文档, 时间: 15m
- [netshoot - 容器网络调试](https://github.com/nicolaka/netshoot) -- 类型: 工具, 时间: 10m
- [Kubernetes 文档 - 临时调试容器](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#ephemeral-container) -- 类型: 文档, 时间: 10m

<!-- ZH_UI -->
1. 遵循系统化方法：是 DNS？路由？Pod？Service？还是 CNI？
2. 使用 kubectl exec 配合 curl 或 wget 从 Pod 内部测试连通性
3. 掌握使用 kubectl debug 的临时调试容器挂接到运行中的 Pod
4. 在 Pod 内或节点上用 tcpdump 抓包，追踪实际网络流量
5. 诊断常见故障：Pod 无法访问外部 DNS、跨节点流量丢包、连接重置
6. 使用 CNI 专用工具：Calico 用 calicoctl，Cilium 用 cilium status 和 hubble observe
7. 调试网络策略问题：应用了策略后一切中断——如何定位被阻断的流量
