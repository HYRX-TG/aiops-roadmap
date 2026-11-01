---
id: rate-limiting
title: Rate Limiting
zone: scaling
edges:
  to:
    - id: api-gateway
      question: Rate limiting is protecting the API. But I keep implementing the same auth, routing, and throttling logic in every service — is there a better way?
      detail: >-
        Every new service I build has the same cross-cutting concerns: check
        the token, enforce rate limits, route the request, log it. It's
        duplicated in every repo. I've heard there's something that sits in
        front of everything and handles this centrally — what is it?
difficulty: 2
tags:
  - rate-limiting
  - throttling
  - api
  - protection
  - nginx
  - token-bucket
  - leaky-bucket
  - redis
category: concept
milestones:
  - Explain the difference between a token bucket and a leaky bucket
  - Implement rate limiting at the Nginx level
  - Understand per-IP vs per-user vs per-API-key limits
  - Know what a 429 response is and what Retry-After communicates
  - Explain the thundering herd problem and how rate limits help
  - Know how Redis enables distributed rate limiting across multiple servers
title_zh: "限流"

---


A load balancer distributes legitimate traffic efficiently. But it distributes malicious traffic equally well. Bots scraping your product catalog, API clients in retry loops with exponential-backoff disabled, or a single user hammering your search endpoint thousands of times per minute — all of these get routed to your servers and count against your capacity. Rate limiting throttles clients before they overwhelm your backend.

<!-- DEEP_DIVE -->

## What rate limiting does

Rate limiting enforces a maximum request rate per client — per IP address, per API key, per authenticated user, or some combination. When a client exceeds the limit, the server returns `429 Too Many Requests` with a `Retry-After` header indicating when they can try again.

Clients who stay within limits are unaffected. Clients who exceed limits are throttled. The legitimate majority of your users are protected from the bad behavior of a few.

## Token bucket and leaky bucket

Two classic algorithms for rate limiting:

**Token bucket**: a bucket holds up to N tokens. Tokens refill at a fixed rate. Each request consumes one token. If the bucket is empty, the request is rejected. This allows short bursts (if the bucket is full) while enforcing an average rate over time.

**Leaky bucket**: requests enter a queue (the bucket). The queue drains at a fixed rate — one request processed every X milliseconds. If the queue is full, new requests are rejected. This enforces a strict constant output rate with no bursting.

Token bucket is more common for API rate limiting because it allows bursting, which is friendlier to legitimate clients that might make a few quick requests in succession.

## Implementing rate limiting in Nginx

Nginx has built-in rate limiting with `limit_req`:

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_req_status 429;
            proxy_pass http://backend;
        }
    }
}
```

This limits each IP to 10 requests/second, allows a burst of 20, and returns 429 when exceeded. `$binary_remote_addr` is the client IP. This state is stored in shared memory (`zone=api:10m` — 10 MB, enough for ~160,000 IPs).

## Per-user limits in distributed systems

IP-based limiting works for unauthenticated traffic but breaks down in several ways:
- Legitimate users behind a NAT (corporate network, VPN) all share one IP
- API clients rotate IPs
- Authenticated users should have their own limit regardless of IP

For per-user or per-API-key rate limiting across multiple servers, the limit state needs to be shared. Redis is the standard solution: increment a counter key per user per time window, and check whether it exceeds the limit. Multiple servers share the same Redis counter.

```python
def is_rate_limited(user_id):
    key = f"rate:user:{user_id}:{int(time.time() // 60)}"  # per-minute window
    count = redis.incr(key)
    redis.expire(key, 120)  # expire after 2 windows
    return count > 100  # 100 requests per minute limit
