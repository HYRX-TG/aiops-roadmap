---
id: authentication-basics
title: Authentication Basics
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: >-
        Auth is working. Now how do I get this whole thing — app, database,
        login and all — running somewhere other people can reach?
      detail: >-
        I've got users, sessions, login, logout. It works on localhost. But
        I have no idea how to get this running on a real server where other
        people can actually use it. And I'm a little nervous about whether
        the auth is even secure enough for that.
difficulty: 2
tags:
  - authentication
  - sessions
  - tokens
  - jwt
  - oauth
  - cookies
  - security
category: concept
milestones:
  - Explain the difference between authentication and authorization
  - Implement session-based login with cookies in a web app
  - Understand how tokens (JWT) work and when to use them instead of sessions
  - Know what OAuth is and why "Sign in with Google" exists
title_zh: "认证基础"

---


Right now, anyone who visits your app can do anything. There's no concept of "who are you?" and no way to show different things to different people. Authentication is how your app verifies identity — confirming that a user is who they claim to be. It's one of the first things you need the moment your app has any concept of user data, personal content, or restricted actions.

<!-- DEEP_DIVE -->

## Sessions and cookies

The most common way to handle auth in a web app is session-based authentication. The flow is straightforward:

1. User submits their email and password
2. Server checks the credentials against the database
3. Server creates a **session** — a record that says "this person is logged in" — and stores it (in memory, a database, or Redis)
4. Server sends back a **cookie** containing the session ID
5. On every subsequent request, the browser automatically sends the cookie, and the server looks up the session to know who's making the request

The session lives on the server. The cookie is just a pointer to it. When the user logs out, the server deletes the session.

This works well for traditional web apps where the server renders HTML. The browser handles cookies automatically — no JavaScript required.

## Tokens and JWTs

Token-based auth works differently. Instead of storing a session on the server, the server creates a **token** — a signed blob of data that contains the user's identity — and sends it to the client. The client stores it (usually in localStorage or a cookie) and sends it with every request.

**JSON Web Tokens (JWTs)** are the standard format. A JWT has three parts: a header, a payload (containing claims like `user_id: 42, role: admin`), and a cryptographic signature. The server can verify the signature without looking anything up — the token itself contains all the information needed.

The tradeoff: sessions require server-side storage but are easy to revoke (just delete the session). JWTs require no server-side storage but are hard to revoke (the token is valid until it expires). In practice, most apps use short-lived JWTs with refresh tokens to get the best of both.

## OAuth and "Sign in with Google"

OAuth solves a different problem: letting users log in to your app using an account they already have (Google, GitHub, etc.) without giving you their password. The flow involves redirecting the user to the provider, the provider confirming their identity, and sending your app a token that proves who they are.

You don't implement OAuth from scratch — you use a library. But understanding what's happening underneath matters because OAuth-related failures (expired tokens, misconfigured redirect URIs, provider outages) are common incidents you'll deal with later.

## Authentication vs authorization

Authentication asks "who are you?" Authorization asks "what are you allowed to do?" They're different concerns. A user can be authenticated (logged in) but not authorized (not an admin). Most apps need both, and confusing them leads to security bugs.

<!-- RESOURCES -->

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) -- type: reference, time: 30m
- [JWT.io — Introduction to JWTs](https://jwt.io/introduction) -- type: guide, time: 15m
- [OAuth 2.0 Simplified — Aaron Parecki](https://www.oauth.com/) -- type: guide, time: 1h

<!-- ZH_SUMMARY -->
目前，任何访问你应用的人都能做任何事。这里没有“你是谁？”的概念，也无法向不同的人展示不同的内容。身份验证是你的应用验证身份的方式——确认用户就是他们声称的那个人。一旦你的应用涉及任何用户数据、个人内容或受限操作的概念，这就是你首先需要的东西之一。

<!-- ZH_DEEP_DIVE -->
## 会话与 Cookie

在 Web 应用中处理认证最常见的方式是基于会话的认证。流程很直接：

1. 用户提交邮箱和密码
2. 服务器对照数据库校验凭据
3. 服务器创建一个**会话**——一条表示“此人已登录”的记录——并将其存储起来（内存、数据库或 Redis 中）
4. 服务器返回一个包含会话 ID 的 **Cookie**
5. 之后每个请求，浏览器都会自动发送该 Cookie，服务器查找会话以确定是谁在发起请求

会话存在于服务器上。Cookie 只是指向它的一个指针。用户登出时，服务器删除该会话。

这对于由服务器渲染 HTML 的传统 Web 应用很有效。浏览器会自动处理 Cookie——无需 JavaScript。

## 令牌与 JWT

基于令牌的认证工作方式不同。服务器不在服务端存储会话，而是创建一个**令牌**——一段包含用户身份、经过签名的数据——并发送给客户端。客户端将其存储起来（通常放在 localStorage 或 Cookie 中），并在每次请求时发送。

**JSON Web Token（JWT）** 是标准格式。一个 JWT 包含三部分：头部、载荷（包含诸如 `user_id: 42, role: admin` 之类的声明）以及加密签名。服务器无需查询任何东西即可验证签名——令牌本身包含了所需的全部信息。

权衡之处：会话需要服务端存储，但易于撤销（只需删除会话）。JWT 无需服务端存储，但难以撤销（令牌在过期前一直有效）。实践中，大多数应用使用短时效的 JWT 配合刷新令牌，以兼得两者之长。

## OAuth 与“使用 Google 登录”

OAuth 解决的是另一个问题：让用户使用他们已有的账号（Google、GitHub 等）登录你的应用，而无需把密码交给你。流程包括将用户重定向到提供方，由提供方确认其身份，并向你的应用发送一个能证明其身份的令牌。

你不需要从零实现 OAuth——使用一个库即可。但理解底层发生了什么很重要，因为与 OAuth 相关的故障（令牌过期、重定向 URI 配置错误、提供方服务中断）是你日后会经常处理的常见事故。

## 认证与授权

认证问的是“你是谁？”授权问的是“你被允许做什么？”它们是不同的关注点。一个用户可以已认证（已登录）但未获授权（不是管理员）。大多数应用两者都需要，而将它们混为一谈会导致安全漏洞。

<!-- ZH_RESOURCES -->
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) -- 类型: 参考, 时间: 30m
- [JWT.io — Introduction to JWTs](https://jwt.io/introduction) -- 类型: 指南, 时间: 15m
- [OAuth 2.0 Simplified — Aaron Parecki](https://www.oauth.com/) -- 类型: 指南, 时间: 1h

<!-- ZH_UI -->
1. 解释认证与授权的区别
2. 在 Web 应用中用 Cookie 实现基于会话的登录
3. 理解令牌（JWT）的工作原理，以及何时应使用令牌而非会话
4. 了解什么是 OAuth，以及“使用 Google 登录”为何存在
5. 认证已经能用了。现在我要怎么把整个东西——应用、数据库、登录等等——部署到别人能访问的地方？
6. 我已经有了用户、会话、登录、登出。在 localhost 上能跑。但我完全不知道该怎么把它跑在真实服务器上让别人真正用起来。而且我有点担心认证是否足够安全、能不能撑住这个场景。
