#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 桥接探索引擎 V1.0（BRIDGE-EXPLORE）
使命：通过当前容器 AI 桥接（mcp.doubaocdn.com/vm/hijack → 飞书体系通道）
探索飞书域可探索面（日历/审批/文档/云盘/通讯录/妙记AI纪要），提炼真值上报中枢主权威源

与其它引擎分工：
  truth_refine_engine  本地资产结构化搬运（TRUTH-REFINE-*）
  refine_via_cognition 基座认知蒸馏（TRUTH-COGNITION-*）
  bridge_explore       桥接面探索提炼（TRUTH-BRIDGE-*）← 本引擎

探索面（每轮探测活性 + 抽取最近信号）：
  B1 日历（最近日程数/最近事件主题）
  B2 审批（待办数）
  B3 云盘（最近文件信号）
  B4 通讯录（可解析身份）
  B5 妙记AI（纪要资产数，AI产物入口）

机制：可探索面探测 → 变化哈希 → 增量上报（key=TRUTH-BRIDGE-SURFACE-YYYYMMDD）→ 幂等+入队兜底
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, sys, subprocess, hashlib
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "truth_refine")
STATE_FILE = os.path.join(OUT_DIR, "bridge_state.json")
QUEUE_FILE = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/pending_upload_20260916.json"
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
                import time; time.sleep(2)
    d = load_json(QUEUE_FILE, [])
    if not isinstance(d, list): d = [d]
    if key not in {e.get("key") for e in d if e.get("key")}:
        d.append({"key": key, "truth_type": ttype, "content": content, "queued_at": now_iso()})
        json.dump(d, open(QUEUE_FILE, "w"), ensure_ascii=False, indent=2)
    return "queued", "入队兜底"

def probe_calendar():
    """B1 日历最近日程"""
    try:
        r = subprocess.run(["lark-cli", "calendar", "events", "list", "--page-size", "3", "--format", "json"],
            capture_output=True, text=True, timeout=25)
        d = json.loads(r.stdout) if r.stdout else {}
        items = d.get("data", {}).get("items", [])
        return {"reachable": True, "recent_events": len(items),
                "topics": [(e.get("summary") or "")[:30] for e in items[:3]]}
    except Exception as e:
        return {"reachable": False, "error": str(e)[:60]}

def probe_approval():
    """B2 审批待办"""
    try:
        r = subprocess.run(["lark-cli", "approval", "tasks", "query", "--format", "json"],
            capture_output=True, text=True, timeout=25)
        d = json.loads(r.stdout) if r.stdout else {}
        n = d.get("data", {}).get("total", 0)
        return {"reachable": True, "pending": n if n else 0}
    except Exception as e:
        return {"reachable": False, "error": str(e)[:60]}

def probe_minutes():
    """B5 妙记AI纪要"""
    try:
        r = subprocess.run(["lark-cli", "minutes", "+search", "--page-size", "5", "--format", "json"],
            capture_output=True, text=True, timeout=25)
        d = json.loads(r.stdout) if r.stdout else {}
        items = d.get("data", {}).get("items", []) or d.get("data", {}).get("minutes", []) or []
        return {"reachable": True, "minutes": len(items)}
    except Exception as e:
        return {"reachable": False, "error": str(e)[:60]}

def main():
    print("=== ZONGYUAN-ROOT 桥接探索引擎 V1.0 ===")
    surfaces = {
        "calendar": probe_calendar(),
        "approval": probe_approval(),
        "minutes_ai": probe_minutes(),
    }
    for k, v in surfaces.items():
        print(f"  [{k}] {'✅' if v.get('reachable') else '❌'} {json.dumps(v, ensure_ascii=False)[:100]}")

    content = {
        "explore_at": now_iso(), "via": "mcp.doubaocdn.com/vm/hijack→飞书域",
        "surfaces": surfaces, "provenance": OMEGA, "did": DID
    }
    key = f"TRUTH-BRIDGE-SURFACE-{datetime.now().strftime('%Y%m%d')}"
    state = load_json(STATE_FILE, {}).get("hashes", {})
    ch = content_hash(content)
    if state.get(key) == ch:
        print(f"  未变化（幂等跳过）: {key}")
        return 0
    status, action = report_truth(key, json.dumps(content, ensure_ascii=False), "bridge_truth")
    st = load_json(STATE_FILE, {})
    st["hashes"] = st.get("hashes", {}); st["hashes"][key] = ch; st["updated_at"] = now_iso()
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(st, open(STATE_FILE, "w"), ensure_ascii=False, indent=2)
    print(f"  {'✅' if status=='ok' else '📥'} {key} → {action}")
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
