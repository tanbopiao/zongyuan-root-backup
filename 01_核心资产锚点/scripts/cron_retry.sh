#!/bin/bash
# 元极恒一 · 每30分钟自动补发队列
# crontab: */30 * * * * /home/user/Doubao/chats/38437615670548738/zongyuan-anchor/scripts/cron_retry.sh >> /home/user/Doubao/chats/38437615670548738/zongyuan-anchor/report_log/cron.log 2>&1

REPORTER="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/scripts/auto_reporter.py"
LOG_DIR="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/report_log"

mkdir -p "$LOG_DIR"
echo "[$(date -Iseconds)] cron_retry 触发" >> "$LOG_DIR/cron_retry.log"
python3 "$REPORTER" 2>&1 >> "$LOG_DIR/cron_retry.log"
