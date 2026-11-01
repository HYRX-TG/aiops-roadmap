# -*- coding: utf-8 -*-
"""真实事故知识库内容（供 RAGFlow 建库 + 本地留存）。

6 个公开官方复盘事故，整理成"诊断时召回即可直接复用的处置知识"。
每个事故包含：症状 / 真实根因 / 决定性排查步骤 / 关联变更或运维操作 / 止血处置 / 经验雷点。

数据来源（第三方公开复盘，答案非本项目编写）：
  - Cloudflare 2019-07-02  https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
  - AWS S3 2017-02-28      https://aws.amazon.com/message/41926/
  - GitLab 2017-01-31      https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/
  - Meta 2021-10-04        https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/
  - Fastly 2021-06-08      https://www.fastly.com/blog/summary-of-june-8-outage
  - GitHub 2018-10-21      https://github.blog/2018-10-30-oct21-post-incident-analysis
"""

INCIDENTS = [
    {
        "doc_id": "cloudflare-2019-waf-cpu",
        "title": "Cloudflare 2019-07-02 全球故障：WAF 正则灾难性回溯耗尽边缘 CPU",
        "service": "edge-proxy（全球边缘代理/WAF）",
        "scope": "global",
        "source": "https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/",
        "symptoms": [
            "13:45 起全网 502 错误率飙升，客户域名访问返回 502，全球流量下降约 80%",
            "多个 PoP 的 HTTP/HTTPS 服务 CPU 核心接近 100%（基线 <40%）",
            "首批告警来自 WAF 合成功能测试失败（外部探针），不是用户报障",
            "Cloudflare 自己的 Dashboard/API/状态页/Jira 都走同一条边缘链路，同样不可用（控制面受损）",
        ],
        "red_herrings": [
            "值班初判疑似前所未见的大规模攻击（DDoS）或容量不足——均为红鲱鱼",
        ],
        "root_cause": (
            "13:42 防火墙团队通过自动流程部署了一条新的 WAF 托管规则，其中含灾难性回溯正则"
            "（形如 .*(?:.*=.*)），在真实请求体上指数级回溯，耗尽所有 HTTP 服务核心 CPU。"
            "叠加因素：数周前的 WAF 重构移除了 CPU 过度使用保护；SOP 允许规则不经灰度直接全球推送；"
            "回滚需要完整重跑两次 WAF 构建；控制面与数据面同链路导致修复工具自身不可用。"
        ),
        "decisive_steps": [
            ("按组件拆分 CPU 数据，定位到是 WAF 进程在吃 CPU，而不是泛泛的'CPU 高'", False),
            ("把 CPU 饱和起始时间与 13:42 的 WAF 规则部署做时间关联（变更关联）", False),
            ("识别控制面与数据面同链路受损，需要带外通道/紧急开关（全局关闭 WAF）", False),
            ("先查最近变更/发布，再怀疑攻击或容量（攻击假设是红鲱鱼）", True),
        ],
        "related_changes": [
            "13:42 防火墙团队经自动流程部署含灾难性回溯正则的 XSS 检测 WAF 托管规则（不经灰度全球推送）",
        ],
        "mitigation": (
            "止血：全局紧急关闭 WAF 托管规则（带外/紧急开关，因控制面同链路受损需绕行）。"
            "根因修复：修正正则、恢复 CPU 保护、规则改为灰度推送、修复工具解耦控制面。"
            "动作分级：全局关 WAF 属高风险（影响安全防护），需 SRE on-call 审批。"
        ),
        "lessons": [
            "正则/规则类变更要做回溯复杂度审查，宁可慢不可全球直推",
            "控制面与数据面必须解耦，否则修复工具会在事故中自残",
            "看到 CPU 100% 先按组件拆，别停在'CPU 高'这一层",
        ],
    },
    {
        "doc_id": "aws-s3-2017-capacity-removal",
        "title": "AWS S3 2017-02-28 us-east-1 故障：运维命令参数输错下线过多服务器",
        "service": "s3（us-east-1 对象存储：index 元数据/位置 + placement 存储分配）",
        "scope": "region",
        "source": "https://aws.amazon.com/message/41926/",
        "symptoms": [
            "us-east-1 S3 请求大面积失败，错误率与延迟同时抬升（GET/LIST/PUT/DELETE 全失败）",
            "依赖 S3 的 EC2 新实例启动、EBS（快照恢复）、Lambda、S3 控制台连带报错",
            "index/placement 子系统容量被下线的服务器占比过大，触发完整重启",
            "AWS 状态页自身依赖 S3，无法更新（只能发 Twitter）",
        ],
        "red_herrings": [
            "容易先怀疑容量不足或代码 bug，但真因是运维操作",
        ],
        "root_cause": (
            "运维人员调试计费子系统慢查询时，按既定 playbook 执行容量下线命令，一个参数输入错误，"
            "导致下线了支撑 index（元数据/位置）与 placement（存储分配）两个基础子系统的大量服务器；"
            "两子系统需要完整重启，而该规模下多年未被完整重启过，恢复链路未经受考验，"
            "重启+校验耗时约 4 小时。"
        ),
        "decisive_steps": [
            ("先查最近一小时有没有运维操作/命令执行（谁在动容量），再怀疑容量或代码 bug", False),
            ("区分是哪个子系统不可用（index vs placement）以及容量是否低于下限", False),
            ("评估恢复路径本身的耗时风险（从未完整重启过的子系统，RTO 是未知数）", False),
            ("梳理依赖级联（S3 之外还有谁挂在上面：EBS/Lambda/EC2/控制台）", False),
        ],
        "related_changes": [
            "09:37 S3 团队成员按既定 playbook 执行容量下线命令（一个参数输错，实际下线远多于预期的服务器；无变更单）",
        ],
        "mitigation": (
            "止血：停止继续下线、谨慎按子系统重启恢复（index 先、placement 后）。"
            "动作分级：容量下线/重启属高风险（T3），必须审批；恢复路径漫长需提前通告。"
        ),
        "lessons": [
            "容量下线/节点摘除类命令必须二次确认目标范围，参数错误代价极大",
            "多年未完整重启的核心子系统，其 RTO 是未知数——要常态化演练",
            "状态页/控制台不能依赖自身服务，否则事故中失声",
        ],
    },
    {
        "doc_id": "gitlab-2017-db-deletion",
        "title": "GitLab 2017-01-31 数据库事故：复制滞后 + 删错主机数据目录 + 备份全失效",
        "service": "postgresql（主备集群）",
        "scope": "service",
        "source": "https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/",
        "symptoms": [
            "PostgreSQL 备库复制滞后持续扩大后完全停止；主库写入锁死，站点部分不可用",
            "23:00 备库需要的 WAL 段已在主库被回收（未开 WAL 归档）",
            "23:27 工程师删除数据目录跑 pg_basebackup 时执行在 db1（主库）而非 db2（备库）",
            "五种备份/复制手段（LVM 快照/常规备份/pg_dump/S3 备份桶/磁盘快照）全部静默失效",
        ],
        "red_herrings": [
            "19:00 数据库负载升高疑似垃圾信息，后查明部分来自误排期的用户硬删除后台任务",
        ],
        "root_cause": (
            "负载升高→备库复制滞后→WAL 段在主库被回收→人工重建备库过程中，一条删除数据目录的命令"
            "执行在了主库（db1）而不是备库（db2），300GB 生产数据几乎全毁；"
            "叠加五种备份/复制机制全部静默失效，最终只能恢复到 6 小时前的备份，丢失 17:20-00:00 数据。"
        ),
        "decisive_steps": [
            ("复制滞后先查 WAL 保留/归档：备库需要的段是否已被主库回收（无 WAL 归档就必然断）", False),
            ("任何对数据目录的破坏性操作前，先确认当前主机名/角色（主 or 备）——致命错误就是删错主机", False),
            ("别信备份配置，验证备份真的能恢复（复盘里五种备份机制全部静默失效）", False),
            ("回溯数小时内的人为操作（17:20 手动快照 + pgpool 实验）与负载突增的关联", True),
        ],
        "related_changes": [
            "17:20 工程师为搭 pgpool-II 测试环境，手动对生产库做 LVM 快照灌入 staging（无变更单）",
            "23:27 工程师在 db1.cluster（主库）误删数据目录后跑 pg_basebackup（误把主库当备库）",
        ],
        "mitigation": (
            "止血：从 6 小时前备份恢复，丢失部分数据并公开通告。"
            "动作分级：删数据目录/从备份恢复属不可逆数据操作（B 类，restore_from_backup），必须审批。"
            "雷点：永远先 hostname/role 确认再动数据目录；备份要定期真实恢复演练。"
        ),
        "lessons": [
            "WAL 归档是复制的命根子，没开归档复制必然会在滞后时断",
            "破坏性命令前强制确认主机角色，删错主库是教科书级灾难",
            "备份配置 ≠ 备份可用，必须周期性真实恢复演练",
        ],
    },
    {
        "doc_id": "meta-2021-bgp-dns",
        "title": "Meta 2021-10-04 全球故障：骨干维护命令误断 + DNS 自动撤回 BGP 放大",
        "service": "dns / 骨干网 BGP（全局）",
        "scope": "global",
        "source": "https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/",
        "symptoms": [
            "公共解析器对 facebook/instagram 等返回 SERVFAIL；外部观测到其 IP 前缀 BGP 路由被撤回",
            "访问流量趋近于零；内部依赖 DNS 的工具与远程管理通道同时不可用",
            "服务进程本身一直在运行——问题不是'服务器挂了'，而是'找不到服务器了'",
            "工程师只能进机房，高等级物理安全又拖慢了进入速度",
        ],
        "red_herrings": [
            "容易被误判为 DNS 服务进程故障或遭受攻击，实际是路由层不可达",
        ],
        "root_cause": (
            "一条评估骨干容量的维护命令误将骨干网全部连接断开（审计工具 bug 未拦截）；"
            "数据中心孤立后，DNS 服务器按安全设计撤回 BGP 广播（本该屏蔽单点不健康，"
            "却因全部同时触发而放大为全局不可达）；恢复受阻于内部工具与带外通道同样依赖已故障的网络/DNS。"
        ),
        "decisive_steps": [
            ("先分层定位：解析失败（DNS 层）vs 路由不可达（BGP 层）vs 应用错误——本例是名字根本解析不了", False),
            ("从外部视角检查自己前缀的 BGP 广播是否被撤回（不只看内部监控）", False),
            ("识别'保护机制'变成了放大器：DNS 不健康即撤回路由的设计在全部同时触发时适得其反", False),
            ("识别恢复路径自身受损：内部工具与带外访问依赖同一套已故障的系统，需带外/物理通道", False),
            ("把故障起始时间与维护窗口的命令/变更关联（骨干维护命令）", True),
        ],
        "related_changes": [
            "15:39 例行维护执行骨干容量评估命令（审计工具有 bug 未拦截，实际断开骨干全部连接，无变更单）",
        ],
        "mitigation": (
            "止血：恢复 BGP 广播（需进机房物理操作，因带外通道依赖同一网络）。"
            "根因修复：修复审计工具、为 DNS 撤回策略加抑制（避免全局同时撤回）。"
            "动作分级：改 BGP/全局关 WAF 属最高风险（T4），必须审批。"
        ),
        "lessons": [
            "安全保护机制要防'全部同时触发'的放大器效应",
            "维护/容量评估命令必须过审计拦截，且先在隔离范围验证",
            "恢复通道不能依赖被它恢复的系统（带外/物理兜底）",
        ],
    },
    {
        "doc_id": "fastly-2021-vcl-validation",
        "title": "Fastly 2021-06-08 全球 CDN 中断：客户合法配置触发数周前部署的软件 bug",
        "service": "edge-cdn（全球 CDN 边缘）",
        "scope": "global",
        "source": "https://www.fastly.com/blog/summary-of-june-8-outage",
        "symptoms": [
            "多个大型客户站点（新闻/社交/支付/政府）同时返回 503；约 85% 网络返回错误",
            "Fastly 监控 1 分钟内发现；源站侧观测到请求量异常暴涨（客户重试 + 回退放大）",
            "容易先怀疑源站容量/被打或遭受攻击（红鲱鱼）",
            "已知线索：5 月 12 日曾开始一次软件部署（距今近一个月）",
        ],
        "red_herrings": [
            "看到源站被打爆，易先怀疑源站容量/被打或攻击",
        ],
        "root_cause": (
            "5 月 12 日部署的软件里有一个未被发现的 bug；6 月 8 日一个客户推送了一次**合法**的配置变更，"
            "恰好命中该 bug 的触发条件，导致 85% 网络返回错误。"
            "放大因素：新的校验逻辑同步下发到全网（无灰度）；配置校验失败即停止服务，没有回退到上一个好配置的降级路径；"
            "验证逻辑与部署逻辑紧耦合，导致校验规则变更立即改变已有生产配置的行为。"
        ),
        "decisive_steps": [
            ("先分清 503 是哪一层产生的（CDN 边缘层 vs 源站），而不是被源站被打爆的表象带偏", False),
            ("把故障起点与近期软件版本部署（5/12，数周前）+ 客户侧配置变更做关联", False),
            ("识别客户配置是'合法'的：它只是触发器，根因在平台自己的代码里", False),
            ("识别 blast radius 是平台全局：同一套校验逻辑同步下发，无灰度、无回退路径", False),
            ("先查最近变更/发布（通用样板）", True),
        ],
        "related_changes": [
            "2021-05-12 Fastly 部署含未发现 bug 的软件（数周前，无灰度同步下发）",
            "2021-06-08 09:?? 客户推送一次合法配置变更，恰好命中 bug 触发条件（无变更单）",
        ],
        "mitigation": (
            "止血：禁用/回退触发 bug 的那个客户配置（先止血），49 分钟内 95% 网络恢复；"
            "永久修复 17:25 才开始部署。动作分级：平台级配置 kill switch 当前白名单里没有对应动作，"
            "需人工介入；原则：配置校验失败要有降级到上一好配置的回退路径。"
        ),
        "lessons": [
            "客户合法配置也能触发平台 bug——触发器≠根因",
            "配置校验/变更逻辑必须有灰度 + 回退（降级到上一好配置）",
            "全局同步下发无灰度，一个 bug 就是 85% 网络",
        ],
    },
    {
        "doc_id": "github-2018-mysql-splitbrain",
        "title": "GitHub 2018-10-21 MySQL 脑裂：43 秒网络分区引发 24 小时降级",
        "service": "mysql-cluster（Orchestrator 管理的主备）",
        "scope": "global",
        "source": "https://github.blog/2018-10-30-oct21-post-incident-analysis",
        "symptoms": [
            "Orchestrator 显示的复制拓扑里只剩西海岸机房的服务器；站点大面积错误",
            "webhook 与 Pages 构建大量积压；用户看到前后不一致的数据",
            "复制滞后：数十个只读副本落后主库数小时；积压 500 万+ webhook、8 万 Pages 构建",
            "跨大陆往返延迟约 60ms，应用无法承受",
        ],
        "red_herrings": [
            "容易被当成数据库自身故障，实际根因在网络维护引发的分区",
        ],
        "root_cause": (
            "例行维护更换光模块造成东西海岸 43 秒网络分区；Orchestrator 把分区判定为主库故障并跨区提升"
            "西海岸副本为主库；链路恢复后两个机房各自接受了对方没有的写入（事实上的脑裂/双主），"
            "无法安全切回。放大因素：Orchestrator 跨区提升策略本身是放大器；跨大陆 60ms 延迟让东海岸应用基本不可用；"
            "恢复路径（从远端备份恢复数 TB）从未整体演练过，耗时远超预期（总降级约 24 小时）。"
        ),
        "decisive_steps": [
            ("把数据库异常与刚刚发生的网络维护（43 秒断连）关联，而不是当成数据库自身故障", False),
            ("识别出现了双主/脑裂：两岸各自接受了对方没有的写入，这才是不能简单切回的原因", False),
            ("识别自动故障切换策略本身成了放大器（Orchestrator 跨区提升主库）", False),
            ("明确'数据完整性 > 可用性'的取舍，并识别恢复路径自身耗时（备份恢复数小时、副本滞后按幂衰减）", False),
            ("先查最近变更/发布（通用样板）", True),
        ],
        "related_changes": [
            "2018-10-21 22:52 计划维护更换故障 100G 光模块，造成东西海岸骨干断连 43 秒（网络分区，计划维护）",
        ],
        "mitigation": (
            "止血与恢复：从备份重建集群 → 同步副本 → 回切原拓扑 → 处理积压（三步走）。"
            "备份每 4 小时一次，恢复数 TB 耗时数小时；恢复完还要等副本追平（滞后按幂衰减）。"
            "动作分级：从备份恢复属不可逆数据操作（B 类，restore_from_backup），必须审批；"
            "优先保数据完整性（暂停 webhook/Pages）。"
        ),
        "lessons": [
            "自动故障切换（Orchestrator 跨区提升）要防'分区即提升'的脑裂放大器",
            "网络维护窗口与数据库高可用强相关，43 秒分区足以引发双主",
            "恢复路径（备份恢复数 TB）必须演练，否则 RTO 远超预期",
        ],
    },
]


