---
id: runbooks-and-playbooks
title: Runbooks and Playbooks
zone: sre
edges:
  to:
    - id: on-call-health
      question: >-
        I've got runbooks written. But the on-call rotation is still miserable
        — people are dreading it.
      detail: >-
        The documentation helps a bit, but we're still getting paged too much
        and for things that don't actually need immediate action. The rotation
        feels unfair, people are burning out, and I'm not sure how to fix the
        human side of it.
difficulty: 2
tags:
  - runbooks
  - playbooks
  - on-call
  - documentation
  - incident-response
  - sre
category: practice
milestones:
  - Write a runbook for a real alert in your system
  - Include decision trees and exact copy-paste commands — not vague steps
  - Verify the runbook by having someone else follow it without your help
  - Establish a process for keeping runbooks up to date after incidents
title_zh: "运行手册与操作手册"

---


Right now, when something breaks at 3 AM, the on-call engineer figures it out from scratch. They dig through Slack history, they call the person who built the thing, they try things until something works. Every incident is an improvisation. A runbook changes this: it's the documented procedure for diagnosing and resolving a specific alert or failure mode. When a runbook exists and is good, an engineer who has never seen that system before can follow it and resolve the incident. That's the bar.

<!-- DEEP_DIVE -->

## Runbooks vs playbooks

These terms are often used interchangeably, but there's a useful distinction:

**Runbooks** are procedure documents for specific operational tasks — usually tied to a specific alert or system. "When you get paged for high connection pool utilization on the checkout database, do this." Runbooks are prescriptive and specific.

**Playbooks** are higher-level guides for incident response — they cover patterns and decision trees rather than specific procedures. "When responding to an incident, follow these steps to diagnose the layer at which the failure is occurring." Playbooks guide judgment; runbooks guide action.

In practice, "runbook" is used for both. The key is that the document gives you what you need to act without requiring improvisation.

## What makes a runbook actually useful

Most runbooks fail because they describe what happens, not what to do. "If you see this alert, investigate the database connections" is not a runbook. It's a summary of the alert you just read.

A useful runbook has:

**Context**: What does this alert mean? What's the blast radius? What are the symptoms users are experiencing?

**Immediate triage questions**: Is this a partial failure or complete? Has traffic volume changed? Did a recent deployment happen?

**Step-by-step diagnosis**: Exact commands to run, with expected output. `kubectl get pods -n checkout | grep -v Running` — not "check if pods are running."

**Remediation steps**: What to actually do. With rollback instructions if the fix makes things worse.

**Escalation criteria**: When does this alert require waking someone up vs. it can wait until morning? Who do you escalate to?

**Post-resolution**: What to note in the incident log. Whether a post-mortem is needed.

## Copy-paste commands are good, not lazy

Some engineers feel that providing copy-paste commands in runbooks is hand-holding. The opposite is true. When an engineer is paged at 3 AM, their cognitive capacity is reduced. They shouldn't be constructing complex commands from memory. Give them the exact command. If the command needs a variable they'll have to fill in (like a pod name), use clear placeholders: `kubectl delete pod <POD_NAME> -n checkout`.

## Keeping runbooks current

Runbooks go stale. Systems change. The top cause of stale runbooks is that the post-mortem action item "update the runbook" never gets done.

Two practices that help:

**Include a "last verified" date in the runbook.** Make it policy that any engineer who uses a runbook during an incident is expected to update it with any corrections or additions within 24 hours afterward.

**Runbooks-as-code.** Store runbooks in the same Git repository as the system they document, alongside the alerting rules that reference them. When you change an alert, you change the runbook. Review them in PRs.

<!-- RESOURCES -->

