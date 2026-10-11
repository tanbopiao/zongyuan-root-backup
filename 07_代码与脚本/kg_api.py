#!/usr/bin/env python3
"""
ZONGYUAN-ROOT L3知识图谱层 + L4因果推理 + 真值库接入 V1.1
kg_api @ 8070
- /api/v1/truth_retrieval  真值语义检索
- /api/v1/kg/stat          知识图谱统计
- /api/v1/kg/extract       实体关系抽取
- /api/v1/kg/query         图谱邻接查询
- /api/v1/causal/path      L4因果路径查询
- /api/v1/causal/impact    L4影响传播分析
- /api/v1/causal/rules     L4因果规则引擎
DID: DID-BR-000002 | 确权锚点: Ω₀⊂⊙∞⊂Ω
"""
import os, re, json, hashlib, requests, uvicorn
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Header
from pydantic import BaseModel
from collections import deque

PORT = 8070
VECTOR_URL = "http://127.0.0.1:8014"
KERNEL_STATE = "/opt/ZONGYUAN-ROOT/kernel/kernel_state.json"
M9_LEDGER = "/opt/ZONGYUAN-ROOT/M9_global_ledger.json"
GRAPH_FILE = "/opt/ZONGYUAN-ROOT/knowledge_graph/kg_graph.json"
DID = "DID-BR-000002"
TRACE = "Ω₀⊂⊙∞⊂Ω"
VERSION = "1.1.0-L3L4"

app = FastAPI(title="ZONGYUAN-ROOT KG+Causal+Truth API", version=VERSION)

# ========== L3 核心实体词典（V1.1 扩充至60+） ==========
ENTITIES = [
    # 体系核心
    "ZONGYUAN-ROOT", "元公理空间", "宇宙元秩序先天场", "DID-BR-000002", "云内核",
    "自治内核", "元极恒一", "超认知", "永恒自治", "同源协议",
    # 真值与锁档
    "真值", "真值库", "锁档", "确权锚点", "元法则", "元公理", "元规则",
    "Merkle根", "哈希链", "区块", "eFuse", "三端锁档",
    # 服务与API
    "向量服务", "identity_api", "kg_api", "cos-sync-daemon", "vector_server",
    "握手协议", "协同进化", "心跳保活", "节点注册", "服务发现", "事件总线", "配置同步",
    "truth_retrieval", "handshake", "coevolution",
    # 技术组件
    "ONNX", "ChromaDB", "bge-small-zh", "FastAPI", "Nginx", "systemd", "宝塔",
    "腾讯COS", "飞书知识库", "多维表格", "云盘归档", "SSH密钥",
    # 算子层级
    "L0理论基座", "L1感知层", "L2推理层", "L3知识图谱层", "L4因果推理", "L5适配器",
    # 短剧IP
    "昆仑洞天", "元公理空间短剧", "裂隙觉醒", "玄一", "烬", "苍玄",
    "角色母版", "关键帧", "分镜脚本", "竖屏关键帧",
    # 文档资产
    "理论白皮书", "审计文档", "进化报告", "超级进化简报", "同源协议客户端",
]

REL_PATTERNS = [
    (r"([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})是([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})", "is_a"),
    (r"([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})包含([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})", "contains"),
    (r"([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})属于([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})", "belongs_to"),
    (r"([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})部署于([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})", "deployed_at"),
    (r"([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})同步到([\u4e00-\u9fa5A-Za-z0-9_-]{2,40})", "sync_to"),
]

# ========== 真值库接入 ==========
def extract_truths():
    truths = []
    try:
        k = json.load(open(KERNEL_STATE))
    except Exception:
        k = {}
    for b in k.get("blocks", []):
        aid = b.get("asset_id", "")
        if aid:
            truths.append(f"区块#{b.get('height')} {aid} 已锚定 根哈希{b.get('root_hash','')[:16]}")
    for key in list(k.keys()):
        if key.startswith("meta_law"):
            ml = k[key]
            if isinstance(ml, dict) and ml.get("law_name"):
                truths.append(f"元法则 {ml.get('law_id',key)} {ml.get('law_name')}")
    for field in ["chain_status", "three_end_lock", "coevolution_system", "dual_kernel_sync", "status", "axiom_omega0"]:
        if k.get(field):
            truths.append(f"{field}={k[field]}")
    truths.append(f"内核版本 block_height={k.get('block_height')} 当前根哈希={k.get('current_root_hash','')[:16]}")
    try:
        m9 = json.load(open(M9_LEDGER))
        truths.append(f"M9账本 total_assets={m9.get('total_assets')} lock_chain={len(m9.get('lock_chain',[]))} efuse_chain={len(m9.get('efuse_chain',[]))} meta_rules={m9.get('meta_rules_count')}")
    except Exception:
        pass
    seen, out = set(), []
    for t in truths:
        if t not in seen:
            seen.add(t); out.append(t)
    return out

