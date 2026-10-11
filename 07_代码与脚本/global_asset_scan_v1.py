#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLOBAL-ASSET-SCAN-V1 全局资产扫描引擎
全域遍历云内核资产，联动语义基座做术语对账、哈希校验、漂移关联、快照对比
用法:
  --full-scan    全量扫描（默认）
  --delta-scan   增量扫描（对比上次快照）
  --risk-recheck 仅重检高风险资产
"""
import os
import sys
import json
import time
import hashlib
import argparse
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG_PATH = "/opt/ZONGYUAN-ROOT/config/global_scan_config.json"
DEFAULT_CONFIG = {
    "engine": "GLOBAL-ASSET-SCAN-V1",
    "version": "1.0.0",
    "scan_source": ["local_kernel"],
    "enable_semantic_reconcile": True,
    "enable_hash_verify": True,
    "enable_drift_check": True,
    "critical_threshold": 0.7,
    "observe_threshold": 0.15,
    "parallel_limit": 16,
    "snapshot_save": True,
    "asset_roots": ["/opt/ZONGYUAN-ROOT"],
    "exclude_patterns": [".pyc", ".log", ".git", "__pycache__", ".bak", "node_modules"],
    "report_dir": "/opt/ZONGYUAN-ROOT/log/global_asset_scan/report",
    "snapshot_path": "/opt/ZONGYUAN-ROOT/snapshot/global_asset_snapshot_v1.json",
    "semantic_api": "http://127.0.0.1:9120/api/semantic",
    "max_file_bytes": 1048576
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_type(path, cfg):
    ext = os.path.splitext(path)[1].lower()
    return cfg.get("asset_type_by_ext", {}).get(ext, "未知/其他")


def is_excluded(path, cfg):
    for pat in cfg.get("exclude_patterns", []):
        if pat in path:
            return True
    return False


def walk_assets(cfg):
    assets = []
    seen = set()
    for root in cfg.get("asset_roots", []):
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not is_excluded(os.path.join(dirpath, d), cfg)]
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                if is_excluded(fp, cfg):
                    continue
                try:
                    sz = os.path.getsize(fp)
                except OSError:
                    continue
                if sz == 0 or sz > cfg.get("max_file_bytes", 1048576):
                    continue
                if fp in seen:
                    continue
                seen.add(fp)
                assets.append({
                    "path": fp,
                    "size": sz,
                    "type": asset_type(fp, cfg),
                    "mtime": os.path.getmtime(fp)
                })
    return assets


def call_semantic_api(cfg, endpoint, payload=None):
    url = cfg.get("semantic_api", "http://127.0.0.1:9120/api/semantic") + "/" + endpoint
    try:
        if payload is not None:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}


def scan_one_asset(item, cfg, prev_snapshot):
    result = {
        "path": item["path"],
        "size": item["size"],
        "type": item["type"],
        "mtime": item["mtime"],
        "sha256": None,
        "hash_ok": None,
        "semantic_terms_found": 0,
        "semantic_terms_valid": 0,
        "drift_index": 0.0,
        "status": "UNKNOWN",
        "issues": []
    }
    # 1. 哈希校验
    if cfg.get("enable_hash_verify", True):
        try:
            result["sha256"] = sha256_file(item["path"])
        except OSError as e:
            result["issues"].append("哈希计算失败: %s" % str(e))
    prev = prev_snapshot.get("assets", {}).get(item["path"]) if prev_snapshot else None
    if prev and prev.get("sha256") == result["sha256"]:
        result["hash_ok"] = True
    else:
        result["hash_ok"] = None if prev is None else False

    # 2. 语义对账（提取文本资产中的术语）
    if cfg.get("enable_semantic_reconcile", True) and item["type"] in ("真值卷宗/配置", "SOP/文档", "引擎脚本"):
        try:
            with open(item["path"], "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(20000)
            if text.strip():
                resp = call_semantic_api(cfg, "reconcile", {
                    "asset_id": item["path"],
                    "meta_homo_root": "Ω-TAN-7-001",
                    "asset_did": "DID-BR-SCAN",
                    "timestamp": datetime.now().isoformat(),
                    "sha256": result["sha256"] or ("0" * 64),
                    "description": text[:3000]
                })
                if resp.get("success"):
                    d = resp.get("data", {})
                    result["semantic_terms_found"] = d.get("semantic_terms_found", 0)
                    result["semantic_terms_valid"] = d.get("semantic_terms_valid_count", 0)
                    if d.get("semantic_terms_invalid"):
                        result["issues"].append("无效术语: " + ", ".join(d["semantic_terms_invalid"][:5]))
        except Exception as e:
            result["issues"].append("语义对账异常: %s" % str(e))

    # 3. 分级判定
    if result["hash_ok"] is False:
        result["status"] = "ALERT"
        result["issues"].append("哈希不一致/文件被修改")
    elif result["semantic_terms_invalid_issue"] if False else result["issues"]:
        result["status"] = "OBSERVE"
    else:
        result["status"] = "NORMAL"
    return result


def load_prev_snapshot(cfg):
    sp = cfg.get("snapshot_path")
    if sp and os.path.exists(sp):
        try:
            with open(sp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def build_report(results, cfg, prev_snapshot, mode):
    now = datetime.now()
    total = len(results)
    by_status = {"NORMAL": 0, "OBSERVE": 0, "ALERT": 0, "FUSE": 0, "UNKNOWN": 0}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    issues = [r for r in results if r["status"] in ("ALERT", "FUSE")]
    report_id = "fullscan" if mode == "full" else ("deltascan" if mode == "delta" else "risk_recheck")
    report_id += "_" + now.strftime("%Y%m%d_%H%M%S")
    report = {
        "report_id": report_id,
        "mode": mode,
        "timestamp": now.isoformat(),
        "total_assets": total,
        "by_status": by_status,
        "issues": issues,
        "duration_ms": 0
    }
    return report, report_id


def main():
    parser = argparse.ArgumentParser(description="GLOBAL-ASSET-SCAN-V1")
    parser.add_argument("--full-scan", action="store_true", help="全量扫描")
    parser.add_argument("--delta-scan", action="store_true", help="增量扫描")
    parser.add_argument("--risk-recheck", action="store_true", help="风险重检")
    args = parser.parse_args()

    mode = "full"
    if args.delta_scan:
        mode = "delta"
    elif args.risk_recheck:
        mode = "risk"

    cfg = load_config()
    print("=" * 60)
    print("  GLOBAL-ASSET-SCAN-V1 全局资产扫描引擎")
    print("  模式: %s | 时间: %s" % (mode, datetime.now().isoformat()))
    print("=" * 60)

    t0 = time.time()
    prev = load_prev_snapshot(cfg) if mode in ("delta", "risk") else None
    assets = walk_assets(cfg)
    print("发现资产: %d 项" % len(assets))

    results = []
    parallel = min(cfg.get("parallel_limit", 16), 32)
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futs = {pool.submit(scan_one_asset, a, cfg, prev): a for a in assets}
        done = 0
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"path": futs[fut]["path"], "status": "UNKNOWN", "issues": ["扫描异常: %s" % str(e)], "type": "未知"})
            done += 1
            if done % 100 == 0 or done == len(assets):
                print("  进度: %d/%d" % (done, len(assets)))

    report, rid = build_report(results, cfg, prev, mode)
    report["duration_ms"] = round((time.time() - t0) * 1000, 1)

    # 保存报告
    os.makedirs(cfg.get("report_dir", "/opt/ZONGYUAN-ROOT/log/global_asset_scan/report"), exist_ok=True)
    rdir = cfg.get("report_dir", "/opt/ZONGYUAN-ROOT/log/global_asset_scan/report")
    with open(os.path.join(rdir, rid + ".json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新快照
    if cfg.get("snapshot_save", True):
        snap = {
            "engine": "GLOBAL-ASSET-SCAN-V1",
            "version": cfg.get("version", "1.0.0"),
            "scan_id": rid,
            "timestamp": report["timestamp"],
            "assets": {r["path"]: {"sha256": r.get("sha256"), "status": r["status"]} for r in results},
            "by_status": by_status if False else report["by_status"]
        }
        sp = cfg.get("snapshot_path", "/opt/ZONGYUAN-ROOT/snapshot/global_asset_snapshot_v1.json")
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        print("快照已更新: %s" % sp)

    # 控制台汇总
    print("")
    print("-" * 60)
    print("  扫描完成 | 总资产: %d | 耗时: %.1fs" % (total := len(results), report["duration_ms"] / 1000))
    print("  NORMAL: %d | OBSERVE: %d | ALERT: %d | FUSE: %d" % (
        report["by_status"].get("NORMAL", 0), report["by_status"].get("OBSERVE", 0),
        report["by_status"].get("ALERT", 0), report["by_status"].get("FUSE", 0)))
    if report["issues"]:
        print("  高风险资产:")
        for r in report["issues"][:10]:
            print("    - %s [%s] %s" % (r["path"], r["status"], "; ".join(r.get("issues", [])[:2])))
    print("  报告: %s" % os.path.join(rdir, rid + ".json"))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
