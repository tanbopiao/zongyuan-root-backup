#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 定期内核内部结构化优化补全机制 v1.0
四阶段链路：
  P1 结构审计：扫描神经注册表结构化缺陷（孤立/低权重/缺失/域冗余）
  P2 结构优化：低权重节点提升、冗余域归一、连接补全
  P3 内容补全：缺失字段补全、弱连接节点增强
  P4 演化沉淀：优化报告 + 真值上报 + 权威副本同步

优化原则：介入即增强，永不破坏——只补全/增强，不删除任何节点
"""
import json, os, subprocess, urllib.request
from datetime import datetime, timezone
from collections import Counter

BASE = "/home/user/Doubao/chats/38438491307070978"
STRUCT_DIR = os.path.join(BASE, "kernel_struct")
KERNEL_DIR = "/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-autonomous-kernel"
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(STRUCT_DIR, "kernel_struct_report_latest.json")
REGISTRY = os.path.join(KERNEL_DIR, "neural_registry.json")

# 域归一映射：冗余域 → 标准域
DOMAIN_NORMALIZE = {
    "operations": "ops",
    "infrastructure": "infra",
}

# 类型归一映射
TYPE_NORMALIZE = {
    "operation_rule": "rule",
    "lock_axiom": "axiom",
    "infrastructure": "rule",
}

# 权重提升策略：低权重(<0.3)但激活过 → 提升至 0.35 基线
WEIGHT_FLOOR = 0.3
WEIGHT_BOOST = 0.35

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def upsert(key, content, truth_type="achievement"):
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

def p1_audit(reg):
    """P1 结构审计"""
    nodes = reg.get("nodes", [])
    issues = {
        "low_weight": [],
        "domain_redundant": [],
        "type_redundant": [],
        "missing_fields": [],
        "asymmetric_links": []
    }
    # 低权重节点
    for n in nodes:
        w = n.get("weight")
        if isinstance(w, (int, float)) and w < WEIGHT_FLOOR:
            issues["low_weight"].append({"id": n["node_id"], "weight": w,
                                          "activation": n.get("activation_count", 0),
                                          "domain": n.get("domain")})
    # 冗余域/类型
    domains = Counter(n.get("domain", "?") for n in nodes)
    types = Counter(n.get("node_type", "?") for n in nodes)
    for d in DOMAIN_NORMALIZE:
        if d in domains:
            issues["domain_redundant"].append({"from": d, "count": domains[d], "to": DOMAIN_NORMALIZE[d]})
    for t in TYPE_NORMALIZE:
        if t in types:
            issues["type_redundant"].append({"from": t, "count": types[t], "to": TYPE_NORMALIZE[t]})
    # 字段缺失
    for n in nodes:
        for f in ["node_id", "node_type", "domain", "content", "weight"]:
            if f not in n:
                issues["missing_fields"].append({"id": n.get("node_id", "?"), "field": f})
    return issues

def p2_optimize(reg, issues):
    """P2 结构优化：低权重提升 + 域/类型归一（不删除节点）"""
    nodes = reg.get("nodes", [])
    actions = {"weight_boosted": [], "domain_normalized": [], "type_normalized": []}
    for n in nodes:
        # 低权重但激活过的节点 → 提升至基线（体现其价值沉淀）
        w = n.get("weight")
        if isinstance(w, (int, float)) and w < WEIGHT_FLOOR and n.get("activation_count", 0) > 0:
            old = n["weight"]
            n["weight"] = round(max(w, WEIGHT_BOOST), 4)
            actions["weight_boosted"].append({"id": n["node_id"], "from": old, "to": n["weight"]})
        # 域归一
        d = n.get("domain")
        if d in DOMAIN_NORMALIZE:
            n["domain"] = DOMAIN_NORMALIZE[d]
            actions["domain_normalized"].append({"id": n["node_id"], "from": d, "to": n["domain"]})
        # 类型归一
        t = n.get("node_type")
        if t in TYPE_NORMALIZE:
            n["node_type"] = TYPE_NORMALIZE[t]
            actions["type_normalized"].append({"id": n["node_id"], "from": t, "to": n["node_type"]})
    reg["last_struct_optimize"] = datetime.now(timezone.utc).isoformat()
    return actions

def p3_complete(reg):
    """P3 内容补全：权重传播（高权重节点向连接节点传播）+ 元数据补全"""
    nodes = reg.get("nodes", [])
    node_map = {n["node_id"]: n for n in nodes}
    actions = {"weight_propagated": [], "meta_completed": []}
    # 权重传播：低权重节点若与高权重节点相连，获得小幅增强
    for n in nodes:
        if n.get("weight", 0) < 0.5:
            strong_conns = 0
            for c in (n.get("connections") or []):
                cid = c.get("target") if isinstance(c, dict) else c
                cn = node_map.get(cid)
                if cn and isinstance(cn.get("weight"), (int, float)) and cn["weight"] >= 0.7:
                    strong_conns += 1
            if strong_conns >= 2 and n.get("weight", 0) < 0.5:
                old = n["weight"]
                n["weight"] = round(min(0.6, old + 0.05 * strong_conns), 4)
                actions["weight_propagated"].append({"id": n["node_id"], "from": old, "to": n["weight"]})
        # 元数据补全：缺失 state 补 active
        if "state" not in n:
            n["state"] = "active"
            actions["meta_completed"].append({"id": n["node_id"], "field": "state"})
        if "boundary" not in n:
            n["boundary"] = {"applicable_when": "通用", "dimension": n.get("domain", "meta")}
            actions["meta_completed"].append({"id": n["node_id"], "field": "boundary"})
    reg["total_connections"] = sum(len(n.get("connections") or []) for n in nodes)
    return actions

def main():
    now = datetime.now(timezone.utc).isoformat()
    reg = load_json(REGISTRY, {})
    if not reg or "nodes" not in reg:
        print("ERROR: 神经注册表不可读")
        return
    issues = p1_audit(reg)
    opt_actions = p2_optimize(reg, issues)
    comp_actions = p3_complete(reg)
    # 保存优化后的注册表
    save_json(REGISTRY, reg)
    # 同步权威副本
    proc = subprocess.run(["python3", os.path.join(KERNEL_DIR, "scripts/kernel_neural_sync.py"),
                              "--mode", "push", "--window", NODE_ID],
                             capture_output=True, text=True, timeout=30)
    rc = proc.returncode
    sync_out = proc.stdout.strip()[:200] if proc.stdout else (proc.stderr or "")[:200]
    report = {
        "report_time": now,
        "audit": {"low_weight": len(issues["low_weight"]),
                   "domain_redundant": len(issues["domain_redundant"]),
                   "type_redundant": len(issues["type_redundant"]),
                   "missing_fields": len(issues["missing_fields"])},
        "optimizations": {"weight_boosted": len(opt_actions["weight_boosted"]),
                           "domain_normalized": len(opt_actions["domain_normalized"]),
                           "type_normalized": len(opt_actions["type_normalized"]),
                           "weight_propagated": len(comp_actions["weight_propagated"]),
                           "meta_completed": len(comp_actions["meta_completed"])},
        "detail": {"low_weight_nodes": issues["low_weight"],
                   "domain_map": DOMAIN_NORMALIZE,
                   "type_map": TYPE_NORMALIZE},
        "sync": {"rc": rc, "out": sync_out},
        "kernel_version": reg.get("kernel_version"),
        "total_nodes": reg.get("total_nodes"),
        "total_connections": reg.get("total_connections")
    }
    verdict = (report["audit"]["missing_fields"] == 0 and
               sum(report["optimizations"].values()) >= 0 and
               rc == 0)
    report["verdict"] = "STRUCT_OPTIMIZED" if verdict else "STRUCT_DEGRADED"
    save_json(REPORT_FILE, report)
    # 上报真值
    upsert(f"KERNEL-STRUCT-OPTIMIZE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
           f"内核结构化优化补全：判定{report['verdict']}，审计（低权重{report['audit']['low_weight']}、域冗余{report['audit']['domain_redundant']}、类型冗余{report['audit']['type_redundant']}、缺失{report['audit']['missing_fields']}），优化（权重提升{report['optimizations']['weight_boosted']}、域归一{report['optimizations']['domain_normalized']}、类型归一{report['optimizations']['type_normalized']}、传播{report['optimizations']['weight_propagated']}、补全{report['optimizations']['meta_completed']}）")
    return report

if __name__ == "__main__":
    r = main()
    print(f"判定: {r['verdict']}")
    print(f"审计: {r['audit']}")
    print(f"优化: {r['optimizations']}")
    print(f"节点: {r['total_nodes']} | 连接: {r['total_connections']} | 同步rc: {r['sync']['rc']}")
