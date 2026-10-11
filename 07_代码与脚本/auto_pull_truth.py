#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 云端真值增量拉取脚本
====================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | NODE-DEV-DOUBAO-WORK-001
用途: 从云端记忆网关拉取新增真值, 增量完善本地持久层根目录自治内核
协议: X-Capture-Token + X-DID 双鉴权
原则: 增量优先、失败快速跳过不重试、空闲跳过、最小额度消耗
"""
import json, os, sys, time, urllib.request, urllib.error, datetime

# ============ 配置 ============
CRED_PATH = "/home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env"
PULL_ENDPOINT_PRIMARY = "https://www.huodouai.com/api/truth"
PULL_ENDPOINT_BACKUP = "https://drama.huodouai.com/api/truth"
LOCAL_PULL_DIR = "/home/user/ZONGYUAN-ROOT/06_云端中枢同步/cloud_truths_pull"
STATE_FILE = os.path.join(LOCAL_PULL_DIR, "pull_state.json")
MAX_PULL_PER_RUN = 200  # 单次最多拉取条数, 防止额度超限
DID = "DID-BR-000002"

def load_token():
    for line in open(CRED_PATH):
        if line.strip().startswith("ZR_TOKEN="):
            return line.split("=",1)[1].strip().strip('"')
    return ""

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"last_pull_ts": 0, "last_seq": 0, "total_pulled": 0, "last_success": None}

def save_state(state):
    os.makedirs(LOCAL_PULL_DIR, exist_ok=True)
    json.dump(state, open(STATE_FILE,"w"), ensure_ascii=False, indent=2)

def pull_truths(endpoint, token, since_seq=0, limit=MAX_PULL_PER_RUN):
    """从云端拉取真值列表, 返回 (success, truths_list)"""
    url = f"{endpoint}?limit={limit}"
    if since_seq > 0:
        url += f"&since={since_seq}"
    headers = {"X-Capture-Token": token, "X-DID": DID, "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        # 兼容多种返回结构
        truths = data.get("truths") or data.get("data") or data.get("items") or data.get("results") or []
        if isinstance(data, list):
            truths = data
        return True, truths
    except Exception as e:
        return False, f"ERR:{type(e).__name__}:{e}"

def main():
    # 双轴前置校验（P0安全底线）
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from dual_axis_precheck import precheck, print_result
        pc = precheck("auto_pull_truth", risk_override="medium")
        print_result(pc, verbose=False)
        if pc.blocked:
            print("[PULL] 双轴校验阻断，终止执行", flush=True)
            return
    except Exception as _e:
        print(f"[PULL] 双轴前置校验模块不可用({_e})，继续执行", flush=True)

    os.makedirs(LOCAL_PULL_DIR, exist_ok=True)
    token = load_token()
    if not token:
        print("[PULL] 未找到云端凭证, 跳过", flush=True)
        return

    state = load_state()
    since_seq = state.get("last_seq", 0)
    print(f"[PULL] 起始seq={since_seq}, 历史已拉取={state.get('total_pulled',0)}", flush=True)

    # 主通道拉取, 失败降级备用
    success, truths = pull_truths(PULL_ENDPOINT_PRIMARY, token, since_seq)
    channel = "www"
    if not success:
        print(f"[PULL] 主通道失败({truths}), 降级备用通道", flush=True)
        success, truths = pull_truths(PULL_ENDPOINT_BACKUP, token, since_seq)
        channel = "drama"

    if not success:
        print(f"[PULL] 双通道均失败: {truths}, 快速跳过不重试", flush=True)
        return

    if not truths or len(truths) == 0:
        print("[PULL] 云端无新增真值, 空闲跳过", flush=True)
        state["last_success"] = datetime.datetime.now().isoformat()
        save_state(state)
        return

    # 增量写入本地持久层
    new_count = 0
    max_seq = since_seq
    today = datetime.datetime.now().strftime("%Y%m%d")
    batch_file = os.path.join(LOCAL_PULL_DIR, f"truths_batch_{today}.json")

    # 读取已有批次
    existing = []
    if os.path.exists(batch_file):
        try:
            existing = json.load(open(batch_file))
        except Exception:
            existing = []
    existing_keys = {t.get("key") or t.get("truth_id") or json.dumps(t,sort_keys=True)[:64] for t in existing}

    for t in truths:
        key = t.get("key") or t.get("truth_id") or json.dumps(t,sort_keys=True)[:64]
        seq = t.get("seq") or t.get("id") or 0
        if isinstance(seq, str):
            try: seq = int(seq)
            except: seq = 0
        if key in existing_keys:
            continue
        # 补充拉取元数据
        t["_pulled_from"] = channel
        t["_pulled_at"] = datetime.datetime.now().isoformat()
        existing.append(t)
        existing_keys.add(key)
        new_count += 1
        if seq > max_seq:
            max_seq = seq

    # 写入批次文件
    json.dump(existing, open(batch_file,"w"), ensure_ascii=False, indent=2)

    # 更新状态
    state["last_seq"] = max_seq
    state["total_pulled"] = state.get("total_pulled", 0) + new_count
    state["last_success"] = datetime.datetime.now().isoformat()
    state["last_channel"] = channel
    save_state(state)

    print(f"[PULL] 完成: 通道={channel}, 新增={new_count}, 批次累计={len(existing)}, 最大seq={max_seq}", flush=True)
    print(f"[PULL] 批次文件: {batch_file}", flush=True)

if __name__ == "__main__":
    main()
