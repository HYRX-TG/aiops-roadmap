---
id: use-method
title: The USE Method
zone: observability
edges:
  to:
    - id: prometheus-basics
      question: >-
        I know what USE means now. How do I actually collect utilization,
        saturation, and error metrics from my infrastructure?
      detail: >-
        USE makes sense in theory but I don't know how to get these numbers.
        Is CPU utilization something I instrument in my app, or does something
        scrape it from the host? Who collects disk saturation? I'm not sure
        where the boundary is between app metrics and infra metrics.
difficulty: 1
tags:
  - metrics
  - use-method
  - utilization
  - saturation
  - infrastructure
  - observability
category: concept
milestones:
  - Define Utilization, Saturation, and Errors for a resource
  - Apply USE to at least two resources (CPU and disk) for a running service
  - Know when to apply RED vs USE — services vs resources
  - Understand what "saturation" means and why it matters more than utilization alone
title_zh: "USE 方法"

---


When your application metrics look fine but the server feels slow, you're asking questions about infrastructure — and the USE method is how you answer them systematically. Coined by Brendan Gregg, USE stands for Utilization, Saturation, and Errors. For every resource in your system — CPU, memory, disk, network — you ask those three questions. The answers tell you whether a resource is the bottleneck and how close it is to failing.

The most important signal is saturation, and it's the most commonly overlooked. Utilization tells you how busy a resource is — a CPU at 80% is fairly loaded. But saturation tells you whether there's work piling up, waiting for that resource. A CPU at 80% with no run queue is handling load well. A CPU at 80% with a run queue of 10 means processes are queued and waiting — and your application is slower than it needs to be. High saturation means you've hit capacity even if utilization isn't at 100%.

The USE method is for resources, not services. For services (APIs, databases, microservices), you use the RED method — Rate, Errors, Duration. The two methods complement each other: RED alerts you that your service is slow, USE tells you why. If p99 latency is spiking and the CPU run queue is growing, you've found your bottleneck.

<!-- DEEP_DIVE -->

## The three signals

### Utilization: how busy is the resource?

Utilization is the percentage of time a resource is busy, or the percentage of capacity in use. It's the number most people already monitor — "CPU is at 70%", "disk is 85% full."

High utilization is worth watching but not inherently alarming. Resources can run at high utilization and still perform well, as long as there's no queuing (saturation). The problems start when utilization approaches 100% — at that point, any additional load causes queuing.

### Saturation: is there work queued and waiting?

Saturation measures whether requests for a resource are queuing up. This is the critical signal that utilization alone misses.

- **CPU saturation**: run queue length — how many processes are waiting for a CPU turn
- **Memory saturation**: swap usage — if the system is using swap, it's paging memory to disk, which is extremely slow
- **Disk saturation**: I/O queue depth — how many disk operations are waiting
- **Network saturation**: packet drops and interface errors — if the network buffer is full, packets get dropped

A resource at 60% utilization with a persistent queue is already saturated. You may need to add capacity or reduce load even though the utilization number looks fine.

### Errors: is the resource reporting errors?

Hardware errors, driver errors, ECC memory errors, disk read errors — things the OS and hardware report about the resource itself. These are different from application errors. A disk with a growing number of reallocated sectors is about to fail. A network card with a rising CRC error count has a hardware problem.

In practice, infrastructure errors are often detected late or not at all. Setting up monitoring for hardware-level errors (via SMART data, IPMI, or kernel logs) is a mark of mature infrastructure operations.

## Applying USE to common resources

### CPU

| Metric | Tool / Prometheus metric |
|--------|--------------------------|
| Utilization | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` |
| Saturation | `node_load1` (1-minute load average) or `node_schedstat_waiting_seconds_total` |
| Errors | Rare — CPU errors are hardware events, typically in kernel logs |

A CPU that's 80% utilized with a load average equal to the number of cores is fine. The same CPU with a load average 2x the core count is saturated — processes are queuing.

### Memory

| Metric | Tool / Prometheus metric |
|--------|--------------------------|
| Utilization | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` |
| Saturation | `node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes` (swap in use) |
| Errors | ECC memory errors (from `node_edac_*` metrics if available) |

Memory utilization near 100% is a warning. Memory saturation (active swap usage, especially increasing swap usage) is an emergency — disk is orders of magnitude slower than RAM, and swap usage causes severe application slowdowns.

### Disk I/O

| Metric | Tool / Prometheus metric |
|--------|--------------------------|
| Utilization | `rate(node_disk_io_time_seconds_total[5m])` — time the disk was busy |
| Saturation | `rate(node_disk_io_time_weighted_seconds_total[5m])` — I/O wait time |
| Errors | `rate(node_disk_read_errors_total[5m])`, `rate(node_disk_write_errors_total[5m])` |

A disk at 100% I/O utilization for extended periods indicates the disk is the bottleneck. SSDs typically handle saturation much better than spinning disks.

### Network

| Metric | Tool / Prometheus metric |
|--------|--------------------------|
| Utilization | `rate(node_network_transmit_bytes_total[5m])` vs interface capacity |
| Saturation | `rate(node_network_transmit_drop_total[5m])` — dropped packets |
| Errors | `rate(node_network_transmit_errs_total[5m])` |

