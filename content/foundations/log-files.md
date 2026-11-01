---
id: log-files
title: Log Files & Logging
zone: foundations
edges:
  to:
    - id: grep-and-searching
      question: There are thousands of lines in these logs. How do I find what I need?
      detail: >-
        I found the log file but it's enormous — tens of thousands of lines and
        the error I care about is somewhere in there. Scrolling is hopeless.
        There must be a way to search for a specific message, watch for new
        lines as they come in, or filter down to just the errors. How do I
        actually work with this much output?
difficulty: 1
tags:
  - logs
  - syslog
  - journalctl
  - var-log
  - log-rotation
  - debugging
category: concept
milestones:
  - Find and read relevant logs in /var/log for a running service
  - 'Use journalctl to filter logs by service, time, and severity'
  - Explain what log rotation is and why it matters
title_zh: "日志文件与日志记录"

---


When a server is misbehaving, the first thing you do as an SRE is check the logs. Logs are the running diary of everything happening on a system — every request handled, every error thrown, every service started or stopped. They are almost always the fastest path from "something is broken" to "I know what is broken." Knowing where logs live, how to read them efficiently, and how to search through gigabytes of log data is arguably the single most practical skill in this entire roadmap.

<!-- DEEP_DIVE -->

**Where logs live.** On Linux, logs are primarily in two places:

- **`/var/log/`** — the traditional log directory. Inside you will find:
  - `/var/log/syslog` or `/var/log/messages` — the main system log, containing messages from the kernel, system services, and anything that uses the syslog protocol.
  - `/var/log/auth.log` — authentication events: SSH logins (successful and failed), sudo usage, user creation. Check this first if you suspect unauthorized access.
  - `/var/log/kern.log` — kernel messages, including hardware errors and OOM kills.
  - `/var/log/nginx/`, `/var/log/apache2/`, `/var/log/mysql/` — application-specific logs, typically in their own subdirectories.
  - `/var/log/dmesg` — boot-time kernel messages, useful for diagnosing hardware and driver issues.

- **The systemd journal** — a structured, binary log managed by `journald`. Every service managed by systemd has its output captured here. Access it with `journalctl`.

**journalctl — your log Swiss Army knife.**

- `journalctl -u nginx` — all logs for the Nginx service
- `journalctl -u nginx --since "2 hours ago"` — filtered by time
- `journalctl -u nginx --since "2024-01-15 10:00" --until "2024-01-15 11:00"` — specific time range
- `journalctl -u nginx -f` — follow logs in real time (like `tail -f`)
- `journalctl -p err` — only error-level messages across all services
- `journalctl -b` — all logs from the current boot
- `journalctl -b -1` — logs from the previous boot (essential for diagnosing why a machine rebooted)
- `journalctl --disk-usage` — how much space the journal is using

The journal is structured data, not just text. Each log entry has metadata: timestamp, service name, PID, priority level. This makes it far more searchable than flat text files.

**Reading logs during an incident.** When you get paged at 3 AM because a service is down, here is a practical workflow:

1. `systemctl status myservice` — is it running? When did it last start? First few log lines right there.
2. `journalctl -u myservice --since "30 min ago"` — what happened leading up to the failure?
3. Look for patterns: is it one error repeated, or a cascade? Is there an OOM kill in `journalctl -p err`?
4. Check related services: `journalctl -u postgresql --since "30 min ago"` — maybe the database went down first.
5. Check system-level events: `dmesg | tail -50` — hardware errors? disk full? OOM killer?

**Searching logs with command-line tools.** This is where pipes and redirection pay off:

- `grep "ERROR" /var/log/myapp/app.log` — find all errors
- `grep -c "500" /var/log/nginx/access.log` — count 500 errors
- `tail -f /var/log/nginx/access.log | grep --line-buffered "POST /api"` — watch POST requests in real time
- `zgrep "timeout" /var/log/myapp/app.log.2.gz` — search through compressed rotated logs

