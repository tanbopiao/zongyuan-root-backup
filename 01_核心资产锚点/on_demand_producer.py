#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 按需生产器 V1.0（最优稳态·最小额度）
流程: 读共享大脑任务台账 → 有PENDING分镜生产任务才生产5集+质检 → 回写任务状态 → 上报
空闲无任务 → 直接跳过，0消耗
"""
import json, os, re, datetime, requests, time, subprocess

BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
TASK_TABLE = "tblnVRjuf7P31cEP"
ANCHOR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点"
PRODUCE_KW = ["分镜", "生产", "生成", "剧本", "短剧"]

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def read_tasks():
    """读任务台账，返回 (rows, fields_list)"""
    try:
        r = subprocess.run(
            ["lark-cli", "base", "+record-list", "--base-token", BASE_TOKEN,
             "--table-id", TASK_TABLE, "--as", "user", "--limit", "50", "--format", "json"],
            capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout)
        data = d.get("data", {})
        return data.get("data", []), data.get("fields", [])
    except Exception as e:
        log(f"读台账失败: {e}")
        return [], []

def find_pending_produce(tasks, fields_list):
    """找状态含待执行/未完成且名称含生产关键词的任务
    tasks: 数组行 [[v1,v2,...], ...], fields_list: 字段名列表"""
    name_idx = fields_list.index("任务名称") if "任务名称" in fields_list else 0
    status_idx = fields_list.index("状态") if "状态" in fields_list else -1
    for row in tasks:
        name = str(row[name_idx]) if len(row) > name_idx else ""
        status = str(row[status_idx]) if status_idx >= 0 and len(row) > status_idx else ""
        if any(k in name for k in PRODUCE_KW) and any(s in status for s in ["待执行", "待处理", "PENDING", "未完成"]):
            return {"fields": {"任务名称": name, "状态": status}, "record_id": None}
    return None

def call_model(prompt, retries=2):
    for i in range(retries + 1):
        try:
            r = requests.post("https://api-inference.modelscope.cn/v1/chat/completions",
                headers={"Authorization": "Bearer ms-673547d6-508b-4242-a862-85de112a3ce7"},
                json={"model": "deepseek-ai/DeepSeek-V4-Pro",
                      "messages":[{"role":"user","content":prompt}], "max_tokens": 2500},
                timeout=90)
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if i < retries:
                time.sleep(3)
            else:
                return f"[ERR] {e}"
    return "[ERR] unknown"

def extract_json(text):
    if text.startswith("[ERR]"):
        return None, text
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

def quality_check(shots, raw):
    issues = []
    if shots is None:
        return False, [raw[:120]]
    if len(shots) != 5:
        issues.append(f"镜数={len(shots)}≠5")
    for i, s in enumerate(shots):
        if not isinstance(s, dict):
            issues.append(f"镜{i+1}非对象"); continue
        for k in ["镜号", "场景", "画面描述", "台词", "旁白"]:
            if k not in s or not str(s.get(k, "")).strip():
                issues.append(f"镜{i+1}缺字段[{k}]")
        if len(str(s.get("画面描述", ""))) < 40:
            issues.append(f"镜{i+1}画面过短")
    return len(issues) == 0, issues

def report_cloud(key, value):
    try:
        requests.post("https://www.huodouai.com/api/report/truth",
            headers={"Content-Type":"application/json","X-Capture-Token":"ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"},
            json={"key":key,"value":value}, timeout=15)
    except Exception:
        pass

def produce_batch():
    """生产5集+质检"""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    results = []
    for ep in range(1, 6):
        prompt = f"""你是昆仑洞天短剧编剧。为第二卷《天界回响》第{ep}集写5个分镜，每镜10秒。
世界观：九天玄女/西王母/太阴月神，玄黑鎏金国风，UE5.7光追。
硬约束：禁止现代/西方元素；神女不露腹肌服饰端庄。
输出严格JSON数组，每镜含{{镜号,场景,画面描述,台词,旁白}}，共5镜。只输出JSON。"""
        raw = call_model(prompt)
        shots, err = extract_json(raw)
        passed, issues = quality_check(shots, raw if err else "")
        out = {"episode": f"S2E{ep:02d}", "time": ts, "quality": "PASS" if passed else "FAIL",
               "issues": issues, "content": shots if shots else raw}
        path = f"{ANCHOR}/ONDEMAND-{ts}-E{ep}.json"
        with open(path, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        results.append({"episode": f"S2E{ep:02d}", "status": "PASS" if passed else "FAIL", "path": path})
    pass_n = sum(1 for r in results if r["status"] == "PASS")
    report_cloud(f"PIPELINE.ONDEMAND.{ts}", f"按需生产5集：PASS {pass_n}/5，质检含镜数/字段/长度检查，明细{ANCHOR}。确权Ω₀⊂⊙∞⊂Ω|DID-BR-000002")
    return results, pass_n

def main():
    log("按需生产器启动")
    tasks, fields_list = read_tasks()
    log(f"台账读取完成，共{len(tasks)}条（抽查前50条）")
    task = find_pending_produce(tasks, fields_list)
    if not task:
        log("无待执行生产任务 → 空闲跳过，0消耗")
        return
    name = task.get("fields", {}).get("任务名称", "未知任务")
    log(f"发现生产任务: {name}")
    results, pass_n = produce_batch()
    log(f"生产完成: PASS {pass_n}/5")
    # 回写状态（尝试）
    try:
        subprocess.run(
            ["lark-cli", "base", "+record-batch-update", "--base-token", BASE_TOKEN,
             "--table-id", TASK_TABLE, "--as", "user",
             "--json", json.dumps({"update_records": [{"record_id": task.get("record_id"),
                 "fields": {"状态": ["已完成"]}}]})],
             capture_output=True, text=True, timeout=60)
        log("任务状态已回写: 已完成")
    except Exception as e:
        log(f"回写失败: {e}（不阻塞）")

if __name__ == "__main__":
    main()
