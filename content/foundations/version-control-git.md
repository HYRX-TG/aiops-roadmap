---
id: version-control-git
title: Version Control with Git
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: I can track my code. Now let me write something more powerful.
      detail: >-
        I can track my changes and I have a proper editor workflow now. The next
        thing I want is to stop doing repetitive things by hand — running the
        same sequences of commands, copying the same files. Is scripting the
        answer to that, and what does it actually look like in practice?
difficulty: 1
tags:
  - git
  - version-control
  - github
  - collaboration
  - commits
  - branches
category: tool
milestones:
  - 'Initialize a repo, make commits, and view the log'
  - 'Create a branch, make changes, and merge it back'
  - Push code to GitHub
title_zh: "使用 Git 进行版本控制"

---


Git is the version control system that tracks every change you make to your code, lets you rewind to any previous state, and makes it possible for teams of hundreds of engineers to work on the same codebase without stepping on each other's toes. It is not optional -- every professional software and infrastructure workflow depends on Git, and understanding it deeply will pay dividends every single day of your career.

<!-- DEEP_DIVE -->

At its core, Git is a tool that takes snapshots of your project. Every time you **commit**, Git records the exact state of every tracked file at that moment. You can think of it like a save system in a video game -- you can always go back to any previous save. Run `git init` in a directory and it becomes a Git repository. Create a file, run `git add myfile.py` to stage it (tell Git you want to include it in the next snapshot), and then `git commit -m "Add my first file"` to create the snapshot. Run `git log` and you will see your commit with a unique hash, a timestamp, and your message.

**Branches** are where Git gets powerful. A branch is just a separate line of development. Say you want to try a risky change without messing up your working code. Run `git checkout -b experiment` to create and switch to a new branch. Make your changes, commit them. If the experiment works, you merge it back into your main branch with `git checkout main` followed by `git merge experiment`. If it was a disaster, just delete the branch with `git branch -d experiment` and your main branch is untouched. This workflow is the backbone of how professional teams build software -- every feature, every bug fix, every infrastructure change gets its own branch.

The real power unlocks when you connect your local repository to a **remote** like GitHub, GitLab, or Bitbucket. Run `git remote add origin https://github.com/yourusername/yourrepo.git` to link them, then `git push -u origin main` to upload your code. Now your code lives in the cloud, backed up and accessible from anywhere. Other people can **clone** your repository, make changes on their own branches, and submit **pull requests** (PRs) -- proposals to merge their changes into the main branch. Code review happens on PRs, and this is where teams catch bugs, share knowledge, and maintain quality.

For SRE and DevOps, Git is not just for application code. Your infrastructure definitions (Terraform files, Ansible playbooks, Kubernetes manifests) all live in Git. This practice is called **Infrastructure as Code** (IaC), and it means your entire infrastructure is versioned, reviewable, and reproducible. If a bad config change breaks production, you can look at the Git log to see exactly what changed, who changed it, and when. Then you revert the commit and you are back to a working state. This is infinitely better than someone manually editing a config on a server with no record of what happened.

A few practical tips that will save you headaches. First, write meaningful commit messages -- "fix bug" tells you nothing six months later, but "Fix nginx timeout by increasing proxy_read_timeout to 300s" tells you everything. Second, commit often in small, logical chunks rather than one massive commit at the end of the day. Third, learn `git diff` (shows what changed), `git stash` (temporarily shelves your changes), and `git blame` (shows who last modified each line of a file). These three commands will become your best friends during debugging sessions.

One thing that trips up beginners: Git and GitHub are not the same thing. Git is the version control tool that runs locally on your machine. GitHub is a web platform that hosts Git repositories and adds collaboration features like pull requests, issues, and actions. You can use Git without GitHub, but in practice, almost everyone uses some kind of remote hosting platform.

<!-- RESOURCES -->

