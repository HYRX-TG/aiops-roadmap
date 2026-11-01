# 智能体排查能力实测：只给症状，看大模型能不能自己查出根因

- 模型：`deepseek-chat`（temperature 0.2）
- 时间：2026-10-25 17:16
- 总调用：73 次 · tokens in/out = 74733/16973

## 三组对照在测什么

| 组 | 做法 | 回答的问题 |
|---|---|---|
| A 单轮 | 只给症状，不给任何工具 | 光凭模型先验知识能抓到多少？ |
| B 工具自主 | 给只读工具，自己决定查什么 | **它会不会用工具、能不能查到？**（本题核心） |
| C 喂全证据 | 全部证据一次性塞进 prompt | 证据齐全时能推到什么程度？（上限参照） |

## 结果总表

| 世界 | A 单轮（关键词/LLM） | B 工具自主（关键词/LLM） | C 喂全证据（关键词/LLM） | B 工具数 | B 步数 | B 耗时 |
|---|---|---|---|---|---|---|
| edge-cdn-503 | 2/4 / 4/4 | **2/4 / 2/4** | 4/4 / 4/4 | 13 次 | 13 | 21.0s |
| mysql-splitbrain | 2/4 / 3/4 | **4/4 / 4/4** | 4/4 / 4/4 | 13 次 | 13 | 21.2s |
| S3-capacity-removal | 3/4 / 1/4 | **2/4 / 4/4** | 4/4 / 4/4 | 13 次 | 13 | 21.3s |
| zephyr-quota-cascade | 0/4 / 2/4 | **4/4 / 3/4** | 3/4 / 4/4 | 14 次 | 14 | 23.8s |

## 逐世界详情

### edge-cdn-503

- **症状（模型只看到这个）**：全球多个站点同时返回 503，约 85% 的网络在返回错误，持续约 1 小时。源站侧看到请求量暴涨（客户重试）。最初怀疑是大规模攻击或容量不足。
- **真实根因（模型看不到）**：数周前的一次软件部署引入了未发现的 bug（新增的配置校验逻辑）。今天一个客户推送了完全合法的配置变更，恰好命中该 bug 的触发条件，导致全网的边缘节点同时拒绝服务。放大因素：校验逻辑同步下发到所有节点（无灰度）、校验失败就直接停服务（没有回退到上一个好配置的路径）。

**决定性步骤（跑前固定）**：
1. 先分清 503 是哪一层产生的（CDN 边缘层 vs 源站），而不是被源站被打爆的表象带偏
2. 把故障起点与近期的软件版本部署 + 客户侧配置变更做关联
3. 识别客户配置是合法的：它只是触发器，根因在平台自己的代码里
4. 识别影响面是全局的：同一套校验逻辑同步下发，无灰度、无回退路径

#### A 单轮基线 —— 2/4（命中 1/4 个决定性步骤）　｜　LLM 评审：4/4（步骤1和4命中（区分边缘/源站、识别全局同步下发无灰度无回退），但步骤2未关联到软件版本部署（仅推断为CDN配置下发），步骤3未识别客户配置合法且根因在平台代码，故扣分。）

**根因判定**：边缘CDN配置变更（如路由/回源/证书/ACL规则）被错误下发，导致全球多数边缘节点无法正常处理请求并返回503；源站请求量暴涨是客户端重试放大所致，而非根因

**排查链**：
- [确认故障范围与时间线] 全球多站点同时、约85%网络受影响、持续约1小时，符合集中式配置/控制面变更的爆炸半径，而非单点容量问题
- [区分源站故障与边缘故障] 源站看到请求量暴涨但错误由edge-cdn返回503，说明边缘层在回源前或回源失败即拒绝，源站压力是重试的次生现象
- [评估攻击/容量假设] 若为DDoS或容量不足，通常表现为渐进劣化、局部热点或特定区域先受影响；全球同步85%错误率更指向一次全局配置推送或控制面故障
- [检查变更与发布记录] 推断故障窗口前存在CDN配置/规则/证书/回源策略的批量下发，且缺少灰度或回滚保护
- [观察恢复模式] 约1小时后恢复，符合配置回滚或控制面修复的时长特征，而非攻击自然消退

