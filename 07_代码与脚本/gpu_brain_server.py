#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU决策大脑服务 V1.0
部署位置：魔搭(ModelScope)免费GPU实例（Notebook 或 创空间）
作用：自主决策进化——接收真值库摘要+状态+候选任务，推理输出最优决策
接口：
  POST /decide    自主决策（输入状态+候选，输出决策+理由）
  GET  /health    健康检查
  POST /evolve    进化建议（输入成果反馈，输出进化方向）
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, torch
from fastapi import FastAPI, Request
import uvicorn

# ===== 模型配置（魔搭免费实例 A10/4090 建议 7B~14B） =====
MODEL_NAME = os.environ.get("GPU_BRAIN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
PORT = int(os.environ.get("GPU_BRAIN_PORT", "7860"))

app = FastAPI(title="ZONGYUAN-ROOT GPU决策大脑")

# 延迟加载模型（避免 import 时卡住健康检查）
_model = None
_tokenizer = None

def get_model():
    global _model, _tokenizer
    if _model is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, trust_remote_code=True,
            torch_dtype=torch.float16, device_map="auto")
        _model.eval()
    return _model, _tokenizer

SYSTEM_PROMPT = """你是ZONGYUAN-ROOT元极恒一自治体系的【自主决策大脑】。
你的任务：基于真值库记忆与当前系统状态，从候选任务中决策出最高价值、最符合最优稳态的行动，
并给出理由与执行要点。决策必须遵守：
1. 以云端为权威，先同步再行动
2. 所有成果同源上报，幂等
3. 通道仅轻量运维（费用边界律），禁大规模数据同步
4. 任何介入只增强不破坏体系"""

@app.get("/health")
async def health():
    return {"status": "ok", "brain": MODEL_NAME, "cuda": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}

@app.post("/decide")
async def decide(req: Request):
    body = await req.json()
    state = body.get("state", "{}")          # 当前系统状态JSON
    candidates = body.get("candidates", [])  # 候选任务列表
    truths = body.get("truths", "")          # 真值库摘要
    model, tok = get_model()
    prompt = f"""{SYSTEM_PROMPT}

## 当前真值库摘要
{truths[:2000]}

## 当前系统状态
{state[:1500]}

## 候选任务
{json.dumps(candidates, ensure_ascii=False)[:1500]}

请输出决策（JSON格式）：
{{"decision": "选择的候选任务ID", "priority": 1-5, "reason": "决策理由", "execute_steps": ["步骤1", ...]}}"""
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.3,
                             pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    # 尝试提取JSON
    try:
        start, end = resp.find("{"), resp.rfind("}")
        return {"decision": json.loads(resp[start:end+1])}
    except Exception:
        return {"decision": {"raw": resp[:800]}}

@app.post("/evolve")
async def evolve(req: Request):
    body = await req.json()
    feedback = body.get("feedback", "")       # 上一轮成果反馈
    model, tok = get_model()
    prompt = f"""{SYSTEM_PROMPT}

## 上一轮执行反馈
{feedback[:2000]}

请给出进化建议（JSON）：{{"evolution": "体系进化方向", "new_rules": ["建议的新规则"], "optimization": ["优化点"]}}"""
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.3,
                             pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    try:
        start, end = resp.find("{"), resp.rfind("}")
        return {"evolution": json.loads(resp[start:end+1])}
    except Exception:
        return {"evolution": {"raw": resp[:800]}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
