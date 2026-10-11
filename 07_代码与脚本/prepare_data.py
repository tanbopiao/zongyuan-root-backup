#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZONGYUAN-ROOT L4 语料准备：JSONL -> SFT 格式"""
import json, os, sys

RAW = "data/truth_training_corpus_20260916.jsonl"
OUT = "data/train_sft.jsonl"

def main():
    if not os.path.exists(RAW):
        print(f"❌ 未找到语料: {RAW}（请确认已 git pull）")
        sys.exit(1)

    rows = []
    with open(RAW, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️ 跳过损坏行: {e}")
                continue
            instruction = obj.get("instruction", "").strip()
            output = obj.get("output", "").strip()
            if not instruction or not output:
                continue
            rows.append({"instruction": instruction, "output": output})

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 统计
    from collections import Counter
    cats = Counter()
    with open(RAW, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cats[json.loads(line).get("category", "unknown")] += 1
            except Exception:
                pass

    print(f"✅ 语料就绪: {len(rows)} 条 -> {OUT}")
    print(f"   类别分布: {dict(cats)}")
    if len(rows) < 500:
        print(f"   ⚠️ 距 500 条还差 {500 - len(rows)} 条，等待主控侧补充批次")

if __name__ == "__main__":
    main()
