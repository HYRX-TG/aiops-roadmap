#!/bin/sh
# 一键造错脚本（在虚拟机 Guest 内运行）：制造 4 类真实故障，全部带自动恢复。
# 设计原则：可重复跑、不搞破坏、90 秒内自愈——演示用，不是压测。
#
# 两种跑法：
#   A. 你 SSH 进虚拟机：  sh inject-errors.sh
#   B. 宿主机 vmrun：    vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromHostToGuest "<vmx>" inject-errors.sh /tmp/inject.sh
#                        vmrun -T ws -gu <guest用户> -gp <guest密码> runProgramInGuest "<vmx>" /bin/sh /tmp/inject.sh
#                        vmrun -T ws -gu <guest用户> -gp <guest密码> copyFileFromGuestToHost "<vmx>" /tmp/wb_out.txt out.txt
#
# 输出统一落 /tmp/wb_out.txt（vmrun 不回传 stdout，只能拷文件看）。

exec > /tmp/wb_out.txt 2>&1
SUDO_PW="${VM_SUDO_PW:-<你的sudo密码>}"          # ← 按你虚拟机实际 sudo 密码改
LOG=/var/log/demo-app.log

echo "=== 造错开始 $(date) ==="

# 1) 灌错误日志（探针的燃料）：12 条支付回调超时 ERROR
for i in $(seq 1 12); do
  echo "$(date '+%F %T') ERROR payment callback timeout seq=$i trace=tx-$(head -c 6 /dev/urandom | base64 | tr -d '/+=')" >> "$LOG" 2>/dev/null \
    || echo "$(date '+%F %T') ERROR payment callback timeout seq=$i (log write failed)" >> /tmp/demo-app.log
done
echo "[1] 错误日志已灌入：$LOG"

# 2) CPU 打满 30 秒（自动恢复）
nohup sh -c "timeout 30 sh -c 'while :; do :; done'" >/dev/null 2>&1 &
echo "[2] CPU 满载 30s（一个核），自动恢复"

# 3) 磁盘气球 512M，90 秒后自动清理
dd if=/dev/zero of=/tmp/balloon bs=1M count=512 status=none 2>/dev/null
nohup sh -c "sleep 90; rm -f /tmp/balloon" >/dev/null 2>&1 &
echo "[3] /tmp 写入 512M 气球文件，90s 后自动删除"

# 4) nginx 停 60 秒再拉起来（没装 nginx 则跳过）
if systemctl list-unit-files 2>/dev/null | grep -q "nginx"; then
  echo "$SUDO_PW" | sudo -S systemctl stop nginx 2>/dev/null
  nohup sh -c "sleep 60; echo $SUDO_PW | sudo -S systemctl start nginx" >/dev/null 2>&1 &
  echo "[4] nginx 已停，60s 后自动恢复"
else
  echo "[4] 未安装 nginx，跳过（可换：systemctl stop <你的服务>）"
fi

echo "=== 造错完成，等探针上报后看大盘 ==="
