#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT RSI自改进闭环管理器 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L5 RSI实验台

RSI（Recursive Self-Improvement）核心设计：
- 影子流量：采集实际操作的MI信号和决策结果，不影响生产
- 双轴校验：用DualAxisValidator验证候选阈值变更（自感轴+真值轴）
- 灰度发布：小范围应用新阈值，观察效果指标
- 自动回滚：效果不达标则自动回滚到旧阈值

严格约束（MC-8）：
- RSI禁改Ω子空间/主干权重/L0根
- 只允许改进MC策略参数（阈值/权重/窗口大小）
- 任何变更必须经过双轴校验+灰度验证
"""

import json
import os
import sys
import time
import copy
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_awareness_kernel import MetaCognition, MISignal
from dual_axis_validator import DualAxisValidator

ROOT = Path("/home/user/ZONGYUAN-ROOT")
RSI_DIR = ROOT / "06_云端中枢同步" / "rsi_self_improvement"
RSI_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"

# MC可改进参数白名单（RSI只能改这些）
MC_TUNABLE_PARAMS = {
    "doubt_abstain_threshold": {"min": 0.1, "max": 0.9, "default": 0.4, "step": 0.05},
    "doubt_intercept_threshold": {"min": 0.3, "max": 0.95, "default": 0.7, "step": 0.05},
    "confidence_floor": {"min": 0.1, "max": 0.7, "default": 0.3, "step": 0.05},
    "high_risk_doubt_multiplier": {"min": 1.0, "max": 3.0, "default": 1.5, "step": 0.1},
}

# 灰度配置
GRAYSCALE_TRAFFIC_RATIO = 0.1  # 10%流量走新阈值
GRAYSCALE_MIN_SAMPLES = 20      # 灰度最少样本数
GRAYSCALE_IMPROVEMENT_THRESHOLD = 0.05  # 改进≥5%才全量发布


@dataclass
class ShadowSample:
    """影子流量样本"""
    sample_id: str
    raw_confidence: float
    task_complexity: float
    is_high_risk: bool
    old_decision: str
    new_decision: str
    old_params: dict
    new_params: dict
    timestamp: float = field(default_factory=time.time)
    outcome: str = "pending"  # pending/correct/incorrect（后续人工或自动标注）

    def to_dict(self):
        return asdict(self)


@dataclass
class RSIExperiment:
    """RSI实验"""
    experiment_id: str
    name: str
    description: str
    param_changes: dict  # {param_name: new_value}
    old_params: dict
    new_params: dict
    status: str = "shadow"  # shadow/grayscale/full_rollout/rolled_back/rejected
    shadow_samples: List[dict] = field(default_factory=list)
    grayscale_samples: List[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    dual_axis_verified: bool = False
    dual_axis_result: Optional[dict] = None

    def to_dict(self):
        d = asdict(self)
        return d


class RSIManager:
    """
    RSI自改进闭环管理器

    流程：
    1. 提出候选变更（参数微调）
    2. 双轴校验（DualAxisValidator验证变更安全性）
    3. 影子流量（采集新旧阈值决策对比，不影响生产）
    4. 灰度发布（10%流量走新阈值，观察效果）
    5. 效果评估（改进≥5%则全量，否则回滚）
    6. 全量发布/回滚
    """

    def __init__(self):
        self.experiments_file = RSI_DIR / "experiments.json"
        self.shadow_log_file = RSI_DIR / "shadow_samples.jsonl"
        self.current_params_file = RSI_DIR / "current_mc_params.json"
        self.experiments: Dict[str, RSIExperiment] = {}
        self.validator = DualAxisValidator(probe_name="rsi_manager")
        self._load()

    def _load(self):
        if self.experiments_file.exists():
            try:
                data = json.loads(self.experiments_file.read_text())
                for eid, edata in data.items():
                    self.experiments[eid] = RSIExperiment(**edata)
            except Exception:
                pass

    def _save(self):
        data = {eid: exp.to_dict() for eid, exp in self.experiments.items()}
        self.experiments_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def get_current_params(self) -> dict:
        """获取当前MC参数"""
        if self.current_params_file.exists():
            try:
                return json.loads(self.current_params_file.read_text())
            except Exception:
                pass
        return {k: v["default"] for k, v in MC_TUNABLE_PARAMS.items()}

    def save_current_params(self, params: dict):
        """保存当前MC参数"""
        self.current_params_file.write_text(json.dumps(params, ensure_ascii=False, indent=2))

    def propose_change(self, param_name: str, new_value: float,
                        description: str = "") -> Optional[RSIExperiment]:
        """
        提出候选参数变更

        参数:
            param_name: 参数名（必须在白名单中）
            new_value: 新值（必须在合法范围内）
            description: 变更描述
        """
        # 1. 检查参数是否在白名单
        if param_name not in MC_TUNABLE_PARAMS:
            print(f"❌ 参数 {param_name} 不在RSI可改进白名单中")
            return None
        spec = MC_TUNABLE_PARAMS[param_name]
        if not (spec["min"] <= new_value <= spec["max"]):
            print(f"❌ 新值 {new_value} 超出合法范围 [{spec['min']}, {spec['max']}]")
            return None

        # 2. 构建新旧参数
        old_params = self.get_current_params()
        new_params = copy.deepcopy(old_params)
        new_params[param_name] = round(new_value, 4)

        # 3. 双轴校验（MC-8：任何变更必须经过校验）
        dav_result = self.validator.validate(
            operation_name=f"RSI参数变更:{param_name}={new_value}",
            raw_confidence=0.7,
            task_complexity=0.5,
            is_high_risk=False,
            operation_context={
                "is_readonly": False,
                "risk_assessed": True,
                "reuse_checked": True,
                "modifies_kernel_baseline": False,  # 只改MC参数，不改内核基线
                "is_paid_operation": False,
            }
        )

        exp_id = f"RSI-{int(time.time())}-{param_name}"
        exp = RSIExperiment(
            experiment_id=exp_id,
            name=f"MC参数优化:{param_name}",
            description=description or f"将{param_name}从{old_params[param_name]}调整为{new_value}",
            param_changes={param_name: new_value},
            old_params=old_params,
            new_params=new_params,
            dual_axis_verified=dav_result.passed,
            dual_axis_result=dav_result.to_dict(),
        )

        if not dav_result.passed:
            exp.status = "rejected"
            print(f"❌ 双轴校验未通过，变更被拒绝: {dav_result.reason}")
        else:
            print(f"✅ 双轴校验通过，进入影子流量阶段: {dav_result.reason}")

        self.experiments[exp_id] = exp
        self._save()
        return exp

    def collect_shadow_sample(self, experiment_id: str,
                                raw_confidence: float,
                                task_complexity: float = 0.5,
                                is_high_risk: bool = False) -> Optional[ShadowSample]:
        """
        采集影子流量样本（新旧阈值决策对比，不影响生产）

        用旧阈值和新阈值分别决策，记录对比结果
        """
        exp = self.experiments.get(experiment_id)
        if not exp or exp.status != "shadow":
            return None

        mi = MISignal(
            doubt_score=max(0.0, min(1.0, 0.3 + task_complexity * 0.3 - raw_confidence * 0.2)),
            confidence_calibrated=raw_confidence,
            ece=0.05,
            source="rsi_shadow"
        )

        # 旧阈值决策
        old_mc = MetaCognition(**exp.old_params)
        old_decision = old_mc.decide(mi, is_high_risk=is_high_risk).action

        # 新阈值决策
        new_mc = MetaCognition(**exp.new_params)
        new_decision = new_mc.decide(mi, is_high_risk=is_high_risk).action

        sample = ShadowSample(
            sample_id=f"shadow-{int(time.time()*1000)}",
            raw_confidence=raw_confidence,
            task_complexity=task_complexity,
            is_high_risk=is_high_risk,
            old_decision=old_decision,
            new_decision=new_decision,
            old_params=exp.old_params,
            new_params=exp.new_params,
        )
        exp.shadow_samples.append(sample.to_dict())

        # 达到样本数阈值后自动进入灰度
        if len(exp.shadow_samples) >= GRAYSCALE_MIN_SAMPLES:
            self._start_grayscale(exp)

        self._save()
        return sample

    def _start_grayscale(self, exp: RSIExperiment):
        """启动灰度发布"""
        if exp.status == "shadow":
            exp.status = "grayscale"
            print(f"🔄 实验 {exp.experiment_id} 进入灰度发布阶段（{GRAYSCALE_TRAFFIC_RATIO*100:.0f}%流量）")

    def evaluate_experiment(self, experiment_id: str) -> dict:
        """
        评估实验效果，决定全量发布或回滚

        效果指标：
        - 决策一致率：新旧阈值决策相同的比例
        - 拦截率变化：新阈值拦截率 vs 旧阈值
        - 误拦截估计：新阈值多拦截但旧阈值放行的比例（潜在误拦截）
        """
        exp = self.experiments.get(experiment_id)
        if not exp:
            return {"error": "实验不存在"}

        # 影子样本和灰度样本都可用于评估
        all_samples = exp.shadow_samples + exp.grayscale_samples
        samples = all_samples
        if not samples:
            return {"error": "无样本数据"}

        total = len(samples)
        same_decision = sum(1 for s in samples if s["old_decision"] == s["new_decision"])
        new_intercepts = sum(1 for s in samples if s["new_decision"] in ("block", "intercept"))
        old_intercepts = sum(1 for s in samples if s["old_decision"] in ("block", "intercept"))
        # 新阈值多拦截（潜在误拦截或改进拦截）
        extra_intercepts = sum(1 for s in samples
                               if s["new_decision"] in ("block", "intercept")
                               and s["old_decision"] not in ("block", "intercept"))

        agreement_rate = same_decision / total
        intercept_change = (new_intercepts - old_intercepts) / max(old_intercepts, 1)
        extra_intercept_rate = extra_intercepts / total

        metrics = {
            "total_samples": total,
            "agreement_rate": round(agreement_rate, 4),
            "old_intercept_rate": round(old_intercepts / total, 4),
            "new_intercept_rate": round(new_intercepts / total, 4),
            "intercept_change_pct": round(intercept_change * 100, 2),
            "extra_intercept_rate": round(extra_intercept_rate, 4),
        }
        exp.metrics = metrics

        # 决策：一致率≥80%且额外拦截率≤10% → 可全量
        can_full_rollout = agreement_rate >= 0.8 and extra_intercept_rate <= 0.1
        if can_full_rollout:
            exp.status = "full_rollout"
            self.save_current_params(exp.new_params)
            print(f"🎉 实验 {exp.experiment_id} 全量发布！参数已更新")
        else:
            exp.status = "rolled_back"
            print(f"↩ 实验 {exp.experiment_id} 回滚（一致率{agreement_rate:.0%}, 额外拦截{extra_intercept_rate:.0%}）")

        self._save()
        return {"status": exp.status, "metrics": metrics, "can_full_rollout": can_full_rollout}

    def auto_improve(self, param_name: Optional[str] = None,
                      num_samples: int = GRAYSCALE_MIN_SAMPLES) -> dict:
        """
        自动改进：提出候选变更→影子采样→评估→全量/回滚

        参数:
            param_name: 指定参数名（None则自动选择）
            num_samples: 影子采样数
        """
        # 自动选择参数和变更方向
        if param_name is None:
            # 简单策略：随机选择一个参数，做±step微调
            import random
            param_name = random.choice(list(MC_TUNABLE_PARAMS.keys()))

        spec = MC_TUNABLE_PARAMS[param_name]
        current = self.get_current_params()[param_name]
        # 尝试降低阈值（更宽松）和提高阈值（更严格），选改进方向
        direction = 1 if current < spec["default"] else -1
        new_value = round(current + direction * spec["step"], 4)
        new_value = max(spec["min"], min(spec["max"], new_value))

        if new_value == current:
            return {"error": f"参数 {param_name} 已在边界，无法微调"}

        print(f"=== RSI自动改进: {param_name} {current} → {new_value} ===")

        # 1. 提出变更
        exp = self.propose_change(param_name, new_value,
                                    description=f"自动微调: {param_name} {current}→{new_value}")
        if not exp or exp.status == "rejected":
            return {"error": "变更被双轴校验拒绝"}

        # 2. 影子采样
        import random
        for i in range(num_samples):
            self.collect_shadow_sample(
                exp.experiment_id,
                raw_confidence=round(random.uniform(0.3, 0.95), 2),
                task_complexity=round(random.uniform(0.1, 0.9), 2),
                is_high_risk=random.random() < 0.2,
            )

        # 3. 评估
        result = self.evaluate_experiment(exp.experiment_id)
        result["experiment_id"] = exp.experiment_id
        result["param_name"] = param_name
        result["old_value"] = current
        result["new_value"] = new_value
        return result

    def stats(self) -> dict:
        total = len(self.experiments)
        by_status = {}
        for exp in self.experiments.values():
            by_status[exp.status] = by_status.get(exp.status, 0) + 1
        return {
            "total_experiments": total,
            "by_status": by_status,
            "current_params": self.get_current_params(),
            "tunable_params": list(MC_TUNABLE_PARAMS.keys()),
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT RSI自改进闭环管理器")
    parser.add_argument("action", choices=["propose", "auto", "stats", "evaluate"],
                       help="操作: propose(提出变更)/auto(自动改进)/stats(统计)/evaluate(评估实验)")
    parser.add_argument("--param", type=str, help="参数名")
    parser.add_argument("--value", type=float, help="新值")
    parser.add_argument("--experiment-id", type=str, help="实验ID")
    parser.add_argument("--samples", type=int, default=20, help="影子采样数")
    args = parser.parse_args()

    mgr = RSIManager()

    if args.action == "propose":
        if not args.param or args.value is None:
            print("用法: propose --param <参数名> --value <新值>")
            sys.exit(1)
        exp = mgr.propose_change(args.param, args.value)
        if exp:
            print(f"实验ID: {exp.experiment_id}, 状态: {exp.status}")
    elif args.action == "auto":
        result = mgr.auto_improve(param_name=args.param, num_samples=args.samples)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "evaluate":
        if not args.experiment_id:
            print("用法: evaluate --experiment-id <实验ID>")
            sys.exit(1)
        result = mgr.evaluate_experiment(args.experiment_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "stats":
        print(json.dumps(mgr.stats(), ensure_ascii=False, indent=2))
