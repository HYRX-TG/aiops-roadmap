---
id: environment-variables
title: Environment Variables and Config
zone: running
edges:
  to:
    - id: process-management
      question: >-
        My app is configured. How do I keep it running reliably after I close
        SSH?
      detail: >-
        I've been starting my app by running it in an SSH session, and the
        moment I close the terminal it just dies. If the server reboots it's
        gone completely. How do I make it stay running regardless of what
        happens?
difficulty: 1
tags:
  - environment-variables
  - secrets
  - config
  - dotenv
  - 12factor
  - systemd
category: concept
milestones:
  - Store app configuration in environment variables instead of hardcoded values
  - Create a .env file on the server and ensure it is not committed to Git
  - Configure a systemd service to load environment variables from a file
title_zh: "环境变量与配置"

---


Every app needs configuration that varies between environments: your laptop uses a local database, the server uses a real one. Your laptop can have test API keys; the server needs production keys. The wrong approach is to hardcode these values in your code. The right approach is environment variables.

An environment variable is a key-value pair that exists in the process's environment. Your app reads them at runtime. They are not in your code, not in your Git history, and different on every server.

<!-- DEEP_DIVE -->

**Why not hardcode config?**

```python
# BAD — the database password is in your code and will be committed to Git
DATABASE_URL = "postgresql://admin:s3cr3tpassword@localhost/mystore"
STRIPE_SECRET_KEY = "sk_live_abc123..."

# GOOD — read from environment, fail loudly if missing
import os
DATABASE_URL = os.environ["DATABASE_URL"]
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
```

Once a secret is in Git history, it is there forever — even if you delete the line later, it is in every commit before that deletion. Anyone with read access to the repo has the secret. Secrets that end up in public repos get scraped by bots within minutes.

**Setting environment variables**

```bash
# Set for the current shell session only (lost when you close the terminal)
export DATABASE_URL="postgresql://deploy:password@localhost/mystore"

# Verify
echo $DATABASE_URL

# Run your app with the variable set
DATABASE_URL="postgresql://..." python3 app.py
```

**The .env file**

For multiple variables, use a `.env` file on the server. This is a plain text file with one `KEY=VALUE` per line:

```bash
# /home/deploy/mystore/.env
DATABASE_URL=postgresql://deploy:password@localhost/mystore
SECRET_KEY=a-very-long-random-string-here-use-openssl-rand-hex-32
STRIPE_SECRET_KEY=sk_live_abc123...
FLASK_ENV=production
DEBUG=false
```

```bash
# Generate a strong random secret key
openssl rand -hex 32
# d8e4f3a1b2c9...

# Lock down permissions — only your user can read it
chmod 600 /home/deploy/mystore/.env

# Make sure it is in .gitignore — never commit this file
echo ".env" >> /home/deploy/mystore/.gitignore
```

To use the `.env` file in your shell session:

```bash
# Source it — loads all variables into the current shell
source /home/deploy/mystore/.env

# Or use dotenv-style loading from your app
# (python-dotenv, dotenv for Node, etc.)
```

**Loading .env in systemd (the right way for production)**

When your app runs as a systemd service, it does not have your shell session's environment. You need to explicitly pass variables:

```ini
# /etc/systemd/system/mystore.service
[Unit]
Description=My Store Application
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/mystore
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

The `EnvironmentFile=` directive reads your `.env` file and injects all the variables into the service's environment. Your app sees them as normal environment variables.

```bash
# After editing the service file, reload systemd and restart
sudo systemctl daemon-reload
sudo systemctl restart mystore

# Verify the service sees the variables
sudo systemctl show mystore --property=Environment
```

**Secrets vs. configuration**

Not all config is equally sensitive:

| Type | Example | Sensitivity |
|------|---------|------------|
| Secret | DB password, API key, secret key | High — rotate if exposed |
| Credential | External API URL | Medium — changes per environment |
| Config | Port number, log level | Low — can be in code or env |
| Feature flag | DEBUG=true | Low — often fine in code |

Apply `chmod 600` to your `.env` file so only the file owner can read it. Consider using a secrets manager (AWS Secrets Manager, HashiCorp Vault) once your setup grows beyond a single server.

**If you accidentally commit a secret**

1. Assume it is compromised — someone may have already found it
2. Revoke/rotate the secret immediately (change the password, regenerate the API key)
3. Remove it from code and move to env vars
4. Optionally: rewrite Git history to remove it from commits (but assume it is already out there)

The most important step is #2. Removing from Git history is secondary.

<!-- RESOURCES -->

- [The Twelve-Factor App - Config](https://12factor.net/config) -- type: article, time: 10m
- [systemd EnvironmentFile documentation](https://www.freedesktop.org/software/systemd/man/systemd.exec.html#EnvironmentFile=) -- type: reference, time: 10m
- [python-dotenv](https://pypi.org/project/python-dotenv/) -- type: reference, time: 5m

<!-- ZH_SUMMARY -->
每个应用都需要随环境变化的配置：你的笔记本电脑使用本地数据库，服务器使用真实数据库。你的笔记本电脑可以使用测试 API 密钥；服务器则需要生产密钥。错误的做法是把这些值硬编码在代码中。正确的做法是使用环境变量。

环境变量是存在于进程环境中的键值对。你的应用在运行时读取它们。它们不在你的代码中，不在你的 Git 历史中，并且在每台服务器上都不同。

<!-- ZH_DEEP_DIVE -->
**为什么不硬编码配置？**

```python
# 错误做法——数据库密码写在代码里，会被提交到 Git
DATABASE_URL = "postgresql://admin:s3cr3tpassword@localhost/mystore"
STRIPE_SECRET_KEY = "sk_live_abc123..."

