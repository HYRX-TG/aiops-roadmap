---
id: slo-alerting
title: SLO-Based Alerting
zone: sre
edges:
  to:
    - id: incident-roles
      question: >-
        The alert fired and it's real — the SLO is burning fast. Now what? I've
        got six people in a chat thread and nobody knows who's in charge.
      detail: >-
        I've been in incidents where everyone's talking at once, multiple people
        are making changes simultaneously, and nobody knows the current status.
        It's chaos on top of chaos. There has to be a better way to organise
        the response when things go wrong.
difficulty: 3
tags:
  - slo
  - alerting
  - burn-rate
  - sre
  - multi-window
  - prometheus
category: practice
milestones:
  - Explain why threshold alerts on raw metrics cause alert fatigue
  - Define what a burn rate is and how it differs from a raw error rate
  - Implement a multi-window burn rate alert for a service
  - Understand the tradeoff between fast burn (precision) and slow burn (coverage) alerts
title_zh: "基于 SLO 的告警"

---


Traditional alerting pages you when something is obviously broken — error rate above 5%, latency above 1 second. The problem: by the time a threshold alert fires, you've often already burned a significant chunk of your error budget. SLO-based alerting flips the model: instead of alerting on raw metrics, you alert on the rate at which you're consuming budget. The goal is to page you when there's still time to act, not just to tell you the damage has already happened.

<!-- DEEP_DIVE -->

## Why threshold alerts are insufficient for SLOs

A 5% error rate threshold doesn't discriminate between a 5% error rate for 2 minutes (a small blip) and a 5% error rate for 6 hours (a major incident burning through your monthly budget). Both fire the same alert. You can't prioritize between them without manually looking at how long the condition has persisted.

Worse, a 0.2% error rate that persists for 30 days will consume your entire monthly budget without ever triggering a 5% alert. The threshold-based alert misses the slow burn entirely.

## Burn rate: the right signal

The burn rate is how fast you're consuming your error budget relative to the rate that would exhaust it exactly at the end of the window.

If your error budget allows 0.1% failures over 30 days, a burn rate of 1x means you're consuming budget at exactly the right rate — you'll use up exactly 100% by day 30. A burn rate of 2x means you're consuming twice as fast — you'll exhaust the budget in 15 days. A burn rate of 10x means you'll exhaust it in 3 days.

The alerting logic becomes: alert when burn rate is high enough that, if sustained, you'll exhaust your budget before you can recover.

## Multi-window alerting: fast and slow

The canonical SLO alerting approach (from the Google SRE Workbook) uses two detection windows for each alert:

**Short window (1 hour)**: Catches fast burns. If you're burning at 14x your budget in the last hour, that's a critical incident — page immediately. This is precise but can have false positives from short spikes.

**Long window (6 hours)**: Confirms sustained burns. Cross-checking the short window against the long window reduces false positives while still catching real incidents before too much budget is consumed.

A full alerting setup has multiple tiers:

| Burn rate | Window | Severity | Budget consumed if sustained |
|-----------|--------|----------|------------------------------|
| 14.4x | 1h | Critical | 100% in 2 days |
| 6x | 6h | High | 100% in 5 days |
| 3x | 24h | Medium | 100% in 10 days |
| 1x | 3 days | Low/ticket | Budget on pace to exhaust |

## Implementation in practice

In Prometheus/Alertmanager, a burn rate alert looks roughly like:

```yaml
alert: HighErrorBudgetBurnRate
expr: |
  (
    sum(rate(http_requests_total{status=~"5.."}[1h]))
    /
    sum(rate(http_requests_total[1h]))
  ) > (14.4 * 0.001)
for: 2m
labels:
  severity: critical
```

The threshold `14.4 * 0.001` means: 14.4x burn rate on a 0.1% error budget. Adjust for your actual SLO target.

Many observability platforms (Datadog, Grafana Cloud, Google Cloud Operations) now have first-class SLO alerting that handles this math for you — you define the SLI and the SLO, and the platform manages the burn rate calculation.

<!-- RESOURCES -->

