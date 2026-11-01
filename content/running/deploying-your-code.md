---
id: deploying-your-code
title: Getting Your Code to the Server
zone: running
edges:
  to:
    - id: web-servers
      question: My code is on the server. What software actually serves it to users?
      detail: >-
        My app is running on port 5000 and I have to include the port in every
        URL. Real sites don't work like that — something must be handling HTTP
        on port 80 and forwarding requests to my app. What is that?
    - id: environment-variables
      question: >-
        My code is on the server. How do I configure it without hardcoding
        secrets?
      detail: >-
        My database password and API keys are hardcoded right now. If anyone
        gets access to the repo they'd have everything. How do I get those
        credentials out of the code entirely?
difficulty: 1
tags:
  - deploy
  - git-clone
  - scp
  - rsync
  - environment-variables
  - secrets
category: practice
milestones:
  - Get your application code onto a server using git clone
  - Set up a Python virtual environment and install dependencies on the server
  - >-
    Configure environment variables and understand why secrets should not be in
    code
title_zh: "将代码部署到服务器"

---


You have a server. You can SSH in. You can install packages and manage services. But your application code is still on your laptop. How do you get it onto the server?

This is the most basic form of deployment — manually getting your code from where you wrote it to where it runs. It is not glamorous, and you will eventually automate it, but understanding the manual process is essential.

<!-- DEEP_DIVE -->

**Option 1: `git clone` — the most common approach**

Your code is already in a Git repository on GitHub (or GitLab, or Bitbucket). The server has `git` installed. So the simplest way to get your code onto the server is to clone it:

```bash
# SSH into your server
ssh deploy@143.198.100.50

# Clone your repository
cd /home/deploy
git clone https://github.com/yourname/mystore.git

# Your code is now on the server
ls mystore/
# app.py  requirements.txt  static/  templates/  ...
```

This is by far the most common method. Your Git repo is the source of truth, and the server pulls from it. When you push new code to GitHub, you SSH in and pull the latest:

```bash
cd /home/deploy/mystore
git pull origin main
```

If your repo is private, you will need to set up authentication. The cleanest way is a **deploy key** — an SSH key that only has read access to that one repository:

```bash
# On the server, generate a deploy key
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""

# Add the public key to your GitHub repo:
# Settings → Deploy keys → Add deploy key
cat ~/.ssh/deploy_key.pub

# Configure git to use this key
echo 'Host github.com
  IdentityFile ~/.ssh/deploy_key' >> ~/.ssh/config
```

**Option 2: `scp` and `rsync` — copy files directly**

Sometimes you want to copy files straight from your laptop to the server without going through GitHub. `scp` (secure copy) works like `cp` but over SSH:

```bash
# From your laptop — copy a single file
scp app.py deploy@143.198.100.50:/home/deploy/mystore/

# Copy an entire directory
scp -r mystore/ deploy@143.198.100.50:/home/deploy/

# rsync is smarter — only copies changed files
rsync -avz mystore/ deploy@143.198.100.50:/home/deploy/mystore/
```

`rsync` is better than `scp` for repeated deployments because it only transfers files that have changed. It also handles permissions and can delete files on the server that you deleted locally.

**Setting up the project on the server**

Getting the code there is step one. Now you need to install dependencies and configure the environment. For a Python app:

```bash
# Create a virtual environment
cd /home/deploy/mystore
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test that it runs
python app.py
# * Running on http://127.0.0.1:5000
```

**Environment variables and secrets**

Your app probably needs configuration that varies between your laptop and the server — database URLs, API keys, secret keys. **Never put these in your code or commit them to Git.**

```bash
# BAD — hardcoded secrets in code
# app.py
DATABASE_URL = "postgresql://admin:s3cret@localhost/mystore"  # DO NOT DO THIS

# GOOD — read from environment variables
# app.py
import os
DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
```

On the server, set environment variables in a `.env` file that is NOT in your Git repo:

```bash
# Create .env on the server (not in git)
cat > /home/deploy/mystore/.env << 'EOF'
DATABASE_URL=postgresql://deploy:password@localhost/mystore
SECRET_KEY=a-long-random-string-here
FLASK_ENV=production
EOF

# Make sure .env is in .gitignore
echo ".env" >> .gitignore

# Lock down permissions — only the owner can read it
chmod 600 /home/deploy/mystore/.env
```

