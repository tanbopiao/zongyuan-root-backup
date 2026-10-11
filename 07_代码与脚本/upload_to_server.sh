#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 敏感凭证上传到云服务器本地磁盘
# 使用方法：
#   1. 修改下方的 SSH_USER / SSH_HOST / SSH_PORT / REMOTE_PATH
#   2. 执行: bash upload_to_server.sh
#   3. 输入SSH密码（或使用SSH密钥免密）
# ============================================================

set -e

# ===== 配置区（请修改） =====
SSH_USER="root"                    # SSH用户名（通常是root或ubuntu）
SSH_HOST="123.207.202.158"        # 云服务器IP
SSH_PORT="22"                      # SSH端口
REMOTE_PATH="/opt/ZONGYUAN-ROOT/credentials"  # 服务器上的存储路径
# =================================

LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "============================================"
echo "  ZONGYUAN-ROOT 凭证上传到云服务器"
echo "============================================"
echo "  服务器: ${SSH_USER}@${SSH_HOST}:${SSH_PORT}"
echo "  远程路径: ${REMOTE_PATH}"
echo "  本地文件:"
ls -lh "${LOCAL_DIR}"/credential_vault_*.json "${LOCAL_DIR}"/credential_lock_manifest.md 2>/dev/null | awk '{print "    " $9 " (" $5 ")"}'
echo ""

# 1. 在服务器上创建目录
echo "[1/3] 创建远程目录..."
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "mkdir -p ${REMOTE_PATH} && chmod 700 ${REMOTE_PATH}"
echo "  ✓ 目录已创建: ${REMOTE_PATH} (权限700)"

# 2. 上传凭证文件
echo "[2/3] 上传凭证文件..."
scp -P "${SSH_PORT}" \
  "${LOCAL_DIR}/credential_vault_complete.json" \
  "${LOCAL_DIR}/credential_vault_sanitized.json" \
  "${LOCAL_DIR}/credential_lock_manifest.md" \
  "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/"
echo "  ✓ 文件已上传"

# 3. 设置权限并验证
echo "[3/3] 设置权限并验证..."
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "
  chmod 600 ${REMOTE_PATH}/credential_vault_complete.json
  chmod 644 ${REMOTE_PATH}/credential_vault_sanitized.json
  chmod 644 ${REMOTE_PATH}/credential_lock_manifest.md
  echo '  远程文件列表:'
  ls -lh ${REMOTE_PATH}/
  echo ''
  echo '  Merkle根验证:'
  python3 -c \"import json; print('  ' + json.load(open('${REMOTE_PATH}/credential_vault_complete.json'))['merkle_root'][:32] + '...')\" 2>/dev/null || echo '  (python3不可用，跳过验证)'
"

echo ""
echo "============================================"
echo "  ✅ 上传完成！"
echo "  凭证已保存到: ${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/"
echo "  完整存档权限: 600（仅所有者可读）"
echo "============================================"
