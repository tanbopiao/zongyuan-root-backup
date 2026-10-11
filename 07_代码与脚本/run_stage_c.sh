#!/bin/bash
# 阶段C：视频内核(CogVideoX-1.5B) → 5镜短视频（真实渲染）
cd /mnt/workspace
TOKEN=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.zr_gpu_tokens.json'))); print([t['token'] for t in d['tokens'] if t.get('active')][0])")
echo "═══ 下载 CogVideoX-1.5B 权重（modelscope 内网） ═══"
python3 - << 'PYEOF'
try:
    from modelscope import snapshot_download
    p=snapshot_download("ZhipuAI/CogVideoX-1.5b", cache_dir="/mnt/workspace/archive/video_model")
    print("  ✅ 权重下载完成:", p)
except Exception as e:
    print("  ⚠️ 下载异常（不影响后续切换）:", str(e)[:100])
PYEOF
echo "═══ 切换到 video 内核 ═══"
bash switch_kernel.sh video
python3 - << PYEOF
import json, time, urllib.request, os
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":"video_render","context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid, tries=240):
    for _ in range(tries):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=30))
        if r["status"] in ("success","failed"): return r
        time.sleep(5)
    return {"status":"timeout"}
os.makedirs("/mnt/workspace/active/videos", exist_ok=True)
for i in range(1,6):
    ctx=f"镜{i}: 9:16竖屏/10秒/运镜(推拉摇移)/角色动作自然/环境动态(衣袂火焰云雾)/光影变化/CogVideoX-1.5B"
    r=poll(submit(ctx))
    raw=str(r.get("result",{}).get("raw",""))[:60]
    print(f"  镜{i}: {'✅' if r['status']=='success' else '❌'} {r['status']} | {raw}")
PYEOF
echo "═══ 阶段C 完成 ═══"
