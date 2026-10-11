#!/bin/bash
# ZONGYUAN 实例部署内容一键查询 (instance_scan.sh) | 确权 Ω₀⊂⊙∞⊂Ω | DID-BR-000002
# 零依赖(仅 bash 内置+标准命令), 在魔搭实例终端粘贴执行, 输出部署清单
echo "===HOST==="; hostname; uname -a | cut -c1-120
echo "===HOME==="; ls -la ~ 2>/dev/null | head -40
echo "===FILES(worker/agent/gpu/train/py)==="; find ~ -maxdepth 3 \( -name "*worker*" -o -name "*agent*" -o -name "*gpu*" -o -name "*train*" -o -name "*.py" -o -name "*.sh" \) -type f 2>/dev/null | head -60
echo "===PROC(python/node/worker/agent)==="; ps aux 2>/dev/null | grep -iE "python|node|worker|agent|train|jupyter|uvicorn|fastapi" | grep -v grep | head -25
echo "===PORT==="; (ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | head -20
echo "===GPU==="; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || rocm-smi --showproductname 2>/dev/null || echo "NO_GPU_CLI"
echo "===PYENV==="; python3 --version 2>&1; python3 -c "import torch; print('torch', torch.__version__, '| cuda_avail=', torch.cuda.is_available(), '| hip=', getattr(torch.version,'hip','N/A'))" 2>/dev/null || echo "NO_TORCH"
echo "===NET==="; curl -s -o /dev/null -w "ntfy=%{http_code} " --max-time 4 https://ntfy.sh 2>/dev/null; curl -s -o /dev/null -w "cloud=%{http_code} " --max-time 4 https://www.huodouai.com/api/status 2>/dev/null; curl -s -o /dev/null -w "ms=%{http_code}\n" --max-time 4 https://modelscope.cn 2>/dev/null || echo "NET_FAIL"
echo "===DONE==="
