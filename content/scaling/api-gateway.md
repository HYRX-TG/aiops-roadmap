---
id: api-gateway
title: API Gateways
zone: scaling
edges:
  to:
    - id: waf
      question: The gateway handles routing and auth centrally. But I'm seeing malicious traffic — SQL injection attempts, bots scanning for vulnerabilities. What do I put in front to block that?
      detail: >-
        The API gateway takes care of legitimate cross-cutting concerns. But
        it's not designed to inspect request payloads for attack patterns. I
        need something that understands HTTP deeply enough to distinguish a
        valid request from an exploit attempt.
difficulty: 2
tags:
  - api-gateway
  - kong
  - aws-api-gateway
  - nginx
  - reverse-proxy
  - routing
  - authentication
  - rate-limiting
category: concept
milestones:
  - Explain what an API gateway does that a plain reverse proxy does not
  - Know what Kong is and what its plugins handle (auth, rate limiting, logging)
  - Understand when AWS API Gateway (managed) beats self-hosted Kong
  - Explain the trade-off between centralising logic in a gateway vs keeping it in services
  - Know what request/response transformation is and when you need it
title_zh: "API 网关"

---


As a system grows from one service into many, you end up implementing the same cross-cutting concerns in every service: authenticate the request, check the rate limit, log it, route it to the right backend. An API gateway centralizes these concerns — it's a single entry point that handles the common stuff before passing requests to your services. Every service behind it is simpler because it doesn't have to implement auth or throttling itself.

<!-- DEEP_DIVE -->

## What an API gateway adds over a plain reverse proxy

A plain reverse proxy (Nginx, HAProxy) forwards requests to backends. An API gateway does that plus:

- **Authentication and authorization**: verify JWTs, check API keys, validate OAuth tokens before the request ever reaches a service. Services trust that if a request arrives, it's already been authenticated.
- **Rate limiting**: enforce per-API-key or per-user rate limits centrally. Every service gets rate limiting automatically without any code.
- **Request/response transformation**: rewrite headers, reshape request bodies, aggregate responses from multiple backends into one.
- **Logging and observability**: capture request/response metadata at the gateway — latency, status codes, API key used — in a consistent format across all services.
- **API versioning and routing**: route `/api/v1/products` to one backend and `/api/v2/products` to another.

## Kong

Kong is an open-source API gateway built on top of Nginx. It's configured through a REST API (or declarative config files) and extended with plugins. Built-in plugins cover auth (JWT, API key, OAuth2), rate limiting, request transformation, logging (to Datadog, Kafka, etc.), and more.

Deploying Kong means running the Kong process (and its config database, typically Postgres) in front of your services. Each service is configured as an "upstream" with routes that define which URLs map to it.

```yaml
# kong.yaml (declarative config)
services:
  - name: product-service
    url: http://product-service.internal:8080
    routes:
      - name: products-route
        paths: ["/api/products"]
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 1000
```

## AWS API Gateway

AWS API Gateway is a fully managed alternative. You define your API in the AWS console or via CloudFormation/Terraform, and AWS handles scaling, availability, and operations. It integrates natively with AWS Lambda (for serverless backends), ECS, and HTTP endpoints.

The managed option is simpler operationally — no Kong cluster to run — but less flexible for complex routing logic. AWS API Gateway also supports WebSockets and HTTP/2.

Cost: AWS API Gateway charges per API call, which can get expensive at high throughput. Self-hosted Kong has no per-request cost (just the EC2 instances running it).

## When a gateway makes sense — and when it doesn't

**Makes sense**: you have multiple services (2+) sharing auth logic, rate limits, or routing rules. The overhead of a gateway is justified by eliminating repeated implementation across services.

**Might not make sense**: a single monolith with one API. The added latency hop (typically 1-5ms) and operational complexity of a gateway isn't worth it for routing to one service. Your load balancer is sufficient.

## The trade-off: centralized logic

Centralizing auth and rate limiting in the gateway is convenient — but it makes the gateway a critical path dependency. If the gateway has a bug or misconfiguration, every API call is affected. Keep gateway logic minimal and service-agnostic; anything service-specific should stay in the service.

<!-- RESOURCES -->

