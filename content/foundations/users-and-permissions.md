---
id: users-and-permissions
title: Users & Permissions
zone: foundations
edges:
  to:
    - id: package-management
      question: I understand who can do what. How do I install software?
      detail: >-
        I keep getting 'permission denied' errors when I try to install things.
        And when I do get it working by using sudo, I'm not sure what I actually
        just did or whether I should have. How does software installation work
        on Linux, and why does it need elevated privileges?
difficulty: 1
tags:
  - users
  - groups
  - permissions
  - chmod
  - chown
  - sudo
  - root
  - security
category: concept
milestones:
  - Explain the difference between root and a regular user
  - Change file ownership and permissions with chown and chmod
  - Use sudo and explain why running everything as root is dangerous
title_zh: "用户与权限"

---


Linux is a multi-user system. Even if you are the only person using your laptop, Linux still thinks in terms of users, groups, and permissions. Every file is owned by someone. Every process runs as someone. And the all-powerful **root** user can do literally anything — including destroying the entire system with a single command. Understanding this permission model is how you keep systems secure and how you avoid the dreaded "Permission denied" errors that will otherwise haunt you.

<!-- DEEP_DIVE -->

Every Linux system has users, and every user has a numeric **UID** (User ID). The most important user is **root** (UID 0) — the superuser, the administrator, the account that can read any file, kill any process, and modify any system configuration. Running commands as root is like driving without a seatbelt — it works great until it does not. A typo as root can wipe the entire filesystem. This is why modern Linux practice is to use a regular user account and escalate to root privileges only when needed, using `sudo`.

The `sudo` command ("superuser do") lets an authorized user run a single command with root privileges. Instead of logging in as root and running `apt update`, you run `sudo apt update` from your regular account. The system logs who ran what with sudo, creating an audit trail. The configuration file `/etc/sudoers` controls who is allowed to use sudo — never edit it directly, always use `visudo`, which validates the syntax before saving (a broken sudoers file can lock you out of root access entirely).

**Groups** are how Linux organizes users. Every user belongs to at least one group (their primary group), and can belong to many. Groups simplify permission management — instead of giving ten users individual access to a directory, you create a group, add the users to it, and give the group access. Common groups you will encounter: `sudo` or `wheel` (users who can use sudo), `docker` (users who can run Docker commands), `www-data` (the web server user).

File permissions in Linux follow a simple model: every file and directory has three sets of permissions for three categories — **owner**, **group**, and **others** (everyone else). Each set has three permission bits:

- **r** (read) — can view the file contents or list a directory
- **w** (write) — can modify the file or create/delete files in a directory
- **x** (execute) — can run the file as a program or enter a directory

When you run `ls -la`, you see something like `-rwxr-xr--`. Breaking that down: the owner can read, write, and execute; the group can read and execute; others can only read. The `chmod` command changes permissions. You can use symbolic notation (`chmod u+x script.sh` — add execute for the owner) or octal notation (`chmod 755 script.sh` — rwx for owner, r-x for group and others). For SRE work, the octal numbers you will use constantly are `644` (files: owner reads/writes, everyone else reads), `755` (directories and scripts: owner full access, everyone else read/execute), and `600` (private files like SSH keys: owner only).

The `chown` command changes ownership. `chown alice:developers myfile.txt` sets the owner to alice and the group to developers. You will use this frequently when deploying applications — web server files need to be owned by the web server user, application logs need to be writable by the application user.

**Why this matters for SRE:** Half of the "it works on my machine but not on the server" problems come down to permissions. A deployment script that cannot write to `/var/www` because it is running as the wrong user. An application that crashes because it cannot read its config file. A cron job that fails silently because it runs as root but the script expects a regular user's environment. SSH key authentication failing because the key file permissions are too open (`chmod 600 ~/.ssh/id_rsa` — SSH refuses to use a key that others can read). Understanding the permission model turns these from mysterious failures into obvious fixes.

A practical exercise: create a file, check its permissions with `ls -la`, change them with `chmod`, change ownership with `chown`, then try to access it as a different user. Notice how the system enforces the rules. Then try the same with a directory — notice that `x` on a directory means something different (the ability to `cd` into it) than `x` on a file (the ability to execute it).

<!-- RESOURCES -->

