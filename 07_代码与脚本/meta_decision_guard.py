#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 6H定时任务元意识决策前置守卫 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω

在6H定时任务每个步骤执行前，通过元意识决策编排器评估怀疑度，
动态选择执行策略（proceed/degrade/abstain/intercept/escalate）。

集成方式：
- 6H定时任务query中每个步骤前调用本脚本评估
- 评估结果写入决策日志，供执行后反馈闭环使用
- degrade策略自动切换免费API/减少批量/跳过消耗型操作

使用方式：
    python3 meta_decision_guard.py <step_name> [--risk high|medium|low] [--doubt 0.0-1.0]
    返回JSON: {"action": "proceed|degrade|abstain|intercept|escalate", "doubt_score": 0.25, ...}
"""

import json
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
DECISION_LOG_DIR = ROOT / "06_云端中枢同步" / "meta_decision_feedback"
DECISION_LOG_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"

# 6H定时任务步骤风险配置
STEP_RISK_CONFIG = {
    "converge_norm": {"risk": "low", "base_doubt": 0.1, "description": "收敛归一前置检查"},
    "on_demand_producer": {"risk": "medium", "base_doubt": 0.3, "description": "按需生产（可能调用付费API）"},
    "channel_probe": {"risk": "low", "base_doubt": 0.1, "description": "云端通道探测"},
    "auto_report": {"risk": "medium", "base_doubt": 0.25, "description": "云端真值上报"},
    "feishu_relay": {"risk": "medium", "base_doubt": 0.25, "description": "飞书中转兜底"},
    "feishu_base_sync": {"risk": "medium", "base_doubt": 0.25, "description": "飞书Base台账同步"},
    "feishu_notify": {"risk": "low", "base_doubt": 0.15, "description": "飞书通知推送"},
    "auto_sync_knowledge": {"risk": "high", "base_doubt": 0.4, "description": "知识同步（SSH隧道+内部API）"},
    "auto_bootstrap_cloud": {"risk": "high", "base_doubt": 0.45, "description": "云端自举增强（SSH隧道+内部API）"},
    "auto_pull_truth": {"risk": "medium", "base_doubt": 0.2, "description": "云端真值拉取"},
    "memory_index_integration": {"risk": "low", "base_doubt": 0.15, "description": "记忆索引增量接入"},
    "gasa_invariant_synth": {"risk": "low", "base_doubt": 0.1, "description": "GASA不变量合成（只读）"},
    "auto_truth_distill": {"risk": "medium", "base_doubt": 0.25, "description": "全自动真值提炼上报"},
}

# 策略阈值
THRESHOLDS = {
    "proceed_max": 0.3,
    "degrade_max": 0.5,
    "abstain_max": 0.7,
    "intercept_max": 0.9,
}


@dataclass
class GuardDecision:
    """守卫决策结果"""
    step_name: str
    risk_level: str
    doubt_score: float
    action: str
    reason: str
    degrade_config: Optional[dict] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "step_name": self.step_name,
            "risk_level": self.risk_level,
            "doubt_score": round(self.doubt_score, 4),
            "action": self.action,
            "reason": self.reason,
            "degrade_config": self.degrade_config,
            "timestamp": self.timestamp,
            "node": NODE,
            "did": DID,
        }


def classify_action(doubt_score: float, is_high_risk: bool) -> str:
    """根据怀疑度分类执行策略"""
    d = doubt_score
    # 高风险操作阈值更严格
    if is_high_risk:
        if d <= 0.2:
            return "proceed"
        elif d <= 0.4:
            return "degrade"
        elif d <= 0.6:
            return "abstain"
        elif d <= 0.85:
            return "intercept"
        else:
            return "escalate"
    else:
        if d <= THRESHOLDS["proceed_max"]:
            return "proceed"
        elif d <= THRESHOLDS["degrade_max"]:
            return "degrade"
        elif d <= THRESHOLDS["abstain_max"]:
            return "abstain"
        elif d <= THRESHOLDS["intercept_max"]:
            return "intercept"
        else:
            return "escalate"


def get_degrade_config(step_name: str) -> dict:
    """获取降级执行配置"""
    configs = {
        "on_demand_producer": {"limit": 5, "skip_paid_api": True, "use_free_only": True},
        "auto_report": {"batch_size": 10, "retry_count": 1, "timeout": 5},
        "auto_sync_knowledge": {"max_nodes": 10, "skip_ssh": False, "timeout": 8},
        "auto_bootstrap_cloud": {"skip_ssh": True, "read_only": True},
        "auto_truth_distill": {"max_candidates": 10, "value_threshold": 0.7},
        "gasa_invariant_synth": {"max_candidates": 2, "skip_z3": False},
    }
    return configs.get(step_name, {"limit": 5, "read_only": True})


def guard(step_name: str, risk_override: Optional[str] = None,
          doubt_override: Optional[float] = None) -> GuardDecision:
    """
    执行元意识决策守卫

    参数:
        step_name: 步骤名称（必须在STEP_RISK_CONFIG中注册）
        risk_override: 覆盖风险等级
        doubt_override: 覆盖怀疑度（0.0~1.0）

    返回:
        GuardDecision
    """
    config = STEP_RISK_CONFIG.get(step_name, {
        "risk": risk_override or "medium",
        "base_doubt": 0.3,
        "description": step_name,
    })

    risk_level = risk_override or config.get("risk", "medium")
    base_doubt = config.get("base_doubt", 0.3)

    # 计算怀疑度（基础怀疑度 + 随机扰动模拟MI信号）
    import random
    random.seed(int(time.time()) + hash(step_name) % 10000)
    mi_noise = random.uniform(-0.05, 0.05)  # MI信号微小扰动
    doubt_score = max(0.0, min(1.0, base_doubt + mi_noise))

    if doubt_override is not None:
        doubt_score = doubt_override

    is_high_risk = risk_level == "high"
    action = classify_action(doubt_score, is_high_risk)

    # 生成原因和降级配置
    reasons = {
        "proceed": f"低怀疑度{doubt_score:.2f}，正常执行",
        "degrade": f"中等怀疑度{doubt_score:.2f}，降级执行（免费API优先/减少批量）",
        "abstain": f"较高怀疑度{doubt_score:.2f}，弃答消耗型操作，保留查询/巡检",
        "intercept": f"高怀疑度{doubt_score:.2f}，拦截操作并告警",
        "escalate": f"极高怀疑度{doubt_score:.2f}，升级人工审批",
    }
    reason = reasons.get(action, "未知")

    degrade_config = get_degrade_config(step_name) if action == "degrade" else None

    decision = GuardDecision(
        step_name=step_name,
        risk_level=risk_level,
        doubt_score=doubt_score,
        action=action,
        reason=reason,
        degrade_config=degrade_config,
    )

    # 记录决策日志（供执行后反馈闭环使用）
    _log_decision(decision)

    return decision


def _log_decision(decision: GuardDecision):
    """记录决策日志"""
    log_file = DECISION_LOG_DIR / f"guard_decisions_{time.strftime('%Y%m%d')}.jsonl"
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + "\n")
    except Exception:
        pass


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="6H定时任务元意识决策前置守卫")
    parser.add_argument("step_name", help="步骤名称")
    parser.add_argument("--risk", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--doubt", type=float, default=None, help="怀疑度覆盖(0.0-1.0)")
    parser.add_argument("--list", action="store_true", help="列出所有已注册步骤")
    args = parser.parse_args()

    if args.list:
        print("已注册步骤:")
        for step, cfg in STEP_RISK_CONFIG.items():
            print(f"  {step}: risk={cfg['risk']}, doubt={cfg['base_doubt']} - {cfg['description']}")
        sys.exit(0)

    decision = guard(args.step_name, risk_override=args.risk, doubt_override=args.doubt)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))

    # 退出码：intercept/escalate返回非零，供shell判断是否跳过
    if decision.action in ("intercept", "escalate"):
        sys.exit(2)
    elif decision.action == "abstain":
        sys.exit(1)
