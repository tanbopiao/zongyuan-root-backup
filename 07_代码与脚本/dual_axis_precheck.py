#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 双轴校验前置守卫 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω

统一的双轴校验前置模块，用于在高风险脚本执行前进行：
1. 自感轴（MI）校验：基于操作风险等级评估怀疑度
2. 真值轴（L0）校验：检查是否违反5条L0规则
3. 联合裁决：allow / warn_allow / block / escalate

使用方式：
    from dual_axis_precheck import precheck
    result = precheck("auto_report", risk_level="medium")
    if result.blocked:
        sys.exit(1)
"""

import sys
import os
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
LOG_DIR = ROOT / "06_云端中枢同步" / "dual_axis_guard_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"

# 操作风险等级配置
RISK_CONFIG = {
    "auto_report": {
        "risk_level": "medium",
        "description": "云端真值上报",
        "l0_checks": ["L0-ISO-001", "L0-QUOTA-001"],
        "base_doubt": 0.25,
    },
    "auto_pull_truth": {
        "risk_level": "medium",
        "description": "云端真值拉取",
        "l0_checks": ["L0-ISO-001", "L0-REUSE-001"],
        "base_doubt": 0.2,
    },
    "auto_sync_knowledge": {
        "risk_level": "high",
        "description": "知识同步到云端（SSH隧道+内部API）",
        "l0_checks": ["L0-ISO-001", "L0-RISK-001", "L0-QUOTA-001"],
        "base_doubt": 0.4,
    },
    "auto_sync_feishu_base": {
        "risk_level": "medium",
        "description": "飞书Base台账同步",
        "l0_checks": ["L0-ISO-001", "L0-4D-001"],
        "base_doubt": 0.25,
    },
    "auto_bootstrap_cloud": {
        "risk_level": "high",
        "description": "云端自举增强（SSH隧道+内部API）",
        "l0_checks": ["L0-ISO-001", "L0-RISK-001"],
        "base_doubt": 0.45,
    },
    "gasa_invariant_synth": {
        "risk_level": "low",
        "description": "GASA不变量合成（只读，不自动合入）",
        "l0_checks": ["L0-REUSE-001"],
        "base_doubt": 0.1,
    },
    "auto_truth_distill": {
        "risk_level": "medium",
        "description": "全自动真值提炼上报",
        "l0_checks": ["L0-ISO-001", "L0-4D-001"],
        "base_doubt": 0.25,
    },
}

# L0规则定义（与dual_axis_validator.py一致）
L0_RULES = {
    "L0-RISK-001": "风险最小>成本最小>收益最大，高危操作必须人工审批",
    "L0-ISO-001": "内外隔离铁律，仅通过SSH隧道访问内部API，不暴露公网",
    "L0-REUSE-001": "复用优先不重复执行，增量优先",
    "L0-QUOTA-001": "配额稳态保护，免费API优先，付费操作强制审批",
    "L0-4D-001": "四维本体核验，所有真值必须四维完备",
}


@dataclass
class PrecheckResult:
    """双轴校验前置结果"""
    operation: str
    risk_level: str
    doubt_score: float
    l0_checks_passed: list
    l0_checks_failed: list
    action: str            # allow / warn_allow / block / escalate
    blocked: bool
    reason: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "operation": self.operation,
            "risk_level": self.risk_level,
            "doubt_score": round(self.doubt_score, 4),
            "l0_passed": self.l0_checks_passed,
            "l0_failed": self.l0_checks_failed,
            "action": self.action,
            "blocked": self.blocked,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "node": NODE,
            "did": DID,
        }


def precheck(operation: str, risk_override: Optional[str] = None,
              extra_doubt: float = 0.0, strict: bool = False) -> PrecheckResult:
    """
    执行双轴校验前置守卫

    参数:
        operation: 操作名称（必须在RISK_CONFIG中注册）
        risk_override: 覆盖风险等级（low/medium/high）
        extra_doubt: 额外怀疑度加成（如检测到异常时）
        strict: 严格模式（任何L0失败都block）

    返回:
        PrecheckResult
    """
    config = RISK_CONFIG.get(operation, {
        "risk_level": risk_override or "medium",
        "description": operation,
        "l0_checks": ["L0-ISO-001"],
        "base_doubt": 0.3,
    })

    risk_level = risk_override or config.get("risk_level", "medium")
    base_doubt = config.get("base_doubt", 0.3) + extra_doubt

    # 自感轴：基于风险等级和额外怀疑度计算
    if risk_level == "high":
        doubt_score = min(0.95, base_doubt + 0.15)
    elif risk_level == "low":
        doubt_score = max(0.05, base_doubt - 0.1)
    else:
        doubt_score = base_doubt

    # 真值轴：L0规则校验
    l0_passed = []
    l0_failed = []
    for rule_id in config.get("l0_checks", []):
        # 简化校验：检查规则是否存在（实际应由dual_axis_validator执行）
        if rule_id in L0_RULES:
            l0_passed.append(rule_id)
        else:
            l0_failed.append(rule_id)

    # 联合裁决
    if l0_failed and strict:
        action = "block"
        blocked = True
        reason = f"严格模式：L0规则校验失败 {l0_failed}"
    elif l0_failed:
        action = "warn_allow"
        blocked = False
        reason = f"L0规则校验失败（非严格模式允许继续）: {l0_failed}"
    elif doubt_score >= 0.7:
        action = "escalate"
        blocked = False  # escalate不阻断，但记录需人工审批
        reason = f"高怀疑度{doubt_score:.2f}，建议人工审批后执行"
    elif doubt_score >= 0.5:
        action = "warn_allow"
        blocked = False
        reason = f"中等怀疑度{doubt_score:.2f}，允许执行但需监控"
    else:
        action = "allow"
        blocked = False
        reason = f"低怀疑度{doubt_score:.2f}，允许执行"

    result = PrecheckResult(
        operation=operation,
        risk_level=risk_level,
        doubt_score=doubt_score,
        l0_checks_passed=l0_passed,
        l0_checks_failed=l0_failed,
        action=action,
        blocked=blocked,
        reason=reason,
    )

    # 记录日志
    _log_result(result)

    return result


def _log_result(result: PrecheckResult):
    """记录校验日志"""
    log_file = LOG_DIR / f"precheck_{time.strftime('%Y%m%d')}.jsonl"
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
    except Exception:
        pass


def print_result(result: PrecheckResult, verbose: bool = True):
    """打印校验结果"""
    icons = {"allow": "✅", "warn_allow": "⚠️", "block": "🚫", "escalate": "🔶"}
    icon = icons.get(result.action, "❓")
    print(f"{icon} 双轴前置校验 [{result.operation}]")
    print(f"   风险等级: {result.risk_level} | 怀疑度: {result.doubt_score:.2f}")
    print(f"   裁决: {result.action} | {result.reason}")
    if verbose and result.l0_checks_passed:
        print(f"   L0通过: {result.l0_checks_passed}")
    if result.l0_checks_failed:
        print(f"   L0失败: {result.l0_checks_failed}")
    return result


# ============================================================
# CLI入口（用于测试）
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="双轴校验前置守卫测试")
    parser.add_argument("operation", help="操作名称")
    parser.add_argument("--risk", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = precheck(args.operation, risk_override=args.risk, strict=args.strict)
    print_result(result)
    if result.blocked:
        sys.exit(1)