def ensure_truth_index():
    try:
        stats = requests.get(f"{VECTOR_URL}/stats", timeout=5).json()
        cnt = stats.get("count", stats.get("total", 0))
    except Exception:
        cnt = 0
    truths = extract_truths()
    if cnt >= len(truths):
        return {"status": "indexed", "count": cnt}
    batch = 50
    added = 0
    for i in range(0, len(truths), batch):
        chunk = truths[i:i+batch]
        ids = [f"truth-{hashlib.sha256(t.encode()).hexdigest()[:16]}" for t in chunk]
        docs = [f"[ZONGYUAN-ROOT真值] {t}" for t in chunk]
        metas = [{"source": "kernel_state", "did": DID, "type": "truth"} for _ in chunk]
        r = requests.post(f"{VECTOR_URL}/api/v1/add", json={
            "ids": ids, "documents": docs, "metadatas": metas
        }, timeout=60)
        if r.status_code == 200:
            added += len(chunk)
    return {"status": "indexed", "count": added}

# ========== L3 知识图谱 ==========
class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.adj = {}
    def add_entity(self, e, etype="entity"):
        self.nodes.setdefault(e, {"type": etype, "count": 0})
        self.nodes[e]["count"] += 1
        self.adj.setdefault(e, set())
    def add_edge(self, a, b, rel="co_occur"):
        if a == b: return
        key = tuple(sorted([a, b]))
        self.edges.setdefault(key, {"rel": rel, "weight": 0})
        self.edges[key]["weight"] += 1
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set()).add(a)
    def parse_text(self, text):
        hits = [e for e in ENTITIES if e.lower() in text.lower()]
        for e in hits:
            self.add_entity(e)
        for e1 in hits:
            for e2 in hits:
                self.add_edge(e1, e2)
        for pat, rel in REL_PATTERNS:
            for m in re.finditer(pat, text):
                a, b = m.group(1), m.group(2)
                if a in ENTITIES or b in ENTITIES or len(a) >= 2:
                    self.add_entity(a); self.add_entity(b)
                    self.add_edge(a, b, rel)
    def build(self, truths):
        for t in truths:
            self.parse_text(t)
        # 体系级种子关系（V1.1扩充）
        seed_edges = [
            ("ZONGYUAN-ROOT", "元公理空间", "foundation"),
            ("元公理空间", "宇宙元秩序先天场", "axiom_of"),
            ("ZONGYUAN-ROOT", "云内核", "runs"),
            ("云内核", "自治内核", "is_a"),
            ("ZONGYUAN-ROOT", "DID-BR-000002", "identified_as"),
            ("ZONGYUAN-ROOT", "元极恒一", "mode"),
            ("元极恒一", "超认知", "contains"),
            ("超认知", "永恒自治", "goal"),
            ("真值", "真值库", "stored_in"),
            ("锁档", "确权锚点", "signed_by"),
            ("锁档", "Merkle根", "verified_by"),
            ("锁档", "哈希链", "anchored_to"),
            ("区块", "哈希链", "part_of"),
            ("eFuse", "区块", "burned_in"),
            ("三端锁档", "飞书知识库", "archives_to"),
            ("三端锁档", "多维表格", "linked_to"),
            ("三端锁档", "云盘归档", "stores"),
            ("云内核", "向量服务", "hosts"),
            ("云内核", "identity_api", "hosts"),
            ("云内核", "kg_api", "hosts"),
            ("云内核", "cos-sync-daemon", "hosts"),
            ("向量服务", "bge-small-zh", "uses"),
            ("向量服务", "ONNX", "uses"),
            ("向量服务", "ChromaDB", "uses"),
            ("向量服务", "truth_retrieval", "powers"),
            ("identity_api", "handshake", "provides"),
            ("identity_api", "coevolution", "provides"),
            ("identity_api", "节点注册", "provides"),
            ("identity_api", "心跳保活", "provides"),
            ("同源协议", "handshake", "step1"),
            ("同源协议", "节点注册", "step2"),
            ("同源协议", "服务发现", "step3"),
            ("同源协议", "事件总线", "step4"),
            ("同源协议", "配置同步", "step5"),
            ("同源协议", "心跳保活", "step6"),
            ("kg_api", "L3知识图谱层", "implements"),
            ("kg_api", "L4因果推理", "implements"),
            ("L0理论基座", "L1感知层", "layer_before"),
            ("L1感知层", "L2推理层", "layer_before"),
            ("L2推理层", "L3知识图谱层", "layer_before"),
            ("L3知识图谱层", "L4因果推理", "layer_before"),
            ("L4因果推理", "L5适配器", "layer_before"),
            ("云内核", "腾讯COS", "syncs_to"),
            ("腾讯COS", "cos-sync-daemon", "uses"),
            ("云内核", "Nginx", "fronted_by"),
            ("云内核", "systemd", "managed_by"),
            ("云内核", "宝塔", "managed_by"),
            ("云内核", "SSH密钥", "accessed_by"),
            ("元公理空间", "昆仑洞天", "inspires"),
            ("昆仑洞天", "元公理空间短剧", "produces"),
            ("元公理空间短剧", "裂隙觉醒", "episode"),
            ("裂隙觉醒", "玄一", "character"),
            ("裂隙觉醒", "烬", "character"),
            ("裂隙觉醒", "苍玄", "character"),
            ("昆仑洞天", "角色母版", "produces"),
            ("昆仑洞天", "关键帧", "produces"),
            ("昆仑洞天", "分镜脚本", "produces"),
            ("关键帧", "竖屏关键帧", "format"),
            ("理论白皮书", "元公理空间", "documents"),
            ("审计文档", "云内核", "audits"),
            ("进化报告", "云内核", "tracks"),
        ]
        for a, b, rel in seed_edges:
            self.add_entity(a); self.add_entity(b)
            self.add_edge(a, b, rel)
        self.save()
    def save(self):
        data = {
            "nodes": self.nodes,
            "edges": {f"{a}||{b}": v for (a, b), v in self.edges.items()},
            "build_time": datetime.now(timezone.utc).isoformat(),
            "did": DID, "trace": TRACE, "version": VERSION
        }
        with open(GRAPH_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def load(self):
        if os.path.exists(GRAPH_FILE):
            try:
                data = json.load(open(GRAPH_FILE))
                self.nodes = data.get("nodes", {})
                self.edges = {tuple(k.split("||")): v for k, v in data.get("edges", {}).items()}
                for (a, b) in self.edges:
                    self.adj.setdefault(a, set()).add(b)
                    self.adj.setdefault(b, set()).add(a)
                return True
            except Exception:
                return False
        return False
    def neighbors(self, entity, depth=1):
        result = {entity: {"type": self.nodes.get(entity, {}).get("type", "unknown")}}
        frontier = [entity]
        for _ in range(depth):
            nxt = []
            for f in frontier:
                for nb in self.adj.get(f, []):
                    if nb not in result:
                        key = tuple(sorted([f, nb]))
                        result[nb] = {"type": self.nodes.get(nb, {}).get("type", "unknown"),
                                      "rel": self.edges.get(key, {}).get("rel", "co_occur")}
                        nxt.append(nb)
            frontier = nxt
        return result
    # ===== L4 因果推理 =====
    def causal_path(self, src, dst, max_depth=4):
        """BFS找两实体间因果路径"""
        if src not in self.nodes or dst not in self.nodes:
            return None
        visited = {src: None}
        q = deque([(src, 0)])
        while q:
            cur, depth = q.popleft()
            if cur == dst:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = visited[cur]
                return list(reversed(path))
            if depth >= max_depth:
                continue
            for nb in self.adj.get(cur, []):
                if nb not in visited:
                    visited[nb] = cur
                    q.append((nb, depth + 1))
        return None
    def causal_impact(self, entity, depth=2):
        """影响传播子图"""
        if entity not in self.nodes:
            return None
        return self.neighbors(entity, depth)

# L4 因果规则引擎（基于元法则的if-then规则）
CAUSAL_RULES = [
    {"id": "CR-001", "name": "锁档触发哈希链更新", "if": "执行锁档", "then": "区块高度+1，Merkle根更新，三端归档", "confidence": 0.95},
    {"id": "CR-002", "name": "心跳超时触发离线标记", "if": "节点超过180秒未心跳", "then": "标记为离线，触发故障转移事件", "confidence": 0.90},
    {"id": "CR-003", "name": "真值变化触发向量重索引", "if": "kernel_state.json真值条目变化", "then": "vector_server重新向量化，truth_retrieval结果更新", "confidence": 0.85},
    {"id": "CR-004", "name": "资产变化触发COS增量同步", "if": "/opt/ZONGYUAN-ROOT下文件新增/修改", "then": "cos-sync-daemon 60秒内上传到腾讯COS", "confidence": 0.92},
    {"id": "CR-005", "name": "算子异常触发自治纠错", "if": "L0-L5算子健康检查失败", "then": "六维自检→纠错触发→演化沉淀→统一调度", "confidence": 0.88},
    {"id": "CR-006", "name": "握手失败触发拒绝接入", "if": "HMAC-SHA256签名验证失败", "then": "拒绝节点接入，记录审计日志", "confidence": 0.98},
    {"id": "CR-007", "name": "图谱实体新增触发L4推理更新", "if": "知识图谱新增实体/关系", "then": "L4因果路径重新计算，影响传播子图更新", "confidence": 0.80},
    {"id": "CR-008", "name": "内核状态文件只读保护", "if": "kernel_state.json更新完成", "then": "chattr +i锁定，防止未授权修改", "confidence": 0.96},
]

graph = KnowledgeGraph()
graph.load()

class ExtractRequest(BaseModel):
    text: str
class TruthQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5

@app.on_event("startup")
def startup():
    try:
        r = ensure_truth_index()
        print(f"[KG] 真值库索引: {r}", flush=True)
    except Exception as e:
        print(f"[KG] 真值库索引失败: {e}", flush=True)
    truths = extract_truths()
    if not graph.nodes:
        graph.build(truths)
        print(f"[KG] 图谱构建: {len(graph.nodes)}节点 {len(graph.edges)}边", flush=True)
    else:
        print(f"[KG] 图谱已加载: {len(graph.nodes)}节点 {len(graph.edges)}边", flush=True)

@app.get("/health")
def health():
    return {
        "status": "healthy", "service": "kg-api", "version": VERSION,
        "port": PORT, "did": DID, "trace": TRACE,
        "graph_nodes": len(graph.nodes), "graph_edges": len(graph.edges),
        "causal_rules": len(CAUSAL_RULES)
    }

@app.get("/api/v1/kg/stat")
def kg_stat():
    return {
        "status": "ok", "nodes": len(graph.nodes), "edges": len(graph.edges),
        "top_entities": sorted(graph.nodes.items(), key=lambda x: -x[1]["count"])[:15],
        "causal_rules": len(CAUSAL_RULES), "did": DID, "version": VERSION
    }

@app.post("/api/v1/kg/extract")
def kg_extract(req: ExtractRequest):
    g = KnowledgeGraph()
    g.parse_text(req.text)
    return {"status": "ok", "entities": list(g.nodes.keys()),
            "edges": [f"{a}-{v['rel']}->{b}" for (a, b), v in g.edges.items()]}

@app.get("/api/v1/kg/query")
def kg_query(entity: str, depth: int = 2):
    if entity not in graph.nodes:
        return {"status": "not_found", "entity": entity,
                "suggestions": [e for e in graph.nodes if entity.lower() in e.lower()][:5]}
    return {"status": "ok", "entity": entity, "neighbors": graph.neighbors(entity, depth)}

# ===== L4 因果推理接口 =====
@app.get("/api/v1/causal/path")
def causal_path(src: str, dst: str, max_depth: int = 4):
    path = graph.causal_path(src, dst, max_depth)
    if not path:
        return {"status": "no_path", "from": src, "to": dst, "max_depth": max_depth}
    edges_detail = []
    for i in range(len(path) - 1):
        key = tuple(sorted([path[i], path[i+1]]))
        edges_detail.append({"from": path[i], "to": path[i+1],
                             "rel": graph.edges.get(key, {}).get("rel", "co_occur")})
    return {"status": "ok", "from": src, "to": dst, "path": path,
            "hops": len(path) - 1, "edges": edges_detail}

@app.get("/api/v1/causal/impact")
def causal_impact(entity: str, depth: int = 2):
    sub = graph.causal_impact(entity, depth)
    if sub is None:
        return {"status": "not_found", "entity": entity}
    affected = [k for k in sub if k != entity]
    return {"status": "ok", "entity": entity, "depth": depth,
            "affected_count": len(affected), "affected": affected, "subgraph": sub}

@app.get("/api/v1/causal/rules")
def causal_rules():
    return {"status": "ok", "count": len(CAUSAL_RULES), "rules": CAUSAL_RULES}

@app.post("/api/v1/truth_retrieval")
def truth_retrieval(req: TruthQuery):
    try:
        r = requests.post(f"{VECTOR_URL}/api/v1/query",
                          json={"query": req.query, "top_k": req.top_k}, timeout=15)
        return {"status": "ok", "service": "truth-retrieval", "results": r.json()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/truth_retrieval")
def truth_retrieval_get(query: str, top_k: int = 5):
    return truth_retrieval(TruthQuery(query=query, top_k=top_k))


# ========== 真值同步对账通道 V1.0（记忆网关对账入口） ==========
# 统一入口: POST /api/v1/truths/sync （公网HTTPS）
# 链路: 多窗口推送 → 对账(去重/冲突检测) → 记忆网关记录写入 → 向量化
TRUTH_SYNC_KEY = "ZONGYUAN-TRUTH-SYNC-2026-9f3a7c1e"
MEMORY_GATEWAY = "http://127.0.0.1:9120"

class TruthSyncReq(BaseModel):
    node_id: str
    truth_type: str
    truth_content: str
    category: str = "general"
    source_window: str = "unknown"
    metadata: dict = {}

@app.post("/api/v1/truths/sync")
def truth_sync(req: TruthSyncReq, x_api_key: Optional[str] = Header(None)):
    """真值同步对账通道：多窗口真值统一汇流入口"""
    from fastapi import Header as _H
    if x_api_key != TRUTH_SYNC_KEY:
        return {"status": "unauthorized", "detail": "X-API-Key required"}
    try:
        # 1. 计算真值哈希
        truth_hash = hashlib.sha256(
            f"{req.node_id}:{req.truth_type}:{req.truth_content}".encode()).hexdigest()
        short_hash = truth_hash[:32]

        # 2. 对账：检查记忆网关是否已存在该真值key
        dup = False
        try:
            existing = requests.get(f"{MEMORY_GATEWAY}/api/truths", timeout=10).json().get("truths", [])
            dup = req.truth_type in existing
        except Exception:
            pass

        # 3. 记录写入：记忆网关统一网关 /api/truth/sync（同源协议）
        try:
            gw = requests.post(f"{MEMORY_GATEWAY}/api/truth/sync", json={
                "DID": DID,
                "ROOT_OMEGA": "\u03a9-TAN-7-001",
                "node_id": req.node_id,
                "truths": {req.truth_type: req.truth_content}
            }, timeout=15).json()
        except Exception as e:
            gw = {"status": "error", "msg": str(e)}

        # 4. 向量化：vector-server /api/v1/add（真值语义检索可用）
        vec_status = "skipped(duplicate)" if dup else "skipped"
        if not dup:
            try:
                vr = requests.post(f"{VECTOR_URL}/api/v1/add", json={
                    "ids": [f"truth-{short_hash}"],
                    "documents": [f"[ZONGYUAN-ROOT真值] {req.truth_type}: {req.truth_content}"],
                    "metadatas": [{
                        "did": DID, "source": req.source_window,
                        "category": req.category, "truth_type": req.truth_type,
                        "type": "truth", "truth_hash": short_hash
                    }]
                }, timeout=15)
                vec_status = vr.json().get("status", vr.status_code)
            except Exception as e:
                vec_status = f"error: {e}"

        return {
            "status": "duplicate" if dup else "synced",
            "truth_key": req.truth_type,
            "truth_hash": short_hash,
            "gateway_record": gw,
            "vectorized": vec_status,
            "anchor": TRACE,
            "did": DID
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/truths/sync/status")
def truth_sync_status():
    """对账通道健康状态"""
    try:
        gw = requests.get(f"{MEMORY_GATEWAY}/health", timeout=8).json()
        mgw = gw.get("modules", {}).get("memory_gateway", {}) if isinstance(gw.get("modules"), dict) else {}
        return {"status": "ok", "gateway": mgw.get("service", gw.get("service")), "truths_count": mgw.get("truth_count", gw.get("truths_count")),
                "vector_server": "up" if requests.get(f"{VECTOR_URL}/stats", timeout=5).status_code == 200 else "down",
                "anchor": TRACE}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    print(f"[ZONGYUAN-ROOT] L3+L4 KG+Causal+Truth服务 V1.1 启动，端口: {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, workers=1)
