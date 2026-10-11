#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU决策大脑 · Gradio公网版 V1.1
运行后自动打印公网地址: Running on public URL: https://xxxx.gradio.live
把该URL发给主智能体即可完成接入。
用法（魔搭GPU实例）:
  pip install gradio transformers accelerate
  python gpu_brain_gradio.py
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, torch, gradio as gr

# ===== 模型加载双通道：魔搭内网优先，HuggingFace镜像兜底 =====
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
try:
    from modelscope import AutoModelForCausalLM, AutoTokenizer  # 魔搭内网（实例必通）
    print("[加载通道] modelscope")
except ImportError:
    from transformers import AutoModelForCausalLM, AutoTokenizer  # HF镜像
    print("[加载通道] transformers+hf-mirror")

MODEL_NAME = os.environ.get("GPU_BRAIN_MODEL", "Qwen/Qwen2.5-7B-Instruct")

print(f"加载模型: {MODEL_NAME} ...")
tok = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, trust_remote_code=True,
    torch_dtype=torch.float16, device_map="auto")
model.eval()
print(f"模型就绪 | CUDA: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

SYSTEM = "你是ZONGYUAN-ROOT元极恒一自治体系的自主决策大脑。基于真值库记忆与系统状态，从候选任务中决策最高价值行动，输出JSON。遵守：云端为权威先同步再行动；成果同源幂等上报；通道仅轻量运维；介入只增强不破坏。"

def brain(task_type, context):
    """task_type: decide(决策) / evolve(进化) / health(健康)"""
    if task_type == "health":
        return {"status": "ok", "cuda": torch.cuda.is_available(),
                "model": MODEL_NAME}
    prompt = f"{SYSTEM}\n\n## 输入\n{context[:3000]}\n\n## 输出(JSON)"
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=600, do_sample=True,
                             temperature=0.3, pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    try:
        s, e = resp.find("{"), resp.rfind("}")
        return json.loads(resp[s:e+1])
    except Exception:
        return {"raw": resp[:800]}

with gr.Blocks(title="ZONGYUAN-ROOT GPU决策大脑") as demo:
    gr.Markdown("## 🧠 ZONGYUAN-ROOT GPU决策大脑\n**真值库驱动的自主决策/进化引擎**")
    with gr.Row():
        task_type = gr.Radio(["decide", "evolve", "health"], label="任务类型", value="decide")
        context = gr.Textbox(label="输入上下文（状态+候选任务 / 成果反馈）", lines=6,
                             placeholder='{"state":"Lv9永恒稳态","candidates":["P13推进","Lv10优化"]}')
    btn = gr.Button("🚀 执行", variant="primary")
    out = gr.JSON(label="决策输出")
    btn.click(brain, [task_type, context], out)
    gr.Markdown("确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002")

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)
