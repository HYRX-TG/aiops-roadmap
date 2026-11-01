---
id: the-terminal
title: The Terminal
zone: foundations
edges:
  to:
    - id: what-is-a-process
      question: I ran a command. What actually happened?
      detail: >-
        I typed a command and it ran. But what actually happened? I see it
        appear in the process list, I can kill it, it has a PID — but I don't
        understand what any of that means underneath. What is the thing I just
        created when I ran that command?
    - id: pipes-and-redirection
      question: I can run commands. How do I combine them?
      detail: >-
        I keep running one command, writing down the result, then running the
        next command with that result. There must be a way to feed output
        directly from one command into another without all the manual in-between
        steps. And I want to save output to a file sometimes too — how does all
        of that work?
    - id: text-editors-and-ides
      question: I need to write and edit files. What tools do I use?
      detail: >-
        I keep having to edit files on the server and I have no idea what to
        open them with. I tried vim once and couldn't even figure out how to
        quit. Is there a sane way to approach this?
    - id: essential-linux-commands
      question: I have a shell — what commands do I actually need to know?
      detail: >-
        I can open a terminal but I don't know what to type beyond cd and ls.
        I keep seeing commands like ps, df, find, kill mentioned everywhere but
        I have no idea when to use which one. What are the commands I actually
        need to survive on a Linux server?
difficulty: 1
tags:
  - terminal
  - shell
  - command-line
  - bash
  - cli
category: tool
milestones:
  - Navigate your filesystem using only the terminal
  - 'Run 10 basic commands (ls, cd, pwd, mkdir, rm, cp, mv, cat, echo, grep)'
title_zh: "终端"

---


The terminal is a text-based interface for talking to your computer. Instead of clicking icons and dragging windows, you type commands and read text output. It might feel like a step backward at first, but for SRE and DevOps work, the terminal is not just a tool -- it is *the* tool. Servers do not have graphical interfaces. When something breaks at 3 AM, you are going to SSH into a machine and fix it with typed commands.

<!-- DEEP_DIVE -->

Let's clear up some terminology first. The **terminal** (or terminal emulator) is the application that provides the window where you type. The **shell** is the program running inside that window that actually interprets your commands. The most common shell is **Bash** (Bourne Again Shell), which is the default on most Linux systems. macOS now defaults to **Zsh**, which is very similar. When someone says "open a terminal," they mean launch the terminal emulator, which starts a shell session where you can type commands.

Here are the commands you will use every single day. `pwd` prints your current directory -- where you are right now in the filesystem. `ls` lists the files in the current directory (`ls -la` shows hidden files and details). `cd` changes directory (`cd /var/log` takes you to the log directory, `cd ..` goes up one level). `mkdir` creates a directory. `rm` removes files (`rm -r` removes directories -- be careful, there is no trash can). `cp` copies files, `mv` moves or renames them. `cat` prints a file's contents to the screen. `echo` prints text. `grep` searches for patterns in text -- this one is incredibly powerful and you will use it constantly.

What makes the terminal truly powerful is **composition**. You can chain commands together using **pipes** (`|`). For example, `cat /var/log/syslog | grep "error" | wc -l` reads the system log, filters for lines containing "error," and counts them. That is three tools working together in a single line. Try doing that with a GUI. You can also redirect output to files with `>` (overwrite) and `>>` (append). This composability is why the Unix philosophy of "do one thing well" is so effective -- small, focused tools combine into powerful workflows.

For SRE work, the terminal is where you will spend most of your time. You will use it to SSH into remote servers, inspect logs, check system resource usage with `top` or `htop`, manage services with `systemctl`, install packages, configure firewalls, run deployment scripts, and interact with tools like Docker, Kubernetes, Terraform, and Git. Every single one of these tools is command-line first. GUIs exist for some of them, but the CLI is always more powerful and scriptable.

One practical tip: start building muscle memory now. Force yourself to use the terminal for tasks you would normally do with a GUI. Need to create a project folder with some files? Do it with `mkdir` and `touch`. Want to find a file? Use `find` or `locate` instead of Spotlight or Windows Search. The first week will feel slow, but within a month it will feel natural, and within a few months you will wonder how you ever lived without it.

Do not worry about memorizing everything. The `man` command (short for manual) is your built-in reference -- `man ls` shows you every option for the `ls` command. You can also use `--help` with most commands. Learning to read documentation is itself an essential SRE skill.

<!-- RESOURCES -->

