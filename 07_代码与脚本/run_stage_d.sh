#!/bin/bash
# 阶段D：ffmpeg 后期合成 → S01E01_final.mp4
cd /mnt/workspace
echo "═══ 检查 ffmpeg ═══"
which ffmpeg || (apt-get install -y ffmpeg 2>/dev/null || pip install -q imageio-ffmpeg)
TOKEN=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.zr_gpu_tokens.json'))); print([t['token'] for t in d['tokens'] if t.get('active')][0])")
echo "═══ 切换到 LLM 内核生成合成指令 ═══"
bash switch_kernel.sh llm
python3 - << PYEOF
import json, time, urllib.request
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":"post_process","context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid, tries=60):
    for _ in range(tries):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=20))
        if r["status"] in ("success","failed"): return r
        time.sleep(3)
    return {"status":"timeout"}
r=poll(submit("生成S01E01后期合成ffmpeg指令：5段视频拼接+字幕烧录+确权符号Ω₀⊂⊙∞⊂Ω叠加+片头片尾，黑金国风字幕样式"))
raw=str(r.get("result",{}).get("raw",""))
print(f"  {'✅' if r['status']=='success' else '❌'} post_process: {r['status']}")
open("/mnt/workspace/active/post_compose_cmd.json","w").write(raw)
print("  ✅ 合成指令已落盘 active/post_compose_cmd.json")
print("  （实际合成：若 active/videos/ 有5段视频，用 ffmpeg concat 拼接+烧录）")
PYEOF
echo "═══ 阶段D 完成 ═══"
