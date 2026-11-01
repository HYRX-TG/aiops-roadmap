---
id: terraform-basics
title: Infrastructure as Code with Terraform
zone: delivery
edges:
  to:
    - id: terraform-state
      question: >-
        Terraform works locally. How does state work when a team or CI pipeline
        uses it?
      detail: >-
        Terraform tracks what it manages in a state file. Locally that's fine.
        But when two people or two CI runs apply Terraform at the same time,
        state conflicts corrupt everything. Remote state with locking solves
        this.
difficulty: 2
tags:
  - terraform
  - iac
  - hcl
  - infrastructure-as-code
  - cloud
  - automation
category: tool
milestones:
  - Install Terraform and authenticate with a cloud provider
  - Write a config that provisions a server
  - Run terraform plan and understand the output
  - Run terraform apply and verify the resource was created
  - Run terraform destroy to clean up
title_zh: "使用 Terraform 实现基础设施即代码"

---


Terraform lets you describe infrastructure in code and apply it to the real world. You write HCL (HashiCorp Configuration Language) files declaring what should exist — a server, a DNS record, a database — and Terraform figures out what API calls to make to create, update, or delete resources to match.

It works with every major cloud provider and hundreds of third-party services, all through the same workflow: `plan`, `apply`, `destroy`.

<!-- DEEP_DIVE -->

## The core workflow

```bash
terraform init      # download provider plugins
terraform plan      # show what will change
terraform apply     # make it so
terraform destroy   # tear everything down
```

`plan` is your safety net. It shows exactly what Terraform intends to do before doing it — which resources will be created, modified, or destroyed. Review the plan before applying, always.

## HCL basics

A Terraform configuration has three main constructs:

**Providers** — the cloud or service you're targeting:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

**Resources** — the infrastructure you want:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

**Variables** — parameterize your config:

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.micro"
}

resource "aws_instance" "web" {
  instance_type = var.instance_type
  ...
}
```

## Reading a plan

```
Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t3.micro"
      + id            = (known after apply)
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

`+` = create, `~` = modify in place, `-/+` = destroy and recreate, `-` = destroy. `-/+` is the dangerous one — it means the resource will be deleted and a new one created. For databases and stateful resources, that's a data-destroying change. Read plans carefully before applying.

## A minimal example: provision a DigitalOcean droplet

```hcl
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  description = "DigitalOcean API token"
  sensitive   = true
}

resource "digitalocean_droplet" "web" {
  name   = "web-server"
  region = "nyc3"
  size   = "s-1vcpu-1gb"
  image  = "ubuntu-24-04-x64"
}

output "ip_address" {
  value = digitalocean_droplet.web.ipv4_address
}
```

Run `terraform apply`, enter the token when prompted, confirm the plan. Terraform creates the droplet. The output block prints the IP when done.

## Outputs and references

Resources can reference each other. Add a DNS record pointing to the droplet:

```hcl
resource "digitalocean_domain" "example" {
  name = "example.com"
}

resource "digitalocean_record" "www" {
  domain = digitalocean_domain.example.name
  type   = "A"
  name   = "www"
  value  = digitalocean_droplet.web.ipv4_address
}
```

Terraform resolves dependencies automatically — it creates the droplet before the DNS record, because the record depends on the droplet's IP.

## State

Terraform tracks what it has created in a **state file** (`terraform.tfstate`). This is how it knows that `aws_instance.web` corresponds to instance `i-0abc1234` in AWS. It uses the state to compute the diff between desired config and current reality.

The state file is critical. Lose it, and Terraform can no longer manage the resources it created. Corrupt it, and the next apply may create duplicates or make destructive changes. For solo local use, the local state file is fine. For teams and CI, you need remote state — that's the next node.

<!-- RESOURCES -->