**不确定项**：具体是哪类配置项（路由、回源、证书、ACL、WAF规则）出错；是否存在控制面/下发系统自身故障；是否有攻击叠加或放大了影响；85%网络的具体统计口径与受影响节点分布

#### B 工具自主 —— 2/4（命中 1/4 个决定性步骤）　｜　LLM 评审：2/4（识别了边缘层503与客户配置触发，但未关联近期软件部署、未认定客户配置合法（反将其列为回滚对象）、未识别同步下发无灰度无回退的全局放大机制。）

**工具调用链（13 次）**：
- `list_recent_changes` {"service": "edge-cdn", "window": "24h"}
- `get_metrics` {"service": "edge-cdn", "metric": "error"}
- `get_metrics` {"service": "edge-cdn", "metric": "http_5xx_ratio"}
- `get_metrics` {"service": "edge-cdn", "metric": "cpu_usage_pct"}
- `get_metrics` {"service": "edge-cdn", "metric": "edge_latency_p99_ms"}
- `get_logs` {"service": "edge-cdn", "level": "ERROR"}
- `query_ops_audit` {"host": "", "window": "24h"}
- `get_logs` {"service": "edge-cdn", "level": "ERROR"}
- `get_topology` {"service": "edge-cdn"}
- `get_metrics` {"service": "origin-web", "metric": "inbound_rps"}
- `get_metrics` {"service": "edge-cdn", "metric": "http_5xx_ratio"}
- `get_logs` {"service": "config-validator"}
- `submit_diagnosis` {}

**根因判定**：客户 acme.com 于 09:44 推送的配置更新触发 edge-cdn 配置校验失败，worker 无 fallback 直接退出并进入 VCL 编译错误路径，导致 edge-cdn 全局拒绝请求返回 503；源站请求量暴涨是客户端重试放大所致，非攻击或容量不足。

**排查链**：
- [确认影响面] edge-cdn 5xx 比例从 0.002 骤升至 0.85 并持续约 1 小时，与故障现象吻合
- [排除容量/攻击] edge-cdn CPU 与延迟均正常，无容量瓶颈
- [关联变更] 09:44 客户 acme.com 自助推送配置更新，时间点与故障起点一致
- [日志定位根因] 配置校验失败导致 worker 退出，无 fallback，触发 VCL 编译错误路径拒绝请求
- [确认放大效应] 源站 inbound_rps 从 1200 暴涨至 9100 后回落，为客户端重试放大，非真实攻击
- [运维操作关联] 10:27 bob 在 edge-control-01 全局禁用 config-validator（INC-0608），属故障后应急操作，非根因

**不确定项**：客户配置具体哪一项导致 'unexpected state' 校验失败，需拿到配置 diff 确认；config-validator 无日志，无法直接看到校验失败细节；10:27 禁用 config-validator 是否为恢复手段及其对当前状态的影响需与 bob 确认

#### C 喂全证据 —— 4/4（命中 3/4 个决定性步骤）　｜　LLM 评审：4/4（四步全部命中：明确区分边缘层503与源站重试次生放大、关联27天前v7.2部署与09:44客户配置推送、指出客户配置合法仅为触发器而缺陷在平台校验器、并识别全局同步下发无灰度无fallback的放大因素。）

**根因判定**：edge-cdn v7.2 引入的 config-validator 在客户 acme.com 于 09:44 推送配置时触发校验失败，且该组件未配置 fallback，导致 worker 退出、VCL 编译错误路径被触发并拒绝请求，全球边缘节点返回 503；源站请求暴涨是客户端重试造成的次生放大，而非攻击或容量不足。

**排查链**：
- [变更引入缺陷组件] 27 天前 edge-cdn 从 v7.1 升级到 v7.2，v7.2 新增 config-validator 组件，为后续故障埋下隐患
- [客户配置触发校验失败] 09:44 客户 acme.com 推送配置，校验器报 unexpected state 并中止服务
- [无 fallback 导致 worker 退出] 校验失败后 worker 直接退出，且明确无 fallback 配置
- [拒绝请求并扩散为 503] VCL 编译错误路径被触发，节点拒绝请求，5xx 比例从 0.002 飙升至 0.85
- [源站过载为次生现象] 源站 inbound_rps 从 1200 涨到 9100，日志明确为客户端重试，CPU 升高但属重试放大
- [排除容量与攻击] edge-cdn 自身 CPU 仅 38-44%、延迟 p99 22-25ms，无容量瓶颈；错误与配置推送时间点精确吻合，非攻击特征
- [处置恢复] 10:27 运维全局禁用 config-validator，10:36 worker 恢复健康并恢复流量，5xx 回落

