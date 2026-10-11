#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_runner.py — 总调度器
依次执行 01→02→03→04→05→06，每步检查退出状态；
某阶段失败不阻断后续阶段，记录状态后继续。
生成 logs/run_YYYYMMDD_HHMMSS.json 运行日志（符合 run_log_schema）。
用法: python3 pipeline_runner.py [--trigger cron|manual|submit]
"""
import os, sys, json, subprocess, datetime, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(ROOT, "logs")
os.makedirs(LOGS, exist_ok=True)

STAGES = [
    ("detect", "01_detect.py"),
    ("extract", "02_extract.py"),
    ("visualize", "03_visualize.py"),
    ("productize", "04_productize.py"),
    ("price", "05_price.py"),
    ("circulate", "06_circulate.py"),
]


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", default="manual", choices=["cron", "manual", "submit"])
    args = ap.parse_args()

    run_id = "RUN-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    started = now_iso()
    stages_status = {}
    asset_ids = []

    for sid, script in STAGES:
        spath = os.path.join(SCRIPT_DIR, script)
        cmd = [sys.executable, spath]
        if sid == "detect":
            cmd += ["--trigger", args.trigger]
        print(f"\n=== [{run_id}] stage: {sid} -> {script} ===")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            stdout_tail = (r.stdout or "").strip().splitlines()[-3:]
            if r.returncode == 0:
                stages_status[sid] = {"status": "ok", "message": " | ".join(stdout_tail)}
            else:
                err = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
                stages_status[sid] = {"status": "fail", "message": " | ".join(err)}
        except Exception as e:
            stages_status[sid] = {"status": "fail", "message": str(e)}

    # 汇总各阶段统计
    try:
        with open(os.path.join(DATA, "new_assets.json"), "r", encoding="utf-8") as f:
            stages_status["detect"]["new_count"] = json.load(f).get("new_count", 0)
    except Exception:
        stages_status["detect"].setdefault("new_count", 0)

    try:
        with open(os.path.join(DATA, "asset_cards.json"), "r", encoding="utf-8") as f:
            ac = json.load(f)
            stages_status["extract"]["cards_count"] = ac.get("new_this_run", 0)
            asset_ids = [c["asset_id"] for c in ac.get("cards", [])]
    except Exception:
        stages_status["extract"].setdefault("cards_count", 0)

    stages_status["visualize"]["output_path"] = "output/asset_showcase.html"
    try:
        with open(os.path.join(DATA, "product_entries.json"), "r", encoding="utf-8") as f:
            stages_status["productize"]["products_count"] = json.load(f).get("new_this_run", 0)
    except Exception:
        stages_status["productize"].setdefault("products_count", 0)
    try:
        with open(os.path.join(DATA, "pricing_results.json"), "r", encoding="utf-8") as f:
            stages_status["price"]["priced_count"] = json.load(f).get("new_this_run", 0)
    except Exception:
        stages_status["price"].setdefault("priced_count", 0)
    try:
        with open(os.path.join(DATA, "circulation_results.json"), "r", encoding="utf-8") as f:
            stages_status["circulate"]["circulated_count"] = json.load(f).get("total", 0)
    except Exception:
        stages_status["circulate"].setdefault("circulated_count", 0)

    # 总状态
    fails = [s for s, v in stages_status.items() if v.get("status") == "fail"]
    status = "success" if not fails else ("partial" if len(fails) < len(STAGES) else "failed")

    log = {
        "run_id": run_id,
        "started_at": started,
        "finished_at": now_iso(),
        "status": status,
        "trigger": args.trigger,
        "stages": stages_status,
        "asset_ids": asset_ids,
        "artifacts": {
            "asset_cards": "data/asset_cards.json",
            "showcase": "output/asset_showcase.html",
            "products": "data/product_entries.json",
            "pricing": "data/pricing_results.json",
            "circulation": "data/circulation_results.json",
        },
    }
    log_path = os.path.join(LOGS, f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\n=== [{run_id}] DONE status={status} log={log_path} ===")
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
