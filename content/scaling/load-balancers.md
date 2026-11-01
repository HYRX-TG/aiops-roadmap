---
id: load-balancers
title: Load Balancers
zone: scaling
edges:
  to:
    - id: session-problem
      question: >-
        Load balancer is in place. But now users keep getting randomly logged
        out. What's going on?
      detail: >-
        Everything looked fine after I added the load balancer, but now users
        keep complaining they're getting signed out mid-session. I didn't change
        any auth code — why is this suddenly happening?
    - id: application-caching
      question: >-
        The site is slow even though the servers aren't overloaded. Every
        request hits the database for the same data over and over.
      detail: >-
        I watched the queries — the same product pages, the same category
        listings, the same results being fetched from the database on every
        single request. The servers have capacity but the database is the
        bottleneck. Can I just keep frequently-used data somewhere faster?
    - id: rate-limiting
      question: The load balancer is distributing traffic. But bots and badly-written clients are hammering my API with hundreds of requests a second. How do I protect against that?
      detail: >-
        The LB handles normal traffic fine. But scrapers, abusive clients, and
        traffic spikes from retrying clients can still overwhelm my servers. A
        few bad actors shouldn't be able to take down the whole service. How do
        I throttle individual clients without affecting everyone else?
difficulty: 1
tags:
  - load-balancer
  - alb
  - aws
  - high-availability
  - health-checks
  - target-groups
category: concept
milestones:
  - Create an AWS Application Load Balancer with a target group
  - Register two EC2 instances behind the load balancer
  - Configure health checks and watch the ALB remove an unhealthy instance
  - Understand the difference between a Layer 4 and Layer 7 load balancer
title_zh: "负载均衡器"

---


A load balancer sits in front of your application servers and distributes incoming requests across them. When you have three app servers, the load balancer is the single entry point — it accepts the connection, picks a backend server, and forwards the request. It's the traffic cop that makes horizontal scaling possible.

<!-- DEEP_DIVE -->

## What a load balancer actually does

When a request arrives at the load balancer, it selects one of the registered backend servers (called targets) and proxies the request to it. The client talks to the load balancer's IP address; the load balancer talks to the backend. From the backend's perspective, every request looks like it came from the load balancer.

Most cloud load balancers also perform **health checks**: they periodically send a request to each backend (typically an HTTP `GET /health` endpoint or a TCP connection) and mark backends as healthy or unhealthy. Traffic is only sent to healthy backends. If a server crashes, the load balancer detects the failed health check within seconds and stops sending it traffic. This is where availability comes from — not just performance.

## Layer 4 vs Layer 7

Load balancers operate at different layers of the network stack:

**Layer 4 (transport layer)** balancers forward TCP or UDP connections. They see source/destination IP and port, but not the HTTP content. They're fast and simple — they just route connections — but they can't make routing decisions based on URL path, cookies, or headers.

**Layer 7 (application layer)** balancers understand HTTP. They can route based on URL path (`/api/` → one set of servers, `/static/` → another), read cookies, terminate TLS, add headers, and inspect request content. AWS's **Application Load Balancer (ALB)** is a Layer 7 load balancer; the older **Classic Load Balancer** and **Network Load Balancer** operate at Layer 4.

For most web applications, a Layer 7 load balancer is what you want. The ability to route by URL, terminate TLS in one place, and make routing decisions based on headers covers the vast majority of use cases.

## Setting one up on AWS

1. Create an **Application Load Balancer** in the EC2 console. Choose internet-facing (or internal for backend services). Configure your VPC and subnets — pick at least two availability zones.
2. Create a **Target Group** — a logical group of backends. Register your EC2 instances in it. Configure the health check: path (`/health`), protocol, and thresholds (how many successes before marking healthy, how many failures before marking unhealthy).
3. Create a **Listener** on the ALB — port 80 (or 443 with a TLS certificate). Attach a rule that forwards traffic to your target group.

Your domain should now point to the ALB's DNS name, not directly to your EC2 instances. The instances can have private IPs only — they don't need to be publicly accessible.

## Algorithms: round robin and beyond

By default, ALBs use **round robin** — requests are distributed evenly across healthy backends in order. This works well when requests have similar cost. Other algorithms:

- **Least connections**: send to the backend with the fewest active connections — better when some requests take much longer than others
- **IP hash**: hash the client IP to always send the same client to the same backend — this is effectively sticky sessions at the network layer, with all its problems

Round robin is fine for most applications. The session problem (coming up next) should be solved in your application layer, not by messing with the load balancer's routing algorithm.

<!-- RESOURCES -->

