#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 白皮书构建+仿真部署流水线
# 风格: 玄黑鎏金 V1.0 (FROZEN)
# 通道: 本地仿真 → 飞书审批 → TAT部署
# ============================================================
set -e

PIPELINE_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$PIPELINE_DIR/src/whitepaper.md"
DIST_DIR="$PIPELINE_DIR/dist"
VERSION=$(date +%Y%m%d-%H%M%S)
SIMULATE_DIR="$PIPELINE_DIR/simulate-wwwroot"

echo "═══════════════════════════════════════════════"
echo " ZONGYUAN-ROOT 白皮书构建流水线"
echo " 版本: $VERSION"
echo "═══════════════════════════════════════════════"

# ---------- 阶段1：构建 HTML ----------
echo ""
echo "[阶段1/4] Markdown → 玄黑鎏金 HTML..."
cd "$PIPELINE_DIR"
python3 build.py "$SRC" "$DIST_DIR/whitepaper.html" "$VERSION"

# 同步 .md 副本到 dist
cp "$SRC" "$DIST_DIR/whitepaper.md"
echo "✅ MD 副本已同步: dist/whitepaper.md"

# ---------- 阶段2：本地仿真部署 ----------
echo ""
echo "[阶段2/4] 本地仿真部署（模拟 Nginx 根目录）..."
mkdir -p "$SIMULATE_DIR/whitepaper"
cp "$DIST_DIR/whitepaper.html" "$SIMULATE_DIR/whitepaper/index.html"
cp "$DIST_DIR/whitepaper.md" "$SIMULATE_DIR/whitepaper/whitepaper.md"
echo "✅ 仿真部署完成: $SIMULATE_DIR/whitepaper/"
echo "   模拟 URL: http://localhost/whitepaper/"

# ---------- 阶段3：仿真验证 ----------
echo ""
echo "[阶段3/4] 仿真验证..."
HTML_SIZE=$(stat -c%s "$SIMULATE_DIR/whitepaper/index.html" 2>/dev/null || stat -f%z "$SIMULATE_DIR/whitepaper/index.html")
MD_SIZE=$(stat -c%s "$SIMULATE_DIR/whitepaper/whitepaper.md" 2>/dev/null || stat -f%z "$SIMULATE_DIR/whitepaper/whitepaper.md")

# 验证 HTML 关键元素
CHECKS=0
TOTAL=5

if grep -q "玄黑鎏金\|gold\|c9a962" "$SIMULATE_DIR/whitepaper/index.html"; then
  echo "  [✅] 风格校验: 玄黑鎏金配色存在"; CHECKS=$((CHECKS+1))
else
  echo "  [❌] 风格校验: 未找到鎏金配色"
fi

if grep -q "Ω₀⊂⊙∞⊂Ω" "$SIMULATE_DIR/whitepaper/index.html"; then
  echo "  [✅] 确权校验: Ω₀锚点存在"; CHECKS=$((CHECKS+1))
else
  echo "  [❌] 确权校验: 未找到Ω₀锚点"
fi

if grep -q "sidebar\|toc-" "$SIMULATE_DIR/whitepaper/index.html"; then
  echo "  [✅] 目录校验: 侧边目录存在"; CHECKS=$((CHECKS+1))
else
  echo "  [❌] 目录校验: 未找到侧边目录"
fi

if grep -q "<table>" "$SIMULATE_DIR/whitepaper/index.html" || grep -q "<table " "$SIMULATE_DIR/whitepaper/index.html"; then
  echo "  [✅] 内容校验: 表格已渲染"; CHECKS=$((CHECKS+1))
else
  echo "  [❌] 内容校验: 未找到表格"
fi

if [ "$HTML_SIZE" -gt 10000 ]; then
  echo "  [✅] 体积校验: HTML ${HTML_SIZE}B (>10KB)"; CHECKS=$((CHECKS+1))
else
  echo "  [❌] 体积校验: HTML 过小 (${HTML_SIZE}B)"
fi

echo ""
echo "  验证结果: $CHECKS/$TOTAL 通过"

# ---------- 阶段4：生成部署清单 ----------
echo ""
echo "[阶段4/4] 生成部署清单..."
cat > "$DIST_DIR/DEPLOY-MANIFEST.json" << MANIFESTEOF
{
  "pipeline": "ZR-WEBSITE-PIPELINE",
  "version": "$VERSION",
  "build_time": "$(date -Iseconds)",
  "style": "STYLE-GOLD-BLACK-V1.0-FROZEN",
  "artifacts": {
    "html": {
      "path": "dist/whitepaper.html",
      "size_bytes": $HTML_SIZE,
      "deploy_target": "/www/wwwroot/www.huodouai.com/whitepaper/index.html"
    },
    "markdown": {
      "path": "dist/whitepaper.md",
      "size_bytes": $MD_SIZE,
      "deploy_target": "/www/wwwroot/www.huodouai.com/whitepaper/whitepaper.md"
    }
  },
  "simulation": {
    "dir": "$SIMULATE_DIR/whitepaper/",
    "verified": "$CHECKS/$TOTAL",
    "status": "$([ $CHECKS -eq $TOTAL ] && echo 'PASS' || echo 'FAIL')"
  },
  "deploy_channel": "TAT (Tencent Cloud Automation Tool)",
  "server": "123.207.202.158 (腾讯云轻量·OpenCloudOS 9)",
  "domain": "www.huodouai.com",
  "approval_required": true,
  "omega_anchor": "Ω₀⊂⊙∞⊂Ω",
  "did": "DID-BR-000002"
}
MANIFESTEOF
echo "✅ 部署清单: dist/DEPLOY-MANIFEST.json"

echo ""
echo "═══════════════════════════════════════════════"
echo " 构建完成 ｜ 版本 $VERSION"
echo " HTML: $DIST_DIR/whitepaper.html (${HTML_SIZE}B)"
echo " MD:   $DIST_DIR/whitepaper.md (${MD_SIZE}B)"
echo " 仿真: $SIMULATE_DIR/whitepaper/"
echo " 状态: $([ $CHECKS -eq $TOTAL ] && echo '✅ 全部通过 → 可提交审批' || echo '⚠️ 部分未通过 → 需修复')"
echo "═══════════════════════════════════════════════"
