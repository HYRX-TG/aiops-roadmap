---
id: beszel
title: 'Beszel: Simple Server Monitoring'
zone: self-hosting
difficulty: 1
tags:
  - self-hosting
  - monitoring
  - beszel
  - docker
category: tool
milestones:
  - Deploy Beszel with Docker Compose
  - Add your server as a monitored host
  - See CPU, memory, disk, and network stats in the dashboard
  - Set up a basic alert for disk usage
title_zh: "Beszel：简易服务器监控"

---


Beszel is a lightweight server monitoring tool that runs as a single Docker container. It gives you a clean web dashboard showing CPU, memory, disk, network, and container stats for each of your servers. No complicated setup, no YAML config files to wrestle with — deploy it, add your hosts, and you have monitoring.

For a homelab with one or two servers, this is often all you need.

<!-- DEEP_DIVE -->

## How it works

Beszel has two parts:

- **Hub** — the web UI and data collector. This runs on one machine (wherever you want to view your dashboard).
- **Agent** — a tiny binary that runs on each machine you want to monitor. It collects system metrics and sends them to the hub.

The agent is lightweight — it uses minimal CPU and memory, and you won't notice it running.

## Deploying the hub

```yaml
# docker-compose.yml
services:
  beszel:
    image: henrygd/beszel
    container_name: beszel
    restart: unless-stopped
    ports:
      - "8090:8090"
    volumes:
      - ./beszel-data:/beszel_data
```

```bash
docker compose up -d
```

Open `http://YOUR-SERVER-IP:8090` and create your admin account.

## Adding a server

In the Beszel web UI, click to add a new system. It gives you a command to run the agent — either as a Docker container or a standalone binary. For Docker:

```yaml
services:
  beszel-agent:
    image: henrygd/beszel-agent
    container_name: beszel-agent
    restart: unless-stopped
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      PORT: 45876
      KEY: "<your-key-from-the-ui>"
```

The agent starts reporting immediately. Within seconds you'll see your server's stats in the dashboard.

## What you get

The dashboard shows real-time and recent historical data for each host:

- **CPU** — usage percentage, per-core breakdown
- **Memory** — used, available, swap
- **Disk** — usage per mount, read/write rates
- **Network** — bandwidth in/out
- **Docker containers** — CPU and memory per container, running status

It also supports basic alerting — you can set thresholds (e.g., disk usage above 90%) and get notified.

## When Beszel isn't enough

Beszel is great for "is my server healthy right now?" It's less suited for:

- Long-term metric storage and trend analysis
- Custom application metrics (e.g., request latency from your reverse proxy)
- Complex alerting rules with multiple conditions
- Monitoring across many servers with aggregated views

If you find yourself wanting these, Prometheus + Grafana is the next step.

<!-- RESOURCES -->

- [Simple Monitoring with Beszel](https://blog.esc.sh/simple-monitoring-with-beszel/) -- type: guide, time: 15min
- [Beszel on GitHub](https://github.com/henrygd/beszel) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
Beszel 是一款轻量级服务器监控工具，以单个 Docker 容器运行。它提供一个简洁的 Web 仪表盘，展示每台服务器的 CPU、内存、磁盘、网络和容器统计信息。无需复杂配置，无需与 YAML 配置文件较劲——部署它、添加主机，你就拥有了监控能力。

对于只有一两台服务器的家庭实验室来说，这通常就是你需要的全部。

<!-- ZH_DEEP_DIVE -->
## 工作原理

Beszel 由两部分组成：

- **Hub** — Web UI 和数据收集器。它运行在一台机器上（你想在哪里查看仪表盘都可以）。
- **Agent** — 一个极小的二进制程序，运行在每台你想监控的机器上。它收集系统指标并发送给 hub。

Agent 非常轻量——占用极少的 CPU 和内存，你几乎不会注意到它在运行。

## 部署 hub

```yaml
# docker-compose.yml
services:
  beszel:
    image: henrygd/beszel
    container_name: beszel
    restart: unless-stopped
    ports:
      - "8090:8090"
    volumes:
      - ./beszel-data:/beszel_data
```

```bash
docker compose up -d
```

打开 `http://YOUR-SERVER-IP:8090` 并创建你的管理员账户。

## 添加服务器

在 Beszel Web UI 中，点击添加新系统。它会给你一条运行 agent 的命令——可以作为 Docker 容器运行，也可以作为独立二进制运行。对于 Docker：

```yaml
services:
  beszel-agent:
    image: henrygd/beszel-agent
    container_name: beszel-agent
    restart: unless-stopped
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      PORT: 45876
      KEY: "<your-key-from-the-ui>"
```

Agent 会立即开始上报。几秒钟内你就能在仪表盘中看到服务器的统计数据。

## 你能得到什么

仪表盘会显示每台主机的实时和近期历史数据：

- **CPU** — 使用率百分比、每核心明细
- **内存** — 已用、可用、swap
- **磁盘** — 每个挂载点的使用情况、读写速率
- **网络** — 入/出带宽
- **Docker 容器** — 每个容器的 CPU 和内存、运行状态

它还支持基础告警——你可以设置阈值（例如磁盘使用率超过 90%）并接收通知。

## 当 Beszel 不够用时

Beszel 非常适合回答“我的服务器现在健康吗？”它不太适合：

- 长期指标存储和趋势分析
- 自定义应用指标（例如来自反向代理的请求延迟）
- 带多个条件的复杂告警规则
- 跨多台服务器监控并聚合视图

如果你发现自己需要这些功能，下一步就是 Prometheus + Grafana。

<!-- ZH_RESOURCES -->
- [使用 Beszel 进行简单监控](https://blog.esc.sh/simple-monitoring-with-beszel/) -- type: guide, time: 15min
- [GitHub 上的 Beszel](https://github.com/henrygd/beszel) -- type: reference, time: 5min

<!-- ZH_UI -->
1. 使用 Docker Compose 部署 Beszel
2. 将你的服务器添加为受监控主机
3. 在仪表盘中查看 CPU、内存、磁盘和网络统计
4. 为磁盘使用率设置基本告警
