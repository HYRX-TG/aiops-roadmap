---
id: essential-linux-commands
title: Essential Linux Commands
zone: foundations
edges:
  to:
    - id: grep-and-searching
      question: I can navigate and manage files — but the output is overwhelming. How do I search through it?
      detail: >-
        ps aux gives me 80 lines. df gives me 10. cat on a log file gives me
        thousands. I need to find a specific process, filter for errors, count
        things. I keep piping to grep but I'm mostly guessing at the syntax.
        What's the right way to search through all this output?
difficulty: 1
tags:
  - linux
  - commands
  - terminal
  - shell
  - cli
category: practice
milestones:
  - Navigate and manipulate files entirely from the command line
  - Inspect running processes, disk usage, and memory from the terminal
  - Combine commands with pipes to answer practical questions about a system
title_zh: "必备 Linux 命令"
---


The terminal gives you a shell. But what do you actually type? There are hundreds of Linux commands, but as an SRE you will reach for the same couple dozen over and over. This node covers the ones that matter — not a complete reference, but the commands you need to be fluent in before anything else makes sense.

<!-- DEEP_DIVE -->

## Navigation and file management

These are the commands you use to move around and manage the filesystem. You should be able to do all of this without thinking:

- `pwd` — print working directory. Where are you right now?
- `ls` — list files. `ls -l` shows permissions, owner, size, and date. `ls -la` includes hidden files (dotfiles).
- `cd /var/log` — change directory. `cd ..` goes up one level. `cd ~` goes home. `cd -` goes back to where you just were.
- `mkdir -p /opt/myapp/config` — create directory (and parents if needed).
- `cp file.txt backup.txt` — copy. `cp -r dir/ backup/` for directories.
- `mv old.txt new.txt` — rename or move.
- `rm file.txt` — delete. `rm -r dir/` for directories. **There is no trash can. This is permanent.**
- `touch file.txt` — create an empty file, or update the timestamp if it already exists.
- `find /var/log -name "*.log" -mtime -1` — find files by name, time, size. More powerful than it looks.

## Viewing files

- `cat file.txt` — print the whole file. Fine for short files, terrible for large ones.
- `less file.txt` — page through a file. Use `/` to search, `q` to quit. Use this instead of `cat` for anything longer than a screen.
- `head -20 file.txt` — first 20 lines.
- `tail -20 file.txt` — last 20 lines. `tail -f file.txt` follows the file in real time as new lines are written — your live log viewer.

## Processes

- `ps aux` — list all running processes with PID, CPU, memory, and the command that started them.
- `ps aux | grep nginx` — the single most common process command you will use. Find a specific process by name.
- `top` — interactive process viewer, updated every few seconds. Press `q` to quit, `k` to kill a process by PID, `M` to sort by memory, `P` to sort by CPU.
- `htop` — a friendlier version of top. Not always installed by default but worth getting.
- `kill 1234` — send SIGTERM (graceful shutdown) to PID 1234.
- `kill -9 1234` — send SIGKILL (force kill). Use this only when the process won't respond to SIGTERM.

One important quirk: `ps aux | grep nginx` will also show the grep process itself in the output. Filter it out with `ps aux | grep [n]ginx` — the bracket trick prevents grep from matching itself.

## Disk and memory

- `df -h` — disk space on all mounted filesystems. The `-h` flag makes sizes human-readable (GB, MB). Check this when a server is behaving oddly — a full disk is a surprisingly common cause of outages.
- `du -sh /var/log` — how much disk space a directory is using. `du -sh *` in a directory gives a breakdown of every subdirectory.
- `du -sh * | sort -rh` — the combination you actually want: size of everything in the current directory, sorted largest first. Invaluable for tracking down what ate your disk.
- `free -h` — memory usage: total, used, free, and buffer/cache. The "available" column is what matters — it accounts for memory the kernel can reclaim.

## Network basics (commands)