- [AWS Application Load Balancer Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) -- type: docs, time: 30m
- [AWS Load Balancer Types Compared](https://aws.amazon.com/elasticloadbalancing/features/) -- type: docs, time: 10m
- [NGINX Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
负载均衡器位于应用服务器前端，将传入请求分发到各台服务器上。当你拥有三台应用服务器时，负载均衡器就是唯一的入口——它接受连接、选择一台后端服务器并转发请求。它是让水平扩展成为可能的流量调度器。

<!-- ZH_DEEP_DIVE -->
## 负载均衡器实际做了什么

当请求到达负载均衡器时，它会从已注册的后端服务器（称为 target）中选择一个，并将请求代理到该服务器。客户端与负载均衡器的 IP 地址通信；负载均衡器再与后端通信。从后端的角度来看，每个请求看起来都来自负载均衡器。

大多数云负载均衡器还会执行**健康检查**：它们定期向每个后端发送请求（通常是 HTTP `GET /health` 端点或 TCP 连接），并将后端标记为健康或不健康。流量只会发送到健康的后端。如果某台服务器崩溃，负载均衡器会在几秒内检测到健康检查失败，并停止向其发送流量。可用性正是来源于此——而不仅仅是性能。

## 第 4 层与第 7 层

负载均衡器工作在网络栈的不同层次：

**第 4 层（传输层）**负载均衡器转发 TCP 或 UDP 连接。它们能看到源/目标 IP 和端口，但看不到 HTTP 内容。它们快速且简单——只负责路由连接——但无法根据 URL 路径、cookie 或 header 做出路由决策。

**第 7 层（应用层）**负载均衡器理解 HTTP。它们可以根据 URL 路径进行路由（`/api/` → 一组服务器，`/static/` → 另一组）、读取 cookie、终止 TLS、添加 header，并检查请求内容。AWS 的 **Application Load Balancer (ALB)** 是第 7 层负载均衡器；较旧的 **Classic Load Balancer** 和 **Network Load Balancer** 工作在第 4 层。

对于大多数 Web 应用来说，第 7 层负载均衡器正是你需要的。按 URL 路由、在一处终止 TLS、以及根据 header 做出路由决策的能力，覆盖了绝大多数用例。

## 在 AWS 上搭建一个

1. 在 EC2 控制台中创建一个 **Application Load Balancer**。选择面向互联网（或为后端服务选择内部）。配置你的 VPC 和子网——至少选择两个可用区。
2. 创建一个 **Target Group**——后端的逻辑分组。将你的 EC2 实例注册到其中。配置健康检查：路径（`/health`）、协议和阈值（标记为健康前需要多少次成功，标记为不健康前需要多少次失败）。
3. 在 ALB 上创建一个 **Listener**——端口 80（或使用 TLS 证书的 443）。附加一条将流量转发到你的 target group 的规则。

你的域名现在应该指向 ALB 的 DNS 名称，而不是直接指向你的 EC2 实例。实例可以只有私有 IP——它们不需要可公开访问。

## 算法：轮询及其他

默认情况下，ALB 使用**轮询**——请求按顺序均匀分配到健康的后端。当请求成本相近时，这种方式效果很好。其他算法：

- **最少连接**：发送到活动连接数最少的后端——当某些请求耗时远长于其他请求时更合适
- **IP 哈希**：对客户端 IP 进行哈希，始终将同一客户端发送到同一后端——这实际上是在网络层实现粘性会话，并带有其所有问题

轮询对大多数应用来说已经足够。会话问题（接下来会讨论）应该在应用层解决，而不是通过调整负载均衡器的路由算法来解决。

<!-- ZH_RESOURCES -->
- [AWS Application Load Balancer 文档](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) -- 类型: 文档, 时间: 30m
- [AWS 负载均衡器类型对比](https://aws.amazon.com/elasticloadbalancing/features/) -- 类型: 文档, 时间: 10m
- [NGINX 负载均衡](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) -- 类型: 文档, 时间: 15m

<!-- ZH_UI -->
1. 创建一个带有目标组的 AWS 应用负载均衡器
2. 在负载均衡器后面注册两个 EC2 实例
3. 配置健康检查，观察 ALB 移除不健康的实例
4. 理解四层和七层负载均衡器的区别
5. 负载均衡器已就位。但现在用户总是被随机登出。发生了什么？
6. 添加负载均衡器后一切看起来都正常，但现在用户不断抱怨他们在会话中途被登出。我没有改动任何认证代码——为什么突然出现这种情况？
7. 服务器没有过载，但网站很慢。每个请求都反复从数据库获取相同的数据。
8. 我观察了查询——相同的产品页面、相同的分类列表、相同的结果在每次请求时都从数据库获取。服务器有容量，但数据库是瓶颈。我能不能把频繁使用的数据放到更快的地方？
9. 负载均衡器正在分发流量。但机器人和编写拙劣的客户端正以每秒数百个请求冲击我的 API。我该如何防护？
10. 负载均衡器能正常处理常规流量。但爬虫、滥用客户端以及重试客户端带来的流量峰值仍然可能压垮我的服务器。少数不良行为者不应该能拖垮整个服务。我如何在不影响其他用户的情况下对单个客户端进行限流？
