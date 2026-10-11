#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU 决策大脑 · FastAPI V5 异步任务框架
- 异步任务：POST /task 提交 → task_id；GET /task/{id} 轮询状态
- 长推理后台线程执行，API 立即返回，绕开 ngrok 30s 同步超时
- 认证：X-API-Key（/health 匿名）；任务队列内存 + 断点落盘
- 测试模式：GPU_BRAIN_MOCK=1 时 brain 返回模拟结果（本地仿真用）
端口 7860
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, threading, time, uuid, traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

MOCK = os.environ.get("GPU_BRAIN_MOCK", "0") == "1"

if not MOCK:
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    try:
        from modelscope import AutoModelForCausalLM, AutoTokenizer
        print("[加载通道] modelscope")
    except ImportError:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print("[加载通道] transformers+hf-mirror")
    import torch
    MODEL_NAME = os.environ.get("GPU_BRAIN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    print(f"加载模型: {MODEL_NAME} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, trust_remote_code=True,
                                                 torch_dtype=torch.float16, device_map="auto")
    model.eval()
    print(f"模型就绪 | CUDA: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
else:
    MODEL_NAME = "MOCK-MODEL"
    print("[测试模式] GPU_BRAIN_MOCK=1，使用模拟推理")

SYSTEM = ("你是ZONGYUAN-ROOT元极恒一自治体系的自主决策大脑。基于真值库记忆与系统状态，"
          "从候选任务中决策最高价值行动，输出JSON。遵守：云端为权威先同步再行动；"
          "成果同源幂等上报；通道仅轻量运维；介入只增强不破坏。")

TASK_PROMPTS = {
    "axiom_simulate": "你是元公理仿真验证器。对候选公理做逻辑推演：检查自洽性、边界条件、与现有元法则的冲突风险。输出JSON：{consistency, boundary_risks, conflict_with, suggestion}",
    "geodesic_search": "你是四维逻辑隐空间测地线求解器。给定体系当前状态与目标稳态，规划最优演化路径。输出JSON：{optimal_path, alternatives, bottleneck, resource_estimate}",
    "fault_predict": "你是系统故障推演器。基于状态快照推演未来连锁故障并生成自愈预案。输出JSON：{predictions, chain, self_heal_script, rollback}",
    "arbitrate_assist": "你是同源节点冲突仲裁辅助器。核验冲突真值证据链，生成参考报告（无终审权）。输出JSON：{evidence_score, analysis, reference_ruling}",
    "metric_fit": "你是体系指标拟合器。分析多维指标，计算进化得分与短板。输出JSON：{scores, weak_dimensions, next_optimization}",
}

def brain(task_type, context):
    if task_type == "health":
        return {"status": "ok", "cuda": not MOCK, "model": MODEL_NAME}
    sys_p = TASK_PROMPTS.get(task_type, SYSTEM)
    if MOCK:
        time.sleep(0.3)
        return {"task_type": task_type, "raw": f"[MOCK-{task_type}] 输入:{str(context)[:60]} → 输出:仿真通过，风险低，建议提交中枢审批"}
    msgs = [{"role": "system", "content": sys_p},
            {"role": "user", "content": str(context)[:3000]}]
    ids = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                  return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=32, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    return {"task_type": task_type, "raw": text}

app = FastAPI(title="ZONGYUAN-ROOT GPU Brain", version="V5.1-HIGH-CAP")

def _load_tokens():
    try:
        d = json.load(open(os.path.expanduser("~/.zr_gpu_tokens.json")))
        return {t["token"] for t in d.get("tokens", []) if t.get("active")}
    except Exception:
        return set()

AUTH_ENABLED = os.environ.get("GPU_BRAIN_AUTH", "1") == "1"

@app.middleware("http")
async def auth_mw(request: Request, call_next):
    if not AUTH_ENABLED or request.url.path in ("/health", "/"):
        return await call_next(request)
    key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if key in _load_tokens():
        return await call_next(request)
    return JSONResponse({"error": "unauthorized", "msg": "invalid or missing X-API-Key"}, status_code=401)

# ---------- 异步任务队列 ----------
TASKS = {}          # task_id -> {"status","task_type","context","result","error","created","updated"}
TASKS_LOCK = threading.Lock()
STATE_FILE = os.path.expanduser("~/.zr_gpu_tasks.json")

def _save_state():
    with TASKS_LOCK:
        json.dump({k: {kk: (vv if kk != "result" else str(vv)[:200]) for kk, vv in v.items()}
                   for k, v in TASKS.items()}, open(STATE_FILE, "w"), ensure_ascii=False, indent=1)

def _runner(tid, task_type, context):
    try:
        res = brain(task_type, context)
        with TASKS_LOCK:
            TASKS[tid]["status"] = "success"
            TASKS[tid]["result"] = res
            TASKS[tid]["updated"] = time.time()
    except Exception as e:
        with TASKS_LOCK:
            TASKS[tid]["status"] = "failed"
            TASKS[tid]["error"] = f"{type(e).__name__}: {e}"
            TASKS[tid]["updated"] = time.time()
    _save_state()

@app.post("/task")
async def submit_task(req: Request):
    try:
        body = await req.json()
        task_type = body.get("task_type") or body.get("type") or "decide"
        context = body.get("context") or body.get("prompt") or json.dumps(body, ensure_ascii=False)
        tid = uuid.uuid4().hex[:12]
        with TASKS_LOCK:
            TASKS[tid] = {"status": "pending", "task_type": task_type, "context": str(context)[:300],
                          "result": None, "error": None, "created": time.time(), "updated": time.time()}
        threading.Thread(target=_runner, args=(tid, task_type, context), daemon=True).start()
        return {"task_id": tid, "status": "pending", "poll": f"/task/{tid}"}
    except Exception as e:
        return JSONResponse({"error": "submit_failed", "detail": f"{type(e).__name__}: {e}"}, status_code=500)

@app.get("/task/{tid}")
async def get_task(tid: str):
    with TASKS_LOCK:
        t = TASKS.get(tid)
        if not t:
            return JSONResponse({"error": "task_not_found", "task_id": tid}, status_code=404)
        return {"task_id": tid, "status": t["status"], "task_type": t["task_type"],
                "result": t["result"], "error": t["error"]}

@app.get("/tasks")
async def list_tasks():
    with TASKS_LOCK:
        return {"count": len(TASKS),
                "tasks": [{ "task_id": k, "status": v["status"], "task_type": v["task_type"]}
                          for k, v in list(TASKS.items())[-50:]]}

@app.get("/health")
async def health():
    return brain("health", "")

@app.get("/")
async def root():
    return {"service": "ZONGYUAN-ROOT GPU Brain", "version": "V5.0-ASYNC",
            "api": ["GET /health(匿名)", "POST /task(提交异步任务)", "GET /task/{id}(轮询)",
                    "GET /tasks(列表)"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