- [Alerting on SLOs - Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/) -- type: book, time: 45m
- [Prometheus SLO alerting rules - Sloth](https://sloth.dev/) -- type: tool, time: 30m
- [SLO Burn Rate Alerts - Datadog Blog](https://www.datadoghq.com/blog/burn-rate-slo-alerts/) -- type: article, time: 15m

<!-- ZH_SUMMARY -->
传统告警是在系统明显出问题时才通知你——错误率超过 5%、延迟超过 1 秒。问题在于：等到阈值告警触发时，你往往已经消耗了相当大一部分错误预算。基于 SLO 的告警颠覆了这一模式：不再针对原始指标告警，而是针对你消耗预算的速率告警。其目标是在你仍有时间采取行动时通知你，而不只是告诉你损害已经发生。

<!-- ZH_DEEP_DIVE -->
## 为什么阈值告警不足以支撑 SLO

5% 错误率阈值无法区分 2 分钟内 5% 的错误率（一次小抖动）和 6 小时内 5% 的错误率（一场重大事故，正在烧掉你整月的预算）。两者触发的是同一个告警。如果不手动查看该状态持续了多久，你就无法在两者之间排定优先级。

更糟的是，0.2% 的错误率若持续 30 天，会耗尽你整月的预算，却始终不会触发 5% 的告警。基于阈值的告警完全漏掉了这种缓慢燃烧。

## 燃烧率：正确的信号

燃烧率是指你消耗错误预算的速度，相对于恰好在窗口结束时耗尽预算的那个速度的比值。

如果你的错误预算允许 30 天内 0.1% 的失败，那么 1x 的燃烧率意味着你正以恰到好处的速度消耗预算——到第 30 天你会正好用掉 100%。2x 的燃烧率意味着你消耗速度是两倍——你会在 15 天内耗尽预算。10x 的燃烧率意味着你会在 3 天内耗尽它。

告警逻辑就变成：当燃烧率高到如果持续下去、你会在恢复之前就耗尽预算时，就告警。

## 多窗口告警：快与慢

经典的 SLO 告警方法（来自 Google SRE Workbook）为每个告警使用两个检测窗口：

**短窗口（1 小时）**：捕捉快速燃烧。如果你在过去一小时内以 14x 的预算速度燃烧，那就是一场严重事故——立即呼叫。这很精确，但可能因短时尖峰产生误报。

**长窗口（6 小时）**：确认持续燃烧。用长窗口交叉核对短窗口，可以减少误报，同时仍能在消耗过多预算之前捕捉到真实事故。

一套完整的告警配置包含多个层级：

| 燃烧率 | 窗口 | 严重程度 | 若持续将消耗的预算 |
|-----------|--------|----------|------------------------------|
| 14.4x | 1h | Critical | 2 天内 100% |
| 6x | 6h | High | 5 天内 100% |
| 3x | 24h | Medium | 10 天内 100% |
| 1x | 3 days | Low/ticket | 预算按此速度将耗尽 |

## 实践中的实现

在 Prometheus/Alertmanager 中，燃烧率告警大致如下：

```yaml
alert: HighErrorBudgetBurnRate
expr: |
  (
    sum(rate(http_requests_total{status=~"5.."}[1h]))
    /
    sum(rate(http_requests_total[1h]))
  ) > (14.4 * 0.001)
for: 2m
labels:
  severity: critical
```

阈值 `14.4 * 0.001` 意味着：在 0.1% 错误预算上的 14.4x 燃烧率。请根据你实际的 SLO 目标进行调整。

许多可观测性平台（Datadog、Grafana Cloud、Google Cloud Operations）现在都提供一流的 SLO 告警，替你处理这些计算——你定义 SLI 和 SLO，平台负责管理燃烧率计算。

<!-- ZH_RESOURCES -->
- [基于 SLO 的告警 - Google SRE 工作手册](https://sre.google/workbook/alerting-on-slos/) -- 类型：书籍，时长：45 分钟
- [Prometheus SLO 告警规则 - Sloth](https://sloth.dev/) -- 类型：工具，时长：30 分钟
- [SLO 燃尽率告警 - Datadog 博客](https://www.datadoghq.com/blog/burn-rate-slo-alerts/) -- 类型：文章，时长：15 分钟

<!-- ZH_UI -->
1. 解释为什么对原始指标设置阈值告警会导致告警疲劳
2. 定义什么是燃烧率，以及它与原始错误率的区别
3. 为服务实现多窗口燃烧率告警
4. 理解快速燃烧（精确性）与慢速燃烧（覆盖性）告警之间的权衡
5. 告警触发了且是真实的——SLO 正在快速燃烧。接下来怎么办？聊天线程里有六个人，却没人知道谁负责。
6. 我经历过这样的事故：所有人同时说话，多个人同时做变更，没人知道当前状态。混乱之上再加混乱。事情出错时，一定有更好的方式来组织响应。
