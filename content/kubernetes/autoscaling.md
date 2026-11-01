---
id: autoscaling
title: Autoscaling
zone: kubernetes
edges:
  to:
    - id: k8s-for-production
      zone: kubernetes-production
      question: >-
        My cluster scales itself now. But I built all of this by following
        tutorials — is this actually ready for real traffic?
      detail: >-
        I have deployments, services, ingress, autoscaling — it all works
        in my test cluster. But I have no idea if this setup would survive
        a real production workload. What does it take to run Kubernetes for
        real — not just as a learning exercise?
difficulty: 2
tags:
  - kubernetes
  - autoscaling
  - hpa
  - vpa
  - cluster-autoscaler
  - metrics-server
  - k8s
category: practice
milestones:
  - Install Metrics Server and verify kubectl top pods works
  - Create an HPA targeting 50% CPU utilisation and watch it scale under load
  - >-
    Understand the difference between HPA (Pod count) and VPA (Pod resource
    requests)
  - Understand how the cluster autoscaler adds nodes when Pods are unschedulable
title_zh: "自动扩缩容"

---


Kubernetes can automatically adjust the number of Pod replicas based on observed metrics. The Horizontal Pod Autoscaler (HPA) adds or removes replicas when CPU or memory utilization crosses thresholds. The Cluster Autoscaler adds or removes nodes when Pods can't be scheduled. Together, they let your cluster grow and shrink with actual demand.

<!-- DEEP_DIVE -->

## Prerequisites: Metrics Server

The HPA watches metrics, but it needs something to provide them. **Metrics Server** collects resource utilization from each node's kubelet and exposes it through the Kubernetes metrics API. Without Metrics Server, `kubectl top pods` doesn't work and the HPA has nothing to read.

Install it:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Verify:

```bash
kubectl top nodes
kubectl top pods
```

Most managed clusters (EKS, GKE, AKS) install Metrics Server by default.

## The Horizontal Pod Autoscaler (HPA)

The HPA watches the resource utilization of a Deployment (or other scalable resource) and adjusts the replica count to keep utilization near the target:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50   # scale when avg Pod CPU > 50% of its request
```

The HPA checks every 15 seconds (by default). If average CPU across all Pods exceeds 50% of their CPU request, it adds replicas. If utilization drops significantly below, it removes them — with a scale-down cool-down period to avoid flapping.

## Why resource requests are required

The HPA measures utilization as a percentage of the resource **request**. If requests aren't set, the HPA has no denominator — it can't compute utilization — and simply won't function. This is why setting resource requests is a strict prerequisite for autoscaling.

## The Vertical Pod Autoscaler (VPA)

The HPA changes how many Pods run. The **Vertical Pod Autoscaler** changes what resources individual Pods are allowed to request. VPA watches actual usage over time and recommends (or automatically adjusts) the `requests` on the Pod template to better match real consumption.

VPA and HPA don't work well together when targeting the same metric — they'll fight over what the right behavior is. Common practice: use VPA in recommendation-only mode (`updateMode: Off`) to get sizing suggestions, then apply those manually to your resource requests.

## The Cluster Autoscaler

The HPA and VPA operate within the existing set of nodes. But what if all nodes are full? The **Cluster Autoscaler** (CA) adds new nodes when Pods are stuck in `Pending` because no existing node can accommodate them. It also removes underutilized nodes by cordoning and draining them.

The Cluster Autoscaler integrates with cloud provider APIs to actually provision or terminate instances. On EKS, it adjusts Auto Scaling Group desired counts. On GKE, it's built into the managed node pool. In all cases, it's triggered by unschedulable Pods, not by CPU utilization.

## KEDA: scaling on custom signals

The built-in HPA scales on CPU and memory. **KEDA** (Kubernetes Event-Driven Autoscaling) extends the HPA to scale on external event sources: Kafka consumer lag, SQS queue depth, Prometheus query results, HTTP request rate, and dozens more. For event-driven workloads — workers that process a queue — KEDA is often a better fit than raw CPU-based autoscaling.

<!-- RESOURCES -->

- [Kubernetes Docs - Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) -- type: docs, time: 25m
- [Metrics Server GitHub](https://github.com/kubernetes-sigs/metrics-server) -- type: tool, time: 10m
- [Cluster Autoscaler GitHub](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) -- type: docs, time: 20m
- [KEDA - Kubernetes Event-Driven Autoscaling](https://keda.sh/) -- type: tool, time: 20m

<!-- ZH_SUMMARY -->
Kubernetes 可以根据观测到的指标自动调整 Pod 副本数量。当 CPU 或内存利用率超过阈值时，Horizontal Pod Autoscaler（HPA）会增加或减少副本。当 Pod 无法被调度时，Cluster Autoscaler 会增加或移除节点。二者结合，使集群能够随实际需求扩缩容。

<!-- ZH_DEEP_DIVE -->
## 前置条件：Metrics Server

HPA 会监控指标，但它需要由某个组件来提供这些指标。**Metrics Server** 从每个节点的 kubelet 收集资源利用率，并通过 Kubernetes metrics API 暴露出来。如果没有 Metrics Server，`kubectl top pods` 就无法工作，HPA 也就没有可读取的数据。

安装它：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

验证：

```bash
kubectl top nodes
kubectl top pods
```

大多数托管集群（EKS、GKE、AKS）默认会安装 Metrics Server。

## Horizontal Pod Autoscaler（HPA）

HPA 会监控 Deployment（或其他可伸缩资源）的资源利用率，并调整副本数，使利用率保持在目标值附近：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50   # scale when avg Pod CPU > 50% of its request
```

