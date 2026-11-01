---
id: media-streaming-cross-continent
title: Streaming Across Continents
zone: self-hosting
edges:
  to: []
difficulty: 3
tags:
  - self-hosting
  - media
  - streaming
  - vps
  - cdn
  - nginx
  - jellyfin
  - plex
  - dns
category: practice
milestones:
  - Understand why cross-continent streaming fails on public internet paths
  - Provision a second VPS in a region close to your users
  - Configure the regional VPS to proxy to your origin VPS
  - Set up latency-based DNS routing to direct users to their nearest VPS
  - Verify 4K streaming works from the remote region
title_zh: "跨洲流式传输"

---


Your home server is in North America. A friend in Asia tries to stream 4K — it buffers constantly. The problem isn't your upload speed or their download speed: it's the path the packets take between the two continents.

The fix is a second cheap VPS near your users, with DNS routing them to it automatically. Traffic between your two VPS nodes travels over the cloud provider's backbone instead of congested public internet. This is a pattern documented in detail at **[Plex 4K Streaming and Cross-Continent Playback](https://blog.esc.sh/plex-cross-continent-4k-streaming/)**.

<!-- DEEP_DIVE -->

## Why it buffers

Public internet routing between continents is unpredictable. Packets from Asia to North America can bounce through multiple carrier handoffs, each adding latency and congestion risk. A 4K stream needs sustained throughput — any congestion event causes a buffer.

This is not a latency problem. Even 150ms round-trip is fine for streaming. The issue is **packet loss and throughput drops** on congested inter-carrier links.

## The poor man's CDN

Big CDNs solve this by having servers everywhere. You can approximate this with two cheap VPS nodes and latency-based DNS:

```
User in Asia
     │
     ▼ (DNS → nearest VPS)
 Asia VPS  ──── cloud backbone ────  US VPS  ── WireGuard ──  Home Server
(nginx proxy)                      (nginx proxy)
```

- **US VPS** — already set up from the previous node. Proxies to your home server via WireGuard.
- **Asia VPS** — new. Proxies to the US VPS over the cloud provider's internal network.
- **DNS** — latency-based routing sends each user to the nearest VPS automatically.

The key insight: traffic between two VPS nodes at the same provider travels the provider's private backbone, not the public internet. Linode (Akamai) nodes between regions use Akamai's backbone. This dramatically reduces packet loss compared to consumer ISP paths.

## Why Linode/Akamai specifically

Linode is now part of Akamai, which operates one of the largest private backbone networks in the world. When you run two Linode VMs in different regions, inter-VM traffic routes over that backbone — the same infrastructure that major CDNs use. A $5–6/month node in Tokyo and another in Newark gives you a path that avoids most of the congested public peering points.

