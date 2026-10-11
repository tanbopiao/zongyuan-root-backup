#!/usr/bin/env bash
# ZONGYUAN-ROOT 全域锁档补报脚本：通道恢复后运行即可上报云内核
# 用法: bash report_to_kernel.sh [gw_url]  （默认 http://127.0.0.1:9120）
set -e
GW="${1:-http://127.0.0.1:9120}"
python3 - << PYEOF
import json, time, urllib.request
GW = "$GW"
snapshot = json.load(open("$(pwd)/ssh-key-seal-20260912/LOCK-GLOBAL-REPORT-20260912.json"))
payload = {
  "DID": snapshot["did"], "ROOT_OMEGA": "Ω-TAN-7-001",
  "node_id": "doubao-main-agent-001",
  "truths": snapshot["truths"],
  "meta": {"source": "doubao_main_agent", "sync_time": time.strftime("%Y-%m-%d %H:%M:%S"),
           "truth_count": len(snapshot["truths"]), "purpose": "GLOBAL_LOCK_REPORT_SSH_SEAL_RETRY"}
}
req = urllib.request.Request(f"{GW}/api/integration/homo_truths", data=json.dumps(payload).encode(),
                             headers={"Content-Type":"application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as resp:
    print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False, indent=2))
PYEOF