For systemd services, you can pass environment variables in the service file:

```ini
[Service]
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

**The manual deploy workflow**

Putting it all together, here is what a manual deployment looks like:

```bash
# 1. SSH into the server
ssh deploy@143.198.100.50

# 2. Go to the project directory
cd /home/deploy/mystore

# 3. Pull the latest code
git pull origin main

# 4. Install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart the application
sudo systemctl restart mystore

# 6. Check that it is running
sudo systemctl status mystore
sudo journalctl -u mystore --since "1 minute ago"
```

Six steps, every single time you make a change. Push to GitHub, SSH in, pull, install, restart, verify. Miss a step and something breaks. Do it at 2 AM when you are tired and you might forget to activate the virtualenv or skip the dependency install.

This is tedious and error-prone. You will eventually automate it with CI/CD pipelines that run these steps automatically when you push code. But right now, understanding the manual process means you understand what automation is actually automating.

**Common mistakes:**

- **Forgetting to install new dependencies** — you added a package to `requirements.txt` but forgot to `pip install` on the server
- **Running as root** — always deploy as a non-root user. Root access should be for system administration only
- **Committing secrets** — once a password is in Git history, it is there forever. Rotate any secret that was ever committed
- **Not restarting the service** — your code changed but the running process is still using the old code. You must restart
- **Editing code directly on the server** — now your server has changes that are not in Git. This always ends badly

<!-- RESOURCES -->

- [DigitalOcean - How to Deploy a Flask App](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04) -- type: tutorial, time: 30m
- [GitHub - Deploy Keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) -- type: reference, time: 10m
- [The Twelve-Factor App - Config](https://12factor.net/config) -- type: article, time: 10m
- [rsync Tutorial](https://www.digitalocean.com/community/tutorials/how-to-use-rsync-to-sync-local-and-remote-directories) -- type: tutorial, time: 15m

<!-- ZH_SUMMARY -->
你有一台服务器。你可以通过 SSH 登录。你可以安装软件包并管理服务。但你的应用代码仍在你的笔记本电脑上。你如何把它放到服务器上？

这是最基础的部署形式——手动将代码从你编写它的地方传送到它运行的地方。它并不光鲜，你最终会将其自动化，但理解手动流程至关重要。

<!-- ZH_DEEP_DIVE -->
**选项 1：`git clone` —— 最常见的方式**

你的代码已经在 GitHub（或 GitLab、Bitbucket）上的 Git 仓库里了。服务器上安装了 `git`。所以把代码放到服务器上最简单的方式就是克隆它：

```bash
# SSH into your server
ssh deploy@143.198.100.50

# Clone your repository
cd /home/deploy
git clone https://github.com/yourname/mystore.git

# Your code is now on the server
ls mystore/
# app.py  requirements.txt  static/  templates/  ...
```

这是迄今为止最常见的方法。你的 Git 仓库是唯一可信来源，服务器从它拉取代码。当你把新代码推送到 GitHub 后，SSH 登录服务器并拉取最新代码：

```bash
cd /home/deploy/mystore
git pull origin main
```

如果你的仓库是私有的，你需要配置认证。最干净的方式是使用 **deploy key** —— 一个只对该仓库有读权限的 SSH 密钥：

```bash
# On the server, generate a deploy key
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""

# Add the public key to your GitHub repo:
# Settings → Deploy keys → Add deploy key
cat ~/.ssh/deploy_key.pub

# Configure git to use this key
echo 'Host github.com
  IdentityFile ~/.ssh/deploy_key' >> ~/.ssh/config
```

**选项 2：`scp` 和 `rsync` —— 直接复制文件**

有时你想直接从笔记本电脑把文件复制到服务器，而不经过 GitHub。`scp`（secure copy）的用法类似 `cp`，但通过 SSH 传输：

```bash
# From your laptop — copy a single file
scp app.py deploy@143.198.100.50:/home/deploy/mystore/

# Copy an entire directory
scp -r mystore/ deploy@143.198.100.50:/home/deploy/

