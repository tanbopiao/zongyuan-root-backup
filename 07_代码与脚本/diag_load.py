#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 加载诊断：逐分片全量读取 + transformers 加载"""
import os, json, sys, torch, time
from safetensors import safe_open

path = '/workspace/zongyuan-l4-truth-train/models/Qwen2.5-7B-Instruct'
def log(*a):
    print(*a, flush=True)

log('STEP1: torch', torch.__version__)
idx = json.load(open(os.path.join(path, 'model.safetensors.index.json')))
files = sorted(set(v.split('/')[0] for v in idx['weight_map'].values()))
log('STEP2: index files =', files)

for f in files:
    fp = os.path.join(path, f)
    sz = os.path.getsize(fp)
    t0 = time.time()
    try:
        with safe_open(fp, framework='pt', device='cpu') as sf:
            keys = list(sf.keys())
            n = 0
            for k in keys:
                _ = sf.get_tensor(k)  # 真实读取全部数据
                n += 1
        log(f'STEP3: {f} FULL-READ OK n={n} size={sz} ({time.time()-t0:.1f}s)')
    except Exception as e:
        log(f'STEP3: {f} FULL-READ FAIL size={sz} -> {str(e)[:120]}')

log('STEP4: transformers 加载开始')
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
try:
    m = AutoModelForCausalLM.from_pretrained(path, quantization_config=bnb,
                                             device_map='auto', trust_remote_code=True)
    log('STEP5: MODEL OK')
except Exception as e:
    log(f'STEP5: MODEL FAIL -> {str(e)[:200]}')
