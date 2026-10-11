#!/bin/bash
# 阶段B：图像内核(SDXL-Turbo) → 5张关键帧（真实生成）
cd /mnt/workspace
TOKEN=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.zr_gpu_tokens.json'))); print([t['token'] for t in d['tokens'] if t.get('active')][0])")
echo "═══ 安装 diffusers 依赖 ═══"
pip install -q diffusers transformers accelerate 2>&1 | tail -1
echo "═══ 切换到 image 内核 ═══"
bash switch_kernel.sh image
python3 - << PYEOF
import json, time, urllib.request, os
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":"keyframe","context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid, tries=180):
    for _ in range(tries):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=30))
        if r["status"] in ("success","failed"): return r
        time.sleep(5)
    return {"status":"timeout"}
os.makedirs("/mnt/workspace/active/keyframes", exist_ok=True)
# 读取分镜（若存在）作为关键帧输入
sb=""
try: sb=open("/mnt/workspace/active/storyboard_episode.json").read()[:1500]
except: sb="昆仑九尾狐觉醒，五幕剧情"
for i in range(1,6):
    ctx=f"镜{i}: 继承红裙九尾狐母版视觉特征；{sb[:800]}；UE5.7全局光追/伦勃朗光影/黑金国风；确权符号Ω₀⊂⊙∞⊂Ω；MR-BAD反向"
    r=poll(submit(ctx))
    img=str(r.get("result",{}).get("image",""))
    raw=str(r.get("result",{}).get("raw",""))[:60]
    print(f"  镜{i}: {'✅' if r['status']=='success' else '❌'} {r['status']} | {img or raw}")
PYEOF
echo "═══ 阶段B 完成：关键帧在 active/keyframes/ ═══"