Network saturation manifests as packet drops and increased retransmission at the TCP layer, which causes application-level latency spikes.

## How to collect USE metrics

You almost never instrument USE metrics in your application code. These come from the host — the operating system, kernel, and hardware. The standard tool for Prometheus is **node_exporter**:

```bash
# Run node_exporter on each host
docker run -d \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter \
  --path.rootfs=/host
```

node_exporter exposes hundreds of host-level metrics. A Prometheus scrape config to collect them:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']  # node_exporter default port
```

For Kubernetes environments, the Prometheus kube-state-metrics and metrics-server expose cluster-level resource metrics. Cloud environments have managed equivalents — CloudWatch, Cloud Monitoring, Azure Monitor — that collect host metrics without running your own exporter.

## USE in practice: diagnosing a slow service

Scenario: your API's p99 latency jumped from 120ms to 800ms an hour ago.

Using USE to diagnose:

1. **CPU utilization**: 78% (up from 45%) — elevated but not extreme
2. **CPU saturation** (load average): 12 on a 4-core host — 3x the core count. Processes are queuing for CPU time.
3. **Memory utilization**: 65% (normal)
4. **Memory saturation** (swap): 0 bytes (fine)
5. **Disk I/O**: low

Diagnosis: the CPU is saturated. Something caused a 3x increase in CPU load. The latency increase is caused by processes queuing for CPU time. Next step: profile which code is consuming the CPU.

This is the USE method doing its job — a systematic walk through resources that leads you to the bottleneck rather than guessing.

<!-- RESOURCES -->

- [The USE Method — Brendan Gregg](https://www.brendangregg.com/usemethod.html) -- type: article, time: 15m
- [Linux Performance — Brendan Gregg](https://www.brendangregg.com/linuxperf.html) -- type: article, time: 20m
- [node_exporter — Prometheus host metrics exporter](https://github.com/prometheus/node_exporter) -- type: article, time: 10m
- [Systems Performance: Enterprise and Cloud (Brendan Gregg)](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) -- type: book, time: 600m
- [RED Method vs USE Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
当应用指标看起来正常但服务器却感觉变慢时，你实际上是在追问基础设施层面的问题——而 USE 方法正是系统化回答这些问题的方式。USE 由 Brendan Gregg 提出，代表 Utilization（利用率）、Saturation（饱和度）和 Errors（错误）。对于系统中的每一种资源——CPU、内存、磁盘、网络——你都要问这三个问题。答案会告诉你某个资源是否是瓶颈，以及它距离失效还有多近。

最重要的信号是饱和度，而它也是最常被忽视的。利用率告诉你一个资源有多忙——CPU 达到 80% 说明负载已经相当高。但饱和度告诉你是否有工作正在堆积、等待该资源。CPU 达到 80% 且运行队列为空，说明它很好地承受了负载。CPU 达到 80% 且运行队列长度为 10，意味着进程在排队等待——你的应用因此比它本应有的速度更慢。高饱和度意味着即使利用率没到 100%，你也已经触及容量上限。

USE 方法针对的是资源，而不是服务。对于服务（API、数据库、微服务），你要用 RED 方法——Rate（速率）、Errors（错误）、Duration（时长）。这两种方法相辅相成：RED 提醒你服务变慢了，USE 告诉你原因。如果 p99 延迟飙升且 CPU 运行队列在增长，你就找到了瓶颈。

<!-- ZH_DEEP_DIVE -->
## 三个信号

### 利用率：资源有多忙？

利用率是资源处于忙碌状态的时间百分比，或者已使用容量所占的百分比。这是大多数人已经在监控的数字——“CPU 使用率 70%”、“磁盘已用 85%”。

高利用率值得关注，但本身并不必然意味着告警。资源可以在高利用率下运行且仍然表现良好，只要没有排队（饱和）。问题始于利用率接近 100% 时——此时任何额外的负载都会导致排队。

### 饱和度：是否有工作正在排队等待？

饱和度衡量对某个资源的请求是否正在排队。这是仅靠利用率会遗漏的关键信号。

- **CPU 饱和度**：运行队列长度——有多少进程正在等待 CPU 时间片
- **内存饱和度**：swap 使用量——如果系统正在使用 swap，说明它正在将内存分页到磁盘，这极其缓慢
- **磁盘饱和度**：I/O 队列深度——有多少磁盘操作正在等待
- **网络饱和度**：丢包和接口错误——如果网络缓冲区已满，数据包会被丢弃

一个利用率为 60% 但存在持续排队的资源，实际上已经饱和。即使利用率数字看起来正常，你可能也需要增加容量或减少负载。

### 错误：资源是否报告错误？

硬件错误、驱动错误、ECC 内存错误、磁盘读取错误——操作系统和硬件关于资源本身报告的问题。这些不同于应用错误。一块重分配扇区数不断增长的磁盘即将故障。一块 CRC 错误计数持续上升的网卡存在硬件问题。

在实践中，基础设施错误往往被发现得很晚，甚至根本未被发现。为硬件级错误设置监控（通过 SMART 数据、IPMI 或内核日志）是成熟基础设施运维的标志。

## 将 USE 应用于常见资源

### CPU

| 指标 | 工具 / Prometheus 指标 |
|--------|--------------------------|
| 利用率 | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` |
| 饱和度 | `node_load1`（1 分钟负载平均值）或 `node_schedstat_waiting_seconds_total` |
| 错误 | 罕见——CPU 错误属于硬件事件，通常出现在内核日志中 |