- [Linux Command Line Basics - Ubuntu Tutorial](https://ubuntu.com/tutorials/command-line-for-beginners) -- type: tutorial, time: 1h
- [The Linux Command Line (free book by William Shotts)](https://linuxcommand.org/tlcl.php) -- type: book, time: varies
- [MIT Missing Semester - The Shell](https://missing.csail.mit.edu/2020/course-shell/) -- type: course, time: 1h
- [Explain Shell - Paste a command and get it explained](https://explainshell.com/) -- type: tool, time: 5m
- [OverTheWire: Bandit - Learn CLI through a game](https://overthewire.org/wargames/bandit/) -- type: practice, time: 5h

<!-- ZH_SUMMARY -->
终端是一种基于文本的界面，用于与计算机进行交互。你不再点击图标、拖动窗口，而是输入命令并阅读文本输出。起初这可能让人觉得是一种退步，但对于 SRE 和 DevOps 工作而言，终端不仅是一个工具——它就是*那个*工具。服务器没有图形界面。当凌晨 3 点出现故障时，你将通过 SSH 登录到一台机器，用输入命令的方式修复它。

<!-- ZH_DEEP_DIVE -->
先澄清一些术语。**终端**（或终端模拟器）是提供你输入命令的窗口的应用程序。**shell** 是在那个窗口内运行、真正解释你命令的程序。最常见的 shell 是 **Bash**（Bourne Again Shell），它是大多数 Linux 系统上的默认 shell。macOS 现在默认使用 **Zsh**，两者非常相似。当有人说“打开终端”时，他们的意思是启动终端模拟器，这会启动一个 shell 会话，你可以在其中输入命令。

以下是你每天都会用到的命令。`pwd` 打印当前目录——即你此刻在文件系统中的位置。`ls` 列出当前目录中的文件（`ls -la` 显示隐藏文件和详细信息）。`cd` 切换目录（`cd /var/log` 带你进入日志目录，`cd ..` 向上一级）。`mkdir` 创建目录。`rm` 删除文件（`rm -r` 删除目录——小心，没有回收站）。`cp` 复制文件，`mv` 移动或重命名文件。`cat` 将文件内容打印到屏幕上。`echo` 打印文本。`grep` 在文本中搜索模式——这个命令极其强大，你会经常使用它。

终端真正强大的地方在于**组合**。你可以使用**管道**（`|`）将命令串联起来。例如，`cat /var/log/syslog | grep "error" | wc -l` 读取系统日志，筛选出包含“error”的行，并统计它们的数量。这就是三个工具在一行中协同工作。试试用 GUI 做到这一点。你还可以使用 `>`（覆盖）和 `>>`（追加）将输出重定向到文件。这种可组合性正是 Unix 哲学“做好一件事”如此有效的原因——小而专注的工具组合成强大的工作流。

对于 SRE 工作来说，终端是你将花费大部分时间的地方。你会用它通过 SSH 登录远程服务器、检查日志、使用 `top` 或 `htop` 检查系统资源使用情况、使用 `systemctl` 管理服务、安装软件包、配置防火墙、运行部署脚本，以及与 Docker、Kubernetes、Terraform 和 Git 等工具交互。这些工具中的每一个都是命令行优先的。其中一些有 GUI，但 CLI 总是更强大且更易于脚本化。

一个实用建议：现在就开始建立肌肉记忆。强迫自己用终端完成你通常会用 GUI 完成的任务。需要创建一个包含一些文件的项目文件夹？用 `mkdir` 和 `touch` 来做。想找一个文件？使用 `find` 或 `locate`，而不是 Spotlight 或 Windows Search。第一周会感觉很慢，但一个月内就会变得自然，几个月后你会想没有它你是怎么活过来的。

不要担心记住所有东西。`man` 命令（manual 的缩写）是你内置的参考——`man ls` 会显示 `ls` 命令的每个选项。你也可以对大多数命令使用 `--help`。学会阅读文档本身就是一项必不可少的 SRE 技能。

<!-- ZH_RESOURCES -->
- [Linux 命令行基础 - Ubuntu 教程](https://ubuntu.com/tutorials/command-line-for-beginners) -- 类型：教程，时长：1 小时
- [The Linux Command Line（William Shotts 免费书籍）](https://linuxcommand.org/tlcl.php) -- 类型：书籍，时长：不定
- [MIT Missing Semester - The Shell](https://missing.csail.mit.edu/2020/course-shell/) -- 类型：课程，时长：1 小时
- [Explain Shell - 粘贴命令即可获得解释](https://explainshell.com/) -- 类型：工具，时长：5 分钟
- [OverTheWire: Bandit - 通过游戏学习 CLI](https://overthewire.org/wargames/bandit/) -- 类型：练习，时长：5 小时

<!-- ZH_UI -->
1. 仅使用终端浏览文件系统
2. 运行 10 个基础命令（ls、cd、pwd、mkdir、rm、cp、mv、cat、echo、grep）
3. 我运行了一条命令。实际发生了什么？
4. 我输入了一条命令，它运行了。但实际发生了什么？我看到它出现在进程列表里，我可以杀掉它，它有一个 PID——但我完全不明白这些底层意味着什么。我运行那条命令时，到底创建了什么？
5. 我能运行命令了。如何把它们组合起来？
6. 我总是先运行一条命令，记下结果，再用那个结果运行下一条命令。一定有办法把一条命令的输出直接喂给另一条命令，省去中间那些手动步骤。而且有时候我还想把输出保存到文件——这些到底怎么运作？
7. 我需要编写和编辑文件。该用什么工具？
8. 我总是得在服务器上编辑文件，却完全不知道该用什么打开它们。我试过一次 vim，连怎么退出都搞不明白。有没有靠谱的方法来应对这件事？
9. 我有了一个 shell——我实际需要知道哪些命令？
10. 我能打开终端，但除了 cd 和 ls 就不知道输入什么了。我到处看到 ps、df、find、kill 这些命令被提到，却完全不知道什么时候该用哪个。要在 Linux 服务器上生存下去，我实际需要哪些命令？
