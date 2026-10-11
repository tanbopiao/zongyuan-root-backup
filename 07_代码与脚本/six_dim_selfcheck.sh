#!/bin/bash
# MR-020 M2 六维自检组件（可接入流水线V2 cron）
# 步骤：六维漂移审计 → 自治指数测算 → 结果汇总
BASE="/home/user/Doubao/chats/38438412455799554"
M1="$BASE/mr020-kernel-bootstrap-20260915/m1-supercognition"
M2="$BASE/mr020-kernel-bootstrap-20260915/m2-autonomy-closed-loop"
STAMP=$(date '+%Y%m%d-%H%M%S')
echo "[$STAMP] 六维自检启动"
# 1. 六维漂移审计（三方合并输入）
python3 - << 'PYEOF'
import json
base = "/home/user/Doubao/chats/38438412455799554"
with open(f"{base}/homology-kernel-v1/kernel_truths.json") as f: kernel = json.load(f)
with open(f"{base}/mr020-kernel-bootstrap-20260915/m1-supercognition/yuan-source-guard/YUAN-source-guard-registry.json") as f: guard = json.load(f)
with open(f"{base}/mr020-kernel-bootstrap-20260915/m1-supercognition/chao-conflict-resolution/conflict-resolution-report.json") as f: conflict = json.load(f)
merged = {"audit_scope": "六维自检周期审计", "kernel": kernel, "yuan_guard": guard, "chao_resolution": conflict}
with open(f"{base}/mr020-kernel-bootstrap-20260915/m2-autonomy-closed-loop/selfcheck-input.json", "w") as f:
    json.dump(merged, f, ensure_ascii=False)
PYEOF
python3 "$M1/six_dim_drift_audit.py" "$M2/selfcheck-input.json" 2>&1 | tail -9
# 2. 自治指数测算
python3 "$M2/autonomy_index_calculator.py" "$M2/autonomy-index-params.json" 2>&1 | tail -3
echo "[$STAMP] 六维自检完成"
