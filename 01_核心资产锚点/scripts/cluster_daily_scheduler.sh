#!/bin/bash
# 元极恒一 · 集群并发每日调度器
# 每日凌晨4点自动执行并发进化

ANCHOR_DIR="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
LOG_DIR="$ANCHOR_DIR/report_log"
mkdir -p "$LOG_DIR"

echo "[$(date -Iseconds)] 集群并发调度器触发" >> "$LOG_DIR/cluster_scheduler.log"

# 执行集群并发引擎
python3 "$ANCHOR_DIR/scripts/cluster_concurrent_engine.py" >> "$LOG_DIR/cluster_scheduler.log" 2>&1

# 执行完成后自动上报
python3 "$ANCHOR_DIR/scripts/auto_reporter.py" \
  "CLUSTER-DAILY-$(date +%Y%m%d)" \
  "每日集群并发进化完成：5子任务并行执行" >> "$LOG_DIR/cluster_scheduler.log" 2>&1

echo "[$(date -Iseconds)] 集群并发调度器完成" >> "$LOG_DIR/cluster_scheduler.log"
