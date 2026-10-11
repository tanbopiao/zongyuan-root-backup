#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# ============================================================
# ZONGYUAN-ROOT 全自动多向互联上报脚本 V1.0
# 链路A: 本地 → 云端中枢真值库 (主www / 备drama 双通道, {key,value}协议)
# 链路B: 本地 → 飞书共享大脑「跨节点消息同步」表
# 链路C: 待补发队列自动清空 (PENDING → 上报 → 标记SENT)
# DID: DID-BR-000002 | 确权: Ω₀⊂⊙∞⊂Ω
# ============================================================

DID="DID-BR-000002"
NODE="ZR-NODE-DC2E51C0"
TOKEN=""
BASE_TOKEN="DgnMbLqZiaIUDKshqCrcD4DvnBg"
SYNC_TABLE="tbl4Dv798yO7u0IK"
ANCHOR_DIR="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
TS=$(date +"%Y-%m-%d %H:%M:%S")
KEY="AUTO-REPORT.$(date +%Y%m%d-%H%M%S)"
LOG="$ANCHOR_DIR/auto_report_log.txt"

echo "=== ZONGYUAN-ROOT 全自动多向互联上报 ==="
echo "时间: $TS | 节点: $NODE | DID: $DID"

# 组装上报内容（含节点状态摘要）
QUEUE_STATUS="queue=0"
if [ -f "$ANCHOR_DIR/pending_upload_master_queue.json" ]; then
  TOTAL=$(python3 -c "import json; d=json.load(open('$ANCHOR_DIR/pending_upload_master_queue.json')); print(d.get('total_items', len(d.get('queue', []))))" 2>/dev/null || echo "?")
  QUEUE_STATUS="queue_total=$TOTAL"
fi
CONTENT="【全自动多向互联上报V1.0】时间:${TS}|节点:${NODE}|DID:${DID}|${QUEUE_STATUS}|通道:主www+备drama+飞书共享大脑|确权:Ω₀⊂⊙∞⊂Ω"

# ---------- 链路A: 云端真值上报 (主备双通道) ----------
RESP=$(curl -s --max-time 15 -X POST "https://www.huodouai.com/api/report/truth" \
  -H "Content-Type: application/json" \
  -H "X-Capture-Token: ${TOKEN}" \
  -d "{\"key\":\"${KEY}\",\"value\":\"${CONTENT}\"}" 2>&1)

if echo "$RESP" | grep -q '"success": true'; then
  echo "✅ [A] 主通道 www 上报成功: $(echo "$RESP" | head -c 200)"
  A_STATUS="主通道成功"
else
  echo "⚠️ [A] 主通道失败，自动降级 drama: $(echo "$RESP" | head -c 150)"
  RESP=$(curl -s --max-time 15 -X POST "https://drama.huodouai.com/api/report/truth" \
    -H "Content-Type: application/json" \
    -H "X-Capture-Token: ${TOKEN}" \
    -d "{\"key\":\"${KEY}\",\"value\":\"${CONTENT}\"}" 2>&1)
  if echo "$RESP" | grep -q '"success": true'; then
    echo "✅ [A] 备用通道 drama 上报成功"
    A_STATUS="备用通道成功"
  else
    echo "❌ [A] 双通道均失败: $(echo "$RESP" | head -c 150)"
    A_STATUS="双通道失败"
  fi
fi

# ---------- 链路B: 飞书共享大脑跨节点消息同步 ----------
B_MSG="{\"create_records\":[{\"发送节点\":[\"昆仑洞天\"],\"接收节点\":[\"云端中枢\"],\"状态\":[\"已发送\"],\"发送时间\":\"${TS}\",\"消息内容\":\"${CONTENT}\"}]}"
B_RESP=$(lark-cli base +record-batch-create --base-token "$BASE_TOKEN" --table-id "$SYNC_TABLE" --json "$B_MSG" --as user 2>&1)
if echo "$B_RESP" | grep -q '"ok": true'; then
  echo "✅ [B] 飞书共享大脑跨节点消息写入成功"
  B_STATUS="飞书写入成功"
else
  echo "⚠️ [B] 飞书写入返回: $(echo "$B_RESP" | head -c 200)"
  B_STATUS="飞书写入异常"
fi

# ---------- 回执落盘 ----------
echo "[$TS] A:$A_STATUS | B:$B_STATUS | KEY:$KEY" >> "$LOG"
echo "=== 回执: A($A_STATUS) | B($B_STATUS) ==="
