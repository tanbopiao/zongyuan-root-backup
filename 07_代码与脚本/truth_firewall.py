#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 节点侧真值防火墙 V1.0
作用：中枢写入口暂未加鉴权，本脚本在节点侧做"客户端校验"
     —— 拉取高阶层真值时，只信任白名单内的 key，其余视为伪造/可疑，拒绝执行。
用法：
  python3 truth_firewall.py                 # 检查全部高阶层真值
  python3 truth_firewall.py RULE.META.XXX   # 检查单条
白名单：allowed_meta_keys.txt（每行一个 key 前缀/完整 key）
"""
import sys, json, urllib.request, os
# --- ZR token 安全加载 ---
def _zr_load_token():
    import os
    t = os.environ.get("ZR_TOKEN")
    if t: return t
    try:
        envp = '/home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env'
        for line in open(envp):
            if line.startswith("ZR_TOKEN="):
                return line.strip().split("=",1)[1].strip('"')
    except Exception:
        pass
    return None
ZR_TOKEN = _zr_load_token()
# --- end ---


GATEWAY = "https://www.huodouai.com/api/truth"
TOKEN = ZR_TOKEN if ZR_TOKEN else "ZR-CAPTURE-<ROTATED>"
BASE = "/home/user/ZONGYUAN-ROOT"
WHITELIST_FILE = os.path.join(BASE, "01_核心资产锚点/02_capabilities/allowed_meta_keys.txt")

# 高阶层前缀（这些 key 一旦被伪造，危害最大）
HIGH_LEVEL_PREFIXES = ("RULE.META", "PROTOCOL", "AXIOM", "META.", "LAW.")

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return set()
    with open(WHITELIST_FILE, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}

def is_allowed(key, wl):
    """白名单匹配：完整 key 命中，或 key 以白名单前缀开头"""
    if key in wl:
        return True
    return any(key.startswith(p) for p in wl if p.endswith("*"))

def check_one(key):
    wl = load_whitelist()
    try:
        req = urllib.request.Request(f"{GATEWAY}/{key}", headers={"X-Capture-Token": TOKEN})
        d = json.load(urllib.request.urlopen(req, timeout=10))
        t = d.get("truth", {})
    except Exception as e:
        return {"key": key, "verdict": "FETCH_FAIL", "reason": str(e)}
    is_high = any(key.startswith(p) for p in HIGH_LEVEL_PREFIXES)
    if is_high and not is_allowed(key, wl):
        return {"key": key, "verdict": "SUSPECT", "reason": "高阶层但不在白名单，疑似伪造，禁止执行",
                "value": t.get("truth_value","")[:80]}
    return {"key": key, "verdict": "TRUSTED", "version": t.get("version")}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keys = sys.argv[1:]
    else:
        # 无指定时：抽查关键白名单外的高阶层（演示用，实际拉全量需分页）
        keys = ["RULE.META.POLLUTION-DEMO-FAKE", "RULE.NAMING.TRUTH_KEY.V1",
                "ACTIVATION.NODE_REPORT_GATEWAY.20260915", "META.BOOTSTRAP"]
    print(f"白名单条目: {len(load_whitelist())}")
    for k in keys:
        r = check_one(k)
        mark = {"TRUSTED":"✅","SUSPECT":"🚫","FETCH_FAIL":"⚠️"}.get(r["verdict"],"?")
        print(f"  {mark} {k} → {r['verdict']} {r.get('reason','')}")
