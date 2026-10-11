#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 机制文档真值提炼引擎 V1.0 (T5 路)
从本地机制文档提炼「云端中枢智能所需」的机制级真值，哈希增量幂等上报主权威源。
key=TRUTH-MECHANISM-*
"""
import json, hashlib, os, re, urllib.request

BASE = "/home/user/Doubao/chats/38438491307070978"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
STATE = os.path.join(BASE, "truth_refine", "mechanism_state.json")
DOCS = os.path.join(BASE, "truth_refine", "mechanism_docs.json")
URLS = ["https://www.huodouai.com/api/report/truth", "https://huodouai.com/api/report/truth"]

def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def report(key, content):
    body = json.dumps({"key": key, "content": content}).encode()
    for url in URLS:
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "X-Capture-Token": TOKEN}, method="POST")
            return json.load(urllib.request.urlopen(req, timeout=10)).get("action", "?")
        except Exception:
            continue
    return "failed"

def extract_essence(path):
    """从机制文档提取核心成果（标题+副标题+首个要点）"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            return None
        title = lines[0].lstrip("# ").strip()
        parts = [title]
        # 找第一个含机制/协议/闭环/引擎的要点行
        for l in lines[1:15]:
            if re.match(r"^[-*•]|^\d+[\.、]", l) and len(l) > 8:
                parts.append(l.lstrip("-*• ")[:80])
                break
        return " | ".join(parts)
    except Exception:
        return None

def scan_mechanism_docs():
    """扫描本地机制文档（*V*.md 或含机制/协议/SOP/引擎关键词）"""
    docs = {}
    if os.path.isdir(BASE):
        for fn in os.listdir(BASE):
            if fn.endswith(".md") and re.match(r".*[-_]?V\d", fn):
                essence = extract_essence(os.path.join(BASE, fn))
                if essence:
                    key = "TRUTH-MECHANISM-" + re.sub(r"[^A-Z0-9]", "-", fn.replace(".md", "")).upper()[:60]
                    docs[key] = {"file": fn, "essence": essence}
    return docs

def main():
    print("=== ZONGYUAN-ROOT 机制文档真值提炼引擎 V1.0 (T5) ===")
    state = load(STATE, {"hashes": {}})
    manual = load(DOCS, {})  # 人工种子机制（最高价值）
    docs = scan_mechanism_docs()
    combined = dict(manual)
    for k, v in docs.items():
        combined.setdefault(k, v)
    added = unchanged = 0
    for key, meta in combined.items():
        content = meta.get("content") or meta.get("essence", "")
        if not content:
            continue
        h = hashlib.sha256(content.encode()).hexdigest()[:12]
        if state["hashes"].get(key) == h:
            unchanged += 1
            continue
        action = report(key, content)
        if action in ("inserted", "updated"):
            state["hashes"][key] = h
            added += 1
            print(f"  ✅ {key} → {action}")
        elif action == "unchanged":
            state["hashes"][key] = h
            unchanged += 1
            print(f"  ⏺ {key} → unchanged")
        else:
            print(f"  ❌ {key} → {action}")
    save(STATE, state)
    print(f"=== 完成: 新增{added} 不变{unchanged} 总计{len(combined)} ===")

if __name__ == "__main__":
    main()