- [Kong Documentation](https://docs.konghq.com/) -- type: docs, time: 30m
- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html) -- type: docs, time: 20m
- [API Gateway Pattern - Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/microservices/design/gateway) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
当系统从一个服务发展为多个服务时，你最终会在每个服务中实现相同的横切关注点：认证请求、检查速率限制、记录日志、将其路由到正确的后端。API 网关将这些关注点集中化——它是一个单一入口点，在将请求传递给你的服务之前处理这些通用事项。它背后的每个服务都变得更简单，因为它不必自己实现认证或限流。

<!-- ZH_DEEP_DIVE -->
## API 网关相比普通反向代理增加了什么

普通反向代理（Nginx、HAProxy）将请求转发到后端。API 网关在此基础上还提供：

- **身份认证与授权**：在请求到达服务之前验证 JWT、检查 API key、校验 OAuth token。服务可以信任：只要请求到达，就已经通过了认证。
- **限流**：集中实施按 API key 或按用户的限流。每个服务无需任何代码即可自动获得限流能力。
- **请求/响应转换**：重写 header、重塑请求体、将多个后端的响应聚合为一个。
- **日志与可观测性**：在网关处捕获请求/响应元数据——延迟、状态码、使用的 API key——并以一致的格式覆盖所有服务。
- **API 版本管理与路由**：将 `/api/v1/products` 路由到一个后端，将 `/api/v2/products` 路由到另一个后端。

## Kong

Kong 是一个构建在 Nginx 之上的开源 API 网关。它通过 REST API（或声明式配置文件）进行配置，并通过插件进行扩展。内置插件涵盖认证（JWT、API key、OAuth2）、限流、请求转换、日志（输出到 Datadog、Kafka 等）等。

部署 Kong 意味着在你的服务前面运行 Kong 进程（及其配置数据库，通常是 Postgres）。每个服务都配置为一个“upstream”，并通过路由定义哪些 URL 映射到它。

```yaml
# kong.yaml (declarative config)
services:
  - name: product-service
    url: http://product-service.internal:8080
    routes:
      - name: products-route
        paths: ["/api/products"]
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 1000
```

## AWS API Gateway

AWS API Gateway 是一个全托管的替代方案。你在 AWS 控制台中或通过 CloudFormation/Terraform 定义 API，AWS 负责处理扩缩容、可用性和运维。它与 AWS Lambda（用于无服务器后端）、ECS 和 HTTP 端点原生集成。

托管方案在运维上更简单——无需运行 Kong 集群——但在复杂路由逻辑方面灵活性较低。AWS API Gateway 还支持 WebSockets 和 HTTP/2。

成本：AWS API Gateway 按 API 调用次数收费，在高吞吐量下可能变得昂贵。自托管的 Kong 没有按请求计费的成本（只有运行它的 EC2 实例成本）。

## 网关何时有意义——何时没有

**有意义**：你有多个服务（2 个以上）共享认证逻辑、限流或路由规则。网关的额外开销是合理的，因为它消除了各服务中重复的实现。

**可能没有意义**：只有一个 API 的单一单体应用。对于路由到一个服务而言，网关增加的延迟跳数（通常 1-5ms）和运维复杂性并不值得。你的负载均衡器已经足够。

## 权衡：集中式逻辑

将认证和限流集中在网关中很方便——但这使网关成为关键路径上的依赖。如果网关有 bug 或配置错误，每个 API 调用都会受到影响。保持网关逻辑最小化且与服务无关；任何服务特定的内容都应留在服务内部。

<!-- ZH_RESOURCES -->
- [Kong 文档](https://docs.konghq.com/) -- 类型：文档，时长：30m
- [AWS API Gateway 文档](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html) -- 类型：文档，时长：20m
- [API 网关模式 - Microsoft Azure 架构中心](https://learn.microsoft.com/en-us/azure/architecture/microservices/design/gateway) -- 类型：文章，时长：15m

<!-- ZH_UI -->
1. 解释 API 网关相比普通反向代理多做了什么
2. 了解 Kong 是什么，以及它的插件处理哪些事情（认证、限流、日志）
3. 理解 AWS API Gateway（托管）何时优于自托管 Kong
4. 解释将逻辑集中到网关与保留在服务中之间的权衡
5. 了解什么是请求/响应转换，以及何时需要它
6. 网关集中处理路由和认证。但我看到恶意流量——SQL 注入尝试、扫描漏洞的机器人。我该在前面放什么来拦截？
7. API 网关负责合法的横切关注点。但它并非为检查请求载荷中的攻击模式而设计。我需要一个足够深入理解 HTTP 的东西，能区分合法请求和漏洞利用尝试。
