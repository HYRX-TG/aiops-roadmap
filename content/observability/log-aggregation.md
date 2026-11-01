---
id: log-aggregation
title: Centralised Log Aggregation
zone: observability
edges:
  to:
    - id: querying-logs-effectively
      question: >-
        All my logs are in one place but I don't really know how to search
        them. I'm just scrolling.
      detail: >-
        I got everything centralized but now I'm staring at a wall of log lines
        and doing the same grep I was doing before. I know the query tool is
        more powerful than that — I just don't know how to use it well.
    - id: log-costs-and-retention
      question: My log bill is getting alarming. I'm logging everything and it adds up.
      detail: >-
        Every service is shipping logs and apparently I've been keeping 90 days
        of everything. The cost is growing faster than my traffic and I have no
        idea what I'm actually paying to store versus what I actually look at.
    - id: metrics-and-monitoring
      question: >-
        Logs tell me what happened. What tells me how the system is performing
        right now?
      detail: >-
        Logs are great for specific events but every performance question I want
        to ask — what's my error rate, how many requests per second, is latency
        getting worse — means querying and counting log lines. That can't be
        the right way to answer real-time performance questions.
difficulty: 1
tags:
  - logging
  - log-aggregation
  - cloudwatch
  - loki
  - elk
  - opensearch
  - fluentd
  - observability
category: practice
milestones:
  - >-
    Ship logs from an application to a central store (CloudWatch Logs, Loki, or
    equivalent)
  - >-
    Write a query to find all error logs from a specific service in the last
    hour
  - >-
    Filter logs by correlation ID to trace a single request across multiple
    services
  - Understand the cost implications of log retention and volume
title_zh: "集中式日志聚合"

---


