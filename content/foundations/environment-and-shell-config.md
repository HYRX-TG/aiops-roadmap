---
id: environment-and-shell-config
title: Environment Variables & Shell Config
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: My environment is set up. Now let me automate things.
      detail: >-
        I keep repeating the same sequences of commands — finding the right
        flags, piping the right outputs, doing the same thing over and over.
        There must be a way to capture these workflows and run them with a
        single command. What does it take to actually write a script instead of
        just typing commands one by one?
difficulty: 1
tags:
  - environment-variables
  - PATH
  - bashrc
  - profile
  - export
  - shell-config
  - dotfiles
category: concept
milestones:
  - Explain what PATH is and how the shell finds commands
  - Set and export environment variables
  - Understand the difference between .bashrc and .profile
title_zh: "环境变量与 Shell 配置"
---


You type `python3` and it runs. But how does your shell know where `python3` lives? You set `DATABASE_URL` in your terminal and your application connects to the right database. But how does the application read that value? The answer is **environment variables** — key-value pairs that the OS passes to every process, controlling everything from which programs are available to how applications behave. And the shell configuration files that set these variables are the reason "it works on my machine" is such a common problem.

<!-- DEEP_DIVE -->

**Environment variables** are key-value pairs that exist in every process's environment. When a process is created (via fork/exec), it inherits a copy of its parent's environment. Run `env` to see all your current environment variables — there will be dozens. The most important ones:

- **PATH** — a colon-separated list of directories where the shell looks for commands. When you type `ls`, the shell searches each directory in PATH (like `/usr/local/bin`, `/usr/bin`, `/bin`) until it finds an executable named `ls`. If a command is "not found," it is almost always a PATH issue. `echo $PATH` shows your current PATH. `which python3` tells you exactly which `python3` the shell would run.
- **HOME** — your home directory (`/home/username` on Linux, `/Users/username` on macOS). The `~` shortcut in paths refers to this.
- **USER** — your username.
- **SHELL** — the path to your default shell (`/bin/bash`, `/bin/zsh`).
- **EDITOR** — the default text editor for commands that need one (like `git commit` without `-m`).
- **LANG / LC_ALL** — locale settings that control language, date formats, and character encoding.

Applications use environment variables extensively for configuration. A database connection string in `DATABASE_URL`, an API key in `API_KEY`, a feature flag in `DEBUG=true` — this pattern is everywhere in modern infrastructure. The Twelve-Factor App methodology explicitly recommends environment variables for configuration because they are language-agnostic and easy to change between environments (dev, staging, production) without modifying code.

**Setting environment variables.** `MY_VAR=hello` sets a variable in the current shell only — child processes will not see it. `export MY_VAR=hello` exports it so that all child processes inherit it. This distinction trips people up constantly. If you set `JAVA_HOME=/usr/lib/jvm/java-17` without `export`, your Java application will not see it because it runs as a child process of the shell.

**Shell configuration files.** These files run automatically when you start a shell, and they are where you put environment variables, aliases, and customizations that you want every time:

- **`~/.bashrc`** — runs every time you open a new interactive Bash shell. This is where most people put their customizations: aliases (`alias ll='ls -la'`), PATH modifications, prompt customization.
- **`~/.bash_profile`** or **`~/.profile`** — runs once when you log in (a "login shell"). SSH sessions are login shells. Opening a new terminal tab on your laptop might or might not be a login shell depending on your terminal emulator.
- **`~/.zshrc`** — the equivalent of `.bashrc` for Zsh (the default shell on macOS).

The login-vs-interactive distinction causes real problems. You add `export PATH=$PATH:/opt/myapp/bin` to `.bashrc`, and it works in your terminal. But a cron job runs in a non-interactive, non-login shell, so it does not source `.bashrc`, and your command is "not found." Understanding which config file runs when saves you from these maddening bugs.

**Common SRE scenarios where this matters:**

- A deployment script fails because the `PATH` on the server does not include the directory where your tool is installed.
- An application cannot connect to the database because the `DATABASE_URL` environment variable is set in the user's shell but not in the systemd service file (systemd services do not inherit your shell environment).
- CI/CD pipelines behave differently from local development because the environment variables are different.
- You SSH into a server and your aliases are gone because the server has a vanilla `.bashrc`.

A practical exercise: check your `PATH` with `echo $PATH`, then use `which` to find where common commands live. Add a directory to your PATH in `.bashrc`, open a new terminal, and verify it works. Then set an environment variable without `export` and try to access it from a child process (`bash -c 'echo $MY_VAR'`) — notice it is empty. Then export it and try again.

<!-- RESOURCES -->

