---
id: programming-fundamentals
title: Programming Fundamentals
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: I know the theory. Let me apply it to automate real tasks.
      detail: >-
        I understand the concepts — loops, functions, data structures — but I've
        only written toy programs. I want to actually automate the things I do
        in the terminal, or write something that does real work without me
        having to babysit it. What would I actually write, and in what language?
    - id: what-is-a-web-service
      zone: building
      question: I can write code. How do I build something people can use?
      detail: >-
        I can write scripts that run on my machine. But the software I actually
        want to build — something a user can open in a browser, something that
        serves data over an API — is a completely different thing. I don't even
        know what's involved in making something that lives on the network and
        responds to requests.
difficulty: 1
tags:
  - programming
  - variables
  - loops
  - functions
  - data-structures
  - logic
category: concept
milestones:
  - 'Write a program that uses variables, loops, and functions'
  - 'Implement a simple data structure (list, dictionary/map)'
  - Solve a basic coding challenge
title_zh: "编程基础"

---


Programming is not about memorizing syntax -- it is about learning to break problems into small, logical steps that a computer can follow. Once you internalize the core concepts of variables, loops, conditionals, and functions, you can pick up any programming language in a matter of days because they all share these same building blocks.

<!-- DEEP_DIVE -->

Let's start with **variables** -- they are just named containers for data. In Python, `name = "Alice"` stores the text "Alice" in a variable called `name`. `count = 42` stores the number 42. `is_active = True` stores a boolean (true/false) value. Every program you ever write will use variables to hold onto information while it works with it. The key insight is that variables can change -- that is why they are called variables. You can write `count = count + 1` and now `count` is 43. This ability to store, retrieve, and update data is the foundation of all computation.

**Conditionals** let your program make decisions. `if count > 100: print("That's a lot!")` only runs the print statement when the condition is true. Add `elif` for additional conditions and `else` for the default case. **Loops** let your program repeat actions. `for i in range(10): print(i)` prints the numbers 0 through 9. `while count < 100: count = count + 1` keeps incrementing until the condition is no longer true. Conditionals and loops together give your code the ability to handle complex logic -- check this, repeat that, do something different when a certain condition is met.

**Functions** are where you start thinking like a real programmer. A function is a reusable block of code that takes inputs, does something, and (optionally) returns an output. In Python: `def greet(name): return f"Hello, {name}!"`. Now you can call `greet("Alice")` and get back "Hello, Alice!" anywhere in your program. Functions let you organize your code, avoid repetition, and build abstractions. Instead of writing the same ten lines of code in five places, you write a function once and call it five times. When you need to fix a bug, you fix it in one place.

**Data structures** are how you organize information. A **list** (or array) stores items in order: `servers = ["web-01", "web-02", "db-01"]`. You can loop through it, add items, remove items, and access them by position (`servers[0]` gives you "web-01"). A **dictionary** (or map/hash) stores key-value pairs: `server_status = {"web-01": "healthy", "web-02": "degraded", "db-01": "healthy"}`. Now you can look up any server's status instantly with `server_status["web-01"]`. These two data structures alone will handle the vast majority of your day-to-day programming needs. As an SRE, you will constantly work with lists of servers, dictionaries of configuration values, and similar structures.

Here is an exercise that ties everything together. Write a program that reads a list of server names and their CPU usage (you can hardcode the data), then prints a warning for any server above 80% usage. This requires variables (to store data), a data structure (dictionary for server-to-usage mapping), a loop (to check each server), a conditional (to compare against the threshold), and a function (to encapsulate the check logic). It is a tiny program, but it mirrors exactly the kind of monitoring logic you will write professionally.

The most important skill at this stage is not writing perfect code -- it is developing your **problem-solving instinct**. When faced with a task, practice breaking it into smaller pieces. "Monitor server health" becomes: get the list of servers, check each one's metrics, compare to thresholds, and alert if something is wrong. Each of those pieces becomes a function, and suddenly a complex problem is just a collection of simple ones.

<!-- RESOURCES -->

