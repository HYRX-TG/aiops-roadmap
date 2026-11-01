---
id: http-protocol
title: 'HTTP: How Browsers Talk to Servers'
zone: networking
edges:
  to:
    - id: where-do-i-run-this
      zone: running
      question: I understand HTTP. But where do I actually run my app for real users?
      detail: >-
        My app works on localhost and I can curl it. But I need it somewhere
        permanently accessible — not my laptop, not a local port. Where do you
        actually put something you want real users to be able to reach?
    - id: encryption-basics
      question: HTTP is plaintext. Can anyone read my traffic?
      detail: >-
        I just realized my login form is sending usernames and passwords in
        plain text over the network. Anyone watching the traffic could read
        them. How does HTTPS actually prevent that?
difficulty: 1
tags:
  - http
  - https
  - protocol
  - status-codes
  - methods
  - curl
  - application-layer
category: concept
milestones:
  - Understand the HTTP request-response cycle with methods and status codes
  - 'Use curl to make GET, POST, PUT, and DELETE requests'
  - Read and understand HTTP headers in browser dev tools
title_zh: "HTTP：浏览器如何与服务器通信"

---


Your web server is running and your phone can load the page. But what is actually happening? The browser is not just "connecting" — it is speaking a very specific language called HTTP. It sends a structured request, the server sends a structured response, and both sides know exactly what to expect because they follow the same protocol.

<!-- DEEP_DIVE -->

**HTTP** (Hypertext Transfer Protocol) is an **application layer** protocol. It sits on top of TCP — TCP handles the reliable delivery of bytes, and HTTP defines what those bytes mean. When you type a URL into your browser, here is what happens:

1. The browser opens a TCP connection to the server (port 80 for HTTP, 443 for HTTPS)
2. The browser sends an **HTTP request**
3. The server processes the request and sends back an **HTTP response**
4. The browser renders the response

An HTTP request looks like this:

```
GET /products HTTP/1.1
Host: 192.168.1.42:5000
Accept: text/html
User-Agent: Mozilla/5.0
```

The first line is the **request line**: the method (`GET`), the path (`/products`), and the HTTP version. The following lines are **headers** — metadata about the request. Then optionally a **body** (for POST/PUT requests).

**HTTP Methods** define what you want to do:

| Method | Purpose | Has Body? | Example |
|--------|---------|-----------|---------|
| **GET** | Retrieve data | No | Load a webpage, fetch an API response |
| **POST** | Send data to create something | Yes | Submit a form, create a user |
| **PUT** | Replace an existing resource | Yes | Update a user profile entirely |
| **PATCH** | Partially update a resource | Yes | Change just the email address |
| **DELETE** | Remove a resource | Usually no | Delete an account |
| **HEAD** | Same as GET but response has no body | No | Check if a resource exists |

**HTTP Status Codes** are the server's response — a three-digit number that tells the client what happened:

```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 42

{"id": 1, "name": "Widget", "price": 10}
```

The major categories:
- **2xx — Success:** `200 OK` (here is your data), `201 Created` (new resource made), `204 No Content` (done, nothing to return)
- **3xx — Redirect:** `301 Moved Permanently` (use this new URL forever), `302 Found` (temporarily use this other URL), `304 Not Modified` (use your cached version)
- **4xx — Client error:** `400 Bad Request` (your request is malformed), `401 Unauthorized` (who are you?), `403 Forbidden` (I know who you are, but no), `404 Not Found` (that does not exist), `429 Too Many Requests` (slow down)
- **5xx — Server error:** `500 Internal Server Error` (something broke), `502 Bad Gateway` (the upstream server failed), `503 Service Unavailable` (server is overloaded or down), `504 Gateway Timeout` (upstream took too long)

**curl** is the command-line tool for making HTTP requests. It is the Swiss Army knife of networking and every SRE uses it daily:

```bash
# Simple GET request
curl http://192.168.1.42:5000/products

# See the full request and response headers
curl -v http://192.168.1.42:5000/products

# POST with JSON body
curl -X POST http://192.168.1.42:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Just get the status code
curl -o /dev/null -s -w "%{http_code}" http://192.168.1.42:5000/health

# PUT request
curl -X PUT http://192.168.1.42:5000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com"}'

# DELETE request
curl -X DELETE http://192.168.1.42:5000/api/users/1

# Follow redirects
curl -L http://example.com
```

