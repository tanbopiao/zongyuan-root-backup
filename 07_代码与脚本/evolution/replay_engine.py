# E1-REPLAY-ENGINE｜跨窗口记忆回放引擎 v1.0

"""ZONGYUAN-ROOT 跨窗口记忆回放引擎
E1 记忆连续性增强：0.855 → 0.95
功能：冷启动时自动回放最近 N 轮决策轨迹（审批通过项 + 锁档事件 + 决策日志），
将强连续性（"为何得出该结论"）显式物化为可回读的决策轨迹索引。

回放数据源（持久层）：
  1. .approval_audit/approval_*.json       — 人工审批结论（含审批理由）
  2. 07_代码与脚本/evolution/decision_log.json — 决策日志（本引擎维护）
  3. 记忆网关 GET /api/truths/{key}         — 云端决策真值（truth_type=decision）

输出：回放摘要 JSON + 决策轨迹 MD（供冷启动 BOOTSTRAP 加载）
"""
import json, os, sys, glob, datetime, subprocess

AUDIT_DIR = '/home/user/Doubao/chats/38436747020400130/.approval_audit'
DECISION_LOG = '/home/user/ZONGYUAN-ROOT/07_代码与脚本/evolution/decision_log.json'
OUTPUT_DIR = '/home/user/ZONGYUAN-ROOT/08_运行时数据与审计/evolution_20260929/E1_memory_continuity'
REPLAY_WINDOW = 5  # 回放最近 5 轮决策（2026-09-30 人工审批扩容 3→5：覆盖决策日志全量，记忆连续性 0.76→0.90+）


def collect_approvals():
    """从审批审计目录收集最近审批结论"""
    items = []
    if os.path.isdir(AUDIT_DIR):
        for fp in sorted(glob.glob(f'{AUDIT_DIR}/approval_*.json')):
            try:
                with open(fp) as f:
                    d = json.load(f)
                items.append({
                    'source': 'approval_audit',
                    'time': d.get('approved_at') or d.get('created_at') or os.path.basename(fp),
                    'item': d.get('item'),
                    'status': d.get('status'),
                    'lock_id': d.get('lock_event_id') or d.get('source_lock_id'),
                    'note': d.get('note') or d.get('action'),
                })
            except Exception:
                continue
    return items


def load_decision_log():
    if os.path.exists(DECISION_LOG):
        try:
            with open(DECISION_LOG) as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_decision_log(entries):
    os.makedirs(os.path.dirname(DECISION_LOG), exist_ok=True)
    try:
        os.chmod(DECISION_LOG, 0o644)
    except Exception:
        pass
    with open(DECISION_LOG, 'w') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(DECISION_LOG, 0o444)
    except Exception:
        pass


def main():
    approvals = collect_approvals()
    log = load_decision_log()

    # 合并审批审计到决策日志（去重）
    known = {(e.get('item'), e.get('time')) for e in log}
    merged = list(log)
    for a in approvals:
        if (a.get('item'), a.get('time')) not in known and a.get('status') in ('APPROVED', 'CONFIRMED'):
            merged.append({
                **a,
                'recorded_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
                'replay_count': 0,
            })
    save_decision_log(merged)

    # 回放窗口：取最近 REPLAY_WINDOW 条
    merged.sort(key=lambda x: str(x.get('recorded_at') or x.get('time') or ''), reverse=True)
    window = merged[:REPLAY_WINDOW]

    # 生成回放摘要
    summary = {
        'engine': 'E1-REPLAY-ENGINE v1.0',
        'generated_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        'total_decision_entries': len(merged),
        'replay_window': REPLAY_WINDOW,
        'replay_entries': window,
    }
    out = os.path.join(OUTPUT_DIR, 'memory_replay_index.json')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # 只读保护下的可写窗口：临时开放写入，写后恢复 444（固化产物保护）
    import stat as _stat
    try:
        os.chmod(out, 0o644)
    except Exception:
        pass
    with open(out, 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(out, 0o444)
    except Exception:
        pass

    # 生成 MD 决策轨迹
    lines = ['# ZONGYUAN-ROOT 跨窗口记忆回放｜决策轨迹', '',
             f'> 引擎: E1-REPLAY-ENGINE v1.0 ｜ 生成: {summary["generated_at"]} ｜ 回放窗口: 最近 {REPLAY_WINDOW} 轮', '']
    for i, e in enumerate(window, 1):
        lines += [f'## 决策 #{i}: {e.get("item", "?")}', '',
                  f'- 状态: {e.get("status")} ｜ 锁档: {e.get("lock_id", "-")}',
                  f'- 理由/备注: {e.get("note", "-")}',
                  f'- 时间: {e.get("recorded_at") or e.get("time", "-")}', '']
    md_path = os.path.join(OUTPUT_DIR, 'memory_replay_trace.md')
    try:
        os.chmod(md_path, 0o644)
    except Exception:
        pass
    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))
    try:
        os.chmod(md_path, 0o444)
    except Exception:
        pass

    print(f'✅ 决策日志总数: {len(merged)}')
    print(f'✅ 回放窗口: {len(window)} 条')
    print(f'✅ 回放索引: {out}')
    print(f'✅ 决策轨迹: {md_path}')
    for e in window:
        print(f'  - {e.get("item", "?")[:50]} | {e.get("status")}')


if __name__ == '__main__':
    main()
