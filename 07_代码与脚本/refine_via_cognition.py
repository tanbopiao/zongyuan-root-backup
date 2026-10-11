#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 基座认知蒸馏引擎 V1.0（REFINE-VIA-COGNITION）
使命：从豆包基座（运行中的基座模型实例）提炼真值，补充本地结构化的盲区
与 TRUTH-REFINE-ENGINE 的区别：
  - 本地引擎：搬运/结构化本地资产（元法则/能力/语料）
  - 认知引擎：由基座模型基于【运行观察+执行轨迹+资产关联】蒸馏 NEW 真值
    （模式洞察/经验教训/关联发现/演进建议——这些只存在于基座认知中，不在地表数据里）

蒸馏通道（基座每轮填充认知内容）：
  C1 运行洞察 OPS   TRUTH-COGNITION-OPS-YYYYMMDDHHMM（本轮运行模式判定）
  C2 经验教训 LESSON TRUTH-COGNITION-LESSON-{seq}（从轨迹蒸馏的可复用规则）
  C3 关联发现 INSIGHT TRUTH-COGNITION-INSIGHT-{seq}（跨资产关联/演进建议）

增量：内容哈希对比只报新增；幂等；写通道繁忙自动入队兜底
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, sys, hashlib, time, glob
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
OUT_DIR = os.path.join(BASE, "truth_refine")
STATE_FILE = os.path.join(OUT_DIR, "cognition_state.json")
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
    return load_json(STATE_FILE, {}).get("hashes", {})

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

def collect_context():
    """收集基座认知输入材料（运行观察+轨迹+资产）"""
    ctx = {}
    ctx["guard"] = load_json(os.path.join(BASE, "sandbox_guard/guard_status.json"), {})
    # 轨迹
    trail = load_json(os.path.join(ANCHOR, "success_trail.json"), {})
    lessons = load_json(os.path.join(ANCHOR, "error_lessons.json"), {})
    ctx["trail_count"] = len(trail) if isinstance(trail, list) else len(trail.get("items", []))
    ctx["lesson_count"] = len(lessons) if isinstance(lessons, list) else len(lessons.get("items", []))
    # 队列
    q = load_json(QUEUE_FILE, [])
    ctx["queue"] = [e.get("key") for e in (q if isinstance(q, list) else [q]) if e.get("key")]
    # 语料
    cp = os.path.join(BASE, "model_training/truth_training_corpus_20260916.jsonl")
    try:
        with open(cp, encoding="utf-8") as f: ctx["corpus_lines"] = sum(1 for _ in f)
    except Exception: ctx["corpus_lines"] = 0
    # 探索
    hub_files = sorted(glob.glob(os.path.join(BASE, "hub_collab/hub_explore_*.json")), key=os.path.getmtime)
    ctx["hub_latest"] = os.path.basename(hub_files[-1]) if hub_files else "none"
    # 云端状态
    try:
        import urllib.request
        req = urllib.request.Request("https://huodouai.com/api/report/status",
            headers={"X-Capture-Token": TOKEN}, method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            ctx["cloud_status"] = json.loads(resp.read().decode())
    except Exception as e:
        ctx["cloud_status"] = {"error": str(e)[:60]}
    return ctx

def main():
    print("=== ZONGYUAN-ROOT 基座认知蒸馏引擎 V1.0 ===")
    ctx = collect_context()
    print(f"材料: 轨迹{ctx['trail_count']} 教训{ctx['lesson_count']} 语料{ctx['corpus_lines']}条 队列{len(ctx['queue'])}条 云端{ctx.get('cloud_status',{}).get('status','?')}")

    # 基座认知真值由基座注入：/tmp/refine_cognition_input.json 存在则读取
    cognition = []
    inj = "/tmp/refine_cognition_input.json"
    if os.path.exists(inj):
        try:
            cognition = json.load(open(inj))
        except Exception as e:
            print(f"注入读取失败: {e}")

    if not cognition:
        print("无基座注入认知真值（本轮由基座在调用时生成）")
        return 0

    state = load_state()
    new_hashes = {}
    ok, queued, unchanged = 0, 0, 0
    for t in cognition:
        key = t.get("key"); content = t.get("content")
        if not key or not content: continue
        ch = content_hash(content)
        new_hashes[key] = ch
        if state.get(key) == ch:
            unchanged += 1; continue
        status, action = report_truth(key, content, t.get("truth_type", "cognition_truth"))
        if status == "ok": ok += 1
        else: queued += 1
        print(f"  {'✅' if status=='ok' else '📥'} {key} → {action}")
    save_state(new_hashes)
    print(f"=== 完成: 上报{ok} 入队{queued} 未变{unchanged} 总计{len(cognition)} ===")

if __name__ == "__main__":
    main()