The `-v` (verbose) flag is your best friend when debugging. It shows you exactly what is being sent and received — every header, every status code, the full conversation between client and server.

**The application layer** is the top of the networking stack. The model looks like this:

| Layer | Protocol | What it does |
|-------|----------|--------------|
| Application | HTTP, DNS, SMTP | Defines the meaning of the communication |
| Transport | TCP, UDP | Reliable (or fast) delivery of data |
| Network | IP | Addressing and routing between networks |
| Link | Ethernet, WiFi | Physical transmission between devices |

HTTP does not care how TCP delivers the bytes. TCP does not care what the bytes mean. Each layer does one job and trusts the layer below it. This is why you can run HTTP over WiFi, Ethernet, cellular, or satellite — HTTP speaks TCP, and TCP works on anything.

**Headers** carry important metadata. Some you will see constantly:

- `Content-Type: application/json` — the body is JSON
- `Authorization: Bearer eyJ...` — authentication token
- `Cache-Control: max-age=3600` — cache this for an hour
- `X-Request-ID: abc-123` — unique ID for tracing requests through systems
- `User-Agent: curl/7.68.0` — what client made the request

One important thing to notice: **HTTP is plaintext**. Every request and response — including passwords, cookies, personal data — travels across the network as readable text. Run `curl -v` and you can see every byte. Anyone between you and the server (the WiFi operator, your ISP, any router along the way) can read it all. This is a serious problem, and solving it requires encryption — which is a topic on its own.

<!-- RESOURCES -->

