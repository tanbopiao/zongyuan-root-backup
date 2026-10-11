#!/usr/bin/env bash
# submit_and_run.sh — 提交即触发脚本
# 用法: ./submit_and_run.sh truth_key truth_value truth_type confidence
# 例:   ./submit_and_run.sh "creative.drama.test" "测试短剧资产" creative 0.9
set -euo pipefail

KEY="${1:?用法: submit_and_run.sh <truth_key> <truth_value> <truth_type> <confidence>}"
VAL="${2:?缺少 truth_value}"
TYPE="${3:-creative}"
CONF="${4:-0.9}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
GW="https://www.huodouai.com/api/report/truth"

echo "[submit_and_run] 上报真值: key=$KEY type=$TYPE conf=$CONF"

# 1. 上报真值到记忆网关
RESP=$(curl -sS --max-time 15 -X POST "$GW" \
  -H "Content-Type: application/json" \
  -d "{\"truth_key\":\"$KEY\",\"truth_value\":\"$(echo "$VAL" | sed 's/"/\\"/g')\",\"source_node\":\"submit_and_run\",\"confidence\":$CONF,\"truth_type\":\"$TYPE\"}")

echo "[submit_and_run] 网关回执: $RESP"

# 2. 立即触发流水线
echo "[submit_and_run] 触发 pipeline_runner --trigger submit"
cd "$ROOT"
python3 "$SCRIPT_DIR/pipeline_runner.py" --trigger submit

echo "[submit_and_run] 完成。"
