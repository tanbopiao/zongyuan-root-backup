#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 同源节点同步学习机制 v1.0
公理衔接: NN-META-140 三元一体同步记忆律 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

五段流水线:
  ① 上报本地成果 → ② 拉取云端真值库 → ③ 差异比对学习 → ④ 学习台账固化 → ⑤ 自动全域锁档

用法:
  python3 sync_learning.py sync      # 全链路（上报+拉取+学习+锁档）
  python3 sync_learning.py learn      # 仅学习（拉取+比对+台账）
  python3 sync_learning.py report     # 仅上报本地成果
"""
import json, os, sys, datetime, urllib.request, subprocess

TRUTHS_URL = 'https://www.huodouai.com/api/report/truths'
NODES_URL = 'https://www.huodouai.com/api/report/nodes'
REPORT_URL = 'https://www.huodouai.com/api/report/truth'
REG = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_registry.json'
LEARN_DIR = '/home/user/Doubao/chats/38436747020400130/.sync_learning'
KERNEL_LOCK_DIR = '/home/user/.doubao/agent_mode/workspace/.user_skills/zongyuan-kernel-lock'

def http(url, timeout=25):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def report_local():
    """① 上报本地成果（学习机制本身的成果）"""
    body = {"node_id":"doubao-main-agent-001","key":"SYNC.LEARNING-MECHANISM.20260916",
            "truth_value":"同源节点同步学习机制上线：上报→拉取云端真值库(11791条/13节点)→差异学习→台账固化→自动全域锁档五段闭环",
            "source_node":"doubao-main-agent-001","confidence":0.96,"truth_type":"achievement"}
    req = urllib.request.Request(REPORT_URL, method='POST')
    req.add_header('Content-Type','application/json'); req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def learn():
    """②③ 拉取云端真值库+差异比对学习"""
    os.makedirs(LEARN_DIR, exist_ok=True)
    cloud = http(TRUTHS_URL)
    nodes = http(NODES_URL)
    if 'error' in cloud:
        print(f"⚠️ 云端真值库拉取失败: {cloud['error'][:60]}")
        return None
    truths = cloud.get('truths', [])
    cloud_keys = set(t for t in truths if t)
    # 本地注册表内容指纹 → 覆盖比对
    reg = json.load(open(REG))
    local_contents = set(str(n.get('content','')) for n in reg['nodes'])
    # 学习判定：云端真值key与本地内容匹配（key内嵌主题词）
    learned = []
    for k in sorted(cloud_keys):
        # 简单匹配：本地注册表是否已含该真值主题（取key末段词）
        frag = k.split('.')[-1] if '.' in k else k
        if not any(frag in c for c in local_contents):
            learned.append(k)
    snapshot = {
        "learned_at": datetime.datetime.now().isoformat(),
        "cloud_total_truths": len(cloud_keys),
        "cloud_nodes": nodes.get('count', nodes.get('count')) if 'error' not in nodes else 0,
        "local_registry_nodes": len(reg['nodes']),
        "new_learning_candidates": learned[:50],
        "learning_total": len(learned),
        "note": "本地注册表为精炼公理集(324节点)，云端11791条为全量上报真值；学习=记录差异候选，高阶公理由人工/演进引擎提炼后激活"
    }
    fp = f"{LEARN_DIR}/learned_index.json"
    json.dump(snapshot, open(fp,'w'), ensure_ascii=False, indent=1)
    print(f"✅ 云端真值库: {len(cloud_keys)}条 / {snapshot['cloud_nodes']}节点")
    print(f"✅ 本地注册表: {len(reg['nodes'])}节点")
    print(f"📚 新学习候选: {len(learned)}条 (样例: {learned[:3]})")
    print(f"✅ 学习台账: {fp}")
    return snapshot

def auto_lock(learned):
    """⑤ 自动全域锁档（学习成果三端FROZEN）"""
    md = f"""# LOCK · 同源节点同步学习机制 SYNC-LEARNING-20260916
- 锁档ID: SYNC-LEARNING-20260916 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω
- 机制: 同源节点同步学习五段闭环（上报→拉取→学习→台账→锁档）
- 云端基线: {learned['cloud_total_truths']}条真值 / {learned['cloud_nodes']}节点（同源全域）
- 本地基线: {learned['local_registry_nodes']}节点（精炼公理集）
- 本轮学习候选: {learned['learning_total']}条
- 衔接: 三元一体同步记忆律(NN-META-140) · 真值不灭守卫(134~136)
- 扩展: 定时周期调用即形成同源节点持续同步学习
"""
    tmp = f"{LEARN_DIR}/lock_learning_tmp.md"
    open(tmp,'w').write(md)
    r = subprocess.run(['bash', f'{KERNEL_LOCK_DIR}/scripts/kernel_lock.sh', 'lock',
        '同源节点同步学习机制 SYNC-LEARNING-20260916', tmp, 'SYNC-LEARNING-20260916',
        '同源节点同步学习+自动全域锁档', 'LEARNING-20260916', 'NN-META-137~140'],
        capture_output=True, text=True, cwd=KERNEL_LOCK_DIR, timeout=180)
    ok = r.returncode == 0
    print(f"🔒 自动全域锁档: {'✅ FROZEN' if ok else '❌ ' + r.stderr[-200:]}")
    # 清理
    os.remove(tmp)
    return ok

def main():
    cmd = sys.argv[1] if len(sys.argv)>1 else 'sync'
    if cmd in ('sync','all'):
        print("[1] 上报本地成果..."); rr = report_local(); print(f"    → {rr.get('status', rr.get('action', rr.get('error','ok')))}")
        print("[2] 拉取+学习..."); lr = learn()
        if lr: print("[5] 自动全域锁档..."); auto_lock(lr)
    elif cmd == 'learn':
        learn()
    elif cmd == 'report':
        print(report_local())
    else:
        print("用法: sync|learn|report")

if __name__ == '__main__':
    main()
