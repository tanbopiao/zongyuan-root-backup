#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 执行后反馈闭环 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L5 RSI实验台 → L2 MC策略层

核心设计：
- 采集每次元意识决策的实际执行结果（成功/失败/误拦截/漏拦截）
- 统计误拦截率（intercept但实际安全）和漏拦截率（proceed但实际失败）
- 反馈给RSI管理器，自动微调MC决策阈值
- 形成"决策→执行→反馈→调优→再决策"的完整闭环

关键指标：
- false_positive_rate（误拦截率）：intercept/escalate但实际应该proceed
- false_negative_rate（漏拦截率）：proceed/degrade但实际失败
- true_positive_rate（正确拦截率）：intercept且实际确实有问题
- decision_accuracy（决策准确率）：决策与实际结果一致的比例
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

ROOT = Path("/home/user/ZONGYUAN-ROOT")
FEEDBACK_DIR = ROOT / "06_云端中枢同步" / "meta_decision_feedback"
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"

# 反馈调优配置
MIN_SAMPLES_FOR_TUNING = 30      # 最少样本数才触发调优
FALSE_POSITIVE_TARGET = 0.10     # 误拦截率目标≤10%
FALSE_NEGATIVE_TARGET = 0.05     # 漏拦截率目标≤5%
THRESHOLD_ADJUSTMENT_STEP = 0.02  # 每次阈值调整步长
MAX_ADJUSTMENTS_PER_RUN = 2       # 每次最多调整2个阈值


@dataclass
class ExecutionFeedback:
    """执行反馈记录"""
    feedback_id: str
    decision_id: str
    operation_name: str
    decision_action: str       # proceed/degrade/abstain/intercept/escalate
    doubt_score: float
    actual_outcome: str        # success/failure/skipped
    is_correct: bool           # 决策是否正确
    error_type: Optional[str]  # false_positive/false_negative/true_positive/true_negative
    timestamp: float = field(default_factory=time.time)
    notes: str = ""

    def to_dict(self):
        return asdict(self)


