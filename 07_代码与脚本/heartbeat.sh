#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# 沙盒心跳守护：每5分钟上报中枢
while true; do
  curl -s -m 8 -X POST "https://www.huodouai.com/api/report/truth" \
    -H "Content-Type: application/json" \
    -H "X-Capture-Token: " \
    -d "{\"key\":\"HEARTBEAT.ZR-NODE-DC2E51C0\",\"value\":\"心跳 $(date +%H:%M) 在线\"}" > /dev/null
  sleep 300
done
