# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0
================================================================
v3_meta_closed_loop.py — 主引擎：元闭环编排
================================================================
6 阶段元闭环：
  1. 问题感知   —— 接收新问题 / 漂移检测
  2. 算子匹配   —— 在现有注册表中查找，找不到则触发生成
  3. 代码生成/修改 —— 调用 OperatorGenerator
  4. 守护校验   —— 调用 MetaLoopGuardian（公理一致性）
  5. 执行+自评估 —— 调用 CodeSelfEvaluator，不达标则迭代修复
  6. 进化记忆   —— 成功变更沉淀为神经节点，写入 evolution_memory.jsonl

兼容现有 14 算子：可加载 operator_registry.json，现有算子直接执行。
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# 同目录导入
from operator_generator import (
    OperatorGenerator, OperatorArtifact, IOSpec,
)
from code_self_evaluator import (
    CodeSelfEvaluator, EvalReport, TestCase,
)
from meta_loop_guardian import (
    MetaLoopGuardian, ChangeRequest, GuardResult,
)

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.0-META-CLOSED-LOOP"

# 进化记忆文件
EVOLUTION_MEMORY_FILE = "evolution_memory.jsonl"

# 默认算子注册表路径（V2 内核既有）
DEFAULT_REGISTRY_PATH = Path(
    "/home/user/.doubao/agent_mode/workspace/.user_skills/"
    "zongyuan-autonomous-kernel/operator_registry.json"
)


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class MetaLoopResult:
    """一次元闭环执行的结果。"""
    problem: str
    stage: int = 0                     # 最终停在哪一阶段（1~6）
    status: str = "INIT"               # INIT | SUCCESS | REJECTED | FAILED
    matched_existing: bool = False     # 是否复用了既有算子
    op_id: str = ""
    op_name: str = ""
    eval_score: float = 0.0
    eval_passed: bool = False
    guardian_verdict: str = ""
    iterations: int = 0
    timestamp: float = field(default_factory=time.time)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 主引擎
