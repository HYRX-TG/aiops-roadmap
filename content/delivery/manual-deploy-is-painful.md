---
id: manual-deploy-is-painful
title: Manual Deploys Are Painful
zone: delivery
edges:
  to:
    - id: what-is-ci-cd
      question: What is CI/CD and how does it fix this?
      detail: >-
        I want to get to a point where I push code and it just ends up running
        somewhere — tests passing, deployed, without me doing anything manually.
        I've heard 'CI/CD' thrown around but I don't understand what it actually
        is or how it works.
difficulty: 1
tags:
  - ci-cd
  - deployment
  - automation
  - devops
category: concept
milestones:
  - List every manual step in your current deploy process
  - Identify which steps could fail silently
  - Understand why manual deployments don't scale
title_zh: "手动部署令人痛苦"

---


Every deploy is a ritual. SSH into the server, pull the latest code, install dependencies, run migrations, restart the service, check the logs, hope nothing broke. Miss one step — or run them out of order — and you've just taken down production.

This is fine once. It's unsustainable at any meaningful velocity, and it's a solved problem.

<!-- DEEP_DIVE -->

## The ritual

A typical manual deploy looks like this:

```bash
ssh user@yourserver.com
cd /opt/myapp
git pull origin main
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart myapp
sudo journalctl -u myapp -n 50
```

Seven commands. Every single time. In the right order. Without typos.

## Why this breaks down

**Human error is inevitable.** Step 4 works 99% of the time. The 1% it fails is always at 2 AM after a Friday release. You skip it because you're tired. Now you're debugging a dependency mismatch at midnight.

**No audit trail.** Who deployed what, when? When something breaks, you're guessing whether the last deploy caused it. With automation, every deploy is a timestamped, logged event tied to a specific commit.

**Can't scale.** Two engineers deploying manually means two people SSHing into the same server and potentially stepping on each other. Five engineers means chaos.

**Tests get skipped.** Running the test suite before a manual deploy is technically optional. Under pressure, it gets skipped. Bugs reach production that a 30-second automated check would have caught.

**Snowflake servers.** Every manual step you apply to a server makes it slightly different from every other server. Over time you get a snowflake: a server only you understand, that can't be reproduced if it dies.

## The hidden cost

The real damage isn't the time each deploy takes — it's the deploys you don't do. When deploying is painful, engineers batch changes into large releases instead of shipping small improvements continuously. Large releases mean more risk, more blast radius when something goes wrong, and longer feedback loops between writing code and seeing it work in production.

Teams with automated deployments ship many times a day. Teams with manual deployments ship once a week and call it bold.

<!-- RESOURCES -->

- [Google SRE Book: Release Engineering](https://sre.google/sre-book/release-engineering/) -- type: reference, time: 20min

<!-- ZH_SUMMARY -->
每次部署都像一场仪式。SSH 登录服务器、拉取最新代码、安装依赖、执行数据库迁移、重启服务、查看日志、祈祷一切正常。漏掉一步——或者顺序搞错——你就把生产环境搞挂了。

偶尔来一次还行。但在任何有意义的速度下都不可持续，而且这早已是一个被解决的问题。

<!-- ZH_DEEP_DIVE -->
## 仪式

典型的手动部署是这样的：

```bash
ssh user@yourserver.com
cd /opt/myapp
git pull origin main
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart myapp
sudo journalctl -u myapp -n 50
```

七条命令。每一次都是如此。顺序不能错。不能有拼写错误。

## 为什么会崩溃

**人为错误不可避免。** 第 4 步在 99% 的情况下都能正常工作。而那失败的 1%，总是发生在周五发布之后的凌晨 2 点。你因为疲惫而跳过了它。现在你正在午夜调试依赖不匹配的问题。

**没有审计追踪。** 谁在什么时候部署了什么？当出问题时，你只能猜测是不是上一次部署导致的。有了自动化，每一次部署都是一个带时间戳、有日志记录的事件，并关联到特定的提交。

**无法扩展。** 两个工程师手动部署意味着两个人 SSH 登录到同一台服务器，可能会互相干扰。五个工程师就意味着混乱。

**测试被跳过。** 在手动部署前运行测试套件在技术上属于可选项。在压力之下，它就会被跳过。本可以被 30 秒自动化检查捕获的 bug 就这样进入了生产环境。

**雪花服务器。** 你对服务器执行的每一个手动步骤，都会让它与其他所有服务器略有不同。久而久之你就得到了一台雪花：一台只有你才理解的服务器，一旦它挂了就无法复现。

## 隐藏成本

真正的损害不是每次部署所花的时间——而是那些你没有做的部署。当部署很痛苦时，工程师会把变更攒成大型发布，而不是持续交付小的改进。大型发布意味着更高的风险、出问题时更大的爆炸半径，以及从写代码到看到它在生产环境工作之间更长的反馈回路。

拥有自动化部署的团队每天发布很多次。拥有手动部署的团队每周发布一次，还称之为大胆。

<!-- ZH_RESOURCES -->
- [Google SRE 手册：发布工程](https://sre.google/sre-book/release-engineering/) -- 类型：参考，时长：20 分钟

<!-- ZH_UI -->
1. 列出当前部署流程中的每一个手动步骤
2. 找出哪些步骤可能静默失败
3. 理解为什么手动部署无法扩展
4. 什么是 CI/CD，它如何解决这个问题？
5. 我希望达到这样的状态：我推送代码后，它就能自动运行起来——测试通过、完成部署，全程无需我手动操作。我听说过“CI/CD”这个词，但不明白它到底是什么，也不清楚它是如何工作的。
