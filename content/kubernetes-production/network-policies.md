---
id: network-policies
title: Network Policies and Pod Isolation
zone: kubernetes-production
edges:
  to: []
difficulty: 3
tags:
  - kubernetes
  - network-policy
  - isolation
  - namespaces
  - egress
  - ingress
  - k8s
  - production
  - security
category: concept
milestones:
  - >-
    Understand that Kubernetes has no network isolation by default — any pod
    can reach any other pod in the cluster by IP
  - >-
    Know what a NetworkPolicy does: it selects pods by label and specifies
    which ingress and egress connections are allowed
  - >-
    Understand the default-deny pattern: apply a deny-all policy first, then
    add explicit allow rules only for what's needed
  - >-
    Know that NetworkPolicy requires a CNI plugin that enforces it (Calico,
    Cilium, Weave) — not all CNIs do
  - >-
    Apply namespace isolation: allow a pod to talk only to pods in its own
    namespace plus specific external dependencies
title_zh: "网络策略与 Pod 隔离"

---


By default, any pod in a Kubernetes cluster can send traffic to any other pod by IP address, regardless of namespace. There is no network firewall between namespaces, no isolation between services. NetworkPolicies are the Kubernetes mechanism for defining which pods are allowed to communicate — but they only work if your CNI enforces them.

<!-- DEEP_DIVE -->

## The open-by-default problem

In a default Kubernetes cluster with no NetworkPolicies applied:
- Your payment service can make HTTP calls to your internal admin API
- A pod in the `staging` namespace can reach pods in the `production` namespace
- Any compromised pod can try to reach any other service in the cluster

This is fine for small internal systems. It becomes a real risk when you have sensitive services, regulated data, or significant blast radius from a single compromised pod.

## What a NetworkPolicy does

A NetworkPolicy selects pods using a label selector and defines which ingress (incoming) and egress (outgoing) connections are allowed. Anything not explicitly allowed is denied — but only if a default-deny policy is in place.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database          # this policy applies to database pods
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api       # only allow traffic from api pods
      ports:
        - protocol: TCP
          port: 5432
```

This policy says: pods labeled `app: database` can only receive traffic on port 5432 from pods labeled `app: api`. Everything else is dropped.

## The default-deny pattern

NetworkPolicies are additive — they only restrict pods that have at least one policy selecting them. A pod with no policies is unrestricted.

The right approach: apply a deny-all policy to every namespace first, then add explicit allow rules.

```yaml
# Deny all ingress and egress for all pods in this namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}         # empty selector = select all pods
  policyTypes:
    - Ingress
    - Egress
```

Now nothing can communicate. Add explicit policies for what's needed:

```yaml
# Allow DNS (required for almost everything)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
```

Build up your policies incrementally: add the default-deny, then enable communication service by service, testing as you go.

## Namespace isolation

Restrict communication to only intra-namespace traffic plus specific exceptions:

```yaml
# Allow ingress only from pods in the same namespace
ingress:
  - from:
      - podSelector: {}    # any pod in the same namespace

# Allow ingress from a specific other namespace
ingress:
  - from:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: monitoring
        podSelector:
          matchLabels:
            app: prometheus
```

Combining `namespaceSelector` and `podSelector` in the same `from` entry means "pods matching this selector in the namespace matching that selector" — it's an AND. Putting them in separate `from` entries means OR.

## CNI requirement: not all enforce NetworkPolicy

NetworkPolicy is an API object. The enforcement depends on your CNI plugin:

**Enforce NetworkPolicy:** Calico, Cilium, Weave Net, Antrea

**Do NOT enforce NetworkPolicy:** Flannel (by default)

If you apply a NetworkPolicy and your CNI doesn't enforce it, the policy is silently ignored. Traffic flows freely. Check which CNI your cluster uses.

For managed clusters: GKE uses Calico or Dataplane V2 (Cilium-based). EKS uses VPC CNI (does not enforce NetworkPolicy by default) — you need to enable the network policy controller separately. AKS supports Calico and Cilium.

## Testing your policies

After applying policies, verify they work:

```bash
# From an api pod, connect to the database - should work
kubectl exec -it api-pod -n production -- nc -zv database-svc 5432

