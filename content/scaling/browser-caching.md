---
id: browser-caching
title: Browser Caching
zone: scaling
edges:
  to:
    - id: cdn-and-edge
      question: >-
        Browser caching helps repeat visitors. What about users loading the site
        for the first time, from far away?
      detail: >-
        Repeat visitors are faster now, but someone opening the site for the
        first time from the other side of the world is still hitting my single
        server. That initial load is slow and I don't know how to fix it
        without moving the server closer to them somehow.
difficulty: 1
tags:
  - caching
  - cache-control
  - etag
  - http
  - browser
  - static-assets
  - performance
category: concept
milestones:
  - >-
    Understand what a Cache-Control header does and the difference between
    max-age and no-cache
  - Explain what an ETag is and how conditional requests work
  - >-
    Set appropriate cache headers for static assets (images, CSS, JS) vs dynamic
    responses
  - Understand cache busting and why you need it when assets change
title_zh: "浏览器缓存"

---


Every user visiting your site downloads your CSS, JavaScript, and images. Without browser caching, they download all of it again on every visit — even if nothing has changed since yesterday. Browser caching uses HTTP headers to tell the browser "you already have this, keep it and use it next time." Done right, repeat visitors load pages almost instantly with zero server requests for static assets.

<!-- DEEP_DIVE -->

## The Cache-Control header

`Cache-Control` is the primary header for controlling how long browsers cache responses.

```
Cache-Control: max-age=31536000, immutable
```

`max-age=31536000` means the browser can reuse this response for up to 31,536,000 seconds (one year) without even checking the server. `immutable` (supported by most modern browsers) is an additional hint that the content will never change — skip revalidation entirely.

For static assets with content-hashed filenames (like `app.a3f9b1c.js`), a one-year max-age is safe because the filename changes whenever the content changes.

For dynamic HTML responses:

```
Cache-Control: no-cache
```

`no-cache` does not mean "don't cache" — it means "cache it, but always revalidate with the server before using the cached copy." This lets the server return a `304 Not Modified` with no body if the content hasn't changed, saving bandwidth while ensuring freshness.

## ETags and conditional requests

An ETag is a fingerprint of a response (usually a hash of the content). The server includes it in the response:

```
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

On the next request, the browser sends:

```
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

If the content hasn't changed, the server returns `304 Not Modified` (no body, just headers). The browser uses its cached copy. This is a conditional request — the browser checks whether it needs to re-download before downloading.

This is cheaper than re-downloading content but still requires a round-trip to the server. For truly static assets with long max-age, the browser doesn't even make the request.

## Cache busting

Long cache TTLs create a problem: if you update a file, browsers that have it cached won't fetch the new version until the TTL expires (potentially a year away). The solution is **cache busting**: include a content hash in the filename.

```html
<script src="/static/app.a3f9b1c.js"></script>
```

When you update the file, the hash changes, the filename changes, and browsers treat it as a new resource and fetch it fresh. The old filename-based cache entry just expires naturally.

All modern frontend build tools (Vite, Webpack, esbuild) do this automatically.

## What to cache and for how long

| Resource type | `Cache-Control` | Rationale |
|---|---|---|
| Content-hashed JS/CSS/images | `max-age=31536000, immutable` | Filename changes when content changes |
| Non-hashed static assets (logo.png) | `max-age=86400` | Cache for a day, accept some lag |
| API responses | `no-cache` or `no-store` | Usually user-specific or frequently changing |
| HTML pages | `no-cache` | Always revalidate; want fresh deploys |
| Fonts | `max-age=31536000, immutable` | Rarely change, content-addressed |

## Setting headers

