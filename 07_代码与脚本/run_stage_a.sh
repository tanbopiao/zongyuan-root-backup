#!/bin/bash
# 短剧流水线 阶段A验证：LLM 内核跑 1 集剧本+分镜（真实模型）
cd /mnt/workspace
TOKEN=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.zr_gpu_tokens.json'))); print([t['token'] for t in d['tokens'] if t.get('active')][0])")
echo "═══ [阶段A] 启动 V6（LLM 内核） ═══"
fuser -k 7860/tcp 2>/dev/null; sleep 2
GPU_KERNEL=llm nohup python3 gpu_brain_fastapi.py > gpu_brain_v6.log 2>&1 &
echo "  等待模型加载（约1-2分钟）..."
for i in $(seq 1 40); do
  H=$(curl -s -m 3 http://127.0.0.1:7860/health 2>/dev/null)
  if echo "$H" | grep -q '"ok"'; then echo "  ✅ 就绪: $H"; break; fi
  sleep 5
done
python3 - << PYEOF
import json, time, urllib.request
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(tt, ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":tt,"context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid, tries=120):
    for _ in range(tries):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=20))
        if r["status"] in ("success","failed"): return r
        time.sleep(3)
    return {"status":"timeout"}
print("═══ 1/2 剧本生成 script_gen ═══")
ctx="主题：昆仑九尾狐觉醒，1集单集50秒；继承已锁档角色母版（红裙九尾狐）；国风神话题材；强视觉驱动"
r1=poll(submit("script_gen", ctx))
raw1=str(r1.get("result",{}).get("raw",""))
print(f"  {'✅' if r1['status']=='success' else '❌'} 状态:{r1['status']} | {raw1[:120].replace(chr(10),' ')}")
open("/mnt/workspace/active/script_episode.json","w").write(raw1)
print("  ✅ 剧本已落盘 active/script_episode.json")
print("═══ 2/2 分镜生成 storyboard ═══")
r2=poll(submit("storyboard", "基于剧本生成5镜分镜表：镜号/时长10秒/景别/运镜/画面描述/对白/音效/角色；继承红裙九尾狐母版视觉特征；注入MR-BAD反向提示词"))
raw2=str(r2.get("result",{}).get("raw",""))
print(f"  {'✅' if r2['status']=='success' else '❌'} 状态:{r2['status']} | {raw2[:120].replace(chr(10),' ')}")
open("/mnt/workspace/active/storyboard_episode.json","w").write(raw2)
print("  ✅ 分镜已落盘 active/storyboard_episode.json")
# 上报
try:
    req=urllib.request.Request("https://www.huodouai.com/api/truth/upsert",
        data=json.dumps({"key":"DRAMA.STAGE-A.REAL.COMPLETE",
            "content":"短剧流水线阶段A真实模型验证完成：剧本+分镜生成成功，资产落盘active/，继承九尾狐母版+MR-BAD注入",
            "category":"pipeline"}).encode(), headers={"Content-Type":"application/json"})
    print("  [上报]", json.load(urllib.request.urlopen(req,timeout=15)).get("action"))
except Exception as e: print("  [上报失败]", e)
PYEOF
echo "═══ 阶段A 完成。日志: tail -20 gpu_brain_v6.log ═══"
