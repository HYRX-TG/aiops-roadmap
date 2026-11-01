---
id: service-mesh-intro
title: Service Meshes
zone: kubernetes-production
edges:
  to:
    - id: always-firefighting
      zone: sre
      question: >-
        The infrastructure is sorted — GitOps, autoscaling, security,
        networking. But we're still scrambling every time something breaks.
        Is there a more structured way to run all of this?
      detail: >-
        We have great tooling now. But incidents are still chaos — nobody
        knows who's in charge, we keep having the same problems, and there's
        no process for learning from failures. The technology is solid but
        the way we operate feels broken. How do teams actually do this
        professionally?
difficulty: 3
tags:
  - kubernetes
  - istio
  - linkerd
  - cilium
  - service-mesh
  - mtls
  - k8s
  - production
category: concept
milestones:
  - >-
    Understand what a service mesh does: automatic mTLS, traffic policies,
    request tracing
  - >-
    Know the three main options: Istio (full-featured), Linkerd (simple), Cilium
    (eBPF, no sidecar)
  - >-
    Understand the real cost: CPU overhead per pod, operational complexity,
    steep learning curve
  - Know honestly when you need a service mesh vs when you're over-engineering
title_zh: "服务网格"

---


A service mesh moves networking concerns — encryption, retries, timeouts, observability — out of application code and into infrastructure. It intercepts all service-to-service traffic and adds these capabilities automatically, without changing the applications themselves. The catch: it adds real operational complexity and resource overhead.

<!-- DEEP_DIVE -->

## How it works: the sidecar model

The traditional service mesh approach injects a proxy sidecar container into every pod. This proxy intercepts all inbound and outbound network traffic. The application talks to localhost; the sidecar handles the actual network communication.

```
Pod: [your-app container] <—localhost—> [envoy proxy sidecar]
                                                ↕
                                         cluster network
```

Because the proxy is at the kernel network level, it can intercept and transform traffic without any code changes to the application. You get mTLS, retries, circuit breaking, and request metrics for free.

The data plane (the proxies) is configured by a control plane that watches Kubernetes resources and pushes configuration to all proxies.

## What a service mesh gives you

**Automatic mTLS** — every connection between pods gets encrypted and authenticated. Both sides present certificates issued by the mesh's certificate authority. Certificates are rotated automatically. No changes required in application code.

**Request-level metrics** — latency, error rate, request rate, and response size per source/destination pair. You can answer "what percentage of requests from the order service to the inventory service are failing?" without any application instrumentation.

**Distributed tracing** — the mesh injects trace headers and propagates them automatically. Traces appear in Jaeger or Zipkin without application changes (though applications still need to propagate headers through async calls).

**Retries and timeouts** — configurable at the mesh level per route. One policy applies to all services using that route.

**Traffic splitting** — send 5% of traffic to the new version, 95% to the stable version. Shift gradually. All controlled by CRDs, not by replica count.

**Circuit breaking** — automatically stop sending requests to a service that's failing, giving it time to recover.

## The three main options

**Istio** — the most complete and most widely adopted. Extensive feature set: advanced traffic management, authorization policies, telemetry. Also the most complex. The control plane (istiod) is significant infrastructure. Configuration is verbose. Learning curve is steep.

If you need the full feature set and have a team that will invest in operating it, Istio is the most capable option.

**Linkerd** — much simpler. Written in Rust (lower resource overhead). Opinionated and minimal. Easier to install and operate. Lacks some of Istio's advanced traffic management features but covers the core use cases well.

If you want a mesh that's easier to operate and covers 90% of use cases, Linkerd is the right choice.

**Cilium** — eBPF-based. No sidecar. Uses Linux kernel eBPF programs to implement networking at the kernel level rather than through a proxy. Lower per-pod overhead. Also serves as the CNI (replacing traditional sidecar-based approaches entirely).

Requires a recent Linux kernel (5.10+). Works best on AWS, GKE, and AKS where you control the node OS. The most performant option. Increasingly the choice for new deployments.

## The real cost

**CPU and memory overhead** — every pod gets a sidecar proxy. On large clusters with many small pods, this adds up: a typical Envoy sidecar uses 50–100m CPU and 50–100Mi memory per pod at idle, more under load.

**Latency overhead** — every request goes through two proxy hops (source sidecar → destination sidecar). Well-tuned meshes add < 1ms in the p99. Poorly tuned or under-resourced meshes can add much more.

**Operational complexity** — the mesh control plane is its own distributed system. It needs to be upgraded, monitored, and debugged. When the mesh has a bug, networking for your entire cluster can be affected.

**Debugging difficulty** — when something goes wrong with network connectivity, the mesh is now a suspect. Debugging requires understanding proxy configuration, certificate issues, and mesh policies on top of Kubernetes networking.

## Honest assessment: do you need it?

A service mesh earns its cost when you need mTLS between every service for compliance, or when you have enough services that per-service observability instrumentation has become unmanageable, or when you're doing sophisticated traffic management (canary deployments, traffic splitting).

If you have 5 services with no compliance requirements, add Prometheus metrics to your apps directly, use your ingress controller for basic traffic splitting, and skip the mesh. The operational overhead doesn't pay off at small scale.

<!-- RESOURCES -->

