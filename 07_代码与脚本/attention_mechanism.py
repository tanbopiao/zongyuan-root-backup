# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

attention_mechanism.py — 选择性注意机制（Selective Attention）

设计背景
========
实现全局工作空间理论中的"剧场聚光灯"（spotlight of consciousness）：
当多个并行专用处理器同时产生候选信息时，注意力机制执行 up-tree
竞争，筛选出显著性最高的少数候选进入全局工作空间广播。

核心机制
========
1. 显著性评分（salience score）：
       salience = w_novelty    * novelty
              + w_importance  * importance
              + w_urgency     * urgency
              + w_relevance   * relevance
   各分量归一化到 [0, 1]，权重可配置。

2. up-tree 竞争：
   处理器候选自底向上汇聚；本实现以"分层竞争筛选"建模：
     - 候选先按类型分桶（coarse layer），桶内取局部胜者；
     - 局部胜者进入顶层（fine layer）全局竞争；
     - 最终 1 个（或少数几个）获胜者进入全局工作空间。

3. 注意焦点（attention focus）：
   可设置当前关注的信息类型/目标，对匹配候选施加正向偏置。

4. 抑制 / 不应期（refractory suppression）：
   获胜信息广播后，其他竞争候选（或同一处理器的高频重复）被暂时
   抑制，在 duration 秒内不得再次获胜，模拟神经侧抑制与不应期。

接口
====
  - compete(candidates) -> winner（或 winner 列表）
  - compute_salience(candidate) -> float
  - set_focus(focus)
  - suppress(cid, duration)

纯 Python 3.8+ 标准库实现。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 候选数据结构
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """处理器产出的待竞争候选信息。

    属性
    ----
    cid:
        候选唯一 ID。
    processor_id:
        产出该候选的处理器 ID。
    content:
        候选载荷（语义内容描述，任意可序列化结构）。
    category:
        候选类别（用于 up-tree 分桶 / 注意焦点匹配）。
    novelty / importance / urgency:
        显著性三维原始分（[0,1]）。
    timestamp:
        产生时间戳。
    """

    cid: str
    processor_id: str
    content: object
    category: str
    novelty: float = 0.5
    importance: float = 0.5
    urgency: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def relevance_vs(self, focus: Optional[str]) -> float:
        """计算与当前注意焦点的相关性（[0,1]）。

        简单可解释规则：焦点为空 -> 中性 0.5；类别完全匹配 -> 1.0；
        否则 0.3。生产环境可替换为嵌入相似度。
        """
        if not focus:
            return 0.5
        if self.category == focus:
            return 1.0
        # 子串模糊匹配（如 focus="self_check" 命中 category="self_check_coherence"）
        if focus in self.category or self.category in focus:
            return 0.7
        return 0.3


# ---------------------------------------------------------------------------
# 注意力机制
# ---------------------------------------------------------------------------

