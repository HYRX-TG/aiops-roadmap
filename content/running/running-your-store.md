---
id: running-your-store
title: Running Your Store
zone: running
edges:
  to:
    - id: your-store-takes-off
      zone: scaling
      question: My store is live — but it's on a single server. What happens when that isn't enough?
      detail: >-
        It's running and I'm proud of it. But I know this is fragile — one
        server, one point of failure. If it goes down, the store goes down. And
        if traffic actually grows, I have no idea how this handles it. What does
        the next step look like?
    - id: manual-deploy-is-painful
      zone: delivery
      question: >-
        Deploying was exciting the first time. Now I dread it — too many
        manual steps and I always forget something.
      detail: >-
        I SSH in, pull the code, restart the service, check the logs, hope
        nothing broke. Every deploy is stressful and I've already shipped a
        broken config once because I forgot a step. There has to be a way to
        make this automatic and repeatable.
    - id: what-is-sre
      zone: sre
      question: My store is live. Now I'm responsible for keeping it up. How do people think about that?
      detail: >-
        I deployed it and it works. But now what? I have no idea how to know
        if it's actually reliable, or what to do when it breaks at 2 AM, or
        how to think about uptime as a goal. Is there a discipline for this?
difficulty: 2
tags:
  - deployment
  - gunicorn
  - nginx
  - certbot
  - systemd
  - production
category: practice
milestones:
  - Deploy a Flask app on a cloud VM with Gunicorn and Nginx
  - 'Configure DNS, obtain a TLS certificate, and serve over HTTPS'
  - Access your running app from your phone using your domain name
title_zh: "运行你的商店"

---


This is it. You have built an ecommerce store — Flask app, database, the works. You understand networking, servers, Linux, web servers, DNS, and TLS. Now you are going to put it all together: take your app from your laptop and get it running on a real server, with a real domain name, over HTTPS, accessible to anyone in the world. This is the full deployment walkthrough.

<!-- DEEP_DIVE -->

**The goal:** Go from `localhost:5000` on your laptop to `https://mystore.com` accessible to anyone.

**What you need before starting:**
- A cloud VM with a public IP (from a provider like DigitalOcean — $6/month)
- A registered domain name (from Namecheap, Cloudflare, Porkbun — ~$10/year)
- Your application code in a Git repository
- SSH access to your server

**Step 1: Set up the server**

You already know how to do this from the Linux basics:

```bash
# SSH into your server
ssh deploy@143.198.100.50

# Update the system
sudo apt update && sudo apt upgrade -y

# Install everything you need
sudo apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx
```

**Step 2: Deploy your application code**

```bash
# Clone your repository
cd /home/deploy
git clone https://github.com/you/mystore.git
cd mystore

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**Step 3: Test with Gunicorn**

Gunicorn is a production WSGI server. It replaces Flask's built-in development server:

```bash
# Test that your app runs
gunicorn -w 4 -b 127.0.0.1:5000 app:app

# -w 4: run 4 worker processes (handles 4 requests simultaneously)
# -b 127.0.0.1:5000: bind to localhost port 5000
# app:app: the Flask application object
```

Visit `http://143.198.100.50:5000` — wait, that will not work. Gunicorn is listening on `127.0.0.1` (localhost only). That is intentional — Nginx will be the public-facing front end. Press `Ctrl+C` to stop Gunicorn for now.

**Step 4: Create a systemd service**

You want Gunicorn to start automatically and restart if it crashes:

```ini
# Create /etc/systemd/system/mystore.service
[Unit]
Description=My Store - Gunicorn
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/mystore
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable mystore
sudo systemctl start mystore
sudo systemctl status mystore
# Should show "active (running)"
```

**Step 5: Configure Nginx as a reverse proxy**

Nginx receives HTTP requests from the internet and forwards them to Gunicorn:

```nginx
# /etc/nginx/sites-available/mystore
server {
    listen 80;
    server_name mystore.com www.mystore.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/deploy/mystore/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/mystore /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default   # Remove default site

# Test the config and reload
sudo nginx -t
sudo systemctl reload nginx
```

Now visit `http://143.198.100.50` — you should see your app. Nginx is receiving the request on port 80 and proxying it to Gunicorn on port 5000.

**Step 6: Point your domain at the server**

In your domain registrar's DNS settings, create A records:

```
Type: A    Name: @              Value: 143.198.100.50    TTL: 300
Type: A    Name: www            Value: 143.198.100.50    TTL: 300
```

Wait a few minutes for DNS propagation, then verify:

```bash
dig mystore.com +short
# Should return 143.198.100.50
```

Visit `http://mystore.com` — your app should load. You are now serving your app on your own domain.

**Step 7: Enable HTTPS with Certbot**

The final step — encrypt everything with a free Let's Encrypt certificate:

```bash
sudo certbot --nginx -d mystore.com -d www.mystore.com
```

