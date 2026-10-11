#!/usr/bin/env python3
# 本地常驻任务队列（免费，吃空闲CPU）
import json, os, time, subprocess
Q = "/home/user/Doubao/chats/38438491307070978/local_workers/queue.json"
if not os.path.exists(Q):
    json.dump([], open(Q,"w"))
print("[queue] 常驻任务队列已就绪")
