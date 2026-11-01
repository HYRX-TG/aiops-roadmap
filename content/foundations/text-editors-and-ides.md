---
id: text-editors-and-ides
title: Text Editors & IDEs
zone: foundations
edges:
  to:
    - id: version-control-git
      question: I can edit files. But how do I track changes and collaborate?
      detail: >-
        I just broke something that was working yesterday and I have no idea
        what I changed. I've been overwriting files with no history of what they
        looked like before. And if someone else touches the same files at the
        same time, everything will be a mess. How do people actually manage
        this?
difficulty: 1
tags:
  - vim
  - nano
  - vscode
  - editors
  - ide
  - tools
category: tool
milestones:
  - Edit a file using vim or nano
  - Set up VS Code with a useful extension
  - Edit a configuration file on a remote server
title_zh: "文本编辑器与 IDE"

---


Code is just text, and you need a tool to write it. The tool you choose -- whether it is a minimal terminal editor like vim or a full-featured IDE like VS Code -- shapes your daily workflow more than almost any other decision. Learning at least one terminal-based editor is non-negotiable for SRE work because you will inevitably need to edit a config file on a remote server where VS Code is not available.

<!-- DEEP_DIVE -->

Let's start with the terminal editors because they are the ones that will save you in a pinch. **nano** is the friendly one -- open a file with `nano myfile.txt`, make your changes, press `Ctrl+O` to save, and `Ctrl+X` to exit. The commands are listed right at the bottom of the screen. It is the editor you reach for when you just need to quickly change one line in a config file and move on with your life.

**vim** is the powerful one, and it has a famously steep learning curve. Vim operates in modes: when you open a file with `vim myfile.txt`, you start in **Normal mode** where key presses are commands, not text input. Press `i` to enter **Insert mode** where you can actually type. Press `Esc` to go back to Normal mode. Type `:wq` and press Enter to save and quit. Type `:q!` to quit without saving. That is genuinely enough to get started. The internet is full of jokes about people getting trapped in vim, but once you learn the basics, it becomes incredibly efficient. The motions (`w` to jump a word, `dd` to delete a line, `yy` to copy a line, `p` to paste) let you edit text at the speed of thought once they become muscle memory.

Now for the tool you will probably spend most of your time in: **VS Code**. It has won the editor wars for good reason -- it is free, fast enough, has an enormous extension ecosystem, and works with every language. Install it, then add a few extensions to make your life better: the Python extension for Python development, GitLens for powerful Git integration, and Remote - SSH for editing files on remote machines directly from your local VS Code. That last one is a game-changer -- it bridges the gap between "comfortable local editor" and "needing to edit files on a server."

Why does editor choice matter for SRE and DevOps work specifically? Because you will constantly switch between contexts. One minute you are writing a Python script locally in VS Code, the next you are SSH-ed into a production server editing an Nginx config with vim, and then you are reviewing a Terraform file in a pull request. Being comfortable in at least one graphical editor and one terminal editor means you are never stuck. You do not need to master vim's every feature -- just know enough to open, edit, save, and quit without panicking.

Configuration files deserve special mention. As an SRE, you will edit YAML files (Kubernetes manifests, CI/CD pipelines), JSON files (tool configs), TOML files, INI files, and more. These files are extremely sensitive to formatting -- a single wrong indent in a YAML file can break your entire deployment. This is where editor features like syntax highlighting and auto-indentation go from "nice to have" to "preventing outages." Configure your editor to show whitespace characters and use consistent indentation, and future-you will be grateful.

<!-- RESOURCES -->

