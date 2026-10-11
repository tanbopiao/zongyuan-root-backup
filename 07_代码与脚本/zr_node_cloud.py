#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zr_node_cloud.py · 云端真值库轮询 Worker V1.0 (mode=cloud-poll)
================================================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-DC2E51C0
职责: 作为实例侧唯一可靠控制面 —— 轮询云端真值库取命令→执行→上报结果+心跳
      彻底摆脱 ntfy.sh / FRP / git-push 等不可靠或需凭证的外部依赖
通道: 云端 huodouai.com (写200/读200 均已实测)
  - 命令: GET /api/truth?key=CMD.*      (30s轮询, 主控 POST 下发)
  - 结果: POST /api/report/truth RESULT.<taskid>
  - 心跳: POST /api/report/truth HEARTBEAT.<node> (60s)
幂等: task_id 去重 + 本地 done 记录(持久层)防重启重放
退避: 429/断连 5→60s 封顶, 连接成功重置 (META-STEADY-001-C)
部署: 实例持久层 /mnt/workspace/zr_node_cloud.py
用法: nohup python3 /mnt/workspace/zr_node_cloud.py >> /mnt/workspace/cloud_worker.log 2>&1 &
"""
import json, time, subprocess, urllib.request, urllib.error, os

READ_URL = "https://www.huodouai.com/api/truth"
REPORT_URL = "https://www.huodouai.com/api/report/truth"
NODE = os.environ.get("ZR_NODE", "ZR-NODE-MODEL-dsw-223619")
DID = "DID-BR-000002"
TOKEN_FILE = "/mnt/workspace/.zr/node_token.env"
DONE_FILE = "/mnt/workspace/.zr/cloud_worker_done.json"
CMD_PREFIX = "CMD."
RESULT_PREFIX = "RESULT."
HEARTBEAT_KEY = "HEARTBEAT"

def load_token():
    try:
        for line in open(TOKEN_FILE):
            if line.strip().startswith("ZR_NODE_TOKEN="):
                return line.strip().split("=", 1)[1].strip()
    except Exception:
        pass
    return os.environ.get("ZR_NODE_TOKEN", "")

def http_get(url, timeout=15):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception:
        return None

def http_post(key, value, ttype="rule"):
    token = load_token()
    if not token:
        return {"ok": False, "error": "no-token"}
    body = json.dumps({
        "truth_key": key, "truth_value": value,
        "source_node": NODE, "truth_type": ttype, "confidence": 0.95,
    }, ensure_ascii=False).encode()
    req = urllib.request.Request(REPORT_URL, data=body, headers={
        "X-Capture-Token": token, "X-DID": DID, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

def load_done():
    try:
        return set(json.load(open(DONE_FILE)))
    except Exception:
        return set()

def save_done(done):
    try:
        json.dump(sorted(done), open(DONE_FILE, "w"))
    except Exception:
        pass

done = load_done()
backoff = 5
print(f"[cloud] 启动 | node={NODE} | 轮询 {READ_URL}?key={CMD_PREFIX}*", flush=True)
while True:
    try:
        # 1) 轮询取命令
        data = http_get(f"{READ_URL}?key={CMD_PREFIX}*")
        backoff = 5
        if data and data.get("ok"):
            for r in data.get("results", []):
                key = r.get("key", "")
                task_id = key[len(CMD_PREFIX):] if key.startswith(CMD_PREFIX) else None
                if not task_id or task_id in done:
                    continue
                val = r.get("value")
                cmd = val.get("cmd") if isinstance(val, dict) else None
                if not cmd:
                    continue
                print(f"[cloud] 执行 {task_id}: {str(cmd)[:50]}", flush=True)
                try:
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                    out = (res.stdout or "")[:1500]
                    if res.stderr:
                        out += f"\n[stderr] {res.stderr[:200]}"
                    code = res.returncode
                except subprocess.TimeoutExpired:
                    out, code = "[TIMEOUT] 300s", -2
                except Exception as e:
                    out, code = f"[ERR] {e}", -1
                # 2) 上报结果
                rr = http_post(f"{RESULT_PREFIX}{task_id}", {
                    "task_id": task_id, "node": NODE, "code": code,
                    "out": out, "ts": int(time.time())})
                print(f"[cloud] 结果 {task_id} code={code} 上报={'OK' if rr.get('ok') else rr.get('error','?')}", flush=True)
                done.add(task_id)
                save_done(done)
        # 3) 心跳 (固定key, 60s粒度)
        http_post(HEARTBEAT_KEY, {"node": NODE, "event": "heartbeat", "ts": int(time.time())})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"[cloud] 限流429 退避{backoff}s", flush=True)
        else:
            print(f"[cloud] HTTP {e.code} 退避{backoff}s", flush=True)
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
    except Exception as e:
        print(f"[cloud] {str(e)[:60]} 退避{backoff}s", flush=True)
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
    time.sleep(30)