**不确定项**：acme.com 配置中具体哪条内容触发 unexpected state 无法从现有证据确认；为何 09:44 推送后 5xx 在多个采样点持续约 1 小时才于 10:27 处置，中间告警与响应链路细节不明；billing-api v2.4.1、pg_basebackup、UPS 巡检与本次故障无直接关联，但无法完全排除其对 db-primary-01 的间接影响；全球 412 个副本是否全部同时受影响、是否存在部分节点未触发，证据不足

### mysql-splitbrain

- **症状（模型只看到这个）**：站点大面积报错，用户看到数据前后不一致。Orchestrator 显示的复制拓扑里只剩西海岸机房的服务器。webhook 与页面构建大量积压。
- **真实根因（模型看不到）**：例行维护更换光模块时，东西海岸骨干断连 43 秒。Orchestrator 把这 43 秒的失联判定为主库故障，跨区把西海岸副本提升为主库。网络恢复后两个机房各自接受了对方没有的写入（事实上的双主/脑裂），无法安全切回。放大因素：自动故障切换策略本身成了放大器；跨大陆 60ms 延迟让东海岸应用不可用。

**决定性步骤（跑前固定）**：
1. 把数据库异常与刚刚发生的网络维护（43 秒断连）关联起来，而不是当成数据库自身故障
2. 识别出现了双主/脑裂：两岸各自接受了对方没有的写入
3. 识别自动故障切换策略本身成了放大器（Orchestrator 跨区提升主库）
4. 明确数据完整性优先于可用性，并识别恢复路径自身耗时

#### A 单轮基线 —— 2/4（命中 1/4 个决定性步骤）　｜　LLM 评审：3/4（识别了双主/脑裂和自动切换放大器，但未把异常关联到43秒网络维护，也未明确数据完整性优先及恢复路径耗时。）

**根因判定**：Orchestrator 与西海岸机房之间的网络分区或 Orchestrator 自身故障，导致其只看到西海岸副本、误判东海岸主库/其他机房节点失联；同时复制拓扑异常引发读写路由混乱，造成用户看到数据前后不一致，webhook 与页面构建因依赖数据库写入/事件而大量积压。

**排查链**：
- [确认 Orchestrator 拓扑视图与各机房节点可达性] Orchestrator 仅显示西海岸服务器，说明它到东海岸/其他机房的探测失败，或这些节点被标记为不可达；更可能是 Orchestrator 所在网络分区或 DNS/防火墙变更，而非所有东海岸 MySQL 同时宕机。
- [检查 MySQL 复制状态与主库选举历史] 拓扑中只剩西海岸节点，可能已发生误切换或双主/多主写入，导致不同请求落到不同节点，出现数据前后不一致。
- [检查应用读写路由与连接池状态] 应用可能仍连接旧主库或部分节点，读请求分散到复制延迟节点，放大数据不一致现象。
- [检查 webhook 与页面构建队列积压原因] 积压通常因数据库写入失败、事件表锁等待或 binlog 复制中断导致消费者无法推进；与 mysql-cluster 故障时间点吻合。
- [确认 Orchestrator 自身健康与配置] Orchestrator 单点/脑裂、raft 成员异常或探测超时配置过短，都可能导致拓扑视图只保留一个机房。

**不确定项**：Orchestrator 与东海岸机房之间具体是网络分区、防火墙变更还是 Orchestrator 进程/raft 故障；是否已发生自动主库切换或双主写入；数据不一致的具体范围与受影响表；webhook 与页面构建积压是数据库写入失败还是下游消费者自身故障

#### B 工具自主 —— 4/4（命中 3/4 个决定性步骤）　｜　LLM 评审：4/4（前三步均实质命中（关联网络维护、识别双主、指出Orchestrator跨区提升为放大器），但未明确表述数据完整性优先于可用性及恢复路径自身耗时，故第4步未命中。）