- [Terraform Documentation: Getting Started](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) -- type: guide, time: 30min
- [Terraform Language Reference](https://developer.hashicorp.com/terraform/language) -- type: reference, time: ongoing
- [DigitalOcean Terraform Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
Terraform 让你用代码描述基础设施，并将其应用到现实世界。你编写 HCL（HashiCorp Configuration Language）文件，声明应当存在哪些资源——一台服务器、一条 DNS 记录、一个数据库——Terraform 会计算出需要发起哪些 API 调用，以创建、更新或删除资源，使其与声明保持一致。

它适用于所有主流云厂商和数百种第三方服务，且都通过同一套工作流：`plan`、`apply`、`destroy`。

<!-- ZH_DEEP_DIVE -->
## 核心工作流程

```bash
terraform init      # 下载 provider 插件
terraform plan      # 显示将要发生的变更
terraform apply     # 执行变更
terraform destroy   # 销毁所有资源
```

`plan` 是你的安全网。它会在执行之前准确显示 Terraform 打算做什么——哪些资源将被创建、修改或销毁。务必在执行 apply 之前先审阅 plan。

## HCL 基础

一个 Terraform 配置包含三个主要构造：

**Providers** —— 你要操作的目标云或服务：

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

**Resources** —— 你想要的基础设施：

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

**Variables** —— 为你的配置提供参数化能力：

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.micro"
}

resource "aws_instance" "web" {
  instance_type = var.instance_type
  ...
}
```

## 解读 plan

```
Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t3.micro"
      + id            = (known after apply)
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

`+` = 创建，`~` = 原地修改，`-/+` = 销毁并重建，`-` = 销毁。`-/+` 是危险的那一个——它意味着资源将被删除并创建一个新的。对于数据库和有状态资源而言，这是一种会破坏数据的变更。在执行 apply 之前请仔细阅读 plan。

## 一个最小示例：创建 DigitalOcean droplet

```hcl
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  description = "DigitalOcean API token"
  sensitive   = true
}

resource "digitalocean_droplet" "web" {
  name   = "web-server"
  region = "nyc3"
  size   = "s-1vcpu-1gb"
  image  = "ubuntu-24-04-x64"
}

output "ip_address" {
  value = digitalocean_droplet.web.ipv4_address
}
```

运行 `terraform apply`，在提示时输入 token，确认 plan。Terraform 会创建该 droplet。完成后 output 块会打印出 IP 地址。

## Outputs 与引用

资源之间可以相互引用。添加一条指向该 droplet 的 DNS 记录：

```hcl
resource "digitalocean_domain" "example" {
  name = "example.com"
}

resource "digitalocean_record" "www" {
  domain = digitalocean_domain.example.name
  type   = "A"
  name   = "www"
  value  = digitalocean_droplet.web.ipv4_address
}
```

Terraform 会自动解析依赖关系——它会先创建 droplet，再创建 DNS 记录，因为该记录依赖于 droplet 的 IP。

## State

Terraform 在 **state 文件**（`terraform.tfstate`）中跟踪它已创建的内容。正是通过它，Terraform 才知道 `aws_instance.web` 对应 AWS 中的实例 `i-0abc1234`。它利用 state 来计算期望配置与当前实际状态之间的差异。

state 文件至关重要。丢失它，Terraform 就无法再管理它创建的资源。损坏它，下一次 apply 可能会创建重复资源或做出破坏性变更。对于个人本地使用，本地 state 文件就足够了。对于团队和 CI 场景，你需要远程 state——那是下一个节点的内容。

<!-- ZH_RESOURCES -->
- [Terraform 文档：入门](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) -- 类型：指南，时间：30 分钟
- [Terraform 语言参考](https://developer.hashicorp.com/terraform/language) -- 类型：参考，时间：持续
- [DigitalOcean Terraform Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 安装 Terraform 并向云服务商完成认证
2. 编写一个用于创建服务器的配置
3. 运行 terraform plan 并理解输出
4. 运行 terraform apply 并确认资源已创建
5. 运行 terraform destroy 进行清理
6. Terraform 在本地可以正常工作。当团队或 CI 流水线使用它时，state 是如何工作的？
7. Terraform 在 state 文件中跟踪其管理的资源。本地使用没问题。但当两个人或两次 CI 运行同时执行 Terraform apply 时，state 冲突会破坏一切。带锁的远程 state 可以解决这个问题。
