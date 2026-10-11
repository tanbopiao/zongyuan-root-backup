#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 任务自动编排器 V1.0
定时读取任务台账 → 按优先级+依赖排序 → 自动执行 → 回写状态 → 失败重试
"""
import json
import subprocess
import time
import os
import sys
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
ORCH_DIR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/task_orchestrator"
LEDGER_PATH = f"{ORCH_DIR}/task_ledger.json"
RETRY_PATH = f"{ORCH_DIR}/task_retry_queue.json"
LOG_PATH = f"{ORCH_DIR}/orchestrator.log"

PRIO_MAP = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

def now():
    return datetime.now(TZ).isoformat()

def log(msg):
    line = f"[{now()}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_ledger():
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ledger(data):
    data["last_scan"] = now()
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_retry_queue():
    if os.path.exists(RETRY_PATH):
        with open(RETRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"queue": []}

def save_retry_queue(q):
    with open(RETRY_PATH, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=2)

def deps_satisfied(task, done_ids):
    return all(d in done_ids for d in task.get("depend_on", []))

def run_task(task):
    script = task["script_path"]
    args = task.get("args", [])
    timeout = task.get("timeout_sec", 120)
    if not os.path.exists(script):
        return False, f"script not found: {script}"
    try:
        cmd = ["python3" if script.endswith(".py") else "bash", script] + args
        ret = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        output = (ret.stdout + ret.stderr)[-2000:]
        return ret.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except Exception as e:
        return False, f"exception: {e}"

def main():
    log("=" * 60)
    log("任务自动编排器启动")
    ledger = load_ledger()
    pending = [t for t in ledger["tasks"] if t["status"] == "pending"]
    log(f"待执行任务: {len(pending)}")

    done_ids = set()
    success = 0
    failed = 0
    skipped = 0

    # 多轮调度，直到无新可执行任务
    while True:
        # 找出依赖已满足的pending任务
        ready = [t for t in ledger["tasks"]
                 if t["status"] == "pending" and deps_satisfied(t, done_ids)]
        ready.sort(key=lambda x: PRIO_MAP.get(x["priority"], 99))

        if not ready:
            break

        for task in ready:
            log(f"执行 [{task['priority']}] {task['task_id']}: {task['name']}")
            ok, msg = run_task(task)
            task["last_run"] = now()

            if ok:
                task["status"] = "success"
                task["result"] = msg[-500:]
                done_ids.add(task["task_id"])
                success += 1
                log(f"  ✅ 成功")
            else:
                task["retry_count"] += 1
                if task["retry_count"] >= task["max_retry"]:
                    task["status"] = "failed"
                    failed += 1
                    log(f"  ❌ 失败（达到最大重试 {task['max_retry']}次）: {msg[:200]}")
                else:
                    skipped += 1
                    log(f"  ⚠️ 失败（重试 {task['retry_count']}/{task['max_retry']}）: {msg[:200]}")
                task["result"] = msg[-500:]
            save_ledger(ledger)

    summary = f"成功:{success} 重试:{skipped} 失败:{failed} 总:{len(pending)}"
    ledger["last_run_summary"] = summary
    save_ledger(ledger)
    log(f"完成 - {summary}")
    log("=" * 60)

if __name__ == "__main__":
    main()