Certbot will:
1. Verify you control the domain (by placing a file and having Let's Encrypt check it)
2. Obtain a TLS certificate
3. Automatically update your Nginx config to serve HTTPS on port 443
4. Set up HTTP → HTTPS redirect
5. Configure auto-renewal (certificates expire every 90 days)

```bash
# Verify auto-renewal works
sudo certbot renew --dry-run
```

**Step 8: Set up the firewall**

Lock down everything except what you need:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP (for redirect to HTTPS)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

**You are live.** Open your phone, type `https://mystore.com`, and see your store. The padlock icon shows HTTPS is working. Your friend across the country can access it. Anyone in the world can access it.

**What is actually happening on every request:**

```
Customer's phone
  → DNS lookup: mystore.com → 143.198.100.50
  → TCP connection to 143.198.100.50:443
  → TLS handshake (certificate verified, encryption established)
  → HTTP request: GET /products
  → Nginx receives the request
  → Nginx proxies to Gunicorn at 127.0.0.1:5000
  → Gunicorn hands it to a Flask worker
  → Flask processes the request, queries the database
  → Response travels back: Flask → Gunicorn → Nginx → TLS encryption → Internet → Phone
  → Customer sees the products page
```

Every piece of this — TCP, HTTP, DNS, TLS, Nginx, Gunicorn, systemd — is something you learned on the way here. Nothing is magic anymore.

**The deployment checklist:**

- [ ] Cloud VM running Ubuntu with a public IP
- [ ] Non-root user with SSH key authentication
- [ ] Application code cloned and dependencies installed
- [ ] Gunicorn running your app as a systemd service
- [ ] Nginx configured as a reverse proxy
- [ ] Domain A records pointing to your server
- [ ] TLS certificate installed with Certbot
- [ ] Firewall configured (UFW: 22, 80, 443)
- [ ] Site accessible at `https://yourdomain.com`

This is a real deployment. It is manual, it is a single server, and it will not scale to millions of users. But it is real — and every concept from here on (containers, CI/CD, load balancers, auto-scaling) builds on this foundation. You just deployed a web application. That is a genuine accomplishment.

<!-- RESOURCES -->

- [DigitalOcean - Deploy Flask with Gunicorn and Nginx](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04) -- type: tutorial, time: 45m
- [Certbot Instructions for Nginx on Ubuntu](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal) -- type: tutorial, time: 15m
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) -- type: reference, time: 15m
- [UFW Essentials - DigitalOcean](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands) -- type: reference, time: 15m

<!-- ZH_SUMMARY -->
就是这样。你已经构建了一个电商商店——Flask 应用、数据库，一应俱全。你理解了网络、服务器、Linux、Web 服务器、DNS 和 TLS。现在你要把这一切整合起来：把你的应用从笔记本电脑上带走，让它在真实服务器上运行，拥有真实的域名，通过 HTTPS 访问，世界上任何人都能访问。这就是完整的部署演练。

<!-- ZH_DEEP_DIVE -->
**目标：** 从你笔记本电脑上的 `localhost:5000` 到任何人都能访问的 `https://mystore.com`。

**开始之前你需要准备：**
- 一台带公网 IP 的云 VM（来自 DigitalOcean 之类的提供商——每月 $6）
- 一个已注册的域名（来自 Namecheap、Cloudflare、Porkbun——约 $10/年）
- 你的应用代码放在 Git 仓库中
- 对服务器的 SSH 访问权限

**第 1 步：设置服务器**

你已经从 Linux 基础中知道如何做这件事：

```bash
# SSH into your server
ssh deploy@143.198.100.50

# Update the system
sudo apt update && sudo apt upgrade -y

# Install everything you need
sudo apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx
```

**第 2 步：部署你的应用代码**

```bash
# Clone your repository
cd /home/deploy
git clone https://github.com/you/mystore.git
cd mystore

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**第 3 步：用 Gunicorn 测试**

Gunicorn 是一个生产级 WSGI 服务器。它取代 Flask 内置的开发服务器：

```bash
# Test that your app runs
gunicorn -w 4 -b 127.0.0.1:5000 app:app

# -w 4: run 4 worker processes (handles 4 requests simultaneously)
# -b 127.0.0.1:5000: bind to localhost port 5000
# app:app: the Flask application object
```

访问 `http://143.198.100.50:5000`——等等，这样不行。Gunicorn 监听的是 `127.0.0.1`（仅 localhost）。这是有意为之——Nginx 将作为面向公众的前端。现在按 `Ctrl+C` 停止 Gunicorn。

**第 4 步：创建一个 systemd 服务**

你希望 Gunicorn 自动启动，并在崩溃时重启：

```ini
# Create /etc/systemd/system/mystore.service
[Unit]
Description=My Store - Gunicorn
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/mystore
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable mystore
sudo systemctl start mystore
sudo systemctl status mystore
# Should show "active (running)"
```

**第 5 步：将 Nginx 配置为反向代理**

Nginx 接收来自互联网的 HTTP 请求，并将它们转发给 Gunicorn：

```nginx
# /etc/nginx/sites-available/mystore
server {
    listen 80;
    server_name mystore.com www.mystore.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/deploy/mystore/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/mystore /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default   # Remove default site

# Test the config and reload
sudo nginx -t
sudo systemctl reload nginx
```