- [Linux File Permissions Explained - DigitalOcean](https://www.digitalocean.com/community/tutorials/linux-permissions-basics-and-how-to-use-umask-on-a-vps) -- type: tutorial, time: 30m
- [Understanding Linux File Permissions - Red Hat](https://www.redhat.com/sysadmin/linux-file-permissions-explained) -- type: article, time: 20m
- [Sudo Explained - Linuxize](https://linuxize.com/post/sudo-command-in-linux/) -- type: tutorial, time: 15m
- [Linux Users and Groups - Arch Wiki](https://wiki.archlinux.org/title/Users_and_groups) -- type: reference, time: 30m
- [chmod Calculator](https://chmod-calculator.com/) -- type: tool, time: 5m

<!-- ZH_SUMMARY -->
Linux 是一个多用户系统。即使你是唯一使用笔记本电脑的人，Linux 仍然以用户、组和权限的视角来思考。每个文件都有其所有者。每个进程都以某个用户的身份运行。而拥有至高权力的 **root** 用户可以真正做到任何事情——包括用一条命令摧毁整个系统。理解这一权限模型，是保障系统安全的关键，也是避免那些否则会一直困扰你的、令人头疼的“Permission denied”错误的关键。

<!-- ZH_DEEP_DIVE -->
每个 Linux 系统都有用户，每个用户都有一个数字 **UID**（用户 ID）。最重要的用户是 **root**（UID 0）——超级用户、管理员，这个账户可以读取任何文件、终止任何进程、修改任何系统配置。以 root 身份运行命令就像不系安全带开车——一切顺利时没问题，直到出问题为止。root 的一个拼写错误就可能抹掉整个文件系统。这就是为什么现代 Linux 实践是使用普通用户账户，只在需要时通过 `sudo` 提升到 root 权限。

`sudo` 命令（“superuser do”）允许授权用户以 root 权限运行单条命令。你不必登录为 root 再运行 `apt update`，而是从普通账户运行 `sudo apt update`。系统会记录谁用 sudo 运行了什么，形成审计轨迹。配置文件 `/etc/sudoers` 控制谁可以使用 sudo——绝不要直接编辑它，始终使用 `visudo`，它会在保存前校验语法（损坏的 sudoers 文件可能让你完全无法获得 root 访问权限）。

**组**是 Linux 组织用户的方式。每个用户至少属于一个组（其主组），并且可以属于多个组。组简化了权限管理——不必为十个用户分别授予对某个目录的访问权限，而是创建一个组，将用户加入该组，再给该组授予访问权限。你会遇到的常见组：`sudo` 或 `wheel`（可以使用 sudo 的用户）、`docker`（可以运行 Docker 命令的用户）、`www-data`（Web 服务器用户）。

Linux 中的文件权限遵循一个简单模型：每个文件和目录都有三组权限，分别对应三个类别——**所有者**、**组**和**其他人**（其他所有人）。每组有三个权限位：

- **r**（读）——可以查看文件内容或列出目录内容
- **w**（写）——可以修改文件，或在目录中创建/删除文件
- **x**（执行）——可以将文件作为程序运行，或进入目录

当你运行 `ls -la` 时，会看到类似 `-rwxr-xr--` 的内容。拆解来看：所有者可以读、写、执行；组可以读、执行；其他人只能读。`chmod` 命令用于更改权限。你可以使用符号表示法（`chmod u+x script.sh`——为所有者添加执行权限）或八进制表示法（`chmod 755 script.sh`——所有者为 rwx，组和其他人为 r-x）。对于 SRE 工作，你会经常使用的八进制数字是 `644`（文件：所有者读/写，其他人读）、`755`（目录和脚本：所有者完全访问，其他人读/执行）和 `600`（私有文件，如 SSH 密钥：仅所有者）。

`chown` 命令用于更改所有权。`chown alice:developers myfile.txt` 将所有者设为 alice，组设为 developers。你在部署应用时会频繁使用它——Web 服务器文件需要由 Web 服务器用户拥有，应用日志需要由应用用户可写。

**为什么这对 SRE 很重要：** 一半的“在我机器上能跑，但在服务器上不行”问题都归结为权限。部署脚本因为以错误的用户运行而无法写入 `/var/www`。应用因为无法读取其配置文件而崩溃。cron 任务因为以 root 运行但脚本期望普通用户的环境而静默失败。SSH 密钥认证失败，因为密钥文件权限过于开放（`chmod 600 ~/.ssh/id_rsa`——SSH 拒绝使用其他人可读的密钥）。理解权限模型可以将这些神秘的故障变成显而易见的修复。

一个实践练习：创建一个文件，用 `ls -la` 检查其权限，用 `chmod` 更改权限，用 `chown` 更改所有权，然后尝试以另一个用户身份访问它。注意系统如何强制执行这些规则。然后对目录做同样的操作——注意目录上的 `x` 与文件上的 `x` 含义不同（前者是 `cd` 进入目录的能力，后者是执行文件的能力）。

<!-- ZH_RESOURCES -->
- [Linux 文件权限详解 - DigitalOcean](https://www.digitalocean.com/community/tutorials/linux-permissions-basics-and-how-to-use-umask-on-a-vps) -- 类型: 教程, 时长: 30m
- [理解 Linux 文件权限 - Red Hat](https://www.redhat.com/sysadmin/linux-file-permissions-explained) -- 类型: 文章, 时长: 20m
- [Sudo 详解 - Linuxize](https://linuxize.com/post/sudo-command-in-linux/) -- 类型: 教程, 时长: 15m
- [Linux 用户与组 - Arch Wiki](https://wiki.archlinux.org/title/Users_and_groups) -- 类型: 参考, 时长: 30m
- [chmod 计算器](https://chmod-calculator.com/) -- 类型: 工具, 时长: 5m

<!-- ZH_UI -->
1. 解释 root 用户与普通用户的区别
2. 使用 chown 和 chmod 更改文件所有权和权限
3. 使用 sudo，并解释为什么以 root 身份运行一切是危险的
4. 我明白谁可以做什么。如何安装软件？
5. 我在尝试安装东西时总是遇到“permission denied”错误。而当我用 sudo 让它工作时，我不确定自己实际做了什么，或者是否应该这么做。Linux 上的软件安装是如何工作的，为什么它需要提升的权限？
