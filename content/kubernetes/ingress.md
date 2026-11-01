---
id: ingress
title: Ingress
zone: kubernetes
edges:
  to:
    - id: persistent-volumes
      question: >-
        Networking is sorted — my app is reachable from the outside world. What
        about storage? My app needs to write files that survive Pod restarts.
      detail: >-
        My app is reachable from the internet now. But my app also writes files
        — user uploads, generated reports. When a pod restarts, those files are
        gone. A pod's filesystem is ephemeral, which means I can't just write to
        disk the way I would on a regular server. How does Kubernetes handle
        data that needs to survive?
    - id: debugging-ingress
      question: >-
        My Ingress is applied but I'm getting 404s — or sometimes 502s — and
        nothing is reaching my app.
      detail: >-
        The Service works fine from inside the cluster, but hitting the domain
        from the outside returns 404. Sometimes 502. I applied the Ingress
        resource and it shows up in kubectl, but I have no idea what's actually
        wrong or where to look.
    - id: ingress-controllers
      question: >-
        I applied an Ingress but nothing happened until I installed something
        called an 'ingress controller' — what is that?
      detail: >-
        I wrote an Ingress YAML, applied it, and... nothing. Traffic didn't
        route. Then someone told me I need an 'ingress controller' installed
        first. Turns out the Ingress resource is just a config file — it
        doesn't actually handle traffic. What does, and how do I pick one?
difficulty: 2
tags:
  - kubernetes
  - ingress
  - ingress-controller
  - nginx
  - traefik
  - http-routing
  - tls
  - k8s
