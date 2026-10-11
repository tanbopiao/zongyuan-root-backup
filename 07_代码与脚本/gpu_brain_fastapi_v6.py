#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU 决策大脑 · FastAPI V6 短剧流水线集成版
- 三内核管理（遵守 NN-SCHEDULING-003 单内核独占）：
    GPU_KERNEL=llm   → Qwen2.5-7B（剧本/分镜/文案/质检）
    GPU_KERNEL=image → SDXL-Turbo（关键帧）
    GPU_KERNEL=video → CogVideoX-1.5B INT4（视频渲染）
- 五类 pipeline 任务：script_gen / storyboard / keyframe / video_render / post_process
- 内核不匹配返回 KERNEL_MISMATCH，由 master 脚本原子切换后重试
- 异步任务 + 断点落盘（V5 继承）
- 测试模式 GPU_BRAIN_MOCK=1 全链路模拟
端口 7860
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, threading, time, uuid, subprocess
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

MOCK = os.environ.get("GPU_BRAIN_MOCK", "0") == "1"
KERNEL = os.environ.get("GPU_KERNEL", "llm")

# ---------- 模型内核（惰性加载，单内核独占） ----------
_model = None; _tok = None
def _load_llm():
    global _model, _tok
    if _model is not None: return
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    try:
        from modelscope import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    _tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True)
    _model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True,
                                                  torch_dtype=torch.float16, device_map="auto")
    _model.eval()

def _load_image():
    """SDXL-Turbo INT8 惰性加载"""
    global _model, _tok
    if _model is not None: return
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    from diffusers import AutoPipelineForText2Image
    import torch
    _model = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")
    _model.to("cuda")

def _load_video():
    """CogVideoX-1.5B INT4 惰性加载"""
    global _model, _tok
    if _model is not None: return
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    from modelscope import AutoModelForCausalLM, AutoTokenizer
    import torch
    _tok = AutoTokenizer.from_pretrained("ZhipuAI/CogVideoX-1.5b", trust_remote_code=True)
    _model = AutoModelForCausalLM.from_pretrained(
        "ZhipuAI/CogVideoX-1.5b", trust_remote_code=True,
        torch_dtype=torch.float16, device_map="auto", load_in_4bit=True)

TASK_PROMPTS = {
    "decide": "你是ZONGYUAN-ROOT自治体系决策大脑，输出JSON决策。",
    "evolve": "你是进化引擎，输出JSON进化建议。",
    "axiom_simulate": "你是元公理仿真验证器，检查自洽性与冲突。输出JSON。",
    "geodesic_search": "你是四维隐空间测地线求解器。输出JSON。",
    "fault_predict": "你是故障推演器，生成自愈预案。输出JSON。",
    "arbitrate_assist": "你是冲突仲裁辅助器（无终审权）。输出JSON。",
    "metric_fit": "你是体系指标拟合器。输出JSON。",
    # ---- 短剧流水线任务 ----
    "script_gen": ("你是短剧编剧。按ZONGYUAN-ROOT短剧流水线规范创作：单集50秒=5镜×10秒；"
                   "继承已锁档角色母版（红裙九尾狐/九天玄女等）；对白每镜≤2句；强视觉驱动。"
                   "输出JSON：{episode, logline, characters, script:[{scene, dialogue, action, emotion}]}"),
    "storyboard": ("你是分镜师。将剧本转为5镜分镜表：每镜含{镜号S01E01-0X, 时长10秒, 景别, 运镜, 画面描述, 对白, 音效, 角色}；"
                   "画面描述必须引用角色母版视觉特征；自动注入MR-BAD反向提示词。输出JSON。"),
    "keyframe": ("你是关键帧提示词工程师。构造文生图提示词：角色母版正向描述+画面描述+场景光影风格(UE5.7光追/伦勃朗光影/Portra400/黑金国风)"
                 "+确权符号Ω₀⊂⊙∞⊂Ω+强制反向MR-BAD黑名单。输出JSON：{positive_prompt, negative_prompt, params:{ratio:9:16, model:SDXL-Turbo}}"),
    "video_render": ("你是视频渲染调度员。将关键帧+运镜转视频渲染指令：9:16竖屏/10秒/CogVideoX-1.5B INT4。"
                     "输出JSON：{frames, motion, duration, params:{ratio:9:16, model:CogVideoX-1.5b}}"),
    "post_process": ("你是后期合成编排员。生成ffmpeg合成指令：片段拼接+字幕烧录+确权叠加+片头片尾。"
                     "输出JSON：{concat_list, subtitle_style, watermark, audio_mix, output}"),
    "promo_gen": ("你是宣发物料策划。生成预告片文案/海报规格/社媒文案。输出JSON。"),
    "prompt_batch": "你是镜头提示词批量生成器，输出JSON数组。",
}

