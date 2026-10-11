#!/bin/bash
# 魔搭实例一键启用 FastAPI 路由版 GPU 大脑（7860 端口，与 ngrok 现映射一致）
set -e
cd /mnt/workspace
pip install -q fastapi uvicorn gradio transformers accelerate 2>/dev/null | tail -1 || true
curl -sL -o gpu_brain_fastapi.py "https://aka.doubaocdn.com/s/QGllGM7GOO"
python gpu_brain_fastapi.py
