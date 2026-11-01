---
id: coredns
title: CoreDNS and Cluster DNS
zone: kubernetes
edges:
  to:
    - id: dns-debugging-k8s
      question: >-
        My DNS lookups are randomly slow — some take 5 seconds, some fail
        entirely. Where do I even start?
      detail: >-
        Pods resolve service names most of the time, but under load, DNS gets
        flaky. Sometimes lookups time out. I also noticed that resolving
        `api.stripe.com` from inside a pod takes way longer than it should. I
        don't know if it's CoreDNS, my resolv.conf, or something else.
difficulty: 2
tags:
  - kubernetes
  - coredns
  - dns
  - service-discovery
  - k8s
category: concept
milestones:
  - >-
    Know that CoreDNS runs as pods in kube-system and is the cluster's DNS
    server
  - >-
    Understand that every pod's /etc/resolv.conf is configured to point at the
    CoreDNS Service IP
  - >-
    Know the naming convention:
    <service>.<namespace>.svc.cluster.local
  - >-
    Understand headless Services: DNS returns pod IPs directly instead of a
    single ClusterIP
  - >-
    Know how CoreDNS watches the API server for Service and Endpoint changes to
    keep DNS records up to date
  - >-
    Understand ExternalName Services: a DNS CNAME that points to an external
    hostname
title_zh: "CoreDNS 与集群 DNS"

---


Every Kubernetes cluster runs a DNS server — CoreDNS. It's what lets you reach a Service by name instead of by IP. When a pod curls `my-service.default.svc.cluster.local`, CoreDNS resolves that name to the Service's ClusterIP. It runs as pods in `kube-system`, watches the Kubernetes API for Service changes, and automatically keeps DNS records in sync. Everything in your cluster depends on it working.

<!-- DEEP_DIVE -->

## How pods find CoreDNS

When kubelet creates a pod, it configures the pod's `/etc/resolv.conf` to point at the CoreDNS Service IP. You can see this from inside any pod:

```bash
kubectl exec my-pod -- cat /etc/resolv.conf
```

```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

The `nameserver` is the ClusterIP of the `kube-dns` Service in `kube-system` (the Service is still called `kube-dns` for historical reasons, even though CoreDNS replaced kube-dns years ago). Every DNS lookup from inside a pod goes to this IP.

## The naming convention

CoreDNS creates DNS records for every Service in the cluster. The full format is:

```
<service-name>.<namespace>.svc.cluster.local
```

From a pod in the same namespace, you can use just the service name:

```bash
# All of these resolve to the same ClusterIP
curl my-service                                    # same namespace
curl my-service.default                            # explicit namespace
curl my-service.default.svc                        # explicit subdomain
curl my-service.default.svc.cluster.local          # fully qualified
```

The short forms work because of the `search` domains in `resolv.conf`. When you look up `my-service`, the resolver appends each search domain in order until it gets a result: first `my-service.default.svc.cluster.local`, then `my-service.svc.cluster.local`, and so on.

## How CoreDNS stays in sync

CoreDNS runs a Kubernetes plugin that watches the API server for Service and Endpoint changes. When you create, delete, or modify a Service, CoreDNS picks up the change within seconds and updates its DNS records. There's no manual configuration — everything is automatic.

You can see CoreDNS running:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl get svc -n kube-system kube-dns
```

CoreDNS typically runs as a Deployment with 2 replicas for availability.

## Headless Services and DNS

A normal Service has a ClusterIP, and its DNS record resolves to that single IP. A headless Service (`clusterIP: None`) works differently — its DNS record returns the IP addresses of all the individual pods behind it.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-db
spec:
  clusterIP: None    # headless
  selector:
    app: my-db
  ports:
    - port: 5432
```

```bash
# Normal Service: resolves to one ClusterIP
dig my-app.default.svc.cluster.local
# → 10.96.0.15

# Headless Service: resolves to individual pod IPs
dig my-db.default.svc.cluster.local
# → 10.244.1.5
# → 10.244.2.8
# → 10.244.1.12
```

Headless Services are used by StatefulSets, where each pod needs to be individually addressable (like database replicas that need to find each other).

## ExternalName Services

An ExternalName Service is just a DNS alias — a CNAME record that points to an external hostname:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-database
spec:
  type: ExternalName
  externalName: mydb.example.com
```

When a pod looks up `my-database.default.svc.cluster.local`, CoreDNS returns a CNAME pointing to `mydb.example.com`. This is useful for pointing internal service names at external databases or APIs without hardcoding hostnames in your application config.

## Pod DNS records

CoreDNS can also create DNS records for individual pods, using the pod's IP with dots replaced by dashes:

```
10-244-1-5.default.pod.cluster.local
```

This is mostly used by StatefulSets, where each pod gets a stable DNS name through the headless Service:

```
my-db-0.my-db.default.svc.cluster.local
my-db-1.my-db.default.svc.cluster.local
```

## What happens if CoreDNS goes down

If both CoreDNS replicas crash, new DNS lookups fail cluster-wide. Pods that have already resolved a name and are holding a TCP connection will keep working. But any new connection attempt that needs DNS resolution will hang or fail.

This is why CoreDNS runs as a Deployment with multiple replicas, has resource requests to prevent eviction, and is treated as critical infrastructure. Monitoring CoreDNS health is essential.

<!-- RESOURCES -->

