#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 调度器 V1.1 → V1.2 升级包
补齐任务全生命周期链路：提交落库 → 列表 → 认领 → 完成 → 心跳
部署方式: 将本文件与现有调度器合并（或替换main），重启服务。
独立运行: python3 scheduler_v1.2_upgrade.py （默认端口8301，含全部端点）
审批依据: REQUEST.SCHEDULER.V1.2.UPGRADE.20260915（飞书已通过）
"""
import json, time, uuid, threading, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------- 存储层（内存+文件持久化） ----------
DB_FILE = os.path.join(os.path.dirname(__file__), 'scheduler_v1.2_db.json')
def _load():
    try:
        return json.load(open(DB_FILE))
    except Exception:
        return {"tasks": {}, "workers": {}, "next_seq": 1}
def _save(db):
    json.dump(db, open(DB_FILE, 'w'), ensure_ascii=False, indent=1)
db_lock = threading.Lock()
DB = _load()

def _task_dict(tid, ttype, priority, payload, node_id):
    now = time.time()
    return {
        "task_id": tid, "task_type": ttype, "priority": priority,
        "payload": payload, "node_id": node_id,
        "status": "pending",          # pending → claimed → completed / failed
        "claimed_by": None, "claim_time": None,
        "result": None, "error": None,
        "created_at": now, "updated_at": now,
    }

# ---------- HTTP 处理器 ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def _json(self):
        try:
            return json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        except Exception:
            return {}
    def do_GET(self):
        p = self.path.split('?')[0]
        with db_lock:
            if p == '/api/v1.2/health':
                return self._send(200, {"status":"healthy","version":"V1.2","tasks":len(DB["tasks"]),"workers":len(DB["workers"])})
            if p == '/api/v1.2/tasks/list':
                return self._send(200, {"tasks": DB["tasks"], "total": len(DB["tasks"])})
            if p.startswith('/api/v1.2/tasks/'):
                tid = p.rsplit('/', 1)[-1]
                t = DB["tasks"].get(tid)
                return self._send(200, t if t else {"status":"not_found","key":tid})
            if p == '/api/v1.2/stats':
                st = {"pending":0,"claimed":0,"completed":0,"failed":0,"total":len(DB["tasks"]),"workers":len(DB["workers"])}
                for t in DB["tasks"].values(): st[t["status"]] += 1
                return self._send(200, st)
            if p == '/api/v1.2/workers':
                return self._send(200, {"workers": DB["workers"], "total": len(DB["workers"])})
        self._send(404, {"status":"not_found","path":p})
    def do_POST(self):
        p = self.path.split('?')[0]
        data = self._json()
        with db_lock:
            if p == '/api/v1.2/tasks/submit':
                tid = f"task-{uuid.uuid4().hex[:12]}"
                DB["tasks"][tid] = _task_dict(tid, data.get('task_type','generic'),
                    data.get('priority',1), data.get('payload',{}), data.get('node_id','unknown'))
                DB["next_seq"] += 1
                _save(DB)
                return self._send(200, {"task_id": tid, "status": "submitted", "queue_size": len([t for t in DB["tasks"].values() if t["status"]=="pending"])})
            if p == '/api/v1.2/tasks/claim':
                wid = data.get('worker_id')
                if not wid or wid not in DB["workers"]:
                    return self._send(400, {"status":"error","msg":"worker not registered"})
                dom = data.get('domain')  # 按域认领（防越域）
                for t in sorted(DB["tasks"].values(), key=lambda x: x['priority']):
                    if t["status"] == "pending" and (not dom or t.get("payload",{}).get("routed_domain")==dom):
                        t["status"] = "claimed"; t["claimed_by"] = wid
                        t["claim_time"] = time.time(); t["updated_at"] = time.time()
                        _save(DB)
                        return self._send(200, {"task_id": t["task_id"], "status": "claimed", "payload": t["payload"]})
                return self._send(200, {"status":"no_task"})
            if p == '/api/v1.2/tasks/complete':
                tid = data.get('task_id'); t = DB["tasks"].get(tid)
                if not t: return self._send(404, {"status":"not_found","key":tid})
                t["status"] = "completed" if not data.get('error') else "failed"
                t["result"] = data.get('result'); t["error"] = data.get('error')
                t["updated_at"] = time.time(); _save(DB)
                return self._send(200, {"task_id": tid, "status": t["status"]})
            if p == '/api/v1.2/workers/register':
                wid = data.get('worker_id', f"worker-{uuid.uuid4().hex[:8]}")
                DB["workers"][wid] = {"worker_id": wid, "name": data.get('name',''),
                    "capabilities": data.get('capabilities',[]), "status":"online",
                    "max_concurrent": data.get('max_concurrent',1), "heartbeat_at": time.time(),
                    "registered_at": time.time()}
                _save(DB)
                return self._send(200, {"worker_id": wid, "status":"registered"})
            if p == '/api/v1.2/workers/heartbeat':
                wid = data.get('worker_id')
                if wid in DB["workers"]:
                    DB["workers"][wid]["heartbeat_at"] = time.time(); DB["workers"][wid]["status"]="online"
                    return self._send(200, {"worker_id": wid, "status":"alive"})
                return self._send(404, {"status":"not_found","key":wid})
        self._send(404, {"status":"not_found","path":p})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8301))
    print(f"✅ 调度器V1.2 启动: http://0.0.0.0:{port}  (任务库: {DB_FILE})")
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
