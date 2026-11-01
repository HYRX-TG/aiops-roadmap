---
id: ingress-controllers
title: "Ingress Controllers: What Actually Handles Your Traffic"
zone: kubernetes
edges:
  to:
    - id: load-balancer-integration
      question: >-
        I installed my ingress controller and it created a LoadBalancer Service
        — where did that external IP come from?
      detail: >-
        I set up nginx-ingress and suddenly there's an external IP I never
        created. On my cloud cluster it appeared in seconds. On my local cluster
        it just says 'pending' forever. Something is provisioning real load
        balancers from cloud providers, and I have no idea what that mechanism
        is or how to make it work outside the cloud.
difficulty: 2
tags:
  - kubernetes
  - ingress
  - nginx
  - traefik
  - envoy
  - gateway-api
  - k8s
category: concept
milestones:
  - >-
    Understand that an Ingress resource is just a config object — something
    needs to read it and act on it
  - >-
    Know how controllers work: watch the API server for Ingress resources,
    generate reverse proxy config, reload
  - >-
    Know the main options: nginx-ingress (most common, annotation-driven),
    Traefik (auto-discovery, dashboard), Envoy-based (Contour, Emissary —
    advanced L7 features)
  - >-
    Understand the Gateway API: Kubernetes' successor to Ingress — more
    expressive, role-oriented, not limited to HTTP
  - >-
    Know what IngressClass is and how it lets you run multiple controllers in
    the same cluster
title_zh: "Ingress 控制器：真正处理你流量的是什么"

---


An Ingress resource in Kubernetes is just a YAML config — it describes how HTTP traffic should be routed, but it doesn't actually do anything by itself. An ingress controller is the component that reads those Ingress resources and runs the actual reverse proxy. Without a controller installed, your Ingress YAML sits there doing nothing. There are many controllers to choose from, and Kubernetes is gradually replacing the Ingress API with the more powerful Gateway API.

<!-- DEEP_DIVE -->

## How ingress controllers work

An ingress controller follows the same pattern as any Kubernetes controller:

1. **Watch** — it watches the API server for Ingress resources (and related objects like Services, Secrets for TLS certs)
2. **React** — when it detects a new or changed Ingress, it generates the appropriate reverse proxy configuration
3. **Apply** — it configures and reloads the underlying proxy (nginx, envoy, traefik, etc.)

The controller itself runs as pods inside the cluster, usually in its own namespace (`ingress-nginx`, `traefik`, etc.). It's exposed externally via a Service of type LoadBalancer (on cloud) or NodePort (on bare metal).

```
Internet → Cloud LB → Ingress Controller Pod → Service → App Pod
```

## nginx-ingress

The most widely deployed ingress controller. It runs nginx as a reverse proxy and generates nginx configuration from your Ingress resources.

```bash
# Install with Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx
```

A basic Ingress resource that nginx-ingress handles:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

**Good for:** Most use cases. Familiar if you know nginx. Rich annotation-based configuration. Largest community and most Stack Overflow answers.

**Limitations:** Configuration through annotations can get messy. Config changes trigger nginx reloads — nginx handles these gracefully (existing connections drain, new workers pick up new connections), but high-churn environments may see brief latency spikes during reloads.

## Traefik

Traefik auto-discovers services and can configure routing without annotations. It has a built-in dashboard for monitoring.

**Good for:** Smaller setups, teams that want less YAML. The dashboard is useful for seeing what's routed where. Also commonly used in non-Kubernetes environments (Docker, bare metal).

**Limitations:** Less commonly seen in large production Kubernetes deployments compared to nginx-ingress or Envoy-based options.

## Envoy-based controllers

Several controllers use Envoy as the underlying proxy: **Contour** (by VMware/Projectcontour), **Emissary-Ingress** (by Ambassador), and **Gateway API implementations**.

Envoy is a more modern, API-driven proxy compared to nginx. It supports hot reloading without dropping connections, has native gRPC support, and is the same proxy used by service meshes like Istio.

**Good for:** Teams that need advanced L7 features, gRPC routing, or are already using Envoy elsewhere. Large-scale environments where connection-draining during config changes matters.

## IngressClass

A cluster can run multiple ingress controllers simultaneously. IngressClass tells Kubernetes which controller should handle which Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: k8s.io/ingress-nginx
```

Then on your Ingress:

```yaml
spec:
  ingressClassName: nginx
```

This is how you can run nginx-ingress for public traffic and a separate controller for internal traffic in the same cluster.

## The Gateway API

The Ingress API has known limitations: it's HTTP-only, configuration through annotations is vendor-specific and messy, and there's no separation between "cluster admin" and "application developer" concerns.

The Gateway API is Kubernetes' replacement. It splits responsibilities:

- **GatewayClass** — what kind of infrastructure (managed by infra team)
- **Gateway** — a specific listener configuration (managed by cluster admin)
- **HTTPRoute** — how traffic routes to Services (managed by app developers)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-app
spec:
  parentRefs:
    - name: my-gateway
  hostnames:
    - "myapp.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: my-app
          port: 80
```

The Gateway API also supports TCP, UDP, gRPC, and TLS routing — not just HTTP. Most major ingress controllers now support it alongside the classic Ingress API.

It's not a hard migration — Ingress resources continue to work, and you can adopt Gateway API incrementally. But for new clusters, Gateway API is the recommended approach.

<!-- RESOURCES -->