- [Istio Documentation](https://istio.io/latest/docs/) -- type: docs, time: 30m
- [Linkerd Getting Started](https://linkerd.io/2.15/getting-started/) -- type: docs, time: 20m
- [Cilium Documentation](https://docs.cilium.io/en/stable/) -- type: docs, time: 25m

<!-- ZH_SUMMARY -->
服务网格将网络相关的关注点——加密、重试、超时、可观测性——从应用代码中移出，下沉到基础设施层。它拦截所有服务间流量，并自动添加这些能力，而无需改动应用本身。代价是：它会带来实实在在的运维复杂度和资源开销。

<!-- ZH_DEEP_DIVE -->
## 工作原理：边车模型

传统服务网格的做法是向每个 Pod 注入一个代理边车容器。这个代理会拦截所有入站和出站网络流量。应用与 localhost 通信；边车负责实际的网络通信。

```
Pod: [your-app container] <—localhost—> [envoy proxy sidecar]
                                                ↕
                                         cluster network
```

由于代理位于内核网络层，它可以在不修改应用代码的情况下拦截和转换流量。你可以免费获得 mTLS、重试、熔断和请求指标。

数据平面（即各个代理）由一个控制平面配置，控制平面会监听 Kubernetes 资源并将配置推送到所有代理。

## 服务网格能给你带来什么

**自动 mTLS** —— Pod 之间的每条连接都会被加密和认证。双方都会出示由网格证书颁发机构签发的证书。证书会自动轮换。应用代码无需任何改动。

**请求级指标** —— 按源/目标对统计的延迟、错误率、请求速率和响应大小。无需任何应用埋点，你就能回答“从订单服务到库存服务的请求中有百分之多少在失败？”

**分布式追踪** —— 网格会注入追踪头并自动传播它们。无需修改应用，追踪数据就会出现在 Jaeger 或 Zipkin 中（不过应用仍然需要在异步调用中传播这些头）。

**重试和超时** —— 可在网格层面按路由配置。一条策略适用于使用该路由的所有服务。

**流量拆分** —— 将 5% 的流量发送到新版本，95% 发送到稳定版本。逐步切换。全部通过 CRD 控制，而不是通过副本数。

**熔断** —— 自动停止向正在失败的服务发送请求，给它时间恢复。

## 三个主要选项

**Istio** —— 功能最完整、采用最广泛。功能集丰富：高级流量管理、授权策略、遥测。也是最复杂的。控制平面（istiod）是相当重的基础设施。配置冗长。学习曲线陡峭。

如果你需要完整的功能集，并且有团队愿意投入精力运维它，Istio 是能力最强的选项。

**Linkerd** —— 简单得多。用 Rust 编写（资源开销更低）。有明确取舍且极简。更易于安装和运维。缺少 Istio 的一些高级流量管理功能，但很好地覆盖了核心用例。

如果你想要一个更易于运维、能覆盖 90% 用例的网格，Linkerd 是正确选择。

**Cilium** —— 基于 eBPF。没有边车。使用 Linux 内核 eBPF 程序在内核层面实现网络，而不是通过代理。每个 Pod 的开销更低。同时充当 CNI（完全取代传统的基于边车的方式）。

需要较新的 Linux 内核（5.10+）。在你能控制节点操作系统的 AWS、GKE 和 AKS 上效果最好。性能最强的选项。越来越多地成为新部署的选择。

## 真实成本

**CPU 和内存开销** —— 每个 Pod 都会有一个边车代理。在有许多小 Pod 的大型集群上，这会累积起来：一个典型的 Envoy 边车在空闲时每个 Pod 使用 50–100m CPU 和 50–100Mi 内存，负载下更多。

**延迟开销** —— 每个请求都要经过两跳代理（源边车 → 目标边车）。调优良好的网格在 p99 上增加 < 1ms。调优不佳或资源不足的网格可能增加得多得多。

**运维复杂性** —— 网格控制平面本身就是一个分布式系统。它需要升级、监控和调试。当网格出现 bug 时，整个集群的网络都可能受到影响。

**调试难度** —— 当网络连接出现问题时，网格现在成了嫌疑对象。调试需要在 Kubernetes 网络之上理解代理配置、证书问题和网格策略。

## 诚实的评估：你需要它吗？

当你需要为满足合规要求而在每个服务之间启用 mTLS，或者当你的服务多到按服务做可观测性埋点已变得难以管理，或者当你正在进行复杂的流量管理（金丝雀部署、流量拆分）时，服务网格才值得它的成本。

如果你只有 5 个服务且没有合规要求，直接为应用添加 Prometheus 指标，用你的 ingress controller 做基本的流量拆分，然后跳过网格。在小规模下，运维开销并不划算。

<!-- ZH_RESOURCES -->
- [Istio 文档](https://istio.io/latest/docs/) -- 类型: 文档, 时间: 30m
- [Linkerd 入门](https://linkerd.io/2.15/getting-started/) -- 类型: 文档, 时间: 20m
- [Cilium 文档](https://docs.cilium.io/en/stable/) -- 类型: 文档, 时间: 25m

<!-- ZH_UI -->
1. 理解服务网格的作用：自动 mTLS、流量策略、请求追踪
2. 了解三种主要选择：Istio（功能全面）、Linkerd（简单）、Cilium（eBPF，无 sidecar）
3. 理解真实成本：每个 Pod 的 CPU 开销、运维复杂性、陡峭的学习曲线
4. 诚实判断何时需要服务网格、何时属于过度设计
5. 基础设施已经理顺——GitOps、自动扩缩容、安全、网络。但每次出问题我们仍然手忙脚乱。有没有更有结构的方式来运行这一切？
6. 我们现在有很好的工具。但事故仍然一片混乱——没人知道谁负责，同样的问题反复出现，也没有从失败中学习的流程。技术是扎实的，但我们的运作方式感觉是坏的。团队究竟是如何专业地做到这一点的？