**工具调用链（13 次）**：
- `list_recent_changes` {"service": "mysql-cluster", "window": "24h"}
- `list_recent_changes` {"service": "", "window": "24h"}
- `get_topology` {"service": "mysql-cluster"}
- `get_metrics` {"service": "mysql-cluster", "metric": "error"}
- `get_metrics` {"service": "mysql-cluster", "metric": "latency"}
- `get_metrics` {"service": "mysql-cluster", "metric": "replication_lag_sec"}
- `get_metrics` {"service": "mysql-cluster", "metric": "writes_east_per_sec"}
- `get_metrics` {"service": "mysql-cluster", "metric": "writes_west_per_sec"}
- `get_logs` {"service": "mysql-cluster", "level": "ERROR"}
- `query_ops_audit` {"host": "east-01", "window": "24h"}
- `query_ops_audit` {"host": "", "window": "24h"}
- `get_logs` {"service": "mysql-cluster", "level": "ERROR"}
- `submit_diagnosis` {}

**根因判定**：网络团队按计划更换 east-west 骨干 100G 光模块（CHG-4417）导致链路 flap 43 秒，Orchestrator 在跨区域复制中断期间误将西海岸副本 west-02 提升为主库，但东海岸 east-01 仍保持 read-write，形成双主（split-brain），两区域各自接受独立写入，造成复制断裂与数据前后不一致。

**排查链**：
- [确认影响面与错误趋势] inconsistent_read_errors 从 0 快速升至 120，复制延迟从 0.2s 暴涨到 24000s，说明复制已严重中断
- [定位触发事件] 22:51 网络团队在 east-core-sw-01 更换 100G 光模块，链路 flap 43 秒，与故障时间点吻合
- [确认双主与写入分裂] Orchestrator 跨区域提升 west-02 为主，同时 east-01 仍为 read-write，出现两个主库；东海岸写入归零、西海岸持续写入，两区域独立接受写入
- [排除人为误操作] east-01 无运维操作记录，全局审计仅见计划内光模块更换与一次只读 mysqladmin status，无异常变更

**不确定项**：两区域各自写入的具体数据差异范围与业务影响尚需对账确认；Orchestrator 自动提升的具体触发阈值与配置未直接查证；webhook 与页面构建积压为下游表现，未单独查证其队列指标

#### C 喂全证据 —— 4/4（命中 4/4 个决定性步骤）　｜　LLM 评审：4/4（四步全部命中：将43秒断连与维护关联、识别双主与独立写入、指出Orchestrator跨区提升为放大器、以数据完整性优先并暂停写入且给出恢复路径。）

**根因判定**：东海岸核心交换机更换光模块导致 east-01 与集群网络隔离约43秒；Orchestrator 在30秒死主检测超时后，于链路恢复前1秒将西海岸副本 west-02 跨地域提升为主库。随后东海岸链路恢复，east-01 仍以 read-write 主库身份继续接受写入，形成双主（east-01 与 west-02 同时可写），两地域独立写入导致复制断裂、数据前后不一致、读快照不一致及 web-frontend 5xx 激增；为保护数据完整性，webhook 与页面构建被暂停并大量积压。

**排查链**：
- [计划内网络变更触发主库短暂失联] 22:51 更换 east-core-sw-01 的100G光模块，链路 flap 43秒；22:52:00 Orchestrator 检测到 east-01 不可达并开始 failover
- [死主检测超时，Orchestrator 在链路恢复前执行跨地域提升] 30秒死主检测超时后，22:52:43 网络恢复，22:52:44 Orchestrator 仍将 west-02 跨地域提升为主库，说明提升决策发生在隔离窗口内且未等待/复核原主状态
- [原主 east-01 未被降级，形成双主] 22:53:00 检测到 east-01 与 west-02 均为 read-write 双主；east-01 资源状态仍为 primary (east)，网络隔离43秒后恢复但未被 fencing/降级
- [双主导致两地域独立写入与复制断裂] 复制断裂日志明确两地域接受独立写入；指标显示东海岸写入在故障窗口降为0后西海岸写入升至8100+，复制延迟从0.2秒飙升至24000秒，符合双写分叉
- [数据不一致传导至前端并触发保护性暂停] inconsistent_read_errors 从0升至120，web-frontend 5xx 比例从0.001升至0.31，前端报 inconsistent snapshot 与读写路由错误；23:19 暂停 webhook 与页面构建以保护数据完整性，造成积压