- [Automate the Boring Stuff with Python - Al Sweigart](https://automatetheboringstuff.com/) -- type: book, time: 10h
- [Python Official Tutorial](https://docs.python.org/3/tutorial/) -- type: docs, time: 4h
- [freeCodeCamp - Scientific Computing with Python](https://www.freecodecamp.org/learn/scientific-computing-with-python/) -- type: course, time: 20h
- [Exercism - Python Track](https://exercism.org/tracks/python) -- type: interactive, time: varies
- [Think Python - How to Think Like a Computer Scientist](https://greenteapress.com/thinkpython2/html/index.html) -- type: book, time: 8h

<!-- ZH_SUMMARY -->
编程不是记忆语法——而是学会将问题拆解为计算机能够遵循的小的逻辑步骤。一旦你内化了变量、循环、条件语句和函数这些核心概念，你就能在几天内掌握任何编程语言，因为它们都共享这些相同的构建块。

<!-- ZH_DEEP_DIVE -->
先从**变量**说起——它们不过是给数据起的具名容器。在 Python 中，`name = "Alice"` 把文本 "Alice" 存入名为 `name` 的变量。`count = 42` 存储数字 42。`is_active = True` 存储一个布尔值（真/假）。你今后编写的每个程序都会用变量在运行过程中保存信息。关键点在于变量可以改变——这正是它们被称为“变量”的原因。你可以写 `count = count + 1`，此时 `count` 就变成了 43。这种存储、读取和更新数据的能力是一切计算的基础。

**条件语句**让你的程序能够做出判断。`if count > 100: print("That's a lot!")` 只在条件为真时才执行 print 语句。用 `elif` 添加更多条件，用 `else` 处理默认情况。**循环**让你的程序重复执行动作。`for i in range(10): print(i)` 打印数字 0 到 9。`while count < 100: count = count + 1` 会持续递增，直到条件不再为真。条件语句与循环结合，让你的代码能够处理复杂逻辑——检查这个、重复那个、在满足特定条件时做不同的事。

**函数**是你开始像真正的程序员那样思考的地方。函数是一段可复用的代码块，它接收输入、执行操作，并（可选地）返回输出。在 Python 中：`def greet(name): return f"Hello, {name}!"`。现在你可以在程序的任何地方调用 `greet("Alice")`，得到 "Hello, Alice!"。函数让你能够组织代码、避免重复、构建抽象。与其在五个地方写同样的十行代码，不如写一次函数、调用五次。当你需要修复 bug 时，只需改一处。

**数据结构**是你组织信息的方式。**列表**（或数组）按顺序存储条目：`servers = ["web-01", "web-02", "db-01"]`。你可以遍历它、添加条目、删除条目，并按位置访问（`servers[0]` 得到 "web-01"）。**字典**（或映射/哈希）存储键值对：`server_status = {"web-01": "healthy", "web-02": "degraded", "db-01": "healthy"}`。现在你可以用 `server_status["web-01"]` 瞬间查到任意服务器的状态。仅这两种数据结构就能满足你日常编程的绝大多数需求。作为 SRE，你会经常处理服务器列表、配置值字典以及类似的结构。

下面是一个把所学内容串起来的练习。编写一个程序，读取服务器名称列表及其 CPU 使用率（数据可以硬编码），然后对使用率超过 80% 的服务器打印警告。这需要用到变量（存储数据）、数据结构（服务器到使用率的字典映射）、循环（逐个检查服务器）、条件语句（与阈值比较）以及函数（封装检查逻辑）。程序虽小，却精确对应了你将来在职业工作中编写的那类监控逻辑。

这个阶段最重要的技能不是写出完美的代码——而是培养你的**解决问题的直觉**。面对一项任务时，练习把它拆解成更小的部分。“监控服务器健康”就变成：获取服务器列表、检查每台服务器的指标、与阈值比较、出问题时告警。每一部分都变成一个函数，于是一个复杂问题就变成了一组简单问题的集合。

<!-- ZH_RESOURCES -->
- [Automate the Boring Stuff with Python - Al Sweigart](https://automatetheboringstuff.com/) -- 类型: 书籍, 时长: 10h
- [Python Official Tutorial](https://docs.python.org/3/tutorial/) -- 类型: 文档, 时长: 4h
- [freeCodeCamp - Scientific Computing with Python](https://www.freecodecamp.org/learn/scientific-computing-with-python/) -- 类型: 课程, 时长: 20h
- [Exercism - Python Track](https://exercism.org/tracks/python) -- 类型: 互动, 时长: 不定
- [Think Python - How to Think Like a Computer Scientist](https://greenteapress.com/thinkpython2/html/index.html) -- 类型: 书籍, 时长: 8h

<!-- ZH_UI -->
1. 编写一个使用变量、循环和函数的程序
2. 实现一个简单的数据结构（列表、字典/映射）
3. 解决一个基础编程挑战
4. 我懂理论了。让我把它应用到自动化真实任务上。
5. 我理解这些概念——循环、函数、数据结构——但我只写过玩具程序。我想真正自动化我在终端里做的事情，或者写出能真正干活、不需要我盯着的东西。我实际会写什么，用什么语言？
6. 我会写代码。我如何构建人们能用的东西？
7. 我能写在自己机器上运行的脚本。但我真正想构建的软件——用户能在浏览器里打开的东西、通过 API 提供数据的东西——完全是另一回事。我甚至不知道让某个东西存在于网络上并响应请求涉及哪些内容。
