---
id: apis-and-rest
title: APIs & REST
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: I have a clean API. How do I expose it to the world?
      detail: >-
        I can curl my endpoints locally and everything works. But I want someone
        on the other side of the internet to be able to hit these endpoints too
        — and I'm not sure how to get there without just punching holes in
        firewalls and hoping for the best.
difficulty: 1
tags:
  - api
  - rest
  - http
  - json
  - endpoints
  - curl
category: concept
milestones:
  - Build a REST API with proper HTTP methods and status codes
  - Test API endpoints using curl or a tool like Postman
  - 'Understand request/response format, headers, and JSON payloads'
title_zh: "API 与 REST"

---


Your Flask app returns HTML pages. That is fine for a website, but what if you also want a mobile app? Or a CLI tool? Or another service that needs your data? You do not want to build the same logic three times. An API lets you expose your backend as a service that any client can consume — browser, phone, script, or another server.

<!-- DEEP_DIVE -->

An **API (Application Programming Interface)** is a contract: "Send me this request, I will give you this response." It decouples the client (who wants data or actions) from the server (who provides them). The most common style for web APIs is **REST**.

**REST** (Representational State Transfer) uses standard HTTP methods to operate on resources:

| Method | Purpose | Example |
|--------|---------|---------|
| GET | Read data | `GET /api/users/42` — get user 42 |
| POST | Create data | `POST /api/users` — create a new user |
| PUT | Replace data | `PUT /api/users/42` — replace user 42 |
| PATCH | Update data | `PATCH /api/users/42` — update some fields |
| DELETE | Remove data | `DELETE /api/users/42` — delete user 42 |

A REST API in Flask:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
users = {}
next_id = 1

@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify(list(users.values()))

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)

@app.route("/api/users", methods=["POST"])
def create_user():
    global next_id
    data = request.json
    user = {"id": next_id, "name": data["name"], "email": data["email"]}
    users[next_id] = user
    next_id += 1
    return jsonify(user), 201

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    del users[user_id]
    return "", 204
```

**HTTP status codes** tell the client what happened:

- **200 OK** — request succeeded
- **201 Created** — new resource created
- **204 No Content** — success, nothing to return (common for DELETE)
- **400 Bad Request** — client sent invalid data
- **401 Unauthorized** — authentication required
- **403 Forbidden** — authenticated but not allowed
- **404 Not Found** — resource does not exist
- **500 Internal Server Error** — something broke on the server

Using the right status codes is important. Do not return 200 with `{"error": "not found"}` — return 404. Clients (and monitoring tools) rely on status codes.

**JSON** is the lingua franca of APIs. Requests send JSON bodies, responses return JSON. It is human-readable, every language can parse it, and it maps naturally to the objects and dictionaries your code already uses.

**Testing APIs with curl:**

```bash
# GET request
curl http://localhost:5000/api/users

# POST request with JSON body
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# DELETE request
curl -X DELETE http://localhost:5000/api/users/1
```

**Headers** carry metadata about the request and response. `Content-Type: application/json` tells the server you are sending JSON. `Authorization: Bearer <token>` sends authentication credentials. `Accept: application/json` tells the server what format you want back.

**API design principles that matter:**

- Use nouns for resources (`/api/users`), not verbs (`/api/getUsers`)
- Use plural names (`/api/users`, not `/api/user`)
- Nest related resources (`/api/users/42/orders` — orders for user 42)
- Use query parameters for filtering (`/api/users?role=admin&active=true`)
- Version your API (`/api/v1/users`) so you can evolve without breaking clients
- Return meaningful error messages with appropriate status codes

**Why SREs care:** APIs are how services communicate in any modern architecture. Monitoring API latency, error rates, and throughput (the "RED metrics" — Rate, Errors, Duration) is fundamental to SRE. When an incident happens, you need to understand which API calls are failing and why. API design also affects reliability — poorly designed APIs lead to cascading failures, retry storms, and outages.

<!-- RESOURCES -->

- [RESTful API Design Best Practices](https://restfulapi.net/) -- type: reference, time: 30m
- [HTTP Status Codes Reference](https://httpstatuses.com/) -- type: reference, time: 10m
- [Postman Learning Center](https://learning.postman.com/) -- type: tutorial, time: 1h
- [curl Tutorial](https://curl.se/docs/tutorial.html) -- type: tutorial, time: 30m

<!-- ZH_SUMMARY -->
你的 Flask 应用返回 HTML 页面。这对网站来说没问题，但如果你还想要一个移动应用呢？或者一个 CLI 工具？又或者另一个需要你数据的服务？你不会想把这套逻辑重复构建三次。API 让你可以把后端作为服务暴露出来，任何客户端都能消费——浏览器、手机、脚本或另一台服务器。

<!-- ZH_DEEP_DIVE -->
**API（应用程序编程接口）** 是一种契约：“给我发送这个请求，我就会给你这个响应。”它将客户端（需要数据或操作的一方）与服务端（提供数据或操作的一方）解耦。Web API 最常见的方式是 **REST**。

**REST**（表述性状态转移）使用标准 HTTP 方法对资源进行操作：

| 方法 | 用途 | 示例 |
|--------|---------|---------|
| GET | 读取数据 | `GET /api/users/42` — 获取用户 42 |
| POST | 创建数据 | `POST /api/users` — 创建新用户 |
| PUT | 替换数据 | `PUT /api/users/42` — 替换用户 42 |
| PATCH | 更新数据 | `PATCH /api/users/42` — 更新部分字段 |
| DELETE | 删除数据 | `DELETE /api/users/42` — 删除用户 42 |

Flask 中的 REST API：

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
users = {}
next_id = 1

@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify(list(users.values()))

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)

@app.route("/api/users", methods=["POST"])
def create_user():
    global next_id
    data = request.json
    user = {"id": next_id, "name": data["name"], "email": data["email"]}
    users[next_id] = user
    next_id += 1
    return jsonify(user), 201

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    del users[user_id]
    return "", 204
```

