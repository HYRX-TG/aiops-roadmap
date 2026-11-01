---
id: web-servers
title: Web Servers
zone: running
edges:
  to:
    - id: dns-and-domain-names
      question: >-
        My web server works, but I'm using raw IP addresses. How do I give my
        site a real name?
      detail: >-
        Nginx is running and I can hit it with the IP address. But I need an
        actual domain name — something people can type. I have no idea how
        domain names get tied to IP addresses or what I'd have to set up to make
        my-app.example.com point at my server.
    - id: tls-and-certificates
      question: 'My web server works over HTTP, but I need HTTPS. How do I set up TLS?'
      detail: >-
        My site works over HTTP but the browser is showing a 'Not Secure'
        warning. I know I need HTTPS but I have no idea how to get a certificate
        or what TLS actually involves. How does any of this work, and how do I
        get the padlock?
    - id: reading-logs
      question: >-
        Nginx is running and serving traffic. How do I see what requests are
        coming in?
      detail: >-
        Nginx is serving traffic but I have no visibility into what's happening.
        Is my app actually responding? Are there errors? What URLs are people
        hitting? There must be a log somewhere that shows me all of this — where
        is it and how do I make sense of it?
difficulty: 1
tags:
  - nginx
  - apache
  - web-server
  - http
  - static-files
  - serving
category: tool
milestones:
  - Install Nginx and serve a static HTML page
  - Configure Nginx to serve different content based on URL path
  - Understand the difference between a web server and your Flask dev server
title_zh: "Web 服务器"

---


Your Flask app has a built-in web server — you run `python app.py` and it serves pages on port 5000. But that server is designed for development. It handles one request at a time, crashes without helpful errors, and has no concept of security or performance. Real websites are served by dedicated **web server** software — programs that are built from the ground up to handle HTTP traffic reliably and efficiently.

<!-- DEEP_DIVE -->

A **web server** is a program that listens for HTTP requests and sends back HTTP responses. That is it. At its core, it is surprisingly simple: a client asks for a file, and the server sends it back.

In the early web, that was literally all web servers did — serve files. You put `index.html` in a directory, and when someone visited your site, the web server read that file from disk and sent it back over HTTP. This still works and is how many static sites are served today.

**Nginx** (pronounced "engine-x") is the most popular web server. Install it on Ubuntu with `sudo apt install nginx`, and it immediately starts serving a default welcome page on port 80:

```bash
# Install Nginx
sudo apt install nginx

# Check it is running
sudo systemctl status nginx

# The default page is served from:
ls /var/www/html/
# index.nginx-debian.html
```

Visit `http://your-ip` in a browser and you see the Nginx welcome page. That is a web server doing its job — listening on port 80 and serving an HTML file.

**Nginx configuration** lives in `/etc/nginx/`. Here is a simple config that serves a website:

```nginx
server {
    listen 80;
    server_name mystore.com;

    root /var/www/mystore;
    index index.html;

    # Serve files from the /var/www/mystore directory
    location / {
        try_files $uri $uri/ =404;
    }

    # Serve static assets with caching headers
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Put your HTML, CSS, JavaScript, and images in `/var/www/mystore/`, reload Nginx (`sudo nginx -s reload`), and your site is live. Nginx will serve those files to anyone who connects.

**Why not just use Flask's built-in server?** The differences are enormous:

| | Flask dev server | Nginx |
|---|---|---|
| **Connections** | One at a time (single-threaded) | Thousands simultaneously |
| **Static files** | Slow (goes through Python) | Blazing fast (reads directly from disk) |
| **Stability** | Crashes on errors | Keeps running, logs errors |
| **Performance** | Written in Python | Written in C, highly optimized |
| **Security** | No built-in protections | Rate limiting, access control, header management |

For your Flask or Django app, the production setup uses a **WSGI server** like Gunicorn to run your Python code, and Nginx in front to handle the HTTP layer:

```bash
# Run your Flask app with Gunicorn (production Python server)
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

Gunicorn runs 4 worker processes of your app, each able to handle requests. Nginx receives HTTP requests from the network and passes them to Gunicorn. This separation of concerns — Nginx handles HTTP, Gunicorn handles Python — is how virtually every Python web application is deployed.

**Apache** (`httpd`) is the other major web server. It has been around since 1995 and still powers a significant portion of the internet. Apache uses a different configuration style (`.htaccess` files, `<VirtualHost>` blocks) and a different architecture, but serves the same fundamental purpose. You will encounter Apache in legacy environments, WordPress hosting, and PHP applications.

