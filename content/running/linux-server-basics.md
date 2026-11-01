---
id: linux-server-basics
title: Linux Server Basics
zone: running
edges:
  to:
    - id: deploying-your-code
      question: I can manage a Linux server. How do I get my code onto it?
      detail: >-
        I can SSH in and install packages. But my app code is still sitting on
        my laptop. How do I actually move it to the server, install what it
        needs, and get it running?
    - id: users-and-permissions
      zone: foundations
      question: I keep hitting permission denied. What is actually going on with users and permissions?
      detail: >-
        I'm using chmod and chown but I'm mostly guessing. Why does 755 work
        but 644 doesn't for my script? What does it mean that a file has an
        owner and a group? I want to understand the model, not just copy
        commands until something works.
    - id: systemd-and-services
      zone: foundations
      question: I'm using systemctl but I don't really understand what systemd is doing.
      detail: >-
        I can start and stop services, but when something goes wrong I don't
        know where to look or what the error means. What is systemd actually
        doing under the hood — how does it manage processes, what are unit
        files really, and how do I debug it properly?
    - id: files-and-filesystems
      zone: foundations
      question: I keep seeing paths like /etc and /var — how is the Linux filesystem actually organized?
      detail: >-
        I know the paths by muscle memory but I don't really understand the
        logic. Why is config in /etc? Why are logs in /var/log and not somewhere
        else? Is there a system to this, or is it just historical accident?
difficulty: 1
tags:
  - linux
  - ssh
  - systemd
  - apt
  - permissions
  - server-admin
category: practice
milestones:
  - SSH into a remote server and navigate the filesystem
  - Install packages with apt and manage services with systemctl
  - Create a non-root user with sudo access and set up SSH key authentication
title_zh: "Linux 服务器基础"

---


You have a server — a cloud VM with a public IP, running Ubuntu. Now you need to actually use it. That means connecting to it remotely, navigating the filesystem, installing software, managing services, and doing basic security hardening. These are the fundamental skills of Linux server administration, and you will use them every single day as an SRE.

<!-- DEEP_DIVE -->

**SSH (Secure Shell)** is how you connect to a server. It gives you a terminal session on the remote machine, encrypted end-to-end. Every command you type runs on the server, not on your laptop:

```bash
# Connect as root (first time only — you will create a proper user)
ssh root@143.198.100.50

# Connect as a regular user
ssh deploy@143.198.100.50

# Connect with a specific key file
ssh -i ~/.ssh/my_key deploy@143.198.100.50
```

**SSH key authentication** is more secure than passwords. You generate a key pair on your laptop — a private key (stays on your laptop, never shared) and a public key (goes on the server). When you connect, SSH uses cryptographic challenge-response to prove you have the private key without ever sending it over the network:

```bash
# Generate an SSH key pair (on your laptop)
ssh-keygen -t ed25519 -C "your-email@example.com"
# Creates: ~/.ssh/id_ed25519 (private) and ~/.ssh/id_ed25519.pub (public)

# Copy your public key to the server
ssh-copy-id deploy@143.198.100.50

# Now you can log in without a password
ssh deploy@143.198.100.50
```

**First things first — create a non-root user.** Running everything as root is dangerous. One typo and you can destroy the entire system. Create a regular user with `sudo` access:

```bash
# On the server as root:
adduser deploy                  # Create user, set password
usermod -aG sudo deploy         # Give sudo access

# Copy your SSH key to the new user
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Now log out and log back in as deploy
exit
ssh deploy@143.198.100.50

# Test sudo
sudo whoami    # Should print "root"
```

**The Linux filesystem** has a standard layout. Knowing where things live saves you time:

| Path | What lives there |
|------|-----------------|
| `/` | Root of everything |
| `/home/deploy/` | Your user's home directory |
| `/etc/` | Configuration files (nginx.conf, systemd services) |
| `/var/log/` | Log files |
| `/var/www/` | Web content (by convention) |
| `/tmp/` | Temporary files (cleared on reboot) |
| `/usr/bin/` | Installed programs |
| `/opt/` | Optional/third-party software |

```bash
# Useful navigation commands
pwd                    # Where am I?
ls -la                 # List files with details
cd /etc/nginx/         # Go to nginx config
cat /etc/os-release    # What OS is this?
df -h                  # Disk usage
free -h                # Memory usage
htop                   # Live process monitor (install with apt)
```

**Package management with `apt`** is how you install software on Ubuntu/Debian:

```bash
# Update the package list (always do this first)
sudo apt update

# Install packages
sudo apt install nginx python3 python3-pip python3-venv git htop

# Upgrade all installed packages
sudo apt upgrade

# Remove a package
sudo apt remove nginx

# Search for packages
apt search postgres
```

**File permissions** control who can read, write, and execute files. Every file has an owner, a group, and permissions for owner/group/others:

