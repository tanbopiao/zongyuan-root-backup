#!/usr/bin/env bash
# ============================================================
# ZONGYUAN-ROOT 变更前置快照与回滚工具
# 确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
# 用法：
#   snapshot_rollback.sh snapshot <标签>    # 创建快照
#   snapshot_rollback.sh list                # 列出快照
#   snapshot_rollback.sh rollback <标签>    # 回滚到指定快照
#   snapshot_rollback.sh diff <标签>         # 对比当前与快照差异
# ============================================================
set -e
ROOT="/home/user/ZONGYUAN-ROOT"
SNAP_DIR="$ROOT/06_云端中枢同步/snapshots"
mkdir -p "$SNAP_DIR"

cmd_snapshot() {
    local tag="${1:-manual}"
    local ts=$(date +%Y%m%dT%H%M%S)
    local snap="$SNAP_DIR/snap_${ts}_${tag}"
    mkdir -p "$snap"
    # 快照关键目录（排除大体积的审计日志/真值库）
    for d in "01_核心资产锚点" "04_系统配置" "07_代码与脚本" "meta-rules"; do
        [ -d "$ROOT/$d" ] && cp -r "$ROOT/$d" "$snap/" 2>/dev/null || true
    done
    # 记录元信息
    cat > "$snap/MANIFEST.json" <<EOF
{
  "snapshot_id": "snap_${ts}_${tag}",
  "tag": "$tag",
  "timestamp": "$ts",
  "node": "NODE-DEV-DOUBAO-WORK-001",
  "did": "DID-BR-000002",
  "dirs_snapshotted": ["01_核心资产锚点","04_系统配置","07_代码与脚本","meta-rules"]
}
EOF
    local size=$(du -sh "$snap" | cut -f1)
    echo "✅ 快照已创建: snap_${ts}_${tag} (大小: $size)"
    echo "   路径: $snap"
}

cmd_list() {
    echo "可用快照:"
    ls -1dt "$SNAP_DIR"/snap_* 2>/dev/null | while read d; do
        local name=$(basename "$d")
        local size=$(du -sh "$d" | cut -f1)
        local tag=$(grep '"tag"' "$d/MANIFEST.json" 2>/dev/null | cut -d'"' -f4 || echo "?")
        echo "  $name  [$tag]  $size"
    done
}

cmd_rollback() {
    local tag="$1"
    [ -z "$tag" ] && { echo "用法: rollback <快照标签或ID>"; exit 1; }
    local snap=$(ls -1d "$SNAP_DIR"/snap_*"$tag"* 2>/dev/null | head -1)
    [ -z "$snap" ] && { echo "❌ 未找到快照: $tag"; exit 1; }
    echo "⚠ 即将回滚到: $(basename "$snap")"
    echo "  这将覆盖当前 01/04/07/meta-rules 目录"
    read -p "  确认回滚? (输入 YES 确认): " confirm
    [ "$confirm" != "YES" ] && { echo "已取消"; exit 0; }
    # 回滚前先创建安全快照
    cmd_snapshot "pre_rollback_$(basename "$snap")"
    # 执行回滚
    for d in "01_核心资产锚点" "04_系统配置" "07_代码与脚本" "meta-rules"; do
        if [ -d "$snap/$d" ]; then
            rm -rf "$ROOT/$d"
            cp -r "$snap/$d" "$ROOT/$d"
            echo "  ✅ 已回滚: $d"
        fi
    done
    echo "✅ 回滚完成: $(basename "$snap")"
}

cmd_diff() {
    local tag="$1"
    [ -z "$tag" ] && { echo "用法: diff <快照标签或ID>"; exit 1; }
    local snap=$(ls -1d "$SNAP_DIR"/snap_*"$tag"* 2>/dev/null | head -1)
    [ -z "$snap" ] && { echo "❌ 未找到快照: $tag"; exit 1; }
    echo "对比: 当前 vs $(basename "$snap")"
    for d in "01_核心资产锚点" "04_系统配置" "07_代码与脚本" "meta-rules"; do
        [ -d "$snap/$d" ] && diff -rq "$ROOT/$d" "$snap/$d" 2>/dev/null | head -20 || true
    done
}

case "${1:-help}" in
    snapshot) cmd_snapshot "$2" ;;
    list)     cmd_list ;;
    rollback) cmd_rollback "$2" ;;
    diff)     cmd_diff "$2" ;;
    *)        echo "用法: $0 {snapshot|list|rollback|diff} [标签]" ;;
esac
