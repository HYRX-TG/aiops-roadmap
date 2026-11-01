---
id: prometheus-grafana
title: 'Prometheus + Grafana: Full Observability Stack'
zone: self-hosting
difficulty: 2
tags:
  - self-hosting
  - monitoring
  - prometheus
  - grafana
  - observability
category: tool
milestones:
  - Understand what Prometheus does (scraping, storing, querying metrics)
  - Deploy Prometheus and Grafana with Docker Compose
  - Add node_exporter to monitor your server's hardware
  - Import a pre-built Grafana dashboard
  - Write a basic alerting rule
title_zh: "Prometheus + Grafana：全栈可观测性"

---


Prometheus collects metrics from your services on a schedule, stores them as time-series data, and lets you query them. Grafana takes that data and turns it into dashboards and alerts. Together, they're the standard monitoring stack used everywhere from homelabs to production infrastructure at scale.

It's more involved to set up than a simple monitoring tool, but once running, you get historical data, custom dashboards, and alerting that can notify you through almost any channel.

<!-- DEEP_DIVE -->

## How the pieces fit together

```
Your services → exporters → Prometheus (scrape + store) → Grafana (visualize + alert)
```

**Prometheus** doesn't collect metrics by pushing them from your services. Instead, it *pulls* (scrapes) metrics from HTTP endpoints on a schedule (usually every 15 seconds). Each service exposes a `/metrics` endpoint that Prometheus reads.

**Exporters** are small programs that expose metrics for things that don't natively speak Prometheus. The most common is `node_exporter`, which exposes hardware and OS metrics (CPU, memory, disk, network) for Linux machines.

**Grafana** connects to Prometheus as a data source and lets you build dashboards, set alert rules, and send notifications to Slack, Discord, email, or whatever you use.

## Deploying the stack

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

  node-exporter:
    image: prom/node-exporter
    container_name: node-exporter
    restart: unless-stopped
    pid: host
    network_mode: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus-data:
  grafana-data:
```

## Configuring Prometheus

Create `prometheus.yml` next to your Compose file:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['host.docker.internal:9100']
```

This tells Prometheus to scrape `node_exporter` every 15 seconds. Add more targets as you add exporters for other services.

```bash
docker compose up -d
```

Prometheus is now at `http://YOUR-SERVER-IP:9090`, Grafana at `http://YOUR-SERVER-IP:3000`.

## Setting up Grafana

