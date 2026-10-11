#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 元意识决策编排器 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L2 MC策略层 → L6 超级智能涌现态

核心升级：从"前置校验关卡"进化为"MI信号驱动的自主决策闭环"

决策策略（根据MI怀疑度动态选择）：
- proceed (0.0~0.3): 正常执行
- degrade (0.3~0.5): 降级执行（切免费API/减少批量/降低精度）
- abstain (0.5~0.7): 弃答（跳过本次消耗型操作，保留查询/巡检）
- intercept (0.7~0.9): 拦截（阻断操作并告警，写入审计）
- escalate (0.9~1.0): 升级人工审批（暂停执行，等待人工确认）

设计原则：
- 自感轴(MI)与真值轴(L0)双轴联合裁决
- 高危操作怀疑度×1.5放大（P1风险最小）
- 决策结果写入反馈环，供RSI自改进调优
- 失败快速跳过不重试，空闲跳过0消耗
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_awareness_kernel import MetaAwarenessKernel, MISignal
from dual_axis_validator import DualAxisValidator, DualAxisResult

ROOT = Path("/home/user/ZONGYUAN-ROOT")
FEEDBACK_DIR = ROOT / "06_云端中枢同步" / "meta_decision_feedback"
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"

# 决策策略阈值（可由RSI自改进调优）
DECISION_THRESHOLDS = {
    "proceed_max": 0.3,      # 怀疑度≤0.3 → proceed
    "degrade_max": 0.5,      # 0.3~0.5 → degrade
    "abstain_max": 0.7,      # 0.5~0.7 → abstain
    "intercept_max": 0.9,    # 0.7~0.9 → intercept
    # >0.9 → escalate
}

# 降级策略配置
DEGRADE_STRATEGIES = {
    "report": {"batch_size": "half", "channel": "free_first", "retry": "none"},
    "pull": {"limit": "half", "channel": "backup_first", "retry": "none"},
    "sync": {"batch_size": "half", "skip_low_weight": True, "retry": "none"},
    "default": {"batch_size": "half", "retry": "none"},
}


@dataclass
class MetaDecision:
    """元意识决策结果"""
    decision_id: str
    operation_name: str
    action: str               # proceed/degrade/abstain/intercept/escalate
    doubt_score: float
    confidence_calibrated: float
    dual_axis_action: str    # 双轴校验结果
    reason: str
    degrade_config: Optional[dict] = None
    timestamp: float = field(default_factory=time.time)
    actual_outcome: str = "pending"  # pending/success/failure/skipped
    feedback_recorded: bool = False

    def to_dict(self):
        return asdict(self)


