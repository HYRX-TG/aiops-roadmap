---
id: installing-software
title: Installing Software on Linux
zone: running
edges:
  to:
    - id: ports-and-listening
      question: >-
        I have my runtime installed and my app running. How does traffic
        actually reach it?
      detail: >-
        My app is running, but when I try to access it from another machine
        nothing comes through. I don't really understand what a port is or how
        traffic is supposed to get from the internet to the process running on
        my server.
difficulty: 1
tags:
  - apt
  - package-manager
  - ubuntu
  - nodejs
  - python
  - runtime
  - dependencies
category: practice
milestones:
  - >-
    Install a package using apt and understand the difference between apt update
    and apt install
  - >-
    Install Node.js or Python on a fresh Ubuntu server using the correct method
    for your runtime
  - >-
    Understand why some software needs a third-party repository instead of the
    default Ubuntu repos
title_zh: "在 Linux 上安装软件"

---


Linux distributions ship with a package manager — a tool for finding, downloading, installing, and updating software. On Ubuntu (and Debian), that is `apt`. It is the primary way you install everything on a server: your app's runtime, web server, database, monitoring tools, everything.

Unlike your laptop where you download a `.dmg` or `.exe` and double-click it, on a server you install software from the terminal, and the package manager handles downloading the right version, checking dependencies, and putting files in the right places.

<!-- DEEP_DIVE -->

**The basics: `apt update` and `apt install`**

`apt` installs from a list of package repositories. The first step is always to update that list so you know what is available:

```bash
# Update the local list of available packages (does NOT upgrade anything)
sudo apt update

# Install a package
sudo apt install nginx

# Install multiple packages at once
sudo apt install nginx git curl htop unzip

# Remove a package
sudo apt remove nginx

# Remove a package AND its config files
sudo apt purge nginx

# Search for a package by name
apt search nodejs
```

Always run `apt update` before installing. If you skip it, you may install an outdated version that has known bugs or security issues.

**Installing Python**

Ubuntu 22.04 ships with Python 3. But you usually need a few extras:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Verify
python3 --version    # Python 3.10.x
pip3 --version
```

For a Python web app, you will also want to use a virtual environment to isolate dependencies:

```bash
# Create a virtualenv for your project
cd /home/deploy/myapp
python3 -m venv venv

# Activate it
source venv/bin/activate

# Now pip installs go into venv/, not system-wide
pip install flask gunicorn

# Deactivate when done
deactivate
```

**Installing Node.js**

The Node.js version in Ubuntu's default repositories is often outdated. Use NodeSource to get a current LTS version:

```bash
# Install Node.js 20 LTS via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version    # v20.x.x
npm --version
```

**Why you sometimes need a third-party repository**

Ubuntu's default package repositories prioritize stability over recency. The Node.js version in the default repos might be years old. Third-party repositories (like NodeSource for Node, or postgresql.org for Postgres) provide newer versions.

When you add a third-party repo, you are trusting that source. Stick to official sources from the software vendor, not random PPAs.

```bash
# Example: what adding a repo looks like under the hood
# The curl | bash command above essentially does this:
# 1. Downloads a script that adds the repo to /etc/apt/sources.list.d/
# 2. Imports the repo's GPG key so apt can verify packages
# 3. Runs apt update
# 4. Now apt install nodejs gets the NodeSource version
```

**Useful packages to always have on a server**

```bash
sudo apt install -y \
    git \          # You'll need this to clone your app
    curl \         # Useful for testing HTTP endpoints locally
    htop \         # Better process viewer than top
    unzip \        # For unpacking archives
    ufw \          # Firewall (may already be installed)
    fail2ban       # Bans IPs with too many failed SSH attempts
```

**Keeping software updated**

```bash
# Update the package list and upgrade all installed packages
sudo apt update && sudo apt upgrade

# Unattended security updates (Ubuntu default — verify it's running)
sudo systemctl status unattended-upgrades
```

Security patches are released constantly. An unpatched server is a liability. Set up unattended security updates and occasionally run a full `apt upgrade` for non-security updates.

**Where apt installs things**

Understanding where files land helps you debug and configure software:

| Path | What goes there |
|------|----------------|
| `/usr/bin/` | Executables (nginx, python3, node) |
| `/etc/nginx/` | Configuration files |
| `/var/log/nginx/` | Log files |
| `/lib/systemd/system/` | systemd service files |
| `/var/lib/` | Application data (database files, etc.) |

<!-- RESOURCES -->

- [Ubuntu apt documentation](https://ubuntu.com/server/docs/package-management) -- type: reference, time: 15m
- [NodeSource - Node.js Installation](https://github.com/nodesource/distributions) -- type: reference, time: 10m
- [Python venv documentation](https://docs.python.org/3/library/venv.html) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
Linux 发行版自带包管理器——一种用于查找、下载、安装和更新软件的工具。在 Ubuntu（以及 Debian）上，这个工具就是 `apt`。它是你在服务器上安装一切软件的主要方式：应用的运行时、Web 服务器、数据库、监控工具，等等。

与你在笔记本电脑上下载 `.dmg` 或 `.exe` 并双击安装不同，在服务器上你需要从终端安装软件，而包管理器会负责下载正确的版本、检查依赖关系，并把文件放到正确的位置。

<!-- ZH_DEEP_DIVE -->
**基础知识：`apt update` 与 `apt install`**

`apt` 从一系列软件包仓库中安装软件。第一步始终是更新该列表，以便了解有哪些可用的软件包：

```bash
# 更新本地可用软件包列表（不会升级任何软件）
sudo apt update

