---
id: ansible-intro
title: Configuration Management with Ansible
zone: delivery
edges:
  to:
    - id: terraform-basics
      question: >-
        I understand Ansible for server configuration. Now I want to provision
        the infrastructure itself.
      detail: >-
        Ansible configures servers that already exist. But who creates the
        servers in the first place? I'm still clicking through the cloud console
        to spin up infrastructure, and that feels just as manual as the problem
        I just solved. There must be a way to define the infrastructure itself
        as code.
difficulty: 2
tags:
  - ansible
  - configuration-management
  - automation
  - playbooks
  - idempotency
category: tool
milestones:
  - Install Ansible and connect to a server via SSH
  - Write a playbook that installs a package and starts a service
  - Understand what idempotency means and why it matters in automation
  - Use variables and templates in a playbook
title_zh: "使用 Ansible 进行配置管理"

---


Ansible connects to servers over SSH and applies configuration using YAML playbooks. No agent installed on the target server. No daemon running anywhere. Just SSH, Python on the remote host, and a YAML file describing what the server should look like.

It's the standard tool for "given a fresh server, make it ready to run my application."

<!-- DEEP_DIVE -->

## How Ansible works

Ansible is agentless. You run it from your local machine (or CI runner). It SSHes into each target server, transfers and runs a small Python script, applies your configuration, then disconnects.

The targets are defined in an **inventory** file:

```ini
[webservers]
web1.example.com
web2.example.com

[databases]
db1.example.com
```

Or a simple list:

```ini
[all]
192.168.1.100
192.168.1.101
```

## A playbook

A playbook is the unit of work in Ansible. It maps groups from your inventory to a list of tasks:

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: true       # sudo

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: true

    - name: Copy nginx config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-enabled/myapp.conf
      notify: Reload nginx

    - name: Enable and start nginx
      systemd:
        name: nginx
        enabled: true
        state: started

  handlers:
    - name: Reload nginx
      systemd:
        name: nginx
        state: reloaded
```

Run it:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Ansible connects to each `webserver` host, installs nginx, copies the config, and ensures the service is running.

## Idempotency

The key property of Ansible tasks is **idempotency**: running the same playbook twice produces the same result, with no unintended side effects the second time.

`apt: state: present` means "ensure nginx is installed." If it's already installed, Ansible does nothing. It doesn't reinstall it. It doesn't fail. It reports `ok` and moves on.

This is why Ansible (and IaC tools generally) use declarative language: you describe the desired state, not the steps to get there. The tool figures out whether anything needs doing.

Compare this to a shell script: `apt install nginx` fails with an error if nginx is already installed (unless you add `-y` and ignore errors). Shell scripts are not idempotent by default.

## Variables and templates

Variables make playbooks reusable across environments:

```yaml
vars:
  app_port: 8000
  app_name: myapp

tasks:
  - name: Configure app
    template:
      src: app.conf.j2
      dest: /etc/nginx/sites-enabled/{{ app_name }}.conf
```

Templates use Jinja2 syntax. `{{ app_port }}` in the template gets replaced with `8000` at runtime.

Variables can be defined in the playbook, in separate `group_vars/` files (per inventory group), or passed on the command line with `-e`. This lets you use the same playbook for staging and production, with different variable values.

## Roles

For larger setups, **roles** are reusable bundles of tasks, handlers, templates, and defaults. A role for `nginx` contains everything needed to install and configure it. You can share roles on Ansible Galaxy (the community registry) or write your own.

```yaml
roles:
  - nginx
  - myapp
  - monitoring
```

## Ansible vs shell scripts

Shell scripts get the job done but they're brittle: they fail on partial runs, aren't idempotent, and become unmaintainable as they grow. Ansible gives you the same capability with idempotency, error handling, and structure built in.

Shell scripts are still appropriate for simple one-time tasks. For recurring configuration management — servers that need to be kept in a defined state — Ansible is the right tool.

<!-- RESOURCES -->

- [Ansible Documentation: Getting Started](https://docs.ansible.com/ansible/latest/getting_started/index.html) -- type: reference, time: 20min
- [Ansible Galaxy](https://galaxy.ansible.com/) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
Ansible 通过 SSH 连接服务器，并使用 YAML playbook 应用配置。目标服务器上无需安装 agent。任何地方都不需要运行守护进程。只需要 SSH、远程主机上的 Python，以及一个描述服务器应有状态的 YAML 文件。

它是用于“给定一台全新服务器，使其准备好运行我的应用”的标准工具。

<!-- ZH_DEEP_DIVE -->
## Ansible 的工作原理

Ansible 是无代理的。你从本地机器（或 CI runner）上运行它。它通过 SSH 连接到每台目标服务器，传输并运行一个小型 Python 脚本，应用你的配置，然后断开连接。

目标在 **inventory** 文件中定义：

```ini
[webservers]
web1.example.com
web2.example.com

