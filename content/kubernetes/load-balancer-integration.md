---
id: load-balancer-integration
title: Load Balancers and Kubernetes
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - load-balancer
  - metallb
  - cloud
  - external-dns
  - k8s
category: concept
milestones:
  - >-
    Understand what type: LoadBalancer actually does — it talks to the cloud
    provider to provision a real load balancer
  - >-
    Know what the cloud controller manager is: the component that bridges
    Kubernetes and cloud provider APIs
  - >-
    Understand the cost reality: every LoadBalancer Service creates a separate
    cloud LB, which adds up fast
  - >-
    Know why Ingress exists as a pattern: one LoadBalancer fronting one Ingress
    controller that routes to many Services
  - >-
    Understand MetalLB: LoadBalancer support for bare metal and on-prem clusters
    using ARP or BGP mode
  - >-
    Know what ExternalDNS does: automatically creates DNS records for
    LoadBalancer Services
title_zh: "负载均衡器与 Kubernetes"

---


When you set a Service to `type: LoadBalancer` on a cloud cluster, an external IP appears within seconds. On a local cluster, the same thing just shows `<pending>` forever. The difference is the cloud controller manager — a component that bridges Kubernetes and cloud provider APIs. Understanding this mechanism explains how external traffic enters your cluster, why it costs money, and what to do when there's no cloud.

<!-- DEEP_DIVE -->

## What type: LoadBalancer actually does

A LoadBalancer Service is a superset of NodePort. When you create one:

1. Kubernetes assigns a ClusterIP (like any Service)
2. Kubernetes opens a NodePort on every node (like a NodePort Service)
3. Kubernetes tells the cloud controller manager: "I need an external load balancer for this Service"
4. The cloud controller manager calls the cloud provider's API (AWS ELB, GCP Network LB, Azure LB) to provision a real load balancer
5. The cloud LB is configured to forward traffic to the NodePort on all nodes
6. The external IP is written back to the Service's `status.loadBalancer.ingress`

```
Internet → Cloud Load Balancer → NodePort (on any node) → kube-proxy → Pod
```

The whole chain happens automatically. You create a Service, and within a minute you have a public IP backed by a cloud load balancer.

## The cloud controller manager

The cloud controller manager is the component that makes this work. It runs as pods in `kube-system` and is specific to your cloud provider:

- On EKS, it's the AWS cloud controller manager — it creates ELBs/NLBs
- On GKE, it's the GCE cloud controller — it creates Google Cloud Load Balancers
- On AKS, it's the Azure cloud controller — it creates Azure Load Balancers

When it sees a new Service of type LoadBalancer, it:
1. Creates a load balancer through the cloud API
2. Configures health checks against the NodePort
3. Adds all cluster nodes as targets
4. Reports the external IP back to Kubernetes

You can influence the load balancer type with annotations. On AWS, modern clusters use the AWS Load Balancer Controller (a separate install) instead of the in-tree cloud provider:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    # AWS Load Balancer Controller: create an NLB
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
    # With target-type "ip", traffic goes directly to pod IPs
    # bypassing NodePort and kube-proxy entirely
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: my-app
```

With the `ip` target type, the traffic path is shorter: `Internet → NLB → Pod IP` directly, skipping NodePort and kube-proxy. The NLB registers pod IPs as targets instead of routing through node ports. This gives better performance and more predictable load balancing.

The older in-tree approach (`service.beta.kubernetes.io/aws-load-balancer-type: "nlb"`) still works but is deprecated. You'll see it in older tutorials.

## The cost problem

Every LoadBalancer Service creates a separate cloud load balancer. On AWS, a Network Load Balancer costs ~$16/month plus data processing charges. If you have 10 services, that's $160/month just for load balancers — before any traffic.

This is why Ingress exists as a pattern:
- One LoadBalancer Service → one ingress controller
- The ingress controller routes HTTP traffic to many backend Services based on hostname/path
- You pay for one load balancer instead of ten

For non-HTTP services (databases, gRPC, TCP), you might still need individual LoadBalancer Services. But for HTTP, Ingress is the cost-effective approach.

## When there's no cloud: MetalLB

On bare metal, on-prem clusters, or local development clusters (kind, minikube), there's no cloud controller manager. Services of type LoadBalancer stay in `Pending` forever because nothing provisions the external IP.

MetalLB fills this gap. It's an open-source load balancer implementation for non-cloud Kubernetes clusters. It works in two modes:

### ARP mode (Layer 2)

One node claims the external IP and responds to ARP requests for it. Traffic goes to that node, then kube-proxy routes it to the right pod. Simple, works on any network, but all traffic for a given IP goes through a single node (no true load balancing at the network level).

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.1.240-192.168.1.250    # IPs MetalLB can assign
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: l2
  namespace: metallb-system
```

