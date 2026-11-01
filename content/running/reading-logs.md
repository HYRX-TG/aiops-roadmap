---
id: reading-logs
title: Reading Logs
zone: running
edges:
  to:
    - id: troubleshooting-basics
      question: I can read logs. How do I use them to systematically debug problems?
      detail: >-
        I can find and read logs now. But when something breaks I still end up
        randomly restarting things and hoping it helps. I need a more systematic
        approach — a way to narrow down which part of the stack is actually
        broken instead of just guessing.
difficulty: 1
tags:
  - logs
  - journalctl
  - nginx
  - tail
  - grep
  - debugging
  - stdout
  - stderr
category: practice
milestones:
  - Use journalctl to view live and filtered logs for a systemd service
  - Find and read the Nginx access log and error log
  - Filter logs by time range and search for specific error messages
title_zh: "读取日志"

---


Your app is running, Nginx is serving traffic, and then something breaks. A page returns 500. An image is not loading. The app is crashing every few minutes. The first thing you do is look at the logs.

Logs are the record of what your system did. Every request Nginx handled. Every error your app threw. Every time systemd restarted a service. Learning to find and read logs is the most important debugging skill you have.

<!-- DEEP_DIVE -->

**Two log systems to know**

On a modern Ubuntu server, logs come from two places:

1. **journald** — systemd's log collector. Captures stdout/stderr from every systemd service. Accessed via `journalctl`.
2. **Log files on disk** — traditional log files in `/var/log/`. Nginx, syslog, auth logs, and others write here.

**journalctl — your app's logs**

If your app runs as a systemd service, all its output goes to journald:

```bash
# All logs for your service
sudo journalctl -u mystore

# Follow live output — like tail -f, shows new entries as they arrive
sudo journalctl -u mystore -f

# Last N lines
sudo journalctl -u mystore -n 50

# Logs since a time
sudo journalctl -u mystore --since "1 hour ago"
sudo journalctl -u mystore --since "2024-01-15 10:00:00"

# Only errors and above (filters out INFO/DEBUG)
sudo journalctl -u mystore -p err

# Logs since the last boot (useful after a server restart)
sudo journalctl -u mystore -b

# All services, not just yours — useful when debugging boot problems
sudo journalctl -f
```

**Nginx logs**

Nginx writes two log files:

```bash
# Access log — one line per request
sudo tail -f /var/log/nginx/access.log

# Error log — problems Nginx encountered
sudo tail -f /var/log/nginx/error.log

# Both at once
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

The access log format looks like:

```
143.198.100.50 - - [15/Jan/2024:10:00:01 +0000] "GET /products HTTP/1.1" 200 4523 "https://mystore.com/" "Mozilla/5.0 ..."
                                                  [method] [path]          [status] [bytes sent]
```

Key things to look for:
- **Status 4xx** — client errors (404 = not found, 403 = forbidden, 429 = rate limited)
- **Status 5xx** — server errors (500 = your app threw an exception, 502 = Nginx cannot reach your app, 504 = your app is too slow)
- **502 Bad Gateway** — means Nginx is running but your app is not, or is not listening on the expected port
- **Repeated requests from one IP** — could be a scanner or a stuck client

**Filtering logs with grep**

```bash
# Find all 500 errors in the Nginx access log
sudo grep " 500 " /var/log/nginx/access.log

# Find all errors from a specific IP
sudo grep "1.2.3.4" /var/log/nginx/access.log

# Find errors in your app's logs
sudo journalctl -u mystore | grep -i "error\|exception\|traceback"

# Count how many 502 errors occurred
sudo grep -c " 502 " /var/log/nginx/access.log
```

**Auth logs — who is trying to get in**

```bash
# See SSH login attempts (successful and failed)
sudo tail -f /var/log/auth.log

# Count failed login attempts
sudo grep "Failed password" /var/log/auth.log | wc -l
# If this number is in the thousands, someone is actively brute-forcing you
# Make sure PasswordAuthentication is set to no in sshd_config
```

**Syslog — system-level events**

```bash
# General system log
sudo tail -f /var/log/syslog

# Kernel messages — hardware issues, OOM kills, etc.
sudo dmesg | tail -20
```

**Following multiple logs at once**

When debugging a request that goes through multiple layers (Nginx → your app → database), watching all logs simultaneously helps:

```bash
# Open multiple terminals, or use tmux
# Terminal 1: Nginx access log
sudo tail -f /var/log/nginx/access.log

# Terminal 2: Your app's logs
sudo journalctl -u mystore -f

# Terminal 3: Run your test request
curl http://localhost/some-endpoint
```

**Reading Python tracebacks in logs**

When your Python app crashes, you get a traceback in the logs. Read it from the bottom up — the last line tells you what went wrong, the lines above show how you got there:

```
Traceback (most recent call last):
  File "/home/deploy/mystore/app.py", line 42, in get_products
    results = db.execute(query)
  File "/home/deploy/mystore/db.py", line 15, in execute
    return self.conn.execute(sql)
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

Bottom line: `could not connect to server` — the database is down or unreachable. The lines above show the call path.

<!-- RESOURCES -->