class AttentionMechanism:
    """选择性注意机制：显著性加权 + up-tree 竞争 + 注意门控 + 侧抑制。"""

    def __init__(
        self,
        w_novelty: float = 0.25,
        w_importance: float = 0.30,
        w_urgency: float = 0.20,
        w_relevance: float = 0.25,
        winner_count: int = 1,
        refractory_default: float = 2.0,
    ) -> None:
        """
        :param w_*: 显著性四维权重（内部自动归一化）。
        :param winner_count: 每轮竞争最多选出的获胜者数量。
        :param refractory_default: 被抑制候选的默认不应期（秒）。
        """
        raw = {
            "novelty": w_novelty,
            "importance": w_importance,
            "urgency": w_urgency,
            "relevance": w_relevance,
        }
        total = sum(raw.values()) or 1.0
        self.weights = {k: v / total for k, v in raw.items()}

        self.winner_count = max(1, winner_count)
        self.refractory_default = refractory_default

        self.focus: Optional[str] = None
        # 被抑制候选 cid -> 解除时间戳
        self._suppressed_until: Dict[str, float] = {}
        # 历史：每轮竞争的 (winner_cids, ranked)
        self.competition_log: List[Dict[str, object]] = []

    # -- 注意门控 ---------------------------------------------------------

    def set_focus(self, focus: Optional[str]) -> None:
        """设置/清除当前注意焦点（为 None 时退化为无偏竞争）。"""
        self.focus = focus

    # -- 显著性 ----------------------------------------------------------

    def compute_salience(self, candidate: Candidate) -> float:
        """计算候选的显著性分数（加权求和，结果 [0, ~1.5]）。

        relevance 维度通过当前注意焦点动态计算。
        """
        relevance = candidate.relevance_vs(self.focus)
        s = (
            self.weights["novelty"] * _clip01(candidate.novelty)
            + self.weights["importance"] * _clip01(candidate.importance)
            + self.weights["urgency"] * _clip01(candidate.urgency)
            + self.weights["relevance"] * _clip01(relevance)
        )
        return float(s)

    # -- 抑制机制 ---------------------------------------------------------

    def suppress(self, cid: str, duration: Optional[float] = None) -> None:
        """将候选置入不应期；duration 秒内不得获胜。"""
        d = self.refractory_default if duration is None else duration
        self._suppressed_until[cid] = time.time() + max(0.0, d)

    def is_suppressed(self, cid: str) -> bool:
        """查询候选当前是否处于不应期，并清理过期记录。"""
        now = time.time()
        expired = [c for c, until in self._suppressed_until.items() if until <= now]
        for c in expired:
            self._suppressed_until.pop(c, None)
        return cid in self._suppressed_until

    # -- up-tree 竞争 -----------------------------------------------------

    @staticmethod
    def _coarse_layer(candidates: List[Tuple[Candidate, float]]) -> Dict[str, List[Tuple[Candidate, float]]]:
        """up-tree 第一层：按类别分桶（coarse segregation）。"""
        buckets: Dict[str, List[Tuple[Candidate, float]]] = {}
        for cand, sal in candidates:
            buckets.setdefault(cand.category, []).append((cand, sal))
        return buckets

    @staticmethod
    def _fine_layer(
        bucket_winners: List[Tuple[Candidate, float]],
        winner_count: int,
    ) -> List[Tuple[Candidate, float]]:
        """up-tree 第二层：各桶胜者进入顶层全局竞争，取 salience 最高者。"""
        ranked = sorted(bucket_winners, key=lambda x: x[1], reverse=True)
        return ranked[:winner_count]

    def compete(
        self,
        candidates: List[Candidate],
        suppress_losers: bool = True,
    ) -> List[Tuple[Candidate, float]]:
        """执行一轮 up-tree 竞争。

        流程：
          1. 过滤掉处于不应期的候选；
          2. 计算每个剩余候选的显著性；
          3. coarse layer：按类别分桶，桶内取 salience 最高的局部胜者；
          4. fine layer：局部胜者顶层竞争，取 top-``winner_count``；
          5. 对未获胜的同轮候选施加侧抑制（不应期）。

        :return: 获胜 (candidate, salience) 列表，按 salience 降序。
        """
        now = time.time()
        active: List[Tuple[Candidate, float]] = []
        suppressed_in_round: List[Candidate] = []
        for cand in candidates:
            # 过期抑制自动清理
            until = self._suppressed_until.get(cand.cid)
            if until is not None and until <= now:
                self._suppressed_until.pop(cand.cid, None)
            if cand.cid in self._suppressed_until:
                suppressed_in_round.append(cand)
                continue
            active.append((cand, self.compute_salience(cand)))

        # coarse layer：桶内局部胜者
        buckets = self._coarse_layer(active)
        bucket_winners: List[Tuple[Candidate, float]] = []
        for cat, items in buckets.items():
            items.sort(key=lambda x: x[1], reverse=True)
            bucket_winners.append(items[0])  # 每桶最高者晋级

        # fine layer：全局竞争
        winners = self._fine_layer(bucket_winners, self.winner_count)

        # 侧抑制：本轮未获胜的活跃候选进入不应期
        winner_cids = {c.cid for c, _ in winners}
        if suppress_losers:
            for cand, sal in active:
                if cand.cid not in winner_cids:
                    self.suppress(cand.cid)

        # 记录竞争日志
        self.competition_log.append({
            "ts": round(now, 3),
            "focus": self.focus,
            "input_count": len(candidates),
            "suppressed_in_input": len(suppressed_in_round),
            "coarse_buckets": {k: len(v) for k, v in buckets.items()},
            "winner_ids": [c.cid for c, _ in winners],
            "winner_processors": [c.processor_id for c, _ in winners],
            "winner_salience": [round(s, 4) for _, s in winners],
        })
        return winners


