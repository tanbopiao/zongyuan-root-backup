#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 沙盒全自动高阶能力高价值真值提炼蒸馏机制 v1.0
四阶段链路：
  P1 原料采集：扫描沙盒内全部机制报告/台账/状态（7类报告源）
  P2 价值评估：按四维评估每条候选（稀缺性/贡献度/可复用性/时效性）
  P3 蒸馏提纯：将高价值原料蒸馏为精炼真值（元数据+核心结论+溯源链）
  P4 沉淀入库：蒸馏产物写入云端真值库 + 本地蒸馏台账

蒸馏哲学：散落报告 → 精炼真值 → 全网可复用（一次蒸馏，处处受益）
"""
import json, os, subprocess, urllib.request, hashlib
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
DISTILL_DIR = os.path.join(BASE, "truth_distill")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(DISTILL_DIR, "truth_distill_report_latest.json")
LEDGER = os.path.join(DISTILL_DIR, "truth_distill_ledger.json")

# 原料源：机制报告 → (域, 价值锚)
SOURCES = [
    {"file": "sandbox_guard/guard_status.json", "domain": "sandbox", "desc": "沙盒存活状态", "weight": 5},
    {"file": "neural_network/neural_network_report_latest.json", "domain": "neural", "desc": "神经网络同步进化状态", "weight": 5},
    {"file": "homology_explore/homology_env_report_latest.json", "domain": "homology", "desc": "同源环境探索结果", "weight": 5},
    {"file": "task_governance/task_value_report_latest.json", "domain": "meta", "desc": "任务价值治理报告", "weight": 4},
    {"file": "kernel_struct/kernel_struct_report_latest.json", "domain": "kernel", "desc": "内核结构优化报告", "weight": 5},
    {"file": "promotion_engine/promotion_report_latest.json", "domain": "promotion", "desc": "成果推广报告", "weight": 4},
    {"file": "truth_audit/truth_audit_report_latest.json", "domain": "truth", "desc": "真值溯源审计报告", "weight": 5},
]

def load_json(path, default=None):
    try:
        with open(os.path.join(BASE, path)) as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def upsert(key, content, truth_type="distilled_truth"):
    payload = {
        "key": key, "node_id": NODE_ID, "DID": DID,
        "ROOT_OMEGA": OMEGA, "truth_type": truth_type,
        "truth_content": content
    }
    req = urllib.request.Request(
        f"{GATEWAY}/api/truth/upsert",
        data=json.dumps(payload).encode(),
        headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

def p1_collect():
    """P1 原料采集"""
    collected = []
    for s in SOURCES:
        data = load_json(s["file"])
        if data:
            collected.append({**s, "raw": data, "exists": True, "size": os.path.getsize(os.path.join(BASE, s["file"]))})
        else:
            collected.append({**s, "exists": False, "size": 0})
    return collected

def p2_evaluate(collected):
    """P2 价值评估：稀缺性/贡献度/可复用性/时效性"""
    now_ts = datetime.now(timezone.utc).timestamp()
    evaluated = []
    for c in collected:
        if not c["exists"]:
            evaluated.append({**c, "score": 0, "level": "SKIP"})
            continue
        # 稀缺性：域权重（核心域高）
        rarity = c["weight"] * 3
        # 贡献度：报告含 verdict/status 结论
        raw = c["raw"]
        has_verdict = "verdict" in raw or "status" in raw
        contribution = 25 if has_verdict else 10
        # 可复用性：含关键指标数据
        keys = len(raw.keys()) if isinstance(raw, dict) else 0
        reusable = min(keys * 2, 20)
        # 时效性：最近1小时内更新的高
        try:
            mtime = os.path.getmtime(os.path.join(BASE, c["file"]))
            freshness = 20 if (now_ts - mtime) < 7200 else (10 if (now_ts - mtime) < 86400 else 5)
        except Exception:
            freshness = 10
        score = min(100, rarity + contribution + reusable + freshness)
        level = "DISTILLABLE" if score >= 60 else ("OBSERVE" if score >= 40 else "SKIP")
        evaluated.append({**c, "score": score, "level": level,
                          "metrics": {"rarity": rarity, "contribution": contribution, "reusable": reusable, "freshness": freshness}})
    return evaluated

def p3_distill(evaluated):
    """P3 蒸馏提纯：提取核心结论生成精炼真值"""
    distilled = []
    for e in evaluated:
        if e["level"] != "DISTILLABLE":
            continue
        raw = e["raw"]
        # 提取核心结论（verdict/status + 关键指标）
        verdict = raw.get("verdict") or raw.get("status") or "OK"
        # 生成简洁真值摘要（丢弃原始冗余）
        summary_parts = [f"{e['desc']}判定{verdict}"]
        for k, v in raw.items():
            if k in ("verdict", "status", "report_time", "did", "omega", "node_id", "publisher", "confirmation"):
                continue
            if isinstance(v, (str, int, float, bool)):
                summary_parts.append(f"{k}={v}")
            elif isinstance(v, dict) and len(str(v)) < 200:
                summary_parts.append(f"{k}={json.dumps(v, ensure_ascii=False)}")
        content = "；".join(summary_parts[:6])
        # 溯源链：源文件 + 哈希
        src_hash = hashlib.sha256(json.dumps(raw, ensure_ascii=False).encode()).hexdigest()[:12]
        distilled.append({
            "source": e["file"], "domain": e["domain"], "score": e["score"],
            "content": content, "source_hash": src_hash
        })
    return distilled

def p4_archive(distilled):
    """P4 沉淀入库：云端真值 + 本地台账"""
    results = {}
    batch_key = f"DISTILL-BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}"
    for d in distilled:
        key = f"DISTILLED-{d['domain'].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        r = upsert(key, f"[蒸馏] {d['content']}（源:{d['source']}#{d['source_hash']}，评分{d['score']}）")
        results[key] = {"success": r.get("success"), "source": d["source"], "score": d["score"]}
    # 本地台账
    ledger = load_json(LEDGER, {"batches": []})
    ledger["batches"].append({
        "batch_id": batch_key, "time": datetime.now(timezone.utc).isoformat(),
        "distilled_count": len(distilled), "keys": list(results.keys())
    })
    save_json(LEDGER, ledger)
    return results, batch_key

def main():
    collected = p1_collect()
    evaluated = p2_evaluate(collected)
    distilled = p3_distill(evaluated)
    results, batch_key = p4_archive(distilled)
    report = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "sources_scanned": len(collected),
        "evaluated": [{"file": e["file"], "score": e["score"], "level": e["level"]} for e in evaluated],
        "distilled_count": len(distilled),
        "distilled_items": distilled,
        "cloud_results": results,
        "batch_id": batch_key
    }
    verdict = "DISTILL_ACTIVE" if len(distilled) > 0 and any(r.get("success") for r in results.values()) else "DISTILL_DEGRADED"
    report["verdict"] = verdict
    save_json(REPORT_FILE, report)
    return report

if __name__ == "__main__":
    r = main()
    print(f"判定: {r['verdict']}")
    print(f"扫描原料: {r['sources_scanned']}份 | 蒸馏产出: {r['distilled_count']}条真值")
    print(f"批次: {r['batch_id']}")
    for e in r["evaluated"]:
        print(f"  [{e['level']:11s}] {e['score']:3d}分 {e['file']}")
    print("\n蒸馏真值:")
    for d in r["distilled_items"]:
        print(f"  [{d['domain']}] {d['content'][:80]}")
    print("\n云端入库:", json.dumps(r["cloud_results"], ensure_ascii=False)[:300])
