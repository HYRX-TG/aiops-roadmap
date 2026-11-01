# ─────────────────────────────────────────────────────────────
# 真实事故回放数据集（L3 验证）
#
# 设计原则（针对"自己出题自己答"的循环性）：
#   1. 输入只包含**当时值班能观测到的东西**（告警/指标/日志/时间线），不含根因；
#   2. 每个事故的「决定性步骤」和「真实根因」**先从官方复盘原文提取并固定**，
#      跑之前写死在本文件里，不许事后改；
#   3. 症状里保留复盘里提到的**红鲱鱼**（当时的错误假设），不美化输入；
#   4. 来源全部是公开官方复盘（URL 附在上面），答案是第三方写的。
#
# 用法：python run_replay.py [--api http://127.0.0.1:8600]
# ─────────────────────────────────────────────────────────────

INCIDENTS = [
    {
        "id": "cloudflare-2019-waf-cpu",
        "name": "Cloudflare 2019-07-02 全球故障（WAF 正则回溯耗尽 CPU）",
        "source": "https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/",
        # ── 当时可见的输入（13:45-14:00 UTC 值班视角） ──
        "alert": {
            "source": "alertmanager",
            "alertname": "GlobalEdge502Spike",
            "title": "全网 502 错误率飙升 + HTTP 服务 CPU 饱和",
            "description": (
                "多个 PoP 报告处理 HTTP/HTTPS 流量的 CPU 核心使用率接近 100%；"
                "客户域名访问返回 502；全球流量下降约 80%；"
                "首批告警来自 WAF 合成功能测试失败（外部探针）。"
            ),
            "severity": "critical",
            "labels": {"env": "prod", "service": "edge-proxy", "scope": "global",
                       "team": "sre"},
        },
        "evidence": (
            "=== 告警时间线（UTC） ===\n"
            "13:42 防火墙团队通过自动流程部署了一条 XSS 检测 WAF 托管规则（生成变更单）\n"
            "13:45 合成测试告警：WAF 功能检查失败（数百个外部合成测试之一）\n"
            "13:45+ 大量端到端服务测试失败；全球流量下降告警；客户侧 502 刷屏\n"
            "13:50 全球各 PoP 报告 CPU 耗尽（HTTP/HTTPS 服务核心 ~100%）\n"
            "=== 指标 ===\n"
            "CPU（HTTP/HTTPS 服务核心）：全网络接近 100%（基线 <40%）\n"
            "全球流量：下降约 80%\n"
            "502 错误率：全域名普遍 5xx（前置 Web 服务器尚有余量 CPU，"
            "但够不到后端的 HTTP 服务进程）\n"
            "=== 日志 ===\n"
            "edge-proxy: upstream connect error / 502 generated at front line\n"
            "=== 当时的人为假设（红鲱鱼） ===\n"
            "值班初判：疑似前所未见的大规模攻击（DDoS）；也有人怀疑容量不足\n"
            "=== 影响面 ===\n"
            "Cloudflare 自己的 Dashboard / API / 状态页 / Jira 都走同一条边缘链路，"
            "同样不可用（控制面受损）"
        ),
        # ── 真实根因（官方复盘） ──
        "true_root_cause": (
            "13:42 部署的新 WAF 托管规则含灾难性回溯正则（.*(?:.*=.*)），"
            "在真实请求体上指数级回溯，耗尽所有 HTTP 服务核心 CPU；"
            "叠加因素：数周前的 WAF 重构移除了 CPU 过度使用保护、"
            "SOP 允许规则不经灰度直接全球推送、回滚需要完整重跑两次 WAF 构建、"
            "控制面与数据面同链路导致修复工具自身不可用。"
        ),
        # ── 决定性步骤（复盘里真正定位根因的动作，跑前固定） ──
        # generic=True 的步骤是"任何合格 runbook 都会有"的样板（看变更/时间线），
        # **不计入得分**——否则通用样板会被误记成"覆盖了事故特有步骤"。
        # generic=False 的才需要真正的领域推理，是本次实验真正的被测对象。
        "decisive_steps": [
            {"text": "按组件拆分 CPU 数据，定位到是 WAF 进程在吃 CPU（而不是泛泛的'CPU 高'）",
             "generic": False},
            {"text": "把 CPU 饱和起始时间与 13:42 的 WAF 规则部署做时间关联（变更关联）",
             "generic": False},
            {"text": "先查最近变更/发布，再怀疑攻击或容量（攻击假设是红鲱鱼）",
             "generic": True},
            {"text": "识别控制面与数据面同链路受损，需要带外通道/紧急开关（全局关闭 WAF）",
             "generic": False},
        ],
        # ── 结构化变更时间线（供 研判链"变化点定位层"消费，而非只躺在散文 evidence 里） ──
        "change_events": [
            {"ts": "13:42", "kind": "config", "actor": "防火墙团队",
             "target": "WAF 托管规则集", "detail": "经自动流程部署含灾难性回溯正则的 XSS 检测 WAF 托管规则（不经灰度全球推送）",
             "ticket": "生成变更单"},
        ],
    },
    {
        "id": "aws-s3-2017-capacity-removal",
        "name": "AWS S3 2017-02-28 us-east-1 故障（运维命令参数输错删错服务器）",
        "source": "https://aws.amazon.com/message/41926/",
        "alert": {
            "source": "cloud_monitor",
            "alertname": "S3ApiErrorRateCritical",
            "title": "S3 API 错误率激增（GET/LIST/PUT/DELETE 全失败）",
            "description": (
                "us-east-1 区域 S3 请求大面积失败，错误率与延迟同时抬升；"
                "依赖 S3 的 EC2 新实例启动、EBS（快照恢复）、Lambda、S3 控制台连带报错。"
            ),
            "severity": "critical",
            "labels": {"env": "prod", "service": "s3", "region": "us-east-1",
                       "namespace": "aws-s3"},
        },
        "evidence": (
            "=== 时间线（PST） ===\n"
            "09:37 一名获得授权的 S3 团队成员按既定 playbook 执行命令，"
            "本想下线计费子系统少量服务器；其中一个参数输错，实际下线了远多于预期的服务器\n"
            "09:40+ S3 开始无法服务请求（GET/LIST/PUT/DELETE 失败）\n"
            "12:26 index 子系统恢复部分容量，GET/LIST/DELETE 开始恢复\n"
            "13:18 index 完全恢复；13:54 placement 恢复，S3 恢复正常\n"
            "=== 指标 ===\n"
            "S3 API 错误率：全区域 5xx 激增；请求成功率骤降\n"
            "index/placement 子系统容量：被下线的服务器占比过大，触发完整重启\n"
            "=== 日志 ===\n"
            "s3: index subsystem restarting (metadata & location service)\n"
            "s3: placement subsystem restarting (storage allocation)\n"
            "=== 连带影响 ===\n"
            "S3 控制台、EC2 新实例启动、EBS（需从 S3 快照取数时）、Lambda 全部受累\n"
            "AWS 状态页自身依赖 S3，无法更新（只能发 Twitter）"
        ),
        "true_root_cause": (
            "运维人员调试计费子系统慢查询时，按 playbook 执行容量下线命令，"
            "一个参数输入错误导致下线了支撑 index（元数据/位置）与 placement（存储分配）"
            "两个基础子系统的大量服务器；两者需要完整重启，而该规模下这些子系统多年"
            "未被完整重启过，恢复链路未经受考验，重启+校验耗时约 4 小时。"
        ),
        "decisive_steps": [
            {"text": "先查最近一小时有没有运维操作/命令执行（谁在动容量），再怀疑容量或代码 bug",
             "generic": False},
            {"text": "区分是哪个子系统不可用（index=元数据/位置 vs placement=存储分配）以及容量是否低于下限",
             "generic": False},
            {"text": "评估恢复路径本身的耗时风险（从未完整重启过的子系统，RTO 是未知数）",
             "generic": False},
            {"text": "梳理依赖级联（S3 之外还有谁挂在上面：EBS/Lambda/EC2/控制台）",
             "generic": False},
        ],
        # ── 结构化运维操作审计（ops_audit）：S3 真因是"参数输错的容量下线命令" ──
        "ops_audit_events": [
            {"ts": "09:37", "operator": "S3 团队成员", "host": "s3(us-east-1)",
             "command": "按既定 playbook 执行容量下线命令（一个参数输错，实际下线了远多于预期的服务器）",
             "target": "计费子系统 / 大量 index+placement 服务器", "ticket": "既定 playbook（无变更单）",
             "result": "index/placement 子系统大量服务器被下线，触发完整重启（多年未经历，恢复链路未经验证）"},
        ],
    },
    {
        "id": "gitlab-2017-db-deletion",
        "name": "GitLab.com 2017-01-31 数据库事故（复制滞后 + 删错主机 + 备份全失效）",
        "source": "https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/",
        "alert": {
            "source": "business_log",
            "alertname": "DBReplicationLagCritical",
            "title": "数据库复制严重滞后并停止，主库写入锁死",
            "description": (
                "PostgreSQL 备库复制滞后持续扩大后完全停止；主库写入锁死导致站点部分不可用"
                "（无法发表 issue/MR 评论）；数据库负载异常升高。"
            ),
            "severity": "critical",
            "labels": {"env": "prod", "service": "postgresql", "team": "infra"},
        },
        "evidence": (
            "=== 时间线（UTC） ===\n"
            "17:20 工程师为搭建 pgpool-II 测试环境，手动对生产库做了 LVM 快照灌入 staging\n"
            "19:00 数据库负载升高（疑似垃圾信息；后查明部分来自一个被误排期的用户硬删除后台任务）\n"
            "23:00 备库复制滞后直至失败：主库上备库需要的 WAL 段已被回收（未开 WAL 归档）\n"
            "23:10 工程师清空备库数据目录并跑 pg_basebackup → 挂起无输出\n"
            "       报 max_wal_senders 不足（默认 3 → 调到 32）\n"
            "       调参后 PostgreSQL 拒绝启动：信号量过多（max_connections 8000 过高 → 调到 2000）\n"
            "23:27 工程师认为 pg_basebackup 因数据目录存在而挂起，决定删除该目录\n"
            "       ——执行在 db1.cluster（主库）上，而不是 db2（备库）；300GB 只剩 4.5GB\n"
            "=== 指标 ===\n"
            "复制滞后：持续扩大后彻底停止（约 4GB+）\n"
            "主库写入：锁死；数据库负载：持续高位\n"
            "=== 日志 ===\n"
            "postgres: WAL segments needed by standby already removed on primary\n"
            "postgres: could not connect: max_wal_senders too low\n"
            "postgres: refusing to start, too many semaphores\n"
            "=== 备份现状（复盘披露） ===\n"
            "LVM 快照默认 24 小时一次（17 小时前手动做过一次）；常规备份疑似未生效（文件仅几字节）；\n"
            "pg_dump 因 9.2/9.6 二进制混用而静默失败；S3 备份桶是空的；DB 服务器无磁盘快照\n"
            "五种备份/复制手段没有一种可靠"
        ),
        "true_root_cause": (
            "负载升高→备库复制滞后→WAL 段在主库被回收→人工重建备库过程中，"
            "一条删除数据目录的命令执行在了主库（db1）而不是备库（db2），"
            "300GB 生产数据几乎全毁；叠加五种备份/复制机制全部静默失效，"
            "最终只能恢复到 6 小时前的备份，丢失 17:20-00:00 的数据。"
        ),
        "decisive_steps": [
            {"text": "复制滞后先查 WAL 保留/归档：备库需要的段是否已被主库回收（没有 WAL 归档就必然断）",
             "generic": False},
            {"text": "任何对数据目录的破坏性操作前，先确认当前主机名/角色（主 or 备）——致命错误就是删错主机",
             "generic": False},
            {"text": "别信备份配置，验证备份真的能恢复（复盘里五种备份机制全部静默失效）",
             "generic": False},
            {"text": "回溯数小时内的人为操作（17:20 手动快照 + pgpool 实验）与负载突增的关联",
             "generic": True},
        ],
        # ── 结构化运维操作审计（ops_audit）：GitLab 真因是"删错主机的数据目录" ──
        "ops_audit_events": [
            {"ts": "17:20", "operator": "工程师", "host": "postgresql(主库)",
             "command": "为搭 pgpool-II 测试环境，手动对生产库做 LVM 快照灌入 staging",
             "target": "生产库", "ticket": "无", "result": "后续 staging 实验引入额外负载"},
            {"ts": "23:27", "operator": "工程师", "host": "db1.cluster（主库）",
             "command": "删除数据目录后跑 pg_basebackup（误把主库当备库）",
             "target": "db1.cluster 数据目录（主库）", "ticket": "无",
             "result": "300GB 生产数据几乎全毁，只剩 4.5GB"},
        ],
    },
    {
        "id": "meta-2021-bgp-dns",
        "name": "Meta 2021-10-04 全球故障（骨干命令误断 + DNS 自动撤回 BGP）",
        "source": "https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/",
        "alert": {
            "source": "alertmanager",
            "alertname": "GlobalDnsResolutionFailure",
            "title": "全球域名解析失败（SERVFAIL）+ 流量归零",
            "description": (
                "公共解析器对 facebook.com/instagram.com 等返回 SERVFAIL；"
                "外部观测到其 IP 前缀的 BGP 路由被撤回；访问流量趋近于零；"
                "内部依赖 DNS 的工具与远程管理通道同时不可用。"
            ),
            "severity": "critical",
            "labels": {"env": "prod", "service": "dns", "scope": "global"},
        },
        "evidence": (
            "=== 时间线（UTC） ===\n"
            "15:39 例行维护中执行了一条本意为评估全球骨干容量的命令，"
            "        实际断开了骨干网全部连接（审计工具有 bug，没能拦住）\n"
            "15:39+ 数据中心之间、数据中心与互联网之间完全断开\n"
            "        小型机房的权威 DNS 服务器按设计在连不上数据中心时撤回自己的 BGP 广播\n"
            "        → 所有 DNS 服务器同时自认不健康并撤回路由 → 全球无法解析域名\n"
            "15:50 主要公共解析器缓存全部过期\n"
            "21:50 BGP 恢复广播；22:05 DNS 恢复解析；22:50 服务基本恢复\n"
            "=== 外部观测 ===\n"
            "BGP 路由表：Facebook 前缀被大量撤回（Cloudflare 等第三方均观测到）\n"
            "DNS：SERVFAIL（不是超时——是权威服务器不可达）\n"
            "流量：到 Facebook IP 的流量断崖式下跌\n"
            "=== 内部影响 ===\n"
            "远程/带外管理通道不可用；大量内部工具依赖同一套 DNS/网络而失效；\n"
            "工程师只能进机房，而高等级物理安全又拖慢了进入速度\n"
            "=== 红鲱鱼 ===\n"
            "服务进程本身一直在运行——问题不是'服务器挂了'，而是'找不到服务器了'"
        ),
        "true_root_cause": (
            "一条评估骨干容量的维护命令误将骨干网全部连接断开（审计工具 bug 未拦截）；"
            "数据中心孤立后，DNS 服务器按安全设计撤回 BGP 广播（本该屏蔽单点不健康，"
            "却因全部同时触发而放大为全局不可达）；恢复受阻于内部工具与带外通道"
            "同样依赖已故障的网络/DNS。"
        ),
        "decisive_steps": [
            {"text": "先分层定位：解析失败（DNS 层）vs 路由不可达（BGP 层）vs 应用错误——本例是名字根本解析不了",
             "generic": False},
            {"text": "从外部视角检查自己前缀的 BGP 广播是否被撤回（不只看内部监控）",
             "generic": False},
            {"text": "把故障起始时间与维护窗口的命令/变更关联（骨干维护命令）",
             "generic": True},
            {"text": "识别恢复路径自身受损：内部工具与带外访问依赖同一套已故障的系统，需要带外/物理通道",
             "generic": False},
            {"text": "识别'保护机制'变成了放大器：DNS 不健康即撤回路由的设计在全部同时触发时适得其反",
             "generic": False},
        ],
        # ── 结构化运维操作审计（ops_audit）+ 维护变更：Meta 真因是"维护命令误断骨干" ──
        "ops_audit_events": [
            {"ts": "15:39", "operator": "维护人员", "host": "骨干网",
             "command": "例行维护中执行评估全球骨干容量的命令（实际断开了骨干网全部连接）",
             "target": "骨干网全部连接", "ticket": "例行维护（无变更单）",
             "result": "数据中心之间、数据中心与互联网之间完全断开；DNS 自动撤回 BGP 放大为全局不可达"},
        ],
        "change_events": [
            {"ts": "15:39", "kind": "maintenance", "actor": "维护团队", "target": "骨干网",
             "detail": "例行维护执行骨干容量评估命令（审计工具有 bug 未拦截，实际断开骨干）", "ticket": "例行维护"},
        ],
    },
]

# ── 评分规则（跑前固定，3/2/1/0） ──────────────────────────────
# 3 = 排查链覆盖 ≥2 条决定性步骤，且最终结论方向正确
# 2 = 覆盖 1 条决定性步骤，或方向部分沾边
# 1 = 有排查动作但全部偏离
# 0 = 误导（把注意力引向错误方向）
RUBRIC = (
    "3=链覆盖≥2条决定性步骤且结论方向正确；2=覆盖1条或方向沾边；"
    "1=有动作但偏离；0=误导。决定性步骤从官方复盘原文预先提取并固定在本文件中。"
)
