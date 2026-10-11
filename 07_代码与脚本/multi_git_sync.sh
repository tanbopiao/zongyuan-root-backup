#!/bin/bash
# ZONGYUAN-ROOT 多Git平台同步脚本 V1.1
# 同时推送到 AtomGit + GitHub + Gitee 三个平台
# 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
set -e

REPO_DIR="/home/user/ZONGYUAN-ROOT-backup"
cd "$REPO_DIR"

echo "=========================================="
echo "多Git平台同步 V1.1 | DID-BR-000002"
echo "平台: AtomGit | GitHub(tanbopiao) | Gitee(huodou-cloud-intelligence-aios)"
echo "=========================================="

# 检查是否有变更
if [ -z "$(git status --porcelain)" ]; then
    echo "[状态] 无变更 → 空闲跳过"
    exit 0
fi

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
    if git push "$platform" main 2>&1 | tail -2; then
        echo "  ✅ $PLATFORM_NAME 推送成功"
        SUCCESS=$((SUCCESS+1))
    else
        echo "  ❌ $PLATFORM_NAME 推送失败（快速跳过）"
        FAILED=$((FAILED+1))
    fi
    echo
done

echo "=========================================="
echo "[汇总] 成功: $SUCCESS | 失败: $FAILED | 跳过: $SKIPPED"
echo "=========================================="
