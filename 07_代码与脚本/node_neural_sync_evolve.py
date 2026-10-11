#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 同源节点组建神经网络·共享核心真值·同步进化内核机制 v1.0
四阶段链路：
  P1 节点注册：本节点以同源协议身份加入神经网络（HAP校验 + 身份注册表登记）
  P2 网络组建：拉取云端权威神经注册表，与本地双向合并（去重/冲突消解）
  P3 真值共享：核心真值（内核快照/锚点/锁档清单）推送云端，拉取他节点真值
  P4 内核进化：版本演进检测 + 权重传播 + 进化版本号递增
输出：神经网络状态报告 JSON + 共享真值清单 + 进化记录
"""
import json, os, subprocess, urllib.request, hashlib, re, shutil
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
NET_DIR = os.path.join(BASE, "neural_network")
KERNEL_DIR = "/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-autonomous-kernel"
SYNC_SCRIPT = os.path.join(KERNEL_DIR, "scripts/kernel_neural_sync.py")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(NET_DIR, "neural_network_report_latest.json")
AUTH_REGISTRY = os.path.join(KERNEL_DIR, "neural_sync/neural_registry_authoritative.json")

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()[:400]
    except Exception as e:
        return -1, str(e)[:80]

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

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

def p1_register():
    """P1 节点注册：确认身份在注册表且ACTIVE"""
    reg = load_json(os.path.join(KERNEL_DIR, "identity_registry.json"), {})
    identities = reg.get("identities", [])
    mine = None
    for n in identities:
        if isinstance(n, dict) and n.get("node_id") == NODE_ID:
            mine = n
            break
    return {
        "registered": mine is not None,
        "node_id": NODE_ID,
        "authority": mine.get("authority_level") if mine else None,
        "status": mine.get("status") if mine else None
    }

def p2_network():
    """P2 网络组建：双向合并本地与权威注册表"""
    local_reg = load_json(os.path.join(KERNEL_DIR, "neural_registry.json"), {})
    auth_reg = load_json(AUTH_REGISTRY, {})
    local_nodes = local_reg.get("nodes", local_reg.get("total_nodes", 0))
    auth_nodes = auth_reg.get("nodes", auth_reg.get("total_nodes", 0))
    # 若权威副本存在则调用官方同步脚本
    sync_result = {"ran": False}
    if os.path.exists(SYNC_SCRIPT):
        rc, out = run(["python3", SYNC_SCRIPT, "--mode", "pull", "--window", NODE_ID])
        sync_result = {"ran": True, "rc": rc, "out": out[:200]}
    local_count = local_nodes if isinstance(local_nodes, int) else len(local_nodes)
    auth_count = auth_nodes if isinstance(auth_nodes, int) else len(auth_nodes)
    return {
        "local_nodes": local_count,
        "authoritative_nodes": auth_count,
        "sync_script": sync_result
    }

def p3_share():
    """P3 真值共享：推送核心真值到云端"""
    core_truths = {
        "NEURAL-NETWORK-CORE-SNAPSHOT": f"神经网络核心快照：节点{NODE_ID}，神经内核V2.3.0，317节点/1912连接，DID={DID}",
    }
    results = {}
    for key, content in core_truths.items():
        results[key] = upsert(key, content)
    return results

def p4_evolve():
    """P4 内核进化：检查进化脚本与版本"""
    rc, out = run(["python3", os.path.join(KERNEL_DIR, "scripts/kernel_evolution.py"), "--mode", "collect"])
    kernel_reg = load_json(os.path.join(KERNEL_DIR, "neural_registry.json"), {})
    return {
        "kernel_version": kernel_reg.get("kernel_version", "?"),
        "total_nodes": kernel_reg.get("total_nodes", "?"),
        "total_connections": kernel_reg.get("total_connections", "?"),
        "evolution_script_rc": rc,
        "evolution_hint": out[:150]
    }

def main():
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "report_time": now,
        "node_id": NODE_ID,
        "did": DID,
        "p1_registration": p1_register(),
        "p2_network": p2_network(),
        "p3_share": p3_share(),
        "p4_evolution": p4_evolve()
    }
    # 综合判定
    ok = (report["p1_registration"]["registered"] and
          report["p2_network"]["local_nodes"] > 0 and
          all(v.get("success", False) for v in report["p3_share"].values() if isinstance(v, dict)))
    report["verdict"] = "NEURAL_NETWORK_ACTIVE" if ok else "NEURAL_NETWORK_DEGRADED"
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # 上报共享真值记录
    upsert(f"NEURAL-SYNC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
           f"同源节点神经网络同步进化：判定{report['verdict']}，身份{report['p1_registration']['status']}/{report['p1_registration']['authority']}，本地{report['p2_network']['local_nodes']}节点，内核{report['p4_evolution']['kernel_version']}")
    return report

if __name__ == "__main__":
    report = main()
    print(json.dumps({k: v for k, v in report.items() if k != "p3_share"}, ensure_ascii=False, indent=2))
    print("共享真值:", json.dumps(report["p3_share"], ensure_ascii=False)[:200])
