---
id: dns
title: 'DNS: How Names Become Addresses'
zone: networking
difficulty: 1
tags:
  - dns
  - domain
  - nameserver
  - records
  - dig
  - resolution
edges:
  to:
    - id: dns-and-domain-names
      zone: running
      question: >-
        I understand how DNS works now. How do I actually get a domain name
        and point it at my own server?
      detail: >-
        I get the theory — resolvers, authoritative nameservers, A records.
        But I've never actually bought a domain or configured DNS records for
        something I'm running. How does that actually work in practice?
category: concept
milestones:
  - >-
    Explain what happens between typing a domain name and the first packet being
    sent
  - Use dig to look up DNS records for a domain
  - Identify the common DNS record types and what each is used for
title_zh: "DNS：名称如何变为地址"

---


You've never typed `142.250.80.100` into your browser. You type `google.com`. But the internet only knows about IP addresses — there's no such thing as `google.com` at the network level. Something has to translate the name into an address before a single packet can be sent. That translation is **DNS** — the Domain Name System. It runs silently before every web request, every email, and every API call you've ever made.

<!-- DEEP_DIVE -->

**How a DNS lookup works:**

When you type `google.com`, your computer doesn't know the IP. Here's what happens:

```
1. Your computer checks its local cache — has it looked this up recently?
2. If not, it asks your configured DNS resolver (usually your ISP's or 8.8.8.8)
3. The resolver asks a root nameserver: "who handles .com?"
4. The root nameserver says: "ask the .com TLD nameserver"
5. The TLD nameserver says: "ask Google's authoritative nameserver"
6. Google's nameserver answers: "google.com is 142.250.80.100"
7. Your computer connects to that IP
```

This whole process takes milliseconds. The result is cached so subsequent lookups are instant.

```bash
# Look up a domain's IP
dig google.com

# See the full resolution chain
dig +trace google.com

# Look up a specific record type
dig MX gmail.com      # mail servers
dig TXT github.com    # text records (often used for verification)
```

**Common DNS record types:**

| Record | Purpose | Example |
|--------|---------|---------|
| `A` | Maps a domain to an IPv4 address | `google.com → 142.250.80.100` |
| `AAAA` | Maps a domain to an IPv6 address | `google.com → 2607:f8b0:...` |
| `CNAME` | Alias — points one name to another | `www.example.com → example.com` |
| `MX` | Mail server for the domain | `gmail.com → mail servers` |
| `TXT` | Arbitrary text — used for verification, SPF records | Domain ownership proofs |
| `NS` | Which nameservers are authoritative for this domain | `example.com → ns1.example.com` |

**TTL (Time to Live):** Every DNS record has a TTL — how long resolvers should cache it before asking again. A TTL of 3600 means "cache this for an hour." This is why DNS changes don't take effect instantly — you have to wait for old cached records to expire. Lower TTL = faster propagation, more DNS queries. Higher TTL = slower propagation, fewer queries.

**Why DNS matters for SREs:** DNS is load bearing infrastructure. When DNS breaks, everything breaks — your app, your monitoring, your alerts. DNS is also the first thing to check when a service suddenly becomes unreachable. `dig` is one of the most-used debugging tools in infrastructure work.

<!-- RESOURCES -->

- [How DNS Works - Cloudflare](https://www.cloudflare.com/learning/dns/what-is-dns/) -- type: article, time: 15m
- [DNS record types explained](https://www.cloudflare.com/learning/dns/dns-records/) -- type: article, time: 10m
- [dig command tutorial](https://linuxize.com/post/how-to-use-dig-command-to-query-dns/) -- type: tutorial, time: 10m

<!-- ZH_SUMMARY -->
你从未在浏览器里输入过 `142.250.80.100`，你输入的是 `google.com`。但互联网只认识 IP 地址——在网络层面上根本不存在 `google.com` 这种东西。在发出任何一个数据包之前，必须有某个东西把这个名字翻译成一个地址。这个翻译就是 **DNS**——域名系统。它在你发起的每一次 Web 请求、每一封邮件、每一次 API 调用之前都悄无声息地运行着。

<!-- ZH_DEEP_DIVE -->
**DNS 查询的工作原理：**

当你输入 `google.com` 时，你的计算机并不知道对应的 IP。以下是实际发生的过程：

```
1. 你的计算机检查本地缓存——最近是否查询过该域名？
2. 如果没有，它会向你配置的 DNS 解析器发起查询（通常是你的 ISP 的解析器或 8.8.8.8）
3. 解析器向根域名服务器询问："谁负责 .com？"
4. 根域名服务器回答："去问 .com TLD 域名服务器"
5. TLD 域名服务器回答："去问 Google 的权威域名服务器"
6. Google 的域名服务器回答："google.com 是 142.250.80.100"
7. 你的计算机连接到该 IP
```

整个过程只需几毫秒。结果会被缓存，因此后续查询可以立即返回。

```bash
# 查询某个域名的 IP
dig google.com

# 查看完整的解析链路
dig +trace google.com

# 查询特定类型的记录
dig MX gmail.com      # 邮件服务器
dig TXT github.com    # 文本记录（常用于验证）
```

**常见 DNS 记录类型：**

| 记录 | 用途 | 示例 |
|--------|---------|---------|
| `A` | 将域名映射到 IPv4 地址 | `google.com → 142.250.80.100` |
| `AAAA` | 将域名映射到 IPv6 地址 | `google.com → 2607:f8b0:...` |
| `CNAME` | 别名——将一个名称指向另一个名称 | `www.example.com → example.com` |
| `MX` | 该域名的邮件服务器 | `gmail.com → mail servers` |
| `TXT` | 任意文本——用于验证、SPF 记录 | 域名所有权证明 |
| `NS` | 哪些域名服务器是该域名的权威服务器 | `example.com → ns1.example.com` |

**TTL（Time to Live，生存时间）：** 每条 DNS 记录都有一个 TTL——即解析器在再次查询之前应缓存该记录多长时间。TTL 为 3600 表示“缓存一小时”。这就是 DNS 变更不会立即生效的原因——你必须等待旧的缓存记录过期。TTL 越低 = 传播越快，DNS 查询越多。TTL 越高 = 传播越慢，查询越少。

**为什么 DNS 对 SRE 很重要：** DNS 是承载关键业务的基础设施。当 DNS 出故障时，一切都会出故障——你的应用、你的监控、你的告警。当某个服务突然无法访问时，DNS 也是首先要检查的内容。`dig` 是基础设施工作中最常用的调试工具之一。

<!-- ZH_RESOURCES -->
- [How DNS Works - Cloudflare](https://www.cloudflare.com/learning/dns/what-is-dns/) -- 类型: 文章, 时间: 15m
- [DNS record types explained](https://www.cloudflare.com/learning/dns/dns-records/) -- 类型: 文章, 时间: 10m
- [dig command tutorial](https://linuxize.com/post/how-to-use-dig-command-to-query-dns/) -- 类型: 教程, 时间: 10m

<!-- ZH_UI -->
1. 解释从输入域名到发出第一个数据包之间发生了什么
2. 使用 dig 查询域名的 DNS 记录
3. 识别常见的 DNS 记录类型及其各自用途
4. 我现在理解 DNS 的工作原理了。我该如何实际获取一个域名并将它指向我自己的服务器？
5. 我懂理论——解析器、权威名称服务器、A 记录。但我从未真正购买过域名，也没为我运行的服务配置过 DNS 记录。这在实践中究竟是如何运作的？
