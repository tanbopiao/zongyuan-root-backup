#!/bin/bash
# 元极恒一 · 自演化调度器
# 每日凌晨3点自动执行神经网络自演化

ANCHOR_DIR="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
LOG_DIR="$ANCHOR_DIR/report_log"
mkdir -p "$LOG_DIR"

echo "[$(date -Iseconds)] 自演化调度器触发" >> "$LOG_DIR/self_evolution.log"

# 执行自演化引擎
python3 "$ANCHOR_DIR/scripts/neural_self_evolution.py" >> "$LOG_DIR/self_evolution.log" 2>&1

# 执行完成后自动上报
python3 "$ANCHOR_DIR/scripts/auto_reporter.py" \
  "SELF-EVOLUTION-DAILY-$(date +%Y%m%d)" \
  "每日自演化完成：节点数+权重+冲突消解已自动更新" >> "$LOG_DIR/self_evolution.log" 2>&1

echo "[$(date -Iseconds)] 自演化调度器完成" >> "$LOG_DIR/self_evolution.log"