HPA 默认每 15 秒检查一次。如果所有 Pod 的平均 CPU 超过其 CPU request 的 50%，它就会增加副本。如果利用率显著低于该值，它就会减少副本——并带有缩容冷却期，以避免频繁抖动。

## 为什么必须设置资源 requests

HPA 将利用率衡量为资源 **request** 的百分比。如果没有设置 requests，HPA 就没有分母——无法计算利用率——也就根本无法工作。这就是为什么设置资源 requests 是自动伸缩的严格前置条件。

## Vertical Pod Autoscaler（VPA）

HPA 改变的是运行多少个 Pod。**Vertical Pod Autoscaler** 改变的则是单个 Pod 被允许请求多少资源。VPA 会长期观察实际使用量，并建议（或自动调整）Pod 模板上的 `requests`，使其更好地匹配真实消耗。

当 VPA 和 HPA 针对同一指标时，它们无法很好地协同工作——它们会就正确行为产生冲突。常见做法是：以仅推荐模式（`updateMode: Off`）使用 VPA 获取规格建议，然后手动将这些建议应用到你的资源 requests 中。

## Cluster Autoscaler

HPA 和 VPA 在现有节点集合内运作。但如果所有节点都满了怎么办？**Cluster Autoscaler**（CA）会在 Pod 因没有现有节点能够容纳而卡在 `Pending` 状态时添加新节点。它还会通过 cordon 和 drain 来移除利用率不足的节点。

Cluster Autoscaler 与云提供商 API 集成，以实际创建或终止实例。在 EKS 上，它会调整 Auto Scaling Group 的期望数量。在 GKE 上，它内置于托管节点池中。在所有情况下，它都是由不可调度的 Pod 触发，而不是由 CPU 利用率触发。

## KEDA：基于自定义信号进行伸缩

内置 HPA 基于 CPU 和内存进行伸缩。**KEDA**（Kubernetes Event-Driven Autoscaling）扩展了 HPA，使其能够基于外部事件源进行伸缩：Kafka 消费者延迟、SQS 队列深度、Prometheus 查询结果、HTTP 请求速率，以及数十种其他信号。对于事件驱动型工作负载——处理队列的 worker——KEDA 通常比基于原始 CPU 的自动伸缩更合适。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) -- 类型: 文档, 时长: 25m
- [Metrics Server GitHub](https://github.com/kubernetes-sigs/metrics-server) -- 类型: 工具, 时长: 10m
- [Cluster Autoscaler GitHub](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) -- 类型: 文档, 时长: 20m
- [KEDA - Kubernetes 事件驱动自动扩缩容](https://keda.sh/) -- 类型: 工具, 时长: 20m

<!-- ZH_UI -->
1. 安装 Metrics Server 并验证 kubectl top pods 可用
2. 创建目标 CPU 利用率为 50% 的 HPA，并观察其在负载下扩缩容
3. 理解 HPA（Pod 数量）与 VPA（Pod 资源请求）的区别
4. 理解集群自动扩缩器如何在 Pod 无法调度时添加节点
5. 我的集群现在能自动扩缩容了。但这些都是跟着教程搭的——这真的能承载真实流量吗？
6. 我有 Deployment、Service、Ingress、自动扩缩容——在测试集群里都跑通了。但我完全不知道这套配置能否扛住真实生产负载。真正运行 Kubernetes 需要什么——而不只是当作学习练习？
