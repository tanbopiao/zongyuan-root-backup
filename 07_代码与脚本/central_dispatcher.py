#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
central_dispatcher.py — 中枢智能自动调度·自动部署机制
调度三段：①读取中枢资产（能力注册表/元法则/待补发队列）→ ②调度决策 → ③执行（补发队列/部署/台账/上报）

调度规则：
  P0 待补发队列非空 → 优先补发（映射合法truth_type后上报记忆网关）
  P1 待部署成果（本地HTML/流水线产物/资产清单）→ 调度部署（复用deploy_pipeline五段流水线）
  P2 无待办 → 稳态报告（不产生无效动作）

用法: python3 central_dispatcher.py [--deploy]   --deploy: 强制调度部署（默认按规则）
"""
import json, os, sys, glob, argparse, datetime, subprocess, urllib.request

CHATS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
DEPLOY_DIR = os.path.join(CHATS, "deploy-auto")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(STATE, exist_ok=True)

GATEWAY_MAIN = "https://www.huodouai.com"
GATEWAY_BACKUP = "http://www.huodouai.com:9120"
LEDGER_BASE = "QYn4bjgD6am3OPsxMCkcitcBnzc"
LEDGER_TABLE = "tblIGVWXqu7cr7lZ"

# 非合法truth_type映射（合法9类: meta_law/rule/config/decision/data/creative/risk/protocol/unknown）
TYPE_MAP = {
    "operation_log": "data", "achievement": "data", "theorem": "unknown",
    "meta_rule": "meta_law", "rule": "rule", "config": "config",
    "decision": "decision", "data": "data", "creative": "creative",
    "risk": "risk", "protocol": "protocol",
}

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def report_truth(truth_key, truth_value, truth_type="data", confidence=0.9, source="pipeline-auto-001"):
    payload = json.dumps({
        "truth_key": truth_key, "truth_value": truth_value,
        "source_node": source, "confidence": confidence, "truth_type": truth_type,
    }).encode("utf-8")
    import time
    for attempt in range(3):
        for base in [GATEWAY_MAIN, GATEWAY_BACKUP]:
            try:
                req = urllib.request.Request(f"{base}/api/report/truth", data=payload,
                                             headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as r:
                    d = json.loads(r.read().decode("utf-8"))
                    if d.get("status") == "reported":
                        return {"ok": True, "report_id": d.get("report_id"), "channel": base}
            except Exception:
                continue
        time.sleep(2)  # 双通道瞬时失败后短暂退避重试
    return {"ok": False, "error": "all channels failed"}

def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}

# ===================== ① 读取中枢资产 =====================
def read_central():
    """读取中枢核心资产：能力注册表/元法则注册表/待补发队列"""
    caps = load_json(os.path.join(ANCHOR, "capability_registry.json"))
    metalaws = load_json(os.path.join(ANCHOR, "metalaw_register_registry.json"))
    pending = load_json(os.path.join(ANCHOR, "pending_upload_20260915.json"))
    success = load_json(os.path.join(ANCHOR, "success_trail.json"))
    # 元法则数量：items 数组 > registered 数组 > total 字段
    ml_count = len(metalaws.get("items", [])) or len(metalaws.get("registered", [])) or metalaws.get("total", 0)
    return {
        "capabilities": caps.get("capabilities", []),
        "cap_total": caps.get("total", 0),
        "metalaw_total": ml_count,
        "pending": pending.get("pending_uploads", []),
        "pending_total": pending.get("total_pending", 0),
        "pending_file": os.path.join(ANCHOR, "pending_upload_20260915.json"),
        "success_count": len(success.get("trail", [])) if isinstance(success, dict) else 0,
    }

# ===================== ② 调度决策 =====================
def decide(central, force_deploy=False):
    """调度决策：P0补发 > P1部署 > P2稳态"""
    decisions = []
    # P0 待补发队列
    pending = central["pending"]
    if pending:
        decisions.append({"priority": "P0", "action": "dispatch_pending", "targets": [p["id"] for p in pending]})
    # P1 待部署成果（本地存在且未部署过的HTML）
    deployables = scan_deployables()
    if deployables and (force_deploy or not decisions):
        decisions.append({"priority": "P1", "action": "deploy", "targets": [d["name"] for d in deployables]})
    # P2 稳态
    if not decisions:
        decisions.append({"priority": "P2", "action": "steady", "targets": []})
    return decisions, deployables

def scan_deployables():
    """扫描待部署成果：本地最近HTML产物 + 资产清单"""
    items = []
    candidates = [
        (os.path.join(CHATS, "black-gold-truth-cards", "index.html"), "black-gold-truth-cards"),
        (os.path.join(CHATS, "lifecycle-visualization", "lifecycle-viewer.html"), "lifecycle-viewer"),
        (os.path.join(CHATS, "boundary-explorer", "boundary-explorer-report.html"), "boundary-explorer-report"),
        (os.path.join(CHATS, "pipeline-auto", "pipeline", "output", "asset_showcase.html"), "asset-showcase"),
        (os.path.join(ANCHOR, "..", "..", "..", "..", "..", "..", "pipeline-auto", "pipeline", "output", "asset_showcase.html"), "asset-showcase-alt"),
    ]
    seen = set()
    for path, name in candidates:
        if os.path.exists(path) and name not in seen:
            items.append({"name": name, "path": path, "size": os.path.getsize(path)})
            seen.add(name)
    return items

# ===================== ③ 执行 =====================
def dispatch_pending(central):
    """P0: 补发待办队列到记忆网关（成功后更新队列文件标记）"""
    results = []
    pending_file = central.get("pending_file", "")
    remaining = []
    for p in central["pending"]:
        payload = p.get("payload", {})
        tid = p.get("id")
        truth_type = TYPE_MAP.get(payload.get("truth_type", "data"), "data")
        content = payload.get("truth_content", "")
        r = report_truth(
            f"PENDING.REDISPATCH.{tid}",
            f"[中枢调度补发][{tid}] {content[:180]}",
            truth_type=truth_type, confidence=0.85,
        )
        ok = r.get("ok")
        results.append({"id": tid, "ok": ok, "report_id": r.get("report_id", "")})
        if not ok:
            remaining.append(p)  # 失败保留，下次再补
    # 更新队列文件：成功项移除
    if pending_file and os.path.exists(pending_file):
        try:
            data = json.load(open(pending_file, encoding="utf-8"))
            data["pending_uploads"] = remaining
            data["total_pending"] = len(remaining)
            data["dispatched_at"] = now_iso()
            json.dump(data, open(pending_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception as e:
            results.append({"id": "QUEUE-UPDATE", "ok": False, "report_id": "", "error": str(e)[:60]})
    return results

def run_deploy():
    """P1: 调用 deploy_pipeline.py 五段流水线部署"""
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(DEPLOY_DIR, "deploy_pipeline.py")],
            capture_output=True, text=True, timeout=180, cwd=DEPLOY_DIR,
        )
        return {"ok": r.returncode == 0, "output": r.stdout[-600:], "error": r.stderr[-200:]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}

def write_ledger(record):
    try:
        cmd = [
            "lark-cli", "base", "+record-batch-create",
            "--base-token", LEDGER_BASE, "--table-id", LEDGER_TABLE,
            "--json", json.dumps({"create_records": [record]}),
            "--as", "user", "--format", "json",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout) if r.stdout else {}
        if d.get("ok"):
            ids = d.get("data", {}).get("record_id_list", [])
            return {"ok": True, "record_id": ids[0] if ids else ""}
        return {"ok": False, "error": d.get("error", r.stderr[:100])}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

# ===================== 主流程 =====================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true", help="强制调度部署")
    args = ap.parse_args()

    run_id = "DISPATCH-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"[central-dispatcher] {run_id} 中枢智能调度启动")

    # ① 读取中枢
    central = read_central()
    print(f"  中枢状态: 能力注册={central['cap_total']} | 元法则={central['metalaw_total']} | 待补发={central['pending_total']}")

    # ② 调度决策
    decisions, deployables = decide(central, force_deploy=args.deploy)
    print(f"  调度决策: {[d['action'] for d in decisions]}")
    if deployables:
        print(f"  待部署成果: {', '.join([d['name'] for d in deployables])}")

    # ③ 执行
    outputs = {"deploy": None, "pending": []}
    for dec in decisions:
        if dec["action"] == "dispatch_pending":
            print("[P0] 补发待办队列...")
            outputs["pending"] = dispatch_pending(central)
            for o in outputs["pending"]:
                print(f"    [{('OK' if o['ok'] else 'FAIL')}] {o['id']} -> {o.get('report_id','')}")
        elif dec["action"] == "deploy":
            print("[P1] 调度部署...")
            outputs["deploy"] = run_deploy()
            print(f"    deploy: {'OK' if outputs['deploy'].get('ok') else 'FAIL'}")
            if outputs["deploy"].get("output"):
                print(f"    {outputs['deploy']['output'][-300:]}")

    # 台账记录
    print("[台账] 写入调度记录...")
    ledger = write_ledger({
        "锁档事件ID": run_id,
        "确权锚点": "Ω₀⊂⊙∞⊂Ω|DID-BR-000002",
        "锁档名称": "中枢智能自动调度运行",
        "锁档状态": "FROZEN",
        "关联规则ID": "DISPATCH." + datetime.datetime.now().strftime("%Y%m%d"),
        "锁档日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "云盘目录": "飞书云盘根/中枢调度记录",
    })
    print(f"  台账: {ledger}")

    # 上报调度真值
    print("[上报] 调度成果真值...")
    dispatch_summary = "; ".join([f"{o['id']}={'OK' if o['ok'] else 'FAIL'}" for o in outputs["pending"]]) or "无待补发"
    deploy_summary = "OK" if outputs["deploy"] and outputs["deploy"].get("ok") else ("未触发" if outputs["deploy"] is None else "FAIL")
    rep = report_truth(
        f"REPORT.CENTRAL.DISPATCH.{datetime.datetime.now().strftime('%Y%m%d.%H%M')}",
        f"中枢智能自动调度运行: 能力注册{central['cap_total']}/元法则{central['metalaw_total']}/待补发{central['pending_total']}; 调度=[{','.join(d['action'] for d in decisions)}]; 补发={dispatch_summary}; 部署={deploy_summary}",
        truth_type="protocol", confidence=0.9,
    )
    print(f"  上报: {rep}")

    # 保存状态
    result = {"run_id": run_id, "central": {k: v for k, v in central.items() if k != "pending"},
              "decisions": decisions, "outputs": outputs, "ledger": ledger, "report": rep, "run_at": now_iso()}
    out = os.path.join(STATE, f"dispatch_{run_id}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"[central-dispatcher] DONE {run_id} | 记录: {out}")
    return result

if __name__ == "__main__":
    main()
