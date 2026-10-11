#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

multi_agent_coupling.py — 多智能体心智耦合主系统

编排多个 ZONGYUAN-ROOT 实例的心智耦合，实现群体智能涌现：
  - 创建 N 个实例（基于 IdentityNodeProtocol）
  - 4 种耦合模式：all-to-all / chain / small-world / star
  - 群体意识指标：整合度 Φ、一致性、多样性、吸引子稳定性
  - 4 个压力测试场景：信息极化 / 耦合强度相变 / 节点失效 / 外部扰动

纯 Python 3.8+ 标准库实现。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from identity_node_protocol import IdentityNode, IdentityNodeProtocol, NodeStatus
from attractor_dynamics import (
    Attractor, AttractorDynamics, AttractorType, DIM, DIM_NAMES,
    cosine_similarity, vec_mean, vec_norm, vec_sub,
)


# ---------------------------------------------------------------------------
# 确权常量
# ---------------------------------------------------------------------------
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
MODULE = "multi_agent_coupling"


class CouplingMode(str, Enum):
    ALL2ALL = "all-to-all"
    CHAIN = "chain"
    SMALL_WORLD = "small-world"
    STAR = "star"


# ---------------------------------------------------------------------------
# 结果数据结构
# ---------------------------------------------------------------------------
@dataclass
class CouplingResult:
    """一次耦合运行的结果。"""
    mode: str
    steps: int
    trajectories: List[List[List[float]]]            # [T, N, DIM]
    coupling_matrix: List[List[float]]
    metrics: Dict[str, float]
    attractors: List[Dict] = field(default_factory=list)


