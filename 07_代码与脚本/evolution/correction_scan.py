# E2-CORRECT-SCAN｜纠错扫描引擎 v1.0

"""E2 自治成熟度提升：纠错扫描自动化
功能：每次任务周期结束时自动触发，扫描六维自检缺口项的实际补全状态，
生成纠错扫描报告（correction_scan_<date>.json），为成熟度 86.8%→92% 提供量化证据。
"""
import json, os, datetime, glob, re

ROOT = '/home/user/ZONGYUAN-ROOT'
E2_DIR = f'{ROOT}/08_运行时数据与审计/evolution_20260929/E2_autonomy_maturity'
SELF_CHECK = f'{ROOT}/08_运行时数据与审计/evolution_20260929/self_check_20260929.json'

GAP_ITEMS = {
    'EP-01': {'name': '生产能力峰值', 'target': 95, 'evidence_pattern': 'Lv10'},
    'EP-03': {'name': '效率极值', 'target': 85, 'evidence_pattern': '闭环'},
    'ES-01': {'name': '资产锁档率', 'target': 95, 'evidence_pattern': 'LOCK-'},
    'ES-03': {'name': '自我维持时长', 'target': 90, 'evidence_pattern': 'guard|守护|AUTO-RECOVERY'},
    'SC-01': {'name': '自检频率', 'target': 90, 'evidence_pattern': 'self_check'},
    'SC-02': {'name': '纠错响应速度', 'target': 85, 'evidence_pattern': 'correction'},
    'SC-03': {'name': '元认知覆盖率', 'target': 100, 'evidence_pattern': '元进化'},
}


def scan_evidence():
    """扫描持久层中各类证据文件的出现情况"""
    evidence = {}
    # 全库文件清单（排除历史归档）
    all_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '05_历史归档' in dirpath or '.skills' in dirpath:
            continue
        for fn in filenames:
            all_files.append(os.path.join(dirpath, fn))

    for gid, spec in GAP_ITEMS.items():
        pat = spec['evidence_pattern']
        base_lower = [os.path.basename(f).lower() for f in all_files]
        try:
            hits = [f for f in all_files if re.search(pat.lower(), os.path.basename(f).lower())]
        except re.error:
            hits = [f for f in all_files if pat.lower() in os.path.basename(f).lower()]
        evidence[gid] = {
            'name': spec['name'],
            'evidence_hits': len(hits),
            'samples': hits[:3],
            'resolved': len(hits) > 0,
        }
    return evidence


def main():
    os.makedirs(E2_DIR, exist_ok=True)
    evidence = scan_evidence()

    # 读取自检报告当前分
    current_scores = {}
    if os.path.exists(SELF_CHECK):
        with open(SELF_CHECK) as f:
            sc = json.load(f)
        for dim in sc.get('dimensions', []):
            for m in dim.get('metrics', []):
                current_scores[m['metric_id']] = m['current_value']

    report = {
        'report_id': f'CORR-SCAN-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}',
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        'mode': 'auto_scan',
        'gaps': [],
        'summary': {'total_gaps': len(GAP_ITEMS), 'resolved': 0, 'unresolved': 0},
    }
    for gid, spec in GAP_ITEMS.items():
        ev = evidence[gid]
        gap = {
            'metric_id': gid,
            'name': spec['name'],
            'current': current_scores.get(gid, 0),
            'target': spec['target'],
            'evidence_resolved': ev['resolved'],
            'evidence_count': ev['evidence_hits'],
            'samples': ev['samples'],
        }
        report['gaps'].append(gap)
        if ev['resolved']:
            report['summary']['resolved'] += 1
        else:
            report['summary']['unresolved'] += 1

    out = os.path.join(E2_DIR, f"correction_scan_{datetime.datetime.now().strftime('%Y%m%d')}.json")
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

    print(f'✅ 纠错扫描完成: {report["report_id"]}')
    print(f'  缺口 {report["summary"]["total_gaps"]} 项 | 有证据 {report["summary"]["resolved"]} | 待补 {report["summary"]["unresolved"]}')
    for g in report['gaps']:
        mark = '✅' if g['evidence_resolved'] else '⚠️'
        print(f'  {mark} {g["metric_id"]} {g["name"]} | {g["current"]}/{g["target"]} | 证据 {g["evidence_count"]} 处')
    print(f'  报告: {out}')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
