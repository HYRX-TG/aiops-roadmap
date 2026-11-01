---
id: cron-and-scheduling
title: Cron & Task Scheduling
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: My cron jobs are getting complicated. When should I write a real script instead?
      detail: >-
        I started with simple one-liners in cron, but now I'm chaining five
        commands together, handling errors, and it's getting hard to read. At
        what point does this stop being a cron job and start being something
        that deserves a proper script? And what does that even look like?
difficulty: 1
tags:
  - cron
  - crontab
  - scheduling
  - automation
  - systemd-timers
category: practice
milestones:
  - Write a crontab entry that runs a script on a schedule
  - Explain the five cron time fields and read any cron expression
  - Capture cron job output and debug a job that isn't running
title_zh: "Cron 与任务调度"
---


Some tasks need to happen on a schedule — clean up old files every night, run a database backup every hour, send a health check ping every five minutes. You do not want to do these by hand. **cron** is the standard Linux tool for scheduling recurring tasks, and it has been around since the 1970s. You will encounter it everywhere: on servers you manage, in applications you inherit, in containers you debug. Understanding how it works and where it fails is a practical necessity.

<!-- DEEP_DIVE -->

## How cron works

`crond` is a daemon that runs in the background and wakes up every minute to check if any scheduled jobs need to run. Jobs are defined in **crontab** files — one per user, managed with the `crontab` command.

```bash
crontab -e    # open your crontab for editing
crontab -l    # list your current crontab
crontab -r    # remove your crontab (careful — no confirmation)
```

Each line in a crontab defines one job. The format is:

```
minute  hour  day-of-month  month  day-of-week  command
```

Five time fields, then the command. The fields:

| Field | Range | Special |
|---|---|---|
| minute | 0–59 | |
| hour | 0–23 | |
| day of month | 1–31 | |
| month | 1–12 | |
| day of week | 0–7 | 0 and 7 both mean Sunday |

`*` in a field means "every". Special values:
- `*/5` — every 5 (e.g., every 5 minutes)
- `1,15` — at 1 and 15
- `1-5` — 1 through 5

## Reading cron expressions

```
# Run at 2:30 AM every day
30 2 * * * /opt/scripts/backup.sh

# Run every 5 minutes
*/5 * * * * /opt/scripts/healthcheck.sh

# Run at midnight on the 1st of every month
0 0 1 * * /opt/scripts/monthly-report.sh

# Run at 9 AM Monday through Friday
0 9 * * 1-5 /opt/scripts/morning-checks.sh

# Run every hour
0 * * * * /opt/scripts/cleanup.sh
```

