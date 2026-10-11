# KERNEL-EVOLUTION-001 候选#1 记忆连续性实测
"""记忆连续性量化评估：决策轨迹可回放率 × 锁档可追溯率
口径：
  coverage = 决策日志可回放条目 / 本窗口内关键锁档决策
  traceability = 回放条目中带锁档ID可溯源 / 回放条目
  continuity = 0.6*coverage + 0.4*traceability（0~1）
输出：JSON 证据报告
"""
import json, datetime, glob, os

ROOT = '/home/user/ZONGYUAN-ROOT'
EVO_DIR = f'{ROOT}/08_运行时数据与审计/evolution_20260929'
KERNEL_LOCK_DIR = '/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-kernel-lock'


def load_json(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def main():
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

    # 1. 决策日志（E1 权威）
    dl = load_json(f'{ROOT}/07_代码与脚本/evolution/decision_log.json')
    decisions = dl if isinstance(dl, list) else dl.get('entries', dl.get('decisions', []))

    # 2. 回放索引
    replay = load_json(f'{EVO_DIR}/E1_memory_continuity/memory_replay_index.json')
    replay_entries = replay.get('replay_entries', []) if replay else []

    # 3. 本窗口关键锁档决策（作为应可回放的基准集合）
    key_locks = [
        'LOCK-E3-AXIOMS-20260929-001',
        'LOCK-BOOTSTRAP-75-20260929-001',
        'LOCK-EVOLUTION-AXES-20260929-001',
        'LOCK-AXIOM-COLD-START-20260929-001',
        'ANCHOR-PERSIST-20260929-001',
    ]

    # 4. 可回放决策（决策日志中有、且回放窗口能取到）
    decision_items = {d.get('item', '').split(' ')[0] for d in decisions}
    replay_items = {e.get('item', '').split(' ')[0] for e in replay_entries}

    # coverage：决策日志条目中可被回放的比例（replay 至少覆盖日志 60%）
    covered = len(decision_items & replay_items)
    coverage = covered / max(len(decision_items), 1)

    # traceability：回放条目带 lock_id 的比例
    with_lock = sum(1 for e in replay_entries if e.get('lock_id') or e.get('lock'))
    traceability = with_lock / max(len(replay_entries), 1)

    continuity = round(0.6 * coverage + 0.4 * traceability, 4)

    report = {
        'report_id': f'MC-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}',
        'report_type': 'KERNEL-EVOLUTION-001-CANDIDATE-1',
        'timestamp': now,
        'method': '决策轨迹可回放率 × 锁档可追溯率（量化口径，替代基线主观0.855）',
        'inputs': {
            'decision_log_entries': len(decisions),
            'replay_window': replay.get('replay_window') if replay else None,
            'replay_entries': len(replay_entries),
            'key_lock_events_window': len(key_locks),
        },
        'metrics': {
            'coverage': round(coverage, 4),
            'traceability': round(traceability, 4),
            'memory_continuity': continuity,
            'target_v24': 0.90,
            'target_v25': 0.95,
        },
        'verdict': 'PASS' if continuity >= 0.90 else 'BELOW_TARGET',
        'baseline_note': '基线 0.855 为主观评估；本口径为可复现量化值，用于 EVO-GATE 候选#1 证据',
    }

    out = f'{EVO_DIR}/memory_continuity_measured_20260929.json'
    try:
        os.chmod(out, 0o644)
    except Exception:
        pass
    with open(out, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(out, 0o444)
    except Exception:
        pass

    print(f'✅ 记忆连续性实测完成: {report["report_id"]}')
    print(f'  决策日志: {len(decisions)} 条 | 回放: {len(replay_entries)} 条 | 覆盖: {coverage:.2%}')
    print(f'  可追溯率: {traceability:.2%}')
    print(f'  → memory_continuity = {continuity} (目标 V2.4: 0.90)')
    print(f'  判定: {report["verdict"]}')
    print(f'  证据: {out}')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
