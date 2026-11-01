---
id: debugging-services
title: Debugging Services
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - debugging
  - services
  - endpoints
  - selectors
  - dns
  - k8s
category: practice
milestones:
  - >-
    Use kubectl get endpoints to check whether a Service has any pods behind it
  - >-
    Diagnose a selector mismatch — the single most common reason a Service
    routes to nothing
  - Test Service reachability from inside the cluster using kubectl exec + curl
  - Verify DNS resolution with nslookup or dig from inside a pod
title_zh: "调试服务"

---


When a Service isn't routing traffic, the problem is almost always one of two things: the selector doesn't match any pod labels, or there are no healthy pods for it to send traffic to. Kubernetes gives you straightforward tools to confirm which one it is.

<!-- DEEP_DIVE -->

## Check endpoints first

A Service routes to pods by matching their labels. If the labels don't match, the Service has no backends — and you'll get timeouts or connection refused on every request.

Check whether the Service actually has any pods behind it:

```bash
kubectl get endpoints my-service
```

**If the ENDPOINTS column shows `<none>`**, the selector isn't matching any pods. That's your problem.

**If the ENDPOINTS column shows IPs**, the Service found pods — the issue is elsewhere (DNS, wrong port, the pods themselves are unhealthy).

## Diagnose a selector mismatch

A selector mismatch is the #1 Service bug. The Service has a `selector` block; pods have `labels`. They have to match exactly.

Check what the Service is selecting:

```bash
kubectl describe service my-service
```

Look at the `Selector` line:

```
Selector:  app=my-app,tier=frontend
```

Now check what labels your pods actually have:

```bash
kubectl get pods --show-labels
```

Compare the two. If there's any difference — a typo, a missing label, a different value — the Service won't find those pods. Fix the label on the pod (via its Deployment template) or fix the selector on the Service.

## Test reachability from inside the cluster

Services use cluster-internal IPs and DNS. You can't curl them from your laptop — you have to test from inside the cluster. Spin up a temporary debug pod:

```bash
kubectl run debug --image=curlimages/curl --rm -it --restart=Never -- /bin/sh
```

From inside, curl the Service by its DNS name:

```bash
# By short name (works within same namespace)
curl http://my-service:8080

# By fully qualified name
curl http://my-service.default.svc.cluster.local:8080
```

If the DNS name resolves but the connection is refused, the pods themselves are rejecting the connection (wrong port, app not listening). If DNS doesn't resolve, there may be a CoreDNS issue.

## Check DNS resolution

From inside any pod or the debug container above:

```bash
nslookup my-service
```

You should see it resolve to the Service's ClusterIP. If it doesn't resolve at all, CoreDNS may be having problems — check it with:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

## Check the port

A common mistake: the Service `port` (what you call from outside) and `targetPort` (what the container actually listens on) are wrong.

```yaml
spec:
  ports:
    - port: 80          # what you curl
      targetPort: 8080  # what the container listens on
```

If you curl `:80` and the container listens on `:8080` but `targetPort` is set to `80`, you'll get connection refused. Check with `kubectl describe service` and confirm `targetPort` matches the actual container port.

## A systematic approach

1. `kubectl get endpoints my-service` — does it have any pod IPs?
2. If empty: `kubectl describe service my-service` vs `kubectl get pods --show-labels` — find the selector mismatch
3. If populated: test from inside the cluster with curl
4. If DNS fails: check CoreDNS pods in kube-system
5. If connection refused: verify `targetPort` matches the container's listening port

<!-- RESOURCES -->

- [Kubernetes Docs - Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
当 Service 无法路由流量时，问题几乎总是出在以下两种情况之一：selector 没有匹配到任何 Pod 标签，或者没有健康的 Pod 可供其发送流量。Kubernetes 提供了直接的工具来确认究竟是哪一种情况。

<!-- ZH_DEEP_DIVE -->
## 先检查 endpoints

Service 通过匹配 Pod 的标签来将流量路由到 Pod。如果标签不匹配，Service 就没有后端——每个请求都会超时或被拒绝连接。

检查 Service 背后是否真的有 Pod：

```bash
kubectl get endpoints my-service
```

**如果 ENDPOINTS 列显示 `<none>`**，说明选择器没有匹配到任何 Pod。这就是问题所在。

**如果 ENDPOINTS 列显示 IP**，说明 Service 找到了 Pod——问题在别处（DNS、端口错误、Pod 本身不健康）。

## 诊断选择器不匹配

选择器不匹配是 Service 的头号 bug。Service 有一个 `selector` 块；Pod 有 `labels`。两者必须完全匹配。

检查 Service 在选择什么：

```bash
kubectl describe service my-service
```

查看 `Selector` 行：

```
Selector:  app=my-app,tier=frontend
```

现在检查你的 Pod 实际有哪些标签：

```bash
kubectl get pods --show-labels
```

对比两者。如果有任何差异——拼写错误、缺少标签、值不同——Service 就找不到这些 Pod。修复 Pod 上的标签（通过其 Deployment 模板）或修复 Service 上的选择器。

## 从集群内部测试可达性

Service 使用集群内部 IP 和 DNS。你无法从笔记本电脑上 curl 它们——必须从集群内部测试。启动一个临时调试 Pod：

```bash
kubectl run debug --image=curlimages/curl --rm -it --restart=Never -- /bin/sh
```

从内部，通过 DNS 名称 curl 该 Service：

```bash
# By short name (works within same namespace)
curl http://my-service:8080

# By fully qualified name
curl http://my-service.default.svc.cluster.local:8080
```

如果 DNS 名称能解析但连接被拒绝，说明 Pod 本身在拒绝连接（端口错误、应用未监听）。如果 DNS 无法解析，可能存在 CoreDNS 问题。

## 检查 DNS 解析

从任意 Pod 或上面的调试容器内部：

```bash
nslookup my-service
```

你应该看到它解析为 Service 的 ClusterIP。如果完全无法解析，CoreDNS 可能有问题——用以下命令检查：

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

## 检查端口

一个常见错误：Service 的 `port`（你从外部调用的端口）和 `targetPort`（容器实际监听的端口）配置错误。

```yaml
spec:
  ports:
    - port: 80          # what you curl
      targetPort: 8080  # what the container listens on
```

如果你 curl `:80`，容器监听 `:8080`，但 `targetPort` 被设为 `80`，你会得到连接被拒绝。用 `kubectl describe service` 检查，并确认 `targetPort` 与实际容器端口匹配。

## 系统化排查方法

1. `kubectl get endpoints my-service` —— 它是否有任何 Pod IP？
2. 如果为空：对比 `kubectl describe service my-service` 与 `kubectl get pods --show-labels` —— 找出选择器不匹配
3. 如果有内容：从集群内部用 curl 测试
4. 如果 DNS 失败：检查 kube-system 中的 CoreDNS Pod
5. 如果连接被拒绝：验证 `targetPort` 与容器的监听端口匹配

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 调试服务](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/) -- type: docs, time: 20m

<!-- ZH_UI -->
1. 使用 kubectl get endpoints 检查 Service 后端是否有 Pod
2. 诊断 selector 不匹配——Service 路由不到任何后端的最常见原因
3. 使用 kubectl exec + curl 从集群内部测试 Service 可达性
4. 在 Pod 内使用 nslookup 或 dig 验证 DNS 解析
