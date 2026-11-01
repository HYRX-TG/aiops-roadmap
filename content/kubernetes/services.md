---
id: services
title: Kubernetes Services
zone: kubernetes
edges:
  to:
    - id: service-types
      question: >-
        I understand Services for internal traffic. How do I expose a Service
        outside the cluster?
      detail: >-
        My Service works inside the cluster, but I need actual users to reach it
        from the internet. Is that a different type of Service, or a completely
        different kind of resource? I keep seeing 'Ingress' in the docs and I'm
        not sure where Services end and that begins.
    - id: debugging-services
      question: >-
        I created a Service but I can't reach my app through it — requests just
        time out.
      detail: >-
        kubectl get svc shows the Service is there with a ClusterIP. But when I
        try to curl it from another pod, nothing comes back. I have no idea if
        the problem is the Service itself, the labels on my pods, or something
        else entirely.
    - id: k8s-networking-model
      question: >-
        I create a Service and traffic just reaches my pods. But how does it
        actually work underneath?
      detail: >-
        I've been using Services and they route traffic. But I have no idea
        what's happening at the network level. How does a pod on one node talk
        to a pod on a different node? There's no port mapping like Docker, no
        NAT — pods just reach each other by IP. That can't be magic.
difficulty: 1
tags:
  - kubernetes
  - services
  - clusterip
  - networking
  - dns
  - load-balancing
  - k8s
category: concept
milestones:
  - Create a ClusterIP Service that routes to your Pod
  - Reach the Service from another Pod using its DNS name
  - Understand how Kubernetes DNS resolves service.namespace.svc.cluster.local
  - Use kubectl describe service to understand endpoints and selectors
title_zh: "Kubernetes 服务"

---


Pods are ephemeral — their IP addresses change whenever they're replaced. A Kubernetes Service gives your workload a stable name and virtual IP that load-balances across a set of Pods, and registers it in cluster DNS so other workloads can find it without hardcoding any Pod IPs.

<!-- DEEP_DIVE -->

## The problem with Pod IPs

Every Pod gets an IP address. But Pod IPs are ephemeral. Kill a Pod and its IP is gone. The replacement Pod gets a different IP. If another service is hardcoded to the old IP, it's now pointing at nothing.

Services solve this with a level of indirection. You define a Service with a **selector** that matches your Pods by label, and Kubernetes continuously maintains the list of matching Pod IPs (the "endpoints"). The Service has a stable virtual IP (the ClusterIP) that never changes, and `kube-proxy` on each node handles routing traffic from that virtual IP to real Pod IPs.

## Writing a ClusterIP Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: default
spec:
  selector:
    app: my-app        # matches Pods with this label
  ports:
    - port: 80         # the port the Service listens on
      targetPort: 8080 # the container's actual port
  type: ClusterIP      # this is the default, can be omitted
```

Any Pod in the cluster can now reach your app at `my-app.default.svc.cluster.local:80` — or just `my-app:80` from within the same namespace.

## Kubernetes DNS

CoreDNS runs in `kube-system` and handles DNS resolution for Services. The full DNS name pattern is:

```
<service-name>.<namespace>.svc.cluster.local
```

Within the same namespace, the short name `<service-name>` resolves. From a different namespace, you need at least `<service-name>.<namespace>`. The full form always works from anywhere.

## How traffic actually gets there

`kube-proxy` runs on every node and watches for Service and Endpoint changes. In its default iptables mode, it installs iptables rules that intercept traffic destined for the ClusterIP and rewrite the destination to a randomly selected Pod IP. The ClusterIP itself doesn't listen on anything — it's purely a routing target maintained by iptables rules.

## Inspecting a Service

```bash
kubectl describe service my-app
```

Look at the `Endpoints:` field — it shows the actual Pod IPs currently receiving traffic. If it's empty, your selector doesn't match any Pods. This is the most common cause of "my Service isn't working" — a label typo in the selector or the Pod template.

```bash
kubectl get endpoints my-app
```

## Services and readiness probes

Services only route traffic to Pods that are passing their readiness probe. A Pod that fails its readiness check is automatically removed from the Service's endpoint list until it recovers. This is how the two systems work together: the Service handles discovery and load-balancing, readiness probes control which Pods are eligible to receive traffic.

<!-- RESOURCES -->

- [Kubernetes Docs - Services](https://kubernetes.io/docs/concepts/services-networking/service/) -- type: docs, time: 25m
- [Kubernetes DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) -- type: docs, time: 15m
- [A Guide to the Kubernetes Networking Model](https://sookocheff.com/post/kubernetes/understanding-kubernetes-networking-model/) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
Pod 是临时的——每当它们被替换时，其 IP 地址都会发生变化。Kubernetes Service 为你的工作负载提供一个稳定的名称和虚拟 IP，在一组 Pod 之间进行负载均衡，并将其注册到集群 DNS 中，这样其他工作负载无需硬编码任何 Pod IP 就能找到它。

<!-- ZH_DEEP_DIVE -->
## Pod IP 的问题

每个 Pod 都会获得一个 IP 地址。但 Pod IP 是临时的。杀掉一个 Pod，它的 IP 就没了。替代的 Pod 会获得一个不同的 IP。如果另一个服务硬编码了旧 IP，那它现在指向的就是空无一物。

Service 通过一层间接寻址解决了这个问题。你定义一个 Service，用 **selector** 按标签匹配你的 Pod，Kubernetes 会持续维护匹配的 Pod IP 列表（即 "endpoints"）。Service 有一个稳定不变的虚拟 IP（ClusterIP），每个节点上的 `kube-proxy` 负责将发往该虚拟 IP 的流量路由到真实的 Pod IP。

## 编写一个 ClusterIP Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: default
spec:
  selector:
    app: my-app        # matches Pods with this label
  ports:
    - port: 80         # the port the Service listens on
      targetPort: 8080 # the container's actual port
  type: ClusterIP      # this is the default, can be omitted
```