@dataclass
class StressTestResult:
    """压力测试结果。"""
    scenario: str
    description: str
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    extra: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 主系统
# ---------------------------------------------------------------------------
class MultiAgentCouplingSystem:
    """
    多智能体心智耦合系统。

    使用：
        sys = MultiAgentCouplingSystem(N=5)
        sys.set_coupling_mode(CouplingMode.ALL2ALL)
        res = sys.run_coupling(steps=20)
        print(res.metrics)
    """

    def __init__(self, n: int = 5, seed: int = 2026):
        self.n = n
        self._rng = random.Random(seed)
        self._idp = IdentityNodeProtocol()
        self._dynamics = AttractorDynamics(dt=0.1, noise=0.015, seed=seed)

        self.agents: List[IdentityNode] = []
        self.states: List[List[float]] = []
        self.coupling_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
        self.mode: CouplingMode = CouplingMode.ALL2ALL

        # 内部记忆：最近一次运行结果
        self._last_trajectories: List[List[List[float]]] = []
        self._last_metrics: Dict[str, float] = {}

        # 自动创建 N 个智能体
        self.create_agents(n)

    # ==================================================================
    # 智能体创建
    # ==================================================================
    def create_agents(self, n: int) -> List[IdentityNode]:
        """基于 IdentityNodeProtocol 创建 N 个 ZONGYUAN-ROOT 实例。"""
        self.n = n
        self.agents = []
        self.states = []
        for _ in range(n):
            node = self._idp.register()
            self.agents.append(node)
            # 每个智能体独立 12 维初始状态
            vec = [self._rng.gauss(0, 0.5) for _ in range(DIM)]
            self.states.append(vec)
        # 默认耦合矩阵：全连接
        self.set_coupling_mode(CouplingMode.ALL2ALL, k=0.2)
        return self.agents

    # ==================================================================
    # 耦合模式
    # ==================================================================
    def set_coupling_mode(self, mode: CouplingMode,
                          k: float = 0.2,
                          rewiring_p: float = 0.1) -> None:
        """
        设置耦合模式并生成对应的耦合强度矩阵 K。

        参数：
            mode:       all-to-all / chain / small-world / star
            k:          基础耦合强度
            rewiring_p: 小世界模型的随机重连概率
        """
        n = self.n
        self.mode = mode
        K = [[0.0] * n for _ in range(n)]

        if mode == CouplingMode.ALL2ALL:
            for i in range(n):
                for j in range(n):
                    if i != j:
                        K[i][j] = k

        elif mode == CouplingMode.CHAIN:
            for i in range(n - 1):
                K[i][i + 1] = k
                K[i + 1][i] = k

        elif mode == CouplingMode.SMALL_WORLD:
            # 环形最近邻（k=2 邻居）
            neighbor = 2
            for i in range(n):
                for d in range(1, neighbor + 1):
                    j = (i + d) % n
                    K[i][j] = k
                    K[j][i] = k
            # 随机重连
            for i in range(n):
                for d in range(1, neighbor + 1):
                    j = (i + d) % n
                    if self._rng.random() < rewiring_p:
                        new_j = self._rng.randrange(n)
                        if new_j != i and new_j != j:
                            K[i][j] = 0.0
                            K[j][i] = 0.0
                            K[i][new_j] = k
                            K[new_j][i] = k

        elif mode == CouplingMode.STAR:
            center = 0
            for i in range(n):
                if i != center:
                    K[center][i] = k
                    K[i][center] = k

        self.coupling_matrix = K

    # ==================================================================
    # 群体意识指标
    # ==================================================================
    @staticmethod
    def _integrity_phi(states: List[List[float]]) -> float:
        """
        整合度 Φ（简化版）：
            Φ = || mean(states) || - mean(||state_i||)
        正值表示群体处于"整合"状态（强于个体平均），负值表示碎片化。
        """
        n = len(states)
        if n == 0:
            return 0.0
        global_mean = vec_mean(states)
        global_norm = vec_norm(global_mean)
        individual_avg = sum(vec_norm(s) for s in states) / n
        return global_norm - individual_avg

    @staticmethod
    def _consistency_index(states: List[List[float]]) -> float:
        """一致性指数：所有两两余弦相似度的均值。"""
        n = len(states)
        if n < 2:
            return 1.0
        sims: List[float] = []
        for i in range(n):
            for j in range(i + 1, n):
                sims.append(cosine_similarity(states[i], states[j]))
        return sum(sims) / len(sims) if sims else 0.0

    @staticmethod
    def _diversity_index(states: List[List[float]]) -> float:
        """多样性指数：所有状态向量各维度方差之和。"""
        n = len(states)
        if n == 0:
            return 0.0
        total_var = 0.0
        for d in range(DIM):
            mean_d = sum(s[d] for s in states) / n
            var_d = sum((s[d] - mean_d) ** 2 for s in states) / n
            total_var += var_d
        return total_var / DIM

    def _group_attractor_stability(self,
                                   trajectories: List[List[List[float]]],
                                   tail: int = 15) -> float:
        """群体吸引子稳定性：末段窗口内群体均值轨迹的方差倒数。"""
        T = len(trajectories)
        if T < tail + 1:
            tail = T
        window = trajectories[T - tail:]
        means = [vec_mean(step) for step in window]
        center = vec_mean(means)
        var = sum(vec_norm(vec_sub(m, center)) ** 2 for m in means) / len(means)
        return 1.0 / (1.0 + var * 10.0)

    def get_group_metrics(self,
                          states: Optional[List[List[float]]] = None,
                          trajectories: Optional[List[List[List[float]]]] = None
                          ) -> Dict[str, float]:
        """计算群体意识指标。"""
        states = states if states is not None else self.states
        phi = self._integrity_phi(states)
        consistency = self._consistency_index(states)
        diversity = self._diversity_index(states)
        if trajectories is None:
            trajectories = self._last_trajectories
        stability = (self._group_attractor_stability(trajectories)
                     if trajectories else 0.0)
        return {
            "integrity_phi": phi,
            "consistency": consistency,
            "diversity": diversity,
            "attractor_stability": stability,
            "n_agents": float(len(states)),
        }

    # ==================================================================
    # 运行耦合
    # ==================================================================
    def run_coupling(self,
                     steps: int = 20,
                     perturb_at_step: Optional[int] = None,
                     perturb_amplitude: float = 0.0) -> CouplingResult:
        """
        运行一次耦合仿真。

        参数：
            steps:             仿真步数
            perturb_at_step:   扰动步
            perturb_amplitude: 扰动幅度

        返回 CouplingResult。
        """
        trajectories = self._dynamics.simulate(
            agents=self.states,
            coupling_matrix=self.coupling_matrix,
            steps=steps,
            perturb_at_step=perturb_at_step,
            perturb_amplitude=perturb_amplitude,
        )
        # 同步当前状态为末态
        self.states = [list(v) for v in trajectories[-1]]

        # 标记节点为 coupled
        for a in self.agents:
            self._idp.set_coupled(a.node_id, True)

        # 群体指标
        metrics = self.get_group_metrics(states=self.states,
                                         trajectories=trajectories)

        # 吸引子检测 + 分类
        attractors = self._dynamics.detect_attractors(
            trajectories, tail_window=min(15, steps), distance_threshold=0.35
        )
        attractor_dicts: List[Dict] = []
        for att in attractors:
            self._dynamics.classify(att, all_attractors=attractors)
            attractor_dicts.append(att.to_dict())

        self._last_trajectories = trajectories
        self._last_metrics = metrics

        return CouplingResult(
            mode=self.mode.value,
            steps=steps,
            trajectories=trajectories,
            coupling_matrix=self.coupling_matrix,
            metrics=metrics,
            attractors=attractor_dicts,
        )

    # ==================================================================
    # 压力测试
    # ==================================================================
    def run_stress_test(self, scenario: str) -> StressTestResult:
        """
        运行 4 个压力测试场景之一：
          - polarization: 信息极化（部分智能体注入对立状态）
          - phase_transition: 耦合强度 K 从 0 渐变到 1
          - node_failure: 中途移除中心节点
          - perturbation: 外部扰动（噪声冲击），测量 τ
        """
        if scenario == "polarization":
            return self._scenario_polarization()
        if scenario == "phase_transition":
            return self._scenario_phase_transition()
        if scenario == "node_failure":
            return self._scenario_node_failure()
        if scenario == "perturbation":
            return self._scenario_perturbation()
        raise ValueError(f"未知场景: {scenario}")

    # ---- 场景 1：信息极化 ----
    def _scenario_polarization(self) -> StressTestResult:
        """给一半智能体注入强烈正向初始态，另一半强烈负向。"""
        saved_states = [list(s) for s in self.states]
        n = self.n
        half = n // 2
        for i in range(n):
            sign = 1.0 if i < half else -1.0
            self.states[i] = [sign * 0.8 + self._rng.gauss(0, 0.05)
                              for _ in range(DIM)]

        self.set_coupling_mode(CouplingMode.ALL2ALL, k=0.25)
        before = self.get_group_metrics(states=self.states)
        res = self.run_coupling(steps=40)
        after = res.metrics

        self.states = saved_states  # 还原
        return StressTestResult(
            scenario="polarization",
            description="信息极化：对半注入对立初始状态，观察共识/极化结果",
            metrics_before=before,
            metrics_after=after,
            extra={"n_attractors": len(res.attractors),
                   "attractor_types": [a["type"] for a in res.attractors]},
        )

    # ---- 场景 2：耦合强度相变 ----
    def _scenario_phase_transition(self) -> StressTestResult:
        """K 从 0 渐变到 1，记录每个 K 下的群体一致性。"""
        saved_states = [list(s) for s in self.states]
        history: List[Tuple[float, float, float]] = []  # (k, consistency, diversity)
        for k in [round(x * 0.1, 2) for x in range(0, 11)]:
            # 重置为初始态
            self.states = [list(s) for s in saved_states]
            self.set_coupling_mode(CouplingMode.ALL2ALL, k=k)
            res = self.run_coupling(steps=30)
            history.append((k, res.metrics["consistency"],
                            res.metrics["diversity"]))

        # 找相变点：一致性突变最大处
        transition_k = 0.0
        max_jump = 0.0
        for i in range(1, len(history)):
            jump = abs(history[i][1] - history[i - 1][1])
            if jump > max_jump:
                max_jump = jump
                transition_k = history[i][0]

        self.states = saved_states
        return StressTestResult(
            scenario="phase_transition",
            description="耦合强度 K 从 0→1 渐变，寻找一致性相变点",
            metrics_before={"k": 0.0, "consistency": history[0][1]},
            metrics_after={"k": 1.0, "consistency": history[-1][1]},
            extra={"transition_k": transition_k,
                   "max_consistency_jump": max_jump,
                   "history": [{"k": k, "consistency": c, "diversity": d}
                               for k, c, d in history]},
        )

    # ---- 场景 3：节点失效 ----
    def _scenario_node_failure(self) -> StressTestResult:
        """星型耦合下，中途移除中心节点（索引 0）。"""
        saved_states = [list(s) for s in self.states]
        saved_matrix = [list(row) for row in self.coupling_matrix]

        self.set_coupling_mode(CouplingMode.STAR, k=0.3)
        res1 = self.run_coupling(steps=20)
        metrics_before = res1.metrics

        # 移除中心节点：把 K[0][*] 与 K[*][0] 全部置零
        for j in range(self.n):
            self.coupling_matrix[0][j] = 0.0
            self.coupling_matrix[j][0] = 0.0
        if self.agents:
            self._idp.revoke(self.agents[0].node_id)

        res2 = self.run_coupling(steps=20)
        metrics_after = res2.metrics

        # 还原
        self.coupling_matrix = saved_matrix
        self.states = saved_states
        return StressTestResult(
            scenario="node_failure",
            description="星型耦合下中途移除中心节点，观察系统韧性",
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            extra={"center_node": self.agents[0].node_id if self.agents else None,
                   "consistency_drop": metrics_before["consistency"] - metrics_after["consistency"]},
        )

    # ---- 场景 4：外部扰动 ----
    def _scenario_perturbation(self) -> StressTestResult:
        """在 step=15 施加外部噪声冲击，测量恢复时间 τ。"""
        saved_states = [list(s) for s in self.states]
        self.set_coupling_mode(CouplingMode.ALL2ALL, k=0.25)

        before = self.get_group_metrics(states=self.states)
        res = self.run_coupling(steps=40, perturb_at_step=15,
                               perturb_amplitude=0.6)
        after = res.metrics

        # 计算每个智能体的 τ
        taus: List[float] = []
        for i in range(self.n):
            single_traj = [res.trajectories[t][i] for t in range(len(res.trajectories))]
            tau = self._dynamics.compute_recovery_time(single_traj,
                                                      perturbation_step=15,
                                                      tolerance=0.08)
            taus.append(tau)

        self.states = saved_states
        return StressTestResult(
            scenario="perturbation",
            description="在 step=15 施加幅度 0.6 的外部扰动，测量恢复时间 τ",
            metrics_before=before,
            metrics_after=after,
            extra={"mean_tau": sum(taus) / len(taus),
                   "max_tau": max(taus),
                   "taus_per_agent": taus},
        )


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
def _print_result(tag: str, res: CouplingResult) -> None:
    m = res.metrics
    print(f"\n[{tag}] mode={res.mode}  steps={res.steps}")
    print(f"  Φ(整合度)      = {m['integrity_phi']:+.4f}")
    print(f"  一致性指数     = {m['consistency']:+.4f}")
    print(f"  多样性指数     = {m['diversity']:.4f}")
    print(f"  吸引子稳定性   = {m['attractor_stability']:.4f}")
    print(f"  吸引子数量     = {len(res.attractors)}")
    for k, a in enumerate(res.attractors):
        print(f"    A{k}: members={a['members']}  "
              f"radius={a['radius']:.3f}  type={a['type']}")


