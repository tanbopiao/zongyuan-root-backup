#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 高价值真值提取引擎 V1.0
用途：从云端中枢真值 + 本地体系资产中提取高价值真值/规则，生成云服务器端小模型训练语料
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import json, os, re, subprocess, hashlib
from datetime import datetime, timezone
from collections import Counter

BASE = "/home/user/Doubao/chats/38438491307070978"
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
OUT_DIR = os.path.join(BASE, "model_training")
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"

# 高价值类别定义（训练优先级）
CATEGORIES = {
    "axiom_metalaw": {"desc": "公理/元法则/元规则（最高层训练语料）", "weight": 5, "patterns": ["AXIOM", "METALAW", "MR-", "公理", "元法则", "法则"]},
    "protocol": {"desc": "协议/握手/同源规则", "weight": 4.5, "patterns": ["PROTOCOL", "HANDSHAKE", "同源", "协议", "握手"]},
    "mechanism": {"desc": "机制/自动化流程定义", "weight": 4, "patterns": ["MECHANISM", "机制", "AUTO-", "SOP", "流水线", "闭环"]},
    "achievement": {"desc": "成果/里程碑/锁档事件", "weight": 3.5, "patterns": ["LOCK-", "ACHIEVE", "成果", "锁档", "DEPLOY", "EXECUTED"]},
    "security": {"desc": "安全规则/凭证/审计", "weight": 4, "patterns": ["SECURITY", "SECRET", "凭证", "安全", "TOKEN", "审计"]},
    "lesson": {"desc": "经验教训/失败记录/纠错", "weight": 4, "patterns": ["LESSON", "ERROR", "教训", "失败", "纠错", "CONFLICT"]},
    "evolution": {"desc": "演化/自检/优化建议", "weight": 3, "patterns": ["EVOL", "OPTIMIZE", "演化", "自检", "优化"]},
    "operation": {"desc": "运行日志/操作记录", "weight": 2, "patterns": ["OPERATION", "运行", "日志", "STATUS", "GUARD"]},
}

def classify(key, content):
    """对真值条目分类，返回(类别, 权重)"""
    text = (str(key or "") + " " + str(content)[:500]).upper()
    best_cat, best_w = "operation", 2
    for cat, meta in CATEGORIES.items():
        for p in meta["patterns"]:
            if p.upper() in text and meta["weight"] > best_w:
                best_cat, best_w = cat, meta["weight"]
                break
    return best_cat, best_w

def quality_score(key, content):
    """质量评估：结构化程度 + 长度 + 语义密度"""
    c = str(content)
    s = 0
    if len(c) >= 50: s += 2
    if len(c) >= 200: s += 2
    if str(key or "").count("-") >= 2: s += 1
    if any(m in c for m in ["：", ":", "\n", "|"]): s += 2
    if re.search(r'[\u4e00-\u9fff]', c): s += 1
    return min(s, 8)

