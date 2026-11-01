---
id: hello-world
title: 'Hello, World!'
zone: foundations
edges:
  to:
    - id: how-computers-run-code
      question: I wrote code and it ran... but how?
      detail: >-
        I typed some text, hit run, and words appeared. But what actually
        happened? My code isn't electricity — so how did the computer understand
        it? And why do some languages need to be 'compiled' while others just
        run? I feel like I'm missing something fundamental about how any of this
        works.
difficulty: 1
tags:
  - programming
  - beginner
  - first-program
category: concept
milestones:
  - Write and run a Hello World program
  - Modify it to print your name
title_zh: "“你好，世界！”"

---


Every programmer's journey starts with the same tiny ritual: making a computer print "Hello, World!" on a screen. It sounds almost too simple, but this single act proves something profound -- you just told a machine what to do, and it listened. That is the essence of programming: writing instructions that a computer can execute.

<!-- DEEP_DIVE -->

Code is just text. Seriously. Open any text editor, type `print("Hello, World!")`, save it as `hello.py`, and run it with `python hello.py` in your terminal. Congratulations -- you are now a programmer. There is no gatekeeping ceremony, no special hardware required. A computer does exactly what you tell it to, nothing more and nothing less. That is both its superpower and its biggest source of frustration.

But why does this matter? Because everything you interact with on a computer -- every app, every website, every game -- started as text files like the one you just wrote. Someone sat down and typed instructions, line by line. Instagram's backend, Google's search engine, the firmware in your microwave -- all of it is code written by humans (and increasingly, by AI assistants, but that is a different topic).

For SRE and DevOps specifically, programming is not optional. You will write scripts to automate deployments, build tools to monitor systems, and debug code that is failing in production at 2 AM. The good news is you do not need to be a world-class software engineer. You need to be comfortable enough with code to solve problems, and that comfort starts right here.

Let's try it in a few languages to show that the concept is universal. In Python: `print("Hello, World!")`. In JavaScript: `console.log("Hello, World!");`. In Bash: `echo "Hello, World!"`. In Go: you need a bit more boilerplate, but the idea is identical. Every language has its own syntax -- its own grammar rules -- but they all do the same fundamental thing: take your instructions and make the computer execute them.

If you have never written code before, here is your homework: pick Python (it is the friendliest for beginners), install it, and write a program that prints your name. Then make it print your name five times. Then make it ask for someone's name and greet them. Each tiny step builds a mental model for how programming works, and that model is the foundation for everything else on this roadmap.

<!-- RESOURCES -->

- [Python Official Tutorial - Getting Started](https://docs.python.org/3/tutorial/introduction.html) -- type: tutorial, time: 1h
- [freeCodeCamp - Python for Beginners (YouTube)](https://www.youtube.com/watch?v=rfscVS0vtbw) -- type: video, time: 4h
- [Replit - Write Code in Your Browser](https://replit.com/) -- type: tool, time: 15m
- [The Missing Semester of Your CS Education - MIT](https://missing.csail.mit.edu/) -- type: course, time: 2h

<!-- ZH_SUMMARY -->
每个程序员的旅程都始于同一个微小的仪式：让计算机在屏幕上打印出“Hello, World!”。听起来简单得几乎不值一提，但这一简单的举动却证明了一件深刻的事——你刚刚告诉一台机器该做什么，而它照做了。这正是编程的本质：编写计算机能够执行的指令。

<!-- ZH_DEEP_DIVE -->
代码不过是文本。说真的。打开任意一个文本编辑器，输入 `print("Hello, World!")`，保存为 `hello.py`，然后在终端中用 `python hello.py` 运行它。恭喜你——你现在是一名程序员了。没有什么准入仪式，也不需要特殊硬件。计算机完全按照你的指令行事，不多不少。这既是它的超能力，也是它最大的挫败来源。

但这为什么重要？因为你在计算机上交互的一切——每个应用、每个网站、每个游戏——都始于像你刚刚写的那样的文本文件。有人坐下来，一行一行地输入指令。Instagram 的后端、Google 的搜索引擎、你微波炉里的固件——所有这些都是人类编写的代码（而且越来越多是由 AI 助手编写，但那是另一个话题了）。

具体到 SRE 和 DevOps，编程不是可选项。你会编写脚本来自动化部署、构建工具来监控系统，并在凌晨 2 点调试在生产环境中出故障的代码。好消息是，你不需要成为世界级的软件工程师。你只需要对代码足够熟悉，能够解决问题，而这种熟悉感就从这里开始。

让我们用几种语言试一试，以说明这个概念是通用的。在 Python 中：`print("Hello, World!")`。在 JavaScript 中：`console.log("Hello, World!");`。在 Bash 中：`echo "Hello, World!"`。在 Go 中：你需要多一点样板代码，但思路完全相同。每种语言都有自己的语法——自己的文法规则——但它们做的都是同一件根本性的事情：接收你的指令，让计算机执行它们。

如果你以前从未写过代码，这是你的作业：选择 Python（它对初学者最友好），安装它，写一个打印你名字的程序。然后让它把你的名字打印五次。然后让它询问某人的名字并问候他们。每一个微小的步骤都会构建一个关于编程如何运作的心智模型，而这个模型是这条路线图上其他一切的基础。

<!-- ZH_RESOURCES -->
- [Python 官方教程 - 入门](https://docs.python.org/3/tutorial/introduction.html) -- 类型：教程，时长：1小时
- [freeCodeCamp - Python 初学者教程（YouTube）](https://www.youtube.com/watch?v=rfscVS0vtbw) -- 类型：视频，时长：4小时
- [Replit - 在浏览器中编写代码](https://replit.com/) -- 类型：工具，时长：15分钟
- [你计算机科学教育中缺失的一课 - MIT](https://missing.csail.mit.edu/) -- 类型：课程，时长：2小时

<!-- ZH_UI -->
1. 编写并运行一个 Hello World 程序
2. 修改它，使其打印你的名字
3. 我写了代码，它运行了……但这是怎么做到的？
4. 我输入了一些文本，点击运行，然后文字出现了。但实际发生了什么？我的代码又不是电——那计算机是如何理解它的？为什么有些语言需要“编译”，而另一些可以直接运行？我觉得自己对这一切如何运作缺少了某种根本性的理解。
