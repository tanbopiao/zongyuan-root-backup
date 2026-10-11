# E1-DECISION-REPORT｜决策日志上报网关脚本 v1.0

"""E1 记忆连续性增强：决策日志上报记忆网关
将本地决策日志（decision_log.json）增量同步到云端记忆网关，
truth_type=decision，确保跨实例决策可追溯。
"""
import json, os, sys, datetime, urllib.request

DECISION_LOG = '/home/user/ZONGYUAN-ROOT/07_代码与脚本/evolution/decision_log.json'
SYNC_MARK = '/home/user/ZONGYUAN-ROOT/07_代码_与脚本/evolution/.decision_sync_mark'
# 修正路径
SYNC_MARK = '/home/user/ZONGYUAN-ROOT/07_代码与脚本/evolution/.decision_sync_mark'
GATEWAY = 'https://www.huodouai.com/api/report/truth'
BACKUP = 'https://drama.huodouai.com/api/report/truth'
NODE = 'ZR-NODE-DC2E51C0'


def main():
    if not os.path.exists(DECISION_LOG):
        print('❌ 决策日志不存在')
        return 1
    with open(DECISION_LOG) as f:
        entries = json.load(f)

    last_sync = 0
    if os.path.exists(SYNC_MARK):
        with open(SYNC_MARK) as f:
            last_sync = int(f.read().strip() or '0')

    new_entries = entries[last_sync:] if last_sync <= len(entries) else entries
    if not new_entries:
        print('✅ 无新决策需上报')
        return 0

    ok_count = 0
    for i, e in enumerate(new_entries):
        key = f"decision.{datetime.datetime.now().strftime('%Y%m%d')}.{last_sync + i + 1}"
        payload = {
            'truth_key': key,
            'truth_value': f"决策[{e.get('item','?')}] 状态[{e.get('status')}] 锁档[{e.get('lock_id','-')}] 理由[{e.get('note','-')}]",
            'source_node': NODE,
            'confidence': 1.0,
            'truth_type': 'decision',
        }
        body = json.dumps(payload).encode()
        req = urllib.request.Request(GATEWAY, data=body, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                r = json.loads(resp.read().decode())
            if r.get('success'):
                ok_count += 1
        except Exception:
            # 主站失败降级备用
            try:
                req2 = urllib.request.Request(BACKUP, data=body, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req2, timeout=10) as resp:
                    r = json.loads(resp.read().decode())
                if r.get('success'):
                    ok_count += 1
            except Exception as ex:
                print(f'  ⚠️ 上报失败: {e.get("item","?")[:30]} ({ex})')

    with open(SYNC_MARK, 'w') as f:
        f.write(str(len(entries)))
    print(f'✅ 决策日志上报完成: {ok_count}/{len(new_entries)} 条 → 记忆网关(truth_type=decision)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