# From a web pod, connect to the database - should be blocked
kubectl exec -it web-pod -n production -- nc -zv database-svc 5432
# Connection should timeout or be refused
```

Tools like `netshoot` (a pod with networking utilities) are useful for testing reachability within the cluster.

<!-- RESOURCES -->

- [Kubernetes Docs - Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) -- type: docs, time: 25m
- [Network Policy Editor (visual tool)](https://editor.networkpolicy.io/) -- type: tool, time: 15m

<!-- ZH_SUMMARY -->
默认情况下，Kubernetes 集群中的任何 Pod 都可以通过 IP 地址向任何其他 Pod 发送流量，无论它们位于哪个命名空间。命名空间之间没有网络防火墙，服务之间也没有隔离。NetworkPolicy 是 Kubernetes 中用于定义哪些 Pod 允许通信的机制——但只有当你的 CNI 强制执行这些策略时，它们才会生效。

<!-- ZH_DEEP_DIVE -->
## 默认开放的问题

在未应用任何 NetworkPolicy 的默认 Kubernetes 集群中：
- 你的支付服务可以向内部管理 API 发起 HTTP 调用
- `staging` 命名空间中的 Pod 可以访问 `production` 命名空间中的 Pod
- 任何被攻陷的 Pod 都可以尝试访问集群中的任何其他服务

对于小型内部系统来说这没什么问题。但当你拥有敏感服务、受监管数据，或者单个被攻陷的 Pod 会造成重大爆炸半径时，这就成了真正的风险。

## NetworkPolicy 的作用

NetworkPolicy 通过标签选择器选择 Pod，并定义允许哪些入站（ingress）和出站（egress）连接。任何未被显式允许的连接都会被拒绝——但前提是存在默认拒绝策略。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database          # this policy applies to database pods
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api       # only allow traffic from api pods
      ports:
        - protocol: TCP
          port: 5432
```

这条策略表示：带有 `app: database` 标签的 Pod 只能接收来自带有 `app: api` 标签的 Pod 在 5432 端口上的流量。其他所有流量都会被丢弃。

## 默认拒绝模式

NetworkPolicy 是叠加式的——它们只限制至少被一条策略选中的 Pod。没有任何策略选中的 Pod 是不受限制的。

正确的做法：先为每个命名空间应用一条全部拒绝策略，然后再添加显式的允许规则。

```yaml
# Deny all ingress and egress for all pods in this namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}         # empty selector = select all pods
  policyTypes:
    - Ingress
    - Egress
```

现在任何通信都无法进行。为所需的内容添加显式策略：

```yaml
# Allow DNS (required for almost everything)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
```

逐步构建你的策略：先添加默认拒绝，然后逐个服务地启用通信，边测试边推进。

## 命名空间隔离

将通信限制为仅命名空间内部流量，外加特定的例外：

```yaml
# Allow ingress only from pods in the same namespace
ingress:
  - from:
      - podSelector: {}    # any pod in the same namespace

# Allow ingress from a specific other namespace
ingress:
  - from:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: monitoring
        podSelector:
          matchLabels:
            app: prometheus
```

在同一个 `from` 条目中组合 `namespaceSelector` 和 `podSelector` 表示"匹配该选择器的命名空间中匹配此选择器的 Pod"——这是 AND 关系。将它们放在不同的 `from` 条目中则表示 OR 关系。

## CNI 要求：并非所有 CNI 都会执行 NetworkPolicy

NetworkPolicy 是一个 API 对象。其执行取决于你的 CNI 插件：

**执行 NetworkPolicy：** Calico、Cilium、Weave Net、Antrea

**不执行 NetworkPolicy：** Flannel（默认情况下）

如果你应用了 NetworkPolicy 而你的 CNI 不执行它，该策略会被静默忽略。流量会自由流动。请检查你的集群使用哪种 CNI。

对于托管集群：GKE 使用 Calico 或 Dataplane V2（基于 Cilium）。EKS 使用 VPC CNI（默认不执行 NetworkPolicy）——你需要单独启用网络策略控制器。AKS 支持 Calico 和 Cilium。

## 测试你的策略

应用策略后，验证它们是否生效：

```bash
# From an api pod, connect to the database - should work
kubectl exec -it api-pod -n production -- nc -zv database-svc 5432

# From a web pod, connect to the database - should be blocked
kubectl exec -it web-pod -n production -- nc -zv database-svc 5432
# Connection should timeout or be refused
```

像 `netshoot`（一个包含网络工具的 Pod）这样的工具对于测试集群内的可达性很有用。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 网络策略](https://kubernetes.io/docs/concepts/services-networking/network-policies/) -- 类型：文档，时长：25 分钟
- [网络策略编辑器（可视化工具）](https://editor.networkpolicy.io/) -- 类型：工具，时长：15 分钟

<!-- ZH_UI -->
1. 理解 Kubernetes 默认没有网络隔离——任何 pod 都可以通过 IP 访问集群中的任何其他 pod
2. 了解 NetworkPolicy 的作用：它按标签选择 pod，并指定允许哪些入站和出站连接
3. 理解默认拒绝模式：先应用一条全部拒绝的策略，然后只为需要的连接添加明确的允许规则
4. 了解 NetworkPolicy 需要能强制执行它的 CNI 插件（Calico、Cilium、Weave）——并非所有 CNI 都支持
5. 应用命名空间隔离：只允许 pod 与自身命名空间内的 pod 以及特定的外部依赖通信
