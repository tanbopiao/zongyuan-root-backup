#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 同源协议统一上报通道 V3.0（HOMOLOGY-REPORT-UNIFIED）
优先级：https://huodouai.com/api/report/truth（含语义校验）
     → https://drama.huodouai.com/api/report/truth（同源域名）
     → http://drama.huodouai.com:9120/api/truth/upsert（旧通道回退）
全部失败 → 写入待补发队列
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, time, urllib.request

TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
ENDPOINTS = [
    "https://huodouai.com/api/report/truth",
    "https://www.huodouai.com/api/report/truth",
    "https://drama.huodouai.com/api/report/truth",
    "http://drama.huodouai.com:9120/api/truth/upsert",
]
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"

def report_truth(key, content, ttype="achievement", node_id="local-dev-001"):
    """统一上报：新端点优先，全失败入待补发队列"""
    payload = {"key": key, "node_id": node_id, "DID": "DID-BR-000002",
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": ttype,
               "content": content, "truth_content": content}
    last_err = ""
    for url in ENDPOINTS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                    headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    r = json.loads(resp.read().decode())
                    if r.get("success"):
                        return True, r.get("action"), r.get("truth_count", "")
                    last_err = f"resp:{r}"
            except Exception as e:
                last_err = str(e)
                if attempt < 1: time.sleep(2)
    # 全失败 → 入队
    try:
        d = json.load(open(f"{ANCHOR}/pending_upload_20260916.json"))
        if not isinstance(d, list): d = [d]
        if not any(e.get('key') == key for e in d):
            d.append({"key": key, "truth_type": ttype, "content": content,
                      "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00")})
            json.dump(d, open(f"{ANCHOR}/pending_upload_20260916.json", "w"), ensure_ascii=False, indent=2)
    except Exception:
        pass
    return False, f"error:{last_err[:60]}", ""

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    def argv(name, default=""):
        for i, a in enumerate(args):
            if a == name and i + 1 < len(args):
                return args[i + 1]
        return default
    key = argv("--key", "HOMOLOGY-REPORT-UNIFIED-V3-TEST")
    content = argv("--content", "同源协议统一上报通道V3.0验证（新端点优先+9120回退+入队兜底）")
    ttype = argv("--type", "achievement")
    ok, action, count = report_truth(key, content, ttype)
    print(f"上报: {'✅' if ok else '❌'} action={action} count={count}")