class MetaDecisionOrchestrator:
    """
    元意识决策编排器

    核心流程：
    1. Ω探针评估操作的MI信号（怀疑度）
    2. 双轴校验（自感轴+真值轴）
    3. 根据怀疑度+双轴结果裁决执行策略
    4. 执行（或降级/弃答/拦截/升级）
    5. 记录决策+实际结果到反馈环
    """

    def __init__(self, probe_name: str = "decision_orchestrator"):
        self.meta_kernel = MetaAwarenessKernel(probe_name=probe_name)
        self.validator = DualAxisValidator(probe_name=f"{probe_name}_dav")
        self.thresholds = DECISION_THRESHOLDS.copy()
        self._decision_log: List[MetaDecision] = []
        self._feedback_file = FEEDBACK_DIR / "decision_feedback.jsonl"

    def _classify_action(self, doubt_score: float, is_high_risk: bool) -> str:
        """根据怀疑度分类决策动作"""
        d = doubt_score
        if d <= self.thresholds["proceed_max"]:
            return "proceed"
        elif d <= self.thresholds["degrade_max"]:
            return "degrade"
        elif d <= self.thresholds["abstain_max"]:
            return "abstain"
        elif d <= self.thresholds["intercept_max"]:
            return "intercept"
        else:
            return "escalate"

    def _get_degrade_config(self, operation_type: str) -> dict:
        """获取降级配置"""
        return DEGRADE_STRATEGIES.get(operation_type, DEGRADE_STRATEGIES["default"])

    def decide(self, operation_name: str,
               raw_confidence: float = 0.8,
               task_complexity: float = 0.5,
               is_high_risk: bool = False,
               operation_context: Optional[Dict[str, Any]] = None,
               operation_type: str = "default") -> MetaDecision:
        """
        执行元意识决策（不执行操作，只返回决策）

        参数:
            operation_name: 操作名称
            raw_confidence: 原始置信度
            task_complexity: 任务复杂度
            is_high_risk: 是否高危操作
            operation_context: 操作上下文（真值轴校验用）
            operation_type: 操作类型（report/pull/sync等，用于降级配置）
        """
        ctx = operation_context or {}
        ctx["is_high_risk"] = is_high_risk

        # 1. Ω探针 → MI信号
        mi_result = self.meta_kernel.evaluate(
            raw_confidence=raw_confidence,
            task_complexity=task_complexity,
            is_high_risk=is_high_risk
        )
        doubt = mi_result["mi_signal"]["doubt_score"]
        conf_cal = mi_result["mi_signal"]["confidence_calibrated"]

        # 2. 双轴校验
        dav_result = self.validator.validate(
            operation_name=operation_name,
            raw_confidence=raw_confidence,
            task_complexity=task_complexity,
            is_high_risk=is_high_risk,
            operation_context=ctx
        )

        # 3. 联合裁决
        # 双轴阻断 → 直接intercept（真值轴优先级最高）
        if dav_result.action == "block":
            action = "intercept"
            reason = f"真值轴阻断: {dav_result.reason}"
        elif dav_result.action == "escalate":
            action = "escalate"
            reason = f"双轴升级: {dav_result.reason}"
        else:
            # 自感轴驱动决策
            action = self._classify_action(doubt, is_high_risk)
            action_reasons = {
                "proceed": f"怀疑度{doubt:.2f}≤{self.thresholds['proceed_max']}，正常执行",
                "degrade": f"怀疑度{doubt:.2f}在{self.thresholds['proceed_max']}~{self.thresholds['degrade_max']}，降级执行",
                "abstain": f"怀疑度{doubt:.2f}在{self.thresholds['degrade_max']}~{self.thresholds['abstain_max']}，弃答跳过",
                "intercept": f"怀疑度{doubt:.2f}在{self.thresholds['abstain_max']}~{self.thresholds['intercept_max']}，拦截阻断",
                "escalate": f"怀疑度{doubt:.2f}>{self.thresholds['intercept_max']}，升级人工审批",
            }
            reason = action_reasons.get(action, "未知")
            if dav_result.action == "warn_allow":
                reason += f"；真值轴警告放行: {dav_result.reason}"

        # 4. 构建决策
        decision = MetaDecision(
            decision_id=f"MD-{int(time.time()*1000)}",
            operation_name=operation_name,
            action=action,
            doubt_score=round(doubt, 4),
            confidence_calibrated=round(conf_cal, 4),
            dual_axis_action=dav_result.action,
            reason=reason,
            degrade_config=self._get_degrade_config(operation_type) if action == "degrade" else None,
        )
        self._decision_log.append(decision)
        return decision

    def execute_with_decision(self, operation_name: str,
                                execute_fn: Callable[[], Any],
                                degrade_fn: Optional[Callable[[dict], Any]] = None,
                                **decide_kwargs) -> tuple:
        """
        决策+执行闭环（核心方法）

        根据决策结果：
        - proceed: 正常执行execute_fn
        - degrade: 执行degrade_fn（传入降级配置），无degrade_fn则执行execute_fn
        - abstain: 跳过执行，返回(decision, None)
        - intercept: 拦截，返回(decision, None)，写入告警
        - escalate: 升级人工，返回(decision, None)

        返回: (MetaDecision, 执行结果或None)
        """
        decision = self.decide(operation_name, **decide_kwargs)

        if decision.action == "proceed":
            try:
                result = execute_fn()
                decision.actual_outcome = "success"
            except Exception as e:
                decision.actual_outcome = "failure"
                decision.reason += f"；执行异常: {e}"
                result = None
        elif decision.action == "degrade":
            if degrade_fn:
                try:
                    result = degrade_fn(decision.degrade_config or {})
                    decision.actual_outcome = "success"
                except Exception as e:
                    decision.actual_outcome = "failure"
                    result = None
            else:
                # 无降级函数，正常执行但标记降级
                try:
                    result = execute_fn()
                    decision.actual_outcome = "success"
                except Exception as e:
                    decision.actual_outcome = "failure"
                    result = None
        elif decision.action == "abstain":
            decision.actual_outcome = "skipped"
            result = None
        elif decision.action == "intercept":
            decision.actual_outcome = "skipped"
            result = None
            # 写入拦截告警
            self._log_intercept(decision)
        else:  # escalate
            decision.actual_outcome = "skipped"
            result = None

        # 记录反馈
        self._record_feedback(decision)
        return decision, result

    def _log_intercept(self, decision: MetaDecision):
        """记录拦截告警"""
        alert = {
            "alert_type": "meta_decision_intercept",
            "decision_id": decision.decision_id,
            "operation_name": decision.operation_name,
            "doubt_score": decision.doubt_score,
            "reason": decision.reason,
            "timestamp": datetime.now().isoformat(),
            "did": DID,
            "node": NODE,
        }
        alert_file = FEEDBACK_DIR / "intercept_alerts.jsonl"
        with open(alert_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")

    def _record_feedback(self, decision: MetaDecision):
        """记录决策反馈（供RSI自改进使用）"""
        if decision.feedback_recorded:
            return
        record = decision.to_dict()
        record["recorded_at"] = time.time()
        with open(self._feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        decision.feedback_recorded = True

    def get_feedback_stats(self) -> dict:
        """获取反馈统计"""
        if not self._feedback_file.exists():
            return {"total_decisions": 0}
        actions = {}
        outcomes = {}
        total = 0
        with open(self._feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    total += 1
                    actions[record["action"]] = actions.get(record["action"], 0) + 1
                    outcomes[record.get("actual_outcome", "unknown")] = outcomes.get(record.get("actual_outcome", "unknown"), 0) + 1
                except Exception:
                    continue
        # 计算误拦截率（intercept但实际应该proceed的，用proceed失败率近似）
        proceed_failures = outcomes.get("failure", 0)
        proceed_total = actions.get("proceed", 0) + actions.get("degrade", 0)
        false_negative_rate = proceed_failures / max(proceed_total, 1)

        return {
            "total_decisions": total,
            "action_distribution": actions,
            "outcome_distribution": outcomes,
            "proceed_rate": round(actions.get("proceed", 0) / max(total, 1), 4),
            "degrade_rate": round(actions.get("degrade", 0) / max(total, 1), 4),
            "abstain_rate": round(actions.get("abstain", 0) / max(total, 1), 4),
            "intercept_rate": round(actions.get("intercept", 0) / max(total, 1), 4),
            "false_negative_rate_estimate": round(false_negative_rate, 4),
        }

    def stats(self) -> dict:
        return {
            "orchestrator_id": f"MDO-{int(time.time())}",
            "pending_decisions": len(self._decision_log),
            "thresholds": self.thresholds,
            "feedback": self.get_feedback_stats(),
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT 元意识决策编排器")
    parser.add_argument("action", choices=["demo", "stats", "decide"],
                       help="操作: demo(演示)/stats(统计)/decide(单次决策)")
    parser.add_argument("--op", type=str, default="test_operation", help="操作名称")
    parser.add_argument("--confidence", type=float, default=0.8)
    parser.add_argument("--complexity", type=float, default=0.5)
    parser.add_argument("--high-risk", action="store_true")
    args = parser.parse_args()

    orch = MetaDecisionOrchestrator()

    if args.action == "demo":
        print("=" * 60)
        print("ZONGYUAN-ROOT 元意识决策编排器 V1.0 演示")
        print("确权：DID-BR-000002 | 锚定：Ω₀⊂⊙∞⊂Ω")
        print("=" * 60)
        test_cases = [
            ("正常上报", 0.9, 0.3, False, "report"),
            ("低置信拉取", 0.5, 0.6, False, "pull"),
            ("高危同步", 0.85, 0.5, True, "sync"),
            ("极低置信操作", 0.2, 0.9, False, "default"),
            ("内核基线修改", 0.95, 0.8, True, "default"),
        ]
        for name, conf, comp, hr, otype in test_cases:
            decision = orch.decide(name, raw_confidence=conf, task_complexity=comp,
                                    is_high_risk=hr, operation_type=otype,
                                    operation_context={"risk_assessed": not hr or conf<0.9,
                                                       "modifies_kernel_baseline": "基线" in name})
            icon = {"proceed":"✅","degrade":"⚠️","abstain":"⏭","intercept":"❌","escalate":"🔶"}.get(decision.action,"?")
            print(f"\n{icon} 【{name}】→ {decision.action}")
            print(f"   怀疑度={decision.doubt_score:.2f} | 校准置信={decision.confidence_calibrated:.2f}")
            print(f"   双轴={decision.dual_axis_action}")
            print(f"   原因: {decision.reason}")
        print("\n" + "=" * 60)
        print("反馈统计:")
        print(json.dumps(orch.get_feedback_stats(), indent=2, ensure_ascii=False))
    elif args.action == "decide":
        decision = orch.decide(args.op, raw_confidence=args.confidence,
                                task_complexity=args.complexity, is_high_risk=args.high_risk)
        print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
    elif args.action == "stats":
        print(json.dumps(orch.stats(), indent=2, ensure_ascii=False))