- [PagerDuty Runbook Guide](https://response.pagerduty.com/oncall/alerting_principles/) -- type: guide, time: 15m
- [How to Write a Runbook That People Actually Use](https://www.transposit.com/devops-wiki/devops-practice/runbook/) -- type: article, time: 10m
- [Google SRE Book - Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) -- type: book, time: 20m

<!-- ZH_SUMMARY -->
现在，当凌晨3点出现故障时，值班工程师只能从零开始排查。他们翻遍Slack历史记录，打电话给系统的构建者，不断尝试直到某个方法奏效。每一次事故都是一次即兴发挥。Runbook改变了这一点：它是用于诊断和解决特定告警或故障模式的有据可查的流程。当runbook存在且质量良好时，一个从未接触过该系统的工程师也能照着它解决事故。这就是标准。

<!-- ZH_DEEP_DIVE -->
## Runbook 与 Playbook 的区别

这两个术语经常被混用，但有一个有用的区分：

**Runbook** 是针对特定运维任务的操作流程文档——通常与某个特定告警或系统绑定。“当你因结账数据库连接池利用率过高而被呼叫时，执行以下操作。”Runbook 是规定性的、具体的。

**Playbook** 是更高层次的故障响应指南——它们涵盖的是模式和决策树，而非具体操作步骤。“在响应故障时，按照以下步骤诊断故障发生在哪一层。”Playbook 指导判断；Runbook 指导行动。

在实践中，“runbook”一词被用于两者。关键在于，文档要提供你采取行动所需的一切，而不需要临场发挥。

## 什么样的 Runbook 才真正有用

大多数 Runbook 之所以失败，是因为它们描述的是发生了什么，而不是该做什么。“如果你看到这个告警，请调查数据库连接”——这不是 Runbook，这只是你刚读过的告警的摘要。

有用的 Runbook 包含：

**背景信息**：这个告警意味着什么？影响范围有多大？用户正在经历什么症状？

**即时分诊问题**：这是部分故障还是完全故障？流量是否发生了变化？最近是否发生了部署？

**逐步诊断**：要运行的确切命令，以及预期输出。`kubectl get pods -n checkout | grep -v Running`——而不是“检查 Pod 是否在运行”。

**修复步骤**：实际该做什么。如果修复使情况恶化，还需包含回滚说明。

**升级标准**：这个告警何时需要半夜叫人起来，何时可以等到早上？该向谁升级？

**解决后处理**：在故障日志中记录什么。是否需要事后复盘。

## 可复制粘贴的命令是好事，不是偷懒

有些工程师认为在 Runbook 中提供可复制粘贴的命令是手把手教人。事实恰恰相反。当工程师在凌晨 3 点被呼叫时，他们的认知能力是下降的。他们不应该凭记忆构造复杂命令。给他们确切的命令。如果命令需要他们填写变量（比如 Pod 名称），使用清晰的占位符：`kubectl delete pod <POD_NAME> -n checkout`。

## 保持 Runbook 更新

Runbook 会过时。系统会变化。Runbook 过时的首要原因是事后复盘的行动项“更新 Runbook”从未被执行。

有两个有帮助的做法：

**在 Runbook 中包含“最后验证”日期。** 将其定为制度：任何在故障期间使用过 Runbook 的工程师，都应在事后 24 小时内将其所做的更正或补充更新到 Runbook 中。

**Runbook 即代码。** 将 Runbook 与其所记录的系统存放在同一个 Git 仓库中，与引用它们的告警规则放在一起。当你修改告警时，你就修改 Runbook。在 PR 中审查它们。

<!-- ZH_RESOURCES -->
- [PagerDuty Runbook 指南](https://response.pagerduty.com/oncall/alerting_principles/) -- 类型：指南，时长：15 分钟
- [如何编写人们真正会用的 Runbook](https://www.transposit.com/devops-wiki/devops-practice/runbook/) -- 类型：文章，时长：10 分钟
- [Google SRE 手册 - 故障排查](https://sre.google/sre-book/effective-troubleshooting/) -- 类型：书籍，时长：20 分钟

<!-- ZH_UI -->
1. 为系统中的真实告警编写一份运行手册
2. 包含决策树和可直接复制粘贴的精确命令——而非模糊步骤
3. 让其他人独立按手册操作以验证其有效性
4. 建立事故后保持运行手册更新的流程
5. 我已经写好了运行手册。但值班轮换仍然很痛苦——大家都在害怕值班。
6. 文档有点帮助，但我们仍然被频繁呼叫，而且很多是不需要立即处理的事情。轮换感觉不公平，大家在倦怠，我不确定如何解决人的问题。