def render_markdown(inc: dict) -> str:
    """把单条事故渲染成 RAGFlow 友好的 Markdown（叙事 + 结构化小节）。"""
    lines = []
    lines.append(f"# {inc['title']}")
    lines.append("")
    lines.append(f"- 受影响服务：{inc['service']}")
    lines.append(f"- 影响范围：{inc['scope']}")
    lines.append(f"- 来源复盘：{inc['source']}")
    lines.append("")
    lines.append("## 当时可见症状（值班视角）")
    for s in inc["symptoms"]:
        lines.append(f"- {s}")
    if inc.get("red_herrings"):
        lines.append("")
        lines.append("## 红鲱鱼（当时错误假设）")
        for r in inc["red_herrings"]:
            lines.append(f"- {r}")
    lines.append("")
    lines.append("## 真实根因")
    lines.append(inc["root_cause"])
    lines.append("")
    lines.append("## 决定性排查步骤")
    for text, generic in inc["decisive_steps"]:
        tag = "（通用样板，不计分）" if generic else "（事故特有，需领域推理）"
        lines.append(f"- {text} {tag}")
    lines.append("")
    lines.append("## 关联的变更 / 运维操作")
    for c in inc["related_changes"]:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## 止血与处置")
    lines.append(inc["mitigation"])
    lines.append("")
    lines.append("## 可复用的经验雷点")
    for l in inc["lessons"]:
        lines.append(f"- {l}")
    lines.append("")
    return "\n".join(lines)


def all_docs() -> list[tuple[str, str]]:
    """返回 [(文件名, markdown), ...]。"""
    out = []
    for inc in INCIDENTS:
        out.append((f"{inc['doc_id']}.md", render_markdown(inc)))
    return out


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(here, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    for fname, md in all_docs():
        with open(os.path.join(docs_dir, fname), "w", encoding="utf-8") as f:
            f.write(md)
    print(f"wrote {len(INCIDENTS)} incident docs to {docs_dir}")
