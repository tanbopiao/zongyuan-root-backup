#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deploy_pipeline.py — 自动上报成果·自动部署官网机制
五段流水线：①探测部署通道 → ②上报成果真值 → ③部署/交付 → ④验证公网 → ⑤台账记录

部署通道策略（自动降级）：
  P0 官网部署API（POST /api/deploy 等，探测到 200 即走真实部署）
  P1 aka 公网链接交付（当前实际可用，历史多次验证 200）
  P2 飞书云盘归档（媒体资产归档飞书云盘，用户偏好）

用法: python3 deploy_pipeline.py [--artifact <html路径>] [--name <名称>]
默认部署黑金真值卡 + 生命周期看板 + 边界探索报告三件套。
"""
import json, os, sys, argparse, datetime, subprocess, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
CHATS = os.path.abspath(os.path.join(ROOT, ".."))
STATE = os.path.join(ROOT, "data")
os.makedirs(STATE, exist_ok=True)

GATEWAY_MAIN = "https://www.huodouai.com"
GATEWAY_BACKUP = "http://www.huodouai.com:9120"

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def http_code(url, method="GET", data=None, headers=None, timeout=8):
    try:
        req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

# ===================== ① 探测部署通道 =====================
def probe_deploy_channels():
    """探测官网部署 API 是否可用（历史全部 502，探测到 200 即部署通道恢复）"""
    endpoints = [
        ("https://www.huodouai.com/api/deploy", "POST"),
        ("https://www.huodouai.com/api/page", "POST"),
        ("https://www.huodouai.com/api/html/upload", "POST"),
        ("https://www.huodouai.com/api/publish", "POST"),
    ]
    results = []
    for url, method in endpoints:
        code = http_code(url, method)
        results.append({"url": url, "code": code})
    available = [r for r in results if r["code"] == 200]
    return {"results": results, "deploy_api_available": bool(available), "available": available}

# ===================== ② 上报成果真值 =====================
def report_truth(truth_key, truth_value, truth_type="data", confidence=0.9, source="pipeline-auto-001"):
    payload = json.dumps({
        "truth_key": truth_key, "truth_value": truth_value,
        "source_node": source, "confidence": confidence, "truth_type": truth_type,
    }).encode("utf-8")
    import time
    # 主通道 + 备通道，双通道瞬时失败后退避重试
    for attempt in range(3):
        for base in [GATEWAY_MAIN, GATEWAY_BACKUP]:
            try:
                req = urllib.request.Request(f"{base}/api/report/truth", data=payload,
                                             headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as r:
                    d = json.loads(r.read().decode("utf-8"))
                    if d.get("status") == "reported":
                        return {"ok": True, "report_id": d.get("report_id"), "channel": base, "validation": d.get("validation", {}).get("status")}
            except Exception:
                continue
        time.sleep(2)
    return {"ok": False, "error": "all channels failed"}

# ===================== ③ 部署 / 交付 =====================
def deploy_via_api(url, html_path, name):
    """P0: 官网部署 API（若可用）"""
    with open(html_path, "rb") as f:
        data = f.read()
    # 尝试 multipart 或 raw 上传
    try:
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "text/html", "X-File-Name": name})
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"ok": r.status == 200, "code": r.status, "body": r.read().decode()[:200]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}

def deploy_via_aka(html_path):
    """P1: aka 公网链接交付（使用 FileBatchUpload 等价物——akaupload 脚本）"""
    # 尝试用 akaupload / aka 工具
    for tool in ["aka", "akaupload"]:
        try:
            r = subprocess.run(["which", tool], capture_output=True, text=True)
            if r.returncode == 0:
                res = subprocess.run([tool, html_path], capture_output=True, text=True, timeout=60)
                if res.returncode == 0:
                    url = res.stdout.strip().split()[-1]
                    if url.startswith("http"):
                        return {"ok": True, "url": url, "method": tool}
        except Exception:
            continue
    return {"ok": False, "error": "aka tool not available (use FileBatchUpload)"}

# ===================== ④ 验证公网 =====================
def verify_url(url):
    code = http_code(url)
    return {"url": url, "code": code, "ok": code == 200}

# ===================== ⑤ 台账记录 =====================
def write_ledger(record):
    """通过 lark-cli 写飞书多维表格台账"""
    try:
        cmd = [
            "lark-cli", "base", "+record-batch-create",
            "--base-token", "QYn4bjgD6am3OPsxMCkcitcBnzc",
            "--table-id", "tblIGVWXqu7cr7lZ",
            "--json", json.dumps({"create_records": [record]}),
            "--as", "user", "--format", "json"
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
    ap.add_argument("--artifact", default="")
    ap.add_argument("--name", default="")
    args = ap.parse_args()

    run_id = "DEPLOY-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"[deploy-pipeline] {run_id} 启动")

    # 默认三件套
    artifacts = []
    if args.artifact:
        artifacts.append({"path": args.artifact, "name": args.name or os.path.basename(args.artifact)})
    else:
        artifacts = [
            {"path": os.path.join(CHATS, "black-gold-truth-cards", "index.html"), "name": "black-gold-truth-cards"},
            {"path": os.path.join(CHATS, "lifecycle-visualization", "lifecycle-viewer.html"), "name": "lifecycle-viewer"},
            {"path": os.path.join(CHATS, "boundary-explorer", "boundary-explorer-report.html"), "name": "boundary-explorer-report"},
        ]
    artifacts = [a for a in artifacts if os.path.exists(a["path"])]
    print(f"  待部署成果: {len(artifacts)} 件")
    for a in artifacts:
        print(f"    - {a['name']} ({os.path.getsize(a['path'])}B)")

    # ① 探测部署通道
    print("[①] 探测部署通道...")
    probe = probe_deploy_channels()
    print(f"  部署API可用: {probe['deploy_api_available']}")
    for r in probe["results"]:
        print(f"    {r['code']} {r['url']}")

    # ③ 部署/交付
    print("[③] 部署/交付...")
    deployed = []
    for a in artifacts:
        item = {"name": a["name"], "path": a["path"]}
        if probe["deploy_api_available"]:
            ep = probe["available"][0]["url"]
            res = deploy_via_api(ep, a["path"], a["name"])
            item.update(res)
            item["channel"] = "api"
        else:
            res = deploy_via_aka(a["path"])
            item.update(res)
            item["channel"] = "aka"
        # 验证
        if item.get("url"):
            item["verify"] = verify_url(item["url"])
        deployed.append(item)
        st = "OK" if item.get("ok") else "FALLBACK"
        print(f"    [{st}] {a['name']} -> {item.get('url', item.get('error',''))}")

    # ② 上报成果真值
    print("[②] 上报成果真值...")
    summary = "; ".join([f"{d['name']}={d.get('url','FAIL')}" for d in deployed])
    report = report_truth(
        f"REPORT.DEPLOY.AUTO.{datetime.datetime.now().strftime('%Y%m%d.%H%M')}",
        f"自动部署机制运行: 部署通道探测={probe['deploy_api_available']}(API可用/aka交付), 成果{len(deployed)}件: {summary}",
        truth_type="data", confidence=0.9,
    )
    print(f"  上报: {report}")

    # ⑤ 台账
    print("[⑤] 台账记录...")
    ledger = write_ledger({
        "锁档事件ID": run_id,
        "确权锚点": "Ω₀⊂⊙∞⊂Ω|DID-BR-000002",
        "锁档名称": "自动上报部署机制运行",
        "锁档状态": "FROZEN",
        "关联规则ID": f"REPORT.DEPLOY.AUTO.{datetime.datetime.now().strftime('%Y%m%d.%H%M')}",
        "锁档日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "云盘目录": "飞书云盘根/自动部署记录",
    })
    print(f"  台账: {ledger}")

    # 保存运行记录
    result = {
        "run_id": run_id, "probe": probe, "deployed": deployed,
        "report": report, "ledger": ledger, "run_at": now_iso(),
    }
    out = os.path.join(STATE, f"deploy_{run_id}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"[deploy-pipeline] DONE {run_id} | 记录: {out}")
    return result

if __name__ == "__main__":
    main()
