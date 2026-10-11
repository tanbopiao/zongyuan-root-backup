#!/usr/bin/env python3
# 多维表格对外桥接：外部写请求行 → 我轮询 → 调真模型 → 写回结果
import time, requests, json
from datetime import datetime
# --- ZR token 安全加载 ---
def _zr_load_token():
    import os
    t = os.environ.get("ZR_TOKEN")
    if t: return t
    try:
        for line in open('/home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env'):
            if line.startswith("ZR_TOKEN="):
                return line.strip().split("=",1)[1].strip('"')
    except Exception: pass
    return None
ZR_TOKEN = _zr_load_token()
# --- end ---


HUB = "https://www.huodouai.com/api/report/truth"
TOKEN = ZR_TOKEN if ZR_TOKEN else "ZR-CAPTURE-<ROTATED>"
QUEUE_KEY = "BRIDGE.REQUEST.QUEUE"
RESULT_KEY = "BRIDGE.RESULT.LATEST"

def pull_request():
    """从云端黑板拉最新请求"""
    try:
        r = requests.get(f"https://www.huodouai.com/api/truth/{QUEUE_KEY}", timeout=8)
        return r.json().get("truth", {}).get("truth_value")
    except: return None

def post_result(q, a):
    """把结果写回云端黑板"""
    requests.post(HUB, headers={"X-Capture-Token": TOKEN, "Content-Type":"application/json"},
        json={"key": RESULT_KEY, "value": json.dumps({"q":q[:100],"a":a[:500],"t":datetime.now().isoformat()})}, timeout=8)

if __name__ == "__main__":
    print("✅ 多维表格桥接器启动")