现在访问 `http://143.198.100.50`——你应该能看到你的应用。Nginx 在 80 端口接收请求，并将其代理到 5000 端口上的 Gunicorn。

**第 6 步：将你的域名指向服务器**

在你的域名注册商的 DNS 设置中，创建 A 记录：

```
Type: A    Name: @              Value: 143.198.100.50    TTL: 300
Type: A    Name: www            Value: 143.198.100.50    TTL: 300
```

等待几分钟让 DNS 传播，然后验证：

```bash
dig mystore.com +short
# Should return 143.198.100.50
```

访问 `http://mystore.com`——你的应用应该能加载。你现在正在自己的域名上提供应用服务。

**第 7 步：用 Certbot 启用 HTTPS**

最后一步——用免费的 Let's Encrypt 证书加密一切：

```bash
sudo certbot --nginx -d mystore.com -d www.mystore.com
```

Certbot 将会：
1. 验证你控制该域名（通过放置一个文件并让 Let's Encrypt 检查它）
2. 获取 TLS 证书
3. 自动更新你的 Nginx 配置，在 443 端口上提供 HTTPS
4. 设置 HTTP → HTTPS 重定向
5. 配置自动续期（证书每 90 天过期）

```bash
# Verify auto-renewal works
sudo certbot renew --dry-run
```

**第 8 步：设置防火墙**

锁定除你需要的一切之外的所有内容：

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP (for redirect to HTTPS)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

**你已上线。** 打开你的手机，输入 `https://mystore.com`，看到你的商店。挂锁图标表示 HTTPS 正常工作。你全国各地的朋友可以访问它。世界上任何人都可以访问它。

**每个请求实际发生的过程：**

```
Customer's phone
  → DNS lookup: mystore.com → 143.198.100.50
  → TCP connection to 143.198.100.50:443
  → TLS handshake (certificate verified, encryption established)
  → HTTP request: GET /products
  → Nginx receives the request
  → Nginx proxies to Gunicorn at 127.0.0.1:5000
  → Gunicorn hands it to a Flask worker
  → Flask processes the request, queries the database
  → Response travels back: Flask → Gunicorn → Nginx → TLS encryption → Internet → Phone
  → Customer sees the products page
```

这一切的每一部分——TCP、HTTP、DNS、TLS、Nginx、Gunicorn、systemd——都是你一路走来学到的。不再有任何魔法。

**部署检查清单：**

- [ ] 运行 Ubuntu 且带公网 IP 的云 VM
- [ ] 使用 SSH 密钥认证的非 root 用户
- [ ] 应用代码已克隆且依赖已安装
- [ ] Gunicorn 作为 systemd 服务运行你的应用
- [ ] Nginx 配置为反向代理
- [ ] 域名 A 记录指向你的服务器
- [ ] 使用 Certbot 安装 TLS 证书
- [ ] 防火墙已配置（UFW：22、80、443）
- [ ] 站点可通过 `https://yourdomain.com` 访问

这是一次真实的部署。它是手动的，是单台服务器，并且无法扩展到数百万用户。但它是真实的——从这里往后的每一个概念（容器、CI/CD、负载均衡器、自动扩缩容）都建立在这个基础之上。你刚刚部署了一个 Web 应用。这是一项真正的成就。

<!-- ZH_RESOURCES -->
- [DigitalOcean - 使用 Gunicorn 和 Nginx 部署 Flask](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04) -- 类型: 教程, 时长: 45分钟
- [Ubuntu 上 Nginx 的 Certbot 指南](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal) -- 类型: 教程, 时长: 15分钟
- [Nginx 反向代理指南](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) -- 类型: 参考, 时长: 15分钟
- [UFW 基础 - DigitalOcean](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands) -- 类型: 参考, 时长: 15分钟

<!-- ZH_UI -->
1. 在云虚拟机上使用 Gunicorn 和 Nginx 部署 Flask 应用
2. 配置 DNS、获取 TLS 证书，并通过 HTTPS 提供服务
3. 使用你的域名从手机访问正在运行的应用
4. 我的商店已上线——但它运行在单台服务器上。当这不够用时会发生什么？
5. 它正在运行，我为此感到自豪。但我知道这很脆弱——单台服务器，单点故障。如果它宕机，商店就会下线。而且如果流量真的增长，我不知道它该如何应对。下一步是什么样的？
6. 第一次部署很令人兴奋。现在我却害怕它——手动步骤太多，我总是忘记某些东西。
7. 我通过 SSH 登录、拉取代码、重启服务、检查日志，祈祷没有出问题。每次部署都充满压力，而且我已经因为忘记一个步骤而发布过一次损坏的配置。一定有一种方法可以让这件事变得自动化和可重复。
8. 我的商店已上线。现在我有责任让它保持运行。人们是如何思考这件事的？
9. 我部署了它，它能工作。但现在呢？我不知道如何判断它是否真正可靠，或者在凌晨 2 点它出故障时该做什么，也不知道如何将正常运行时间作为一个目标来思考。是否有这样一门学科？