一个利用率为 80%、负载平均值等于核心数的 CPU 是正常的。同一个 CPU 如果负载平均值达到核心数的 2 倍，就已经饱和——进程正在排队。

### 内存

| 指标 | 工具 / Prometheus 指标 |
|--------|--------------------------|
| 利用率 | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` |
| 饱和度 | `node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes`（已使用的 swap） |
| 错误 | ECC 内存错误（来自 `node_edac_*` 指标，如果可用） |

内存利用率接近 100% 是一个警告。内存饱和（活跃的 swap 使用，尤其是 swap 使用量持续增长）则是紧急情况——磁盘比 RAM 慢几个数量级，swap 使用会导致应用严重变慢。

### 磁盘 I/O

| 指标 | 工具 / Prometheus 指标 |
|--------|--------------------------|
| 利用率 | `rate(node_disk_io_time_seconds_total[5m])`——磁盘处于忙碌状态的时间 |
| 饱和度 | `rate(node_disk_io_time_weighted_seconds_total[5m])`——I/O 等待时间 |
| 错误 | `rate(node_disk_read_errors_total[5m])`、`rate(node_disk_write_errors_total[5m])` |

磁盘长时间处于 100% I/O 利用率，表明磁盘是瓶颈。SSD 通常比机械硬盘能更好地应对饱和。

### 网络

| 指标 | 工具 / Prometheus 指标 |
|--------|--------------------------|
| 利用率 | `rate(node_network_transmit_bytes_total[5m])` 对比接口容量 |
| 饱和度 | `rate(node_network_transmit_drop_total[5m])`——丢弃的数据包 |
| 错误 | `rate(node_network_transmit_errs_total[5m])` |

网络饱和表现为丢包以及 TCP 层重传增加，这会导致应用层延迟飙升。

## 如何采集 USE 指标

你几乎从不在应用代码中埋点采集 USE 指标。这些指标来自主机——操作系统、内核和硬件。Prometheus 的标准工具是 **node_exporter**：

```bash
# Run node_exporter on each host
docker run -d \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter \
  --path.rootfs=/host
```

node_exporter 暴露数百个主机级指标。用于采集它们的 Prometheus 抓取配置：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']  # node_exporter default port
```

对于 Kubernetes 环境，Prometheus 的 kube-state-metrics 和 metrics-server 暴露集群级资源指标。云环境有对应的托管方案——CloudWatch、Cloud Monitoring、Azure Monitor——无需运行自己的 exporter 即可采集主机指标。

## USE 实践：诊断一个缓慢的服务

场景：你的 API 的 p99 延迟在一小时前从 120ms 跳升到了 800ms。

使用 USE 进行诊断：

1. **CPU 利用率**：78%（从 45% 上升）——偏高但不极端
2. **CPU 饱和度**（负载平均值）：4 核主机上为 12——是核心数的 3 倍。进程正在排队等待 CPU 时间。
3. **内存利用率**：65%（正常）
4. **内存饱和度**（swap）：0 字节（正常）
5. **磁盘 I/O**：低

诊断：CPU 已饱和。有某种原因导致 CPU 负载增加了 3 倍。延迟上升是由进程排队等待 CPU 时间造成的。下一步：分析哪些代码在消耗 CPU。

这就是 USE 方法在发挥作用——系统性地逐一检查资源，引导你找到瓶颈，而不是靠猜测。

<!-- ZH_RESOURCES -->
- [USE 方法 — Brendan Gregg](https://www.brendangregg.com/usemethod.html) -- 类型: 文章, 时间: 15m
- [Linux 性能 — Brendan Gregg](https://www.brendangregg.com/linuxperf.html) -- 类型: 文章, 时间: 20m
- [node_exporter — Prometheus 主机指标导出器](https://github.com/prometheus/node_exporter) -- 类型: 文章, 时间: 10m
- [系统性能：企业与云（Brendan Gregg）](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) -- 类型: 书籍, 时间: 600m
- [RED 方法与 USE 方法对比](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) -- 类型: 文章, 时间: 10m

<!-- ZH_UI -->
1. 为资源定义利用率、饱和度和错误
2. 对运行中的服务至少对两个资源（CPU 和磁盘）应用 USE
3. 知道何时应用 RED 与 USE——服务与资源
4. 理解“饱和度”的含义，以及为什么它比单看利用率更重要
5. 我现在知道 USE 是什么意思了。我该如何实际从基础设施中采集利用率、饱和度和错误指标？
6. USE 在理论上说得通，但我不知道如何获取这些数字。CPU 利用率是我在应用中埋点采集，还是由某个东西从主机上抓取？谁来采集磁盘饱和度？我不确定应用指标和基础设施指标之间的边界在哪里。
