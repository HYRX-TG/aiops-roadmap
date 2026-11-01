---
id: scripting-bash-python
title: 'Scripting: Bash & Python'
zone: foundations
edges:
  to:
    - id: static-site
      zone: building
      question: >-
        Scripts are great, but I want to build something people can actually
        see.
      detail: >-
        Scripts are great for automation, but I want to build something with a
        UI — a page someone can visit, or a service that responds to requests.
        I'm not sure how scripts relate to that at all. What's the gap between
        'writing scripts' and 'building something for the web'?
difficulty: 1
tags:
  - bash
  - python
  - scripting
  - automation
  - cron
  - shell-scripting
category: practice
milestones:
  - Write a bash script that automates a repetitive task
  - Write a Python script that processes a file
  - Set up a cron job
title_zh: "脚本编写：Bash 与 Python"

---


Scripting is where programming stops being theoretical and starts saving you real time. A bash script can automate that tedious deployment process you do every week, a Python script can parse log files and extract the exact error patterns you need, and a cron job can run either of them on a schedule while you sleep. This is the bridge between "I know how to code" and "I use code to make my life dramatically easier."

<!-- DEEP_DIVE -->

**Bash scripting** is writing a series of terminal commands in a file and running them together. Create a file called `backup.sh`, start it with `#!/bin/bash` (this tells the system to use bash to interpret it), and add your commands. A simple example: a script that backs up a directory, timestamps the archive, and deletes backups older than 7 days. Make it executable with `chmod +x backup.sh` and run it with `./backup.sh`. Bash is perfect for tasks that are essentially "run these five commands in order" -- file manipulation, service restarts, log rotation, deployment steps. It is already installed on every Linux and macOS system, so there is zero setup.

Here is a real-world bash pattern you will use constantly. Say you need to check if a service is running and restart it if it is not:

```bash
#!/bin/bash
SERVICE="nginx"
if systemctl is-active --quiet $SERVICE; then
    echo "$SERVICE is running"
else
    echo "$SERVICE is down, restarting..."
    systemctl restart $SERVICE
    echo "$SERVICE restarted at $(date)" >> /var/log/service-restarts.log
fi
```

That is a dozen lines of code that could be the difference between a 30-second automated recovery and a 3 AM phone call. Bash scripts excel at this kind of glue work -- stitching together system commands with a bit of logic.

**Python** steps in when things get more complex. Need to parse JSON from an API? Process a CSV with thousands of rows? Send a Slack notification when something fails? Python handles all of this with clean, readable code and an enormous library ecosystem. For example, processing a log file to count error types:

```python
from collections import Counter

errors = Counter()
with open("/var/log/app.log") as f:
    for line in f:
        if "ERROR" in line:
            error_type = line.split("ERROR")[1].strip().split(":")[0]
            errors[error_type] += 1

for error, count in errors.most_common(10):
    print(f"{count:>5} | {error}")
```

Python is the language of choice for SRE tooling, and for good reason -- it is readable, it has libraries for everything (requests for HTTP, boto3 for AWS, kubernetes for K8s), and you can write something useful in a few minutes.

**Cron jobs** are how you schedule scripts to run automatically. The cron daemon on Linux checks a schedule table and runs commands at specified times. Run `crontab -e` to edit your schedule. The format is `minute hour day-of-month month day-of-week command`. For example, `0 2 * * * /home/user/backup.sh` runs your backup script at 2:00 AM every day. `*/5 * * * * /home/user/check_disk.sh` runs a disk check every 5 minutes. The syntax looks cryptic at first, but sites like crontab.guru let you build expressions interactively.

The rule of thumb for choosing between bash and Python: if your script is mostly running system commands with a little logic, use bash. If it involves data processing, API calls, complex logic, or error handling, use Python. In practice, many SRE teams end up with a mix -- bash scripts for simple operational tasks and Python for anything more involved. And since you already learned Git, put all your scripts in a repository from day one. Future-you trying to figure out why the backup script was changed last Tuesday will thank present-you.

One last piece of advice: start automating things that annoy you. Every time you catch yourself doing the same manual task for the third time, stop and write a script. Over weeks and months, you will build a personal toolkit of scripts that makes you dramatically more productive. This habit -- seeing repetition as an opportunity for automation -- is the defining trait of effective SRE and DevOps engineers.

<!-- RESOURCES -->

