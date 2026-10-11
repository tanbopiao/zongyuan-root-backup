#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN GPU 实例反向轮询 Agent（SOP 最简版）
- 每 5s GET 云服务器 7860 /api/agent/pull 拉任务
- 拿到 cmd -> subprocess 执行 -> POST /api/agent/result 回传
- 无需 SSH/frp/ngrok
"""
import requests, subprocess, time, json, sys

SERVER = "http://123.207.202.158:7860"
PULL   = SERVER + "/api/agent/pull"
RESULT = SERVER + "/api/agent/result"
AGENT_ID = "t4-cloudstudio-38380684638744576"
INTERVAL = 5

def run_cmd(cmd):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        out = (p.stdout or "")[-4000:]
        err = (p.stderr or "")[-2000:]
        return {"ok": p.returncode == 0, "stdout": out, "stderr": err, "rc": p.returncode}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "rc": -1}

def main():
    print(f"[agent] start, id={AGENT_ID}, poll={PULL}", flush=True)
    while True:
        try:
            r = requests.get(PULL, timeout=15)
            if r.status_code != 200:
                print(f"[agent] pull http {r.status_code} {r.text[:120]}", flush=True)
                time.sleep(INTERVAL); continue
            data = r.json()
            cmd = data.get("cmd") or data.get("command")
            if not cmd:
                time.sleep(INTERVAL); continue
            task_id = data.get("task_id", "unknown")
            print(f"[agent] recv task {task_id}: {cmd[:100]}", flush=True)
            res = run_cmd(cmd)
            res.update({"task_id": task_id, "agent_id": AGENT_ID})
            requests.post(RESULT, json=res, timeout=20)
            print(f"[agent] done task {task_id} rc={res['rc']}", flush=True)
        except requests.exceptions.ConnectionError:
            print("[agent] conn refused, retry...", flush=True)
            time.sleep(INTERVAL)
        except Exception as e:
            print(f"[agent] err {e}", flush=True)
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
