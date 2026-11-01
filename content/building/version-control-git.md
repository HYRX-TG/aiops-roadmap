---
id: version-control-git
title: Version Control & Git
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: >-
        I can manage my code properly now. How do I actually get it running for
        others?
      detail: >-
        My code is on GitHub but that doesn't mean anyone can actually use it —
        it's still just source code sitting in a repo. I want people to be able
        to open a browser and see a running app. How do I get from here to
        there?
difficulty: 1
tags:
  - git
  - version-control
  - github
  - gitlab
  - collaboration
category: concept
milestones:
  - 'Initialize a Git repo, make commits, and view history'
  - 'Create branches, make changes, and merge them'
  - Push code to GitHub or GitLab and collaborate with others
title_zh: "版本控制与 Git"

---


You have been building your app, and it is getting bigger. You made a change yesterday that broke something, and now you cannot remember what you changed or how to undo it. You are copying folders named `app_v2_final_FINAL` and praying. There has to be a better way — and there is. It is called Git.

<!-- DEEP_DIVE -->

**Git** is a version control system. It tracks every change you make to your code, who made it, and when. Think of it as an unlimited undo button with annotations. Every meaningful change is saved as a **commit** — a snapshot of your entire project at that moment.

```bash
# Start tracking a project
git init

# See what changed
git status

# Stage and commit changes
git add app.py
git commit -m "Add user registration endpoint"

# See the full history
git log --oneline
```

Every commit gets a unique hash (like `a3f82c1`). You can jump back to any commit, compare two commits, or see exactly what changed between them. When something breaks, `git diff` shows you what changed and `git checkout` lets you go back.

**Branches** are where Git gets powerful. A branch is a parallel version of your code. You can create a branch, experiment freely, and if it works, merge it back. If it does not work, delete the branch. Your main code is never touched:

```bash
# Create and switch to a new branch
git checkout -b add-shopping-cart

# Work on your feature... make commits...

# Switch back to main and merge
git checkout main
git merge add-shopping-cart
```

This is how teams work. Each person works on their own branch. Nobody steps on anyone else's work. When a feature is ready, it gets merged into the main branch.

**GitHub** (and GitLab, Bitbucket) is where your Git repository lives online. It is not the same as Git itself — Git is the tool, GitHub is a hosting service. Pushing your code to GitHub gives you:

- A backup of your entire project history
- A place for others to see and contribute to your code
- **Pull requests** — a way to propose changes and have them reviewed before merging
- **Issues** — a way to track bugs and feature requests

```bash
# Connect your local repo to GitHub
git remote add origin https://github.com/you/your-app.git

# Push your code
git push -u origin main
```

**Why does this matter for SRE/DevOps?** Everything in modern operations is code — infrastructure definitions, deployment scripts, monitoring configs, CI/CD pipelines. If it is not in Git, it does not exist. Version control is the foundation of:

- **Infrastructure as Code** — your server setup is versioned just like application code
- **CI/CD pipelines** — automated builds and deployments trigger on Git events
- **Incident response** — `git log` tells you exactly what changed and when, which is critical for debugging production issues
- **Collaboration** — multiple engineers can work on the same system without chaos

The `.gitignore` file tells Git which files to skip — things like compiled binaries, dependency folders (`node_modules/`, `venv/`), and secrets (`.env` files with API keys). Never commit secrets to Git. Once something is in Git history, it is very hard to fully remove.

<!-- RESOURCES -->

