#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zr_cmd_push.py · 主控侧云端命令下发/确认工具 V1.0
================================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-DC2E51C0
配套 zr_node_cloud.py (实例侧 cloud-poll worker):
  - 下发: 写云端 CMD.<taskid> = {cmd, node?}
  - 确认: 读云端 RESULT.<taskid> (实例执行后写入)

用法:
  python3 zr_cmd_push.py send <task_id> "<shell cmd>"        # 下发命令
  python3 zr_cmd_push.py check <task_id> [--wait 30]         # 轮询读结果(默认最多30s)
  python3 zr_cmd_push.py heartbeat <node>                    # 手动查心跳
"""
import json, sys, time, urllib.request, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zr_node_protocol import report_truth

READ_URL = "https://www.huodouai.com/api/truth"
GATEWAY = "https://www.huodouai.com/api/report/truth"

def http_get(url, timeout=15):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception:
        return None

def read_key(prefix):
    """读云端 key 前缀的最新结果 (results 通常按新→旧)"""
    data = http_get(f"{READ_URL}?key={prefix}*")
    if not data or not data.get("ok"):
        return None
    return data.get("results", [])

def cmd_send(task_id, cmd, node=None):
    val = {"cmd": cmd, "node": node, "ts": int(time.time())}
    if node:
        val["node"] = node
    r = report_truth(f"CMD.{task_id}", json.dumps(val, ensure_ascii=False),
                     source_node="ZR-NODE-DC2E51C0")
    return r

def cmd_check(task_id, wait=30):
    """轮询读 RESULT.<taskid> 直到实例上报 (上限 wait 秒)"""
    deadline = time.time() + wait
    while time.time() < deadline:
        rs = read_key(f"RESULT.{task_id}")
        if rs:
            # 取最新(第一条)与 task_id 匹配的
            for r in rs:
                k = r.get("key", "")
                if k.endswith(f"RESULT.{task_id}") or k == f"RESULT.{task_id}":
                    return r
        time.sleep(3)
    return None

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    act = args[0]
    if act == "send" and len(args) >= 3:
        r = cmd_send(args[1], args[2], args[3] if len(args) > 3 else None)
        print("下发:", json.dumps(r, ensure_ascii=False))
    elif act == "check" and len(args) >= 2:
        w = int(args[2]) if len(args) > 2 else 30
        r = cmd_check(args[1], w)
        if r:
            print("结果:", json.dumps(r, ensure_ascii=False))
        else:
            print(f"未收到 RESULT.{args[1]} (超时 {w}s)")
    elif act == "heartbeat" and len(args) >= 2:
        rs = read_key("HEARTBEAT")
        print("心跳记录:", json.dumps(rs[:3], ensure_ascii=False))
    else:
        print(__doc__)
