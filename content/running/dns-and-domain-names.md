---
id: dns-and-domain-names
title: DNS & Domain Names
zone: running
edges:
  to:
    - id: running-your-store
      question: I have a domain name. How do I put it all together and deploy my app?
      detail: >-
        I've got DNS pointing at my server and all the pieces working
        separately. But I've never assembled them into a real live deployment —
        Nginx in front, HTTPS configured, actual domain in the browser. What
        does putting all of it together actually look like?
difficulty: 1
tags:
  - dns
  - domain-names
  - nameservers
  - udp
  - dig
  - nslookup
category: concept
milestones:
  - Understand how a DNS query resolves a domain name to an IP address
  - Use dig and nslookup to query DNS records
  - Explain why DNS uses UDP and when it falls back to TCP
title_zh: "DNS 与域名"

---


You have a server at `73.42.100.15`. You tell your friend to visit your website. Are you going to say "go to seventy-three dot forty-two dot one hundred dot fifteen"? Of course not. You want them to type `mystore.com`. But computers do not understand `mystore.com` — they need an IP address. Something has to translate the name into a number. That something is **DNS**.

<!-- DEEP_DIVE -->

**DNS** (Domain Name System) is the phone book of the internet. When you type `google.com` into your browser, the very first thing that happens — before any HTTP request, before any TCP connection — is a DNS lookup. Your computer asks "what IP address does `google.com` point to?" and gets back `142.250.80.46`. Only then does the browser connect.

The lookup process is a chain of questions:

1. **Your computer** checks its local cache. Have I looked this up recently? If yes, use the cached answer.
2. **Your router** might have it cached too.
3. **Your ISP's resolver** (or a public resolver like `8.8.8.8` or `1.1.1.1`) handles the actual lookup if nobody has the answer cached.
4. The resolver asks the **root nameservers** — "who handles `.com`?"
5. The root says "ask the `.com` TLD nameservers."
6. The `.com` nameserver says "the nameservers for `google.com` are `ns1.google.com`."
7. The resolver asks `ns1.google.com` — "what is the IP for `google.com`?"
8. The answer comes back: `142.250.80.46`.

All of this happens in milliseconds. The result is cached at multiple levels so subsequent lookups are even faster.

```bash
# Query DNS with dig — the SRE's best friend
dig google.com

# Short answer only
dig google.com +short
# 142.250.80.46

# Trace the full resolution path
dig google.com +trace

# Query a specific DNS server
dig google.com @8.8.8.8      # Google's DNS
dig google.com @1.1.1.1      # Cloudflare's DNS

# nslookup — simpler alternative
nslookup google.com
```

**DNS Record Types** — a domain can have multiple types of records:

| Type | Purpose | Example |
|------|---------|---------|
| **A** | Maps domain to IPv4 address | `mystore.com → 73.42.100.15` |
| **AAAA** | Maps domain to IPv6 address | `mystore.com → 2001:db8::1` |
| **CNAME** | Alias for another domain | `www.mystore.com → mystore.com` |
| **MX** | Mail server for the domain | `mystore.com → mail.mystore.com` |
| **TXT** | Arbitrary text (used for verification, SPF, etc.) | `"v=spf1 include:_spf.google.com"` |
| **NS** | Nameservers responsible for this domain | `mystore.com → ns1.cloudflare.com` |

```bash
# Query specific record types
dig mystore.com A          # IPv4 address
dig mystore.com AAAA       # IPv6 address
dig mystore.com MX         # Mail servers
dig mystore.com NS         # Nameservers
dig mystore.com TXT        # Text records
dig www.mystore.com CNAME  # Aliases
```

**Registering a domain** is straightforward. You go to a registrar (Namecheap, Cloudflare, Porkbun), search for a name, and pay $10-15/year for a `.com`. Then you configure DNS records — at minimum, an **A record** pointing your domain to your server's IP address.

**TTL (Time To Live)** controls how long DNS answers are cached. When you set an A record with a TTL of 3600 (seconds), DNS resolvers will cache that answer for one hour before asking again. Low TTL means changes propagate fast but generate more DNS queries. High TTL means fewer queries but slower updates. When you are about to change servers, lower the TTL ahead of time so the switchover is fast.

**Why does DNS use UDP?**

This is a great question, and the answer teaches you something important about protocol choice. DNS queries are tiny — a question like "what is the IP for google.com?" fits in a single packet (usually under 512 bytes). TCP requires a three-way handshake (SYN, SYN-ACK, ACK) before any data is sent — that is three round trips just to set up the connection, then the actual query, then the teardown. For a small, single-packet question and answer, that overhead is absurd.

UDP lets you fire off one packet with the question and get one packet back with the answer. No handshake, no connection setup, no teardown. For DNS, this means:

- **Faster** — one round trip instead of multiple
- **Less load on DNS servers** — no need to maintain connection state for millions of queries per second
- **Simpler** — if the response does not arrive, just ask again

DNS *does* fall back to TCP in two cases: when the response is too large to fit in a single UDP packet (over 512 bytes, or 4096 with EDNS), and for **zone transfers** between DNS servers (replicating entire zone files). But for 99% of normal DNS lookups, UDP is the right tool.

```bash
# See DNS queries happening in real time (requires tcpdump)
sudo tcpdump -i any port 53

# You will see UDP packets going to and from port 53 (the DNS port)
```

**DNS can fail, and when it does, everything breaks.** If your DNS resolver is down, your browser cannot translate any domain name, and the internet effectively stops working. This is why major outages at DNS providers (like the 2021 Facebook outage where their BGP misconfiguration made their DNS servers unreachable) take down everything. As an SRE, you will monitor DNS health, use multiple DNS providers, and understand DNS propagation delays.

**The `/etc/resolv.conf` file** on Linux tells your system which DNS resolver to use:

```bash
cat /etc/resolv.conf
# nameserver 8.8.8.8
# nameserver 1.1.1.1
```

And `/etc/hosts` lets you override DNS entirely for specific domains — useful for testing:

```bash
# /etc/hosts
127.0.0.1   mystore.com
# Now "mystore.com" points to localhost on this machine
```

<!-- RESOURCES -->

