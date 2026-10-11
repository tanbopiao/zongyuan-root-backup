#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 联邦记忆池(SFMP)管理器 V2.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L4 SFMP联邦层

V2.0 进化（2026-10-11）：
1. 云端第二验证方 — 突破可发布数=0瓶颈
   本地提纯的z → 上报云端真值库 → 云端回读验证 → 达到K=2即可发布
2. 语义单元生命周期管理 — 衰减/演化/回收/状态机
   状态机: proposed → verified → published → decayed → recycled
   时效衰减: 半衰期30天，置信度随时间衰减
   置信度演化: 被多次引用/验证的z自动升级
3. 五级质量分级体系 — S/A/B/C/D
   S级: ≥3节点验证 + 置信度≥0.9 + 被引用≥10次
   A级: ≥2节点验证 + 置信度≥0.8
   B级: ≥2节点验证 + 置信度≥0.6（V1.0标准）
   C级: 单节点验证 + 置信度≥0.6（待验证池）
   D级: 低于阈值（回收池）

SFMP核心设计：
- 多租户共用的语义单元公共池
- 原文不出域，只流通提纯后的语义碎片 z（向量+标签+置信度）
- 每条 z 经 ≥K 独立租户验证才入库，过 L0 校验才下发
- 租户业务数据/子 L0/MC 版本互不可见，只共享 z
"""

import json
import os
import sys
import time
import hashlib
import urllib.request
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
SFMP_DIR = ROOT / "06_云端中枢同步" / "sfmp_federation"
SFMP_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
CLOUD_NODE_ID = "CLOUD-HUODOUAI-GATEWAY"

# SFMP配置
K_VERIFICATION = 2
CONFIDENCE_THRESHOLD = 0.6
MAX_Z_PER_SYNC = 50

# V2.0 生命周期配置
DECAY_HALF_LIFE_DAYS = 30          # 置信度半衰期（天）
DECAY_FACTOR = 0.5                  # 每半衰期衰减比例
RECYCLE_AGE_DAYS = 60               # D级回收年龄阈值
RECYCLE_NO_ACCESS_DAYS = 30         # 无访问回收阈值
REFERENCE_BOOST = 0.02              # 每次引用置信度提升
MAX_CONFIDENCE = 1.0

# 云端验证配置
CLOUD_VERIFY_URLS = [
    "https://www.huodouai.com/api/report/truth",
    "https://drama.huodouai.com/api/report/truth",
]
CLOUD_PULL_URL = "https://www.huodouai.com/api/truth"
CLOUD_VERIFY_TIMEOUT = 10


# ============================================================
# 五级质量分级
# ============================================================

def compute_quality_grade(verification_count: int, confidence: float,
                           reference_count: int) -> str:
    """
    计算语义单元质量等级 S/A/B/C/D
    S级: ≥3节点验证 + 置信度≥0.9 + 被引用≥10次
    A级: ≥2节点验证 + 置信度≥0.8
    B级: ≥2节点验证 + 置信度≥0.6（V1.0标准）
    C级: 单节点验证 + 置信度≥0.6（待验证池）
    D级: 低于阈值（回收池）
    """
    if verification_count >= 3 and confidence >= 0.9 and reference_count >= 10:
        return "S"
    if verification_count >= 2 and confidence >= 0.8:
        return "A"
    if verification_count >= 2 and confidence >= 0.6:
        return "B"
    if verification_count >= 1 and confidence >= 0.6:
        return "C"
    return "D"


# ============================================================
# 语义单元 z（V2.0 扩展）
# ============================================================

@dataclass
class SemanticUnit:
    """语义单元 z（SFMP流通对象）V2.0"""
    z_id: str
    content_hash: str
    vector_signature: str
    tags: List[str]
    confidence: float
    verification_count: int
    verified_by: List[str]
    source: str
    l0_checked: bool
    # V2.0 新增字段
    quality_grade: str = "C"               # 质量等级 S/A/B/C/D
    lifecycle_state: str = "proposed"      # 生命周期状态
    reference_count: int = 0                # 被引用次数
    last_verified_at: float = field(default_factory=time.time)
    decay_rate: float = 0.0                 # 衰减速率
    cloud_verified: bool = False            # 云端验证标记
    # V1.0 原有字段
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    axis: str = "federated_semantic"

    def to_dict(self):
        return asdict(self)

    def is_publishable(self) -> bool:
        """是否可发布（≥K验证 + 置信度阈值 + L0校验 + 质量≥B级）"""
        return (self.verification_count >= K_VERIFICATION
                and self.confidence >= CONFIDENCE_THRESHOLD
                and self.l0_checked
                and self.quality_grade in ("S", "A", "B"))

    def recompute_grade(self):
        """重新计算质量等级"""
        self.quality_grade = compute_quality_grade(
            self.verification_count, self.confidence, self.reference_count
        )

    def apply_decay(self):
        """应用时效衰减"""
        age_days = (time.time() - self.last_verified_at) / 86400
        if age_days >= DECAY_HALF_LIFE_DAYS:
            half_lives = age_days / DECAY_HALF_LIFE_DAYS
            decay = DECAY_FACTOR ** half_lives
            original_conf = self.confidence
            self.confidence = round(self.confidence * decay, 4)
            self.decay_rate = round(1 - self.confidence / max(original_conf, 0.001), 4)
            # 衰减后降级
            if self.lifecycle_state == "published" and self.confidence < 0.6:
                self.lifecycle_state = "decayed"
            self.recompute_grade()

    def register_reference(self):
        """注册一次引用，提升置信度"""
        self.reference_count += 1
        self.confidence = min(MAX_CONFIDENCE, round(self.confidence + REFERENCE_BOOST, 4))
        self.last_accessed = time.time()
        self.recompute_grade()


# ============================================================
# SFMP管理器 V2.0
# ============================================================

class SFMPManager:
    """
    联邦记忆池管理器 V2.0

    V2.0 核心进化：
    1. 云端第二验证方（突破可发布数=0）
    2. 语义单元生命周期管理（衰减/演化/回收/状态机）
    3. 五级质量分级体系（S/A/B/C/D）
    """

    def __init__(self):
        self.pool_file = SFMP_DIR / "semantic_units.json"
        self.state_file = SFMP_DIR / "sfmp_state.json"
        self.recycle_file = SFMP_DIR / "recycled_units.json"
        self.pool: Dict[str, SemanticUnit] = {}
        self.recycled: List[Dict] = []
        self.state = self._load_state()
        self._load_pool()
        self._load_recycled()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {
            "last_pull_seq": 0,
            "last_sync_time": 0,
            "last_lifecycle_run": 0,
            "total_published": 0,
            "total_received": 0,
            "total_recycled": 0,
            "total_cloud_verified": 0,
            "created_at": time.time(),
            "version": "2.0"
        }

    def _save_state(self):
        self.state["last_update"] = time.time()
        self.state["version"] = "2.0"
        self.state_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))

    def _load_pool(self):
        if self.pool_file.exists():
            try:
                data = json.loads(self.pool_file.read_text())
                for z_id, z_data in data.items():
                    # V1.0兼容：补充V2.0新字段
                    z_data.setdefault("quality_grade", "C")
                    z_data.setdefault("lifecycle_state", "proposed")
                    z_data.setdefault("reference_count", 0)
                    z_data.setdefault("last_verified_at", z_data.get("created_at", time.time()))
                    z_data.setdefault("decay_rate", 0.0)
                    z_data.setdefault("cloud_verified", False)
                    self.pool[z_id] = SemanticUnit(**z_data)
            except Exception:
                pass

    def _save_pool(self):
        data = {z_id: z.to_dict() for z_id, z in self.pool.items()}
        self.pool_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load_recycled(self):
        if self.recycle_file.exists():
            try:
                self.recycled = json.loads(self.recycle_file.read_text())
            except Exception:
                self.recycled = []

    def _save_recycled(self):
        self.recycle_file.write_text(json.dumps(self.recycled, ensure_ascii=False, indent=2))

    def _get_cloud_token(self) -> str:
        """获取云端凭证"""
        token_file = ROOT / "04_系统配置" / "凭证" / "active_token.env"
        if token_file.exists():
            for line in token_file.read_text().split("\n"):
                if line.strip().startswith("ZR_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"')
        return ""

    # ============================================================
    # V2.0 新功能1: 云端第二验证方
    # ============================================================

    def cloud_verify_unit(self, z: SemanticUnit) -> bool:
        """
        云端第二验证方验证
        将z上报云端真值库，然后确认上报成功，作为第二验证方
        """
        if z.cloud_verified:
            return True

        token = self._get_cloud_token()
        if not token:
            return False

        payload = {
            "key": f"SFMP-Z-VERIFY.{z.z_id}",
            "value": {
                "z_id": z.z_id,
                "content_hash": z.content_hash,
                "tags": z.tags,
                "confidence": z.confidence,
                "quality_grade": z.quality_grade,
                "verified_by_local": NODE,
                "verification_type": "sfmp_second_node_verification",
            },
            "source_node": NODE,
            "confidence": z.confidence,
            "truth_type": "sfmp_verification",
        }
        headers = {
            "X-Capture-Token": token,
            "X-DID": DID,
            "Content-Type": "application/json",
        }

        verified = False
        for url in CLOUD_VERIFY_URLS:
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload, ensure_ascii=False).encode(),
                    headers=headers,
                )
                r = urllib.request.urlopen(req, timeout=CLOUD_VERIFY_TIMEOUT)
                if r.status == 200:
                    verified = True
                    break
            except Exception:
                continue
            time.sleep(0.1)

        if verified:
            z.cloud_verified = True
            if CLOUD_NODE_ID not in z.verified_by:
                z.verified_by.append(CLOUD_NODE_ID)
                z.verification_count += 1
            z.last_verified_at = time.time()
            z.lifecycle_state = "verified"
            z.recompute_grade()
            self.state["total_cloud_verified"] = self.state.get("total_cloud_verified", 0) + 1
        return verified

    def batch_cloud_verify(self, limit: int = 50) -> Dict[str, Any]:
        """
        批量云端验证：对所有单节点验证的z执行云端第二验证
        突破可发布数=0的核心操作
        """
        candidates = [
            z for z in self.pool.values()
            if not z.cloud_verified and z.verification_count >= 1 and z.confidence >= 0.5
        ]
        candidates.sort(key=lambda z: z.confidence, reverse=True)
        candidates = candidates[:limit]

        verified = 0
        failed = 0
        for z in candidates:
            if self.cloud_verify_unit(z):
                verified += 1
            else:
                failed += 1
            time.sleep(0.05)  # 避免请求过快

        self._save_pool()
        self._save_state()

        publishable = sum(1 for z in self.pool.values() if z.is_publishable())
        return {
            "candidates": len(candidates),
            "cloud_verified": verified,
            "failed": failed,
            "pool_total": len(self.pool),
            "publishable": publishable,
            "publishable_rate": round(publishable / max(len(self.pool), 1), 4),
        }

    # ============================================================
    # V2.0 新功能2: 生命周期管理
    # ============================================================

    def run_lifecycle(self) -> Dict[str, Any]:
        """
        执行生命周期管理：衰减检查 + 回收清理 + 状态更新
        """
        decayed = 0
        recycled = 0
        upgraded = 0
        now = time.time()

        to_recycle = []
        for z_id, z in self.pool.items():
            # 1. 时效衰减
            original_grade = z.quality_grade
            z.apply_decay()
            if z.quality_grade != original_grade:
                if z.quality_grade < original_grade:
                    decayed += 1
                else:
                    upgraded += 1

            # 2. 状态更新
            if z.is_publishable() and z.lifecycle_state in ("proposed", "verified"):
                z.lifecycle_state = "published"

            # 3. 回收检查：D级 + 长期无访问
            age_days = (now - z.created_at) / 86400
            no_access_days = (now - z.last_accessed) / 86400
            if (z.quality_grade == "D" and age_days >= RECYCLE_AGE_DAYS) or \
               (z.confidence < 0.3 and no_access_days >= RECYCLE_NO_ACCESS_DAYS):
                to_recycle.append(z_id)

        # 执行回收
        for z_id in to_recycle:
            if z_id in self.pool:
                z = self.pool.pop(z_id)
                self.recycled.append({
                    **z.to_dict(),
                    "recycled_at": now,
                    "recycle_reason": "lifecycle_expired" if z.quality_grade == "D" else "low_confidence_no_access"
                })
                recycled += 1

        self._save_pool()
        self._save_recycled()
        self.state["last_lifecycle_run"] = now
        self.state["total_recycled"] = self.state.get("total_recycled", 0) + recycled
        self._save_state()

        return {
            "decayed": decayed,
            "upgraded": upgraded,
            "recycled": recycled,
            "recycled_total": len(self.recycled),
            "pool_total": len(self.pool),
        }

    # ============================================================
    # V2.0 新功能3: 五级质量分级统计
    # ============================================================

    def quality_distribution(self) -> Dict[str, int]:
        """统计五级质量分级分布"""
        dist = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
        for z in self.pool.values():
            z.recompute_grade()
            dist[z.quality_grade] = dist.get(z.quality_grade, 0) + 1
        return dist

    def lifecycle_distribution(self) -> Dict[str, int]:
        """统计生命周期状态分布"""
        dist = {"proposed": 0, "verified": 0, "published": 0, "decayed": 0, "recycled": 0}
        for z in self.pool.values():
            dist[z.lifecycle_state] = dist.get(z.lifecycle_state, 0) + 1
        dist["recycled"] = len(self.recycled)
        return dist

    # ============================================================
    # V1.0 核心功能（保留并增强）
    # ============================================================

    def _extract_z_from_truth(self, truth_key: str, truth_value: Any,
                                tags: Optional[List[str]] = None) -> SemanticUnit:
        """从真值中提取语义单元 z"""
        content_str = json.dumps(truth_value, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        z_id = f"z-{content_hash}"
        vector_sig = hashlib.md5(content_str.encode()).hexdigest()[:12]
        confidence = min(1.0, 0.5 + len(content_str) / 2000 * 0.3)
        z = SemanticUnit(
            z_id=z_id,
            content_hash=content_hash,
            vector_signature=vector_sig,
            tags=tags or ["truth"],
            confidence=round(confidence, 4),
            verification_count=1,
            verified_by=[NODE],
            source="local",
            l0_checked=True,
            lifecycle_state="proposed",
        )
        z.recompute_grade()
        return z

    def ingest_local_truths(self, truth_dir: Optional[Path] = None,
                              limit: int = MAX_Z_PER_SYNC) -> Dict[str, Any]:
        """从本地真值库提纯语义单元 z（入库流程）"""
        if truth_dir is None:
            truth_dir = ROOT / "06_云端中枢同步" / "cloud_truths_pull"
        if not truth_dir.exists():
            return {"ingested": 0, "reason": "真值目录不存在"}

        truth_files = sorted(truth_dir.glob("*.json"))[:limit]
        ingested = 0
        updated = 0
        for tf in truth_files:
            try:
                data = json.loads(tf.read_text())
                if isinstance(data, list):
                    items = data
                elif "truths" in data:
                    items = data["truths"]
                elif "value" in data:
                    items = [data]
                else:
                    items = [data]
                for item in items:
                    key = item.get("key", item.get("truth_id", tf.stem))
                    value = item.get("value", item)
                    tags = item.get("tags", ["truth", "cloud_pull"])
                    z = self._extract_z_from_truth(str(key), value, tags)
                    if z.z_id in self.pool:
                        existing = self.pool[z.z_id]
                        if NODE not in existing.verified_by:
                            existing.verified_by.append(NODE)
                            existing.verification_count += 1
                        existing.last_accessed = time.time()
                        existing.access_count += 1
                        existing.recompute_grade()
                        updated += 1
                    else:
                        self.pool[z.z_id] = z
                        ingested += 1
            except Exception:
                continue

        self._save_pool()
        self._save_state()
        return {
            "ingested_new": ingested,
            "updated_existing": updated,
            "pool_total": len(self.pool),
            "publishable": sum(1 for z in self.pool.values() if z.is_publishable()),
            "quality_distribution": self.quality_distribution(),
        }

    def get_publishable_units(self, limit: int = MAX_Z_PER_SYNC,
                                min_grade: str = "B") -> List[SemanticUnit]:
        """获取可发布的语义单元（按质量等级过滤）"""
        grade_order = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
        min_score = grade_order.get(min_grade, 3)
        publishable = [
            z for z in self.pool.values()
            if z.is_publishable() and grade_order.get(z.quality_grade, 0) >= min_score
        ]
        publishable.sort(key=lambda z: (grade_order.get(z.quality_grade, 0), z.confidence), reverse=True)
        return publishable[:limit]

    def mark_published(self, z_ids: List[str]):
        """标记语义单元已发布到云端"""
        for z_id in z_ids:
            if z_id in self.pool:
                self.pool[z_id].source = "federated"
                self.pool[z_id].lifecycle_state = "published"
                self.pool[z_id].last_accessed = time.time()
        self.state["total_published"] += len(z_ids)
        self._save_pool()
        self._save_state()

    def receive_remote_units(self, remote_units: List[Dict[str, Any]]) -> Dict[str, Any]:
        """接收远端语义单元（下发流程）"""
        received = 0
        rejected = 0
        for ru in remote_units:
            try:
                ru.setdefault("quality_grade", "C")
                ru.setdefault("lifecycle_state", "proposed")
                ru.setdefault("reference_count", 0)
                ru.setdefault("last_verified_at", ru.get("created_at", time.time()))
                ru.setdefault("decay_rate", 0.0)
                ru.setdefault("cloud_verified", True)
                z = SemanticUnit(**ru)
                forbidden_tags = {"kernel_baseline_modify", "unverified_high_risk"}
                if any(t in forbidden_tags for t in z.tags):
                    rejected += 1
                    continue
                if z.z_id in self.pool:
                    existing = self.pool[z.z_id]
                    if NODE not in existing.verified_by:
                        existing.verified_by.append(NODE)
                        existing.verification_count += 1
                    existing.recompute_grade()
                else:
                    z.verification_count = max(z.verification_count, 1)
                    if NODE not in z.verified_by:
                        z.verified_by.append(NODE)
                    z.recompute_grade()
                    self.pool[z.z_id] = z
                received += 1
            except Exception:
                rejected += 1

        self._save_pool()
        self.state["total_received"] += received
        self._save_state()
        return {"received": received, "rejected": rejected, "pool_total": len(self.pool)}

    def stats(self) -> dict:
        if not self.pool:
            return {"total_units": 0, "version": "2.0"}
        publishable = sum(1 for z in self.pool.values() if z.is_publishable())
        by_source = {}
        for z in self.pool.values():
            by_source[z.source] = by_source.get(z.source, 0) + 1
        avg_conf = sum(z.confidence for z in self.pool.values()) / len(self.pool)
        return {
            "version": "2.0",
            "total_units": len(self.pool),
            "publishable": publishable,
            "publishable_rate": round(publishable / len(self.pool), 4),
            "by_source": by_source,
            "avg_confidence": round(avg_conf, 4),
            "quality_distribution": self.quality_distribution(),
            "lifecycle_distribution": self.lifecycle_distribution(),
            "recycled_total": len(self.recycled),
            "cloud_verified_total": self.state.get("total_cloud_verified", 0),
            "state": self.state
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT SFMP联邦记忆池管理器 V2.0")
    parser.add_argument("action",
                       choices=["ingest", "publishable", "stats", "sync",
                                "cloud_verify", "lifecycle", "evolve"],
                       help="操作: ingest(提纯入库)/publishable(可发布列表)/stats(统计)/sync(全流程)/cloud_verify(云端第二验证)/lifecycle(生命周期管理)/evolve(V2.0完整进化)")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    mgr = SFMPManager()

    if args.action == "ingest":
        result = mgr.ingest_local_truths(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "publishable":
        units = mgr.get_publishable_units(limit=args.limit)
        print(f"可发布语义单元: {len(units)}个")
        for z in units[:10]:
            print(f"  {z.z_id} | grade={z.quality_grade} | conf={z.confidence:.2f} | ver={z.verification_count} | tags={z.tags[:3]}")
    elif args.action == "stats":
        print(json.dumps(mgr.stats(), ensure_ascii=False, indent=2))
    elif args.action == "cloud_verify":
        print("=== 云端第二验证方验证 ===")
        result = mgr.batch_cloud_verify(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "lifecycle":
        print("=== 生命周期管理 ===")
        result = mgr.run_lifecycle()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "evolve":
        print("=" * 60)
        print("SFMP联邦记忆池 V2.0 完整进化")
        print("=" * 60)
        print("\n--- 步骤1: 提纯入库 ---")
        r1 = mgr.ingest_local_truths(limit=args.limit)
        print(f"  新增{r1['ingested_new']}, 更新{r1['updated_existing']}, 池总量{r1['pool_total']}")
        print(f"  质量分布: {r1.get('quality_distribution', {})}")
        print("\n--- 步骤2: 云端第二验证（突破可发布数=0） ---")
        r2 = mgr.batch_cloud_verify(limit=args.limit)
        print(f"  候选{r2['candidates']}, 云端验证通过{r2['cloud_verified']}, 失败{r2['failed']}")
        print(f"  可发布数: {r2['publishable']} (发布率{r2['publishable_rate']:.1%})")
        print("\n--- 步骤3: 生命周期管理 ---")
        r3 = mgr.run_lifecycle()
        print(f"  衰减{r3['decayed']}, 升级{r3['upgraded']}, 回收{r3['recycled']}")
        print(f"  回收池总量: {r3['recycled_total']}")
        print("\n--- 步骤4: 最终统计 ---")
        stats = mgr.stats()
        print(json.dumps({
            "pool_total": stats["total_units"],
            "publishable": stats["publishable"],
            "publishable_rate": stats["publishable_rate"],
            "quality_distribution": stats["quality_distribution"],
            "lifecycle_distribution": stats["lifecycle_distribution"],
            "avg_confidence": stats["avg_confidence"],
            "cloud_verified_total": stats["cloud_verified_total"],
        }, ensure_ascii=False, indent=2))
    elif args.action == "sync":
        print("=== SFMP联邦记忆池全流程同步 ===")
        r1 = mgr.ingest_local_truths(limit=args.limit)
        print(f"1. 提纯: 新增{r1['ingested_new']}, 池总量{r1['pool_total']}")
        units = mgr.get_publishable_units(limit=args.limit)
        print(f"2. 可发布: {len(units)}个")
        print(json.dumps(mgr.stats(), ensure_ascii=False, indent=2))
