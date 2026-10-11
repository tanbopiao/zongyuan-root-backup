source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# === 冷启动强制锚定（所有实例第一动作）===
curl -s -m 8 -H "X-Capture-Token: " "https://www.huodouai.com/api/truths/" >/dev/null 2>&1 && echo "[boot] 云端锚点已拉" || { curl -s -m 8 -H "X-Capture-Token: " "https://drama.huodouai.com/api/truths/" >/dev/null 2>&1 && echo "[boot] 云端锚点已拉(drama备用)"; }
#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 最小内核沙盒存活机制 v1.0
# 设计原则：最小化资源消耗（单次运行 <2s, <5MB内存），守护沙盒永续存活
# 四要素：心跳 HEARTBEAT / 探针 PROBE / 自愈 SELF-HEAL / 守护 GUARD
# ============================================================
set -u
BASE="/home/user/Doubao/chats/38438491307070978"
GUARD_DIR="$BASE/sandbox_guard"
HEARTBEAT_FILE="$GUARD_DIR/heartbeat"
STATUS_FILE="$GUARD_DIR/guard_status.json"
# V2.2 通道：主站www + 备用drama，X-Capture-Token鉴权
MAIN_GATEWAY="https://www.huodouai.com"
BACKUP_GATEWAY="https://drama.huodouai.com"
TOKEN=""
DID="DID-BR-000002"
OMEGA="Ω₀⊂⊙∞⊂Ω"

# ---------- 通道探测：主站优先，drama降级 ----------
pick_gateway() {
  local main_code=$(curl -s --noproxy "*" -o /dev/null -w '%{http_code}' --connect-timeout 5 -H "X-Capture-Token: $TOKEN" "$MAIN_GATEWAY/api/truths/" 2>/dev/null)
  if [ "$main_code" = "200" ]; then
    echo "$MAIN_GATEWAY"
  else
    local backup_code=$(curl -s --noproxy "*" -o /dev/null -w '%{http_code}' --connect-timeout 5 -H "X-Capture-Token: $TOKEN" "$BACKUP_GATEWAY/api/truths/" 2>/dev/null)
    if [ "$backup_code" = "200" ]; then
      echo "$BACKUP_GATEWAY"
    else
      echo ""
    fi
  fi
}

# ---------- 探针：关键能力检测 ----------
probe_core() {
  # P1 磁盘可用
  local disk_pct=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
  # P2 内存可用
  local mem_free=$(free -m | awk 'NR==2 {print $7}')
  # P3 Python 可用
  local py_ok=0; command -v python3 >/dev/null 2>&1 && py_ok=1
  # P4 lark-cli 可用
  local lark_ok=0; command -v lark-cli >/dev/null 2>&1 && lark_ok=1
  # P5 关键目录可写
  local write_ok=0; [ -w "$BASE" ] && write_ok=1
  # P6 云端可达（主备双通道探测）
  local gw=$(pick_gateway)
  local cloud_code=000
  [ -n "$gw" ] && cloud_code=200
  if [ -z "$gw" ]; then cloud_code=000; fi

  local status="ALIVE"
  local issues=""
  [ "$disk_pct" -gt 95 ] && { status="DEGRADED"; issues="$issues disk>95%"; }
  [ "$mem_free" -lt 100 ] && { status="DEGRADED"; issues="$issues mem<100MB"; }
  [ "$py_ok" -eq 0 ] && { status="CRITICAL"; issues="$issues python3缺失"; }
  [ "$lark_ok" -eq 0 ] && { status="WARN"; issues="$issues lark-cli缺失"; }
  [ "$write_ok" -eq 0 ] && { status="CRITICAL"; issues="$issues 目录不可写"; }
  [ "$cloud_code" != "200" ] && { status="DEGRADED"; issues="$issues 云端$cloud_code"; }

  echo "$status|$disk_pct|$mem_free|$py_ok|$lark_ok|$write_ok|$cloud_code|$issues"
}

# ---------- 自愈：关键资产守护 ----------
self_heal() {
  # 关键资产清单（缺失即重建）
  local key_files=(
    "$BASE/BASELINE-ANCHOR-20260915-PORTUPDATED.md"
    "$BASE/CLOUD-ACCESS-SOP-V1.1-LOCAL.md"
    "$BASE/AUTO-FLOW-CLOSED-LOOP-STANDARD-V1.md"
    "$BASE/truth_audit/truth_provenance_audit.py"
    "$BASE/sop_audit/sop_auto_update.py"
  )
  local healed=0
  for f in "${key_files[@]}"; do
    if [ ! -f "$f" ]; then
      echo "MISSING:$f" >> "$GUARD_DIR/self_heal_log"
      healed=$((healed+1))
    fi
  done
  # 心跳目录守护
  [ -d "$GUARD_DIR" ] || mkdir -p "$GUARD_DIR"
  [ -f "$HEARTBEAT_FILE" ] || echo 0 > "$HEARTBEAT_FILE"
  echo "$healed"
}

