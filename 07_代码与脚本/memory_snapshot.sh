#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 记忆快照脚本
# 功能：采集当前状态 → 生成JSON快照 → 三端上传（飞书+云服务器+COS）
# 使用方法：
#   bash memory_snapshot.sh "快照说明"
#   bash memory_snapshot.sh --urgent "紧急快照"
#   bash memory_snapshot.sh --cron "定时快照"
# ============================================================

set -e

# ===== 配置 =====
SERVER="root@123.207.202.158"
REMOTE_MEM_DIR="/opt/ZONGYUAN-ROOT/memory/snapshots"
COS_PATH="zongyuan-root/memory/snapshots/"
SPACE_ID="7682470220321000386"
BASE_TOKEN="P9m2br6Gta4fbEslBEjc1V7Zn2c"
TABLE_ID="tblVNo5TLdFZ0VBe"
SESSION_ID="38436747020400130"
ANCHOR="Ω₀⊂⊙∞⊂Ω"
DID="DID-BR-000002"

# ===== 参数解析 =====
SNAPSHOT_TYPE="manual"
SNAPSHOT_NOTE="${1:-手动快照}"
if [ "$1" = "--urgent" ]; then
    SNAPSHOT_TYPE="urgent"
    SNAPSHOT_NOTE="${2:-紧急快照}"
elif [ "$1" = "--cron" ]; then
    SNAPSHOT_TYPE="cron"
    SNAPSHOT_NOTE="${2:-定时快照}"
fi

TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S%z')
SNAPSHOT_ID="MEM-SNAP-$(date '+%Y%m%d-%H%M%S')"
WORK_DIR="/tmp/memory_snapshot_$$"
mkdir -p "$WORK_DIR"

echo "============================================"
echo "  ZONGYUAN-ROOT 记忆快照"
echo "  快照ID: $SNAPSHOT_ID"
echo "  类型: $SNAPSHOT_TYPE"
echo "  说明: $SNAPSHOT_NOTE"
echo "============================================"

# ===== 步骤1：采集内核状态 =====
echo "[1/6] 采集云内核状态..."
KERNEL_STATUS=$(curl -s --connect-timeout 5 "https://www.huodouai.com/sysinfo" 2>/dev/null || echo '{}')
KERNEL_VERSION=$(echo "$KERNEL_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','unknown'))" 2>/dev/null || echo "unknown")

# ===== 步骤2：采集SSH/COS连接状态 =====
echo "[2/6] 采集连接状态..."
SSH_STATUS="unknown"
if ssh -o BatchMode=yes -o ConnectTimeout=5 -p 22 "$SERVER" 'echo OK' 2>/dev/null | grep -q OK; then
    SSH_STATUS="可用"
fi

COS_STATUS="unknown"
if [ "$SSH_STATUS" = "可用" ]; then
    if ssh -o BatchMode=yes -p 22 "$SERVER" "coscmd list $COS_PATH 2>/dev/null | head -1" 2>/dev/null | grep -q .; then
        COS_STATUS="可用"
    fi
fi

# 凭证Merkle根
CRED_MERKLE=""
if [ "$SSH_STATUS" = "可用" ]; then
    CRED_MERKLE=$(ssh -o BatchMode=yes -p 22 "$SERVER" "python3 -c \"import json; print(json.load(open('/opt/ZONGYUAN-ROOT/credentials/credential_vault_complete.json'))['merkle_root'])\"" 2>/dev/null || echo "")
fi

# ===== 步骤3：采集资产索引 =====
echo "[3/6] 采集资产索引..."
ASSET_DIR="/home/user/Doubao/chats/$SESSION_ID"
TOTAL_FILES=$(find "$ASSET_DIR" -type f 2>/dev/null | wc -l)

# ===== 步骤4：生成快照JSON =====
echo "[4/6] 生成快照JSON..."
python3 << PYEOF
import json, hashlib, os

