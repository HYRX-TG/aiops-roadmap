---
id: grep-and-searching
title: Searching and Filtering Output
zone: foundations
edges:
  to:
    - id: regular-expressions
      question: The patterns I write in grep work, but I'm guessing at the syntax. What are the actual rules?
      detail: >-
        I've been copying grep patterns from Stack Overflow and they mostly work,
        but I don't really know why. What does .* mean? Why does [0-9]+ match
        numbers? Sometimes my pattern matches too much, sometimes nothing at all.
        I want to be able to write these from scratch instead of guessing.
    - id: text-processing
      question: I can filter lines — but what if I need to reshape or count the output?
      detail: >-
        grep finds the lines I care about, but then what? Sometimes I need just
        one field out of each line, or I want to count how many times each value
        appears, or remove duplicates. The data is all there, I just need it in
        a different shape.
difficulty: 1
tags:
  - grep
  - tail
  - searching
  - filtering
  - logs
  - shell
  - cli
category: practice
milestones:
  - Use grep with flags (-i, -r, -v, -c, -A, -B) to find patterns in files and command output
  - Follow live log output and filter it in real time
  - Build multi-stage pipe commands to answer specific questions about a system
title_zh: "搜索和过滤输出"

---


When a server is misbehaving, you are not going to read log files line by line. You are going to search through them. `grep` is the tool you reach for first — it filters input to only the lines that match a pattern — and once you combine it with pipes, it becomes one of the most powerful tools in your arsenal. This node covers grep, the flags that matter, and the real patterns you will use constantly as an SRE.

<!-- DEEP_DIVE -->

## grep basics

`grep "pattern" file` — print every line in `file` that contains the pattern.

The flags you need to know:

- `-i` — case-insensitive. `grep -i "error"` matches ERROR, Error, error.
- `-v` — invert. Print lines that do **not** match. Useful for filtering noise: `grep -v "healthcheck"`.
- `-n` — show line numbers alongside matches.
- `-c` — count matches instead of printing them. `grep -c "ERROR" app.log` tells you how many errors, not which ones.
- `-r` — recursive. Search an entire directory. `grep -r "database_url" /etc/` searches every file under `/etc/`.
- `-l` — only print filenames of files that contain a match, not the matching lines themselves.
- `-E` — extended regex. Lets you use `|` for alternation: `grep -E "ERROR|WARN"` matches either.

## Context flags — essential during incidents

When you find an error, you often want to see what happened before and after it:

- `-A 5` — print 5 lines **after** each match
- `-B 5` — print 5 lines **before** each match
- `-C 5` — print 5 lines of context on **both** sides

```bash
# Show what led up to each FATAL log entry
grep -C 10 "FATAL" /var/log/myapp/app.log
```

## grep with pipes — where it gets powerful

grep doesn't just work on files. It works on any input, which makes it essential in pipelines:

```bash
# Is nginx actually running?
ps aux | grep [n]ginx

# The bracket trick: prevents grep from matching its own process in the output.
# ps aux | grep nginx shows the grep process too.
# ps aux | grep [n]ginx does not, because the pattern [n]ginx doesn't match "grep nginx".

# How many 500 errors in the last hour's nginx log?
grep "HTTP/1.1\" 5" /var/log/nginx/access.log | grep -c ""

# Show only error and warning lines from journalctl
journalctl -u myapp --since "1 hour ago" | grep -E "ERROR|WARN"

# What IPs are hitting my server most?
grep "GET /api/endpoint" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

## tail — following live output

`tail -f /var/log/nginx/access.log` — follow a log file in real time. New lines appear as they are written. This is how you watch what a service is doing right now.

Combine it with grep to filter the live stream:

```bash
# Watch for errors in real time, ignore everything else
tail -f /var/log/myapp/app.log | grep --line-buffered "ERROR"

# Watch POST requests hitting a specific endpoint
tail -f /var/log/nginx/access.log | grep --line-buffered "POST /api/payments"
```

The `--line-buffered` flag is important here — without it, grep buffers output and you won't see results immediately.

For systemd services, `journalctl -u myapp -f` is often better than tailing a log file directly — it follows the journal stream, which captures stdout/stderr even if the service doesn't write to a file.

## head and tail for slicing

- `head -20 file` — first 20 lines
- `tail -20 file` — last 20 lines
- `tail -n +100 file` — everything from line 100 onward (skip the first 99 lines)

## Searching compressed logs

Logs get rotated and compressed. `zgrep` works like grep but on `.gz` files without decompressing them first:

```bash
zgrep "payment_failed" /var/log/myapp/app.log.3.gz
```

## Practical SRE patterns

```bash
# Did the service restart recently? When?
journalctl -u myapp | grep "Started"

# Are there OOM kills in the last hour?
journalctl -p err --since "1 hour ago" | grep -i "out of memory"

# What ports is this machine listening on, and which process owns each?
ss -tlnp | grep LISTEN

# Which systemd services failed?
systemctl list-units --type=service | grep failed

# Find all config files that reference a specific database host
grep -r "db.internal.example.com" /etc/ 2>/dev/null

# Count requests per HTTP status code in nginx access log
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

<!-- RESOURCES -->