```bash
ls -la myapp/
# -rw-r--r-- 1 deploy deploy  1234 Jan 15 10:00 app.py
# drwxr-xr-x 2 deploy deploy  4096 Jan 15 10:00 static/
#
# -rw-r--r-- means:
#   owner (deploy): read + write
#   group (deploy): read only
#   others:         read only

# Change permissions
chmod 755 script.sh     # rwxr-xr-x (owner can execute, others can read/execute)
chmod 600 secret.key    # rw------- (only owner can read/write)

# Change ownership
sudo chown deploy:deploy /var/www/mystore
```

**systemd** is the service manager on modern Linux. It starts services on boot, restarts them if they crash, and manages their logs. Every long-running process on your server should be a systemd service:

```bash
# Check if a service is running
sudo systemctl status nginx

# Start, stop, restart a service
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# Enable a service to start on boot
sudo systemctl enable nginx

# View logs for a service
sudo journalctl -u nginx           # All logs
sudo journalctl -u nginx -f        # Follow (tail) logs in real time
sudo journalctl -u nginx --since "1 hour ago"
```

Creating your own systemd service (you will do this for your app):

```ini
# /etc/systemd/system/mystore.service
[Unit]
Description=My Store Application
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/mystore
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Load the new service, enable and start it
sudo systemctl daemon-reload
sudo systemctl enable mystore
sudo systemctl start mystore
```

**Basic security hardening** — a few things you should do on every new server:

```bash
# 1. Disable root login via SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 2. Disable password authentication (use keys only)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 3. Set up a firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable

# 4. Keep the system updated
sudo apt update && sudo apt upgrade
```

**Why SREs care:** Linux server management is the most fundamental SRE skill. Every production system, every CI/CD pipeline, every container — it all runs on Linux. SSH, systemd, package management, file permissions, log reading — you will use these daily. When a service goes down at 2 AM, the first thing you do is SSH in and check `systemctl status` and `journalctl`.

<!-- RESOURCES -->

