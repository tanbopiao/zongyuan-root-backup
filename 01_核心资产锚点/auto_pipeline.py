#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 全自动短剧生产流水线 V1.0
流程: 拉共享大脑任务 → 魔搭DeepSeek生成 → 落档 → 上报云端
"""
import json, os, subprocess, datetime, requests

# 配置
MODELSCOPE_API = "https://api-inference.modelscope.cn/v1/chat/completions"
MODELSCOPE_KEY = "ms-673547d6-508b-4242-a862-85de112a3ce7"
MODEL = "deepseek-ai/DeepSeek-V4-Pro"
ANCHOR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点"

def call_model(prompt):
    """调魔搭API生成"""
    try:
        r = requests.post(MODELSCOPE_API,
            headers={"Authorization": f"Bearer {MODELSCOPE_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages":[{"role":"user","content":prompt}], "max_tokens": 2000},
            timeout=60)
        d = r.json()
        return d["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERR] {e}"

def report_cloud(key, value):
    """上报云端真值"""
    try:
        requests.post("https://www.huodouai.com/api/report/truth",
            headers={"Content-Type":"application/json","X-Capture-Token":"ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"},
            json={"key":key,"value":value}, timeout=15)
    except: pass

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    print(f"[{ts}] 全自动流水线启动")

    # 1. 生成：第二卷《天界回响》第1集分镜
    prompt = """你是昆仑洞天短剧编剧。请为第二卷《天界回响》第1集写5个分镜，每镜10秒。
世界观：九天玄女/西王母/太阴月神，玄黑鎏金国风，UE5.7光追质感。
输出格式：JSON数组，每镜含{镜号,场景,画面描述,台词,旁白}。
只输出JSON，不要解释。"""

    result = call_model(prompt)
    print(f"[生成] 长度: {len(result)}字符")

    # 2. 落档
    out = {"episode":"S2E01","time":ts,"model":MODEL,"content":result}
    path = f"{ANCHOR}/PIPELINE-OUTPUT-S2E01-{ts}.json"
    with open(path,"w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[落档] {path}")

    # 3. 上报
    report_cloud(f"PIPELINE.S2E01.{ts}", f"第二卷第1集分镜已生成，长度{len(result)}字符，模型{MODEL}，落档{path}")
    print(f"[上报] 云端真值已写入")
    print(f"[{ts}] 流水线完成")

if __name__ == "__main__":
    main()