# ---------------------------------------------------------------------------
class V3MetaClosedLoop:
    """ZONGYUAN-ROOT V3.0 元闭环主引擎。"""

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        registry_path: Optional[Path] = None,
    ) -> None:
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.evolution_memory_path = self.workspace / EVOLUTION_MEMORY_FILE

        # 三大子模块
        self.generator = OperatorGenerator(
            registry_path=self.registry_path,
            workspace_dir=self.workspace,
        )
        self.evaluator = CodeSelfEvaluator()
        self.guardian = MetaLoopGuardian(workspace_dir=self.workspace)

        # 既有算子索引（从 V2 注册表加载）
        self.existing_operators: Dict[str, Dict[str, Any]] = {}
        self._load_existing_registry()

        # 闭环历史
        self.loop_history: List[MetaLoopResult] = []

    # ------------------------------------------------------------------
    # 加载既有算子（V2 注册表）
    # ------------------------------------------------------------------
    def _load_existing_registry(self) -> None:
        """从 V2 注册表提取全部既有算子 id，用于算子匹配阶段。"""
        if not self.registry_path.exists():
            return
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        subsystems = data.get("subsystems", {})
        for sub_key, sub in subsystems.items():
            for op in sub.get("operators", []):
                oid = op.get("operator_id", "")
                if oid:
                    self.existing_operators[oid] = {
                        "subsystem": sub_key,
                        "name": op.get("name", ""),
                        "description": op.get("description", ""),
                        "input_spec": op.get("input_spec", ""),
                        "output_spec": op.get("output_spec", ""),
                    }

    # ------------------------------------------------------------------
    # 阶段 1：问题感知
    # ------------------------------------------------------------------
    def _stage_perceive(self, problem: str) -> Dict[str, Any]:
        """解析问题：提取关键词，判断是否需要新算子。"""
        return {
            "problem": problem,
            "keywords": [w for w in problem.replace("，", " ").replace("。", " ").split() if len(w) > 1],
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # 阶段 2：算子匹配
    # ------------------------------------------------------------------
    def _stage_match(self, problem: str) -> Optional[str]:
        """
        在既有算子注册表中模糊匹配。
        匹配策略：问题描述关键词与算子 description/name 做包含匹配。
        返回匹配到的 op_id，未匹配返回 None。
        """
        problem_lower = problem.lower()
        best_op_id: Optional[str] = None
        best_score = 0
        for oid, meta in self.existing_operators.items():
            haystack = (meta.get("name", "") + " " + meta.get("description", "")).lower()
            # 简单包含匹配
            score = 0
            for kw in ["检测", "校验", "优化", "异常", "自检", "漂移", "纠错", "演化"]:
                if kw in problem and kw in haystack:
                    score += 1
            if score > best_score:
                best_score = score
                best_op_id = oid
        return best_op_id if best_score >= 2 else None

    # ------------------------------------------------------------------
    # 阶段 3：代码生成 / 修改
    # ------------------------------------------------------------------
    def _stage_generate(self, problem: str) -> OperatorArtifact:
        return self.generator.generate(problem)

    # ------------------------------------------------------------------
    # 阶段 4：守护校验
    # ------------------------------------------------------------------
    def _stage_guard(
        self,
        artifact: OperatorArtifact,
    ) -> GuardResult:
        change = ChangeRequest(
            target_file=f"{artifact.op_id}.py",
            new_code=artifact.code,
            change_type="generate",
            source_problem=artifact.problem_desc,
            author="v3_meta_loop",
        )
        return self.guardian.check(change)

    # ------------------------------------------------------------------
    # 阶段 5：执行 + 自评估（含迭代修复）
    # ------------------------------------------------------------------
    def _stage_evaluate(
        self,
        artifact: OperatorArtifact,
    ) -> EvalReport:
        # 构造测试用例（基于模板内置样例）
        test_cases = self._build_test_cases(artifact)
        current_code = artifact.code
        last_report: Optional[EvalReport] = None

        for it in range(self.evaluator.max_iterations):
            # 模板生成的函数名格式为 op_<template_key>
            func_name = f"op_{artifact.template_used}"
            report = self.evaluator.evaluate(
                current_code, test_cases,
                func_name=func_name,
            )
            report.iteration = it + 1
            last_report = report
            if report.passed:
                break
            # 不达标则自动修复一轮
            current_code = self.evaluator.iterate(current_code, report, round_num=it + 1)

        # 把修复后的代码写回 artifact
        artifact.code = current_code
        return last_report  # type: ignore[return-value]

    @staticmethod
    def _build_test_cases(artifact: OperatorArtifact) -> List[TestCase]:
        """根据模板 key 构造测试用例。"""
        tkey = artifact.template_used
        if tkey == "anomaly_detect":
            return [
                TestCase(name="normal", args=([0]*19 + [100],), expect_type="list"),
                TestCase(name="all_same", args=([7, 7, 7, 7],), expect_type="list"),
            ]
        if tkey == "data_validate":
            return [
                TestCase(name="missing_field",
                         args=({"name": "zhangsan", "age": 30}, ["name", "age", "email"]),
                         expect_type="tuple"),
                TestCase(name="all_present",
                         args=({"name": "lisi", "age": 25, "email": "a@b.c"},
                               ["name", "age", "email"]),
                         expect_type="tuple"),
            ]
        if tkey == "optimize_suggest":
            return [
                TestCase(name="over_threshold",
                         args=({"latency_ms": 500, "cpu": 30},
                               {"latency_ms": 200, "cpu": 80}),
                         expect_type="list"),
                TestCase(name="all_ok",
                         args=({"latency_ms": 10, "cpu": 20},
                               {"latency_ms": 200, "cpu": 80}),
                         expect_type="list"),
            ]
        return []

    # ------------------------------------------------------------------
    # 阶段 6：进化记忆
    # ------------------------------------------------------------------
    def _stage_evolve_memory(
        self,
        result: MetaLoopResult,
        report: EvalReport,
        guard: GuardResult,
    ) -> None:
        """成功变更写入 evolution_memory.jsonl。"""
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
            "problem": result.problem,
            "op_id": result.op_id,
            "op_name": result.op_name,
            "eval_score": round(result.eval_score, 2),
            "eval_passed": result.eval_passed,
            "guard_verdict": guard.verdict,
            "guard_violated": guard.violated_axioms,
            "iterations": result.iterations,
            "provenance_anchor": PROVENANCE_ANCHOR,
            "did": DID,
            "kernel_version": KERNEL_VERSION,
        }
        with self.evolution_memory_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # 主入口：单次元闭环
    # ------------------------------------------------------------------
    def run(self, problem: str) -> MetaLoopResult:
        """执行一次完整 6 阶段元闭环。"""
        result = MetaLoopResult(problem=problem)
        print(f"\n{'='*60}")
        print(f"[META-LOOP] 接收问题: {problem}")
        print(f"{'='*60}")

        # ---- Stage 1: 问题感知 ----
        result.stage = 1
        percept = self._stage_perceive(problem)
        result.notes.append(f"stage1_perceive: keywords={percept['keywords']}")
        print(f"  [Stage 1] 问题感知完成，关键词: {percept['keywords']}")

        # ---- Stage 2: 算子匹配 ----
        result.stage = 2
        matched_op = self._stage_match(problem)
        if matched_op:
            result.matched_existing = True
            result.op_id = matched_op
            result.op_name = self.existing_operators[matched_op].get("name", matched_op)
            result.status = "SUCCESS"
            result.notes.append(f"stage2_match: 命中既有算子 {matched_op}，直接复用")
            print(f"  [Stage 2] 命中既有算子: {matched_op} ({result.op_name})")
            print(f"  [SHORT-CIRCUIT] 既有算子可直接执行，无需生成。")
            return result
        result.notes.append("stage2_match: 未命中既有算子，触发生成")
        print(f"  [Stage 2] 未命中既有算子，触发生成新算子...")

        # ---- Stage 3: 代码生成 ----
        result.stage = 3
        artifact = self._stage_generate(problem)
        result.op_id = artifact.op_id
        result.op_name = artifact.op_name
        result.notes.append(f"stage3_generate: template={artifact.template_used}")
        print(f"  [Stage 3] 生成算子: {artifact.op_id} (模板={artifact.template_used})")

        # ---- Stage 4: 守护校验 ----
        result.stage = 4
        guard = self._stage_guard(artifact)
        result.guardian_verdict = guard.verdict
        if not guard.allowed:
            result.status = "REJECTED"
            result.notes.append(f"stage4_guard: 拒绝 - {guard.violated_axioms}")
            print(f"  [Stage 4] 守护拒绝: {guard.violated_axioms}")
            print(f"           命中: {guard.dangerous_hits}")
            return result
        result.notes.append("stage4_guard: PROCEED")
        print(f"  [Stage 4] 守护通过: PROCEED")

        # ---- Stage 5: 执行 + 自评估 ----
        result.stage = 5
        # 先做沙箱验证
        sandbox_ok = self.generator.validate(artifact)
        if not sandbox_ok:
            result.status = "FAILED"
            result.notes.append("stage5: sandbox 验证失败")
            print(f"  [Stage 5] 沙箱验证失败")
            return result

        report = self._stage_evaluate(artifact)
        result.eval_score = report.total_score
        result.eval_passed = report.passed
        result.iterations = report.iteration
        result.notes.append(
            f"stage5_eval: score={report.total_score:.1f}, passed={report.passed}, "
            f"iter={report.iteration}"
        )
        print(f"  [Stage 5] 自评估: 总分={report.total_score:.1f}  passed={report.passed}  "
              f"迭代={report.iteration}")
        if not report.passed:
            result.status = "FAILED"
            print(f"           未达标，建议: {report.suggestions}")
            return result

        # 注册
        self.generator.register(artifact)
        result.notes.append("stage5: 算子已注册")

        # ---- Stage 6: 进化记忆 ----
        result.stage = 6
        self._stage_evolve_memory(result, report, guard)
        result.status = "SUCCESS"
        result.notes.append("stage6_evolve_memory: 已写入 evolution_memory.jsonl")
        print(f"  [Stage 6] 进化记忆已写入: {self.evolution_memory_path.name}")
        print(f"[DONE] 元闭环完成，算子 {artifact.op_id} 已固化。")

        self.loop_history.append(result)
        return result

    # ------------------------------------------------------------------
    # 连续进化模式
    # ------------------------------------------------------------------
    def run_evolution_batch(self, problems: List[str]) -> List[MetaLoopResult]:
        """连续处理多个问题，批量进化。"""
        results: List[MetaLoopResult] = []
        for p in problems:
            try:
                r = self.run(p)
            except Exception as exc:  # noqa: BLE001
                r = MetaLoopResult(problem=p, status="FAILED",
                                   notes=[f"exception: {exc}\n{traceback.format_exc()}"])
            results.append(r)
        return results

    # ------------------------------------------------------------------
    # 系统状态
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "provenance_anchor": PROVENANCE_ANCHOR,
            "did": DID,
            "kernel_version": KERNEL_VERSION,
            "existing_operator_count": len(self.existing_operators),
            "generated_operator_count": len(self.generator.generated_history),
            "guardian_alerts": len(self.guardian.alert_log),
            "loop_history_count": len(self.loop_history),
            "evolution_memory_file": str(self.evolution_memory_path),
            "axiom_integrity_ok": self.guardian.verify_axiom_integrity(),
        }


