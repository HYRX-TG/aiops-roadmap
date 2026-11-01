---
id: log-costs-and-retention
title: Log Costs and Retention
zone: observability
edges:
  to:
    - id: metrics-and-monitoring
      question: >-
        Log costs are under control now. But I still can't answer "is my
        service healthy right now" without querying and counting. What's the
        right tool for that?
      detail: >-
        I've pruned the noisy logs and set up retention policies so I'm not
        storing everything forever. But even with clean logs, I'm still
        reaching for metrics every time I want a real-time answer about
        performance. Logs and metrics feel like they answer different questions.
difficulty: 2
tags:
  - logging
  - cost
  - retention
  - sampling
  - observability
category: practice
milestones:
  - Set up log retention policies so you're not paying to store logs you never query
  - Understand the difference between sampling, filtering, and dropping logs
  - Identify which log streams are high-volume and low-value
  - Implement log-level filtering at the agent level to reduce ingestion volume
title_zh: "日志成本与保留策略"

---


Logs are one of the easiest infrastructure costs to let spiral out of control. The problem is that logging feels free at first — you add a library, set it to INFO, ship everything to CloudWatch or Loki, and move on. Then three months later you look at your bill and half of it is log ingestion and storage. You're storing 90 days of every debug message from every service, most of which you've never queried and never will.

The core tension is that comprehensive logs have real value for debugging, and cheap logs mean less visibility. Every cost-cutting measure in logging is a tradeoff between money saved and information you might not have when you need it. The goal isn't to log as little as possible — it's to log the right things, keep them for the right duration, and drop the rest.

The good news is that the highest-value logs (errors, warnings, important business events) are also low volume. The high-volume stuff (debug output, health checks, routine request logs) is where most of the cost lives, and most of it has very low value after 24–48 hours. Once you understand that asymmetry, the strategy becomes obvious: keep the expensive-to-lose logs longer, drop or sample the cheap-to-lose logs aggressively.

<!-- DEEP_DIVE -->

## What drives log costs

Log costs come from three places:

**Ingestion volume** — how many bytes per second you're shipping to the log store. This is the most direct cost lever. Every byte you ship gets charged for. Managed services like CloudWatch Logs charge around $0.50–$1.00 per GB ingested. A busy service emitting verbose DEBUG logs can generate gigabytes per hour easily.

**Storage duration** — how long you keep logs before they expire. If you keep 90 days of logs, you're paying for 90 days of storage. Most log stores charge per GB-month. If your ingestion rate is 100 GB/day and you keep 90 days, you're storing 9,000 GB at any given time. At $0.03/GB/month that's $270/month just for storage, on top of ingestion.

**Query costs** — some systems (notably CloudWatch Logs Insights) charge per GB scanned when you run a query. The bigger and longer your log data, the more expensive every query becomes. This creates an incentive to keep less data — but it also means you should be specific in your queries rather than scanning everything.

## The main cost reduction strategies

### Filter at the agent, before ingestion

The most effective cost reduction is to drop logs before they ever reach the central store. If a log line is never ingested, it's never charged for. Fluent Bit and Fluentd both support filter rules that can drop lines matching certain criteria.

**Drop DEBUG logs before shipping:**

In Fluent Bit, you can drop lines based on field values:
```ini
[FILTER]
    Name   grep
    Match  *
    Exclude level debug
```

This drops any log line where the `level` field equals "debug" before it's forwarded to the log store. Your applications can still emit debug logs (useful for local development), but they'll never reach the central store in production.

**Drop noisy health check logs:**

Load balancers and Kubernetes liveness probes typically hit a `/health` or `/ping` endpoint every 10 seconds. At scale, this generates tens of thousands of 200 OK log lines per hour. They're never interesting.

```ini
[FILTER]
    Name   grep
    Match  *
    Exclude path /health
```

**Drop logs from verbose third-party libraries:**

Many libraries emit detailed debug output that you can't control at the application level. Filter them out at the agent:
```ini
[FILTER]
    Name   grep
    Match  *
    Exclude logger_name "com.amazonaws.http.AmazonHttpClient"
```

### Sampling high-volume low-value streams

Sampling means: instead of shipping every log line, ship 1 in N. For streams that are high volume but low value — like successful routine requests — sampling lets you keep a representative sample without the full cost.

