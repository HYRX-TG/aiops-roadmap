---
id: initial-server-setup
title: Setting Up a Fresh Server
zone: running
edges:
  to:
    - id: installing-software
      question: My server is secured. How do I install the software my app needs?
      detail: >-
        The server is locked down. Now I need to get my app's runtime on it —
        the right version of Python, or Node, or whatever it needs. But I'm not
        sure how to install software on Linux without breaking anything.
difficulty: 1
tags:
  - security
  - hardening
  - sudo
  - non-root
  - ufw
  - ssh-config
  - users
category: practice
milestones:
  - Create a non-root user with sudo access on a fresh Ubuntu server
  - Copy SSH keys to the new user and verify login works before disabling root
  - Disable root login and password authentication in sshd_config
title_zh: "设置一台全新的服务器"

---


A fresh VPS comes with a root user and password authentication enabled. This is a reasonable starting point for a provider to give you access, but it is not safe to leave it this way. Root is the superuser — one bad command and you can wipe the entire server. Password authentication means bots are actively trying to brute-force your login right now (check `/var/log/auth.log` — you will see hundreds of failed attempts within hours of creating a new server).

Before you install anything or touch your application code, run through this checklist on every new server.

<!-- DEEP_DIVE -->

**Step 1: Create a non-root user**

Never do day-to-day work as root. Create a regular user and give it `sudo` access for when you genuinely need elevated privileges:

```bash
# SSH in as root first
ssh root@YOUR_SERVER_IP

# Create a new user (replace 'deploy' with your preferred username)
adduser deploy
# You'll be prompted for a password — set one, even if you plan to use keys only

# Add the user to the sudo group
usermod -aG sudo deploy

# Verify
groups deploy
# deploy : deploy sudo
```

**Step 2: Set up SSH keys for the new user**

Copy your public key to the new user's account so you can SSH in as them:

```bash
# Still on the server as root — copy root's authorized_keys to the new user
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Or from your laptop, using `ssh-copy-id`:

```bash
# From your laptop
ssh-copy-id deploy@YOUR_SERVER_IP
```

**Step 3: Test the new user BEFORE locking yourself out**

This is critical. Open a new terminal and verify you can log in as the new user before you disable root login:

```bash
# In a NEW terminal window — do NOT close your root session yet
ssh deploy@YOUR_SERVER_IP

# Test sudo
sudo whoami
# Should print: root
```

If this works, you are safe to proceed. If it does not work, fix it while you still have the root session open.

**Step 4: Harden SSH configuration**

```bash
# Edit the SSH server config
sudo nano /etc/ssh/sshd_config

# Find and change these lines:
PermitRootLogin no          # Disallow root login entirely
PasswordAuthentication no   # Require SSH keys, disallow passwords
PubkeyAuthentication yes    # Make sure key auth is explicitly enabled

# Save the file, then restart SSH
sudo systemctl restart sshd
```

After restarting, test in a new terminal that you can still connect as your deploy user. If something went wrong, your existing session is still open and you can fix it.

**Step 5: Update the system**

```bash
sudo apt update
sudo apt upgrade -y

# Optionally, install useful baseline tools
sudo apt install -y htop curl wget git unzip
```

**Step 6: Set up a basic firewall**

Even before you know which ports your app will use, configure a default-deny firewall and open only SSH:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw enable

# Verify
sudo ufw status
```

You will open ports 80 and 443 later when you set up your web server. The firewall section covers this in detail.

**The full checklist (quick reference)**

```
[ ] SSH in as root
[ ] Create non-root user with sudo access
[ ] Copy SSH public key to new user
[ ] Test: ssh in as new user in a NEW terminal, verify sudo works
[ ] Disable root login in sshd_config
[ ] Disable password authentication in sshd_config
[ ] Restart sshd and test again
[ ] Run apt update && apt upgrade
[ ] Set up ufw: default deny, allow 22
[ ] Never do day-to-day work as root again
```

**Why this matters**

Within minutes of a new server being created, automated bots will start scanning it and attempting SSH login as root with common passwords. `PasswordAuthentication no` makes these attempts useless. `PermitRootLogin no` means even if somehow an attacker got a key, they would need your deploy user's key, not root's.

This is not paranoia — this is baseline hygiene. Every production server should have this done before anything else is installed.

<!-- RESOURCES -->

