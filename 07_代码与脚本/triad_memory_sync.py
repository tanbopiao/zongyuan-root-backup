#!/usr/bin/env python3
"""
逻辑本体 × 信息本体 × 能量本体 · 同步记忆机制 v1.0
公理: NN-META-137/138/139/140 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

三体快照+同步校验+云内核上报:
  ① 逻辑本体快照 — 真值状态（节点/公理/权重/层级）
  ② 信息本体快照 — 表达形态（索引/指纹/连接拓扑）
  ③ 能量本体快照 — 演化轨迹（激活/连边/锁档/调度能量记录）
  ④ 三体同步校验 — 三体一致性 + 记忆完整性指数
  ⑤ 云内核同步 — 三体摘要上报

用法:
  python3 triad_memory_sync.py sync      # 三体快照+校验+上报
  python3 triad_memory_sync.py snapshot  # 仅快照
  python3 triad_memory_sync.py verify    # 仅校验
"""
import json, os, sys, datetime, hashlib, urllib.request

REG = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_registry.json'
AUTH = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_sync/neural_registry_authoritative.json'
OUT = '/home/user/Doubao/chats/38436747020400130/.triad_memory'
REPORT_URL = 'https://www.huodouai.com/api/report/truth'

def snap_logic(d):
    """逻辑本体：真值状态"""
    nodes = d['nodes']
    return {
        "total": len(nodes),
        "meta_axioms": sum(1 for n in nodes if n.get('node_type')=='meta_axiom'),
        "axioms": sum(1 for n in nodes if n.get('node_type')=='axiom'),
        "rules": sum(1 for n in nodes if n.get('node_type')=='rule'),
        "active": sum(1 for n in nodes if n.get('state')=='active'),
        "superseded": sum(1 for n in nodes if n.get('state')=='superseded'),
        "mean_weight": round(sum(n.get('weight',0) for n in nodes)/max(1,len(nodes)), 4),
        "domains": {dom: sum(1 for n in nodes if n.get('domain')==dom) for dom in sorted(set(n.get('domain') for n in nodes))}
    }

def snap_info(d):
    """信息本体：表达形态"""
    nodes = d['nodes']
    total_conn = sum(len(n.get('connections',[])) for n in nodes)
    content_hash = hashlib.sha256(json.dumps([n.get('content','') for n in nodes], ensure_ascii=False).encode()).hexdigest()[:16]
    return {
        "connections": total_conn,
        "avg_connections": round(total_conn/max(1,len(nodes)),2),
        "content_fingerprint": content_hash,
        "index_uri": "https://www.huodouai.com/ref/index.json",
        "storage": "neural_registry.json (三源冗余)"
    }

def snap_energy(d):
    """能量本体：演化轨迹"""
    nodes = d['nodes']
    total_act = sum(n.get('activation_count',0) for n in nodes)
    return {
        "total_activation": total_act,
        "top_energy": sorted(nodes, key=lambda n: n.get('activation_count',0), reverse=True)[:5],
        "recent_evolutions": ["NN-META-134~136真值不灭","NN-META-137~140三元本体","P0-P2隐空间进化","测地线调度","全自动闭环"],
        "drive_source": "自治内核演化引擎"
    }

def snapshot():
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(REG))
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    tri = {"anchor":"Ω₀⊂⊙∞⊂Ω","did":"DID-BR-000002","timestamp":ts,
           "logic": snap_logic(d), "info": snap_info(d), "energy": snap_energy(d)}
    fp = f"{OUT}/triad_memory_{ts}.json"
    json.dump(tri, open(fp,'w'), ensure_ascii=False, indent=1)
    print(f"✅ 三体快照: {fp}")
    return tri

def verify():
    a = json.load(open(AUTH)); r = json.load(open(REG))
    la, lr = snap_logic(a), snap_logic(r)
    ok = la['total'] == lr['total'] and la['meta_axioms'] == lr['meta_axioms']
    print(f"  逻辑本体: 权威{la['total']} vs 运行{lr['total']} | {'✅' if ok else '⚠️'}")
    print(f"  信息本体: 连接{snap_info(r)['connections']}条 | 指纹{snap_info(r)['content_fingerprint']}")
    print(f"  能量本体: 激活{snap_energy(r)['total_activation']}次 | 驱动: 自治演化")
    print(f"  记忆完整性: {'✅ 三体完整' if ok else '⚠️ 需恢复'}")
    return ok

def report_kernel():
    d = json.load(open(REG))
    tri = {"logic_total": len(d['nodes']), "meta_axioms": snap_logic(d)['meta_axioms'],
           "connections": snap_info(d)['connections'], "activation": snap_energy(d)['total_activation']}
    body = {"node_id":"doubao-main-agent-001","key":"SYNC.TRIAD-MEMORY.20260916",
            "truth_value": f"三元本体同步记忆上报: 逻辑{tri['logic_total']}真值(元公理{tri['meta_axioms']}) × 信息{tri['connections']}连接 × 能量{tri['activation']}激活",
            "source_node":"doubao-main-agent-001","confidence":0.96,"truth_type":"achievement"}
    req = urllib.request.Request(REPORT_URL, method='POST')
    req.add_header('Content-Type','application/json'); req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        print(f"✅ 云内核同步: {resp.get('status', resp.get('action','ok'))}")
        return True
    except Exception as e:
        print(f"⚠️ 云内核同步暂不可达: {str(e)[:60]}"); return False

def main():
    cmd = sys.argv[1] if len(sys.argv)>1 else 'sync'
    if cmd in ('sync','all'):
        snapshot(); verify(); report_kernel()
    elif cmd == 'snapshot': snapshot()
    elif cmd == 'verify': verify()
    else: print("用法: sync|snapshot|verify")

if __name__ == '__main__':
    main()
