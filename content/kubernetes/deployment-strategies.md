---
id: deployment-strategies
title: Deployment Strategies
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - deployment-strategies
  - blue-green
  - canary
  - rolling-update
  - argo-rollouts
  - k8s
category: concept
milestones:
  - >-
    Implement a blue-green deployment using two Deployments and a Service
    selector swap
  - Implement a basic canary by running two Deployments with weighted traffic
  - Understand what Argo Rollouts adds on top of standard Kubernetes Deployments
  - >-
    Know when to use rolling update vs blue-green vs canary based on risk
    tolerance
title_zh: "部署策略"

---


Kubernetes rolling updates are safe for most changes, but they give you limited control: old and new versions handle traffic simultaneously during the transition. Blue-green and canary deployments give you more options — either an instant, clean switch between versions, or a gradual rollout with real traffic testing before full commitment.

<!-- DEEP_DIVE -->

## Rolling update (the default)

The Deployment rolling update gradually replaces old Pods with new ones. It's zero-downtime for properly configured apps and requires no extra tooling. The trade-off: during the transition, old and new versions both receive traffic simultaneously.

If your change is backwards-incompatible — a breaking API change, a database schema change that the old code can't read — a rolling update can cause errors during the transition window. In those cases, you need more control.

## Blue-green deployments

Blue-green means two complete environments: the live one (blue) and the new version (green). All traffic is on blue. When you're confident in green — you've tested it, your metrics look good — you switch all traffic to it at once by updating a Service selector.

On Kubernetes, implement this with two Deployments:

```yaml
# Service — controls which version gets traffic
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
    slot: blue      # change to "green" to switch all traffic instantly
  ports:
    - port: 80
      targetPort: 8080
```

Deploy the green Deployment alongside blue (with label `slot: green`), test it with port-forward or a separate Service, then flip:

```bash
kubectl patch service my-app -p '{"spec":{"selector":{"slot":"green"}}}'
```

Traffic immediately flows to green. If anything is wrong, flip back to blue instantly. Once satisfied, scale down blue.

The cost: you're running twice the compute during the switchover window. For large Deployments, that's significant.

## Canary deployments

Canary means sending a small slice of real traffic to the new version while the majority stays on the old version. If the canary looks healthy — error rate, latency, business metrics — you gradually increase the traffic split until the rollout is complete.

A simple Kubernetes canary without extra tooling: two Deployments sharing the same Service label, with different replica counts to control the traffic split:

```yaml
# stable: 9 replicas → ~90% of traffic
# canary: 1 replica  → ~10% of traffic
# Service selector matches both via shared label "app: my-app"
```

This is blunt — the split is purely proportional to replica counts. For precise traffic weights (10% regardless of replica count), you need an Ingress controller that supports traffic splitting (Traefik, NGINX with annotations), or a service mesh (Istio, Linkerd).

## Argo Rollouts