### BGP mode

MetalLB peers with your network's routers via BGP and announces the external IPs. The routers distribute traffic across multiple nodes. True load balancing at the network level, but requires BGP-capable routers.

## ExternalDNS

Once you have external IPs (from cloud LBs or MetalLB), ExternalDNS can automatically create DNS records for them. It watches for Services and Ingresses with specific annotations, then creates A records in your DNS provider (Route 53, Cloudflare, Google Cloud DNS, etc.):

```yaml
metadata:
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
```

When the Service gets an external IP, ExternalDNS creates `myapp.example.com → <external-ip>` in your DNS. When the Service is deleted, the DNS record is cleaned up. No manual DNS management.

<!-- RESOURCES -->

- [Kubernetes Docs - Service Type LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer) -- type: docs, time: 10m
- [MetalLB Documentation](https://metallb.io/) -- type: docs, time: 20m
- [ExternalDNS Documentation](https://github.com/kubernetes-sigs/external-dns) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当你在云集群上将 Service 设置为 `type: LoadBalancer` 时，几秒内就会出现一个外部 IP。而在本地集群上，同样操作只会永远显示 `<pending>`。差异在于 cloud controller manager——一个连接 Kubernetes 与云厂商 API 的组件。理解这一机制，就能解释外部流量如何进入你的集群、为什么会产生费用，以及在没有云的情况下该怎么办。

<!-- ZH_DEEP_DIVE -->
## LoadBalancer 类型实际做了什么

LoadBalancer Service 是 NodePort 的超集。当你创建一个 LoadBalancer Service 时：

1. Kubernetes 分配一个 ClusterIP（和任何 Service 一样）
2. Kubernetes 在每个节点上打开一个 NodePort（和 NodePort Service 一样）
3. Kubernetes 告诉 cloud controller manager：“我需要为这个 Service 提供一个外部负载均衡器”
4. cloud controller manager 调用云厂商的 API（AWS ELB、GCP Network LB、Azure LB）来真正创建一个负载均衡器
5. 云负载均衡器被配置为将流量转发到所有节点上的 NodePort
6. 外部 IP 被写回 Service 的 `status.loadBalancer.ingress`

```
Internet → Cloud Load Balancer → NodePort (on any node) → kube-proxy → Pod
```

整条链路自动完成。你创建一个 Service，一分钟之内就得到一个由云负载均衡器支撑的公网 IP。

## cloud controller manager

cloud controller manager 是让这一切运转起来的组件。它以 Pod 的形式运行在 `kube-system` 中，并且特定于你的云厂商：

- 在 EKS 上，它是 AWS cloud controller manager——负责创建 ELB/NLB
- 在 GKE 上，它是 GCE cloud controller——负责创建 Google Cloud Load Balancer
- 在 AKS 上，它是 Azure cloud controller——负责创建 Azure Load Balancer

当它看到一个类型为 LoadBalancer 的新 Service 时，它会：
1. 通过云 API 创建一个负载均衡器
2. 针对 NodePort 配置健康检查
3. 将所有集群节点添加为目标
4. 将外部 IP 上报回 Kubernetes

你可以通过注解来影响负载均衡器的类型。在 AWS 上，现代集群使用 AWS Load Balancer Controller（需要单独安装）而不是内置的 cloud provider：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    # AWS Load Balancer Controller: create an NLB
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
    # With target-type "ip", traffic goes directly to pod IPs
    # bypassing NodePort and kube-proxy entirely
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: my-app
```

使用 `ip` 目标类型时，流量路径更短：`Internet → NLB → Pod IP` 直达，跳过 NodePort 和 kube-proxy。NLB 将 Pod IP 注册为目标，而不是通过节点端口进行路由。这带来更好的性能和更可预测的负载均衡。

较旧的内置方式（`service.beta.kubernetes.io/aws-load-balancer-type: "nlb"`）仍然可用，但已被弃用。你会在较旧的教程中看到它。

## 成本问题

每个 LoadBalancer Service 都会创建一个独立的云负载均衡器。在 AWS 上，一个 Network Load Balancer 每月约 $16，外加数据处理费用。如果你有 10 个服务，仅负载均衡器每月就要 $160——这还不算任何流量。

这就是 Ingress 作为一种模式存在的原因：
- 一个 LoadBalancer Service → 一个 ingress controller
- ingress controller 根据主机名/路径将 HTTP 流量路由到多个后端 Service
- 你只需为一个负载均衡器付费，而不是十个

对于非 HTTP 服务（数据库、gRPC、TCP），你可能仍然需要单独的 LoadBalancer Service。但对于 HTTP，Ingress 是更具成本效益的方案。

## 没有云环境时：MetalLB

在裸金属、本地部署集群或本地开发集群（kind、minikube）上，没有 cloud controller manager。类型为 LoadBalancer 的 Service 会永远停留在 `Pending` 状态，因为没有任何组件来提供外部 IP。

MetalLB 填补了这一空白。它是一个面向非云 Kubernetes 集群的开源负载均衡器实现。它有两种工作模式：

### ARP 模式（Layer 2）

一个节点认领该外部 IP 并响应针对它的 ARP 请求。流量到达该节点，然后由 kube-proxy 路由到正确的 Pod。简单，适用于任何网络，但给定 IP 的所有流量都经过单个节点（在网络层面没有真正的负载均衡）。

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.1.240-192.168.1.250    # IPs MetalLB can assign
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: l2
  namespace: metallb-system
```

### BGP 模式

MetalLB 通过 BGP 与你的网络路由器建立对等连接，并宣告外部 IP。路由器将流量分发到多个节点。在网络层面实现真正的负载均衡，但需要支持 BGP 的路由器。

## ExternalDNS

一旦你有了外部 IP（来自云负载均衡器或 MetalLB），ExternalDNS 就可以自动为它们创建 DNS 记录。它会监视带有特定注解的 Service 和 Ingress，然后在你的 DNS 提供商（Route 53、Cloudflare、Google Cloud DNS 等）中创建 A 记录：

```yaml
metadata:
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
```

当 Service 获得外部 IP 时，ExternalDNS 会在你的 DNS 中创建 `myapp.example.com → <external-ip>`。当 Service 被删除时，DNS 记录会被清理。无需手动管理 DNS。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Service 类型 LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer) -- type: docs, time: 10m
- [MetalLB 文档](https://metallb.io/) -- type: docs, time: 20m
- [ExternalDNS 文档](https://github.com/kubernetes-sigs/external-dns) -- type: docs, time: 15m

<!-- ZH_UI -->
1. 理解 type: LoadBalancer 实际做了什么——它与云提供商通信以配置真实的负载均衡器
2. 了解什么是 cloud controller manager：连接 Kubernetes 与云提供商 API 的组件
3. 理解成本现实：每个 LoadBalancer Service 都会创建一个独立的云 LB，成本会快速累积
4. 了解 Ingress 作为一种模式存在的原因：一个 LoadBalancer 前置一个 Ingress controller，路由到多个 Service
5. 理解 MetalLB：为裸金属和本地集群提供 LoadBalancer 支持，使用 ARP 或 BGP 模式
6. 了解 ExternalDNS 的作用：为 LoadBalancer Service 自动创建 DNS 记录
