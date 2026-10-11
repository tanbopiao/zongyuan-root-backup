#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# drama:9120记忆网关恢复监测 + 写入链路验证
API="https://www.huodouai.com/api/gateway/truths?level=public"
TOKEN=""
LOG="/home/user/Doubao/chats/38438412455799554/report-gateway-verify-20260915/drama-watchdog.log"
for i in $(seq 1 60); do
  CODE=$(curl -s -o /tmp/dw.txt -w "%{http_code}" -m 5 -H "X-Capture-Token: $TOKEN" "$API" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    COUNT=$(python3 -c "import json; print(json.load(open('/tmp/dw.txt')).get('count','?'))" 2>/dev/null)
    echo "[$(date '+%F %T')] ✅ 9120恢复！真值总数: $COUNT" >> "$LOG"
    # 验证写入链路（上报测试真值）
    R=$(curl -s -m 8 -X POST "https://www.huodouai.com/api/report/truth" -H "Content-Type: application/json" \
      -d '{"truth_key":"VERIFY.GATEWAY.RESTORED.20260915","truth_value":"9120恢复后写入链路验证","source_node":"NN-META-024","confidence":0.9}' 2>&1)
    echo "[$(date '+%F %T')] 写入链路验证: $R" >> "$LOG"
    exit 0
  fi
  sleep 55
done
echo "[$(date '+%F %T')] 监测窗口结束（60次），9120未恢复" >> "$LOG"
