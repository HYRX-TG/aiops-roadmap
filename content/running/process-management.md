---
id: process-management
title: Keeping Your App Running with systemd
zone: running
edges:
  to:
    - id: web-servers
      question: >-
        My app is running as a managed service. What handles incoming HTTP
        traffic?
      detail: >-
        My app runs as a systemd service now — it survives disconnects and
        reboots. But I'm still accessing it on port 5000. I need it to work like
        a normal website on port 80, not something I have to type a custom port
        for.
    - id: reading-logs
      question: >-
        My app is running as a systemd service. How do I see its output and
        errors?
      detail: >-
        I started getting errors — requests failing, maybe the service crashing
        and restarting — but I have no idea what's actually happening inside.
        Where does all the output go when there's no terminal to see it?
difficulty: 1
tags:
  - systemd
  - process-management
  - service
  - daemon
  - journald
  - gunicorn
  - pm2
category: practice
milestones:
  - Write a systemd service file for a Python or Node.js application
  - Enable the service to start on boot and verify it restarts after a crash
  - Use journalctl to view live and historical logs for your service
title_zh: "使用 systemd 保持应用持续运行"

---


You run your app: `python3 app.py`. It works. You close your SSH session. The process is gone — it was a child of your shell, and when the shell ended, so did the app. You reboot the server. Your app does not come back.

A process manager solves this. It runs your application as a background service, independent of any shell session. If the app crashes, the process manager restarts it. When the server boots, the process manager starts it automatically. On Linux, that process manager is `systemd`.

<!-- DEEP_DIVE -->

**Why not just use `nohup` or `screen`?**

You might have heard of workarounds:

```bash
# nohup — keeps the process running after logout, but no auto-restart
nohup python3 app.py &

# screen / tmux — keep a persistent session, but fragile and manual
screen -S myapp
python3 app.py
# Ctrl+A, D to detach
```

These work for testing but are bad for production. If your app crashes, it stays dead. If the server reboots, you have to SSH in and manually start it again. Do not use these for anything that matters.

**systemd services**

systemd is the init system on modern Linux — the first process that starts on boot, responsible for starting everything else. Any long-running process should be a systemd service. You define it in a `.service` file:

```ini
# /etc/systemd/system/mystore.service

[Unit]
Description=My Store Application
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/mystore
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Breaking down the important fields:

| Field | What it does |
|-------|-------------|
| `After=network.target` | Do not start until the network is up |
| `User=deploy` | Run as this user (not root) |
| `WorkingDirectory=` | The process's working directory |
| `EnvironmentFile=` | Load environment variables from this file |
| `ExecStart=` | The command to run your app |
| `Restart=always` | Restart if the process exits for any reason |
| `RestartSec=5` | Wait 5 seconds between restart attempts |
| `WantedBy=multi-user.target` | Start this service in normal multi-user mode |

**For a Node.js app:**

```ini
[Unit]
Description=My Node App
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/mynodeapp
EnvironmentFile=/home/deploy/mynodeapp/.env
ExecStart=/usr/bin/node /home/deploy/mynodeapp/server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Enabling and starting the service**

```bash
# Copy the service file to the right location (or create it there directly)
sudo nano /etc/systemd/system/mystore.service

# Tell systemd to reload its service file list
sudo systemctl daemon-reload

# Enable: start automatically on boot
sudo systemctl enable mystore

# Start: run it right now
sudo systemctl start mystore

# Check status
sudo systemctl status mystore
```

The status output looks like:

```
● mystore.service - My Store Application
     Loaded: loaded (/etc/systemd/system/mystore.service; enabled)
     Active: active (running) since Mon 2024-01-15 10:00:00 UTC; 5min ago
   Main PID: 12345 (gunicorn)
      Tasks: 5 (limit: 2340)
     Memory: 85.3M
        CPU: 1.234s
     CGroup: /system.slice/mystore.service
             ├─12345 /home/deploy/mystore/venv/bin/python3 -c ...
             └─12346 ...
```

