#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

attractor_dynamics.py — 群体吸引子动力学（Attractor Dynamics）

在 12 维心智状态空间中分析多智能体耦合后的稳态吸引子：
  维度：觉醒度 / 整合度 / 分化度 / 稳定性 / 可塑性 / 连贯性 /
        目的性 / 社会性 / 反思度 / 创造性 / 情感价 / 唤醒度

耦合方程（欧拉离散化）：
    dX_i/dt = f(X_i) + Σ_j K_ij · (X_j - X_i) + noise
    X_i(t+dt) = X_i(t) + dt · [self_bias_i + Σ_j K_ij·(X_j-X_i)] + σ·ξ

功能：
  - simulate(agents, coupling_matrix, steps) -> trajectories
  - detect_attractors(trajectories) -> list[Attractor]
  - classify(attractor) -> str
  - compute_recovery_time(trajectory, perturbation_step) -> float

纯 Python 3.8+ 标准库，矩阵运算用嵌套列表。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 确权常量
# ---------------------------------------------------------------------------
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
MODULE = "attractor_dynamics"
DIM = 12  # 12 维心智状态空间

# 12 维状态向量维度名
DIM_NAMES = [
    "arousal",       # 觉醒度
    "integration",   # 整合度
    "differentiation",  # 分化度
    "stability",     # 稳定性
    "plasticity",    # 可塑性
    "coherence",     # 连贯性
    "purpose",       # 目的性
    "sociality",     # 社会性
    "reflection",    # 反思度
    "creativity",    # 创造性
    "valence",       # 情感价
    "wakefulness",   # 唤醒度
]


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
class AttractorType(str, Enum):
    """吸引子类型。"""
    CONSENSUS = "consensus"       # 共识：所有智能体收敛到同一状态
    POLARIZED = "polarized"       # 极化：分裂为 2+ 簇
    CHAOTIC = "chaotic"           # 混沌：无稳定收敛
    OSCILLATORY = "oscillatory"   # 振荡：周期性变化
    UNKNOWN = "unknown"


@dataclass
class Attractor:
    """一个识别出的稳态吸引子。"""
    center: List[float]                 # 吸引子中心（12 维）
    members: List[int]                  # 属于该吸引子的智能体索引
    radius: float                       # 簇内平均半径（离散度）
    stability: float                    # 末段轨迹方差倒数的归一化指标
    atype: AttractorType = AttractorType.UNKNOWN
    cycle_period: Optional[float] = None  # 振荡吸引子的周期（步）

    def to_dict(self) -> Dict:
        return {
            "center": [round(v, 4) for v in self.center],
            "members": list(self.members),
            "radius": round(self.radius, 4),
            "stability": round(self.stability, 4),
            "type": self.atype.value,
            "cycle_period": self.cycle_period,
        }


# ---------------------------------------------------------------------------
# 工具函数（纯 Python 线性代数）
# ---------------------------------------------------------------------------
def vec_sub(a: List[float], b: List[float]) -> List[float]:
    return [x - y for x, y in zip(a, b)]


