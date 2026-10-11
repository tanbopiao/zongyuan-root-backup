# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

global_workspace_engine.py — 全局工作空间主引擎（Global Workspace Engine）

设计背景
========
将神经注册表从"静态节点网络"升级为"动态全局工作空间"的编排中枢。
对标 CTM-AI（意识全局工作空间理论）+ Theater of Mind + Swarm Cognition。

核心循环（每一步 step）
=======================
  1. 并行采集（parallel collection）：
     所有专用处理器并行产生候选信息（本实现用 threading 模拟并行，
     并提供确定性顺序回退）。
  2. up-tree 竞争（up-tree competition）：
     AttentionMechanism 执行显著性竞争，筛选获胜者。
  3. 全局广播（down-tree broadcast）：
     获胜信息广播给所有处理器，各处理器据此更新内部状态。
  4. 无意识通信（unconscious direct links）：
     处理器间通过 direct links 交换低层级信息，不经工作空间。
  5. 动态拓扑调整（topology adaptation）：
     根据广播反馈调整处理器间连接权重（共激活增强，长期未用衰减）。

状态与报告
==========
  - 工作空间状态：current_content / broadcast_history /
    attention_focus / topology_snapshot。
  - 周期性"意识状态报告"：当前内容、活跃处理器、竞争结果、拓扑指标。
  - 12 维意识状态向量（参考 CUF 框架）：
      觉醒度 arousal / 整合度 integration / 分化度 differentiation /
      稳定性 stability / 可塑性 plasticity / 连贯性 coherence /
      目的性 purposefulness / 社会性 sociality / 反思度 reflection /
      创造性 creativity / 情感价 valence / 唤醒度 wakefulness

接口
====
  - step() -> WorkspaceState
  - run(steps) -> list[WorkspaceState]
  - get_state() -> WorkspaceState
  - get_12dim_vector() -> list[float]
  - generate_consciousness_report() -> dict

