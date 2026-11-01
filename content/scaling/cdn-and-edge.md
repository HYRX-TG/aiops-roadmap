---
id: cdn-and-edge
title: CDNs and Edge Caching
zone: scaling
edges:
  to: []
difficulty: 1
tags:
  - cdn
  - cloudfront
  - edge
  - caching
  - latency
  - static-assets
  - performance
  - aws
category: concept
milestones:
  - Set up CloudFront in front of an S3 bucket serving static assets
  - Understand what a cache-control header does and how to set appropriate TTLs
  - Configure CloudFront to forward requests to your origin for dynamic content
  - Understand the difference between a CDN cache hit and a cache miss
title_zh: "CDN 与边缘缓存"

---


A CDN (Content Delivery Network) is a globally distributed network of cache servers. Instead of serving all your assets from one origin server in us-east-1, a CDN copies your content to dozens of edge locations worldwide. A user in Singapore gets your images and CSS from a server in Singapore, not from Virginia. The result: faster first loads for global users and dramatically less traffic hitting your origin.

<!-- DEEP_DIVE -->

## How CDNs work

When a user requests a cacheable resource through a CDN, the request goes to the nearest edge location (point of presence). If the edge has a cached copy, it serves it directly without touching your origin server. If it doesn't (a cache miss), the edge fetches the resource from your origin, caches it, and serves it. Every subsequent request from any user near that edge location gets the cached copy.

Your DNS points to the CDN. Users never directly resolve your origin server's IP. The CDN is a global caching layer with automatic geographic routing built in.

## CloudFront on AWS

CloudFront is AWS's CDN. Setting it up involves:

1. Create a **distribution** in the CloudFront console
2. Set an **origin**: either an S3 bucket (for static assets) or your ALB/EC2 (for dynamic content)
3. Configure **cache behaviors**: which URL paths to cache, how long (TTL), and which headers to pass through to the origin
4. Update your DNS (or your asset URLs) to point to the CloudFront distribution domain (e.g., `d1234abcd.cloudfront.net`)

For static assets, point CloudFront at an S3 bucket. Upload your CSS, JS, and images to S3; CloudFront distributes them globally. No EC2 instance needed for static file serving.

For dynamic content, you can put CloudFront in front of your ALB. CloudFront will cache responses with appropriate `Cache-Control` headers and pass through uncacheable requests to the ALB. This also lets CloudFront absorb DDoS traffic before it reaches your instances.

## Cache behavior configuration

The most important per-behavior settings:

- **TTL**: minimum, maximum, and default TTL for cached responses. CloudFront respects `Cache-Control: max-age` from the origin up to your configured maximum.
- **Cache key**: what combination of URL, headers, query strings, and cookies determines if two requests are for the "same" resource. Narrower cache keys = higher hit rates.
- **Compress**: CloudFront can compress responses automatically (gzip, Brotli). Enable this — it reduces transfer size by 60-80% for text content.
- **Viewer protocol policy**: HTTP or HTTPS only. Set HTTPS only or redirect HTTP → HTTPS.

## Cache invalidation

When you deploy new static assets, CDN edge caches still have the old versions. Two ways to handle this:

1. **Content-hashed filenames** (preferred): `app.a3f9b1c.js` — the URL changes when content changes, so old caches naturally expire while the CDN caches the new URL separately.

2. **Explicit invalidation**: call the CloudFront API to invalidate specific paths (`/static/*`) or all paths (`/*`). CloudFront propagates the invalidation to all edges within a few minutes. Use sparingly — there's a cost per invalidation path after the first 1000/month.

## Beyond static assets

Modern CDNs do more than serve files:
- **SSL termination**: CloudFront handles TLS globally, near the user, using certificates from AWS Certificate Manager
- **DDoS protection**: CloudFront (with AWS Shield) absorbs volumetric attacks before they reach your origin
- **Edge functions**: Lambda@Edge and CloudFront Functions let you run code at edge locations — for A/B testing, URL rewrites, auth token validation
- **Caching dynamic responses**: product pages, category listings — anything with appropriate Cache-Control headers

<!-- RESOURCES -->

- [AWS CloudFront Getting Started](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html) -- type: docs, time: 30m
- [CDN Concepts - Cloudflare Learning](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/) -- type: article, time: 10m
- [CloudFront with S3 Tutorial](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStartedCreateDistribution.html) -- type: tutorial, time: 30m

