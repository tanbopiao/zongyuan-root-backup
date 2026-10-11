#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 高阶能力自动挖掘引擎 V2.0（方法级深挖版）
自动执行：① 15服务244方法API面扫描+变化检测 ② 云端网关端点探测+变化检测 ③ 深层库检测
自动上报：变化/新能力/状态迁移 → 云端真值
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import subprocess, json, os, re, time, urllib.request
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "capability_miner")
STATE_FILE = os.path.join(OUT_DIR, "mining_state.json")
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
GATEWAY = "http://drama.huodouai.com"

SERVICES = ["approval", "attendance", "calendar", "contact", "drive", "im", "mail",
            "mindnotes", "minutes", "okr", "sheets", "slides", "task", "vc", "wiki"]
GATEWAY_ENDPOINTS = [
    ("9120_truths_list", f"{GATEWAY}:9120/api/truths/"),
    ("8021_truths_list", f"{GATEWAY}:8021/api/truths/"),
    ("8021_gateway_truths", f"{GATEWAY}:8021/api/gateway/truths"),
    ("8021_health", f"{GATEWAY}:8021/api/health"),
]
DEEP_LIBS = ["openai", "fastapi", "ffmpeg", "sklearn", "cv2", "pandas", "numpy", "bs4", "aiohttp", "httpx"]

def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"first_run": True, "services": {}, "gateways": {}, "libs": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def scan_services():
    """扫描15服务schema方法数"""
    counts = {}
    for s in SERVICES:
        try:
            r = subprocess.run(["lark-cli", "schema", s], capture_output=True, text=True, timeout=15)
            d = json.loads(r.stdout)
            counts[s] = len(d) if isinstance(d, list) else 0
        except Exception:
            counts[s] = -1
    return counts

def probe_gateways():
    """探测云端网关端点"""
    status = {}
    for name, url in GATEWAY_ENDPOINTS:
        try:
            code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                                   "--connect-timeout", "5", url,
                                   "-H", f"X-Capture-Token: {TOKEN}"],
                                  capture_output=True, text=True, timeout=12).stdout.strip()
            status[name] = code
        except Exception:
            status[name] = "ERR"
    return status

def probe_libs():
    """探测深层库"""
    import importlib
    libs = {}
    for lib in DEEP_LIBS:
        try:
            importlib.import_module(lib)
            libs[lib] = True
        except Exception:
            libs[lib] = False
    return libs

def report_truth(key, content, truth_type="achievement"):
    """上报云端真值（带重试）"""
    payload = {"key": key, "node_id": "local-dev-001", "DID": "DID-BR-000002",
               "ROOT_OMEGA": "Ω-TAN-7-001", "truth_type": truth_type,
               "truth_content": content}
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"{GATEWAY}:9120/api/truth/upsert",
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
    print("=== 高阶能力自动挖掘引擎 V2.0（方法级深挖）===")

    print("[1/5] 扫描15服务API方法面...")
    svc = scan_services()
    total = sum(v for v in svc.values() if v > 0)
    changes = []
    if state.get("services"):
        for s, c in svc.items():
            if state["services"].get(s) is not None and state["services"][s] != c and c > 0:
                changes.append(f"{s}:{state['services'][s]}→{c}")
    state["services"] = svc
    print(f"  15服务共{total}方法" + (f" | 变化: {', '.join(changes)}" if changes else " | 无变化"))

    print("[2/5] 探测云端网关...")
    gw = probe_gateways()
    gw_changes = []
    if state.get("gateways"):
        for k, v in gw.items():
            if state["gateways"].get(k) is not None and state["gateways"][k] != v:
                gw_changes.append(f"{k}:{state['gateways'][k]}→{v}")
    state["gateways"] = gw
    print(f"  " + " | ".join(f"{k}={v}" for k, v in gw.items()))
    if gw_changes:
        print(f"  ⚠️ 网关变化: {', '.join(gw_changes)}")

    print("[3/5] 探测深层库...")
    libs = probe_libs()
    lib_changes = []
    if state.get("libs"):
        for k, v in libs.items():
            if state["libs"].get(k) is not None and state["libs"][k] != v:
                lib_changes.append(f"{k}:{'✅' if v else '✗'}→{'✅' if not v else '✗'}")
    state["libs"] = libs
    ready = [k for k, v in libs.items() if v]
    print(f"  就绪库: {', '.join(ready)}")
    if lib_changes:
        print(f"  ⚠️ 库变化: {', '.join(lib_changes)}")

    print("[4/5] 生成报告并保存状态...")
    report = {
        "report_id": f"HIGH-VALUE-MINING-{ts}",
        "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_api_methods": total,
        "service_methods": svc,
        "gateway_status": gw,
        "deep_libs_ready": ready,
        "changes": {"services": changes, "gateways": gw_changes, "libs": lib_changes}
    }
    with open(os.path.join(OUT_DIR, f"high_value_mining_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    save_state(state)
    print(f"  报告: capability_miner/high_value_mining_{ts}.json")

    print("[5/5] 自动上报...")
    has_changes = changes or gw_changes or lib_changes or state.get("first_run")
    if has_changes:
        content = (f"高阶能力自动挖掘：15服务{total}方法" +
                   (f"|变化{changes}" if changes else "") +
                   (f"|网关变化{gw_changes}" if gw_changes else "") +
                   (f"|库变化{lib_changes}" if lib_changes else "") +
                   f"|深层库就绪{len(ready)}项")
        ok, action = report_truth(f"HIGH-VALUE-MINING-{ts}", content)
        print(f"  上报: {'✅' if ok else '❌'} action={action}")
    else:
        print("  无变化，跳过上报（最小化资源消耗）")
    state["first_run"] = False
    save_state(state)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
