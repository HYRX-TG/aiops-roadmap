---
id: how-computers-run-code
title: How Computers Run Code
zone: foundations
edges:
  to:
    - id: operating-system-basics
      question: Code runs on hardware. But what manages all that?
      detail: >-
        My code runs, but I also have a browser, a music player, and a dozen
        other things running at the same time. How does the computer handle all
        of that simultaneously? And how does my program get access to the disk
        or network without directly touching the hardware? Something must be
        coordinating all of this — what is it?
difficulty: 1
tags:
  - cpu
  - compilation
  - interpretation
  - machine-code
  - hardware
category: concept
milestones:
  - Explain the difference between compiled and interpreted languages
  - Understand what the CPU actually does with your code
title_zh: "计算机如何运行代码"

---


When you ran that Hello World program, something remarkable happened behind the scenes. Your human-readable code got transformed into a stream of ones and zeros that a tiny chip in your computer -- the CPU -- could understand and execute. Understanding this transformation is the key to understanding why some programs are fast, why some crash, and why different programming languages exist in the first place.

<!-- DEEP_DIVE -->

At the very bottom of the stack, your CPU only understands one thing: machine code. These are simple numeric instructions like "load this number into a register," "add these two registers together," or "jump to this memory address." That is it. Your CPU cannot read Python or JavaScript. It does not know what a "string" or a "function" is. It just crunches numbers at billions of operations per second.

So how does `print("Hello, World!")` become something the CPU can execute? There are two main approaches: compilation and interpretation. A **compiled** language (like C, Go, or Rust) uses a program called a compiler to translate your entire source code into machine code *before* you run it. The output is a binary file -- an executable -- that the CPU can run directly. This is why compiled programs tend to be fast: the translation work is done ahead of time. An **interpreted** language (like Python or Ruby) uses a program called an interpreter that reads your code line by line and executes it on the fly. There is no separate compilation step, which makes development faster and more interactive, but execution is generally slower because the translation happens at runtime.

In practice, the line between compiled and interpreted is blurry. Java compiles to "bytecode" that runs on the Java Virtual Machine (JVM), which then interprets or JIT-compiles it to machine code. Python compiles your `.py` files to `.pyc` bytecode behind the scenes. JavaScript engines like V8 (used in Chrome and Node.js) use sophisticated just-in-time (JIT) compilation to get near-native speed. The key takeaway is not the exact mechanism -- it is that there is always a translation step from human-readable code to something the hardware can execute.

Why does this matter for SRE work? Because understanding the compilation and runtime model of a language tells you a lot about how it behaves in production. A Go service compiles to a single static binary -- easy to deploy, no runtime dependencies. A Python service needs a Python interpreter installed, plus all its library dependencies. A Java service needs a JVM and has a warm-up period before the JIT kicks in. These are not just academic distinctions; they directly affect how you build, deploy, and troubleshoot services.

It is also worth understanding the concept of **high-level vs. low-level** languages. A low-level language like C or assembly gives you direct control over memory and hardware but requires you to manage every detail yourself. A high-level language like Python abstracts all of that away -- you don't worry about memory allocation, you just write `x = "hello"` and the language handles the rest. Most SRE work lives in the high-level world (Python, Go, Bash), but understanding what is happening underneath helps you debug the hard problems -- memory leaks, performance issues, and the mysterious crashes that only happen in production.

<!-- RESOURCES -->

