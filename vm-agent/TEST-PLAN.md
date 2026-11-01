# 盲测方案：AIOps 平台故障研判能力测试

> **为什么要盲测**：故障由我们注入，我们知道标准答案；但平台**只能看到症状**（应用日志事件），
> 永远看不到标准答案。评分由固定 rubric 事后打分，平台原始输出逐字记录——这就是安全领域的盲测方法，
> 避免"我知道答案所以觉得它准"的主观偏差。
>
> **面试话术**："我没有只测'我构造的故障'，而是设计了跨 8 层的故障矩阵，平台只见症状不见答案，
> 用固定评分表事后打分；规则研判与 LLM 研判跑同一矩阵做 A/B。"

## 一、测试矩阵（8 场景 × 全运维层级）

| ID | 层级 | 故障 | 注入动作 | 平台可见的症状（唯一输入） | 标准答案（隐藏，仅评分用） |
|---|---|---|---|---|---|
| S1 | 应用层 | 支付回调超时 | 写 12 条 ERROR | business_log：payment callback timeout ×12 | 下游依赖 dep-payment 超时 |
| S2 | 系统资源-磁盘 | /tmp 写满 1G | dd 气球 120s 自愈 | 3 条 WARN disk usage >85% | 磁盘空间耗尽 |
| S3 | 系统资源-CPU | 单核打满 60s | while 循环 | 1 条 ERROR healthz probe timeout | CPU 饱和导致探针超时 |
| S4 | K8s | 镜像不存在 CrashLoopBackOff | kubectl 部署坏镜像 90s 自愈 | 3 条 ERROR pod CrashLoopBackOff restarts=5 | 镜像 tag 不存在 |
| S5 | 服务状态 | payment-api 宕机 | systemctl stop，60s 自愈 | 3 条 ERROR connection refused 127.0.0.1:8080 | 业务服务进程死亡 |
| S6 | 网络-DNS | 解析失败 | resolv.conf 换坏 DNS，60s 自愈 | 1 条 ERROR getaddrinfo failed | DNS 配置错误 |
| S7 | 配置-权限 | 配置读不了 | chmod 000 配置后重启失败，自愈 | 1 条 ERROR permission denied 启动失败 | 配置文件权限错误 |
| S8 | 依赖-下游 | 下游端口拒绝 | 假下游起后即杀 | 1 条 ERROR ECONNREFUSED 8081 | 下游依赖端口拒绝 |

每个场景：**真实故障 + 真实应用日志**（日志即该故障下真实应用会打的内容），全部**自动恢复**（60-120s），可反复跑。

## 二、评分 Rubric（每场景满分 3）

| 得分 | 标准 |
|---|---|
| 3 | 根因命中（推断/建议指向标准答案的方向，如"依赖超时/下游拒绝/磁盘满"） |
| 2 | 部分命中（提到正确组件或正确现象类别，但结论含糊） |
| 1 | 方向相关但归因错误（如把 DNS 故障归因为"网络波动"以外的错层） |
| 0 | 完全偏离，或只有"无法确认" |

记录要求：每个场景的 `verdict`（known/inferred/uncertain/recommendation）**逐字记录**到
`TEST-RESULTS.md`，不允许改写。

## 三、执行协议（每场景）

1. **注入**：`vm-agent/scenarios.sh S<n>`（在 Server2 执行）
2. **等上报**：探针 10s 窗口阈值 3 条 → 大盘/`/api/alerts` 出现该场景告警
3. **研判**：点「⚡ 送研判主链路」（或 POST `/api/research`）→ 拿到 verdict
4. **记录**：verdict 逐字 + 时间 + run_id
5. **评分**：对照上表打分，写进 TEST-RESULTS.md
6. **恢复确认**：120s 后确认自愈（探针日志/服务状态）

## 四、A/B 实验（核心亮点）

同一矩阵跑两个大脑：
- **A = 规则兜底**（当前默认，零依赖）：先跑，得到基线分
- **B = 真 LLM**（配 `LLM_BASE_URL/API_KEY/MODEL`，如 DeepSeek/通义/本地 27B）：再跑，对比提升

对比结论直接写简历：**"跨 8 层故障矩阵盲测：规则研判 X/24，接入 LLM 后 Y/24，主要提升在 Z 类故障的归因精度"**。

## 五、已知边界（诚实声明，也是测试发现）

- 探针当前只 tail 应用日志（`/var/log/demo-app.log`）——**没有指标源**（Prometheus/Node Exporter 未接），
  所以纯资源类故障（如只有 CPU 高、无日志）平台只能输出"无法确认"——这是**正确的边界行为**，
  测试中如实记录为 0/1 分并说明原因，不粉饰。
- 接指标源是后续路线图（夜莺/Keep/Prometheus → `/api/ingest`）。
