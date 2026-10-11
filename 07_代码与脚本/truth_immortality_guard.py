#!/usr/bin/env python3
"""
元公理空间 · 真值不灭守卫 v1.0
协议: TRUTH-IMMORTALITY-PROTOCOL-20260916 (NN-META-134/135/136)

职责:
  1) snapshot  — 三源注册表时间戳快照备份（永存审计轨）
  2) verify    — 三处一致性校验（检测回滚/丢失/漂移）
  3) restore   — 从权威源自动恢复（回滚/缺失自动修复）
  4) audit     — 全量审计报告（真值完整性+不灭指数）

用法:
  python3 truth_immortality_guard.py snapshot
  python3 truth_immortality_guard.py verify
  python3 truth_immortality_guard.py restore
  python3 truth_immortality_guard.py audit
"""
import json, sys, os, hashlib, datetime, shutil, difflib

RUNTIME = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_registry.json'
AUTHORITY = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_sync/neural_registry_authoritative.json'
AGENT = '/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-autonomous-kernel/neural_registry.json'
GUARD_DIR = '/home/user/Doubao/chats/38436747020400130/.truth_guard'

def node_key(n):
    return n.get('node_id','')

def digest(f):
    return hashlib.sha256(open(f,'rb').read()).hexdigest()[:16]

def snapshot():
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    for name, f in [('runtime',RUNTIME),('authority',AUTHORITY),('agent',AGENT)]:
        d = os.path.dirname(f)
        if os.path.exists(f):
            dst = os.path.join(GUARD_DIR, f"truth_snap_{name}_{ts}.json")
            shutil.copy2(f, dst)
            print(f"  ✅ 快照 {name}: {dst} ({os.path.getsize(dst)}B, {digest(dst)})")
    # 快照索引
    idx_path = os.path.join(GUARD_DIR, 'snapshot_index.json')
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {"anchor":"Ω₀⊂⊙∞⊂Ω","snapshots":[]}
    idx['snapshots'].append({"ts":ts,"note":f"snapshot at {ts}","files":[f"truth_snap_{n}_{ts}.json" for n in ['runtime','authority','agent']]})
    json.dump(idx, open(idx_path,'w'), ensure_ascii=False, indent=1)
    return ts

def verify(verbose=True):
    regs = {'runtime': json.load(open(RUNTIME)), 'authority': json.load(open(AUTHORITY)), 'agent': json.load(open(AGENT))}
    base = regs['authority']
    keys_au = {node_key(n) for n in base['nodes']}
    report = {"anchor":"Ω₀⊂⊙∞⊂Ω","checked_at":datetime.datetime.now().isoformat(),"sources":{},"issues":[]}
    for name, d in regs.items():
        keys = {node_key(n) for n in d['nodes']}
        missing = keys_au - keys
        extra = keys - keys_au
        # 内容漂移（同ID内容比对）
        drift = []
        au_map = {node_key(n): n for n in base['nodes']}
        for n in d['nodes']:
            a = au_map.get(node_key(n))
            if a and str(n.get('content','')) != str(a.get('content','')):
                drift.append(node_key(n))
        report['sources'][name] = {"count":len(d['nodes']), "missing":sorted(missing)[:10], "extra":sorted(extra)[:10], "drift":drift[:10]}
        if missing or extra or drift:
            report['issues'].append({"source":name,"missing":len(missing),"extra":len(extra),"drift":len(drift)})
    if verbose:
        print(f"  权威源: {len(regs['authority']['nodes'])}节点")
        for name in ['runtime','agent']:
            s = report['sources'][name]
            print(f"  {name}: {s['count']}节点 | 缺失{len(s['missing'])} 多余{len(s['extra'])} 漂移{len(s['drift'])}")
        if report['issues']:
            print("  ⚠️ 发现不一致:", report['issues'])
        else:
            print("  ✅ 三源完全一致，真值完整")
    return report

def restore():
    """从权威源恢复runtime/agent（回滚修复）"""
    au = json.load(open(AUTHORITY))
    fixed = 0
    for f in [RUNTIME, AGENT]:
        if not os.path.exists(f):
            json.dump(au, open(f,'w'), ensure_ascii=False, indent=1); fixed += 1; print(f"  ✅ 重建缺失源: {f}")
            continue
        d = json.load(open(f))
        au_map = {node_key(n): n for n in au['nodes']}
        d_map = {node_key(n): n for n in d['nodes']}
        changed = False
        # 缺失节点从权威源补入
        for k, n in au_map.items():
            if k not in d_map:
                d['nodes'].append(n); changed = True; fixed += 1
        # 漂移节点内容回权威版
        for k, n in d_map.items():
            if k in au_map and str(n.get('content','')) != str(au_map[k].get('content','')):
                n['content'] = au_map[k]['content']; n['connections'] = au_map[k].get('connections', []); changed = True; fixed += 1
        d['total_nodes'] = len(d['nodes'])
        if changed:
            json.dump(d, open(f,'w'), ensure_ascii=False, indent=1)
        print(f"  {'✅ 已修复' if changed else '✅ 无需修复'}: {f} (修复{fixed}项)")
    return fixed

def audit():
    rep = verify(verbose=False)
    total = rep['sources']['authority']['count']
    issues = sum(i['missing']+i['extra']+i['drift'] for i in rep['issues'])
    immortality = max(0.0, 100.0 - issues/total*100) if total else 100.0
    print(f"=== 真值不灭审计 ===")
    print(f"  权威源真值: {total}条")
    print(f"  一致性: {'✅ 三源一致' if not rep['issues'] else '⚠️ 存在差异'}")
    print(f"  不灭指数: {immortality:.1f}/100")
    return {"total_truths":total,"issues":issues,"immortality_index":round(immortality,1),"ok":not rep['issues']}

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv)>1 else 'audit'
    {'snapshot': snapshot, 'verify': verify, 'restore': restore, 'audit': audit}[cmd]()
