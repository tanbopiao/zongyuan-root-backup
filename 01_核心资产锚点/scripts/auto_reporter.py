#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一共享大脑 · 全自动上报调度器 V1.0
链路A: 本地 → 云端真值库（主www/备drama双通道自动降级）
链路B: 本地 → 飞书共享大脑「元极恒一共享大脑」跨节点消息同步表
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import requests, hashlib, json, time, os, sys
from datetime import datetime, timezone

# === 配置区 ===
TRUTH_MAIN = "https://www.huodouai.com/api/report/truth"
TRUTH_BACKUP = "https://drama.huodouai.com/api/report/truth"
HEALTH_URL = "https://www.huodouai.com/api/report/status"
FEISHU_BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
DID = "DID-BR-000002"
BOOTSTRAP_KEY = "元极恒一"
CAPTURE_TOKEN = "ZR-CAPTURE-OMEGA-d04bb54ba2a55a7d"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "report_log")
RETRY_QUEUE = os.path.join(LOG_DIR, "retry_queue.json")
MAX_RETRY = 5

os.makedirs(LOG_DIR, exist_ok=True)

def sha256(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(os.path.join(LOG_DIR, "reporter.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def post_truth(key, value):
    """链路A: 上报云端真值库，主备自动降级"""
    headers = {"X-Capture-Token": CAPTURE_TOKEN, "Content-Type": "application/json"}
    body = {"key": key, "value": value}
    for name, url in [("main", TRUTH_MAIN), ("backup", TRUTH_BACKUP)]:
        try:
            r = requests.post(url, json=body, headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                log(f"✅ 真值上报成功[{name}]: key={key[:40]} action={data.get('action','?')}")
                return {"ok": True, "channel": name, "resp": data}
        except Exception as e:
            log(f"⚠️ 真值上报失败[{name}]: {e}")
    return {"ok": False, "error": "all channels unreachable"}

def load_queue():
    if os.path.exists(RETRY_QUEUE):
        with open(RETRY_QUEUE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_queue(q):
    with open(RETRY_QUEUE, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=2)

def retry_dispatch():
    """补发队列：指数退避，最多MAX_RETRY次"""
    q = load_queue()
    if not q:
        log("补发队列为空")
        return
    new_q = []
    for item in q:
        if item.get("retry_count", 0) >= MAX_RETRY:
            log(f"❌ 永久失败丢弃: {item.get('key','?')}")
            continue
        res = post_truth(item["key"], item["value"])
        if not res["ok"]:
            item["retry_count"] = item.get("retry_count", 0) + 1
            item["next_retry"] = time.time() + (2 ** item["retry_count"]) * 30
            new_q.append(item)
    save_queue(new_q)
    log(f"补发完成: {len(q) - len(new_q)}成功, {len(new_q)}待重试")

def report(key, value, source="NODE-DEV-DOUBAO-WORK-001", cat="task"):
    """对外统一上报入口"""
    # L0校验
    if not key or not value:
        log("❌ L0校验失败: key或value为空")
        return {"ok": False, "msg": "L0 validation failed"}
    
    # 附加元信息
    ts = datetime.now(timezone.utc).isoformat()
    full_value = f"[元极恒一|{DID}|{source}|{cat}|{ts}]\n{value}"
    h = sha256(full_value)
    
    res = post_truth(key, full_value)
    
    if not res["ok"]:
        q = load_queue()
        q.append({"key": key, "value": full_value, "retry_count": 0, "ts": ts})
        save_queue(q)
        log(f"📥 进入补发队列: {key[:40]}")
    
    return res

def health_check():
    """探测云端通道健康"""
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            count = data.get("truth_count", data.get("total", "?"))
            log(f"💚 云端健康: truth_count={count}")
            return {"ok": True, "truth_count": count}
    except Exception as e:
        log(f"💔 云端健康检查失败: {e}")
    return {"ok": False}

if __name__ == "__main__":
    log("═══ 元极恒一全自动上报调度器启动 ═══")
    health_check()
    retry_dispatch()
    # 示例上报
    if len(sys.argv) > 2:
        report(sys.argv[1], sys.argv[2])
    log("═══ 本轮执行完毕 ═══")
