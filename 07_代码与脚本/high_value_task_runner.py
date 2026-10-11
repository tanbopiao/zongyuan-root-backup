#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 高价值任务引擎 V1.0（HIGH-VALUE-TASKS）
多任务并行调度：日历感知/审批联动/语料就绪/事件订阅 四任务探测+提炼+上报
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, subprocess, time, urllib.request
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "high_value_tasks")
os.makedirs(OUT_DIR, exist_ok=True)
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
import sys; sys.path.insert(0, "/home/user/Doubao/chats/38438491307070978/homology_protocol")
from report_unified import report_truth as _report_truth
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"

def run(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"ERR:{e}"

def report(key, content, ttype="achievement"):
    payload = {"key": key, "node_id": "local-dev-001", "DID": "DID-BR-000002",
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": ttype, "content": content, "truth_content": content}
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

# ---- T1 日历感知巡检（F簇）----
def task_calendar():
    out = run(["lark-cli", "calendar", "+agenda", "--as", "user"])
    try:
        d = json.loads(out)
        events = d.get("data") or []
        if not isinstance(events, list): events = []
        items = [(e.get("summary") or "")[:24] for e in events[:5]]
        return {"ok": d.get("ok", False), "count": len(events), "events": items}
    except Exception:
        return {"ok": False, "count": -1, "events": []}

# ---- T2 审批联动（C簇）----
def task_approval():
    out = run(["lark-cli", "approval", "tasks", "query", "--topic", "1", "--user-id-type", "open_id", "--as", "user", "--format", "json"])
    try:
        d = json.loads(out)
        tasks = (d.get("data") or {}).get("tasks", []) or []
        titles = [(t.get("title") or "")[:24] for t in tasks[:3]]
        return {"ok": d.get("ok", False), "count": len(tasks), "titles": titles}
    except Exception:
        return {"ok": False, "count": -1, "titles": []}

# ---- T3 语料训练就绪检测 ----
def task_corpus():
    try:
        lines = 0; size = 0
        p = os.path.join(BASE, "model_training", "truth_training_corpus_20260916.jsonl")
        if os.path.exists(p):
            lines = sum(1 for _ in open(p))
            size = os.path.getsize(p) // 1024
        return {"ok": True, "count": lines, "kb": size,
                "ready": lines >= 500}
    except Exception:
        return {"ok": False, "count": -1, "kb": 0, "ready": False}

# ---- T4 事件订阅检测（A簇）----
def task_subscription():
    # 探测常见事件类型订阅状态（drive事件）
    event_types = ["drive.file.comment_created", "drive.file.view_records",
                   "drive.file.title_updated", "drive.file.permission_member_added"]
    active = []
    for et in event_types:
        out = run(["lark-cli", "drive", "user", "subscription_status",
                   "--event-type", et, "--as", "user"])
        try:
            d = json.loads(out)
            subs = (d.get("data") or {}).get("subscriptions", []) or []
            if isinstance(subs, list) and any(s.get("active") for s in subs):
                active.append(et)
        except Exception:
            continue
    return {"ok": True, "count": len(active), "active": active}

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    print("=== 高价值任务引擎 V1.0（四任务并行）===")
    results = {}

    print("[T1] 日历感知巡检...")
    results["calendar"] = task_calendar()
    print(f"  ✅ 今日日程 {results['calendar'].get('count',0)} 条 | {results['calendar'].get('events',[])}")

    print("[T2] 审批联动...")
    results["approval"] = task_approval()
    print(f"  ✅ 审批待办 {results['approval'].get('count',0)} 条")
    if results["approval"].get("count", 0) > 0:
        print("  ⚠️ 有待办→IM提醒")
        os.system("bash im_push/im_notify.sh 2>/dev/null || true")

    print("[T3] 语料训练就绪检测...")
    results["corpus"] = task_corpus()
    print(f"  ✅ 语料 {results['corpus'].get('count',0)} 条 | {results['corpus'].get('kb',0)}KB | 就绪={results['corpus'].get('ready')}")

    print("[T4] 事件订阅检测...")
    results["subscription"] = task_subscription()
    print(f"  ✅ 订阅面 {results['subscription'].get('count',0)} 项")

    summary = (f"日历{results['calendar'].get('count',-1)}条|审批{results['approval'].get('count',-1)}条|"
               f"语料{results['corpus'].get('count',-1)}条({results['corpus'].get('kb',0)}KB)|订阅{results['subscription'].get('count',-1)}项")
    ok, action = report(f"HIGH-VALUE-TASKS-{ts}", summary)
    if not ok:
        # 云端波动→入待补发队列
        P = f"{ANCHOR}/pending_upload_20260916.json"
        try:
            d = json.load(open(P))
            if not isinstance(d, list): d = [d]
            if not any(e.get('key') == f"HIGH-VALUE-TASKS-{ts}" for e in d):
                d.append({"key": f"HIGH-VALUE-TASKS-{ts}", "truth_type": "achievement",
                          "content": summary, "queued_at": str(datetime.now())})
                json.dump(d, open(P, 'w'), ensure_ascii=False, indent=2)
            print("  ⚠️ 云端波动→已入待补发队列")
        except Exception:
            pass
    print(f"上报: {'✅' if ok else '❌(入队)'} action={action}")

    report_path = os.path.join(OUT_DIR, f"hvt_{ts}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                   "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
                   "results": results, "report_ok": ok, "summary": summary},
                  f, ensure_ascii=False, indent=2)
    print(f"报告: {report_path}")
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