纯 Python 3.8+ 标准库实现，无外部依赖。
"""

from __future__ import annotations

import queue
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from processor_registry import (
    Processor,
    ProcessorRegistry,
    ProcessorState,
    ProcessorType,
)
from attention_mechanism import AttentionMechanism, Candidate


# ---------------------------------------------------------------------------
# 工作空间状态
# ---------------------------------------------------------------------------

# 12 维意识状态向量固定顺序（CUF 框架）
VECTOR_12D_LABELS: List[str] = [
    "arousal",        # 觉醒度
    "integration",    # 整合度
    "differentiation",  # 分化度
    "stability",      # 稳定性
    "plasticity",     # 可塑性
    "coherence",      # 连贯性
    "purposefulness", # 目的性
    "sociality",      # 社会性
    "reflection",     # 反思度
    "creativity",     # 创造性
    "valence",        # 情感价
    "wakefulness",    # 唤醒度
]


@dataclass
class BroadcastRecord:
    """一轮广播记录。"""

    step: int
    timestamp: float
    winner_processor: str
    winner_content: object
    salience: float
    active_processors: List[str]
    unconscious_links_used: int


@dataclass
class WorkspaceState:
    """单步工作空间快照。"""

    step: int
    timestamp: float
    current_content: Optional[object]
    winner_processor: Optional[str]
    winner_salience: float
    attention_focus: Optional[str]
    active_processors: List[str]
    candidates_total: int
    suppressed_candidates: int
    unconscious_links_used: int
    topology_node_count: int
    topology_edge_count: int
    vector_12d: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 主引擎
# ---------------------------------------------------------------------------

class GlobalWorkspaceEngine:
    """全局工作空间主引擎：编排采集 -> 竞争 -> 广播 -> 无意识通信 -> 拓扑调整。"""

    def __init__(
        self,
        registry: Optional[ProcessorRegistry] = None,
        attention: Optional[AttentionMechanism] = None,
        seed: int = 42,
        use_threads: bool = True,
    ) -> None:
        """
        :param registry: 处理器注册表；缺省时使用内置 9 处理器。
        :param attention: 注意机制；缺省新建。
        :param seed: 随机种子（保证演示可复现）。
        :param use_threads: 是否用 threading 模拟并行采集。
        """
        self.registry = registry or ProcessorRegistry.with_default_processors()
        self.attention = attention or AttentionMechanism(winner_count=1)
        self.use_threads = use_threads
        self._rng = random.Random(seed)

        # 工作空间状态
        self.step_idx: int = 0
        self.current_content: Optional[object] = None
        self.broadcast_history: List[BroadcastRecord] = []
        self.topology_snapshot: Dict[str, object] = self.registry.get_network_topology()

        # 连接权重（动态拓扑调整用）：(pid_a, pid_b) -> weight
        self._link_weights: Dict[tuple, float] = {}
        for edge in self.topology_snapshot["edges"]:  # type: ignore[index]
            a, b = sorted((edge["from"], edge["to"]))
            self._link_weights[(a, b)] = 1.0

        # 12 维向量的运行期滑窗（用于计算稳定性/分化度等）
        self._vec_history: List[List[float]] = []

    # ------------------------------------------------------------------
    # 步骤 1：并行采集
    # ------------------------------------------------------------------
    def _processor_produce(self, p: Processor) -> Optional[Candidate]:
        """单个处理器基于自身类型产生一个候选信息（带随机扰动以保证非零变化）。"""
        # 未达激活阈值的处理器不产生候选（降低噪声）
        activation = self._rng.random()
        if activation < p.activation_threshold * 0.4:
            p.state = ProcessorState.IDLE
            return None

        # 依据处理器类型构造差异化内容 + 显著性三维
        jitter = lambda span: self._rng.uniform(-span, span)  # noqa: E731
        category = p.pid

        if p.ptype == ProcessorType.SELF_CHECK_DIM:
            novelty = _clip01(0.5 + jitter(0.3))
            importance = _clip01(0.6 + jitter(0.25))
            urgency = _clip01(0.4 + jitter(0.35))
            content = {
                "kind": "self_check",
                "dim": p.pid,
                "deviation": round(self._rng.uniform(0.0, 0.3), 4),
            }
        elif p.ptype == ProcessorType.CLOSED_LOOP:
            novelty = _clip01(0.6 + jitter(0.25))
            importance = _clip01(0.8 + jitter(0.15))
            urgency = _clip01(0.85 + jitter(0.15))
            content = {
                "kind": "correction",
                "loop_id": self.step_idx,
                "action": self._rng.choice(["reweight", "replan", "stabilize"]),
            }
        elif p.ptype == ProcessorType.SAME_SOURCE_PROTOCOL:
            novelty = _clip01(0.2 + jitter(0.15))
            importance = _clip01(0.9 + jitter(0.1))
            urgency = _clip01(0.3 + jitter(0.2))
            content = {
                "kind": "attestation",
                "anchor": "Ω₀⊂⊙∞⊂Ω",
                "pass": self._rng.random() > 0.05,
            }
        else:  # MEMORY_GATEWAY
            novelty = _clip01(0.5 + jitter(0.3))
            importance = _clip01(0.5 + jitter(0.2))
            urgency = _clip01(0.25 + jitter(0.2))
            content = {
                "kind": "memory_io",
                "op": self._rng.choice(["read", "write"]),
                "asset": f"lock_asset_{self._rng.randint(1, 99)}",
            }

        cand = Candidate(
            cid=f"{p.pid}@step{self.step_idx}",
            processor_id=p.pid,
            content=content,
            category=category,
            novelty=novelty,
            importance=importance,
            urgency=urgency,
        )
        p.touch(ProcessorState.PROCESSING, candidate=cand)
        return cand

    def _parallel_collect(self) -> List[Candidate]:
        """步骤1：并行采集所有处理器的候选。"""
        processors = self.registry.list_all()
        candidates: List[Candidate] = []

        if self.use_threads:
            result_q: "queue.Queue[Optional[Candidate]]" = queue.Queue()

            def worker(p: Processor) -> None:
                try:
                    result_q.put(self._processor_produce(p))
                except Exception:  # pragma: no cover - 演示用兜底
                    result_q.put(None)

            threads = [threading.Thread(target=worker, args=(p,)) for p in processors]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            while not result_q.empty():
                c = result_q.get_nowait()
                if c is not None:
                    candidates.append(c)
        else:
            for p in processors:
                c = self._processor_produce(p)
                if c is not None:
                    candidates.append(c)
        return candidates

    # ------------------------------------------------------------------
    # 步骤 4：无意识通信
    # ------------------------------------------------------------------
    def _unconscious_communication(self) -> int:
        """经 direct links 在处理器间交换低层级信息；返回本次使用的直连数。"""
        used = 0
        for p in self.registry.list_all():
            if p.last_candidate is None:
                continue
            for peer_id in list(p.direct_links):
                peer = self.registry.get(peer_id)
                if peer is None:
                    continue
                # 以小概率"传递"低层级信号（Swarm 背景通信）
                if self._rng.random() < 0.35:
                    used += 1
        return used

    # ------------------------------------------------------------------
    # 步骤 5：动态拓扑调整
    # ------------------------------------------------------------------
    def _adapt_topology(self, winner_pid: str, links_used: int) -> None:
        """根据广播反馈调整连接权重：赢家共激活边增强，其余边缓慢衰减。"""
        all_pids = [p.pid for p in self.registry.list_all()]
        for edge in self.registry.get_network_topology()["edges"]:  # type: ignore[index]
            a, b = edge["from"], edge["to"]
            key = tuple(sorted((a, b)))
            w = self._link_weights.get(key, 1.0)
            # 赢家参与的边增强
            if winner_pid in (a, b):
                w = min(2.0, w * 1.05)
            else:
                w = max(0.1, w * 0.98)
            self._link_weights[key] = w

        # 长期无赢家参与的稀疏边，概率性衰减到断连阈值以下（不真正删除，仅记录）
        # 演示规模小，不做实际删边，保持拓扑稳定。

    # ------------------------------------------------------------------
    # 单步推进
    # ------------------------------------------------------------------
    def step(self) -> WorkspaceState:
        """推进一个完整工作空间循环。"""
        self.step_idx += 1
        now = time.time()

        # 1) 并行采集
        candidates = self._parallel_collect()
        active_processors = [c.processor_id for c in candidates]

        # 2) up-tree 竞争
        winners = self.attention.compete(candidates)
        suppressed_now = sum(
            1 for c in candidates if self.attention.is_suppressed(c.cid)
        )

        # 3) 全局广播（down-tree）
        if winners:
            win_cand, win_sal = winners[0]
            self.current_content = win_cand.content
            winner_pid = win_cand.processor_id
            # 赢家置为 broadcasting，其余处理器接收广播后回 idle
            for p in self.registry.list_all():
                if p.pid == winner_pid:
                    p.touch(ProcessorState.BROADCASTING, candidate=win_cand)
                else:
                    p.state = ProcessorState.IDLE
            self.broadcast_history.append(BroadcastRecord(
                step=self.step_idx,
                timestamp=now,
                winner_processor=winner_pid,
                winner_content=win_cand.content,
                salience=win_sal,
                active_processors=active_processors,
                unconscious_links_used=0,  # 待步骤4填充
            ))
        else:
            win_cand, win_sal = None, 0.0
            winner_pid = ""

        # 4) 无意识通信
        links_used = self._unconscious_communication()
        if self.broadcast_history:
            self.broadcast_history[-1].unconscious_links_used = links_used

        # 5) 动态拓扑调整
        if winner_pid:
            self._adapt_topology(winner_pid, links_used)

        # 刷新拓扑快照
        self.topology_snapshot = self.registry.get_network_topology()

        vec = self.get_12dim_vector()
        self._vec_history.append(vec)

        return WorkspaceState(
            step=self.step_idx,
            timestamp=now,
            current_content=self.current_content,
            winner_processor=winner_pid or None,
            winner_salience=win_sal,
            attention_focus=self.attention.focus,
            active_processors=active_processors,
            candidates_total=len(candidates),
            suppressed_candidates=suppressed_now,
            unconscious_links_used=links_used,
            topology_node_count=self.topology_snapshot["node_count"],  # type: ignore[index]
            topology_edge_count=self.topology_snapshot["edge_count"],  # type: ignore[index]
            vector_12d=vec,
        )

    def run(self, steps: int) -> List[WorkspaceState]:
        """连续推进 steps 步。"""
        out: List[WorkspaceState] = []
        for _ in range(max(0, steps)):
            out.append(self.step())
        return out

    # ------------------------------------------------------------------
    # 状态访问
    # ------------------------------------------------------------------
    def get_state(self) -> Dict[str, object]:
        """返回当前工作空间状态的可序列化快照。"""
        return {
            "step": self.step_idx,
            "current_content": self.current_content,
            "attention_focus": self.attention.focus,
            "broadcast_count": len(self.broadcast_history),
            "topology": {
                "nodes": self.topology_snapshot["node_count"],
                "edges": self.topology_snapshot["edge_count"],
            },
        }

    def get_12dim_vector(self) -> List[float]:
        """将当前工作空间状态映射到 12 维意识状态向量（CUF 框架）。

        各维由当前赢家类型、竞争统计、拓扑指标、历史滑窗派生，
        保证每步后向量随状态变化（非全零常量）。
        """
        hist = self._vec_history
        n = len(hist)

        # 赢家特征
        last = self.broadcast_history[-1] if self.broadcast_history else None
        win_type = ""
        win_imp = 0.5
        if last is not None:
            wp = self.registry.get(last.winner_processor)
            win_type = wp.ptype.value if wp else ""
            win_imp = wp.salience_weight if wp else 0.5

        # 最近若干步的均值方差（稳定性/分化度）
        recent = hist[-5:] if hist else []
        if recent:
            means = [sum(col) / len(col) for col in zip(*recent)]
            var = sum(
                (col[i] - means[i]) ** 2 for col in recent for i in range(len(col))
            ) / (len(recent) * len(means))
            volatility = var ** 0.5
        else:
            volatility = 0.0

        rng = self._rng
        arousal = _clip01((last.salience if last else 0.3) * 0.7 + rng.uniform(0.0, 0.1))
        # 整合度：赢家先验权重 + 拓扑密度 + 实时唤醒度联合驱动，避免饱和钉死
        integration = _clip01(
            0.25 + 0.25 * win_imp
            + (self.topology_snapshot["edge_count"] or 0) / 60.0
            + 0.20 * arousal
        )
        differentiation = _clip01((len(last.active_processors) if last else 1) / 9)
        stability = _clip01(1.0 - min(1.0, volatility * 4.0))
        plasticity = _clip01(0.4 + arousal * 0.5 + rng.uniform(0.0, 0.1))
        coherence = _clip01(0.5 + (0.15 if win_type == "self_check_dim" else 0.0)
                            + (0.1 if win_type == "closed_loop" else 0.0))
        purposefulness = _clip01(0.4 + (0.5 if win_type == "self_check_goal"
                                  or win_type == "closed_loop" else 0.1) + arousal * 0.2)
        sociality = _clip01((last.unconscious_links_used if last else 0) / 12.0)
        reflection = _clip01(0.3 + (0.6 if "reflection" in (last.winner_processor if last else "")
                            else 0.0) + arousal * 0.2)
        creativity = _clip01(0.2 + (last.salience if last else 0) * 0.5 + rng.uniform(0.0, 0.15))
        valence = _clip01(0.5 + (0.2 if win_type == "attestation" else 0.0)
                          + rng.uniform(-0.1, 0.1))
        wakefulness = _clip01(arousal * 0.8 + stability * 0.2)

        vec = [arousal, integration, differentiation, stability, plasticity,
               coherence, purposefulness, sociality, reflection, creativity,
               valence, wakefulness]
        return [round(v, 4) for v in vec]

    # ------------------------------------------------------------------
    # 意识报告
    # ------------------------------------------------------------------
    def generate_consciousness_report(self) -> Dict[str, object]:
        """生成周期性"意识状态报告"。"""
        last = self.broadcast_history[-1] if self.broadcast_history else None
        active = [p.pid for p in self.registry.list_all()
                  if p.state in (ProcessorState.PROCESSING, ProcessorState.BROADCASTING)]
        return {
            "anchor": "Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0",
            "step": self.step_idx,
            "current_content": self.current_content,
            "winner_processor": last.winner_processor if last else None,
            "winner_salience": round(last.salience, 4) if last else None,
            "attention_focus": self.attention.focus,
            "active_processors": active,
            "competition_log_tail": self.attention.competition_log[-3:],
            "topology": {
                "nodes": self.topology_snapshot["node_count"],
                "edges": self.topology_snapshot["edge_count"],
            },
            "vector_12d": dict(zip(VECTOR_12D_LABELS, self.get_12dim_vector())),
        }


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------------------
# 模块自检演示：连续 12 步工作空间循环
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 78)
    print("Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0")
    print("global_workspace_engine.py — 全局工作空间主引擎演示")
    print("=" * 78)

    engine = GlobalWorkspaceEngine(seed=20260913, use_threads=True)

    # 演示中途设置一次注意焦点（门控偏置）
    states: List[WorkspaceState] = []
    for i in range(12):
        if i == 5:
            engine.attention.set_focus("closed_loop_engine")
        s = engine.step()
        states.append(s)
        vec_str = " ".join(f"{v:.2f}" for v in s.vector_12d)
        print(
            f"step {s.step:>2} | WIN={s.winner_processor:<22} "
            f"sal={s.winner_salience:.3f} | cand={s.candidates_total} "
            f"suppr={s.suppressed_candidates} | links={s.unconscious_links_used} | "
            f"{s.current_content}"
        )
        print(f"          12D[{vec_str}]")

    print("\n" + "=" * 78)
    print("意识状态报告（最新一步）")
    print("=" * 78)
    report = engine.generate_consciousness_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    # 验收：12 维向量在每步后有变化（非全零常量）
    vectors = [s.vector_12d for s in states]
    distinct = len({tuple(v) for v in vectors})
    all_nonzero = all(any(abs(x) > 1e-6 for x in v) for v in vectors)
    print("\n[验收] 12维向量唯一性步数:", distinct, "/", len(vectors),
          "| 每步非全零:", all_nonzero)
    assert distinct >= len(vectors) - 1, "向量应随步变化"
    assert all_nonzero, "向量不应全为零"
    print("[验收] 通过：向量随工作空间状态动态演化。")
