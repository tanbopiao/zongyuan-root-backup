#!/usr/bin/env bash
# ZONGYUAN-ROOT L4 一键管线：环境 -> 数据 -> 训练 -> 评估
set -euo pipefail

echo "═══════════════════════════════════════"
echo "  ZONGYUAN-ROOT L4 真值提炼模型管线"
echo "  T4 免费基础型 · 60h/月预算"
echo "═══════════════════════════════════════"

echo ""
echo "=== 阶段 1/4 环境安装（~2h） ==="
bash setup.sh

echo ""
echo "=== 阶段 2/4 语料准备（秒级） ==="
python3 prepare_data.py

echo ""
echo "=== 阶段 3/4 QLoRA 微调（~3-4h） ==="
python3 train.py

echo ""
echo "=== 阶段 4/4 评估（~5min） ==="
python3 eval.py

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ 管线完成！立即下载 output_l4/ 回本地"
echo "  tar czf l4_output.tar.gz output_l4"
echo "═══════════════════════════════════════"
