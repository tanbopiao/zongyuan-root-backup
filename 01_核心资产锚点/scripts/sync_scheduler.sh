#!/bin/bash
# 元极恒一 · 跨实例同步调度器
# 每小时执行一次同步

ANCHOR_DIR="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
LOG_DIR="$ANCHOR_DIR/report_log"
mkdir -p "$LOG_DIR"

echo "[$(date -Iseconds)] 跨实例同步触发" >> "$LOG_DIR/sync_scheduler.log"

# 执行跨实例同步
python3 "$ANCHOR_DIR/scripts/cross_instance_sync.py" >> "$LOG_DIR/sync_scheduler.log" 2>&1

# 同步完成后自动上报
python3 "$ANCHOR_DIR/scripts/auto_reporter.py" \
  "SYNC-HOURLY-$(date +%Y%m%d%H)" \
  "每小时跨实例同步完成" >> "$LOG_DIR/sync_scheduler.log" 2>&1

echo "[$(date -Iseconds)] 跨实例同步完成" >> "$LOG_DIR/sync_scheduler.log"