- [Environment Variables in Linux - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-read-and-set-environmental-and-shell-variables-on-linux) -- type: tutorial, time: 25m
- [Bash Startup Files Explained - GNU Manual](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html) -- type: reference, time: 15m
- [The Twelve-Factor App - Config](https://12factor.net/config) -- type: article, time: 10m
- [Understanding PATH - Linux Handbook](https://linuxhandbook.com/path-variable/) -- type: tutorial, time: 15m
- [Dotfiles Guide - GitHub](https://dotfiles.github.io/) -- type: reference, time: 30m

<!-- ZH_SUMMARY -->
你输入 `python3`，它就能运行。但你的 shell 是如何知道 `python3` 在哪里？你在终端里设置了 `DATABASE_URL`，你的应用就连接到了正确的数据库。但应用是如何读取那个值的？答案是**环境变量**——操作系统传递给每个进程的键值对，控制着从哪些程序可用到应用如何行为的一切。而设置这些变量的 shell 配置文件，正是“在我机器上能跑”成为如此常见问题的原因。

<!-- ZH_DEEP_DIVE -->
**环境变量**是存在于每个进程环境中的键值对。当进程被创建时（通过 fork/exec），它会继承父进程环境的一份副本。运行 `env` 可以查看当前所有的环境变量——通常会有几十个。其中最重要的几个：

- **PATH** —— 一个以冒号分隔的目录列表，shell 会在这些目录中查找命令。当你输入 `ls` 时，shell 会依次搜索 PATH 中的每个目录（如 `/usr/local/bin`、`/usr/bin`、`/bin`），直到找到名为 `ls` 的可执行文件。如果某个命令“找不到”，几乎总是 PATH 的问题。`echo $PATH` 显示当前的 PATH。`which python3` 会告诉你 shell 实际会运行哪个 `python3`。
- **HOME** —— 你的主目录（Linux 上是 `/home/username`，macOS 上是 `/Users/username`）。路径中的 `~` 快捷方式指的就是它。
- **USER** —— 你的用户名。
- **SHELL** —— 默认 shell 的路径（`/bin/bash`、`/bin/zsh`）。
- **EDITOR** —— 需要编辑器时命令使用的默认文本编辑器（比如不带 `-m` 的 `git commit`）。
- **LANG / LC_ALL** —— 控制语言、日期格式和字符编码的区域设置。

应用程序广泛使用环境变量进行配置。`DATABASE_URL` 中的数据库连接字符串、`API_KEY` 中的 API 密钥、`DEBUG=true` 中的功能开关——这种模式在现代基础设施中随处可见。Twelve-Factor App 方法论明确推荐使用环境变量进行配置，因为它们与语言无关，并且可以轻松地在不同环境（开发、预发布、生产）之间切换而无需修改代码。

**设置环境变量。** `MY_VAR=hello` 只在当前 shell 中设置变量——子进程看不到它。`export MY_VAR=hello` 会将其导出，使所有子进程都能继承它。这个区别经常让人栽跟头。如果你设置 `JAVA_HOME=/usr/lib/jvm/java-17` 而没有 `export`，你的 Java 应用将看不到它，因为它是作为 shell 的子进程运行的。

**Shell 配置文件。** 这些文件在你启动 shell 时自动运行，你可以在这里放置希望每次都生效的环境变量、别名和自定义配置：

- **`~/.bashrc`** —— 每次打开新的交互式 Bash shell 时运行。大多数人在这里放置自定义配置：别名（`alias ll='ls -la'`）、PATH 修改、提示符定制。
- **`~/.bash_profile`** 或 **`~/.profile`** —— 在登录时（“登录 shell”）运行一次。SSH 会话就是登录 shell。在你的笔记本上打开新的终端标签页是否是登录 shell，取决于你的终端模拟器。
- **`~/.zshrc`** —— Zsh（macOS 上的默认 shell）中相当于 `.bashrc` 的文件。

登录 shell 与交互式 shell 的区别会引发实际问题。你在 `.bashrc` 中添加了 `export PATH=$PATH:/opt/myapp/bin`，它在你的终端中工作正常。但 cron 任务运行在非交互、非登录的 shell 中，因此不会加载 `.bashrc`，你的命令就会“找不到”。理解哪个配置文件在何时运行，能让你避免这些令人抓狂的 bug。

**与此相关的常见 SRE 场景：**

- 部署脚本失败，因为服务器上的 `PATH` 不包含你的工具所在的目录。
- 应用无法连接数据库，因为 `DATABASE_URL` 环境变量设置在用户的 shell 中，但没有设置在 systemd 服务文件中（systemd 服务不会继承你的 shell 环境）。
- CI/CD 流水线的行为与本地开发不同，因为环境变量不同。
- 你 SSH 登录到服务器后发现别名都没了，因为服务器使用的是原版 `.bashrc`。

一个实践练习：用 `echo $PATH` 检查你的 `PATH`，然后用 `which` 找出常用命令所在的位置。在 `.bashrc` 中向 PATH 添加一个目录，打开新终端，验证它是否生效。然后设置一个不带 `export` 的环境变量，尝试从子进程中访问它（`bash -c 'echo $MY_VAR'`）——注意它是空的。然后导出它再试一次。

<!-- ZH_RESOURCES -->
- [Linux 中的环境变量 - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-read-and-set-environmental-and-shell-variables-on-linux) -- 类型：教程，时长：25 分钟
- [Bash 启动文件详解 - GNU 手册](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html) -- 类型：参考，时长：15 分钟
- [十二要素应用 - 配置](https://12factor.net/config) -- 类型：文章，时长：10 分钟
- [理解 PATH - Linux Handbook](https://linuxhandbook.com/path-variable/) -- 类型：教程，时长：15 分钟
- [Dotfiles 指南 - GitHub](https://dotfiles.github.io/) -- 类型：参考，时长：30 分钟

<!-- ZH_UI -->
1. 解释什么是 PATH 以及 shell 如何查找命令
2. 设置并导出环境变量
3. 理解 .bashrc 与 .profile 的区别
4. 我的环境已配置好，现在让我来把事情自动化。
5. 我总在重复相同的命令序列——找正确的参数、管道接上正确的输出、一遍又一遍做同样的事。一定有办法把这些工作流记录下来，用一条命令就能运行。要真正写出脚本、而不是一条条敲命令，需要做些什么？