集群中的任何 Pod 现在都可以通过 `my-app.default.svc.cluster.local:80` 访问你的应用——或者在同一命名空间内直接用 `my-app:80`。

## Kubernetes DNS

CoreDNS 运行在 `kube-system` 中，负责 Service 的 DNS 解析。完整的 DNS 名称模式为：

```
<service-name>.<namespace>.svc.cluster.local
```

在同一命名空间内，短名称 `<service-name>` 即可解析。从不同命名空间访问，至少需要 `<service-name>.<namespace>`。完整形式从任何地方都能正常工作。

## 流量实际是如何到达的

`kube-proxy` 在每个节点上运行，监听 Service 和 Endpoint 的变化。在其默认的 iptables 模式下，它会安装 iptables 规则，拦截发往 ClusterIP 的流量，并将目标重写为随机选中的 Pod IP。ClusterIP 本身并不监听任何东西——它纯粹是由 iptables 规则维护的路由目标。

## 检查 Service

```bash
kubectl describe service my-app
```

查看 `Endpoints:` 字段——它显示当前实际接收流量的 Pod IP。如果为空，说明你的 selector 没有匹配到任何 Pod。这是 "我的 Service 不工作" 最常见的原因——selector 或 Pod 模板中的标签拼写错误。

```bash
kubectl get endpoints my-app
```

## Service 与就绪探针

Service 只会将流量路由到通过就绪探针的 Pod。未通过就绪检查的 Pod 会自动从 Service 的 endpoint 列表中移除，直到恢复。这就是两个系统协同工作的方式：Service 负责服务发现和负载均衡，就绪探针控制哪些 Pod 有资格接收流量。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Services](https://kubernetes.io/docs/concepts/services-networking/service/) -- 类型: 文档, 时间: 25m
- [Kubernetes 中 Service 和 Pod 的 DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) -- 类型: 文档, 时间: 15m
- [Kubernetes 网络模型指南](https://sookocheff.com/post/kubernetes/understanding-kubernetes-networking-model/) -- 类型: 文章, 时间: 20m

<!-- ZH_UI -->
1. 创建一个 ClusterIP Service，将流量路由到你的 Pod
2. 从另一个 Pod 使用其 DNS 名称访问该 Service
3. 理解 Kubernetes DNS 如何解析 service.namespace.svc.cluster.local
4. 使用 kubectl describe service 理解 endpoints 和 selectors
5. 我理解了用于内部流量的 Service。如何将 Service 暴露到集群外部？
6. 我的 Service 在集群内部正常工作，但我需要真实用户从互联网访问它。这是另一种类型的 Service，还是完全不同的资源类型？我总是在文档里看到“Ingress”，不确定 Service 的边界在哪里、Ingress 从哪里开始。
7. 我创建了一个 Service，但无法通过它访问我的应用——请求只是超时。
8. kubectl get svc 显示 Service 存在并带有 ClusterIP。但当我从另一个 pod 尝试 curl 它时，没有任何返回。我完全不知道问题出在 Service 本身、Pod 上的标签，还是其他完全不同的地方。
9. 我创建了一个 Service，流量就到达了我的 Pod。但它底层究竟是如何工作的？
10. 我一直在使用 Service，它们能路由流量。但我不知道网络层面发生了什么。一个节点上的 Pod 如何与另一个节点上的 Pod 通信？没有像 Docker 那样的端口映射，没有 NAT——Pod 之间直接通过 IP 互相访问。这不可能是魔法。
