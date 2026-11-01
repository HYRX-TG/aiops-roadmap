---
id: vm-scaling-pain-points
title: The Pain of Scaling VMs
zone: scaling
edges:
  to:
    - id: containerization
      zone: containers
      question: All this VM management is exhausting. Every deploy is a slow AMI bake and a rolling ASG update. Is there a better model for packaging and running my app?
      detail: >-
        Every code change means a new AMI bake, a new launch template version,
        and waiting for the ASG to roll it out. VMs take minutes to boot.
        I'm patching the OS on every machine in the fleet. I keep hearing that
        containers solve this — but I don't really understand how or whether
        the migration is worth the effort.
    - id: manual-deploy-is-painful
      zone: delivery
      question: >-
        Even if I stick with VMs, deploying changes by hand to a fleet of
        servers is not going to work. How do I automate this?
      detail: >-
        I can't SSH into every server and pull code manually — not with an
        auto-scaling group spinning machines up and down. I need the deploy
        to happen automatically, tested before it goes out, and rolled back
        if something breaks. Where do I even start with that?
difficulty: 1
tags:
  - vms
  - pain-points
  - ami
  - scaling
  - kubernetes
  - containers
  - deployment
  - operations
category: concept
milestones:
  - List the operational pain points of a VM-based scaling architecture
  - Explain why AMI-based deployments are slow compared to container images
  - Understand the resource efficiency problem with always-on VMs
  - Describe how idle capacity costs money in an ASG / MIG setup
title_zh: "扩展虚拟机的痛点"

---


The VM-based scaling architecture we've built — ASG, ALB, RDS, ElastiCache — works and handles serious traffic. But operating it is slow and expensive in ways that compound as the system grows. Understanding these pain points is what motivates the move to containers and eventually Kubernetes.

<!-- DEEP_DIVE -->

## Slow deployments

The AMI bake-and-roll cycle is the biggest operational drag. A code change that takes 30 seconds to write requires:
1. A CI build that runs tests (5-10 minutes)
2. A Packer AMI bake (5-10 minutes)
3. An ASG instance refresh (10-30 minutes for the fleet to roll)

Total: 20-50 minutes from merge to deployed. For urgent fixes or rapid iteration, this feels impossibly slow. Containers (Docker images) build in seconds and deploy with a rolling update in 1-2 minutes.

## Resource waste from always-on VMs

VMs boot once and run until terminated. The minimum ASG size is always running, even at 3 AM when traffic is near zero. Each instance has a full Linux OS consuming memory and CPU, plus your application, plus all the background processes that come with a full OS. The actual utilization of the underlying hardware might be 5-15%.

Container orchestration (Kubernetes) runs many containers on fewer VMs, packing workloads tightly and dramatically improving utilization. You pay for the same EC2 instances but run far more on each one.

## OS management at scale

With a fleet of VMs, you are responsible for the OS of each one. CVEs get published, kernel patches come out, package updates arrive. A fleet of 20 instances means patching 20 instances (or baking and rolling a new AMI, which takes an hour). You're also running 20 identical Linux installations, each of which can drift — different package versions, inconsistent configs — if you're not careful.

Containers solve this at the application layer (the container image is immutable and identical everywhere) while managed Kubernetes reduces OS concerns to node groups that are managed by AWS/GCP.

## Deployment complexity per service

Everything above describes the complexity for *one* application. As the business grows and the monolith is broken into services, you multiply this complexity by the number of services. Each service needs its own ASG, its own AMI pipeline, its own Launch Template, its own ALB target group. Managing a dozen services this way is painful; managing a hundred is effectively impossible without container orchestration.

## What containers fix

Container images are small (tens to hundreds of MB) compared to AMIs (gigabytes). They build in seconds. A `docker run` starts a container in under a second. You can run many containers on one VM. Kubernetes adds the orchestration layer: scheduling containers onto nodes, health checking and restarting failed containers, rolling deploys, resource limits, service discovery. The operational model is fundamentally simpler at scale.

<!-- RESOURCES -->

