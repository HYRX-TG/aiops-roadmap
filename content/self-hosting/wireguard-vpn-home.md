---
id: wireguard-vpn-home
title: 'WireGuard: Run Your Own VPN Server at Home'
zone: self-hosting
edges:
  to: []
difficulty: 3
tags:
  - self-hosting
  - wireguard
  - vpn
  - networking
  - remote-access
category: tool
milestones:
  - Install WireGuard on your home server
  - Generate server and client key pairs
  - Configure port forwarding on your router for WireGuard's UDP port
  - Configure a client (phone or laptop) and connect successfully
  - Access a home service through the tunnel
title_zh: "WireGuard：在家中运行你自己的 VPN 服务器"

---


WireGuard is a modern VPN protocol — fast, cryptographically strong, and built into the Linux kernel. Running it yourself means you own the entire stack: no third-party accounts, no service limits, no dependency on anyone else.

The trade-off: you manage it. Key generation, client configs, port forwarding on your router, dynamic DNS for your changing home IP. It's not hard, but there are more moving parts than Tailscale.

<!-- DEEP_DIVE -->

## How WireGuard works

WireGuard is fundamentally different from older VPNs. There are no usernames, passwords, or certificate authorities. Instead, each peer (your server and each client device) has a public/private key pair. You exchange public keys and configure allowed IPs — that's the entire trust model.

The result is a virtual network interface (`wg0`) that looks like a regular network interface. Traffic routed through it is encrypted using the peer's public key, and only the peer with the matching private key can decrypt it.

## The prerequisites

Unlike Tailscale, WireGuard requires:

1. **An open UDP port on your router** — typically 51820. You need to port-forward this to your home server.
2. **Dynamic DNS** — your home IP changes. Set up a DDNS hostname (DuckDNS or Cloudflare) so clients always know where to reach your server.

## wg-easy: the recommended starting point

Rather than configuring WireGuard by hand, run [wg-easy](https://github.com/wg-easy/wg-easy) — a Docker container that gives you a simple web UI for managing clients. It handles key generation and config file creation for each peer.

```yaml
services:
  wg-easy:
    image: ghcr.io/wg-easy/wg-easy
    environment:
      - WG_HOST=your-ddns-hostname.duckdns.org
      - PASSWORD_HASH=<bcrypt hash of your UI password>
    volumes:
      - ~/.wg-easy:/etc/wireguard
    ports:
      - "51820:51820/udp"
      - "51821:51821/tcp"
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
      - net.ipv4.ip_forward=1
    restart: unless-stopped
```

The web UI lets you create a new client, download its config as a `.conf` file or scan a QR code, and revoke access at any time.

## Client setup

Each client (phone, laptop) needs the WireGuard app installed. You import the config file from wg-easy and connect. The tunnel is established directly to your home server over the internet.

## Split tunneling

By default you can configure whether clients route *all* their traffic through your home (full tunnel) or only traffic destined for your home network (split tunnel). Split tunneling is usually what you want for remote access to home services — your regular internet browsing stays on the local network.

## When WireGuard makes more sense than Tailscale

- You don't want any third-party service involved (pure self-hosted)
- You have users who won't or can't create a Tailscale account
- You want to control exactly which clients exist and revoke them without a dashboard login
- You're running a larger household and want no device limits

<!-- RESOURCES -->

- [wg-easy on GitHub](https://github.com/wg-easy/wg-easy) -- type: guide, time: 20min
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/) -- type: reference, time: 15min
- [DuckDNS (free dynamic DNS)](https://www.duckdns.org/) -- type: tool, time: 5min

<!-- ZH_SUMMARY -->
WireGuard 是一种现代 VPN 协议——速度快、加密强度高，并且内置于 Linux 内核。自行运行意味着你掌控整个技术栈：没有第三方账户、没有服务限制、不依赖任何人。

代价是：你需要自己管理它。密钥生成、客户端配置、路由器上的端口转发、为不断变化的家庭 IP 配置动态 DNS。这并不难，但涉及的环节比 Tailscale 更多。

<!-- ZH_DEEP_DIVE -->
## WireGuard 的工作原理

WireGuard 与老式 VPN 有着本质区别。它没有用户名、密码或证书颁发机构。相反，每个对等节点（你的服务器和每个客户端设备）都有一对公钥/私钥。你交换公钥并配置允许的 IP——这就是整个信任模型。

最终得到一个虚拟网络接口（`wg0`），它看起来就像一个普通的网络接口。通过它路由的流量会使用对等节点的公钥加密，只有持有匹配私钥的对等节点才能解密。

## 前提条件

与 Tailscale 不同，WireGuard 需要：

1. **路由器上开放一个 UDP 端口**——通常是 51820。你需要将此端口转发到你的家庭服务器。
2. **动态 DNS**——你的家庭 IP 会变化。设置一个 DDNS 主机名（DuckDNS 或 Cloudflare），以便客户端始终知道如何连接到你的服务器。

## wg-easy：推荐的起点

与其手动配置 WireGuard，不如运行 [wg-easy](https://github.com/wg-easy/wg-easy)——一个 Docker 容器，为你提供一个简单的 Web UI 来管理客户端。它负责为每个对等节点生成密钥和创建配置文件。

```yaml
services:
  wg-easy:
    image: ghcr.io/wg-easy/wg-easy
    environment:
      - WG_HOST=your-ddns-hostname.duckdns.org
      - PASSWORD_HASH=<bcrypt hash of your UI password>
    volumes:
      - ~/.wg-easy:/etc/wireguard
    ports:
      - "51820:51820/udp"
      - "51821:51821/tcp"
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
      - net.ipv4.ip_forward=1
    restart: unless-stopped
```

Web UI 让你可以创建新客户端、将其配置下载为 `.conf` 文件或扫描二维码，并随时撤销访问权限。

## 客户端设置

每个客户端（手机、笔记本电脑）都需要安装 WireGuard 应用。你从 wg-easy 导入配置文件并连接。隧道会通过互联网直接建立到你的家庭服务器。

## 拆分隧道

默认情况下，你可以配置客户端是将*所有*流量都路由到你的家庭网络（全隧道），还是只路由发往你家庭网络的流量（拆分隧道）。对于远程访问家庭服务，拆分隧道通常是你想要的——你日常的互联网浏览仍留在本地网络上。

## 何时 WireGuard 比 Tailscale 更合适

- 你不想涉及任何第三方服务（纯自托管）
- 你有不会或无法创建 Tailscale 账户的用户
- 你想精确控制存在哪些客户端，并在无需登录仪表盘的情况下撤销它们
- 你运营一个较大的家庭，并且不想有设备数量限制

<!-- ZH_RESOURCES -->
- [GitHub 上的 wg-easy](https://github.com/wg-easy/wg-easy) -- 类型：指南，时长：20 分钟
- [WireGuard 快速入门](https://www.wireguard.com/quickstart/) -- 类型：参考，时长：15 分钟
- [DuckDNS（免费动态 DNS）](https://www.duckdns.org/) -- 类型：工具，时长：5 分钟

<!-- ZH_UI -->
1. 在家用服务器上安装 WireGuard
2. 生成服务器和客户端密钥对
3. 在路由器上为 WireGuard 的 UDP 端口配置端口转发
4. 配置客户端（手机或笔记本电脑）并成功连接
5. 通过隧道访问家庭服务
