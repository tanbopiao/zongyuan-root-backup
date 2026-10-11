#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# 自动进化闭环流水线 V2（P3）｜扫描→提炼→上报→锁档
# 用法: bash auto-evolution-pipeline.sh [--dry-run]
BASE="/home/user/Doubao/chats/38438412455799554"
TOKEN=""
API="https://www.huodouai.com/api/gateway"
DRY="${1:-}"
echo "════ 自动进化闭环 V2 ════"
echo "[1/5] 扫描本地资产..."
COUNT=$(find "$BASE" -maxdepth 2 -type f 2>/dev/null | wc -l)
echo "      资产文件: $COUNT"

echo "[2/5] 提炼真值摘要..."
SNAPSHOT=$(python3 -c "
import json
d = json.load(open('$BASE/homology-kernel-v1/kernel_truths.json'))
print(f'{len(d[\"truths\"])}条真值')
" 2>/dev/null)

echo "[3/5] 上报记忆网关..."
if [ "$DRY" = "--dry-run" ]; then
  echo "      [dry-run] 跳过上报"
else
  RESP=$(curl -s -m 10 -X POST $API/report \
    -H "X-Capture-Token: $TOKEN" -H "Content-Type: application/json" \
    -d "{\"node_id\":\"NN-META-024\",\"DID\":\"DID-BR-000002\",\"ROOT_OMEGA\":\"Ω-TAN-7-001\",\"truth_type\":\"operation_log\",\"truth_content\":\"自动闭环流水线V2运行：扫描${COUNT}资产/提炼${SNAPSHOT}\"}" 2>&1)
  echo "      上报: $(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok synced='+str(d.get('synced','?')))" 2>/dev/null || echo FAIL)"
fi

echo "[4/5] 锁档归档..."
if [ "$DRY" = "--dry-run" ]; then
  echo "      [dry-run] 跳过锁档"
else
  cd /home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-kernel-lock
  bash scripts/kernel_lock.sh lock "自动闭环·流水线V2运行记录" "$BASE/evolution-deploy-20260913/EXECUTION-PLAN-20260913.md" "LOCK-PIPELINE-V2-20260913-001" "自动进化闭环流水线V2" "自动执行六步闭环" "" 2>&1 | grep -E "知识库文档|锁档事件" | head -2
fi

echo "[5/5] 神经激活..."
echo "      完成（由上层内核激活）"
echo "════ 闭环完成 ════"
