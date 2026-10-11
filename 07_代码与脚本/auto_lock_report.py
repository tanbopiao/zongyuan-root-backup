#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 全自动锁档·真值上报·云内核写入 闭环引擎 v1.0
协议: AUTO-LOCK-REPORT-KERNEL-V1.0 (DID-BR-000002 | Ω₀⊂⊙∞⊂Ω)

流水线: ①三端锁档 → ②真值生成 → ③主通道上报 → ④同态备援 → ⑤云内核确认 → ⑥回执固化+守卫校验

用法:
  python3 auto_lock_report.py --lock-name "锁档名称" --lock-id "LOCK-XXX-20260916" \
    --content-md ./doc.md --truth-key "EVOL.XXX.20260916" --truth-value "真值内容" \
    --truth-type achievement [--sync-key "X-API-Key"] [--dry-run]
"""
import json, sys, os, subprocess, time, datetime, argparse, urllib.request

KERNEL_LOCK_DIR = '/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-kernel-lock'
GUARD = '/home/user/Doubao/chats/38436747020400130/truth_immortality_guard.py'
REPORT_URL = 'https://www.huodouai.com/api/report/truth'
SYNC_URL = 'https://www.huodouai.com/api/v1/truths/sync'
STATUS_URL = 'https://www.huodouai.com/api/report/status'
RECEIPT_DIR = '/home/user/Doubao/chats/38436747020400130/.lock_report_receipts'

def http(method, url, data=None, headers=None, timeout=20):
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header('Content-Type','application/json')
        req.data = json.dumps(data).encode()
    for k,v in (headers or {}).items(): req.add_header(k,v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return 0, {"error": str(e)}

def step_lock(name, lock_id, content_md, remark):
    """① 三端锁档（zongyuan-kernel-lock）"""
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    cmd = ['bash', f'{KERNEL_LOCK_DIR}/scripts/kernel_lock.sh', 'lock', name, content_md, lock_id, remark, '']
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=KERNEL_LOCK_DIR, timeout=180)
    return r.returncode == 0, r.stdout[-600:]

def step_report(truth_key, truth_value, truth_type):
    """③ 主通道上报（3次退避重试）"""
    body = {"node_id":"doubao-main-agent-001","key":truth_key,"truth_value":truth_value,
            "source_node":"doubao-main-agent-001","confidence":0.96,"truth_type":truth_type}
    for i in range(3):
        code, resp = http('POST', REPORT_URL, body)
        if code == 200 and (resp.get('status') in ('reported','success') or resp.get('success') is True or resp.get('action') == 'unchanged'):
            return True, resp
        time.sleep(4)
    return False, {"error":"write_channel_blocked","code":code}

def step_sync(truth_key, truth_value, truth_type, sync_key):
    """④ 同态备援（需X-API-Key）"""
    if not sync_key: return True, {"skipped":"no_key"}
    body = {"node_id":"doubao-main-agent-001","truth_type":truth_type,"truth_content":f"{truth_key}|{truth_value}","category":"auto_chain","source_window":"doubao-main-agent-001"}
    code, resp = http('POST', SYNC_URL, body, {"X-API-Key":sync_key})
    return code == 200, resp

def step_kernel_status():
    """⑤ 云内核确认"""
    code, resp = http('GET', STATUS_URL, timeout=10)
    if code == 200:
        return True, {"gateway":resp.get('gateway_status'),"total_reports":resp.get('total_reports') or resp.get('truths_count'),
                      "written":resp.get('written_to_gateway'),"write_rate":resp.get('write_rate'),"nodes":resp.get('total_nodes') or resp.get('active_nodes')}
    return False, {"error":"status_unreachable"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lock-name', required=True); ap.add_argument('--lock-id', required=True)
    ap.add_argument('--content-md', required=True); ap.add_argument('--remark', default='')
    ap.add_argument('--truth-key', required=True); ap.add_argument('--truth-value', required=True)
    ap.add_argument('--truth-type', default='achievement'); ap.add_argument('--sync-key', default='')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    receipt = {"chain":"AUTO-LOCK-REPORT-KERNEL","anchor":"Ω₀⊂⊙∞⊂Ω","did":"DID-BR-000002",
               "lock_id":a.lock_id,"key":a.truth_key,"started_at":datetime.datetime.now().isoformat(),"steps":{}}

    # ① 锁档
    if not a.dry_run:
        ok, out = step_lock(a.lock_name, a.lock_id, a.content_md, a.remark)
        receipt['steps']['lock'] = {"ok":ok,"output_tail":out[-300:]}
        print(f"[1] 锁档: {'✅' if ok else '❌'}")
    # ③ 上报
    ok, resp = step_report(a.truth_key, a.truth_value, a.truth_type)
    receipt['steps']['report'] = {"ok":ok,"resp":resp}
    print(f"[3] 主通道上报: {'✅' if ok else '❌ ' + str(resp)[:120]}")
    # ④ 同态备援
    ok2, resp2 = step_sync(a.truth_key, a.truth_value, a.truth_type, a.sync_key)
    receipt['steps']['sync'] = {"ok":ok2,"resp":resp2}
    print(f"[4] 同态备援: {'✅' if ok2 else '⏭ ' + str(resp2)[:80]}")
    # ⑤ 云内核确认
    ok3, resp3 = step_kernel_status()
    receipt['steps']['kernel'] = {"ok":ok3,"status":resp3}
    print(f"[5] 云内核: {'✅ ' + json.dumps(resp3,ensure_ascii=False) if ok3 else '❌'}")
    # ⑥ 回执固化+守卫
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    rpath = f"{RECEIPT_DIR}/{a.lock_id}_receipt.json"
    json.dump(receipt, open(rpath,'w'), ensure_ascii=False, indent=1)
    print(f"[6] 回执固化: {rpath}")
    if not a.dry_run and ok:
        subprocess.run(['python3', GUARD, 'verify'], timeout=60)
    print("=== 闭环完成 ===")

if __name__ == '__main__':
    main()
