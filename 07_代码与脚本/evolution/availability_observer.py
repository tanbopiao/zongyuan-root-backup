#!/usr/bin/env python3
"""A3 可用性观测器：三通道长期观测 + 自动告警 + 固化"""
import json, subprocess, datetime, os, sys

BASE = '/home/user/ZONGYUAN-ROOT'
OUT_DIR = os.path.join(BASE, '08_运行时数据与审计/evolution_20260929')
os.makedirs(OUT_DIR, exist_ok=True)

CHANNELS = [
    {"name": "A_主通道", "url": "https://www.huodouai.com/api/report/status", "kind": "cloud_main"},
    {"name": "B_备通道", "url": "https://drama.huodouai.com/api/report/status", "kind": "cloud_backup"},
    {"name": "C_飞书Base", "url": None, "kind": "feishu_base", "base_token": "QYn4bjgD6am3OPsxMCkcitcBnzc"},
]

def probe_http(url, timeout=10):
    try:
        r = subprocess.run(['curl', '-sS', '--max-time', str(timeout), '-o', '/dev/null',
                            '-w', '%{http_code}|%{time_total}', url], capture_output=True, text=True, timeout=timeout+5)
        code, t = r.stdout.strip().split('|')
        return {"reachable": code == '200', "http_code": int(code), "latency_s": round(float(t), 3)}
    except Exception as e:
        return {"reachable": False, "http_code": 0, "latency_s": 0, "error": str(e)}

def probe_feishu():
    try:
        r = subprocess.run(['lark-cli', 'base', '+table-list', '--base-token', CHANNELS[2]['base_token'], '--as', 'user'],
                           capture_output=True, text=True, timeout=20)
        return {"reachable": r.returncode == 0, "http_code": r.returncode, "latency_s": 0,
                "note": "lark-cli base table-list" + ("OK" if r.returncode == 0 else "FAIL")}
    except Exception as e:
        return {"reachable": False, "error": str(e)}

now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
results = []
all_ok = True
for ch in CHANNELS:
    if ch["kind"] == "feishu_base":
        res = probe_feishu()
    else:
        res = probe_http(ch["url"])
    results.append({"channel": ch["name"], "kind": ch["kind"], **res})
    if not res["reachable"]:
        all_ok = False

record = {
    "check_id": f"OBS-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    "timestamp": now,
    "channels": results,
    "all_reachable": all_ok,
    "availability": "3/3" if all_ok else f"{sum(1 for r in results if r['reachable'])}/3",
}

log_path = os.path.join(OUT_DIR, 'availability_log.jsonl')
with open(log_path, 'a') as f:
    f.write(json.dumps(record, ensure_ascii=False) + '\n')

print(json.dumps(record, ensure_ascii=False, indent=2))
print(f"\n{'✅ 三通道全部可达' if all_ok else '⚠️ 存在不可达通道，需告警处理'} | 日志: {log_path}")