**Argo Rollouts** is a Kubernetes controller that replaces the standard Deployment with a `Rollout` resource that natively supports progressive delivery strategies:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10       # send 10% to new version
        - pause: {duration: 5m}
        - analysis: {...}     # check Prometheus metrics; abort if error rate spikes
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
```

Argo Rollouts integrates with ArgoCD for GitOps-driven progressive delivery — a Git commit triggers the rollout, analysis gates decide whether to proceed or auto-rollback.

## Choosing a strategy

- **Rolling update** — the right default for backwards-compatible changes. No extra tooling, no extra cost.
- **Blue-green** — when you need an instant, clean switch between versions and can afford the extra compute.
- **Canary** — when you want to test a new version with real production traffic before committing to a full rollout, especially for high-risk changes.

<!-- RESOURCES -->

- [Argo Rollouts Documentation](https://argo-rollouts.readthedocs.io/) -- type: docs, time: 30m
- [Kubernetes Deployment Strategies - Container Solutions](https://blog.container-solutions.com/kubernetes-deployment-strategies) -- type: article, time: 15m
- [Kubernetes Docs - Deployments (strategy section)](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Kubernetes 滚动更新对大多数变更来说是安全的，但它提供的控制有限：在过渡期间，旧版本和新版本会同时处理流量。蓝绿部署和金丝雀部署提供了更多选择——要么在版本之间进行即时、干净的切换，要么在完全投入之前通过真实流量测试进行渐进式发布。

<!-- ZH_DEEP_DIVE -->
## 滚动更新（默认方式）

Deployment 的滚动更新会逐步用新 Pod 替换旧 Pod。对于配置得当的应用而言，这是零停机的，且无需额外工具。代价是：在过渡期间，旧版本和新版本会同时接收流量。

如果你的变更不向后兼容——比如破坏性的 API 变更、旧代码无法读取的数据库 schema 变更——滚动更新可能会在过渡窗口内引发错误。这种情况下，你需要更强的控制能力。

## 蓝绿部署

蓝绿意味着两套完整的环境：线上环境（蓝）和新版本（绿）。所有流量都在蓝上。当你对绿有把握时——已经测试过、指标看起来良好——通过更新 Service selector 一次性把所有流量切过去。

在 Kubernetes 上，用两个 Deployment 实现：

```yaml
# Service — controls which version gets traffic
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
    slot: blue      # change to "green" to switch all traffic instantly
  ports:
    - port: 80
      targetPort: 8080
```

在蓝旁边部署绿的 Deployment（带标签 `slot: green`），用 port-forward 或单独的 Service 测试它，然后切换：

```bash
kubectl patch service my-app -p '{"spec":{"selector":{"slot":"green"}}}'
```

流量立即流向绿。如果出任何问题，瞬间切回蓝。确认无误后，缩容蓝。

代价是：在切换窗口内你要运行两倍的计算资源。对于大型 Deployment，这很可观。

## 金丝雀部署

金丝雀意味着把一小部分真实流量发给新版本，而大部分流量留在旧版本。如果金丝雀看起来健康——错误率、延迟、业务指标——就逐步增大流量分配比例，直到发布完成。

一个不依赖额外工具的简单 Kubernetes 金丝雀：两个 Deployment 共享同一个 Service 标签，用不同的副本数控制流量分配：

```yaml
# stable: 9 replicas → ~90% of traffic
# canary: 1 replica  → ~10% of traffic
# Service selector matches both via shared label "app: my-app"
```

这种方式很粗糙——分配比例完全与副本数成正比。要精确控制流量权重（无论副本数多少都是 10%），你需要支持流量拆分的 Ingress controller（Traefik、带注解的 NGINX），或者 service mesh（Istio、Linkerd）。

## Argo Rollouts

**Argo Rollouts** 是一个 Kubernetes controller，它用 `Rollout` 资源替代标准 Deployment，原生支持渐进式交付策略：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10       # send 10% to new version
        - pause: {duration: 5m}
        - analysis: {...}     # check Prometheus metrics; abort if error rate spikes
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
```

Argo Rollouts 与 ArgoCD 集成，实现 GitOps 驱动的渐进式交付——一次 Git 提交触发发布，分析门禁决定是继续还是自动回滚。

## 选择策略

- **滚动更新**——向后兼容变更的合适默认选择。无需额外工具，无额外成本。
- **蓝绿**——当你需要在版本之间即时、干净地切换，且能承担额外计算资源时。
- **金丝雀**——当你想在全面发布之前用真实生产流量测试新版本时，尤其是高风险变更。

<!-- ZH_RESOURCES -->
- [Argo Rollouts 文档](https://argo-rollouts.readthedocs.io/) -- 类型: 文档, 时间: 30m
- [Kubernetes 部署策略 - Container Solutions](https://blog.container-solutions.com/kubernetes-deployment-strategies) -- 类型: 文章, 时间: 15m
- [Kubernetes 文档 - Deployments（strategy 部分）](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 使用两个 Deployment 和 Service 选择器切换实现蓝绿部署
2. 通过运行两个 Deployment 并加权流量实现基础金丝雀发布
3. 理解 Argo Rollouts 在标准 Kubernetes Deployment 之上增加了什么
4. 了解如何根据风险容忍度选择滚动更新、蓝绿部署或金丝雀发布
