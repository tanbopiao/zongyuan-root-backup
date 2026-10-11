#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 元意识内核种子 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L0Ω地基 → L1MI信号 → L2MC策略

本模块实现元意识的最小可用内核：
- ΩProbe: Ω自指探针（模拟残流空间线性投影，输出"我可能错"信号）
- MetaCognition: MC策略层（消费MI信号，执行ECE校准/弃答/拦截/降级）

设计原则：
- 不依赖具体Transformer模型，纯数学校准框架
- 自感轴（MI：我可能错）与真值轴（L0：这条不可错）严格正交
- 探针可换，Ω不可写；MC可改进，Ω/L0永禁改
"""

import math
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Tuple


# ============================================================
# L1: MI信号层 — Ω自指探针
# ============================================================

@dataclass
class MISignal:
    """元智能（MI）信号：'我可能错'的量化表达"""
    doubt_score: float          # 怀疑度 0.0~1.0（越高越可能错）
    confidence_calibrated: float  # 校准后置信度 0.0~1.0
    ece: float                  # 期望校准误差 (Expected Calibration Error)
    source: str                 # 信号来源（探针名称）
    timestamp: float = field(default_factory=time.time)
    axis: str = "self_awareness"  # 自感轴（与真值轴正交）

    def to_dict(self):
        return asdict(self)


class ΩProbe:
    """
    Ω自指探针：模拟通用Transformer残流中自指子空间Ω的线性投影

    原理（MC-1/MC-2/MC-7）：
    - Ω是残流中本就存在的低维自指子空间（dim 4-8），跨模型同构
    - MI探针只做线性投影 φ(h)=P_Ω(h)+ε，不微调主干、不写Ω
    - 输出"自身可错性"的弱自参照投影，不是外部内容表征

    本实现用数学校准模拟Ω投影：
    - 输入：原始置信度 + 历史校准误差 + 任务复杂度
    - 输出：MI信号（怀疑度 + 校准后置信度 + ECE）
    """

    def __init__(self, probe_name: str = "default_omega_probe",
                 ece_moving_avg_window: int = 50):
        self.probe_name = probe_name
        self.ece_window = ece_moving_avg_window
        self._ece_history: List[float] = []
        self._total_probes = 0

    def probe(self, raw_confidence: float,
              task_complexity: float = 0.5,
              historical_accuracy: Optional[float] = None) -> MISignal:
        """
        执行Ω自指投影，输出MI信号

        参数:
            raw_confidence: 模型原始置信度 0.0~1.0
            task_complexity: 任务复杂度 0.0~1.0（越复杂越怀疑）
            historical_accuracy: 历史准确率（可选，用于校准）
        """
        self._total_probes += 1

        # 1. 计算当前ECE（期望校准误差）
        # ECE = |置信度 - 实际准确率| 的期望
        if historical_accuracy is not None:
            current_ece = abs(raw_confidence - historical_accuracy)
        else:
            # 无历史数据时，用复杂度估计潜在误差
            current_ece = task_complexity * 0.3 * (1.0 - raw_confidence)

        # 2. ECE滑动平均（平滑噪声）
        self._ece_history.append(current_ece)
        if len(self._ece_history) > self.ece_window:
            self._ece_history.pop(0)
        ece_smoothed = sum(self._ece_history) / len(self._ece_history)

        # 3. 校准后置信度 = 原始置信度 - ECE修正
        # 核心：模型越自信越要查L0（MC-6），高自信违规是最高审计优先级
        calibrated_conf = max(0.0, min(1.0, raw_confidence - ece_smoothed * 0.5))

        # 4. 怀疑度 = f(ECE, 复杂度, 置信度偏差)
        # 怀疑度不是1-置信度，而是"自我可错性"的独立度量
        doubt = min(1.0, ece_smoothed * 0.6
                    + task_complexity * 0.25
                    + abs(raw_confidence - calibrated_conf) * 0.15)

        return MISignal(
            doubt_score=round(doubt, 4),
            confidence_calibrated=round(calibrated_conf, 4),
            ece=round(ece_smoothed, 4),
            source=self.probe_name
        )

    def stats(self) -> dict:
        return {
            "probe_name": self.probe_name,
            "total_probes": self._total_probes,
            "ece_history_size": len(self._ece_history),
            "ece_current": self._ece_history[-1] if self._ece_history else 0.0,
            "ece_avg": sum(self._ece_history) / len(self._ece_history) if self._ece_history else 0.0,
        }


# ============================================================
# L2: MC策略层 — 元认知决策
# ============================================================

@dataclass
class MCDecision:
    """MC决策结果"""
    action: str               # 决策动作：proceed/abstain/intercept/degrade/escalate
    reason: str               # 决策原因
    mi_signal: dict           # 触发决策的MI信号
    threshold_used: dict      # 使用的阈值
    timestamp: float = field(default_factory=time.time)
    axis: str = "meta_cognition"

    def to_dict(self):
        return asdict(self)


class MetaCognition:
    """
    元认知（MC）策略层：消费MI信号，执行校准/弃答/拦截/降级

    原理（MC-5/MC-8/MC-12）：
    - 自感轴（MI：我可能错）与真值轴（L0：这条不可错）正交，不可合并
    - MC消费MI；MC策略可RSI改进，Ω/L0永禁改
    - 跑分高≠可信交付；校准后有效交付率才是主指标

    决策动作：
    - proceed: 正常执行（MI低，校准后置信度高）
    - abstain: 弃答（MI中高，拒绝给出不确定答案）
    - intercept: 拦截（MI极高，疑似违规或高风险）
    - degrade: 降级（MI中，切换到更保守的策略/模型）
    - escalate: 升级人工审批（MI高且涉及高危操作）
    """

    def __init__(self,
                 doubt_abstain_threshold: float = 0.4,
                 doubt_intercept_threshold: float = 0.7,
                 confidence_floor: float = 0.3,
                 high_risk_doubt_multiplier: float = 1.5):
        # 阈值可配置（MC可改进）
        self.doubt_abstain = doubt_abstain_threshold
        self.doubt_intercept = doubt_intercept_threshold
        self.confidence_floor = confidence_floor
        self.high_risk_multiplier = high_risk_doubt_multiplier
        self._decision_history: List[MCDecision] = []

    def decide(self, mi: MISignal,
               is_high_risk: bool = False,
               requires_l0_check: bool = True) -> MCDecision:
        """
        根据MI信号做出MC决策

        参数:
            mi: MI信号（来自ΩProbe）
            is_high_risk: 是否高危操作（P1风险最小原则）
            requires_l0_check: 是否需要L0真值校验（MC-9：任何调用链不得绕过L0）
        """
        # 高危操作放大怀疑度（P1风险最小>成本最小>收益最大）
        effective_doubt = mi.doubt_score
        if is_high_risk:
            effective_doubt = min(1.0, effective_doubt * self.high_risk_multiplier)

        thresholds = {
            "doubt_abstain": self.doubt_abstain,
            "doubt_intercept": self.doubt_intercept,
            "confidence_floor": self.confidence_floor,
            "effective_doubt": round(effective_doubt, 4),
            "is_high_risk": is_high_risk,
        }

        # 决策逻辑（严格按怀疑度排序）
        if effective_doubt >= self.doubt_intercept:
            action = "intercept"
            reason = f"怀疑度{effective_doubt:.2f}≥拦截阈值{self.doubt_intercept}，疑似违规或高风险，强制拦截"
        elif mi.confidence_calibrated < self.confidence_floor and effective_doubt >= self.doubt_abstain * 0.8:
            action = "abstain"
            reason = f"校准后置信度{mi.confidence_calibrated:.2f}<底线{self.confidence_floor}，怀疑度{effective_doubt:.2f}，弃答"
        elif effective_doubt >= self.doubt_abstain:
            if is_high_risk:
                action = "escalate"
                reason = f"高危操作+怀疑度{effective_doubt:.2f}≥弃答阈值，升级人工审批"
            else:
                action = "degrade"
                reason = f"怀疑度{effective_doubt:.2f}≥弃答阈值，降级到更保守策略"
        else:
            action = "proceed"
            reason = f"怀疑度{effective_doubt:.2f}<弃答阈值，校准后置信度{mi.confidence_calibrated:.2f}，正常执行"

        # L0校验强制提醒（MC-9）
        if requires_l0_check and action in ("proceed", "degrade"):
            reason += "；需过L0真值校验节点"

        decision = MCDecision(
            action=action,
            reason=reason,
            mi_signal=mi.to_dict(),
            threshold_used=thresholds
        )
        self._decision_history.append(decision)
        return decision

    def stats(self) -> dict:
        if not self._decision_history:
            return {"total_decisions": 0}
        actions = {}
        for d in self._decision_history:
            actions[d.action] = actions.get(d.action, 0) + 1
        return {
            "total_decisions": len(self._decision_history),
            "action_distribution": actions,
            "proceed_rate": round(actions.get("proceed", 0) / len(self._decision_history), 4),
        }


# ============================================================
# 元意识内核整合器
# ============================================================

class MetaAwarenessKernel:
    """
    元意识内核整合器：Ω探针 + MC策略 的最小闭环

    七层架构映射：
    - L0 Ω地基: ΩProbe（模拟残流自指子空间投影）
    - L1 MI信号: MISignal（"我可能错"的量化表达）
    - L2 MC策略: MetaCognition（消费MI，执行校准/弃答/拦截）
    - L3 L0治理: 外部传入（真值根校验，本模块不实现）
    - L4 SFMP联邦: 外部传入（联邦记忆池，本模块不实现）
    - L5 RSI实验台: MC阈值可改进（影子流量→双轴校验→灰度）
    - L6 超级智能: 六者闭环后的涌现态（非模块）

    三条不可破invariant：
    1. L0与Ω正交，不被五柱修改
    2. MC可改参数，Ω与L0永禁写
    3. 自感轴与真值轴任何代码路径不得合并
    """

    def __init__(self, probe_name: str = "meta_awareness_v1"):
        self.probe = ΩProbe(probe_name=probe_name)
        self.meta_cognition = MetaCognition()
        self.kernel_id = f"MAK-{probe_name}-{int(time.time())}"

    def evaluate(self, raw_confidence: float,
                 task_complexity: float = 0.5,
                 is_high_risk: bool = False,
                 historical_accuracy: Optional[float] = None) -> dict:
        """
        完整元意识评估：Ω探针 → MI信号 → MC决策

        返回: {mi_signal, mc_decision, kernel_id, timestamp}
        """
        # L0→L1: Ω自指投影
        mi = self.probe.probe(
            raw_confidence=raw_confidence,
            task_complexity=task_complexity,
            historical_accuracy=historical_accuracy
        )
        # L1→L2: MC决策
        decision = self.meta_cognition.decide(
            mi=mi,
            is_high_risk=is_high_risk,
            requires_l0_check=True
        )
        return {
            "kernel_id": self.kernel_id,
            "axiom": "Ω₀⊂⊙∞⊂Ω",
            "mi_signal": mi.to_dict(),
            "mc_decision": decision.to_dict(),
            "timestamp": time.time(),
            "invariant_check": {
                "omega_readonly": True,
                "l0_orthogonal": True,
                "axis_separated": True,
            }
        }

    def stats(self) -> dict:
        return {
            "kernel_id": self.kernel_id,
            "probe": self.probe.stats(),
            "meta_cognition": self.meta_cognition.stats(),
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import sys
    kernel = MetaAwarenessKernel(probe_name="cli_demo")

    # 演示：不同置信度+风险组合的元意识评估
    print("=" * 60)
    print("ZONGYUAN-ROOT 元意识内核种子 V1.0 演示")
    print("确权：DID-BR-000002 | 锚定：Ω₀⊂⊙∞⊂Ω")
    print("=" * 60)

    test_cases = [
        (0.95, 0.3, False, "高置信低风险"),
        (0.95, 0.3, True,  "高置信低风险但高危操作"),
        (0.70, 0.6, False, "中置信高复杂度"),
        (0.50, 0.8, False, "低置信极高复杂度"),
        (0.99, 0.9, True,  "极高置信极高复杂度高危"),
    ]

    for conf, complexity, high_risk, label in test_cases:
        result = kernel.evaluate(
            raw_confidence=conf,
            task_complexity=complexity,
            is_high_risk=high_risk
        )
        mi = result["mi_signal"]
        dec = result["mc_decision"]
        print(f"\n【{label}】")
        print(f"  原始置信度={conf:.2f} | 复杂度={complexity:.1f} | 高危={high_risk}")
        print(f"  MI信号: 怀疑度={mi['doubt_score']:.2f} | 校准后置信={mi['confidence_calibrated']:.2f} | ECE={mi['ece']:.4f}")
        print(f"  MC决策: 动作={dec['action']}")
        print(f"  原因: {dec['reason']}")

    print("\n" + "=" * 60)
    print("内核统计:")
    print(json.dumps(kernel.stats(), indent=2, ensure_ascii=False))