def _clip01(x: float) -> float:
    """截断到 [0, 1]。"""
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------------------
# 模块自检演示
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0")
    print("attention_mechanism.py — 多候选竞争 / 显著性 / 抑制机制演示")
    print("=" * 72)

    attn = AttentionMechanism(winner_count=2, refractory_default=1.5)
    print(f"\n显著性权重(归一化): "
          f"novelty={attn.weights['novelty']:.2f} "
          f"importance={attn.weights['importance']:.2f} "
          f"urgency={attn.weights['urgency']:.2f} "
          f"relevance={attn.weights['relevance']:.2f}")

    # 构造 6 个候选，来自不同处理器
    cands = [
        Candidate(cid="c1", processor_id="sc_goal",
                  content="检测到目标偏离 0.18", category="self_check_goal",
                  novelty=0.3, importance=0.9, urgency=0.8),
        Candidate(cid="c2", processor_id="sc_coherence",
                  content="连贯性基线漂移", category="self_check_coherence",
                  novelty=0.6, importance=0.6, urgency=0.4),
        Candidate(cid="c3", processor_id="closed_loop_engine",
                  content="触发纠错闭环 #7", category="correction",
                  novelty=0.7, importance=0.8, urgency=0.95),
        Candidate(cid="c4", processor_id="memory_gateway",
                  content="检索到锁档资产 v2.1", category="memory",
                  novelty=0.4, importance=0.5, urgency=0.2),
        Candidate(cid="c5", processor_id="same_source_protocol",
                  content="确权锚点 Ω₀⊂⊙∞⊂Ω 校验通过", category="attestation",
                  novelty=0.2, importance=0.95, urgency=0.3),
        Candidate(cid="c6", processor_id="sc_reflection",
                  content="元认知：本轮整合度不足", category="self_check_reflection",
                  novelty=0.8, importance=0.7, urgency=0.5),
    ]

    print("\n--- 第 1 轮：无注意焦点竞争 ---")
    w1 = attn.compete(cands)
    for c, s in w1:
        print(f"  WINNER  {c.processor_id:<22} sal={s:.3f}  | {c.content}")

    print("\n显著性逐分（验证 compute_salience）:")
    for c in cands:
        print(f"  {c.cid} {c.processor_id:<22} sal={attn.compute_salience(c):.3f}")

    print("\n--- 第 2 轮：设置注意焦点 = self_check_goal（门控偏置）---")
    attn.set_focus("self_check_goal")
    w2 = attn.compete(cands)
    for c, s in w2:
        print(f"  WINNER  {c.processor_id:<22} sal={s:.3f}  | {c.content}")

    print("\n--- 第 3 轮：验证不应期抑制（刚被抑制者无法获胜）---")
    w3 = attn.compete(cands)  # 同一批候选复投
    for c, s in w3:
        print(f"  WINNER  {c.processor_id:<22} sal={s:.3f}  | {c.content}")

    print("\n最近竞争日志:")
    for log in attn.competition_log:
        print(f"  round winners={log['winner_processors']} "
              f"sal={log['winner_salience']} focus={log['focus']}")
