---
id: package-management
title: Package Management
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: >-
        I keep typing the same install commands over and over on every new
        server. Can I just write a script to do all of this?
      detail: >-
        Every time I set up a machine I'm running the same twenty apt install
        commands, copying the same config files, setting the same permissions.
        It's tedious and I keep forgetting steps. There has to be a way to
        just write this down once and run it.
difficulty: 1
tags:
  - apt
  - yum
  - dnf
  - apk
  - packages
  - repositories
  - dependencies
category: concept
milestones:
  - 'Install, update, and remove a package using your distro''s package manager'
  - Explain what a repository is and how dependencies work
  - Search for packages from the command line
title_zh: "包管理"

---


On Linux, you do not usually download installers from websites like you do on Windows or macOS. Software is managed through a **package manager** — a tool that installs, updates, and removes programs while automatically handling dependencies. It knows that installing Nginx also requires OpenSSL, and it fetches both for you. Every Linux distribution has one, and using it correctly is how you keep servers secure, reproducible, and maintainable.

<!-- DEEP_DIVE -->

A **package** is a bundled piece of software — the compiled program, its configuration files, documentation, and metadata about what other packages it depends on. Packages live in **repositories** (repos) — online servers that your package manager knows how to talk to. When you run `sudo apt install nginx`, your system checks its configured repositories, finds the Nginx package, resolves all its dependencies, downloads everything, and installs it in the right locations. This is massively better than manually downloading software because the package manager tracks what is installed, can upgrade everything at once, and can cleanly remove software without leaving orphaned files behind.

**The major package managers you will encounter:**

- **APT** (`apt`, `apt-get`) — used by Debian, Ubuntu, and their derivatives. Packages are `.deb` files. `sudo apt update` refreshes the package list from repos. `sudo apt install <package>` installs. `sudo apt upgrade` upgrades all installed packages. `apt search <query>` finds packages. This is probably the one you will use most.
- **YUM / DNF** — used by RHEL, CentOS, Fedora, Rocky Linux. Packages are `.rpm` files. DNF is the newer replacement for YUM (same commands, better dependency resolution). `sudo dnf install <package>`, `sudo dnf update`, `dnf search <query>`.
- **APK** — used by Alpine Linux. Lightweight and fast, designed for containers. `apk add <package>`, `apk update`, `apk search <query>`. You will encounter this when working with Docker images based on Alpine.

**Why `sudo`?** Installing software modifies system directories (`/usr/bin`, `/etc`, `/lib`). Only root can write to these locations. That is why you need `sudo` for install commands. This is the users-and-permissions model in action — it prevents a random user from installing malicious software system-wide.

**Repositories and trust.** Your system comes configured with official repositories maintained by the distribution. These packages are tested and signed — when you install from an official repo, you can be reasonably confident the software is not tampered with. Adding third-party repositories (PPAs on Ubuntu, EPEL on RHEL) gives you access to more software but requires you to trust the maintainer. In production environments, many companies run their own internal package mirrors to control exactly what software is available and ensure reproducibility.

**Dependencies** are the reason package managers exist. Real software does not exist in isolation. Nginx depends on OpenSSL for HTTPS. PostgreSQL depends on system libraries for locale handling. A package manager resolves the entire dependency tree — if package A needs B, and B needs C and D, it installs all of them in the right order. This is also why you should never install software by downloading random binaries and copying them to `/usr/local/bin` — the package manager cannot track those, cannot update them, and cannot resolve their dependencies.

**Security updates** are critical for SRE work. When a vulnerability is discovered in OpenSSL or the Linux kernel, the distribution maintainers release a patched package. Running `sudo apt update && sudo apt upgrade` (or the equivalent for your distro) pulls in those patches. Many production environments automate this with unattended upgrades for security patches. Not keeping packages updated is one of the most common ways servers get compromised.

A practical exercise: try `apt list --installed` (or `dnf list installed`) to see every package on your system — you will be surprised how many there are. Then run `apt show nginx` to see a package's metadata, including its dependencies. Install something, check where its files were placed with `dpkg -L nginx` (or `rpm -ql nginx`), then remove it cleanly with `apt remove nginx`.

<!-- RESOURCES -->

