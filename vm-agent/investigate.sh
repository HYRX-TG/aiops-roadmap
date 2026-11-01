#!/bin/sh
# ─────────────────────────────────────────────────────────────
# 生产级只读排查工具集（在虚拟机 Guest 内运行）
# 铁律：本脚本只执行只读命令（get/describe/logs/top/df/free/ps/journalctl），
#       绝不执行任何变更操作（delete/scale/rollout/evict/drain）。
#       危险处置动作一律交给「人」在审批后执行。
# 输出：结构化证据文本，供探针附带到告警事件 → 后端研判
# ─────────────────────────────────────────────────────────────
export HOME=/home/tbt
export KUBECONFIG=/home/tbt/.kube/config

echo "### 1. 节点状态（Node）"
kubectl get nodes -o wide 2>&1 | head -4
kubectl describe node tbt 2>/dev/null | grep -A12 "Conditions:" | head -14

echo "### 2. 本节点资源水位（无 metrics-server 时用 /proc + cgroup）"
echo "-- CPU 负载: $(cat /proc/loadavg)"
echo "-- 内存: $(free -m | awk '/Mem:/{printf "used=%sM avail=%sM total=%sM", $3,$7,$2}')"
echo "-- 磁盘: $(df -h / | tail -1 | awk '{print "used="$3" avail="$4" use%="$5}')"
echo "-- inode: $(df -i / | tail -1 | awk '{print "use%="$5}')"
echo "-- Top5 CPU 进程（资源抢占的直接证据，负载均值在本 VM 不可靠故以 ps 为准）:"
ps -eo pid,user,pcpu,pmem,etime,args --sort=-pcpu 2>/dev/null | head -6
echo "-- Top3 内存进程:"
ps -eo pid,user,pcpu,pmem,etime,args --sort=-rss 2>/dev/null | head -4

echo "### 3. Pod 状态全景（非 Running / 重启异常）"
kubectl get pods -A --field-selector status.phase!=Running 2>&1 | head -8
kubectl get pods -A 2>&1 | awk '$5 ~ /^[1-9]/ {print}' | head -6

echo "### 4. 最近 Warning 事件（最近变更/驱逐/拉取失败的时间线）"
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp 2>&1 | tail -8

echo "### 5. 最近变更记录（跨部门发布溯源）"
kubectl get deploy -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image,UPDATED_AT:.metadata.managedFields[-1].time 2>&1 | head -8
echo "-- 变更台账 /var/log/changes.log:"
tail -5 /var/log/changes.log 2>/dev/null || echo "（无台账）"
kubectl get events -A --sort-by=.lastTimestamp 2>&1 | grep -iE "scal|creat|delet|kill|pull" | tail -6

echo "### 6. 系统服务健康（kubelet/containerd/sshd/payment-api）"
for svc in kubelet containerd sshd payment-api; do
  echo "$svc: $(systemctl is-active $svc 2>/dev/null) $(systemctl show -p ActiveEnterTimestamp --value $svc 2>/dev/null | head -c 19)"
done
echo "-- 机器 uptime（判断'机器重启过'还是'服务自己死了'）: $(uptime) ; boot: $(who -b 2>/dev/null)"
echo "-- dmesg 最近错误: $(dmesg 2>/dev/null | tail -20 | grep -iE 'error|fail|oom|killed process' | tail -3 || echo '需root')"

echo "### 7. 容器运行时状态"
crictl ps -a 2>/dev/null | awk 'NR==1 || $4!="Running"' | head -8 || true

echo "### 8. 网络连通性（本机回环 + 上游 DNS）"
echo "-- DNS: $(timeout 2 getent hosts dep-payment.internal 2>&1 || echo '解析失败')"
echo "-- 8080(payment-api): $(timeout 2 bash -c 'echo > /dev/tcp/127.0.0.1/8080' 2>&1 && echo 通 || echo 不通)"

echo "### INVESTIGATE_DONE"
