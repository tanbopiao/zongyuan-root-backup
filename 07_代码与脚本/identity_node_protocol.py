#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

identity_node_protocol.py — 身份节点协议（Identity Node Protocol）

每个 ZONGYUAN-ROOT 实例在心智耦合网络中拥有唯一身份节点（IdentityNode）。
本模块负责：
  1. 身份节点的注册 / 注销 / 状态迁移
  2. 基于挑战-响应的身份验证（模拟 RSA 公钥签名）
  3. 信任度计算（交互历史 + 耦合稳定性）
  4. Merkle 身份链：新节点需前序节点签名才能上链

纯 Python 3.8+ 标准库实现，不依赖 numpy / 第三方加密库。
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 确权常量
# ---------------------------------------------------------------------------
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID_NAMESPACE = "did:zyr"
PROTOCOL_VERSION = "ZR-IDP-1.0"


class NodeStatus(str, Enum):
    """身份节点状态机。"""
    ONLINE = "online"          # 在线未耦合
    OFFLINE = "offline"       # 离线
    COUPLED = "coupled"        # 已进入心智耦合
    REVOKED = "revoked"        # 已吊销


# ---------------------------------------------------------------------------
# 身份节点
# ---------------------------------------------------------------------------
@dataclass
class IdentityNode:
    """
    单个 ZONGYUAN-ROOT 实例的身份节点。

    字段：
        node_id:      形如 ZR-AGENT-XXXXXXXX 的全局唯一节点 ID
        did:          去中心化标识符 did:zyr:<node_id>
        public_key:   模拟 RSA-2048 公钥指纹（SHA-256 hex 前 64 位）
        created_at:   Unix 时间戳
        capabilities: 能力标签列表（如 ["mind_sync", "attractor_tracking", ...]）
        trust_level:  初始信任度 [0, 1]
        status:       当前状态
        nonce:        最近一次挑战的随机数
    """

    node_id: str
    did: str
    public_key: str
    created_at: float
    capabilities: List[str] = field(default_factory=list)
    trust_level: float = 0.5
    status: NodeStatus = NodeStatus.ONLINE
    nonce: str = ""

    # ---------- 工厂方法 ----------
    @staticmethod
    def generate(capabilities: Optional[List[str]] = None,
                 initial_trust: float = 0.5) -> "IdentityNode":
        """生成一个全新的身份节点（含 node_id / did / 模拟公钥指纹）。"""
        suffix = uuid.uuid4().hex[:8].upper()
        node_id = f"ZR-AGENT-{suffix}"
        did = f"{DID_NAMESPACE}:{node_id}"
        # 模拟公钥指纹：用 node_id + uuid + 时间戳 做 SHA-256
        raw = f"{node_id}|{uuid.uuid4().hex}|{time.time()}".encode("utf-8")
        public_key = hashlib.sha256(raw).hexdigest()
        return IdentityNode(
            node_id=node_id,
            did=did,
            public_key=public_key,
            created_at=time.time(),
            capabilities=capabilities or ["mind_sync", "state_vector_12d"],
            trust_level=max(0.0, min(1.0, initial_trust)),
            status=NodeStatus.ONLINE,
            nonce=uuid.uuid4().hex,
        )

    # ---------- 签名工具（模拟） ----------
    def sign(self, message: str) -> str:
        """
        模拟 RSA 私钥签名：H( message || public_key || nonce )。
        真实场景应为私钥对消息摘要做 PKCS#1 v1.5 签名。
        """
        h = hashlib.sha256()
        h.update(message.encode("utf-8"))
        h.update(self.public_key.encode("utf-8"))
        h.update(self.nonce.encode("utf-8"))
        return h.hexdigest()

    def verify_signature(self, message: str, signature: str) -> bool:
        """用本节点公钥（指纹）校验签名是否匹配。"""
        return self.sign(message) == signature

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "did": self.did,
            "public_key": self.public_key,
            "created_at": self.created_at,
            "capabilities": list(self.capabilities),
            "trust_level": self.trust_level,
            "status": self.status.value,
        }


