#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 真值提炼引擎 V1.0（TRUTH-REFINE-ENGINE）
核心使命：不断提炼补齐中枢智能主权威源进化需要的真值
四路提炼：
  T1 元法则真值（metalaw_register_registry.json 全量，逐条结构化）
  T2 能力真值（capability_registry.json 全量，逐条结构化）
  T3 语料就绪状态（truth_training_corpus jsonl 条数/字节/就绪阈值）
  T4 权威源同步元信息（主权威源版本/节点/审计日志，进化基线）
增量机制：state 文件按内容哈希对比，只上报新增/变更（最小额度）
兜底机制：上报失败自动入待补发队列（云端恢复自动补发）
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, sys, hashlib, time
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
OUT_DIR = os.path.join(BASE, "truth_refine")
STATE_FILE = os.path.join(OUT_DIR, "refine_state.json")
QUEUE_FILE = os.path.join(ANCHOR, "pending_upload_20260916.json")
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"

def now_iso():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

def load_json(p, default):
    try:
        with open(p) as f: return json.load(f)
    except Exception: return default

def content_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

def load_state():
    d = load_json(STATE_FILE, {})
    return d.get("hashes", {})

def save_state(hashes):
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump({"hashes": hashes, "updated_at": now_iso()}, open(STATE_FILE, "w"), ensure_ascii=False, indent=2)

def enqueue(key, content, ttype):
    d = load_json(QUEUE_FILE, [])
    if not isinstance(d, list): d = [d]
    keys = {e.get("key") for e in d if e.get("key")}
    if key not in keys:
        d.append({"key": key, "truth_type": ttype, "content": content, "queued_at": now_iso()})
        json.dump(d, open(QUEUE_FILE, "w"), ensure_ascii=False, indent=2)
        return True
    return False

def report_truth(key, content, ttype):
    """统一上报：https 新通道优先，失败入队兜底"""
    payload = {"key": key, "node_id": "local-dev-001", "DID": DID,
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": ttype,
               "content": content, "truth_content": content}
    for url in ["https://www.huodouai.com/api/report/truth",
                "https://huodouai.com/api/report/truth",
                "https://drama.huodouai.com/api/report/truth"]:
        for attempt in range(2):
            try:
                import urllib.request
                req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                    headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=20) as resp:
                    r = json.loads(resp.read().decode())
                    if r.get("success"):
                        return "ok", r.get("action", "?")
            except Exception:
                time.sleep(2)
    enqueue(key, content, ttype)
    return "queued", "入队兜底"

def refine_metalaws():
    """T1 元法则真值提炼（39条）"""
    d = load_json(os.path.join(ANCHOR, "metalaw_register_registry.json"), {})
    items = d.get("items", d.get("metalaws", [])) if isinstance(d, dict) else d
    truths = []
    for m in items:
        mid = m.get("metalaw_id", "")
        if not mid: continue
        truths.append((f"TRUTH-REFINE-METARULE-{mid}", {
            "rule_id": mid, "name_en": m.get("name_en", ""), "name_cn": m.get("name_cn", ""),
            "category": m.get("category_cn", m.get("category", "")), "source": m.get("source", ""),
            "status": "FROZEN", "provenance": OMEGA, "refined_at": now_iso()
        }))
    return truths

def refine_capabilities():
    """T2 能力真值提炼（11项）"""
    d = load_json(os.path.join(ANCHOR, "capability_registry.json"), {})
    items = d.get("capabilities", []) if isinstance(d, dict) else d
    truths = []
    for c in items:
        cid = c.get("cap_id", "")
        if not cid: continue
        truths.append((f"TRUTH-REFINE-CAPABILITY-{cid}", {
            "cap_id": cid, "name": c.get("name", ""), "name_en": c.get("name_en", ""),
            "category": c.get("category", ""), "trigger": c.get("trigger", ""),
            "steps_abbr": (c.get("steps", "") or "")[:120], "status": "ACTIVE", "provenance": OMEGA
        }))
    return truths

def refine_corpus():
    """T3 语料就绪状态真值"""
    corpus_path = os.path.join(BASE, "model_training", "truth_training_corpus_20260916.jsonl")
    lines = 0; size = 0
    try:
        size = os.path.getsize(corpus_path)
        with open(corpus_path, encoding="utf-8") as f: lines = sum(1 for _ in f)
    except Exception: pass
    ready = lines >= 500
    return [(f"TRUTH-REFINE-CORPUS-STATUS", {
        "lines": lines, "bytes": size, "ready_threshold": 500,
        "ready": ready, "purpose": "云服务器端小模型训练真值语料",
        "next_action": "就绪可训练" if ready else f"距就绪差{500-lines}条", "provenance": OMEGA
    })]

def refine_master_meta():
    """T4 权威源同步元信息真值"""
    return [(f"TRUTH-REFINE-MASTER-SOURCE-SYNC", {
        "master": "ZONGYUAN-ROOT 主权威源", "did": DID,
        "metalaws_total": len(refine_metalaws()), "capabilities_total": len(refine_capabilities()),
        "channel": "同源协议统一通道V3.0(https huodouai/www/drama)", "provenance": OMEGA,
        "refined_at": now_iso()
    })]

def main():
    print("=== ZONGYUAN-ROOT 真值提炼引擎 V1.0 ===")
    all_truths = []
    for name, fn in [("元法则", refine_metalaws), ("能力", refine_capabilities),
                     ("语料", refine_corpus), ("权威源", refine_master_meta)]:
        try:
            ts = fn(); all_truths.extend(ts)
            print(f"[{name}] 提炼 {len(ts)} 条")
        except Exception as e:
            print(f"[{name}] 提炼失败: {e}")

    state = load_state()
    new_hashes = {}
    ok, queued, unchanged = 0, 0, 0
    for key, content in all_truths:
        ch = content_hash(content)
        new_hashes[key] = ch
        if state.get(key) == ch:
            unchanged += 1
            continue
        status, action = report_truth(key, json.dumps(content, ensure_ascii=False), "evolution_truth")
        if status == "ok": ok += 1
        else: queued += 1
        print(f"  {'✅' if status=='ok' else '📥'} {key} → {action}")

    save_state(new_hashes)
    print(f"=== 完成: 上报{ok} 入队{queued} 未变{unchanged} 总计{len(all_truths)} ===")

if __name__ == "__main__":
    main()