```apache
# Apache virtual host configuration
<VirtualHost *:80>
    ServerName mystore.com
    DocumentRoot /var/www/mystore

    <Directory /var/www/mystore>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

**Virtual hosts** let a single web server handle multiple websites. One Nginx instance can serve `mystore.com` from one directory and `myblog.com` from another, routing requests based on the `Host` header. This is how shared hosting works — hundreds of websites on one server.

**Access logs** are one of the most useful things a web server gives you. Every request is logged:

```
192.168.1.43 - - [15/Jan/2024:14:30:00 +0000] "GET /products HTTP/1.1" 200 4523
192.168.1.43 - - [15/Jan/2024:14:30:01 +0000] "GET /static/style.css HTTP/1.1" 304 0
10.0.0.5 - - [15/Jan/2024:14:30:05 +0000] "POST /api/order HTTP/1.1" 500 128
```

Each line tells you: who connected (IP), when, what they requested (method + path), the status code, and the response size. When something goes wrong, this is the first place you look. As an SRE, you will spend a lot of time reading web server logs.

**Why SREs care:** Web servers are the front door to almost every service. Nginx and Apache configuration, log analysis, performance tuning, and troubleshooting are core SRE skills. Understanding how a web server handles requests — from accepting the TCP connection to sending the response — helps you debug everything from slow pages to connection timeouts to 502 errors.

<!-- RESOURCES -->

- [Nginx Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html) -- type: tutorial, time: 30m
- [DigitalOcean - How To Install Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04) -- type: tutorial, time: 20m
- [Apache vs Nginx - DigitalOcean](https://www.digitalocean.com/community/tutorials/apache-vs-nginx-practical-considerations) -- type: article, time: 15m
- [Nginx Documentation](https://nginx.org/en/docs/) -- type: reference, time: varies

<!-- ZH_SUMMARY -->
你的 Flask 应用自带一个内置的 Web 服务器——运行 `python app.py`，它就会在 5000 端口上提供页面服务。但这个服务器是为开发而设计的。它一次只处理一个请求，崩溃时不会给出有用的错误信息，也完全没有安全或性能方面的考虑。真实的网站由专用的 **Web 服务器**软件来提供服务——这类程序从底层开始就是为可靠、高效地处理 HTTP 流量而构建的。

<!-- ZH_DEEP_DIVE -->
**Web 服务器**是一个监听 HTTP 请求并返回 HTTP 响应的程序。仅此而已。从本质上讲，它简单得令人惊讶：客户端请求一个文件，服务器将其返回。

在早期的 Web 中，Web 服务器实际上就只做这一件事——提供文件。你把 `index.html` 放在一个目录中，当有人访问你的站点时，Web 服务器从磁盘读取该文件并通过 HTTP 返回。这种方式至今仍然有效，也是如今许多静态站点的服务方式。

**Nginx**（发音为 "engine-x"）是最流行的 Web 服务器。在 Ubuntu 上使用 `sudo apt install nginx` 安装，它会立即开始在 80 端口上提供默认欢迎页面：

```bash
# Install Nginx
sudo apt install nginx

# Check it is running
sudo systemctl status nginx

# The default page is served from:
ls /var/www/html/
# index.nginx-debian.html
```

在浏览器中访问 `http://your-ip`，你会看到 Nginx 欢迎页面。这就是 Web 服务器在履行其职责——监听 80 端口并提供 HTML 文件。

**Nginx 配置**位于 `/etc/nginx/`。以下是一个提供网站服务的简单配置：

```nginx
server {
    listen 80;
    server_name mystore.com;

    root /var/www/mystore;
    index index.html;

    # Serve files from the /var/www/mystore directory
    location / {
        try_files $uri $uri/ =404;
    }

    # Serve static assets with caching headers
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

将你的 HTML、CSS、JavaScript 和图片放入 `/var/www/mystore/`，重新加载 Nginx（`sudo nginx -s reload`），你的站点就上线了。Nginx 会将这些文件提供给任何连接的人。

**为什么不直接使用 Flask 内置的服务器？** 差异是巨大的：

| | Flask 开发服务器 | Nginx |
|---|---|---|
| **连接数** | 一次一个（单线程） | 同时数千个 |
| **静态文件** | 慢（经过 Python） | 极快（直接从磁盘读取） |
| **稳定性** | 出错即崩溃 | 持续运行，记录错误 |
| **性能** | 用 Python 编写 | 用 C 编写，高度优化 |
| **安全性** | 无内置防护 | 限流、访问控制、请求头管理 |

对于你的 Flask 或 Django 应用，生产环境使用 **WSGI 服务器**（如 Gunicorn）来运行你的 Python 代码，并由 Nginx 在前端处理 HTTP 层：

```bash
# Run your Flask app with Gunicorn (production Python server)
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

