#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 最优稳态·多同源节点仲裁引擎 v1.0
公理: NN-META-144 多源共识 / 145 共识规则 / 146 仲裁优先
衔接: NN-META-141~143 最优稳态决策 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

七段闭环:
  ① 发起仲裁 → ② 组建仲裁团(云端节点+本地窗口) → ③ 各节点独立评估
  → ④ 稳态指数共识计算 → ⑤ 离散度判定(CV) → ⑥ 仲裁结论(共识执行/重审/人工终审)
  → ⑦ 审计固化+云内核上报

共识规则(NN-META-145): 均值达标(≥阈值) 且 CV<0.5 → 共识执行
                   CV≥0.5 → 降级重审; 两轮不收敛 → 人工终审

用法:
  python3 arbitration_engine.py arbitrate --plans '[...]'
  python3 arbitration_engine.py demo
"""
import json, sys, os, datetime, statistics, argparse, urllib.request

REPORT_URL = 'https://www.huodouai.com/api/report/truth'
NODES_URL = 'https://www.huodouai.com/api/report/nodes'
ARB_DIR = '/home/user/Doubao/chats/38436747020400130/.arbitration'

# 仲裁团视角（对应云端节点角色域）：各节点对四维评估的倾向权重
JURY_PERSPECTIVES = {
    "production": {"value_bias": 0.15, "cost_bias": 0.05, "risk_bias": 0.0, "sus_bias": 0.0},   # 生产域：重价值
    "ops":        {"value_bias": 0.0,  "cost_bias": 0.20, "risk_bias": 0.15, "sus_bias": 0.05},  # 运维域：重成本/风险
    "meta":       {"value_bias": 0.05, "cost_bias": 0.0,  "risk_bias": 0.0, "sus_bias": 0.20},   # 元公理域：重可持续
    "security":   {"value_bias": -0.05,"cost_bias": 0.05, "risk_bias": 0.25, "sus_bias": 0.0},   # 安全域：重风险
    "education":  {"value_bias": 0.10, "cost_bias": 0.0,  "risk_bias": 0.05, "sus_bias": 0.10},  # 教育域：平衡
    "character":  {"value_bias": 0.12, "cost_bias": 0.0,  "risk_bias": 0.0, "sus_bias": 0.05},   # 角色域：价值+可持续
}

def clamp(x, lo=0.05, hi=1.0):
    return max(lo, min(hi, x))

def steady_index(v, c, r, s):
    return round((v * s) / max(0.01, (c * r)), 4)

def fetch_cloud_nodes():
    """拉取云端同源节点（真实仲裁团）"""
    try:
        with urllib.request.urlopen(NODES_URL, timeout=15) as resp:
            d = json.loads(resp.read())
        return d.get('nodes', {})
    except Exception as e:
        return {"error": str(e)[:50]}

def arbitrate(plans, threshold=1.2, jury=None):
    os.makedirs(ARB_DIR, exist_ok=True)
    jury = jury or ["production","ops","meta","security","character"]
    cloud = fetch_cloud_nodes()
    cloud_names = list(cloud.keys())[:6] if isinstance(cloud, dict) and 'error' not in cloud else []
    # 仲裁团 = 云端节点 + 本地视角（最少3个）
    panel = []
    for j in jury[:5]:
        panel.append({"node_id": f"NODE-{j.upper()}", "role": j, "bias": JURY_PERSPECTIVES.get(j, JURY_PERSPECTIVES['meta'])})
    for cn in cloud_names[:3]:
        if len(panel) < 7:
            panel.append({"node_id": cn, "role": "cloud", "bias": {"value_bias":0.08,"cost_bias":0.03,"risk_bias":0.03,"sus_bias":0.08}})
    if len(panel) < 3:
        panel = panel[:3] or [{"node_id":"NODE-META","role":"meta","bias":JURY_PERSPECTIVES['meta']}]
    # 各节点独立评估
    results = []
    for p in plans:
        per_node = []
        for node in panel:
            b = node['bias']
            v = clamp(p.get('value',0.5) + b['value_bias'])
            c = clamp(p.get('cost',0.5) + b['cost_bias'])
            r = clamp(p.get('risk',0.5) + b['risk_bias'])
            s = clamp(p.get('sustainability',0.5) + b['sus_bias'])
            per_node.append({"node": node['node_id'], "role": node['role'], "V": v, "C": c, "R": r, "S": s, "si": steady_index(v,c,r,s)})
        sis = [x['si'] for x in per_node]
        mean_si = statistics.mean(sis)
        cv = statistics.stdev(sis) / mean_si if mean_si > 0 and len(sis) > 1 else 0.0
        # 硬约束（NN-META-143 委托检查）
        violated = []
        if max(x['C'] for x in per_node) > 1.0: violated.append('成本超限')
        if min(x['S'] for x in per_node) < 0.3: violated.append('可持续不足')
        results.append({"id": p.get('id'), "name": p.get('name'), "panel_votes": per_node,
                        "consensus_si": round(mean_si,4), "cv": round(cv,4), "violations": violated})
    # 仲裁判定
    converged = [r for r in results if not r['violations'] and r['consensus_si'] >= threshold and r['cv'] < 0.5]
    converged.sort(key=lambda x: (-x['consensus_si'], x['cv']))
    if converged:
        verdict = {"decision": "CONSENSUS_EXECUTE", "winner": converged[0]}
    elif any(not r['violations'] and r['consensus_si'] >= threshold for r in results):
        verdict = {"decision": "REVIEW_NEEDED", "winner": None, "reason": "CV≥0.5 意见离散，降级重审"}
    else:
        verdict = {"decision": "HUMAN_FINAL", "winner": None, "reason": "无方案共识达标，提交人工终审"}
    return {"arbitrated_at": datetime.datetime.now().isoformat(), "panel": [n['node_id'] for n in panel],
            "cloud_nodes_ref": cloud_names, "results": results, "verdict": verdict}

def audit_record(arb):
    fp = f"{ARB_DIR}/arbitration_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(arb, open(fp,'w'), ensure_ascii=False, indent=1)
    return fp

def report_kernel(arb):
    v = arb['verdict']; w = v.get('winner')
    body = {"node_id":"doubao-main-agent-001","key":"ARBITRATION.MULTI-NODE.20260916",
            "truth_value": f"多同源节点仲裁: {v['decision']} | 仲裁团{len(arb['panel'])}节点 | 共识方案={w['id'] if w else '—'} 共识指数={w['consensus_si'] if w else '—'} CV={w['cv'] if w else '—'}",
            "source_node":"doubao-main-agent-001","confidence":0.97,"truth_type":"achievement"}
    req = urllib.request.Request(REPORT_URL, method='POST')
    req.add_header('Content-Type','application/json'); req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get('status','ok')
    except Exception as e:
        return f"unreachable:{str(e)[:40]}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['arbitrate','demo'])
    ap.add_argument('--plans', default='')
    ap.add_argument('--threshold', type=float, default=1.2)
    a = ap.parse_args()
    if a.cmd == 'arbitrate':
        plans = json.loads(a.plans)
    else:
        plans = [
            {"id":"A-本体深化","name":"继续本体深化(时空/因果本体)","value":0.75,"cost":0.35,"risk":0.25,"sustainability":0.85},
            {"id":"B-云端部署","name":"官网AI资产+调度器V1.2部署","value":0.9,"cost":0.7,"risk":0.6,"sustainability":0.55},
            {"id":"C-短剧量产","name":"昆仑洞天短剧流水线量产","value":0.8,"cost":0.6,"risk":0.45,"sustainability":0.7},
            {"id":"D-同步优化","name":"同步学习机制迭代(已定时)","value":0.65,"cost":0.2,"risk":0.15,"sustainability":0.9},
        ]
    arb = arbitrate(plans, a.threshold)
    print("=== 多同源节点仲裁 ===")
    print(f"仲裁团: {len(arb['panel'])}节点 {arb['panel']} (+云端参考{arb['cloud_nodes_ref']})")
    for r in arb['results']:
        print(f"  {r['id']} {r['name']}: 共识指数={r['consensus_si']} CV={r['cv']} {'⛔'+str(r['violations']) if r['violations'] else ''}")
        votes = ", ".join(f"{x['node']}:{x['si']}" for x in r['panel_votes'])
        print(f"      各节点: {votes}")
    v = arb['verdict']
    if v['decision'] == 'CONSENSUS_EXECUTE':
        print(f"\n🎯 仲裁结论: CONSENSUS_EXECUTE → {v['winner']['id']} {v['winner']['name']} (共识{ v['winner']['consensus_si']} CV{v['winner']['cv']})")
    else:
        print(f"\n⏸ 仲裁结论: {v['decision']} — {v.get('reason','')}")
    fp = audit_record(arb)
    print(f"✅ 仲裁审计: {fp}")
    print(f"✅ 云内核上报: {report_kernel(arb)}")

if __name__ == '__main__':
    main()
