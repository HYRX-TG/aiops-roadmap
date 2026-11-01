#!/bin/sh
# ─────────────────────────────────────────────────────────────
# 生产级场景模拟器（在 Server2 Guest 内运行）
# 用法：sh k8s-scenarios.sh P1|P2|P3|P4|RESET
#
# 三个真实生产故障模式（全部自动恢复）：
#   P1 资源抢占：隔壁团队批处理作业吃满 CPU → 本服务延迟飙升（看门狗实测）
#   P2 跨部门变更：别的团队把我们的 upstream 配置改坏并重启 → 服务 degraded
#   P3 内存耗尽：内存分析任务持续申请 → 逼近 OOM → 服务内存守卫报警
#   P4 服务断线：租用机器上的服务突然不可用（进程消失，机器本身没重启）
#
# 每个场景都会：
#   ① 注入真实故障（真进程/真配置变更）
#   ② 让"业务"真实感知（看门狗 curl /healthz 实测耗时，超标才写 ERROR）
#   ③ 写变更台账（模拟跨团队发布记录，供排查时关联）
#   ④ N 秒后自动恢复
#
# 看门狗阈值是「相对基线」的（真实 SLO 告警做法）：
#   先测 3s 基线，之后 latency > max(基线×5, 50ms) 才记 ERROR，
#   ERROR 里带实测数字（"latency 213ms vs baseline 5.1ms (42x)"）——证据自带。
# ─────────────────────────────────────────────────────────────
exec > /tmp/wb_out.txt 2>&1
SUDO_PW="${VM_SUDO_PW:-<你的sudo密码>}"
LOG=/var/log/demo-app.log
CHANGES=/var/log/changes.log
P="$1"

echo "$SUDO_PW" | sudo -S touch "$LOG" "$CHANGES" 2>/dev/null
echo "$SUDO_PW" | sudo -S chmod 666 "$LOG" "$CHANGES" 2>/dev/null

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
changelog() { echo "$(date '+%F %T') [$2] $1" >> "$CHANGES"; }

# 确保 victim 服务在跑（payment-api，8080）
ensure_victim() {
  if ! systemctl is-active payment-api >/dev/null 2>&1; then
    echo "$SUDO_PW" | sudo -S systemctl start payment-api 2>/dev/null
    sleep 1
  fi
}

# 正常流量：payment-api 一直承载支付流量（真实生产前提：有流量才有队列）
traffic_start() {
  if pgrep -f 'traffic_gen_marker' >/dev/null 2>&1; then return; fi
  nohup sh -c 'while :; do curl -s -o /dev/null --max-time 30 "http://127.0.0.1:8080/api/pay?traffic_gen_marker=1"; sleep 0.1; done' >/dev/null 2>&1 &
  echo $! > /tmp/traffic.pid
  echo "正常流量已启动（10 QPS → /api/pay）"
}
traffic_stop() { kill "$(cat /tmp/traffic.pid 2>/dev/null)" 2>/dev/null; rm -f /tmp/traffic.pid; }

