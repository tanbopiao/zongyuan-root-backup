#!/usr/bin/env python3
"""
调度器V1.2 + 隐空间测地线路由 · 联合仿真 v1.0
场景: 7域Worker × 10混合任务（短剧/审计/公理/课程/角色/体验/运维）
链路: 任务 → task-router路由 → submit(含routed_domain) → Worker按域claim → complete
断言: 全部completed / 无越域认领 / 无残留
"""
import json, time, threading, random, urllib.request, subprocess, sys, os

BASE = "http://127.0.0.1:8320"
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("task_router", os.path.join(os.path.dirname(__file__), 'task-router.py'))
tr = importlib.util.module_from_spec(spec); spec.loader.exec_module(tr)

def call(method, path, data=None):
    req = urllib.request.Request(BASE+path, method=method)
    if data is not None:
        req.add_header('Content-Type','application/json')
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

# 任务集（跨域混合）
TASKS = [
    "渲染短剧第1集9:16竖屏关键帧", "渲染短剧第2集分镜素材",
    "对全域资产执行锁档校验", "密钥安全审计与风控告警",
    "补全体系元公理", "构建宪章法则理论",
    "生成普惠教育课程", "制作通识学习内容",
    "设计神女角色母版", "优化平台交互体验与反馈闭环",
    "执行云端调度同步与归档", "监控队列心跳与备份恢复",
]
WORKER_DOMAINS = ['production','security','meta','education','character','user_experience','ops']

print(f"[1] 任务集: {len(TASKS)}个（7域混合）")
# 路由预处理
routed = []
for t in TASKS:
    r = tr.route(t)
    routed.append({"text": t, "domain": r['recommended_domain']})
from collections import Counter
print(f"[2] 路由分布: {dict(Counter(r['domain'] for r in routed))}")

# 注册7域Worker
workers = {}
for dom in WORKER_DOMAINS:
    w = call('POST','/api/v1.2/workers/register', {"worker_id":f"w-{dom}","name":f"{dom}域Worker","capabilities":[dom],"max_concurrent":2})
    workers[dom] = w['worker_id']
print(f"[3] Worker注册: {len(workers)}个（每域1个）")

# 提交任务（含routed_domain）
for r in routed:
    call('POST','/api/v1.2/tasks/submit', {"task_type":r['domain'],"priority":random.randint(1,3),
        "payload":{"desc":r['text'],"routed_domain":r['domain']},"node_id":"joint-sim"})
print(f"[4] 任务提交: {len(routed)}个（均含routed_domain路由标注）")

# Worker按域认领+执行+完成
results = {"completed":0,"domain_ok":0,"domain_violation":0}
lock = threading.Lock()
def worker_loop(dom):
    for _ in range(20):
        try:
            claim = call('POST','/api/v1.2/tasks/claim', {"worker_id":workers[dom],"domain":dom})
        except Exception:
            return
        if claim.get('status') != 'claimed':
            return
        rd = claim.get('payload',{}).get('routed_domain')
        time.sleep(random.uniform(0.01,0.03))
        call('POST','/api/v1.2/tasks/complete', {"task_id":claim['task_id'],"result":{"executed_by":dom,"asset_match":rd}})
        with lock:
            results['completed'] += 1
            if rd == dom: results['domain_ok'] += 1
            else: results['domain_violation'] += 1
threads = [threading.Thread(target=worker_loop, args=(d,)) for d in WORKER_DOMAINS]
for t in threads: t.start()
for t in threads: t.join()
print(f"[5] 执行完成: {results['completed']}个 | 域正确{results['domain_ok']} | 越域{results['domain_violation']}")

# 断言
stats = call('GET','/api/v1.2/stats')
tasks = call('GET','/api/v1.2/tasks/list')['tasks']
assert stats['pending'] == 0, "有pending残留"
assert stats['claimed'] == 0, "有claimed未完成"
assert stats['completed'] == len(TASKS), "完成数不符"
assert results['domain_violation'] == 0, "存在越域认领!"
assert results['domain_ok'] == len(TASKS), "域正确率非100%"
print(f"[6] 断言全部通过 ✅ pending=0 claimed=0 completed={stats['completed']} 域正确率=100%")
rep = {"version":"JOINT-SIM-V1","tasks":len(TASKS),"workers":len(WORKER_DOMAINS),
    "routed_domains":dict(Counter(r['domain'] for r in routed)),
    "completed":results['completed'],"domain_ok":results['domain_ok'],
    "domain_violation":0,"assertions":"ALL_PASSED"}
json.dump(rep, open('/home/user/Doubao/chats/38436747020400130/joint_simulation_result.json','w'), ensure_ascii=False, indent=1)
print(f"[7] 报告已写入 joint_simulation_result.json")