- [Crash Course Computer Science - The CPU (YouTube)](https://www.youtube.com/watch?v=FZGugFqdr60) -- type: video, time: 10m
- [Khan Academy - How Computers Work](https://www.khanacademy.org/computing/code-org/computers-and-the-internet) -- type: course, time: 2h
- [Compiled vs Interpreted Languages - freeCodeCamp](https://www.freecodecamp.org/news/compiled-versus-interpreted-languages/) -- type: article, time: 15m
- [Ben Eater - Building an 8-bit Computer (YouTube)](https://www.youtube.com/playlist?list=PLowKtXNTBypGqImE405J2565dvjafglHU) -- type: video, time: varies

<!-- ZH_SUMMARY -->
当你运行那个 Hello World 程序时，幕后发生了一些奇妙的事情。你编写的、人类可读的代码被转换成了一串由 1 和 0 组成的比特流，而你计算机中一块小小的芯片——CPU——能够理解并执行它。理解这一转换过程，是理解为什么有些程序运行得快、有些程序会崩溃，以及为什么不同编程语言从一开始就存在的原因的关键。

<!-- ZH_DEEP_DIVE -->
在技术栈的最底层，你的 CPU 只理解一件事：机器码。这些是简单的数字指令，比如“把这个数字加载到寄存器中”、“将这两个寄存器相加”或“跳转到这个内存地址”。仅此而已。你的 CPU 无法读取 Python 或 JavaScript。它不知道什么是“字符串”或“函数”。它只是以每秒数十亿次操作的速度处理数字。

那么，`print("Hello, World!")` 是如何变成 CPU 可以执行的东西的呢？主要有两种方法：编译和解释。**编译型**语言（如 C、Go 或 Rust）使用一个称为编译器的程序，在运行代码*之前*将整个源代码翻译成机器码。输出是一个二进制文件——一个可执行文件——CPU 可以直接运行。这就是编译型程序往往很快的原因：翻译工作提前完成了。**解释型**语言（如 Python 或 Ruby）使用一个称为解释器的程序，逐行读取代码并即时执行。没有单独的编译步骤，这使得开发更快、更具交互性，但执行通常较慢，因为翻译发生在运行时。

在实践中，编译型和解释型之间的界限是模糊的。Java 编译成“字节码”，在 Java 虚拟机（JVM）上运行，然后由 JVM 解释或 JIT 编译成机器码。Python 在后台将你的 `.py` 文件编译成 `.pyc` 字节码。像 V8（用于 Chrome 和 Node.js）这样的 JavaScript 引擎使用复杂的即时（JIT）编译来达到接近原生的速度。关键要点不是确切的机制——而是始终存在一个从人类可读代码到硬件可执行内容的翻译步骤。

为什么这对 SRE 工作很重要？因为理解语言的编译和运行时模型可以让你深入了解它在生产环境中的行为。Go 服务编译成单个静态二进制文件——易于部署，没有运行时依赖。Python 服务需要安装 Python 解释器，以及所有库依赖。Java 服务需要 JVM，并且在 JIT 启动之前有一个预热期。这些不仅仅是学术上的区别；它们直接影响你如何构建、部署和排查服务问题。

理解**高级语言与低级语言**的概念也值得注意。像 C 或汇编这样的低级语言让你直接控制内存和硬件，但需要你自己管理每一个细节。像 Python 这样的高级语言将所有这些抽象掉——你不必担心内存分配，只需写 `x = "hello"`，语言会处理其余部分。大多数 SRE 工作生活在高级世界中（Python、Go、Bash），但了解底层发生的事情有助于你调试难题——内存泄漏、性能问题，以及只在生产环境中发生的神秘崩溃。

<!-- ZH_RESOURCES -->
- [计算机科学速成课 - CPU（YouTube）](https://www.youtube.com/watch?v=FZGugFqdr60) -- 类型：视频，时长：10m
- [可汗学院 - 计算机如何工作](https://www.khanacademy.org/computing/code-org/computers-and-the-internet) -- 类型：课程，时长：2h
- [编译型语言与解释型语言 - freeCodeCamp](https://www.freecodecamp.org/news/compiled-versus-interpreted-languages/) -- 类型：文章，时长：15m
- [Ben Eater - 构建一台 8 位计算机（YouTube）](https://www.youtube.com/playlist?list=PLowKtXNTBypGqImE405J2565dvjafglHU) -- 类型：视频，时长：不定

<!-- ZH_UI -->
1. 解释编译型语言与解释型语言的区别
2. 理解 CPU 实际如何处理你的代码
3. 代码运行在硬件上。但什么在管理这一切？
4. 我的代码在运行，但同时还有浏览器、音乐播放器和十几个其他程序在运行。计算机如何同时处理所有这些？我的程序又如何在不直接接触硬件的情况下访问磁盘或网络？一定有某个东西在协调这一切——它是什么？
