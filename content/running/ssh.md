---
id: ssh
title: 'SSH: Your Window Into the Server'
zone: running
edges:
  to:
    - id: initial-server-setup
      question: I can SSH into my server. What should I do before anything else?
      detail: >-
        I can SSH in, but I'm logged in as root which already feels wrong. And I
        noticed what looks like automated login attempts in the auth log — bots
        are already trying to get in. What are the first things I need to do to
        lock this down?
difficulty: 1
tags:
  - ssh
  - keys
  - authentication
  - ed25519
  - scp
  - config
category: practice
milestones:
  - Generate an SSH key pair and copy the public key to a server
  - Connect to a server using SSH key authentication (no password)
  - Create a ~/.ssh/config entry to connect with a short alias
title_zh: "SSH：你通往服务器的窗口"

---


SSH (Secure Shell) is the protocol that lets you control a remote server from your terminal. When you type `ssh user@server`, you get a shell that runs on the server — every command you type executes there, not on your laptop. All traffic is encrypted. This is how every SRE, developer, and sysadmin interacts with remote servers.

There is no GUI, no remote desktop, no drag-and-drop. SSH is the interface. Getting comfortable with it is non-negotiable.

<!-- DEEP_DIVE -->

**How SSH works (simplified)**

SSH uses public-key cryptography. You generate a key pair: a **private key** (stays on your laptop, never leaves it) and a **public key** (goes on the server). When you connect, SSH proves you have the private key without ever sending it over the network. No password goes over the wire.

The server keeps a list of authorized public keys in `~/.ssh/authorized_keys`. If your public key is in that file, you can log in.

**Generating an SSH key pair**

```bash
# Generate a key pair (on your laptop)
ssh-keygen -t ed25519 -C "your-email@example.com"

# When prompted for a file location, press Enter to accept the default:
# ~/.ssh/id_ed25519       ← private key (NEVER share this)
# ~/.ssh/id_ed25519.pub   ← public key (safe to share)

# View your public key — this is what goes on servers
cat ~/.ssh/id_ed25519.pub
# ssh-ed25519 AAAA...long string... your-email@example.com
```

Use `ed25519` — it is more secure and generates shorter keys than the older `rsa`. If you see tutorials using `ssh-keygen -t rsa`, use `ed25519` instead.

**Connecting to a server**

```bash
# Basic connection
ssh root@143.198.100.50

# With a specific private key file
ssh -i ~/.ssh/id_ed25519 root@143.198.100.50

# With a non-standard port
ssh -p 2222 root@143.198.100.50
```

The first time you connect to a server, SSH shows you the server's fingerprint and asks if you trust it. Type `yes`. SSH saves the fingerprint in `~/.ssh/known_hosts` and will alert you if it ever changes (a sign the server may have been replaced or compromised).

**Copying your public key to a server**

```bash
# Easiest way — if the server already has password auth enabled
ssh-copy-id root@143.198.100.50
# This copies ~/.ssh/id_ed25519.pub into /root/.ssh/authorized_keys on the server

# Manual way — paste into authorized_keys yourself
cat ~/.ssh/id_ed25519.pub
# (copy the output, then on the server:)
# echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys
```

**The `~/.ssh/config` file — your shortcut list**

Typing `ssh root@143.198.100.50` every time is tedious. The config file lets you define aliases:

```
# ~/.ssh/config

Host mystore
    HostName 143.198.100.50
    User deploy
    IdentityFile ~/.ssh/id_ed25519

Host staging
    HostName 143.198.100.51
    User deploy
    IdentityFile ~/.ssh/id_ed25519
```

Now you can just type:
```bash
ssh mystore       # connects as deploy@143.198.100.50
ssh staging       # connects to staging
scp myfile.txt mystore:/home/deploy/  # works too
```

**Copying files with `scp`**

`scp` is SSH-based file copy. Syntax mirrors `cp` but with `user@host:path` for remote paths:

```bash
# Copy a file from your laptop to the server
scp myfile.txt deploy@143.198.100.50:/home/deploy/

# Copy a directory
scp -r myapp/ deploy@143.198.100.50:/home/deploy/

# Copy from server to your laptop
scp deploy@143.198.100.50:/home/deploy/logs/app.log ./
```

**Common problems**

```bash
# "Permission denied (publickey)" — your key is not in authorized_keys
# Fix: copy your public key to the server

# "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED"
# The server's fingerprint changed — could be legitimate (server was rebuilt) or suspicious
# Fix: remove the old entry: ssh-keygen -R 143.198.100.50

# "Connection refused"
# SSH is not running on the server, or the firewall is blocking port 22
# Fix: check that sshd is running and the firewall allows port 22

# Slow connection / long pause before prompt
# DNS reverse lookup is timing out
# Fix: add UseDNS no to /etc/ssh/sshd_config on the server
```

**SSH agent — not retyping your passphrase**

If you added a passphrase to your key (good idea), you would have to type it every time you SSH. `ssh-agent` caches the decrypted key in memory for your session:

```bash
# Start the agent (usually happens automatically on macOS/Linux with a GUI)
eval "$(ssh-agent -s)"

# Add your key to the agent (type passphrase once)
ssh-add ~/.ssh/id_ed25519

# Now SSH connections use the cached key — no passphrase prompts
ssh mystore
```

<!-- RESOURCES -->

