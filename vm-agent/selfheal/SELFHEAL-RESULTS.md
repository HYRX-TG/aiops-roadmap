# 自愈闭环实测（第四轮）：真的注入故障，看平台能不能真的修好

后端：http://127.0.0.1:8811　服务：sandbox-payment　时间：2026-10-25 16:43:31

## 一句话结论

**4/4 个真实故障被真正修复**（其中 2 个是全自动、2 个经人工审批放行后修复）。
这里的"修好"不是平台自己宣称的：是独立的健康探针（`GET /healthz`）从 500 变回 200，
且探针检查的是**真实状态**——配置文件是否合法 JSON、临时目录是否超配额、
固定规模计算的墙钟耗时是否回到基线。

## 逐场景结果

| 场景 | 故障生效 | 命中剧本 | 平台动作 | 是否需审批 | agent 执行 | 探针恢复 | 耗时 | 结果 |
|---|---|---|---|---|---|---|---|---|
| S1 CPU 被吵闹邻居抢占 | ✅ | resource_contention | kill_noisy_neighbor | 需审批（已放行） | ✅ | ✅ 200 | 3.19s | **已自愈** |
| S2 临时目录被气球文件撑爆（磁盘写满） | ✅ | disk_pressure | cleanup_temp_files | 全自动 | ✅ | ✅ 200 | 1.47s | **已自愈** |
| S3 运维操作改坏配置（有操作审计） | ✅ | ops_change_incident | restore_config_from_backup | 全自动 | ✅ | ✅ 200 | 2.0s | **已自愈** |
| S4 服务进程被杀（OOM） | ✅ | oom_killed | restart_service | 需审批（已放行） | ✅ | ✅ 200 | 6.04s | **已自愈** |

## 分阶段耗时（MTTR 拆解）

| 场景 | 故障生效 | 诊断 | 审批 | 执行+验证 | 端到端 |
|---|---|---|---|---|---|
| S1 | 2.84s | 0.25s | 0.02s | 0.04s | **3.19s** |
| S2 | 0.6s | 0.24s | -s | 0.05s | **1.47s** |
| S3 | 0.05s | 0.24s | -s | 0.06s | **2.0s** |
| S4 | 1.06s | 0.24s | 0.03s | 2.55s | **6.04s** |

## 每个场景到底发生了什么

### S1 CPU 被吵闹邻居抢占
- 注入：启动 8 个 CPU hog（PID [17816, 24544, 44176]…，90s 后自愈退出）
- 故障确认：`healthz HTTP 500 —— config=ok; tempdir=ok; cpu=固定计算墙钟 28ms / CPU 时间 = 抢占比 1.79× （> 1.35×，CPU 被抢占）`
- 平台诊断：剧本 `resource_contention` → 护栏动作 `scale_up` → 计划状态 `pending_approval`
- 人工审批：已放行执行，下单 1 个白名单动作（节点侧 agent 执行+验证）
- agent 执行 `kill_noisy_neighbor`：已终止 PID [17816, 24544, 44176, 32732, 36516, 31044, 15932, 8068]（共 8 个记录）
  - 验证探针（process_gone）：通过 —— PID [17816, 24544, 44176, 32732, 36516, 31044, 15932, 8068] 全部已终止
  - 引擎判定：`fixed`
- 最终探针：`healthz 200 —— config=ok; tempdir=ok; cpu=ok`

### S2 临时目录被气球文件撑爆（磁盘写满）
- 注入：写入 6 个气球文件共 96MB（配额 64.0MB）
- 故障确认：`healthz HTTP 500 —— config=ok; tempdir=ok; cpu=固定计算墙钟 24ms / CPU 时间 = 抢占比 1.52× （> 1.35×，CPU 被抢占）`
- 平台诊断：剧本 `disk_pressure` → 护栏动作 `unclassified` → 计划状态 `pending_approval`
- agent 执行 `cleanup_temp_files`：删除 6 个临时文件，释放 96.0MB：['balloon_1.dat', 'balloon_2.dat', 'balloon_3.dat', 'balloon_4.dat', 'balloon_5.dat']
  - 验证探针（disk_below_pct）：通过 —— 临时目录 0.0MB = 配额 0%（阈值 90%）
  - 引擎判定：`fixed`
- 最终探针：`healthz 200 —— config=ok; tempdir=ok; cpu=ok`

