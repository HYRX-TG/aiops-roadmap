---
id: tls-and-certificates
title: 'TLS, Certificates & HTTPS'
zone: running
edges:
  to:
    - id: running-your-store
      question: I understand HTTPS and TLS. How do I put it all together and deploy?
      detail: >-
        I understand the individual pieces — HTTPS, certificates, DNS, web
        server. But I've never done a full deployment from scratch and I'm not
        sure in what order everything goes together or what I'm likely to mess
        up.
difficulty: 2
tags:
  - tls
  - ssl
  - https
  - certificates
  - certificate-authority
  - lets-encrypt
category: concept
milestones:
  - Understand the TLS handshake and what happens when you visit an HTTPS site
  - Explain what a certificate is and what a Certificate Authority does
  - Inspect a website's certificate in your browser or with openssl
title_zh: "TLS、证书与 HTTPS"

---


You visit `https://mybank.com` and type your password. How do you know the connection is actually encrypted? How does your browser know it is really talking to the bank and not an attacker? And how did they establish a shared encryption key without anyone eavesdropping? The answer to all of these is **TLS** — the protocol that makes HTTPS work.

<!-- DEEP_DIVE -->

**TLS** (Transport Layer Security) is the protocol that encrypts HTTP traffic, turning it into HTTPS. It sits between TCP and HTTP — TCP handles reliable delivery, TLS encrypts the data, and HTTP defines the meaning. The older name, **SSL** (Secure Sockets Layer), is technically deprecated but you will still hear people say "SSL certificate" everywhere. They mean TLS.

**The TLS Handshake** is what happens when your browser connects to an HTTPS site. It takes a fraction of a second, but a lot happens:

```
Browser                                    Server
   │                                          │
   ├──── Client Hello ───────────────────────→│  "I want to talk securely.
   │     (supported TLS versions,             │   Here are the ciphers I support."
   │      supported ciphers)                  │
   │                                          │
   │←─── Server Hello ───────────────────────┤  "Let's use TLS 1.3 with
   │     (chosen cipher,                      │   AES-256. Here's my certificate."
   │      server certificate)                 │
   │                                          │
   │     Browser verifies certificate         │  "Is this cert signed by a
   │     against trusted CAs                  │   CA I trust? Is it expired?
   │                                          │   Does the domain match?"
   │                                          │
   ├──── Key Exchange ───────────────────────→│  Both sides generate a shared
   │←────────────────────────────────────────┤  symmetric key using the
   │                                          │  server's public key
   │                                          │
   │←───── Encrypted HTTP traffic ──────────→│  All data is now encrypted
   │       (using symmetric AES key)          │  with the shared key
```

After the handshake, everything is encrypted with AES (symmetric, fast). The asymmetric cryptography was only used during the handshake to securely exchange the symmetric key — exactly the hybrid approach from the encryption basics.

**Certificates** are how the server proves its identity. A certificate is a file that says "this public key belongs to mystore.com" and is signed by a trusted third party. It contains:

- The domain name(s) the certificate is valid for
- The server's public key
- Who issued (signed) the certificate
- When it expires
- A digital signature proving it has not been tampered with

You can inspect any site's certificate:

```bash
# View a website's certificate with openssl
openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | \
  openssl x509 -noout -text | head -20

# Quick check — see the issuer and expiry
openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | \
  openssl x509 -noout -issuer -dates

# Or just click the lock icon in your browser's address bar
```

**Certificate Authorities (CAs)** are the trusted third parties that sign certificates. Your browser and operating system ship with a list of trusted CAs (about 100-150 of them). When a server presents a certificate, your browser checks: "Was this signed by a CA I trust?" If yes, the connection proceeds. If not, you get the scary "Your connection is not private" warning.

The **chain of trust** works like this:

```
Root CA (pre-installed in your browser)
  └── signs → Intermediate CA
                └── signs → Your server's certificate
```

Root CA keys are kept in offline vaults. They sign intermediate CA certificates, and intermediates sign server certificates. If a root CA's key were compromised, every certificate they ever signed would be untrustworthy — so root keys are guarded extremely carefully.

**Let's Encrypt** changed everything. Before 2015, SSL certificates cost $50-300/year and required a manual verification process. Let's Encrypt is a free, automated Certificate Authority that issues certificates in seconds:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get a certificate — fully automated
sudo certbot --nginx -d mystore.com -d www.mystore.com

