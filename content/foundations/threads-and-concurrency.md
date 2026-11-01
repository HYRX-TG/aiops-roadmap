---
id: threads-and-concurrency
title: Threads & Concurrency
zone: foundations
edges:
  to:
    - id: programming-fundamentals
      question: I understand how programs run. Now how do I write them?
      detail: >-
        I understand the machinery — processes, threads, how the OS manages
        them. But understanding how something runs isn't the same as being able
        to write it. I want to go from 'I know what a program is' to 'I can
        actually write one.' Where do I start?
difficulty: 1
tags:
  - threads
  - concurrency
  - parallelism
  - multi-threading
  - race-condition
  - context-switch
category: concept
milestones:
  - Explain the difference between a process and a thread
  - Use ps -eLf or top -H to view threads of a running process
  - Explain why a single-threaded web server cannot handle many users
title_zh: "线程与并发"

---


A process is great for running one thing. But what happens when a web server needs to handle ten thousand connections at the same time? Creating ten thousand separate processes would be absurdly expensive — each one gets its own memory space, its own resources. This is why **threads** exist. A thread is a lightweight unit of execution that lives inside a process, shares its memory, and can run alongside other threads. Most production software you will manage as an SRE is multi-threaded, and understanding this is how you make sense of CPU usage, thread pool exhaustion, and deadlocks.

<!-- DEEP_DIVE -->

**Processes vs threads — the fundamental difference.** A process has its own memory space. When you fork a process, the child gets a copy of the parent's memory — they are isolated from each other. A thread, by contrast, lives inside a process and **shares** the same memory space with all other threads in that process. This makes threads much cheaper to create (no memory copying) and much faster to switch between (less state to save and restore). The trade-off is that shared memory makes threads dangerous — if two threads modify the same variable at the same time, you get a **race condition**, and the results are unpredictable.

To visualize it: a process is like a house — it has its own address, its own walls, its own furniture. A thread is like a person living in that house. Multiple people (threads) share the same kitchen, the same bathroom, the same living room (shared memory). This is efficient, but if two people try to use the stove at the same time without coordinating, things go wrong.

**How multi-threading works in practice.** When you run `nginx` or `java -jar myapp.jar`, the main process starts and then creates multiple threads. A Java web application might have a **thread pool** of 200 threads — each incoming HTTP request gets assigned to a thread, which handles the request and then returns to the pool. If all 200 threads are busy, new requests queue up and eventually time out. This is **thread pool exhaustion**, and it is one of the most common causes of "the application is not responding" incidents you will deal with as an SRE.

You can see threads with the `ps -eLf` command, which shows every thread as its own line with a **TID** (Thread ID) alongside the PID. Or use `top` and press `H` to toggle thread view — you will see individual threads and their CPU usage. When you see a Java process using 400% CPU on a 4-core machine, it is not magic — it is four threads each using 100% of a core.

**Context switching.** The CPU can only execute one thread per core at a time. When the OS needs to switch from one thread to another — because the current thread is waiting for I/O, or its time slice is up — it performs a **context switch**: saving the current thread's state (registers, program counter) and loading the next thread's state. Context switches are fast (microseconds) but not free. If your system is doing millions of context switches per second, it spends more time switching than actually doing work. You can monitor this with `vmstat` — the `cs` column shows context switches per second.

