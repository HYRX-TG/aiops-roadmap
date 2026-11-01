---
id: pipes-and-redirection
title: Pipes & Redirection
zone: foundations
edges:
  to:
    - id: environment-and-shell-config
      question: I can chain commands. How do I customize my shell environment?
      detail: >-
        Pipes are starting to click. But I keep noticing things I have to set up
        every time I open a terminal — aliases, paths, settings that just
        disappear when I close the session. Where does all of this actually
        live?
difficulty: 1
tags:
  - pipes
  - redirection
  - stdin
  - stdout
  - stderr
  - unix-philosophy
  - composition
category: concept
milestones:
  - 'Explain what stdin, stdout, and stderr are'
  - Chain three commands together with pipes to solve a problem
  - Redirect output to a file and separate stdout from stderr
title_zh: "管道与重定向"

---


Run `ls`. The output appears on your screen. But what if you want to save it to a file? Or feed it into another command that filters the results? Or discard error messages while keeping the useful output? This is what **pipes and redirection** are for — they let you control where data flows between commands. This is the single most powerful idea in the Unix world: small commands that do one thing, connected together to do anything.

<!-- DEEP_DIVE -->

Every process on Linux has three standard data streams, opened automatically when it starts:

- **stdin (standard input)** — file descriptor 0. Where the process reads input from. By default, this is your keyboard.
- **stdout (standard output)** — file descriptor 1. Where the process writes normal output. By default, this is your terminal screen.
- **stderr (standard error)** — file descriptor 2. Where the process writes error messages. Also your terminal screen by default, but crucially separate from stdout.

These three streams are the foundation of everything that follows. They are why `ls` prints to your screen, why error messages from a failing command show up alongside normal output, and why you can reroute all of it.

**Redirection** changes where these streams go:

- `command > file` — redirect stdout to a file (overwrites the file). `ls > filelist.txt` saves the directory listing to a file instead of printing it.
- `command >> file` — append stdout to a file (does not overwrite).
- `command 2> file` — redirect stderr to a file. Useful for saving error logs: `./build.sh 2> errors.log`.
- `command > file 2>&1` — redirect both stdout and stderr to the same file. The `2>&1` means "send stderr wherever stdout is going." This is essential for capturing complete output from scripts and cron jobs.
- `command < file` — redirect a file into stdin. `sort < names.txt` sorts the contents of the file.
- `command > /dev/null` — discard output. `/dev/null` is a special file that swallows everything written to it. `command > /dev/null 2>&1` silences a command completely.

**Pipes** (`|`) connect the stdout of one command to the stdin of the next:

- `cat access.log | grep "POST"` — read the file and filter for lines containing "POST"
- `ps aux | grep nginx | grep -v grep` — list processes, filter for nginx, remove the grep itself from results
- `cat access.log | awk '{print $9}' | sort | uniq -c | sort -rn | head -20` — extract HTTP status codes from an access log, count occurrences, and show the top 20

That last example is the Unix philosophy at its most powerful: six simple tools, each doing one thing, composed into an ad-hoc log analysis pipeline. No code, no scripts — just pipes. As an SRE, you will build pipelines like this constantly during incidents to quickly answer questions like "what are the most common error codes in the last hour?" or "which IP addresses are making the most requests?"

**Useful commands that pair well with pipes:**

- `grep` — filter lines matching a pattern. `grep -i "error" app.log` (case-insensitive).
- `awk` — extract and manipulate fields. `awk '{print $1, $4}' access.log` prints the first and fourth columns.
- `sed` — stream editor for find-and-replace. `sed 's/old/new/g' file.txt`.
- `sort` — sort lines. `sort -n` for numeric sort, `sort -r` for reverse.
- `uniq` — deduplicate adjacent lines. Almost always used after `sort`. `uniq -c` counts occurrences.
- `wc` — count lines (`wc -l`), words (`wc -w`), or characters (`wc -c`).
- `head` / `tail` — show the first or last N lines. `tail -f logfile` follows a log in real time.
- `cut` — extract fields by delimiter. `cut -d',' -f2 data.csv` gets the second column of a CSV.
- `tee` — split output to both a file and stdout. `command | tee output.log` lets you see the output AND save it.

**The practical difference between stdout and stderr.** Run a command that produces both normal output and errors: `ls /home /nonexistent 2>/dev/null`. The listing of `/home` appears (stdout), but the "No such file or directory" error for `/nonexistent` is discarded (stderr sent to /dev/null). Being able to separate these streams is critical for scripting — you want your script's output to be clean data that the next command can process, while errors go to a log file for debugging.

<!-- RESOURCES -->