# 正确做法——从环境变量读取，缺失时立即报错
import os
DATABASE_URL = os.environ["DATABASE_URL"]
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
```

一旦密钥进入 Git 历史，它就会永远留在那里——即使你后来删除了那一行，它仍然存在于删除之前的每一次提交中。任何对仓库有读权限的人都能拿到这个密钥。最终进入公开仓库的密钥会在几分钟内被机器人抓取。

**设置环境变量**

```bash
# 仅在当前 shell 会话中设置（关闭终端后失效）
export DATABASE_URL="postgresql://deploy:password@localhost/mystore"

# 验证
echo $DATABASE_URL

# 在设置了该变量的情况下运行应用
DATABASE_URL="postgresql://..." python3 app.py
```

**.env 文件**

当变量较多时，在服务器上使用 `.env` 文件。这是一个纯文本文件，每行一个 `KEY=VALUE`：

```bash
# /home/deploy/mystore/.env
DATABASE_URL=postgresql://deploy:password@localhost/mystore
SECRET_KEY=a-very-long-random-string-here-use-openssl-rand-hex-32
STRIPE_SECRET_KEY=sk_live_abc123...
FLASK_ENV=production
DEBUG=false
```

```bash
# 生成强随机密钥
openssl rand -hex 32
# d8e4f3a1b2c9...

# 锁定权限——只有你的用户能读取
chmod 600 /home/deploy/mystore/.env

# 确保它被加入 .gitignore——永远不要提交此文件
echo ".env" >> /home/deploy/mystore/.gitignore
```

要在 shell 会话中使用 `.env` 文件：

```bash
# source 它——将所有变量加载到当前 shell
source /home/deploy/mystore/.env

# 或在应用中使用 dotenv 风格的加载方式
# （python-dotenv、Node 的 dotenv 等）
```

**在 systemd 中加载 .env（生产环境的正确做法）**

当你的应用作为 systemd 服务运行时，它没有你 shell 会话的环境变量。你需要显式传入变量：

```ini
# /etc/systemd/system/mystore.service
[Unit]
Description=My Store Application
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/mystore
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

`EnvironmentFile=` 指令会读取你的 `.env` 文件，并将所有变量注入服务的环境中。你的应用会将它们视为普通的环境变量。

```bash
# 编辑服务文件后，重新加载 systemd 并重启
sudo systemctl daemon-reload
sudo systemctl restart mystore

# 验证服务能看到这些变量
sudo systemctl show mystore --property=Environment
```

**密钥与配置的区别**

并非所有配置都同样敏感：

| 类型 | 示例 | 敏感度 |
|------|---------|------------|
| 密钥 | 数据库密码、API key、secret key | 高——一旦泄露就轮换 |
| 凭据 | 外部 API URL | 中——随环境变化 |
| 配置 | 端口号、日志级别 | 低——可放在代码或环境变量中 |
| 功能开关 | DEBUG=true | 低——通常放在代码中即可 |

对 `.env` 文件应用 `chmod 600`，使只有文件所有者能读取它。当你的部署规模超出单台服务器时，考虑使用密钥管理器（AWS Secrets Manager、HashiCorp Vault）。

**如果你不小心提交了密钥**

1. 假定它已泄露——可能已经有人发现了它
2. 立即撤销/轮换该密钥（修改密码、重新生成 API key）
3. 从代码中移除它，改为使用环境变量
4. 可选：重写 Git 历史以从提交中移除它（但假定它已经流出去了）

最重要的步骤是第 2 步。从 Git 历史中移除是次要的。

<!-- ZH_RESOURCES -->
- [十二要素应用 - 配置](https://12factor.net/config) -- 类型: 文章, 时间: 10分钟
- [systemd EnvironmentFile 文档](https://www.freedesktop.org/software/systemd/man/systemd.exec.html#EnvironmentFile=) -- 类型: 参考, 时间: 10分钟
- [python-dotenv](https://pypi.org/project/python-dotenv/) -- 类型: 参考, 时间: 5分钟

<!-- ZH_UI -->
1. 将应用配置存储在环境变量中，而不是硬编码值
2. 在服务器上创建 .env 文件，并确保它不被提交到 Git
3. 配置 systemd 服务从文件加载环境变量
4. 我的应用已配置好。关闭 SSH 后，如何让它可靠地持续运行？
5. 我一直通过在 SSH 会话中运行来启动应用，一关闭终端它就挂了。如果服务器重启，它就彻底没了。无论发生什么，我怎样才能让它保持运行？