- [MDN - An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) -- type: reference, time: 20m
- [HTTP Status Codes Reference](https://httpstatuses.com/) -- type: reference, time: 10m
- [curl Tutorial](https://curl.se/docs/tutorial.html) -- type: tutorial, time: 30m
- [Julia Evans - HTTP Zine](https://wizardzines.com/zines/http/) -- type: zine, time: 15m
- [Everything curl (free book)](https://everything.curl.dev/) -- type: book, time: varies

<!-- ZH_SUMMARY -->
你的 Web 服务器正在运行，你的手机也能加载页面。但实际发生了什么？浏览器并不只是“连接”而已——它正在使用一种非常特定的语言，叫做 HTTP。它发送结构化的请求，服务器返回结构化的响应，双方都确切知道该期待什么，因为它们遵循相同的协议。

<!-- ZH_DEEP_DIVE -->
**HTTP**（超文本传输协议）是一种**应用层**协议。它运行在 TCP 之上——TCP 负责字节的可靠传输，而 HTTP 定义这些字节的含义。当你在浏览器中输入一个 URL 时，会发生以下过程：

1. 浏览器向服务器打开一个 TCP 连接（HTTP 使用端口 80，HTTPS 使用端口 443）
2. 浏览器发送一个 **HTTP 请求**
3. 服务器处理请求并返回一个 **HTTP 响应**
4. 浏览器渲染响应内容

一个 HTTP 请求看起来像这样：

```
GET /products HTTP/1.1
Host: 192.168.1.42:5000
Accept: text/html
User-Agent: Mozilla/5.0
```

第一行是**请求行**：方法（`GET`）、路径（`/products`）和 HTTP 版本。接下来的几行是**头部**——关于请求的元数据。然后可选地跟一个**主体**（用于 POST/PUT 请求）。

**HTTP 方法**定义了你想要做什么：

| 方法 | 用途 | 有主体？ | 示例 |
|--------|---------|-----------|---------|
| **GET** | 获取数据 | 否 | 加载网页、获取 API 响应 |
| **POST** | 发送数据以创建资源 | 是 | 提交表单、创建用户 |
| **PUT** | 替换现有资源 | 是 | 完整更新用户资料 |
| **PATCH** | 部分更新资源 | 是 | 仅修改电子邮件地址 |
| **DELETE** | 删除资源 | 通常无 | 删除账户 |
| **HEAD** | 与 GET 相同，但响应无主体 | 否 | 检查资源是否存在 |

**HTTP 状态码**是服务器的响应——一个三位数字，告诉客户端发生了什么：

```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 42

{"id": 1, "name": "Widget", "price": 10}
```

主要类别：
- **2xx — 成功：** `200 OK`（这是你要的数据）、`201 Created`（新资源已创建）、`204 No Content`（完成，无内容返回）
- **3xx — 重定向：** `301 Moved Permanently`（永久使用这个新 URL）、`302 Found`（临时使用另一个 URL）、`304 Not Modified`（使用你缓存的版本）
- **4xx — 客户端错误：** `400 Bad Request`（你的请求格式有误）、`401 Unauthorized`（你是谁？）、`403 Forbidden`（我知道你是谁，但不行）、`404 Not Found`（不存在）、`429 Too Many Requests`（慢一点）
- **5xx — 服务器错误：** `500 Internal Server Error`（出故障了）、`502 Bad Gateway`（上游服务器失败）、`503 Service Unavailable`（服务器过载或宕机）、`504 Gateway Timeout`（上游响应超时）

**curl** 是用于发起 HTTP 请求的命令行工具。它是网络领域的瑞士军刀，每个 SRE 每天都在使用：

```bash
# 简单的 GET 请求
curl http://192.168.1.42:5000/products

# 查看完整的请求和响应头部
curl -v http://192.168.1.42:5000/products

# 带 JSON 主体的 POST 请求
curl -X POST http://192.168.1.42:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# 仅获取状态码
curl -o /dev/null -s -w "%{http_code}" http://192.168.1.42:5000/health

# PUT 请求
curl -X PUT http://192.168.1.42:5000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com"}'

# DELETE 请求
curl -X DELETE http://192.168.1.42:5000/api/users/1

# 跟随重定向
curl -L http://example.com
```

`-v`（详细）标志是调试时最好的朋友。它会准确显示发送和接收的内容——每个头部、每个状态码，以及客户端与服务器之间的完整对话。

**应用层**是网络栈的顶层。模型如下所示：

| 层 | 协议 | 作用 |
|-------|----------|--------------|
| 应用层 | HTTP、DNS、SMTP | 定义通信的含义 |
| 传输层 | TCP、UDP | 可靠（或快速）的数据传输 |
| 网络层 | IP | 网络间的寻址和路由 |
| 链路层 | Ethernet、WiFi | 设备间的物理传输 |

HTTP 不关心 TCP 如何传输字节。TCP 不关心字节的含义。每一层只做一件事，并信任其下层。这就是为什么你可以在 WiFi、以太网、蜂窝网络或卫星网络上运行 HTTP——HTTP 使用 TCP，而 TCP 可以在任何介质上工作。

**头部**携带重要的元数据。你会经常看到以下这些：

- `Content-Type: application/json` — 主体是 JSON
- `Authorization: Bearer eyJ...` — 认证令牌
- `Cache-Control: max-age=3600` — 缓存一小时
- `X-Request-ID: abc-123` — 用于在系统中追踪请求的唯一 ID
- `User-Agent: curl/7.68.0` — 发起请求的客户端

需要注意的一件重要事情：**HTTP 是明文传输的**。每个请求和响应——包括密码、Cookie、个人数据——都以可读文本的形式在网络中传输。运行 `curl -v`，你可以看到每一个字节。你和服务器之间的任何人（WiFi 运营商、你的 ISP、沿途的任何路由器）都能读取全部内容。这是一个严重的问题，解决它需要加密——这是另一个独立的话题。

<!-- ZH_RESOURCES -->
- [MDN - HTTP 概览](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) -- 类型: 参考, 时间: 20m
- [HTTP 状态码参考](https://httpstatuses.com/) -- 类型: 参考, 时间: 10m
- [curl 教程](https://curl.se/docs/tutorial.html) -- 类型: 教程, 时间: 30m
- [Julia Evans - HTTP Zine](https://wizardzines.com/zines/http/) -- 类型: zine, 时间: 15m
- [Everything curl（免费书籍）](https://everything.curl.dev/) -- 类型: 书籍, 时间: 不定

<!-- ZH_UI -->
1. 理解 HTTP 请求-响应周期，包括方法和状态码
2. 使用 curl 发起 GET、POST、PUT 和 DELETE 请求
3. 在浏览器开发者工具中阅读和理解 HTTP 头
4. 我理解了 HTTP。但真实用户使用我的应用时，我到底该在哪里运行它？
5. 我的应用在 localhost 上能跑，也能用 curl 访问。但我需要一个永久可访问的地方——不是我的笔记本，也不是本地端口。你想让真实用户访问的东西，到底该放在哪里？
6. HTTP 是明文传输。任何人都能读取我的流量吗？
7. 我刚意识到我的登录表单正在网络上以明文发送用户名和密码。任何监听流量的人都能读到它们。HTTPS 究竟是如何防止这种情况的？