def brain(task_type, context):
    if task_type == "health":
        return {"status": "ok", "cuda": not MOCK, "kernel": KERNEL}
    sys_p = TASK_PROMPTS.get(task_type, TASK_PROMPTS["decide"])
    # 内核匹配检查（MOCK 模式同样执行，保证单内核公理逻辑一致）
    need_kernel = {"script_gen":"llm","storyboard":"llm","promo_gen":"llm","prompt_batch":"llm",
                   "keyframe":"image","video_render":"video"}.get(task_type, "llm")
    if need_kernel != KERNEL:
        return {"error": "KERNEL_MISMATCH", "detail": f"task={task_type} 需 {need_kernel} 内核，当前 {KERNEL}",
                "action": f"请master脚本原子切换到{need_kernel}内核后重试"}
    if MOCK:
        time.sleep(0.2)
        return {"task_type": task_type, "raw": f"[MOCK-{task_type}|{KERNEL}] 输入:{str(context)[:50]} → 仿真通过，输出规范符合流水线SOP"}
    try:
        _load_llm() if need_kernel == "llm" else (_load_image() if need_kernel == "image" else _load_video())
    except Exception as e:
        return {"error": "kernel_load_failed", "detail": f"{type(e).__name__}: {e}"}
    import torch
    msgs = [{"role": "system", "content": sys_p}, {"role": "user", "content": str(context)[:3000]}]
    ids = _tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                   return_tensors="pt").to(_model.device)
    with torch.no_grad():
        out = _model.generate(ids, max_new_tokens=256, do_sample=False, pad_token_id=_tok.eos_token_id)
    text = _tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    if need_kernel == "image":
        try:
            img = _model(prompt=text, num_inference_steps=4, guidance_scale=0.0,
                         height=832, width=480).images[0]
            p = f"/mnt/workspace/active/keyframes/{uuid.uuid4().hex[:8]}.png"
            os.makedirs(os.path.dirname(p), exist_ok=True)
            img.save(p)
            return {"task_type": task_type, "image": p}
        except Exception as e:
            return {"task_type": task_type, "raw": text, "image_error": f"{type(e).__name__}: {e}"}
    return {"task_type": task_type, "raw": text}

app = FastAPI(title="ZONGYUAN-ROOT GPU Brain", version="V6.0-DRAMA")

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
TASKS = {}; TASKS_LOCK = threading.Lock()
STATE_FILE = os.path.expanduser("~/.zr_gpu_tasks.json")
def _save_state():
    with TASKS_LOCK:
        json.dump({k: {kk: (vv if kk != "result" else str(vv)[:200]) for kk, vv in v.items()}
                   for k, v in TASKS.items()}, open(STATE_FILE, "w"), ensure_ascii=False, indent=1)
def _runner(tid, task_type, context):
    try:
        res = brain(task_type, context)
        with TASKS_LOCK:
            TASKS[tid]["status"] = "success"; TASKS[tid]["result"] = res; TASKS[tid]["updated"] = time.time()
    except Exception as e:
        with TASKS_LOCK:
            TASKS[tid]["status"] = "failed"; TASKS[tid]["error"] = f"{type(e).__name__}: {e}"; TASKS[tid]["updated"] = time.time()
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
        if not t: return JSONResponse({"error": "task_not_found", "task_id": tid}, status_code=404)
        return {"task_id": tid, "status": t["status"], "task_type": t["task_type"],
                "result": t["result"], "error": t["error"]}

@app.get("/tasks")
async def list_tasks():
    with TASKS_LOCK:
        return {"count": len(TASKS),
                "tasks": [{"task_id": k, "status": v["status"], "task_type": v["task_type"]} for k, v in list(TASKS.items())[-50:]]}

@app.get("/kernel")
async def kernel_info():
    return {"kernel": KERNEL, "mock": MOCK, "support": {"llm": "Qwen2.5-7B", "image": "SDXL-Turbo", "video": "CogVideoX-1.5B-INT4"}}

@app.get("/health")
async def health():
    return brain("health", "")

@app.get("/")
async def root():
    return {"service": "ZONGYUAN-ROOT GPU Brain", "version": "V6.0-DRAMA",
            "api": ["GET /health", "GET /kernel", "POST /task", "GET /task/{id}", "GET /tasks"],
            "pipeline_tasks": ["script_gen", "storyboard", "keyframe", "video_render", "post_process", "promo_gen"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