- [Pro Git Book (free)](https://git-scm.com/book/en/v2) -- type: book, time: varies
- [GitHub Skills](https://skills.github.com/) -- type: interactive, time: 2h
- [Oh My Git! - Game](https://ohmygit.org/) -- type: interactive, time: 1h
- [Git Branching Tutorial](https://learngitbranching.js.org/) -- type: interactive, time: 1h

<!-- ZH_SUMMARY -->
你一直在开发你的应用，它正变得越来越大。昨天你做了一处改动，结果弄坏了某些功能，现在你既想不起改了什么，也不知道如何撤销。你复制着名为 `app_v2_final_FINAL` 的文件夹，并祈祷一切顺利。一定有更好的办法——确实有。它叫做 Git。

<!-- ZH_DEEP_DIVE -->
**Git** 是一个版本控制系统。它追踪你对代码所做的每一次更改、更改者以及更改时间。可以把它想象成一个带注释的无限撤销按钮。每一次有意义的更改都会保存为一个 **commit** —— 即那一刻整个项目的快照。

```bash
# 开始追踪一个项目
git init

# 查看发生了什么变化
git status

# 暂存并提交更改
git add app.py
git commit -m "Add user registration endpoint"

# 查看完整历史
git log --oneline
```

每个 commit 都会获得一个唯一的哈希值（如 `a3f82c1`）。你可以跳回任意 commit、比较两个 commit，或查看它们之间具体发生了什么变化。当出现问题时，`git diff` 会显示变化内容，`git checkout` 让你回到过去。

**分支** 是 Git 强大之处。分支是代码的并行版本。你可以创建一个分支，自由实验，如果可行就合并回去。如果不可行，就删除该分支。你的主代码永远不会被触碰：

```bash
# 创建并切换到新分支
git checkout -b add-shopping-cart

# 开发你的功能……进行提交……

# 切回 main 并合并
git checkout main
git merge add-shopping-cart
```

团队就是这样协作的。每个人在自己的分支上工作。没有人会干扰他人的工作。当功能就绪时，它会被合并到主分支。

**GitHub**（以及 GitLab、Bitbucket）是你的 Git 仓库在线存放的地方。它和 Git 本身不是一回事 —— Git 是工具，GitHub 是托管服务。将代码推送到 GitHub 可以为你提供：

- 整个项目历史的备份
- 一个供他人查看和贡献代码的地方
- **Pull request** —— 一种在合并前提出更改并让其接受审查的方式
- **Issue** —— 一种追踪 bug 和功能请求的方式

```bash
# 将本地仓库连接到 GitHub
git remote add origin https://github.com/you/your-app.git

# 推送代码
git push -u origin main
```

**这对 SRE/DevOps 为什么重要？** 现代运维中的一切都是代码 —— 基础设施定义、部署脚本、监控配置、CI/CD 流水线。如果它不在 Git 中，它就不存在。版本控制是以下事项的基础：

- **基础设施即代码** —— 你的服务器配置像应用代码一样被版本化
- **CI/CD 流水线** —— 自动化构建和部署由 Git 事件触发
- **事件响应** —— `git log` 准确告诉你发生了什么变化以及何时变化，这对调试生产问题至关重要
- **协作** —— 多名工程师可以协作处理同一系统而不会陷入混乱

`.gitignore` 文件告诉 Git 跳过哪些文件 —— 比如编译后的二进制文件、依赖文件夹（`node_modules/`、`venv/`）以及密钥（包含 API key 的 `.env` 文件）。永远不要将密钥提交到 Git。一旦某些内容进入 Git 历史，就很难彻底移除。

<!-- ZH_RESOURCES -->
- [Pro Git Book（免费）](https://git-scm.com/book/en/v2) -- 类型：书籍，时长：不定
- [GitHub Skills](https://skills.github.com/) -- 类型：互动，时长：2小时
- [Oh My Git! - 游戏](https://ohmygit.org/) -- 类型：互动，时长：1小时
- [Git 分支教程](https://learngitbranching.js.org/) -- 类型：互动，时长：1小时

<!-- ZH_UI -->
1. 初始化 Git 仓库、提交更改并查看历史记录
2. 创建分支、修改代码并合并分支
3. 将代码推送到 GitHub 或 GitLab 并与他人协作
4. 我现在能正确管理代码了。怎样才能真正让它运行起来供他人使用？
5. 我的代码在 GitHub 上，但这并不意味着任何人都能实际使用它——它仍然只是躺在仓库里的源代码。我希望人们能打开浏览器看到一个运行中的应用。我该如何从这里走到那一步？