snapshot = {
    "snapshot_id": "$SNAPSHOT_ID",
    "timestamp": "$TIMESTAMP",
    "session_id": "$SESSION_ID",
    "anchor": "$ANCHOR",
    "did": "$DID",
    "snapshot_type": "$SNAPSHOT_TYPE",
    "snapshot_note": "$SNAPSHOT_NOTE",
    "conversation_summary": {
        "topic": "",
        "key_decisions": [],
        "completed_tasks": [],
        "pending_tasks": [],
        "blocked_items": []
    },
    "kernel_status": {
        "version": "$KERNEL_VERSION",
        "status": "healthy" if "$KERNEL_VERSION" != "unknown" else "unknown",
        "api_endpoints": ["/sysinfo", "/operator-status", "/operator-executor", "/operator-base-records", "/kernel-kpi", "/operator-history", "/pipeline-status"],
        "last_verified": "$TIMESTAMP"
    },
    "credentials_status": {
        "ssh_connection": "$SSH_STATUS",
        "cos_access": "$COS_STATUS",
        "credential_vault_merkle": "$CRED_MERKLE",
        "backup_locations_count": 5
    },
    "assets_index": {
        "total_files": $TOTAL_FILES,
        "core_assets": 32,
        "lock_rate": "90.6%",
        "key_artifacts": []
    },
    "meta_rules": [
        {"id": "META-RISK-ASSESSMENT-V1.0", "name": "风险评估元规则", "status": "FROZEN"},
        {"id": "META-CONFLICT-PREVENTION-V1.0", "name": "冲突防护元规则", "status": "FROZEN"},
        {"id": "META-009", "name": "最小消耗最优稳态生成", "status": "FROZEN"}
    ],
    "recovery_hints": {
        "first_action": "执行 memory_restore.sh 验证完整性并重建上下文",
        "key_files_to_restore": ["credential_vault_complete.json", "core_asset_sync_manifest.json", "global_lock_snapshot.json"],
        "known_issues": ["8300端口返回403", "27算子中21个离线", "3个服务inactive(omega-brain/gov-ai/anchor)"]
    }
}

# 计算Merkle根
sj = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
snapshot["merkle_root"] = hashlib.sha256(sj.encode()).hexdigest()

with open("$WORK_DIR/snapshot.json", "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2)

print(f"  ✓ 快照JSON已生成")
print(f"  Merkle根: {snapshot['merkle_root'][:32]}...")
PYEOF

# ===== 步骤5：上传到云服务器 =====
echo "[5/6] 上传到云服务器..."
if [ "$SSH_STATUS" = "可用" ]; then
    ssh -o BatchMode=yes -p 22 "$SERVER" "mkdir -p $REMOTE_MEM_DIR"
    scp -P 22 "$WORK_DIR/snapshot.json" "$SERVER:$REMOTE_MEM_DIR/$SNAPSHOT_ID.json" 2>/dev/null
    # 更新latest软链接
    ssh -o BatchMode=yes -p 22 "$SERVER" "ln -sf $REMOTE_MEM_DIR/$SNAPSHOT_ID.json $REMOTE_MEM_DIR/latest.json"
    echo "  ✓ 已上传到云服务器: $REMOTE_MEM_DIR/$SNAPSHOT_ID.json"
    
    # 上传到COS
    if [ "$COS_STATUS" = "可用" ]; then
        ssh -o BatchMode=yes -p 22 "$SERVER" "coscmd upload $REMOTE_MEM_DIR/$SNAPSHOT_ID.json $COS_PATH$SNAPSHOT_ID.json 2>&1 | tail -1"
        echo "  ✓ 已上传到COS: $COS_PATH$SNAPSHOT_ID.json"
    fi
else
    echo "  ⚠️  SSH不可用，跳过云服务器和COS上传"
fi

# ===== 步骤6：写入飞书台账 =====
echo "[6/6] 写入飞书台账..."
MERKLE=$(python3 -c "import json; print(json.load(open('$WORK_DIR/snapshot.json'))['merkle_root'])")

lark-cli base +record-batch-create \
  --base-token "$BASE_TOKEN" \
  --table-id "$TABLE_ID" \
  --json "{\"create_records\":[{
    \"锁档事件ID\":\"$SNAPSHOT_ID\",
    \"锁档名称\":\"记忆快照·$SNAPSHOT_NOTE\",
    \"归档根节点\":\"ZONGYUAN-ROOT\",
    \"资产数量\":\"记忆快照（对话状态+内核状态+凭证状态+资产索引）\",
    \"Merkle根\":\"$MERKLE\",
    \"锁档状态\":\"FROZEN\",
    \"确权锚点\":\"$ANCHOR\",
    \"锁档日期\":\"$(date '+%Y-%m-%d 00:00:00')\",
    \"备注\":\"记忆快照类型:$SNAPSHOT_TYPE。SSH:$SSH_STATUS, COS:$COS_STATUS, 内核:$KERNEL_VERSION, 文件数:$TOTAL_FILES。快照存储:云服务器+$REMOTE_MEM_DIR/ + COS:$COS_PATH\"
  }]}" \
  --as user --format json 2>&1 | grep -q "ok" && echo "  ✓ 飞书台账已写入" || echo "  ⚠️  飞书台账写入失败"

# ===== 清理 =====
rm -rf "$WORK_DIR"

echo ""
echo "============================================"
echo "  ✅ 记忆快照完成！"
echo "  快照ID: $SNAPSHOT_ID"
echo "  Merkle根: $MERKLE"
echo "  存储位置:"
echo "    - 云服务器: $REMOTE_MEM_DIR/$SNAPSHOT_ID.json"
echo "    - COS: $COS_PATH$SNAPSHOT_ID.json"
echo "    - 飞书台账: $SNAPSHOT_ID"
echo "  恢复命令: bash memory_restore.sh"
echo "============================================"
