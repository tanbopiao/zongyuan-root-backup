#!/bin/bash
# kg-api 恢复监测 + 记忆网关自动写入
# 每60秒检测一次，恢复后自动执行真值同步
API="https://www.huodouai.com/api/v1/truths/sync/status"
SYNC="https://www.huodouai.com/api/v1/truths/sync"
KEY="ZONGYUAN-TRUTH-SYNC-2026-9f3a7c1e"
LOG="/home/user/Doubao/chats/38438412455799554/kg-watchdog.log"

for i in $(seq 1 60); do
  CODE=$(curl -s -o /tmp/kg_status.txt -w "%{http_code}" -m 5 "$API" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    echo "[$(date '+%F %T')] kg-api恢复（HTTP 200）" >> "$LOG"
    # 尝试写入记忆网关（全域锁档真值）
    RESP=$(curl -s -m 10 -X POST "$SYNC" \
      -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
      -d '{
        "node_id": "NN-META-024",
        "truth_type": "lock.global.kernel.002",
        "truth_content": "全域锁档LOCK-GLOBAL-KERNEL-20260912-002：同源内核V2/16真值/FRP连接/服务器状态，飞书三端固化",
        "category": "kernel_lock",
        "source_window": "38438412455799554",
        "metadata": {"lock_id": "LOCK-GLOBAL-KERNEL-20260912-002", "date": "2026-09-12"}
      }' 2>&1)
    echo "[$(date '+%F %T')] 写入结果: $RESP" >> "$LOG"
    if echo "$RESP" | grep -qE "synced|duplicate"; then
      echo "[$(date '+%F %T')] ✅ 记忆网关更新成功" >> "$LOG"
      exit 0
    fi
    echo "[$(date '+%F %T')] 写入被拒（可能key过期），继续监测..." >> "$LOG"
  fi
  sleep 55
done
echo "[$(date '+%F %T')] 监测窗口结束（60次），kg-api未恢复" >> "$LOG"
