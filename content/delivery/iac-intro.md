---
id: iac-intro
title: Infrastructure as Code
zone: delivery
edges:
  to:
    - id: terraform-basics
      question: IaC makes sense. Show me Terraform.
      detail: >-
        I get the concept — but what does it actually look like to write IaC? I
        want to see what a real Terraform config looks like and understand what
        happens when I run it.
    - id: ansible-intro
      question: What about configuring the servers themselves? I've heard of Ansible.
      detail: >-
        Terraform provisions infrastructure — it creates servers. Ansible
        configures what's on them — it installs packages, writes config files,
        manages services. They solve different problems and are often used
        together.
difficulty: 1
tags:
  - iac
  - infrastructure-as-code
  - terraform
  - ansible
  - automation
  - devops
category: concept
milestones:
  - Explain what 'snowflake servers' are and why they're a problem
  - Describe the difference between declarative and imperative IaC
  - >-
    Understand the difference between provisioning (Terraform) and configuration
    (Ansible)
title_zh: "基础设施即代码"

---


You've automated your deployments — but the servers they deploy to were created by hand. Someone logged into a cloud console, clicked through a wizard, and tweaked things until it worked. That server exists nowhere except in AWS (or Hetzner, or DigitalOcean) and in its creator's memory.

Infrastructure as Code means describing your infrastructure in version-controlled files. The same discipline CI/CD brings to application code, applied to the servers themselves.

<!-- DEEP_DIVE -->

## The snowflake server problem

A server that was set up manually accumulates changes over time. A package installed to debug an issue. A config file tweaked to fix a problem. An extra port opened and forgotten. Over months, the server drifts from any documented state.

This is called a **snowflake server** — unique, fragile, and irreproducible. When it dies, you spend days trying to recreate what you had. When you need a second one (staging, load balancing), you can't.

IaC solves this by making the code the truth. The server is always reproducible because the code that creates it is in version control. If it dies, you run the code again and get an identical replacement.

## Declarative vs imperative

**Declarative IaC** (Terraform, Pulumi): you describe the desired end state. "I want a server with 2 CPUs, 4GB RAM, Ubuntu 24.04, in us-east-1." The tool figures out what actions to take to get there.

**Imperative IaC** (Ansible, shell scripts): you describe the steps to take. "Run apt update. Install nginx. Copy this config file. Restart the service." You control the sequence.

Both have their place. Declarative is better for provisioning (what resources should exist). Imperative is better for configuration (what should be running on them).

## Two problems, two tools

There's a common source of confusion: Terraform and Ansible seem to overlap. They don't — they solve adjacent problems.

**Terraform** provisions infrastructure. It creates cloud resources: servers, networks, load balancers, DNS records, storage buckets. It knows nothing about what's running inside those servers.

**Ansible** configures what's on a server. It connects over SSH and runs tasks: install nginx, write a config file, enable a systemd service. It doesn't provision the server — it expects the server to already exist.

In practice, they're often used together: Terraform creates the infrastructure, Ansible configures it. Or one without the other, depending on what you need.

## IaC in CI/CD

Once your infrastructure is code, you can run it in your pipeline. A `terraform plan` on every pull request shows what infrastructure changes would result. A `terraform apply` on merge actually makes those changes. Your infrastructure gets the same review, testing, and audit trail as your application code.

This is the end goal: your entire stack — application code and infrastructure — reproduced from Git, deployed automatically, and never hand-configured.

<!-- RESOURCES -->

- [HashiCorp: What is IaC?](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code) -- type: reference, time: 10min
- [Pets vs Cattle (concept)](https://cloudscaling.com/blog/cloud-computing/the-history-of-pets-vs-cattle/) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
你已经自动化了部署——但部署目标服务器却是手工创建的。有人登录云控制台，通过向导一路点击，反复调整直到能用为止。那台服务器只存在于 AWS（或 Hetzner、DigitalOcean）中，以及创建者的记忆里。

基础设施即代码意味着用受版本控制的文件来描述你的基础设施。这与 CI/CD 为应用代码带来的纪律相同，只不过应用对象是服务器本身。

<!-- ZH_DEEP_DIVE -->
## 雪花服务器问题

手动搭建的服务器会随着时间累积变更。为调试问题安装的软件包。为修复问题而调整的配置文件。额外开放却已被遗忘的端口。数月之后，服务器便偏离了任何有记录的状态。

这被称为**雪花服务器**——独一无二、脆弱且无法复现。当它宕机时，你要花好几天试图重建原有的配置。当你需要第二台（用于预发布、负载均衡）时，你做不到。

IaC 通过让代码成为唯一事实来源来解决这个问题。服务器始终可复现，因为创建它的代码就在版本控制中。如果它宕机了，你重新运行代码，就能得到一个完全相同的替代品。

## 声明式与命令式

**声明式 IaC**（Terraform、Pulumi）：你描述期望的最终状态。“我想要一台 2 CPU、4GB 内存、Ubuntu 24.04、位于 us-east-1 的服务器。”工具会自行推断需要采取哪些操作来达成该状态。

**命令式 IaC**（Ansible、shell 脚本）：你描述要执行的步骤。“运行 apt update。安装 nginx。复制这个配置文件。重启服务。”由你控制执行顺序。

两者各有其适用场景。声明式更适合资源制备（应该存在哪些资源）。命令式更适合配置管理（这些资源上应该运行什么）。

## 两个问题，两种工具

有一个常见的混淆来源：Terraform 和 Ansible 看起来有重叠。其实不然——它们解决的是相邻的问题。

**Terraform** 负责制备基础设施。它创建云资源：服务器、网络、负载均衡器、DNS 记录、存储桶。它对那些服务器内部运行着什么一无所知。

**Ansible** 负责配置服务器上的内容。它通过 SSH 连接并执行任务：安装 nginx、写入配置文件、启用 systemd 服务。它不负责制备服务器——它期望服务器已经存在。

在实践中，它们经常一起使用：Terraform 创建基础设施，Ansible 对其进行配置。或者根据你的需要，只使用其中之一。

## CI/CD 中的 IaC

一旦你的基础设施变成了代码，你就可以在流水线中运行它。在每个 pull request 上执行 `terraform plan`，可以展示将会产生哪些基础设施变更。在合并时执行 `terraform apply`，则真正实施这些变更。你的基础设施获得了与应用程序代码相同的评审、测试和审计追踪。

这就是最终目标：你的整个技术栈——应用程序代码和基础设施——都能从 Git 复现、自动部署，并且永远不需要手工配置。

<!-- ZH_RESOURCES -->
- [HashiCorp：什么是 IaC？](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code) -- 类型：参考，时间：10 分钟
- [宠物与牛（概念）](https://cloudscaling.com/blog/cloud-computing/the-history-of-pets-vs-cattle/) -- 类型：参考，时间：5 分钟

<!-- ZH_UI -->
1. 解释什么是“雪花服务器”以及为什么它们是个问题
2. 描述声明式与命令式 IaC 的区别
3. 理解 provisioning（Terraform）与 configuration（Ansible）的区别
4. IaC 有道理。给我看看 Terraform。
5. 我理解概念了——但编写 IaC 实际是什么样子？我想看看真实的 Terraform 配置长什么样，并理解运行它时会发生什么。
6. 那配置服务器本身呢？我听说过 Ansible。
7. Terraform 负责 provisioning 基础设施——它创建服务器。Ansible 配置服务器上的内容——它安装软件包、写入配置文件、管理服务。它们解决不同的问题，并且经常一起使用。