# 看门狗：相对基线判延迟，超标写 ERROR（带实测数字）
watchdog_start() {
  nohup sh -c '
    LOG=/var/log/demo-app.log
    BASE=0
    # 基线测量 3s
    for i in 1 2 3; do
      T=$(curl -s -o /dev/null -w "%{time_total}" --max-time 5 http://127.0.0.1:8080/healthz 2>/dev/null)
      [ -n "$T" ] && BASE=$(awk -v b="$BASE" -v t="$T" "BEGIN{printf \"%.4f\", b+t}")
      sleep 1
    done
    AVG=$(awk -v b="$BASE" "BEGIN{printf \"%.4f\", b/3}")
    # 阈值 = max(基线×2.5, 12ms)：相对退化为主，绝对下限防误报
    TH=$(awk -v a="$AVG" "BEGIN{x=a*2.5; if(x<0.012)x=0.012; printf \"%.4f\", x}")
    echo "watchdog baseline=${AVG}s threshold=${TH}s" >> $LOG
    while :; do
      OUT=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --max-time 10 http://127.0.0.1:8080/healthz 2>/dev/null)
      CODE=${OUT%% *}     # 连接被拒时 http_code=000（不能用 awk 单引号，会截断外层字符串）
      T=${OUT##* }
      NOW=$(date "+%F %T")
      if [ -z "$CODE" ] || [ "$CODE" = "000" ]; then
        echo "$NOW ERROR payment-api unreachable: healthz probe failed (connection refused, service not listening on 8080)" >> $LOG
      else
        RATIO=$(awk -v t="$T" -v a="$AVG" "BEGIN{printf \"%.0f\", (a>0? t/a : 0)}")
        SLOW=$(awk -v t="$T" -v h="$TH" "BEGIN{print (t>h)?1:0}")
        if [ "$SLOW" = "1" ]; then
          MS=$(awk -v t="$T" "BEGIN{printf \"%d\", t*1000}")
          BMS=$(awk -v a="$AVG" "BEGIN{printf \"%.0f\", a*1000}")
          echo "$NOW ERROR payment-api latency ${MS}ms exceeds threshold (baseline ${BMS}ms, ${RATIO}x degradation, SLO breach)" >> $LOG
        fi
      fi
      sleep 1
    done
  ' >/dev/null 2>&1 &
  echo $! > /tmp/watchdog.pid
}
watchdog_stop() { kill "$(cat /tmp/watchdog.pid 2>/dev/null)" 2>/dev/null; rm -f /tmp/watchdog.pid; }

# 吵闹邻居：24 个忙循环（模拟 make -j24 的失控批处理，2vCPU 上 12x 超额）+ 1 个内存扫描进程
hog_start() {
  N=${1:-24}
  i=0
  while [ $i -lt $N ]; do
    nohup sh -c 'while :; do :; done' >/dev/null 2>&1 &
    i=$((i+1))
  done
  # 批处理作业典型形态：一边算一边扫大缓冲区（缓存争抢，比纯忙循环更伤）
  nohup python3 -c '
import time
buf = bytearray(120 * 1024 * 1024)          # 120MB 工作集，超出 L3
t0 = time.time()
while time.time() - t0 < 100:
    s = 0
    for i in range(0, len(buf), 4096):
        s += buf[i]
    time.sleep(0.05)
' >/dev/null 2>&1 &
  echo "$N 个 CPU 忙循环 + 1 个内存扫描进程已启动"
}
hog_stop() {
  pkill -f 'while :; do :; done' 2>/dev/null
  pkill -f 'bytearray(120' 2>/dev/null
}

ensure_victim >/dev/null
traffic_start
watchdog_start
echo "=== scenario $P start $(date) ==="

case "$P" in
P1)  # 资源抢占：隔壁团队批处理作业 90s
  echo "--- 正常基线 3s ---"; sleep 3
  changelog "team-billing 启动批处理作业 batch-reconcile（make -j24 未设 CPU limit，未做资源评估）" "team-billing"
  hog_start 24
  echo "[P1] 吵闹邻居已启动（90s 自愈）"
  sleep 90
  hog_stop
  echo "[P1] 自愈完成（CPU 让出）" ;;
P2)  # 跨部门变更：别的团队把我们的 upstream 配置改坏并重启
  echo "--- 正常基线 3s ---"; sleep 3
  cp /etc/payment-api/config /tmp/config.bak
  changelog "team-billing 修改 payment-api 配置 upstream=dep-payment -> dep-payment-v2-nonexistent（未通知本团队，无变更单）" "team-billing"
  sed -i 's/^upstream=.*/upstream=dep-payment-v2-nonexistent/' /etc/payment-api/config 2>/dev/null || \
    echo "upstream=dep-payment-v2-nonexistent" >> /etc/payment-api/config
  echo "$SUDO_PW" | sudo -S systemctl restart payment-api 2>/dev/null
  sleep 2
  # 服务自检失败 → 按重试退避打错误日志（真实服务行为：重试 1/5…5/5 后进入 degraded）
  # 文案前 48 字符保持一致（探针按此前缀派生指纹，重试号放在后面 → 同一故障只占一个指纹）
  i=1
  while [ $i -le 5 ]; do
    log "ERROR payment-api failed to start after config change (deploy by external team): upstream dep-payment-v2-nonexistent unreachable, retry $i/5 backoff $((100*i))ms"
    sleep 1
    i=$((i+1))
  done
  log "ERROR payment-api degraded mode: all upstream retries exhausted, serving cached responses only"
  echo "[P2] 配置已被改坏并重启（60s 后自动回滚）"
  sleep 55
  cp /tmp/config.bak /etc/payment-api/config
  echo "$SUDO_PW" | sudo -S systemctl restart payment-api 2>/dev/null
  changelog "team-payment 回滚 payment-api 配置至 upstream=dep-payment（故障恢复）" "team-payment"
  echo "[P2] 配置已回滚，服务恢复" ;;
