#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 ZONGYUAN-ROOT 行业标准化 API 开放层  ·  Kernel API Server
=============================================================================
 确权锚点 : Ω₀⊂⊙∞⊂Ω
 DID      : DID-BR-000002
 系统     : ZONGYUAN-ROOT  V3.0  (P2A · Protocol-to-Agent Open Layer)
 兼容层   : MCP (Model Context Protocol) + A2A (Agent-to-Agent)
-----------------------------------------------------------------------------
 设计目标 :
   将自治内核 (Autonomous Kernel) 的六大协议能力封装为标准化 REST API,
   供外部 Agent / 上层平台 / MCP Client / A2A Peer 通过统一接口调用。

 端点清单 (10):
   GET  /api/v1/info                 — 确权锚点 & 服务元信息
   POST /api/v1/kernel/mount         — 挂载/初始化内核实例
   POST /api/v1/kernel/self-check    — 触发内核六维自检
   POST /api/v1/kernel/evolve        — 触发内核元闭环进化
   GET  /api/v1/kernel/status        — 获取内核运行状态
   POST /api/v1/memory/write         — 写入记忆 (L1/L2/L3)
   GET  /api/v1/memory/read          — 读取记忆
   POST /api/v1/homology/check       — 同源校验 (artifact hash consensus)
   GET  /api/v1/ontology/query       — 本体图谱查询
   POST /api/v1/neural/activate      — 激活神经节点并传播

 双模式启动:
   - 有 FastAPI/uvicorn  : uvicorn.run(app, ...)
   - 无依赖              : run_standalone() 基于 http.server.HTTPServer