- [grep Manual - GNU](https://www.gnu.org/software/grep/manual/grep.html) -- type: reference, time: 30m
- [grep Cheat Sheet - ryanstutorials.net](https://ryanstutorials.net/linuxtutorial/grep.php) -- type: tutorial, time: 20m
- [The Art of Command Line (GitHub)](https://github.com/jlevy/the-art-of-command-line) -- type: reference, time: varies
- [Linux tail command - examples and usage](https://linuxize.com/post/linux-tail-command/) -- type: tutorial, time: 10m

<!-- ZH_SUMMARY -->
当服务器出现异常时，你不会逐行阅读日志文件，而是会去搜索它们。`grep` 是你首先会想到的工具——它把输入过滤为只匹配某个模式的行——而一旦把它与管道结合起来，它就会成为你武器库中最强大的工具之一。本节点涵盖 grep、重要的标志，以及你作为 SRE 会经常使用的真实模式。

<!-- ZH_DEEP_DIVE -->
## grep 基础

`grep "pattern" file` — 打印 `file` 中包含该模式的每一行。

你需要了解的标志：

- `-i` — 忽略大小写。`grep -i "error"` 会匹配 ERROR、Error、error。
- `-v` — 反转。打印**不**匹配的行。用于过滤噪音很有用：`grep -v "healthcheck"`。
- `-n` — 在匹配项旁显示行号。
- `-c` — 统计匹配数量而不是打印它们。`grep -c "ERROR" app.log` 告诉你有多少个错误，而不是哪些错误。
- `-r` — 递归。搜索整个目录。`grep -r "database_url" /etc/` 会搜索 `/etc/` 下的每个文件。
- `-l` — 只打印包含匹配项的文件名，而不是匹配行本身。
- `-E` — 扩展正则表达式。允许使用 `|` 进行或运算：`grep -E "ERROR|WARN"` 匹配任意一个。

## 上下文标志 — 事故期间至关重要

当你发现一个错误时，通常想看看它之前和之后发生了什么：

- `-A 5` — 打印每个匹配项**之后**的 5 行
- `-B 5` — 打印每个匹配项**之前**的 5 行
- `-C 5` — 在**两侧**各打印 5 行上下文

```bash
# Show what led up to each FATAL log entry
grep -C 10 "FATAL" /var/log/myapp/app.log
```

## grep 配合管道 — 威力所在

grep 不仅作用于文件。它作用于任何输入，这使得它在管道中不可或缺：

```bash
# Is nginx actually running?
ps aux | grep [n]ginx

# The bracket trick: prevents grep from matching its own process in the output.
# ps aux | grep nginx shows the grep process too.
# ps aux | grep [n]ginx does not, because the pattern [n]ginx doesn't match "grep nginx".

# How many 500 errors in the last hour's nginx log?
grep "HTTP/1.1\" 5" /var/log/nginx/access.log | grep -c ""

# Show only error and warning lines from journalctl
journalctl -u myapp --since "1 hour ago" | grep -E "ERROR|WARN"

# What IPs are hitting my server most?
grep "GET /api/endpoint" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

## tail — 跟踪实时输出

`tail -f /var/log/nginx/access.log` — 实时跟踪日志文件。新行在写入时出现。这就是你观察服务当前正在做什么的方式。

将其与 grep 结合以过滤实时流：

```bash
# Watch for errors in real time, ignore everything else
tail -f /var/log/myapp/app.log | grep --line-buffered "ERROR"

# Watch POST requests hitting a specific endpoint
tail -f /var/log/nginx/access.log | grep --line-buffered "POST /api/payments"
```

这里的 `--line-buffered` 标志很重要 — 没有它，grep 会缓冲输出，你就无法立即看到结果。

对于 systemd 服务，`journalctl -u myapp -f` 通常比直接跟踪日志文件更好 — 它跟踪 journal 流，即使服务不写入文件也能捕获 stdout/stderr。

## head 和 tail 用于切片

- `head -20 file` — 前 20 行
- `tail -20 file` — 后 20 行
- `tail -n +100 file` — 从第 100 行开始的所有内容（跳过前 99 行）

## 搜索压缩日志

日志会被轮转和压缩。`zgrep` 的工作方式与 grep 类似，但作用于 `.gz` 文件而无需先解压：

```bash
zgrep "payment_failed" /var/log/myapp/app.log.3.gz
```

## 实用的 SRE 模式

```bash
# Did the service restart recently? When?
journalctl -u myapp | grep "Started"

# Are there OOM kills in the last hour?
journalctl -p err --since "1 hour ago" | grep -i "out of memory"

# What ports is this machine listening on, and which process owns each?
ss -tlnp | grep LISTEN

# Which systemd services failed?
systemctl list-units --type=service | grep failed

# Find all config files that reference a specific database host
grep -r "db.internal.example.com" /etc/ 2>/dev/null

# Count requests per HTTP status code in nginx access log
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

<!-- ZH_RESOURCES -->
- [grep 手册 - GNU](https://www.gnu.org/software/grep/manual/grep.html) -- 类型：参考，时间：30分钟
- [grep 速查表 - ryanstutorials.net](https://ryanstutorials.net/linuxtutorial/grep.php) -- 类型：教程，时间：20分钟
- [命令行艺术 (GitHub)](https://github.com/jlevy/the-art-of-command-line) -- 类型：参考，时间：不定
- [Linux tail 命令 - 示例与用法](https://linuxize.com/post/linux-tail-command/) -- 类型：教程，时间：10分钟

<!-- ZH_UI -->
1. 使用带标志（-i、-r、-v、-c、-A、-B）的 grep 在文件和命令输出中查找模式
2. 实时跟踪日志输出并即时过滤
3. 构建多级管道命令来回答关于系统的特定问题
4. 我写的 grep 模式能用，但语法是猜的。实际规则是什么？
5. 我一直从 Stack Overflow 复制 grep 模式，大多能用，但我不太明白为什么。.* 是什么意思？为什么 [0-9]+ 能匹配数字？有时我的模式匹配太多，有时什么都匹配不到。我希望能从零开始写这些模式，而不是靠猜。
6. 我能过滤行了——但如果需要重塑或统计输出呢？
7. grep 找到了我关心的行，然后呢？有时我只需要每行中的一个字段，或者想统计每个值出现的次数，或者去重。数据都在那里，我只是需要换一种形态。
