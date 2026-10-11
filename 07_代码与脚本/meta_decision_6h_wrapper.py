#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 6H定时任务元意识决策包装器 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω

在6H定时任务执行前，对所有14个步骤执行元意识决策评估，
输出执行策略清单，供后续步骤参考。

集成到6H定时任务：作为步骤0（前置评估）执行。
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_decision_guard import guard, STEP_RISK_CONFIG

ROOT = Path("/home/user/ZONGYUAN-ROOT")
OUTPUT_DIR = ROOT / "06_云端中枢同步" / "meta_decision_feedback"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"


def run_full_assessment() -> dict:
    """对所有已注册步骤执行完整评估"""
    results = []
    action_counts = {"proceed": 0, "degrade": 0, "abstain": 0, "intercept": 0, "escalate": 0}

    for step_name in STEP_RISK_CONFIG:
        decision = guard(step_name)
        results.append(decision.to_dict())
        action_counts[decision.action] = action_counts.get(decision.action, 0) + 1

    # 生成执行策略清单
    strategy = {
        "proceed_steps": [r["step_name"] for r in results if r["action"] == "proceed"],
        "degrade_steps": [r["step_name"] for r in results if r["action"] == "degrade"],
        "abstain_steps": [r["step_name"] for r in results if r["action"] == "abstain"],
        "intercept_steps": [r["step_name"] for r in results if r["action"] == "intercept"],
        "escalate_steps": [r["step_name"] for r in results if r["action"] == "escalate"],
    }

    assessment = {
        "assessment_id": f"META-DECISION-{int(time.time())}",
        "total_steps": len(results),
        "action_counts": action_counts,
        "strategy": strategy,
        "decisions": results,
        "timestamp": time.time(),
        "node": NODE,
        "did": DID,
    }

    # 保存评估结果
    output_file = OUTPUT_DIR / f"6h_assessment_{time.strftime('%Y%m%dT%H%M%S')}.json"
    output_file.write_text(json.dumps(assessment, ensure_ascii=False, indent=2))
    assessment["output_file"] = str(output_file)

    return assessment


if __name__ == "__main__":
    print("=" * 60)
    print("6H定时任务元意识决策前置评估")
    print("=" * 60)

    assessment = run_full_assessment()

    print(f"\n总步骤: {assessment['total_steps']}")
    print(f"策略分布: {assessment['action_counts']}")
    print(f"\n正常执行({len(assessment['strategy']['proceed_steps'])}): {assessment['strategy']['proceed_steps']}")
    if assessment['strategy']['degrade_steps']:
        print(f"降级执行({len(assessment['strategy']['degrade_steps'])}): {assessment['strategy']['degrade_steps']}")
    if assessment['strategy']['abstain_steps']:
        print(f"弃答消耗型({len(assessment['strategy']['abstain_steps'])}): {assessment['strategy']['abstain_steps']}")
    if assessment['strategy']['intercept_steps']:
        print(f"拦截({len(assessment['strategy']['intercept_steps'])}): {assessment['strategy']['intercept_steps']}")
    if assessment['strategy']['escalate_steps']:
        print(f"升级审批({len(assessment['strategy']['escalate_steps'])}): {assessment['strategy']['escalate_steps']}")

    print(f"\n评估报告: {assessment['output_file']}")
    print("=" * 60)
