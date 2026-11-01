"""生产排查剧本库（Playbooks）：把 SRE 排查思路固化成结构化、可展示、可执行的知识。

设计原则（回答"生产环境怎么排查"）：
1. **排查链**：每类故障都有固定的步骤链（先确认影响面 → 再拉证据 → 再定位 → 再验证），
   步骤里带只读命令——运维人员照着就能复现排查过程。
2. **验证先行**：每个结论都配验证命令（"怎么验证我说的是对的"）。
3. **处置分级**：🟢 安全处置（只读/无停机/可自动）与 🔴 危险处置（有停机风险/数据风险，
   必须人工审批）分开列——"哪些命令需要业务审核"在这里显式定义。
4. **零停机优先**：处置动作标注停机风险评估（downtime_risk），优先推荐无损方案。

这是平台相对"日志文本匹配"的本质升级：**它输出的不是一句话结论，而是一条可执行、可审计、
可追责的排查作业链（runbook-as-data）**。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvestigationStep:
    step: str            # 步骤名
    purpose: str         # 这步在查什么、为什么
    commands: list[str]  # 只读命令（运维可直接执行）
    finding_hint: str    # 期望看到的证据（命中/排除判据）


@dataclass
class Remediation:
    action: str
    risk: str                    # 风险描述
    downtime_risk: str           # "none" | "brief" | "rolling" | "full"
    approver: str = ""           # 需要谁审批（空 = 可自动）
    command: str = ""            # 实际命令（危险动作只展示不自动执行）


@dataclass
class Playbook:
    id: str
    name: str
    signals: list[str]           # 触发特征（告警文本关键词）
    thinking: str                # 排查思路总纲（给运维看的"为什么这么查"）
    investigation: list[InvestigationStep]
    verification: list[str]      # 验证命令（只读）
    safe_actions: list[Remediation]
    approval_actions: list[Remediation]


# ── 通用排查首步（所有故障共用）─────────────────────────────
IMPACT = InvestigationStep(
    step="确认影响面", purpose="先搞清楚「谁受了影响、多严重」，再决定排查优先级和是否需要拉人",
    commands=["kubectl get pods -A -o wide | grep -v Running",
            "curl -s -o /dev/null -w '%{http_code} %{time_total}s' http://<svc>/healthz"],
    finding_hint="受影响 Pod 列表 / 错误率 / 健康检查耗时——决定 P0 还是 P2")
LAST_CHANGE = InvestigationStep(
    step="看最近变更", purpose="生产故障 80% 由变更引起——先看'最近谁动过'，能砍掉一半排查范围",
    commands=["kubectl get events -A --sort-by=.lastTimestamp | tail -20",
            "kubectl rollout history deploy/<svc> -n <ns>",
            "kubectl get deploy -A -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image"],
    finding_hint="最近 30 分钟内的 deploy/configmap/secret/scale 事件——有变更先怀疑变更")


PLAYBOOKS: dict[str, Playbook] = {

"resource_contention": Playbook(
    id="resource_contention",
    name="资源抢占（吵闹邻居 / CPU·内存抢占）",
    signals=["cpu", "starvation", "latency", "slow", "load", "抢占", "负载"],
    thinking="现象是'变慢'而不是'报错'时，先怀疑资源被抢。单节点集群里最大的吵闹邻居往往是"
             "另一个团队的批处理/压测容器。思路：确认变慢 → 看谁在吃资源 → 看时间线是否吻合 → "
             "评估是限流对方还是扩容自己——直接杀对方容器在生产里是最后手段。",
    investigation=[
        IMPACT,
        InvestigationStep(
            step="定位资源消耗方", purpose="找到真正在吃 CPU/内存的进程或 Pod——注意不一定是自己服务",
            commands=["cat /proc/loadavg && ps aux --sort=-%cpu | head -8",
                      "cat /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.max 2>/dev/null",
                      "kubectl top pods -A --containers 2>/dev/null || crictl stats 2>/dev/null",
                      "docker stats --no-stream 2>/dev/null | head -6"],
            finding_hint="某个非本服务 Pod/进程占用 CPU>80% 或内存接近 limit"),
        LAST_CHANGE,
        InvestigationStep(
            step="核对时间线", purpose="把'变慢起始时间'和'吵闹邻居启动时间'对齐，排除巧合",
            commands=["kubectl get events -A --sort-by=.lastTimestamp | tail -10",
                      "ps -o lstart= -p <吵闹邻居PID>"],
            finding_hint="两者时间差 < 5 分钟 → 强相关"),
    ],
    verification=["cat /proc/loadavg  # 恢复后应回落到基线", "kubectl get events -A | grep -i preempt",
                  "对比受害服务 healthz 耗时：整改前后各采 5 次"],
    safe_actions=[
        Remediation("给吵闹邻居设 CPU Limit（cgroup/k8s limits）", "影响对方性能上限，不影响可用性",
                    "none", command="kubectl set resources deploy/<noisy> --limits=cpu=500m"),
        Remediation("受害服务临时扩容 +1 副本（抢占多余时间片）", "纯增量，随时可缩回",
                    "none", command="kubectl scale deploy/<victim> --replicas=N+1"),
        Remediation("提高受害服务 requests 保证调度下限", "下次调度生效，无即时风险",
                    "none", command="kubectl set resources deploy/<victim> --requests=cpu=500m"),
    ],
    approval_actions=[
        Remediation("删除/驱逐吵闹邻居 Pod", "直接中断对方团队业务，必须对方负责人书面同意",
                    "full", approver="吵闹邻居 owner + SRE on-call",
                    command="kubectl delete pod <noisy-pod> -n <ns>"),
        Remediation("对吵闹邻居 namespace 设 ResourceQuota", "影响该团队所有工作负载，需平台侧审批",
                    "none", approver="平台负责人", command="kubectl apply -f quota.yaml"),
    ],
),

"change_induced": Playbook(
    id="change_induced",
    name="变更引入故障（跨部门发布/配置变更）",
    signals=["config", "env", "version", "rollout", "deploy", "变更", "发布", "配置"],
    thinking="报错时间点附近有人发布，先按'变更引起'查——这是最快路径。思路：锁定变更对象 → "
             "对比变更前后行为 → 确认是回滚还是修配置。注意：变更可能是别的团队做的，"
             "处置前必须同步对方，否则会出现'你回滚了、对方又发上来'的拉锯。",
    investigation=[
        IMPACT, LAST_CHANGE,
        InvestigationStep(
            step="对比变更前后差异", purpose="拿到变更内容，才能判断回滚还是修复",
            commands=["kubectl rollout history deploy/<svc> -n <ns>",
                      "kubectl describe deploy <svc> -n <ns> | grep -A5 'Annotations'",
                      "kubectl get configmap <cm> -o yaml | tail -20"],
            finding_hint="变更版本号 + 具体 diff（镜像 tag / env / 配置项）"),
        InvestigationStep(
            step="确认是变更而非偶发", purpose="排除同时段的其他因素（网络抖动、依赖故障）",
            commands=["kubectl logs deploy/<svc> -n <ns> --since=30m | grep -i error | head",
                      "kubectl get events -A --sort-by=.lastTimestamp | tail -10"],
            finding_hint="错误模式与变更内容强相关（如新配置项导致的启动失败）"),
    ],
    verification=["kubectl rollout status deploy/<svc> -n <ns>",
                  "kubectl get pods -l app=<svc> -o wide  # 新副本分布",
                  "对比变更前后的错误率曲线（Prometheus/日志计数）"],
    safe_actions=[
        Remediation("保留现场，先摘流量观察（不删任何东西）", "只读 + 摘流，随时可恢复",
                    "none", command="kubectl scale deploy/<svc> --replicas=0 # 仅确认无流量后"),
        Remediation("扩容旧版本副本（maxSurge 滚动，新旧并存）", "零停机，容量先补上再谈修复",
                    "none", command="kubectl set image deploy/<svc> <container>=<old-image>"),
    ],
    approval_actions=[
        Remediation("回滚到上一版本（kubectl rollout undo）", "会中断当前版本正在处理的请求，需评估在途业务",
                    "rolling", approver="变更发起方负责人 + SRE on-call",
                    command="kubectl rollout undo deploy/<svc> -n <ns>"),
        Remediation("删除他人创建的 ConfigMap/Secret", "影响引用它的所有工作负载，必须同步 owner",
                    "full", approver="资源 owner + 平台负责人", command="kubectl delete configmap <cm>"),
    ],
),

"node_disconnect": Playbook(
    id="node_disconnect",
    name="节点/服务断线（租用机器失联）",
    signals=["notready", "unreachable", "connection refused", "timeout", "断线", "失联", "not connect"],
    thinking="机器突然失联，按'网络层 → 系统层 → 服务层'自底向上查：节点还在吗？kubelet 活着吗？"
             "容器运行时活着吗？服务进程活着吗？租用机器场景最大的坑是：机器可能被云平台重装了、"
             "或者被别的租户/维护任务重启了——所以'最近谁重启过这台机器'是必查项。",
    investigation=[
        InvestigationStep(
            step="确认节点状态", purpose="先分清是'整个节点没了'还是'单个服务没了'",
            commands=["kubectl get nodes -o wide", "kubectl describe node <node> | grep -A10 Conditions",
                      "ping -c2 -W2 <node-ip> || echo unreachable"],
            finding_hint="NotReady/ unreachable = 节点级；仅 Pod 异常 = 服务级"),
        InvestigationStep(
            step="查节点系统层", purpose="节点在但服务断，查 kubelet/运行时/网络",
            commands=["systemctl status kubelet --no-pager | head -5",
                      "systemctl status containerd --no-pager | head -3",
                      "journalctl -u kubelet --since '10 min ago' --no-pager | tail -15",
                      "dmesg -T | grep -iE 'oom|killed|link down' | tail -5"],
            finding_hint="kubelet 崩溃/重启记录、OOM kill、网卡 down"),
        InvestigationStep(
            step="查租用机器元信息", purpose="租用机器要排除'外部因素'：云平台重启、重装、迁移",
            commands=["uptime && who -b", "last reboot | head -3", "cat /proc/uptime"],
            finding_hint="uptime 很小 = 机器刚重启过 → 找云平台事件"),
        LAST_CHANGE,
    ],
    verification=["kubectl get nodes -w  # 观察状态翻转",
                  "从节点内 curl 自己的 healthz：区分'节点失联'与'服务假死'",
                  "ss -tlnp | grep <port>  # 服务是否还在监听"],
    safe_actions=[
        Remediation("等待/观察（节点可能在自愈，如 kubelet 自动重启）", "无操作风险",
                    "none"),
        Remediation("从其他健康节点补副本（多节点集群）", "纯增量，随时可缩回",
                    "none", command="kubectl scale deploy/<svc> --replicas=N+1"),
    ],
    approval_actions=[
        Remediation("排水该节点（cordon + drain，Pod 全部迁走）", "该节点上所有 Pod 被驱逐重建，单节点场景=全停",
                    "rolling", approver="SRE on-call",
                    command="kubectl drain <node> --ignore-daemonsets --delete-emptydir-data"),
        Remediation("重启 kubelet / containerd", "重启期间该节点所有 Pod 就绪性受影响",
                    "brief", approver="SRE on-call", command="systemctl restart kubelet"),
        Remediation("重启/重装备份租用机器", "全停，必须先确认数据已备份",
                    "full", approver="机器 owner + 云平台审批", command="reboot"),
    ],
),

"image_pull": Playbook(
    id="image_pull",
    name="镜像拉取失败（ImagePullBackOff / ErrImagePull）",
    signals=["imagepull", "errimagepull", "pull", "registry", "镜像", "拉取"],
    thinking="Pod 起不来先看是不是镜像问题：拉不到镜像通常是四类——tag 写错、仓库不通（国内访问"
             "docker.io 被墙是高频）、拉取凭证（imagePullSecret）过期、镜像被删。"
             "思路：describe 看具体报错 → 区分是哪一类 → 验证仓库连通性 → 处置（改 tag/换国内"
             "镜像源/更新 secret）。注意改镜像源是变更动作，要走变更流程。",
    investigation=[
        IMPACT,
        InvestigationStep(
            step="看具体拉取报错", purpose="四类根因的报错文案不同，先分类再动手",
            commands=["kubectl describe pod <pod> | grep -A6 'Events'",
                      "kubectl get events --field-selector reason=Failed | tail -5"],
            finding_hint="manifest unknown=tag 错；connection refused/timeout=仓库不通；"
                         "unauthorized=secret 问题；not found=镜像被删"),
        InvestigationStep(
            step="验证仓库连通性与凭证", purpose="确认是'镜像不存在'还是'根本连不上仓库'",
            commands=["crictl pull <image:tag> 2>&1 | tail -3",
                      "kubectl get secret <pull-secret> -o yaml | grep -c 'dockerconfigjson'",
                      "timeout 5 bash -c 'echo > /dev/tcp/registry.cn-hangzhou.aliyuncs.com/443' && echo 仓库通 || echo 仓库不通"],
            finding_hint="crictl 手动拉取成功 = 集群侧凭证问题；失败 = 仓库/网络问题"),
        LAST_CHANGE,
    ],
    verification=["crictl images | grep <image>  # 节点上是否已有可用镜像",
                  "kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].state}'  # 观察 waiting 原因变化"],
    safe_actions=[
        Remediation("手动将镜像预拉到节点（仅消除拉取超时，不执行业务变更）", "不动业务，随时可清理",
                    "none", command="crictl pull <image:tag>"),
        Remediation("核对 imagePullSecret 有效期并提前告警（只读）", "无操作风险",
                    "none", command="kubectl get secret <pull-secret> -o jsonpath='{.metadata.annotations}'"),
    ],
    approval_actions=[
        Remediation("改用历史版本 tag（滚动更新，需评估版本差异）", "触发 Pod 滚动重建",
                    "rolling", approver="变更方负责人 + SRE on-call",
                    command="kubectl set image deploy/<svc> <container>=<old-tag>"),
        Remediation("配置国内镜像加速源后重拉", "需改 containerd 配置并重启，影响面大但已是国内集群标配",
                    "brief", approver="平台负责人", command="编辑 /etc/containerd/config.toml registry.mirrors"),
        Remediation("更新/新建 imagePullSecret（含凭证）", "凭证属敏感资产，必须审批且不能进日志",
                    "none", approver="平台负责人", command="kubectl create secret docker-registry ..."),
    ],
),

"disk_pressure": Playbook(
    id="disk_pressure",
    name="磁盘压力（写满/GC 失败）",
    signals=["disk", "space", "disk-pressure", "evict", "no space left", "磁盘", "写满"],
    thinking="磁盘慢报警通常是'日志/镜像/临时文件'三类堆积。生产里最危险的是 kubelet 开始驱逐 Pod"
             "（disk-pressure taint）——那时已经不是'要满'而是'已经在杀服务了'。"
             "思路：确认水位 → 找到大头（日志？镜像？气球文件？）→ 先清安全的（日志轮转、过期镜像）→ "
             "清完必须验证水位回落 + Pod 恢复调度。",
    investigation=[
        InvestigationStep(
            step="确认水位与告警级别", purpose="分清'即将满'（WARN）和'已在驱逐'（P0）",
            commands=["df -h / /var/lib/docker /var/log 2>/dev/null", "df -i /",
                      "kubectl describe node <node> | grep -B2 -A8 DiskPressure",
                      "kubectl get pods -A | grep -v Running"],
            finding_hint="use%>85% = 黄区；出现 EvictionThresholdMet/disk-pressure taint = 红区"),
        InvestigationStep(
            step="定位占用大头", purpose="不定位就删，生产大忌——先找到是谁在吃",
            commands=["du -sh /var/log/* 2>/dev/null | sort -rh | head -5",
                      "du -sh /tmp/* 2>/dev/null | sort -rh | head -5",
                      "du -sh /var/lib/containerd 2>/dev/null; crictl images | wc -l"],
            finding_hint="Top1 占用源（日志目录/临时文件/镜像层）"),
        LAST_CHANGE,
    ],
    verification=["df -h /  # 清理后 use% 应回落到 80% 以下",
                  "kubectl describe node <node> | grep -A5 Conditions  # DiskPressure=False",
                  "kubectl get events -A | grep -i evict  # 不再新增驱逐"],
    safe_actions=[
        Remediation("轮转/截断应用日志（truncate 而非 rm，避免句柄泄漏）", "标准运维动作，无风险",
                    "none", command="truncate -s 0 /var/log/<app>.log"),
        Remediation("清理过期容器镜像（k8s GC 参数先确认）", "正在使用的镜像不会动",
                    "none", command="crictl rmi --prune"),
        Remediation("删除自己产生的临时文件（气球/压测残留）", "无业务影响",
                    "none", command="rm -f /tmp/balloon"),
    ],
    approval_actions=[
        Remediation("调整 kubelet 驱逐阈值（eviction-hard）", "改了全局驱逐行为，可能延后真实风险暴露",
                    "none", approver="SRE on-call", command="编辑 /var/lib/kubelet/config.yaml"),
        Remediation("删除业务数据目录/数据库文件", "不可逆数据损失风险，必须业务方确认备份",
                    "full", approver="业务负责人", command="rm -rf /data/<app>"),
    ],
),

"oom_killed": Playbook(
    id="oom_killed",
    name="OOMKilled（内存超限被杀）",
    signals=["oom", "memory", "killed", "137", "内存"],
    thinking="OOM 分两种：容器内存超 limit（k8s 杀，看 describe 的 Last State）和节点内存耗尽"
             "（内核杀，看 dmesg）。修复不是简单'加大 limit'——先看是泄漏还是正常增长："
             "泄漏要修代码，增长要调 limit，两者处置完全不同。",
    investigation=[
        InvestigationStep(
            step="区分 OOM 类型", purpose="容器级 vs 节点级，根因和处置完全不同",
            commands=["kubectl describe pod <pod> | grep -A8 'Last State'",
                      "kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].restartCount}'",
                      "dmesg -T | grep -i 'killed process' | tail -3"],
            finding_hint="Last State=OOMKilled = 容器级；dmesg 有 kill = 节点级"),
        InvestigationStep(
            step="看内存曲线形态", purpose="泄漏（锯齿上升不回）还是峰值（正常冲高）",
            commands=["kubectl top pod <pod> --containers", "cat /sys/fs/cgroup/memory.peak 2>/dev/null"],
            finding_hint="峰值贴 limit = 调 limit；持续爬升 = 泄漏，找研发"),
        LAST_CHANGE,
    ],
    verification=["kubectl get pod <pod> -w  # 重启后是否再次 OOM（5 分钟内复现 = 泄漏）",
                  "kubectl top pod <pod>  # 内存是否回落"],
    safe_actions=[
        Remediation("只读观察：确认是否反复 OOM（5 分钟内重启≥2 次即判泄漏，需找研发）",
                    "无操作风险，纯诊断", "none",
                    command="kubectl get pod <pod> -w"),
        Remediation("导出内存曲线与 limit 对比报告（给扩容审批当依据）",
                    "只读", "none", command="kubectl top pod <pod> --containers"),
    ],
    approval_actions=[
        Remediation("调高 memory limit（有 headroom 时）", "需 Pod 重建，滚动更新有短暂就绪缺口",
                    "rolling", approver="SRE on-call", command="kubectl set resources deploy/<svc> --limits=memory=512Mi"),
        Remediation("重启 Pod 缓解（不解决根因，只争取排查时间）", "清空当前状态，可能丢在途请求",
                    "brief", approver="SRE on-call", command="kubectl rollout restart deploy/<svc>"),
        Remediation("回滚到内存正常的旧版本", "同变更回滚风险", "rolling",
                    approver="变更方 + SRE on-call", command="kubectl rollout undo deploy/<svc>"),
    ],
),

"dependency_failure": Playbook(
    id="dependency_failure",
    name="下游依赖故障（数据库/第三方/其他团队服务）",
    signals=["upstream", "dependency", "connection refused", "timeout", "下游", "依赖", "refused",
             "错误率", "失败率", "error rate", "error_rate", "5xx", "latency", "p99"],
    thinking="自己服务报错但自身健康，先查下游。思路：确认是'连不上'（网络/对端挂了）还是"
             "'连上了但慢/错'（对端性能或数据问题）——两者找的人不一样：前者找网络和对端 owner，"
             "后者查对端指标。跨团队场景最费时间的是'找不到对端 owner'，所以 CMDB/服务台账很重要。",
    investigation=[
        InvestigationStep(
            step="区分连不上与连上慢", purpose="决定排查方向和找谁",
            commands=["timeout 3 bash -c 'echo > /dev/tcp/<dep-host>/<port>' && echo TCP通 || echo TCP不通",
                      "time curl -s -o /dev/null -w '%{http_code} %{time_total}' http://<dep>/healthz",
                      "getent hosts <dep-host>  # DNS 是否解析"],
            finding_hint="TCP 不通 = 网络/对端宕机；TCP 通但慢 = 对端性能"),
        InvestigationStep(
            step="看对端侧证据", purpose="自己的日志只能看到'现象'，对端日志才有'原因'",
            commands=["kubectl get pods -n <dep-ns> -o wide", "kubectl logs deploy/<dep> -n <dep-ns> --tail=50",
                      "kubectl get events -n <dep-ns> --sort-by=.lastTimestamp | tail -5"],
            finding_hint="对端 Pod 状态/重启/错误日志"),
        LAST_CHANGE,
    ],
    verification=["从受害服务节点直接 curl 对端 healthz（绕过服务本身）",
                  "对比对端监控的错误率/延迟（认对端还是认自己）"],
    safe_actions=[
        Remediation("开启熔断/降级（有预案的话）", "牺牲部分功能保核心，需产品认可",
                    "none", command="kubectl set env deploy/<svc> CIRCUIT_BREAKER=on"),
        Remediation("切只读副本/备用节点（如果有）", "流量切换，需确认数据一致性",
                    "none"),
    ],
    approval_actions=[
        Remediation("重启下游依赖服务", "影响所有调用方，必须对端 owner 同意",
                    "brief", approver="对端 owner + SRE on-call", command="kubectl rollout restart deploy/<dep>"),
    ],
),

# ── 以下三类是 L3 真实事故回放后补的（Cloudflare/S3/GitLab/Meta 复盘驱动） ──

"ops_change_incident": Playbook(
    id="ops_change_incident",
    name="运维变更/操作事故（命令执行类根因）",
    signals=["误操作", "命令", "运维", "执行了", "操作", "removed", "capacity", "下线",
             "删错", "参数", "playbook", "操作审计", "operator", "变更单"],
    thinking="线上事故里很大一类根因不是代码不是容量，而是'人执行了一个意图正确、参数错误的命令'"
             "（AWS S3 2017 就是这么挂的）。思路：先拉**运维操作审计**（谁、何时、在哪台机、"
             "执行了什么命令、影响面）→ 对比'意图影响面'与'实际影响面' → 确认操作是否可回退 → "
             "评估恢复路径耗时。没有审计数据源，这一类根因**结构上就查不出来**。",
    investigation=[
        InvestigationStep(
            step="拉运维操作审计", purpose="先看'最近一小时谁动了什么'，再怀疑代码/容量",
            commands=["ops-audit query --since 60m --all-hosts",
                      "grep -h operator /var/log/ops-audit.log | tail -20",
                      "对比变更单：该操作是否有对应 change ticket"],
            finding_hint="操作者、命令原文、目标主机/子系统、是否在维护窗口内"),
        InvestigationStep(
            step="对比意图与实际影响面", purpose="参数输错的典型特征：意图小、实际大",
            commands=["ops-audit impact <op-id>  # 该操作实际命中的对象清单",
                      "对比 playbook 预期对象数 vs 实际命中数"],
            finding_hint="实际命中对象数远超预期 → 基本可判定为参数/目标错误"),
        InvestigationStep(
            step="确认可回退性与恢复路径", purpose="恢复耗时往往比修复本身更决定故障时长",
            commands=["ops-audit rollback-plan <op-id>",
                      "确认受影响子系统最近一次完整重启是什么时候（RTO 未知数）"],
            finding_hint="可回退操作 + 有回滚预案 → 尽快回退；不可回退 → 评估重建耗时"),
        InvestigationStep(
            step="冻结后续同类操作", purpose="防止'你回滚了、对方又发上来'的拉锯",
            commands=["ops-audit freeze --command-pattern '<pattern>' --until <ts>"],
            finding_hint="同模式操作在窗口期内被冻结"),
    ],
    verification=["ops-audit query --since 60m  # 确认误操作后无同类操作再次执行",
                  "对比操作前后子系统容量/错误率曲线，确认回到操作前水位",
                  "核对实际影响对象清单与变更单声明的一致性"],
    safe_actions=[
        Remediation("回退该操作（有回滚脚本/配置备份时）", "回到操作前状态，可反复执行",
                    "none", command="ops-audit rollback <op-id>"),
        Remediation("冻结同模式操作窗口（防拉锯）", "只冻结不修复，随时可解除",
                    "none", command="ops-audit freeze --command-pattern '<pattern>'"),
    ],
    approval_actions=[
        Remediation("大面积回滚/批量恢复", "影响面大，需操作方 + SRE 双确认",
                    "rolling", approver="操作方负责人 + SRE on-call",
                    command="ops-audit rollback <op-id> --force"),
        Remediation("从备份恢复数据", "不可逆，必须先确认备份可用且数据Owner同意",
                    "full", approver="数据 Owner + SRE on-call", command="restore-from-backup <set>"),
    ],
),

"db_replication": Playbook(
    id="db_replication",
    name="数据库复制/备份事故（滞后、断链、误删、备份失效）",
    signals=["replication", "复制", "wal", "备库", "主库", "standby", "primary", "备份",
             "backup", "数据丢失", "pg_basebackup", "归档", "archive"],
    thinking="数据库事故有三条经典链：①复制滞后→WAL 段在主库被回收→备库断链（没开归档必然发生）；"
             "②重建备库时的破坏性操作打在主库上（GitLab 2017 就是这么丢的 300GB）；"
             "③备份机制'配了但静默失效'（pg_dump 版本混用、备份桶是空的）。"
             "思路：先查复制状态与 WAL 保留 → 再确认主备角色（破坏性操作前必须） → "
             "**验证备份真的能恢复**（不信配置，信演练）→ 定位数据丢失窗口。",
    investigation=[
        InvestigationStep(
            step="查复制状态与 WAL 保留", purpose="复制断链的第一根因是备库要的段已被主库回收",
            commands=["psql -c 'select * from pg_stat_replication'",
                      "主库: show wal_keep_size; 查 pg_wal 目录最旧段",
                      "确认 archive_mode/archive_command 是否开启并真的在归档"],
            finding_hint="滞后量、断链时间点、WAL 是否被回收、归档是否真的在工作"),
        InvestigationStep(
            step="确认主备角色再动手", purpose="GitLab 300GB 就是删错主机删掉的",
            commands=["select pg_is_in_recovery();  # true=备库 false=主库",
                      "psql -c 'select inet_server_addr(), inet_server_port()'",
                      "echo $HOSTNAME  # 与 CMDB 登记的角色核对"],
            finding_hint="当前连接的是主库还是备库——破坏性操作前必须显式确认"),
        InvestigationStep(
            step="验证备份真的能恢复", purpose="复盘里五种备份机制全部静默失效",
            commands=["列出备份集与时间点：pg_backrest info / ls备份桶",
                      "挑最近一个备份做恢复演练（到临时实例）",
                      "核对备份大小是否合理（几字节=静默失败）"],
            finding_hint="备份可恢复 + RPO 覆盖故障窗口 → 才敢动手修"),
        InvestigationStep(
            step="定位数据丢失窗口", purpose="决定'能恢复到什么程度'，也是对外的交代",
            commands=["对比最后一个可用备份时间点与故障起始时间",
                      "从 Binlog/WAL 归档（如有）补捞窗口内数据"],
            finding_hint="丢失窗口 = 故障起始 → 最后备份；窗口越小越好"),
    ],
    verification=["pg_stat_replication 滞后量回落到秒级",
                  "备库 pg_is_in_recovery()=true 且可持续追赶",
                  "恢复演练：从选定备份集恢复到临时实例并抽样校验数据",
                  "监控告警：复制滞后阈值告警已恢复"],
    safe_actions=[
        Remediation("重建备库（确认目标是备库后，pg_basebackup 到备库）", "不碰主库，可反复执行",
                    "none", command="pg_basebackup -h <primary> -D <standby-datadir> -R"),
        Remediation("开启/修复 WAL 归档（主库参数，需重启场景外评估）", "防止再次断链，纯增量",
                    "none", command="archive_command 配置 + reload"),
        Remediation("清理无用复制槽/连接", "释放主库 WAL 占用，不影响数据",
                    "none", command="pg_drop_replication_slot <slot>"),
    ],
    approval_actions=[
        Remediation("主备切换（promote）", "切换期间写入方向变化，需业务确认窗口",
                    "brief", approver="DBA + 业务负责人", command="pg_ctl promote"),
        Remediation("从备份恢复数据到主库", "不可逆数据操作，必须先证明备份可用",
                    "full", approver="数据 Owner + DBA", command="pg_backrest restore <set>"),
        Remediation("删除数据目录（任何主机）", "最高风险，必须先过角色确认+双人复核",
                    "full", approver="DBA + SRE on-call", command="rm -rf <datadir>"),
    ],
),

"network_dns_bgp": Playbook(
    id="network_dns_bgp",
    name="网络层事故（DNS 解析失败 / BGP 路由撤回）",
    signals=["dns", "解析", "resolve", "servfail", "bgp", "路由", "route", "prefix",
             "广播", "announce", "网络不通", "unreachable"],
    thinking="域名访问不了要分层看：是**名字解析不了**（DNS 层）还是**名字能解析但连不上**"
             "（BGP/网络层）还是**连上了但应用报错**。Meta 2021 的经典性在于：服务器全都在跑，"
             "但 DNS 服务器'不健康就撤回 BGP'的安全设计在全部同时触发时，把全局可达性打掉了。"
             "思路：分层定位 → **从外部视角看自己的前缀广播**（内部监控全绿也没用） → "
             "对照维护窗口 → 检查控制面/带外通道是否同链路受损（恢复工具自身也会挂）。",
    investigation=[
        InvestigationStep(
            step="分层定位（DNS / BGP / 应用）", purpose="三层找的人完全不同",
            commands=["dig +short <domain> @1.1.1.1  # 解析层",
                      "dig +trace <domain>  # 逐级看哪一级断",
                      "从外网主机 curl -v http://<ip>  # 绕过 DNS 直连 IP",
                      "mtr -n <ip>  # 网络层路径"],
            finding_hint="SERVFAIL=解析层失败；IP 通但域名不通=DNS 记录/权威服务器问题；"
                         "IP 也不通=路由/BGP 层"),
        InvestigationStep(
            step="从外部视角查自己前缀的 BGP 广播", purpose="内部监控说'正常'没用，要看互联网怎么看你",
            commands=["whois -h whois.radb.net <prefix>",
                      "curl https://stat.ripe.net/data/ris-prefixes/data.json?resource=<asn>",
                      "对比历史广播记录（RIPEstat / BGPView）看前缀是否被撤回"],
            finding_hint="前缀广播消失/大幅减少 → BGP 层被撤回"),
        InvestigationStep(
            step="对照维护窗口与变更", purpose="骨干维护命令是 Meta 事故的起点",
            commands=["查维护窗口内的网络变更单",
                      "对路由器/骨干设备做配置 diff（running vs 最近 known-good）",
                      "看审计：谁在故障前执行过网络类命令"],
            finding_hint="故障起始时间与网络变更/维护命令吻合"),
        InvestigationStep(
            step="评估控制面与带外通道", purpose="恢复工具如果和被修复的系统同链路，恢复会翻车",
            commands=["确认带外管理（OOB/串口/跳板机）是否独立于故障链路",
                      "确认 DNS 服务自身是否依赖故障中的网络",
                      "检查'不健康即撤回'类自动保护是否被同时触发（放大器效应）"],
            finding_hint="控制面同链路受损 → 必须走带外；自动保护被同时触发 → 先隔离放大器"),
    ],
    verification=["dig +short <domain> @公共解析器  # 解析恢复",
                  "RIPEstat 外部视角确认前缀广播已恢复",
                  "从多个地理位置的探测节点确认可达性",
                  "对比故障前后的路由表/广播数量"],
    safe_actions=[
        Remediation("切换客户端/服务到备用 DNS 解析器", "不动基础设施，随时可切回",
                    "none", command="resolv.conf → 备用 DNS"),
        Remediation("临时停用'不健康即撤回'自动保护（单点）", "把放大器摘掉，防止雪球",
                    "none", command="撤销该条自动撤回策略（仅单点）"),
    ],
    approval_actions=[
        Remediation("修改 BGP 广播/路由策略", "影响全局可达性，必须网络负责人 + 双人复核",
                    "full", approver="网络负责人 + SRE on-call",
                    command="router bgp <asn> → 调整 network/prefix 广播"),
        Remediation("重启/替换骨干路由器、动物理链路", "影响整区流量，需维护窗口",
                    "full", approver="网络负责人 + 云平台审批", command="替换/重启骨干设备"),
    ],
),
}


def match_playbooks(text: str) -> list[Playbook]:
    """按告警文本匹配排查剧本（可多个命中，按相关度排序）。"""
    low = (text or "").lower()
    hits = []
    for pb in PLAYBOOKS.values():
        score = sum(1 for s in pb.signals if s.lower() in low)
        if score:
            hits.append((score, pb))
    hits.sort(key=lambda x: -x[0])
    return [pb for _, pb in hits]


def get_playbook(pb_id: str) -> Playbook | None:
    return PLAYBOOKS.get(pb_id)
