---
id: reverse-proxy-caching
title: Reverse Proxy Caching
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - varnish
  - nginx
  - reverse-proxy
  - caching
  - http-cache
  - cache-control
  - performance
category: concept
milestones:
  - Explain what a reverse proxy cache is and how it differs from object caching
  - Know what Varnish is and what problem it solves
  - Explain how Nginx can act as a caching layer with proxy_cache
  - Know which responses can be cached by a reverse proxy (GET, public, correct headers)
  - Explain what a cache hit ratio is and how to measure it
  - Understand how Cache-Control headers determine what a proxy cache stores
title_zh: "反向代理缓存"

---


Object caching requires instrumenting your application code — every database call that should be cached needs to be wrapped. Reverse proxy caching is a different layer: it sits in front of your application and caches complete HTTP responses. Popular pages that thousands of users request in sequence hit the cache instead of your Python process, without any changes to application code.

<!-- DEEP_DIVE -->

## How it works

A reverse proxy cache (Varnish, Nginx with proxy_cache, or a similar system) sits between the client and the backend application. When a cacheable response arrives, the proxy stores it. Subsequent requests for the same URL and cache key get the stored response served directly — the backend is never contacted.

For high-traffic, infrequently-changing pages — the homepage, top category pages, product listings — the cache hit rate can reach 95%+. Your Python processes go from handling thousands of requests per second to handling only uncacheable requests and cache misses.

## What can be cached by a reverse proxy

Only responses that are safe to serve to multiple users can be cached:
- `GET` requests only (not `POST`, `PUT`, `DELETE`)
- Responses with appropriate `Cache-Control` headers (`public`, `max-age`)
- Responses that are the same for all users (not logged-in user's dashboard, not cart pages)

Responses with `Cache-Control: private`, `Set-Cookie`, or `Authorization` headers should not be cached by a proxy — these are user-specific.

This means reverse proxy caching is most useful for the public-facing parts of your site. The logged-in, personalized experience still hits your application servers.

## Nginx as a caching proxy

Nginx can serve as a caching reverse proxy with `proxy_cache`:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;

server {
    location / {
        proxy_pass http://backend;
        proxy_cache my_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_key "$scheme$host$request_uri";
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

The `X-Cache-Status` header tells you whether a response was a `HIT` or `MISS` — useful for debugging.

## Varnish Cache

Varnish is a purpose-built HTTP accelerator, faster than Nginx for caching workloads and much more configurable. Varnish's VCL (Varnish Configuration Language) lets you write complex caching logic: vary the cache key by cookie value, return different content for different user segments, do grace-mode serving of stale content while the backend re-fetches.

Varnish is overkill for most early-stage scaling scenarios, but it's the tool used by high-traffic publishers and e-commerce sites that need fine-grained control over caching behavior.

## Cache hit ratio

The **cache hit ratio** is the percentage of requests served from cache vs total requests. A ratio of 90% means only 10% of requests reach your backend. Monitor this metric — it tells you how effective your caching is. If it drops, either your TTLs are too short, you're seeing traffic for uncacheable URLs, or a deployment flushed the cache and it's warming up.

## Relationship to CDNs

A reverse proxy cache at the origin serves all traffic from a single location. A CDN (CloudFront, Fastly, Cloudflare) does the same thing but from edge locations worldwide. For global users, a CDN is a reverse proxy cache that also solves the geographic latency problem.

<!-- RESOURCES -->

- [Nginx Caching Guide](https://docs.nginx.com/nginx/admin-guide/content-cache/content-caching/) -- type: docs, time: 20m
- [Varnish Cache Documentation](https://varnish-cache.org/docs/) -- type: docs, time: 30m
- [HTTP Caching - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
对象缓存需要对应用代码进行埋点——每个应当被缓存的数据库调用都需要被包装。反向代理缓存则是另一个层面：它位于应用之前，缓存完整的 HTTP 响应。成千上万用户依次请求的热门页面会命中缓存，而不是落到你的 Python 进程上，且无需对应用代码做任何改动。

<!-- ZH_DEEP_DIVE -->
## 工作原理

反向代理缓存（Varnish、带 proxy_cache 的 Nginx 或类似系统）位于客户端与后端应用之间。当可缓存的响应到达时，代理会将其存储起来。后续对同一 URL 和缓存键的请求会直接返回已存储的响应——后端完全不会被访问。

对于高流量、不常变化的页面——首页、顶级分类页、商品列表页——缓存命中率可以达到 95% 以上。你的 Python 进程将从每秒处理数千个请求，变为只处理不可缓存的请求和缓存未命中。

## 反向代理可以缓存什么

只有可以安全地提供给多个用户的响应才能被缓存：
- 仅限 `GET` 请求（不包括 `POST`、`PUT`、`DELETE`）
- 带有适当 `Cache-Control` 头的响应（`public`、`max-age`）
- 对所有用户都相同的响应（不是已登录用户的仪表盘，也不是购物车页面）

带有 `Cache-Control: private`、`Set-Cookie` 或 `Authorization` 头的响应不应被代理缓存——这些是用户特定的内容。

这意味着反向代理缓存对网站的公开部分最有用。已登录的个性化体验仍然会访问你的应用服务器。

## 使用 Nginx 作为缓存代理

Nginx 可以通过 `proxy_cache` 充当缓存反向代理：

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;

server {
    location / {
        proxy_pass http://backend;
        proxy_cache my_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_key "$scheme$host$request_uri";
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

`X-Cache-Status` 头会告诉你响应是 `HIT` 还是 `MISS`——这对调试很有用。

## Varnish Cache

Varnish 是专为 HTTP 加速而构建的，在缓存工作负载下比 Nginx 更快，而且可配置性高得多。Varnish 的 VCL（Varnish Configuration Language）让你可以编写复杂的缓存逻辑：按 cookie 值改变缓存键、为不同用户群体返回不同内容、在后端重新获取数据时以 grace 模式提供过期内容。

对大多数早期扩展场景来说，Varnish 属于过度设计，但它是高流量内容发布商和电商网站所使用的工具，这些场景需要对缓存行为进行细粒度控制。

## 缓存命中率

**缓存命中率**是从缓存提供的请求占总请求的百分比。90% 的命中率意味着只有 10% 的请求会到达后端。监控这个指标——它能告诉你缓存的有效性。如果它下降了，要么是你的 TTL 太短，要么是出现了对不可缓存 URL 的流量，要么是一次部署清空了缓存、缓存正在预热。

## 与 CDN 的关系

源站的反向代理缓存从单一位置为所有流量提供服务。CDN（CloudFront、Fastly、Cloudflare）做的是同样的事情，但通过全球各地的边缘节点。对于全球用户来说，CDN 就是一个反向代理缓存，同时还解决了地理延迟问题。

<!-- ZH_RESOURCES -->
- [Nginx 缓存指南](https://docs.nginx.com/nginx/admin-guide/content-cache/content-caching/) -- 类型: 文档, 时间: 20m
- [Varnish Cache 文档](https://varnish-cache.org/docs/) -- 类型: 文档, 时间: 30m
- [HTTP 缓存 - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching) -- 类型: 文章, 时间: 15m

<!-- ZH_UI -->
1. 解释什么是反向代理缓存，以及它与对象缓存有何不同
2. 了解 Varnish 是什么以及它解决什么问题
3. 解释 Nginx 如何通过 proxy_cache 充当缓存层
4. 了解反向代理可以缓存哪些响应（GET、公开、正确的响应头）
5. 解释什么是缓存命中率以及如何测量它
6. 理解 Cache-Control 响应头如何决定代理缓存存储什么