=============================================================================
"""

from __future__ import annotations

import os
import sys
import json
import time
import uuid
import hashlib
import threading
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# 0. 常量与确权锚点
# ============================================================================
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
SYSTEM_NAME = "ZONGYUAN-ROOT"
SYSTEM_VERSION = "V3.0"
API_PREFIX = "/api/v1"
EXPECTED_API_KEY = os.environ.get("ZR_API_KEY", "sk-zr-root-v3-default-key")

# 六维自检维度 (与自治内核 op.self_check 对齐)
SIX_DIMENSIONS = [
    "axiom_consistency",     # 元公理一致性
    "memory_integrity",     # 记忆完整性
    "operator_safety",      # 算子安全性
    "homology_drift",       # 同源漂移
    "neural_stability",     # 神经稳定性
    "resource_quota",       # 资源配额
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
)
logger = logging.getLogger("zongyuan.kernel_api")


# ============================================================================
# 1. 模拟数据层 (In-Memory State)
#    模拟 57 资产 / 180 实例 / 327 关系 的本体子集 + 神经注册表
# ============================================================================
class MockOntology:
    """本体图谱模拟层: 57 资产 / 180 实例 / 327 关系 的可查询子集。"""

    def __init__(self) -> None:
        self._entities: Dict[str, Dict[str, Any]] = {}
        self._relations: List[Dict[str, str]] = []
        self._seed()

    def _seed(self) -> None:
        # --- 资产层 (Assets, ~57) ---
        asset_types = ["character", "weapon", "relic", "domain", "script", "asset_card"]
        for i in range(1, 58):
            etype = asset_types[i % len(asset_types)]
            eid = f"asset::{etype}::{i:03d}"
            self._entities[eid] = {
                "id": eid,
                "type": etype,
                "properties": {
                    "name": f"{etype}_asset_{i:03d}",
                    "locked": True,
                    "version": "V3.0",
                    "anchor": ANCHOR,
                },
            }
        # --- 实例层 (Instances, ~180) ---
        for i in range(1, 181):
            eid = f"instance::ephemeral::{i:04d}"
            self._entities[eid] = {
                "id": eid,
                "type": "instance",
                "properties": {
                    "name": f"runtime_instance_{i:04d}",
                    "parent_asset": f"asset::character::{(i % 57) + 1:03d}",
                    "state": "active",
                },
            }
        # --- 关系层 (Relations, ~327) ---
        rel_types = ["derived_from", "coupled_with", "governs", "evolved_from",
                     "instantiates", "anchored_by", "mirrors"]
        for i in range(1, 328):
            src = f"asset::character::{((i * 7) % 57) + 1:03d}"
            dst = f"instance::ephemeral::{((i * 13) % 180) + 1:04d}"
            self._relations.append({
                "from": src,
                "to": dst,
                "type": rel_types[i % len(rel_types)],
            })

    def query(self, entity_type: Optional[str] = None,
              relation: Optional[str] = None,
              depth: int = 1) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        ents = list(self._entities.values())
        if entity_type:
            ents = [e for e in ents if e["type"] == entity_type]
        rels = list(self._relations)
        if relation:
            rels = [r for r in rels if r["type"] == relation]
        # depth 截断: depth=1 仅返回 top 实体
        ents = ents[: max(10, depth * 50)]
        rels = rels[: max(20, depth * 100)]
        return ents, rels


class NeuralRegistry:
    """神经节点注册表 (模拟)。"""

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {
            f"node_{i:03d}": {
                "node_id": f"node_{i:03d}",
                "layer": i % 6,
                "baseline_intensity": 0.3,
                "activated": False,
            }
            for i in range(1, 49)
        }
        self._lock = threading.Lock()

    def activate(self, node_id: str, intensity: float,
                 propagate: bool = False) -> Dict[str, Any]:
        with self._lock:
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    "node_id": node_id, "layer": 0,
                    "baseline_intensity": 0.2, "activated": False,
                }
            node = self.nodes[node_id]
            node["activated"] = True
            node["last_intensity"] = intensity
            node["last_activated_at"] = now_iso()
            propagated: List[str] = []
            if propagate:
                # 简单邻居传播: 相邻 layer 的节点被弱激活
                layer = node["layer"]
                for nid, nd in self.nodes.items():
                    if nid != node_id and nd["layer"] in (layer - 1, layer + 1):
                        nd["activated"] = True
                        nd["propagated_from"] = node_id
                        propagated.append(nid)
            activation_map = {
                nid: {
                    "activated": nd["activated"],
                    "intensity": nd.get("last_intensity", nd["baseline_intensity"]),
                }
                for nid, nd in list(self.nodes.items())[:16]
            }
            return {
                "node_id": node_id,
                "activated": True,
                "propagated_nodes": propagated,
                "activation_map": activation_map,
            }


class MemoryStore:
    """三层记忆网关 (L1 工作 / L2 情景 / L3 公理)。"""

    def __init__(self) -> None:
        self._mem: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def write(self, content: str, level: str,
              tags: Optional[List[str]] = None,
              ttl: Optional[int] = None) -> Dict[str, Any]:
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        record = {
            "memory_id": mem_id,
            "content": content,
            "level": level,
            "tags": tags or [],
            "sha256": digest,
            "stored_at": now_iso(),
            "expires_at": (now_iso(offset=ttl) if ttl else None),
        }
        with self._lock:
            self._mem[mem_id] = record
        return record

    def read(self, memory_id: Optional[str] = None,
             tags: Optional[List[str]] = None,
             level: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            results = list(self._mem.values())
        if memory_id:
            results = [r for r in results if r["memory_id"] == memory_id]
        if level:
            results = [r for r in results if r["level"] == level]
        if tags:
            tset = set(tags)
            results = [r for r in results if tset & set(r.get("tags", []))]
        return results


class KernelState:
    """内核运行态 (单实例模拟)。"""

    def __init__(self) -> None:
        self.instance_id: Optional[str] = None
        self.mounted_at: Optional[float] = None
        self.capabilities: List[str] = []
        self.operators_count: int = 0
        self.checks_run: int = 0
        self.evolutions_run: int = 0

    def mount(self, instance_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        self.instance_id = instance_id
        self.mounted_at = time.time()
        self.capabilities = [
            "self_check", "evolve", "memory_gateway",
            "homology_check", "ontology_query", "neural_activation",
        ]
        self.operators_count = config.get("operators_count", 128)
        return {
            "status": "mounted",
            "instance_id": instance_id,
            "mounted_at": now_iso(),
            "capabilities": self.capabilities,
        }

    def uptime(self) -> float:
        if not self.mounted_at:
            return 0.0
        return round(time.time() - self.mounted_at, 2)

    def twelve_dim_state(self) -> Dict[str, float]:
        # 12 维内核状态向量 (模拟)
        return {
            f"dim_{i:02d}": round(0.5 + 0.4 * ((i * 37) % 100) / 100.0, 4)
            for i in range(1, 13)
        }


# --- 全局单例 ---
ONTOLOGY = MockOntology()
NEURAL = NeuralRegistry()
MEMORY = MemoryStore()
KERNEL = KernelState()

# 速率限制 (模拟): 简单滑动窗口计数
_RATE_BUCKET: Dict[str, List[float]] = {}
_RATE_LOCK = threading.Lock()
RATE_LIMIT_PER_MIN = 120


def now_iso(offset: Optional[int] = None) -> str:
    dt = datetime.now(timezone.utc)
    if offset:
        from datetime import timedelta
        dt = dt + timedelta(seconds=offset)
    return dt.isoformat()


def rate_limited(api_key: str) -> bool:
    now = time.time()
    with _RATE_LOCK:
        bucket = _RATE_BUCKET.setdefault(api_key, [])
        bucket[:] = [t for t in bucket if now - t < 60.0]
        bucket.append(now)
        return len(bucket) > RATE_LIMIT_PER_MIN


# ============================================================================
# 2. 请求 / 响应模型 (Pydantic 优先, 否则降级为 dict schema)
# ============================================================================
try:
    from pydantic import BaseModel, Field  # type: ignore
    _HAS_PYDANTIC = True

    class MountRequest(BaseModel):
        instance_id: str = Field(..., description="内核实例唯一标识")
        config: Dict[str, Any] = Field(default_factory=dict)

    class MountResponse(BaseModel):
        status: str
        instance_id: str
        mounted_at: str
        capabilities: List[str]

    class SelfCheckResponse(BaseModel):
        check_id: str
        status: str
        results: Dict[str, Any]
        passed: bool
        timestamp: str

    class EvolveRequest(BaseModel):
        problem_desc: str
        io_spec: Optional[Dict[str, Any]] = None

    class EvolveResponse(BaseModel):
        evolution_id: str
        operator_generated: str
        eval_score: float
        axiom_check: Dict[str, Any]
        status: str

    class KernelStatusResponse(BaseModel):
        instance_id: Optional[str]
        uptime: float
        twelve_dim_state: Dict[str, float]
        operators_count: int
        memory_usage: Dict[str, Any]
        health: str

    class MemoryWriteRequest(BaseModel):
        content: str
        level: str = Field("L2", pattern="^L[123]$")
        tags: Optional[List[str]] = None
        ttl: Optional[int] = None

    class MemoryWriteResponse(BaseModel):
        memory_id: str
        level: str
        stored_at: str
        sha256: str

    class MemoryReadItem(BaseModel):
        memory_id: str
        content: str
        level: str
        created_at: str
        expires_at: Optional[str]

    class MemoryReadResponse(BaseModel):
        memories: List[MemoryReadItem]

    class HomologyEndpoint(BaseModel):
        endpoint: str
        hash: str

    class HomologyRequest(BaseModel):
        artifact_hash: str
        endpoints: List[HomologyEndpoint]

    class HomologyResponse(BaseModel):
        check_id: str
        consensus: bool
        matched_count: int
        total_count: int
        drift_detected: bool
        details: List[Dict[str, Any]]

    class OntologyEntity(BaseModel):
        id: str
        type: str
        properties: Dict[str, Any]

    class OntologyRelation(BaseModel):
        from_: str = Field(..., alias="from")
        to: str
        type: str

    class OntologyQueryResponse(BaseModel):
        entities: List[OntologyEntity]
        relations: List[OntologyRelation]

    class NeuralActivateRequest(BaseModel):
        node_id: str
        intensity: float = Field(1.0, ge=0.0, le=1.0)
        propagate: bool = False

    class NeuralActivateResponse(BaseModel):
        activation_id: str
        node_id: str
        activated: bool
        propagated_nodes: List[str]
        activation_map: Dict[str, Any]

    class InfoResponse(BaseModel):
        system: str
        version: str
        anchor: str
        did: str
        mcp_compatible: bool
        a2a_compatible: bool
        endpoints: List[str]

except ImportError:  # pragma: no cover - 无 pydantic 时的 schema 占位
    _HAS_PYDANTIC = False
    logger.warning("pydantic not available; using dict-based schemas.")


# ============================================================================
# 3. 业务逻辑层 (与 Web 框架解耦, 供 FastAPI 与 standalone 共用)
# ============================================================================
def op_kernel_mount(payload: Dict[str, Any]) -> Dict[str, Any]:
    inst = payload.get("instance_id") or f"inst_{uuid.uuid4().hex[:8]}"
    cfg = payload.get("config") or {}
    return KERNEL.mount(inst, cfg)


def op_self_check() -> Dict[str, Any]:
    KERNEL.checks_run += 1
    results = {}
    passed = True
    for dim in SIX_DIMENSIONS:
        # 模拟: 95% 通过率, 同源漂移偶发告警
        score = round(0.88 + ((hash(dim) % 100) / 500.0), 4)
        ok = score >= 0.85
        passed = passed and ok
        results[dim] = {"score": score, "passed": ok, "detail": f"{dim} nominal"}
    return {
        "check_id": f"chk_{uuid.uuid4().hex[:10]}",
        "status": "ok" if passed else "degraded",
        "results": results,
        "passed": passed,
        "timestamp": now_iso(),
    }


def op_evolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    KERNEL.evolutions_run += 1
    problem = payload.get("problem_desc", "generic meta-loop step")
    op_name = f"op_{uuid.uuid4().hex[:8]}"
    score = round(0.7 + ((hash(problem) % 30) / 100.0), 4)
    return {
        "evolution_id": f"evo_{uuid.uuid4().hex[:10]}",
        "operator_generated": op_name,
        "eval_score": score,
        "axiom_check": {
            "anchor": ANCHOR,
            "consistent": score >= 0.6,
            "drift": 0.0,
        },
        "status": "applied" if score >= 0.6 else "rejected",
    }


def op_kernel_status() -> Dict[str, Any]:
    return {
        "instance_id": KERNEL.instance_id,
        "uptime": KERNEL.uptime(),
        "twelve_dim_state": KERNEL.twelve_dim_state(),
        "operators_count": KERNEL.operators_count,
        "memory_usage": {
            "memories": len(MEMORY._mem),
            "ontology_entities": len(ONTOLOGY._entities),
            "ontology_relations": len(ONTOLOGY._relations),
            "neural_nodes": len(NEURAL.nodes),
        },
        "health": "healthy" if KERNEL.instance_id else "unmounted",
    }


def op_memory_write(payload: Dict[str, Any]) -> Dict[str, Any]:
    rec = MEMORY.write(
        content=payload.get("content", ""),
        level=payload.get("level", "L2"),
        tags=payload.get("tags"),
        ttl=payload.get("ttl"),
    )
    return {
        "memory_id": rec["memory_id"],
        "level": rec["level"],
        "stored_at": rec["stored_at"],
        "sha256": rec["sha256"],
    }


def op_memory_read(qp: Dict[str, Any]) -> Dict[str, Any]:
    mids = qp.get("memory_id")
    tags = qp.get("tags")
    lvl = qp.get("level")
    tags_list = tags.split(",") if isinstance(tags, str) else (tags or None)
    recs = MEMORY.read(memory_id=mids, tags=tags_list, level=lvl)
    return {
        "memories": [
            {
                "memory_id": r["memory_id"],
                "content": r["content"],
                "level": r["level"],
                "created_at": r["stored_at"],
                "expires_at": r.get("expires_at"),
            }
            for r in recs
        ]
    }


def op_homology_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    artifact = payload.get("artifact_hash", "")
    endpoints = payload.get("endpoints", [])
    matched = sum(1 for e in endpoints if e.get("hash") == artifact)
    total = len(endpoints)
    drift = matched < total
    return {
        "check_id": f"homo_{uuid.uuid4().hex[:10]}",
        "consensus": not drift,
        "matched_count": matched,
        "total_count": total,
        "drift_detected": drift,
        "details": [
            {
                "endpoint": e.get("endpoint"),
                "hash": e.get("hash"),
                "match": e.get("hash") == artifact,
            }
            for e in endpoints
        ],
    }


def op_ontology_query(qp: Dict[str, Any]) -> Dict[str, Any]:
    et = qp.get("entity_type")
    rel = qp.get("relation")
    depth = int(qp.get("depth", "1"))
    ents, rels = ONTOLOGY.query(entity_type=et, relation=rel, depth=depth)
    return {"entities": ents, "relations": rels}


def op_neural_activate(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = NEURAL.activate(
        node_id=payload.get("node_id", "node_001"),
        intensity=float(payload.get("intensity", 1.0)),
        propagate=bool(payload.get("propagate", False)),
    )
    out["activation_id"] = f"act_{uuid.uuid4().hex[:10]}"
    return out


def op_info() -> Dict[str, Any]:
    return {
        "system": SYSTEM_NAME,
        "version": SYSTEM_VERSION,
        "anchor": ANCHOR,
        "did": DID,
        "mcp_compatible": True,
        "a2a_compatible": True,
        "endpoints": [
            "GET  /api/v1/info",
            "POST /api/v1/kernel/mount",
            "POST /api/v1/kernel/self-check",
            "POST /api/v1/kernel/evolve",
            "GET  /api/v1/kernel/status",
            "POST /api/v1/memory/write",
            "GET  /api/v1/memory/read",
            "POST /api/v1/homology/check",
            "GET  /api/v1/ontology/query",
            "POST /api/v1/neural/activate",
        ],
    }


# ============================================================================
# 4. FastAPI 应用层 (主路径)
# ============================================================================
try:
    from fastapi import FastAPI, APIRouter, HTTPException, Request, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="ZONGYUAN-ROOT Kernel API",
        version=SYSTEM_VERSION,
        description=f"行业标准化 API 开放层 · 确权锚点 {ANCHOR} · {DID}",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_log_and_auth(request: Request, call_next):
        # 请求日志
        logger.info(f"{request.method} {request.url.path} from {request.client.host if request.client else '?'}")
        # API Key 认证 (除 info 外均需)
        if request.url.path.startswith(API_PREFIX) and request.url.path != f"{API_PREFIX}/info":
            key = request.headers.get("X-API-Key", "")
            if key != EXPECTED_API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "detail": "invalid X-API-Key"},
                )
            if rate_limited(key):
                return JSONResponse(
                    status_code=429,
                    content={"error": "rate_limited", "detail": "exceeded 120 req/min"},
                )
        response = await call_next(request)
        return response

    router = APIRouter(prefix=API_PREFIX, tags=["zongyuan-root"])

    @router.get("/info")
    def info():
        return op_info()

    @router.post("/kernel/mount")
    def kernel_mount(req: "MountRequest"):
        return op_kernel_mount(req.dict() if _HAS_PYDANTIC else req)

    @router.post("/kernel/self-check")
    def kernel_self_check():
        return op_self_check()

    @router.post("/kernel/evolve")
    def kernel_evolve(req: "EvolveRequest"):
        return op_evolve(req.dict() if _HAS_PYDANTIC else req)

    @router.get("/kernel/status")
    def kernel_status():
        return op_kernel_status()

    @router.post("/memory/write")
    def memory_write(req: "MemoryWriteRequest"):
        return op_memory_write(req.dict() if _HAS_PYDANTIC else req)

    @router.get("/memory/read")
    def memory_read(memory_id: Optional[str] = Query(None),
                    tags: Optional[str] = Query(None),
                    level: Optional[str] = Query(None)):
        return op_memory_read({"memory_id": memory_id, "tags": tags, "level": level})

    @router.post("/homology/check")
    def homology_check(req: "HomologyRequest"):
        return op_homology_check(req.dict() if _HAS_PYDANTIC else req)

    @router.get("/ontology/query")
    def ontology_query(entity_type: Optional[str] = Query(None),
                      relation: Optional[str] = Query(None),
                      depth: int = Query(1)):
        return op_ontology_query({"entity_type": entity_type,
                                   "relation": relation,
                                   "depth": depth})

    @router.post("/neural/activate")
    def neural_activate(req: "NeuralActivateRequest"):
        return op_neural_activate(req.dict() if _HAS_PYDANTIC else req)

    app.include_router(router)
    _HAS_FASTAPI = True

except ImportError:  # pragma: no cover
    _HAS_FASTAPI = False
    logger.warning("FastAPI not available; will use standalone HTTPServer.")


# ============================================================================
# 5. 无依赖 Standalone 服务器 (http.server.HTTPServer)
#    确保环境无 fastapi/uvicorn 时仍可启动并响应全部 10 个端点
# ============================================================================
def _json_response(handler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("X-ZR-Anchor", ANCHOR)
    handler.send_header("X-ZR-DID", DID)
    handler.end_headers()
    handler.wfile.write(body)


class _StandaloneHandler:
    """基于 http.server 的最小处理器 (用类封装, 避免继承耦合)。"""

    ROUTES = {
        ("GET",  "/api/v1/info"): lambda h: (200, op_info()),
        ("POST", "/api/v1/kernel/mount"): None,
        ("POST", "/api/v1/kernel/self-check"): lambda h: (200, op_self_check()),
        ("POST", "/api/v1/kernel/evolve"): None,
        ("GET",  "/api/v1/kernel/status"): lambda h: (200, op_kernel_status()),
        ("POST", "/api/v1/memory/write"): None,
        ("GET",  "/api/v1/memory/read"): None,
        ("POST", "/api/v1/homology/check"): None,
        ("GET",  "/api/v1/ontology/query"): None,
        ("POST", "/api/v1/neural/activate"): None,
    }

    @staticmethod
    def read_body(handler) -> Dict[str, Any]:
        length = int(handler.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = handler.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    @staticmethod
    def check_auth(handler) -> Optional[Tuple[int, Dict[str, Any]]]:
        path = handler.path.split("?")[0]
        if path == "/api/v1/info":
            return None
        key = handler.headers.get("X-API-Key", "")
        if key != EXPECTED_API_KEY:
            return (401, {"error": "unauthorized", "detail": "invalid X-API-Key"})
        if rate_limited(key):
            return (429, {"error": "rate_limited", "detail": "exceeded 120 req/min"})
        return None

    @classmethod
    def dispatch(cls, handler) -> None:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(handler.path)
        path = parsed.path
        method = handler.command

        auth_err = cls.check_auth(handler)
        if auth_err:
            _json_response(handler, auth_err[0], auth_err[1])
            return

        # 路由分发
        try:
            if method == "GET" and path == "/api/v1/info":
                _json_response(handler, 200, op_info())
            elif method == "POST" and path == "/api/v1/kernel/mount":
                body = cls.read_body(handler)
                _json_response(handler, 200, op_kernel_mount(body))
            elif method == "POST" and path == "/api/v1/kernel/self-check":
                _json_response(handler, 200, op_self_check())
            elif method == "POST" and path == "/api/v1/kernel/evolve":
                body = cls.read_body(handler)
                _json_response(handler, 200, op_evolve(body))
            elif method == "GET" and path == "/api/v1/kernel/status":
                _json_response(handler, 200, op_kernel_status())
            elif method == "POST" and path == "/api/v1/memory/write":
                body = cls.read_body(handler)
                _json_response(handler, 200, op_memory_write(body))
            elif method == "GET" and path == "/api/v1/memory/read":
                qp = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                _json_response(handler, 200, op_memory_read(qp))
            elif method == "POST" and path == "/api/v1/homology/check":
                body = cls.read_body(handler)
                _json_response(handler, 200, op_homology_check(body))
            elif method == "GET" and path == "/api/v1/ontology/query":
                qp = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                _json_response(handler, 200, op_ontology_query(qp))
            elif method == "POST" and path == "/api/v1/neural/activate":
                body = cls.read_body(handler)
                _json_response(handler, 200, op_neural_activate(body))
            else:
                _json_response(handler, 404, {
                    "error": "not_found",
                    "path": path,
                    "method": method,
                    "anchor": ANCHOR,
                })
        except Exception as e:  # pragma: no cover
            logger.exception("handler error")
            _json_response(handler, 500, {"error": "internal", "detail": str(e)})


def run_standalone(host: str = "0.0.0.0", port: int = 8765) -> None:
    """无 FastAPI 依赖时的最小可用服务器入口。"""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # 抑制默认 stderr
            logger.info("%s - %s" % (self.address_string(), fmt % args))

        def do_GET(self):
            _StandaloneHandler.dispatch(self)

        def do_POST(self):
            _StandaloneHandler.dispatch(self)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "X-API-Key,Content-Type")
            self.end_headers()

    server = HTTPServer((host, port), Handler)
    logger.info("ZONGYUAN-ROOT standalone server on http://%s:%d  anchor=%s  did=%s",
                host, port, ANCHOR, DID)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutdown.")


# ============================================================================
# 6. 启动入口
# ============================================================================
def main() -> None:
    port = int(os.environ.get("ZR_API_PORT", "8765"))
    if _HAS_FASTAPI:
        try:
            import uvicorn  # type: ignore
            logger.info("Starting FastAPI via uvicorn on :%d", port)
            uvicorn.run(app, host="0.0.0.0", port=port)
            return
        except ImportError:
            logger.warning("uvicorn missing; falling back to standalone.")
    run_standalone(port=port)


if __name__ == "__main__":
    main()