category: practice
milestones:
  - Install an Ingress controller (nginx-ingress or Traefik)
  - >-
    Write an Ingress resource that routes two hostnames to two different
    Services
  - Configure TLS termination using a certificate (cert-manager + Let's Encrypt)
  - >-
    Explain the difference between the Ingress resource and the Ingress
    controller
title_zh: "Ingress"

---


Ingress is a Kubernetes resource that describes HTTP routing rules — which hostname or path goes to which Service. An Ingress controller reads those rules and actually routes the traffic. One controller can front many Services, replacing the need for a separate cloud load balancer per Service.

<!-- DEEP_DIVE -->

## The Ingress resource vs the Ingress controller

This is the most confusing thing about Ingress: there are two separate pieces that must work together.

**Ingress resource** — a Kubernetes API object you create. It's just data: "route `api.example.com` to the `api` Service on port 80, route `app.example.com` to the `frontend` Service on port 80."

**Ingress controller** — a separate piece of software running in your cluster that watches Ingress resources and actually configures itself to route traffic. It is not installed by default — you have to install one.

Popular choices:
- **ingress-nginx** — the most widely used, based on nginx
- **Traefik** — popular in smaller deployments, has built-in Let's Encrypt support
- **AWS Load Balancer Controller** — native integration with AWS ALB
- **GKE Ingress** — GKE's default, integrates with Google Cloud Load Balancing

## Writing an Ingress resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
        - app.example.com
      secretName: my-app-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

## TLS termination with cert-manager

Manually managing TLS certificates at scale is painful. **cert-manager** is a Kubernetes controller that automates certificate issuance and renewal — typically from Let's Encrypt.

The setup:
1. Install cert-manager in your cluster
2. Create a `ClusterIssuer` resource configured with your Let's Encrypt account and ACME solver settings
3. Add the `cert-manager.io/cluster-issuer` annotation to your Ingress resources

cert-manager watches for Ingress resources with that annotation, requests a certificate from Let's Encrypt using an HTTP or DNS challenge, stores it as a Kubernetes Secret, and renews it automatically before expiry. Your Ingress controller reads the Secret and terminates TLS at the edge.

## Host-based vs path-based routing

Ingress supports both patterns:

- **Host-based**: `api.example.com` → api Service, `app.example.com` → frontend Service
- **Path-based**: `example.com/api` → api Service, `example.com/` → frontend Service

Host-based routing is cleaner and avoids problems with apps that have different base paths baked in. Path-based works, but you need to be careful about how your backend apps handle the path prefix.

## IngressClass

Modern Kubernetes uses `IngressClass` to tell an Ingress resource which controller should handle it. If you have multiple controllers installed (nginx for most traffic, ALB controller for a specific workload), `ingressClassName` in the spec specifies which controller picks up each Ingress resource. Without it, the behavior depends on which controller is set as the default.

<!-- RESOURCES -->

- [Kubernetes Docs - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) -- type: docs, time: 25m
- [ingress-nginx controller](https://kubernetes.github.io/ingress-nginx/) -- type: tool, time: 20m
- [cert-manager Documentation](https://cert-manager.io/docs/) -- type: docs, time: 30m
- [Traefik Kubernetes Ingress](https://doc.traefik.io/traefik/providers/kubernetes-ingress/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Ingress 是 Kubernetes 中的一种资源，用于描述 HTTP 路由规则——哪个主机名或路径应转发到哪个 Service。Ingress 控制器会读取这些规则并实际执行流量路由。一个控制器可以代理多个 Service，从而无需为每个 Service 单独配置一个云负载均衡器。

<!-- ZH_DEEP_DIVE -->
## Ingress 资源与 Ingress 控制器

这是 Ingress 最令人困惑的地方：有两个独立的部分必须协同工作。

**Ingress 资源** —— 你创建的 Kubernetes API 对象。它只是数据：“将 `api.example.com` 路由到 `api` Service 的 80 端口，将 `app.example.com` 路由到 `frontend` Service 的 80 端口。”

**Ingress 控制器** —— 运行在集群中的独立软件，它监视 Ingress 资源，并实际配置自身来路由流量。它默认不会被安装——你需要自行安装一个。

常见选择：
- **ingress-nginx** —— 使用最广泛，基于 nginx
- **Traefik** —— 在较小规模部署中流行，内置 Let's Encrypt 支持
- **AWS Load Balancer Controller** —— 与 AWS ALB 原生集成
- **GKE Ingress** —— GKE 的默认方案，与 Google Cloud Load Balancing 集成

## 编写 Ingress 资源

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
        - app.example.com
      secretName: my-app-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

## 使用 cert-manager 进行 TLS 终止

在大规模场景下手动管理 TLS 证书非常痛苦。**cert-manager** 是一个 Kubernetes 控制器，可自动完成证书的签发与续期——通常来自 Let's Encrypt。

配置步骤：
1. 在集群中安装 cert-manager
2. 创建一个 `ClusterIssuer` 资源，配置你的 Let's Encrypt 账户和 ACME 求解器设置
3. 为你的 Ingress 资源添加 `cert-manager.io/cluster-issuer` 注解

cert-manager 会监视带有该注解的 Ingress 资源，通过 HTTP 或 DNS 挑战向 Let's Encrypt 申请证书，将其存储为 Kubernetes Secret，并在到期前自动续期。你的 Ingress 控制器读取该 Secret，并在边缘终止 TLS。

## 基于主机与基于路径的路由

Ingress 同时支持这两种模式：

- **基于主机**：`api.example.com` → api Service，`app.example.com` → frontend Service
- **基于路径**：`example.com/api` → api Service，`example.com/` → frontend Service

基于主机的路由更清晰，也能避免那些内置了不同基础路径的应用出现问题。基于路径的方式可行，但你需要小心后端应用如何处理路径前缀。

## IngressClass

现代 Kubernetes 使用 `IngressClass` 来告诉 Ingress 资源应由哪个控制器处理。如果你安装了多个控制器（大多数流量用 nginx，特定工作负载用 ALB 控制器），spec 中的 `ingressClassName` 会指定每个 Ingress 资源由哪个控制器接管。若不指定，行为取决于哪个控制器被设置为默认。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) -- 类型: 文档, 时间: 25m
- [ingress-nginx 控制器](https://kubernetes.github.io/ingress-nginx/) -- 类型: 工具, 时间: 20m
- [cert-manager 文档](https://cert-manager.io/docs/) -- 类型: 文档, 时间: 30m
- [Traefik Kubernetes Ingress](https://doc.traefik.io/traefik/providers/kubernetes-ingress/) -- 类型: 文档, 时间: 20m

<!-- ZH_UI -->
1. 安装 Ingress 控制器（nginx-ingress 或 Traefik）
2. 编写一个 Ingress 资源，将两个主机名路由到两个不同的 Service
3. 使用证书配置 TLS 终止（cert-manager + Let's Encrypt）
4. 解释 Ingress 资源与 Ingress 控制器之间的区别
5. 网络问题解决了——我的应用可以从外部访问了。那存储呢？我的应用需要写入在 Pod 重启后仍然存在的文件。
6. 我的应用现在可以从互联网访问了。但我的应用还会写文件——用户上传、生成的报告。当 Pod 重启时，这些文件就没了。Pod 的文件系统是临时的，这意味着我不能像在普通服务器上那样直接写磁盘。Kubernetes 如何处理需要持久化的数据？
7. 我的 Ingress 已应用，但收到 404——有时是 502——而且没有任何流量到达我的应用。
8. Service 在集群内部工作正常，但从外部访问域名返回 404。有时是 502。我应用了 Ingress 资源，它在 kubectl 中显示出来了，但我完全不知道哪里出了问题，也不知道该从哪里排查。
9. 我应用了一个 Ingress，但什么都没发生，直到我安装了某个叫“ingress controller”的东西——那是什么？
10. 我写了一个 Ingress YAML，应用了它，然后……什么都没发生。流量没有路由。后来有人告诉我需要先安装“ingress controller”。原来 Ingress 资源只是一个配置文件——它实际上并不处理流量。那什么处理流量，我该如何选择？
