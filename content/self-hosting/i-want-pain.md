---
id: i-want-pain
title: I Want to Install Everything Manually
zone: self-hosting
edges:
  to:
    - id: installing-software
      zone: running
      question: >-
        How do people actually install and run services on bare Linux without
        Docker?
      detail: >-
        I've seen apt, but also snap, pip, building from source... I don't know
        which one to use for server software, or how to make sure a service
        starts back up automatically when the machine reboots.
difficulty: 3
tags:
  - self-hosting
  - linux
  - native
  - advanced
category: practice
milestones:
  - Compile something from source
  - Debug a broken dependency at 2am
  - Reconsider
title_zh: "我想手动安装所有内容"

---


Respect. This is the path of building software from source, managing systemd units by hand, and memorising config file locations across a dozen different projects.

It's a legitimate way to learn Linux deeply. It's also why Docker was invented.

<!-- DEEP_DIVE -->

The self-hosting community has largely standardised on Docker because native installs don't scale well — even for a single person running a handful of services. When your Nextcloud update breaks because PHP upgraded, or your Jellyfin depends on a libssl version that conflicts with something else, you'll understand the appeal of containers.

That said: if you want to go this route, the [Arch Wiki](https://wiki.archlinux.org/) is the best Linux reference on the internet, even if you're not running Arch. And the [Running Zone](/zone/running) on this roadmap covers Linux service management properly.

Good luck. You'll need it.

<!-- RESOURCES -->

- [Arch Wiki](https://wiki.archlinux.org/) -- type: reference, time: ongoing

<!-- ZH_SUMMARY -->
致敬。这是从源码构建软件、手动管理 systemd 单元、并记住十几个不同项目配置文件位置的路径。

这是深入学习 Linux 的正当方式。这也是 Docker 被发明出来的原因。

<!-- ZH_DEEP_DIVE -->
自托管社区基本已经统一到 Docker 上，因为原生安装的扩展性很差——哪怕只是一个人跑几个服务也是如此。当你的 Nextcloud 因为 PHP 升级而更新失败，或者你的 Jellyfin 依赖的 libssl 版本与其他东西冲突时，你就会明白容器的吸引力所在。

话虽如此：如果你想走这条路，[Arch Wiki](https://wiki.archlinux.org/) 是互联网上最好的 Linux 参考，即使你运行的不是 Arch。而本路线图上的 [Running Zone](/zone/running) 则系统地涵盖了 Linux 服务管理。

祝你好运。你会需要它的。

<!-- ZH_RESOURCES -->
- [Arch Wiki](https://wiki.archlinux.org/) -- 类型：参考，时间：持续

<!-- ZH_UI -->
1. 从源码编译一些东西
2. 凌晨两点调试损坏的依赖
3. 重新考虑
4. 在没有 Docker 的裸 Linux 上，人们实际上是如何安装和运行服务的？
5. 我见过 apt，也见过 snap、pip、从源码构建……我不知道服务器软件该用哪一种，也不知道如何确保机器重启后服务能自动重新启动。