- [Pipelines - Linux Documentation Project](https://tldp.org/LDP/abs/html/io-redirection.html) -- type: reference, time: 30m
- [MIT Missing Semester - Shell Tools and Scripting](https://missing.csail.mit.edu/2020/shell-tools/) -- type: course, time: 1h
- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) -- type: reference, time: 1h
- [Explain Shell](https://explainshell.com/) -- type: tool, time: 5m
- [Linux Pipes and Redirection - Linode](https://www.linode.com/docs/guides/piping-and-redirecting-linux-commands/) -- type: tutorial, time: 20m

<!-- ZH_SUMMARY -->
运行 `ls`。输出会显示在屏幕上。但如果你想把它保存到文件呢？或者把它传给另一个命令来过滤结果？又或者丢弃错误消息而保留有用的输出？这就是 **管道与重定向** 的用途——它们让你控制数据在命令之间的流向。这是 Unix 世界中最强大的一个理念：让每个小命令只做一件事，再把它们连接起来，就能完成任何任务。

<!-- ZH_DEEP_DIVE -->
Linux 上的每个进程都有三个标准数据流，在进程启动时自动打开：

- **stdin（标准输入）** — 文件描述符 0。进程从这里读取输入。默认情况下，这是你的键盘。
- **stdout（标准输出）** — 文件描述符 1。进程将正常输出写入这里。默认情况下，这是你的终端屏幕。
- **stderr（标准错误）** — 文件描述符 2。进程将错误消息写入这里。默认情况下也是你的终端屏幕，但关键在于它与 stdout 是分离的。

这三个流是后续一切内容的基础。它们解释了为什么 `ls` 会打印到你的屏幕、为什么失败命令的错误消息会与正常输出一起出现，以及为什么你可以重定向所有这些内容。

**重定向**改变这些流的去向：

- `command > file` — 将 stdout 重定向到文件（覆盖文件）。`ls > filelist.txt` 将目录列表保存到文件，而不是打印出来。
- `command >> file` — 将 stdout 追加到文件（不覆盖）。
- `command 2> file` — 将 stderr 重定向到文件。适合保存错误日志：`./build.sh 2> errors.log`。
- `command > file 2>&1` — 将 stdout 和 stderr 都重定向到同一个文件。`2>&1` 的意思是“把 stderr 发送到 stdout 所去的地方”。这对于捕获脚本和 cron 作业的完整输出至关重要。
- `command < file` — 将文件重定向到 stdin。`sort < names.txt` 对文件内容进行排序。
- `command > /dev/null` — 丢弃输出。`/dev/null` 是一个特殊文件，会吞掉写入它的所有内容。`command > /dev/null 2>&1` 完全静默一个命令。

**管道**（`|`）将一个命令的 stdout 连接到下一个命令的 stdin：

- `cat access.log | grep "POST"` — 读取文件并筛选包含 "POST" 的行
- `ps aux | grep nginx | grep -v grep` — 列出进程，筛选 nginx，从结果中移除 grep 自身
- `cat access.log | awk '{print $9}' | sort | uniq -c | sort -rn | head -20` — 从访问日志中提取 HTTP 状态码，统计出现次数，并显示前 20 个

最后一个例子是 Unix 哲学最强大的体现：六个简单工具，每个只做一件事，组合成一个临时的日志分析管道。没有代码，没有脚本——只有管道。作为 SRE，你会在事故处理期间不断构建这样的管道，以快速回答诸如“过去一小时最常见的错误码是什么？”或“哪些 IP 地址发出的请求最多？”之类的问题。

**与管道搭配良好的实用命令：**

- `grep` — 筛选匹配模式的行。`grep -i "error" app.log`（不区分大小写）。
- `awk` — 提取和操作字段。`awk '{print $1, $4}' access.log` 打印第一列和第四列。
- `sed` — 用于查找替换的流编辑器。`sed 's/old/new/g' file.txt`。
- `sort` — 对行排序。`sort -n` 用于数值排序，`sort -r` 用于反向排序。
- `uniq` — 去重相邻行。几乎总是用在 `sort` 之后。`uniq -c` 统计出现次数。
- `wc` — 统计行数（`wc -l`）、单词数（`wc -w`）或字符数（`wc -c`）。
- `head` / `tail` — 显示前 N 行或后 N 行。`tail -f logfile` 实时跟踪日志。
- `cut` — 按分隔符提取字段。`cut -d',' -f2 data.csv` 获取 CSV 的第二列。
- `tee` — 将输出同时分到文件和 stdout。`command | tee output.log` 让你既能查看输出又能保存它。

**stdout 与 stderr 的实际区别。** 运行一个同时产生正常输出和错误的命令：`ls /home /nonexistent 2>/dev/null`。`/home` 的列表会出现（stdout），但 `/nonexistent` 的 "No such file or directory" 错误被丢弃（stderr 发送到 /dev/null）。能够分离这些流对脚本编写至关重要——你希望脚本的输出是干净的数据，以便下一个命令可以处理，而错误则进入日志文件用于调试。

<!-- ZH_RESOURCES -->
- [管道 - Linux 文档项目](https://tldp.org/LDP/abs/html/io-redirection.html) -- 类型：参考，时间：30分钟
- [MIT 缺失的学期 - Shell 工具与脚本](https://missing.csail.mit.edu/2020/shell-tools/) -- 类型：课程，时间：1小时
- [命令行艺术](https://github.com/jlevy/the-art-of-command-line) -- 类型：参考，时间：1小时
- [Explain Shell](https://explainshell.com/) -- 类型：工具，时间：5分钟
- [Linux 管道与重定向 - Linode](https://www.linode.com/docs/guides/piping-and-redirecting-linux-commands/) -- 类型：教程，时间：20分钟

<!-- ZH_UI -->
1. 解释 stdin、stdout 和 stderr 是什么
2. 用管道将三个命令串联起来解决问题
3. 将输出重定向到文件，并将 stdout 与 stderr 分离
4. 我能串联命令了。如何自定义我的 shell 环境？
5. 管道开始变得清晰了。但我总注意到每次打开终端都要重新设置一些东西——别名、路径、设置，一关闭会话就消失了。这些到底存在哪里？