- [DigitalOcean - Initial Server Setup with Ubuntu 22.04](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) -- type: tutorial, time: 20m
- [sshd_config man page](https://man.openbsd.org/sshd_config) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
一台全新的 VPS 默认启用 root 用户和密码认证。作为服务商提供访问权限的起点，这无可厚非，但保持这种状态并不安全。root 是超级用户——一条错误的命令就可能清空整个服务器。密码认证意味着机器人此刻正在积极尝试暴力破解你的登录（查看 `/var/log/auth.log`——新服务器创建后几小时内，你就会看到数百次失败尝试）。

在安装任何软件或改动应用代码之前，请在每台新服务器上逐项完成这份检查清单。

<!-- ZH_DEEP_DIVE -->
**步骤 1：创建非 root 用户**

永远不要以 root 身份进行日常工作。创建一个普通用户，并为其授予 `sudo` 权限，以便在你确实需要提权时使用：

```bash
# 首先以 root 身份通过 SSH 登录
ssh root@YOUR_SERVER_IP

# 创建一个新用户（将 'deploy' 替换为你偏好的用户名）
adduser deploy
# 系统会提示你设置密码——即使你打算只用密钥登录，也要设置一个

# 将该用户添加到 sudo 组
usermod -aG sudo deploy

# 验证
groups deploy
# deploy : deploy sudo
```

**步骤 2：为新用户设置 SSH 密钥**

将你的公钥复制到新用户的账户，以便你能以该用户身份通过 SSH 登录：

```bash
# 仍在服务器上以 root 身份操作——将 root 的 authorized_keys 复制给新用户
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

或者从你的笔记本电脑上使用 `ssh-copy-id`：

```bash
# 从你的笔记本电脑上执行
ssh-copy-id deploy@YOUR_SERVER_IP
```

**步骤 3：在把自己锁在外面之前测试新用户**

这一步至关重要。打开一个新终端，在禁用 root 登录之前验证你能以新用户身份登录：

```bash
# 在一个新终端窗口中——此时不要关闭你的 root 会话
ssh deploy@YOUR_SERVER_IP

# 测试 sudo
sudo whoami
# 应输出：root
```

如果这一步成功，你就可以安全地继续。如果失败，趁 root 会话仍然打开时修复它。

**步骤 4：加固 SSH 配置**

```bash
# 编辑 SSH 服务器配置
sudo nano /etc/ssh/sshd_config

# 找到并修改以下行：
PermitRootLogin no          # 完全禁止 root 登录
PasswordAuthentication no   # 要求使用 SSH 密钥，禁止密码登录
PubkeyAuthentication yes    # 确保显式启用密钥认证

# 保存文件，然后重启 SSH
sudo systemctl restart sshd
```

重启后，在一个新终端中测试你仍能以 deploy 用户身份连接。如果出了问题，你现有的会话仍然打开，可以修复它。

**步骤 5：更新系统**

```bash
sudo apt update
sudo apt upgrade -y

# 可选：安装有用的基础工具
sudo apt install -y htop curl wget git unzip
```

**步骤 6：设置基础防火墙**

即使你还不知道应用会使用哪些端口，也要先配置一个默认拒绝的防火墙，并且只开放 SSH：

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw enable

# 验证
sudo ufw status
```

稍后设置 Web 服务器时，你再开放 80 和 443 端口。防火墙章节会详细介绍这一点。

**完整检查清单（快速参考）**

```
[ ] 以 root 身份通过 SSH 登录
[ ] 创建具有 sudo 权限的非 root 用户
[ ] 将 SSH 公钥复制给新用户
[ ] 测试：在新终端中以新用户身份 SSH 登录，验证 sudo 可用
[ ] 在 sshd_config 中禁用 root 登录
[ ] 在 sshd_config 中禁用密码认证
[ ] 重启 sshd 并再次测试
[ ] 运行 apt update && apt upgrade
[ ] 设置 ufw：默认拒绝，允许 22
[ ] 永远不再以 root 身份进行日常工作
```

**为什么这很重要**

新服务器创建后的几分钟内，自动化机器人就会开始扫描它，并尝试用常见密码以 root 身份进行 SSH 登录。`PasswordAuthentication no` 使这些尝试变得毫无用处。`PermitRootLogin no` 意味着即使攻击者以某种方式获得了密钥，他们也需要你的 deploy 用户的密钥，而不是 root 的密钥。

这不是偏执——这是基线卫生。每台生产服务器都应该在安装任何其他东西之前完成这些工作。

<!-- ZH_RESOURCES -->
- [DigitalOcean - Ubuntu 22.04 初始服务器设置](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) -- 类型：教程，时长：20 分钟
- [sshd_config 手册页](https://man.openbsd.org/sshd_config) -- 类型：参考，时长：10 分钟

<!-- ZH_UI -->
1. 在全新的 Ubuntu 服务器上创建一个具有 sudo 权限的非 root 用户
2. 将 SSH 密钥复制到新用户，并在禁用 root 之前验证登录是否正常
3. 在 sshd_config 中禁用 root 登录和密码认证
4. 我的服务器已加固。如何安装应用所需的软件？
5. 服务器已锁定。现在我需要在其上部署应用的运行时——正确版本的 Python、Node 或其他所需组件。但我不确定如何在 Linux 上安装软件而不破坏任何东西。