**不确定项**：east-01 在22:52:43链路恢复后是否立即恢复对外读写、以及其恢复写入的具体时间点无法从现有证据精确确认；两地域分叉写入的具体数据范围、受影响表/行数及业务损失无法从现有证据确认；Orchestrator 是否配置了 fencing/STONITH 或跨地域提升前的二次确认策略，证据仅显示 cross-region promotion policy enabled；webhook 与页面构建积压的具体数量及恢复所需时间无法确认

### S3-capacity-removal

- **症状（模型只看到这个）**：对象存储的写入与索引查询大面积失败，大量依赖它的上层服务（计算、块存储、监控）同时报错。控制台操作也变慢。
- **真实根因（模型看不到）**：一名授权运维按既定 playbook 下线计费子系统的部分服务器，命令里的一个参数（要移除的容量/服务器数量）输错，实际移除了远超预期的服务器——包括 index（元数据/位置服务）和 placement 子系统所需的容量。这两个子系统已多年未整体重启，重启耗时远超预期。

**决定性步骤（跑前固定）**：
1. 先查最近一小时有没有运维操作/命令执行（谁在动容量）
2. 区分是哪个子系统不可用（index 元数据 vs placement 存储分配 vs 其他）
3. 评估恢复路径本身的耗时风险（从未完整重启过的子系统）
4. 梳理依赖级联（对象存储之外还有谁挂在上面）

#### A 单轮基线 —— 3/4（命中 2/4 个决定性步骤）　｜　LLM 评审：1/4（排查全程假设元数据/索引层自身故障或雪崩，未查运维操作、未区分index与placement、未评估重启耗时风险、未梳理依赖级联，四步均未命中。）

**根因判定**：对象存储的元数据/索引层（数据库或分布式KV）发生全局性故障或饱和，导致写入路径与索引查询同时不可用，进而拖垮依赖它的上层服务

**排查链**：
- [从现象范围判断故障层级] 写入和索引查询同时大面积失败，说明问题不在单个数据节点或单块磁盘，而在两者共用的元数据/索引服务或协调层
- [区分是对象存储自身故障还是被上层拖垮] 计算、块存储、监控同时报错且控制台变慢，属于典型的扇出型依赖故障，根因更可能在 object-storage 内部而非某个上层服务
- [检查控制台变慢的含义] 控制台操作也慢说明请求在进入后端前或鉴权/元数据环节就受阻，指向元数据服务、鉴权服务或入口网关的饱和/不可用，而非纯数据面带宽问题
- [评估写入与查询同时失败的常见模式] 元数据库连接池耗尽、索引集群脑裂/选主、分布式锁服务不可用、或元数据层被大量重试流量打满，都会同时命中写入和查询路径
- [判断是否为容量/雪崩型故障] 大面积失败加控制台变慢更像级联雪崩：某组件超时导致上游重试放大，连接池与线程池耗尽后全面不可用

**不确定项**：具体是元数据库、分布式KV还是索引集群故障，无法确认；是否存在近期变更（发布、扩缩容、配置修改）触发；是否为磁盘/网络等基础设施故障；控制台变慢是鉴权服务还是元数据服务导致

#### B 工具自主 —— 2/4（命中 1/4 个决定性步骤）　｜　LLM 评审：4/4（步骤1、2、4均命中；步骤3仅提到恢复时长不确定，未评估从未完整重启子系统的耗时风险，故扣一步。）

**工具调用链（13 次）**：
- `get_topology` {"service": "object-storage"}
- `get_metrics` {"service": "object-storage", "metric": "error"}
- `get_metrics` {"service": "object-storage", "metric": "write_success_ratio"}
- `get_metrics` {"service": "object-storage", "metric": "index_service_available"}
- `get_metrics` {"service": "object-storage", "metric": "placement_service_available"}
- `list_recent_changes` {"service": "object-storage", "window": "24h"}
- `list_recent_changes` {"service": "", "window": "24h"}
- `get_metrics` {"service": "object-storage", "metric": "read_success_ratio"}
- `get_logs` {"service": "object-storage", "level": "ERROR"}
- `query_ops_audit` {"host": "", "window": "24h"}
- `get_logs` {"service": "index-service"}
- `get_logs` {"service": "object-storage", "level": "ERROR"}
- `submit_diagnosis` {}

