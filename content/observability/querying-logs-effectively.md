---
id: querying-logs-effectively
title: Querying Logs Effectively
zone: observability
edges:
  to:
    - id: metrics-and-monitoring
      question: >-
        Logs tell me about specific events. But how do I see how my service is
        performing overall, right now?
      detail: >-
        I can dig up what happened after the fact in the logs, but I can't
        answer "is my service currently healthy?" from logs alone. Every
        question I want to ask — what's my error rate, how many requests per
        second — requires me to query and count. There must be a better tool
        for real-time performance questions.
difficulty: 1
tags:
  - logging
  - log-querying
  - loki
  - cloudwatch-logs-insights
  - observability
category: practice
milestones:
  - Write queries to filter logs by field values (service name, log level, user ID)
  - Use a correlation ID to trace a single request across multiple services in logs
  - Understand the difference between full-text search and structured field queries
  - Know when logs are the right tool vs. when metrics would answer the question better
title_zh: "高效查询日志"

---


Getting logs into a central store is only half the work. The other half is being able to find what you need when something goes wrong. Most people start by scrolling through the log viewer and ctrl-F-ing for keywords — the same thing they were doing on the command line. That approach hits a wall quickly. When you're dealing with thousands of log lines across dozens of services, you need to write actual queries rather than browse.

The mental model shift is from "find the line that says what I'm looking for" to "ask a question of the log data." The difference is the same as using SQL versus scrolling through a spreadsheet. The query language lets you filter by specific fields, narrow by time range, join on correlation IDs across services, and extract counts and rates — none of which is practical with manual browsing.

The investment in learning your log query language pays for itself the first time you're in an incident. Knowing how to answer "show me all errors in the payment service in the last 30 minutes, for users in the EU, grouped by error type" in under a minute is the difference between a 10-minute investigation and a 2-hour one.

<!-- DEEP_DIVE -->

## Full-text search vs. structured field queries

Log systems support two types of search, and they're used for different things.

**Full-text search** treats the entire log line as text and searches for a substring match. This is the equivalent of grep. It's useful when you don't know the exact field name, when you're searching for an error message you already know, or when your logs aren't structured.

```
# Full-text search — find any line containing this string
"connection refused"
```

**Structured field queries** filter on specific key-value pairs. This is only possible when your logs are structured (JSON). It's faster, more precise, and composable — you can combine multiple field filters.

```
# Structured query — find lines where the level field equals "error"
# AND the service field equals "payment-service"
level="error" AND service="payment-service"
```

The practical difference: full-text search for "error" will match log lines that happen to contain the word "error" anywhere — in the message, in a variable value, in a user-provided string. A structured query for `level="error"` only matches lines where the log level is actually set to error by your logging library.

When your logs are structured, always prefer field queries over full-text search. They're more precise and much faster at scale.

## Querying with Loki (LogQL)

LogQL is Loki's query language. It has two parts: a log stream selector (which selects which log streams to look at, based on labels) and an optional filter pipeline.

**Basic label filtering:**
```logql
{service="payment-service"}
```
This selects all log lines from the payment-service label. Labels in Loki are the metadata attached at ship time (service name, namespace, pod name).

**Adding a filter on log content:**
```logql
{service="payment-service"} |= "error"
```
The `|=` operator filters for lines containing the string "error". This is full-text search within the selected stream.

**Filtering on JSON fields (structured logs):**
```logql
{service="payment-service"} | json | level="error"
```
The `| json` step parses each log line as JSON and extracts the fields. After that, you can filter on any field.

**Combining filters:**
```logql
{service="payment-service"} | json | level="error" | duration_ms > 1000
```
Error logs from the payment service where the request took more than 1 second.

**Filtering by correlation ID:**
```logql
{namespace="production"} | json | request_id="req_a8f3d2c1"
```
This finds all log lines with that request ID, across every service in the production namespace — showing you the complete story of that one request.

## Querying with CloudWatch Logs Insights

CloudWatch Logs Insights uses its own SQL-like query language. The basic building blocks are `fields`, `filter`, `stats`, and `sort`.

**Find all errors in the last hour:**
```sql
fields @timestamp, @message
| filter level = "error"
| sort @timestamp desc
| limit 100
```

**Filter by service and error level:**
```sql
fields @timestamp, service, message, user_id
| filter level = "error" and service = "payment-service"
| sort @timestamp desc
```

**Trace a single request by correlation ID:**
```sql
fields @timestamp, service, level, message
| filter request_id = "req_a8f3d2c1"
| sort @timestamp asc
```

Note the `sort @timestamp asc` — when tracing a request, you want chronological order so you can see what happened first.

**Count errors by type:**
```sql
filter level = "error"
| stats count(*) as error_count by reason
| sort error_count desc
```

This gives you a breakdown of what's failing and how often, which is useful for prioritising what to fix.

## The correlation ID workflow