- [Cloudflare - What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/) -- type: article, time: 10m
- [How DNS Works (comic)](https://howdns.works/) -- type: interactive, time: 10m
- [Julia Evans - How DNS Works Zine](https://wizardzines.com/zines/dns/) -- type: zine, time: 15m
- [mess with dns - Experiment with DNS](https://messwithdns.net/) -- type: interactive, time: 30m
- [dig Command Examples](https://www.thegeekstuff.com/2012/02/dig-command-examples/) -- type: reference, time: 15m

<!-- ZH_SUMMARY -->
你有一台服务器，IP 地址是 `73.42.100.15`。你让朋友访问你的网站，你会说“去七十三点四十二点一百点十五”吗？当然不会。你希望他们输入 `mystore.com`。但计算机不理解 `mystore.com`——它们需要 IP 地址。必须有某种东西把名字转换成数字。这个东西就是 **DNS**。

<!-- ZH_DEEP_DIVE -->
**DNS**（Domain Name System，域名系统）是互联网的电话簿。当你在浏览器中输入 `google.com` 时，最先发生的事情——在任何 HTTP 请求之前、在任何 TCP 连接之前——就是一次 DNS 查询。你的计算机会问“`google.com` 指向哪个 IP 地址？”，然后得到 `142.250.80.46`。只有在这之后，浏览器才会发起连接。

查询过程是一连串的提问：

1. **你的计算机**检查本地缓存。我最近查过这个吗？如果有，就使用缓存的答案。
2. **你的路由器**可能也缓存了它。
3. **你的 ISP 的解析器**（或像 `8.8.8.8`、`1.1.1.1` 这样的公共解析器）在没有任何地方缓存答案时处理实际查询。
4. 解析器询问**根域名服务器**——“谁负责 `.com`？”
5. 根服务器说“去问 `.com` TLD 域名服务器。”
6. `.com` 域名服务器说“`google.com` 的域名服务器是 `ns1.google.com`。”
7. 解析器询问 `ns1.google.com`——“`google.com` 的 IP 是什么？”
8. 答案返回：`142.250.80.46`。

所有这些都在毫秒级内完成。结果会在多个层级被缓存，因此后续查询会更快。

```bash
# Query DNS with dig — the SRE's best friend
dig google.com

# Short answer only
dig google.com +short
# 142.250.80.46

# Trace the full resolution path
dig google.com +trace

# Query a specific DNS server
dig google.com @8.8.8.8      # Google's DNS
dig google.com @1.1.1.1      # Cloudflare's DNS

# nslookup — simpler alternative
nslookup google.com
```

**DNS 记录类型**——一个域名可以拥有多种类型的记录：

| 类型 | 用途 | 示例 |
|------|---------|---------|
| **A** | 将域名映射到 IPv4 地址 | `mystore.com → 73.42.100.15` |
| **AAAA** | 将域名映射到 IPv6 地址 | `mystore.com → 2001:db8::1` |
| **CNAME** | 另一个域名的别名 | `www.mystore.com → mystore.com` |
| **MX** | 该域名的邮件服务器 | `mystore.com → mail.mystore.com` |
| **TXT** | 任意文本（用于验证、SPF 等） | `"v=spf1 include:_spf.google.com"` |
| **NS** | 负责该域名的域名服务器 | `mystore.com → ns1.cloudflare.com` |

```bash
# Query specific record types
dig mystore.com A          # IPv4 address
dig mystore.com AAAA       # IPv6 address
dig mystore.com MX         # Mail servers
dig mystore.com NS         # Nameservers
dig mystore.com TXT        # Text records
dig www.mystore.com CNAME  # Aliases
```

**注册域名**很简单。你前往注册商（Namecheap、Cloudflare、Porkbun），搜索一个名称，然后为一个 `.com` 支付每年 10-15 美元。接着你配置 DNS 记录——至少需要一条 **A 记录**，将你的域名指向服务器的 IP 地址。

**TTL（Time To Live，生存时间）**控制 DNS 答案被缓存多长时间。当你设置一条 TTL 为 3600（秒）的 A 记录时，DNS 解析器会将该答案缓存一小时，然后再次询问。低 TTL 意味着变更传播快，但会产生更多 DNS 查询。高 TTL 意味着查询更少，但更新更慢。当你即将更换服务器时，提前降低 TTL，以便切换更快。

**为什么 DNS 使用 UDP？**

这是一个很好的问题，答案能让你学到关于协议选择的重要知识。DNS 查询很小——像“`google.com` 的 IP 是什么？”这样的问题能装进单个数据包（通常小于 512 字节）。TCP 在发送任何数据之前需要三次握手（SYN、SYN-ACK、ACK）——仅建立连接就需要三个往返，然后是实际查询，最后是拆除连接。对于一个小型的单包问答来说，这种开销是荒谬的。

UDP 让你发送一个包含问题的数据包，然后收到一个包含答案的数据包。没有握手，没有连接建立，没有拆除。对于 DNS 来说，这意味着：

- **更快**——一个往返而不是多个
- **DNS 服务器负载更低**——无需为每秒数百万次查询维护连接状态
- **更简单**——如果响应没有到达，再问一次即可

DNS *确实*在两种情况下回退到 TCP：当响应太大而无法装入单个 UDP 数据包时（超过 512 字节，或使用 EDNS 时超过 4096 字节），以及 DNS 服务器之间的**区域传送**（复制整个区域文件）。但对于 99% 的正常 DNS 查询，UDP 是正确的工具。

```bash
# See DNS queries happening in real time (requires tcpdump)
sudo tcpdump -i any port 53

# You will see UDP packets going to and from port 53 (the DNS port)
```

**DNS 可能失败，而一旦失败，一切都会崩溃。** 如果你的 DNS 解析器宕机，你的浏览器就无法翻译任何域名，互联网实际上就停止工作了。这就是为什么 DNS 提供商发生重大故障（比如 2021 年 Facebook 的故障，其 BGP 配置错误导致他们的 DNS 服务器不可达）会导致一切瘫痪。作为 SRE，你会监控 DNS 健康状况、使用多个 DNS 提供商，并理解 DNS 传播延迟。

Linux 上的 **`/etc/resolv.conf` 文件**告诉你的系统使用哪个 DNS 解析器：

```bash
cat /etc/resolv.conf
# nameserver 8.8.8.8
# nameserver 1.1.1.1
```

而 `/etc/hosts` 让你可以针对特定域名完全覆盖 DNS——这对测试很有用：

```bash
# /etc/hosts
127.0.0.1   mystore.com
# Now "mystore.com" points to localhost on this machine
```

<!-- ZH_RESOURCES -->
- [Cloudflare - 什么是 DNS？](https://www.cloudflare.com/learning/dns/what-is-dns/) -- 类型：文章，时长：10 分钟
- [DNS 工作原理（漫画）](https://howdns.works/) -- 类型：互动，时长：10 分钟
- [Julia Evans - DNS 工作原理小志](https://wizardzines.com/zines/dns/) -- 类型：小志，时长：15 分钟
- [mess with dns - DNS 实验](https://messwithdns.net/) -- 类型：互动，时长：30 分钟
- [dig 命令示例](https://www.thegeekstuff.com/2012/02/dig-command-examples/) -- 类型：参考，时长：15 分钟

<!-- ZH_UI -->
1. 理解 DNS 查询如何将域名解析为 IP 地址
2. 使用 dig 和 nslookup 查询 DNS 记录
3. 解释 DNS 为何使用 UDP 以及何时回退到 TCP
4. 我有一个域名。如何把所有部分组合起来并部署我的应用？
5. 我已经把 DNS 指向我的服务器，各个部分也都能单独工作。但我从未把它们组装成一个真实的线上部署——前面是 Nginx、配置好 HTTPS、浏览器里是真实域名。把所有部分组合起来实际上是什么样子？