Other providers work too, but the backbone quality varies. Akamai/Linode is the choice documented in **[the original writeup](https://blog.esc.sh/plex-cross-continent-4k-streaming/)** for this pattern.

## Step 1: Provision the regional VPS

Pick a Linode (or equivalent) in a region close to your users — Tokyo, Singapore, Frankfurt, etc. Same specs as your US VPS: cheapest tier, enough bandwidth.

Install nginx:

```bash
sudo apt update && sudo apt install nginx certbot python3-certbot-nginx
```

## Step 2: Configure nginx on the regional VPS

The regional VPS proxies to your US VPS (not directly to your home server):

```nginx
server {
    server_name media.yourdomain.com;

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/media.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/media.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # Disable buffering — pass bytes through immediately
    proxy_buffering off;
    proxy_request_buffering off;

    # Point to your US VPS hostname
    proxy_pass https://media-us.yourdomain.com;
    proxy_set_header Host media-us.yourdomain.com;
    proxy_set_header X-Real-IP $remote_addr;

    client_max_body_size 100M;
}
```

Key settings for media streaming:
- `proxy_buffering off` — nginx passes data through as it arrives rather than buffering the whole response. Essential for video.
- `proxy_request_buffering off` — same for uploads (playback position sync, etc).

Get the cert:

```bash
sudo certbot --nginx -d media.yourdomain.com
```

## Step 3: DNS with latency-based routing

You need DNS that routes each user to their nearest VPS. Two options:

**AWS Route 53 (straightforward):** Create two A records for `media.yourdomain.com` — one pointing to your US VPS IP, one to your Asia VPS IP — both with a **Latency** routing policy and their respective regions. Route 53 resolves to whichever has lower latency from the user's location. Cost: ~$0.50/month for a hosted zone plus minimal query costs.

**Cloudflare Load Balancing:** Cloudflare's load balancer with geographic steering does the same thing. Costs more than Route 53 for this use case.

Either way, give the regional record a shorter TTL (60s) so failover works if a VPS goes down.

## Step 4: US VPS — nothing changes

Your US VPS already proxies to your home server via WireGuard. No changes needed there. The Asia VPS just treats the US VPS as its upstream.

## What this solves and what it doesn't

This fixes throughput problems caused by congested public internet paths. It does not reduce round-trip latency — that's physical distance and can't be fixed without a server closer to the user.

For most media streaming use cases (Jellyfin, Plex), latency doesn't matter. Buffering does. This pattern eliminates the buffering.

Cost: one extra VPS, ~$5–6/month. For multiple distant regions, add more nodes — the pattern scales linearly.

<!-- RESOURCES -->

- [Plex 4K Cross-Continent Streaming](https://blog.esc.sh/plex-cross-continent-4k-streaming/) -- type: guide, time: 20min
- [Expose Self-Hosted Services to the Internet](https://blog.esc.sh/expose-selfhosted-services-to-internet/) -- type: guide, time: 30min
- [AWS Route 53 Latency Routing](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-latency.html) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
你的家庭服务器位于北美。一位在亚洲的朋友尝试流式播放 4K 视频——却频繁缓冲。问题不在于你的上传速度或对方的下载速度，而在于数据包往返于两大洲之间所经过的网络路径。

解决方案是在用户附近部署一台廉价 VPS，并通过 DNS 自动将用户路由到该节点。两台 VPS 节点之间的流量将经由云服务商的骨干网传输，而非拥堵的公共互联网。这一模式在 **[Plex 4K Streaming and Cross-Continent Playback](https://blog.esc.sh/plex-cross-continent-4k-streaming/)** 中有详细记录。

<!-- ZH_DEEP_DIVE -->
## 为什么会缓冲

跨洲的公网路由是不可预测的。从亚洲到北美的数据包可能经过多个运营商的多次转手，每一次都会增加延迟和拥塞风险。4K 流媒体需要持续稳定的吞吐量——任何拥塞事件都会导致缓冲。

这不是延迟问题。即使是 150ms 的往返时间，对流媒体来说也没问题。问题在于**拥塞的跨运营商链路上的丢包和吞吐量下降**。

## 穷人版 CDN

大型 CDN 通过在各处部署服务器来解决这个问题。你可以用两个便宜的 VPS 节点加上基于延迟的 DNS 来近似实现：

```
亚洲用户
     │
     ▼ (DNS → 最近的 VPS)
 亚洲 VPS  ──── 云骨干网 ────  美国 VPS  ── WireGuard ──  家庭服务器
(nginx 代理)                      (nginx 代理)
```

- **美国 VPS** —— 已在上一节点中搭建完成。通过 WireGuard 代理到你的家庭服务器。
- **亚洲 VPS** —— 新增。通过云服务商的内部网络代理到美国 VPS。
- **DNS** —— 基于延迟的路由会自动将每个用户发送到最近的 VPS。

关键洞察：同一服务商的两个 VPS 节点之间的流量走的是服务商的私有骨干网，而不是公网。Linode（Akamai）跨区域的节点之间使用 Akamai 的骨干网。与消费者 ISP 路径相比，这大幅降低了丢包。

## 为什么特别选 Linode/Akamai

Linode 现在隶属于 Akamai，后者运营着世界上最大的私有骨干网络之一。当你在不同区域运行两台 Linode 虚拟机时，虚拟机之间的流量会走那条骨干网——也就是大型 CDN 使用的同一套基础设施。一台在东京、另一台在纽瓦克的每月 5–6 美元的节点，就能给你一条避开大多数拥塞公网对等点的路径。

其他服务商也可以，但骨干网质量参差不齐。Akamai/Linode 是**[原始文章](https://blog.esc.sh/plex-cross-continent-4k-streaming/)**中为这种模式记录的选择。

## 第 1 步：开通区域 VPS

在靠近用户的区域选一台 Linode（或同等产品）——东京、新加坡、法兰克福等。规格与美国 VPS 相同：最低档，带宽足够即可。

安装 nginx：

```bash
sudo apt update && sudo apt install nginx certbot python3-certbot-nginx
```

## 第 2 步：在区域 VPS 上配置 nginx

区域 VPS 代理到你的美国 VPS（而不是直接代理到家庭服务器）：

```nginx
server {
    server_name media.yourdomain.com;

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/media.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/media.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # Disable buffering — pass bytes through immediately
    proxy_buffering off;
    proxy_request_buffering off;

    # Point to your US VPS hostname
    proxy_pass https://media-us.yourdomain.com;
    proxy_set_header Host media-us.yourdomain.com;
    proxy_set_header X-Real-IP $remote_addr;

    client_max_body_size 100M;
}
```

媒体流的关键设置：
- `proxy_buffering off` —— nginx 在数据到达时直接透传，而不是缓冲整个响应。对视频至关重要。
- `proxy_request_buffering off` —— 对上传（播放位置同步等）同理。

获取证书：

```bash
sudo certbot --nginx -d media.yourdomain.com
```

## 第 3 步：基于延迟路由的 DNS

你需要能把每个用户路由到最近 VPS 的 DNS。两个选项：

**AWS Route 53（直接了当）：** 为 `media.yourdomain.com` 创建两条 A 记录——一条指向你的美国 VPS IP，一条指向你的亚洲 VPS IP——两者都使用 **Latency** 路由策略并设置各自的区域。Route 53 会解析到从用户位置延迟更低的那一个。费用：托管区域约 $0.50/月，加上极少的查询费用。

**Cloudflare Load Balancing：** Cloudflare 带地理引导的负载均衡器做同样的事。在这个用例下比 Route 53 贵。

无论哪种方式，给区域记录设置较短的 TTL（60s），这样某个 VPS 宕机时故障转移才能生效。

## 第 4 步：美国 VPS —— 无需改动

你的美国 VPS 已经通过 WireGuard 代理到家庭服务器。那里不需要任何改动。亚洲 VPS 只是把美国 VPS 当作它的上游。

## 这解决了什么，没解决什么

这修复了由拥塞公网路径导致的吞吐量问题。它不降低往返延迟——那是物理距离，没有更靠近用户的服务器就无法解决。

对大多数媒体流用例（Jellyfin、Plex）来说，延迟不重要，缓冲才重要。这种模式消除了缓冲。

成本：多一台 VPS，约 $5–6/月。对于多个遥远区域，增加更多节点——这种模式可线性扩展。

<!-- ZH_RESOURCES -->
- [Plex 4K 跨洲串流](https://blog.esc.sh/plex-cross-continent-4k-streaming/) -- 类型: 指南, 时长: 20 分钟
- [将自托管服务暴露到互联网](https://blog.esc.sh/expose-selfhosted-services-to-internet/) -- 类型: 指南, 时长: 30 分钟
- [AWS Route 53 延迟路由](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-latency.html) -- 类型: 参考, 时长: 10 分钟

<!-- ZH_UI -->
1. 理解跨洲流媒体在公共互联网路径上失败的原因
2. 在靠近用户的区域开通第二台 VPS
3. 配置区域 VPS 反向代理到源站 VPS
4. 设置基于延迟的 DNS 路由，将用户引导至最近的 VPS
5. 验证从远程区域可正常进行 4K 流媒体播放
