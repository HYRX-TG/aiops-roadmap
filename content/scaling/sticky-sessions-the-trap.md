---
id: sticky-sessions-the-trap
title: 'Sticky Sessions: The Trap'
zone: scaling
edges:
  to:
    - id: shared-sessions-redis
      question: 'OK, sticky sessions are a dead end. What''s the right solution?'
      detail: >-
        The right fix is to stop storing sessions on the server altogether. Move
        session state to a shared external store — then any server can handle
        any request, and you have true horizontal scalability.
difficulty: 1
tags:
  - sticky-sessions
  - session-affinity
  - load-balancer
  - anti-pattern
  - scaling
category: concept
milestones:
  - Explain what sticky sessions are and how they work
  - Describe why sticky sessions break when a server dies
  - Explain why sticky sessions undermine the benefits of horizontal scaling
  - Understand why this is an anti-pattern for stateless scaling
title_zh: "粘性会话：陷阱"

---


Sticky sessions (also called session affinity) seem like an obvious fix to the session problem: if user requests always go to the same server, the session data on that server is always found. It works, but it creates new problems that are worse than the one it solves.

<!-- DEEP_DIVE -->

## How sticky sessions work

A load balancer implementing sticky sessions tracks which server each user has been assigned to, and always routes that user's requests to that server. The mechanism is usually a cookie: on the first request, the load balancer sets a cookie (like `AWSALB` on AWS ALBs) recording which backend was chosen. On every subsequent request, the load balancer reads this cookie and sends the request to the same backend.

As long as that server is running, the session problem appears solved.

## Why it's a trap

### The server dies

The most obvious failure: the server a user is "stuck to" goes down. Their next request hits the load balancer, which looks for the server named in their affinity cookie — and that server is gone. The load balancer has to pick a new server, which has no session data. The user is logged out.

With sticky sessions, a single server failure logs out every user who was pinned to it simultaneously. Instead of graceful degradation you get a sudden wave of logged-out users and a customer support flood.

### Uneven load distribution

One of the main benefits of a load balancer is distributing load evenly. Sticky sessions break this. If a small number of users happen to do very heavy work (large file uploads, complex search queries, long-running operations), those requests all pile up on whatever servers those users are pinned to. Other servers might be idle while two servers are at 100% CPU — and the load balancer can't rebalance because it's committed to the stickiness guarantee.

### Can't drain servers for deployment

Rolling deployments work by taking servers out of rotation one at a time, deploying new code, and putting them back. But with sticky sessions, "taking a server out of rotation" means all the users pinned to it get redirected and lose their sessions. You either break sessions on every deployment or you have to keep old servers running until their sessions naturally expire.

### Capacity isn't actually horizontal

With true stateless horizontal scaling, you can spin up new servers and immediately get capacity. With sticky sessions, new servers don't help existing users — they only help users who haven't been assigned a server yet. Your ability to respond to a traffic spike by adding capacity is seriously degraded.

## The bottom line

Sticky sessions are a band-aid that papers over a session architecture problem. They work well enough in low-stakes setups where you're adding a second server "just in case" and reliability isn't critical. But they don't give you real horizontal scaling, and they make your availability story worse in the scenarios that matter most (server failures).

The right fix is to make sessions genuinely shared: move them to Redis so any server can handle any request.

<!-- RESOURCES -->

- [AWS ALB Sticky Sessions Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/sticky-sessions.html) -- type: docs, time: 10m
- [Session Management Anti-Patterns - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
粘性会话（也称为会话亲和性）似乎是解决会话问题的明显方案：如果用户请求始终发往同一台服务器，那么该服务器上的会话数据就总能被找到。这确实可行，但它会带来比所解决问题更糟糕的新问题。

<!-- ZH_DEEP_DIVE -->
## 粘性会话如何工作

实现粘性会话的负载均衡器会跟踪每个用户被分配到哪台服务器，并始终将该用户的请求路由到那台服务器。其机制通常是一个 cookie：在首次请求时，负载均衡器会设置一个 cookie（例如 AWS ALB 上的 `AWSALB`），记录选择了哪个后端。在随后的每次请求中，负载均衡器读取这个 cookie，并将请求发送到同一个后端。

只要那台服务器还在运行，会话问题看起来就解决了。

## 为什么这是个陷阱

### 服务器宕机

最明显的故障：用户“粘住”的服务器宕机了。他们的下一个请求到达负载均衡器，负载均衡器查找其亲和性 cookie 中指定的服务器——而那台服务器已经不在了。负载均衡器必须选择一台新服务器，而新服务器没有会话数据。用户被登出。

使用粘性会话时，单台服务器故障会同时登出所有被固定到该服务器的用户。你得到的不是优雅降级，而是突然涌现大量被登出的用户和客服请求洪流。

### 负载分布不均

负载均衡器的主要优势之一是均匀分布负载。粘性会话破坏了这一点。如果少数用户恰好执行非常繁重的工作（大文件上传、复杂搜索查询、长时间运行的操作），这些请求会全部堆积在这些用户所固定的服务器上。其他服务器可能处于空闲状态，而两台服务器 CPU 占用率达到 100%——负载均衡器无法重新平衡，因为它必须遵守粘性保证。

### 无法为部署排空服务器

滚动部署的工作方式是逐台将服务器从轮换中移除、部署新代码，然后再放回。但使用粘性会话时，“将服务器从轮换中移除”意味着固定到它的所有用户都会被重定向并丢失会话。你要么在每次部署时破坏会话，要么必须保持旧服务器运行，直到它们的会话自然过期。

### 容量实际上不是水平扩展的

在真正的无状态水平扩展中，你可以启动新服务器并立即获得容量。使用粘性会话时，新服务器对现有用户没有帮助——它们只帮助尚未被分配服务器的用户。你通过增加容量来应对流量高峰的能力被严重削弱。

## 结论

粘性会话是一种权宜之计，掩盖了会话架构问题。在低风险场景中——你只是“以防万一”添加第二台服务器，可靠性并不关键——它们足够好用。但它们并不能给你真正的水平扩展，而且在最重要的场景（服务器故障）中，它们让你的可用性表现更糟。

正确的修复方法是让会话真正共享：将会话移到 Redis，这样任何服务器都能处理任何请求。

<!-- ZH_RESOURCES -->
- [AWS ALB 粘性会话文档](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/sticky-sessions.html) -- 类型: 文档, 时间: 10m
- [会话管理反模式 - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) -- 类型: 文章, 时间: 20m

<!-- ZH_UI -->
1. 解释什么是粘性会话以及它们如何工作
2. 描述为什么服务器宕机时粘性会话会失效
3. 解释为什么粘性会话会削弱水平扩展的优势
4. 理解为什么这对无状态扩展是一种反模式
5. 好吧，粘性会话是死路一条。正确的解决方案是什么？
6. 正确的做法是完全停止在服务器上存储会话。将会话状态迁移到共享的外部存储——这样任何服务器都能处理任何请求，你就实现了真正的水平可扩展性。