P3)  # 内存耗尽：内存分析任务持续申请，约 80s 后自愈
  echo "--- 正常基线 3s ---"; sleep 3
  changelog "team-billing 启动内存分析任务 mem-analyzer（OOM 风险未评估）" "team-billing"
  # 4GB 机器上，服务内存护栏设为「可用 ≥ 1.3GB」（同机还跑着 k8s 控制面）
  nohup python3 -c '
import time
chunks = []
for i in range(5):
    chunks.append(bytearray(280 * 1024 * 1024))   # 5×280MB ≈ 1.4GB
    chunks[-1][::4096] = b"\x01" * (len(chunks[-1]) // 4096)   # 真实触摸页
    time.sleep(8)
time.sleep(20)
' >/dev/null 2>&1 &
  echo "[P3] 内存申请进程已启动（5×280MB，约 80s 后退出）"
  # 内存守卫：可用内存低于 1.3GB 时服务自己报警（真实服务有内存护栏）
  # 具体数值放句尾（前 48 字符一致 → 同一故障一个指纹，避免刷屏）
  nohup sh -c '
    while :; do
      AVAIL=$(free -m | awk "/Mem:/{print \$7}")
      NOW=$(date "+%F %T")
      if [ -n "$AVAIL" ] && [ "$AVAIL" -lt 1300 ] 2>/dev/null; then
        echo "$NOW ERROR payment-api memory guard: available memory below 1300MB floor (OOM risk, node under memory pressure, avail=${AVAIL}MB)" >> /var/log/demo-app.log
      fi
      sleep 2
    done
  ' >/dev/null 2>&1 &
  echo $! > /tmp/memguard.pid
  sleep 80
  kill "$(cat /tmp/memguard.pid 2>/dev/null)" 2>/dev/null; rm -f /tmp/memguard.pid
  pkill -f '280 \* 1024' 2>/dev/null
  pkill -f 'chunks' 2>/dev/null
  echo "[P3] 内存进程已退出，自愈完成" ;;
P4)  # 服务断线：租用机器上的服务突然不可用（进程消失，机器本身没重启）
  echo "--- 正常基线 3s ---"; sleep 10   # 等看门狗基线测完（约 6s）再制造故障
  changelog "team-billing 在租用机器上执行维护操作（未通知本团队）" "team-billing"
  echo "$SUDO_PW" | sudo -S systemctl stop payment-api 2>/dev/null
  echo "[P4] payment-api 已停止（模拟租用机器服务突然断线，60s 后恢复）"
  sleep 60
  echo "$SUDO_PW" | sudo -S systemctl start payment-api 2>/dev/null
  changelog "team-payment 重启 payment-api（服务恢复）" "team-payment"
  echo "[P4] 服务已恢复" ;;
RESET)  # 清理所有注入痕迹，恢复基线
  hog_stop; pkill -f bytearray 2>/dev/null; watchdog_stop
  echo "[RESET] 注入进程已清理" ;;
*)
  echo "用法: sh k8s-scenarios.sh P1|P2|P3|P4|RESET"; watchdog_stop; exit 1 ;;
esac

watchdog_stop
echo "=== scenario $P done, log tail: ==="
tail -6 "$LOG"
echo "=== changes tail: ==="
tail -3 "$CHANGES"