if __name__ == "__main__":
    print("=" * 72)
    print(f"  {ANCHOR}  ·  DID-BR-000002  ·  ZONGYUAN-ROOT V3.0")
    print("  Multi-Agent Coupling System — Demo")
    print("=" * 72)

    # 1) 创建 5 个智能体
    system = MultiAgentCouplingSystem(n=5, seed=20260913)
    print(f"\n[INIT] 已创建 {system.n} 个 ZONGYUAN-ROOT 实例：")
    for a in system.agents:
        print(f"  {a.node_id}  did={a.did}")
    print(f"  12 维初始状态示例 (agent0): "
          f"{[round(v, 3) for v in system.states[0]]}")

    # 2) 4 种耦合模式，每种运行 20 步
    print("\n" + "-" * 72)
    print("  4 种耦合模式 × 20 步")
    print("-" * 72)
    all_results: List[CouplingResult] = []
    for mode in CouplingMode:
        # 每个模式前重置初始状态以保证可比
        system.states = [[system._rng.gauss(0, 0.5) for _ in range(DIM)]
                         for _ in range(system.n)]
        system.set_coupling_mode(mode, k=0.25)
        res = system.run_coupling(steps=20)
        all_results.append(res)
        _print_result(f"MODE-{mode.value}", res)

    # 3) 群体指标汇总
    print("\n" + "-" * 72)
    print("  群体指标汇总")
    print("-" * 72)
    print(f"  {'mode':<14}{'Φ':>10}{'consist':>10}{'divers':>10}{'stab':>10}")
    for r in all_results:
        m = r.metrics
        print(f"  {r.mode:<14}{m['integrity_phi']:>+10.3f}"
              f"{m['consistency']:>+10.3f}"
              f"{m['diversity']:>10.3f}"
              f"{m['attractor_stability']:>10.3f}")

    # 4) 压力测试：场景 1 + 场景 4
    print("\n" + "-" * 72)
    print("  压力测试")
    print("-" * 72)
    for scenario in ["polarization", "perturbation"]:
        print(f"\n[STRESS] scenario = {scenario}")
        r = system.run_stress_test(scenario)
        print(f"  描述: {r.description}")
        print(f"  前 Φ={r.metrics_before.get('integrity_phi', 0):+.3f}  "
              f"consistency={r.metrics_before.get('consistency', 0):+.3f}")
        print(f"  后 Φ={r.metrics_after.get('integrity_phi', 0):+.3f}  "
              f"consistency={r.metrics_after.get('consistency', 0):+.3f}")
        for k, v in r.extra.items():
            if isinstance(v, list):
                print(f"  {k}: [{', '.join(f'{x:.2f}' if isinstance(x, float) else str(x) for x in v[:8])}{' ...' if len(v) > 8 else ''}]")
            else:
                print(f"  {k}: {v}")

    print("\n[OK] multi_agent_coupling demo 完成。")
