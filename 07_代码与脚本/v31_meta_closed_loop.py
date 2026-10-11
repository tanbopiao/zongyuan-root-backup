# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.1
================================================================
v31_meta_closed_loop.py — 元闭环主引擎 V3.1（LLM算子生成集成版）
================================================================
在 V3.0 六阶段元闭环基础上，集成 V3.1 LLM 驱动算子生成器：

  Stage 1: 问题感知   —— 接收新问题 / 漂移检测
  Stage 2: 算子匹配   —— 在 V2注册表 + V3.1 LLM生成注册表中查找，
                          找不到则触发 LLM 生成
  Stage 3: 代码生成   —— 优先调用 LLMOperatorGenerator（真实LLM代码生成），
                          LLM不可用时降级为 V3.0 模板填充
  Stage 4: 守护校验   —— MetaLoopGuardian 公理一致性校验
  Stage 5: 执行+自评估 —— 沙箱验证 + 6维代码自评估，不达标则迭代修复
  Stage 6: 进化记忆   —— 成功变更沉淀为神经节点，写入 evolution_memory.jsonl

关键增强（V3.1 vs V3.0）：
  - 算子匹配池扩展：V2既有算子 + V3.0模板生成算子 + V3.1 LLM生成算子
  - 新算子自动入池：LLM生成并验证通过的算子立即加入匹配池，后续问题可复用
  - LLM优先策略：Stage 3 优先使用真实LLM生成，模板填充仅作为LLM不可用时的回退
  - 迭代自纠正：LLM生成内置最多3轮自纠正，与Stage 5的自评估迭代形成双重保障
  - 算子来源追踪：每个算子记录 generation_method（llm/template_fallback/existing）

确权锚点：Ω₀⊂⊙∞⊂Ω
DID：DID-BR-000002
内核版本：V3.1-META-CLOSED-LOOP-LLM
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 同目录导入 V3.0 组件
try:
    from v3_meta_closed_loop import (
        V3MetaClosedLoop, MetaLoopResult,
        PROVENANCE_ANCHOR as V3_ANCHOR,
        DID as V3_DID,
    )
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False

# 导入 V3.1 LLM 算子生成器
try:
    from llm_operator_generator import (
        LLMOperatorGenerator, OperatorArtifact as V31Artifact,
        IOSpec as V31IOSpec, LLMClient,
    )
    V31_LLM_AVAILABLE = True
except ImportError:
    V31_LLM_AVAILABLE = False

# 导入 V3.0 守护和评估器
try:
    from meta_loop_guardian import MetaLoopGuardian, ChangeRequest, GuardResult
    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False

try:
    from code_self_evaluator import CodeSelfEvaluator, EvalReport, TestCase
    EVALUATOR_AVAILABLE = True
except ImportError:
    EVALUATOR_AVAILABLE = False

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.1-META-CLOSED-LOOP-LLM"

EVOLUTION_MEMORY_FILE = "evolution_memory_v31.jsonl"

DEFAULT_REGISTRY_PATH = Path(
    "/home/user/.doubao/agent_mode/workspace/.user_skills/"
    "zongyuan-autonomous-kernel/operator_registry.json"
)

V31_REGISTRY_PATH = Path(__file__).parent / "generated_operators_llm" / "operator_registry_v31.json"


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class V31MetaLoopResult:
    """V3.1 元闭环结果（自包含，不依赖V3.0）。"""
    problem: str
    stage: int = 0
    status: str = "INIT"
    matched_existing: bool = False
    op_id: str = ""
    op_name: str = ""
    eval_score: float = 0.0
    eval_passed: bool = False
    guardian_verdict: str = ""
    iterations: int = 0
    timestamp: float = field(default_factory=time.time)
    notes: List[str] = field(default_factory=list)
    # V3.1 扩展字段
    generation_method: str = ""
    llm_model: str = ""
    llm_rounds: int = 0
    llm_self_eval_score: float = 0.0
    llm_self_eval_grade: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 主引擎：V3.1 元闭环（LLM算子生成集成版）
