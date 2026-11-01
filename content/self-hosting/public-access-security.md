---
id: public-access-security
title: 'Before You Go Public: Security Considerations'
zone: self-hosting
edges:
  to:
    - id: public-website
      question: My service is a website or web app — what are my options?
      detail: >-
        It's a blog, dashboard, or web app — people navigate to a URL and it
        loads in the browser. Regular web traffic. No video streaming or massive
        file downloads.
    - id: public-media-streaming
      question: >-
        I want to let people stream from my media server without needing a VPN —
        how?
      detail: >-
        I want people to open a URL in their browser or app and just watch — no
        VPN, no account with me, no setup on their end. Just a link that works.
difficulty: 2
tags:
  - self-hosting
  - security
  - public
  - dmz
  - networking
category: principle
milestones:
  - Understand the attack surface of a public-facing home service
  - >-
    Know what a DMZ/VLAN isolation approach looks like (even if you don't
    implement it now)
title_zh: "在公开之前：安全注意事项"

---


Putting something on the public internet means real traffic — and real attack attempts. Bots scan the entire IPv4 address space continuously. Within minutes of a service going public, it will receive connection attempts from all over the world.

This doesn't mean don't do it. It means understand what you're signing up for.

<!-- DEEP_DIVE -->

## What actually happens

When you expose a service publicly, automated scanners will find it. They'll probe common paths, try default credentials, and test for known CVEs in whatever software you're running. This is just the reality of the internet — it happens to every public-facing host, including major cloud providers.

The question is: what happens if they succeed?

## The pivot risk

This is the part people underestimate. Suppose someone exploits a vulnerability in your Nextcloud or Jellyfin — maybe an unpatched CVE, maybe a weak password. They're now running code on your server.

But your server is on your home network. From there, they can see your NAS, your other machines, your router, everything else on the LAN. A single compromised application becomes a foothold into your entire home network.

Cloudflare Tunnel and other tools hide your home IP — but they don't prevent this. The exploit still lands on a machine inside your network.

## Keep software updated

This is the highest-leverage thing you can do. Most exploits target known, patched vulnerabilities in outdated software. Enable automatic updates for your OS packages. Pin container images to specific versions and update them regularly. Don't leave services running that you're not actively maintaining.

## Don't expose unauthenticated services

Anything public should require authentication before doing anything interesting. Even if you think "nobody knows the URL" — they will. Use strong, unique passwords or SSO. Consider adding Cloudflare Access or a similar auth layer in front of sensitive services.

## The proper hardening approach: DMZ / VLAN isolation

If you want to do this right, the textbook answer is to put public-facing services in a separate network segment — a DMZ (demilitarized zone) or dedicated VLAN — isolated from the rest of your home network by firewall rules.

In this setup, even if an attacker fully compromises your Nextcloud server, they hit a firewall wall. They can't reach your NAS or your desktop. The blast radius is contained.

This is a networking topic that goes beyond self-hosting — it involves managed switches, VLAN-capable routers, and firewall rules. We won't go deeper on it here, but it's worth knowing the concept exists and what it's called when you're ready.

## Practical baseline

Before going public:
- Your software is up to date
- Every service behind the public URL requires authentication
- You have a plan for keeping it updated
- You understand that if something goes wrong, it's on your home network

With that understood, pick your approach.

<!-- RESOURCES -->

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) -- type: reference, time: 30min

<!-- ZH_SUMMARY -->
把服务放到公网上意味着真实的流量——以及真实的攻击尝试。机器人会持续扫描整个 IPv4 地址空间。服务公开后几分钟内，就会收到来自世界各地的连接尝试。

这并不意味着不要这么做，而是意味着要清楚自己将要面对什么。

<!-- ZH_DEEP_DIVE -->
## 实际会发生什么

当你公开暴露一个服务时，自动化扫描器会找到它。它们会探测常见路径、尝试默认凭据，并针对你所运行的任何软件测试已知 CVE。这就是互联网的现实——每个面向公网的主机都会遭遇这些，包括大型云服务商。

问题是：如果它们得逞了，会发生什么？

## 横向移动风险

这是人们低估的部分。假设有人利用了你 Nextcloud 或 Jellyfin 中的某个漏洞——可能是一个未修补的 CVE，也可能是一个弱密码。他们现在已经在你的服务器上运行代码了。

但你的服务器位于家庭网络中。从那里，他们可以看到你的 NAS、你的其他机器、你的路由器，以及局域网上的其他一切。一个被攻陷的应用就成了进入你整个家庭网络的立足点。

Cloudflare Tunnel 和其他工具会隐藏你的家庭 IP——但它们无法阻止这一点。漏洞利用仍然会落在你网络内部的一台机器上。

## 保持软件更新

这是你能做的杠杆率最高的事情。大多数漏洞利用针对的是过时软件中已知且已修补的漏洞。为你的操作系统软件包启用自动更新。将容器镜像固定到特定版本并定期更新。不要让你并未积极维护的服务继续运行。

## 不要暴露未认证的服务

任何公开的东西都应该在做任何有价值的事情之前要求认证。即使你认为“没人知道这个 URL”——他们会的。使用强且唯一的密码或 SSO。考虑在敏感服务前面加上 Cloudflare Access 或类似的认证层。

## 正确的加固方法：DMZ / VLAN 隔离

如果你想做得规范，教科书式的答案是把面向公网的服务放在一个单独的网络段中——一个 DMZ（隔离区）或专用 VLAN——通过防火墙规则与家庭网络的其余部分隔离。

在这种设置下，即使攻击者完全攻陷了你的 Nextcloud 服务器，他们也会撞上一堵防火墙墙。他们无法访问你的 NAS 或你的桌面。爆炸半径被限制住了。

这是一个超出 self-hosting 范畴的网络话题——它涉及管理型交换机、支持 VLAN 的路由器和防火墙规则。我们不会在这里深入展开，但值得知道这个概念的存在以及它叫什么，等你准备好时再用。

## 实用基线

在公开之前：
- 你的软件是最新的
- 公开 URL 后面的每个服务都要求认证
- 你有保持其更新的计划
- 你明白如果出了问题，它发生在你的家庭网络上

理解了这些之后，选择你的方法。

<!-- ZH_RESOURCES -->
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) -- 类型：参考，时间：30分钟

<!-- ZH_UI -->
1. 理解面向公网的家庭服务的攻击面
2. 了解 DMZ/VLAN 隔离方案是什么样的（即使现在不实施）
3. 我的服务是网站或 Web 应用——我有哪些选择？
4. 它是博客、仪表盘或 Web 应用——用户访问 URL，在浏览器中加载。普通 Web 流量。没有视频流或大文件下载。
5. 我想让人们无需 VPN 就能从我的媒体服务器串流——怎么做？
6. 我想让人们只需在浏览器或应用中打开一个 URL 就能直接观看——无需 VPN、无需在我这里注册账号、无需在他们那边做任何设置。只需一个可用的链接。