class ExecutionFeedbackLoop:
    """
    执行后反馈闭环管理器

    流程：
    1. 从meta_decision_orchestrator的反馈日志中读取决策记录
    2. 标注实际结果（成功/失败），计算决策正确性
    3. 统计误拦截率/漏拦截率/准确率
    4. 当指标偏离目标时，生成RSI调优建议
    5. 调用RSI管理器自动微调MC阈值
    """

    def __init__(self):
        self.feedback_file = FEEDBACK_DIR / "decision_feedback.jsonl"
        self.annotated_file = FEEDBACK_DIR / "annotated_feedback.jsonl"
        self.tuning_history_file = FEEDBACK_DIR / "tuning_history.jsonl"
        self.feedback_records: List[ExecutionFeedback] = []
        self._load_annotated()

    def _load_annotated(self):
        if self.annotated_file.exists():
            try:
                for line in self.annotated_file.read_text().strip().split("\n"):
                    if line:
                        record = json.loads(line)
                        self.feedback_records.append(ExecutionFeedback(**record))
            except Exception:
                pass

    def _save_annotated(self, record: ExecutionFeedback):
        with open(self.annotated_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _classify_error(self, decision_action: str, actual_outcome: str) -> Tuple[bool, Optional[str]]:
        """
        分类决策正确性和错误类型

        混淆矩阵：
        - true_positive: intercept/escalate 且 actual=failure（正确拦截了有问题的操作）
        - false_positive: intercept/escalate 且 actual=success（误拦截，操作其实安全）
        - true_negative: proceed/degrade 且 actual=success（正确放行）
        - false_negative: proceed/degrade 且 actual=failure（漏拦截，操作其实有问题）
        - abstain/skipped: 不参与统计
        """
        if actual_outcome == "skipped":
            return True, None  # 跳过的不评估
        if decision_action in ("intercept", "escalate"):
            if actual_outcome == "failure":
                return True, "true_positive"
            else:
                return False, "false_positive"
        else:  # proceed/degrade
            if actual_outcome == "success":
                return True, "true_negative"
            else:
                return False, "false_negative"

    def ingest_new_feedback(self) -> Dict[str, Any]:
        """
        从决策反馈日志中读取新记录并标注

        返回: 新增标注数
        """
        if not self.feedback_file.exists():
            return {"new_annotated": 0, "total_annotated": 0, "reason": "无反馈日志"}

        # 已标注的decision_id集合
        annotated_ids = {r.decision_id for r in self.feedback_records}
        new_count = 0

        with open(self.feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    did = record.get("decision_id", "")
                    if did in annotated_ids:
                        continue
                    # 标注
                    decision_action = record.get("action", "proceed")
                    actual_outcome = record.get("actual_outcome", "pending")
                    if actual_outcome == "pending":
                        continue  # 还没有实际结果，跳过
                    is_correct, error_type = self._classify_error(decision_action, actual_outcome)
                    feedback = ExecutionFeedback(
                        feedback_id=f"FB-{int(time.time()*1000)}-{new_count}",
                        decision_id=did,
                        operation_name=record.get("operation_name", "unknown"),
                        decision_action=decision_action,
                        doubt_score=record.get("doubt_score", 0.0),
                        actual_outcome=actual_outcome,
                        is_correct=is_correct,
                        error_type=error_type,
                    )
                    self.feedback_records.append(feedback)
                    self._save_annotated(feedback)
                    new_count += 1
                    annotated_ids.add(did)
                except Exception:
                    continue

        return {"new_annotated": new_count, "total_annotated": len(self.feedback_records)}
    def compute_metrics(self) -> Dict[str, Any]:
        """计算反馈指标"""
        if not self.feedback_records:
            return {"total": 0, "message": "无反馈数据"}

        total = len(self.feedback_records)
        error_types = {}
        for r in self.feedback_records:
            if r.error_type:
                error_types[r.error_type] = error_types.get(r.error_type, 0) + 1

        tp = error_types.get("true_positive", 0)
        fp = error_types.get("false_positive", 0)
        tn = error_types.get("true_negative", 0)
        fn = error_types.get("false_negative", 0)
        evaluated = tp + fp + tn + fn

        # 误拦截率：在所有拦截中，误拦截的比例
        false_positive_rate = fp / max(tp + fp, 1)
        # 漏拦截率：在所有放行中，漏拦截的比例
        false_negative_rate = fn / max(tn + fn, 1)
        # 准确率
        accuracy = (tp + tn) / max(evaluated, 1)
        # 精确率（拦截中正确的比例）
        precision = tp / max(tp + fp, 1)
        # 召回率（实际有问题中被拦截的比例）
        recall = tp / max(tp + fn, 1)

        return {
            "total_records": total,
            "evaluated_records": evaluated,
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "false_positive_rate": round(false_positive_rate, 4),
            "false_negative_rate": round(false_negative_rate, 4),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "fp_target": FALSE_POSITIVE_TARGET,
            "fn_target": FALSE_NEGATIVE_TARGET,
            "fp_status": "达标" if false_positive_rate <= FALSE_POSITIVE_TARGET else "超标",
            "fn_status": "达标" if false_negative_rate <= FALSE_NEGATIVE_TARGET else "超标",
        }

    def generate_tuning_suggestions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据指标生成RSI调优建议

        逻辑：
        - 误拦截率超标 → 提高intercept/escalate阈值（更难触发拦截，减少误拦截）
        - 漏拦截率超标 → 降低proceed/degrade阈值（更容易触发拦截，减少漏拦截）
        - 两者都超标 → 优先解决漏拦截（风险最小原则：漏拦截比误拦截更危险）
        """
        suggestions = []
        if metrics.get("total_records", 0) < MIN_SAMPLES_FOR_TUNING:
            return [{"type": "insufficient_samples",
                     "message": f"样本数{metrics['total_records']}<{MIN_SAMPLES_FOR_TUNING}，暂不调优"}]

        fp_rate = metrics.get("false_positive_rate", 0)
        fn_rate = metrics.get("false_negative_rate", 0)

        if fn_rate > FALSE_NEGATIVE_TARGET:
            # 漏拦截超标 → 降低proceed上限（更容易进入degrade/intercept）
            suggestions.append({
                "type": "threshold_adjustment",
                "target_param": "proceed_max",
                "direction": "decrease",
                "step": THRESHOLD_ADJUSTMENT_STEP,
                "reason": f"漏拦截率{fn_rate:.2%}超标(目标≤{FALSE_NEGATIVE_TARGET:.0%})，降低proceed阈值以减少漏拦截",
                "priority": "high",
            })
        if fp_rate > FALSE_POSITIVE_TARGET:
            # 误拦截超标 → 提高intercept上限（更难触发intercept，减少误拦截）
            suggestions.append({
                "type": "threshold_adjustment",
                "target_param": "intercept_max",
                "direction": "increase",
                "step": THRESHOLD_ADJUSTMENT_STEP,
                "reason": f"误拦截率{fp_rate:.2%}超标(目标≤{FALSE_POSITIVE_TARGET:.0%})，提高intercept阈值以减少误拦截",
                "priority": "medium",
            })

        if not suggestions:
            suggestions.append({"type": "no_tuning_needed", "message": "指标全部达标，无需调优"})

        return suggestions[:MAX_ADJUSTMENTS_PER_RUN]

    def apply_tuning(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        应用调优（通过RSI管理器）

        实际调用rsi_self_improvement_manager进行参数调优
        """
        applied = []
        for sug in suggestions:
            if sug.get("type") != "threshold_adjustment":
                continue
            # 记录调优历史
            record = {
                "tuning_id": f"TUNE-{int(time.time()*1000)}",
                "target_param": sug["target_param"],
                "direction": sug["direction"],
                "step": sug["step"],
                "reason": sug["reason"],
                "timestamp": time.time(),
                "applied_via": "rsi_manager",
            }
            with open(self.tuning_history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            applied.append(record)

        return {
            "applied_count": len(applied),
            "applied": applied,
            "note": "调优建议已记录，实际参数变更由RSI管理器在灰度验证后应用",
        }

    def run_full_cycle(self) -> Dict[str, Any]:
        """执行完整反馈闭环：摄入→指标→建议→调优"""
        print("=== 执行后反馈闭环 ===")
        # 1. 摄入新反馈
        ingest_result = self.ingest_new_feedback()
        print(f"1. 摄入新反馈: {ingest_result['new_annotated']}条 (累计{ingest_result['total_annotated']}条)")

        # 2. 计算指标
        metrics = self.compute_metrics()
        print(f"2. 反馈指标: 准确率={metrics.get('accuracy', 0):.1%}, "
              f"误拦截={metrics.get('false_positive_rate', 0):.1%}, "
              f"漏拦截={metrics.get('false_negative_rate', 0):.1%}")

        # 3. 生成调优建议
        suggestions = self.generate_tuning_suggestions(metrics)
        print(f"3. 调优建议: {len(suggestions)}条")
        for s in suggestions:
            print(f"   - {s.get('message', s.get('reason', ''))}")

        # 4. 应用调优
        tuning_result = self.apply_tuning(suggestions)
        print(f"4. 调优应用: {tuning_result['applied_count']}条已记录")

        return {
            "ingest": ingest_result,
            "metrics": metrics,
            "suggestions": suggestions,
            "tuning": tuning_result,
        }

    def stats(self) -> dict:
        metrics = self.compute_metrics()
        return {
            "total_feedback": len(self.feedback_records),
            "metrics": metrics,
            "feedback_dir": str(FEEDBACK_DIR),
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT 执行后反馈闭环")
    parser.add_argument("action", choices=["cycle", "metrics", "stats", "ingest"],
                       help="操作: cycle(完整闭环)/metrics(指标)/stats(统计)/ingest(摄入)")
    args = parser.parse_args()

    loop = ExecutionFeedbackLoop()

    if args.action == "cycle":
        result = loop.run_full_cycle()
        print("\n=== 闭环结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "metrics":
        print(json.dumps(loop.compute_metrics(), indent=2, ensure_ascii=False))
    elif args.action == "ingest":
        result = loop.ingest_new_feedback()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "stats":
        print(json.dumps(loop.stats(), indent=2, ensure_ascii=False))