# Certbot:
# 1. Proves you control the domain (places a file, Let's Encrypt checks it)
# 2. Issues a certificate
# 3. Configures Nginx to use it
# 4. Sets up auto-renewal (certs expire every 90 days)
```

After running Certbot, your Nginx config is updated to serve HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name mystore.com;

    ssl_certificate /etc/letsencrypt/live/mystore.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mystore.com/privkey.pem;

    # ... rest of your config
}

server {
    listen 80;
    server_name mystore.com;
    return 301 https://$server_name$request_uri;  # Redirect HTTP → HTTPS
}
```

**Common TLS issues you will debug as an SRE:**

- **Certificate expired** — Let's Encrypt certs last 90 days. If auto-renewal breaks, your site shows a scary warning. Monitor cert expiry.
- **Domain mismatch** — The certificate says `mystore.com` but you are visiting `www.mystore.com`. Make sure the cert covers all your domains.
- **Mixed content** — Your HTTPS page loads images or scripts over plain HTTP. Browsers block this. All resources must use HTTPS.
- **Intermediate certificate missing** — Your server sends its cert but not the intermediate CA cert. Some browsers fill in the gap, others reject the connection.
- **TLS version too old** — TLS 1.0 and 1.1 are deprecated. Modern browsers require TLS 1.2 or 1.3.

```bash
# Test TLS configuration of a site
curl -vI https://mystore.com 2>&1 | grep -E "SSL|TLS|subject|issuer|expire"

# Check if a cert is valid and not expired
echo | openssl s_client -connect mystore.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**Why SREs care:** TLS certificate management is one of the most common sources of outages. Expired certificates cause immediate, visible failures. Understanding TLS helps you debug connection issues, manage certificate rotation, configure secure defaults, and respond to security advisories about cryptographic vulnerabilities.

<!-- RESOURCES -->

- [Cloudflare - How does TLS work?](https://www.cloudflare.com/learning/ssl/transport-layer-security-tls/) -- type: article, time: 15m
- [Let's Encrypt - How It Works](https://letsencrypt.org/how-it-works/) -- type: article, time: 10m
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/) -- type: tool, time: 5m
- [Certbot Instructions](https://certbot.eff.org/instructions) -- type: tutorial, time: 15m
- [Julia Evans - TLS Zine](https://wizardzines.com/zines/tls/) -- type: zine, time: 15m

<!-- ZH_SUMMARY -->
你访问 `https://mybank.com` 并输入密码。你如何知道连接确实经过了加密？你的浏览器如何知道它真的在与银行通信，而不是与攻击者通信？他们又是如何在无人窃听的情况下建立一个共享加密密钥的？所有这些问题的答案都是 **TLS**——让 HTTPS 得以工作的协议。

<!-- ZH_DEEP_DIVE -->
**TLS**（传输层安全协议）是加密 HTTP 流量的协议，将其转变为 HTTPS。它位于 TCP 和 HTTP 之间——TCP 负责可靠传输，TLS 加密数据，HTTP 定义含义。旧名称 **SSL**（安全套接层）在技术上已被弃用，但你仍会到处听到人们说“SSL 证书”。他们指的是 TLS。

**TLS 握手**是你的浏览器连接到 HTTPS 站点时发生的过程。它只需几分之一秒，但发生了很多事情：

```
Browser                                    Server
   │                                          │
   ├──── Client Hello ───────────────────────→│  "I want to talk securely.
   │     (supported TLS versions,             │   Here are the ciphers I support."
   │      supported ciphers)                  │
   │                                          │
   │←─── Server Hello ───────────────────────┤  "Let's use TLS 1.3 with
   │     (chosen cipher,                      │   AES-256. Here's my certificate."
   │      server certificate)                 │
   │                                          │
   │     Browser verifies certificate         │  "Is this cert signed by a
   │     against trusted CAs                  │   CA I trust? Is it expired?
   │                                          │   Does the domain match?"
   │                                          │
   ├──── Key Exchange ───────────────────────→│  Both sides generate a shared
   │←────────────────────────────────────────┤  symmetric key using the
   │                                          │  server's public key
   │                                          │
   │←───── Encrypted HTTP traffic ──────────→│  All data is now encrypted
   │       (using symmetric AES key)          │  with the shared key
```

握手之后，所有内容都用 AES（对称、快速）加密。非对称加密仅在握手期间用于安全地交换对称密钥——这正是加密基础中的混合方法。

**证书**是服务器证明其身份的方式。证书是一个文件，声明“此公钥属于 mystore.com”，并由受信任的第三方签名。它包含：

- 证书有效的域名
- 服务器的公钥
- 谁颁发（签名）了证书
- 何时过期
- 证明其未被篡改的数字签名