Use [crontab.guru](https://crontab.guru/) to check your expressions interactively — paste in any cron schedule and it tells you in plain English when it will run.

## Special strings

These shortcuts replace the five time fields:

- `@daily` — run once a day at midnight (same as `0 0 * * *`)
- `@hourly` — run once an hour at the start of the hour
- `@weekly` — once a week, Sunday at midnight
- `@monthly` — once a month, the 1st at midnight
- `@reboot` — run once when the system boots. Useful for one-time setup after a restart.

## System-wide cron

Beyond per-user crontabs, there are system-wide locations:

- `/etc/crontab` — the system crontab. Has an extra field for the username to run as.
- `/etc/cron.d/` — directory for cron files, typically dropped there by packages. Same format as `/etc/crontab`.
- `/etc/cron.daily/`, `/etc/cron.hourly/`, `/etc/cron.weekly/`, `/etc/cron.monthly/` — just drop a script in the right directory and it runs on that schedule. No cron syntax needed.

When you install a package that needs scheduled maintenance (like certbot for TLS certificate renewal), it typically puts a file in `/etc/cron.d/` or `/etc/cron.daily/`. This is worth knowing when you are trying to understand where a job came from.

## The most common cron problems

**The job runs manually but not from cron.** Almost always a `PATH` issue. Cron runs with a minimal environment — it does not source your shell profile, so commands that work in your terminal may not be found. Fix it by using absolute paths in your cron commands:

```bash
# Fragile — relies on PATH
*/5 * * * * backup.sh

# Correct — absolute path
*/5 * * * * /opt/scripts/backup.sh

# Or set PATH explicitly at the top of your crontab
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
```

**You never find out when a job fails.** By default, cron emails output to the local user, which goes nowhere on most servers. Redirect output to a log file so you can check it:

```bash
*/5 * * * * /opt/scripts/healthcheck.sh >> /var/log/healthcheck.log 2>&1
```

`2>&1` redirects stderr to stdout, so both go to the log file. Without it, errors silently disappear.

**The job runs as the wrong user.** User crontabs run as that user. If your script needs root privileges, edit root's crontab (`sudo crontab -e`) or use `/etc/cron.d/` with an explicit user field.

**Overlapping runs.** If a job takes longer than its interval, a new instance starts before the previous one finishes. This can cause data corruption. Use a lock file or a tool like `flock`:

```bash
*/5 * * * * flock -n /tmp/myjob.lock /opt/scripts/myjob.sh
```

## systemd timers — the alternative

systemd provides timers as an alternative to cron. A timer unit triggers a service unit on a schedule. The advantages: execution is logged in the journal, you can see when a timer last ran with `systemctl list-timers`, missed runs can be caught up, and you get all of systemd's process management features.

```bash
systemctl list-timers          # show all active timers and when they last/next ran
systemctl status myapp.timer   # status of a specific timer
```

For simple scheduled tasks, cron is fine and much simpler to set up. For anything complex — jobs that need resource limits, dependency ordering, reliable logging, or restart-on-failure — systemd timers are worth the extra setup. Both approaches are common in production; you need to be comfortable with both.

<!-- RESOURCES -->

- [crontab.guru - Interactive cron expression editor](https://crontab.guru/) -- type: tool, time: 5m
- [Cron How-To - Ubuntu](https://help.ubuntu.com/community/CronHowto) -- type: tutorial, time: 20m
- [systemd Timers - Arch Wiki](https://wiki.archlinux.org/title/Systemd/Timers) -- type: reference, time: 30m
- [A Cron Tutorial for Beginners - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-use-cron-to-automate-tasks-ubuntu-1804) -- type: tutorial, time: 25m

<!-- ZH_SUMMARY -->
有些任务需要按计划执行——每晚清理旧文件、每小时运行一次数据库备份、每五分钟发送一次健康检查 ping。你不会想手动做这些事。**cron** 是 Linux 上用于调度周期性任务的标准工具，自 20 世纪 70 年代以来一直存在。你会在各处遇到它：在你管理的服务器上、在你接手的应用中、在你调试的容器里。理解它如何工作以及在哪里会出问题，是一项实际的必备能力。

<!-- ZH_DEEP_DIVE -->
## cron 的工作原理

`crond` 是一个在后台运行的守护进程，每分钟唤醒一次，检查是否有需要运行的定时任务。任务定义在 **crontab** 文件中——每个用户一个，通过 `crontab` 命令管理。

```bash
crontab -e    # 打开你的 crontab 进行编辑
crontab -l    # 列出你当前的 crontab
crontab -r    # 删除你的 crontab（小心——没有确认提示）
```

crontab 中的每一行定义一个任务。格式为：

```
minute  hour  day-of-month  month  day-of-week  command
```

五个时间字段，然后是命令。各字段含义：

| 字段 | 范围 | 特殊说明 |
|---|---|---|
| minute（分钟） | 0–59 | |
| hour（小时） | 0–23 | |
| day of month（日） | 1–31 | |
| month（月） | 1–12 | |
| day of week（星期） | 0–7 | 0 和 7 都表示星期日 |

字段中的 `*` 表示“每一个”。特殊值：
- `*/5` — 每 5 个（例如每 5 分钟）
- `1,15` — 在第 1 和第 15 个
- `1-5` — 从 1 到 5

## 解读 cron 表达式

```
# 每天凌晨 2:30 运行
30 2 * * * /opt/scripts/backup.sh

# 每 5 分钟运行一次
*/5 * * * * /opt/scripts/healthcheck.sh

# 每月 1 号午夜运行
0 0 1 * * /opt/scripts/monthly-report.sh

# 周一到周五上午 9 点运行
0 9 * * 1-5 /opt/scripts/morning-checks.sh

# 每小时运行一次
0 * * * * /opt/scripts/cleanup.sh
```

使用 [crontab.guru](https://crontab.guru/) 交互式检查你的表达式——粘贴任意 cron 调度，它会用通俗的英文告诉你它将在何时运行。

## 特殊字符串

这些快捷方式替代五个时间字段：

- `@daily` — 每天午夜运行一次（等同于 `0 0 * * *`）
- `@hourly` — 每小时整点运行一次
- `@weekly` — 每周一次，周日午夜
- `@monthly` — 每月一次，1 号午夜
- `@reboot` — 系统启动时运行一次。适用于重启后的一次性设置。

## 系统级 cron

除了每用户的 crontab，还有系统级位置：

- `/etc/crontab` — 系统 crontab。多一个字段用于指定以哪个用户身份运行。
- `/etc/cron.d/` — 存放 cron 文件的目录，通常由软件包放入。格式与 `/etc/crontab` 相同。
- `/etc/cron.daily/`、`/etc/cron.hourly/`、`/etc/cron.weekly/`、`/etc/cron.monthly/` — 只需把脚本放入对应目录，它就会按该调度运行。无需 cron 语法。

当你安装需要定时维护的软件包（比如用于 TLS 证书续期的 certbot）时，它通常会在 `/etc/cron.d/` 或 `/etc/cron.daily/` 中放入一个文件。当你想弄清楚某个任务来自哪里时，这一点值得了解。

## 最常见的 cron 问题

**任务手动能运行，但从 cron 运行不了。** 几乎总是 `PATH` 问题。cron 以最小环境运行——它不会加载你的 shell 配置文件，所以在你终端中能用的命令可能找不到。解决方法是在 cron 命令中使用绝对路径：

```bash
# 脆弱——依赖 PATH
*/5 * * * * backup.sh

# 正确——绝对路径
*/5 * * * * /opt/scripts/backup.sh

# 或者在 crontab 顶部显式设置 PATH
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
```

**任务失败时你永远不知道。** 默认情况下，cron 会把输出通过邮件发给本地用户，而在大多数服务器上这封邮件无处可去。把输出重定向到日志文件，这样你就能查看：

```bash
*/5 * * * * /opt/scripts/healthcheck.sh >> /var/log/healthcheck.log 2>&1
```

`2>&1` 把 stderr 重定向到 stdout，这样两者都会写入日志文件。没有它，错误会悄无声息地消失。

**任务以错误的用户身份运行。** 用户 crontab 以该用户身份运行。如果你的脚本需要 root 权限，编辑 root 的 crontab（`sudo crontab -e`）或使用带显式用户字段的 `/etc/cron.d/`。

**运行重叠。** 如果任务耗时超过其间隔，新实例会在前一个完成之前启动。这可能导致数据损坏。使用锁文件或像 `flock` 这样的工具：

```bash
*/5 * * * * flock -n /tmp/myjob.lock /opt/scripts/myjob.sh
```

## systemd 定时器——替代方案

systemd 提供定时器作为 cron 的替代方案。定时器单元按调度触发服务单元。优点：执行记录在 journal 中，你可以用 `systemctl list-timers` 查看定时器上次运行的时间，错过的运行可以被补上，并且你能获得 systemd 的全部进程管理功能。

```bash
systemctl list-timers          # 显示所有活动定时器及其上次/下次运行时间
systemctl status myapp.timer   # 特定定时器的状态
```

对于简单的定时任务，cron 就够用，而且设置起来简单得多。对于任何复杂场景——需要资源限制、依赖顺序、可靠日志或失败重启的任务——systemd 定时器值得额外配置。两种方式在生产环境中都很常见；你需要对两者都熟悉。

<!-- ZH_RESOURCES -->
- [crontab.guru - 交互式 cron 表达式编辑器](https://crontab.guru/) -- 类型: 工具, 时长: 5m
- [Cron 使用指南 - Ubuntu](https://help.ubuntu.com/community/CronHowto) -- 类型: 教程, 时长: 20m
- [systemd 定时器 - Arch Wiki](https://wiki.archlinux.org/title/Systemd/Timers) -- 类型: 参考, 时长: 30m
- [面向初学者的 Cron 教程 - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-use-cron-to-automate-tasks-ubuntu-1804) -- 类型: 教程, 时长: 25m

<!-- ZH_UI -->
1. 编写一条 crontab 条目，按计划运行脚本
2. 解释 cron 的五个时间字段，并能读懂任意 cron 表达式
3. 捕获 cron 任务输出，并调试未运行的任务
4. 我的 cron 任务越来越复杂了。什么时候应该改写成正式脚本？
5. 我从 cron 里的简单单行命令起步，但现在我把五条命令串在一起、处理错误，越来越难读了。到什么程度它就不再算 cron 任务，而应该写成正式脚本？那又该是什么样子？
