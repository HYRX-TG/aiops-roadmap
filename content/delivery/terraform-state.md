---
id: terraform-state
title: Managing Terraform State
zone: delivery
edges:
  to:
    - id: why-kubernetes
      zone: kubernetes
      question: >-
        My infrastructure is automated now. But managing individual servers
        still feels wrong — I just want to say "run five copies of my app
        and keep them healthy."
      detail: >-
        Terraform handles the infrastructure, CI/CD handles the code. But I'm
        still thinking in terms of servers — which machine runs what, how
        many do I need, what happens when one dies. I want to just declare
        what my app needs and let something else figure out where to run it.
difficulty: 2
tags:
  - terraform
  - state
  - remote-state
  - s3
  - terraform-cloud
  - locking
  - collaboration
category: practice
milestones:
  - 'Move local state to remote storage (S3, Terraform Cloud, or equivalent)'
  - Enable state locking to prevent concurrent applies
  - Understand what happens if state becomes corrupted
  - Use workspaces or separate state files per environment
title_zh: "管理 Terraform 状态"

---


Terraform's local `terraform.tfstate` file is fine when you're the only one running it on one machine. The moment two people or a CI runner touch the same infrastructure, you need state that lives somewhere shared, with locking to prevent concurrent writes.

Remote state with locking is a one-time setup that prevents a class of very unpleasant incidents.

<!-- DEEP_DIVE -->

## What state is and why it matters

Terraform doesn't query your cloud provider to discover the current state of every resource on each run — that would be slow and error-prone. Instead, it maintains a state file that maps your config resources to the real-world resource IDs it created.

```json
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "instances": [
        {
          "attributes": {
            "id": "i-0abc12345def",
            "instance_type": "t3.micro",
            ...
          }
        }
      ]
    }
  ]
}
```

When you run `terraform plan`, Terraform compares this state to your config files and to the live provider API. The diff tells it what needs to change.

**Lose the state file**, and Terraform no longer knows it created `i-0abc12345def`. The next `apply` tries to create a new instance. You now have two.

**Corrupt the state file**, and the computed diff may destroy things that shouldn't be destroyed, or leave orphaned resources that are never cleaned up.

## The concurrency problem

Two engineers run `terraform apply` at the same time against the same infrastructure. Both read the state file, both compute a plan, both start making changes. Their writes to the state file interleave and corrupt it.

This also happens with CI pipelines. Two pipeline runs triggered close together both apply Terraform. Same problem.

**Locking** serializes applies. Before applying, Terraform acquires a lock. If another process holds the lock, it waits or fails rather than proceeding. The state file is only written by one process at a time.

## Remote state backends

Move the state file to shared, lockable storage.

### S3 + DynamoDB (AWS)

The most common setup for AWS users:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

S3 stores the state file. DynamoDB provides locking (a record is written to the table while an apply is in progress and deleted after). Both are cheap — an S3 bucket and a DynamoDB table with on-demand pricing cost pennies per month.

### Terraform Cloud / HCP Terraform

HashiCorp's hosted backend. Free for small teams:

```hcl
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      name = "production"
    }
  }
}
```

State storage, locking, a UI for viewing state and plan output, and run history are all included. The easiest option if you don't want to manage the backend infrastructure yourself.

### Other options

- **GCS** (Google Cloud Storage) — same idea as S3, for GCP users
- **Azure Blob Storage** — for Azure users
- **GitLab-managed state** — built into GitLab CI

## Separate state per environment

Don't put staging and production in the same state file. A mistake in a staging apply should never be able to affect production resources.

Two approaches:

**Separate directories/repos per environment:**
```
infra/
  staging/
    main.tf
    backend.tf   # key = "staging/terraform.tfstate"
  production/
    main.tf
    backend.tf   # key = "production/terraform.tfstate"
```

**Terraform workspaces:**
```bash
terraform workspace new staging
terraform workspace new production
terraform workspace select production
terraform apply
```

Workspaces use separate state files within the same backend (the key includes the workspace name). They work well when the infrastructure is identical across environments and only variable values differ. Separate directories are clearer when environments differ structurally.

## If state gets corrupted

State corruption is rare but not impossible — a failed apply, a killed process, or a bug can leave state in an inconsistent state.