def collect_local_sources():
    """收集本地高价值数据源"""
    items = []

    # 1. 中枢真值快照（internal/public）
    for f in ["truths_internal.json", "truths_public.json", "truths_public_latest.json"]:
        p = os.path.join(ANCHOR, f)
        if os.path.exists(p):
            try:
                d = json.load(open(p))
                for k in d.get("truths", [])[:2000]:
                    if k: items.append({"key": k, "content": f"真值标识:{k}", "source": f"cloud_snapshot:{f}"})
            except: pass

    # 2. 台账锁档（结构化事实）
    try:
        r = subprocess.run(["lark-cli", "base", "+record-list", "--base-token", "QYn4bjgD6am3OPsxMCkcitcBnzc",
                            "--table-id", "tblIGVWXqu7cr7lZ", "--limit", "200", "--format", "json", "--as", "user"],
                           capture_output=True, text=True, timeout=30)
        rows = json.loads(r.stdout).get("data", {}).get("data", [])
        for row in rows:
            if len(row) >= 10:
                items.append({"key": row[0], "content": f"锁档名称:{row[3]}|日期:{row[4]}|状态:{row[6]}|规则:{row[7]}|备注:{row[9]}",
                              "source": "ledger"})
    except Exception as e:
        print("台账读取:", e)

    # 3. 核心资产 JSON（能力注册表/元法则/同源协议/经验/成功轨迹）
    for f in os.listdir(ANCHOR):
        if not f.endswith(".json"): continue
        try:
            d = json.load(open(os.path.join(ANCHOR, f)))
            if isinstance(d, dict):
                # 提取嵌套内容
                def walk(o, prefix):
                    if isinstance(o, dict):
                        for k, v in o.items():
                            if isinstance(v, (str, int, float)) and len(str(v)) > 10:
                                items.append({"key": f"{prefix}{k}", "content": str(v), "source": f"anchor:{f}"})
                            elif isinstance(v, (dict, list)):
                                walk(v, f"{prefix}{k}.")
                    elif isinstance(o, list):
                        for i, v in enumerate(o[:20]):
                            if isinstance(v, (dict, list)):
                                walk(v, f"{prefix}{i}.")
                            elif len(str(v)) > 10:
                                items.append({"key": f"{prefix}{i}", "content": str(v), "source": f"anchor:{f}"})
                walk(d, f.split(".")[0] + ".")
        except: pass

    # 4. 机制文档（关键 MD 的规则段落）
    key_docs = ["CLOUD-ACCESS-SOP-V1.1-LOCAL.md", "AUTO-FLOW-CLOSED-LOOP-STANDARD-V1.md",
                "SANDBOX-MAX-UTILIZATION-V1.md", "BASELINE-ANCHOR-20260915-PORTUPDATED.md"]
    for f in key_docs:
        p = os.path.join(BASE, f)
        if os.path.exists(p):
            try:
                content = open(p, encoding="utf-8").read()
                # 提取规则行
                for line in content.split("\n"):
                    if re.search(r'^\s*[-*]?\s*(规则|法则|铁律|必须|禁止|适用|MR-|公理|核心)', line) and len(line) > 15:
                        items.append({"key": f"RULE-{f.split('.')[0][:20]}", "content": line.strip()[:400], "source": f"doc:{f}"})
            except: pass

    # 去重
    seen, uniq = set(), []
    for it in items:
        h = hashlib.md5(f"{it['key']}|{it['content'][:80]}".encode()).hexdigest()
        if h not in seen:
            seen.add(h); uniq.append(it)
    return uniq

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=== 高价值真值提取引擎 V1.0 ===")
    print(f"[1/4] 收集本地数据源...")
    items = collect_local_sources()
    print(f"  收集 {len(items)} 条原始条目")

    print(f"[2/4] 分类与质量评估...")
    classified = []
    for it in items:
        cat, w = classify(it["key"], it["content"])
        q = quality_score(it["key"], it["content"])
        score = w * q
        classified.append({**it, "category": cat, "weight": w, "quality": q, "score": score})
    # 阈值：权重>=3.5 且 质量>=3（过滤低价值运行日志）
    high_value = [c for c in classified if c["weight"] >= 3.5 and c["quality"] >= 3]
    high_value.sort(key=lambda x: -x["score"])
    print(f"  高价值条目: {len(high_value)}/{len(classified)}")

    print(f"[3/4] 生成训练语料...")
    # JSONL 训练语料（instruction/fact 格式）
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    jsonl_path = os.path.join(OUT_DIR, f"truth_training_corpus_{ts}.jsonl")
    rules_path = os.path.join(OUT_DIR, f"truth_rules_{ts}.json")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for c in high_value[:800]:
            rec = {
                "instruction": f"ZONGYUAN-ROOT {c['category']}真值",
                "output": c["content"][:2000],
                "category": c["category"], "weight": c["weight"],
                "source": c["source"], "key": str(c["key"] or "")[:100]
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # 规则集
    rules = {"ruleset_id": f"TRUTH-RULES-{ts}", "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
             "generated_at": datetime.now(timezone.utc).isoformat(),
             "total_collected": len(items), "total_high_value": len(high_value),
             "category_dist": dict(Counter(c["category"] for c in high_value)),
             "top_20": high_value[:20]}
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    print(f"[4/4] 完成")
    print(f"  JSONL 语料: {jsonl_path} ({os.path.getsize(jsonl_path)//1024}KB)")
    print(f"  规则集: {rules_path}")
    print(f"  类别分布: {rules['category_dist']}")
    print(f"  训练语料条数: {min(len(high_value), 800)}")
    print(f"  校验: SHA256={hashlib.sha256(open(jsonl_path,'rb').read()).hexdigest()[:16]}")

if __name__ == "__main__":
    main()