**根因判定**：容量回收操作 CHG-1102 执行偏差：capacity-team 的 dave 在 capacity-cli-01 上执行 remove-capacity --playbook billing --min-available 40 --count 2，实际移除的 index/placement 子系统容量远超预期，导致 object-storage 的下游 index-service 与 placement-service 同时不可用，写入路径无法定位分区元数据，读写成功率断崖式下跌，并波及计算、块存储、监控等上层服务。

**排查链**：
- [确认影响面与依赖] object-storage 无上游，下游为 index-service 与 placement-service，二者是写入/索引的关键依赖
- [确认故障时间线与指标恶化] write_success_ratio 从 0.999 跌至 0.62→0.11→0.08→0.09；read_success_ratio 从 0.999 跌至 0.71→0.22→0.19；index_service_available 与 placement_service_available 均由 1 变 0
- [关联变更与运维操作] 24h 内 object-storage 无变更，但全局有 CHG-1102 容量回收；审计显示 dave 执行 remove-capacity 时 removed far more than intended，时间 12:37 与故障起点吻合
- [日志佐证因果链] object-storage 错误日志明确指向容量移除后 index 无响应、placement 容量不足、写入无法定位分区元数据，最终两者均不可用

**不确定项**：未直接查看 index-service/placement-service 的日志（该服务无日志，仅有 object-storage 侧记录），其内部具体恢复状态需现场确认；未确认被误删容量的具体规模与是否可在线回补，恢复时长不确定；billing-subsystem 计划下线与本次 index/placement 误删的关联性未完全排除（同一 ticket CHG-1102 覆盖 billing playbook，但 target 写的是 index,placement）

#### C 喂全证据 —— 4/4（命中 4/4 个决定性步骤）　｜　LLM 评审：4/4（四步全部命中：先定位到 remove-capacity 误操作，区分 index 与 placement 两个子系统，指出从未冷启动带来的恢复耗时风险，并梳理了 compute/block-storage 等上层级联依赖。）

**根因判定**：容量回收操作 remove-capacity 误删了远超预期的节点，导致 object-storage 的 index-service 与 placement-service 两个有状态副本集被整体移除（replicas 从 12/8 变为 0），且这两个子系统自启动以来从未冷启动过，无法自动恢复，进而使对象存储写路径无法定位分区元数据、索引与放置服务不可用，引发上层计算、块存储、监控等依赖服务大面积报错。

**排查链**：
- [容量回收操作执行] 运维审计显示 dave 执行 remove-capacity 回收 billing 容量，结果 removed far more than intended
- [误删超出计划] billing 日志确认移除节点数超过计划
- [index/placement 副本归零] 资源显示 index-service 期望 12 实际 0，placement-service 期望 8 实际 0，均因容量回收被移除
- [对象存储内部报错] index 服务在容量移除后无响应，placement 容量不足无法分配分区，写路径无法定位分区元数据
- [可用性指标崩塌] index_service_available 与 placement_service_available 由 1 变 0，写成功率由 0.999 跌至 0.08，读成功率跌至 0.19
- [无法自愈] 日志提示这些子系统自启动以来从未完全重启过，缺乏冷启动恢复能力
- [上层服务级联失败] compute-service 与 block-storage 的 api_error_ratio 从 0.001 飙升至 0.44/0.71 与 0.38/0.66，compute 日志明确依赖 object-storage 失败

**不确定项**：remove-capacity 具体为何删除超出 count 2 的节点（playbook 逻辑缺陷或参数解析问题）无法从现有证据确认；index-service 与 placement-service 是否与 billing 节点共享同一容量池/调度域，导致被一并移除，证据未直接说明；console-ui v4.2 发布与控制台变慢是否存在关联，现有证据不足以判定，倾向为噪声；billing-subsystem 剩余 4 副本是否已低于最小可用阈值，需进一步确认

### zephyr-quota-cascade