- [DigitalOcean - SSH Key Authentication Tutorial](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server) -- type: tutorial, time: 20m
- [SSH Config File Guide](https://linuxize.com/post/using-the-ssh-config-file/) -- type: article, time: 10m
- [ssh-keygen man page](https://man.openbsd.org/ssh-keygen) -- type: reference, time: 5m

<!-- ZH_SUMMARY -->
SSH（Secure Shell）是一种协议，让你可以从终端控制远程服务器。当你输入 `ssh user@server` 时，你会获得一个运行在服务器上的 shell——你输入的每条命令都在服务器上执行，而不是在你的笔记本电脑上。所有流量都经过加密。每一位 SRE、开发者和系统管理员都是通过这种方式与远程服务器交互的。

没有 GUI，没有远程桌面，没有拖拽操作。SSH 就是接口。熟练使用它是不可或缺的。

<!-- ZH_DEEP_DIVE -->
**SSH 工作原理（简化版）**

SSH 使用公钥加密。你生成一对密钥：一个**私钥**（留在你的笔记本电脑上，永不离开）和一个**公钥**（放到服务器上）。当你连接时，SSH 证明你拥有私钥，但从不通过网络发送它。密码也不会通过网络传输。

服务器在 `~/.ssh/authorized_keys` 中维护一个已授权的公钥列表。如果你的公钥在该文件中，你就可以登录。

**生成 SSH 密钥对**

```bash
# Generate a key pair (on your laptop)
ssh-keygen -t ed25519 -C "your-email@example.com"

# When prompted for a file location, press Enter to accept the default:
# ~/.ssh/id_ed25519       ← private key (NEVER share this)
# ~/.ssh/id_ed25519.pub   ← public key (safe to share)

# View your public key — this is what goes on servers
cat ~/.ssh/id_ed25519.pub
# ssh-ed25519 AAAA...long string... your-email@example.com
```

使用 `ed25519`——它比旧的 `rsa` 更安全，生成的密钥也更短。如果你看到教程使用 `ssh-keygen -t rsa`，请改用 `ed25519`。

**连接到服务器**

```bash
# Basic connection
ssh root@143.198.100.50

# With a specific private key file
ssh -i ~/.ssh/id_ed25519 root@143.198.100.50

# With a non-standard port
ssh -p 2222 root@143.198.100.50
```

第一次连接到服务器时，SSH 会显示服务器的指纹，并询问你是否信任它。输入 `yes`。SSH 会将指纹保存在 `~/.ssh/known_hosts` 中，如果指纹发生变化（表明服务器可能已被替换或入侵），它会提醒你。

**将公钥复制到服务器**

```bash
# Easiest way — if the server already has password auth enabled
ssh-copy-id root@143.198.100.50
# This copies ~/.ssh/id_ed25519.pub into /root/.ssh/authorized_keys on the server

# Manual way — paste into authorized_keys yourself
cat ~/.ssh/id_ed25519.pub
# (copy the output, then on the server:)
# echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys
```

**`~/.ssh/config` 文件——你的快捷列表**

每次都输入 `ssh root@143.198.100.50` 很繁琐。配置文件让你可以定义别名：

```
# ~/.ssh/config

Host mystore
    HostName 143.198.100.50
    User deploy
    IdentityFile ~/.ssh/id_ed25519

Host staging
    HostName 143.198.100.51
    User deploy
    IdentityFile ~/.ssh/id_ed25519
```

现在你只需输入：
```bash
ssh mystore       # connects as deploy@143.198.100.50
ssh staging       # connects to staging
scp myfile.txt mystore:/home/deploy/  # works too
```

**使用 `scp` 复制文件**

`scp` 是基于 SSH 的文件复制。语法与 `cp` 类似，但远程路径使用 `user@host:path`：

```bash
# Copy a file from your laptop to the server
scp myfile.txt deploy@143.198.100.50:/home/deploy/

# Copy a directory
scp -r myapp/ deploy@143.198.100.50:/home/deploy/

# Copy from server to your laptop
scp deploy@143.198.100.50:/home/deploy/logs/app.log ./
```

**常见问题**

```bash
# "Permission denied (publickey)" — your key is not in authorized_keys
# Fix: copy your public key to the server

# "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED"
# The server's fingerprint changed — could be legitimate (server was rebuilt) or suspicious
# Fix: remove the old entry: ssh-keygen -R 143.198.100.50

# "Connection refused"
# SSH is not running on the server, or the firewall is blocking port 22
# Fix: check that sshd is running and the firewall allows port 22

# Slow connection / long pause before prompt
# DNS reverse lookup is timing out
# Fix: add UseDNS no to /etc/ssh/sshd_config on the server
```

**SSH agent——无需重复输入密码短语**

如果你为密钥添加了密码短语（这是个好主意），每次 SSH 时都得输入它。`ssh-agent` 会在你的会话期间将解密后的密钥缓存在内存中：

```bash
# Start the agent (usually happens automatically on macOS/Linux with a GUI)
eval "$(ssh-agent -s)"

# Add your key to the agent (type passphrase once)
ssh-add ~/.ssh/id_ed25519

# Now SSH connections use the cached key — no passphrase prompts
ssh mystore
```

<!-- ZH_RESOURCES -->
- [DigitalOcean - SSH 密钥认证教程](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server) -- 类型: 教程, 时长: 20m
- [SSH 配置文件指南](https://linuxize.com/post/using-the-ssh-config-file/) -- 类型: 文章, 时长: 10m
- [ssh-keygen 手册页](https://man.openbsd.org/ssh-keygen) -- 类型: 参考, 时长: 5m

<!-- ZH_UI -->
1. 生成 SSH 密钥对并将公钥复制到服务器
2. 使用 SSH 密钥认证（无密码）连接服务器
3. 创建 ~/.ssh/config 条目以使用简短别名连接
4. 我能通过 SSH 登录服务器了。在此之前我应该先做什么？
5. 我能通过 SSH 登录了，但我是以 root 身份登录的，这已经感觉不对劲。而且我注意到 auth 日志里看起来像是自动化的登录尝试——机器人已经在尝试入侵了。为了加固安全，我首先需要做什么？