This is the most powerful technique for diagnosing problems in a distributed system. The steps:

1. Something breaks. You get a report: "user 9912 got an error at 14:32."
2. You don't know which service failed — it could be the API, the payment service, the notification service, any of them.
3. You search for all logs for that user around that time: `user_id="9912"` with a time filter of ±5 minutes.
4. You find a log line with a `request_id`: `"req_a8f3d2c1"`.
5. You search for that request ID across all services: `request_id="req_a8f3d2c1"`.
6. Now you see every log line that was part of that one request — from the API that received it, to the payment service that processed it, to the notification service that tried to send the email. In chronological order.
7. You can see exactly where in the chain the failure happened, what error was thrown, and what the state was at that point.

This entire investigation might take 3 minutes with good structured logs and a correlation ID. Without them, it might take hours of SSH-ing into machines and correlating timestamps manually.

## When to use logs vs. metrics

Logs and metrics answer different questions. Knowing which one to reach for saves time.

**Reach for logs when:**
- You know something specific happened and want to understand the details: what error, for which user, what was the input?
- You're tracing a single request or user session across multiple services.
- You need the exact sequence of events leading up to a failure.
- You're debugging a bug and need to see exactly what the code was doing.

**Reach for metrics when:**
- You want to know the current state of the system: error rate, request rate, latency percentiles.
- You want to compare now to an hour ago or a week ago.
- You want to know if something is trending up or down over time.
- You want to be alerted when a threshold is crossed.

The failure mode to avoid: using log queries to answer metric-shaped questions. Counting log lines to calculate your error rate is slow, expensive, and delayed. Metrics are pre-aggregated and much faster for that use case. Use each tool for what it's good at.

<!-- RESOURCES -->

