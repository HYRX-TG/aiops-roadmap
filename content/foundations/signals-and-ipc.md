---
id: signals-and-ipc
title: Signals & Inter-Process Communication
zone: foundations
edges:
  to:
    - id: systemd-and-services
      question: I know how processes communicate. Who manages all the services?
      detail: >-
        I understand how to send signals to individual processes. But on a real
        server there are dozens of services — they all need to start when the
        machine boots, restart if they crash, and shut down gracefully. How does
        any of that happen automatically? Someone or something must be managing
        all of it.
difficulty: 1
tags:
  - signals
  - ipc
  - sigterm
  - sigkill
  - sighup
  - pipes
  - sockets
  - kill
category: concept
milestones:
  - Explain the difference between SIGTERM and SIGKILL
  - Send signals to a process using kill and understand what happens
  - Explain what happens when you press Ctrl+C in a terminal
title_zh: "信号与进程间通信"

---


You press Ctrl+C and a running program stops. But how? Your terminal did not just yank the program out of existence — it sent a **signal**, a small message from the OS to the process saying "please stop." Signals are one of the oldest and most fundamental ways processes communicate on Linux. They are how you gracefully shut down services, reload configurations without downtime, and handle the unexpected. And as an SRE, you will send and reason about signals constantly.

<!-- DEEP_DIVE -->

A **signal** is a software interrupt delivered to a process. The OS sends it, and the process can either handle it (run custom code in response), ignore it, or let the default behavior happen (which is usually to terminate). Signals are identified by numbers, but you will always use their names. Here are the ones you need to know:

- **SIGTERM (15)** — "Please terminate gracefully." This is the default signal sent by the `kill` command. Well-written programs catch SIGTERM and use it to clean up: close database connections, finish writing files, flush logs, then exit. This is the polite way to stop a process.
- **SIGKILL (9)** — "Die. Now." Cannot be caught, cannot be ignored, cannot be handled. The kernel immediately terminates the process. Use this only as a last resort because the process gets no chance to clean up — open files might be corrupted, connections might be left hanging, temporary files might not be deleted. `kill -9 <PID>` is the command.
- **SIGINT (2)** — "Interrupt." This is what Ctrl+C sends. Similar to SIGTERM but conventionally used for interactive interruption. Programs can catch it to clean up or ask "are you sure?"
- **SIGHUP (1)** — "Hangup." Originally meant the terminal disconnected. Today, many daemons (like Nginx and Apache) catch SIGHUP to mean "reload your configuration file without restarting." This is incredibly useful — `kill -HUP <PID>` reloads the config without dropping any active connections.
- **SIGSTOP / SIGCONT** — Pause and resume a process. SIGSTOP cannot be caught (the process freezes immediately). SIGCONT unfreezes it. Ctrl+Z in a terminal sends SIGTSTP (the catchable version of SIGSTOP). This is what happens when you "background" a process.
- **SIGCHLD** — Sent to a parent when a child process exits. This is how the parent knows to clean up the child's entry in the process table. If the parent never handles SIGCHLD, the dead child becomes a zombie.

**The `kill` command** is misnamed — it does not always kill. It sends signals. `kill <PID>` sends SIGTERM. `kill -9 <PID>` sends SIGKILL. `kill -HUP <PID>` sends SIGHUP. `killall nginx` sends SIGTERM to all processes named nginx. `pkill -f "java.*myapp"` sends SIGTERM to processes matching a pattern — very useful when you need to find and signal a process by its full command line.

**Why graceful shutdown matters.** Imagine a web server handling requests. You need to deploy a new version, so you need to stop the old one. If you SIGKILL it, every in-flight request gets dropped — users see errors. If you SIGTERM it, a well-written server stops accepting new connections, finishes handling the ones in progress, then exits cleanly. This is called **graceful shutdown**, and it is the difference between zero-downtime deployments and angry users. Kubernetes sends SIGTERM to pods during rolling updates, waits a configurable grace period, and only sends SIGKILL if the process has not exited by then. Understanding this lifecycle is essential for running reliable services.

**Beyond signals: other IPC mechanisms.** Signals are limited — they are just notifications, they cannot carry data. For richer communication, Linux provides:

- **Pipes** — `|` in the shell. The output of one process becomes the input of another. `cat log.txt | grep error` creates two processes connected by a pipe.
- **Unix domain sockets** — like network sockets, but for processes on the same machine. Much faster than TCP. Docker communicates with its daemon through `/var/run/docker.sock`.
- **Shared memory** — two processes map the same chunk of memory. Fastest IPC method, but requires careful synchronization.

For SRE work, signals are by far the most important IPC mechanism to master. You will use them daily to manage services, debug stuck processes, and implement graceful deployments.

<!-- RESOURCES -->

