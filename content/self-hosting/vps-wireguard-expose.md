---
id: vps-wireguard-expose
title: 'VPS + WireGuard: Full Control, No Extra Software'
zone: self-hosting
edges:
  to:
    - id: media-streaming-cross-continent
      question: My distant users get buffering — can I fix cross-continent streaming?
      detail: >-
        Friends or family far away get constant buffering even though my
        internet is fast. Is it my upload speed, the physical distance, or
        something about how the VPS is placed?
difficulty: 3
tags:
  - self-hosting
  - vps
  - wireguard
  - nginx
  - tunnel
  - public
category: practice
milestones:
  - Provision a VPS and install WireGuard on it
  - Configure WireGuard on your home server to tunnel to the VPS
  - Bring up the WireGuard tunnel and verify connectivity
  - >-
    Install nginx on the VPS and proxy a public hostname to your home service
    via the tunnel
  - Add HTTPS with Let's Encrypt or Caddy
  - Verify the service is reachable publicly
title_zh: "VPS + WireGuard：完全掌控，无需额外软件"

---


A VPS runs WireGuard and nginx. Your home server connects to the VPS as a WireGuard peer. Traffic arrives at the VPS's public IP, nginx proxies it through the private WireGuard tunnel to your home service — which Cloudflare never touches, and which requires no special software beyond tools you already know.

This approach works for everything: websites, media streaming, any TCP service. No TOS restrictions, no vendor lock-in, and no extra software layer beyond WireGuard and a reverse proxy.

