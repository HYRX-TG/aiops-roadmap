---
id: launch-templates-and-amis
title: Launch Templates and Machine Images
zone: scaling
edges:
  to:
    - id: vm-scaling-pain-points
      question: >-
        AMI baking is slow and painful. Is this really the best way to ship code
        at scale?
      detail: >-
        Every code change triggers a slow cycle: bake a new machine image, wait
        minutes, update the template, roll it out across the fleet. Can't we do better?
difficulty: 2
tags:
  - ami
  - launch-template
  - ec2
  - packer
  - golden-image
  - immutable-infrastructure
  - aws
category: practice
milestones:
  - >-
    Create a custom AMI with your application pre-installed using Packer or
    manual snapshot
  - Reference the AMI in a Launch Template
  - >-
    Understand what a user-data script is and when to use it instead of a baked
    AMI
  - Explain the trade-offs between baked images and runtime configuration
title_zh: "启动模板与机器镜像"

---


When an Auto Scaling Group launches a new instance, it needs to know what software to run and how to configure it. A Launch Template answers the "what hardware" question (instance type, AMI, security groups, IAM role). The AMI answers the "what software is installed" question. Together they define what a new instance looks like the moment it boots.

<!-- DEEP_DIVE -->

## Launch Templates

A Launch Template is the specification the ASG uses when creating a new instance. Key fields:

- **AMI ID**: which machine image to boot from — this is where your application software lives
- **Instance type**: `t3.medium`, `c5.xlarge`, etc.
- **Security groups**: which traffic to allow
- **IAM instance profile**: what AWS permissions the instance has (to read from S3, write to CloudWatch, etc.)
- **Key pair**: for SSH access
- **User-data**: a shell script that runs at boot

Launch Templates support versioning. When you update the template (new AMI version, different instance type), the ASG continues using the old version until you tell it to update — giving you controlled rollouts.

## AMIs (Amazon Machine Images)

An AMI is a snapshot of a disk volume — it captures the OS, installed packages, application code, and configuration at a point in time. When EC2 launches an instance from an AMI, it boots from a copy of that snapshot.

The simplest AMI is AWS's base Amazon Linux or Ubuntu image. If you use one of these, you need a user-data script to install your application on every boot — which can take 3-5 minutes.

A **custom AMI** (sometimes called a golden image or baked image) has your application pre-installed. You boot an instance from a base image, install your software, configure it, then "bake" it into a new AMI using the EC2 console or the AWS CLI (`aws ec2 create-image`). Subsequent instances boot in seconds because the software is already there.

## Packer for automated image building

Doing AMI baking manually doesn't scale — every code change requires you to manually boot an instance, install software, and take a snapshot. HashiCorp Packer automates this. You write a Packer template that describes:
1. Which base AMI to start from
2. Shell commands to install and configure your app
3. What to name the resulting AMI

Packer launches an EC2 instance, runs your provisioners, creates the AMI, and terminates the instance. Plug this into your CI pipeline and every merged PR produces a new AMI ready to deploy.

## User-data vs baked AMI

| Approach | Boot time | Flexibility | Complexity |
|---|---|---|---|
| User-data script only | 3-8 minutes | High (script runs fresh) | Low |
| Pre-baked AMI | 30-60 seconds | Lower (baked at build time) | Medium |
| Baked AMI + minimal user-data | 30-60 seconds | High | Medium |

The hybrid is common: bake the application into the AMI (fast boot), but use user-data for environment-specific config (endpoint URLs, secrets) that differs between staging and production.

## The AMI deployment cycle

With a baked AMI approach, deploying new code looks like:
1. Build new AMI (CI pipeline builds, tests, bakes)
2. Update Launch Template to reference new AMI ID
3. Roll out the ASG: terminate old instances one at a time (or trigger an instance refresh), ASG launches replacements from new template

This is slow — an instance refresh for a 10-instance fleet might take 20-30 minutes. This operational overhead is one reason teams eventually move to containers.

<!-- RESOURCES -->