**Concurrency vs parallelism.** These terms are often confused. **Concurrency** means multiple tasks are in progress at the same time — they might be interleaved on a single CPU core, not truly simultaneous. **Parallelism** means multiple tasks are literally executing at the same instant, on different CPU cores. A single-core machine can be concurrent (switching rapidly between threads) but not parallel. A multi-core machine can be both. As an SRE, this distinction matters when you are sizing machines — adding more CPU cores helps with parallelism, but if your application has a single-threaded bottleneck (like Python's Global Interpreter Lock), extra cores will not help.

**Why this matters for SRE.** Most production incidents related to CPU and performance come down to thread and process behavior. A connection pool running out of threads means your database proxy stops accepting queries. A Go service spawning millions of goroutines (lightweight threads) overwhelms the scheduler. A Node.js application, which is famously single-threaded, blocks its event loop with a CPU-heavy operation and stops responding to all requests. When you understand the threading model of the applications you manage, you can predict failure modes, set appropriate limits, and diagnose issues in minutes instead of hours.

<!-- RESOURCES -->

- [Threads vs Processes - Julia Evans](https://jvns.ca/blog/2016/06/30/why-do-we-use-the-linux-kernels-tcp-stack/) -- type: article, time: 15m
- [Linux Threads Explained - Red Hat](https://www.redhat.com/sysadmin/threads-linux) -- type: article, time: 20m
- [Concurrency Is Not Parallelism (Rob Pike talk)](https://www.youtube.com/watch?v=oV9rvDllKEg) -- type: video, time: 30m
- [Operating Systems: Three Easy Pieces - Concurrency](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf) -- type: book, time: 1h
- [Understanding Context Switching - Brendan Gregg](https://www.brendangregg.com/blog/2017-05-09/cpu-utilization-is-wrong.html) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
进程适合运行单一任务。但当 Web 服务器需要同时处理一万个连接时会发生什么？创建一万个独立进程的代价会高得离谱——每个进程都有自己独立的内存空间和资源。这正是**线程**存在的原因。线程是进程内部轻量级的执行单元，共享进程内存，并能与其他线程并行运行。作为 SRE，你管理的大多数生产软件都是多线程的，理解这一点才能让你看懂 CPU 使用率、线程池耗尽和死锁等问题。

<!-- ZH_DEEP_DIVE -->
**进程与线程——根本区别。** 进程拥有自己的内存空间。当你 fork 一个进程时，子进程会获得父进程内存的一份副本——它们彼此隔离。相比之下，线程存在于进程内部，并与该进程中的所有其他线程**共享**同一内存空间。这使得线程的创建成本低得多（无需复制内存），切换速度也快得多（需要保存和恢复的状态更少）。代价是共享内存让线程变得危险——如果两个线程同时修改同一个变量，就会产生**竞态条件**，结果不可预测。

形象地说：进程就像一栋房子——有自己的地址、自己的墙壁、自己的家具。线程就像住在这栋房子里的人。多个人（线程）共享同一个厨房、同一个卫生间、同一个客厅（共享内存）。这很高效，但如果两个人试图同时使用炉灶而不协调，就会出问题。

**多线程在实践中如何工作。** 当你运行 `nginx` 或 `java -jar myapp.jar` 时，主进程启动，然后创建多个线程。一个 Java Web 应用可能有一个包含 200 个线程的**线程池**——每个传入的 HTTP 请求被分配给一个线程，该线程处理请求后返回池中。如果全部 200 个线程都忙，新请求就会排队，最终超时。这就是**线程池耗尽**，也是你作为 SRE 会遇到的“应用无响应”事件最常见的原因之一。

你可以用 `ps -eLf` 命令查看线程，它会把每个线程显示为单独一行，在 PID 旁边显示 **TID**（线程 ID）。或者使用 `top` 并按 `H` 切换线程视图——你会看到各个线程及其 CPU 使用率。当你看到在 4 核机器上一个 Java 进程使用 400% CPU 时，这不是魔法——而是四个线程各使用一个核心的 100%。

**上下文切换。** CPU 每个核心一次只能执行一个线程。当操作系统需要从一个线程切换到另一个线程时——因为当前线程在等待 I/O，或者它的时间片用完了——它会执行一次**上下文切换**：保存当前线程的状态（寄存器、程序计数器）并加载下一个线程的状态。上下文切换很快（微秒级），但并非没有代价。如果你的系统每秒执行数百万次上下文切换，那么它花在切换上的时间比实际工作还多。你可以用 `vmstat` 监控这一点——`cs` 列显示每秒上下文切换次数。

**并发与并行。** 这两个术语经常被混淆。**并发**意味着多个任务同时在进行中——它们可能在单个 CPU 核心上交错执行，并非真正同时。**并行**意味着多个任务在不同 CPU 核心上真正在同一瞬间执行。单核机器可以是并发的（在线程之间快速切换），但不是并行的。多核机器可以两者兼具。作为 SRE，这个区别在你规划机器规格时很重要——增加更多 CPU 核心有助于并行，但如果你的应用存在单线程瓶颈（比如 Python 的全局解释器锁），额外的核心不会有所帮助。

**为什么这对 SRE 很重要。** 大多数与 CPU 和性能相关的生产事故归根结底都是线程和进程行为。连接池线程耗尽意味着你的数据库代理停止接受查询。一个 Go 服务生成数百万个 goroutine（轻量级线程）会压垮调度器。一个 Node.js 应用——以单线程著称——被一个 CPU 密集型操作阻塞了事件循环，从而停止响应所有请求。当你理解你所管理的应用的线程模型时，你就能预测故障模式、设置合适的限制，并在几分钟而不是几小时内诊断问题。

<!-- ZH_RESOURCES -->
- [线程 vs 进程 - Julia Evans](https://jvns.ca/blog/2016/06/30/why-do-we-use-the-linux-kernels-tcp-stack/) -- 类型: 文章, 时长: 15m
- [Linux 线程详解 - Red Hat](https://www.redhat.com/sysadmin/threads-linux) -- 类型: 文章, 时长: 20m
- [并发不是并行（Rob Pike 演讲）](https://www.youtube.com/watch?v=oV9rvDllKEg) -- 类型: 视频, 时长: 30m
- [操作系统：三个简单部分 - 并发](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf) -- 类型: 书籍, 时长: 1h
- [理解上下文切换 - Brendan Gregg](https://www.brendangregg.com/blog/2017-05-09/cpu-utilization-is-wrong.html) -- 类型: 文章, 时长: 15m

<!-- ZH_UI -->
1. 解释进程与线程的区别
2. 使用 ps -eLf 或 top -H 查看运行中进程的线程
3. 解释为什么单线程 Web 服务器无法处理大量用户
4. 我理解了程序如何运行。那么我该如何编写它们？
5. 我理解了机制——进程、线程、操作系统如何管理它们。但理解某物如何运行并不等于能够编写它。我想从“我知道程序是什么”进阶到“我能真正写出一个程序”。我该从哪里开始？