The key principle: never sample errors. Errors are low volume and high value. You want every error. Sampling makes sense for the high-volume streams: successful INFO logs from very busy endpoints, health check confirmations, routine database query logs.

Fluent Bit doesn't have native probabilistic sampling, but you can implement it with a Lua filter:

```ini
[FILTER]
    Name    lua
    Match   kube.access-log.*
    script  sampling.lua
    call    sample_logs
```

```lua
-- sampling.lua: keep 10% of access logs
function sample_logs(tag, timestamp, record)
    if math.random() < 0.9 then
        return -1, 0, 0  -- drop
    end
    return 0, timestamp, record  -- keep
end
```

This keeps 10% of access log entries — enough to see patterns and diagnose issues, without the full cost.

### Shorter retention for low-value streams

Not all logs need to be kept for the same duration. The right retention period depends on how likely you are to need a log after a given amount of time.

**Error and WARN logs** — you might need these weeks later when a customer files a support ticket, or when you're trying to understand a pattern. 30–90 days is reasonable.

**INFO logs** — useful for recent incident investigations, rarely needed after more than a week or two. 7–14 days for most workloads.

**Debug logs** — if you're shipping any debug logs at all, they should have very short retention. 1–3 days at most. If you haven't used a debug log line within 48 hours, you're almost certainly never going to.

**Audit logs** — logs related to user actions, access events, security-relevant operations. These often have compliance requirements. 1–7 years depending on your industry and jurisdiction.

In CloudWatch Logs, retention is set per log group:
```bash
aws logs put-retention-policy \
  --log-group-name /app/payment-service/info \
  --retention-in-days 14

aws logs put-retention-policy \
  --log-group-name /app/payment-service/error \
  --retention-in-days 90
```

In Loki, retention is configured at the backend level and can be applied per tenant or per stream selector.

## Identifying where your costs actually come from

Before optimising, find out where the volume is. Most log management systems have a usage page or a query you can run to see which log streams are highest volume.

In CloudWatch:
```sql
-- Top log groups by size (run in Log Insights)
stats sum(bytes) as total_bytes by log_group
| sort total_bytes desc
| limit 20
```

In Loki (via LogQL metric query in Grafana):
```logql
sum by (service) (rate({namespace="production"}[5m]))
```

You'll almost always find that 80% of your log volume comes from 20% of your services — often the ones you think about least. A high-traffic API logging every request at INFO, or a misconfigured service emitting debug output continuously.

## The tradeoffs: what you give up

Every cost reduction is a tradeoff. Be explicit about what you're accepting:

| Action | Cost saved | Visibility lost |
|--------|-----------|----------------|
| Drop DEBUG at agent | High | Can't see internal debug detail after the fact; must add ad-hoc debug logging and redeploy |
| Sample INFO logs | Medium | May miss some specific events; patterns are still visible |
| Reduce INFO retention from 30 to 7 days | Medium | Can't investigate incidents older than 7 days |
| Drop health check logs | Low | Can't query health check patterns, but this is almost never needed |

The goal is to make these tradeoffs deliberately — knowing what you're giving up — rather than accidentally cutting something you'll regret later. ERRORs should almost never be sampled or given short retention. That's the data you actually need when things go wrong.

<!-- RESOURCES -->