- [DigitalOcean - Initial Server Setup with Ubuntu](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) -- type: tutorial, time: 20m
- [Linux Journey](https://linuxjourney.com/) -- type: interactive, time: varies
- [The Linux Command Line (free book)](https://linuxcommand.org/tlcl.php) -- type: book, time: varies
- [systemd for Developers](https://systemd.io/) -- type: reference, time: 15m
- [SSH Key Authentication - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server) -- type: tutorial, time: 15m

<!-- ZH_SUMMARY -->
你有一台服务器——一台带公网 IP 的云虚拟机，运行着 Ubuntu。现在你需要真正使用它。这意味着要远程连接它、浏览文件系统、安装软件、管理服务，以及进行基本的安全加固。这些是 Linux 服务器管理的基本技能，作为 SRE，你每天都会用到它们。

<!-- ZH_DEEP_DIVE -->
**SSH（Secure Shell）** 是你连接服务器的方式。它在远程机器上为你提供一个终端会话，端到端加密。你输入的每条命令都在服务器上运行，而不是在你的笔记本电脑上：

```bash
# 以 root 身份连接（仅首次——之后你会创建一个正式用户）
ssh root@143.198.100.50

# 以普通用户身份连接
ssh deploy@143.198.100.50

# 使用指定的密钥文件连接
ssh -i ~/.ssh/my_key deploy@143.198.100.50
```

**SSH 密钥认证**比密码更安全。你在笔记本电脑上生成一对密钥——一个私钥（留在你的笔记本电脑上，绝不共享）和一个公钥（放到服务器上）。当你连接时，SSH 使用加密质询-响应来证明你拥有私钥，而无需通过网络发送它：

```bash
# 生成 SSH 密钥对（在你的笔记本电脑上）
ssh-keygen -t ed25519 -C "your-email@example.com"
# 生成：~/.ssh/id_ed25519（私钥）和 ~/.ssh/id_ed25519.pub（公钥）

# 将你的公钥复制到服务器
ssh-copy-id deploy@143.198.100.50

# 现在你可以无需密码登录
ssh deploy@143.198.100.50
```

**首先要做的事——创建一个非 root 用户。** 以 root 身份运行一切是危险的。一个笔误就可能摧毁整个系统。创建一个具有 `sudo` 权限的普通用户：

```bash
# 在服务器上以 root 身份：
adduser deploy                  # 创建用户，设置密码
usermod -aG sudo deploy         # 授予 sudo 权限

# 将你的 SSH 密钥复制给新用户
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# 现在登出并以 deploy 身份重新登录
exit
ssh deploy@143.198.100.50

# 测试 sudo
sudo whoami    # 应输出 "root"
```

**Linux 文件系统**有标准的布局。了解东西放在哪里能节省你的时间：

| 路径 | 存放内容 |
|------|-----------------|
| `/` | 一切的根 |
| `/home/deploy/` | 你的用户主目录 |
| `/etc/` | 配置文件（nginx.conf、systemd 服务） |
| `/var/log/` | 日志文件 |
| `/var/www/` | Web 内容（按惯例） |
| `/tmp/` | 临时文件（重启时清除） |
| `/usr/bin/` | 已安装的程序 |
| `/opt/` | 可选/第三方软件 |

```bash
# 有用的导航命令
pwd                    # 我在哪？
ls -la                 # 列出文件及详细信息
cd /etc/nginx/         # 进入 nginx 配置目录
cat /etc/os-release    # 这是什么操作系统？
df -h                  # 磁盘使用情况
free -h                # 内存使用情况
htop                   # 实时进程监控（用 apt 安装）
```

**使用 `apt` 进行包管理**是在 Ubuntu/Debian 上安装软件的方式：

```bash
# 更新软件包列表（始终先做这一步）
sudo apt update

# 安装软件包
sudo apt install nginx python3 python3-pip python3-venv git htop

# 升级所有已安装的软件包
sudo apt upgrade

# 移除软件包
sudo apt remove nginx

# 搜索软件包
apt search postgres
```

**文件权限**控制谁可以读取、写入和执行文件。每个文件都有一个所有者、一个组，以及针对所有者/组/其他人的权限：

```bash
ls -la myapp/
# -rw-r--r-- 1 deploy deploy  1234 Jan 15 10:00 app.py
# drwxr-xr-x 2 deploy deploy  4096 Jan 15 10:00 static/
#
# -rw-r--r-- 意味着：
#   所有者 (deploy)：读 + 写
#   组 (deploy)：    只读
#   其他人：         只读

# 更改权限
chmod 755 script.sh     # rwxr-xr-x（所有者可执行，其他人可读/执行）
chmod 600 secret.key    # rw-------（仅所有者可读/写）

# 更改所有权
sudo chown deploy:deploy /var/www/mystore
```

**systemd** 是现代 Linux 上的服务管理器。它在启动时启动服务，在服务崩溃时重启它们，并管理它们的日志。你服务器上每个长期运行的进程都应该是一个 systemd 服务：

```bash
# 检查服务是否正在运行
sudo systemctl status nginx

# 启动、停止、重启服务
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# 启用服务以便开机启动
sudo systemctl enable nginx

# 查看服务的日志
sudo journalctl -u nginx           # 所有日志
sudo journalctl -u nginx -f        # 实时跟踪（tail）日志
sudo journalctl -u nginx --since "1 hour ago"
```

创建你自己的 systemd 服务（你会为你的应用这样做）：

```ini
# /etc/systemd/system/mystore.service
[Unit]
Description=My Store Application
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/mystore
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# 加载新服务，启用并启动它
sudo systemctl daemon-reload
sudo systemctl enable mystore
sudo systemctl start mystore
```

**基本安全加固**——你应该在每台新服务器上做几件事：

```bash
# 1. 通过 SSH 禁用 root 登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 2. 禁用密码认证（仅使用密钥）
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 3. 设置防火墙
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable

# 4. 保持系统更新
sudo apt update && sudo apt upgrade
```

**为什么 SRE 关心这些：** Linux 服务器管理是最基础的 SRE 技能。每个生产系统、每条 CI/CD 流水线、每个容器——都运行在 Linux 上。SSH、systemd、包管理、文件权限、日志阅读——你会每天用到这些。当服务在凌晨 2 点宕机时，你做的第一件事就是 SSH 登录并检查 `systemctl status` 和 `journalctl`。

<!-- ZH_RESOURCES -->
- [DigitalOcean - Ubuntu 初始服务器设置](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) -- 类型: 教程, 时长: 20m
- [Linux Journey](https://linuxjourney.com/) -- 类型: 交互式, 时长: 不定
- [The Linux Command Line（免费书籍）](https://linuxcommand.org/tlcl.php) -- 类型: 书籍, 时长: 不定
- [systemd for Developers](https://systemd.io/) -- 类型: 参考, 时长: 15m
- [SSH 密钥认证 - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server) -- 类型: 教程, 时长: 15m

<!-- ZH_UI -->
1. SSH 登录远程服务器并浏览文件系统
2. 用 apt 安装软件包，用 systemctl 管理服务
3. 创建具有 sudo 权限的非 root 用户并配置 SSH 密钥认证
4. 我能管理一台 Linux 服务器了。怎么把代码放上去？
5. 我能 SSH 登录并安装软件包，但应用代码还在笔记本上。到底怎么把它传到服务器、装好依赖并跑起来？
6. 我总是遇到 permission denied。用户和权限到底是怎么回事？
7. 我在用 chmod 和 chown，但基本靠猜。为什么 755 对我的脚本有效而 644 不行？文件有所有者和所属组是什么意思？我想理解这套模型，而不是一直复制命令直到碰巧能用。
8. 我在用 systemctl，但不太明白 systemd 在做什么。
9. 我能启动和停止服务，但出问题时不知道该看哪里、错误是什么意思。systemd 底层到底在做什么——它如何管理进程、unit 文件究竟是什么、我该如何正确调试？
10. 我总看到 /etc 和 /var 这样的路径——Linux 文件系统到底是怎么组织的？
11. 我靠肌肉记忆记住了这些路径，但并没真正理解其中的逻辑。为什么配置在 /etc？为什么日志在 /var/log 而不是别处？这背后有体系，还是只是历史偶然？