- `curl -I https://example.com` — make an HTTP request. `-I` fetches only the headers. Useful for checking if a service is responding.
- `wget https://example.com/file.tar.gz` — download a file.
- `ping google.com` — check if a host is reachable.
- `ss -tlnp` — show listening TCP sockets and which process owns them. Tells you what is listening on what port. (Older systems use `netstat -tlnp`.)

## Getting help

- `man ls` — the built-in manual for any command. Press `q` to quit.
- `ls --help` — shorter, inline help. Most commands support this.
- `which nginx` — where is the nginx binary? Useful when you have multiple versions installed.
- `type cd` — tells you if a command is a shell builtin, an alias, or an external binary.

## Practical combinations

The real power is in combining commands. A few patterns you will use constantly:

```bash
# Find the process using port 8080
ss -tlnp | grep 8080

# What is eating my disk?
du -sh /var/log/* | sort -rh | head -10

# Is nginx actually running?
ps aux | grep [n]ginx

# How many connections does my app have right now?
ss -tn state established | grep :443 | wc -l

# What changed recently in /etc?
find /etc -mmin -60 -type f
```

You do not need to memorize these. You need to understand the pieces well enough to build them when you need them.

<!-- RESOURCES -->

- [The Linux Command Line (free book by William Shotts)](https://linuxcommand.org/tlcl.php) -- type: book, time: varies
- [Linux Commands Cheat Sheet - Red Hat](https://www.redhat.com/en/blog/linux-commands-cheat-sheet) -- type: reference, time: 10m
- [OverTheWire: Bandit - Learn CLI through challenges](https://overthewire.org/wargames/bandit/) -- type: practice, time: 5h
- [Explain Shell - Paste a command and get it explained](https://explainshell.com/) -- type: tool, time: 5m

<!-- ZH_SUMMARY -->
终端给你一个 shell。但你实际要输入什么？Linux 命令有数百个，但作为 SRE，你会反复用到同样的那几十个。本节点涵盖真正重要的那些——不是一份完整参考，而是你在理解其他一切之前必须熟练使用的命令。

<!-- ZH_DEEP_DIVE -->
## 导航与文件管理

这些是你在文件系统中移动和管理文件时使用的命令。你应该能够不假思索地完成所有这些操作：

- `pwd` — 打印当前工作目录。你现在在哪里？
- `ls` — 列出文件。`ls -l` 显示权限、所有者、大小和日期。`ls -la` 包含隐藏文件（点文件）。
- `cd /var/log` — 切换目录。`cd ..` 向上一级。`cd ~` 回到主目录。`cd -` 回到你刚才所在的位置。
- `mkdir -p /opt/myapp/config` — 创建目录（如有需要，同时创建父目录）。
- `cp file.txt backup.txt` — 复制。目录使用 `cp -r dir/ backup/`。
- `mv old.txt new.txt` — 重命名或移动。
- `rm file.txt` — 删除。目录使用 `rm -r dir/`。**没有回收站。这是永久性的。**
- `touch file.txt` — 创建一个空文件，如果文件已存在则更新其时间戳。
- `find /var/log -name "*.log" -mtime -1` — 按名称、时间、大小查找文件。它比看起来更强大。

## 查看文件

- `cat file.txt` — 打印整个文件。适合短文件，对大文件很糟糕。
- `less file.txt` — 分页浏览文件。使用 `/` 搜索，`q` 退出。对于超过一屏的内容，用这个而不是 `cat`。
- `head -20 file.txt` — 前 20 行。
- `tail -20 file.txt` — 最后 20 行。`tail -f file.txt` 会实时跟随文件，在新行写入时显示——你的实时日志查看器。

## 进程

- `ps aux` — 列出所有正在运行的进程，包括 PID、CPU、内存以及启动它们的命令。
- `ps aux | grep nginx` — 你将使用的最常见的进程命令。按名称查找特定进程。
- `top` — 交互式进程查看器，每隔几秒更新一次。按 `q` 退出，按 `k` 按 PID 终止进程，按 `M` 按内存排序，按 `P` 按 CPU 排序。
- `htop` — top 的更友好版本。默认不一定安装，但值得获取。
- `kill 1234` — 向 PID 1234 发送 SIGTERM（优雅关闭）。
- `kill -9 1234` — 发送 SIGKILL（强制终止）。仅在进程不响应 SIGTERM 时使用。

一个重要的小问题：`ps aux | grep nginx` 也会在输出中显示 grep 进程本身。用 `ps aux | grep [n]ginx` 将其过滤掉——方括号技巧可防止 grep 匹配自身。

## 磁盘与内存

- `df -h` — 所有已挂载文件系统的磁盘空间。`-h` 标志使大小人类可读（GB、MB）。当服务器行为异常时检查这个——磁盘满是导致故障的一个出奇常见的原因。
- `du -sh /var/log` — 一个目录占用了多少磁盘空间。在目录中执行 `du -sh *` 可以得到每个子目录的细分。
- `du -sh * | sort -rh` — 你真正想要的组合：当前目录中所有内容的大小，按从大到小排序。对于追踪是什么吃掉了你的磁盘非常有用。
- `free -h` — 内存使用情况：总计、已用、空闲以及缓冲区/缓存。“available”列才是关键——它考虑了内核可以回收的内存。

## 网络基础（命令）

- `curl -I https://example.com` — 发起 HTTP 请求。`-I` 仅获取响应头。用于检查服务是否有响应。
- `wget https://example.com/file.tar.gz` — 下载文件。
- `ping google.com` — 检查主机是否可达。
- `ss -tlnp` — 显示正在监听的 TCP 套接字以及拥有它们的进程。告诉你什么在监听哪个端口。（较旧的系统使用 `netstat -tlnp`。）

## 获取帮助

- `man ls` — 任何命令的内置手册。按 `q` 退出。
- `ls --help` — 更简短的内联帮助。大多数命令都支持。
- `which nginx` — nginx 二进制文件在哪里？当你安装了多个版本时很有用。
- `type cd` — 告诉你一个命令是 shell 内建命令、别名还是外部二进制文件。

## 实用组合

真正的力量在于组合命令。以下是你将经常使用的一些模式：

```bash
# Find the process using port 8080
ss -tlnp | grep 8080

# What is eating my disk?
du -sh /var/log/* | sort -rh | head -10

# Is nginx actually running?
ps aux | grep [n]ginx

# How many connections does my app have right now?
ss -tn state established | grep :443 | wc -l

# What changed recently in /etc?
find /etc -mmin -60 -type f
```

你不需要记住这些。你需要足够理解这些组成部分，以便在需要时构建它们。

<!-- ZH_RESOURCES -->
- [The Linux Command Line（William Shotts 的免费书籍）](https://linuxcommand.org/tlcl.php) -- 类型：书籍，时间：不定
- [Linux 命令速查表 - Red Hat](https://www.redhat.com/en/blog/linux-commands-cheat-sheet) -- 类型：参考，时间：10 分钟
- [OverTheWire: Bandit - 通过挑战学习 CLI](https://overthewire.org/wargames/bandit/) -- 类型：练习，时间：5 小时
- [Explain Shell - 粘贴命令并获取解释](https://explainshell.com/) -- 类型：工具，时间：5 分钟

<!-- ZH_UI -->
1. 完全从命令行导航和操作文件
2. 从终端检查运行中的进程、磁盘使用情况和内存
3. 用管道组合命令来回答关于系统的实际问题
4. 我能导航和管理文件——但输出太多了。我该如何在其中搜索？
5. ps aux 给我 80 行。df 给我 10 行。对日志文件执行 cat 会给我几千行。我需要找到特定进程、过滤错误、计数。我一直用管道接 grep，但大多是在猜语法。搜索所有这些输出的正确方式是什么？