- [Git Official Documentation - Getting Started](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control) -- type: docs, time: 1h
- [Learn Git Branching - Interactive Tutorial](https://learngitbranching.js.org/) -- type: interactive, time: 2h
- [GitHub Skills - Introduction to GitHub](https://skills.github.com/) -- type: course, time: 1h
- [The Missing Semester - Version Control (MIT)](https://missing.csail.mit.edu/2020/version-control/) -- type: course, time: 1h
- [Oh Shit, Git!?! - Common Git Mistakes and Fixes](https://ohshitgit.com/) -- type: reference, time: 15m

<!-- ZH_SUMMARY -->
Git 是一个版本控制系统，它追踪你对代码所做的每一次更改，让你可以回退到任何之前的状态，并使数百名工程师组成的团队能够在不相互干扰的情况下协作开发同一个代码库。它不是可选项——每一个专业的软件和基础设施工作流都依赖于 Git，深入理解它将在你职业生涯的每一天带来回报。

<!-- ZH_DEEP_DIVE -->
从本质上讲，Git 是一个为你的项目拍摄快照的工具。每次你**提交**（commit）时，Git 都会记录当时每个被跟踪文件的确切状态。你可以把它想象成电子游戏中的存档系统——你随时可以回到之前的任何一个存档。在一个目录中运行 `git init`，它就会变成一个 Git 仓库。创建一个文件，运行 `git add myfile.py` 将其暂存（告诉 Git 你想把它包含在下一个快照中），然后运行 `git commit -m "Add my first file"` 来创建快照。运行 `git log`，你就会看到你的提交，其中包含唯一的哈希值、时间戳和你的提交信息。

**分支**（Branch）是 Git 展现强大能力的地方。分支只是一条独立的开发线。假设你想尝试一项有风险的改动，又不想弄乱正在工作的代码。运行 `git checkout -b experiment` 来创建并切换到一个新分支。做出你的改动，然后提交。如果实验成功，你可以用 `git checkout main` 再执行 `git merge experiment`，把它合并回主分支。如果一塌糊涂，只需用 `git branch -d experiment` 删除该分支，你的主分支丝毫未受影响。这一工作流是专业团队构建软件的支柱——每个功能、每个缺陷修复、每项基础设施变更都有自己的分支。

当你把本地仓库连接到一个**远程**（remote）平台（如 GitHub、GitLab 或 Bitbucket）时，真正的威力才会释放。运行 `git remote add origin https://github.com/yourusername/yourrepo.git` 将它们关联起来，然后运行 `git push -u origin main` 上传你的代码。现在你的代码存在于云端，有备份，且可从任何地方访问。其他人可以**克隆**（clone）你的仓库，在他们自己的分支上做出改动，并提交**拉取请求**（PR）——即将其改动合并到主分支的提议。代码审查在 PR 上进行，团队正是在这里发现缺陷、分享知识并保持质量。

对于 SRE 和 DevOps 而言，Git 不仅仅用于应用代码。你的基础设施定义（Terraform 文件、Ansible playbook、Kubernetes manifest）都存放在 Git 中。这种做法称为**基础设施即代码**（IaC），它意味着你的整个基础设施都是可版本化、可审查、可复现的。如果一次糟糕的配置变更破坏了生产环境，你可以查看 Git 日志，准确了解改了什么、谁改的、何时改的。然后你回滚该提交，就回到了正常工作的状态。这远比某人在服务器上手动编辑配置、却不留任何操作记录要好得多。

几个能帮你省去头疼的实用技巧。第一，编写有意义的提交信息——“fix bug”在六个月后什么也说明不了，但“Fix nginx timeout by increasing proxy_read_timeout to 300s”则说明了一切。第二，经常以小而合乎逻辑的粒度提交，而不是在一天结束时来一次巨型提交。第三，学习 `git diff`（显示改了什么）、`git stash`（临时搁置你的改动）和 `git blame`（显示文件的每一行最后是谁修改的）。在调试过程中，这三条命令会成为你最好的朋友。

有一件事常让初学者困惑：Git 和 GitHub 不是一回事。Git 是运行在你本地机器上的版本控制工具。GitHub 是一个托管 Git 仓库的 Web 平台，并增加了拉取请求、issue 和 actions 等协作功能。你可以不使用 GitHub 而只用 Git，但在实践中，几乎每个人都会使用某种远程托管平台。

<!-- ZH_RESOURCES -->
- [Git 官方文档 - 入门](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control) -- type: docs, time: 1h
- [Learn Git Branching - 交互式教程](https://learngitbranching.js.org/) -- type: interactive, time: 2h
- [GitHub Skills - GitHub 入门](https://skills.github.com/) -- type: course, time: 1h
- [The Missing Semester - 版本控制（MIT）](https://missing.csail.mit.edu/2020/version-control/) -- type: course, time: 1h
- [Oh Shit, Git!?! - 常见 Git 错误与修复方法](https://ohshitgit.com/) -- type: reference, time: 15m

<!-- ZH_UI -->
1. 初始化仓库、提交更改并查看日志
2. 创建分支、修改并合并回去
3. 将代码推送到 GitHub
4. 我能跟踪代码了。现在让我写点更强大的东西。
5. 我现在能跟踪更改，也有了合适的编辑器工作流。接下来我想停止手工重复劳动——运行相同的命令序列、复制相同的文件。脚本是解决之道吗？实践中它到底是什么样子？