- [Bash Scripting Tutorial - Ryan's Tutorials](https://ryanstutorials.net/bash-scripting-tutorial/) -- type: tutorial, time: 3h
- [Automate the Boring Stuff with Python - Al Sweigart](https://automatetheboringstuff.com/) -- type: book, time: 10h
- [Crontab Guru - Cron Expression Editor](https://crontab.guru/) -- type: tool, time: 10m
- [Google's Shell Style Guide](https://google.github.io/styleguide/shellguide.html) -- type: reference, time: 30m
- [Python for DevOps - O'Reilly (Free Chapter)](https://www.oreilly.com/library/view/python-for-devops/9781492057680/) -- type: book, time: varies

<!-- ZH_SUMMARY -->
脚本化是编程从理论走向实际、真正为你节省时间的地方。一个 bash 脚本可以自动化你每周都要做的那些繁琐的部署流程，一个 Python 脚本可以解析日志文件并提取出你需要的精确错误模式，而一个 cron 任务可以让你在睡觉时按计划运行其中任何一个。这就是从“我会写代码”到“我用代码让生活变得轻松得多”之间的桥梁。

<!-- ZH_DEEP_DIVE -->
**Bash 脚本**就是把一系列终端命令写进一个文件，然后一起运行。创建一个名为 `backup.sh` 的文件，以 `#!/bin/bash` 开头（这告诉系统用 bash 来解释它），然后加入你的命令。一个简单的例子：一个脚本，备份一个目录、给归档文件打上时间戳，并删除超过 7 天的备份。用 `chmod +x backup.sh` 让它可执行，然后用 `./backup.sh` 运行它。Bash 非常适合那些本质上就是“按顺序运行这五条命令”的任务——文件操作、服务重启、日志轮转、部署步骤。它已经安装在每个 Linux 和 macOS 系统上，所以零配置。

下面是一个你将会经常用到的真实世界 bash 模式。假设你需要检查某个服务是否在运行，如果没运行就重启它：

```bash
#!/bin/bash
SERVICE="nginx"
if systemctl is-active --quiet $SERVICE; then
    echo "$SERVICE is running"
else
    echo "$SERVICE is down, restarting..."
    systemctl restart $SERVICE
    echo "$SERVICE restarted at $(date)" >> /var/log/service-restarts.log
fi
```

这十几行代码，可能就是 30 秒自动恢复和凌晨 3 点电话之间的差别。Bash 脚本擅长这类胶水工作——用一点逻辑把系统命令拼接起来。

**Python** 在事情变得更复杂时登场。需要解析来自 API 的 JSON？处理一个有数千行的 CSV？在某个东西失败时发送 Slack 通知？Python 用干净、可读的代码和庞大的库生态来处理所有这些。例如，处理一个日志文件来统计错误类型：

```python
from collections import Counter

errors = Counter()
with open("/var/log/app.log") as f:
    for line in f:
        if "ERROR" in line:
            error_type = line.split("ERROR")[1].strip().split(":")[0]
            errors[error_type] += 1

for error, count in errors.most_common(10):
    print(f"{count:>5} | {error}")
```

Python 是 SRE 工具开发的首选语言，而且理由充分——它可读性强，有适用于一切的库（requests 用于 HTTP，boto3 用于 AWS，kubernetes 用于 K8s），你可以在几分钟内写出有用的东西。

**Cron 任务**是你安排脚本自动运行的方式。Linux 上的 cron 守护进程会检查一张调度表，并在指定时间运行命令。运行 `crontab -e` 来编辑你的调度。格式是 `minute hour day-of-month month day-of-week command`。例如，`0 2 * * * /home/user/backup.sh` 每天凌晨 2:00 运行你的备份脚本。`*/5 * * * * /home/user/check_disk.sh` 每 5 分钟运行一次磁盘检查。这个语法乍看很神秘，但像 crontab.guru 这样的网站可以让你交互式地构建表达式。

在 bash 和 Python 之间做选择的经验法则：如果你的脚本主要是运行系统命令加一点逻辑，用 bash。如果涉及数据处理、API 调用、复杂逻辑或错误处理，用 Python。在实践中，许多 SRE 团队最终会混合使用——简单运维任务用 bash 脚本，任何更复杂的事情用 Python。既然你已经学过 Git，从第一天起就把你所有的脚本放进一个仓库。未来那个试图弄清楚为什么备份脚本上周二被改动的你，会感谢现在的你。

最后一条建议：开始自动化那些让你烦的事情。每当你发现自己第三次做同样的手动任务时，停下来写个脚本。经过数周和数月，你会建立起一个个人脚本工具箱，让你效率大幅提升。这个习惯——把重复视为自动化的机会——是高效 SRE 和 DevOps 工程师的决定性特质。

<!-- ZH_RESOURCES -->
- [Bash 脚本教程 - Ryan's Tutorials](https://ryanstutorials.net/bash-scripting-tutorial/) -- 类型：教程，时长：3 小时
- [用 Python 自动化枯燥的工作 - Al Sweigart](https://automatetheboringstuff.com/) -- 类型：书籍，时长：10 小时
- [Crontab Guru - Cron 表达式编辑器](https://crontab.guru/) -- 类型：工具，时长：10 分钟
- [Google 的 Shell 风格指南](https://google.github.io/styleguide/shellguide.html) -- 类型：参考，时长：30 分钟
- [Python for DevOps - O'Reilly（免费章节）](https://www.oreilly.com/library/view/python-for-devops/9781492057680/) -- 类型：书籍，时长：不定

<!-- ZH_UI -->
1. 编写一个自动化重复任务的 bash 脚本
2. 编写一个处理文件的 Python 脚本
3. 设置一个 cron 任务
4. 脚本很好，但我想构建人们真正能看到的东西。
5. 脚本很适合自动化，但我想构建带 UI 的东西——一个人们可以访问的页面，或一个能响应请求的服务。我不确定脚本与此有何关系。‘编写脚本’和‘为 Web 构建东西’之间的差距是什么？