**HTTP 状态码**告诉客户端发生了什么：

- **200 OK** — 请求成功
- **201 Created** — 新资源已创建
- **204 No Content** — 成功，无内容返回（DELETE 常见）
- **400 Bad Request** — 客户端发送了无效数据
- **401 Unauthorized** — 需要认证
- **403 Forbidden** — 已认证但无权限
- **404 Not Found** — 资源不存在
- **500 Internal Server Error** — 服务端出错

使用正确的状态码很重要。不要返回 200 和 `{"error": "not found"}` — 应返回 404。客户端（以及监控工具）依赖状态码。

**JSON** 是 API 的通用语言。请求发送 JSON 正文，响应返回 JSON。它人类可读，每种语言都能解析，并且能自然地映射到代码中已在使用的对象和字典。

**使用 curl 测试 API：**

```bash
# GET request
curl http://localhost:5000/api/users

# POST request with JSON body
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# DELETE request
curl -X DELETE http://localhost:5000/api/users/1
```

**请求头**携带关于请求和响应的元数据。`Content-Type: application/json` 告诉服务端你正在发送 JSON。`Authorization: Bearer <token>` 发送认证凭据。`Accept: application/json` 告诉服务端你希望返回的格式。

**重要的 API 设计原则：**

- 资源使用名词（`/api/users`），而非动词（`/api/getUsers`）
- 使用复数名称（`/api/users`，而非 `/api/user`）
- 嵌套相关资源（`/api/users/42/orders` — 用户 42 的订单）
- 使用查询参数进行过滤（`/api/users?role=admin&active=true`）
- 对 API 进行版本管理（`/api/v1/users`），以便在不破坏客户端的情况下演进
- 返回有意义的错误消息和适当的状态码

**SRE 为何关注：** 在任何现代架构中，API 都是服务间通信的方式。监控 API 延迟、错误率和吞吐量（即“RED 指标”——Rate、Errors、Duration）是 SRE 的基础工作。发生故障时，你需要了解哪些 API 调用失败以及原因。API 设计也会影响可靠性——设计不良的 API 会导致级联故障、重试风暴和宕机。

<!-- ZH_RESOURCES -->
- [RESTful API 设计最佳实践](https://restfulapi.net/) -- 类型：参考，时间：30m
- [HTTP 状态码参考](https://httpstatuses.com/) -- 类型：参考，时间：10m
- [Postman 学习中心](https://learning.postman.com/) -- 类型：教程，时间：1h
- [curl 教程](https://curl.se/docs/tutorial.html) -- 类型：教程，时间：30m

<!-- ZH_UI -->
1. 使用正确的 HTTP 方法和状态码构建 REST API
2. 使用 curl 或 Postman 等工具测试 API 端点
3. 理解请求/响应格式、请求头和 JSON 载荷
4. 我的 API 已经就绪。如何将它暴露给外部世界？
5. 我在本地可以 curl 我的端点，一切正常。但我希望互联网另一端的某个人也能访问这些端点——我不确定如何在不只是打穿防火墙、碰运气的情况下实现这一点。
