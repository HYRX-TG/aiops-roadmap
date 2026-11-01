---
id: service-mesh-problems
title: Problems a Service Mesh Solves
zone: kubernetes-production
edges:
  to:
    - id: service-mesh-intro
      question: Those problems sound familiar. What actually solves them?
      detail: >-
        I'm seeing all of these problems — unencrypted inter-service traffic, no
        request-level metrics, no automatic retries. I'm adding logic to each
        service individually to deal with it. There has to be a way to handle
        this at the infrastructure level instead.
difficulty: 2
tags:
  - kubernetes
  - service-mesh
  - mtls
  - observability
  - traffic
  - security
  - k8s
  - production
category: concept
milestones:
  - >-
    Know what happens when two services talk over plain HTTP inside a cluster —
    and why that's a problem
  - Understand what mTLS is and why implementing it in every app is impractical
  - >-
    Know why request-level visibility (latency, error rate per route) is hard to
    get without instrumentation
  - >-
    Understand what a service mesh offloads so your application code doesn't
    have to
title_zh: "服务网格解决的问题"

---


When services communicate over plain HTTP inside a Kubernetes cluster, you're operating without encryption, without identity verification between services, and without meaningful visibility into what's happening at the request level. These aren't theoretical concerns — they become operational problems as your service count grows.

<!-- DEEP_DIVE -->

## The unencrypted inter-service problem

Inside a Kubernetes cluster, service-to-service traffic travels over the cluster network unencrypted by default. Any pod that can observe network traffic — through a misconfiguration, a compromised pod, or a shared node — can read the payloads of requests between services.

For many internal services this is acceptable. For services that carry credentials, personal data, or payment information, it isn't.

The solution is mTLS (mutual TLS): both sides of a connection present certificates, verify each other's identity, and encrypt the channel. But implementing mTLS in every service means:
- Certificate management in every service
- Certificate rotation in every service
- Handling TLS negotiation failures in every service
- Consistent configuration across every language and framework

Most teams don't do this consistently. They add it to services where they remember to, and leave it out elsewhere.

## The observability gap

When a request from the frontend fails after passing through authentication → API gateway → order service → inventory service → database, which service is responsible? The frontend gets a 500 error. That's all you know.

With standard metrics and logs:
- You can see error rates per service
- You can see log output per service
- You cannot see the request as it traveled through the chain

Distributed tracing solves this (trace IDs propagated through request headers), but it requires every service to instrument and propagate trace headers correctly. In practice, one service in the chain that doesn't propagate trace IDs breaks the entire trace.

## Retry and timeout logic, duplicated everywhere

Service A calls Service B. Service B times out. Service A should retry with backoff. But Service A also calls Service C. The same retry logic is duplicated. And Service C has dependencies too.

This logic ends up implemented differently in every service, in every language, with different defaults and different failure modes. A service that was built by a team that didn't think about timeouts introduces a timeout-less connection that hangs indefinitely, creating cascading failures.

## Traffic shifting for canary deployments

You want to roll out a new version of the payment service to 5% of traffic first. With standard Kubernetes Services, you control this by replica count: 1 pod of the new version out of 20 pods total = 5% of traffic. It's imprecise and couples rollout percentage to pod count.

A proper canary deployment sends exactly 5% of requests to the new version regardless of replica count. Doing this without additional infrastructure requires logic in the ingress controller or the calling services — neither of which is designed for this.

## The signal that you need a service mesh

You need a service mesh when you find yourself solving these problems repeatedly:
- Adding mTLS to services one at a time and never finishing
- Building retry/timeout configurations in every service
- Flying blind during incidents because you don't know which hop is failing
- Wanting canary deployments but not being able to implement them cleanly

At small scale (3–5 services, internal-only traffic, low compliance requirements), plain HTTP plus basic logging is fine. The mesh adds operational complexity — it earns that cost when the alternative problems are more expensive.

<!-- RESOURCES -->