- [Controlling AWS CloudWatch Logs Costs (AWS)](https://aws.amazon.com/blogs/mt/best-practices-for-centralizing-logs-with-amazon-cloudwatch-logs/) -- type: article, time: 15m
- [Reducing Loki Log Ingestion Costs (Grafana Labs)](https://grafana.com/docs/loki/latest/operations/storage/retention/) -- type: article, time: 15m
- [Log Sampling Strategies (Datadog)](https://www.datadoghq.com/blog/log-sampling/) -- type: article, time: 10m
- [Fluent Bit Filtering Documentation](https://docs.fluentbit.io/manual/pipeline/filters) -- type: article, time: 20m

<!-- ZH_SUMMARY -->
日志是最容易失控的基础设施成本之一。问题在于，日志一开始感觉是免费的——你添加一个库，设为 INFO 级别，把所有内容发送到 CloudWatch 或 Loki，然后就不管了。三个月后你查看账单，发现一半的费用来自日志摄取和存储。你存储了每个服务每条 debug 消息的 90 天数据，其中大部分你从未查询过，将来也不会查询。

核心矛盾在于：全面的日志对调试有真正的价值，而廉价的日志意味着更少的可见性。日志方面的每一项降本措施，都是在节省的金钱与需要时可能缺失的信息之间做权衡。目标不是尽可能少地记录日志——而是记录正确的内容、保留正确的时长，其余的都丢弃。

好消息是，价值最高的日志（错误、警告、重要的业务事件）同时也是低量的。高量的内容（debug 输出、健康检查、例行请求日志）才是大部分成本所在，而其中大部分在 24–48 小时后价值极低。一旦理解了这种不对称性，策略就变得显而易见：对丢失代价高的日志保留更久，对丢失代价低的日志积极丢弃或采样。

<!-- ZH_DEEP_DIVE -->
## 日志成本的驱动因素

日志成本来自三个方面：

**摄取量** —— 你每秒向日志存储发送多少字节。这是最直接的成本杠杆。你发送的每一个字节都会被计费。像 CloudWatch Logs 这样的托管服务，每摄取 1 GB 收费约 $0.50–$1.00。一个繁忙的服务如果输出冗长的 DEBUG 日志，很容易每小时产生数 GB 的数据。

**存储时长** —— 日志在过期前保留多长时间。如果你保留 90 天的日志，就要为 90 天的存储付费。大多数日志存储按 GB-月计费。如果你的摄取速率是 100 GB/天，保留 90 天，那么任意时刻你都在存储 9,000 GB。按 $0.03/GB/月计算，仅存储一项每月就是 $270，这还不包括摄取费用。

**查询成本** —— 某些系统（尤其是 CloudWatch Logs Insights）在你运行查询时按扫描的 GB 数收费。你的日志数据越大、时间跨度越长，每次查询就越贵。这促使你保留更少的数据——但这也意味着你的查询应该更精确，而不是扫描所有内容。

## 主要的降本策略

### 在 Agent 层、摄取之前进行过滤

最有效的降本方式是在日志到达中央存储之前就将其丢弃。如果一行日志从未被摄取，就永远不会被计费。Fluent Bit 和 Fluentd 都支持过滤规则，可以丢弃符合特定条件的日志行。

**在发送前丢弃 DEBUG 日志：**

在 Fluent Bit 中，你可以根据字段值丢弃日志行：
```ini
[FILTER]
    Name   grep
    Match  *
    Exclude level debug
```

这会在日志被转发到日志存储之前，丢弃所有 `level` 字段等于 "debug" 的日志行。你的应用仍然可以输出 debug 日志（对本地开发有用），但在生产环境中它们永远不会到达中央存储。

**丢弃嘈杂的健康检查日志：**

负载均衡器和 Kubernetes 存活探针通常每 10 秒访问一次 `/health` 或 `/ping` 端点。在大规模场景下，这每小时会产生数万条 200 OK 日志行。它们从来都没有价值。

```ini
[FILTER]
    Name   grep
    Match  *
    Exclude path /health
```

**丢弃来自冗长第三方库的日志：**

许多库会输出详细的 debug 信息，而你在应用层无法控制。在 agent 层把它们过滤掉：
```ini
[FILTER]
    Name   grep
    Match  *
    Exclude logger_name "com.amazonaws.http.AmazonHttpClient"
```

### 对高流量低价值日志流进行采样

采样的意思是：不是发送每一行日志，而是每 N 行发送 1 行。对于高流量但低价值的日志流——比如成功的常规请求——采样让你在保留代表性样本的同时避免全部成本。

关键原则：绝不对错误进行采样。错误量小且价值高。你需要每一条错误。采样适用于高流量日志流：非常繁忙端点的成功 INFO 日志、健康检查确认日志、常规数据库查询日志。

Fluent Bit 没有原生的概率采样功能，但你可以用 Lua 过滤器实现：

```ini
[FILTER]
    Name    lua
    Match   kube.access-log.*
    script  sampling.lua
    call    sample_logs
```

```lua
-- sampling.lua: keep 10% of access logs
function sample_logs(tag, timestamp, record)
    if math.random() < 0.9 then
        return -1, 0, 0  -- drop
    end
    return 0, timestamp, record  -- keep
end
```

这会保留 10% 的访问日志条目——足以观察模式和诊断问题，同时避免全部成本。

### 对低价值日志流使用更短的保留期

并非所有日志都需要保留相同的时长。合适的保留期取决于你在给定时间之后有多大可能还需要某条日志。

**Error 和 WARN 日志** —— 你可能在几周后客户提交支持工单时需要这些日志，或者在试图理解某种模式时需要它们。30–90 天是合理的。

**INFO 日志** —— 对近期的事件调查有用，超过一两周后很少需要。大多数工作负载保留 7–14 天。

**Debug 日志** —— 如果你确实发送了任何 debug 日志，它们应该有非常短的保留期。最多 1–3 天。如果你在 48 小时内没有用到某条 debug 日志，那你几乎肯定永远不会用到它。

**审计日志** —— 与用户操作、访问事件、安全相关操作有关的日志。这些通常有合规要求。根据你的行业和司法管辖区，保留 1–7 年。

在 CloudWatch Logs 中，保留期是按日志组设置的：
```bash
aws logs put-retention-policy \
  --log-group-name /app/payment-service/info \
  --retention-in-days 14

aws logs put-retention-policy \
  --log-group-name /app/payment-service/error \
  --retention-in-days 90
```

在 Loki 中，保留期在后端层面配置，可以按租户或按流选择器应用。

## 识别成本的实际来源

在优化之前，先找出数据量来自哪里。大多数日志管理系统都有用量页面，或者你可以运行查询来查看哪些日志流的数据量最大。

在 CloudWatch 中：
```sql
-- Top log groups by size (run in Log Insights)
stats sum(bytes) as total_bytes by log_group
| sort total_bytes desc
| limit 20
```

在 Loki 中（通过 Grafana 中的 LogQL 指标查询）：
```logql
sum by (service) (rate({namespace="production"}[5m]))
```

你几乎总会发现，80% 的日志量来自 20% 的服务——而且往往是你最不关注的那些服务。一个高流量的 API 以 INFO 级别记录每个请求，或者一个配置错误的服务持续输出 debug 信息。

## 权衡：你放弃了什么

每一项降本措施都是一种权衡。要明确你接受了什么：

| 操作 | 节省的成本 | 失去的可观测性 |
|--------|-----------|----------------|
| 在 agent 层丢弃 DEBUG | 高 | 事后无法看到内部 debug 细节；必须临时添加 debug 日志并重新部署 |
| 对 INFO 日志采样 | 中 | 可能遗漏某些特定事件；但模式仍然可见 |
| 将 INFO 保留期从 30 天缩短到 7 天 | 中 | 无法调查超过 7 天前的事件 |
| 丢弃健康检查日志 | 低 | 无法查询健康检查模式，但这几乎从来不需要 |

目标是刻意做出这些权衡——清楚你放弃了什么——而不是意外砍掉某些你日后会后悔的东西。ERROR 几乎永远不应该被采样或给予较短的保留期。那才是出问题时你真正需要的数据。

<!-- ZH_RESOURCES -->
- [控制 AWS CloudWatch Logs 成本 (AWS)](https://aws.amazon.com/blogs/mt/best-practices-for-centralizing-logs-with-amazon-cloudwatch-logs/) -- 类型: 文章, 时长: 15m
- [降低 Loki 日志摄取成本 (Grafana Labs)](https://grafana.com/docs/loki/latest/operations/storage/retention/) -- 类型: 文章, 时长: 15m
- [日志采样策略 (Datadog)](https://www.datadoghq.com/blog/log-sampling/) -- 类型: 文章, 时长: 10m
- [Fluent Bit 过滤文档](https://docs.fluentbit.io/manual/pipeline/filters) -- 类型: 文章, 时长: 20m

<!-- ZH_UI -->
1. 设置日志保留策略，避免为从不查询的日志付费存储
2. 理解采样、过滤和丢弃日志之间的区别
3. 识别哪些日志流是高容量低价值的
4. 在 agent 层面实现日志级别过滤以减少摄取量
5. 日志成本现在已受控。但我仍然无法在不查询和计数的情况下回答“我的服务现在健康吗”。适合这个需求的工具是什么？
6. 我已经清理了嘈杂的日志并设置了保留策略，不再永久存储所有内容。但即使日志干净，每次想要实时了解性能时我仍然会求助于指标。日志和指标似乎在回答不同的问题。
