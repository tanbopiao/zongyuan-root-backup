#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_improve_runner.py — 自我改进闭环调度器
串联 07_evaluate → 08_propose → 09_verify，形成六环闭环的前三环自动化：
①观察/评估(07) → ③提案(08) → ⑤验证/沉淀(09)
与主流水线(01-06)互补：主流水线处理"外部真值→商业化"，本闭环处理"系统自身→自我进化"。

用法: python3 self_improve_runner.py [--loop]
  --loop: 连续运行（评估→提案→(可选执行)→验证→沉淀），默认单轮
"""
import os, sys, json, subprocess, datetime, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
LOGS = os.path.join(ROOT, "logs")
os.makedirs(LOGS, exist_ok=True)

STAGES = [
    ("evaluate", "07_evaluate.py"),
    ("propose", "08_propose.py"),
    ("verify", "09_verify.py"),
]


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="持续闭环（默认单轮）")
    args = ap.parse_args()

    run_id = "IMP-RUN-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    started = now_iso()
    stages_status = {}

    for sid, script in STAGES:
        spath = os.path.join(SCRIPT_DIR, script)
        print(f"\n=== [{run_id}] stage: {sid} -> {script} ===")
        try:
            r = subprocess.run([sys.executable, spath], capture_output=True, text=True, timeout=120)
            tail = (r.stdout or "").strip().splitlines()[-4:]
            if r.returncode == 0:
                stages_status[sid] = {"status": "ok", "message": " | ".join(tail)}
            else:
                err = (r.stderr or r.stdout or "").strip().splitlines()[-4:]
                stages_status[sid] = {"status": "fail", "message": " | ".join(err)}
        except Exception as e:
            stages_status[sid] = {"status": "fail", "message": str(e)}

    fails = [s for s, v in stages_status.items() if v.get("status") == "fail"]
    status = "success" if not fails else "partial"

    log = {
        "run_id": run_id,
        "started_at": started,
        "finished_at": now_iso(),
        "status": status,
        "loop": args.loop,
        "stages": stages_status,
    }
    log_path = os.path.join(LOGS, f"improve_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\n=== [{run_id}] DONE status={status} log={log_path} ===")
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
