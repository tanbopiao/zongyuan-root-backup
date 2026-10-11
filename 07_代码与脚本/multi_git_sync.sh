#!/bin/bash
# ZONGYUAN-ROOT 多Git平台同步脚本 V1.0
# 同时推送到 AtomGit + GitHub + Gitee 三个平台
# 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
set -e

REPO_DIR="/home/user/ZONGYUAN-ROOT-backup"
cd "$REPO_DIR"

echo "=========================================="
echo "多Git平台同步 V1.0 | DID-BR-000002"
echo "=========================================="

# 检查是否有变更
if [ -z "$(git status --porcelain)" ]; then
    echo "[状态] 无变更 → 空闲跳过"
    exit 0
fi

# 配置多remote（如不存在）
git remote | grep -q "^github$" || git remote add github git@github.com:zongyuangen/zongyuan-root-backup.git 2>/dev/null || true
git remote | grep -q "^gitee$" || git remote add gitee git@gitee.com:zongyuangen/zongyuan-root-backup.git 2>/dev/null || true

echo "[Remote配置]"
git remote -v
echo

# 提交变更
git add -A
COMMIT_MSG="多平台同步自动归档 | DID-BR-000002 | $(date -Iseconds)"
git commit -m "$COMMIT_MSG" 2>&1 | tail -1
echo

# 推送到各平台
SUCCESS=0
FAILED=0
SKIPPED=0

for platform in origin github gitee; do
    PLATFORM_NAME=$(case $platform in
        origin) echo "AtomGit";;
        github) echo "GitHub";;
        gitee) echo "Gitee";;
    esac)
    
    echo "→ 推送到 $PLATFORM_NAME..."
    if git push "$platform" main 2>&1 | tail -3; then
        echo "  ✅ $PLATFORM_NAME 推送成功"
        SUCCESS=$((SUCCESS+1))
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 255 ]; then
            echo "  ⏭ $PLATFORM_NAME 认证未就绪（SSH公钥未添加），跳过"
            SKIPPED=$((SKIPPED+1))
        else
            echo "  ❌ $PLATFORM_NAME 推送失败"
            FAILED=$((FAILED+1))
        fi
    fi
    echo
done

echo "=========================================="
echo "[汇总] 成功: $SUCCESS | 跳过: $SKIPPED | 失败: $FAILED"
echo "=========================================="
