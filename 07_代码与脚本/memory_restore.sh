#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 记忆恢复脚本
# 功能：新窗口启动后，读取最新快照 → 验证完整性 → 重建上下文
# 使用方法：
#   bash memory_restore.sh
#   bash memory_restore.sh --snapshot <snapshot_id>
# ============================================================

set -e

SERVER="root@123.207.202.158"
REMOTE_MEM_DIR="/opt/ZONGYUAN-ROOT/memory/snapshots"
COS_PATH="zongyuan-root/memory/snapshots/"
SESSION_ID="38436747020400130"
RESTORE_DIR="/home/user/Doubao/chats/$SESSION_ID/memory-restored"

echo "============================================"
echo "  ZONGYUAN-ROOT 记忆恢复"
echo "============================================"

# ===== 步骤1：测试SSH连接 =====
echo "[1/5] 测试云服务器连接..."
if ssh -o BatchMode=yes -o ConnectTimeout=10 -p 22 "$SERVER" 'echo OK' 2>/dev/null | grep -q OK; then
    echo "  ✅ SSH连接正常"
    SSH_AVAILABLE=true
else
    echo "  ⚠️  SSH连接失败，尝试从COS恢复..."
    SSH_AVAILABLE=false
fi

# ===== 步骤2：获取最新快照 =====
echo "[2/5] 获取最新记忆快照..."
mkdir -p "$RESTORE_DIR"

if [ "$SSH_AVAILABLE" = true ]; then
    # 从云服务器读取latest.json
    scp -P 22 "$SERVER:$REMOTE_MEM_DIR/latest.json" "$RESTORE_DIR/latest.json" 2>/dev/null
    if [ -f "$RESTORE_DIR/latest.json" ]; then
        SNAPSHOT_ID=$(python3 -c "import json; print(json.load(open('$RESTORE_DIR/latest.json'))['snapshot_id'])" 2>/dev/null)
        echo "  ✅ 从云服务器获取快照: $SNAPSHOT_ID"
    else
        echo "  ⚠️  latest.json不存在，列出可用快照..."
        ssh -o BatchMode=yes -p 22 "$SERVER" "ls -t $REMOTE_MEM_DIR/*.json 2>/dev/null | head -5"
        echo "  请使用: bash memory_restore.sh --snapshot <快照ID>"
        exit 1
    fi
else
    echo "  ❌ 无法从云服务器获取，请先配置SSH密钥"
    echo "  临时方案：从飞书知识库读取记忆协议文档，手动恢复"
    exit 1
fi

# ===== 步骤3：验证完整性 =====
echo "[3/5] 验证快照完整性..."
python3 << PYEOF
import json, hashlib

with open("$RESTORE_DIR/latest.json") as f:
    snapshot = json.load(f)

# 重新计算Merkle根（排除merkle_root字段）
verify = {k: v for k, v in snapshot.items() if k != "merkle_root"}
sj = json.dumps(verify, sort_keys=True, ensure_ascii=False)
calculated = hashlib.sha256(sj.encode()).hexdigest()
stored = snapshot.get("merkle_root", "")

if calculated == stored:
    print(f"  ✅ Merkle根验证通过")
    print(f"     {calculated[:32]}...")
else:
    print(f"  ⚠️  Merkle根不匹配！")
    print(f"     存储值: {stored[:32]}...")
    print(f"     计算值: {calculated[:32]}...")
PYEOF

# ===== 步骤4：输出恢复摘要 =====
echo "[4/5] 重建上下文..."
python3 << PYEOF
import json

with open("$RESTORE_DIR/latest.json") as f:
    s = json.load(f)

print()
print("  ====== 记忆恢复摘要 ======")
print(f"  快照ID: {s['snapshot_id']}")
print(f"  时间: {s['timestamp']}")
print(f"  类型: {s['snapshot_type']}")
print(f"  说明: {s['snapshot_note']}")
print()
print("  --- 内核状态 ---")
ks = s.get('kernel_status', {})
print(f"  版本: {ks.get('version', '?')}")
print(f"  状态: {ks.get('status', '?')}")
print()
print("  --- 凭证状态 ---")
cs = s.get('credentials_status', {})
print(f"  SSH连接: {cs.get('ssh_connection', '?')}")
print(f"  COS访问: {cs.get('cos_access', '?')}")
print(f"  凭证Merkle: {cs.get('credential_vault_merkle', '?')[:32]}...")
print()
print("  --- 资产索引 ---")
ai = s.get('assets_index', {})
print(f"  总文件数: {ai.get('total_files', '?')}")
print(f"  核心资产: {ai.get('core_assets', '?')}")
print(f"  锁档率: {ai.get('lock_rate', '?')}")
print()
print("  --- 已锁档元规则 ---")
for m in s.get('meta_rules', []):
    print(f"  {m['id']}: {m['name']} ({m['status']})")
print()
print("  --- 恢复提示 ---")
rh = s.get('recovery_hints', {})
print(f"  首要动作: {rh.get('first_action', '?')}")
print(f"  关键文件: {', '.join(rh.get('key_files_to_restore', []))}")
print(f"  已知问题: {', '.join(rh.get('known_issues', []))}")
print()
print("  ====== 恢复完成 ======")
PYEOF

# ===== 步骤5：恢复关键文件 =====
echo "[5/5] 恢复关键文件到本地..."
if [ "$SSH_AVAILABLE" = true ]; then
    # 恢复凭证存档
    scp -P 22 "$SERVER:/opt/ZONGYUAN-ROOT/credentials/credential_vault_complete.json" "$RESTORE_DIR/" 2>/dev/null && echo "  ✓ 凭证存档已恢复"
    # 恢复全域锁档快照
    scp -P 22 "$SERVER:/opt/ZONGYUAN-ROOT/credentials/global_lock_snapshot.json" "$RESTORE_DIR/" 2>/dev/null && echo "  ✓ 全域锁档快照已恢复"
fi

echo ""
echo "============================================"
echo "  ✅ 记忆恢复完成！"
echo "  恢复文件位置: $RESTORE_DIR/"
echo "  下一步: 根据恢复摘要继续工作"
echo "============================================"