- [Docker vs Virtual Machines - Explained](https://www.docker.com/resources/what-container/) -- type: article, time: 10m
- [CNCF Annual Survey - Container adoption trends](https://www.cncf.io/reports/cncf-annual-survey-2023/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
我们构建的基于虚拟机的扩展架构——ASG、ALB、RDS、ElastiCache——运行良好，能够处理高负载流量。但运维它既慢又昂贵，而且随着系统增长，这些问题会不断累积。理解这些痛点，正是推动我们转向容器并最终迁移到 Kubernetes 的动因。

<!-- ZH_DEEP_DIVE -->
## 部署缓慢

AMI 的构建与滚动更新周期是最大的运维拖累。一个编写只需 30 秒的代码变更需要：

1. 运行测试的 CI 构建（5-10 分钟）
2. Packer AMI 构建（5-10 分钟）
3. ASG 实例刷新（整个集群滚动更新需 10-30 分钟）

总计：从合并到部署需要 20-50 分钟。对于紧急修复或快速迭代来说，这慢得令人难以接受。容器（Docker 镜像）构建只需几秒，滚动更新部署只需 1-2 分钟。

## 常开 VM 造成的资源浪费

VM 启动一次后一直运行直到被终止。ASG 的最小规模始终在运行，即使在凌晨 3 点流量接近零时也是如此。每个实例都有一个完整的 Linux 操作系统消耗内存和 CPU，再加上你的应用，以及完整操作系统附带的所有后台进程。底层硬件的实际利用率可能只有 5-15%。

容器编排（Kubernetes）在更少的 VM 上运行更多容器，紧密打包工作负载，大幅提升利用率。你为相同的 EC2 实例付费，但每台实例上运行的东西多得多。

## 大规模 OS 管理

对于一组 VM，你需要对每台的 OS 负责。CVE 会发布，内核补丁会推出，软件包更新会到来。20 个实例的集群意味着要给 20 个实例打补丁（或者构建并滚动更新一个新 AMI，这需要一小时）。你还在运行 20 个相同的 Linux 安装，如果不小心，每个都可能发生漂移——不同的软件包版本、不一致的配置。

容器在应用层解决了这个问题（容器镜像不可变且处处相同），而托管 Kubernetes 将 OS 关注点简化为由 AWS/GCP 管理的节点组。

## 每个服务的部署复杂度

以上所有描述的都是*一个*应用的复杂度。随着业务增长和单体应用被拆分为服务，这个复杂度会乘以服务数量。每个服务都需要自己的 ASG、自己的 AMI 流水线、自己的 Launch Template、自己的 ALB 目标组。以这种方式管理十几个服务很痛苦；没有容器编排，管理上百个服务实际上是不可能的。

## 容器解决了什么

容器镜像很小（几十到几百 MB），相比 AMI（数 GB）要小得多。它们构建只需几秒。`docker run` 在不到一秒内启动一个容器。你可以在一个 VM 上运行多个容器。Kubernetes 增加了编排层：将容器调度到节点上、健康检查并重启失败的容器、滚动部署、资源限制、服务发现。在大规模场景下，运维模型从根本上更简单。

<!-- ZH_RESOURCES -->
- [Docker 与虚拟机对比解析](https://www.docker.com/resources/what-container/) -- 类型: 文章, 时长: 10分钟
- [CNCF 年度调查 - 容器采用趋势](https://www.cncf.io/reports/cncf-annual-survey-2023/) -- 类型: 文章, 时长: 15分钟

<!-- ZH_UI -->
1. 列出基于虚拟机的伸缩架构的运维痛点
2. 解释为什么基于 AMI 的部署比容器镜像慢
3. 理解常开虚拟机带来的资源效率问题
4. 描述在 ASG / MIG 配置中空闲容量如何造成资金浪费
5. 这些虚拟机管理太累人了。每次部署都是缓慢的 AMI 烘焙和滚动 ASG 更新。有没有更好的应用打包和运行模式？
6. 每次代码变更都意味着新的 AMI 烘焙、新的启动模板版本，还要等 ASG 滚动推出。虚拟机启动要几分钟。我在给集群里每台机器打操作系统补丁。我一直听说容器能解决这个问题——但我不太明白怎么解决，也不知道迁移是否值得。
7. 即使继续用虚拟机，手动向一组服务器部署变更也行不通。我该如何自动化？
8. 我不能 SSH 到每台服务器手动拉代码——自动伸缩组在不停地创建和销毁机器，根本做不到。我需要部署自动发生、上线前经过测试、出问题能回滚。我该从哪里开始？
