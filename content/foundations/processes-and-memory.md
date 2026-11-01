---
id: processes-and-memory
title: Processes & Memory
zone: foundations
edges:
  to:
    - id: programming-fundamentals
      question: >-
        I understand how the computer runs things. Now how do I write real
        programs?
      detail: >-
        I can watch processes and poke at memory usage. But whenever I need to
        automate something or write a script, I get stuck — I don't have a solid
        grasp of even the basics like loops and functions. How do I actually
        build that foundation?
difficulty: 1
tags:
  - processes
  - memory
  - ram
  - pid
  - linux
  - system-resources
category: concept
milestones:
  - Use ps and top to inspect running processes
  - Explain the difference between RAM and disk storage
  - Kill a process from the terminal
title_zh: "进程与内存"

---


Every program you run on a computer becomes a **process** -- a living, breathing instance of that program with its own slice of memory, a unique ID, and a lifecycle that the operating system carefully manages. Understanding processes and memory is what separates someone who uses a computer from someone who can troubleshoot why it is slow, unresponsive, or eating all your RAM at 3 AM during an incident.

<!-- DEEP_DIVE -->

When you launch a program -- say you type `python my_script.py` -- the operating system does not just "run the file." It creates a process. That process gets a unique identifier called a **PID** (Process ID), its own chunk of memory to work in, and a spot in the OS scheduler's queue. You can see all running processes with the `ps` command. Try `ps aux` and you will get a wall of output showing every process on the system, who started it, how much CPU and memory it is using, and its PID. The `top` command (or the much friendlier `htop`, if you install it) gives you a live, updating view -- think of it as the task manager for the terminal.

Memory comes in two flavors that you need to understand: **RAM** (Random Access Memory) and **disk storage**. RAM is fast but temporary -- when your process runs, its variables, data structures, and active state all live in RAM. Disk storage is slow but permanent -- your files, your database, your photos all sit on disk. When your computer runs out of RAM, it starts using a section of the disk called **swap space** as overflow, and everything slows to a crawl. This is why a machine with 4 GB of RAM running thirty Chrome tabs feels like it is wading through mud.

Every process also has a **state**. It can be running (actively using the CPU), sleeping (waiting for something, like disk I/O or network data), stopped (paused), or zombie (finished but not yet cleaned up by its parent). When you run `top` and see a process using 99% CPU, that is a process stuck in the running state hogging resources. As an SRE, spotting this pattern is bread and butter -- you will do it constantly when debugging production issues.

Killing processes is a fundamental skill. The `kill` command sends a signal to a process. `kill 12345` sends SIGTERM (a polite "please shut down") to PID 12345. If the process ignores that, `kill -9 12345` sends SIGKILL (the OS forcibly terminates it, no questions asked). You can also use `killall python` to kill all processes with a given name. A word of caution: `kill -9` should be your last resort because it does not give the process a chance to clean up after itself -- open files might not get saved, database connections might not close properly.

Here is a practical exercise that ties it all together. Open two terminal windows. In the first, run `sleep 300` (this creates a process that does nothing for 300 seconds). In the second terminal, run `ps aux | grep sleep` to find it. Note the PID. Then run `kill <PID>` and watch the first terminal -- the sleep command will terminate. Now do it again, but this time use `top` or `htop` to find the process and kill it from there (press `k` in `top`, type the PID, and hit Enter). These are the exact same skills you will use when a runaway Java process is eating 32 GB of RAM in production.

Understanding the relationship between processes and memory is also the foundation for understanding containers, resource limits, and orchestration systems like Kubernetes. When you set a memory limit on a container and the process inside exceeds it, the OS kills that process with an OOM (Out of Memory) signal. Knowing why that happens, and how to investigate it, starts right here.

<!-- RESOURCES -->