`terraform state list` — see all resources in the state.
`terraform state show aws_instance.web` — inspect a specific resource.
`terraform state rm aws_instance.web` — remove a resource from state (stops Terraform from managing it, doesn't delete the real resource).
`terraform import aws_instance.web i-0abc12345` — import an existing resource into state.

The import command is your recovery tool: if state diverges from reality, import the real resource back so Terraform knows about it again.

<!-- RESOURCES -->

- [Terraform Backends Documentation](https://developer.hashicorp.com/terraform/language/backend) -- type: reference, time: 10min
- [Terraform Cloud Free Tier](https://developer.hashicorp.com/terraform/cloud-docs) -- type: reference, time: 10min
- [S3 Backend Configuration](https://developer.hashicorp.com/terraform/language/backend/s3) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
当你只在一台机器上独自运行 Terraform 时，本地的 `terraform.tfstate` 文件没有问题。一旦有两个人或一个 CI runner 同时操作同一套基础设施，你就需要把 state 存放在共享位置，并通过锁定机制防止并发写入。

带锁定的远程 state 是一次性配置，却能避免一类非常令人头疼的事故。

<!-- ZH_DEEP_DIVE -->
## 什么是状态以及它为何重要

Terraform 不会在每次运行时查询云提供商来发现每个资源的当前状态——那样会很慢且容易出错。相反，它维护一个状态文件，将你的配置资源映射到它创建的真实世界资源 ID。

```json
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "instances": [
        {
          "attributes": {
            "id": "i-0abc12345def",
            "instance_type": "t3.micro",
            ...
          }
        }
      ]
    }
  ]
}
```

当你运行 `terraform plan` 时，Terraform 会将此状态与你的配置文件以及实时提供商 API 进行比较。差异告诉它需要更改什么。

**丢失状态文件**，Terraform 就不再知道它创建了 `i-0abc12345def`。下一次 `apply` 会尝试创建一个新实例。你现在有两个了。

**损坏状态文件**，计算出的差异可能会销毁本不该销毁的东西，或者留下永远不会被清理的孤立资源。

## 并发问题

两个工程师同时对同一基础设施运行 `terraform apply`。两者都读取状态文件，两者都计算计划，两者都开始进行更改。他们对状态文件的写入交错并损坏它。

这也会发生在 CI 流水线中。两个几乎同时触发的流水线运行都应用 Terraform。同样的问题。

**锁定**将 apply 串行化。在应用之前，Terraform 获取一个锁。如果另一个进程持有该锁，它会等待或失败而不是继续。状态文件一次只由一个进程写入。

## 远程状态后端

将状态文件移动到共享的、可锁定的存储中。

### S3 + DynamoDB (AWS)

AWS 用户最常见的设置：

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

S3 存储状态文件。DynamoDB 提供锁定（在 apply 进行期间向表中写入一条记录，之后删除）。两者都很便宜——一个 S3 桶和一个按需定价的 DynamoDB 表每月只需几美分。

### Terraform Cloud / HCP Terraform

HashiCorp 的托管后端。对小型团队免费：

```hcl
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      name = "production"
    }
  }
}
```

状态存储、锁定、用于查看状态和计划输出的 UI 以及运行历史都包含在内。如果你不想自己管理后端基础设施，这是最简单的选择。

### 其他选项

- **GCS** (Google Cloud Storage) — 与 S3 思路相同，适用于 GCP 用户
- **Azure Blob Storage** — 适用于 Azure 用户
- **GitLab 管理的状态** — 内置于 GitLab CI

## 每个环境独立状态

不要将 staging 和 production 放在同一个状态文件中。staging apply 中的错误绝不应该能够影响生产资源。

两种方法：

**每个环境使用单独的目录/仓库：**
```
infra/
  staging/
    main.tf
    backend.tf   # key = "staging/terraform.tfstate"
  production/
    main.tf
    backend.tf   # key = "production/terraform.tfstate"
```

**Terraform 工作区：**
```bash
terraform workspace new staging
terraform workspace new production
terraform workspace select production
terraform apply
```

工作区在同一后端内使用单独的状态文件（key 包含工作区名称）。当各环境的基础设施相同且只有变量值不同时，它们效果很好。当环境在结构上不同时，单独的目录更清晰。

## 如果状态损坏了

状态损坏很少见但并非不可能——失败的 apply、被终止的进程或 bug 都可能使状态处于不一致的状态。

`terraform state list` — 查看状态中的所有资源。
`terraform state show aws_instance.web` — 检查特定资源。
`terraform state rm aws_instance.web` — 从状态中移除资源（停止 Terraform 管理它，不会删除真实资源）。
`terraform import aws_instance.web i-0abc12345` — 将现有资源导入状态。

import 命令是你的恢复工具：如果状态与现实偏离，将真实资源导入回来，以便 Terraform 再次知道它。

<!-- ZH_RESOURCES -->
- [Terraform Backends 文档](https://developer.hashicorp.com/terraform/language/backend) -- 类型：参考，时间：10 分钟
- [Terraform Cloud 免费套餐](https://developer.hashicorp.com/terraform/cloud-docs) -- 类型：参考，时间：10 分钟
- [S3 后端配置](https://developer.hashicorp.com/terraform/language/backend/s3) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 将本地状态迁移到远程存储（S3、Terraform Cloud 或同等方案）
2. 启用状态锁定以防止并发 apply
3. 理解状态损坏后会发生什么
4. 按环境使用工作区或独立的状态文件
5. 我的基础设施现在已经自动化了。但管理单台服务器仍然感觉不对——我只想说“运行我的应用的五份副本并保持它们健康。”
6. Terraform 管理基础设施，CI/CD 管理代码。但我仍然在以服务器的角度思考——哪台机器运行什么、我需要多少台、一台挂了怎么办。我只想声明我的应用需要什么，让其他东西去决定在哪里运行它。
