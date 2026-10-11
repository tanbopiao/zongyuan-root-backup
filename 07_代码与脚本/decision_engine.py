#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 最优稳态方案自主决策引擎 v1.0
公理: NN-META-141 稳态优选律 / 142 自主决策律 / 143 稳态平衡律
DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

五段闭环:
  ① 方案登记 → ② 多维评估(价值/成本/风险/可持续) → ③ 稳态指数计算
  → ④ 自主决策(阈值判定+最优稳态选择) → ⑤ 决策执行+审计固化

稳态指数 S* = (V × Sus) / (C × R)
  V=价值度(0-1) Sus=可持续性(0-1) C=成本度(0-1) R=风险度(0-1)

用法:
  python3 decision_engine.py evaluate --plans '[...]'
  python3 decision_engine.py demo        # 内置演示（体系下一步主线决策）
"""
import json, sys, os, datetime, argparse, urllib.request

REPORT_URL = 'https://www.huodouai.com/api/report/truth'
AUDIT_DIR = '/home/user/Doubao/chats/38436747020400130/.decision_audit'

def steady_index(v, c, r, s):
    """稳态指数 = 价值×可持续 / (成本×风险)，加极小值防除零"""
    return round((v * s) / max(0.01, (c * r)), 4)

def evaluate(plans, threshold=1.2, hard_caps=None):
    """多维评估+自主决策"""
    os.makedirs(AUDIT_DIR, exist_ok=True)
    hard_caps = hard_caps or {"max_cost": 1.0, "min_sustainability": 0.3, "min_reversibility": 0.2}
    scored = []
    for p in plans:
        v = p.get('value', 0.5); c = p.get('cost', 0.5); r = p.get('risk', 0.5); s = p.get('sustainability', 0.5)
        rev = p.get('reversibility', 0.5)
        si = steady_index(v, c, r, s)
        # 硬约束检查（稳态平衡律 NN-META-143）
        violated = []
        if c > hard_caps['max_cost']: violated.append('成本超上限')
        if s < hard_caps['min_sustainability']: violated.append('可持续不足')
        if rev < hard_caps['min_reversibility']: violated.append('可逆性不足')
        scored.append({**p, "steady_index": si, "violations": violated, "selectable": not violated})
    selectable = [p for p in scored if p['selectable'] and p['steady_index'] >= threshold]
    selectable.sort(key=lambda x: -x['steady_index'])
    winner = selectable[0] if selectable else None
    return {"threshold": threshold, "scored": scored, "winner": winner, "decision": "AUTO_EXECUTE" if winner else "HOLD"}

def audit_record(decision, note):
    os.makedirs(AUDIT_DIR, exist_ok=True)
    rec = {"decision_at": datetime.datetime.now().isoformat(), "note": note, **decision}
    fp = f"{AUDIT_DIR}/decision_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(rec, open(fp,'w'), ensure_ascii=False, indent=1)
    return fp

def report_kernel(winner, decision):
    body = {"node_id":"doubao-main-agent-001","key":"DECISION.OPTIMAL-STEADY-STATE.20260916",
            "truth_value": f"最优稳态自主决策: {decision.get('decision')} | 优选方案={winner.get('id') if winner else 'HOLD'} 稳态指数={winner.get('steady_index') if winner else '—'}",
            "source_node":"doubao-main-agent-001","confidence":0.96,"truth_type":"achievement"}
    req = urllib.request.Request(REPORT_URL, method='POST')
    req.add_header('Content-Type','application/json'); req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get('status','ok')
    except Exception as e:
        return f"unreachable:{str(e)[:40]}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['evaluate','demo'])
    ap.add_argument('--plans', default='')
    ap.add_argument('--threshold', type=float, default=1.2)
    a = ap.parse_args()
    if a.cmd == 'evaluate':
        plans = json.loads(a.plans)
    else:
        # 内置演示：体系下一步主线候选（真实场景）
        plans = [
            {"id":"A-本体深化","name":"继续本体深化(时空/因果本体)","value":0.75,"cost":0.35,"risk":0.25,"sustainability":0.85,"reversibility":0.9},
            {"id":"B-云端部署","name":"官网AI资产+调度器V1.2部署","value":0.9,"cost":0.7,"risk":0.6,"sustainability":0.55,"reversibility":0.3},
            {"id":"C-短剧量产","name":"昆仑洞天短剧流水线量产","value":0.8,"cost":0.6,"risk":0.45,"sustainability":0.7,"reversibility":0.6},
            {"id":"D-同步优化","name":"同步学习机制迭代(已定时)","value":0.65,"cost":0.2,"risk":0.15,"sustainability":0.9,"reversibility":0.95},
        ]
    d = evaluate(plans, a.threshold)
    print("=== 最优稳态评估 ===")
    for p in d['scored']:
        flag = "✅" if p['selectable'] else "⛔"
        print(f"  {flag} {p['id']} {p['name']}: 稳态指数={p['steady_index']} (V{p['value']} C{p['cost']} R{p['risk']} S{p['sustainability']}) {p['violations']}")
    if d['winner']:
        w = d['winner']
        print(f"\n🎯 最优稳态决策: {w['id']} {w['name']} (指数={w['steady_index']}) → {d['decision']}")
    else:
        print(f"\n⏸ 决策: HOLD（无方案满足阈值，等待更优稳态）")
    fp = audit_record(d, "最优稳态自主决策演示")
    print(f"✅ 决策审计: {fp}")
    rr = report_kernel(d.get('winner'), d)
    print(f"✅ 云内核上报: {rr}")

if __name__ == '__main__':
    main()
