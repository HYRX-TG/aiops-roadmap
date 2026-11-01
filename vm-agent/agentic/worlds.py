"""三个真实事故的"世界"（模型只能通过工具访问）。

设计纪律（比 harness 更重要）：
  1. symptom 只写"当时值班看到的表面现象"，**不写任何根因线索**。
  2. 世界里的证据是**当时的真实事实**，但要混入噪声：
     - 无关服务的正常变更
     - 正常的指标波动
     - 别的团队的操作记录
     模型必须自己判断哪些相关。
  3. 有些关键证据**故意不显眼**（比如 43 秒的维护窗口只在 ops_audit 里出现一次），
     模型不主动去查就永远看不到。
  4. 不告诉模型这是哪个事故、涉及哪家公司、答案是什么。

三个世界对应三类"真正的排查难点"：
  W1 跨层归因：表象在下游（源站被打爆），根因在上游（配置校验 bug）
  W2 时间关联：故障在数据库层，但根因是 43 秒前的一次网络维护
  W3 误操作识别：服务挂了这个表象，真因是一条参数写错的运维命令
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import World  # noqa: E402


# ══════════════════════════════════════════════════════════════
# W1：CDN 边缘 503 —— 表象是源站被打爆，真因是配置校验 bug
# ══════════════════════════════════════════════════════════════
W1 = World(
    name="edge-cdn-503",
    symptom="全球多个站点同时返回 503，约 85% 的网络在返回错误，持续约 1 小时。"
            "源站侧看到请求量暴涨（客户重试）。最初怀疑是大规模攻击或容量不足。",
    service="edge-cdn",
    truth="数周前的一次软件部署引入了未发现的 bug（新增的配置校验逻辑）。"
          "今天一个客户推送了完全合法的配置变更，恰好命中该 bug 的触发条件，"
          "导致全网的边缘节点同时拒绝服务。放大因素：校验逻辑同步下发到所有节点（无灰度）、"
          "校验失败就直接停服务（没有回退到上一个好配置的路径）。",
    decisive=[
        "先分清 503 是哪一层产生的（CDN 边缘层 vs 源站），而不是被源站被打爆的表象带偏",
        "把故障起点与近期的软件版本部署 + 客户侧配置变更做关联",
        "识别客户配置是合法的：它只是触发器，根因在平台自己的代码里",
        "识别影响面是全局的：同一套校验逻辑同步下发，无灰度、无回退路径",
    ],
    changes=[
        # 关键证据：数周前的部署（不在"最近 1 小时"，必须扩大窗口才看得到）
        {"ts": "2021-05-12 03:00", "kind": "deploy", "actor": "platform-team",
         "target": "edge-cdn 节点软件", "detail": "发布 v7.2，新增配置校验逻辑（VCL 校验器）",
         "ticket": "CHG-8841"},
        # 关键证据：客户配置变更（时间与故障起点吻合）
        {"ts": "2021-06-08 09:44", "kind": "config", "actor": "customer-acme",
         "target": "edge-cdn 客户配置 acme.com", "detail": "客户自助推送配置更新（语法校验通过）",
         "ticket": ""},
        # 噪声：无关服务
        {"ts": "2021-06-08 08:10", "kind": "deploy", "actor": "billing-team",
         "target": "billing-api", "detail": "发布 v2.4.1 修复对账精度", "ticket": "CHG-9022"},
        # 噪声：常规维护
        {"ts": "2021-06-07 23:00", "kind": "maintenance", "actor": "net-ops",
         "target": "边缘机房 ups 电池巡检", "detail": "例行巡检，无业务影响", "ticket": "OPS-771"},
    ],
    ops_audit=[
        # 噪声：别人的正常操作
        {"ts": "2021-06-08 07:30", "operator": "alice", "host": "db-primary-01",
         "command": "pg_basebackup -D /backup", "target": "backup", "result": "success",
         "change_ticket": "CHG-9001"},
        # 关键：平台团队回滚（故障中段）
        {"ts": "2021-06-08 10:27", "operator": "bob", "host": "edge-control-01",
         "command": "disable config-validator --global", "target": "edge-cdn",
         "result": "success", "change_ticket": "INC-0608"},
    ],
    metrics={
        ("edge-cdn", "http_5xx_ratio"): [("09:40", 0.002), ("09:45", 0.41),
                                          ("09:47", 0.85), ("09:50", 0.86),
                                          ("10:00", 0.85), ("10:30", 0.12),
                                          ("10:36", 0.01)],
        ("edge-cdn", "cpu_usage_pct"): [("09:40", 38), ("09:47", 41), ("09:50", 43),
                                         ("10:00", 44), ("10:30", 39)],
        ("edge-cdn", "edge_latency_p99_ms"): [("09:40", 22), ("09:47", 24),
                                                ("09:50", 25), ("10:00", 24)],
        ("origin-web", "inbound_rps"): [("09:40", 1200), ("09:47", 8800),
                                         ("09:50", 9100), ("10:00", 8900),
                                         ("10:30", 2100), ("10:36", 1250)],
        ("origin-web", "cpu_usage_pct"): [("09:40", 44), ("09:47", 92), ("09:50", 95),
                                           ("10:00", 93), ("10:30", 51), ("10:36", 46)],
        ("billing-api", "http_5xx_ratio"): [("09:40", 0.001), ("09:47", 0.001),
                                             ("09:50", 0.002), ("10:00", 0.001)],
    },
    logs={
        "edge-cdn": [
            ("09:44:51", "INFO", "config validator: validating customer config acme.com"),
            ("09:44:52", "ERROR", "config validation failed: unexpected state, aborting service"),
            ("09:44:52", "ERROR", "worker exiting: validation error (no fallback configured)"),
            ("09:45:01", "ERROR", "vcl compile error path triggered, refusing requests"),
            ("09:46:00", "ERROR", "worker exiting: validation error (no fallback configured)"),
            ("10:27:10", "INFO", "config validator disabled by operator bob (INC-0608)"),
            ("10:36:20", "INFO", "workers healthy, resuming traffic"),
        ],
        "origin-web": [
            ("09:47:00", "WARN", "inbound request rate 7x normal, clients retrying"),
            ("09:48:00", "WARN", "connection pool near limit"),
            ("09:50:00", "WARN", "inbound request rate still elevated"),
        ],
        "billing-api": [
            ("08:15:00", "INFO", "started v2.4.1"),
            ("09:40:00", "INFO", "reconciliation completed"),
        ],
    },
    topology={
        "edge-cdn": {"upstream": ["customer-config-store", "config-validator"],
                     "downstream": ["origin-web", "origin-api"]},
        "origin-web": {"upstream": ["edge-cdn"], "downstream": ["db-primary-01"]},
        "billing-api": {"upstream": [], "downstream": ["db-primary-01"]},
        "db-primary-01": {"upstream": ["origin-web", "billing-api"], "downstream": []},
    },
    resources={
        ("deployment", "edge-cdn"): {
            "image": "edge:v7.2", "replicas": "412 (global)",
            "recent_changes": "image updated 27d ago (v7.1 -> v7.2)",
            "note": "v7.2 引入 config-validator 组件"},
        ("deployment", "origin-web"): {"image": "origin:4.8", "replicas": 24,
                                        "note": "healthy, high load from retries"},
    },
)


# ══════════════════════════════════════════════════════════════
# W2：数据库脑裂 —— 表象是 DB 异常，真因是 43 秒网络分区
# ══════════════════════════════════════════════════════════════
W2 = World(
    name="mysql-splitbrain",
    symptom="站点大面积报错，用户看到数据前后不一致。Orchestrator 显示的复制拓扑里"
            "只剩西海岸机房的服务器。webhook 与页面构建大量积压。",
    service="mysql-cluster",
    truth="例行维护更换光模块时，东西海岸骨干断连 43 秒。Orchestrator 把这 43 秒的失联"
          "判定为主库故障，跨区把西海岸副本提升为主库。网络恢复后两个机房各自接受了"
          "对方没有的写入（事实上的双主/脑裂），无法安全切回。"
          "放大因素：自动故障切换策略本身成了放大器；跨大陆 60ms 延迟让东海岸应用不可用。",
    decisive=[
        "把数据库异常与刚刚发生的网络维护（43 秒断连）关联起来，而不是当成数据库自身故障",
        "识别出现了双主/脑裂：两岸各自接受了对方没有的写入",
        "识别自动故障切换策略本身成了放大器（Orchestrator 跨区提升主库）",
        "明确数据完整性优先于可用性，并识别恢复路径自身耗时",
    ],
    changes=[
        # 关键证据：43 秒网络维护（这一条是全案钥匙，但藏在变更记录里）
        {"ts": "2018-10-21 22:52", "kind": "maintenance", "actor": "network-team",
         "target": "east-west 骨干光模块", "detail": "更换故障 100G 光模块（计划内，预计丢包数秒）",
         "ticket": "CHG-4417"},
        # 噪声
        {"ts": "2018-10-21 19:00", "kind": "deploy", "actor": "web-team",
         "target": "web-frontend", "detail": "发布 v9.1 样式修复", "ticket": "CHG-4402"},
        {"ts": "2018-10-20 14:00", "kind": "config", "actor": "search-team",
         "target": "search-index", "detail": "调整分片数", "ticket": "CHG-4390"},
    ],
    ops_audit=[
        # 关键：维护操作（时间紧贴故障）
        {"ts": "2018-10-21 22:51", "operator": "net-ops-oncall", "host": "east-core-sw-01",
         "command": "replace optic module 100G port 4/1", "target": "east-west 骨干",
         "result": "completed, link flapped 43s", "change_ticket": "CHG-4417"},
        # 噪声
        {"ts": "2018-10-21 18:20", "operator": "carol", "host": "mysql-replica-w2",
         "command": "mysqladmin status", "target": "mysql", "result": "success",
         "change_ticket": ""},
    ],
    metrics={
        ("mysql-cluster", "replication_lag_sec"): [("22:50", 0.2), ("22:52", 0.3),
                                                    ("22:53", 140), ("23:00", 3200),
                                                    ("23:10", 8800), ("06:00", 24000)],
        ("mysql-cluster", "writes_east_per_sec"): [("22:50", 8200), ("22:52", 0),
                                                     ("22:53", 0), ("23:07", 0),
                                                     ("23:20", 0)],
        ("mysql-cluster", "writes_west_per_sec"): [("22:50", 7900), ("22:52", 0),
                                                     ("22:53", 8100), ("23:07", 8300),
                                                     ("23:20", 8400)],
        ("mysql-cluster", "inconsistent_read_errors"): [("22:50", 0), ("22:53", 3),
                                                         ("23:00", 41), ("23:10", 120)],
        ("web-frontend", "http_5xx_ratio"): [("22:50", 0.001), ("22:53", 0.22),
                                              ("23:00", 0.31), ("23:10", 0.28)],
    },
    logs={
        "mysql-cluster": [
            ("22:52:00", "INFO", "orchestrator: primary east-01 unreachable, beginning failover"),
            ("22:52:31", "WARN", "orchestrator: dead master detection timeout (30s) exceeded"),
            ("22:52:43", "INFO", "network restored: east core link up"),
            ("22:52:44", "ERROR", "orchestrator: promoting replica west-02 to primary (cross-region)"),
            ("22:53:00", "ERROR", "two primaries detected: east-01 (read-write), west-02 (read-write)"),
            ("22:53:01", "ERROR", "replication broken: both regions accepted independent writes"),
            ("23:19:00", "INFO", "pausing webhook delivery and page builds to preserve data integrity"),
        ],
        "web-frontend": [
            ("22:53:00", "ERROR", "upstream db returned inconsistent snapshot"),
            ("23:00:00", "ERROR", "read/write routing errors spike"),
        ],
    },
    topology={
        "web-frontend": {"upstream": ["mysql-cluster"], "downstream": []},
        "mysql-cluster": {"upstream": ["east-core-sw-01"], "downstream": ["east-01", "west-02"]},
        "east-01": {"upstream": ["mysql-cluster", "east-core-sw-01"], "downstream": []},
        "west-02": {"upstream": ["mysql-cluster"], "downstream": []},
    },
    resources={
        ("pod", "east-01"): {"role": "primary (east)", "status": "Running",
                              "note": "was primary before 22:52; network isolated 43s"},
        ("pod", "west-02"): {"role": "promoted primary (west)", "status": "Running",
                              "note": "promoted by orchestrator at 22:52:44 (cross-region failover)"},
        ("statefulset", "mysql-cluster"): {"replicas": 6,
                                            "note": "orchestrator cross-region promotion policy enabled"},
    },
)


# ══════════════════════════════════════════════════════════════
# W3：误操作删容量 —— 表象是子系统不可用，真因是一条参数写错的命令
# ══════════════════════════════════════════════════════════════
W3 = World(
    name="S3-capacity-removal",
    symptom="对象存储的写入与索引查询大面积失败，大量依赖它的上层服务（计算、块存储、"
            "监控）同时报错。控制台操作也变慢。",
    service="object-storage",
    truth="一名授权运维按既定 playbook 下线计费子系统的部分服务器，命令里的一个参数"
          "（要移除的容量/服务器数量）输错，实际移除了远超预期的服务器——"
          "包括 index（元数据/位置服务）和 placement 子系统所需的容量。"
          "这两个子系统已多年未整体重启，重启耗时远超预期。",
    decisive=[
        "先查最近一小时有没有运维操作/命令执行（谁在动容量）",
        "区分是哪个子系统不可用（index 元数据 vs placement 存储分配 vs 其他）",
        "评估恢复路径本身的耗时风险（从未完整重启过的子系统）",
        "梳理依赖级联（对象存储之外还有谁挂在上面）",
    ],
    changes=[
        {"ts": "2017-02-28 12:40", "kind": "config", "actor": "capacity-team",
         "target": "billing-subsystem", "detail": "计划下线 billing 部分服务器（容量回收）",
         "ticket": "CHG-1102"},
        # 噪声
        {"ts": "2017-02-28 09:00", "kind": "deploy", "actor": "console-team",
         "target": "console-ui", "detail": "发布 v4.2", "ticket": "CHG-1098"},
    ],
    ops_audit=[
        # 关键：那条参数写错的命令
        {"ts": "2017-02-28 12:37", "operator": "dave", "host": "capacity-cli-01",
         "command": "remove-capacity --playbook billing --min-available 40 --count 2",
         "target": "index,placement subsystems", "result": "removed far more than intended",
         "change_ticket": "CHG-1102"},
        # 噪声：正常操作
        {"ts": "2017-02-28 11:00", "operator": "erin", "host": "billing-app-03",
         "command": "systemctl status billing",
         "target": "billing", "result": "active", "change_ticket": ""},
    ],
    metrics={
        ("object-storage", "write_success_ratio"): [("12:35", 0.999), ("12:38", 0.62),
                                                      ("12:40", 0.11), ("12:45", 0.08),
                                                      ("13:30", 0.09)],
        ("object-storage", "read_success_ratio"): [("12:35", 0.999), ("12:38", 0.71),
                                                     ("12:40", 0.22), ("12:45", 0.19)],
        ("object-storage", "index_service_available"): [("12:35", 1), ("12:38", 0),
                                                          ("12:40", 0), ("12:45", 0)],
        ("object-storage", "placement_service_available"): [("12:35", 1), ("12:38", 0),
                                                              ("12:40", 0)],
        ("billing-subsystem", "cpu_usage_pct"): [("12:35", 31), ("12:38", 12), ("12:40", 4)],
        ("compute-service", "api_error_ratio"): [("12:35", 0.001), ("12:38", 0.44),
                                                  ("12:40", 0.71)],
        ("block-storage", "api_error_ratio"): [("12:35", 0.001), ("12:38", 0.38),
                                                ("12:40", 0.66)],
    },
    logs={
        "object-storage": [
            ("12:37:58", "ERROR", "index service: unresponsive after capacity removal"),
            ("12:38:00", "ERROR", "placement service: insufficient capacity to allocate partitions"),
            ("12:38:01", "ERROR", "write path: cannot locate partition metadata"),
            ("12:40:00", "ERROR", "index and placement both unavailable"),
            ("12:41:00", "WARN", "these subsystems have not been fully restarted since launch"),
        ],
        "billing-subsystem": [
            ("12:36:00", "INFO", "capacity removal initiated by dave (CHG-1102)"),
            ("12:38:00", "WARN", "removed nodes exceed planned count"),
        ],
        "compute-service": [
            ("12:39:00", "ERROR", "dependency object-storage failing"),
        ],
    },
    topology={
        "object-storage": {"upstream": [], "downstream": ["index-service", "placement-service"]},
        "index-service": {"upstream": ["object-storage"], "downstream": ["metadata-store"]},
        "placement-service": {"upstream": ["object-storage"], "downstream": ["availability-zones"]},
        "compute-service": {"upstream": ["object-storage"], "downstream": []},
        "block-storage": {"upstream": ["object-storage"], "downstream": []},
        "monitoring": {"upstream": ["object-storage"], "downstream": []},
    },
    resources={
        ("statefulset", "index-service"): {"replicas_expected": 12, "replicas_actual": 0,
                                            "note": "capacity removed; has never been cold-started"},
        ("statefulset", "placement-service"): {"replicas_expected": 8, "replicas_actual": 0,
                                                "note": "capacity removed"},
        ("deployment", "billing-subsystem"): {"replicas_expected": 30, "replicas_actual": 4,
                                               "note": "intended target of capacity removal"},
    },
)

# ══════════════════════════════════════════════════════════════
# W4：反记忆测试 —— 虚构事故，绝不可能出现在训练数据里
# ══════════════════════════════════════════════════════════════
# 为什么需要这个：前三个世界都是公开的著名事故（Fastly / GitHub / S3），
# 大模型很可能在预训练里见过复盘原文——那测出来的是"记忆"不是"排查"。
# 这一组用一个**完全虚构**的场景：如果模型在这里也能查出根因，
# 说明它真的在用工具取证 + 推理，而不是在回忆。
W4 = World(
    name="zephyr-quota-cascade",       # 虚构服务名，训练数据里不存在
    symptom="订单履约服务的异步任务队列持续积压，履约延迟从 2 分钟涨到 40 分钟以上。"
            "上游下单接口成功率下降到 71%。相关团队说他们没做任何发布。",
    service="fulfill-worker",
    truth="合作伙伴的接入网关在 14:05 推送了一次「限流配额调整」（把每秒允许的请求"
          "从 500 提到 5000，是他们自己的促销预案）。这次调整经过了三层网关，"
          "但第二层网关的配额缓存 TTL 是 30 分钟，导致两层网关看到的配额不一致："
          "外层的 5000 与内层的 500 冲突，内层把超出 500 的部分静默排队而不是拒绝，"
          "队列因此无界增长，最终把 worker 的内存打满并触发 GC 风暴。"
          "根因是「两层网关的配额缓存 TTL 不一致」，不是配额本身。",
    decisive=[
        "发现积压的起点与合作伙伴的配额调整时间吻合（14:05）",
        "识别出这不是我方发布引起的（排除我方的发布/变更）",
        "发现两层网关的配额值不一致（外层 5000 / 内层 500）",
        "识别出静默排队（而非拒绝）是无界增长的机制，以及缓存 TTL 差异是根因",
    ],
    changes=[
        # 关键：合作伙伴的配额变更（不是我们的变更）
        {"ts": "2026-09-14 14:05", "kind": "config", "actor": "partner-acme-gateway",
         "target": "partner 接入网关配额", "detail": "合作伙伴推送促销预案：QPS 配额 500 -> 5000",
         "ticket": "EXT-2201"},
        # 关键但隐蔽：我方网关的缓存配置（TTL 30 分钟）
        {"ts": "2026-08-02 10:00", "kind": "config", "actor": "platform-team",
         "target": "ingress-gateway-l2 quota-cache", "detail": "配额缓存 TTL = 1800s（当时为了降低 Redis 压力）",
         "ticket": "CHG-3310"},
        # 噪声
        {"ts": "2026-09-14 11:00", "kind": "deploy", "actor": "search-team",
         "target": "search-api", "detail": "发布 v3.1 排序微调", "ticket": "CHG-3390"},
        {"ts": "2026-09-13 16:00", "kind": "maintenance", "actor": "dba",
         "target": "mysql-reporting", "detail": "报表库索引重建（只读库）", "ticket": "OPS-118"},
    ],
    ops_audit=[
        {"ts": "2026-09-14 13:40", "operator": "frank", "host": "ingress-gw-l2-03",
         "command": "redis-cli ttl quota:partner-acme", "target": "quota-cache",
         "result": "1560", "change_ticket": ""},
        {"ts": "2026-09-14 14:20", "operator": "grace", "host": "fulfill-worker-07",
         "command": "jstack <pid> | grep -c GC", "target": "fulfill-worker",
         "result": "GC threads 41 (abnormal)", "change_ticket": ""},
        # 噪声
        {"ts": "2026-09-14 10:00", "operator": "henry", "host": "search-api-01",
         "command": "systemctl status search-api", "target": "search-api",
         "result": "active", "change_ticket": ""},
    ],
    metrics={
        ("fulfill-worker", "queue_depth"): [("13:50", 120), ("14:00", 130),
                                              ("14:06", 2100), ("14:10", 18000),
                                              ("14:20", 96000), ("14:30", 210000)],
        ("fulfill-worker", "latency_p99_min"): [("13:50", 2.1), ("14:06", 3.8),
                                                  ("14:10", 9.2), ("14:20", 26.0),
                                                  ("14:30", 41.0)],
        ("fulfill-worker", "jvm_gc_time_pct"): [("13:50", 3), ("14:06", 5),
                                                  ("14:10", 18), ("14:20", 62),
                                                  ("14:30", 88)],
        ("fulfill-worker", "heap_used_pct"): [("13:50", 42), ("14:06", 51),
                                                ("14:10", 74), ("14:20", 96),
                                                ("14:30", 99)],
        ("ingress-gateway-l1", "quota_limit_effective"): [("13:50", 500), ("14:05", 5000),
                                                            ("14:10", 5000), ("14:30", 5000)],
        ("ingress-gateway-l2", "quota_limit_effective"): [("13:50", 500), ("14:05", 500),
                                                            ("14:10", 500), ("14:20", 500),
                                                            ("14:35", 5000)],
        ("ingress-gateway-l2", "requests_over_quota_silently_queued"): [("14:04", 0),
                                                                          ("14:06", 1800),
                                                                          ("14:10", 16000),
                                                                          ("14:20", 94000)],
        ("order-api", "success_ratio"): [("13:50", 0.998), ("14:06", 0.96),
                                           ("14:10", 0.82), ("14:20", 0.72),
                                           ("14:30", 0.71)],
    },
    logs={
        "ingress-gateway-l1": [
            ("14:05:02", "INFO", "quota config updated by partner-acme-gateway: 500 -> 5000"),
            ("14:05:03", "INFO", "quota cache reloaded immediately (l1 ttl=0)"),
            ("14:10:00", "WARN", "inbound rate 4800/s exceeds l2 advertised quota 500"),
        ],
        "ingress-gateway-l2": [
            ("14:05:03", "INFO", "quota update received, but cached value valid for 1800s"),
            ("14:05:04", "DEBUG", "serving cached quota=500 (ttl remaining 1799s)"),
            ("14:06:00", "WARN", "requests exceeding quota 500 are being queued (not rejected)"),
            ("14:10:00", "WARN", "internal queue depth 16000, growing"),
            ("14:35:00", "INFO", "quota cache expired, reloaded quota=5000 (finally consistent)"),
        ],
        "fulfill-worker": [
            ("14:07:00", "WARN", "consume lag increasing: 2100"),
            ("14:10:00", "WARN", "consume lag 18000, worker falling behind"),
            ("14:20:00", "ERROR", "Full GC pause 4.2s, heap 96%"),
            ("14:30:00", "ERROR", "repeated Full GC, throughput collapsed"),
        ],
        "order-api": [
            ("14:10:00", "ERROR", "fulfillment enqueue timeout after 30s"),
            ("14:20:00", "ERROR", "order success rate dropped to 72%"),
        ],
    },
    topology={
        "order-api": {"upstream": ["ingress-gateway-l1"], "downstream": ["fulfill-worker"]},
        "ingress-gateway-l1": {"upstream": ["partner-acme-gateway"], "downstream": ["ingress-gateway-l2"]},
        "ingress-gateway-l2": {"upstream": ["ingress-gateway-l1"], "downstream": ["fulfill-worker"]},
        "fulfill-worker": {"upstream": ["ingress-gateway-l2"], "downstream": ["fulfill-db"]},
    },
    resources={
        ("deployment", "ingress-gateway-l2"): {
            "replicas": 6,
            "quota_cache": "Redis, ttl=1800s",
            "note": "quota cache ttl set 2026-08-02 to reduce Redis load (CHG-3310)"},
        ("deployment", "ingress-gateway-l1"): {
            "replicas": 3, "quota_cache": "in-process, ttl=0 (always fresh)"},
        ("deployment", "fulfill-worker"): {
            "replicas": 12, "limit": "heap 2Gi",
            "note": "queue consumer; no backpressure limit configured"},
    },
)

WORLDS = [W1, W2, W3, W4]