- [APT Package Management - Ubuntu Documentation](https://ubuntu.com/server/docs/package-management) -- type: reference, time: 30m
- [DNF Command Reference - Fedora Docs](https://docs.fedoraproject.org/en-US/quick-docs/dnf/) -- type: reference, time: 20m
- [How APT and dpkg Work - Debian Handbook](https://www.debian.org/doc/manuals/debian-handbook/apt.en.html) -- type: reference, time: 45m
- [Alpine Linux Package Management](https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper) -- type: reference, time: 15m
- [Linux Package Management Basics - Linode](https://www.linode.com/docs/guides/linux-package-management-overview/) -- type: tutorial, time: 25m

<!-- ZH_SUMMARY -->
在 Linux 上，通常不会像在 Windows 或 macOS 上那样从网站下载安装程序。软件通过**包管理器**来管理——这是一种安装、更新和删除程序的工具，同时会自动处理依赖关系。它知道安装 Nginx 还需要 OpenSSL，并会为你一并获取两者。每个 Linux 发行版都有一个包管理器，正确使用它是保持服务器安全、可复现和可维护的关键。

<!-- ZH_DEEP_DIVE -->
**包**是打包好的软件——编译后的程序、配置文件、文档，以及关于它依赖哪些其他包的元数据。包存放在**仓库**（repo）中——即你的包管理器知道如何与之通信的在线服务器。当你运行 `sudo apt install nginx` 时，系统会检查已配置的仓库，找到 Nginx 包，解析其所有依赖，下载所有内容，并将其安装到正确的位置。这比手动下载软件要好得多，因为包管理器会跟踪已安装的内容，可以一次性升级所有内容，并且可以干净地卸载软件而不留下孤立文件。

**你会遇到的主要包管理器：**

- **APT**（`apt`、`apt-get`）——用于 Debian、Ubuntu 及其衍生版本。包是 `.deb` 文件。`sudo apt update` 从仓库刷新包列表。`sudo apt install <package>` 安装。`sudo apt upgrade` 升级所有已安装的包。`apt search <query>` 查找包。这可能是你最常使用的那个。
- **YUM / DNF**——用于 RHEL、CentOS、Fedora、Rocky Linux。包是 `.rpm` 文件。DNF 是 YUM 的较新替代品（命令相同，依赖解析更好）。`sudo dnf install <package>`、`sudo dnf update`、`dnf search <query>`。
- **APK**——用于 Alpine Linux。轻量且快速，专为容器设计。`apk add <package>`、`apk update`、`apk search <query>`。你在处理基于 Alpine 的 Docker 镜像时会遇到它。

**为什么需要 `sudo`？** 安装软件会修改系统目录（`/usr/bin`、`/etc`、`/lib`）。只有 root 才能写入这些位置。这就是安装命令需要 `sudo` 的原因。这是用户与权限模型的实际体现——它防止普通用户在全系统范围内安装恶意软件。

**仓库与信任。** 你的系统预配置了由发行版维护的官方仓库。这些包经过测试和签名——当你从官方仓库安装时，你可以相当确信软件没有被篡改。添加第三方仓库（Ubuntu 上的 PPA、RHEL 上的 EPEL）让你能访问更多软件，但需要你信任其维护者。在生产环境中，许多公司运行自己的内部包镜像，以精确控制可用的软件并确保可复现性。

**依赖**是包管理器存在的原因。真实的软件不会孤立存在。Nginx 依赖 OpenSSL 来实现 HTTPS。PostgreSQL 依赖系统库来处理区域设置。包管理器会解析整个依赖树——如果包 A 需要 B，而 B 需要 C 和 D，它会按正确顺序安装所有这些包。这也是为什么你永远不应该通过下载随机二进制文件并将其复制到 `/usr/local/bin` 来安装软件——包管理器无法跟踪这些文件，无法更新它们，也无法解析它们的依赖。

**安全更新**对 SRE 工作至关重要。当 OpenSSL 或 Linux 内核中发现漏洞时，发行版维护者会发布修补后的包。运行 `sudo apt update && sudo apt upgrade`（或你的发行版对应的命令）会拉取这些补丁。许多生产环境通过无人值守升级来自动化安全补丁的安装。不保持包更新是服务器被入侵的最常见方式之一。

一个实践练习：尝试 `apt list --installed`（或 `dnf list installed`）查看系统上的每个包——你会惊讶于数量之多。然后运行 `apt show nginx` 查看包的元数据，包括其依赖。安装一些东西，用 `dpkg -L nginx`（或 `rpm -ql nginx`）检查其文件被放置在哪里，然后用 `apt remove nginx` 干净地移除它。

<!-- ZH_RESOURCES -->
- [APT 包管理 - Ubuntu 文档](https://ubuntu.com/server/docs/package-management) -- 类型：参考，时间：30m
- [DNF 命令参考 - Fedora 文档](https://docs.fedoraproject.org/en-US/quick-docs/dnf/) -- 类型：参考，时间：20m
- [APT 和 dpkg 如何工作 - Debian 手册](https://www.debian.org/doc/manuals/debian-handbook/apt.en.html) -- 类型：参考，时间：45m
- [Alpine Linux 包管理](https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper) -- 类型：参考，时间：15m
- [Linux 包管理基础 - Linode](https://www.linode.com/docs/guides/linux-package-management-overview/) -- 类型：教程，时间：25m

<!-- ZH_UI -->
1. 使用发行版的包管理器安装、更新和移除软件包
2. 解释什么是软件仓库以及依赖关系如何运作
3. 从命令行搜索软件包
4. 我在每台新服务器上反复输入相同的安装命令。能不能写个脚本一次性完成这些？
5. 每次配置机器我都要运行同样的二十条 apt install 命令、复制相同的配置文件、设置相同的权限。既繁琐又总忘步骤。总该有办法把这些写下来一次然后直接运行吧。