### S3 运维操作改坏配置（有操作审计）
- 注入：把 config.json 改成非法 JSON（模拟配置变更事故）
- 故障确认：`healthz HTTP 500 —— config=ok; tempdir=ok; cpu=固定计算墙钟 23ms / CPU 时间 = 抢占比 1.47× （> 1.35×，CPU 被抢占）`
- 平台诊断：剧本 `ops_change_incident` → 护栏动作 `unclassified` → 计划状态 `pending_approval`
- agent 执行 `restore_config_from_backup`：已从 config.json.bak 恢复配置（原坏配置另存为 config.json.broken）
  - 验证探针（http_probe）：通过 —— healthz 200 —— config=ok; tempdir=ok; cpu=ok
  - 引擎判定：`fixed`
- 最终探针：`healthz 200 —— config=ok; tempdir=ok; cpu=ok`

### S4 服务进程被杀（OOM）
- 注入：杀掉服务进程 PID 36124
- 故障确认：`healthz HTTP 500 —— config=ok; tempdir=ok; cpu=固定计算墙钟 24ms / CPU 时间 = 抢占比 1.53× （> 1.35×，CPU 被抢占）`
- 平台诊断：剧本 `oom_killed` → 护栏动作 `unclassified` → 计划状态 `pending_approval`
- 人工审批：已放行执行，下单 1 个白名单动作（节点侧 agent 执行+验证）
- agent 执行 `restart_service`：已重新拉起服务（PID 54948）
  - 验证探针（http_probe）：通过 —— healthz 200 —— config=ok; tempdir=ok; cpu=ok
  - 引擎判定：`fixed`
- 最终探针：`healthz 200 —— config=ok; tempdir=ok; cpu=ok`


## 口径修订（2026-10-25，护栏接通后）

自愈引擎现在**必须先过护栏**才能自动下单，判定依据是动作登记表里的
`tier` 与 `blast_radius`（默认策略：`auto_max_tier=2`、`auto_max_blast=pod`）：

| 动作 | tier | 爆炸半径 | 默认是否可自动 | 原因 |
|---|---|---|---|---|
| cleanup_temp_files | 1 | pod | ✅ 可自动 | 只清自己的临时目录 |
| restore_config_from_backup | 2 | pod | ✅ 可自动 | 有备份、可逆、pod 级 |
| kill_noisy_neighbor | 2 | **node** | ❌ 需审批 | 会终止同节点上其他进程（可能是别人的业务） |
| restart_service | **3** | pod | ❌ 需审批 | 重启会中断在途请求 |

所以 S1、S4 从"全自动"变成"需人工审批"。**这不是退步，是把之前被低估的风险摆到台面上**：
上一版把"杀吵闹邻居进程"当成 A 类全自动，但它的爆炸半径其实是整个节点。

如需放宽（例如单机自建、确认节点上只有自己的服务），显式设置：
`AIOPS_REMEDIATION_AUTO_MAX_TIER=3 AIOPS_REMEDIATION_AUTO_MAX_BLAST=node`。
**注意**：护栏自身的 `blast_radius_max` 是硬顶，自动策略不能突破它。

## 诚实说明（这一轮里哪些不是真的）

1. **CPU 抢占的判据是「抢占比 = 墙钟时间 / 本进程 CPU 时间」**，不是读 cgroup 配额。进程被挤下 CPU 时墙钟在走而 CPU 时间不涨，比值就上升（实测空闲 ≈1.0×，注入 8 个 hog 后 1.76×）。它不依赖核数和启动基线，比"跟基线比"更本质，但仍然只是**间接指标**——生产里应该看 cgroup cpu.stat 的 throttling 计数。
2. **磁盘写满用"目录配额"模拟**（写气球文件把临时目录撑过配额），没有真的把某个分区写满——真写满分区在本机风险太大。检测与清理逻辑和真实磁盘写满场景是一致的（找大头 → 清安全的文件 → 验证水位）。
3. **沙箱里的"版本"就是配置文件**，所以 rollback_version 的实现与restore_config 相同；生产里版本回滚走 rollout undo。
4. **生产对应动作与沙箱动作不等价**：沙箱里"终止失控进程"，生产里对应的是"给吵闹邻居设 CPU Limit"（不杀对方进程）——沙箱用更激进的等价动作，是因为单机沙箱没有 cgroup。
5. **审批是我们代履行的**：S4 里平台按设计拒绝自动重启（OOM 重启只是缓解、不解决根因），由脚本扮演值班工程师放行。