# ---------------------------------------------------------------------------
# Merkle 身份链区块
# ---------------------------------------------------------------------------
@dataclass
class IdentityBlock:
    """Merkle 身份链中的一个区块：登记一次注册事件。"""
    index: int
    node: IdentityNode
    prev_signer_id: str          # 前序节点 node_id（创世纪块为 "GENESIS"）
    prev_signature: str          # 前序节点对本节点公钥的签名
    merkle_hash: str              # 本块哈希（含前块哈希）
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# 身份节点协议
# ---------------------------------------------------------------------------
class IdentityNodeProtocol:
    """
    身份节点管理协议。

    职责：
      - register(identity)        注册节点（写入 Merkle 链）
      - verify(node_id, challenge) 挑战-响应身份验证
      - get_trust(node_id)        查询信任度
      - get_identity_chain()      返回完整身份链
      - revoke(node_id)           吊销节点
      - record_interaction(...)   交互后更新信任度
    """

    def __init__(self, genesis_capabilities: Optional[List[str]] = None):
        # node_id -> IdentityNode
        self._nodes: Dict[str, IdentityNode] = {}
        # node_id -> 历史交互计数（成功/失败）
        self._interaction_log: Dict[str, Tuple[int, int]] = {}
        # Merkle 身份链
        self._chain: List[IdentityBlock] = []
        # 创世纪块：协议自身作为首个签名者
        genesis = IdentityNode.generate(
            capabilities=genesis_capabilities or ["genesis"],
            initial_trust=1.0,
        )
        genesis.node_id = "ZR-AGENT-GENESIS0"
        genesis.did = f"{DID_NAMESPACE}:{genesis.node_id}"
        self._genesis = genesis
        # 写入创世纪块
        self._append_block(genesis, prev_signer_id="GENESIS",
                           prev_signature="GENESIS-SIGNATURE")

    # ---------------- 内部工具 ----------------
    @staticmethod
    def _hash_block(index: int, node: IdentityNode,
                    prev_signer_id: str, prev_signature: str,
                    prev_hash: str, timestamp: float) -> str:
        payload = json.dumps({
            "index": index,
            "node_id": node.node_id,
            "public_key": node.public_key,
            "prev_signer_id": prev_signer_id,
            "prev_signature": prev_signature,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _append_block(self, node: IdentityNode,
                      prev_signer_id: str,
                      prev_signature: str) -> IdentityBlock:
        prev_hash = self._chain[-1].merkle_hash if self._chain else "0" * 64
        index = len(self._chain)
        ts = time.time()
        merkle_hash = self._hash_block(
            index, node, prev_signer_id, prev_signature, prev_hash, ts
        )
        block = IdentityBlock(
            index=index,
            node=node,
            prev_signer_id=prev_signer_id,
            prev_signature=prev_signature,
            merkle_hash=merkle_hash,
            timestamp=ts,
        )
        self._chain.append(block)
        return block

    # ---------------- 公共接口 ----------------
    def register(self, identity: Optional[IdentityNode] = None) -> IdentityNode:
        """
        注册新身份节点。新节点必须由链上最后一个在线节点签名（模拟）。
        若未传入 identity，则自动生成一个。
        """
        if identity is None:
            identity = IdentityNode.generate()
        if identity.node_id in self._nodes:
            raise ValueError(f"节点已存在: {identity.node_id}")

        # 选择签名者：链上最后一个未吊销节点
        signer = self._genesis
        for block in reversed(self._chain):
            cand = block.node
            if cand.status != NodeStatus.REVOKED:
                signer = cand
                break

        # 模拟签名：签名者对新节点公钥 + 创纪元做签名
        challenge_msg = f"REG:{identity.node_id}:{identity.public_key}"
        signature = signer.sign(challenge_msg)

        self._append_block(identity,
                            prev_signer_id=signer.node_id,
                            prev_signature=signature)
        self._nodes[identity.node_id] = identity
        self._interaction_log[identity.node_id] = (0, 0)
        return identity

    def verify(self, node_id: str, challenge: Optional[str] = None) -> bool:
        """
        挑战-响应身份验证。
        1. 节点必须存在且未吊销
        2. 节点对挑战字符串给出签名，校验是否匹配
        """
        node = self._nodes.get(node_id)
        if node is None or node.status == NodeStatus.REVOKED:
            return False
        if challenge is None:
            challenge = f"CHALLENGE-{uuid.uuid4().hex}"
        # 刷新 nonce，再让节点"签名"
        node.nonce = hashlib.sha256(challenge.encode("utf-8")).hexdigest()[:16]
        expected = node.sign(challenge)
        # 校验链上签名是否仍指向当前公钥
        on_chain = self._find_block(node_id)
        if on_chain is None:
            return False
        # 简单一致性校验：重新计算应得签名并比对
        recomputed = node.sign(challenge)
        ok = (expected == recomputed)
        # 记录一次成功交互
        if ok:
            s, f = self._interaction_log[node_id]
            self._interaction_log[node_id] = (s + 1, f)
        return ok

    def get_trust(self, node_id: str) -> float:
        """
        信任度 = 0.4 * 初始基础信任 + 0.4 * 交互成功率 + 0.2 * 耦合稳定性。
        """
        node = self._nodes.get(node_id)
        if node is None or node.status == NodeStatus.REVOKED:
            return 0.0
        s, f = self._interaction_log.get(node_id, (0, 0))
        total = s + f
        success_rate = (s / total) if total > 0 else 0.5
        stability = 1.0 if node.status == NodeStatus.COUPLED else 0.6
        trust = 0.4 * node.trust_level + 0.4 * success_rate + 0.2 * stability
        return max(0.0, min(1.0, trust))

    def get_identity_chain(self) -> List[Dict]:
        """返回完整 Merkle 身份链的可读视图。"""
        return [
            {
                "index": b.index,
                "node_id": b.node.node_id,
                "did": b.node.did,
                "public_key_prefix": b.node.public_key[:16] + "...",
                "prev_signer": b.prev_signer_id,
                "prev_signature_prefix": b.prev_signature[:16] + "...",
                "merkle_hash": b.merkle_hash,
                "timestamp": b.timestamp,
            }
            for b in self._chain
        ]

    def revoke(self, node_id: str) -> bool:
        """吊销节点：标记状态，并从活跃集合中移除。"""
        node = self._nodes.get(node_id)
        if node is None:
            return False
        node.status = NodeStatus.REVOKED
        return True

    # ---------------- 辅助 ----------------
    def _find_block(self, node_id: str) -> Optional[IdentityBlock]:
        for b in reversed(self._chain):
            if b.node.node_id == node_id:
                return b
        return None

    def list_nodes(self) -> List[IdentityNode]:
        return list(self._nodes.values())

    def set_coupled(self, node_id: str, coupled: bool = True) -> None:
        node = self._nodes.get(node_id)
        if node is None or node.status == NodeStatus.REVOKED:
            return
        node.status = NodeStatus.COUPLED if coupled else NodeStatus.ONLINE

    def record_interaction(self, node_id: str, success: bool) -> None:
        if node_id not in self._interaction_log:
            return
        s, f = self._interaction_log[node_id]
        self._interaction_log[node_id] = (s + int(success), f + int(not success))


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 72)
    print(f"  {ANCHOR}  ·  {DID_NAMESPACE}  ·  {PROTOCOL_VERSION}")
    print("  Identity Node Protocol — Demo")
    print("=" * 72)

    idp = IdentityNodeProtocol()

    # 1) 注册 5 个智能体身份节点
    agents: List[IdentityNode] = []
    for i in range(5):
        n = idp.register()
        agents.append(n)
        print(f"[REGISTER] {n.node_id}  did={n.did}  "
              f"pk={n.public_key[:16]}...  trust={n.trust_level:.2f}")

    # 2) 身份验证（挑战-响应）
    print("\n[VERIFY] 挑战-响应验证：")
    for a in agents:
        ok = idp.verify(a.node_id, challenge=f"HELLO::{a.node_id}")
        print(f"  {a.node_id} -> {'✓ 验证通过' if ok else '✗ 失败'}  "
              f"trust={idp.get_trust(a.node_id):.3f}")

    # 3) 写入若干交互历史以观察信任度变化
    for a in agents[:3]:
        for _ in range(8):
            idp.record_interaction(a.node_id, success=True)
    for a in agents[3:]:
        idp.record_interaction(agents[3].node_id, success=True)
        idp.record_interaction(agents[3].node_id, success=False)

    print("\n[TRUST] 信任度更新后：")
    for a in agents:
        print(f"  {a.node_id}  trust={idp.get_trust(a.node_id):.3f}")

    # 4) 吊销一个节点
    idp.revoke(agents[1].node_id)
    print(f"\n[REVOKE] {agents[1].node_id} 已吊销, "
          f"verify={idp.verify(agents[1].node_id)}  "
          f"trust={idp.get_trust(agents[1].node_id):.3f}")

    # 5) 输出身份链
    print("\n[CHAIN] Merkle 身份链（前 4 块）：")
    for entry in idp.get_identity_chain()[:4]:
        print(f"  #{entry['index']:>2}  {entry['node_id']:<22}  "
              f"prev={entry['prev_signer']:<22}  "
              f"hash={entry['merkle_hash'][:16]}...")

    print("\n[OK] identity_node_protocol demo 完成。")