**Managing a running service**

```bash
# Stop the service
sudo systemctl stop mystore

# Restart (stop then start) — use this after updating your code
sudo systemctl restart mystore

# Reload (if the app supports it — sends SIGHUP)
sudo systemctl reload mystore

# Check if it will start on boot
sudo systemctl is-enabled mystore

# Disable autostart
sudo systemctl disable mystore
```

**Viewing logs**

systemd captures all stdout and stderr from your service:

```bash
# All logs for your service
sudo journalctl -u mystore

# Follow live output (like tail -f)
sudo journalctl -u mystore -f

# Last 100 lines
sudo journalctl -u mystore -n 100

# Since a specific time
sudo journalctl -u mystore --since "1 hour ago"
sudo journalctl -u mystore --since "2024-01-15 10:00:00"
```

**Testing that restart works**

```bash
# Get your app's process ID
sudo systemctl status mystore | grep "Main PID"
# Main PID: 12345

# Kill the process — systemd should restart it within RestartSec seconds
sudo kill 12345

# Check status — it should show as restarted
sudo systemctl status mystore
```

**The deploy workflow with systemd**

After you update your code:

```bash
ssh deploy@your-server
cd /home/deploy/mystore
git pull origin main
source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart mystore
sudo systemctl status mystore
```

One restart command. systemd handles stopping the old process and starting the new one.

<!-- RESOURCES -->

