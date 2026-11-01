---
id: remote-access-shared
title: 'Goal: Shared Access — Friends and Family'
zone: self-hosting
edges:
  to:
    - id: tailscale
      question: Can I share a private VPN with others?
      detail: >-
        Do the people I share with need accounts? What does setup look like for
        someone non-technical? I want it to actually work for my family, not
        just be theoretically possible.
    - id: wireguard-vpn-home
      question: I want to run my own VPN server and manage who gets in
      detail: >-
        I want control over exactly who has access and the ability to revoke it.
        I don't want to depend on someone else's service to decide who gets in.
difficulty: 1
tags:
  - self-hosting
  - remote-access
  - vpn
  - sharing
category: concept
milestones:
  - 'Identify your use case: trusted shared access'
title_zh: "目标：共享访问 — 亲友"

---


You want a few trusted people — a partner, family members, a friend group — to use your Jellyfin, Nextcloud, or photo library. Not the whole internet. Just the people you choose.

This is still a private access problem. You don't need to expose anything publicly. You just need to extend your private network to a small group of trusted people.

<!-- DEEP_DIVE -->

## Still private, not public

It's worth being clear: even though other people are accessing your services, you don't need to open anything to the internet. Everyone connects through a VPN — which means your services are still invisible to the world, and only people with credentials can reach them.

This is a very different security posture from making something publicly accessible.

## Your two options

**Tailscale** — supports sharing devices or whole networks with other Tailscale accounts. Each person installs the Tailscale app on their device and you share access. Very smooth for family setups. The free tier supports up to 100 devices, which is plenty for most households.

**WireGuard (self-hosted)** — you run a WireGuard server at home and generate a config file for each person. They import it into the WireGuard app. More setup on your end, but full control over who has access and no third-party account required for your users.

For most families, Tailscale is the obvious choice. WireGuard makes sense if you want to avoid third-party dependencies or if your users can't or won't create a Tailscale account.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
你希望几个信任的人——伴侣、家人、朋友群——能使用你的 Jellyfin、Nextcloud 或照片库。不是整个互联网，只是你选定的人。

这仍然是一个私有访问问题。你不需要公开暴露任何东西，只需要把你的私有网络扩展到一个由可信人员组成的小群体。

<!-- ZH_DEEP_DIVE -->
## 依然是私有，而非公开

值得明确一点：即使其他人正在访问你的服务，你也不需要向互联网开放任何东西。所有人都通过 VPN 连接——这意味着你的服务对外界依然不可见，只有持有凭据的人才能访问。

这与将某些东西公开可访问相比，是一种截然不同的安全态势。

## 你的两个选择

**Tailscale** —— 支持与其他 Tailscale 账户共享设备或整个网络。每个人在自己的设备上安装 Tailscale 应用，然后你共享访问权限。对家庭场景来说非常顺畅。免费套餐支持最多 100 台设备，对大多数家庭来说绰绰有余。

**WireGuard（自托管）** —— 你在家里运行一台 WireGuard 服务器，并为每个人生成一个配置文件。他们将其导入 WireGuard 应用。你这边需要更多设置工作，但可以完全控制谁有访问权限，而且你的用户无需第三方账户。

对大多数家庭来说，Tailscale 是显而易见的选择。如果你希望避免第三方依赖，或者你的用户无法或不愿创建 Tailscale 账户，那么 WireGuard 更合适。

<!-- ZH_UI -->
1. 明确你的使用场景：可信共享访问
2. 我可以与他人共享私有 VPN 吗？
3. 我共享的人需要账户吗？对非技术人员来说设置流程是什么样的？我希望它对我的家人真正可用，而不只是理论上可行。
4. 我想运行自己的 VPN 服务器并管理谁可以接入
5. 我想精确控制谁有访问权限，并能随时撤销。我不想依赖别人的服务来决定谁可以接入。
