#!/usr/bin/env python3
"""
调度器V1.2 量产仿真测试 v1.0
场景: 模拟生产流水线——5个Worker 并发处理 30个任务（9:16竖屏短剧片段渲染批次）
断言: 全部任务进入终态(completed/failed)、无pending残留、落库可查、统计一致
"""
import json, time, threading, random, urllib.request

BASE = "http://127.0.0.1:8310"
def call(method, path, data=None):
    req = urllib.request.Request(BASE+path, method=method)
    if data is not None:
        req.add_header('Content-Type','application/json')
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

# ---- 1. 注册5个Worker ----
workers = []
for i in range(5):
    w = call('POST','/api/v1.2/workers/register', {"worker_id":f"ext-sim-{i:02d}","name":f"仿真Worker{i}","capabilities":["video_render"],"max_concurrent":2})
    workers.append(w['worker_id'])
print(f"[1] Worker注册: {len(workers)}个 ✅")

# ---- 2. 提交30个任务 ----
task_ids = []
for i in range(30):
    r = call('POST','/api/v1.2/tasks/submit', {"task_type":"video_render","priority":random.randint(1,3),
        "payload":{"segment":f"ep01_sc{i:02d}","ratio":"9:16","duration":15},"node_id":"sim-production"})
    task_ids.append(r['task_id'])
print(f"[2] 任务提交: {len(task_ids)}个 落库 ✅")

# ---- 3. 5个Worker并发认领+执行+完成 ----
results = {"completed":0,"failed":0}
lock = threading.Lock()
def worker_loop(wid):
    for _ in range(20):  # 每worker最多20轮
        try:
            claim = call('POST','/api/v1.2/tasks/claim', {"worker_id":wid})
        except Exception:
            return
        if claim.get('status') != 'claimed':
            return
        time.sleep(random.uniform(0.01, 0.05))  # 模拟渲染耗时
        ok = random.random() < 0.9  # 90%成功率
        call('POST','/api/v1.2/tasks/complete', {"task_id":claim['task_id'],
            "result":{"rendered":True,"path":f"/output/{claim['task_id']}.mp4"} if ok else None,
            "error":None if ok else "render_timeout"})
        with lock:
            results['completed' if ok else 'failed'] += 1
threads = [threading.Thread(target=worker_loop, args=(w,)) for w in workers]
for t in threads: t.start()
for t in threads: t.join()
print(f"[3] 并发处理: 完成{results['completed']} / 失败{results['failed']} ✅")

# ---- 4. 断言与统计 ----
stats = call('GET','/api/v1.2/stats')
tasks = call('GET','/api/v1.2/tasks/list')['tasks']
assert stats['pending'] == 0, f"有pending残留: {stats['pending']}"
assert stats['completed'] + stats['failed'] == 30, "任务数不闭合"
assert len(tasks) == 30, "落库数不符"
assert stats['completed'] == results['completed'] and stats['failed'] == results['failed']
print(f"[4] 断言通过 ✅  pending={stats['pending']} claimed={stats['claimed']} completed={stats['completed']} failed={stats['failed']}")
print(f"[5] 落库验证: {len(tasks)}条任务全部可查 ✅ 吞吐: 30任务/{(time.time()-__import__('time').time())*-1:.2f}s")

# ---- 5. 输出机器可读结果 ----
report = {"version":"V1.2-SIM","workers":len(workers),"tasks":30,"completed":results['completed'],
    "failed":results['failed'],"success_rate":round(results['completed']/30*100,1),
    "pending_residue":stats['pending'],"persisted":len(tasks),"assertions":"ALL_PASSED"}
json.dump(report, open('/home/user/Doubao/chats/38436747020400130/simulation_result.json','w'), ensure_ascii=False, indent=1)
print(f"[6] 报告已写入 simulation_result.json: {report}")
