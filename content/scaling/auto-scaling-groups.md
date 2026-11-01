---
id: auto-scaling-groups
title: Auto Scaling Groups
zone: scaling
edges:
  to:
    - id: redis-scaling
      question: >-
        My Python servers auto-scale. Now Redis is the single point of failure
        and it's hitting its limits.
      detail: >-
        All those app servers are hammering one Redis instance for every session
        read and write. Redis is fast but has memory limits, and a single node
        going down takes out every user's session. Time to scale Redis itself.
    - id: launch-templates-and-amis
      question: 'When the ASG spins up a new VM, how does it know what software to run?'
      detail: >-
        When the ASG spins up a new VM at 2am during a traffic spike, it needs
        to just work — my app installed, configured, serving traffic within
        minutes. But how does a brand new blank VM know what to run? I can't SSH
        into every new instance manually every time the group scales out.
    - id: connection-pooling
      question: My app servers are scaling out, but now the database is throwing "too many connections" errors before they've even taken any load. What's happening?
      detail: >-
        Every app server opens its own persistent connection pool to the
        database. With ten servers each holding twenty connections open, that's
        already two hundred — and Postgres has a hard limit. When the ASG scales
        out during a spike I start seeing connection errors before the new
        servers have served a single request.
    - id: async-job-queues
      question: My servers scale fine for normal requests — but some operations take 10 seconds and block the whole request. What do I do with those?
      detail: >-
        Sending confirmation emails, resizing uploaded images, generating
        invoices — these are slow no matter how many servers I have. They block
        the web worker for the whole duration, and if they fail the user sees an
        error. I keep thinking there must be a way to just hand them off and
        respond immediately.
difficulty: 2
tags:
  - auto-scaling
  - asg
  - aws
  - ec2
  - launch-template
  - scaling-policies
  - elasticity
category: practice
milestones:
  - Create a Launch Template that installs and starts your application
  - 'Create an Auto Scaling Group with a minimum, maximum, and desired capacity'
  - Attach the ASG to your load balancer's target group
  - Set a scaling policy that adds instances when CPU exceeds 70%
  - Watch the ASG replace a terminated instance automatically
title_zh: "自动扩缩容组"

---


An Auto Scaling Group (ASG) is an AWS construct that manages a fleet of EC2 instances automatically. You define the minimum and maximum size of the fleet, set policies for when to scale in and out, and the ASG handles the rest: launching new instances when load is high, terminating them when it drops, replacing instances that fail health checks. It's the automation layer that makes horizontal scaling practical to operate.

<!-- DEEP_DIVE -->

## The core concepts

An ASG needs three things:

1. **A Launch Template**: the blueprint for new instances — which AMI to use, instance type, security groups, IAM role, user-data script. When the ASG decides to launch a new instance, it uses this template.

2. **Capacity settings**: minimum, maximum, and desired count. The ASG will always maintain at least the minimum and never exceed the maximum. Desired is the current target that scaling policies adjust.

3. **A target group**: the ASG registers each new instance with the load balancer's target group automatically. When the instance passes health checks, it starts receiving traffic. When it's terminated, it's deregistered first.

## Scaling policies

**Target tracking scaling** is the simplest and recommended starting point: pick a metric and a target value, and AWS manages scaling automatically. "Keep average CPU utilization across the fleet at 70%" — the ASG adds instances when CPU is above 70% and removes them when it's been below 70% for long enough. You can also track requests per target (useful if CPU isn't a good proxy for load in your workload).

**Step scaling** gives you more control: "If CPU > 70%, add 2 instances. If CPU > 90%, add 5." Useful when the relationship between load and required capacity isn't linear.

**Scheduled scaling** adds or removes capacity on a time-based schedule. If you know traffic spikes every Monday morning at 9 AM, pre-scale at 8:45 instead of reacting after the spike arrives.

## The new instance bootstrap problem

When the ASG spins up a new EC2 instance, it starts completely blank. It needs to:
- Have your application installed
- Have configuration files in the right places
- Start the application process
- Pass the load balancer's health check

This is solved one of two ways: **user-data scripts** (run at startup, install software on boot — slow but flexible) or **pre-baked AMIs** (the application is already installed, boots fast). The Launch Templates node covers this in detail.

## Instance replacement on failure

If an instance fails the load balancer's health check repeatedly, the ASG terminates it and launches a replacement. This is where the single-server reliability problem goes away: you're not hoping a server stays healthy forever, you're running a system that automatically replaces unhealthy servers. A server that crashes at 3 AM gets replaced within minutes, automatically, without waking anyone up.

Set the minimum to at least 2 and spread across multiple availability zones. That way, a single AZ having a problem doesn't take down your entire fleet.

## Connection draining

When the ASG decides to terminate an instance (scaling in, replacement, or deployment), it first deregisters it from the load balancer and waits for in-flight requests to complete before terminating. This **connection draining** (called "deregistration delay" in AWS) prevents requests from being cut off mid-flight. Set this to your p99 request duration — if 99% of requests complete in under 5 seconds, a 30-second draining window is more than enough.

<!-- RESOURCES -->

