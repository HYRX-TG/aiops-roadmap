---
id: jwt-and-cookie-sessions
title: JWT and Stateless Sessions
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - jwt
  - cookies
  - sessions
  - stateless
  - signed-cookies
  - authentication
  - security
category: concept
milestones:
  - Explain the difference between server-side sessions and client-side sessions
  - Describe how a signed cookie prevents tampering
  - Understand what JWT is and how it differs from a signed cookie
  - Know when to prefer Redis sessions over stateless tokens (and vice versa)
  - >-
    Understand what session revocation means and why it's hard with stateless
    tokens
title_zh: "JWT 与无状态会话"

---


Server-side sessions (whether stored in Redis or a database) require a round-trip to a shared store on every request to look up the session. An alternative approach is to store the session data directly in the browser — in a signed cookie or a JWT — so the server doesn't need to look anything up. Understanding the trade-offs between these approaches matters for building secure, scalable authentication.

<!-- DEEP_DIVE -->

## Signed cookies

A signed cookie stores the session data directly in the cookie value, but signs it with a secret key so the server can verify it hasn't been tampered with. Flask's default session implementation does this with HMAC-SHA1. When you set `session["user_id"] = 42`, Flask serializes that data, signs it with `SECRET_KEY`, and puts the whole thing in a cookie.

On the next request, Flask reads the cookie, verifies the signature, and if valid, trusts the data. No database lookup, no Redis call — the session data is right there in the request.

The catch: the data is readable by the client. It's base64-encoded, not encrypted. Anyone can decode the cookie value and see what's in it. You should never put sensitive data (passwords, tokens, private information) in a signed cookie. User IDs and permissions are generally fine.

## JWTs (JSON Web Tokens)

A JWT is a more standardized version of the same concept: a JSON payload signed with a secret key (HMAC) or a private key (RSA/ECDSA). JWTs are commonly used for API authentication. An API server issues a JWT on login; the client includes it in the `Authorization: Bearer <token>` header on every subsequent request; the server verifies the signature and trusts the claims.

JWTs are self-contained: the payload can include the user ID, roles, expiry, and any other claims you want to verify without a database lookup.

## The revocation problem

This is where stateless sessions have a hard trade-off. With server-side sessions, revoking a session is simple: delete it from Redis. The next request with that session ID finds nothing and the user is logged out.

With a signed cookie or JWT, you can't revoke a specific token without either:
- Maintaining a revocation list (a blocklist) — which means a database lookup on every request, eliminating the main benefit
- Rotating the secret key — which invalidates *all* tokens, logging out every user
- Using short expiry times — so stolen tokens expire quickly, but you need a refresh token mechanism

For internal services and APIs where revocation is rarely needed, JWTs are practical. For user-facing sessions where "log out all sessions" or "deactivate this account immediately" are requirements, server-side sessions in Redis are cleaner.

## When to use which

| Approach | Best for | Downside |
|---|---|---|
| Server-side sessions (Redis) | User web sessions, when instant revocation matters | Requires shared store, adds lookup latency |
| Signed cookies | Simple web apps with small session data | Not encrypted, no revocation |
| JWT | Service-to-service auth, APIs, mobile clients | Revocation is hard |

Most production e-commerce sites use server-side sessions for the logged-in user experience (because being able to force-logout a user or invalidate sessions on password change matters) and JWTs for internal API calls between services.

<!-- RESOURCES -->