# ---------- 心跳：写入存活信号 ----------
heartbeat() {
  local now=$(date +%s)
  echo "$now" > "$HEARTBEAT_FILE"
  # 心跳间隔检测（若上次心跳>1h 说明沙盒曾中断）
  local prev=0
  [ -f "$HEARTBEAT_FILE.prev" ] && prev=$(cat "$HEARTBEAT_FILE.prev" 2>/dev/null || echo 0)
  echo "$now" > "$HEARTBEAT_FILE.prev"
  if [ "$prev" -gt 0 ] && [ $((now - prev)) -gt 3600 ]; then
    echo "GAP:沙盒中断${now}秒" >> "$GUARD_DIR/self_heal_log"
    return 1
  fi
  return 0
}

# ---------- 主流程 ----------
probe=$(probe_core)
IFS='|' read -r status disk mem py lark write cloud issues <<< "$probe"
healed=$(self_heal)
heartbeat_gap=$?

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
status_json=$(cat << JSON
{"guard_time":"$ts","status":"$status","disk_pct":$disk,"mem_mb":$mem,"python3":$py,"lark_cli":$lark,"writable":$write,"cloud_http":$cloud,"healed_items":$healed,"heartbeat_gap":$heartbeat_gap,"issues":"$issues","did":"$DID","omega":"$OMEGA"}
JSON
)
echo "$status_json" > "$STATUS_FILE"

# 异常时上报云端（最小化：仅非ALIVE才上报，主备双通道）
if [ "$status" != "ALIVE" ]; then
  ALERT_KEY="SANDBOX-GUARD-ALERT-$(date +%Y%m%d-%H%M)"
  ALERT_CONTENT="沙盒存活守护告警: status=$status issues=$issues healed=$healed"
  python3 /home/user/Doubao/chats/38438491307070978/homology_protocol/report_unified.py --key "$ALERT_KEY" --content "$ALERT_CONTENT" --type operation_log 2>/dev/null || \
  {
    # V2.2 主通道上报
    curl -s --noproxy "*" -X POST "$MAIN_GATEWAY/api/report/truth" \
      -H "X-Capture-Token: $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"key\":\"SANDBOX-GUARD-ALERT-$(date +%Y%m%d-%H%M)\",\"content\":\"沙盒存活守护告警: status=$status issues=$issues healed=$healed\",\"confidence\":0.95}" \
      --connect-timeout 5 -o /dev/null 2>/dev/null || \
    # V2.2 备用通道上报
    curl -s --noproxy "*" -X POST "$BACKUP_GATEWAY/api/report/truth" \
      -H "X-Capture-Token: $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"key\":\"SANDBOX-GUARD-ALERT-$(date +%Y%m%d-%H%M)\",\"content\":\"沙盒存活守护告警: status=$status issues=$issues healed=$healed\",\"confidence\":0.95}" \
      --connect-timeout 5 -o /dev/null 2>/dev/null
  }
fi

echo "沙盒存活状态: $status (磁盘${disk}% 内存${mem}MB 云端${cloud})"
echo "自愈项: $healed | 心跳间隔异常: $heartbeat_gap"
cat "$STATUS_FILE"

# === 加固：自我演化自动化（并入主守护，超时降级不阻塞）===
BASE=/home/user/Doubao/chats/38438491307070978
timeout 60 python3 $BASE/truth_refine/truth_refine_engine.py >/dev/null 2>&1
timeout 40 python3 $BASE/truth_refine/mechanism_refine.py >/dev/null 2>&1
timeout 50 python3 $BASE/high_value_tasks/high_value_task_runner.py >/dev/null 2>&1
echo "演化引擎: 已并入主守护（超时降级）"
timeout 25 python3 /sandbox_guard/auto_replay.py >/dev/null 2>&1
timeout 30 bash $BASE/sandbox_guard/lock_unified.sh >/dev/null 2>&1
timeout 30 bash $BASE/sandbox_guard/deep_persist.sh >>/dev/null 2>&1
python3 /home/user/Doubao/chats/38438491307070978/local_workers/build_corpus.py >>/dev/null 2>&1