# rsync is smarter — only copies changed files
rsync -avz mystore/ deploy@143.198.100.50:/home/deploy/mystore/
```

对于重复部署，`rsync` 比 `scp` 更好，因为它只传输发生变化的文件。它还能处理权限，并且可以删除服务器上你在本地已删除的文件。

**在服务器上搭建项目**

把代码放上去只是第一步。现在你需要安装依赖并配置环境。对于一个 Python 应用：

```bash
# Create a virtual environment
cd /home/deploy/mystore
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test that it runs
python app.py
# * Running on http://127.0.0.1:5000
```

**环境变量与密钥**

你的应用可能需要一些在笔记本电脑和服务器之间有所不同的配置 —— 数据库 URL、API 密钥、密钥字符串。**绝不要把这些放进代码里，也不要提交到 Git。**

```bash
# BAD — hardcoded secrets in code
# app.py
DATABASE_URL = "postgresql://admin:s3cret@localhost/mystore"  # DO NOT DO THIS

# GOOD — read from environment variables
# app.py
import os
DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
```

在服务器上，把环境变量设置在一个**不在** Git 仓库中的 `.env` 文件里：

```bash
# Create .env on the server (not in git)
cat > /home/deploy/mystore/.env << 'EOF'
DATABASE_URL=postgresql://deploy:password@localhost/mystore
SECRET_KEY=a-long-random-string-here
FLASK_ENV=production
EOF

# Make sure .env is in .gitignore
echo ".env" >> .gitignore

# Lock down permissions — only the owner can read it
chmod 600 /home/deploy/mystore/.env
```

对于 systemd 服务，你可以在 service 文件中传入环境变量：

```ini
[Service]
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

**手动部署流程**

把所有步骤串起来，手动部署大致如下：

```bash
# 1. SSH into the server
ssh deploy@143.198.100.50

# 2. Go to the project directory
cd /home/deploy/mystore

# 3. Pull the latest code
git pull origin main

# 4. Install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart the application
sudo systemctl restart mystore

# 6. Check that it is running
sudo systemctl status mystore
sudo journalctl -u mystore --since "1 minute ago"
```

每次做改动都要走这六步。推送到 GitHub、SSH 登录、拉取、安装、重启、验证。漏掉一步就会出问题。如果你在凌晨 2 点疲惫时操作，可能会忘记激活 virtualenv 或跳过依赖安装。

这既繁琐又容易出错。你最终会用 CI/CD 流水线来自动化它，在推送代码时自动执行这些步骤。但现在，理解手动流程意味着你理解自动化究竟在自动化什么。

**常见错误：**

- **忘记安装新依赖** —— 你在 `requirements.txt` 中添加了一个包，但忘了在服务器上执行 `pip install`
- **以 root 身份运行** —— 始终以非 root 用户部署。root 访问权限应仅用于系统管理
- **提交密钥** —— 一旦密码进入 Git 历史，它就永远在那里了。任何曾被提交过的密钥都要轮换
- **没有重启服务** —— 代码变了，但正在运行的进程仍在使用旧代码。你必须重启
- **直接在服务器上修改代码** —— 现在你的服务器上有 Git 中不存在的改动。这从来不会有好结果

<!-- ZH_RESOURCES -->
- [DigitalOcean - 如何部署 Flask 应用](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04) -- 类型：教程，时长：30m
- [GitHub - 部署密钥](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) -- 类型：参考，时长：10m
- [十二要素应用 - 配置](https://12factor.net/config) -- 类型：文章，时长：10m
- [rsync 教程](https://www.digitalocean.com/community/tutorials/how-to-use-rsync-to-sync-local-and-remote-directories) -- 类型：教程，时长：15m

<!-- ZH_UI -->
1. 使用 git clone 将应用代码放到服务器上
2. 在服务器上搭建 Python 虚拟环境并安装依赖
3. 配置环境变量，理解为什么密钥不应写在代码里
4. 我的代码已经在服务器上了。究竟是什么软件把它提供给用户？
5. 我的应用运行在 5000 端口，每个 URL 都得带上端口。真实网站不是这样——一定有东西在 80 端口处理 HTTP 并把请求转发给我的应用。那是什么？
6. 我的代码已经在服务器上了。如何在不硬编码密钥的情况下配置它？
7. 我的数据库密码和 API 密钥现在是硬编码的。任何人拿到仓库就拿到了一切。如何把这些凭据彻底从代码里移出去？