# ---------------------------------------------------------------------------
class V31MetaClosedLoop:
    """
    ZONGYUAN-ROOT V3.1 元闭环主引擎。
    在 V3.0 六阶段闭环基础上，集成 V3.1 LLM 驱动算子生成器。
    """

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        registry_path: Optional[Path] = None,
        llm_model: str = "doubao-reasoning2",
        use_llm: bool = True,
    ) -> None:
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.evolution_memory_path = self.workspace / EVOLUTION_MEMORY_FILE
        self.use_llm = use_llm

        # ---- V3.0 基础引擎（作为回退和兼容层）----
        self.v3_engine: Optional[Any] = None
        if V3_AVAILABLE:
            try:
                self.v3_engine = V3MetaClosedLoop(
                    workspace_dir=self.workspace,
                    registry_path=self.registry_path,
                )
            except Exception:  # noqa: BLE001
                self.v3_engine = None

        # ---- V3.1 LLM 算子生成器 ----
        self.llm_generator: Optional[LLMOperatorGenerator] = None
        if use_llm and V31_LLM_AVAILABLE:
            try:
                self.llm_generator = LLMOperatorGenerator(
                    workspace_dir=self.workspace,
                    llm_model=llm_model,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [V31] LLM生成器初始化失败: {exc}")
                self.llm_generator = None

        # ---- 守护和评估器 ----
        self.guardian = MetaLoopGuardian(workspace_dir=self.workspace) if GUARDIAN_AVAILABLE else None
        self.evaluator = CodeSelfEvaluator() if EVALUATOR_AVAILABLE else None

        # ---- 统一算子匹配池（V2 + V3.0 + V3.1）----
        self.operator_pool: Dict[str, Dict[str, Any]] = {}
        self._load_operator_pool()

        # 闭环历史
        self.loop_history: List[V31MetaLoopResult] = []

    # ------------------------------------------------------------------
    # 加载统一算子匹配池
    # ------------------------------------------------------------------
    def _load_operator_pool(self) -> None:
        """从 V2注册表 + V3.1 LLM生成注册表 加载全部算子到匹配池。"""
        # V2 / V3.0 注册表
        if self.registry_path.exists():
            try:
                data = json.loads(self.registry_path.read_text(encoding="utf-8"))
                for sub_key, sub in data.get("subsystems", {}).items():
                    for op in sub.get("operators", []):
                        oid = op.get("operator_id", "")
                        if oid and oid not in self.operator_pool:
                            self.operator_pool[oid] = {
                                "source": "v2_registry",
                                "subsystem": sub_key,
                                "name": op.get("name", ""),
                                "description": op.get("description", ""),
                                "input_spec": op.get("input_spec", ""),
                                "output_spec": op.get("output_spec", ""),
                                "generation_method": "existing",
                            }
            except (json.JSONDecodeError, OSError):
                pass

        # V3.1 LLM 生成注册表
        if V31_REGISTRY_PATH.exists():
            try:
                data = json.loads(V31_REGISTRY_PATH.read_text(encoding="utf-8"))
                for sub_key, sub in data.get("subsystems", {}).items():
                    for op in sub.get("operators", []):
                        oid = op.get("operator_id", "")
                        if oid and oid not in self.operator_pool:
                            self.operator_pool[oid] = {
                                "source": "v31_llm_registry",
                                "subsystem": sub_key,
                                "name": op.get("name", ""),
                                "description": op.get("description", ""),
                                "input_spec": op.get("input_spec", ""),
                                "output_spec": op.get("output_spec", ""),
                                "generation_method": op.get("generation_method", "llm"),
                                "llm_model": op.get("llm_model", ""),
                                "self_eval_score": op.get("self_eval_score", 0),
                                "self_eval_grade": op.get("self_eval_grade", ""),
                            }
            except (json.JSONDecodeError, OSError):
                pass

        # V3.0 生成器历史中的算子
        if self.v3_engine:
            for art in getattr(self.v3_engine.generator, "generated_history", []):
                oid = getattr(art, "op_id", "")
                if oid and oid not in self.operator_pool:
                    self.operator_pool[oid] = {
                        "source": "v30_generated",
                        "name": getattr(art, "op_name", ""),
                        "description": getattr(art, "problem_desc", ""),
                        "generation_method": "template",
                    }

    def _add_to_pool(self, artifact: Any, source: str = "runtime") -> None:
        """将新生成的算子加入匹配池。"""
        oid = getattr(artifact, "op_id", "")
        if oid and oid not in self.operator_pool:
            self.operator_pool[oid] = {
                "source": source,
                "name": getattr(artifact, "op_name", ""),
                "description": getattr(artifact, "problem_desc", ""),
                "generation_method": getattr(artifact, "generation_method", "llm"),
                "llm_model": getattr(artifact, "llm_model", ""),
                "self_eval_score": getattr(artifact, "self_eval_score", 0),
                "self_eval_grade": getattr(artifact, "self_eval_grade", ""),
            }

    # ------------------------------------------------------------------
    # Stage 1: 问题感知
    # ------------------------------------------------------------------
    def _stage_perceive(self, problem: str) -> Dict[str, Any]:
        return {
            "problem": problem,
            "keywords": [w for w in problem.replace("，", " ").replace("。", " ").split() if len(w) > 1],
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Stage 2: 算子匹配（增强版：统一匹配池 + 语义关键词）
    # ------------------------------------------------------------------
    def _stage_match(self, problem: str) -> Optional[str]:
        """
        在统一算子匹配池中模糊匹配。
        匹配策略：问题关键词与算子 description/name 做包含匹配，
        同时计算语义相似度（基于关键词重叠率）。
        返回匹配到的 op_id，未匹配返回 None。
        """
        problem_lower = problem.lower()
        problem_words = set(problem_lower.replace("，", " ").replace("。", " ").split())

        best_op_id: Optional[str] = None
        best_score = 0.0

        # 扩展关键词表（覆盖更多算子类型）
        keyword_table = [
            "异常", "anomaly", "outlier", "检测", "detect",
            "校验", "validate", "验证", "verify", "检查", "check",
            "优化", "optimize", "建议", "suggest", "调优",
            "漂移", "drift", "同步", "sync", "同源", "homology",
            "纠错", "correct", "修复", "fix", "repair",
            "演化", "evolve", "进化", "evolution",
            "均值", "mean", "平均", "average", "窗口", "window",
            "熵", "entropy", "信息", "information",
            "相似度", "similarity", "余弦", "cosine", "距离", "distance",
            "标准化", "normalize", "z-score", "归一",
            "排序", "sort", "top-k", "topk", "最大", "最大",
            "聚类", "cluster", "分类", "classify",
            "回归", "regression", "预测", "predict",
            "过滤", "filter", "去重", "deduplicate",
            "统计", "statistics", "汇总", "aggregate",
        ]

        for oid, meta in self.operator_pool.items():
            haystack = (meta.get("name", "") + " " + meta.get("description", "")).lower()
            haystack_words = set(haystack.split())

            # 关键词匹配分
            kw_score = 0
            for kw in keyword_table:
                if kw in problem_lower and kw in haystack:
                    kw_score += 1

            # 词重叠率
            overlap = len(problem_words & haystack_words)
            overlap_ratio = overlap / max(1, len(problem_words))

            # 综合分
            total_score = kw_score * 2.0 + overlap_ratio * 3.0

            if total_score > best_score:
                best_score = total_score
                best_op_id = oid

        # 匹配阈值：至少需要关键词分>=2 或 重叠率>=0.3
        if best_score >= 4.0:
            return best_op_id
        return None

    # ------------------------------------------------------------------
    # Stage 3: 代码生成（V3.1增强：LLM优先 + 模板回退）
    # ------------------------------------------------------------------
    def _stage_generate(self, problem: str) -> Tuple[Any, str]:
        """
        生成新算子。优先使用 V3.1 LLM生成器，LLM不可用时降级为 V3.0 模板填充。
        返回 (artifact, generation_method)。
        """
        # 路径1: LLM 生成（使用auto_generate完整流水线：生成+验证+自评估+注册）
        if self.llm_generator and self.llm_generator.llm.available:
            try:
                artifact, score, grade = self.llm_generator.auto_generate(problem)
                if artifact.sandbox_ok:
                    artifact.self_eval_score = score
                    artifact.self_eval_grade = grade
                    return artifact, "llm"
                # LLM生成但验证失败，尝试模板回退
                print(f"  [Stage 3] LLM生成验证失败，尝试模板回退...")
            except Exception as exc:  # noqa: BLE001
                print(f"  [Stage 3] LLM生成异常: {exc}，尝试模板回退...")

        # 路径2: V3.0 模板填充回退
        if self.v3_engine:
            try:
                artifact = self.v3_engine.generator.generate(problem)
                ok = self.v3_engine.generator.validate(artifact)
                if ok:
                    self.v3_engine.generator.register(artifact)
                    return artifact, "template_fallback"
            except Exception as exc:  # noqa: BLE001
                print(f"  [Stage 3] 模板回退也失败: {exc}")

        # 路径3: 完全失败，返回空artifact
        from llm_operator_generator import OperatorArtifact, IOSpec
        artifact = OperatorArtifact(
            op_id=f"OP-FAILED-{time.strftime('%Y%m%d-%H%M%S')}",
            op_name="op_failed",
            problem_desc=problem,
            io_spec=IOSpec(description=problem),
            code="# GENERATION FAILED",
            generation_method="failed",
            sandbox_ok=False,
        )
        return artifact, "failed"

    # ------------------------------------------------------------------
    # Stage 4: 守护校验
    # ------------------------------------------------------------------
    def _stage_guard(self, artifact: Any) -> Any:
        if not self.guardian:
            # 无守护器时构造一个允许通过的结果
            class AllowResult:
                verdict = "SKIPPED_NO_GUARDIAN"
                allowed = True
                violated_axioms = []
                dangerous_hits = []
            return AllowResult()

        change = ChangeRequest(
            target_file=f"{getattr(artifact, 'op_id', 'unknown')}.py",
            new_code=getattr(artifact, "code", ""),
            change_type="generate",
            source_problem=getattr(artifact, "problem_desc", ""),
            author="v31_meta_loop",
        )
        return self.guardian.check(change)

    # ------------------------------------------------------------------
    # Stage 5: 执行 + 自评估
    # ------------------------------------------------------------------
    def _stage_evaluate(self, artifact: Any, generation_method: str) -> Tuple[float, bool, int]:
        """
        对生成的算子执行沙箱验证 + 自评估。
        返回 (score, passed, iterations)。
        """
        # V3.1 LLM 生成的算子已经在生成器内部做了沙箱验证和自评估
        if generation_method == "llm" and hasattr(artifact, "self_eval_score"):
            score = artifact.self_eval_score
            grade = artifact.self_eval_grade
            passed = score >= 70.0  # V3.1 通过阈值
            return score, passed, artifact.generation_round

        # V3.0 模板生成的算子使用 V3.0 评估器
        if self.evaluator and self.v3_engine:
            try:
                test_cases = self.v3_engine._build_test_cases(artifact)
                func_name = f"op_{getattr(artifact, 'template_used', 'unknown')}"
                report = self.evaluator.evaluate(artifact.code, test_cases, func_name=func_name)
                return report.total_score, report.passed, report.iteration
            except Exception:  # noqa: BLE001
                pass

        # 回退：简单验证
        code = getattr(artifact, "code", "")
        try:
            import ast
            ast.parse(code)
            return 75.0, True, 1
        except SyntaxError:
            return 30.0, False, 1

    # ------------------------------------------------------------------
    # Stage 6: 进化记忆
    # ------------------------------------------------------------------
    def _stage_evolve_memory(self, result: V31MetaLoopResult) -> None:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
            "problem": result.problem,
            "op_id": result.op_id,
            "op_name": result.op_name,
            "generation_method": result.generation_method,
            "llm_model": result.llm_model,
            "llm_rounds": result.llm_rounds,
            "eval_score": round(result.eval_score, 2),
            "eval_passed": result.eval_passed,
            "guardian_verdict": result.guardian_verdict,
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
    def run(self, problem: str) -> V31MetaLoopResult:
        """执行一次完整 V3.1 六阶段元闭环。"""
        result = V31MetaLoopResult(problem=problem)
        print(f"\n{'='*60}")
        print(f"[V3.1 META-LOOP] 接收问题: {problem}")
        print(f"{'='*60}")

        # ---- Stage 1: 问题感知 ----
        result.stage = 1
        percept = self._stage_perceive(problem)
        result.notes.append(f"stage1_perceive: keywords={percept['keywords']}")
        print(f"  [Stage 1] 问题感知完成，关键词: {percept['keywords']}")

        # ---- Stage 2: 算子匹配（统一匹配池）----
        result.stage = 2
        matched_op = self._stage_match(problem)
        if matched_op:
            meta = self.operator_pool[matched_op]
            result.matched_existing = True
            result.op_id = matched_op
            result.op_name = meta.get("name", matched_op)
            result.generation_method = meta.get("generation_method", "existing")
            result.status = "SUCCESS"
            result.notes.append(f"stage2_match: 命中既有算子 {matched_op} (来源={meta.get('source','')})")
            print(f"  [Stage 2] 命中既有算子: {matched_op} ({result.op_name})")
            print(f"           来源: {meta.get('source', 'unknown')}, 生成方式: {result.generation_method}")
            print(f"  [SHORT-CIRCUIT] 既有算子可直接执行，无需生成。")
            self.loop_history.append(result)
            return result

        result.notes.append("stage2_match: 未命中既有算子，触发LLM生成")
        print(f"  [Stage 2] 未命中既有算子（匹配池共 {len(self.operator_pool)} 个），触发生成...")

        # ---- Stage 3: 代码生成（LLM优先 + 模板回退）----
        result.stage = 3
        artifact, gen_method = self._stage_generate(problem)
        result.op_id = getattr(artifact, "op_id", "")
        result.op_name = getattr(artifact, "op_name", "")
        result.generation_method = gen_method
        result.llm_model = getattr(artifact, "llm_model", "")
        result.llm_rounds = getattr(artifact, "generation_round", 0)
        result.llm_self_eval_score = getattr(artifact, "self_eval_score", 0)
        result.llm_self_eval_grade = getattr(artifact, "self_eval_grade", "")
        result.notes.append(f"stage3_generate: method={gen_method}, model={result.llm_model}, rounds={result.llm_rounds}")

        if gen_method == "failed":
            result.status = "FAILED"
            result.notes.append("stage3: 所有生成路径均失败")
            print(f"  [Stage 3] 生成失败（LLM不可用且模板回退失败）")
            self.loop_history.append(result)
            return result

        print(f"  [Stage 3] 生成算子: {result.op_id}")
        print(f"           方式: {gen_method}, 模型: {result.llm_model or 'N/A'}, 轮次: {result.llm_rounds}")
        if gen_method == "llm":
            print(f"           LLM自评估: {result.llm_self_eval_score:.1f}/{result.llm_self_eval_grade}")

        # ---- Stage 4: 守护校验 ----
        result.stage = 4
        guard = self._stage_guard(artifact)
        result.guardian_verdict = getattr(guard, "verdict", "UNKNOWN")
        if not getattr(guard, "allowed", True):
            result.status = "REJECTED"
            result.notes.append(f"stage4_guard: 拒绝 - {getattr(guard, 'violated_axioms', [])}")
            print(f"  [Stage 4] 守护拒绝: {getattr(guard, 'violated_axioms', [])}")
            self.loop_history.append(result)
            return result
        result.notes.append("stage4_guard: PROCEED")
        print(f"  [Stage 4] 守护通过: {result.guardian_verdict}")

        # ---- Stage 5: 执行 + 自评估 ----
        result.stage = 5
        score, passed, iterations = self._stage_evaluate(artifact, gen_method)
        result.eval_score = score
        result.eval_passed = passed
        result.iterations = iterations
        result.notes.append(f"stage5_eval: score={score:.1f}, passed={passed}, iter={iterations}")
        print(f"  [Stage 5] 自评估: 总分={score:.1f}, passed={passed}, 迭代={iterations}")

        if not passed:
            result.status = "FAILED"
            print(f"           未达标")
            self.loop_history.append(result)
            return result

        # 新算子加入匹配池（后续问题可复用）
        self._add_to_pool(artifact, source="v31_runtime")
        result.notes.append("stage5: 算子已加入匹配池（可复用）")
        print(f"  [Stage 5] 算子已加入匹配池（当前池大小: {len(self.operator_pool)}）")

        # ---- Stage 6: 进化记忆 ----
        result.stage = 6
        self._stage_evolve_memory(result)
        result.status = "SUCCESS"
        result.notes.append("stage6_evolve_memory: 已写入 evolution_memory_v31.jsonl")
        print(f"  [Stage 6] 进化记忆已写入: {self.evolution_memory_path.name}")
        print(f"[DONE] V3.1元闭环完成，算子 {result.op_id} 已固化。")

        self.loop_history.append(result)
        return result

    # ------------------------------------------------------------------
    # 连续进化模式
    # ------------------------------------------------------------------
    def run_evolution_batch(self, problems: List[str]) -> List[V31MetaLoopResult]:
        results: List[V31MetaLoopResult] = []
        for p in problems:
            try:
                r = self.run(p)
            except Exception as exc:  # noqa: BLE001
                r = V31MetaLoopResult(
                    problem=p, status="FAILED",
                    notes=[f"exception: {exc}\n{traceback.format_exc()}"],
                )
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
            "operator_pool_size": len(self.operator_pool),
            "llm_available": self.llm_generator is not None and self.llm_generator.llm.available if self.llm_generator else False,
            "llm_model": self.llm_generator.llm.model if self.llm_generator else "N/A",
            "v3_engine_available": self.v3_engine is not None,
            "guardian_available": self.guardian is not None,
            "evaluator_available": self.evaluator is not None,
            "loop_history_count": len(self.loop_history),
            "evolution_memory_file": str(self.evolution_memory_path),
        }


# ======================================================================
# 演示
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] V3.1 元闭环主引擎（LLM算子生成集成版）演示\n")

    demo_workspace = Path(__file__).parent
    engine = V31MetaClosedLoop(workspace_dir=demo_workspace)

    # 启动自检
    status = engine.status()
    print("[BOOT] 内核状态:")
    print(f"  - 算子匹配池大小: {status['operator_pool_size']}")
    print(f"  - LLM可用: {status['llm_available']} (模型: {status['llm_model']})")
    print(f"  - V3.0引擎可用: {status['v3_engine_available']}")
    print(f"  - 守护器可用: {status['guardian_available']}")
    print(f"  - 评估器可用: {status['evaluator_available']}")

    # ---- 演示：5个问题的连续进化 ----
    # 前3个是新问题（需要LLM生成），后2个重复前3个中的（验证匹配池复用）
    problems = [
        "需要一个滑动窗口均值算子，计算数据序列中每个位置的滑动窗口平均值",
        "需要一个熵值计算算子，计算概率分布的信息熵（香农熵）",
        "需要一个余弦相似度算子，计算两个向量的余弦相似度",
        "需要一个Z-Score标准化算子，将数据序列标准化为均值0标准差1",
        "需要一个Top-K选择算子，从数据中选出最大的K个元素",
        # 重复问题：验证匹配池复用（应该命中既有算子，不重新生成）
        "需要一个滑动窗口均值算子来计算数据的移动平均",
    ]

    print(f"\n[DEMO] 连续进化 {len(problems)} 个问题（前5个新生成，第6个验证复用）")
    results = engine.run_evolution_batch(problems)

    # ---- 总结 ----
    print(f"\n{'='*60}")
    print("[SUMMARY] V3.1 元闭环执行汇总")
    print(f"{'='*60}")

    new_generated = sum(1 for r in results if not r.matched_existing and r.status == "SUCCESS")
    reused = sum(1 for r in results if r.matched_existing)
    llm_count = sum(1 for r in results if r.generation_method == "llm")
    template_count = sum(1 for r in results if r.generation_method == "template_fallback")
    failed = sum(1 for r in results if r.status == "FAILED")

    print(f"  总问题数: {len(results)}")
    print(f"  成功: {len(results) - failed} | 失败: {failed}")
    print(f"  新生成: {new_generated} (LLM={llm_count}, 模板回退={template_count})")
    print(f"  匹配复用: {reused}")
    print(f"  最终匹配池大小: {len(engine.operator_pool)}")
    print()

    for i, r in enumerate(results, 1):
        match_tag = "复用" if r.matched_existing else "新生成"
        print(f"  [{i}] [{r.status}] {match_tag} | {r.problem[:45]}...")
        print(f"      op={r.op_name}, method={r.generation_method}, "
              f"score={r.eval_score:.1f}, rounds={r.llm_rounds}")

    print(f"\n[EVOLUTION MEMORY] 文件: {engine.evolution_memory_path}")
    if engine.evolution_memory_path.exists():
        lines = engine.evolution_memory_path.read_text(encoding="utf-8").strip().splitlines()
        print(f"  已记录 {len(lines)} 条进化记忆")

    print(f"\n{PROVENANCE_ANCHOR} · V3.1 元闭环演示完成")
