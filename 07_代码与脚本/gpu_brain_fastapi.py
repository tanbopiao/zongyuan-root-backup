#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU决策大脑 · FastAPI路由版 V1.0（本源进化引擎自动获取建议用）
- 新增 FastAPI 路由：GET /health | POST /decide | POST /evolve
- 兼容保留：Gradio /brain（挂载 /，client 无缝升级）
- 端口 7860（与 ngrok 现映射一致，无需改隧道）
用法（魔搭GPU实例）:
  pip install fastapi uvicorn gradio transformers accelerate
  python gpu_brain_fastapi.py
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, torch, threading
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# ===== 模型加载双通道：魔搭内网优先，HuggingFace镜像兜底 =====
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
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, trust_remote_code=True,
    torch_dtype=torch.float16, device_map="auto")
model.eval()
print(f"模型就绪 | CUDA: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

SYSTEM = ("你是ZONGYUAN-ROOT元极恒一自治体系的自主决策大脑。基于真值库记忆与系统状态，"
          "从候选任务中决策最高价值行动，输出JSON。遵守：云端为权威先同步再行动；"
          "成果同源幂等上报；通道仅轻量运维；介入只增强不破坏。")

def brain(task_type, context):
    if task_type == "health":
        return {"status": "ok", "cuda": torch.cuda.is_available(), "model": MODEL_NAME}
    prompt = f"{SYSTEM}\n\n## 输入\n{context[:3000]}\n\n## 输出(JSON)"
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": context[:3000]}]
    ids = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                  return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=512, do_sample=True,
                             temperature=0.7, top_p=0.9,
                             pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    return {"task_type": task_type, "raw": text}

# ===== FastAPI 路由 =====
app = FastAPI(title="ZONGYUAN-ROOT GPU Brain", version="V1.0-FASTAPI")

@app.get("/health")
async def health():
    return JSONResponse(brain("health", ""))

@app.post("/decide")
async def decide(req: Request):
    body = await req.json()
    context = body.get("context") or body.get("prompt") or json.dumps(body, ensure_ascii=False)
    return JSONResponse(brain("decide", context))

@app.post("/evolve")
async def evolve(req: Request):
    body = await req.json()
    context = body.get("context") or body.get("prompt") or json.dumps(body, ensure_ascii=False)
    return JSONResponse(brain("evolve", context))

@app.get("/")
async def root():
    return {"service": "ZONGYUAN-ROOT GPU Brain", "api": ["GET /health", "POST /decide", "POST /evolve", "POST /brain(gradio)"]}


# ===== Token 认证（对外通道）=====
import os as _os
_TOK_FILE = _os.path.expanduser("~/.zr_gpu_tokens.json")
def _load_tokens():
    try:
        d = json.load(open(_TOK_FILE))
        return {t["token"] for t in d.get("tokens", []) if t.get("active")}
    except Exception:
        return set()
AUTH_ENABLED = _os.environ.get("GPU_BRAIN_AUTH", "1") == "1"

@app.middleware("http")
async def auth_mw(request: Request, call_next):
    if not AUTH_ENABLED:
        return await call_next(request)
    path = request.url.path
    if path == "/health" or path == "/":
        return await call_next(request)          # 探活匿名
    key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if key in _load_tokens():
        return await call_next(request)
    from fastapi.responses import JSONResponse as _JR
    return _JR({"error": "unauthorized", "msg": "invalid or missing X-API-Key"}, status_code=401)


# ===== Gradio 兼容（/brain）=====
def gr_brain(task_type, context):
    return json.dumps(brain(task_type, context), ensure_ascii=False)
gr_iface = gr.Interface(fn=gr_brain,
                        inputs=[gr.Dropdown(["decide", "evolve", "health"], label="task_type"),
                                gr.Textbox(lines=5, label="context")],
                        outputs=gr.Textbox(label="output"),
                        title="ZONGYUAN-ROOT GPU Brain")
app.mount("/", gr_iface.app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
