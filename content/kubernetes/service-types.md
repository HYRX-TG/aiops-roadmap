---
id: service-types
title: 'Service Types: NodePort and LoadBalancer'
zone: kubernetes
edges:
  to:
    - id: ingress
      question: >-
        NodePort and LoadBalancer work but feel clunky for HTTP. Is there a
        better way?
      detail: >-
        Every HTTP service needs its own cloud load balancer? That's going to
        get expensive fast. I have a frontend, an API, a docs site — I don't
        want three separate load balancers. There must be a smarter way to route
        HTTP traffic to different services from a single entry point.
    - id: load-balancer-integration
      question: >-
        I set my Service to type LoadBalancer — on the cloud it got an IP
        instantly, but locally it just says 'pending.' What's going on?
      detail: >-
        On my cloud cluster, I changed the Service type to LoadBalancer and an
        external IP appeared within a minute. But on my local kind cluster, the
        same thing just hangs at 'pending' forever. Something is clearly talking
        to the cloud provider to make it work there — what is it, and what do I
        do when there's no cloud?
difficulty: 1
tags:
  - kubernetes
  - nodeport
  - loadbalancer
  - services
  - networking
  - external-access
  - k8s
category: concept
milestones:
  - Expose a Service with NodePort and reach it via the node's IP and port
  - Expose a Service with LoadBalancer on a cloud provider and get a public IP
  - Explain why you wouldn't use a LoadBalancer Service for every HTTP endpoint
  - >-
    Understand the relationship between NodePort, LoadBalancer, and ClusterIP
    (they build on each other)
title_zh: "服务类型：NodePort 与 LoadBalancer"

---


A ClusterIP Service is only reachable inside the cluster. NodePort and LoadBalancer are Service types that extend access to the outside world, each with different trade-offs. For HTTP services, both are usually superseded by Ingress — but understanding the types explains how external traffic flows into a cluster.

<!-- DEEP_DIVE -->

## How Service types build on each other

Kubernetes Service types aren't separate concepts — they're layers that build on each other:

- **ClusterIP** — virtual IP, internal only. The base type.
- **NodePort** — builds on ClusterIP. Opens a port on every node in the cluster. Traffic hits any node → routed to the ClusterIP → routed to a Pod.
- **LoadBalancer** — builds on NodePort. Provisions a cloud load balancer pointing at your nodes' NodePorts. Traffic hits the load balancer → hits a NodePort → hits a Pod.

## NodePort

NodePort allocates a port (default range: 30000–32767) on every node in the cluster and forwards traffic from `<any-node-ip>:<nodePort>` to the Service.

```yaml
apiVersion: v1
kind: Service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080  # omit to get a randomly assigned port in the range
```

You can now reach the service at `http://<node-ip>:30080`. The problems: you need to know a node's IP, nodes come and go, and the non-standard port is awkward to expose to users.

NodePort is useful for local development clusters (kind, minikube) where there's no cloud load balancer, and for on-premises setups managing their own external load balancing.

## LoadBalancer

LoadBalancer is the cloud-native answer: Kubernetes integrates with the cloud provider's API to provision a real load balancer automatically.

```yaml
apiVersion: v1
kind: Service
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

After applying this on EKS, GKE, or AKS, `kubectl get service` will eventually show an `EXTERNAL-IP` — the public IP or hostname of the provisioned load balancer. Real traffic flows in on port 80.

The problem: every LoadBalancer Service provisions a separate cloud load balancer. At scale — dozens or hundreds of services — that's expensive and unmanageable. This is why HTTP traffic typically goes through Ingress instead.

## When to use which

- **NodePort** — local clusters, on-premises setups, or when you're managing your own external load balancer (like HAProxy, nginx, or a hardware load balancer)
- **LoadBalancer** — TCP/UDP services in the cloud that can't go through HTTP routing: databases with external access, game servers, MQTT brokers, anything that isn't HTTP/HTTPS
- **Ingress** — everything HTTP/HTTPS in production. One load balancer, many services, routing by hostname and path.

On-premises clusters that need LoadBalancer behavior (without a cloud provider) can use **MetalLB**, which implements the LoadBalancer type by announcing Service IPs via ARP or BGP.

<!-- RESOURCES -->

- [Kubernetes Docs - Service Types](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) -- type: docs, time: 20m
- [NodePort vs LoadBalancer vs Ingress - When to use what](https://medium.com/google-cloud/kubernetes-nodeport-vs-loadbalancer-vs-ingress-when-should-i-use-what-922f010849e0) -- type: article, time: 10m
- [MetalLB - LoadBalancer for on-premises clusters](https://metallb.universe.tf/) -- type: tool, time: 20m

<!-- ZH_SUMMARY -->
ClusterIP Service 只能在集群内部访问。NodePort 和 LoadBalancer 是两种将访问扩展到集群外部的 Service 类型，各有不同的取舍。对于 HTTP 服务，这两种类型通常都会被 Ingress 取代——但理解这些类型有助于弄清外部流量是如何流入集群的。

<!-- ZH_DEEP_DIVE -->
## Service 类型如何层层构建

Kubernetes 的 Service 类型并非彼此独立的概念——它们是层层叠加构建的：

- **ClusterIP** —— 虚拟 IP，仅限集群内部。基础类型。
- **NodePort** —— 构建在 ClusterIP 之上。在集群的每个节点上开放一个端口。流量到达任意节点 → 路由到 ClusterIP → 路由到 Pod。
- **LoadBalancer** —— 构建在 NodePort 之上。通过云厂商 API 自动创建一个指向各节点 NodePort 的云负载均衡器。流量到达负载均衡器 → 到达 NodePort → 到达 Pod。

## NodePort

NodePort 会在集群的每个节点上分配一个端口（默认范围：30000–32767），并将来自 `<any-node-ip>:<nodePort>` 的流量转发到该 Service。

```yaml
apiVersion: v1
kind: Service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080  # omit to get a randomly assigned port in the range
```

现在你可以通过 `http://<node-ip>:30080` 访问该服务。问题在于：你需要知道某个节点的 IP，节点会不断增减，而且非标准端口不方便暴露给用户。

