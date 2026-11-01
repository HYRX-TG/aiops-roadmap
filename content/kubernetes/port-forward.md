---
id: port-forward
title: Accessing Pods with Port Forward
zone: kubernetes
edges:
  to:
    - id: services
      question: >-
        Port-forward works for local testing. What's the proper way to expose a
        Pod inside the cluster?
      detail: >-
        Port-forward was useful for checking things worked, but it drops the
        moment I close my terminal and nobody else can use it. My app needs a
        persistent, accessible endpoint inside the cluster that doesn't depend
        on me keeping a command running. How does anything else in the cluster
        actually reach my Pod reliably?
difficulty: 1
tags:
  - kubernetes
  - kubectl
  - port-forward
  - debugging
  - development
  - k8s
category: practice
milestones:
  - Use kubectl port-forward to reach a Pod from your local browser
  - Understand why port-forward is not suitable for production access
  - Know the difference between port-forwarding to a Pod vs to a Service
title_zh: "使用端口转发访问 Pod"

---


`kubectl port-forward` creates a tunnel from a port on your local machine directly to a port on a Pod in the cluster. It bypasses Services, Ingress, and any other cluster networking — making it the fastest way to verify a Pod is working without setting up anything else.

<!-- DEEP_DIVE -->

## How it works

```bash
kubectl port-forward pod/my-app 8080:80
```

This forwards `localhost:8080` on your machine to port 80 on the Pod `my-app`. Open `http://localhost:8080` in a browser and you're hitting that Pod directly.

You can also forward to a Service (which load-balances across the Service's Pods):

```bash
kubectl port-forward service/my-service 8080:80
```

The connection is maintained for as long as the `kubectl` command is running. Kill it with Ctrl-C and the tunnel closes.

## What it's good for

- Checking that a newly deployed Pod is serving the right response before configuring a Service
- Accessing internal dashboards (Prometheus UI, ArgoCD, Kubernetes Dashboard, Grafana) that you deliberately don't expose to the internet
- Debugging a specific Pod instance when you're investigating a problem on that particular replica
- Reaching a database or cache from your local machine without SSH tunnels

## What it's not

Port-forward is a debugging shortcut, not a networking solution. It:

- Only works while the command is running — there's no persistent tunnel
- Only works from your local machine
- Routes to one specific Pod or Service backend — if the Pod restarts, you need to re-run the command
- Has no authentication, TLS, or load balancing beyond what's on the Pod itself

For production traffic to reach your Pods, use Services and Ingress.

## Targeting a specific namespace

If your Pod isn't in the default namespace, add `-n`:

```bash
kubectl port-forward pod/my-app 8080:80 -n my-namespace
```

And if you want to forward a local port to a container port that uses a different number:

```bash
kubectl port-forward pod/my-app 9090:8080
# local:9090 → container:8080
```

<!-- RESOURCES -->

- [kubectl port-forward docs](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_port-forward/) -- type: docs, time: 5m
- [Kubernetes Docs - Access Applications in a Cluster](https://kubernetes.io/docs/tasks/access-application-cluster/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
`kubectl port-forward` 会从本地机器上的一个端口直接建立一条隧道，连接到集群中某个 Pod 上的端口。它绕过了 Service、Ingress 以及其他所有集群网络机制——因此，无需额外配置任何东西，它便是验证 Pod 是否正常工作的最快方式。

<!-- ZH_DEEP_DIVE -->
## 工作原理

```bash
kubectl port-forward pod/my-app 8080:80
```

这条命令会将你机器上的 `localhost:8080` 转发到 Pod `my-app` 的 80 端口。在浏览器中打开 `http://localhost:8080`，你就能直接访问该 Pod。

你也可以转发到 Service（它会在该 Service 的多个 Pod 之间做负载均衡）：

```bash
kubectl port-forward service/my-service 8080:80
```

只要 `kubectl` 命令持续运行，连接就会一直保持。用 Ctrl-C 终止命令，隧道即关闭。

## 适用场景

- 在配置 Service 之前，验证新部署的 Pod 是否返回了正确的响应
- 访问你刻意不暴露到互联网的内部仪表盘（Prometheus UI、ArgoCD、Kubernetes Dashboard、Grafana）
- 当你正在排查某个特定副本上的问题时，调试该 Pod 实例
- 无需 SSH 隧道即可从本地机器访问数据库或缓存

## 不适用场景

Port-forward 是调试用的快捷方式，而非网络解决方案。它：

- 仅在命令运行期间有效——没有持久化隧道
- 仅能从你的本地机器使用
- 路由到某一个特定的 Pod 或 Service 后端——如果 Pod 重启，你需要重新执行命令
- 除了 Pod 本身提供的之外，没有身份认证、TLS 或负载均衡

要让生产流量到达你的 Pod，请使用 Service 和 Ingress。

## 指定命名空间

如果你的 Pod 不在 default 命名空间，请加上 `-n`：

```bash
kubectl port-forward pod/my-app 8080:80 -n my-namespace
```

如果你想将本地端口转发到使用不同端口号的容器端口：

```bash
kubectl port-forward pod/my-app 9090:8080
# local:9090 → container:8080
```

<!-- ZH_RESOURCES -->
- [kubectl port-forward 文档](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_port-forward/) -- 类型: 文档, 时间: 5m
- [Kubernetes 文档 - 在集群中访问应用](https://kubernetes.io/docs/tasks/access-application-cluster/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 使用 kubectl port-forward 从本地浏览器访问 Pod
2. 理解为什么 port-forward 不适合生产环境访问
3. 了解 port-forward 到 Pod 与到 Service 的区别
4. port-forward 适用于本地测试。在集群内部暴露 Pod 的正确方式是什么？
5. port-forward 对验证功能是否正常很有用，但一关闭终端就断开，其他人也无法使用。我的应用需要在集群内有一个持久、可访问的端点，不依赖我持续运行命令。集群中的其他组件究竟如何可靠地访问我的 Pod？
