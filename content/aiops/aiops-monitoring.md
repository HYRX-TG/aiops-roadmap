---
id: aiops-monitoring
title: 监控接入：夜莺 + MCP 暴露工具
title_en: "Monitoring Ingestion: Nightingale + MCP Tools"
zone: aiops
difficulty: 2
tags: [夜莺, Nightingale, MCP, 监控, 指标]
category: practice
milestones:
  - 能说清为什么选夜莺而不是纯 Prometheus
  - 能在夜莺里配置告警并触发 Webhook
  - 能把一个指标查询封装成 MCP 工具供 LLM 调用
edges:
  to:
    - id: aiops-rca
      question: 数据齐了，怎么用大模型做根因分析？
---

## 为什么从监控接入开始

AIOps 再聪明，也必须有**数据底座**。没有统一的监控，模型就是瞎子。

本项目用 **夜莺监控（Nightingale）** 作为统一监控入口：它国产、轻量，能同时接 Prometheus 指标、日志和告警，还自带告警规则与通知。

## 关键一步：把监控变成"模型能调用的工具"

光有仪表盘不够。要让大模型能**主动查询**指标，需要把查询封装成 **MCP（Model Context Protocol）工具**：

```
夜莺 API  ──封装──▶  MCP Server  ──暴露──▶  query_metric / get_alert / list_targets
                                                │
                                                ▼
                                          大模型（按需调用）
```

这样模型在诊断时，可以自己决定"我现在需要看哪个服务的 CPU"并实时拉数据，而不是靠人把截图喂给它。

<!-- DEEP_DIVE -->

## 落地要点

1. **统一告警格式**：夜莺告警 → Webhook → 标准化成 `{service, severity, metric, value, time}` JSON；
2. **工具粒度要小**：不要一个"查所有"的工具，而是 `query_metric`、`get_recent_alerts`、`list_deployed_versions` 这种原子工具，模型更好组合；
3. **权限最小化**：MCP 工具默认只读；写操作（如触发执行）一律走护栏层，不在这里开放。

## 一个常见坑

新手容易把"监控好看"当成"接入完成"。真正的完成标志是：**模型能通过一个工具调用，拿到它诊断所需的那一条指标**——而不是人在 Grafana 里翻半天再截图。

<!-- RESOURCES -->

## 参考资料

- [夜莺监控官方文档](https://n9e.github.io/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Prometheus 查询语言 PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/)