def vec_add(a: List[float], b: List[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def vec_scale(a: List[float], s: float) -> List[float]:
    return [x * s for x in a]


def vec_mean(vs: List[List[float]]) -> List[float]:
    n = len(vs)
    if n == 0:
        return [0.0] * DIM
    return [sum(v[i] for v in vs) / n for i in range(DIM)]


def vec_norm(a: List[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    na = vec_norm(a)
    nb = vec_norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# 吸引子动力学主体
# ---------------------------------------------------------------------------
class AttractorDynamics:
    """
    多智能体耦合后的稳态吸引子分析器。

    参数：
        dt:      欧拉积分步长
        noise:   高斯噪声标准差（每维）
        bias:    每个智能体的自偏置向量（趋向自身吸引子）
        seed:    随机种子（可复现）
    """

    def __init__(self, dt: float = 0.1, noise: float = 0.02,
                 bias: Optional[List[float]] = None, seed: int = 42):
        self.dt = dt
        self.noise = noise
        self.bias = bias or [0.05] * DIM  # 弱自偏置，使系统有内禀漂移
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # 仿真
    # ------------------------------------------------------------------
    def simulate(self,
                 agents: List[List[float]],
                 coupling_matrix: List[List[float]],
                 steps: int,
                 perturb_at_step: Optional[int] = None,
                 perturb_amplitude: float = 0.0) -> List[List[List[float]]]:
        """
        运行耦合仿真。

        参数：
            agents:           N 个智能体的初始 12 维状态向量
            coupling_matrix:  N×N 耦合强度矩阵 K_ij
            steps:            仿真步数
            perturb_at_step:  在该步对所有智能体施加高斯扰动
            perturb_amplitude: 扰动幅度

        返回：
            trajectories: shape = [steps+1, N, DIM]
        """
        n = len(agents)
        # 深拷贝初始状态
        states: List[List[float]] = [list(s) for s in agents]
        trajectories: List[List[List[float]]] = [
            [list(s) for s in states]
        ]

        for t in range(steps):
            # 可选扰动
            if perturb_at_step is not None and t == perturb_at_step:
                for i in range(n):
                    states[i] = [
                        s + perturb_amplitude * self._rng.gauss(0, 1)
                        for s in states[i]
                    ]

            new_states: List[List[float]] = []
            for i in range(n):
                # 耦合项：Σ_j K_ij · (X_j - X_i)
                coupling = [0.0] * DIM
                for j in range(n):
                    if i == j or coupling_matrix[i][j] == 0.0:
                        continue
                    diff = vec_sub(states[j], states[i])
                    w = coupling_matrix[i][j]
                    coupling = vec_add(coupling, vec_scale(diff, w))

                # 自偏置项 f(X_i)：向 bias 方向弱吸引 + 轻微非线性回拉
                drift = vec_sub(self.bias, states[i])
                drift = vec_scale(drift, 0.05)

                # 噪声
                noise_vec = [
                    self.noise * self._rng.gauss(0, 1) for _ in range(DIM)
                ]

                update = vec_add(
                    vec_add(vec_scale(drift, 1.0),
                            vec_scale(coupling, 1.0)),
                    noise_vec,
                )
                new_state = vec_add(states[i], vec_scale(update, self.dt))
                # 限制到 [-1, 1]，避免发散
                new_state = [max(-1.0, min(1.0, v)) for v in new_state]
                new_states.append(new_state)

            states = new_states
            trajectories.append([list(s) for s in states])

        return trajectories

    # ------------------------------------------------------------------
    # 吸引子检测（距离阈值聚类 + 末尾稳态窗口）
    # ------------------------------------------------------------------
    def detect_attractors(self,
                          trajectories: List[List[List[float]]],
                          tail_window: int = 20,
                          distance_threshold: float = 0.35) -> List[Attractor]:
        """
        在轨迹末尾窗口上做距离阈值聚类，识别稳态吸引子。

        步骤：
          1. 取末尾 tail_window 步每个智能体的平均状态
          2. 以距离阈值做单链 / 贪心聚类
          3. 计算每个簇的半径、稳定性
        """
        n = len(trajectories[0])
        T = len(trajectories)
        start = max(0, T - tail_window)

        # 每个智能体在末段窗口的平均位置
        avg_states: List[List[float]] = []
        for i in range(n):
            window = [trajectories[t][i] for t in range(start, T)]
            avg_states.append(vec_mean(window))

        # 稳定性：末段窗口内每个智能体状态方差的平均
        stabilities: List[float] = []
        for i in range(n):
            window = [trajectories[t][i] for t in range(start, T)]
            mean = avg_states[i]
            var = 0.0
            for v in window:
                d = vec_norm(vec_sub(v, mean))
                var += d * d
            var /= max(1, len(window))
            # 方差越小越稳定；映射到 (0,1]
            stabilities.append(1.0 / (1.0 + var * 10.0))

        # 贪心距离聚类
        clusters: List[List[int]] = []
        for i in range(n):
            placed = False
            for c in clusters:
                # 与簇内已有成员的最大距离 < 阈值则归入
                rep_idx = c[0]
                if vec_norm(vec_sub(avg_states[i], avg_states[rep_idx])) < distance_threshold:
                    c.append(i)
                    placed = True
                    break
            if not placed:
                clusters.append([i])

        # 构造 Attractor 对象
        attractors: List[Attractor] = []
        for c in clusters:
            members_states = [avg_states[i] for i in c]
            center = vec_mean(members_states)
            radius = (
                sum(vec_norm(vec_sub(s, center)) for s in members_states) / len(members_states)
                if len(members_states) > 1 else 0.0
            )
            stability = sum(stabilities[i] for i in c) / len(c)
            attractors.append(Attractor(
                center=center,
                members=list(c),
                radius=radius,
                stability=stability,
            ))

        # 按规模降序
        attractors.sort(key=lambda a: -len(a.members))
        return attractors

    # ------------------------------------------------------------------
    # 吸引子分类
    # ------------------------------------------------------------------
    def classify(self,
                 attractor: Attractor,
                 all_attractors: Optional[List[Attractor]] = None,
                 trajectory_for_osc: Optional[List[List[float]]] = None
                 ) -> AttractorType:
        """
        分类单个（或一组）吸引子：
          - consensus: 仅 1 个吸引子且半径小、稳定
          - polarized: 存在 ≥2 个规模相近的簇
          - oscillatory: 轨迹呈现周期性（用自相关峰值检测）
          - chaotic: 半径大 / 稳定性低
        """
        # 振荡检测：对该吸引子成员的轨迹做简单自相关
        if trajectory_for_osc is not None and self._is_oscillatory(trajectory_for_osc):
            attractor.atype = AttractorType.OSCILLATORY
            attractor.cycle_period = self._estimate_period(trajectory_for_osc)
            return AttractorType.OSCILLATORY

        # 单簇情况
        if all_attractors is None or len(all_attractors) == 1:
            if attractor.stability > 0.6 and attractor.radius < 0.25:
                attractor.atype = AttractorType.CONSENSUS
            elif attractor.radius > 0.6 or attractor.stability < 0.2:
                attractor.atype = AttractorType.CHAOTIC
            else:
                attractor.atype = AttractorType.CONSENSUS
            return attractor.atype

        # 多簇情况
        sizes = sorted((len(a.members) for a in all_attractors), reverse=True)
        if len(sizes) >= 2 and sizes[1] >= max(2, sum(sizes) * 0.2):
            attractor.atype = AttractorType.POLARIZED
        elif attractor.radius > 0.6:
            attractor.atype = AttractorType.CHAOTIC
        else:
            attractor.atype = AttractorType.CONSENSUS
        return attractor.atype

    # ------------------------------------------------------------------
    # 韧性：扰动恢复时间 τ
    # ------------------------------------------------------------------
    def compute_recovery_time(self,
                              trajectory: List[List[float]],
                              perturbation_step: int,
                              tolerance: float = 0.05) -> float:
        """
        给定单智能体的轨迹 [T, DIM]，在 perturbation_step 处施加扰动后，
        返回回到扰动前稳态邻域所需的步数 τ。

        判定：从扰动步之后起，连续若干步与扰动前末段均值的距离 < tolerance。
        """
        if perturbation_step <= 0 or perturbation_step >= len(trajectory) - 1:
            return float(len(trajectory))

        # 扰动前基准：扰动步前 5 步的均值
        pre = trajectory[max(0, perturbation_step - 5):perturbation_step]
        baseline = vec_mean(pre) if pre else trajectory[perturbation_step]

        # 从扰动步之后开始扫描
        consecutive_needed = 3
        streak = 0
        for t in range(perturbation_step, len(trajectory)):
            d = vec_norm(vec_sub(trajectory[t], baseline))
            if d < tolerance:
                streak += 1
                if streak >= consecutive_needed:
                    return float(t - perturbation_step)
            else:
                streak = 0
        return float(len(trajectory) - perturbation_step)

    # ------------------------------------------------------------------
    # 内部：振荡检测（自相关）
    # ------------------------------------------------------------------
    @staticmethod
    def _series_norm(traj: List[List[float]]) -> List[float]:
        return [vec_norm(v) for v in traj]

    def _is_oscillatory(self, traj: List[List[float]]) -> bool:
        series = self._series_norm(traj)
        if len(series) < 10:
            return False
        mean = sum(series) / len(series)
        var = sum((x - mean) ** 2 for x in series) / len(series)
        if var < 1e-6:
            return False
        # 自相关
        n = len(series)
        max_lag = n // 2
        best = 0.0
        for lag in range(3, max_lag):
            s = 0.0
            for i in range(n - lag):
                s += (series[i] - mean) * (series[i + lag] - mean)
            s /= (n - lag) * var
            if s > best:
                best = s
        return best > 0.5

    def _estimate_period(self, traj: List[List[float]]) -> float:
        series = self._series_norm(traj)
        if len(series) < 10:
            return float("nan")
        mean = sum(series) / len(series)
        var = sum((x - mean) ** 2 for x in series) / len(series)
        if var < 1e-6:
            return 1.0
        n = len(series)
        max_lag = n // 2
        best_lag = 0
        best_corr = -2.0
        for lag in range(3, max_lag):
            s = 0.0
            for i in range(n - lag):
                s += (series[i] - mean) * (series[i + lag] - mean)
            s /= (n - lag) * var
            if s > best_corr:
                best_corr = s
                best_lag = lag
        return float(best_lag)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 72)
    print(f"  {ANCHOR}  ·  DID-BR-000002  ·  ZONGYUAN-ROOT V3.0")
    print(f"  Attractor Dynamics — Demo  (dim={DIM})")
    print("=" * 72)

    dyn = AttractorDynamics(dt=0.1, noise=0.02, seed=7)

    # 构造 6 个智能体的 12 维初始状态（分两组：A 组偏正、B 组偏负）
    rng = random.Random(123)
    agents: List[List[float]] = []
    for i in range(6):
        base = 0.6 if i < 3 else -0.6
        vec = [base + rng.gauss(0, 0.1) for _ in range(DIM)]
        agents.append(vec)

    # 全连接耦合矩阵
    N = len(agents)
    K = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i != j:
                K[i][j] = 0.25

    print(f"\n[SIMULATE] N={N}, steps=80, coupling=all-to-all K=0.25")
    traj = dyn.simulate(agents, K, steps=80)
    print(f"  trajectory shape = {len(traj)} x {len(traj[0])} x {DIM}")
    print(f"  智能体 0 末态: {[round(v, 3) for v in traj[-1][0]]}")
    print(f"  智能体 5 末态: {[round(v, 3) for v in traj[-1][5]]}")

    # 吸引子检测
    attractors = dyn.detect_attractors(traj, tail_window=20, distance_threshold=0.35)
    print(f"\n[DETECT] 检测到 {len(attractors)} 个吸引子：")
    for k, a in enumerate(attractors):
        atype = dyn.classify(a, all_attractors=attractors,
                             trajectory_for_osc=[traj[t][a.members[0]]
                                                 for t in range(len(traj))])
        print(f"  A{k}: members={a.members}  radius={a.radius:.3f}  "
              f"stability={a.stability:.3f}  type={atype.value}")

    # 韧性测试：施加扰动
    print("\n[RECOVERY] 在 step=40 施加扰动幅度 0.5：")
    traj2 = dyn.simulate(agents, K, steps=80,
                         perturb_at_step=40, perturb_amplitude=0.5)
    for i in range(N):
        tau = dyn.compute_recovery_time([traj2[t][i] for t in range(len(traj2))],
                                       perturbation_step=40, tolerance=0.08)
        print(f"  agent {i}: τ = {tau:.1f} 步")

    print("\n[OK] attractor_dynamics demo 完成。")
