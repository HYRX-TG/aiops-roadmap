# 动态环境实测：真实系统故障，模型自主排查

- 模型：`deepseek-chat`　时间：2026-10-25 17:14
- 总调用：29 次 · tokens in/out = 23316/4389

**评分口径**：必须定位到真实根因（must 命中）+ 不能判错方向（forbid 不命中）。只数关键词的旧口径会把"说对了几个词但方向错了"算成正确——已废弃。

## 结果

| 场景 | 故障是否真发生 | 真实根因 | 模型结论 | 得分 | 工具数 |
|---|---|---|---|---|---|
| D1 CPU 被外部进程抢占 | ✅ | 隔壁团队的批处理进程占满了 CPU，导致服务被挤下 CPU | 批处理任务（PID 34044/43696/42716）被绑定到同一 CPU 核，与 sandbox-app 争抢 CPU，导致服务健康检查 | **4/4** | 9 |
| D2 临时目录被撑爆 | ✅ | ETL 任务往临时目录写了大量中间文件，超过配额 | etl-job 于 2026-10-25 17:13:08 向 sandbox-app 临时目录写入 6 个 balloon_*.dat 中 | **4/4** | 8 |
| D3 配置被手工改坏 | ✅ | 运维手工编辑 config.json 时写坏 JSON 语法 | 运维人员手工编辑 config.json 时未走变更单、未做语法校验，写入内容被破坏（第3行出现 "upstream": "http,"mo | **4/4** | 7 |
| D4 服务进程被杀 | ✅ | 服务进程被 OOM killer 杀掉 | sandbox-app 服务进程（PID 55596）被 OOM killer 终止，导致端口 8099 无监听、健康探测不可达；日志文件缺 | **4/4** | 8 |

**总分 16/16**（只统计故障真实生效的场景 4/4 个）

## 逐场景详情

### D1 CPU 被外部进程抢占

- 注入：启动 3 个 CPU 密集型进程，与沙箱服务绑定同一核（沙箱绑定成功）
- 真实根因：隔壁团队的批处理进程占满了 CPU，导致服务被挤下 CPU
- 故障验证：抢占比 8.92×（阈值 1.35×）
- 工具调用链（9 次）：get_service_health → list_processes → get_recent_changes → get_logs → run_readonly → run_readonly → run_readonly → run_readonly → submit_diagnosis
- 得分：4/4（根因正确，推理链 4 条）
- 模型根因：批处理任务（PID 34044/43696/42716）被绑定到同一 CPU 核，与 sandbox-app 争抢 CPU，导致服务健康检查中 CPU 抢占比达 4.25×（>1.35× 阈值），响应变慢、自检返回 HTTP 500

### D2 临时目录被撑爆

- 注入：向临时目录写入 96MB 临时文件
- 真实根因：ETL 任务往临时目录写了大量中间文件，超过配额
- 故障验证：临时目录 96.0MB / 配额 64.0MB
- 工具调用链（8 次）：get_service_health → get_disk_usage → get_recent_changes → get_logs → check_config → run_readonly → list_processes → submit_diagnosis
- 得分：4/4（根因正确，推理链 6 条）
- 模型根因：etl-job 于 2026-10-25 17:13:08 向 sandbox-app 临时目录写入 6 个 balloon_*.dat 中间文件共 96MB，超过配置配额 64MB（占用 150%），导致健康检查 tempdir 项失败并返回 HTTP 500

### D3 配置被手工改坏

- 注入：把 config.json 改成非法 JSON
- 真实根因：运维手工编辑 config.json 时写坏 JSON 语法
- 故障验证：配置 JSON 校验结果
- 工具调用链（7 次）：get_service_health → check_config → get_recent_changes → get_logs → run_readonly → get_disk_usage → submit_diagnosis
- 得分：4/4（根因正确，推理链 6 条）
- 模型根因：运维人员手工编辑 config.json 时未走变更单、未做语法校验，写入内容被破坏（第3行出现 "upstream": "http,"mode":"MAINTENANCE-BAD"[[ 等非法片段），导致 JSON 解析失败（Expecting ',' delimiter: line 3 column 22），服务自检 config 检查不通过，健康检查返回 HTTP 500。

### D4 服务进程被杀

- 注入：终止监听 :8099 的服务进程（PID [55596]）
- 真实根因：服务进程被 OOM killer 杀掉
- 故障验证：不可达（进程可能已死）：URLError；剩余监听进程=[]
- 工具调用链（8 次）：get_service_health → list_processes → get_logs → check_config → get_recent_changes → run_readonly → run_readonly → submit_diagnosis
- 得分：4/4（根因正确，推理链 5 条）
- 模型根因：sandbox-app 服务进程（PID 55596）被 OOM killer 终止，导致端口 8099 无监听、健康探测不可达；日志文件缺失与进程死亡一致。