- [HashiCorp Packer Documentation](https://developer.hashicorp.com/packer/docs) -- type: docs, time: 30m
- [AWS EC2 User Data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) -- type: docs, time: 15m
- [AWS Instance Refresh](https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-instance-refresh.html) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
当 Auto Scaling Group 启动新实例时，它需要知道要运行什么软件以及如何配置。Launch Template 回答的是“什么硬件”的问题（实例类型、AMI、安全组、IAM 角色）。AMI 回答的是“安装了哪些软件”的问题。二者共同定义了新实例在启动那一刻的形态。

<!-- ZH_DEEP_DIVE -->
## 启动模板

启动模板是 ASG 在创建新实例时使用的规范。关键字段：

- **AMI ID**：从哪个机器镜像启动——你的应用程序软件就存放在这里
- **实例类型**：`t3.medium`、`c5.xlarge` 等
- **安全组**：允许哪些流量
- **IAM 实例配置文件**：实例拥有哪些 AWS 权限（从 S3 读取、写入 CloudWatch 等）
- **密钥对**：用于 SSH 访问
- **User-data**：在启动时运行的 shell 脚本

启动模板支持版本控制。当你更新模板（新的 AMI 版本、不同的实例类型）时，ASG 会继续使用旧版本，直到你指示它更新——这为你提供了可控的滚动发布。

## AMI（Amazon 机器镜像）

AMI 是磁盘卷的快照——它捕获了某一时间点的操作系统、已安装的软件包、应用程序代码和配置。当 EC2 从 AMI 启动实例时，它会从该快照的副本启动。

最简单的 AMI 是 AWS 的基础 Amazon Linux 或 Ubuntu 镜像。如果使用这些镜像，你需要一个 user-data 脚本在每次启动时安装应用程序——这可能需要 3-5 分钟。

**自定义 AMI**（有时称为黄金镜像或烘焙镜像）已预装你的应用程序。你从基础镜像启动一个实例，安装软件、进行配置，然后使用 EC2 控制台或 AWS CLI（`aws ec2 create-image`）将其“烘焙”成新的 AMI。后续实例可以在几秒内启动，因为软件已经存在。

## 使用 Packer 实现自动化镜像构建

手动进行 AMI 烘焙无法规模化——每次代码变更都需要你手动启动实例、安装软件并创建快照。HashiCorp Packer 可以自动化这一过程。你编写一个 Packer 模板，描述：
1. 从哪个基础 AMI 开始
2. 安装和配置应用程序的 shell 命令
3. 生成的 AMI 如何命名

Packer 启动一个 EC2 实例，运行你的 provisioner，创建 AMI，然后终止该实例。将其接入你的 CI 流水线，每个合并的 PR 都会生成一个可部署的新 AMI。

## User-data 与烘焙 AMI 对比

| 方式 | 启动时间 | 灵活性 | 复杂度 |
|---|---|---|---|
| 仅使用 user-data 脚本 | 3-8 分钟 | 高（脚本每次重新运行） | 低 |
| 预烘焙 AMI | 30-60 秒 | 较低（在构建时烘焙） | 中 |
| 烘焙 AMI + 最小 user-data | 30-60 秒 | 高 | 中 |

混合方式很常见：将应用程序烘焙到 AMI 中（快速启动），但使用 user-data 处理因环境而异的配置（端点 URL、密钥），这些配置在预发布和生产环境之间有所不同。

## AMI 部署周期

采用烘焙 AMI 方式时，部署新代码的过程如下：
1. 构建新 AMI（CI 流水线执行构建、测试、烘焙）
2. 更新启动模板以引用新的 AMI ID
3. 滚动更新 ASG：逐个终止旧实例（或触发实例刷新），ASG 从新模板启动替换实例

这个过程很慢——对于 10 个实例的集群，实例刷新可能需要 20-30 分钟。这种运维开销是团队最终转向容器的一个原因。

<!-- ZH_RESOURCES -->
- [HashiCorp Packer 文档](https://developer.hashicorp.com/packer/docs) -- 类型: 文档, 时长: 30 分钟
- [AWS EC2 用户数据](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) -- 类型: 文档, 时长: 15 分钟
- [AWS 实例刷新](https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-instance-refresh.html) -- 类型: 文档, 时长: 15 分钟

<!-- ZH_UI -->
1. 使用 Packer 或手动快照创建预装应用程序的自定义 AMI
2. 在启动模板中引用该 AMI
3. 理解什么是 user-data 脚本，以及何时用它替代预烘焙 AMI
4. 解释预烘焙镜像与运行时配置之间的权衡
5. AMI 烘焙又慢又痛苦。这真的是大规模交付代码的最佳方式吗？
6. 每次代码变更都会触发缓慢循环：烘焙新机器镜像、等待数分钟、更新模板、在全集群推广。我们不能做得更好吗？