- [Kubernetes Docs - Connecting Applications with Services](https://kubernetes.io/docs/concepts/services-networking/connect-applications-service/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当服务在 Kubernetes 集群内部通过明文 HTTP 通信时，你是在没有加密、没有服务间身份验证、也没有对请求层面发生的情况进行有效可观测性的情况下运行。这些并非理论上的担忧——随着服务数量增长，它们会变成实际的运维问题。

<!-- ZH_DEEP_DIVE -->
## 未加密的服务间通信问题

在 Kubernetes 集群内部，服务到服务的流量默认通过集群网络以未加密的方式传输。任何能够观测网络流量的 Pod——无论是由于配置错误、被攻陷的 Pod，还是共享节点——都可以读取服务之间请求的载荷。

对于许多内部服务来说，这是可以接受的。但对于承载凭证、个人数据或支付信息的服务来说，则不可接受。

解决方案是 mTLS（双向 TLS）：连接双方都出示证书、验证彼此身份，并加密通道。但在每个服务中实现 mTLS 意味着：
- 在每个服务中管理证书
- 在每个服务中轮换证书
- 在每个服务中处理 TLS 协商失败
- 在每种语言和框架中保持一致的配置

大多数团队并不会一致地做到这一点。他们只在记得的服务上添加，其他服务则被遗漏。

## 可观测性缺口

当来自前端的请求经过认证 → API 网关 → 订单服务 → 库存服务 → 数据库后失败时，哪个服务应该负责？前端收到一个 500 错误。这就是你所知道的全部。

使用标准的指标和日志：
- 你可以看到每个服务的错误率
- 你可以看到每个服务的日志输出
- 你无法看到请求在链路中传递的过程

分布式追踪可以解决这个问题（通过请求头传播 trace ID），但它要求每个服务都正确地埋点并传播 trace 头。在实践中，链路中只要有一个服务没有传播 trace ID，就会破坏整个追踪。

## 重试与超时逻辑，到处重复

服务 A 调用服务 B。服务 B 超时。服务 A 应该以退避方式重试。但服务 A 还调用服务 C。同样的重试逻辑被重复了一遍。而服务 C 也有自己的依赖。

这些逻辑最终在每个服务、每种语言中以不同的方式实现，具有不同的默认值和不同的故障模式。一个由没有考虑超时的团队构建的服务，会引入一个没有超时设置的连接，导致无限挂起，从而引发级联故障。

## 金丝雀部署的流量切换

你想先把支付服务的新版本发布给 5% 的流量。使用标准的 Kubernetes Service，你通过副本数来控制：总共 20 个 Pod 中 1 个新版本 Pod = 5% 的流量。这种方式不精确，并且将发布百分比与 Pod 数量耦合在一起。

一个恰当的金丝雀部署会无论副本数多少，都精确地将 5% 的请求发送到新版本。在不引入额外基础设施的情况下做到这一点，需要在 ingress controller 或调用方服务中实现逻辑——而这两者都不是为此设计的。

## 你需要服务网格的信号

当你发现自己反复解决这些问题时，你就需要服务网格了：
- 逐个为服务添加 mTLS，却永远做不完
- 在每个服务中构建重试/超时配置
- 在故障期间两眼一抹黑，因为不知道是哪一跳在失败
- 想要金丝雀部署，却无法干净利落地实现

在小规模场景下（3–5 个服务、仅内部流量、合规要求低），纯 HTTP 加上基础日志就足够了。服务网格会增加运维复杂性——当替代方案的问题代价更高时，它才值得这份成本。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 使用 Service 连接应用](https://kubernetes.io/docs/concepts/services-networking/connect-applications-service/) -- type: docs, time: 15m

<!-- ZH_UI -->
1. 了解集群内两个服务通过明文 HTTP 通信时会发生什么——以及为什么这是个问题
2. 理解什么是 mTLS，以及为什么在每个应用中都实现它并不现实
3. 了解为什么没有埋点就很难获得请求级可见性（每条路由的延迟、错误率）
4. 理解服务网格能卸载哪些工作，从而让你的应用代码不必承担
5. 这些问题听起来很熟悉。什么才能真正解决它们？
6. 我遇到了所有这些问题的——服务间流量未加密、没有请求级指标、没有自动重试。我正在为每个服务单独添加逻辑来应对。应该有一种在基础设施层面处理这些问题的方法。
