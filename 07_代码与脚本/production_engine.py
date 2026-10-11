#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 高价值生产引擎 V1.0（攻守兼备·生产型）
在存活守护基础上，把沙盒从"守"升级为"攻守兼备"：
① 真值提取（已有引擎）→ ② 语料主题分析（新）→ ③ 审批待办检查（新）→ ④ 注册表同步 → ⑤ 自动上报
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import subprocess, json, os, re, glob, time, urllib.request
from collections import Counter
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "production")
os.makedirs(OUT_DIR, exist_ok=True)
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
import sys; sys.path.insert(0, "/home/user/Doubao/chats/38438491307070978/homology_protocol")
from report_unified import report_truth as _report_truth
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
TOPIC_KEYWORDS = ['锁档','内核','云端','真值','机制','协议','沙盒','安全','审批','上报','锚点','模型','语料','同源','神经元','演化','归档']

def run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as e:
        return f"ERR:{e}"

def extract_truths():
    """① 真值提取（复用已有引擎）"""
    r = run(["python3", f"{BASE}/model_training/truth_extract_for_model.py"])
    return "✅" in r or "完成" in r, r.split("语料: ")[-1][:80] if "语料: " in r else ""

def analyze_corpus():
    """② 语料主题分析（新）"""
    files = sorted(glob.glob(f"{BASE}/model_training/truth_training_corpus_*.jsonl"))
    if not files: return None
    data = [json.loads(l) for l in open(files[-1])]
    kw_counter = Counter()
    for d in data:
        text = str(d.get('output','')) + ' ' + str(d.get('instruction',''))
        for kw in TOPIC_KEYWORDS:
            if kw in text: kw_counter[kw] += 1
    return {"corpus": files[-1].split('/')[-1], "total": len(data),
            "top_topics": dict(kw_counter.most_common(8))}

def check_approval():
    """③ 审批待办检查（新）"""
    r = run(["lark-cli", "approval", "tasks", "query", "--topic", "1",
             "--user-id-type", "open_id", "--as", "user"])
    try:
        d = json.loads(r)
        if not d.get("ok"):
            return -1, []
        tasks = d.get('data', {}).get('tasks', []) or d.get('data', {}).get('items', []) or []
        return len(tasks), [t.get('title','')[:30] for t in tasks[:3]]
    except Exception:
        return -1, []

def sync_registry():
    """④ 能力注册表同步检查"""
    try:
        d = json.load(open(f"{ANCHOR}/capability_registry.json"))
        return d.get('total', 0), len(d.get('capabilities', []))
    except Exception:
        return 0, 0

def report_truth(key, content):
    payload = {"key": key, "node_id": "local-dev-001", "DID": "DID-BR-000002",
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": "achievement",
               "truth_content": content}
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"http://drama.huodouai.com:9120/api/truth/upsert",
                data=json.dumps(payload).encode(),
                headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                r = json.loads(resp.read().decode())
                return r.get("success"), r.get("action")
        except Exception:
            if attempt < 2: time.sleep(3)
    return False, "error"

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    print("=== 高价值生产引擎 V1.0（攻守兼备·生产型）===")
    report = {"report_id": f"PRODUCTION-{ts}", "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
              "generated_at": datetime.now(timezone.utc).isoformat()}

    print("[1/5] 真值提取...")
    ok, info = extract_truths()
    report["truth_extract"] = {"ok": ok, "info": info}
    print(f"  {'✅' if ok else '❌'} {info}")

    print("[2/5] 语料主题分析...")
    corpus = analyze_corpus()
    report["corpus_analysis"] = corpus
    if corpus:
        print(f"  ✅ {corpus['corpus']} 共{corpus['total']}条")
        print(f"  主题TOP: {', '.join(f'{k}:{v}' for k,v in list(corpus['top_topics'].items())[:5])}")
    else:
        print("  ⚠️ 无语料")

    print("[3/5] 审批待办检查...")
    n_approval, titles = check_approval()
    report["approval_pending"] = {"count": n_approval, "titles": titles}
    print(f"  {'✅ 待办' if n_approval >= 0 else '❌ 查询失败'} {n_approval} 条")

    print("[4/5] 能力注册表同步...")
    total, n_caps = sync_registry()
    report["registry"] = {"total": total, "capabilities": n_caps}
    print(f"  ✅ 注册表 {n_caps} 项能力")

    print("[5/5] 自动上报...")
    content = (f"高价值生产引擎V1.0：真值提取{'成功' if ok else '失败'}"
               f"|语料{corpus['total'] if corpus else 0}条 主题分布{corpus['top_topics'] if corpus else {} }"
               f"|审批待办{n_approval}条"
               f"|能力注册表{n_caps}项")
    ok2, action = report_truth(f"PRODUCTION-{ts}", content)
    report["report_ok"] = ok2
    print(f"  {'✅' if ok2 else '❌'} action={action}")

    with open(os.path.join(OUT_DIR, f"production_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  报告: production/production_{ts}.json")
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