- [journalctl man page](https://man7.org/linux/man-pages/man1/journalctl.1.html) -- type: reference, time: 10m
- [Nginx log format documentation](https://nginx.org/en/docs/http/ngx_http_log_module.html) -- type: reference, time: 10m
- [DigitalOcean - Understanding Nginx Log Files](https://www.digitalocean.com/community/tutorials/how-to-configure-logging-and-log-rotation-in-nginx-on-an-ubuntu-vps) -- type: tutorial, time: 15m

<!-- ZH_SUMMARY -->
你的应用正在运行，Nginx 正在处理流量，然后出了问题。某个页面返回 500。某张图片加载不出来。应用每隔几分钟就崩溃一次。你做的第一件事就是查看日志。

日志是系统行为的记录。Nginx 处理的每一个请求。应用抛出的每一个错误。systemd 每次重启服务的记录。学会查找和阅读日志，是你最重要的调试技能。

<!-- ZH_DEEP_DIVE -->
**需要了解的两套日志系统**

在现代 Ubuntu 服务器上，日志来自两个地方：

1. **journald** — systemd 的日志收集器。捕获每个 systemd 服务的 stdout/stderr。通过 `journalctl` 访问。
2. **磁盘上的日志文件** — `/var/log/` 中的传统日志文件。Nginx、syslog、认证日志等写入此处。

**journalctl — 你的应用日志**

如果你的应用作为 systemd 服务运行，它的所有输出都会进入 journald：

```bash
# All logs for your service
sudo journalctl -u mystore

# Follow live output — like tail -f, shows new entries as they arrive
sudo journalctl -u mystore -f

# Last N lines
sudo journalctl -u mystore -n 50

# Logs since a time
sudo journalctl -u mystore --since "1 hour ago"
sudo journalctl -u mystore --since "2024-01-15 10:00:00"

# Only errors and above (filters out INFO/DEBUG)
sudo journalctl -u mystore -p err

# Logs since the last boot (useful after a server restart)
sudo journalctl -u mystore -b

# All services, not just yours — useful when debugging boot problems
sudo journalctl -f
```

**Nginx 日志**

Nginx 写入两个日志文件：

```bash
# Access log — one line per request
sudo tail -f /var/log/nginx/access.log

# Error log — problems Nginx encountered
sudo tail -f /var/log/nginx/error.log

# Both at once
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

访问日志格式如下：

```
143.198.100.50 - - [15/Jan/2024:10:00:01 +0000] "GET /products HTTP/1.1" 200 4523 "https://mystore.com/" "Mozilla/5.0 ..."
                                                  [method] [path]          [status] [bytes sent]
```

需要重点关注的项：
- **状态码 4xx** — 客户端错误（404 = 未找到，403 = 禁止访问，429 = 被限流）
- **状态码 5xx** — 服务器错误（500 = 你的应用抛出异常，502 = Nginx 无法访问你的应用，504 = 你的应用响应太慢）
- **502 Bad Gateway** — 表示 Nginx 正在运行，但你的应用没有运行，或者没有监听预期的端口
- **来自同一 IP 的重复请求** — 可能是扫描器或卡住的客户端

**使用 grep 过滤日志**

```bash
# Find all 500 errors in the Nginx access log
sudo grep " 500 " /var/log/nginx/access.log

# Find all errors from a specific IP
sudo grep "1.2.3.4" /var/log/nginx/access.log

# Find errors in your app's logs
sudo journalctl -u mystore | grep -i "error\|exception\|traceback"

# Count how many 502 errors occurred
sudo grep -c " 502 " /var/log/nginx/access.log
```

**认证日志 — 谁在试图进入**

```bash
# See SSH login attempts (successful and failed)
sudo tail -f /var/log/auth.log

# Count failed login attempts
sudo grep "Failed password" /var/log/auth.log | wc -l
# If this number is in the thousands, someone is actively brute-forcing you
# Make sure PasswordAuthentication is set to no in sshd_config
```

**Syslog — 系统级事件**

```bash
# General system log
sudo tail -f /var/log/syslog

# Kernel messages — hardware issues, OOM kills, etc.
sudo dmesg | tail -20
```

**同时跟踪多个日志**

当调试一个经过多个层次的请求（Nginx → 你的应用 → 数据库）时，同时查看所有日志会很有帮助：

```bash
# Open multiple terminals, or use tmux
# Terminal 1: Nginx access log
sudo tail -f /var/log/nginx/access.log

# Terminal 2: Your app's logs
sudo journalctl -u mystore -f

# Terminal 3: Run your test request
curl http://localhost/some-endpoint
```

**阅读日志中的 Python traceback**

当你的 Python 应用崩溃时，日志中会出现 traceback。从下往上读 — 最后一行告诉你出了什么问题，上面的行展示了你如何到达那里：

```
Traceback (most recent call last):
  File "/home/deploy/mystore/app.py", line 42, in get_products
    results = db.execute(query)
  File "/home/deploy/mystore/db.py", line 15, in execute
    return self.conn.execute(sql)
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

最后一行：`could not connect to server` — 数据库已宕机或无法访问。上面的行展示了调用路径。

<!-- ZH_RESOURCES -->
- [journalctl man page](https://man7.org/linux/man-pages/man1/journalctl.1.html) -- 类型：参考，时间：10m
- [Nginx 日志格式文档](https://nginx.org/en/docs/http/ngx_http_log_module.html) -- 类型：参考，时间：10m
- [DigitalOcean - 理解 Nginx 日志文件](https://www.digitalocean.com/community/tutorials/how-to-configure-logging-and-log-rotation-in-nginx-on-an-ubuntu-vps) -- 类型：教程，时间：15m

<!-- ZH_UI -->
1. 使用 journalctl 查看 systemd 服务的实时日志和过滤日志
2. 找到并阅读 Nginx 访问日志和错误日志
3. 按时间范围过滤日志并搜索特定错误信息
4. 我会读日志了。如何利用日志系统地排查问题？
5. 我现在能找到并阅读日志了。但出问题时我还是会随意重启服务、指望它能好。我需要更系统的方法——能缩小范围、定位技术栈中真正出问题的部分，而不是靠猜。
