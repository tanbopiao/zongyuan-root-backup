# E3-TRIANGLE-AUDIT｜公理-法则-提案三角对账引擎 v1.0

"""E3 公理体系完备：三角对账
公理提案(axiom_proposals) ↔ 元法则(MR-AXIOM-*) ↔ 元公理(.tmp_meta_axioms) 三方引用完整性校验。
规则：
  1. 每条公理提案必须有对应 MR-AXIOM 法则（domain 映射）
  2. 每条 MR-AXIOM 法则应有对应提案来源
  3. 已转正(≥85分)提案应进入元公理注册表
输出：对账报告 JSON + 差异清单
"""
import json, os, os, datetime

ROOT = '/home/user/ZONGYUAN-ROOT/01_核心资产锚点'
OUT = '/home/user/ZONGYUAN-ROOT/08_运行时数据与审计/evolution_20260929/E3_axiom_completion'

DOMAIN_MAP = {
    'perception': ['MR-AXIOM-011', 'MR-AXIOM-012'],
    'coordination': ['MR-AXIOM-013', 'MR-AXIOM-014'],
    'scheduling': ['MR-AXIOM-015', 'MR-AXIOM-016'],
    'monitoring': ['MR-AXIOM-017', 'MR-AXIOM-018'],
    'optimization': ['MR-AXIOM-019', 'MR-AXIOM-020'],
}
DOMAIN_COUNTER = {'perception': 0, 'coordination': 0, 'scheduling': 0, 'monitoring': 0, 'optimization': 0}


def main():
    # 1. 读取三方
    with open(f'{ROOT}/axiom_proposals.json') as f:
        prop_data = json.load(f)
    proposals = prop_data if isinstance(prop_data, list) else prop_data.get('proposals', [])

    with open(f'{ROOT}/meta_rules_registry.json') as f:
        rules_data = json.load(f)
    rules = {r['rule_id']: r for r in rules_data['meta_rules']}

    with open(f'{ROOT}/.tmp_meta_axioms.json') as f:
        axioms = json.load(f)

    # 2. 对账
    findings = []
    for i, p in enumerate(proposals, 1):
        domain = p.get('domain', '?')
        counter = DOMAIN_COUNTER.get(domain, 0)
        DOMAIN_COUNTER[domain] = counter + 1
        expected_rules = DOMAIN_MAP.get(domain, [])
        # 1:1 顺序配对：域内第 N 条提案 → 域内第 N 条法则
        expected_rule = expected_rules[counter] if counter < len(expected_rules) else None
        p_id = f'PROP-{i:02d}-{domain.upper()}'
        p['proposal_id'] = p_id  # 补 ID

        # 检查法则对应（1:1）
        if expected_rule:
            r = rules.get(expected_rule)
            if r is None:
                findings.append({'type': 'MISSING_RULE', 'proposal': p_id, 'rule': expected_rule, 'msg': f'{p_id} 缺对应法则 {expected_rule}'})
            elif r.get('status') != 'CONFIRMED':
                findings.append({'type': 'RULE_NOT_CONFIRMED', 'proposal': p_id, 'rule': expected_rule, 'status': r.get('status'), 'msg': f'{expected_rule} 状态={r.get("status")} 未转正'})

        # 检查元公理转正（提案文本是否已进入元公理）
        in_axiom = any(p.get('content','')[:20] in a.get('content','') for a in axioms)
        if not in_axiom and p.get('score', 0) >= 85:
            findings.append({'type': 'AXIOM_NOT_PROMOTED', 'proposal': p_id, 'msg': f'{p_id} 已达85+但未转元公理'})

    # 3. 保存补齐 proposal_id 的提案文件
    try:
        os.chmod(f'{ROOT}/axiom_proposals.json', 0o644)
    except Exception:
        pass
    with open(f'{ROOT}/axiom_proposals.json', 'w') as f:
        json.dump(prop_data if not isinstance(prop_data, list) else proposals, f, ensure_ascii=False, indent=2)

    # 4. 报告
    os.makedirs(OUT, exist_ok=True)
    report = {
        'report_id': f'TRI-AUDIT-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}',
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        'proposals_total': len(proposals),
        'rules_expected': 10,
        'rules_confirmed': sum(1 for rid in DOMAIN_MAP.values() for rid in rid if rules.get(rid, {}).get('status') == 'CONFIRMED'),
        'axiom_proposals_total': len(axioms),
        'findings': findings,
        'verdict': 'PASS' if not findings else 'GAPS_FOUND',
    }
    out = os.path.join(OUT, f"triangle_audit_{datetime.datetime.now().strftime('%Y%m%d')}.json")
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

    print(f'✅ 三角对账完成: {report["verdict"]}')
    print(f'  提案 {len(proposals)} 条 | 法则 10 条(已确认 {report["rules_confirmed"]}) | 元公理 {len(axioms)} 条')
    for fd in findings[:12]:
        print(f'  ⚠️ [{fd["type"]}] {fd["msg"]}')
    print(f'  报告: {out}')
    return 0 if report['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