Your application writes structured logs to stdout. Great. But right now those logs only exist in two places: the terminal where you ran the process (if it's still running) and the container's ephemeral buffer (if it's containerised). When the process restarts, that history is gone. When you have 30 container replicas spread across 10 nodes, you'd need to SSH into each one individually to read logs. This is why centralised log aggregation exists: to collect logs from everywhere they're generated and make them searchable from a single place.

The basic flow is straightforward. A log shipping agent runs alongside your applications — either as a sidecar container, a DaemonSet on each Kubernetes node, or a system service. It reads the stdout of your containers or processes, buffers the log lines, and forwards them to a central log store. The central store indexes the logs and provides a query interface. When something breaks at 2am, you open one browser tab and search across every service and every instance from one place.

The choice of tooling depends on where you're running and how much operational complexity you want to take on. The three main approaches are: a managed cloud service (CloudWatch Logs on AWS, Cloud Logging on GCP), a self-hosted lightweight option (Grafana Loki), or the traditional ELK/EFK stack (Elasticsearch or OpenSearch with Logstash or Fluentd and Kibana). Each has tradeoffs in cost, query power, and operational burden.

<!-- DEEP_DIVE -->

## How logs flow from app to query UI

Understanding the pipeline helps you debug it when something goes wrong and make informed decisions about each component.

```
Application stdout
      │
      ▼
Log Shipping Agent (Fluent Bit / Fluentd / CloudWatch Agent)
      │  (reads, buffers, optionally filters/transforms)
      ▼
Log Store (CloudWatch Logs / Loki / Elasticsearch)
      │  (indexes, stores, provides query API)
      ▼
Query UI (CloudWatch Logs Insights / Grafana / Kibana)
```

Each stage has a job:

**The shipping agent** reads log output from your applications, optionally enriches or filters them (adding Kubernetes metadata like pod name and namespace, dropping debug logs, parsing multi-line stack traces), and forwards them to the central store. It usually runs with buffering and retry logic so it doesn't lose logs if the destination is temporarily unavailable.

**The log store** is responsible for ingesting log data, indexing it for fast querying, and storing it durably. Indexing is what makes search fast — instead of scanning every log line every time you query, the index lets the store jump directly to lines matching your filters.

**The query UI** sits on top of the store and gives you a way to write queries, view results, build dashboards, and set up alerts. In many stacks, this is where you'll spend most of your time during an incident.

## The main options

### CloudWatch Logs (AWS)

If you're running on AWS, CloudWatch Logs is the path of least resistance. EC2 instances, ECS containers, and Lambda functions can all be configured to ship logs to CloudWatch with minimal setup. You don't run any infrastructure for it — Amazon manages the collection and storage layer.

The query interface, CloudWatch Logs Insights, is capable of field-level filtering, aggregation, and even visualization. The tradeoff is cost — CloudWatch charges per GB ingested and per GB stored, and those costs add up faster than most people expect.

### Grafana Loki

Loki is a log aggregation system designed by the Grafana team that takes a deliberately different approach to indexing. Traditional systems like Elasticsearch index every field in every log line, which is powerful but expensive. Loki indexes only labels (like `service`, `host`, and `environment`) and stores the log content compressed but unindexed. This makes Loki much cheaper to run at scale, with the tradeoff that queries against unindexed fields are slower.

If you're already running Grafana (or want to), Loki is a natural fit. Fluent Bit can ship to Loki with a straightforward configuration, and the query language (LogQL) is readable and powerful for field-filtered searches.

### ELK / EFK Stack

Elasticsearch is the most powerful option for log search — it indexes every field, making arbitrary queries fast. Kibana is a full-featured UI for searching logs, building dashboards, and configuring alerts. Logstash or Fluentd sits in the middle doing log parsing and routing.

The tradeoff is operational complexity. Running Elasticsearch reliably requires real work — it's memory-hungry, needs careful tuning, and can be difficult to operate at scale without experience. For small teams, this overhead often isn't worth it. OpenSearch is the open-source fork of Elasticsearch and is functionally equivalent for most purposes.

## Shipping agents: Fluent Bit vs. Fluentd

**Fluent Bit** is a lightweight log forwarder written in C. It's fast, has a small memory footprint, and is the recommended choice for most Kubernetes setups. It runs as a DaemonSet (one instance per node), reads container logs, applies filters, and forwards to your chosen backend.

**Fluentd** is the older, heavier sibling. It supports a much larger plugin ecosystem, which is useful if you need complex parsing or routing. But it uses more memory and CPU than Fluent Bit. A common pattern: Fluent Bit on each node for collection, Fluentd as a centralised aggregator for complex processing before forwarding to the store.

## A practical Fluent Bit configuration for Kubernetes + Loki

```ini
[SERVICE]
    Flush     5
    Log_Level info

[INPUT]
    Name              tail
    Path              /var/log/containers/*.log
    Parser            docker
    Tag               kube.*
    Refresh_Interval  5

[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_Tag_Prefix     kube.var.log.containers.
    Merge_Log           On
    Keep_Log            Off

[OUTPUT]
    Name        loki
    Match       *
    Host        loki.monitoring.svc.cluster.local
    Port        3100
    Labels      job=fluentbit, namespace=$kubernetes['namespace_name'], pod=$kubernetes['pod_name']
```

This reads container logs, enriches them with Kubernetes metadata (namespace, pod name, labels), and forwards to Loki with meaningful labels.

## Retention: what to think about before you set it up

Most log stores let you configure retention — how long logs are kept before they're automatically deleted. The default in many managed services is 90 days, which is almost certainly longer than you need for most logs. Retention drives storage costs directly.

A reasonable starting point for small teams:
- ERROR and WARN logs: 30–90 days (you'll need these for incident retrospectives)
- INFO logs: 14–30 days (useful for recent investigations, rarely needed beyond that)
- DEBUG logs: 3–7 days at most (almost never needed after the fact)

Set these deliberately before you start generating volume. It's much easier to configure short retention upfront than to delete 6 months of stored logs later.

<!-- RESOURCES -->

- [Fluent Bit Documentation](https://docs.fluentbit.io/) -- type: article, time: 30m
- [Grafana Loki Getting Started](https://grafana.com/docs/loki/latest/get-started/) -- type: tutorial, time: 30m
- [CloudWatch Logs Insights — Getting Started](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_RunSampleQuery.html) -- type: tutorial, time: 15m
- [Elasticsearch: The Definitive Guide (free online)](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html) -- type: book, time: 300m

<!-- ZH_SUMMARY -->
你的应用将结构化日志写入 stdout。很好。但眼下这些日志只存在于两个地方：运行进程的终端（如果进程还在运行）以及容器的临时缓冲区（如果应用容器化）。进程重启后，这段历史就消失了。当你有 30 个容器副本分布在 10 个节点上时，你需要逐个 SSH 登录才能读取日志。这正是集中式日志聚合存在的意义：从日志产生的所有位置收集日志，并让它们可以从单一位置被搜索。

基本流程很直接。一个日志投递代理与你的应用一同运行——可以是 sidecar 容器、每个 Kubernetes 节点上的 DaemonSet，或一个系统服务。它读取容器或进程的 stdout，缓冲日志行，并将它们转发到中央日志存储。中央存储对日志建立索引并提供查询接口。当凌晨 2 点出问题时，你打开一个浏览器标签页，就能从一处搜索所有服务和所有实例。

工具的选择取决于你的运行环境以及你愿意承担多少运维复杂度。主要有三种方案：托管云服务（AWS 上的 CloudWatch Logs、GCP 上的 Cloud Logging）、自托管的轻量级方案（Grafana Loki），或传统的 ELK/EFK 栈（Elasticsearch 或 OpenSearch 搭配 Logstash 或 Fluentd 以及 Kibana）。每种方案在成本、查询能力和运维负担上各有取舍。

<!-- ZH_DEEP_DIVE -->
## 日志如何从应用流向查询 UI

理解这条流水线有助于在出问题时进行调试，并对每个组件做出明智的决策。

```
Application stdout
      │
      ▼
Log Shipping Agent (Fluent Bit / Fluentd / CloudWatch Agent)
      │  (reads, buffers, optionally filters/transforms)
      ▼
Log Store (CloudWatch Logs / Loki / Elasticsearch)
      │  (indexes, stores, provides query API)
      ▼
Query UI (CloudWatch Logs Insights / Grafana / Kibana)
```

每个阶段都有各自的职责：

**日志采集代理（shipping agent）** 读取应用的日志输出，可选地对其进行富化或过滤（添加 Kubernetes 元数据，如 pod 名称和 namespace；丢弃 debug 日志；解析多行堆栈跟踪），然后转发到中央存储。它通常带有缓冲和重试逻辑，因此即使目标端暂时不可用，也不会丢失日志。

**日志存储（log store）** 负责接收日志数据、为其建立索引以便快速查询，并持久化存储。索引是让搜索变快的关键——有了索引，查询时存储无需扫描每一行日志，而是可以直接跳到符合过滤条件的行。

**查询 UI（query UI）** 位于存储之上，提供编写查询、查看结果、构建仪表盘和设置告警的能力。在许多技术栈中，事故处理期间你会把大部分时间花在这里。

## 主要选项

### CloudWatch Logs (AWS)

如果你运行在 AWS 上，CloudWatch Logs 是最省事的路径。EC2 实例、ECS 容器和 Lambda 函数都可以用最少的配置将日志发送到 CloudWatch。你无需运维任何基础设施——采集和存储层由 Amazon 管理。

查询界面 CloudWatch Logs Insights 支持字段级过滤、聚合，甚至可视化。代价是成本——CloudWatch 按摄入 GB 和存储 GB 收费，这些费用累积的速度比大多数人预期的要快。

### Grafana Loki

Loki 是 Grafana 团队设计的日志聚合系统，在索引方式上有意采取了不同的思路。像 Elasticsearch 这样的传统系统会为每一行日志中的每个字段建立索引，功能强大但成本高昂。Loki 只为标签（如 `service`、`host` 和 `environment`）建立索引，日志内容压缩存储但不建索引。这使得 Loki 在大规模运行时成本低得多，代价是对未建索引字段的查询会更慢。

如果你已经在运行 Grafana（或者打算运行），Loki 是自然的选择。Fluent Bit 可以通过简单的配置将日志发送到 Loki，查询语言（LogQL）可读性强，且对字段过滤搜索很强大。

### ELK / EFK Stack

Elasticsearch 是日志搜索方面最强大的选项——它为每个字段建立索引，使任意查询都很快。Kibana 是一个功能齐全的 UI，用于搜索日志、构建仪表盘和配置告警。Logstash 或 Fluentd 位于中间，负责日志解析和路由。

代价是运维复杂性。可靠地运行 Elasticsearch 需要实打实的工作——它很吃内存，需要仔细调优，没有经验的话在大规模下很难运维。对小团队来说，这种开销往往不值得。OpenSearch 是 Elasticsearch 的开源分支，在大多数用途上功能等价。

## 采集代理：Fluent Bit vs. Fluentd

**Fluent Bit** 是用 C 编写的轻量级日志转发器。它速度快、内存占用小，是大多数 Kubernetes 环境推荐的选择。它以 DaemonSet 方式运行（每个节点一个实例），读取容器日志、应用过滤器，并转发到你选择的后端。

**Fluentd** 是更老、更重的同类产品。它支持大得多的插件生态，如果你需要复杂的解析或路由，这会很有用。但它比 Fluent Bit 消耗更多的内存和 CPU。一种常见模式是：每个节点上用 Fluent Bit 做采集，用 Fluentd 作为集中式聚合器做复杂处理，然后再转发到存储。

## 面向 Kubernetes + Loki 的实用 Fluent Bit 配置

```ini
[SERVICE]
    Flush     5
    Log_Level info

[INPUT]
    Name              tail
    Path              /var/log/containers/*.log
    Parser            docker
    Tag               kube.*
    Refresh_Interval  5

[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_Tag_Prefix     kube.var.log.containers.
    Merge_Log           On
    Keep_Log            Off

[OUTPUT]
    Name        loki
    Match       *
    Host        loki.monitoring.svc.cluster.local
    Port        3100
    Labels      job=fluentbit, namespace=$kubernetes['namespace_name'], pod=$kubernetes['pod_name']
```

这段配置读取容器日志，用 Kubernetes 元数据（namespace、pod 名称、标签）对其进行富化，并以有意义的标签转发到 Loki。

## 保留策略：设置之前需要考虑的事项

大多数日志存储都允许你配置保留期——日志在被自动删除之前保留多长时间。许多托管服务的默认值是 90 天，这几乎肯定比大多数日志实际需要的更长。保留期直接影响存储成本。

对小团队来说，一个合理的起点是：
- ERROR 和 WARN 日志：30–90 天（事故复盘时你会需要这些）
- INFO 日志：14–30 天（对近期排查有用，再往前很少需要）
- DEBUG 日志：最多 3–7 天（事后几乎从不需要）

在开始产生大量日志之前，有意识地设置这些策略。提前配置较短的保留期，比之后删除 6 个月的已存日志要容易得多。

<!-- ZH_RESOURCES -->
- [Fluent Bit 文档](https://docs.fluentbit.io/) -- 类型: 文章, 时间: 30m
- [Grafana Loki 入门](https://grafana.com/docs/loki/latest/get-started/) -- 类型: 教程, 时间: 30m
- [CloudWatch Logs Insights — 入门](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_RunSampleQuery.html) -- 类型: 教程, 时间: 15m
- [Elasticsearch: The Definitive Guide（免费在线版）](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html) -- 类型: 书籍, 时间: 300m

<!-- ZH_UI -->
1. 将应用日志发送到集中存储（CloudWatch Logs、Loki 或同等方案）
2. 编写查询，查找特定服务在过去一小时内的所有错误日志
3. 按关联 ID 过滤日志，以追踪跨多个服务的单个请求
4. 理解日志保留和日志量的成本影响
5. 我的日志都在一个地方，但我真不知道怎么搜索它们。我只是在滚动翻看。
6. 我把一切都集中起来了，但现在我盯着一大堆日志行，还在做和以前一样的 grep。我知道查询工具比这强大得多——我只是不知道该怎么用好它。
7. 我的日志账单开始让人警觉了。我记录了一切，费用就这样累积起来了。
8. 每个服务都在发送日志，显然我一直保留着所有东西 90 天。成本增长得比我的流量还快，我完全不知道我到底在为什么存储付费，又实际查看了什么。
9. 日志告诉我发生了什么。什么能告诉我系统现在的性能如何？
10. 日志非常适合记录特定事件，但我想问的每个性能问题——我的错误率是多少、每秒有多少请求、延迟是否在变差——都意味着要查询和统计日志行。这不可能是回答实时性能问题的正确方式。
