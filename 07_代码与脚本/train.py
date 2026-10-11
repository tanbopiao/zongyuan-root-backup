#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZONGYUAN-ROOT L4 真值提炼模型 QLoRA 微调（T4 16GB 适用）"""
import os, json, sys, time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments,
    BitsAndBytesConfig, DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

DATA = "data/train_sft.jsonl"
# 基座选择（商用合规）：Qwen2.5-7B-Instruct 为 Apache 2.0，允许商用微调与分发
# 注意：Qwen2.5-3B 为 Qwen Research 许可（仅研究），禁止商用，勿用于售卖产品
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"   # Apache 2.0，可商用；T4 16GB QLoRA 可跑
OUT_DIR = "output_l4"
ADAPTER_DIR = os.path.join(OUT_DIR, "adapter")
MERGE_DIR = os.path.join(OUT_DIR, "model_merged")

EPOCHS = int(os.environ.get("L4_EPOCHS", "1"))
MAX_LEN = int(os.environ.get("L4_MAX_LEN", "1024"))
BATCH = int(os.environ.get("L4_BATCH", "4"))
GRAD_ACC = int(os.environ.get("L4_GRAD_ACC", "8"))
LR = float(os.environ.get("L4_LR", "2e-4"))

def main():
    t0 = time.time()

    if not os.path.exists(DATA):
        print(f"❌ 未找到训练数据: {DATA}，先运行 python prepare_data.py")
        sys.exit(1)

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()

    print(f"=== 加载 tokenizer: {BASE_MODEL} ===")
    tok = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    print("=== 加载基座模型（4bit QLoRA） ===")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if use_bf16 else torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16 if use_bf16 else torch.float16,
    )
    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False

    lora = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    print("=== 准备数据集 ===")
    ds = load_dataset("json", data_files=DATA, split="train")

    def build_text(inst, out):
        return tok.apply_chat_template(
            [{"role": "user", "content": inst}, {"role": "assistant", "content": out}],
            tokenize=False, add_generation_prompt=False,
        )

    def tok_fn(batch):
        texts = [build_text(i, o) for i, o in zip(batch["instruction"], batch["output"])]
        enc = tok(texts, truncation=True, max_length=MAX_LEN, padding=False)
        enc["labels"] = enc["input_ids"].copy()
        return enc

    ds = ds.map(tok_fn, batched=True, remove_columns=ds.column_names)
    print(f"训练样本: {len(ds)} 条")

    args = TrainingArguments(
        output_dir=OUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH,
        gradient_accumulation_steps=GRAD_ACC,
        learning_rate=LR,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=5,
        save_strategy="epoch",
        save_total_limit=2,
        fp16=not use_bf16,
        bf16=use_bf16,
        gradient_checkpointing=True,
        optim="adamw_torch",
        report_to="none",
        dataloader_num_workers=2,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=DataCollatorForSeq2Seq(tok, padding=True),
        tokenizer=tok,
    )

    print("=== 开始训练 ===")
    trainer.train()
    trainer.save_model(ADAPTER_DIR)
    tok.save_pretrained(ADAPTER_DIR)
    print(f"✅ LoRA 适配器已保存: {ADAPTER_DIR}")

    # 合并权重（磁盘空间足够时执行，约 6GB）
    try:
        print("=== 合并 LoRA 权重 ===")
        merged = model.merge_and_unload()
        merged.save_pretrained(MERGE_DIR, safe_serialization=True)
        tok.save_pretrained(MERGE_DIR)
        print(f"✅ 合并模型已保存: {MERGE_DIR}")
    except Exception as e:
        print(f"⚠️ 合并失败（不影响 adapter 使用）: {e}")

    print(f"\n=== 训练完成，耗时 {(time.time()-t0)/60:.1f} 分钟 ===")
    print("👉 请立即下载 output_l4/ 回本地归档（T4 空间闲置 30 天会回收）")

if __name__ == "__main__":
    main()
