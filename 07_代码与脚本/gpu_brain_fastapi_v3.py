#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU 决策大脑 · FastAPI V2 纯路由版
- 修复：移除 Gradio 根挂载（避免抢占路由）；/decide /evolve 异常兜底
- 路由：GET /health（匿名）| POST /decide | POST /evolve | GET /
- 认证：X-API-Key（~/.zr_gpu_tokens.json 0600）
端口 7860（ngrok 映射不变）
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
try:
    from modelscope import AutoModelForCausalLM, AutoTokenizer
    print("[加载通道] modelscope")
except ImportError:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print("[加载通道] transformers+hf-mirror")

MODEL_NAME = os.environ.get("GPU_BRAIN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
print(f"加载模型: {MODEL_NAME} ...")
tok = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, trust_remote_code=True,
                                             torch_dtype=torch.float16, device_map="auto")
model.eval()
print(f"模型就绪 | CUDA: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

SYSTEM = ("你是ZONGYUAN-ROOT元极恒一自治体系的自主决策大脑。基于真值库记忆与系统状态，"
          "从候选任务中决策最高价值行动，输出JSON。遵守：云端为权威先同步再行动；"
          "成果同源幂等上报；通道仅轻量运维；介入只增强不破坏。")

def brain(task_type, context):
    if task_type == "health":
        return {"status": "ok", "cuda": torch.cuda.is_available(), "model": MODEL_NAME}
    print(f"[{task_type}] ctx={str(context)[:80]}", flush=True)
    try:
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": str(context)[:3000]}]
        ids = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                      return_tensors="pt").to(model.device)
        print(f"[{task_type}] input_ids={list(ids.shape)}", flush=True)
    except Exception as e:
        return {"error": "template_failed", "detail": f"{type(e).__name__}: {e}"}
    try:
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=256, do_sample=True,
                                 temperature=0.7, top_p=0.9,
                                 pad_token_id=tok.eos_token_id)
        print(f"[{task_type}] gen_ok out={list(out.shape)}", flush=True)
    except Exception as e:
        return {"error": "generate_failed", "detail": f"{type(e).__name__}: {e}"}
    try:
        text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    except Exception as e:
        return {"error": "decode_failed", "detail": f"{type(e).__name__}: {e}"}
    return {"task_type": task_type, "raw": text}

app = FastAPI(title="ZONGYUAN-ROOT GPU Brain", version="V3.0")

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

@app.get("/health")
async def health():
    return brain("health", "")

@app.post("/decide")
async def decide(req: Request):
    try:
        body = await req.json()
        context = body.get("context") or body.get("prompt") or json.dumps(body, ensure_ascii=False)
        return brain("decide", context)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()[-800:]
        return JSONResponse({"error": "decide_failed", "detail": f"{type(e).__name__}: {e}", "trace": tb}, status_code=500)

@app.post("/evolve")
async def evolve(req: Request):
    try:
        body = await req.json()
        context = body.get("context") or body.get("prompt") or json.dumps(body, ensure_ascii=False)
        return brain("evolve", context)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()[-800:]
        return JSONResponse({"error": "evolve_failed", "detail": f"{type(e).__name__}: {e}", "trace": tb}, status_code=500)

@app.get("/")
async def root():
    return {"service": "ZONGYUAN-ROOT GPU Brain", "version": "V2.0",
            "api": ["GET /health(匿名)", "POST /decide(X-API-Key)", "POST /evolve(X-API-Key)"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
