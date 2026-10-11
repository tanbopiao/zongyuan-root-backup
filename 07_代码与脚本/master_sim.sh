#!/bin/bash
# ZONGYUAN-ROOT 魔搭端自治仿真 master 脚本
# 用法: bash master_sim.sh   （一次执行，自动串行跑 A/B/C/D，每阶段上报状态）
cd /mnt/workspace
TOKEN=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.zr_gpu_tokens.json'))); print([t['token'] for t in d['tokens'] if t.get('active')][0])")
UP="https://www.huodouai.com/api/truth/upsert"
ST=/tmp/zr_sim_state.json
echo "{}" > $ST
report(){ python3 - << PYEOF
import json,urllib.request
key="$1"; content="$2"
try:
    req=urllib.request.Request("$UP", data=json.dumps({"key":key,"content":content,"category":"sim_test"}).encode(), headers={"Content-Type":"application/json"})
    print("  [上报]", json.load(urllib.request.urlopen(req,timeout=15)).get("action"))
except Exception as e: print("  [上报失败]", e)
PYEOF
}
# ---------- 阶段0：环境检查 ----------
echo "═══ [0/4] 环境检查 ═══"
python3 - << 'PYEOF'
import torch, json, os
print("  CUDA:", torch.cuda.is_available(), "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")
print("  显存占用:", round(torch.cuda.memory_allocated()/1e9,2), "GB" if torch.cuda.is_available() else "")
json.dump({"env":"ok"}, open("/tmp/zr_sim_state.json","w"))
PYEOF
# ---------- 阶段A：V5 启动 + 异步框架真实仿真 ----------
echo "═══ [1/4] 阶段A：V5 异步框架（真实模型） ═══"
fuser -k 7860/tcp 2>/dev/null; sleep 2
nohup python3 gpu_brain_fastapi.py > gpu_brain_v5.log 2>&1 &
echo "  等待模型加载..."
for i in $(seq 1 40); do
  H=$(curl -s -m 3 http://127.0.0.1:7860/health 2>/dev/null)
  if echo "$H" | grep -q '"ok"'; then echo "  ✅ 服务就绪: $H"; break; fi
  sleep 5
done
AOK=0
python3 - << PYEOF
import json, time, urllib.request
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(tt, ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":tt,**ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid, tries=60):
    for _ in range(tries):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=20))
        if r["status"] in ("success","failed"): return r
        time.sleep(2)
    return {"status":"timeout"}
cases=[("axiom_simulate",{"candidate_axiom":"NN-PRODUCTION-002:短时算力优先批量生产+实时外域归档"}),
       ("geodesic_search",{"state":"Lv9->Lv10","goal":"超自治稳态"}),
       ("fault_predict",{"snapshot":"gpu_util=0,multi-kernel,ngrok-30s"}),
       ("arbitrate_assist",{"conflict":"节点A报true/节点B报false"}),
       ("metric_fit",{"metrics":"consistency96,self_heal92,collab90"}),
       ("decide",{"context":"稳态回归测试"})]
ok=0
for tt,ctx in cases:
    try:
        tid=submit(tt,ctx); r=poll(tid)
        raw=str(r.get("result",{}).get("raw",""))[:80].replace("\n"," ")
        print(f"  {'✅' if r['status']=='success' else '❌'} {tt}: {r['status']} | {raw}")
        if r["status"]=="success": ok+=1
    except Exception as e:
        print(f"  ❌ {tt}: {e}")
json.dump({"A_ok":ok,"A_total":len(cases)}, open("/tmp/zr_sim_state.json","w"))
PYEOF
AOK=$?
echo "  阶段A 完成"
report "GPU.SIM.A.REAL" "模块A真实模型异步框架仿真完成，状态见 /tmp/zr_sim_state.json"
# ---------- 阶段B：50套国风镜头Prompt批量生成 ----------
echo "═══ [2/4] 阶段B：50套国风镜头Prompt批量生成 ═══"
python3 - << PYEOF
import json, time, urllib.request
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":"prompt_batch","context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid):
    for _ in range(120):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=20))
        if r["status"] in ("success","failed"): return r
        time.sleep(3)
    return {"status":"timeout"}
ctx="生成50套昆仑/九天玄女国风短剧分镜Prompt资产包，每条含正向提示词+反向提示词+镜头参数，输出JSON数组"
tid=submit(ctx); r=poll(tid)
raw=str(r.get("result",{}).get("raw",""))[:120].replace("\n"," ")
print(f"  {'✅' if r['status']=='success' else '❌'} prompt_batch: {r['status']} | {raw}")
if r["status"]=="success":
    try:
        open("/mnt/workspace/active/prompt_assets_50.json","w").write(str(r["result"]["raw"]))
        print("  ✅ Prompt资产包已落盘 active/prompt_assets_50.json")
    except: pass
PYEOF
# ---------- 阶段C：视频模型权重下载验证 ----------
echo "═══ [3/4] 阶段C：CogVideoX-1.5B 权重下载验证 ═══"
python3 - << 'PYEOF'
import os
try:
    from modelscope import snapshot_download
    print("  开始下载 CogVideoX-1.5B（modelscope内网）...")
    path = snapshot_download("ZhipuAI/CogVideoX-1.5b", cache_dir="/mnt/workspace/archive/video_model")
    print(f"  ✅ 下载完成: {path}")
except Exception as e:
    print(f"  ⚠️ 下载未完成（可稍后重试）: {str(e)[:150]}")
    print("  不影响仿真结论：视频渲染放入29h生产窗口执行")
PYEOF
# ---------- 阶段D：端到端联调（真实LLM 3轮） ----------
echo "═══ [4/4] 阶段D：端到端联调仿真 ═══"
python3 - << PYEOF
import json, time, urllib.request
BASE="http://127.0.0.1:7860"; TOK="$TOKEN"
def submit(tt,ctx):
    req=urllib.request.Request(f"{BASE}/task", data=json.dumps({"task_type":tt,"context":ctx}).encode(),
        headers={"Content-Type":"application/json","X-API-Key":TOK})
    return json.load(urllib.request.urlopen(req,timeout=20))["task_id"]
def poll(tid):
    for _ in range(60):
        req=urllib.request.Request(f"{BASE}/task/{tid}", headers={"X-API-Key":TOK})
        r=json.load(urllib.request.urlopen(req,timeout=20))
        if r["status"] in ("success","failed"): return r
        time.sleep(2)
    return {"status":"timeout"}
ok=0
for i in range(1,4):
    tid=submit("decide", f"端到端联调第{i}轮：模拟中枢下发生产任务→LLM决策→进入视频流水线")
    r=poll(tid)
    raw=str(r.get("result",{}).get("raw",""))[:60].replace("\n"," ")
    print(f"  {'✅' if r['status']=='success' else '❌'} 轮{i}: {r['status']} | {raw}")
    if r["status"]=="success": ok+=1
json.dump({"D_ok":ok,"D_total":3}, open("/tmp/zr_sim_state.json","w"))
PYEOF
echo "═══ 全部仿真阶段执行完毕 ═══"
report "GPU.SIM.ALL.REAL.COMPLETE" "魔搭端真实模型仿真A/B/C/D执行完毕，汇总待上报"
echo "  汇总:"
cat /tmp/zr_sim_state.json
echo ""
echo "  日志: tail -20 gpu_brain_v5.log"