<!-- ZH_SUMMARY -->
CDN（内容分发网络）是一个全球分布的缓存服务器网络。CDN 不会从 us-east-1 的单一源站服务器提供所有资源，而是将你的内容复制到全球数十个边缘节点。新加坡的用户会从新加坡的服务器获取你的图片和 CSS，而不是从弗吉尼亚获取。结果是：全球用户的首次加载速度更快，并且到达源站的流量大幅减少。

<!-- ZH_DEEP_DIVE -->
## CDN 的工作原理

当用户通过 CDN 请求可缓存的资源时，请求会发往最近的边缘位置（接入点）。如果该边缘节点有缓存副本，它会直接返回，不触及你的源站服务器。如果没有（缓存未命中），边缘节点会从你的源站获取资源、缓存它，然后返回。此后，来自该边缘位置附近任何用户的每次请求都会得到缓存副本。

你的 DNS 指向 CDN。用户永远不会直接解析到你源站服务器的 IP。CDN 是一个内置自动地理路由的全球缓存层。

## AWS 上的 CloudFront

CloudFront 是 AWS 的 CDN。设置它涉及：

1. 在 CloudFront 控制台创建一个 **distribution**（分配）
2. 设置一个 **origin**（源）：可以是 S3 存储桶（用于静态资源）或你的 ALB/EC2（用于动态内容）
3. 配置 **cache behaviors**（缓存行为）：缓存哪些 URL 路径、缓存多久（TTL），以及哪些请求头透传到源站
4. 更新你的 DNS（或资源 URL）指向 CloudFront 分配域名（例如 `d1234abcd.cloudfront.net`）

对于静态资源，将 CloudFront 指向 S3 存储桶。把 CSS、JS 和图片上传到 S3；CloudFront 会将它们分发到全球。静态文件服务无需 EC2 实例。

对于动态内容，你可以将 CloudFront 放在 ALB 前面。CloudFront 会缓存带有适当 `Cache-Control` 头的响应，并将不可缓存的请求透传到 ALB。这还能让 CloudFront 在 DDoS 流量到达你的实例之前将其吸收。

## 缓存行为配置

最重要的每行为设置：

- **TTL**：缓存响应的最小、最大和默认 TTL。CloudFront 会遵循源站的 `Cache-Control: max-age`，上限为你配置的最大值。
- **Cache key**（缓存键）：由 URL、请求头、查询字符串和 Cookie 的哪种组合来决定两个请求是否针对“同一”资源。缓存键越窄 = 命中率越高。
- **Compress**（压缩）：CloudFront 可以自动压缩响应（gzip、Brotli）。启用它——对于文本内容，可将传输大小减少 60-80%。
- **Viewer protocol policy**（查看器协议策略）：仅 HTTP 或仅 HTTPS。设置为仅 HTTPS 或将 HTTP 重定向到 HTTPS。

## 缓存失效

当你部署新的静态资源时，CDN 边缘缓存仍保留旧版本。有两种处理方式：

1. **内容哈希文件名**（首选）：`app.a3f9b1c.js`——内容变化时 URL 随之变化，因此旧缓存自然过期，而 CDN 会单独缓存新 URL。

2. **显式失效**：调用 CloudFront API 使特定路径（`/static/*`）或所有路径（`/*`）失效。CloudFront 会在几分钟内将失效传播到所有边缘节点。请谨慎使用——每月前 1000 个失效路径之后，每个路径都会产生费用。

## 超越静态资源

现代 CDN 做的不仅仅是提供文件：
- **SSL 终止**：CloudFront 在靠近用户的全球范围处理 TLS，使用来自 AWS Certificate Manager 的证书
- **DDoS 防护**：CloudFront（配合 AWS Shield）在容量型攻击到达你的源站之前将其吸收
- **边缘函数**：Lambda@Edge 和 CloudFront Functions 让你在边缘位置运行代码——用于 A/B 测试、URL 重写、认证令牌验证
- **缓存动态响应**：产品页面、分类列表——任何带有适当 Cache-Control 头的内容

<!-- ZH_RESOURCES -->
- [AWS CloudFront 入门](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html) -- 类型: 文档, 时间: 30m
- [CDN 概念 - Cloudflare Learning](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/) -- 类型: 文章, 时间: 10m
- [CloudFront 与 S3 教程](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStartedCreateDistribution.html) -- 类型: 教程, 时间: 30m

<!-- ZH_UI -->
1. 在提供静态资源的 S3 存储桶前设置 CloudFront
2. 理解 cache-control 头的作用，并学会设置合适的 TTL
3. 配置 CloudFront 将动态内容请求转发到源站
4. 理解 CDN 缓存命中与缓存未命中的区别
