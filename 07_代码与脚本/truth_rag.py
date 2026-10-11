#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 真值库RAG检索引擎 V1.0
- 语料: 云端真值库 key 列表(32078) + 本地注册表/文档
- 检索: 中英文分词 → 关键词命中排序 top-k
- 详情: 命中 key 经 /api/truths/{key} 拉取 content（带缓存）
- 用法: python3 truth_rag.py "P13 GPU决策" [k=5]
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, re, os, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE, ".rag/truth_keys.json")
CACHE_DIR = os.path.join(BASE, ".rag/cache")
API = "https://www.huodouai.com"

def load_keys():
    if not os.path.exists(KEY_FILE):
        return []
    return json.load(open(KEY_FILE))

def tokenize(text):
    """中英文轻量分词"""
    text = text.lower()
    toks = set(re.findall(r'[a-z0-9_]{2,}', text))
    toks |= set(re.findall(r'[\u4e00-\u9fff]{1,6}', text))
    return toks

def search(query, k=5):
    q_toks = tokenize(query)
    if not q_toks:
        return []
    scored = []
    for key in load_keys():
        kt = tokenize(key)
        hit = len(q_toks & kt)
        if hit > 0:
            scored.append((hit, key))
    scored.sort(key=lambda x: -x[0])
    return [key for _, key in scored[:k]]

def fetch_detail(key):
    """拉取真值详情（带缓存）"""
    cache = os.path.join(CACHE_DIR, key.replace('/', '_') + '.json')
    if os.path.exists(cache):
        return json.load(open(cache))
    try:
        req = urllib.request.Request(f"{API}/api/truths/{urllib.parse.quote(key)}")
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.load(r)
            truth = d.get('truth', {})
            out = {"key": key,
                   "content": truth.get('truth_value') or truth.get('content') or '',
                   "category": truth.get('category') or truth.get('truth_type') or ''}
            json.dump(out, open(cache, 'w'), ensure_ascii=False)
            return out
    except Exception as e:
        return {"key": key, "content": "", "category": "", "error": str(e)[:60]}

def rag_context(query, k=5):
    """返回注入GPU大脑的检索上下文"""
    keys = search(query, k)
    parts = []
    for key in keys:
        d = fetch_detail(key)
        c = (d.get('content') or '').strip()
        parts.append(f"[真值:{key}] {c[:200]}" if c else f"[真值:{key}]")
    return "\n".join(parts) if parts else "(检索无命中)"

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "P13 推理能力"
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(f"═══ RAG检索: {q} (top-{k}) ═══")
    for key in search(q, k):
        d = fetch_detail(key)
        c = (d.get('content') or '')[:80]
        print(f"  {key} | {c}")
    print()
    print("═══ 注入上下文 ═══")
    print(rag_context(q, k)[:600])
