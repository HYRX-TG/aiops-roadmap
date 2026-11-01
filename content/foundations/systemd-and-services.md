---
id: systemd-and-services
title: systemd & Services
zone: foundations
edges:
  to:
    - id: log-files
      question: Services are running. How do I see what they are doing?
      detail: >-
        My service is running — great. But when something goes wrong I have no
        idea where to look. It crashed and restarted but I don't know why. There
        must be output from it somewhere, some record of what happened. How do I
        find that and actually make sense of it?
    - id: cron-and-scheduling
      question: My service runs continuously — but what if I need to run something on a schedule?
      detail: >-
        I know how to keep a service running. But some things I need to happen
        at a specific time — clean up old files every night, run a backup every
        hour, kick off a report every Monday morning. How do I tell the system
        to run something automatically on a schedule without me having to
        remember to do it?
difficulty: 1
tags:
  - systemd
  - systemctl
  - journalctl
  - services
  - init
  - units
  - daemons
category: concept
milestones:
  - 'Use systemctl to start, stop, restart, and check the status of a service'
  - Read service logs with journalctl
  - Explain what a systemd unit file is and what its key sections do
title_zh: "systemd 与服务"

---


When a Linux server boots, something needs to start all the services that make it useful — the SSH daemon so you can log in, the web server to handle requests, the database to store data, the monitoring agent to report health. That something is the **init system**, and on virtually every modern Linux distribution, it is **systemd**. It is PID 1 — the first process that starts, the parent of all other processes, and the orchestrator that keeps your services running. As an SRE, `systemctl` and `journalctl` will be among your most-used commands.

<!-- DEEP_DIVE -->

**What systemd does.** At its core, systemd manages **units** — and a unit can be a service, a timer, a mount point, a socket, or several other things. The most common unit type is a **service**, which represents a daemon (a long-running background process). When you run `systemctl start nginx`, systemd reads Nginx's unit file, starts the process, and begins monitoring it. If Nginx crashes, systemd can automatically restart it (if configured to do so). When the system shuts down, systemd sends SIGTERM to all services, waits for them to exit gracefully, and then sends SIGKILL to anything still running — this is the signal knowledge from the previous node in action.

**systemctl — the command you will use daily.**

- `systemctl start nginx` — start a service
- `systemctl stop nginx` — stop a service (sends SIGTERM, then SIGKILL after a timeout)
- `systemctl restart nginx` — stop then start
- `systemctl reload nginx` — send SIGHUP to reload config without restarting (not all services support this)
- `systemctl status nginx` — show whether the service is running, its PID, recent log lines, and how long it has been up
- `systemctl enable nginx` — start this service automatically at boot
- `systemctl disable nginx` — do not start at boot
- `systemctl list-units --type=service` — list all loaded services and their states

The `status` command is especially valuable during incidents. It shows you at a glance whether the service is running, when it last started, and the most recent log output. Often that is enough to diagnose the problem without digging further.

**Unit files.** Every service has a unit file, typically at `/etc/systemd/system/` (for custom services) or `/lib/systemd/system/` (for distribution-provided ones). A basic service unit file looks like this:

```ini
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=myapp
ExecStart=/usr/bin/myapp --config /etc/myapp/config.yaml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The key sections: `[Unit]` describes the service and its dependencies (`After=network.target` means "start this after networking is up"). `[Service]` defines how to run it — what command to execute, which user to run as, and what to do if it crashes (`Restart=on-failure` means systemd will automatically restart it if it exits with a non-zero status). `[Install]` controls what happens when you `enable` the service. As an SRE, you will read and write unit files regularly — every custom application you deploy needs one.

**journalctl — reading logs through systemd.** systemd captures the stdout and stderr of every service it manages and stores it in a structured journal. `journalctl -u nginx` shows all logs for Nginx. `journalctl -u nginx --since "1 hour ago"` filters by time. `journalctl -u nginx -f` follows the log in real time (like `tail -f`). `journalctl -p err` shows only error-level messages across all services. The journal is indexed and searchable, which makes it significantly more powerful than manually grepping through log files — though traditional log files in `/var/log/` still exist alongside it.

**Dependencies and ordering.** One of systemd's strengths is managing the order in which services start. Your application might need the database to be running first, and the database might need the filesystem mounted. Unit files express these dependencies with `After=`, `Requires=`, and `Wants=` directives. When something fails to start, `systemctl list-dependencies myservice` shows you the full dependency tree, which often reveals that a dependency failed first.

**Timers — the modern cron.** systemd also provides timers, which are a replacement for cron jobs. A timer unit triggers a service unit on a schedule. The advantage over cron is that timer execution is logged in the journal, missed runs can be handled, and you get all of systemd's service management features (resource limits, dependency ordering, restart policies). You will encounter both cron and systemd timers in production.

<!-- RESOURCES -->

- [systemd for Beginners - DigitalOcean](https://www.digitalocean.com/community/tutorials/systemd-essentials-working-with-services-units-and-the-journal) -- type: tutorial, time: 30m
- [Understanding systemd Units and Unit Files](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) -- type: tutorial, time: 30m
- [journalctl Guide - Linuxize](https://linuxize.com/post/using-journalctl/) -- type: tutorial, time: 20m
- [Arch Wiki - systemd (comprehensive reference)](https://wiki.archlinux.org/title/Systemd) -- type: reference, time: varies
- [systemd by Example](https://systemd-by-example.com/) -- type: tutorial, time: 1h

<!-- ZH_SUMMARY -->
当 Linux 服务器启动时，需要有东西来启动所有让它变得有用的服务——让你能够登录的 SSH 守护进程、处理请求的 Web 服务器、存储数据的数据库、报告健康状况的监控代理。这个东西就是 **init 系统**，而在几乎所有现代 Linux 发行版上，它就是 **systemd**。它是 PID 1——第一个启动的进程、所有其他进程的父进程，以及让服务持续运行的编排者。作为 SRE，`systemctl` 和 `journalctl` 将是你最常用的命令之一。

<!-- ZH_DEEP_DIVE -->
**systemd 的作用。** 其核心是管理 **unit**——一个 unit 可以是服务、定时器、挂载点、套接字，或其他几种类型。最常见的 unit 类型是 **service**，它代表一个守护进程（长期运行的后台进程）。当你运行 `systemctl start nginx` 时，systemd 会读取 Nginx 的 unit 文件，启动进程并开始监控它。如果 Nginx 崩溃，systemd 可以自动重启它（如果配置了这样做）。当系统关闭时，systemd 向所有服务发送 SIGTERM，等待它们优雅退出，然后向仍在运行的任何进程发送 SIGKILL——这就是上一个节点中信号知识的实际应用。

**systemctl——你每天都会用到的命令。**

- `systemctl start nginx`——启动一个服务
- `systemctl stop nginx`——停止一个服务（发送 SIGTERM，超时后发送 SIGKILL）
- `systemctl restart nginx`——停止后再启动
- `systemctl reload nginx`——发送 SIGHUP 以重新加载配置而不重启（并非所有服务都支持）
- `systemctl status nginx`——显示服务是否正在运行、其 PID、最近的日志行以及已运行时长
- `systemctl enable nginx`——在开机时自动启动此服务
- `systemctl disable nginx`——不在开机时启动
- `systemctl list-units --type=service`——列出所有已加载的服务及其状态

`status` 命令在事故处理期间尤其有价值。它让你一眼就能看出服务是否正在运行、上次启动的时间以及最近的日志输出。通常这足以诊断问题，而无需进一步排查。

**Unit 文件。** 每个服务都有一个 unit 文件，通常位于 `/etc/systemd/system/`（用于自定义服务）或 `/lib/systemd/system/`（用于发行版提供的服务）。一个基本的服务 unit 文件如下所示：

```ini
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=myapp
ExecStart=/usr/bin/myapp --config /etc/myapp/config.yaml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