NodePort 适用于没有云负载均衡器的本地开发集群（kind、minikube），以及自行管理外部负载均衡的本地部署环境。

## LoadBalancer

LoadBalancer 是云原生的答案：Kubernetes 与云厂商的 API 集成，自动创建一个真实的负载均衡器。

```yaml
apiVersion: v1
kind: Service
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

在 EKS、GKE 或 AKS 上应用此配置后，`kubectl get service` 最终会显示一个 `EXTERNAL-IP`——即所创建负载均衡器的公网 IP 或主机名。真实流量从 80 端口流入。

问题在于：每个 LoadBalancer 类型的 Service 都会创建一个独立的云负载均衡器。在规模化场景下——几十或几百个服务——这既昂贵又难以管理。这就是 HTTP 流量通常改走 Ingress 的原因。

## 何时使用哪种类型

- **NodePort** —— 本地集群、本地部署环境，或当你自行管理外部负载均衡器（如 HAProxy、nginx 或硬件负载均衡器）时
- **LoadBalancer** —— 云上无法走 HTTP 路由的 TCP/UDP 服务：需要外部访问的数据库、游戏服务器、MQTT broker，以及任何非 HTTP/HTTPS 的服务
- **Ingress** —— 生产环境中所有 HTTP/HTTPS 流量。一个负载均衡器，多个服务，按主机名和路径路由。

需要 LoadBalancer 行为但没有云厂商的本地部署集群可以使用 **MetalLB**，它通过 ARP 或 BGP 宣告 Service IP 来实现 LoadBalancer 类型。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Service 类型](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) -- 类型：文档，时间：20m
- [NodePort vs LoadBalancer vs Ingress - 何时使用哪种](https://medium.com/google-cloud/kubernetes-nodeport-vs-loadbalancer-vs-ingress-when-should-i-use-what-922f010849e0) -- 类型：文章，时间：10m
- [MetalLB - 用于本地集群的 LoadBalancer](https://metallb.universe.tf/) -- 类型：工具，时间：20m

<!-- ZH_UI -->
1. 使用 NodePort 暴露 Service，并通过节点 IP 和端口访问它
2. 在云提供商上使用 LoadBalancer 暴露 Service 并获得公网 IP
3. 解释为什么你不会为每个 HTTP 端点都使用 LoadBalancer Service
4. 理解 NodePort、LoadBalancer 和 ClusterIP 之间的关系（它们层层构建）
5. NodePort 和 LoadBalancer 能用，但对 HTTP 来说显得笨重。有更好的方法吗？
6. 每个 HTTP 服务都需要自己的云负载均衡器？那很快就会变得昂贵。我有一个前端、一个 API、一个文档站点——我不想用三个独立的负载均衡器。一定有一种更聪明的方式，从单一入口点将 HTTP 流量路由到不同服务。
7. 我把 Service 设置为 LoadBalancer 类型——在云上它立刻获得了 IP，但在本地它只显示“pending”。这是怎么回事？
8. 在我的云集群上，我把 Service 类型改为 LoadBalancer，一分钟内就出现了外部 IP。但在我的本地 kind 集群上，同样的事情却永远卡在“pending”。显然有某个东西在与云提供商通信以使其在那里工作——它是什么，当没有云时我该怎么办？
