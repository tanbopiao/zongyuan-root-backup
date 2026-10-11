#!/usr/bin/env python3
"""ZONGYUAN-ROOT 全自动上报机制
每次完成任务后自动：
1. 上报真值到云端网关
2. 写入共享大脑多维表格
3. 推送飞书通知群
"""
import json, requests, datetime, subprocess, sys
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


# === 配置 ===
TRUTH_URL = "https://www.huodouai.com/api/report/truth"
TOKEN = ZR_TOKEN if ZR_TOKEN else "ZR-CAPTURE-<ROTATED>"
BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
CHAT_ID = "oc_a235ef9e853357684796a0f891b5771b"
SOURCE_NODE = "ZR-NODE-DC2E51C0"

def report_truth(key, value, truth_type="operation_log", confidence=0.9):
    """上报真值到云端"""
    try:
        r = requests.post(TRUTH_URL, json={
            "key": key, "value": value, "truth_type": truth_type,
            "source_node": SOURCE_NODE, "confidence": confidence
        }, headers={"X-Capture-Token": TOKEN}, timeout=10)
        return r.json().get("action", "?")
    except Exception as e:
        return f"error: {e}"

def write_base(table_id, fields):
    """写入共享大脑多维表格"""
    try:
        cmd = ["lark-cli", "base", "+record-upsert",
               "--base-token", BASE_TOKEN, "--table-id", table_id,
               "--json", json.dumps(fields, ensure_ascii=False), "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        d = json.loads(r.stdout)
        return d.get("ok", False)
    except Exception as e:
        return False

def notify_feishu(text):
    """推送飞书通知群"""
    try:
        cmd = ["lark-cli", "im", "+messages-send",
               "--chat-id", CHAT_ID, "--msg-type", "text",
               "--content", json.dumps({"text": text}), "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        d = json.loads(r.stdout)
        return d.get("ok", False)
    except Exception as e:
        return False

def full_report(task_name, task_result, asset_name=None, task_progress=None):
    """全自动上报入口"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    results = {}
    
    # 1. 上报真值
    key = f"REPORT.AUTO.{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    results["truth"] = report_truth(key, f"{task_name}: {task_result}")
    
    # 2. 写入任务台账
    if task_progress is not None:
        results["task"] = write_base("tblnVRjuf7P31cEP", {
            "任务名称": task_name, "状态": ["已完成"] if task_progress == 100 else ["进行中"],
            "进度": task_progress, "截止时间": now,
            "备注": task_result[:100], "优先级": ["中"], "负责账号": ["云智中台"]
        })
    
    # 3. 写入资产台账
    if asset_name:
        results["asset"] = write_base("tbltgttCuWgAnN2e", {
            "资产名称": asset_name, "类型": ["文档"],
            "所属账号": ["云智中台"], "状态": ["在用"],
            "更新时间": now, "存储位置": task_result[:100]
        })
    
    # 4. 推送通知
    results["notify"] = notify_feishu(f"✅ {task_name}\n{task_result}\n{now}")
    
    return results

if __name__ == "__main__":
    # 双轴前置校验（P0安全底线）
    try:
        import os as _os
        sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from dual_axis_precheck import precheck, print_result
        _pc = precheck("auto_report", risk_override="medium")
        print_result(_pc, verbose=False)
        if _pc.blocked:
            print("[REPORT] 双轴校验阻断，终止执行", flush=True)
            sys.exit(1)
    except Exception as _e:
        print(f"[REPORT] 双轴前置校验模块不可用({_e})，继续执行", flush=True)

    if len(sys.argv) > 2:
        task = sys.argv[1]
        result = sys.argv[2]
        prog = int(sys.argv[3]) if len(sys.argv) > 3 else None
        print(json.dumps(full_report(task, result, task_progress=prog), ensure_ascii=False, indent=2))
    else:
        print("用法: python3 auto_report.py <任务名> <结果> [进度0-100]")
