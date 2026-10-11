#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_stress_tester 语义API并发压测脚本
对 /api/semantic 系列接口做并发压测，采集吞吐/延迟/错误率，输出报告
用法:
  --scene A|B|C   指定场景（默认A）
  --all           跑全部场景
"""
import os
import sys
import json
import time
import argparse
import threading
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG_PATH = "/opt/ZONGYUAN-ROOT/config/stress_config.json"
DEFAULT_CONFIG = {
    "base_url": "http://127.0.0.1:9120/api/semantic",
    "scenes": {
        "A": {"name": "轻量常规", "concurrency": 10, "total_requests": 200, "timeout": 5},
        "B": {"name": "中负载批量对账", "concurrency": 50, "total_requests": 1000, "timeout": 8},
        "C": {"name": "高负载极限", "concurrency": 120, "total_requests": 2000, "timeout": 10}
    },
    "error_abort_threshold": 0.05,
    "endpoints": {
        "validate": {"weight": 4, "method": "POST", "path": "/validate"},
        "translate": {"weight": 3, "method": "POST", "path": "/translate"},
        "l0-check": {"weight": 2, "method": "POST", "path": "/l0-check"},
        "stats": {"weight": 1, "method": "GET", "path": "/stats"}
    },
    "sample_terms": ["九头身", "凤目", "月白", "神女", "玄黑", "削肩", "仙姿", "华冠", "樱唇", "蛾眉"]
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def build_payload(endpoint, terms):
    t = terms[0]
    if endpoint == "validate":
        return {"term": t, "context": t}
    if endpoint == "translate":
        return {"term": t, "model": "agnes_image"}
    if endpoint == "l0-check":
        return {"text": "纯东方神女，%s，削肩，气场强大，法相庄严" % t}
    return None


def do_request(base_url, ep_name, ep_cfg, terms, timeout):
    url = base_url + ep_cfg["path"]
    start = time.time()
    try:
        if ep_cfg["method"] == "GET":
            req = urllib.request.Request(url)
        else:
            payload = build_payload(ep_name, terms)
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            code = resp.status
        ok = code == 200
        return {"ok": ok, "code": code, "latency_ms": round((time.time() - start) * 1000, 1), "size": len(body)}
    except Exception as e:
        return {"ok": False, "code": -1, "latency_ms": round((time.time() - start) * 1000, 1),
                "error": str(e)[:120]}


def weighted_endpoint_choice(endpoints, rnd_state):
    total = sum(e["weight"] for e in endpoints.values())
    import random
    r = random.randint(1, total)
    acc = 0
    for name, ep in endpoints.items():
        acc += ep["weight"]
        if r <= acc:
            return name
    return "validate"


def run_scene(cfg, scene_key):
    scene = cfg["scenes"][scene_key]
    base_url = cfg["base_url"]
    endpoints = cfg["endpoints"]
    terms = cfg.get("sample_terms", [])
    concurrency = scene["concurrency"]
    total_req = scene["total_requests"]
    timeout = scene["timeout"]
    abort_threshold = cfg.get("error_abort_threshold", 0.05)

    print("")
    print("=" * 64)
    print("  场景%s: %s | 并发=%d | 总请求=%d" % (scene_key, scene["name"], concurrency, total_req))
    print("=" * 64)

    stats_lock = threading.Lock()
    results = {"ok": 0, "fail": 0, "latencies": [], "errors": {}}
    abort_flag = {"value": False}

    def worker(_):
        if abort_flag["value"]:
            return
        ep_name = weighted_endpoint_choice(endpoints, None)
        ep = endpoints[ep_name]
        r = do_request(base_url, ep_name, ep, terms, timeout)
        with stats_lock:
            if r["ok"]:
                results["ok"] += 1
            else:
                results["fail"] += 1
                err_key = str(r.get("code")) + ":" + (r.get("error", "")[:60])
                results["errors"][err_key] = results["errors"].get(err_key, 0) + 1
            results["latencies"].append(r["latency_ms"])
            total_done = results["ok"] + results["fail"]
            if total_done >= 20 and results["fail"] / total_done > abort_threshold:
                abort_flag["value"] = True

    t0 = time.time()
    batch_size = concurrency * 4
    for start_i in range(0, total_req, batch_size):
        batch = list(range(start_i, min(start_i + batch_size, total_req)))
        if abort_flag["value"]:
            print("  [熔断] 错误率超阈值，提前终止")
            break
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futs = [pool.submit(worker, i) for i in batch]
            for _ in as_completed(futs):
                pass
    total_time = time.time() - t0

    ok = results["ok"]
    fail = results["fail"]
    total = ok + fail
    lat = sorted(results["latencies"])
    def pct(p):
        if not lat:
            return 0.0
        idx = min(len(lat) - 1, int(len(lat) * p / 100))
        return lat[idx]
    report = {
        "scene": scene_key,
        "scene_name": scene["name"],
        "concurrency": concurrency,
        "total_requests": total,
        "success": ok,
        "failed": fail,
        "error_rate": round(fail / total * 100, 2) if total else 0,
        "qps": round(total / total_time, 1) if total_time else 0,
        "total_time_s": round(total_time, 2),
        "latency_ms": {
            "p50": pct(50), "p90": pct(90), "p95": pct(95), "p99": pct(99),
            "max": lat[-1] if lat else 0, "avg": round(sum(lat) / len(lat), 1) if lat else 0
        },
        "errors": results["errors"],
        "timestamp": datetime.now().isoformat()
    }
    print("  完成: %d/%d | 错误率: %.2f%% | QPS: %.1f | 耗时: %.2fs" % (
        ok, total, report["error_rate"], report["qps"], report["total_time_s"]))
    print("  P50: %.1fms | P90: %.1fms | P95: %.1fms | P99: %.1fms | MAX: %.1fms" % (
        report["latency_ms"]["p50"], report["latency_ms"]["p90"],
        report["latency_ms"]["p95"], report["latency_ms"]["p99"], report["latency_ms"]["max"]))
    return report


def main():
    parser = argparse.ArgumentParser(description="语义API并发压测")
    parser.add_argument("--scene", choices=["A", "B", "C"], default="A")
    parser.add_argument("--all", action="store_true", help="跑全部场景")
    args = parser.parse_args()

    cfg = load_config()
    os.makedirs("/opt/ZONGYUAN-ROOT/log/semantic_stress_report", exist_ok=True)
    reports = []
    if args.all:
        for k in ["A", "B", "C"]:
            reports.append(run_scene(cfg, k))
    else:
        reports.append(run_scene(cfg, args.scene))

    # 汇总报告
    summary = {
        "engine": "semantic-stress-tester",
        "version": cfg.get("version", "1.0.0"),
        "timestamp": datetime.now().isoformat(),
        "scenes": reports
    }
    out = "/opt/ZONGYUAN-ROOT/log/semantic_stress_report/stress_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("")
    print("报告已保存: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