关键部分：`[Unit]` 描述服务及其依赖关系（`After=network.target` 表示“在网络启动后启动此服务”）。`[Service]` 定义如何运行它——执行什么命令、以哪个用户运行，以及崩溃时该怎么做（`Restart=on-failure` 表示如果它以非零状态退出，systemd 将自动重启它）。`[Install]` 控制当你 `enable` 服务时会发生什么。作为 SRE，你会经常读写 unit 文件——你部署的每个自定义应用都需要一个。

**journalctl——通过 systemd 读取日志。** systemd 捕获它管理的每个服务的 stdout 和 stderr，并将其存储在结构化 journal 中。`journalctl -u nginx` 显示 Nginx 的所有日志。`journalctl -u nginx --since "1 hour ago"` 按时间过滤。`journalctl -u nginx -f` 实时跟踪日志（类似 `tail -f`）。`journalctl -p err` 仅显示所有服务中错误级别的消息。journal 是索引化且可搜索的，这使其比手动 grep 日志文件强大得多——不过 `/var/log/` 中的传统日志文件仍然与它并存。

**依赖关系与顺序。** systemd 的优势之一是管理服务的启动顺序。你的应用可能需要先运行数据库，而数据库可能需要先挂载文件系统。Unit 文件通过 `After=`、`Requires=` 和 `Wants=` 指令来表达这些依赖关系。当某个服务启动失败时，`systemctl list-dependencies myservice` 会显示完整的依赖树，这通常能揭示是某个依赖项先失败了。

**定时器——现代的 cron。** systemd 还提供定时器，作为 cron 作业的替代品。定时器 unit 按计划触发服务 unit。相比 cron 的优势在于：定时器的执行会记录在 journal 中，可以处理错过的运行，并且你能获得 systemd 的所有服务管理功能（资源限制、依赖排序、重启策略）。在生产环境中，你会同时遇到 cron 和 systemd 定时器。

<!-- ZH_RESOURCES -->
- [systemd 入门 - DigitalOcean](https://www.digitalocean.com/community/tutorials/systemd-essentials-working-with-services-units-and-the-journal) -- 类型: 教程, 时长: 30 分钟
- [理解 systemd 单元与单元文件](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) -- 类型: 教程, 时长: 30 分钟
- [journalctl 指南 - Linuxize](https://linuxize.com/post/using-journalctl/) -- 类型: 教程, 时长: 20 分钟
- [Arch Wiki - systemd（全面参考）](https://wiki.archlinux.org/title/Systemd) -- 类型: 参考, 时长: 不定
- [systemd 实例讲解](https://systemd-by-example.com/) -- 类型: 教程, 时长: 1 小时

<!-- ZH_UI -->
1. 使用 systemctl 启动、停止、重启服务并查看服务状态
2. 使用 journalctl 读取服务日志
3. 解释什么是 systemd unit 文件及其关键段落的作用
4. 服务正在运行。我如何查看它们在做什么？
5. 我的服务正在运行——很好。但出问题时我完全不知道去哪里查。它崩溃并重启了，但我不知道原因。它的输出一定记录在某处，有事情经过的某种记录。我如何找到它并真正理解它？
6. 我的服务持续运行——但如果我需要按计划运行某些任务呢？
7. 我知道如何让服务保持运行。但有些事情需要在特定时间发生——每晚清理旧文件、每小时运行备份、每周一早上生成报告。如何让系统按计划自动运行某些任务，而不用我自己记着去做？
