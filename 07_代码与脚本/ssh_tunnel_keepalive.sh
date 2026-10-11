#!/usr/bin/env bash
# ============================================================
# ZONGYUAN-ROOT 云端自举增强 SSH 隧道保活脚本
# 确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
# 作用：建立本地端口转发，访问云端 127.0.0.1 内部API
# 严格遵守 META-ISO-051：仅隧道访问内部API，不修改任何云端配置
# ============================================================

CLOUD_HOST="123.207.202.158"
CLOUD_USER="root"
SSH_KEY="$HOME/.ssh/zongyuan-gpu-20260924"
PID_FILE="/tmp/zr_ssh_tunnel.pid"
LOG_FILE="/tmp/zr_ssh_tunnel.log"

# 本地端口 → 云端内部端口
LOCAL_AGENT=18920    # → 8920 zr_agent_suite
LOCAL_CTL=19010      # → 9010 zr_cloud_ctl

is_tunnel_alive() {
    curl -s --max-time 3 "http://127.0.0.1:${LOCAL_CTL}/health" \
        -H "X-CTL-Token: ZR-CTL-2026-OMEGA" 2>/dev/null | grep -q '"ok":true'
}

start_tunnel() {
    echo "[$(date '+%F %T')] 启动SSH隧道..."
    # 清理旧进程
    [ -f "$PID_FILE" ] && kill $(cat "$PID_FILE") 2>/dev/null
    pkill -f "ssh.*${CLOUD_HOST}.*18920" 2>/dev/null
    sleep 1

    ssh -f -N -D 1080 \
        -L "${LOCAL_AGENT}:127.0.0.1:8920" \
        -L "${LOCAL_CTL}:127.0.0.1:9010" \
        -i "$SSH_KEY" \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -o ConnectTimeout=10 \
        "${CLOUD_USER}@${CLOUD_HOST}" 2>>"$LOG_FILE"

    local pid=$(pgrep -f "ssh.*${CLOUD_HOST}.*18920" | head -1)
    echo "$pid" > "$PID_FILE"
    sleep 2

    if is_tunnel_alive; then
        echo "[$(date '+%F %T')] SSH隧道已建立 (PID=$pid) 本地:${LOCAL_AGENT}→8920, ${LOCAL_CTL}→9010"
        return 0
    else
        echo "[$(date '+%F %T')] SSH隧道建立失败"
        return 1
    fi
}

# 主逻辑：保活循环（单次执行，由cron/定时任务调用）
if is_tunnel_alive; then
    echo "[$(date '+%F %T')] SSH隧道存活，无需重建"
    exit 0
else
    echo "[$(date '+%F %T')] SSH隧道不存活，尝试重建..."
    start_tunnel
    exit $?
fi