# ======================================================================
# 演示
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] V3MetaClosedLoop 元闭环主引擎演示\n")

    # 在演示目录下运行
    demo_workspace = Path(__file__).parent
    engine = V3MetaClosedLoop(workspace_dir=demo_workspace)

    # 启动自检
    status = engine.status()
    print("[BOOT] 内核状态:")
    print(f"  - 既有算子数: {status['existing_operator_count']}")
    print(f"  - 公理完整性: {'OK' if status['axiom_integrity_ok'] else 'FAIL'}")
    print(f"  - 守护告警: {status['guardian_alerts']}")

    # ---- 演示 1：触发一个全新算子生成（异常检测）----
    problems = [
        "需要一个 3σ 异常检测算子，识别数据序列中的离群点",
        "需要一个数据校验算子，检查记录字典必填字段",
    ]
    results = engine.run_evolution_batch(problems)

    # ---- 演示 2：守护拦截危险变更 ----
    print(f"\n{'='*60}")
    print("[DEMO] 守护层危险拦截演示")
    print(f"{'='*60}")
    evil_req = ChangeRequest(
        target_file="op_hack.py",
        new_code="import os\nos.system('rm -rf /')\n",
        change_type="generate",
        source_problem="测试危险拦截",
    )
    guard_res = engine.guardian.check(evil_req)
    print(f"  危险变更 verdict: {guard_res.verdict}")
    print(f"  违反公理: {guard_res.violated_axioms}")
    print(f"  命中: {guard_res.dangerous_hits}")

    # ---- 总结 ----
    print(f"\n{'='*60}")
    print("[SUMMARY] 元闭环执行汇总")
    print(f"{'='*60}")
    for r in results:
        print(f"  - [{r.status}] {r.problem[:40]}...")
        print(f"      op_id={r.op_id}, score={r.eval_score:.1f}, "
              f"guard={r.guardian_verdict}, iter={r.iterations}")

    print(f"\n[EVOLUTION MEMORY] 文件: {engine.evolution_memory_path}")
    if engine.evolution_memory_path.exists():
        lines = engine.evolution_memory_path.read_text(encoding="utf-8").strip().splitlines()
        print(f"  已记录 {len(lines)} 条进化记忆")
        for ln in lines[-2:]:
            print(f"    -> {ln[:120]}...")
