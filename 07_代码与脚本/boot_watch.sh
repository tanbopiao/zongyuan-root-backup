#!/bin/bash
# ============================================================
# boot_watch.sh | 本地实例守护：周期探活+通道状态+对账提醒
# DID-BR-000002 | Ω₀⊂⊙∞⊂Ω
# 用法：nohup bash boot_watch.sh > /dev/null 2>&1 &   （或配 cron）
# 周期：默认 10 分钟一轮
# ============================================================
set -uo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
source "${SCRIPT_DIR}/boot_config.env"
INTERVAL=${1:-600}

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"; }

log "守护启动：每 ${INTERVAL}s 一轮"

while true; do
  # 通道探活
  MAIN=$(curl -s -o /dev/null -w "%{http_code}" -m 8 "${TRUTHS_LIST}" 2>/dev/null)
  BACK=$(curl -s -o /dev/null -w "%{http_code}" -m 8 "https://drama.huodouai.com/api/truths/" 2>/dev/null)

  # 队列状态
  QUEUE_N="0"
  if [ -f "${QUEUE_FILE}" ] && grep -q '"remaining"' "${QUEUE_FILE}" 2>/dev/null; then
    QUEUE_N=$(python3 -c "import json;q=json.load(open('${QUEUE_FILE}'));print(len(q.get('remaining',[])) if isinstance(q,dict) else 0)" 2>/dev/null || echo "?")
  fi

  log "守护：主=${MAIN} 备=${BACK} 待补发=${QUEUE_N}"

  # 主站通且有积压 → 自动补发一次
  if [ "${MAIN}" = "200" ] && [ "${QUEUE_N}" != "0" ] && [ "${QUEUE_N}" != "?" ]; then
    log "主站恢复且有 ${QUEUE_N} 条积压，触发补发"
    bash "${SCRIPT_DIR}/boot_anchor.sh" >> "${LOG_FILE}" 2>&1
  fi

  sleep "${INTERVAL}"
done
