#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 批量生产流水线 V1.0（每天1次×5集+质检）
流程: 魔搭DeepSeek-V4-Pro生成5集分镜 → 确定性质检 → 落档 → 上报云端
"""
import json, os, re, datetime, requests, time

MODELSCOPE_API = "https://api-inference.modelscope.cn/v1/chat/completions"
MODELSCOPE_KEY = "ms-673547d6-508b-4242-a862-85de112a3ce7"
MODEL = "deepseek-ai/DeepSeek-V4-Pro"
ANCHOR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点"
EPISODES = 5

# 质检：现代/西方元素漂移黑名单
DRIFT_BLACKLIST = ["枪", "手枪", "ak", "汽车", "轿车", "手机", "屏幕", "西装",
                   "高楼", "公路", "广告牌", "电灯", "插座", "塑料", "牛仔裤",
                   "墨镜", "耳机", "键盘", "显示器", "音箱"]

def call_model(prompt, retries=2):
    for i in range(retries + 1):
        try:
            r = requests.post(MODELSCOPE_API,
                headers={"Authorization": f"Bearer {MODELSCOPE_KEY}", "Content-Type": "application/json"},
                json={"model": MODEL, "messages":[{"role":"user","content":prompt}], "max_tokens": 2500},
                timeout=90)
            d = r.json()
            return d["choices"][0]["message"]["content"]
        except Exception as e:
            if i < retries:
                time.sleep(3)
                continue
            return f"[ERR] {e}"
    return "[ERR] unknown"

def extract_json(text):
    """从模型输出提取JSON数组"""
    if text.startswith("[ERR]"):
        return None, text
    # 去掉```json围栏
    t = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.M)
    try:
        return json.loads(t), None
    except Exception:
        m = re.search(r"\[.*\]", t, re.S)
        if m:
            try:
                return json.loads(m.group(0)), None
            except Exception:
                return None, "JSON解析失败"
        return None, "JSON解析失败"

def quality_check(ep, shots, raw):
    """确定性质检，返回 (pass, issues)"""
    issues = []
    if shots is None:
        return False, [raw[:120]]
    if len(shots) != 5:
        issues.append(f"镜数={len(shots)}≠5")
    required = ["镜号", "场景", "画面描述", "台词", "旁白"]
    for i, s in enumerate(shots):
        if not isinstance(s, dict):
            issues.append(f"镜{i+1}非对象")
            continue
        for k in required:
            if k not in s or not str(s.get(k, "")).strip():
                issues.append(f"镜{i+1}缺字段[{k}]")
        desc = str(s.get("画面描述", ""))
        if len(desc) < 40:
            issues.append(f"镜{i+1}画面描述过短({len(desc)}字)")
        for w in DRIFT_BLACKLIST:
            if w in desc or w in str(s.get("台词", "")):
                issues.append(f"镜{i+1}疑似漂移词[{w}]")
    return len(issues) == 0, issues

def report_cloud(key, value):
    try:
        requests.post("https://www.huodouai.com/api/report/truth",
            headers={"Content-Type":"application/json","X-Capture-Token":"ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"},
            json={"key":key,"value":value}, timeout=15)
    except Exception:
        pass

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    log_lines = [f"[{ts}] 批量生产流水线启动：{EPISODES}集"]
    results = []

    for ep in range(1, EPISODES + 1):
        prompt = f"""你是昆仑洞天短剧编剧。请为第二卷《天界回响》第{ep}集写5个分镜，每镜10秒。
世界观：九天玄女/西王母/太阴月神，玄黑鎏金国风，UE5.7光追，伦勃朗光影，Portra400胶片质感。
故事线：天界回响波及三界，玄女循因果线索追查，神与人命运交织。
硬约束：禁止任何现代/西方元素（枪械/汽车/手机/西装/高楼/公路等）；神女形象不露腹肌，服饰端庄。
输出严格JSON数组，每镜含{{镜号,场景,画面描述,台词,旁白}}，共5镜。只输出JSON，无其他文字。"""
        raw = call_model(prompt)
        shots, err = extract_json(raw)
        passed, issues = quality_check(ep, shots, raw if err else "")
        status = "PASS" if passed else "FAIL"
        log_lines.append(f"[{ts}] 第{ep}集: {status}" + (f" issues={issues[:3]}" if issues else ""))
        print(f"[{ts}] 第{ep}集: {status}", flush=True)

        # 落档
        out = {"episode": f"S2E{ep:02d}", "time": ts, "model": MODEL,
               "quality": status, "issues": issues, "content": shots if shots else raw}
        path = f"{ANCHOR}/PIPELINE-BATCH-{ts}-E{ep}.json"
        with open(path, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        results.append({"episode": f"S2E{ep:02d}", "status": status, "path": path})

    # 汇总
    pass_n = sum(1 for r in results if r["status"] == "PASS")
    summary = {"batch": ts, "total": EPISODES, "pass": pass_n, "fail": EPISODES - pass_n, "details": results}
    with open(f"{ANCHOR}/PIPELINE-BATCH-{ts}-SUMMARY.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    verdict = "全部达标" if pass_n == EPISODES else f"{EPISODES-pass_n}集未达标"
    report_cloud(f"PIPELINE.BATCH.{ts}", f"批量生产{EPISODES}集分镜：PASS {pass_n}/FAIL {EPISODES-pass_n}，{verdict}，质检含镜数/字段/长度/漂移词检查，明细已落档。确权Ω₀⊂⊙∞⊂Ω|DID-BR-000002")
    log_lines.append(f"[{ts}] 汇总: PASS {pass_n}/{EPISODES}, {verdict}")
    print(f"[{ts}] 汇总: PASS {pass_n}/{EPISODES}, {verdict}", flush=True)
    with open(f"{ANCHOR}/PIPELINE-BATCH-LOG-{ts}.txt", "w") as f:
        f.write("\n".join(log_lines))

if __name__ == "__main__":
    main()