你可以检查任何站点的证书：

```bash
# View a website's certificate with openssl
openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | \
  openssl x509 -noout -text | head -20

# Quick check — see the issuer and expiry
openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | \
  openssl x509 -noout -issuer -dates

# Or just click the lock icon in your browser's address bar
```

**证书颁发机构（CA）**是签署证书的受信任第三方。你的浏览器和操作系统附带一个受信任 CA 列表（大约 100-150 个）。当服务器出示证书时，你的浏览器会检查：“这是由我信任的 CA 签名的吗？”如果是，连接继续。如果不是，你会看到可怕的“你的连接不是私密连接”警告。

**信任链**的工作方式如下：

```
Root CA (pre-installed in your browser)
  └── signs → Intermediate CA
                └── signs → Your server's certificate
```

根 CA 密钥保存在离线保险库中。它们签署中间 CA 证书，中间 CA 签署服务器证书。如果根 CA 的密钥被泄露，它们签署过的每张证书都将不可信——因此根密钥受到极其谨慎的保护。

**Let's Encrypt** 改变了一切。2015 年之前，SSL 证书每年花费 50-300 美元，并且需要手动验证过程。Let's Encrypt 是一个免费、自动化的证书颁发机构，可在几秒钟内颁发证书：

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get a certificate — fully automated
sudo certbot --nginx -d mystore.com -d www.mystore.com

# Certbot:
# 1. Proves you control the domain (places a file, Let's Encrypt checks it)
# 2. Issues a certificate
# 3. Configures Nginx to use it
# 4. Sets up auto-renewal (certs expire every 90 days)
```

运行 Certbot 后，你的 Nginx 配置会更新为提供 HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name mystore.com;

    ssl_certificate /etc/letsencrypt/live/mystore.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mystore.com/privkey.pem;

    # ... rest of your config
}

server {
    listen 80;
    server_name mystore.com;
    return 301 https://$server_name$request_uri;  # Redirect HTTP → HTTPS
}
```

**作为 SRE 你会调试的常见 TLS 问题：**

- **证书过期**——Let's Encrypt 证书有效期为 90 天。如果自动续期失败，你的站点会显示可怕的警告。监控证书过期时间。
- **域名不匹配**——证书上写的是 `mystore.com`，但你访问的是 `www.mystore.com`。确保证书覆盖你所有的域名。
- **混合内容**——你的 HTTPS 页面通过纯 HTTP 加载图片或脚本。浏览器会阻止这种情况。所有资源都必须使用 HTTPS。
- **缺少中间证书**——你的服务器发送了自己的证书，但没有发送中间 CA 证书。有些浏览器会填补这个缺口，其他浏览器会拒绝连接。
- **TLS 版本过旧**——TLS 1.0 和 1.1 已被弃用。现代浏览器要求 TLS 1.2 或 1.3。

```bash
# Test TLS configuration of a site
curl -vI https://mystore.com 2>&1 | grep -E "SSL|TLS|subject|issuer|expire"

# Check if a cert is valid and not expired
echo | openssl s_client -connect mystore.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**为什么 SRE 关心：** TLS 证书管理是最常见的故障来源之一。过期的证书会导致立即、可见的故障。理解 TLS 有助于你调试连接问题、管理证书轮换、配置安全默认值，并响应有关加密漏洞的安全公告。

<!-- ZH_RESOURCES -->
- [Cloudflare - TLS 是如何工作的？](https://www.cloudflare.com/learning/ssl/transport-layer-security-tls/) -- 类型: 文章, 时间: 15m
- [Let's Encrypt - 工作原理](https://letsencrypt.org/how-it-works/) -- 类型: 文章, 时间: 10m
- [SSL Labs 服务器测试](https://www.ssllabs.com/ssltest/) -- 类型: 工具, 时间: 5m
- [Certbot 使用说明](https://certbot.eff.org/instructions) -- 类型: 教程, 时间: 15m
- [Julia Evans - TLS 小志](https://wizardzines.com/zines/tls/) -- 类型: 小志, 时间: 15m

<!-- ZH_UI -->
1. 理解 TLS 握手以及访问 HTTPS 网站时发生了什么
2. 解释什么是证书以及证书颁发机构的作用
3. 在浏览器中或用 openssl 检查网站的证书
4. 我已理解 HTTPS 和 TLS。如何把它们整合起来并部署？
5. 我理解各个独立部分——HTTPS、证书、DNS、Web 服务器。但我从未从零做过完整部署，不确定各部分按什么顺序组合，也不知道容易出错的地方。