- [systemd service documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html) -- type: reference, time: 15m
- [DigitalOcean - systemd Units and Services](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) -- type: tutorial, time: 20m
- [journalctl man page](https://man7.org/linux/man-pages/man1/journalctl.1.html) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
你运行应用：`python3 app.py`。它工作正常。你关闭 SSH 会话。进程消失了——它是 shell 的子进程，shell 结束时，应用也随之结束。你重启服务器。应用没有恢复运行。

进程管理器可以解决这个问题。它把应用作为后台服务运行，独立于任何 shell 会话。如果应用崩溃，进程管理器会重启它。服务器启动时，进程管理器会自动启动它。在 Linux 上，这个进程管理器就是 `systemd`。

<!-- ZH_DEEP_DIVE -->
**为什么不直接使用 `nohup` 或 `screen`？**

你可能听说过一些变通方法：

```bash
# nohup — 退出登录后保持进程运行，但不会自动重启
nohup python3 app.py &

# screen / tmux — 保持一个持久会话，但脆弱且需要手动操作
screen -S myapp
python3 app.py
# Ctrl+A, D 分离会话
```

这些方法适合测试，但不适合生产环境。如果你的应用崩溃了，它就会一直处于停止状态。如果服务器重启了，你必须 SSH 登录并手动再次启动它。不要将这些方法用于任何重要的场景。

**systemd 服务**

systemd 是现代 Linux 上的初始化系统——它是启动时运行的第一个进程，负责启动其他所有内容。任何长时间运行的进程都应该是一个 systemd 服务。你在一个 `.service` 文件中定义它：

```ini
# /etc/systemd/system/mystore.service

[Unit]
Description=My Store Application
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/mystore
EnvironmentFile=/home/deploy/mystore/.env
ExecStart=/home/deploy/mystore/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

下面拆解重要字段：

| 字段 | 作用 |
|-------|-------------|
| `After=network.target` | 在网络就绪之前不启动 |
| `User=deploy` | 以该用户身份运行（而非 root） |
| `WorkingDirectory=` | 进程的工作目录 |
| `EnvironmentFile=` | 从该文件加载环境变量 |
| `ExecStart=` | 运行应用的命令 |
| `Restart=always` | 如果进程因任何原因退出，则重启 |
| `RestartSec=5` | 重启尝试之间等待 5 秒 |
| `WantedBy=multi-user.target` | 在普通多用户模式下启动此服务 |

**对于 Node.js 应用：**

```ini
[Unit]
Description=My Node App
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/mynodeapp
EnvironmentFile=/home/deploy/mynodeapp/.env
ExecStart=/usr/bin/node /home/deploy/mynodeapp/server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**启用并启动服务**

```bash
# 将服务文件复制到正确位置（或直接在那里创建）
sudo nano /etc/systemd/system/mystore.service

# 告诉 systemd 重新加载其服务文件列表
sudo systemctl daemon-reload

# 启用：开机时自动启动
sudo systemctl enable mystore

# 启动：立即运行
sudo systemctl start mystore

# 检查状态
sudo systemctl status mystore
```

状态输出如下所示：

```
● mystore.service - My Store Application
     Loaded: loaded (/etc/systemd/system/mystore.service; enabled)
     Active: active (running) since Mon 2024-01-15 10:00:00 UTC; 5min ago
   Main PID: 12345 (gunicorn)
      Tasks: 5 (limit: 2340)
     Memory: 85.3M
        CPU: 1.234s
     CGroup: /system.slice/mystore.service
             ├─12345 /home/deploy/mystore/venv/bin/python3 -c ...
             └─12346 ...
```

**管理运行中的服务**

```bash
# 停止服务
sudo systemctl stop mystore

# 重启（先停止再启动）——更新代码后使用此命令
sudo systemctl restart mystore

# 重新加载（如果应用支持——发送 SIGHUP）
sudo systemctl reload mystore

# 检查它是否会在开机时启动
sudo systemctl is-enabled mystore

# 禁用自动启动
sudo systemctl disable mystore
```

**查看日志**

systemd 会捕获服务的所有 stdout 和 stderr：

```bash
# 服务的所有日志
sudo journalctl -u mystore

# 实时跟踪输出（类似 tail -f）
sudo journalctl -u mystore -f

# 最后 100 行
sudo journalctl -u mystore -n 100

# 从特定时间开始
sudo journalctl -u mystore --since "1 hour ago"
sudo journalctl -u mystore --since "2024-01-15 10:00:00"
```

**测试重启是否生效**

```bash
# 获取应用的进程 ID
sudo systemctl status mystore | grep "Main PID"
# Main PID: 12345

# 杀掉进程——systemd 应在 RestartSec 秒内重启它
sudo kill 12345

# 检查状态——应显示为已重启
sudo systemctl status mystore
```

**使用 systemd 的部署工作流**

更新代码后：

```bash
ssh deploy@your-server
cd /home/deploy/mystore
git pull origin main
source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart mystore
sudo systemctl status mystore
```

一条重启命令。systemd 会处理停止旧进程并启动新进程。

<!-- ZH_RESOURCES -->
- [systemd service 文档](https://www.freedesktop.org/software/systemd/man/systemd.service.html) -- 类型：参考，时间：15m
- [DigitalOcean - systemd 单元与服务](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) -- 类型：教程，时间：20m
- [journalctl 手册页](https://man7.org/linux/man-pages/man1/journalctl.1.html) -- 类型：参考，时间：10m

<!-- ZH_UI -->
1. 为 Python 或 Node.js 应用编写 systemd 服务文件
2. 启用服务开机自启，并验证崩溃后能自动重启
3. 使用 journalctl 查看服务的实时和历史日志
4. 我的应用已作为受管服务运行。谁来处理传入的 HTTP 流量？
5. 我的应用现在作为 systemd 服务运行——它能承受断连和重启。但我仍在 5000 端口上访问它。我需要它像普通网站一样在 80 端口工作，而不是必须手动输入自定义端口。
6. 我的应用正作为 systemd 服务运行。如何查看它的输出和错误？
7. 我开始遇到错误——请求失败，也许服务在崩溃并重启——但我完全不知道内部到底发生了什么。没有终端可看时，所有输出都去了哪里？