- [Kubernetes Docs - DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) -- type: docs, time: 15m
- [CoreDNS Manual](https://coredns.io/manual/toc/) -- type: docs, time: 20m
- [Customizing DNS Service](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
每个 Kubernetes 集群都运行着一个 DNS 服务器——CoreDNS。正是它让你能够通过名称而非 IP 来访问 Service。当某个 pod 执行 `curl my-service.default.svc.cluster.local` 时，CoreDNS 会将该名称解析为 Service 的 ClusterIP。它以 pod 的形式运行在 `kube-system` 中，监听 Kubernetes API 以获取 Service 变更，并自动保持 DNS 记录同步。集群中的一切都依赖于它的正常工作。

<!-- ZH_DEEP_DIVE -->
## Pod 如何找到 CoreDNS

当 kubelet 创建 Pod 时，它会将 Pod 的 `/etc/resolv.conf` 配置为指向 CoreDNS 的 Service IP。你可以在任意 Pod 内部看到这一点：

```bash
kubectl exec my-pod -- cat /etc/resolv.conf
```

```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`nameserver` 是 `kube-system` 中 `kube-dns` Service 的 ClusterIP（出于历史原因，该 Service 仍叫 `kube-dns`，尽管 CoreDNS 多年前就已取代了 kube-dns）。Pod 内部的每一次 DNS 查询都会发往这个 IP。

## 命名约定

CoreDNS 会为集群中的每个 Service 创建 DNS 记录。完整格式为：

```
<service-name>.<namespace>.svc.cluster.local
```

从同一命名空间内的 Pod 中，你可以只使用服务名：

```bash
# All of these resolve to the same ClusterIP
curl my-service                                    # same namespace
curl my-service.default                            # explicit namespace
curl my-service.default.svc                        # explicit subdomain
curl my-service.default.svc.cluster.local          # fully qualified
```

短格式之所以可用，是因为 `resolv.conf` 中的 `search` 域。当你查询 `my-service` 时，解析器会按顺序追加每个搜索域，直到获得结果：先是 `my-service.default.svc.cluster.local`，然后是 `my-service.svc.cluster.local`，依此类推。

## CoreDNS 如何保持同步

CoreDNS 运行一个 Kubernetes 插件，它会监听 API server 上的 Service 和 Endpoint 变更。当你创建、删除或修改 Service 时，CoreDNS 会在数秒内获取到变更并更新其 DNS 记录。无需手动配置——一切都是自动的。

你可以查看正在运行的 CoreDNS：

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl get svc -n kube-system kube-dns
```

CoreDNS 通常以 Deployment 形式运行，并带有 2 个副本以保证可用性。

## Headless Service 与 DNS

普通 Service 有一个 ClusterIP，其 DNS 记录解析到该单一 IP。Headless Service（`clusterIP: None`）的工作方式不同——其 DNS 记录返回其背后所有各个 Pod 的 IP 地址。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-db
spec:
  clusterIP: None    # headless
  selector:
    app: my-db
  ports:
    - port: 5432
```

```bash
# Normal Service: resolves to one ClusterIP
dig my-app.default.svc.cluster.local
# → 10.96.0.15

# Headless Service: resolves to individual pod IPs
dig my-db.default.svc.cluster.local
# → 10.244.1.5
# → 10.244.2.8
# → 10.244.1.12
```

Headless Service 被 StatefulSet 使用，其中每个 Pod 都需要可单独寻址（例如需要相互发现的数据库副本）。

## ExternalName Service

ExternalName Service 只是一个 DNS 别名——一个指向外部主机名的 CNAME 记录：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-database
spec:
  type: ExternalName
  externalName: mydb.example.com
```

当 Pod 查询 `my-database.default.svc.cluster.local` 时，CoreDNS 返回一个指向 `mydb.example.com` 的 CNAME。这对于将内部服务名指向外部数据库或 API 而无需在应用配置中硬编码主机名非常有用。

## Pod DNS 记录

CoreDNS 还可以为各个 Pod 创建 DNS 记录，使用 Pod 的 IP 并将点替换为短横线：

```
10-244-1-5.default.pod.cluster.local
```

这主要用于 StatefulSet，其中每个 Pod 通过 Headless Service 获得一个稳定的 DNS 名称：

```
my-db-0.my-db.default.svc.cluster.local
my-db-1.my-db.default.svc.cluster.local
```

## 如果 CoreDNS 宕机会发生什么

如果两个 CoreDNS 副本都崩溃，新的 DNS 查询会在整个集群范围内失败。已经解析过名称并持有 TCP 连接的 Pod 会继续工作。但任何需要 DNS 解析的新连接尝试都会挂起或失败。

这就是为什么 CoreDNS 以多副本 Deployment 形式运行、设置了资源请求以防止被驱逐，并被当作关键基础设施对待。监控 CoreDNS 的健康状况至关重要。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 服务和 Pod 的 DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) -- 类型: 文档, 时间: 15m
- [CoreDNS 手册](https://coredns.io/manual/toc/) -- 类型: 文档, 时间: 20m
- [自定义 DNS 服务](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/) -- 类型: 文档, 时间: 10m

<!-- ZH_UI -->
1. 了解 CoreDNS 以 Pod 形式运行在 kube-system 中，是集群的 DNS 服务器
2. 理解每个 Pod 的 /etc/resolv.conf 都配置为指向 CoreDNS 的 Service IP
3. 了解命名规范：<service>.<namespace>.svc.cluster.local
4. 理解无头 Service：DNS 直接返回 Pod IP，而不是单个 ClusterIP
5. 了解 CoreDNS 如何监听 API server 的 Service 和 Endpoint 变更以保持 DNS 记录最新
6. 理解 ExternalName Service：指向外部主机名的 DNS CNAME
7. 我的 DNS 查询随机变慢——有些耗时 5 秒，有些完全失败。我该从哪里入手？
8. Pod 大多数时候能解析服务名，但在高负载下 DNS 变得不稳定，有时查询会超时。我还注意到在 Pod 内解析 `api.stripe.com` 耗时远超预期。我不确定是 CoreDNS、我的 resolv.conf 还是其他原因。