- [Linux Process Management - DigitalOcean](https://www.digitalocean.com/community/tutorials/process-management-in-linux) -- type: tutorial, time: 30m
- [htop Explained - peteris.rocks](https://peteris.rocks/blog/htop/) -- type: article, time: 20m
- [How Linux Uses RAM - Linuxatemyram.com](https://www.linuxatemyram.com/) -- type: article, time: 10m
- [The Missing Semester - Shell Tools (MIT)](https://missing.csail.mit.edu/2020/command-line/) -- type: course, time: 1h
- [Linux Signals Fundamentals - freeCodeCamp](https://www.freecodecamp.org/news/linux-signals-fundamentals/) -- type: tutorial, time: 20m

<!-- ZH_SUMMARY -->
你在计算机上运行的每个程序都会成为一个**进程**——该程序的一个活生生的实例，拥有自己的一片内存、一个唯一 ID，以及由操作系统精心管理的生命周期。理解进程与内存，正是区分“只会用电脑的人”和“能在凌晨 3 点故障发生时排查电脑为何变慢、无响应或吃光内存的人”的关键。

<!-- ZH_DEEP_DIVE -->
当你启动一个程序——比如输入 `python my_script.py`——操作系统并不只是“运行这个文件”。它会创建一个进程。该进程会获得一个唯一标识符，称为 **PID**（进程 ID），拥有自己的一块内存空间用于工作，并在操作系统调度器的队列中占据一个位置。你可以用 `ps` 命令查看所有正在运行的进程。试试 `ps aux`，你会得到满屏的输出，显示系统上的每个进程、谁启动了它、它占用了多少 CPU 和内存，以及它的 PID。`top` 命令（或者更友好的 `htop`，如果你安装了的话）会给你一个实时更新的视图——可以把它看作终端里的任务管理器。

内存有两种你需要理解的类型：**RAM**（随机存取存储器）和**磁盘存储**。RAM 速度快但临时——当你的进程运行时，它的变量、数据结构和活动状态都存放在 RAM 中。磁盘存储速度慢但持久——你的文件、数据库、照片都存放在磁盘上。当计算机的 RAM 耗尽时，它会开始使用磁盘上的一块区域作为溢出空间，称为**交换空间**（swap space），然后一切都会慢如蜗牛。这就是为什么一台拥有 4 GB RAM 的机器运行三十个 Chrome 标签页时会感觉像在泥里跋涉。

每个进程还有一个**状态**。它可以是运行中（正在积极使用 CPU）、睡眠中（等待某些东西，比如磁盘 I/O 或网络数据）、已停止（暂停），或僵尸（已完成但尚未被其父进程清理）。当你运行 `top` 并看到一个进程占用 99% CPU 时，那是一个卡在运行状态、霸占资源的进程。作为 SRE，发现这种模式是家常便饭——你在调试生产问题时将不断这样做。

杀死进程是一项基本技能。`kill` 命令向进程发送信号。`kill 12345` 向 PID 12345 发送 SIGTERM（礼貌的“请关闭”）。如果进程忽略它，`kill -9 12345` 发送 SIGKILL（操作系统强制终止它，不容置疑）。你也可以使用 `killall python` 来杀死所有具有给定名称的进程。一句警告：`kill -9` 应该是你的最后手段，因为它不给进程清理自身的机会——打开的文件可能不会被保存，数据库连接可能无法正确关闭。

这里有一个将所有内容联系起来的实践练习。打开两个终端窗口。在第一个中，运行 `sleep 300`（这会创建一个在 300 秒内什么都不做的进程）。在第二个终端中，运行 `ps aux | grep sleep` 来找到它。记下 PID。然后运行 `kill <PID>` 并观察第一个终端——sleep 命令将终止。现在再做一次，但这次使用 `top` 或 `htop` 找到进程并从那里杀死它（在 `top` 中按 `k`，输入 PID，然后按 Enter）。这些正是你在生产环境中一个失控的 Java 进程吃掉 32 GB RAM 时将使用的技能。

理解进程与内存之间的关系也是理解容器、资源限制和 Kubernetes 等编排系统的基础。当你为容器设置内存限制而其中的进程超出限制时，操作系统会用 OOM（内存不足）信号杀死该进程。了解为什么会发生这种情况以及如何调查它，就从这里开始。

<!-- ZH_RESOURCES -->
- [Linux 进程管理 - DigitalOcean](https://www.digitalocean.com/community/tutorials/process-management-in-linux) -- 类型：教程，时长：30m
- [htop 详解 - peteris.rocks](https://peteris.rocks/blog/htop/) -- 类型：文章，时长：20m
- [Linux 如何使用 RAM - Linuxatemyram.com](https://www.linuxatemyram.com/) -- 类型：文章，时长：10m
- [缺失的一课 - Shell 工具（MIT）](https://missing.csail.mit.edu/2020/command-line/) -- 类型：课程，时长：1h
- [Linux 信号基础 - freeCodeCamp](https://www.freecodecamp.org/news/linux-signals-fundamentals/) -- 类型：教程，时长：20m

<!-- ZH_UI -->
1. 使用 ps 和 top 查看运行中的进程
2. 解释内存与磁盘存储的区别
3. 从终端终止进程
4. 我明白计算机如何运行程序了。现在我怎么编写真正的程序？
5. 我能观察进程并查看内存使用情况。但每当我需要自动化某些事情或编写脚本时，就会卡住——我连循环和函数这类基础都没有扎实掌握。我该如何真正打好这个基础？
