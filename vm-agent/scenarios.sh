#!/bin/sh
# AIOps 盲测故障注入器（在虚拟机 Guest 内运行）
# 用法：sh scenarios.sh S1|S2|S3|S4|S5|S6|S7|S8
# 原则：真实故障 + 真实应用日志（平台的唯一输入），全部自动恢复，可反复跑。
# 输出落 /tmp/wb_out.txt（vmrun 不回传 stdout，需拷文件看）。

exec > /tmp/wb_out.txt 2>&1
SUDO_PW="${VM_SUDO_PW:-<你的sudo密码>}"
LOG=/var/log/demo-app.log
S="$1"

echo "=== scenario $S start $(date) ==="

# 确保日志文件存在可写
echo "$SUDO_PW" | sudo -S touch "$LOG" 2>/dev/null
echo "$SUDO_PW" | sudo -S chmod 666 "$LOG" 2>/dev/null

# 写一条应用日志（带时间戳，探针会剥掉时间戳派生指纹）
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

# ── 准备一个真实业务服务 payment-api（S5/S7 用）────────────────
ensure_payment_api() {
  if [ -f /etc/systemd/system/payment-api.service ]; then return; fi
  echo "$SUDO_PW" | sudo -S mkdir -p /etc/payment-api
  echo "$SUDO_PW" | sudo -S tee /etc/payment-api/config >/dev/null <<'EOF'
listen=127.0.0.1:8080
upstream=dep-payment
timeout_ms=3000
EOF
  echo "$SUDO_PW" | sudo -S tee /usr/local/bin/payment-api.py >/dev/null <<'EOF'
#!/usr/bin/env python3
import http.server, socketserver, time
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/healthz"):
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(200); self.end_headers(); self.wfile_write() if False else self.wfile.write(b"payment ok")
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 8080), H) as s: s.serve_forever()
EOF
  echo "$SUDO_PW" | sudo -S chmod +x /usr/local/bin/payment-api.py
  echo "$SUDO_PW" | sudo -S tee /etc/systemd/system/payment-api.service >/dev/null <<'EOF'
[Unit]
Description=Demo Payment API
[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/payment-api.py
Restart=always
[Install]
WantedBy=multi-user.target
EOF
  echo "$SUDO_PW" | sudo -S systemctl daemon-reload
  echo "$SUDO_PW" | sudo -S systemctl enable --now payment-api 2>/dev/null
}

case "$S" in
S1)  # 应用层：支付回调超时 ×12（同指纹，演示去重：12→1）
  for i in $(seq 1 12); do
    log "ERROR payment callback timeout upstream=dep-payment"
  done
  echo "[S1] 12 条同指纹支付超时 ERROR 已写入（去重后应只剩 1 条告警）" ;;
S2)  # 系统资源-磁盘：/tmp 写满 1G（120s 自愈）
  dd if=/dev/zero of=/tmp/balloon bs=1M count=1024 status=none 2>/dev/null
  nohup sh -c "sleep 120; rm -f /tmp/balloon" >/dev/null 2>&1 &
  for i in 1 2 3; do log "ERROR disk usage /tmp exceeds 85% threshold write failed"; done
  echo "[S2] 1G 气球已写（120s 自愈）+ 3 条磁盘 ERROR" ;;
S3)  # 系统资源-CPU：单核满载 60s
  nohup sh -c "timeout 60 sh -c 'while :; do :; done'" >/dev/null 2>&1 &
  for i in 1 2 3; do log "ERROR healthz probe timeout after 5s (cpu starvation suspected)"; done
  echo "[S3] CPU 满载 60s + 3 条探针超时 ERROR" ;;
S4)  # K8s：坏镜像 CrashLoopBackOff（90s 自愈）
  ensure_payment_api >/dev/null 2>&1
  kubectl create deployment broken --image=nginx:nonexistent-tag-xyz >/dev/null 2>&1 || \
    kubectl set image deployment/broken nginx=nginx:nonexistent-tag-xyz >/dev/null 2>&1
  for i in 1 2 3; do log "ERROR pod broken CrashLoopBackOff restarts=5 reason=ImagePullBackOff"; done
  nohup sh -c "sleep 90; kubectl delete deployment broken --ignore-not-found >/dev/null 2>&1" >/dev/null 2>&1 &
  echo "[S4] 坏镜像 Deployment 已建（90s 自愈）+ 3 条 CrashLoopBackOff ERROR" ;;
S5)  # 服务状态：payment-api 宕机（60s 自愈）
  ensure_payment_api
  echo "$SUDO_PW" | sudo -S systemctl stop payment-api
  for i in 1 2 3; do log "ERROR payment-api unreachable: connection refused 127.0.0.1:8080"; done
  nohup sh -c "sleep 60; echo $SUDO_PW | sudo -S systemctl start payment-api" >/dev/null 2>&1 &
  echo "[S5] payment-api 已停（60s 自愈）+ 3 条拒绝连接 ERROR" ;;
S6)  # 网络-DNS：解析失败（60s 自愈）
  sudo cp /etc/resolv.conf /tmp/resolv.bak 2>/dev/null
  echo "nameserver 10.255.255.1" | sudo tee /etc/resolv.conf >/dev/null
  for i in 1 2 3; do log "ERROR getaddrinfo failed: dep-payment.internal (name resolution error)"; done
  nohup sh -c "sleep 60; sudo cp /tmp/resolv.bak /etc/resolv.conf" >/dev/null 2>&1 &
  echo "[S6] DNS 已换坏（60s 自愈）+ 3 条解析失败 ERROR" ;;
S7)  # 配置-权限：配置文件读不了（自愈）
  ensure_payment_api
  echo "$SUDO_PW" | sudo -S chmod 000 /etc/payment-api/config
  echo "$SUDO_PW" | sudo -S systemctl restart payment-api >/dev/null 2>&1
  for i in 1 2 3; do log "ERROR payment-api failed to start: permission denied /etc/payment-api/config"; done
  nohup sh -c "sleep 60; echo $SUDO_PW | sudo -S chmod 644 /etc/payment-api/config; echo $SUDO_PW | sudo -S systemctl restart payment-api" >/dev/null 2>&1 &
  echo "[S7] 配置权限已坏（60s 自愈）+ 3 条启动失败 ERROR" ;;
S8)  # 依赖-下游：端口拒绝连接
  nohup python3 -m http.server 8081 >/dev/null 2>&1 &
  DOWN=$!; sleep 1; kill $DOWN 2>/dev/null
  for i in 1 2 3; do log "ERROR upstream dep-inventory ECONNREFUSED 127.0.0.1:8081 retry=3"; done
  echo "[S8] 假下游起后即杀 + 3 条 ECONNREFUSED ERROR" ;;
*)
  echo "用法: sh scenarios.sh S1..S8"; exit 1 ;;
esac

echo "=== scenario $S done, tail: ==="
tail -3 "$LOG"