# 安装一个软件包
sudo apt install nginx

# 一次安装多个软件包
sudo apt install nginx git curl htop unzip

# 移除一个软件包
sudo apt remove nginx

# 移除软件包及其配置文件
sudo apt purge nginx

# 按名称搜索软件包
apt search nodejs
```

安装前务必先运行 `apt update`。如果跳过这一步，你可能会安装到存在已知缺陷或安全问题的过时版本。

**安装 Python**

Ubuntu 22.04 自带 Python 3。但通常你还需要一些额外的组件：

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 验证
python3 --version    # Python 3.10.x
pip3 --version
```

对于 Python Web 应用，你还需要使用虚拟环境来隔离依赖：

```bash
# 为你的项目创建虚拟环境
cd /home/deploy/myapp
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 现在 pip 安装的包会进入 venv/，而不是系统全局
pip install flask gunicorn

# 完成后停用
deactivate
```

**安装 Node.js**

Ubuntu 默认仓库中的 Node.js 版本通常已经过时。使用 NodeSource 获取最新的 LTS 版本：

```bash
# 通过 NodeSource 安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node --version    # v20.x.x
npm --version
```

**为什么有时需要第三方仓库**

Ubuntu 默认的软件包仓库优先考虑稳定性而非新版本。默认仓库中的 Node.js 版本可能已经有好几年了。第三方仓库（如 Node 的 NodeSource，或 Postgres 的 postgresql.org）提供更新的版本。

当你添加第三方仓库时，你就是在信任该来源。请坚持使用软件厂商的官方来源，而不是随意的 PPA。

```bash
# 示例：添加仓库在底层大致是这样的
# 上面的 curl | bash 命令本质上做了这些事：
# 1. 下载一个脚本，将仓库添加到 /etc/apt/sources.list.d/
# 2. 导入该仓库的 GPG 密钥，以便 apt 能验证软件包
# 3. 运行 apt update
# 4. 现在 apt install nodejs 获取的是 NodeSource 的版本
```

**服务器上应常备的实用软件包**

```bash
sudo apt install -y \
    git \          # 克隆应用时需要用到
    curl \         # 用于在本地测试 HTTP 端点
    htop \         # 比 top 更好的进程查看器
    unzip \        # 用于解压归档文件
    ufw \          # 防火墙（可能已安装）
    fail2ban       # 封禁 SSH 失败尝试过多的 IP
```

**保持软件更新**

```bash
# 更新软件包列表并升级所有已安装的软件包
sudo apt update && sudo apt upgrade

# 无人值守的安全更新（Ubuntu 默认——确认它正在运行）
sudo systemctl status unattended-upgrades
```

安全补丁不断发布。未打补丁的服务器是一种隐患。请设置无人值守的安全更新，并偶尔运行一次完整的 `apt upgrade` 来获取非安全更新。

**apt 将文件安装到哪里**

了解文件落在何处有助于你调试和配置软件：

| 路径 | 存放内容 |
|------|----------------|
| `/usr/bin/` | 可执行文件（nginx、python3、node） |
| `/etc/nginx/` | 配置文件 |
| `/var/log/nginx/` | 日志文件 |
| `/lib/systemd/system/` | systemd 服务文件 |
| `/var/lib/` | 应用数据（数据库文件等） |

<!-- ZH_RESOURCES -->
- [Ubuntu apt 文档](https://ubuntu.com/server/docs/package-management) -- 类型: 参考, 时间: 15m
- [NodeSource - Node.js 安装](https://github.com/nodesource/distributions) -- 类型: 参考, 时间: 10m
- [Python venv 文档](https://docs.python.org/3/library/venv.html) -- 类型: 参考, 时间: 10m

<!-- ZH_UI -->
1. 使用 apt 安装软件包，并理解 apt update 与 apt install 的区别
2. 在全新的 Ubuntu 服务器上，用适合你运行时的正确方法安装 Node.js 或 Python
3. 理解为什么有些软件需要第三方仓库而不是默认的 Ubuntu 仓库
4. 我的运行时已安装、应用已运行。流量究竟是如何到达它的？
5. 我的应用在运行，但从另一台机器访问时没有任何响应。我不太理解端口是什么，也不清楚流量应该如何从互联网到达服务器上运行的进程。
