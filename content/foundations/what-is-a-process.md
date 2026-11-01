---
id: what-is-a-process
title: What Is a Process?
zone: foundations
edges:
  to:
    - id: threads-and-concurrency
      question: A process runs code. But what if it needs to do many things at once?
      detail: >-
        My app handles one request and then starts the next one. But a real web
        server must be handling thousands at once — it can't just make everyone
        wait in line. How does a single process do many things simultaneously?
        Is it running multiple copies of itself, or something else entirely?
    - id: signals-and-ipc
      question: Processes are running. How do they talk to each other?
      detail: >-
        I press Ctrl+C and something stops. I run kill and something dies. But
        how does one process actually tell another to do something? And what's
        the difference between a process just stopping and it being told to
        stop? I feel like I'm missing how processes actually communicate with
        each other.
    - id: processes-and-memory
      question: A process is running. How does it use memory?
      detail: >-
        I can see a process running in ps — but I have no idea what's actually
        happening in memory. Processes clearly need RAM, but I don't understand
        how they get it, what happens when they need more, or why some of them
        seem to just keep eating memory forever.
difficulty: 1
tags:
  - process
  - fork
  - exec
  - pid
  - process-tree
  - proc-filesystem
  - ps
  - strace
category: concept
milestones:
  - Explain what fork and exec do
  - Use ps and pstree to inspect the process tree
  - Explore /proc to read live process information
  - Use strace to watch a process make system calls
title_zh: "什么是进程？"

---


When you type `ls` in your terminal and press Enter, a surprisingly complex chain of events unfolds. Your shell does not just "run ls." It creates an entirely new process — a copy of itself — and then replaces that copy with the `ls` program. That new process gets its own memory, its own process ID, and a place in a tree of processes that stretches all the way back to the very first process that started when your system booted. Understanding this is understanding how Linux actually works.

<!-- DEEP_DIVE -->

A **process** is a running instance of a program. The program itself is just a file on disk — `/usr/bin/ls`, `/usr/bin/python3`, `/usr/sbin/nginx`. When you execute that file, the kernel creates a process: it allocates memory, assigns a **PID** (Process ID), sets up the process's environment, and starts executing the program's instructions. The program is the recipe; the process is the cake being baked.

**How a process is born: fork and exec.** On Linux, new processes are created through a two-step mechanism that is elegant but initially confusing. First, the existing process (your shell) calls `fork()`, which creates an exact copy of itself — same code, same memory, same everything, but with a new PID. Now there are two identical processes: the parent (your shell) and the child (the copy). Then the child calls `exec()`, which replaces its entire memory and code with a new program (like `ls`). The child process is now running `ls`, not a copy of your shell.

This fork-exec model is everywhere in Linux. When your shell runs a command, it forks and execs. When a web server spawns a worker process, it forks. When `systemd` starts a service, it forks and execs. You can observe this yourself — run `strace -f bash -c "ls"` and you will see the `clone()` system call (the modern version of fork) followed by `execve()`.

**The process tree.** Every process has a parent, and that parent has a parent, all the way up to PID 1 — the **init process** (usually `systemd` on modern Linux). This creates a tree structure. Run `pstree` to see it. Your terminal emulator started a shell, that shell started your command, and so on. This parent-child relationship matters because when a parent process dies, its children become **orphans** and get adopted by PID 1. And when a child process exits but its parent has not yet acknowledged the exit, it becomes a **zombie** — a process that is technically dead but still has an entry in the process table. A few zombies are harmless; thousands of them mean something is broken.

**Inspecting processes.** The `ps` command is your primary tool. `ps aux` shows every process on the system with its PID, user, CPU usage, memory usage, and the command that started it. `ps -ef` shows similar information with the parent PID (PPID), which lets you trace the parent-child chain. `pstree -p` gives you a visual tree with PIDs. For a live, updating view, use `top` or `htop`.

**The /proc filesystem.** Linux exposes process information through a virtual filesystem at `/proc`. Every running process has a directory at `/proc/<PID>/`. Inside you will find:

- `/proc/<PID>/status` — process state, memory usage, owner
- `/proc/<PID>/cmdline` — the full command that started the process
- `/proc/<PID>/fd/` — all open file descriptors (files, sockets, pipes the process has open)
- `/proc/<PID>/environ` — the environment variables the process was started with

This is not just trivia — when you are debugging a production issue and need to know what a running process is actually doing, `/proc` gives you live data without stopping the process. Tools like `ps` and `top` are actually just reading from `/proc` under the hood.

**strace: watching a process in real time.** `strace` attaches to a process and shows you every system call it makes — every file it opens, every network connection it creates, every byte it reads or writes. Run `strace ls` and you will see dozens of system calls: `openat()` opening directories, `getdents()` reading directory entries, `write()` printing output. When a program is failing mysteriously — hanging, crashing, producing wrong output — `strace` often reveals exactly why. It is one of the most powerful debugging tools in an SRE's arsenal. `strace -p <PID>` attaches to an already-running process.

<!-- RESOURCES -->

- [The /proc Filesystem - Linux Documentation Project](https://tldp.org/LDP/Linux-Filesystem-Hierarchy/html/proc.html) -- type: reference, time: 30m
- [strace - The Definitive Guide (Julia Evans)](https://jvns.ca/blog/2015/04/14/strace-zine/) -- type: article, time: 20m
- [How Linux Creates Processes (fork and exec)](https://www.youtube.com/watch?v=PZrQ4eGm-hM) -- type: video, time: 15m
- [Process Management in Linux - GeeksforGeeks](https://www.geeksforgeeks.org/process-management-in-linux/) -- type: tutorial, time: 25m
- [pstree and Process Hierarchy - Red Hat](https://www.redhat.com/sysadmin/linux-process-management) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
当你在终端中输入 `ls` 并按下回车键时，一系列复杂得令人惊讶的事件会依次展开。你的 shell 并不只是“运行 ls”。它会创建一个全新的进程——它自身的一个副本——然后用 `ls` 程序替换掉这个副本。这个新进程拥有自己的内存、自己的进程 ID，并在一个进程树中占据一席之地，而这棵进程树一直向上追溯到系统启动时启动的第一个进程。理解这一点，就是理解 Linux 实际是如何工作的。

<!-- ZH_DEEP_DIVE -->
**进程**是程序的运行实例。程序本身只是磁盘上的一个文件——`/usr/bin/ls`、`/usr/bin/python3`、`/usr/sbin/nginx`。当你执行该文件时，内核会创建一个进程：它分配内存、分配一个 **PID**（进程 ID）、设置进程的环境，并开始执行程序的指令。程序是菜谱；进程是正在烤制的蛋糕。

**进程如何诞生：fork 和 exec。** 在 Linux 上，新进程通过一个优雅但初看令人困惑的两步机制创建。首先，现有进程（你的 shell）调用 `fork()`，它会创建一个自身的精确副本——相同的代码、相同的内存、相同的一切，但拥有新的 PID。现在有两个完全相同的进程：父进程（你的 shell）和子进程（副本）。然后子进程调用 `exec()`，它会用新程序（如 `ls`）替换其全部内存和代码。子进程现在运行的是 `ls`，而不是你 shell 的副本。

这种 fork-exec 模型在 Linux 中无处不在。当你的 shell 运行命令时，它会 fork 并 exec。当 Web 服务器派生一个工作进程时，它会 fork。当 `systemd` 启动一个服务时，它会 fork 并 exec。你可以自己观察——运行 `strace -f bash -c "ls"`，你会看到 `clone()` 系统调用（fork 的现代版本）后跟 `execve()`。

**进程树。** 每个进程都有一个父进程，那个父进程也有一个父进程，一直向上到 PID 1——**init 进程**（在现代 Linux 上通常是 `systemd`）。这形成了一种树形结构。运行 `pstree` 即可看到。你的终端模拟器启动了一个 shell，那个 shell 启动了你的命令，依此类推。这种父子关系很重要，因为当父进程死亡时，其子进程会成为**孤儿**，并被 PID 1 收养。而当子进程退出但其父进程尚未确认退出时，它就会变成**僵尸**——一个技术上已死亡但仍在进程表中保留条目的进程。少量僵尸无害；成千上万个则意味着出了问题。

**检查进程。** `ps` 命令是你的主要工具。`ps aux` 显示系统上的每个进程及其 PID、用户、CPU 使用率、内存使用率以及启动它的命令。`ps -ef` 显示类似信息，但包含父 PID（PPID），让你可以追踪父子链。`pstree -p` 为你提供带 PID 的可视化树。对于实时更新的视图，请使用 `top` 或 `htop`。

**/proc 文件系统。** Linux 通过 `/proc` 处的虚拟文件系统暴露进程信息。每个运行中的进程在 `/proc/<PID>/` 处都有一个目录。在其中你会找到：

- `/proc/<PID>/status` — 进程状态、内存使用、所有者
- `/proc/<PID>/cmdline` — 启动该进程的完整命令
- `/proc/<PID>/fd/` — 所有打开的文件描述符（进程打开的文件、套接字、管道）
- `/proc/<PID>/environ` — 启动该进程时使用的环境变量

这不仅仅是冷知识——当你调试生产问题并需要知道运行中的进程实际在做什么时，`/proc` 可以在不停止进程的情况下为你提供实时数据。`ps` 和 `top` 等工具实际上只是在底层读取 `/proc`。

**strace：实时观察进程。** `strace` 附加到一个进程并显示它进行的每个系统调用——它打开的每个文件、创建的每个网络连接、读取或写入的每个字节。运行 `strace ls`，你会看到几十个系统调用：`openat()` 打开目录、`getdents()` 读取目录条目、`write()` 打印输出。当程序神秘地失败时——挂起、崩溃、产生错误输出——`strace` 通常能准确揭示原因。它是 SRE 武器库中最强大的调试工具之一。`strace -p <PID>` 附加到一个已经在运行的进程。

<!-- ZH_RESOURCES -->
- [/proc 文件系统 - Linux 文档项目](https://tldp.org/LDP/Linux-Filesystem-Hierarchy/html/proc.html) -- 类型: 参考, 时间: 30m
- [strace - 权威指南 (Julia Evans)](https://jvns.ca/blog/2015/04/14/strace-zine/) -- 类型: 文章, 时间: 20m
- [Linux 如何创建进程 (fork 和 exec)](https://www.youtube.com/watch?v=PZrQ4eGm-hM) -- 类型: 视频, 时间: 15m
- [Linux 中的进程管理 - GeeksforGeeks](https://www.geeksforgeeks.org/process-management-in-linux/) -- 类型: 教程, 时间: 25m
- [pstree 与进程层级 - Red Hat](https://www.redhat.com/sysadmin/linux-process-management) -- 类型: 文章, 时间: 15m

<!-- ZH_UI -->
1. 解释 fork 和 exec 的作用
2. 使用 ps 和 pstree 查看进程树
3. 探索 /proc 读取实时进程信息
4. 使用 strace 观察进程发起的系统调用
5. 进程运行代码。但如果它需要同时做很多事情呢？
6. 我的应用处理完一个请求再开始下一个。但真正的 Web 服务器必须同时处理成千上万个请求——它不可能让所有人排队等待。单个进程如何同时做多件事？是运行自身的多个副本，还是完全不同的机制？
7. 进程在运行。它们之间如何通信？
8. 我按下 Ctrl+C，某个东西就停了。我执行 kill，某个东西就死了。但一个进程究竟如何告诉另一个进程去做某事？进程自己停下来和被通知停下来有什么区别？我觉得自己没搞懂进程之间到底如何通信。
9. 进程在运行。它如何使用内存？
10. 我能在 ps 里看到进程在运行——但我完全不知道内存里实际发生了什么。进程显然需要 RAM，但我不理解它们如何获得内存、需要更多内存时会发生什么，或者为什么有些进程似乎一直在吃内存。
