#!/usr/bin/env python3
"""自动恢复补发：云端通了就重发积压信号"""
import json, os, glob, urllib.request, time
BASE = "/home/user/Doubao/chats/38438491307070978"
QUEUE = f"{BASE}/retry_queue"
os.makedirs(QUEUE, exist_ok=True)
def alive():
    try:
        urllib.request.urlopen("https://www.huodouai.com/api/truths/", timeout=6)
        return True
    except: return False
if not alive():
    print("云端未恢复，跳过补发"); raise SystemExit
files = sorted(glob.glob(f"{QUEUE}/*.json"))
sent = 0
for f in files:
    try:
        d = json.load(open(f))
        req = urllib.request.Request("https://www.huodouai.com/api/report/truth",
            data=json.dumps(d).encode(), headers={"Content-Type":"application/json","X-Capture-Token":"DID-BR-000002"})
        urllib.request.urlopen(req, timeout=10)
        os.rename(f, f+".sent"); sent += 1
    except Exception as e:
        print("补发失败", f, e); break
print(f"补发完成: {sent}/{len(files)}")