- [Linux Signals Explained - freeCodeCamp](https://www.freecodecamp.org/news/linux-signals-fundamentals/) -- type: tutorial, time: 20m
- [Signal Handling in Linux - Red Hat](https://www.redhat.com/sysadmin/linux-signal-handling) -- type: article, time: 20m
- [Graceful Shutdown Patterns](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-termination-grace-period) -- type: article, time: 15m
- [Inter-Process Communication in Linux - GeeksforGeeks](https://www.geeksforgeeks.org/inter-process-communication-ipc/) -- type: tutorial, time: 30m
- [The kill Command - Linux man page](https://man7.org/linux/man-pages/man1/kill.1.html) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
你按下 Ctrl+C，一个正在运行的程序就停止了。但这是怎么做到的？你的终端并没有直接把程序从存在中抹去——它发送了一个**信号**，这是操作系统发给进程的一条小消息，意思是“请停止”。信号是 Linux 上进程间通信最古老、最基础的方式之一。你正是通过信号来优雅地关闭服务、在不中断的情况下重新加载配置，以及处理意外情况。而作为一名 SRE，你会不断地发送信号并对其进行分析推理。

<!-- ZH_DEEP_DIVE -->
**信号**是发送给进程的软件中断。操作系统发送信号，进程可以处理它（执行自定义代码作为响应）、忽略它，或者让默认行为发生（通常是终止进程）。信号通过数字标识，但你始终会使用它们的名称。以下是你需要了解的信号：

- **SIGTERM (15)** — “请优雅地终止。”这是 `kill` 命令发送的默认信号。编写良好的程序会捕获 SIGTERM 并用它来清理：关闭数据库连接、完成文件写入、刷新日志，然后退出。这是停止进程的礼貌方式。
- **SIGKILL (9)** — “立即死掉。”无法捕获、无法忽略、无法处理。内核会立即终止进程。仅将此作为最后手段使用，因为进程没有机会清理——打开的文件可能损坏、连接可能挂起、临时文件可能未被删除。命令是 `kill -9 <PID>`。
- **SIGINT (2)** — “中断。”这是 Ctrl+C 发送的信号。类似于 SIGTERM，但惯例上用于交互式中断。程序可以捕获它来清理或询问“你确定吗？”
- **SIGHUP (1)** — “挂断。”最初指终端断开连接。如今，许多守护进程（如 Nginx 和 Apache）捕获 SIGHUP 来表示“重新加载配置文件而不重启”。这非常有用——`kill -HUP <PID>` 重新加载配置而不丢弃任何活动连接。
- **SIGSTOP / SIGCONT** — 暂停和恢复进程。SIGSTOP 无法被捕获（进程立即冻结）。SIGCONT 解冻它。终端中的 Ctrl+Z 发送 SIGTSTP（SIGSTOP 的可捕获版本）。这就是你将进程“放到后台”时发生的情况。
- **SIGCHLD** — 子进程退出时发送给父进程。父进程借此知道要清理进程表中的子进程条目。如果父进程从不处理 SIGCHLD，死掉的子进程就会变成僵尸进程。

**`kill` 命令**名称有误——它并不总是杀死进程。它发送信号。`kill <PID>` 发送 SIGTERM。`kill -9 <PID>` 发送 SIGKILL。`kill -HUP <PID>` 发送 SIGHUP。`killall nginx` 向所有名为 nginx 的进程发送 SIGTERM。`pkill -f "java.*myapp"` 向匹配模式的进程发送 SIGTERM——当你需要按完整命令行查找并发送信号给进程时非常有用。

**为什么优雅关闭很重要。** 想象一个处理请求的 Web 服务器。你需要部署新版本，因此需要停止旧版本。如果你用 SIGKILL 杀死它，每个进行中的请求都会被丢弃——用户会看到错误。如果你用 SIGTERM，编写良好的服务器会停止接受新连接，完成正在处理的请求，然后干净地退出。这称为**优雅关闭**，它是零停机部署与愤怒用户之间的区别。Kubernetes 在滚动更新期间向 Pod 发送 SIGTERM，等待可配置的宽限期，只有在进程届时仍未退出时才发送 SIGKILL。理解这一生命周期对于运行可靠的服务至关重要。

**信号之外：其他 IPC 机制。** 信号是有限的——它们只是通知，不能携带数据。对于更丰富的通信，Linux 提供：

- **管道** — shell 中的 `|`。一个进程的输出成为另一个进程的输入。`cat log.txt | grep error` 创建两个由管道连接的进程。
- **Unix 域套接字** — 类似网络套接字，但用于同一台机器上的进程。比 TCP 快得多。Docker 通过 `/var/run/docker.sock` 与其守护进程通信。
- **共享内存** — 两个进程映射同一块内存。最快的 IPC 方法，但需要仔细同步。

对于 SRE 工作，信号是迄今为止最需要掌握的 IPC 机制。你将每天使用它们来管理服务、调试卡住的进程以及实现优雅部署。

<!-- ZH_RESOURCES -->
- [Linux 信号详解 - freeCodeCamp](https://www.freecodecamp.org/news/linux-signals-fundamentals/) -- 类型: 教程, 时长: 20m
- [Linux 中的信号处理 - Red Hat](https://www.redhat.com/sysadmin/linux-signal-handling) -- 类型: 文章, 时长: 20m
- [优雅关闭模式](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-termination-grace-period) -- 类型: 文章, 时长: 15m
- [Linux 中的进程间通信 - GeeksforGeeks](https://www.geeksforgeeks.org/inter-process-communication-ipc/) -- 类型: 教程, 时长: 30m
- [kill 命令 - Linux man 手册页](https://man7.org/linux/man-pages/man1/kill.1.html) -- 类型: 参考, 时长: 10m

<!-- ZH_UI -->
1. 解释 SIGTERM 和 SIGKILL 的区别
2. 使用 kill 向进程发送信号并理解会发生什么
3. 解释在终端中按下 Ctrl+C 时会发生什么
4. 我知道进程如何通信。谁管理所有服务？
5. 我理解如何向单个进程发送信号。但在真实服务器上有几十个服务——它们都需要在机器启动时启动、崩溃时重启、优雅关闭。这些如何自动发生？肯定有某个东西在管理这一切。
