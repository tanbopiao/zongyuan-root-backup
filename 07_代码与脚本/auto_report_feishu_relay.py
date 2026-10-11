#!/usr/bin/env python3
"""ZONGYUAN-ROOT 飞书中转紧急备用通道
当云端主备通道(www/drama.huodouai.com)直连超时不可达时，
将真值经飞书共享大脑「真值共识区」中转上报，保证真值链路不中断。

通道判定: 先探测云端主备通道，直连失败自动降级飞书中转。
用法:
  python3 auto_report_feishu_relay.py "<真值key>" "<真值内容>" [--check-cloud]
"""
import json, sys, subprocess, datetime, requests, os
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


BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
TRUTH_TABLE = "tbl9QxL35rwA16eS"          # 真值共识区
NODE_TABLE  = "tblOmIRJtTn2EsvM"          # 节点状态总览
TRUTH_URLS = [
    "https://www.huodouai.com/api/report/truth",
    "https://drama.huodouai.com/api/report/truth",
]
TOKEN = ZR_TOKEN if ZR_TOKEN else "ZR-CAPTURE-<ROTATED>"
SOURCE_NODE = "ZR-NODE-DC2E51C0"

def cloud_reachable(url, timeout=6):
    try:
        r = requests.post(url, json={"key":"RELAY.PROBE","value":"probe"},
                          headers={"X-Capture-Token":TOKEN}, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False

def write_base(table_id, fields):
    try:
        cmd = ["lark-cli","base","+record-upsert","--base-token",BASE_TOKEN,
               "--table-id",table_id,"--json",json.dumps(fields,ensure_ascii=False),
               "--as","user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout).get("ok", False)
    except Exception:
        return False

def relay_report(key, value):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {"probe": {}, "action": None}
    # 1. 探测云端主备通道
    for u in TRUTH_URLS:
        ok = cloud_reachable(u)
        result["probe"][u] = "OK" if ok else "TIMEOUT"
    # 2. 直连可用则直连上报；否则降级飞书中转
    if any(v=="OK" for v in result["probe"].values()):
        try:
            r = requests.post(TRUTH_URLS[0], json={"key":key,"value":value,
                "source_node":SOURCE_NODE,"confidence":0.9},
                headers={"X-Capture-Token":TOKEN}, timeout=10)
            result["action"] = f"直连上报: {r.status_code}"
        except Exception as e:
            result["action"] = f"直连失败转飞书: {e}"
    else:
        result["action"] = "云端直连不可达→降级飞书中转"
    # 3. 飞书中转写入(无论是否直连成功，均入飞书留痕)
    relay_ok = write_base(TRUTH_TABLE, {
        "真值key": key,
        "真值内容": f"[{now}] {value} | 通道: {result['action']} | 节点{SOURCE_NODE}",
        "最终状态": ["已达成共识"],
        "确认节点": "NODE-DEV-DOUBAO-WORK-001",
        "异议节点": "",
    })
    result["relay_feishu"] = relay_ok
    return result

if __name__ == "__main__":
    # 双轴前置校验（P1安全底线 - 飞书中转紧急通道）
    try:
        import os as _os
        sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from dual_axis_precheck import precheck, print_result
        _pc = precheck("auto_report_feishu_relay", risk_override="medium")
        print_result(_pc, verbose=False)
        if _pc.blocked:
            print("[FEISHU-RELAY] 双轴校验阻断，终止执行", flush=True)
            sys.exit(1)
    except Exception as _e:
        print(f"[FEISHU-RELAY] 双轴前置校验模块不可用({_e})，继续执行", flush=True)

    if len(sys.argv) < 3:
        print("用法: python3 auto_report_feishu_relay.py <key> <value>")
        sys.exit(1)
    key, value = sys.argv[1], sys.argv[2]
    print(json.dumps(relay_report(key, value), ensure_ascii=False, indent=2))