In Nginx:
```nginx
location ~* \.(js|css|png|jpg|gif|ico|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

In Python (Flask):
```python
@app.after_request
def set_cache_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```

<!-- RESOURCES -->

- [HTTP Caching - MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching) -- type: article, time: 20m
- [Cache-Control for Civilians (Harry Roberts)](https://csswizardry.com/2019/03/cache-control-for-civilians/) -- type: article, time: 15m
- [web.dev - Serve static assets with an efficient cache policy](https://web.dev/uses-long-cache-ttl/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
每位访问你网站的用户都会下载你的 CSS、JavaScript 和图片。如果没有浏览器缓存，他们每次访问都会重新下载所有这些内容——即使从昨天起没有任何变化。浏览器缓存通过 HTTP 头告诉浏览器“你已经有了这些内容，保留它们，下次直接使用”。如果配置得当，回访用户几乎可以瞬间加载页面，静态资源无需任何服务器请求。

<!-- ZH_DEEP_DIVE -->
## Cache-Control 响应头

`Cache-Control` 是控制浏览器缓存响应时长的首要响应头。

```
Cache-Control: max-age=31536000, immutable
```

`max-age=31536000` 表示浏览器可以在最长 31,536,000 秒（一年）内复用该响应，甚至无需向服务器发起校验。`immutable`（大多数现代浏览器均支持）是一个额外的提示，表明内容永远不会改变——完全跳过重新验证。

对于文件名带内容哈希的静态资源（如 `app.a3f9b1c.js`），设置一年的 max-age 是安全的，因为内容一旦变化，文件名也会随之改变。

对于动态 HTML 响应：

```
Cache-Control: no-cache
```

`no-cache` 并不意味着“不要缓存”——它的意思是“可以缓存，但在使用缓存副本之前必须始终向服务器重新验证”。这样，如果内容未发生变化，服务器可以返回不带响应体的 `304 Not Modified`，在保证新鲜度的同时节省带宽。

## ETag 与条件请求

ETag 是响应的一个指纹（通常是内容的哈希值）。服务器会在响应中包含它：

```
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

在下一次请求时，浏览器会发送：

```
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

如果内容未发生变化，服务器返回 `304 Not Modified`（无响应体，仅响应头）。浏览器使用其缓存副本。这就是条件请求——浏览器在下载之前先检查是否需要重新下载。

这比重新下载内容开销更小，但仍然需要一次到服务器的往返。对于设置了较长 max-age 的真正静态资源，浏览器甚至不会发起请求。

## 缓存清除（Cache busting）

较长的缓存 TTL 会带来一个问题：如果你更新了某个文件，已缓存该文件的浏览器在 TTL 过期之前（可能是一年之后）不会获取新版本。解决方案是**缓存清除（cache busting）**：在文件名中包含内容哈希。

```html
<script src="/static/app.a3f9b1c.js"></script>
```

当你更新文件时，哈希会变化，文件名随之改变，浏览器会将其视为新资源并重新获取。基于旧文件名的缓存条目则会自然过期。

所有现代前端构建工具（Vite、Webpack、esbuild）都会自动完成这一操作。

## 缓存什么以及缓存多久

| 资源类型 | `Cache-Control` | 理由 |
|---|---|---|
| 带内容哈希的 JS/CSS/图片 | `max-age=31536000, immutable` | 内容变化时文件名随之变化 |
| 无哈希的静态资源（logo.png） | `max-age=86400` | 缓存一天，接受一定的延迟 |
| API 响应 | `no-cache` 或 `no-store` | 通常与用户相关或频繁变化 |
| HTML 页面 | `no-cache` | 始终重新验证；希望部署即时生效 |
| 字体 | `max-age=31536000, immutable` | 很少变化，内容寻址 |

## 设置响应头

在 Nginx 中：
```nginx
location ~* \.(js|css|png|jpg|gif|ico|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

在 Python（Flask）中：
```python
@app.after_request
def set_cache_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```

<!-- ZH_RESOURCES -->
- [HTTP Caching - MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching) -- 类型: article, 时间: 20m
- [Cache-Control for Civilians (Harry Roberts)](https://csswizardry.com/2019/03/cache-control-for-civilians/) -- 类型: article, 时间: 15m
- [web.dev - Serve static assets with an efficient cache policy](https://web.dev/uses-long-cache-ttl/) -- 类型: article, 时间: 10m

<!-- ZH_UI -->
1. 理解 Cache-Control 响应头的作用，以及 max-age 与 no-cache 的区别
2. 解释什么是 ETag，以及条件请求如何工作
3. 为静态资源（图片、CSS、JS）与动态响应分别设置合适的缓存头
4. 理解缓存清除（cache busting），以及资源变更时为何需要它
5. 浏览器缓存能帮助回访用户。那么首次访问、且距离较远的用户呢？
6. 回访用户现在更快了，但首次从世界另一端打开网站的用户仍然在访问我的单台服务器。首次加载很慢，我不知道如何在不把服务器搬到他们附近的情况下解决这个问题。