```

## Responding correctly

A proper rate limit response:
- HTTP status `429 Too Many Requests`
- `Retry-After: 30` header (seconds until they can try again, or an HTTP-date)
- `X-RateLimit-Limit: 100` — their limit
- `X-RateLimit-Remaining: 0` — requests left in this window
- `X-RateLimit-Reset: 1680000000` — Unix timestamp when the window resets

Good clients (and yours should be one) respect `Retry-After` and back off automatically. Bad clients ignore it — they're the ones the rate limit is designed to stop anyway.

## The thundering herd problem

When many clients hit a rate limit simultaneously and all receive the same `Retry-After` value, they all retry at exactly the same time — causing another spike. Add jitter: randomize the `Retry-After` value by a few seconds so retries are spread out.

<!-- RESOURCES -->

- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/) -- type: article, time: 15m
- [Redis Rate Limiting Patterns](https://redis.io/docs/manual/patterns/rate-limiting/) -- type: docs, time: 10m
- [HTTP 429 - IANA](https://httpwg.org/specs/rfc6585.html#status-429) -- type: article, time: 5m
- [An Introduction to Rate Limiting - Stripe Engineering](https://stripe.com/blog/rate-limiters) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
负载均衡器能高效分发合法流量，但同样也会均匀分发恶意流量。抓取产品目录的机器人、禁用指数退避而陷入重试循环的 API 客户端，或者单个用户每分钟数千次猛击搜索端点——这些请求都会被路由到你的服务器并占用你的容量。限流会在客户端压垮后端之前对其进行节流。

<!-- ZH_DEEP_DIVE -->
## 限流的作用

限流会针对每个客户端强制执行最大请求速率——按 IP 地址、按 API key、按已认证用户，或按这些条件的某种组合。当客户端超过限制时，服务器会返回 `429 Too Many Requests`，并附带 `Retry-After` 响应头，指示客户端何时可以重试。

未超过限制的客户端不受影响。超过限制的客户端会被限流。你的绝大多数合法用户因此不会受到少数不良行为的影响。

## 令牌桶与漏桶

两种经典的限流算法：

**令牌桶**：桶中最多存放 N 个令牌。令牌以固定速率补充。每个请求消耗一个令牌。如果桶为空，请求会被拒绝。这允许短时突发（当桶满时），同时对长期平均速率进行限制。

**漏桶**：请求进入一个队列（即桶）。队列以固定速率排空——每 X 毫秒处理一个请求。如果队列已满，新请求会被拒绝。这会强制输出速率严格恒定，不允许突发。

令牌桶在 API 限流中更常见，因为它允许突发，这对可能连续发起几个快速请求的合法客户端更友好。

## 在 Nginx 中实现限流

Nginx 通过 `limit_req` 内置了限流功能：

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_req_status 429;
            proxy_pass http://backend;
        }
    }
}
```

这将每个 IP 限制为每秒 10 个请求，允许 20 个请求的突发，超过时返回 429。`$binary_remote_addr` 是客户端 IP。该状态存储在共享内存中（`zone=api:10m`——10 MB，足以容纳约 160,000 个 IP）。

## 分布式系统中的按用户限流

基于 IP 的限流适用于未认证流量，但在以下几种情况下会失效：
- 位于 NAT 之后（企业网络、VPN）的合法用户共享同一个 IP
- API 客户端会轮换 IP
- 已认证用户应当拥有自己的限制，而不受 IP 影响

要在多台服务器上实现按用户或按 API key 的限流，限制状态需要共享。Redis 是标准解决方案：按用户、按时间窗口递增计数器 key，并检查是否超过限制。多台服务器共享同一个 Redis 计数器。

```python
def is_rate_limited(user_id):
    key = f"rate:user:{user_id}:{int(time.time() // 60)}"  # per-minute window
    count = redis.incr(key)
    redis.expire(key, 120)  # expire after 2 windows
    return count > 100  # 100 requests per minute limit
```

## 正确响应

规范的限流响应：
- HTTP 状态码 `429 Too Many Requests`
- `Retry-After: 30` 响应头（表示多少秒后可以重试，或一个 HTTP 日期）
- `X-RateLimit-Limit: 100`——其限制额度
- `X-RateLimit-Remaining: 0`——当前窗口剩余的请求数
- `X-RateLimit-Reset: 1680000000`——窗口重置的 Unix 时间戳

好的客户端（你的客户端也应当如此）会遵守 `Retry-After` 并自动退避。差的客户端会忽略它——它们正是限流机制要拦截的对象。

## 惊群问题

当许多客户端同时触达限流阈值，并且都收到相同的 `Retry-After` 值时，它们会在完全相同的时间重试——从而引发又一次流量尖峰。加入抖动：将 `Retry-After` 值随机偏移几秒，使重试分散开来。

<!-- ZH_RESOURCES -->
- [Nginx 限流](https://www.nginx.com/blog/rate-limiting-nginx/) -- 类型: 文章, 时长: 15m
- [Redis 限流模式](https://redis.io/docs/manual/patterns/rate-limiting/) -- 类型: 文档, 时长: 10m
- [HTTP 429 - IANA](https://httpwg.org/specs/rfc6585.html#status-429) -- 类型: 文章, 时长: 5m
- [限流简介 - Stripe Engineering](https://stripe.com/blog/rate-limiters) -- 类型: 文章, 时长: 15m

<!-- ZH_UI -->
1. 解释令牌桶与漏桶的区别
2. 在 Nginx 层面实现限流
3. 理解按 IP、按用户、按 API key 限流的区别
4. 了解 429 响应是什么，以及 Retry-After 传达什么信息
5. 解释惊群问题以及限流如何缓解它
6. 了解 Redis 如何实现跨多台服务器的分布式限流
7. 限流是在保护 API。但我在每个服务里都重复实现相同的认证、路由和限流逻辑——有没有更好的办法？
8. 我构建的每个新服务都有相同的横切关注点：校验 token、执行限流、路由请求、记录日志。每个仓库里都在重复。我听说有东西可以挡在所有服务前面集中处理这些——那是什么？