Gunicorn 运行你的应用的 4 个工作进程，每个进程都能处理请求。Nginx 从网络接收 HTTP 请求并将其传递给 Gunicorn。这种关注点分离——Nginx 处理 HTTP，Gunicorn 处理 Python——是几乎所有 Python Web 应用的部署方式。

**Apache**（`httpd`）是另一个主要的 Web 服务器。它自 1995 年就已存在，至今仍支撑着互联网的很大一部分。Apache 使用不同的配置风格（`.htaccess` 文件、`<VirtualHost>` 块）和不同的架构，但服务于相同的基本目的。你会在遗留环境、WordPress 托管和 PHP 应用中遇到 Apache。

```apache
# Apache virtual host configuration
<VirtualHost *:80>
    ServerName mystore.com
    DocumentRoot /var/www/mystore

    <Directory /var/www/mystore>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

**虚拟主机**让单个 Web 服务器处理多个网站。一个 Nginx 实例可以从一个目录提供 `mystore.com`，从另一个目录提供 `myblog.com`，根据 `Host` 请求头路由请求。这就是共享托管的工作原理——一台服务器上托管数百个网站。

**访问日志**是 Web 服务器提供的最有用的东西之一。每个请求都会被记录：

```
192.168.1.43 - - [15/Jan/2024:14:30:00 +0000] "GET /products HTTP/1.1" 200 4523
192.168.1.43 - - [15/Jan/2024:14:30:01 +0000] "GET /static/style.css HTTP/1.1" 304 0
10.0.0.5 - - [15/Jan/2024:14:30:05 +0000] "POST /api/order HTTP/1.1" 500 128
```

每一行告诉你：谁连接了（IP）、何时连接、请求了什么（方法 + 路径）、状态码以及响应大小。当出现问题时，这是你首先查看的地方。作为 SRE，你会花大量时间阅读 Web 服务器日志。

**为什么 SRE 关心：** Web 服务器是几乎所有服务的前门。Nginx 和 Apache 配置、日志分析、性能调优和故障排查是 SRE 的核心技能。理解 Web 服务器如何处理请求——从接受 TCP 连接 到发送响应——有助于你调试从页面缓慢到连接超时再到 502 错误的各种问题。

<!-- ZH_RESOURCES -->
- [Nginx 入门指南](https://nginx.org/en/docs/beginners_guide.html) -- 类型：教程，时长：30m
- [DigitalOcean - 如何安装 Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04) -- 类型：教程，时长：20m
- [Apache 与 Nginx 对比 - DigitalOcean](https://www.digitalocean.com/community/tutorials/apache-vs-nginx-practical-considerations) -- 类型：文章，时长：15m
- [Nginx 文档](https://nginx.org/en/docs/) -- 类型：参考，时长：不定

<!-- ZH_UI -->
1. 安装 Nginx 并提供一个静态 HTML 页面
2. 配置 Nginx 根据 URL 路径提供不同内容
3. 理解 Web 服务器与 Flask 开发服务器之间的区别
4. 我的 Web 服务器能用了，但我用的是原始 IP 地址。怎么给站点一个真正的名字？
5. Nginx 正在运行，我可以用 IP 地址访问它。但我需要一个真正的域名——人们能输入的东西。我完全不知道域名是怎么和 IP 地址绑定的，也不知道要让 my-app.example.com 指向我的服务器需要做哪些设置。
6. 我的 Web 服务器通过 HTTP 工作，但我需要 HTTPS。怎么配置 TLS？
7. 我的站点通过 HTTP 能用，但浏览器显示“不安全”警告。我知道我需要 HTTPS，但我完全不知道如何获取证书，也不知道 TLS 到底涉及什么。这一切是怎么运作的，我怎么拿到那把锁？
8. Nginx 正在运行并处理流量。我怎么查看进来的请求？
9. Nginx 正在处理流量，但我对正在发生什么毫无可见性。我的应用真的在响应吗？有错误吗？人们在访问哪些 URL？肯定有个日志在某处能告诉我这一切——它在哪，我怎么看懂它？
