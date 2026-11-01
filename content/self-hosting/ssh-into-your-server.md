---
id: ssh-into-your-server
title: SSH Into Your Server
zone: self-hosting
edges:
  to:
    - id: docker-or-native
      question: I'm in. How do I actually install software on this thing?
      detail: >-
        I've got a shell on a fresh machine. I have no idea if I should just apt
        install things, use Docker, or something else entirely. What's the right
        way to actually run services?
difficulty: 1
tags:
  - self-hosting
  - ssh
  - linux
  - terminal
category: practice
milestones:
  - SSH into your server from your laptop
  - Know your server's IP address
  - Create a non-root user and add it to sudoers
  - Set up SSH key authentication
title_zh: "SSH 登录你的服务器"

---


SSH (Secure Shell) lets you log into your server from your laptop over the network. Your server has no monitor, no keyboard — SSH is how you talk to it. You type commands on your laptop, they run on the server.

```bash
ssh username@192.168.1.100
```

That's it. You're in.

<!-- DEEP_DIVE -->

**Finding your server's IP**

If you set a DHCP reservation during install, you already know the IP. If not:
- Check your router's admin page — usually at `192.168.1.1` or `192.168.0.1`. Look for connected devices.
- Or log into the server directly (with a keyboard/monitor temporarily) and run `ip a`

**SSH keys: stop using passwords**

Password authentication works, but SSH keys are better in every way: more secure, more convenient, and no typing passwords on every login.

Generate a key pair on your laptop (if you don't have one already):

```bash
ssh-keygen -t ed25519 -C "homelab"
```

Press Enter to accept the default location (`~/.ssh/id_ed25519`). Set a passphrase if you want (optional).

Copy your public key to the server:

```bash
ssh-copy-id username@192.168.1.100
```

Enter your password once. After that, `ssh username@192.168.1.100` logs you in without a password prompt — it uses your key instead.

**Don't run everything as root**

If you installed Debian bare metal, you created a non-root user during setup. Use that. If you're SSHing into a Proxmox VM that only has root, create a user:

```bash
adduser yourname
usermod -aG sudo yourname
```

Then `ssh yourname@192.168.1.100`. Use `sudo` when you need admin access. Running everything as root is a bad habit — a typo in the wrong place can delete your entire filesystem.

**Handy shortcut: SSH config**

Stop typing IP addresses. Add an entry to `~/.ssh/config` on your laptop:

```
Host homelab
    HostName 192.168.1.100
    User yourname
    IdentityFile ~/.ssh/id_ed25519
```

Now `ssh homelab` is all you need.

<!-- RESOURCES -->

<!-- ZH_SUMMARY -->
SSH（Secure Shell）让你可以从笔记本电脑通过网络登录到服务器。你的服务器没有显示器，也没有键盘——SSH 就是你与它交流的方式。你在笔记本电脑上输入命令，命令在服务器上执行。

```bash
ssh username@192.168.1.100
```

就这样。你已经连上了。

<!-- ZH_DEEP_DIVE -->
**查找服务器的 IP**

如果你在安装时设置了 DHCP 保留，那你已经知道 IP 了。如果没有：
- 查看路由器的管理页面——通常位于 `192.168.1.1` 或 `192.168.0.1`。查找已连接的设备。
- 或者直接登录服务器（临时接上键盘/显示器），运行 `ip a`

**SSH 密钥：别再使用密码了**

密码认证能用，但 SSH 密钥在各方面都更好：更安全、更方便，而且每次登录都不用输入密码。

在你的笔记本电脑上生成一对密钥（如果还没有的话）：

```bash
ssh-keygen -t ed25519 -C "homelab"
```

按 Enter 接受默认位置（`~/.ssh/id_ed25519`）。如果需要，可以设置一个密码短语（可选）。

将你的公钥复制到服务器：

```bash
ssh-copy-id username@192.168.1.100
```

输入一次密码。之后，`ssh username@192.168.1.100` 就能免密码登录——它会使用你的密钥。

**不要用 root 运行一切**

如果你裸机安装了 Debian，你在安装过程中创建了一个非 root 用户。就用那个用户。如果你 SSH 登录的 Proxmox VM 只有 root，创建一个用户：

```bash
adduser yourname
usermod -aG sudo yourname
```

然后 `ssh yourname@192.168.1.100`。需要管理员权限时使用 `sudo`。用 root 运行一切是个坏习惯——在错误的地方打错一个字就可能删掉整个文件系统。

**便捷捷径：SSH 配置**

别再输入 IP 地址了。在你的笔记本电脑上往 `~/.ssh/config` 添加一个条目：

```
Host homelab
    HostName 192.168.1.100
    User yourname
    IdentityFile ~/.ssh/id_ed25519
```

现在你只需要 `ssh homelab`。

<!-- ZH_UI -->
1. 从笔记本电脑通过 SSH 登录服务器
2. 了解服务器的 IP 地址
3. 创建非 root 用户并将其加入 sudoers
4. 配置 SSH 密钥认证
5. 我已登录。到底该如何在这台机器上安装软件？
6. 我在一台全新机器上拿到了 shell。我不知道该直接用 apt 安装、用 Docker，还是完全用别的方式。实际运行服务的正确做法是什么？