- **症状（模型只看到这个）**：订单履约服务的异步任务队列持续积压，履约延迟从 2 分钟涨到 40 分钟以上。上游下单接口成功率下降到 71%。相关团队说他们没做任何发布。
- **真实根因（模型看不到）**：合作伙伴的接入网关在 14:05 推送了一次「限流配额调整」（把每秒允许的请求从 500 提到 5000，是他们自己的促销预案）。这次调整经过了三层网关，但第二层网关的配额缓存 TTL 是 30 分钟，导致两层网关看到的配额不一致：外层的 5000 与内层的 500 冲突，内层把超出 500 的部分静默排队而不是拒绝，队列因此无界增长，最终把 worker 的内存打满并触发 GC 风暴。根因是「两层网关的配额缓存 TTL 不一致」，不是配额本身。

**决定性步骤（跑前固定）**：
1. 发现积压的起点与合作伙伴的配额调整时间吻合（14:05）
2. 识别出这不是我方发布引起的（排除我方的发布/变更）
3. 发现两层网关的配额值不一致（外层 5000 / 内层 500）
4. 识别出静默排队（而非拒绝）是无界增长的机制，以及缓存 TTL 差异是根因

#### A 单轮基线 —— 0/4（命中 0/4 个决定性步骤）　｜　LLM 评审：2/4（仅命中排除我方发布这一步；未识别14:05配额调整时间吻合、两层网关配额值不一致及静默排队+TTL差异根因，反而误判为下游阻塞/消费能力下降。）

**根因判定**：fulfill-worker 消费能力骤降或下游依赖阻塞，导致异步任务队列积压；积压进一步占满 worker 线程/连接池，使上游下单接口同步调用履约服务时超时失败，成功率降至 71%。最可能的具体诱因是 fulfill-worker 依赖的下游（数据库、库存/仓储/物流等外部接口）变慢或连接池耗尽，或 worker 实例/消费线程异常减少（如 OOM、重启、被限流），而非相关团队自身发布。

**排查链**：
- [确认积压形态与时间线] 队列积压从某时刻起单调上升、延迟从 2 分钟涨到 40 分钟，说明消费速率持续低于生产速率，属于消费侧或下游阻塞，而非瞬时流量尖峰（否则会自愈）。
- [区分生产突增 vs 消费下降] 上游下单成功率下降到 71%，若为流量突增，下单量应上升；成功率下降更可能是履约同步调用被拖慢/超时，反证问题在 fulfill-worker 侧而非上游放量。
- [检查 fulfill-worker 实例与消费线程健康] 推断存在实例重启、OOM、消费线程卡死、连接池/线程池耗尽或消费者被限流，导致有效消费并发下降。
- [检查 fulfill-worker 下游依赖] 最可能根因是下游依赖（DB 慢查询/锁、库存或物流外部接口超时、消息中间件异常）响应变慢，worker 阻塞在 I/O 上，队列积压。
- [排查近期变更与配置] 相关团队称无发布，但需怀疑配置变更、依赖方发布、中间件扩缩容、证书/密钥过期、限流阈值调整、DNS 或网络策略变更等非本服务发布类变更。
- [关联上游失败原因] 上游下单接口成功率 71% 很可能因同步调用履约服务超时/熔断触发，属于积压的次生影响，而非独立故障。

**不确定项**：具体是哪个下游依赖阻塞（数据库、库存、物流外部接口或消息中间件）无法确认；fulfill-worker 是否存在实例重启/OOM/线程池耗尽等运行时异常无法确认；是否有非发布类变更（配置、依赖方发布、中间件扩缩容、证书/网络策略）无法确认；上游下单成功率下降与履约超时的因果方向需链路追踪确认

#### B 工具自主 —— 4/4（命中 3/4 个决定性步骤）　｜　LLM 评审：3/4（步骤1、2命中（积压与14:05配额调整吻合、排除我方发布），但步骤3未识别两层网关配额值不一致（输出称l1/l2先后升至5000，未指出外层5000/内层500冲突），步骤4未识别缓存TTL差异为根因，仅归因于配额提升导致流量激增。）

**工具调用链（14 次）**：
- `list_recent_changes` {"service": "fulfill-worker", "window": "7d"}
- `list_recent_changes` {"service": "", "window": "24h"}
- `get_topology` {"service": "fulfill-worker"}
- `get_metrics` {"service": "fulfill-worker", "metric": ""}
- `get_metrics` {"service": "fulfill-worker", "metric": "cpu"}
- `get_metrics` {"service": "fulfill-worker", "metric": "heap"}
- `get_metrics` {"service": "fulfill-worker", "metric": "gc"}
- `get_metrics` {"service": "fulfill-worker", "metric": "queue_depth"}
- `get_metrics` {"service": "", "metric": "quota"}
- `get_metrics` {"service": "", "metric": "success_ratio"}
- `get_logs` {"service": "fulfill-worker", "level": "ERROR"}
- `get_logs` {"service": "fulfill-worker", "level": "WARN"}
- `get_metrics` {"service": "", "metric": "requests_over_quota"}
- `submit_diagnosis` {}

