#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZONGYUAN-ROOT L4 评估：抽 N 条真值，对比基座 vs 微调后"""
import os, json, random, sys

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"   # Apache 2.0 可商用；3B 为 Research 许可不可商用
ADAPTER_DIR = "output_l4/adapter"
DATA = "data/train_sft.jsonl"
N = int(os.environ.get("L4_EVAL_N", "10"))
MAX_NEW = 256

def load_model():
    tok = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, device_map="auto", torch_dtype=torch.float16, trust_remote_code=True
    )
    if os.path.isdir(ADAPTER_DIR) and os.listdir(ADAPTER_DIR):
        model = PeftModel.from_pretrained(model, ADAPTER_DIR)
        print(f"✅ 已加载微调适配器: {ADAPTER_DIR}")
    else:
        print("⚠️ 未找到适配器，使用基座模型（对比基线）")
    model.eval()
    return tok, model

def generate(tok, model, inst):
    msgs = [{"role": "user", "content": inst}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=MAX_NEW,
            do_sample=False, pad_token_id=tok.pad_token_id,
        )
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

def main():
    if not os.path.exists(DATA):
        print(f"❌ 未找到数据: {DATA}")
        sys.exit(1)

    samples = [json.loads(l) for l in open(DATA, encoding="utf-8") if l.strip()]
    random.seed(42)
    picks = random.sample(samples, min(N, len(samples)))

    tok, model = load_model()
    results = []
    for i, s in enumerate(picks):
        pred = generate(tok, model, s["instruction"])
        results.append({"instruction": s["instruction"], "expected": s["output"], "predicted": pred})
        print(f"\n[{i+1}/{len(picks)}] 指令: {s['instruction'][:60]}")
        print(f"  期望: {s['output'][:80]}")
        print(f"  生成: {pred[:100]}")

    os.makedirs("output_l4", exist_ok=True)
    with open("output_l4/eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 评估完成，结果: output_l4/eval_results.json")

if __name__ == "__main__":
    main()