- [OpenVim - Interactive Vim Tutorial](https://www.openvim.com/) -- type: tutorial, time: 30m
- [VS Code Getting Started - Official Docs](https://code.visualstudio.com/docs/getstarted/introvideos) -- type: tutorial, time: 1h
- [The Missing Semester - Editors (MIT)](https://missing.csail.mit.edu/2020/editors/) -- type: course, time: 1h
- [Vim Adventures - Learn Vim by Playing a Game](https://vim-adventures.com/) -- type: interactive, time: 2h
- [nano Editor Basics - Linuxize](https://linuxize.com/post/how-to-use-nano-text-editor/) -- type: tutorial, time: 15m

<!-- ZH_SUMMARY -->
代码不过是文本，你需要一个工具来编写它。你所选择的工具——无论是像 vim 这样极简的终端编辑器，还是像 VS Code 这样功能齐全的 IDE——对日常工作流程的影响几乎超过其他任何决定。至少学习一种基于终端的编辑器对 SRE 工作而言是不可妥协的，因为你不可避免地需要在无法使用 VS Code 的远程服务器上编辑配置文件。

<!-- ZH_DEEP_DIVE -->
先从终端编辑器说起，因为它们能在关键时刻救你一命。**nano** 是那个友好的编辑器——用 `nano myfile.txt` 打开文件，做出修改，按 `Ctrl+O` 保存，按 `Ctrl+X` 退出。命令就列在屏幕底部。当你只需要快速修改配置文件中的一行然后继续干活时，它就是你会去用的编辑器。

**vim** 是那个强大的编辑器，它的学习曲线出了名地陡峭。Vim 以模式运行：当你用 `vim myfile.txt` 打开文件时，你处于 **Normal 模式**，此时按键是命令，而不是文本输入。按 `i` 进入 **Insert 模式**，在那里你才能真正输入。按 `Esc` 回到 Normal 模式。输入 `:wq` 并按回车保存并退出。输入 `:q!` 不保存直接退出。这些真的足够你入门了。网上到处都是关于人们被困在 vim 里的段子，但一旦你学会了基础，它就会变得极其高效。那些动作（`w` 跳过一个单词，`dd` 删除一行，`yy` 复制一行，`p` 粘贴）一旦成为肌肉记忆，就能让你以思维的速度编辑文本。

现在说说你可能会花大部分时间使用的工具：**VS Code**。它赢得了编辑器之战是有充分理由的——它免费、足够快、拥有庞大的扩展生态，并且支持所有语言。安装它，然后添加几个扩展让你的生活更美好：用于 Python 开发的 Python 扩展、用于强大 Git 集成的 GitLens，以及用于直接从本地 VS Code 编辑远程机器上文件的 Remote - SSH。最后一个堪称改变游戏规则——它弥合了“舒适的本地编辑器”和“需要在服务器上编辑文件”之间的鸿沟。

为什么编辑器选择对 SRE 和 DevOps 工作尤其重要？因为你会不断在上下文之间切换。前一分钟你还在本地用 VS Code 写 Python 脚本，下一分钟你就通过 SSH 登录到生产服务器用 vim 编辑 Nginx 配置，然后你又在 pull request 中审查一个 Terraform 文件。至少熟练使用一个图形化编辑器和一个终端编辑器，意味着你永远不会陷入困境。你不需要掌握 vim 的每一个功能——只要知道足够多的东西，能打开、编辑、保存和退出而不慌张就行。

配置文件值得特别一提。作为 SRE，你会编辑 YAML 文件（Kubernetes manifest、CI/CD 流水线）、JSON 文件（工具配置）、TOML 文件、INI 文件等等。这些文件对格式极其敏感——YAML 文件中一个错误的缩进就可能破坏你的整个部署。这正是编辑器的语法高亮和自动缩进等功能从“锦上添花”变成“防止故障”的地方。配置你的编辑器显示空白字符并使用一致的缩进，未来的你会感激不尽。

<!-- ZH_RESOURCES -->
- [OpenVim - 交互式 Vim 教程](https://www.openvim.com/) -- 类型：教程，时长：30 分钟
- [VS Code 入门 - 官方文档](https://code.visualstudio.com/docs/getstarted/introvideos) -- 类型：教程，时长：1 小时
- [缺失的一课 - 编辑器（MIT）](https://missing.csail.mit.edu/2020/editors/) -- 类型：课程，时长：1 小时
- [Vim Adventures - 通过游戏学习 Vim](https://vim-adventures.com/) -- 类型：交互式，时长：2 小时
- [nano 编辑器基础 - Linuxize](https://linuxize.com/post/how-to-use-nano-text-editor/) -- 类型：教程，时长：15 分钟

<!-- ZH_UI -->
1. 使用 vim 或 nano 编辑文件
2. 配置 VS Code 并安装实用扩展
3. 在远程服务器上编辑配置文件
4. 我会编辑文件了。但如何跟踪变更并协作？
5. 我刚刚弄坏了昨天还好好的东西，完全不知道改了什么。我一直在覆盖文件，没有保留它们之前样子的历史记录。如果别人同时动了同样的文件，一切都会乱套。人们到底是怎么管理这个的？
