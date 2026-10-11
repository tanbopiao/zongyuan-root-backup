#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 敏感凭证上传到腾讯云COS
# 前置条件：安装 coscmd 并配置
#   pip install coscmd
#   coscmd config -a <SecretId> -s <SecretKey> -b <BucketName-APPID> -r <Region>
# 使用方法：
#   bash upload_to_cos.sh
# ============================================================

set -e

# ===== COS配置区（请修改） =====
COS_SECRET_ID="your-secret-id"           # 腾讯云SecretId
COS_SECRET_KEY="your-secret-key"         # 腾讯云SecretKey
COS_BUCKET="your-bucket-name-1234567890" # 存储桶名称-APPID
COS_REGION="ap-guangzhou"                 # 地域（广州ap-guangzhou/上海ap-shanghai等）
COS_PATH="zongyuan-root/credentials/"     # COS上的存储路径
# =================================

LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "============================================"
echo "  ZONGYUAN-ROOT 凭证上传到腾讯云COS"
echo "============================================"
echo "  存储桶: ${COS_BUCKET}"
echo "  地域: ${COS_REGION}"
echo "  COS路径: ${COS_PATH}"
echo ""

# 检查coscmd是否安装
if ! command -v coscmd &> /dev/null; then
    echo "[!] coscmd 未安装，正在安装..."
    pip install coscmd -q
    echo "  ✓ coscmd 已安装"
fi

# 配置coscmd
echo "[1/3] 配置coscmd..."
coscmd config -a "${COS_SECRET_ID}" -s "${COS_SECRET_KEY}" -b "${COS_BUCKET}" -r "${COS_REGION}" 2>/dev/null
echo "  ✓ 配置完成"

# 上传文件
echo "[2/3] 上传凭证文件到COS..."
echo "  上传完整存档（含明文，建议开启COS服务端加密）..."
coscmd upload "${LOCAL_DIR}/credential_vault_complete.json" "${COS_PATH}credential_vault_complete.json" 2>&1 | tail -1
echo "  上传脱敏清单..."
coscmd upload "${LOCAL_DIR}/credential_vault_sanitized.json" "${COS_PATH}credential_vault_sanitized.json" 2>&1 | tail -1
echo "  上传锁档文档..."
coscmd upload "${LOCAL_DIR}/credential_lock_manifest.md" "${COS_PATH}credential_lock_manifest.md" 2>&1 | tail -1

# 验证
echo "[3/3] 验证COS文件..."
echo "  COS文件列表:"
coscmd list "${COS_PATH}" 2>&1 | head -10

echo ""
echo "============================================"
echo "  ✅ 上传完成！"
echo "  凭证已保存到COS: cos://${COS_BUCKET}/${COS_PATH}"
echo "  访问域名: https://${COS_BUCKET}.cos.${COS_REGION}.myqcloud.com/${COS_PATH}"
echo ""
echo "  ⚠️  安全建议："
echo "  1. 完整存档(credential_vault_complete.json)含明文，建议设置为私有读写"
echo "  2. 开启COS服务端加密(SSE-COS)保护数据"
echo "  3. 配置COS访问日志，记录所有访问行为"
echo "  4. 定期轮换SecretId/SecretKey"
echo "============================================"
