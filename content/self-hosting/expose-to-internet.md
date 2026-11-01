---
id: expose-to-internet
title: Exposing Services to the Internet
zone: self-hosting
edges:
  to:
    - id: remote-access-just-me
      question: I just want to be able to access it myself
      detail: >-
        The moment I leave my home network, everything's unreachable. I want to
        pull up my files or media from my phone or laptop, wherever I am —
        without opening anything to the whole internet.
    - id: remote-access-shared
      question: Me and some friends or family need access
      detail: >-
        It's not just me — my partner or a few family members need to use this
        too. But I don't want it open to the whole internet, and I can't expect
        them to do anything complicated.
    - id: remote-access-public
      question: It needs to be publicly accessible to anyone on the internet
      detail: >-
        I want anyone with the URL to reach it — no account, no VPN, no setup on
        their end. That feels like a fundamentally different problem from just
        giving access to a few people.
difficulty: 1
tags:
  - self-hosting
  - networking
  - remote-access
  - security
category: concept
milestones:
  - Understand the three different remote access scenarios
  - Know which approach fits your situation
title_zh: "将服务暴露到互联网"

---


Your services work great at home. But the moment you leave, they're unreachable — because your home network is private by design. There's no direct path in from the internet.

Getting remote access means creating that path deliberately. But not all remote access is the same — *why* you need it determines which tool is right.

<!-- DEEP_DIVE -->

## The three scenarios

**Scenario 1: Only you need access.**
You want to check on your services from your phone, use Vaultwarden on the road, or browse your Jellyfin from a hotel. No one else needs in.

**Scenario 2: A small group of trusted people.**
You're sharing Jellyfin with family, or Nextcloud with a partner. A handful of known people with devices you can install software on.

**Scenario 3: Genuinely public.**
A website, a public API, or a service that anyone should be able to reach from a browser — no install required.

## Why this distinction matters

Scenarios 1 and 2 are **private access problems**. The right answer is a VPN-style approach: your services stay completely invisible to the internet, and only authorized devices can reach them. Nobody is scanning your ports. Nobody can probe your login page.

Scenario 3 is **public exposure**. You're deliberately putting something on the open internet. Anyone can attempt to connect. The tools are different — and so are the risks.

## What "just opening a port" looks like

There's also the original approach: configure your router to forward port 80 or 443 directly to your server. It works, but it's the most exposed option — your home IP becomes public, ISPs often block standard ports, and your server is directly reachable from the internet. It's a valid choice for the right situation, but the alternatives here are generally better.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你的服务在家里运行得很好。但一旦你离开家，它们就无法访问了——因为你的家庭网络在设计上就是私有的。从互联网没有直达的路径。

实现远程访问意味着要有意地创建这条路径。但并非所有远程访问都一样——你*为什么*需要它，决定了哪种工具才是正确的。

<!-- ZH_DEEP_DIVE -->
## 三种场景

**场景 1：只有你需要访问。**
你想从手机上检查服务状态，在路上使用 Vaultwarden，或者在酒店浏览你的 Jellyfin。没有其他人需要访问。

**场景 2：一小群可信的人。**
你和家人共享 Jellyfin，或与伴侣共享 Nextcloud。少数已知的人，设备上可以安装软件。

**场景 3：真正公开。**
一个网站、一个公共 API，或任何人在浏览器中都能访问的服务——无需安装任何东西。

## 为什么这个区分很重要

场景 1 和 2 是**私有访问问题**。正确的答案是 VPN 式方案：你的服务对互联网完全不可见，只有授权设备才能访问。没有人在扫描你的端口。没有人能探测你的登录页面。

场景 3 是**公开暴露**。你是在故意把某些东西放到开放互联网上。任何人都可以尝试连接。工具不同——风险也不同。

## “直接开个端口”是什么样子

还有一种原始做法：配置路由器，把 80 或 443 端口直接转发到你的服务器。它能用，但这是暴露程度最高的选项——你的家庭 IP 会变成公开的，ISP 通常会封锁标准端口，而且你的服务器可以从互联网直接访问。在合适的情况下这是个有效选择，但这里的替代方案通常更好。

<!-- ZH_UI -->
1. 理解三种不同的远程访问场景
2. 了解哪种方式适合你的情况
3. 我只希望能自己访问它
4. 一旦离开家庭网络，一切就无法访问了。我希望无论身在何处，都能从手机或笔记本上获取我的文件或媒体——而不必向整个互联网开放任何东西。
5. 我和一些朋友或家人需要访问
6. 不只是我——我的伴侣或几位家人也需要使用它。但我不想向整个互联网开放，也不能指望他们去做任何复杂的操作。
7. 它需要让互联网上的任何人都能公开访问
8. 我希望任何拿到 URL 的人都能访问它——无需账号、无需 VPN、他们那边也无需任何设置。这感觉与只给少数几个人授权是根本不同的问题。
