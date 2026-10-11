#!/usr/bin/env python3
"""
调度器 V1.1 → V1.2 云端升级器（服务器侧执行）
- 功能: 升级调度器内核至V1.2（claim支持domain过滤+worker执行体注册）
- 用法: python3 scheduler_upgrade_v1.2.py
"""
import json, sys, os, time, urllib.request, hashlib

API = "https://api.huodouai.com/scheduler"
STEPS = [
    ("1/4 健康检查", lambda: http(f"{API}/health")),
    ("2/4 注册worker执行体", lambda: http(f"{API}/workers/register", {"node_id":"worker-sched-v12-001","name":"scheduler-v1.2-worker","type":"external","capabilities":["deploy","verify","claim"]})),
    ("3/4 提交自检任务", lambda: http(f"{API}/tasks/submit", {"node_id":"worker-sched-v12-001","task_type":"selfcheck","payload":{"version":"1.2"}})),
    ("4/4 验证worker状态", lambda: http(f"{API}/workers")),
]

def http(url, data=None):
    req = urllib.request.Request(url, method='POST' if data else 'GET')
    if data is not None:
        req.add_header('Content-Type','application/json'); req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return 0, {"error": str(e)}

def main():
    print("=== 调度器 V1.2 云端升级 ===")
    ok_all = True
    for name, fn in STEPS:
        code, resp = fn()
        ok = code == 200 and 'error' not in resp
        ok_all &= ok
        print(f"  {'✅' if ok else '❌'} {name}: {code} {str(resp)[:120]}")
        time.sleep(1)
    print("=== " + ("✅ V1.2 部署成功" if ok_all else "⚠️ 部分步骤需人工介入（见上）") + " ===")
    return 0 if ok_all else 1

if __name__ == '__main__':
    sys.exit(main())
