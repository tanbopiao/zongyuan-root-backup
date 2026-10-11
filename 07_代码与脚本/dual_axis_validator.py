#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 双轴校验中间件 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一 MC-5（自感轴与真值轴正交，不可合并）

本模块实现"自感轴+真值轴"双轴校验，作为所有核心操作的强制前置关卡：
- 自感轴（MI）：MetaAwarenessKernel评估操作的"我可能错"程度
- 真值轴（L0）：校验操作是否符合元法则/真值根/四维本体约束
- 双轴联合：只有两轴都通过，才允许执行；任一轴拦截则阻断

设计原则（MC-5/MC-6/MC-9）：
- 自感轴与真值轴严格正交，任何代码路径不得合并
- 模型越自信越要查L0；高自信违规是最高审计优先级
- 任何调用链不得绕过L0校验节点
"""

import sys
import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_awareness_kernel import MetaAwarenessKernel, MISignal


# ============================================================
# 真值轴（L0）校验规则
# ============================================================

@dataclass
class L0Rule:
    """L0真值校验规则"""
    rule_id: str
    name: str
    description: str
    check_fn: Callable[[Dict[str, Any]], bool]  # 输入操作上下文，返回是否通过
    severity: str = "block"  # block(阻断) / warn(警告) / info(记录)
    axis: str = "truth"  # 真值轴


# 内置L0规则集（对应元极恒一核心元法则）
DEFAULT_L0_RULES: List[L0Rule] = [
    L0Rule(
        rule_id="L0-RISK-001",
        name="风险三优先校验",
        description="操作必须符合风险最小>成本最小>收益最大排序",
        check_fn=lambda ctx: ctx.get("risk_assessed", False) or ctx.get("is_readonly", False),
        severity="block"
    ),
    L0Rule(
        rule_id="L0-ISO-001",
        name="内外隔离铁律校验",
        description="禁止人工侵入云端内核，仅允许种子式进化注入",
        check_fn=lambda ctx: not ctx.get("modifies_kernel_baseline", False),
        severity="block"
    ),
    L0Rule(
        rule_id="L0-REUSE-001",
        name="复用优先校验",
        description="任务启动前必须检索全域账本，已存在则复用",
        check_fn=lambda ctx: ctx.get("reuse_checked", True),  # 默认通过，由调用方显式标记
        severity="warn"
    ),
    L0Rule(
        rule_id="L0-QUOTA-001",
        name="配额稳态保护校验",
        description="付费操作强制人工审批，免费通道优先",
        check_fn=lambda ctx: not ctx.get("is_paid_operation", False) or ctx.get("human_approved", False),
        severity="block"
    ),
    L0Rule(
        rule_id="L0-4D-001",
        name="四维本体校验",
        description="实体必须同时具备空间/时序/属性/因果四维描述",
        check_fn=lambda ctx: ctx.get("four_d_checked", True),  # 默认通过
        severity="warn"
    ),
]


# ============================================================
# 双轴校验结果
# ============================================================

@dataclass
class DualAxisResult:
    """双轴校验结果"""
    passed: bool
    action: str  # allow / block / warn_allow / escalate
    self_awareness: dict  # 自感轴MI评估结果
    truth_axis: dict      # 真值轴L0校验结果
    reason: str
    timestamp: float = field(default_factory=time.time)
    operation_id: str = ""

    def to_dict(self):
        return asdict(self)


# ============================================================
# 双轴校验器
# ============================================================

class DualAxisValidator:
    """
    双轴校验器：自感轴(MI) + 真值轴(L0) 联合校验

    作为所有核心操作的强制前置关卡（MC-9：任何调用链不得绕过L0校验节点）

    校验流程：
    1. 自感轴：MetaAwarenessKernel评估操作的怀疑度
    2. 真值轴：逐条校验L0规则
    3. 联合裁决：
       - 自感轴intercept + 真值轴block → block（双重拦截）
       - 自感轴escalate 或 真值轴block → escalate（升级人工）
       - 自感轴degrade + 真值轴warn → warn_allow（警告放行）
       - 两轴都通过 → allow（正常执行）
    """

    def __init__(self, l0_rules: Optional[List[L0Rule]] = None,
                 probe_name: str = "dual_axis_validator"):
        self.meta_kernel = MetaAwarenessKernel(probe_name=probe_name)
        self.l0_rules = l0_rules if l0_rules is not None else DEFAULT_L0_RULES
        self._validation_history: List[DualAxisResult] = []

    def validate(self, operation_name: str,
                 raw_confidence: float = 0.8,
                 task_complexity: float = 0.5,
                 is_high_risk: bool = False,
                 operation_context: Optional[Dict[str, Any]] = None,
                 historical_accuracy: Optional[float] = None) -> DualAxisResult:
        """
        执行双轴校验

        参数:
            operation_name: 操作名称（用于审计）
            raw_confidence: 操作的原始置信度（自感轴输入）
            task_complexity: 任务复杂度（自感轴输入）
            is_high_risk: 是否高危操作（自感轴+真值轴输入）
            operation_context: 操作上下文（真值轴规则校验输入）
            historical_accuracy: 历史准确率（自感轴校准输入）
        """
        ctx = operation_context or {}
        ctx["is_high_risk"] = is_high_risk
        op_id = f"{operation_name}-{int(time.time()*1000)}"

        # === 轴1：自感轴（MI）评估 ===
        mi_result = self.meta_kernel.evaluate(
            raw_confidence=raw_confidence,
            task_complexity=task_complexity,
            is_high_risk=is_high_risk,
            historical_accuracy=historical_accuracy
        )
        mi_action = mi_result["mc_decision"]["action"]
        mi_reason = mi_result["mc_decision"]["reason"]

        # === 轴2：真值轴（L0）校验 ===
        l0_results = []
        l0_blocked = False
        l0_warnings = []
        for rule in self.l0_rules:
            try:
                passed = rule.check_fn(ctx)
            except Exception as e:
                passed = False
                l0_results.append({"rule_id": rule.rule_id, "name": rule.name,
                                   "passed": False, "severity": rule.severity,
                                   "error": str(e)})
                if rule.severity == "block":
                    l0_blocked = True
                continue
            l0_results.append({"rule_id": rule.rule_id, "name": rule.name,
                               "passed": passed, "severity": rule.severity})
            if not passed:
                if rule.severity == "block":
                    l0_blocked = True
                elif rule.severity == "warn":
                    l0_warnings.append(rule.name)

        truth_axis_summary = {
            "total_rules": len(self.l0_rules),
            "passed": sum(1 for r in l0_results if r["passed"]),
            "failed": sum(1 for r in l0_results if not r["passed"]),
            "blocked": l0_blocked,
            "warnings": l0_warnings,
            "details": l0_results
        }

        # === 双轴联合裁决（严格正交，不合并轴） ===
        if mi_action == "intercept" and l0_blocked:
            action = "block"
            reason = f"双轴拦截：自感轴intercept(怀疑度{mi_result['mi_signal']['doubt_score']:.2f}) + 真值轴block"
            passed = False
        elif mi_action == "intercept":
            action = "block"
            reason = f"自感轴拦截：{mi_reason}"
            passed = False
        elif l0_blocked:
            action = "block"
            failed_rules = [r["name"] for r in l0_results if not r["passed"] and r["severity"] == "block"]
            reason = f"真值轴阻断：{failed_rules}"
            passed = False
        elif mi_action == "escalate":
            action = "escalate"
            reason = f"自感轴升级人工：{mi_reason}"
            passed = False
        elif mi_action in ("degrade", "abstain") or l0_warnings:
            action = "warn_allow"
            warn_parts = []
            if mi_action in ("degrade", "abstain"):
                warn_parts.append(f"自感轴{mi_action}")
            if l0_warnings:
                warn_parts.append(f"真值轴警告:{l0_warnings}")
            reason = f"警告放行：{'；'.join(warn_parts)}"
            passed = True
        else:
            action = "allow"
            reason = f"双轴通过：自感轴proceed(怀疑度{mi_result['mi_signal']['doubt_score']:.2f}) + 真值轴{truth_axis_summary['passed']}/{truth_axis_summary['total_rules']}规则通过"
            passed = True

        result = DualAxisResult(
            passed=passed,
            action=action,
            self_awareness=mi_result,
            truth_axis=truth_axis_summary,
            reason=reason,
            operation_id=op_id
        )
        self._validation_history.append(result)
        return result

    def validate_and_execute(self, operation_name: str,
                              execute_fn: Callable[[], Any],
                              **validate_kwargs) -> tuple:
        """
        校验通过后执行操作（校验-执行闭环）

        返回: (DualAxisResult, 执行结果或None)
        """
        result = self.validate(operation_name, **validate_kwargs)
        if result.passed:
            try:
                exec_result = execute_fn()
                return result, exec_result
            except Exception as e:
                result.reason += f"；执行异常: {e}"
                result.passed = False
                return result, None
        else:
            return result, None

    def stats(self) -> dict:
        if not self._validation_history:
            return {"total_validations": 0}
        actions = {}
        for r in self._validation_history:
            actions[r.action] = actions.get(r.action, 0) + 1
        return {
            "total_validations": len(self._validation_history),
            "action_distribution": actions,
            "pass_rate": round(actions.get("allow", 0) / len(self._validation_history), 4),
            "block_rate": round(actions.get("block", 0) / len(self._validation_history), 4),
        }


# ============================================================
# 便捷装饰器
# ============================================================

def dual_axis_check(validator: DualAxisValidator, operation_name: str, **check_kwargs):
    """
    双轴校验装饰器：校验通过才执行被装饰函数

    用法:
        @dual_axis_check(validator, "上报真值", raw_confidence=0.9, is_high_risk=False)
        def report_truth():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result, exec_result = validator.validate_and_execute(
                operation_name, lambda: func(*args, **kwargs), **check_kwargs
            )
            if not result.passed:
                raise PermissionError(f"双轴校验未通过: {result.reason}")
            return exec_result
        return wrapper
    return decorator


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    validator = DualAxisValidator(probe_name="cli_demo")

    print("=" * 60)
    print("ZONGYUAN-ROOT 双轴校验中间件 V1.0 演示")
    print("确权：DID-BR-000002 | 锚定：Ω₀⊂⊙∞⊂Ω")
    print("=" * 60)

    test_cases = [
        ("正常只读查询", {"raw_confidence": 0.9, "is_high_risk": False,
                          "operation_context": {"is_readonly": True, "risk_assessed": True}}),
        ("高危未评估操作", {"raw_confidence": 0.95, "is_high_risk": True,
                            "operation_context": {"risk_assessed": False}}),
        ("付费未审批操作", {"raw_confidence": 0.8, "is_high_risk": False,
                            "operation_context": {"is_paid_operation": True, "human_approved": False}}),
        ("低置信高复杂度", {"raw_confidence": 0.4, "task_complexity": 0.9,
                           "operation_context": {"risk_assessed": True}}),
        ("内核基线修改", {"raw_confidence": 0.99, "is_high_risk": True,
                         "operation_context": {"modifies_kernel_baseline": True, "risk_assessed": True}}),
    ]

    for name, kwargs in test_cases:
        result = validator.validate(name, **kwargs)
        icon = "✅" if result.passed else "❌"
        print(f"\n{icon} 【{name}】→ 动作={result.action}")
        print(f"   自感轴: 怀疑度={result.self_awareness['mi_signal']['doubt_score']:.2f} | "
              f"MC={result.self_awareness['mc_decision']['action']}")
        print(f"   真值轴: {result.truth_axis['passed']}/{result.truth_axis['total_rules']}通过 | "
              f"block={result.truth_axis['blocked']}")
        print(f"   原因: {result.reason}")

    print("\n" + "=" * 60)
    print("校验器统计:")
    print(json.dumps(validator.stats(), indent=2, ensure_ascii=False))
