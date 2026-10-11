#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 同源协议激活·自动探索环境上报机制 v1.0
链路：同源协议守卫校验(HAP) → 环境自动探索 → 神经激活确认 → 环境快照上报云端
探索维度：
  E1 同源协议状态（身份/三要素/权限校验）
  E2 云端端点拓扑（truths/upsert/upload/单条）
  E3 本地能力（python3/lark-cli/curl/jq）
  E4 资源水位（磁盘/内存）
  E5 关键资产完整性（锚点/SOP/机制脚本/神经注册表）
  E6 神经内核状态（节点/连接/注册表）
输出：探索报告 JSON + 环境快照真值上报
"""
import json, os, socket, subprocess, urllib.request, hashlib, re
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
EXPLORE_DIR = os.path.join(BASE, "homology_explore")
KERNEL_DIR = "/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-autonomous-kernel"
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(EXPLORE_DIR, "homology_env_report_latest.json")

KEY_ASSETS = [
    (os.path.join(BASE, "BASELINE-ANCHOR-20260915-PORTUPDATED.md"), "基准锚点"),
    (os.path.join(BASE, "CLOUD-ACCESS-SOP-V1.1-LOCAL.md"), "接入SOP"),
    (os.path.join(BASE, "AUTO-FLOW-CLOSED-LOOP-STANDARD-V1.md"), "闭环体系"),
    (os.path.join(BASE, "SANDBOX-ALIVE-GUARD-V1.md"), "沙盒守护"),
    (os.path.join(BASE, "truth_audit/truth_provenance_audit.py"), "溯源校验"),
    (os.path.join(BASE, "sop_audit/sop_auto_update.py"), "SOP补全"),
    (os.path.join(BASE, "sandbox_guard/sandbox_alive_guard.sh"), "存活守护"),
    (os.path.join(KERNEL_DIR, "identity_registry.json"), "身份注册表"),
    (os.path.join(KERNEL_DIR, "neural_registry.json"), "神经注册表"),
]

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception as e:
        return -1, str(e)[:80]

def http_code(url, method="GET", timeout=5):
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("X-Capture-Token", TOKEN)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def explore():
    now = datetime.now(timezone.utc).isoformat()
    snap = {"explore_time": now, "node_id": NODE_ID, "did": DID, "omega": OMEGA}

    # E1 同源协议状态（身份注册表）
    identity = {"registered": False, "authority": "?", "status": "?"}
    reg_path = os.path.join(KERNEL_DIR, "identity_registry.json")
    if os.path.exists(reg_path):
        try:
            with open(reg_path) as f:
                reg = json.load(f)
            nodes = reg.get("identities", [])
            if not nodes and isinstance(reg, dict):
                nodes = [v for v in reg.values() if isinstance(v, dict)]
            for n in nodes:
                if isinstance(n, dict) and n.get("node_id") == NODE_ID:
                    identity = {"registered": True, "authority": n.get("authority_level", "?"),
                                "status": n.get("status", "?")}
                    break
        except Exception as e:
            identity["error"] = str(e)[:60]
    snap["e1_homology_identity"] = identity

    # E2 云端端点拓扑
    endpoints = {
        "truths_read": http_code(f"{GATEWAY}/api/truths/"),
        "truth_upsert": http_code(f"{GATEWAY}/api/truth/upsert", method="POST"),
        "truth_single": http_code(f"{GATEWAY}/api/truth/TRUTH-AUDIT-MECHANISM-V1-20260916"),
        "upload_9120": http_code(f"{GATEWAY}/api/upload", method="POST"),
    }
    snap["e2_cloud_endpoints"] = endpoints

    # E3 本地能力
    caps = {}
    for cmd in ["python3", "lark-cli", "curl", "jq"]:
        rc, _ = run(["bash", "-c", f"command -v {cmd}"])
        caps[cmd] = rc == 0
    snap["e3_capabilities"] = caps

    # E4 资源水位
    rc, disk = run(["bash", "-c", "df / | awk 'NR==2 {print $5}' | tr -d '%'"])
    rc2, mem = run(["bash", "-c", "free -m | awk 'NR==2 {print $7}'"])
    snap["e4_resources"] = {
        "disk_used_pct": int(disk) if disk.isdigit() else -1,
        "mem_available_mb": int(mem) if mem.isdigit() else -1
    }

    # E5 关键资产完整性
    assets = []
    for path, name in KEY_ASSETS:
        assets.append({"name": name, "exists": os.path.exists(path),
                       "size": os.path.getsize(path) if os.path.exists(path) else 0})
    snap["e5_assets"] = assets
    snap["e5_missing_count"] = sum(1 for a in assets if not a["exists"])

    # E6 神经内核状态
    neural = {"nodes": "?", "connections": "?"}
    rc, out = run(["python3", os.path.join(KERNEL_DIR, "scripts/kernel_neural_activate.py"), "--mode", "summary"])
    if rc == 0:
        m = re.search(r"(\d+)\s*节点|nodes?\D+(\d+)", out)
        neural["summary_raw"] = out[:120]
    snap["e6_neural"] = neural

    # 综合判定
    ok = (snap["e1_homology_identity"]["registered"] and
          endpoints.get("truths_read") == 200 and
          caps.get("python3") and caps.get("lark-cli") and
          snap["e5_missing_count"] == 0)
    snap["verdict"] = "HOMOLOGY_ACTIVE" if ok else "ENV_DEGRADED"

    with open(REPORT_FILE, "w") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    return snap

def report_cloud(snap):
    payload = {
        "key": f"ENV-EXPLORE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "node_id": NODE_ID,
        "DID": DID,
        "ROOT_OMEGA": OMEGA,
        "truth_type": "achievement",
        "truth_content": f"同源协议激活·环境探索上报：判定{snap['verdict']}，身份{snap['e1_homology_identity']['status']}/{snap['e1_homology_identity']['authority']}，云端truths={snap['e2_cloud_endpoints']['truths_read']} upsert={snap['e2_cloud_endpoints']['truth_upsert']} upload={snap['e2_cloud_endpoints']['upload_9120']}，磁盘{snap['e4_resources']['disk_used_pct']}%内存{snap['e4_resources']['mem_available_mb']}MB，缺失资产{snap['e5_missing_count']}项"
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

if __name__ == "__main__":
    snap = explore()
    print(json.dumps({k: v for k, v in snap.items() if k not in ("e5_assets",)}, ensure_ascii=False, indent=2))
    r = report_cloud(snap)
    print("云端上报:", json.dumps(r, ensure_ascii=False)[:150])