- [Kubernetes Docs - Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) -- type: docs, time: 15m
- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/) -- type: docs, time: 20m
- [nginx-ingress Documentation](https://kubernetes.github.io/ingress-nginx/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Kubernetes 中的 Ingress 资源只是一个 YAML 配置——它描述了 HTTP 流量应如何路由，但本身并不实际执行任何操作。Ingress 控制器是读取这些 Ingress 资源并运行实际反向代理的组件。如果没有安装控制器，你的 Ingress YAML 就会闲置在那里，毫无作用。有许多控制器可供选择，而 Kubernetes 正在逐步用更强大的 Gateway API 取代 Ingress API。

<!-- ZH_DEEP_DIVE -->
## Ingress 控制器的工作原理

Ingress 控制器遵循与任何 Kubernetes 控制器相同的模式：

1. **监听（Watch）** — 它监听 API server 上的 Ingress 资源（以及相关的对象，如 Service、用于 TLS 证书的 Secret）
2. **响应（React）** — 当检测到新增或变更的 Ingress 时，它生成相应的反向代理配置
3. **应用（Apply）** — 它配置并重载底层代理（nginx、envoy、traefik 等）

控制器本身以 Pod 形式运行在集群内，通常位于其专属命名空间中（`ingress-nginx`、`traefik` 等）。它通过 LoadBalancer 类型的 Service（云上）或 NodePort（裸金属）对外暴露。

```
Internet → Cloud LB → Ingress Controller Pod → Service → App Pod
```

## nginx-ingress

部署最广泛的 Ingress 控制器。它以 nginx 作为反向代理运行，并根据你的 Ingress 资源生成 nginx 配置。

```bash
# Install with Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx
```

一个由 nginx-ingress 处理的基础 Ingress 资源：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

**适用场景：** 大多数用例。如果你熟悉 nginx，会很容易上手。基于注解的配置功能丰富。拥有最大的社区和最多的 Stack Overflow 答案。

**局限：** 通过注解进行配置可能会变得杂乱。配置变更会触发 nginx 重载——nginx 能优雅地处理这些重载（现有连接被排空，新的 worker 接收新连接），但在变更频繁的环境中，重载期间可能会出现短暂的延迟尖峰。

## Traefik

Traefik 可自动发现服务，无需注解即可配置路由。它内置了用于监控的 dashboard。

**适用场景：** 较小的部署、希望减少 YAML 的团队。dashboard 对于查看流量路由到哪里很有用。也常用于非 Kubernetes 环境（Docker、裸金属）。

**局限：** 与 nginx-ingress 或基于 Envoy 的方案相比，在大型生产 Kubernetes 部署中较少见到。

## 基于 Envoy 的控制器

有多个控制器使用 Envoy 作为底层代理：**Contour**（由 VMware/Projectcontour 出品）、**Emissary-Ingress**（由 Ambassador 出品）以及 **Gateway API 实现**。

与 nginx 相比，Envoy 是一个更现代、由 API 驱动的代理。它支持不丢弃连接的热重载，原生支持 gRPC，并且是 Istio 等服务网格所使用的同一个代理。

**适用场景：** 需要高级 L7 功能、gRPC 路由，或已在其他地方使用 Envoy 的团队。在配置变更期间连接排空至关重要的规模化环境中。

## IngressClass

一个集群可以同时运行多个 Ingress 控制器。IngressClass 告诉 Kubernetes 哪个控制器应处理哪个 Ingress 资源：

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: k8s.io/ingress-nginx
```

然后在你的 Ingress 上：

```yaml
spec:
  ingressClassName: nginx
```

这就是在同一集群中为公网流量运行 nginx-ingress、并为内部流量运行独立控制器的方式。

## Gateway API

Ingress API 存在已知的局限：它仅支持 HTTP，通过注解进行配置是厂商特定的且杂乱，并且没有将“集群管理员”和“应用开发者”的职责分离。

Gateway API 是 Kubernetes 的替代方案。它拆分职责：

- **GatewayClass** — 基础设施类型（由基础设施团队管理）
- **Gateway** — 特定的监听器配置（由集群管理员管理）
- **HTTPRoute** — 流量如何路由到 Service（由应用开发者管理）

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-app
spec:
  parentRefs:
    - name: my-gateway
  hostnames:
    - "myapp.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: my-app
          port: 80
```

Gateway API 还支持 TCP、UDP、gRPC 和 TLS 路由——不仅仅是 HTTP。大多数主流 Ingress 控制器现在都在经典 Ingress API 之外同时支持它。

这不是一次强制迁移——Ingress 资源继续可用，你可以逐步采用 Gateway API。但对于新集群，Gateway API 是推荐的方式。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Ingress 控制器](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) -- 类型：文档，时长：15 分钟
- [Gateway API 文档](https://gateway-api.sigs.k8s.io/) -- 类型：文档，时长：20 分钟
- [nginx-ingress 文档](https://kubernetes.github.io/ingress-nginx/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 理解 Ingress 资源只是一个配置对象——需要有东西读取它并据此执行操作
2. 了解控制器如何工作：监听 API server 上的 Ingress 资源，生成反向代理配置，重新加载
3. 了解主要选项：nginx-ingress（最常见，注解驱动）、Traefik（自动发现，仪表盘）、基于 Envoy 的（Contour、Emissary——高级 L7 特性）
4. 理解 Gateway API：Kubernetes 中 Ingress 的后继者——表达力更强、面向角色、不限于 HTTP
5. 了解什么是 IngressClass，以及它如何让你在同一集群中运行多个控制器
6. 我安装了 ingress 控制器，它创建了一个 LoadBalancer Service——那个外部 IP 是从哪来的？
7. 我搭好了 nginx-ingress，突然冒出一个我从未创建过的外部 IP。在我的云集群上它几秒就出现了。在我的本地集群上它一直显示“pending”。有东西在从云厂商那里真正地创建负载均衡器，我不知道那是什么机制，也不知道如何在云之外让它工作。