- [AWS Auto Scaling Groups Documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) -- type: docs, time: 30m
- [AWS Target Tracking Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html) -- type: docs, time: 15m
- [AWS Launch Templates](https://docs.aws.amazon.com/autoscaling/ec2/userguide/launch-templates.html) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Auto Scaling Group（ASG）是 AWS 提供的一种构造，用于自动管理一组 EC2 实例。你定义实例集群的最小和最大规模，设置何时扩容和缩容的策略，剩下的由 ASG 处理：负载高时启动新实例，负载下降时终止实例，替换未通过健康检查的实例。正是这一自动化层，让横向扩展在实际运维中变得可行。

<!-- ZH_DEEP_DIVE -->
## 核心概念

ASG 需要三样东西：

1. **启动模板（Launch Template）**：新实例的蓝图——使用哪个 AMI、实例类型、安全组、IAM 角色、user-data 脚本。当 ASG 决定启动新实例时，就会使用这个模板。

2. **容量设置**：最小值、最大值和期望数量。ASG 始终会维持至少最小值，且绝不超过最大值。期望值是当前目标，由扩缩容策略进行调整。

3. **目标组（target group）**：ASG 会自动将每个新实例注册到负载均衡器的目标组。当实例通过健康检查后，就开始接收流量。当实例被终止时，会先将其注销。

## 扩缩容策略

**目标跟踪扩缩容（Target tracking scaling）** 是最简单且推荐的起点：选择一个指标和一个目标值，AWS 会自动管理扩缩容。“将整个集群的平均 CPU 利用率保持在 70%”——当 CPU 高于 70% 时，ASG 会增加实例；当 CPU 低于 70% 持续足够长时间后，ASG 会移除实例。你也可以跟踪每个目标的请求数（如果你的工作负载中 CPU 不能很好地代表负载，这会很有用）。

**步进扩缩容（Step scaling）** 给你更多控制权：“如果 CPU > 70%，增加 2 个实例。如果 CPU > 90%，增加 5 个。”当负载与所需容量之间的关系不是线性时，这很有用。

**计划扩缩容（Scheduled scaling）** 按基于时间的计划增加或移除容量。如果你知道每周一早上 9 点流量会激增，就在 8:45 预先扩容，而不是等高峰到来后再被动响应。

## 新实例的引导问题

当 ASG 启动一个新的 EC2 实例时，它一开始完全是空白的。它需要：
- 安装你的应用程序
- 将配置文件放到正确的位置
- 启动应用程序进程
- 通过负载均衡器的健康检查

这可以通过两种方式之一解决：**user-data 脚本**（在启动时运行，在开机时安装软件——慢但灵活）或**预烘焙 AMI**（应用程序已经安装好，启动快）。Launch Templates 节点会详细讨论这一点。

## 故障时的实例替换

如果某个实例反复未通过负载均衡器的健康检查，ASG 会终止它并启动一个替代实例。单服务器可靠性问题正是在这里消失的：你不再寄希望于一台服务器永远保持健康，而是在运行一个能自动替换不健康服务器的系统。一台在凌晨 3 点崩溃的服务器会在几分钟内被自动替换，无需叫醒任何人。

将最小值设置为至少 2，并分散到多个可用区。这样，单个 AZ 出现问题不会导致整个集群瘫痪。

## 连接排空

当 ASG 决定终止某个实例时（缩容、替换或部署），它会先将该实例从负载均衡器注销，并等待正在处理的请求完成后再终止。这种**连接排空**（在 AWS 中称为“注销延迟”）可以防止请求在传输途中被切断。将此设置为你的 p99 请求持续时间——如果 99% 的请求在 5 秒内完成，那么 30 秒的排空窗口就绰绰有余了。

<!-- ZH_RESOURCES -->
- [AWS Auto Scaling Groups 文档](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) -- 类型：文档，时长：30m
- [AWS 目标跟踪扩缩容](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html) -- 类型：文档，时长：15m
- [AWS 启动模板](https://docs.aws.amazon.com/autoscaling/ec2/userguide/launch-templates.html) -- 类型：文档，时长：15m

<!-- ZH_UI -->
1. 创建一个启动模板，用于安装并启动你的应用程序
2. 创建一个 Auto Scaling 组，设置最小、最大和期望容量
3. 将 ASG 关联到负载均衡器的目标组
4. 设置一个扩展策略，当 CPU 超过 70% 时增加实例
5. 观察 ASG 自动替换被终止的实例
6. 我的 Python 服务器已实现自动扩展。现在 Redis 成了单点故障，而且已经达到极限。
7. 所有应用服务器在每次会话读写时都冲击同一个 Redis 实例。Redis 很快但有内存限制，单个节点宕机会导致所有用户的会话丢失。是时候扩展 Redis 本身了。
8. 当 ASG 启动一台新 VM 时，它怎么知道要运行什么软件？
9. 当 ASG 在凌晨两点流量高峰时启动一台新 VM，它需要直接可用——我的应用已安装、配置好，并在几分钟内开始处理流量。但一台全新的空白 VM 怎么知道要运行什么？我无法在每次组扩展时手动 SSH 到每个新实例。
10. 我的应用服务器正在扩展，但数据库在新服务器还没承受任何负载之前就抛出“连接数过多”错误。发生了什么？
11. 每个应用服务器都会向数据库打开自己的持久连接池。十台服务器各保持二十个连接，就已经是两百个——而 Postgres 有硬性限制。当 ASG 在高峰期间扩展时，新服务器还没处理一个请求，我就开始看到连接错误。
12. 我的服务器处理普通请求时扩展正常——但有些操作需要 10 秒并阻塞整个请求。这些操作该怎么办？
13. 发送确认邮件、调整上传图片大小、生成发票——无论有多少服务器，这些操作都很慢。它们在整个过程中阻塞 Web worker，而且如果失败，用户会看到错误。我一直在想，一定有一种方法可以把它们交出去并立即响应。