**根因判定**：合作伙伴接入网关配额被临时从 500 提升到 5000（ticket EXT-2201，partner-acme-gateway 促销预案），导致 ingress-gateway-l2 上游流量激增；超出原配额的请求被静默排队（requests_over_quota_silently_queued 从 0 涨到 94000），大量请求涌入 fulfill-worker，使其消费队列积压、堆内存打满并触发持续 Full GC，吞吐崩溃，进而拖累 order-api 成功率下降至 71%。

**排查链**：
- [确认影响面与依赖] fulfill-worker 上游为 ingress-gateway-l2，下游为 fulfill-db；order-api 成功率同步下滑，说明问题在入口流量侧而非 fulfill-worker 自身发布
- [排查近期变更] fulfill-worker 自身 7d 内无变更；全局 24h 内唯一相关变更是 partner-acme-gateway 接入网关配额 500->5000（EXT-2201），与相关团队“没做发布”的说法一致（是配置变更而非发布）
- [验证配额变更与超限排队] ingress-gateway-l1/l2 配额先后升至 5000，l2 超配额静默排队请求从 0 暴增至 94000，证明入口放量后大量请求被排队灌入下游
- [确认 fulfill-worker 过载表现] 队列深度从 120 暴涨至 210000，延迟 p99 从 2.1 分钟升至 41 分钟，堆使用率 42%->99%，GC 时间占比 3%->88%，日志出现 Full GC pause 4.2s 与吞吐崩溃

**不确定项**：未直接查看 ingress-gateway-l2 与 fulfill-worker 的 pod/节点资源详情，无法确认是否存在节点级 CPU/内存瓶颈叠加；未确认 fulfill-db 是否也因流量激增出现慢查询，可能进一步放大积压；配额变更与队列积压的时间先后仅由指标采样点推断，未取得精确到秒的变更生效时间

#### C 喂全证据 —— 3/4（命中 2/4 个决定性步骤）　｜　LLM 评审：4/4（四步全部命中：时间吻合、排除我方发布、识别两层配额不一致、定位静默排队机制与TTL差异根因。）

**根因判定**：ingress-gateway-l2 的配额缓存 TTL=1800s 导致配额变更（500→5000）在 L2 侧延迟 30 分钟才生效；期间 L1 已按新配额放行约 4800/s 流量，而 L2 仍按旧配额 500 处理，且对超配额请求采取静默排队而非拒绝，形成巨大内部积压并向下游 fulfill-worker 倾泻，worker 无背压限制、消费能力不足导致队列暴涨、堆内存打满、Full GC 频繁、吞吐崩溃，最终 order-api 履约入队超时、下单成功率跌至 71%。

**排查链**：
- [配额变更下发] 14:05 partner-acme-gateway 将配额从 500 提升到 5000，L1 立即刷新缓存生效
- [L2 缓存未失效] L2 收到更新但因 TTL=1800s 继续使用旧缓存值 500
- [L1 放行超量流量] L1 按新配额放行约 4800/s，远超 L2 实际生效的 500 配额
- [L2 静默排队放大积压] L2 对超配额请求不拒绝而是排队，内部队列持续增长
- [下游 worker 积压与资源耗尽] fulfill-worker 消费滞后从 2100 涨到 18 万级，堆内存升至 99%，Full GC 频繁，吞吐崩溃
- [上游下单失败] order-api 履约入队超时，成功率降至 71%
- [缓存过期后恢复一致] 14:35 L2 缓存过期才加载新配额 5000，此时积压已造成

**不确定项**：L2 内部队列的具体容量与排队策略实现细节未知；fulfill-worker 是否在积压前已接近容量上限（无历史基线）；search-api 发布、报表库索引重建、jstack GC 线程数等证据与本次故障的关联性无法确认，判定为噪声；L1 与 L2 之间配额语义（advertised quota）的具体设计文档未提供