- [JWT.io Introduction](https://jwt.io/introduction) -- type: article, time: 10m
- [Flask Session Security](https://flask.palletsprojects.com/en/stable/security/#set-cookie-options) -- type: docs, time: 10m
- [Stop Using JWTs for Sessions (Joël Franusic)](https://dev.to/rdegges/please-stop-using-local-storage-1i04) -- type: article, time: 10m
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
服务端会话（无论存储在 Redis 还是数据库中）都需要在每次请求时往返访问共享存储来查找会话。另一种方法是将会话数据直接存储在浏览器中——存放在签名 cookie 或 JWT 中——这样服务器就无需进行任何查找。理解这些方法之间的权衡，对于构建安全、可扩展的身份认证至关重要。

<!-- ZH_DEEP_DIVE -->
## 签名 Cookie

签名 Cookie 将会话数据直接存储在 Cookie 值中，但使用密钥对其进行签名，以便服务器可以验证它未被篡改。Flask 的默认会话实现使用 HMAC-SHA1 来实现这一点。当你设置 `session["user_id"] = 42` 时，Flask 会序列化该数据，用 `SECRET_KEY` 对其进行签名，并将整个内容放入 Cookie 中。

在下一次请求时，Flask 读取 Cookie，验证签名，如果有效，则信任该数据。无需数据库查询，无需 Redis 调用——会话数据就在请求中。

问题在于：数据对客户端是可读的。它是 base64 编码的，而非加密的。任何人都可以解码 Cookie 值并查看其中的内容。你绝不应将敏感数据（密码、令牌、私人信息）放入签名 Cookie 中。用户 ID 和权限通常没有问题。

## JWT（JSON Web Token）

JWT 是同一概念的更标准化版本：一个用密钥（HMAC）或私钥（RSA/ECDSA）签名的 JSON 载荷。JWT 通常用于 API 认证。API 服务器在登录时签发 JWT；客户端在后续每次请求中将其包含在 `Authorization: Bearer <token>` 头中；服务器验证签名并信任其中的声明。

JWT 是自包含的：载荷可以包含用户 ID、角色、过期时间以及你希望在不查询数据库的情况下验证的任何其他声明。

## 撤销问题

这正是无状态会话面临艰难权衡的地方。对于服务端会话，撤销会话很简单：从 Redis 中删除它。下一次携带该会话 ID 的请求将找不到任何内容，用户即被登出。

对于签名 Cookie 或 JWT，你无法撤销特定令牌，除非：
- 维护一个撤销列表（黑名单）——这意味着每次请求都要查询数据库，从而消除了主要优势
- 轮换密钥——这会使*所有*令牌失效，登出每一个用户
- 使用较短的过期时间——这样被盗令牌会很快过期，但你需要一个刷新令牌机制

对于很少需要撤销的内部服务和 API，JWT 是实用的。对于面向用户的会话，如果“登出所有会话”或“立即停用此账户”是需求，那么 Redis 中的服务端会话更为清晰。

## 何时使用哪种

| 方案 | 最适合 | 缺点 |
|---|---|---|
| 服务端会话（Redis） | 用户 Web 会话，当即时撤销很重要时 | 需要共享存储，增加查询延迟 |
| 签名 Cookie | 会话数据较小的简单 Web 应用 | 未加密，无法撤销 |
| JWT | 服务间认证、API、移动客户端 | 撤销困难 |

大多数生产环境的电子商务网站对已登录用户的体验使用服务端会话（因为能够强制登出用户或在密码更改时使会话失效很重要），而在服务之间的内部 API 调用中使用 JWT。

<!-- ZH_RESOURCES -->
- [JWT.io 简介](https://jwt.io/introduction) -- 类型: 文章, 时间: 10m
- [Flask Session 安全](https://flask.palletsprojects.com/en/stable/security/#set-cookie-options) -- 类型: 文档, 时间: 10m
- [停止使用 JWT 做会话 (Joël Franusic)](https://dev.to/rdegges/please-stop-using-local-storage-1i04) -- 类型: 文章, 时间: 10m
- [OWASP 会话管理速查表](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) -- 类型: 文章, 时间: 20m

<!-- ZH_UI -->
1. 解释服务端会话与客户端会话的区别
2. 描述签名 cookie 如何防止篡改
3. 理解什么是 JWT 以及它与签名 cookie 的区别
4. 了解何时优先使用 Redis 会话而非无状态令牌（以及反之）
5. 理解会话撤销的含义以及为什么无状态令牌难以实现
