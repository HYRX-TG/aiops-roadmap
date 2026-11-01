---
id: session-problem
title: The Session Problem
zone: scaling
edges:
  to:
    - id: shared-sessions-redis
      question: >-
        The right fix is to move sessions somewhere both servers can read. What
        does that look like?
      detail: >-
        If sessions live on a specific server, that server has to handle every
        request for that user. The real fix is to move session storage out of
        the server entirely — into a shared store that any server can read and
        write. Redis is the standard answer.
    - id: sticky-sessions-the-trap
      question: Can't I just send each user to the same server every time?
      detail: >-
        I mean, the simplest fix seems like just keeping each user on the same
        server, right? Why doesn't that work long-term?
difficulty: 1
tags:
  - sessions
  - stateless
  - load-balancer
  - sticky-sessions
  - scaling
category: concept
milestones:
  - Explain why sessions break when you add a load balancer
  - Identify where your app currently stores session data
  - Understand what 'stateless' means in the context of a web app
title_zh: "会话问题"

---


Web sessions let your app remember who a user is across multiple requests. But the way most apps store sessions by default — in files or memory on the server — breaks completely when you add a load balancer. This is one of the first things that goes wrong when people add horizontal scaling without thinking about state.

<!-- DEEP_DIVE -->

## How sessions work

When a user logs in, the server creates a session: a small data structure that records who this user is and what they're allowed to do. The server generates a random session ID, stores the session data somewhere keyed by that ID, and sends the ID to the browser as a cookie. On every subsequent request, the browser sends the cookie back, the server looks up the session by ID, and knows who the user is.

The critical question: **where does the server store the session data?**

By default, most web frameworks store sessions on the local filesystem or in memory. Flask, for example, has a server-side session extension that defaults to the filesystem. Django stores sessions in the database by default, which is actually fine for scaling — but many apps are configured to use the local filesystem for performance reasons.

## Why this breaks with a load balancer

When you have one server, local session storage works. Every request hits the same server, which has all the session data.

When you have two servers behind a load balancer, a user might log in on Server A (creating a session file on Server A's filesystem), and then their next request gets routed to Server B (which has no such file). From Server B's perspective, the session doesn't exist. The user appears logged out.

This is exactly what users experience: they log in, browse a few pages, and suddenly they're logged out. Or they add items to their cart and the items disappear. The underlying cause is always the same — their next request landed on a different server than the one that stored their session.

## The stateless requirement

This is the concrete, practical version of the "applications must be stateless" requirement from the horizontal scaling node. "Stateless" doesn't mean your app has no data — it means no unique data is stored *locally on the application server*. Session data needs to live somewhere every server can reach.

There are two main approaches:
1. **Shared session store**: move session data to a shared external system (Redis, database) that every app server reads and writes
2. **Client-side sessions**: encode the session data directly in the cookie (signed so it can't be tampered with) — there's nothing to look up on the server

Both solve the problem. The next nodes cover each approach.

<!-- RESOURCES -->

- [Flask-Session Documentation](https://flask-session.readthedocs.io/) -- type: docs, time: 10m
- [Django Sessions Framework](https://docs.djangoproject.com/en/stable/topics/http/sessions/) -- type: docs, time: 15m
- [The Twelve-Factor App - Backing Services](https://12factor.net/backing-services) -- type: article, time: 5m

<!-- ZH_SUMMARY -->
Web 会话让应用能够在多个请求之间记住用户身份。但大多数应用默认的会话存储方式——存储在服务器的文件或内存中——在加入负载均衡器后会彻底失效。这是人们在未考虑状态的情况下进行水平扩展时最先出问题的地方之一。

<!-- ZH_DEEP_DIVE -->
## 会话是如何工作的

当用户登录时，服务器会创建一个会话：一个小的数据结构，记录这个用户是谁以及他们被允许做什么。服务器生成一个随机的会话 ID，将会话数据以该 ID 为键存储在某个地方，并将该 ID 作为 cookie 发送给浏览器。在之后的每次请求中，浏览器都会把该 cookie 发回来，服务器通过 ID 查找会话，从而知道用户是谁。

关键问题：**服务器把会话数据存储在哪里？**

默认情况下，大多数 Web 框架将会话存储在本地文件系统或内存中。例如，Flask 有一个服务端会话扩展，默认使用文件系统。Django 默认将会话存储在数据库中，这对于扩展来说其实没问题——但许多应用出于性能考虑被配置为使用本地文件系统。

## 为什么这在负载均衡器下会出问题

当你只有一台服务器时，本地会话存储是可行的。每个请求都打到同一台服务器，而它拥有全部会话数据。

当你在负载均衡器后面有两台服务器时，用户可能在服务器 A 上登录（在服务器 A 的文件系统上创建了一个会话文件），然后他们的下一个请求被路由到服务器 B（服务器 B 上没有这个文件）。从服务器 B 的视角看，该会话不存在。用户看起来就是已登出状态。

这正是用户所经历的：他们登录，浏览了几个页面，然后突然就被登出了。或者他们往购物车里添加了商品，商品却消失了。底层原因始终相同——他们的下一个请求落在了与存储其会话的服务器不同的另一台服务器上。

## 无状态要求

这是水平扩展节点中“应用必须无状态”要求的具体、实践版本。“无状态”并不意味着你的应用没有数据——它意味着没有唯一数据被存储在*应用服务器本地*。会话数据需要存放在每台服务器都能访问的地方。

主要有两种方法：
1. **共享会话存储**：将会话数据迁移到共享的外部系统（Redis、数据库），每台应用服务器都对其读写
2. **客户端会话**：将会话数据直接编码在 cookie 中（经过签名，因此无法被篡改）——服务器端无需查找任何东西

两种方法都能解决问题。接下来的节点将分别介绍每种方法。

<!-- ZH_RESOURCES -->
- [Flask-Session 文档](https://flask-session.readthedocs.io/) -- 类型: 文档, 时间: 10m
- [Django Sessions 框架](https://docs.djangoproject.com/en/stable/topics/http/sessions/) -- 类型: 文档, 时间: 15m
- [十二要素应用 - 后端服务](https://12factor.net/backing-services) -- 类型: 文章, 时间: 5m

<!-- ZH_UI -->
1. 解释为什么添加负载均衡器后会话会中断
2. 确定你的应用目前在哪里存储会话数据
3. 理解在 Web 应用语境下“无状态”意味着什么
4. 正确的修复方式是把会话迁移到两台服务器都能读取的地方。那具体是什么样子？
5. 如果会话存放在特定服务器上，该服务器就必须处理该用户的所有请求。真正的修复方式是把会话存储完全移出服务器——迁移到一个任何服务器都能读写的共享存储中。Redis 是标准答案。
6. 难道我不能每次都把每个用户发送到同一台服务器吗？
7. 我的意思是，最简单的修复方式似乎就是让每个用户始终留在同一台服务器上，对吧？为什么长期来看行不通？
