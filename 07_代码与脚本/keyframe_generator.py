#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 短剧关键帧生成器 V1.0
DID: DID-BR-000002 | 节点: ZR-NODE-DC2E51C0 | 锚: Ω₀⊂⊙∞⊂Ω

功能: 读取分镜JSON(PIPELINE-OUTPUT-*.json) → 为每镜构建文生图Prompt →
      提交魔搭Qwen/Qwen-Image文生图任务 → 记录task_id → 落档 → 上报云端

图片取回策略(配置化):
  - 当前: 魔搭异步任务HTTP查询端点(/v1/tasks/{id})暂不可用, 记录task_id
          + 提示魔搭控制台取回; 端点打通后自动升级为轮询取图
  - 预留: RESULT_POLL_ENDPOINTS 列表, 端点可用时自动启用

最小额度消耗: 每镜1次文生图调用(免费额度2000次/天), 失败快速跳过不重试
"""
import json
import os
import datetime
import requests

# ===== 配置 =====
MODELSCOPE_API = "https://api-inference.modelscope.cn/v1/images/generations"
MODELSCOPE_KEY = "ms-673547d6-508b-4242-a862-85de112a3ce7"
MODEL = "Qwen/Qwen-Image"
ANCHOR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点"
IMG_DIR = "/home/user/ZONGYUAN-ROOT/02_数字媒体资产/图片"
CLOUD_REPORT = "https://www.huodouai.com/api/report/truth"
CLOUD_BACKUP = "https://drama.huodouai.com/api/report/truth"
REPORT_TOKEN = "ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"
# 结果取回(2026-10-01打通): GET /v1/tasks/{tid} + X-ModelScope-Task-Type: image_generation
TASK_QUERY_API = "https://api-inference.modelscope.cn/v1/tasks/{tid}"
TASK_TYPE_HEADER = "image_generation"
RETRIEVE_AUTO = True  # 全自动取图开关

# 昆仑洞天天元法则强制前置约束(2026-10-01注入, KUNLUN-TIANYUAN-LAW-V1.2/兼容V1.1自检12项)
TIANYUAN_PREFIX = ("【昆仑洞天天元法则L0-002强制前置约束生效】零雄性漂移·东方神女绝对铁律；"
                    "神性与骨相解耦；禁男性骨骼/宽肩/方下颌/魁梧/厚背宽腰/肌肉块；"
                    "力量由气场/法阵/神纹/灵体/眼神承载；收敛度≥95%；"
                    "纯东方上古神女范式；长兵器结构连续完整禁断裂，矛尖与头部保留安全空域；"
                    "UE5.7全局光追,伦勃朗光影,黑金鎏金国风,电影级构图,高细节,"
                    "无现代元素,无西式盔甲,无水印,无白发彩发,无幼态娇媚,")
# 兼容旧版本风格前缀(无天元法则时使用)
STYLE_PREFIX = TIANYUAN_PREFIX

def ts_now():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M")

def load_shots(pipeline_file):
    """从分镜JSON提取画面描述列表"""
    with open(pipeline_file, encoding="utf-8") as f:
        d = json.load(f)
    content = d.get("content", "")
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    shots = json.loads(content)
    return shots, d.get("episode", "S2E01"), d.get("time", ts_now())

def submit_image_task(prompt):
    """提交魔搭文生图任务, 返回task_id或None"""
    try:
        r = requests.post(
            MODELSCOPE_API,
            headers={"Authorization": f"Bearer {MODELSCOPE_KEY}",
                     "Content-Type": "application/json",
                     "X-ModelScope-Async-Mode": "true"},
            json={"model": MODEL, "prompt": prompt, "n": 1, "size": "1024x1024"},
            timeout=120,
        )
        d = r.json()
        if d.get("task_status") == "SUCCEED" and d.get("task_id"):
            return d["task_id"]
        return None
    except Exception as e:
        print(f"  [ERR] 提交失败: {str(e)[:120]}")
        return None

def fetch_image(tid, wait_loop=3, interval=15):
    """轮询取回图片URL(全自动): GET /v1/tasks/{tid} + X-ModelScope-Task-Type"""
    import time
    for i in range(wait_loop):
        try:
            r = requests.get(TASK_QUERY_API.format(tid=tid),
                headers={"Authorization": f"Bearer {MODELSCOPE_KEY}",
                         "X-ModelScope-Task-Type": TASK_TYPE_HEADER}, timeout=20)
            d = r.json()
            st = d.get("task_status")
            imgs = d.get("output_images", [])
            if st == "SUCCEED" and imgs:
                return imgs[0]
            if st == "FAILED":
                return None
        except Exception as e:
            print(f"  [ERR] 查询异常: {str(e)[:100]}")
        time.sleep(interval)
    return None

def report_cloud(key, value):
    """上报云端真值(主备双通道)"""
    for url in (CLOUD_REPORT, CLOUD_BACKUP):
        try:
            requests.post(url,
                headers={"Content-Type": "application/json",
                         "X-Capture-Token": REPORT_TOKEN},
                json={"key": key, "value": value}, timeout=12)
        except Exception:
            pass

def main(pipeline_file=None):
    ts = ts_now()
    os.makedirs(IMG_DIR, exist_ok=True)

    # 1. 输入分镜文件
    if not pipeline_file:
        candidates = sorted(
            [f for f in os.listdir(ANCHOR) if f.startswith("PIPELINE-OUTPUT-S2E01")],
            reverse=True)
        if not candidates:
            print("❌ 未找到分镜文件")
            return
        pipeline_file = os.path.join(ANCHOR, candidates[0])

    shots, episode, ptime = load_shots(pipeline_file)
    print(f"===== 关键帧生成器启动 | {episode} | {ptime} | 分镜数:{len(shots)} =====")

    # 2. 逐镜构建prompt并提交文生图
    keyframes = []
    for idx, shot in enumerate(shots, 1):
        scene = shot.get("场景", f"镜{idx}")
        desc = shot.get("画面描述", "")
        prompt = STYLE_PREFIX + desc
        print(f"[镜{idx}] {scene} ... 提交文生图")
        tid = submit_image_task(prompt)
        if tid and RETRIEVE_AUTO:
            # 全自动取图: 轮询任务结果并下载落盘
            img_url = fetch_image(tid)
            if img_url:
                fname = f"{episode}-镜{idx:02d}-{scene}.png"
                fpath = os.path.join(IMG_DIR, fname)
                img_data = requests.get(img_url, timeout=60).content
                with open(fpath, "wb") as f:
                    f.write(img_data)
                keyframes.append({
                    "镜号": idx, "场景": scene, "prompt": prompt,
                    "task_id": tid, "status": "DOWNLOADED",
                    "file": fpath, "size_bytes": len(img_data), "url": img_url,
                })
                print(f"  -> DOWNLOADED {len(img_data)}字节 -> {fname}")
            else:
                keyframes.append({
                    "镜号": idx, "场景": scene, "prompt": prompt,
                    "task_id": tid, "status": "SUBMITTED-NO-IMG",
                })
                print(f"  -> 提交成功但未取到图(任务可能RUNNING, 可稍后查询task_id)")
        else:
            status = "SUBMITTED" if tid else "FAILED"
            keyframes.append({
                "镜号": idx, "场景": scene, "prompt": prompt,
                "task_id": tid, "status": status,
                "retrieve": "modelscope-console-or-poll-endpoint" if tid else "n/a",
            })
            print(f"  -> {status} {tid or ''}")

    # 3. 落档(任务清单)
    out = {
        "episode": episode,
        "gen_time": ts,
        "model": MODEL,
        "engine": "MODELSCOPE-TEXT-TO-IMAGE",
        "source_pipeline": pipeline_file,
        "style": STYLE_PREFIX,
        "keyframe_tasks": keyframes,
        "retrieve_note": ("全自动取图闭环: GET /v1/tasks/{task_id} + "
                          "X-ModelScope-Task-Type: image_generation (2026-10-01打通)"),
    }
    out_path = os.path.join(IMG_DIR, f"KEYFRAME-TASKS-{episode}-{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"✅ 落档: {out_path}")

    # 4. 上报云端
    submitted = sum(1 for k in keyframes if k["status"] == "SUBMITTED")
    report_cloud(f"KEYFRAME.{episode}.{ts}", {
        "episode": episode, "total": len(keyframes), "submitted": submitted,
        "model": MODEL, "out": out_path, "anchor": "Ω₀⊂⊙∞⊂Ω", "did": "DID-BR-000002"
    })
    print(f"✅ 上报云端: KEYFRAME.{episode}.{ts} | 提交{submitted}/{len(keyframes)}")

    print(f"===== 关键帧生成完成 | 用时批次 {ts} =====")

if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