[databases]
db1.example.com
```

或者一个简单的列表：

```ini
[all]
192.168.1.100
192.168.1.101
```

## Playbook

Playbook 是 Ansible 中的工作单元。它将 inventory 中的组映射到一组任务：

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: true       # sudo

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: true

    - name: Copy nginx config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-enabled/myapp.conf
      notify: Reload nginx

    - name: Enable and start nginx
      systemd:
        name: nginx
        enabled: true
        state: started

  handlers:
    - name: Reload nginx
      systemd:
        name: nginx
        state: reloaded
```

运行它：

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Ansible 连接到每台 `webserver` 主机，安装 nginx，复制配置，并确保服务正在运行。

## 幂等性

Ansible 任务的关键特性是**幂等性**：运行同一个 playbook 两次会产生相同的结果，第二次不会产生意外的副作用。

`apt: state: present` 的意思是“确保 nginx 已安装”。如果它已经安装，Ansible 什么也不做。它不会重新安装。它不会失败。它报告 `ok` 然后继续。

这就是为什么 Ansible（以及一般的 IaC 工具）使用声明式语言：你描述期望的状态，而不是达到该状态的步骤。工具会判断是否需要做任何事情。

将其与 shell 脚本对比：如果 nginx 已经安装，`apt install nginx` 会报错失败（除非你加上 `-y` 并忽略错误）。Shell 脚本默认不是幂等的。

## 变量与模板

变量使 playbook 可以跨环境复用：

```yaml
vars:
  app_port: 8000
  app_name: myapp

tasks:
  - name: Configure app
    template:
      src: app.conf.j2
      dest: /etc/nginx/sites-enabled/{{ app_name }}.conf
```

模板使用 Jinja2 语法。模板中的 `{{ app_port }}` 在运行时会被替换为 `8000`。

变量可以在 playbook 中定义，在单独的 `group_vars/` 文件中定义（按 inventory 组），或者通过命令行用 `-e` 传入。这让你可以用同一个 playbook 用于 staging 和 production，只是变量值不同。

## Roles

对于更大的配置，**roles** 是可复用的任务、handlers、模板和默认值的集合。一个 `nginx` 的 role 包含安装和配置它所需的一切。你可以在 Ansible Galaxy（社区注册中心）上分享 roles，或者编写自己的。

```yaml
roles:
  - nginx
  - myapp
  - monitoring
```

## Ansible 与 shell 脚本

Shell 脚本能完成任务，但它们很脆弱：部分运行时会失败，不是幂等的，并且随着增长会变得难以维护。Ansible 为你提供了相同的能力，同时内置了幂等性、错误处理和结构。

Shell 脚本仍然适用于简单的一次性任务。对于重复性的配置管理——需要保持在定义状态的服务器——Ansible 是正确的工具。

<!-- ZH_RESOURCES -->
- [Ansible 文档：入门](https://docs.ansible.com/ansible/latest/getting_started/index.html) -- 类型：参考，时间：20 分钟
- [Ansible Galaxy](https://galaxy.ansible.com/) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 安装 Ansible 并通过 SSH 连接服务器
2. 编写一个 playbook，安装软件包并启动服务
3. 理解幂等性的含义及其在自动化中的重要性
4. 在 playbook 中使用变量和模板
5. 我已掌握用 Ansible 进行服务器配置。现在我想进一步供给基础设施本身。
6. Ansible 配置的是已存在的服务器。但最初是谁创建这些服务器的？我仍在通过云控制台点击来启动基础设施，这感觉和我刚解决的问题一样手动。一定有办法将基础设施本身定义为代码。