- [LogQL Documentation (Grafana Loki)](https://grafana.com/docs/loki/latest/query/) -- type: article, time: 20m
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html) -- type: article, time: 15m
- [Tutorial: Querying Logs with Loki and Grafana](https://grafana.com/tutorials/query-logs-loki/) -- type: tutorial, time: 25m

<!-- ZH_SUMMARY -->
把日志收集到中央存储只是工作的一半，另一半是在出问题时能快速找到所需信息。大多数人一开始都是滚动浏览日志查看器，用 Ctrl-F 搜索关键词——和在命令行里做的事一样。这种方式很快就会碰壁。当你面对数十个服务的数千行日志时，你需要编写真正的查询，而不是靠浏览。

思维模式的转变在于：从“找到那句写着我要找的内容的日志行”转变为“向日志数据提问”。这就像用 SQL 查询与滚动浏览电子表格的区别。查询语言让你能按特定字段过滤、按时间范围缩小范围、跨服务按关联 ID 进行关联，以及提取计数和速率——这些都无法靠手动浏览实际做到。

学习日志查询语言的投入，在你第一次遇到故障时就能回本。能在不到一分钟内回答“显示过去 30 分钟内支付服务的所有错误，针对欧盟用户，按错误类型分组”这样的问题，就是 10 分钟排查和 2 小时排查之间的差别。

<!-- ZH_DEEP_DIVE -->
## 全文搜索与结构化字段查询

日志系统支持两种类型的搜索，它们用于不同的场景。

**全文搜索**将整行日志视为文本，搜索子字符串匹配。这相当于 grep。当你不知道确切的字段名、当你搜索一条你已经知道的错误消息、或者当你的日志是非结构化的时候，它很有用。

```
# 全文搜索——查找包含此字符串的任意行
"connection refused"
```

**结构化字段查询**基于特定的键值对进行过滤。这只有在你的日志是结构化（JSON）的情况下才可能实现。它更快、更精确、并且可组合——你可以组合多个字段过滤器。

```
# 结构化查询——查找 level 字段等于 "error"
# 且 service 字段等于 "payment-service" 的行
level="error" AND service="payment-service"
```

实际区别在于：全文搜索 "error" 会匹配任何恰好包含 "error" 这个词的日志行——无论是在消息中、在变量值中、还是在用户提供的字符串中。而针对 `level="error"` 的结构化查询只会匹配日志级别确实被你的日志库设置为 error 的行。

当你的日志是结构化的时候，始终优先使用字段查询而非全文搜索。它们更精确，并且在大规模场景下快得多。

## 使用 Loki 查询（LogQL）

LogQL 是 Loki 的查询语言。它有两个部分：日志流选择器（根据标签选择要查看哪些日志流）和可选的过滤器管道。

**基本的标签过滤：**
```logql
{service="payment-service"}
```
这会选择来自 payment-service 标签的所有日志行。Loki 中的标签是在传输时附加的元数据（服务名、命名空间、Pod 名）。

**在日志内容上添加过滤器：**
```logql
{service="payment-service"} |= "error"
```
`|=` 运算符过滤出包含字符串 "error" 的行。这是在所选流内进行的全文搜索。

**基于 JSON 字段过滤（结构化日志）：**
```logql
{service="payment-service"} | json | level="error"
```
`| json` 步骤将每一行日志解析为 JSON 并提取字段。之后，你可以基于任意字段进行过滤。

**组合过滤器：**
```logql
{service="payment-service"} | json | level="error" | duration_ms > 1000
```
来自支付服务的、请求耗时超过 1 秒的错误日志。

**按关联 ID 过滤：**
```logql
{namespace="production"} | json | request_id="req_a8f3d2c1"
```
这会查找具有该请求 ID 的所有日志行，跨越 production 命名空间中的每个服务——向你展示那一个请求的完整故事。

## 使用 CloudWatch Logs Insights 查询

CloudWatch Logs Insights 使用它自己的类 SQL 查询语言。基本的构建块是 `fields`、`filter`、`stats` 和 `sort`。

**查找过去一小时内的所有错误：**
```sql
fields @timestamp, @message
| filter level = "error"
| sort @timestamp desc
| limit 100
```

**按服务和错误级别过滤：**
```sql
fields @timestamp, service, message, user_id
| filter level = "error" and service = "payment-service"
| sort @timestamp desc
```

**按关联 ID 追踪单个请求：**
```sql
fields @timestamp, service, level, message
| filter request_id = "req_a8f3d2c1"
| sort @timestamp asc
```

注意 `sort @timestamp asc`——在追踪请求时，你希望按时间顺序排列，这样你就能看到先发生了什么。

**按类型统计错误：**
```sql
filter level = "error"
| stats count(*) as error_count by reason
| sort error_count desc
```

这会给你一个关于什么在失败以及失败频率的细分，这对于确定修复优先级很有用。

## 关联 ID 工作流

这是在分布式系统中诊断问题最强大的技术。步骤如下：

1. 出问题了。你收到一份报告："用户 9912 在 14:32 遇到了一个错误。"
2. 你不知道哪个服务失败了——可能是 API、支付服务、通知服务，任何一个。
3. 你搜索该用户在那个时间附近的所有日志：`user_id="9912"`，时间过滤范围为 ±5 分钟。
4. 你找到一行带有 `request_id` 的日志：`"req_a8f3d2c1"`。
5. 你跨所有服务搜索该请求 ID：`request_id="req_a8f3d2c1"`。
6. 现在你看到了属于那一个请求的每一行日志——从接收它的 API，到处理它的支付服务，再到尝试发送邮件的通知服务。按时间顺序排列。
7. 你可以确切地看到链条中失败发生在哪里、抛出了什么错误、以及那一刻的状态是什么。

有了良好的结构化日志和关联 ID，整个调查可能只需 3 分钟。没有它们，可能需要数小时 SSH 登录机器并手动关联时间戳。

## 何时使用日志 vs. 指标

日志和指标回答不同的问题。知道该用哪一个可以节省时间。

**在以下情况使用日志：**
- 你知道某件具体的事情发生了，想了解细节：什么错误、对哪个用户、输入是什么？
- 你正在跨多个服务追踪单个请求或用户会话。
- 你需要导致失败的事件的确切顺序。
- 你正在调试一个 bug，需要确切看到代码在做什么。

**在以下情况使用指标：**
- 你想知道系统的当前状态：错误率、请求速率、延迟百分位数。
- 你想将现在与一小时前或一周前进行比较。
- 你想知道某事物随时间呈上升还是下降趋势。
- 你想在跨越阈值时收到告警。

要避免的失败模式：用日志查询来回答指标形态的问题。通过统计日志行来计算错误率是缓慢、昂贵且有延迟的。指标是预聚合的，对于这种用例要快得多。让每个工具发挥它擅长的作用。

<!-- ZH_RESOURCES -->
- [LogQL 文档 (Grafana Loki)](https://grafana.com/docs/loki/latest/query/) -- 类型: 文章, 时间: 20m
- [CloudWatch Logs Insights 查询语法](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html) -- 类型: 文章, 时间: 15m
- [教程：使用 Loki 和 Grafana 查询日志](https://grafana.com/tutorials/query-logs-loki/) -- 类型: 教程, 时间: 25m

<!-- ZH_UI -->
1. 编写查询，按字段值（服务名、日志级别、用户 ID）过滤日志
2. 使用关联 ID 在日志中追踪跨多个服务的单个请求
3. 理解全文搜索与结构化字段查询的区别
4. 知道何时日志是合适的工具，何时指标能更好地回答问题
5. 日志告诉我具体事件。但我怎么查看服务当前的整体运行状况？
6. 我可以在日志中事后挖掘发生了什么，但仅凭日志无法回答“我的服务当前是否健康？”我想问的每个问题——错误率是多少、每秒多少请求——都需要查询和计数。一定有更好的工具来回答实时性能问题。
