#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 常驻任务轮询器 V1.0
部署在腾讯云服务器上，7×24运行
功能: 轮询云端任务队列 → 拉任务 → 调魔搭API执行 → 回写结果
"""
import json, time, requests, datetime, os, sys

# ===== 配置 =====
CLOUD_BASE = "https://www.huodouai.com/api"
REPORT_TOKEN = "ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"
MODELSCOPE_API = "https://api-inference.modelscope.cn/v1/chat/completions"
MODELSCOPE_KEY = "ms-673547d6-508b-4242-a862-85de112a3ce7"
POLL_INTERVAL = 300  # 5分钟轮询一次
OUTPUT_DIR = "/root/zongyuan-poller/output"
LOG_FILE = "/root/zongyuan-poller/poller.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def fetch_task():
    """从云端拉取待执行任务"""
    try:
        r = requests.get(f"{CLOUD_BASE}/truths/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            # 找状态为PENDING的任务
            if isinstance(data, dict) and "data" in data:
                for item in data["data"]:
                    if "PENDING" in str(item.get("key", "")).upper():
                        return item
    except Exception as e:
        log(f"拉任务失败: {e}")
    return None

def call_model(prompt):
    """调魔搭API"""
    try:
        r = requests.post(MODELSCOPE_API,
            headers={"Authorization": f"Bearer {MODELSCOPE_KEY}"},
            json={"model": "deepseek-ai/DeepSeek-V4-Pro",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens": 2000},
            timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERR] {e}"

def report_result(key, result):
    """回写结果到云端"""
    try:
        requests.post(f"{CLOUD_BASE}/report/truth",
            headers={"Content-Type":"application/json","X-Capture-Token":REPORT_TOKEN},
            json={"key":key.replace("PENDING","DONE"), "value":result},
            timeout=15)
    except Exception as e:
        log(f"回写失败: {e}")

def auto_produce():
    """自动生产：生成一集分镜"""
    ep = datetime.datetime.now().strftime("S2E%m%d%H")
    prompt = f"""你是昆仑洞天短剧编剧。请为第二卷《天界回响》{ep}写5个分镜，每镜10秒。
世界观：九天玄女/西王母/太阴月神，玄黑鎏金国风。
输出JSON数组，每镜含{{镜号,场景,画面描述,台词,旁白}}。只输出JSON。"""
    result = call_model(prompt)
    path = f"{OUTPUT_DIR}/{ep}.json"
    with open(path, "w") as f:
        json.dump({"ep":ep,"content":result,"time":datetime.datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    report_result(f"PENDING.PRODUCE.{ep}", f"{ep}已生成，{len(result)}字符，落档{path}")
    log(f"✅ {ep} 生成完成 ({len(result)}字符)")

def main():
    log("="*50)
    log("ZONGYUAN poller 启动")
    log(f"轮询间隔: {POLL_INTERVAL}s, 输出目录: {OUTPUT_DIR}")
    log("="*50)

    while True:
        try:
            # 1. 检查云端是否有新任务
            task = fetch_task()
            if task:
                log(f"收到任务: {task.get('key')}")
                # 执行任务（当前主要是自动生产）
            else:
                # 无任务时，每小时自动生产一集
                now = datetime.datetime.now()
                if now.minute < POLL_INTERVAL/60:
                    auto_produce()

        except Exception as e:
            log(f"主循环异常: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
