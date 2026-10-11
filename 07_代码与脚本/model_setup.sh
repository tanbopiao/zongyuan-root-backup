#!/usr/bin/env bash
# ZONGYUAN-ROOT L4 训练环境安装（T4 16GB）
set -euo pipefail

echo "=== [1/4] 升级 pip ==="
pip install -U pip -q

echo "=== [2/4] 安装基础库 ==="
pip install -q torch --index-url https://download.pytorch.org/whl/cu121

echo "=== [3/4] 安装训练库 ==="
pip install -q transformers accelerate peft bitsandbytes datasets

echo "=== [4/4] 安装魔搭下载器 ==="
pip install -q modelscope

echo "=== 验证 ==="
python3 - <<'PY'
import torch, transformers, peft, bitsandbytes, datasets
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("gpu:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")
print("transformers:", transformers.__version__)
print("peft:", peft.__version__)
PY
echo "✅ 环境就绪"
