#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 标签规范化与跨引擎对齐模块 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω

解决记忆索引与SFMP联邦池标签体系不兼容问题：
- 记忆索引: type:事实 / topic:云端真值 / attr:重要
- SFMP: truth / cloud_pull / important

功能：
1. 标签同义词映射表（统一两套体系）
2. 记忆索引标签规范化（追加SFMP兼容标签）
3. 跨引擎标签匹配增强（支持前缀匹配+同义词）
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
MEMORY_INDEX_FILE = ROOT / "06_云端中枢同步" / "memory_index_store.json"
SFMP_POOL_FILE = ROOT / "06_云端中枢同步" / "sfmp_federation" / "semantic_units.json"

# 标签同义词映射表（记忆索引标签 → SFMP兼容标签列表）
TAG_NORMALIZATION_MAP = {
    # type前缀
    "type:事实": ["truth", "fact"],
    "type:规则": ["rule", "meta_rule"],
    "type:配置": ["config", "setting"],
    "type:日志": ["log", "audit"],
    "type:事件": ["event"],
    "type:告警": ["alert", "warning"],
    # topic前缀
    "topic:云端真值": ["cloud_truth", "cloud_pull", "truth"],
    "topic:元意识": ["meta_awareness", "consciousness", "mi_signal"],
    "topic:双轴校验": ["dual_axis", "l0_check", "validation"],
    "topic:联邦记忆": ["sfmp", "federation", "semantic_unit"],
    "topic:自治内核": ["autonomy", "kernel", "zongyuan_root"],
    "topic:GASA": ["gasa", "invariant", "z3"],
    "topic:RSI": ["rsi", "self_improvement"],
    "topic:配额": ["quota", "resource"],
    "topic:飞书": ["feishu", "lark", "base"],
    # attr前缀
    "attr:重要": ["important", "high_priority"],
    "attr:高危": ["high_risk", "critical"],
    "attr:只读": ["readonly", "locked"],
    "attr:增量": ["incremental"],
    "attr:免费": ["free", "zero_cost"],
}

# 反向映射（SFMP标签 → 记忆索引兼容标签）
REVERSE_TAG_MAP = {}
for mem_tag, sfmp_tags in TAG_NORMALIZATION_MAP.items():
    for st in sfmp_tags:
        REVERSE_TAG_MAP.setdefault(st, []).append(mem_tag)


def normalize_memory_tags(original_tags: List[str]) -> List[str]:
    """将记忆索引标签规范化为SFMP兼容标签（保留原标签+追加兼容标签）"""
    normalized = list(original_tags)
    for tag in original_tags:
        if tag in TAG_NORMALIZATION_MAP:
            for compat_tag in TAG_NORMALIZATION_MAP[tag]:
                if compat_tag not in normalized:
                    normalized.append(compat_tag)
    return normalized


def normalize_sfmp_tags(original_tags: List[str]) -> List[str]:
    """将SFMP标签规范化为记忆索引兼容标签（保留原标签+追加兼容标签）"""
    normalized = list(original_tags)
    for tag in original_tags:
        if tag in REVERSE_TAG_MAP:
            for compat_tag in REVERSE_TAG_MAP[tag]:
                if compat_tag not in normalized:
                    normalized.append(compat_tag)
    return normalized


def compute_enhanced_similarity(tags1: Set[str], tags2: Set[str]) -> float:
    """
    增强版标签相似度计算（支持同义词匹配）
    将两边标签都规范化后计算重叠度
    """
    # 规范化两边标签
    norm1 = set()
    for t in tags1:
        norm1.add(t)
        if t in TAG_NORMALIZATION_MAP:
            norm1.update(TAG_NORMALIZATION_MAP[t])
        if t in REVERSE_TAG_MAP:
            norm1.update(REVERSE_TAG_MAP[t])

    norm2 = set()
    for t in tags2:
        norm2.add(t)
        if t in TAG_NORMALIZATION_MAP:
            norm2.update(TAG_NORMALIZATION_MAP[t])
        if t in REVERSE_TAG_MAP:
            norm2.update(REVERSE_TAG_MAP[t])

    if not norm1 or not norm2:
        return 0.0
    overlap = len(norm1 & norm2)
    union = len(norm1 | norm2)
    return overlap / max(union, 1)


def run_normalization() -> Dict:
    """执行全量标签规范化"""
    result = {
        "memory_updated": 0,
        "sfmp_updated": 0,
        "memory_total": 0,
        "sfmp_total": 0,
        "timestamp": time.time(),
    }

    # 1. 规范化记忆索引标签
    if MEMORY_INDEX_FILE.exists():
        data = json.loads(MEMORY_INDEX_FILE.read_text())
        memories = data.get("memories", {})
        result["memory_total"] = len(memories)

        for mem_id, mem in memories.items():
            original = mem.get("tags", [])
            normalized = normalize_memory_tags(original)
            if normalized != original:
                mem["tags"] = normalized
                mem["tags_normalized"] = True
                result["memory_updated"] += 1

        data["memories"] = memories
        MEMORY_INDEX_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # 2. 规范化SFMP标签
    if SFMP_POOL_FILE.exists():
        sfmp = json.loads(SFMP_POOL_FILE.read_text())
        result["sfmp_total"] = len(sfmp)

        for z_id, z in sfmp.items():
            original = z.get("tags", [])
            normalized = normalize_sfmp_tags(original)
            if normalized != original:
                z["tags"] = normalized
                z["tags_normalized"] = True
                result["sfmp_updated"] += 1

        SFMP_POOL_FILE.write_text(json.dumps(sfmp, ensure_ascii=False, indent=2))

    return result


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="标签规范化与跨引擎对齐")
    parser.add_argument("action", choices=["normalize", "test_match", "stats"])
    args = parser.parse_args()

    if args.action == "normalize":
        print("=== 标签规范化执行 ===")
        result = run_normalization()
        print(f"记忆索引更新: {result['memory_updated']}/{result['memory_total']}")
        print(f"SFMP更新: {result['sfmp_updated']}/{result['sfmp_total']}")
        print("规范化完成")
    elif args.action == "test_match":
        # 测试规范化后的匹配率
        mem_data = json.loads(MEMORY_INDEX_FILE.read_text())
        sfmp_data = json.loads(SFMP_POOL_FILE.read_text())
        memories = mem_data.get("memories", {})
        sfmp = sfmp_data

        matches = 0
        for mem_id, mem in list(memories.items())[:50]:
            mem_tags = set(mem.get("tags", []))
            best_sim = 0
            for z_id, z in sfmp.items():
                z_tags = set(z.get("tags", []))
                sim = compute_enhanced_similarity(mem_tags, z_tags)
                if sim > best_sim:
                    best_sim = sim
            if best_sim >= 0.3:
                matches += 1
        print(f"测试50条记忆，匹配率(≥0.3): {matches}/50 = {matches/50:.0%}")
    elif args.action == "stats":
        print(f"映射表条目: {len(TAG_NORMALIZATION_MAP)}")
        print(f"反向映射条目: {len(REVERSE_TAG_MAP)}")
