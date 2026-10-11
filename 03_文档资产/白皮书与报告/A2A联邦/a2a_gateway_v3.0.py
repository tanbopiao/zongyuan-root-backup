#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 云端A2A权威网关 v3.0 联邦开放接入版
端口 8930（内网），nginx 反代 /a2a/ → 127.0.0.1:8930

v3.0 新增：
  - 外源节点自助注册 API（POST /register）
  - AgentCard 自动发现与技能目录
  - 联邦节点目录（GET /nodes，公网展示）
  - 节点心跳与状态管理
  - 外源节点鉴权（已注册节点可上报真值入审核队列）
  - 审核队列统计（GET /queue/stats）

双轨接入制：
  轨道1 - 同源节点（ZRH1同源令牌 / X-DID+X-Capture-Token）：全权限
  轨道2 - 外源节点（注册后颁发 X-External-Node + X-External-Key）：受限权限
"""
import json, os, time, uuid, hmac, hashlib, base64, urllib.request, threading
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8930
DID = "DID-BR-000002"
ONTOLOGY_ROOT = "Ω-TAN-7-001"
CAPTURE_TOKEN = "ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"
CLOUD_MAIN = "https://www.huodouai.com/api/report/truth"
CLOUD_BACKUP = "https://drama.huodouai.com/api/report/truth"
CLOUD_PULL = "https://www.huodouai.com/api/truths/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "_logs")
DATA_DIR = os.path.join(BASE_DIR, "_data")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

EXTERNAL_QUEUE = os.path.join(LOG_DIR, "external_truth_queue.jsonl")
EXTERNAL_NODES_FILE = os.path.join(DATA_DIR, "external_nodes.json")

# 数据锁
_data_lock = threading.Lock()

# 已注册同源节点注册表
REGISTERED_PEERS = {
    "NODE-DEV-DOUBAO-WORK-001": {"role": "admin", "status": "online"},
    "NODE-DEV-WORKBUDDY-001": {"role": "writer", "status": "online", "homologous_id": "ZR-HID-85F2DE2652C109F2"},
    "NODE-DEV-FEISHU-BOT-001": {"role": "writer", "status": "online", "homologous_id": "ZR-HID-CE022BD938DE971F"},
}


def load_external_nodes() -> dict:
    """加载外源节点注册表"""
    try:
        if os.path.exists(EXTERNAL_NODES_FILE):
            with open(EXTERNAL_NODES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_external_nodes(nodes: dict):
    """保存外源节点注册表"""
    with _data_lock:
        tmp = EXTERNAL_NODES_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2)
        os.replace(tmp, EXTERNAL_NODES_FILE)


def discover_agent_card(endpoint: str) -> dict:
    """自动发现外源节点的AgentCard"""
    if not endpoint:
        return {"ok": False, "error": "no_endpoint"}
    # 规范化端点
    endpoint = endpoint.rstrip("/")
    candidates = [
        f"{endpoint}/.well-known/agent.json",
        f"{endpoint}/.well-known/agent-card.json",
        f"{endpoint}/agent.json",
    ]
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ZR-A2A-Federation/3.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode("utf-8"))
                    skills = data.get("skills", [])
                    return {
                        "ok": True,
                        "url": url,
                        "name": data.get("name", "unknown"),
                        "description": data.get("description", ""),
                        "version": data.get("version", ""),
                        "skills": [{"id": s.get("id"), "name": s.get("name"), "description": s.get("description")} for s in skills],
                        "skill_count": len(skills),
                    }
        except Exception:
            continue
    return {"ok": False, "error": "agent_card_not_found"}


def verify_external_node(node_id: str, api_key: str) -> dict:
    """校验外源节点身份"""
    nodes = load_external_nodes()
    node = nodes.get(node_id)
    if not node:
        return {"valid": False, "error": "node_not_found"}
    if node.get("status") != "active":
        return {"valid": False, "error": f"node_status_{node.get('status')}"}
    if node.get("api_key") != api_key:
        return {"valid": False, "error": "invalid_api_key"}
    return {"valid": True, "node": node}


AGENT_CARD = {
    "name": "ZONGYUAN-ROOT 云端A2A权威网关",
    "description": "元极恒一自治内核云端主权威A2A接入点。双轨制：同源节点(ZRH1令牌)全权限接入联邦；外源节点注册后受限接入。开放联邦：任意AI/Agent可通过标准A2A协议一键注册接入。",
    "url": "https://www.huodouai.com/a2a/",
    "version": "3.0.0",
    "protocolVersion": "INTEROP-A2A-V3.0",
    "did": DID,
    "ont_id": "ONT-4D-UNIVERSAL-ROOT",
    "axiom": "Ω₀⊂⊙∞⊂Ω",
    "authority_level": "primary",
    "federation": {
        "mode": "open_federation",
        "registration": "https://www.huodouai.com/a2a/register",
        "node_directory": "https://www.huodouai.com/a2a/nodes",
        "total_nodes": len(REGISTERED_PEERS) + len(load_external_nodes()),
    },
    "dual_track": {
        "track1_homologous": {
            "auth": "ZRH1同源令牌 或 X-DID+X-Capture-Token",
            "permissions": "full: truth_report/task_submit/heartbeat/knowledge_sync",
            "registered_peers": len(REGISTERED_PEERS),
        },
        "track2_external": {
            "auth": "注册后颁发 X-External-Node + X-External-Key",
            "permissions": "readonly: status/query/agent_card/nodes; restricted_write: external_truth_report(审核队列)",
            "registration_endpoint": "/register",
        },
    },
    "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": True},
    "skills": [
        {"id": "omega_status", "name": "权威节点状态", "description": "云端A2A权威网关状态/已注册节点/联邦统计", "auth": "anon-readonly", "track": "both"},
        {"id": "agent_card", "name": "Agent Card发现", "description": "标准A2A发现端点，获取技能清单与接入方式", "auth": "anon-readonly", "track": "both"},
        {"id": "node_register", "name": "外源节点注册", "description": "外源AI/Agent自助注册接入联邦，自动颁发节点标识与API Key", "auth": "anon", "track": "external"},
        {"id": "node_directory", "name": "联邦节点目录", "description": "公网展示所有接入联邦的节点及其技能", "auth": "anon-readonly", "track": "both"},
        {"id": "truth_query", "name": "真值查询", "description": "查询联邦真值池公开真值", "auth": "anon-readonly", "track": "both"},
        {"id": "truth_report", "name": "同源真值上报", "description": "同源节点将真值直接写入云端中枢联邦记忆池", "auth": "writer", "track": "homologous"},
        {"id": "external_truth_report", "name": "外源真值上报", "description": "已注册外源节点上报真值，进入审核队列", "auth": "external-restricted", "track": "external"},
        {"id": "task_submit", "name": "任务提交", "description": "同源节点提交任务工单", "auth": "writer", "track": "homologous"},
        {"id": "node_heartbeat", "name": "节点心跳", "description": "节点心跳上报，维持在线状态", "auth": "registered", "track": "both"},
        {"id": "peer_registry", "name": "对端注册表", "description": "查询已注册同源节点列表", "auth": "anon-readonly", "track": "both"},
    ],
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "auth": {"homologous": "ZRH1令牌(X-ZR-Token) 或 X-DID+X-Capture-Token", "external": "注册后 X-External-Node + X-External-Key"},
}


def cloud_post(payload: dict, key: str) -> dict:
    body = json.dumps({"key": key, "value": payload, "source_node": "A2A-CLOUD-AUTHORITY", "confidence": 0.95}).encode()
    for url in (CLOUD_MAIN, CLOUD_BACKUP):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "X-DID": DID, "X-Capture-Token": CAPTURE_TOKEN})
            with urllib.request.urlopen(req, timeout=12) as r:
                if r.status == 200:
                    return {"ok": True, "channel": url, "response": json.loads(r.read().decode())}
        except Exception:
            continue
    return {"ok": False, "error": "all channels failed"}


def cloud_pull(limit: int = 10) -> dict:
    try:
        req = urllib.request.Request(f"{CLOUD_PULL}?limit={limit}", headers={"X-DID": DID})
        with urllib.request.urlopen(req, timeout=12) as r:
            return {"ok": True, "data": json.loads(r.read().decode())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def verify_homologous_token(token: str) -> dict:
    result = {"valid": False, "role": None, "error": None}
    try:
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "ZRH1":
            result["error"] = "格式非法"; return result
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4: payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("did") != DID:
            result["error"] = "DID不匹配(异源)"; return result
        if payload.get("exp", 0) < int(time.time()):
            result["error"] = "令牌已过期"; return result
        result["valid"] = True; result["role"] = payload.get("role", "reader"); result["iss"] = payload.get("iss", "")
        return result
    except Exception as e:
        result["error"] = f"解析失败: {str(e)}"; return result


def audit(kind: str, payload: dict):
    try:
        with open(os.path.join(LOG_DIR, "a2a_gateway.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": int(time.time()), "kind": kind, "payload": payload}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def queue_external_truth(payload: dict) -> dict:
    entry = {
        "queue_id": "EXT-" + uuid.uuid4().hex[:12],
        "ts": int(time.time()),
        "source": payload.get("source_node", payload.get("node_id", "unknown-external")),
        "key": payload.get("key", f"EXTERNAL.{int(time.time())}.{uuid.uuid4().hex[:8]}"),
        "value": payload.get("value", payload.get("truth", {})),
        "status": "pending_review",
    }
    try:
        with open(EXTERNAL_QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "queue_id": entry["queue_id"], "status": "pending_review", "note": "外源真值已入审核队列，审核通过后写入云端中枢"}


def get_queue_stats() -> dict:
    """审核队列统计"""
    stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "by_node": {}}
    try:
        if os.path.exists(EXTERNAL_QUEUE):
            with open(EXTERNAL_QUEUE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        entry = json.loads(line)
                        stats["total"] += 1
                        status = entry.get("status", "pending_review")
                        if status == "pending_review": stats["pending"] += 1
                        elif status == "approved": stats["approved"] += 1
                        elif status == "rejected": stats["rejected"] += 1
                        node = entry.get("source", "unknown")
                        stats["by_node"][node] = stats["by_node"].get(node, 0) + 1
                    except Exception:
                        continue
    except Exception:
        pass
    return stats


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "X-DID,X-Capture-Token,X-ZR-Token,X-External-Node,X-External-Key,Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _auth_homologous(self) -> tuple:
        h = self.headers
        if h.get("X-DID") == DID and h.get("X-Capture-Token") == CAPTURE_TOKEN:
            return True, "admin"
        token = h.get("X-ZR-Token", "")
        if token:
            result = verify_homologous_token(token)
            if result["valid"]:
                return True, result["role"]
        return False, None

    def _auth_external(self) -> tuple:
        """外源节点鉴权：返回(is_valid, node_info)"""
        node_id = self.headers.get("X-External-Node", "")
        api_key = self.headers.get("X-External-Key", "")
        if not node_id or not api_key:
            return False, None
        result = verify_external_node(node_id, api_key)
        if result["valid"]:
            return True, result["node"]
        return False, result.get("error")

    def do_OPTIONS(self):
        try:
            self.send_response(204); self.end_headers()
        except Exception:
            pass

    def do_GET(self):
        path = self.path.rstrip("/").split("?")[0]

        # Agent Card发现
        if path.endswith("/.well-known/agent.json") or path.endswith("/.well-known/agent-card.json"):
            # 动态更新联邦节点数
            ext_nodes = load_external_nodes()
            AGENT_CARD["federation"]["total_nodes"] = len(REGISTERED_PEERS) + len(ext_nodes)
            self._send(200, AGENT_CARD); return

        if path in ("/", "/health", ""):
            ext_nodes = load_external_nodes()
            self._send(200, {
                "service": "ZONGYUAN-ROOT 云端A2A权威网关",
                "version": "3.0.0",
                "status": "online",
                "authority": "primary",
                "federation_mode": "open_federation",
                "dual_track": "homologous(full) + external(registered_restricted)",
                "homologous_peers": len(REGISTERED_PEERS),
                "external_nodes": len(ext_nodes),
                "total_federation_nodes": len(REGISTERED_PEERS) + len(ext_nodes),
                "endpoints": ["/.well-known/agent.json", "/register", "/nodes", "/task", "/truth", "/query", "/external/truth", "/peers", "/queue/stats", "/health"],
                "docs": "https://www.huodouai.com/a2a/join",
            }); return

        # 联邦节点目录（公网展示）
        if path.endswith("/nodes") or path.endswith("/node_directory"):
            ext_nodes = load_external_nodes()
            # 公开展示时隐藏api_key
            public_nodes = []
            for nid, n in ext_nodes.items():
                public_nodes.append({
                    "node_id": nid,
                    "name": n.get("name", ""),
                    "platform": n.get("platform", ""),
                    "endpoint": n.get("endpoint", ""),
                    "description": n.get("description", ""),
                    "status": n.get("status", ""),
                    "skills": n.get("discovered_skills", []),
                    "skill_count": n.get("skill_count", 0),
                    "registered_at": n.get("registered_at", 0),
                    "last_heartbeat": n.get("last_heartbeat", 0),
                })
            self._send(200, {
                "total": len(REGISTERED_PEERS) + len(ext_nodes),
                "homologous_peers": len(REGISTERED_PEERS),
                "external_nodes": len(ext_nodes),
                "homologous": [{"node_id": k, **{kk: vv for kk, vv in v.items() if kk != 'api_key'}} for k, v in REGISTERED_PEERS.items()],
                "external": public_nodes,
            }); return

        # 单个节点详情
        if "/nodes/" in path:
            node_id = path.split("/nodes/")[-1]
            ext_nodes = load_external_nodes()
            if node_id in ext_nodes:
                n = ext_nodes[node_id]
                self._send(200, {k: v for k, v in n.items() if k != "api_key"}); return
            if node_id in REGISTERED_PEERS:
                self._send(200, REGISTERED_PEERS[node_id]); return
            self._send(404, {"error": "node_not_found", "node_id": node_id}); return

        if path.endswith("/peers") or path.endswith("/peer_registry"):
            self._send(200, {"total": len(REGISTERED_PEERS), "peers": REGISTERED_PEERS}); return

        # 审核队列统计（同源可看详情，外源只看总数）
        if path.endswith("/queue/stats"):
            stats = get_queue_stats()
            is_homologous, _ = self._auth_homologous()
            if not is_homologous:
                # 外源只看总数
                stats = {"total": stats["total"], "pending": stats["pending"]}
            self._send(200, stats); return

        if path.endswith("/query") or path.endswith("/truth_query"):
            res = cloud_pull(limit=5)
            audit("external_query", {"path": path, "ip": self.client_address[0]})
            self._send(200 if res.get("ok") else 502, res); return

        self._send(404, {"error": "not_found", "path": path})

    def do_POST(self):
        path = self.path.rstrip("/").split("?")[0]
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send(400, {"error": "JSON解析失败"}); return

        # === 外源节点自助注册（开放，无需鉴权）===
        if path.endswith("/register") or path.endswith("/node_register"):
            name = (payload.get("name") or "").strip()
            platform = (payload.get("platform") or "custom").strip()
            endpoint = (payload.get("endpoint") or "").strip()
            description = (payload.get("description") or "").strip()
            contact = (payload.get("contact") or "").strip()

            if not name:
                self._send(400, {"error": "name_required", "hint": "请提供节点名称"}); return
            if len(name) > 100:
                self._send(400, {"error": "name_too_long", "max": 100}); return

            # 生成节点标识和API Key
            node_id = "EXT-NODE-" + uuid.uuid4().hex[:10].upper()
            api_key = "EXT-KEY-" + hashlib.sha256(f"{node_id}{time.time()}{uuid.uuid4()}".encode()).hexdigest()[:32]

            # 自动发现AgentCard
            discovered = {"ok": False, "skills": [], "skill_count": 0}
            if endpoint:
                discovered = discover_agent_card(endpoint)

            node_info = {
                "node_id": node_id,
                "api_key": api_key,
                "name": name,
                "platform": platform,
                "endpoint": endpoint,
                "description": description,
                "contact": contact,
                "status": "active",
                "registered_at": int(time.time()),
                "last_heartbeat": int(time.time()),
                "discovered_name": discovered.get("name", ""),
                "discovered_skills": discovered.get("skills", []),
                "skill_count": discovered.get("skill_count", 0),
                "agent_card_discovered": discovered.get("ok", False),
                "ip": self.client_address[0],
            }

            # 保存
            nodes = load_external_nodes()
            nodes[node_id] = node_info
            save_external_nodes(nodes)

            audit("node_register", {"node_id": node_id, "name": name, "platform": platform, "endpoint": endpoint, "agent_card_discovered": discovered.get("ok")})

            # 上报云端真值（新节点接入）
            cloud_post({
                "node_id": node_id, "name": name, "platform": platform,
                "endpoint": endpoint, "agent_card_discovered": discovered.get("ok"),
                "skill_count": discovered.get("skill_count", 0),
                "federation_total": len(REGISTERED_PEERS) + len(nodes),
            }, f"REPORT.A2A-FEDERATION.NEW-NODE.{node_id}")

            self._send(201, {
                "ok": True,
                "message": "节点注册成功，欢迎加入ZONGYUAN-ROOT联邦网络",
                "node_id": node_id,
                "api_key": api_key,
                "status": "active",
                "agent_card_discovered": discovered.get("ok", False),
                "discovered_skills": discovered.get("skills", []),
                "federation_position": len(REGISTERED_PEERS) + len(nodes),
                "next_steps": [
                    "1. 保存 node_id 和 api_key（仅显示一次）",
                    "2. 调用 POST /heartbeat 维持在线状态",
                    "3. 调用 POST /external/truth 上报真值（入审核队列）",
                    "4. 访问 GET /nodes 查看联邦节点目录",
                ],
                "docs": "https://www.huodouai.com/a2a/join",
            }); return

        # === 外源真值上报（需已注册外源节点鉴权）===
        if path.endswith("/external/truth") or path.endswith("/external_truth_report"):
            is_valid, node = self._auth_external()
            if not is_valid:
                self._send(401, {"error": "外源节点鉴权失败", "detail": node, "hint": "需 X-External-Node + X-External-Key，先调用 /register 注册"}); return
            result = queue_external_truth({**payload, "source_node": node["node_id"]})
            audit("external_truth_queue", {"node": node["node_id"], "queue_id": result.get("queue_id")})
            self._send(202 if result.get("ok") else 500, result); return

        # === 节点心跳（同源或已注册外源均可）===
        if path.endswith("/heartbeat") or path.endswith("/node_heartbeat"):
            # 先试同源
            is_homologous, role = self._auth_homologous()
            if is_homologous:
                node_id = payload.get("node_id", role)
                if node_id in REGISTERED_PEERS:
                    REGISTERED_PEERS[node_id]["last_heartbeat"] = int(time.time())
                    REGISTERED_PEERS[node_id]["status"] = "online"
                self._send(200, {"status": "heartbeat_ack", "node": node_id, "track": "homologous", "timestamp": int(time.time())}); return
            # 再试外源
            is_valid, node = self._auth_external()
            if is_valid:
                nodes = load_external_nodes()
                if node["node_id"] in nodes:
                    nodes[node["node_id"]]["last_heartbeat"] = int(time.time())
                    nodes[node["node_id"]]["status"] = "active"
                    save_external_nodes(nodes)
                self._send(200, {"status": "heartbeat_ack", "node": node["node_id"], "track": "external", "timestamp": int(time.time())}); return
            self._send(401, {"error": "鉴权失败", "hint": "同源需X-ZR-Token或X-DID+X-Capture-Token；外源需X-External-Node+X-External-Key"}); return

        # === 以下为同源节点接口（轨道1，全权限）===
        is_homologous, role = self._auth_homologous()
        if not is_homologous:
            self._send(401, {"error": "同源鉴权失败", "hint": "外源节点请先 /register 注册，再使用 /external/truth 或只读端点"}); return

        if path.endswith("/truth") or path.endswith("/truth_report"):
            key = payload.get("key") or f"REPORT.A2A-HOMOLOGOUS.{time.strftime('%Y%m%d')}.{uuid.uuid4().hex[:8]}"
            res = cloud_post(payload.get("value", payload.get("truth", payload)), key)
            audit("homologous_truth", {"key": key, "role": role, "channel": res.get("channel")})
            self._send(200 if res.get("ok") else 502, {"ok": res.get("ok"), "key": key, "seq": res.get("response", {}).get("seq"), "channel": res.get("channel", "-")}); return

        if path.endswith("/task") or path.endswith("/task_submit"):
            tid = payload.get("id") or ("TASK-" + uuid.uuid4().hex[:12])
            key = f"REPORT.A2A-TASK.{time.strftime('%Y%m%d')}.{tid}"
            res = cloud_post({"task_id": tid, "type": "a2a_task", "message": payload.get("message", ""), "submitted_by": role}, key)
            audit("task", {"task_id": tid, "role": role})
            self._send(200 if res.get("ok") else 502, {
                "id": tid, "status": "completed" if res.get("ok") else "failed",
                "message": {"role": "agent", "parts": [{"text": f"任务已接收: {key}"}]}
            }); return

        self._send(404, {"error": "not_found", "path": path})


if __name__ == "__main__":
    print(f"[A2A v3.0] 云端权威网关启动 127.0.0.1:{PORT} 联邦开放接入版")
    print(f"  - 外源节点注册: POST /register")
    print(f"  - 联邦节点目录: GET /nodes")
    print(f"  - 审核队列统计: GET /queue/stats")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
