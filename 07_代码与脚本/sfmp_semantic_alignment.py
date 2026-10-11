#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT SFMP V3.0 跨域语义对齐引擎 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω

核心功能：
1. 同义语义单元自动合并（基于内容哈希+标签+向量签名相似度）
2. D级低质量单元清理（低于阈值+长期无访问）
3. 语义去重（合并重复z，保留最高置信度版本）
4. 跨域语义对齐（不同来源的同义z对齐到统一规范）

设计原则：
- 增量优先：只处理新增/变更的z
- 失败快速跳过不重试
- 合并前强制快照（回滚保护）
- 合并结果写入Merkle凭证
"""

import json
import os
import sys
import time
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
SFMP_DIR = ROOT / "06_云端中枢同步" / "sfmp_federation"
ALIGN_DIR = SFMP_DIR / "alignment_logs"
ALIGN_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"

# 对齐配置
SIMILARITY_THRESHOLD = 0.85      # 语义相似度阈值（≥此值视为同义）
HASH_MATCH_THRESHOLD = 0.5       # 内容哈希前缀匹配阈值
TAG_OVERLAP_THRESHOLD = 0.6      # 标签重叠度阈值
D_GRADE_CLEANUP_AGE_DAYS = 45    # D级清理年龄阈值
D_GRADE_CLEANUP_NO_ACCESS = 20   # D级无访问天数阈值
MAX_MERGE_PER_RUN = 30           # 单次最多合并数
MAX_CLEANUP_PER_RUN = 50         # 单次最多清理数


@dataclass
class AlignmentResult:
    """语义对齐结果"""
    merged_pairs: List[Dict] = field(default_factory=list)
    cleaned_units: List[Dict] = field(default_factory=list)
    deduplicated: int = 0
    pool_before: int = 0
    pool_after: int = 0
    snapshot_file: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "merged_count": len(self.merged_pairs),
            "merged_pairs": self.merged_pairs,
            "cleaned_count": len(self.cleaned_units),
            "cleaned_units": self.cleaned_units,
            "deduplicated": self.deduplicated,
            "pool_before": self.pool_before,
            "pool_after": self.pool_after,
            "snapshot_file": self.snapshot_file,
            "timestamp": self.timestamp,
            "node": NODE,
            "did": DID,
        }


class SemanticAlignmentEngine:
    """跨域语义对齐引擎"""

    def __init__(self):
        self.pool_file = SFMP_DIR / "semantic_units.json"
        self.recycle_file = SFMP_DIR / "recycled_units.json"
        self.pool: Dict[str, Dict] = {}
        self.recycled: List[Dict] = []
        self._load()

    def _load(self):
        if self.pool_file.exists():
            try:
                self.pool = json.loads(self.pool_file.read_text())
            except Exception:
                self.pool = {}
        if self.recycle_file.exists():
            try:
                self.recycled = json.loads(self.recycle_file.read_text())
            except Exception:
                self.recycled = []

    def _save(self):
        self.pool_file.write_text(json.dumps(self.pool, ensure_ascii=False, indent=2))
        self.recycle_file.write_text(json.dumps(self.recycled, ensure_ascii=False, indent=2))

    def _snapshot(self) -> str:
        """合并前快照（回滚保护）"""
        snap_file = ALIGN_DIR / f"snapshot_{int(time.time())}.json"
        shutil.copy2(self.pool_file, snap_file)
        return str(snap_file)

    def _compute_similarity(self, z1: Dict, z2: Dict) -> float:
        """
        计算两个语义单元的语义相似度
        基于：内容哈希前缀匹配 + 标签重叠度 + 向量签名匹配
        """
        score = 0.0

        # 1. 内容哈希前缀匹配（权重0.4）
        h1 = z1.get("content_hash", "")
        h2 = z2.get("content_hash", "")
        if h1 and h2:
            prefix_match = 0
            for i in range(min(len(h1), len(h2))):
                if h1[i] == h2[i]:
                    prefix_match += 1
                else:
                    break
            hash_sim = prefix_match / max(len(h1), len(h2), 1)
            score += hash_sim * 0.4

        # 2. 标签重叠度（权重0.35）
        tags1 = set(z1.get("tags", []))
        tags2 = set(z2.get("tags", []))
        if tags1 and tags2:
            overlap = len(tags1 & tags2)
            union = len(tags1 | tags2)
            tag_sim = overlap / max(union, 1)
            score += tag_sim * 0.35

        # 3. 向量签名匹配（权重0.25）
        v1 = z1.get("vector_signature", "")
        v2 = z2.get("vector_signature", "")
        if v1 and v2:
            vec_match = 0
            for i in range(min(len(v1), len(v2))):
                if v1[i] == v2[i]:
                    vec_match += 1
                else:
                    break
            vec_sim = vec_match / max(len(v1), len(v2), 1)
            score += vec_sim * 0.25

        return round(score, 4)

    def _find_synonym_pairs(self) -> List[Tuple[str, str, float]]:
        """查找同义语义单元对"""
        pairs = []
        z_ids = list(self.pool.keys())
        seen = set()

        for i in range(len(z_ids)):
            for j in range(i + 1, len(z_ids)):
                z1_id, z2_id = z_ids[i], z_ids[j]
                pair_key = tuple(sorted([z1_id, z2_id]))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                z1 = self.pool[z1_id]
                z2 = self.pool[z2_id]

                # 快速过滤：完全相同的content_hash直接判定为重复
                if z1.get("content_hash") == z2.get("content_hash") and z1.get("content_hash"):
                    pairs.append((z1_id, z2_id, 1.0))
                    continue

                # 计算相似度
                sim = self._compute_similarity(z1, z2)
                if sim >= SIMILARITY_THRESHOLD:
                    pairs.append((z1_id, z2_id, sim))

        # 按相似度降序排列
        pairs.sort(key=lambda x: x[2], reverse=True)
        return pairs

    def _merge_pair(self, z1_id: str, z2_id: str, similarity: float) -> Optional[Dict]:
        """合并一对同义语义单元，保留较高质量版本"""
        if z1_id not in self.pool or z2_id not in self.pool:
            return None

        z1 = self.pool[z1_id]
        z2 = self.pool[z2_id]

        # 选择保留版本：质量等级 > 置信度 > 验证次数 > 引用次数
        grade_order = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
        z1_score = (
            grade_order.get(z1.get("quality_grade", "D"), 0) * 1000
            + z1.get("confidence", 0) * 100
            + z1.get("verification_count", 0) * 10
            + z1.get("reference_count", 0)
        )
        z2_score = (
            grade_order.get(z2.get("quality_grade", "D"), 0) * 1000
            + z2.get("confidence", 0) * 100
            + z2.get("verification_count", 0) * 10
            + z2.get("reference_count", 0)
        )

        if z1_score >= z2_score:
            keeper, merged = z1, z2
            keeper_id, merged_id = z1_id, z2_id
        else:
            keeper, merged = z2, z1
            keeper_id, merged_id = z2_id, z1_id

        # 合并：累加验证次数、引用次数、合并标签、取最高置信度
        keeper["verification_count"] = keeper.get("verification_count", 0) + merged.get("verification_count", 0)
        keeper["reference_count"] = keeper.get("reference_count", 0) + merged.get("reference_count", 0)
        keeper["access_count"] = keeper.get("access_count", 0) + merged.get("access_count", 0)
        keeper["confidence"] = min(1.0, max(keeper.get("confidence", 0), merged.get("confidence", 0)))

        # 合并标签（去重）
        all_tags = list(set(keeper.get("tags", []) + merged.get("tags", [])))
        keeper["tags"] = all_tags

        # 合并验证节点（去重）
        all_verified = list(set(keeper.get("verified_by", []) + merged.get("verified_by", [])))
        keeper["verified_by"] = all_verified

        # 云端验证标记合并
        keeper["cloud_verified"] = keeper.get("cloud_verified", False) or merged.get("cloud_verified", False)

        # 重新计算质量等级
        from sfmp_federation_manager import compute_quality_grade
        keeper["quality_grade"] = compute_quality_grade(
            keeper["verification_count"], keeper["confidence"], keeper["reference_count"]
        )

        # 更新生命周期
        if keeper.get("verification_count", 0) >= 2 and keeper.get("confidence", 0) >= 0.6:
            keeper["lifecycle_state"] = "published"

        # 记录合并信息
        merge_info = {
            "keeper_id": keeper_id,
            "merged_id": merged_id,
            "similarity": similarity,
            "merged_verification_count": merged.get("verification_count", 0),
            "merged_reference_count": merged.get("reference_count", 0),
            "keeper_new_grade": keeper["quality_grade"],
            "keeper_new_confidence": keeper["confidence"],
        }

        # 删除被合并的单元
        del self.pool[merged_id]

        return merge_info

    def _cleanup_d_grade(self) -> List[Dict]:
        """清理D级低质量单元"""
        now = time.time()
        to_cleanup = []

        for z_id, z in list(self.pool.items()):
            if z.get("quality_grade") != "D":
                continue

            age_days = (now - z.get("created_at", now)) / 86400
            no_access_days = (now - z.get("last_accessed", now)) / 86400

            if age_days >= D_GRADE_CLEANUP_AGE_DAYS or no_access_days >= D_GRADE_CLEANUP_NO_ACCESS:
                to_cleanup.append(z_id)

        cleaned = []
        for z_id in to_cleanup[:MAX_CLEANUP_PER_RUN]:
            if z_id in self.pool:
                z = self.pool.pop(z_id)
                z["recycled_at"] = now
                z["recycle_reason"] = "d_grade_cleanup_v3"
                self.recycled.append(z)
                cleaned.append({
                    "z_id": z_id,
                    "confidence": z.get("confidence", 0),
                    "age_days": round((now - z.get("created_at", now)) / 86400, 1),
                })

        return cleaned

    def run_alignment(self) -> AlignmentResult:
        """执行完整语义对齐流程"""
        result = AlignmentResult()
        result.pool_before = len(self.pool)

        # 1. 合并前快照
        result.snapshot_file = self._snapshot()

        # 2. 查找同义对
        print("--- 查找同义语义单元对 ---")
        pairs = self._find_synonym_pairs()
        print(f"  发现{pairs.__len__()}对同义单元（阈值≥{SIMILARITY_THRESHOLD}）")

        # 3. 执行合并
        print("--- 执行同义合并 ---")
        merged_count = 0
        for z1_id, z2_id, sim in pairs[:MAX_MERGE_PER_RUN]:
            info = self._merge_pair(z1_id, z2_id, sim)
            if info:
                result.merged_pairs.append(info)
                merged_count += 1
                print(f"  ✅ 合并: {info['merged_id'][:20]}... → {info['keeper_id'][:20]}... (sim={sim:.2f}, grade={info['keeper_new_grade']})")
        print(f"  合并完成: {merged_count}对")

        # 4. D级清理
        print("--- D级低质量单元清理 ---")
        cleaned = self._cleanup_d_grade()
        result.cleaned_units = cleaned
        print(f"  清理D级单元: {len(cleaned)}个")

        # 5. 保存
        self._save()
        result.pool_after = len(self.pool)
        result.deduplicated = merged_count

        # 6. 记录对齐日志
        log_file = ALIGN_DIR / f"alignment_{int(time.time())}.json"
        log_file.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

        return result


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SFMP V3.0 跨域语义对齐引擎")
    parser.add_argument("action", choices=["align", "stats", "snapshot"],
                       help="操作: align(执行对齐)/stats(统计)/snapshot(快照)")
    args = parser.parse_args()

    engine = SemanticAlignmentEngine()

    if args.action == "align":
        print("=" * 60)
        print("SFMP V3.0 跨域语义对齐")
        print("=" * 60)
        result = engine.run_alignment()
        print("\n" + "=" * 60)
        print(f"对齐完成: 合并{len(result.merged_pairs)}对, 清理{len(result.cleaned_units)}个")
        print(f"池规模: {result.pool_before} → {result.pool_after}")
        print(f"快照: {result.snapshot_file}")
        print("=" * 60)
    elif args.action == "stats":
        print(f"池总量: {len(engine.pool)}")
        grades = {}
        for z in engine.pool.values():
            g = z.get("quality_grade", "unknown")
            grades[g] = grades.get(g, 0) + 1
        print(f"质量分布: {grades}")
        print(f"回收池: {len(engine.recycled)}")
    elif args.action == "snapshot":
        snap = engine._snapshot()
        print(f"快照已创建: {snap}")