**Log rotation.** Logs grow. A busy web server can produce gigabytes of log data per day. Without management, logs will fill up your disk and crash the server. **logrotate** is the standard tool for this — it automatically rotates logs (renames `app.log` to `app.log.1`, compresses old files, and deletes files older than a configured age). Most services configure logrotate automatically when you install them. The config lives in `/etc/logrotate.conf` and `/etc/logrotate.d/`. A full disk caused by unmanaged logs is one of the most common preventable outages — always make sure log rotation is configured.

**Log levels.** Most logging systems use standard severity levels: DEBUG, INFO, WARNING, ERROR, CRITICAL (or similar names). In production, you typically run at INFO or WARNING level — DEBUG produces too much output. But when diagnosing a tricky issue, temporarily increasing the log level to DEBUG can reveal exactly what is happening. Understanding how to change log levels for the services you manage (usually a config file change and a SIGHUP or restart) is a practical skill you will use regularly.

<!-- RESOURCES -->

- [Linux Logging Basics - Loggly](https://www.loggly.com/ultimate-guide/linux-logging-basics/) -- type: tutorial, time: 30m
- [journalctl Cheat Sheet - Red Hat](https://www.redhat.com/sysadmin/journalctl-cheat-sheet) -- type: reference, time: 10m
- [Understanding /var/log - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-view-and-configure-linux-logs-on-ubuntu-and-centos) -- type: tutorial, time: 25m
- [logrotate Guide - Linuxize](https://linuxize.com/post/logrotate/) -- type: tutorial, time: 20m
- [Logging Best Practices for SREs - Google SRE Book](https://sre.google/sre-book/monitoring-distributed-systems/) -- type: book, time: 30m

<!-- ZH_SUMMARY -->
当服务器出现异常时，作为 SRE，你首先要做的就是检查日志。日志是系统上发生的一切的实时记录——每一个被处理的请求、每一个抛出的错误、每一个启动或停止的服务。它们几乎总是从“出问题了”到“我知道哪里出问题了”的最快路径。了解日志存放在哪里、如何高效地读取它们，以及如何在数 GB 的日志数据中进行搜索，可以说是整个路线图中最为实用的一项技能。

<!-- ZH_DEEP_DIVE -->
**日志存放位置。** 在 Linux 上，日志主要存放在两个地方：

- **`/var/log/`** —— 传统的日志目录。里面你会找到：
  - `/var/log/syslog` 或 `/var/log/messages` —— 主系统日志，包含来自内核、系统服务以及任何使用 syslog 协议的程序的消息。
  - `/var/log/auth.log` —— 认证事件：SSH 登录（成功和失败）、sudo 使用、用户创建。如果你怀疑存在未授权访问，先检查这个文件。
  - `/var/log/kern.log` —— 内核消息，包括硬件错误和 OOM kill。
  - `/var/log/nginx/`、`/var/log/apache2/`、`/var/log/mysql/` —— 应用特定的日志，通常位于各自的子目录中。
  - `/var/log/dmesg` —— 启动时的内核消息，用于诊断硬件和驱动问题。

- **systemd journal** —— 由 `journald` 管理的结构化二进制日志。每个由 systemd 管理的服务，其输出都会被捕获到这里。使用 `journalctl` 访问它。

**journalctl —— 你的日志瑞士军刀。**

- `journalctl -u nginx` —— Nginx 服务的所有日志
- `journalctl -u nginx --since "2 hours ago"` —— 按时间过滤
- `journalctl -u nginx --since "2024-01-15 10:00" --until "2024-01-15 11:00"` —— 指定时间范围
- `journalctl -u nginx -f` —— 实时跟踪日志（类似 `tail -f`）
- `journalctl -p err` —— 仅显示所有服务中 error 级别的消息
- `journalctl -b` —— 本次启动的所有日志
- `journalctl -b -1` —— 上一次启动的日志（诊断机器为何重启时必不可少）
- `journalctl --disk-usage` —— journal 占用了多少空间

journal 是结构化数据，而不仅仅是文本。每条日志条目都有元数据：时间戳、服务名、PID、优先级。这使得它比纯文本文件更易于搜索。

**事故期间阅读日志。** 当你凌晨 3 点因为某个服务宕机而被呼叫时，以下是一个实用的工作流程：

1. `systemctl status myservice` —— 它正在运行吗？上次启动是什么时候？前几行日志就在这里。
2. `journalctl -u myservice --since "30 min ago"` —— 故障发生前发生了什么？
3. 寻找模式：是同一个错误重复出现，还是级联故障？`journalctl -p err` 中是否有 OOM kill？
4. 检查相关服务：`journalctl -u postgresql --since "30 min ago"` —— 也许数据库先挂了。
5. 检查系统级事件：`dmesg | tail -50` —— 硬件错误？磁盘满？OOM killer？

**使用命令行工具搜索日志。** 这正是管道和重定向发挥作用的地方：

- `grep "ERROR" /var/log/myapp/app.log` —— 查找所有错误
- `grep -c "500" /var/log/nginx/access.log` —— 统计 500 错误数量
- `tail -f /var/log/nginx/access.log | grep --line-buffered "POST /api"` —— 实时监视 POST 请求
- `zgrep "timeout" /var/log/myapp/app.log.2.gz` —— 搜索压缩的轮转日志

**日志轮转。** 日志会增长。一台繁忙的 Web 服务器每天可能产生数 GB 的日志数据。如果不加管理，日志会填满磁盘并导致服务器崩溃。**logrotate** 是用于此目的的标准工具——它会自动轮转日志（将 `app.log` 重命名为 `app.log.1`，压缩旧文件，并删除超过配置期限的文件）。大多数服务在安装时会自动配置 logrotate。配置文件位于 `/etc/logrotate.conf` 和 `/etc/logrotate.d/`。由未管理的日志导致的磁盘满是最常见的可预防故障之一——始终确保配置了日志轮转。

**日志级别。** 大多数日志系统使用标准严重级别：DEBUG、INFO、WARNING、ERROR、CRITICAL（或类似名称）。在生产环境中，通常运行在 INFO 或 WARNING 级别——DEBUG 会产生过多输出。但在诊断棘手问题时，临时将日志级别提高到 DEBUG 可以准确揭示正在发生什么。了解如何为你管理的服务更改日志级别（通常是修改配置文件并发送 SIGHUP 或重启）是一项你会经常用到的实用技能。

<!-- ZH_RESOURCES -->
- [Linux 日志记录基础 - Loggly](https://www.loggly.com/ultimate-guide/linux-logging-basics/) -- 类型: 教程, 时长: 30m
- [journalctl 速查表 - Red Hat](https://www.redhat.com/sysadmin/journalctl-cheat-sheet) -- 类型: 参考, 时长: 10m
- [理解 /var/log - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-view-and-configure-linux-logs-on-ubuntu-and-centos) -- 类型: 教程, 时长: 25m
- [logrotate 指南 - Linuxize](https://linuxize.com/post/logrotate/) -- 类型: 教程, 时长: 20m
- [SRE 日志记录最佳实践 - Google SRE Book](https://sre.google/sre-book/monitoring-distributed-systems/) -- 类型: 书籍, 时长: 30m

<!-- ZH_UI -->
1. 在 /var/log 中查找并阅读运行中服务的相关日志
2. 使用 journalctl 按服务、时间和严重级别过滤日志
3. 解释什么是日志轮转以及它为何重要
4. 这些日志有几千行。我怎样才能找到我需要的内容？
5. 我找到了日志文件，但它非常大——有数万行，而我关心的错误就在其中某处。滚动翻找毫无希望。一定有办法搜索特定消息、在新增行出现时实时查看，或者过滤到只剩错误。面对这么多输出，我究竟该如何操作？
