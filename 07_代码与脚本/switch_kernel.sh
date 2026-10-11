#!/bin/bash
# GPU 大脑内核原子切换（LLM/image/video）
# 用法: bash switch_kernel.sh <llm|image|video>
set -e
cd /mnt/workspace
KERNEL=$1
if [[ ! "$KERNEL" =~ ^(llm|image|video)$ ]]; then
  echo "❌ 内核必须是 llm/image/video"; exit 1
fi
echo "═══ 切换到 [$KERNEL] 内核 ═══"
# 前置清扫（NN-SCHEDULING-003 单内核独占）
fuser -k 7860/tcp 2>/dev/null || true
pkill -f "gpu_brain" 2>/dev/null || true
sleep 2
python3 -c "import torch; torch.cuda.empty_cache()" 2>/dev/null || true
# 启动目标内核
GPU_KERNEL=$KERNEL nohup python3 gpu_brain_fastapi.py > gpu_brain_v6.log 2>&1 &
echo "  等待服务就绪（$KERNEL 内核加载）..."
for i in $(seq 1 60); do
  H=$(curl -s -m 3 http://127.0.0.1:7860/health 2>/dev/null)
  if echo "$H" | grep -q '"ok"'; then echo "  ✅ [$KERNEL] 就绪: $H"; exit 0; fi
  sleep 5
done
echo "  ❌ 服务未就绪，查看日志: tail -20 gpu_brain_v6.log"
exit 1