For the setup guides: **[WireGuard VPN Setup — blog.esc.sh](https://blog.esc.sh/wireguard-vpn-setup/)** and **[Expose Self-Hosted Services to the Internet — blog.esc.sh](https://blog.esc.sh/expose-selfhosted-services-to-internet/)**

<!-- DEEP_DIVE -->

## The architecture

```
Internet → VPS public IP → nginx → WireGuard tunnel → your home server → service
                           (10.0.0.1)               (10.0.0.2)
```

The VPS has a public IP. Your home server connects to it as a WireGuard peer and gets a private tunnel IP (`10.0.0.2`). nginx on the VPS proxies incoming requests to `10.0.0.2:<port>` — your home server, through the tunnel.

## Step 1: Set up WireGuard on the VPS

Install WireGuard and generate a key pair:

```bash
sudo apt update && sudo apt install wireguard
wg genkey | sudo tee /etc/wireguard/privatekey | wg pubkey | sudo tee /etc/wireguard/publickey
sudo chmod 400 /etc/wireguard/privatekey
```

VPS config (`/etc/wireguard/wg0.conf`):

```ini
[Interface]
Address = 10.0.0.1/24
PrivateKey = <VPS private key>
ListenPort = 51820

[Peer]
PublicKey = <home server public key>
AllowedIPs = 10.0.0.2/32
```

Start it:

```bash
sudo systemctl enable --now wg-quick@wg0
```

## Step 2: Set up WireGuard on your home server

Same installation process. Home server config:

```ini
[Interface]
PrivateKey = <home server private key>
Address = 10.0.0.2/32

[Peer]
PublicKey = <VPS public key>
Endpoint = <VPS public IP>:51820
AllowedIPs = 10.0.0.1/32
PersistentKeepalive = 25
```

**Important:** `AllowedIPs = 10.0.0.1/32` — only route traffic destined for the VPS tunnel IP through WireGuard. Do **not** set `0.0.0.0/0` here, or all your home server's internet traffic will route through the VPS.

Start it and verify connectivity:

```bash
sudo systemctl enable --now wg-quick@wg0
ping -c 2 10.0.0.1   # should work from home server
```

From the VPS, verify the home server is reachable through the tunnel:

```bash
ping -c 2 10.0.0.2
curl 10.0.0.2:8096    # test reaching Jellyfin (or whatever port)
```

## Step 3: Point DNS to your VPS

Add an A record in your DNS provider pointing your domain (or subdomain) to the VPS's public IP.

## Step 4: Install nginx on the VPS and proxy to home

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

Create a site config (`/etc/nginx/sites-enabled/myservice.yourdomain.com`):

```nginx
server {
    server_name myservice.yourdomain.com;

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/myservice.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myservice.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    location / {
        proxy_pass http://10.0.0.2:8096;   # tunnel IP + your service port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name myservice.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

Get a TLS certificate:

```bash
sudo certbot --nginx -d myservice.yourdomain.com
sudo systemctl reload nginx
```

Alternatively, **Caddy** handles TLS automatically with far less config — just `reverse_proxy 10.0.0.2:8096` and it fetches the cert itself.

## Why this is often the better choice

Compared to Pangolin, there's no extra software layer to maintain — just WireGuard and nginx/Caddy, two tools with decades of documentation and wide community knowledge. If something breaks, the debugging surface is small and well-understood.

Compared to Cloudflare Tunnel, your traffic never passes through a third party, and there are no TOS restrictions — stream all the media you want.

The trade-off is that the setup is fully manual. Changing the WireGuard config, managing nginx vhosts, and renewing certs are your responsibility. It's not hard, but it's more work than a managed UI.

<!-- RESOURCES -->

- [WireGuard VPN Setup Guide](https://blog.esc.sh/wireguard-vpn-setup/) -- type: guide, time: 30min
- [Expose Self-Hosted Services to the Internet](https://blog.esc.sh/expose-selfhosted-services-to-internet/) -- type: guide, time: 30min
- [Caddy Server (auto-HTTPS reverse proxy)](https://caddyserver.com/) -- type: reference, time: 15min
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/) -- type: reference, time: 15min

<!-- ZH_SUMMARY -->
一台 VPS 运行 WireGuard 和 nginx。你的家庭服务器作为 WireGuard 对等节点连接到该 VPS。流量到达 VPS 的公网 IP，nginx 通过私有 WireGuard 隧道将其代理到你的家庭服务——Cloudflare 全程不参与，且除了你已熟悉的工具外无需任何特殊软件。

这种方法适用于一切场景：网站、媒体流、任何 TCP 服务。没有 TOS 限制，没有供应商锁定，除了 WireGuard 和反向代理之外没有额外的软件层。

关于搭建指南：**[WireGuard VPN Setup — blog.esc.sh](https://blog.esc.sh/wireguard-vpn-setup/)** 和 **[Expose Self-Hosted Services to the Internet — blog.esc.sh](https://blog.esc.sh/expose-selfhosted-services-to-internet/)**

<!-- ZH_DEEP_DIVE -->
## 架构

```
互联网 → VPS 公网 IP → nginx → WireGuard 隧道 → 你的家庭服务器 → 服务
                        (10.0.0.1)              (10.0.0.2)
```

VPS 拥有公网 IP。你的家庭服务器作为 WireGuard 对端连接到它，并获得一个私有隧道 IP（`10.0.0.2`）。VPS 上的 nginx 将传入请求代理到 `10.0.0.2:<port>`——也就是通过隧道到达你的家庭服务器。

## 第 1 步：在 VPS 上设置 WireGuard

安装 WireGuard 并生成密钥对：

```bash
sudo apt update && sudo apt install wireguard
wg genkey | sudo tee /etc/wireguard/privatekey | wg pubkey | sudo tee /etc/wireguard/publickey
sudo chmod 400 /etc/wireguard/privatekey
```

VPS 配置（`/etc/wireguard/wg0.conf`）：

```ini
[Interface]
Address = 10.0.0.1/24
PrivateKey = <VPS private key>
ListenPort = 51820

[Peer]
PublicKey = <home server public key>
AllowedIPs = 10.0.0.2/32
```

启动它：

```bash
sudo systemctl enable --now wg-quick@wg0
```

## 第 2 步：在你的家庭服务器上设置 WireGuard

安装过程相同。家庭服务器配置：

```ini
[Interface]
PrivateKey = <home server private key>
Address = 10.0.0.2/32

[Peer]
PublicKey = <VPS public key>
Endpoint = <VPS public IP>:51820
AllowedIPs = 10.0.0.1/32
PersistentKeepalive = 25
```

**重要：** `AllowedIPs = 10.0.0.1/32`——只将通过 WireGuard 发往 VPS 隧道 IP 的流量路由过去。**不要**在这里设置 `0.0.0.0/0`，否则你家庭服务器的所有互联网流量都会经由 VPS 路由。

启动它并验证连通性：

```bash
sudo systemctl enable --now wg-quick@wg0
ping -c 2 10.0.0.1   # should work from home server
```

从 VPS 验证家庭服务器可通过隧道访问：

```bash
ping -c 2 10.0.0.2
curl 10.0.0.2:8096    # test reaching Jellyfin (or whatever port)
```

## 第 3 步：将 DNS 指向你的 VPS

在你的 DNS 提供商处添加一条 A 记录，将你的域名（或子域名）指向 VPS 的公网 IP。

## 第 4 步：在 VPS 上安装 nginx 并代理到家庭服务器

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

创建站点配置（`/etc/nginx/sites-enabled/myservice.yourdomain.com`）：

```nginx
server {
    server_name myservice.yourdomain.com;

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/myservice.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myservice.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    location / {
        proxy_pass http://10.0.0.2:8096;   # tunnel IP + your service port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name myservice.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

获取 TLS 证书：

```bash
sudo certbot --nginx -d myservice.yourdomain.com
sudo systemctl reload nginx
```

或者，**Caddy** 会自动处理 TLS，配置量少得多——只需 `reverse_proxy 10.0.0.2:8096`，它就会自行获取证书。

## 为什么这通常是更好的选择

与 Pangolin 相比，没有额外的软件层需要维护——只有 WireGuard 和 nginx/Caddy，这两个工具拥有数十年的文档积累和广泛的社区知识。如果出问题，调试范围小且易于理解。

与 Cloudflare Tunnel 相比，你的流量永远不会经过第三方，也没有 TOS 限制——想串流多少媒体就串流多少。

代价是这套设置完全手动。修改 WireGuard 配置、管理 nginx 虚拟主机以及续期证书都是你的责任。这并不难，但比使用托管 UI 要多做一些工作。

<!-- ZH_RESOURCES -->
- [WireGuard VPN 搭建指南](https://blog.esc.sh/wireguard-vpn-setup/) -- 类型: 指南, 时长: 30 分钟
- [将自托管服务暴露到互联网](https://blog.esc.sh/expose-selfhosted-services-to-internet/) -- 类型: 指南, 时长: 30 分钟
- [Caddy Server（自动 HTTPS 反向代理）](https://caddyserver.com/) -- 类型: 参考, 时长: 15 分钟
- [WireGuard 快速入门](https://www.wireguard.com/quickstart/) -- 类型: 参考, 时长: 15 分钟

<!-- ZH_UI -->
1. 开通一台 VPS 并在其上安装 WireGuard
2. 在家庭服务器上配置 WireGuard，使其通过隧道连接到 VPS
3. 启动 WireGuard 隧道并验证连通性
4. 在 VPS 上安装 nginx，并通过隧道将公网主机名反向代理到你的家庭服务
5. 使用 Let's Encrypt 或 Caddy 添加 HTTPS
6. 验证该服务可从公网访问
7. 我的异地用户出现缓冲——跨洲串流能修好吗？
8. 远方的朋友或家人即使我的网络很快也一直缓冲。是我的上传带宽、物理距离，还是 VPS 的部署位置有问题？
