#!/bin/bash
# ZONGYUAN-ROOT 自治循环定时任务（MA-AUTO-001 落地）
LOG=/home/user/Doubao/chats/38436747020400130/autonomy_loop_cron.log
SKILL=/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-autonomous-kernel
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ====== 自治循环开始 =====" >> "$LOG"
cd "$SKILL"
python3 scripts/autonomy_loop_scheduler.py --mode run >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ====== 自治循环结束 =====" >> "$LOG"
