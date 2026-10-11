#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 中枢协同探索引擎 V1.0（HUB-COLLAB-EXPLORE）
① 拉取云端中枢真值库（truths列表）→ ② 锚点变化检测 → ③ 提炼高价值任务线索
④ 与本地能力/元法则对比 → ⑤ 生成任务建议 → ⑥ 自动上报
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, glob, time, urllib.request
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "hub_collab")
os.makedirs(OUT_DIR, exist_ok=True)
STATE_FILE = os.path.join(OUT_DIR, "hub_state.json")
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
import sys; sys.path.insert(0, "/home/user/Doubao/chats/38438491307070978/homology_protocol")
from report_unified import report_truth as _report_truth
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"

def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"last_anchor_id": None, "last_sync": None}

def save_state(s):
    json.dump(s, open(STATE_FILE, "w"), ensure_ascii=False, indent=2)

def fetch_hub_truths():
    """拉取中枢真值列表（优先8021，回退9120）"""
    for port in [8021, 9120]:
        try:
            req = urllib.request.Request(f"http://drama.huodouai.com:{port}/api/truths/",
                headers={"X-Capture-Token": TOKEN}, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                d = json.loads(resp.read().decode())
                if d.get("status") == "ok" or "truth" in d:
                    return d, port
        except Exception:
            continue
    return None, 0

def extract_task_signals(truth):
    """从真值条目提炼任务线索"""
    signals = []
    t = truth or {}
    key = str(t.get("truth_key", ""))
    cat = str(t.get("category", ""))
    # 高价值信号模式
    if any(k in key for k in ["TASK", "MISSION", "DEPLOY", "REQUIRE", "PLAN", "SCHEDULE", "TODO"]):
        signals.append(("任务指令", key[:60]))
    if cat in ["meta_rule", "protocol", "mechanism"]:
        signals.append(("规则更新", key[:60]))
    if "achievement" in cat or "DEPLOY-EXECUTED" in key:
        signals.append(("部署成果", key[:60]))
    return signals

def compare_with_local(signals):
    """与本地机制对比，识别未跟进项"""
    new_items = []
    try:
        d = json.load(open(f"{ANCHOR}/capability_registry.json"))
        local_caps = {c["name_en"] for c in d.get("capabilities", [])}
    except Exception:
        local_caps = set()
    # 本地已知任务（从生产/挖掘报告推断）
    known = {"PRODUCTION", "MINING", "EXTRACT", "LOCK", "GUARD", "REPORT", "CAPABILITY"}
    for kind, sig in signals:
        if not any(k in sig.upper() for k in known):
            new_items.append({"type": kind, "signal": sig})
    return new_items

def report_truth(key, content):
    payload = {"key": key, "node_id": "local-dev-001", "DID": "DID-BR-000002",
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": "achievement",
               "truth_content": content}
    for attempt in range(3):
        try:
            req = urllib.request.Request("http://drama.huodouai.com:9120/api/truth/upsert",
                data=json.dumps(payload).encode(),
                headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                r = json.loads(resp.read().decode())
                return r.get("success"), r.get("action")
        except Exception:
            if attempt < 2: time.sleep(3)
    return False, "error"

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    state = load_state()
    print("=== 中枢协同探索引擎 V1.0 ===")

    print("[1/5] 拉取中枢真值库...")
    data, port = fetch_hub_truths()
    if not data:
        print("  ❌ 云端不可达（波动中），写入待补发队列")
        P = f"{ANCHOR}/pending_upload_20260916.json"
        entry = {"key": f"HUB-EXPLORE-{ts}", "truth_type": "operation_log",
                 "content": "中枢协同探索：云端不可达，待恢复后重试", "queued_at": str(datetime.now())}
        try:
            d = json.load(open(P))
            if not isinstance(d, list): d = [d]
            if not any(e.get('key') == entry['key'] for e in d):
                d.append(entry); json.dump(d, open(P, 'w'), ensure_ascii=False, indent=2)
        except Exception:
            pass
        return

    truth = data.get("truth", {})
    anchor_id = truth.get("id")
    print(f"  ✅ 中枢锚点 id={anchor_id}（port={port}）")

    print("[2/5] 锚点变化检测...")
    changed = state.get("last_anchor_id") is not None and state["last_anchor_id"] != anchor_id
    print(f"  上次={state.get('last_anchor_id')} 本次={anchor_id} {'⚠️ 有变化' if changed else '无变化'}")

    print("[3/5] 提炼任务线索...")
    signals = extract_task_signals(truth)
    print(f"  提炼信号: {len(signals)} 条")
    for s in signals:
        print(f"    - {s[0]}: {s[1]}")

    print("[4/5] 与本地对比识别新任务...")
    new_items = compare_with_local(signals)
    print(f"  未跟进项: {len(new_items)} 条")

    print("[5/5] 上报与报告...")
    content = (f"中枢协同探索：锚点id={anchor_id}" +
               (f"|变化" if changed else "|无变化") +
               f"|信号{len(signals)}|未跟进{len(new_items)}")
    ok, action = report_truth(f"HUB-EXPLORE-{ts}", content)
    print(f"  上报: {'✅' if ok else '❌'} action={action}")

    report = {"report_id": f"HUB-EXPLORE-{ts}", "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
              "generated_at": datetime.now(timezone.utc).isoformat(),
              "hub_anchor_id": anchor_id, "changed": changed,
              "signals": signals, "new_items": new_items, "report_ok": ok}
    with open(os.path.join(OUT_DIR, f"hub_explore_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    state["last_anchor_id"] = anchor_id
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