1. Log in to Grafana (default: `admin`/`admin`, it'll ask you to change the password)
2. Go to Connections → Data Sources → Add → Prometheus
3. Set the URL to `http://prometheus:9090` (Docker's internal DNS)
4. Save and test

Now import a dashboard. Go to Dashboards → Import, and enter dashboard ID `1860` (the "Node Exporter Full" community dashboard). Select your Prometheus data source. You'll immediately see CPU, memory, disk, network, and dozens of other metrics with historical graphs.

## Adding more exporters

The power of Prometheus is that almost everything has an exporter:

- **cAdvisor** — per-container CPU, memory, network metrics
- **Traefik** — has built-in Prometheus metrics (request counts, latency, error rates)
- **Blackbox exporter** — probe endpoints for uptime monitoring (HTTP, TCP, ICMP)

Each exporter gets a `targets` entry in `prometheus.yml`. The ecosystem is huge.

## Alerting

Grafana can send alerts based on metric thresholds. Common examples:

- Disk usage above 85% → send a Discord notification
- A service's HTTP endpoint returns non-200 for 5 minutes → send an email
- CPU sustained above 90% for 10 minutes → alert

Set these up in Grafana under Alerting → Alert rules. You define the query, the threshold, and where to send the notification (Grafana calls these "contact points").

## Is this overkill for a homelab?

Maybe. If you have one server and five services, Beszel is simpler and covers the basics. But if you enjoy dashboards, want to learn a tool used across the industry, or plan to grow your setup — Prometheus + Grafana is worth the investment. Once it's running, it mostly takes care of itself.

<!-- RESOURCES -->

- [Prometheus and Grafana Setup](https://blog.esc.sh/prometheus-grafana/) -- type: guide, time: 30min
- [Prometheus Documentation](https://prometheus.io/docs/) -- type: reference, time: ongoing
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/) -- type: reference, time: ongoing
- [Node Exporter Full Dashboard](https://grafana.com/grafana/dashboards/1860-node-exporter-full/) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
Prometheus 按计划从你的服务中采集指标，将其存储为时间序列数据，并允许你查询这些数据。Grafana 则接收这些数据，并将其转化为仪表盘和告警。二者结合，构成了从家庭实验室到大规模生产基础设施中无处不在的标准监控栈。

它的搭建比简单的监控工具更为复杂，但一旦运行起来，你就能获得历史数据、自定义仪表盘，以及可通过几乎任何渠道通知你的告警功能。

<!-- ZH_DEEP_DIVE -->
## 各部分如何协同工作

```
你的服务 → exporters → Prometheus（抓取 + 存储）→ Grafana（可视化 + 告警）
```

**Prometheus** 不会通过从你的服务推送指标来收集指标。相反，它会按计划（通常每 15 秒）从 HTTP 端点*拉取*（抓取）指标。每个服务都会暴露一个 `/metrics` 端点，供 Prometheus 读取。

**Exporters** 是一些小程序，用于为本身不支持 Prometheus 的对象暴露指标。最常见的是 `node_exporter`，它为 Linux 机器暴露硬件和操作系统指标（CPU、内存、磁盘、网络）。

**Grafana** 将 Prometheus 作为数据源连接，让你可以构建仪表盘、设置告警规则，并向 Slack、Discord、电子邮件或你使用的任何渠道发送通知。

## 部署整套栈

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

  node-exporter:
    image: prom/node-exporter
    container_name: node-exporter
    restart: unless-stopped
    pid: host
    network_mode: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus-data:
  grafana-data:
```

## 配置 Prometheus

在 Compose 文件旁边创建 `prometheus.yml`：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['host.docker.internal:9100']
```

这会告诉 Prometheus 每 15 秒抓取一次 `node_exporter`。当你为其他服务添加 exporter 时，再添加更多 target。

```bash
docker compose up -d
```

现在 Prometheus 位于 `http://YOUR-SERVER-IP:9090`，Grafana 位于 `http://YOUR-SERVER-IP:3000`。

## 设置 Grafana

1. 登录 Grafana（默认：`admin`/`admin`，它会要求你修改密码）
2. 转到 Connections → Data Sources → Add → Prometheus
3. 将 URL 设置为 `http://prometheus:9090`（Docker 的内部 DNS）
4. 保存并测试

现在导入一个仪表盘。转到 Dashboards → Import，输入仪表盘 ID `1860`（“Node Exporter Full”社区仪表盘）。选择你的 Prometheus 数据源。你会立即看到 CPU、内存、磁盘、网络以及数十个其他指标的历史图表。

## 添加更多 exporter

Prometheus 的强大之处在于几乎一切都有对应的 exporter：

- **cAdvisor** — 按容器统计的 CPU、内存、网络指标
- **Traefik** — 内置 Prometheus 指标（请求数、延迟、错误率）
- **Blackbox exporter** — 探测端点以进行正常运行时间监控（HTTP、TCP、ICMP）

每个 exporter 都会在 `prometheus.yml` 中获得一个 `targets` 条目。生态系统非常庞大。

## 告警

Grafana 可以根据指标阈值发送告警。常见示例：

- 磁盘使用率超过 85% → 发送 Discord 通知
- 某个服务的 HTTP 端点连续 5 分钟返回非 200 → 发送电子邮件
- CPU 持续高于 90% 达 10 分钟 → 告警

在 Grafana 的 Alerting → Alert rules 中设置这些规则。你定义查询、阈值以及将通知发送到哪里（Grafana 将这些称为“contact points”）。

## 这对 homelab 来说是否过度？

也许吧。如果你只有一台服务器和五个服务，Beszel 更简单，也能覆盖基础需求。但如果你喜欢仪表盘、想学习一个全行业都在使用的工具，或者计划扩展你的环境——Prometheus + Grafana 值得投入。一旦运行起来，它基本能自行运转。

<!-- ZH_RESOURCES -->
- [Prometheus 和 Grafana 搭建](https://blog.esc.sh/prometheus-grafana/) -- 类型: 指南, 时间: 30 分钟
- [Prometheus 文档](https://prometheus.io/docs/) -- 类型: 参考, 时间: 持续
- [Grafana 文档](https://grafana.com/docs/grafana/latest/) -- 类型: 参考, 时间: 持续
- [Node Exporter 完整仪表盘](https://grafana.com/grafana/dashboards/1860-node-exporter-full/) -- 类型: 参考, 时间: 5 分钟

<!-- ZH_UI -->
1. 理解 Prometheus 的功能（抓取、存储、查询指标）
2. 使用 Docker Compose 部署 Prometheus 和 Grafana
3. 添加 node_exporter 以监控服务器的硬件
4. 导入预构建的 Grafana 仪表板
5. 编写一条基本的告警规则
