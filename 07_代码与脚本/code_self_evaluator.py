# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0
================================================================
code_self_evaluator.py — 代码自评估器
================================================================
职责：
  - 执行算子后自动评估质量，6 个维度：
      1) 语法正确性      (ast.parse 能否通过)
      2) 功能测试通过率  (给定 test_cases 的 pass 比例)
      3) 边界条件覆盖    (空输入 / 极值 / 类型错误)
      4) 执行时间        (单次执行耗时 ms)
      5) 代码复杂度      (McCabe cyclomatic 近似：分支节点数)
      6) 文档完整性      (是否有 docstring + 类型注解)
  - 不达标自动修改：根据评估报告调用修复策略迭代（最多 3 轮）；
  - 评估报告：JSON 格式，含各维度得分 + 总分 + 改进建议。

接口：
  - evaluate(code, test_cases) -> EvalReport
  - suggest_fixes(report) -> list[str]
  - iterate(code, report) -> new_code

说明：不依赖外部 pip 包，复杂度指标为标准库 AST 实现的近似值。
"""

from __future__ import annotations

import ast
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.0-META-CLOSED-LOOP"

# 满分权重（总和 = 100）
WEIGHTS: Dict[str, int] = {
    "syntax": 15,
    "function": 35,
    "boundary": 15,
    "performance": 10,
    "complexity": 10,
    "documentation": 15,
}

# 及格线
PASS_THRESHOLD = 75.0
MAX_ITERATIONS = 3


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class TestCase:
    """单个测试用例。"""
    name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any] = field(default_factory=dict)
    expect_type: str = "any"        # any / list / dict / bool / tuple
    expect_min_len: Optional[int] = None

    def run(self, func: Callable[..., Any]) -> Tuple[bool, Any, str]:
        try:
            result = func(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001
            return False, None, f"exception: {exc}"

        # 类型检查
        if self.expect_type == "list" and not isinstance(result, list):
            return False, result, f"expected list, got {type(result).__name__}"
        if self.expect_type == "dict" and not isinstance(result, dict):
            return False, result, f"expected dict, got {type(result).__name__}"
        if self.expect_type == "bool" and not isinstance(result, bool):
            return False, result, f"expected bool, got {type(result).__name__}"
        if self.expect_type == "tuple" and not isinstance(result, tuple):
            return False, result, f"expected tuple, got {type(result).__name__}"
        if self.expect_min_len is not None:
            try:
                if len(result) < self.expect_min_len:
                    return False, result, f"len < {self.expect_min_len}"
            except TypeError:
                return False, result, "no len()"
        return True, result, "ok"


@dataclass
class DimensionScore:
    name: str
    raw: float          # 0~1
    weighted: float     # 0~WEIGHTS[name]
    detail: str = ""


@dataclass
class EvalReport:
    """评估报告。"""
    dimensions: List[DimensionScore] = field(default_factory=list)
    total_score: float = 0.0
    passed: bool = False
    suggestions: List[str] = field(default_factory=list)
    iteration: int = 0
    func_name: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "func_name": self.func_name,
            "iteration": self.iteration,
            "total_score": round(self.total_score, 2),
            "passed": self.passed,
            "dimensions": {
                d.name: {"raw": round(d.raw, 3),
                         "weighted": round(d.weighted, 2),
                         "detail": d.detail}
                for d in self.dimensions
            },
            "suggestions": self.suggestions,
            "elapsed_ms": round(self.elapsed_ms, 3),
        }


# ---------------------------------------------------------------------------
# 复杂度计算器（近似 McCabe）
# ---------------------------------------------------------------------------
class _ComplexityCounter(ast.NodeVisitor):
    """统计分支/循环节点数，近似圈复杂度。"""

    def __init__(self) -> None:
        self.branch_nodes = 0

    def visit_If(self, node: ast.If) -> None:
        self.branch_nodes += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.branch_nodes += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.branch_nodes += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.branch_nodes += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # and / or 各算一个分支
        self.branch_nodes += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.branch_nodes += 1
        self.generic_visit(node)


def cyclomatic_approx(tree: ast.AST) -> int:
    counter = _ComplexityCounter()
    counter.visit(tree)
    return 1 + counter.branch_nodes  # 基础复杂度 = 1


# ---------------------------------------------------------------------------
# 受限命名空间
# ---------------------------------------------------------------------------
def _safe_exec_namespace() -> Dict[str, Any]:
    return {
        "__builtins__": {
            "len": len, "range": range, "sum": sum, "abs": abs,
            "min": min, "max": max, "sorted": sorted, "list": list,
            "dict": dict, "tuple": tuple, "set": set, "str": str,
            "int": int, "float": float, "bool": bool, "enumerate": enumerate,
            "zip": zip, "isinstance": isinstance, "print": print,
            "ValueError": ValueError, "TypeError": TypeError,
            "Exception": Exception,
        }
    }


# ---------------------------------------------------------------------------
# 主评估器
# ---------------------------------------------------------------------------
class CodeSelfEvaluator:
    """代码自评估器：6 维评分 + 自动修复迭代。"""

    def __init__(
        self,
        pass_threshold: float = PASS_THRESHOLD,
        max_iterations: int = MAX_ITERATIONS,
    ) -> None:
        self.pass_threshold = pass_threshold
        self.max_iterations = max_iterations
        self.reports: List[EvalReport] = []

    # ------------------------------------------------------------------
    # 提取函数对象
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_func(code: str, func_name: str = "") -> Tuple[Optional[Callable[..., Any]], Optional[ast.AST], str]:
        ns = _safe_exec_namespace()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None, None, "syntax_error"
        try:
            exec(compile(tree, "<eval>", "exec"), ns)  # noqa: S102
        except Exception as exc:  # noqa: BLE001
            return None, tree, f"exec_error: {exc}"

        # 自动找第一个 def
        if not func_name:
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    break
        func = ns.get(func_name) if func_name else None
        return func, tree, func_name or ""

    # ------------------------------------------------------------------
    # 维度 1：语法正确性
    # ------------------------------------------------------------------
    @staticmethod
    def _score_syntax(code: str) -> Tuple[float, str]:
        try:
            ast.parse(code)
            return 1.0, "ast.parse 通过"
        except SyntaxError as exc:
            return 0.0, f"语法错误: {exc}"

    # ------------------------------------------------------------------
    # 维度 2：功能测试通过率
    # ------------------------------------------------------------------
    @staticmethod
    def _score_function(
        func: Optional[Callable[..., Any]],
        test_cases: List[TestCase],
    ) -> Tuple[float, str]:
        if func is None or not test_cases:
            return 0.0, "无函数或无测试用例"
        passed = 0
        details = []
        for tc in test_cases:
            ok, _, msg = tc.run(func)
            if ok:
                passed += 1
            else:
                details.append(f"{tc.name}: {msg}")
        ratio = passed / len(test_cases)
        return ratio, f"通过 {passed}/{len(test_cases)}; " + "; ".join(details[:3])

    # ------------------------------------------------------------------
    # 维度 3：边界条件覆盖
    # ------------------------------------------------------------------
    @staticmethod
    def _score_boundary(
        func: Optional[Callable[..., Any]],
        warmup_args: Optional[Tuple[Any, ...]] = None,
    ) -> Tuple[float, str]:
        if func is None:
            return 0.0, "无函数"
        # 以 warmup_args 的结构为模板，构造空/极值变体
        base_args = warmup_args or ([],)
        n_params = len(base_args)

        def _variant(idx: int, replacement: Any) -> Tuple[Any, ...]:
            args = list(base_args)
            if idx < len(args):
                args[idx] = replacement
            else:
                args.append(replacement)
            return tuple(args)

        boundary_cases: List[Tuple[str, Tuple[Any, ...]]] = [
            ("empty", _variant(0, [])),
            ("single", _variant(0, [42])),
            ("empty_dict", _variant(0, {})),
            ("none_first", _variant(0, None)),
        ]
        survived = 0
        failed = []
        for name, args in boundary_cases:
            try:
                func(*args)
                survived += 1
            except Exception:  # noqa: BLE001
                failed.append(name)
        ratio = survived / len(boundary_cases)
        return ratio, f"边界存活 {survived}/{len(boundary_cases)}; failed={failed}"

    # ------------------------------------------------------------------
    # 维度 4：执行时间
    # ------------------------------------------------------------------
    @staticmethod
    def _score_performance(
        func: Optional[Callable[..., Any]],
        sample_args: Optional[Tuple[Any, ...]] = None,
    ) -> Tuple[float, str, float]:
        if func is None:
            return 0.0, "无函数", 0.0
        sample_args = sample_args or ([1, 2, 3, 4, 5],)
        # 预热
        try:
            func(*sample_args)
        except Exception:  # noqa: BLE001
            return 0.0, "预热失败", 0.0
        # 计时
        n_runs = 100
        t0 = time.perf_counter()
        for _ in range(n_runs):
            func(*sample_args)
        elapsed_ms = (time.perf_counter() - t0) / n_runs * 1000
        # 评分：< 1ms = 1.0; < 5ms = 0.8; < 20ms = 0.6; else 0.4
        if elapsed_ms < 1.0:
            score = 1.0
        elif elapsed_ms < 5.0:
            score = 0.8
        elif elapsed_ms < 20.0:
            score = 0.6
        else:
            score = 0.4
        return score, f"平均 {elapsed_ms:.3f} ms/次", elapsed_ms

    # ------------------------------------------------------------------
    # 维度 5：代码复杂度
    # ------------------------------------------------------------------
    @staticmethod
    def _score_complexity(tree: Optional[ast.AST]) -> Tuple[float, str]:
        if tree is None:
            return 0.0, "无 AST"
        cc = cyclomatic_approx(tree)
        # CC <= 3 = 1.0; <= 6 = 0.8; <= 10 = 0.6; else 0.3
        if cc <= 3:
            score = 1.0
        elif cc <= 6:
            score = 0.8
        elif cc <= 10:
            score = 0.6
        else:
            score = 0.3
        return score, f"近似圈复杂度 CC={cc}"

    # ------------------------------------------------------------------
    # 维度 6：文档完整性
    # ------------------------------------------------------------------
    @staticmethod
    def _score_documentation(code: str, tree: Optional[ast.AST]) -> Tuple[float, str]:
        if tree is None:
            return 0.0, "无 AST"
        has_docstring = bool(ast.get_docstring(tree))
        # 检查函数内是否有 docstring
        func_has_doc = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
                func_has_doc = True
                break
        # 类型注解覆盖率
        typed_args = 0
        total_args = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    total_args += 1
                    if arg.annotation is not None:
                        typed_args += 1
                if node.returns is not None:
                    typed_args += 1
                    total_args += 1
        annot_ratio = (typed_args / total_args) if total_args else 0.0

        score = 0.0
        if has_docstring:
            score += 0.3
        if func_has_doc:
            score += 0.3
        score += 0.4 * annot_ratio
        detail = (f"module_doc={has_docstring}, func_doc={func_has_doc}, "
                  f"annot_ratio={annot_ratio:.2f}")
        return min(score, 1.0), detail

    # ------------------------------------------------------------------
    # 主评估入口
    # ------------------------------------------------------------------
    def evaluate(
        self,
        code: str,
        test_cases: Optional[List[TestCase]] = None,
        func_name: str = "",
    ) -> EvalReport:
        """对一段算子代码执行 6 维评估。"""
        report = EvalReport()

        # 1) 语法
        syn_score, syn_detail = self._score_syntax(code)
        report.dimensions.append(DimensionScore(
            "syntax", syn_score, syn_score * WEIGHTS["syntax"], syn_detail))

        # 语法错则后续维度直接 0
        func, tree, actual_name = self._extract_func(code, func_name)
        report.func_name = actual_name

        if func is None:
            # 语法/执行失败，其余维度记 0
            for dim, w in WEIGHTS.items():
                if dim == "syntax":
                    continue
                report.dimensions.append(DimensionScore(
                    dim, 0.0, 0.0, "前置失败"))
            report.total_score = syn_score * WEIGHTS["syntax"]
            report.passed = False
            report.suggestions = ["修复语法错误或执行时导入错误"]
            return report

        # 2) 功能
        fn_score, fn_detail = self._score_function(func, test_cases or [])
        report.dimensions.append(DimensionScore(
            "function", fn_score, fn_score * WEIGHTS["function"], fn_detail))

        # 从首个测试用例提取 warmup 参数，供边界/性能维度使用
        warmup_args: Tuple[Any, ...] = ()
        if test_cases:
            warmup_args = test_cases[0].args

        # 3) 边界
        bd_score, bd_detail = self._score_boundary(func, warmup_args=warmup_args)
        report.dimensions.append(DimensionScore(
            "boundary", bd_score, bd_score * WEIGHTS["boundary"], bd_detail))

        # 4) 性能
        perf_score, perf_detail, elapsed = self._score_performance(func, sample_args=warmup_args or None)
        report.dimensions.append(DimensionScore(
            "performance", perf_score, perf_score * WEIGHTS["performance"], perf_detail))
        report.elapsed_ms = elapsed

        # 5) 复杂度
        cx_score, cx_detail = self._score_complexity(tree)
        report.dimensions.append(DimensionScore(
            "complexity", cx_score, cx_score * WEIGHTS["complexity"], cx_detail))

        # 6) 文档
        doc_score, doc_detail = self._score_documentation(code, tree)
        report.dimensions.append(DimensionScore(
            "documentation", doc_score, doc_score * WEIGHTS["documentation"], doc_detail))

        # 汇总
        report.total_score = sum(d.weighted for d in report.dimensions)
        report.passed = report.total_score >= self.pass_threshold
        report.suggestions = self.suggest_fixes(report)

        self.reports.append(report)
        return report

    # ------------------------------------------------------------------
    # 改进建议
    # ------------------------------------------------------------------
    def suggest_fixes(self, report: EvalReport) -> List[str]:
        """根据各维度得分生成改进建议。"""
        suggestions: List[str] = []
        score_map = {d.name: d for d in report.dimensions}

        if score_map["syntax"].raw < 1.0:
            suggestions.append("修复语法错误：使用 ast.parse 通过后再继续。")
        if score_map["function"].raw < 0.9:
            suggestions.append("补充/修正功能测试用例，确保主路径输入输出符合规格。")
        if score_map["boundary"].raw < 0.9:
            suggestions.append("增加空输入、单元素、负值等边界分支的保护逻辑。")
        if score_map["performance"].raw < 0.8:
            suggestions.append("优化热路径：避免重复计算，考虑向量化或缓存。")
        if score_map["complexity"].raw < 0.8:
            suggestions.append("拆分高复杂度函数：将多分支逻辑抽成子函数。")
        if score_map["documentation"].raw < 0.7:
            suggestions.append("补充模块/函数 docstring，并为参数与返回值添加类型注解。")
        if not suggestions:
            suggestions.append("当前实现已达及格线，可注册为正式算子。")
        return suggestions

    # ------------------------------------------------------------------
    # 自动修复迭代（启发式）
    # ------------------------------------------------------------------
    def iterate(
        self,
        code: str,
        report: EvalReport,
        round_num: int = 1,
    ) -> str:
        """
        根据评估报告对代码做启发式修复。
        策略：
          - 若函数无 docstring：自动补一行 docstring；
          - 若参数无类型注解：补 `-> Any` 返回注解；
          - 若边界覆盖低：在函数开头插入空输入保护；
          - 不做语义级重写（那是 OperatorGenerator 的职责）。
        """
        new_code = code
        tree = None
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        needs_doc = not ast.get_docstring(tree)
        func_node: Optional[ast.FunctionDef] = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break

        # 修复 1：补模块 docstring
        if needs_doc:
            new_code = '"""自动生成算子模块。"""\n\n' + new_code

        # 修复 2：补函数 docstring
        if func_node and not ast.get_docstring(func_node):
            # 在函数体第一行插入 docstring
            lines = new_code.splitlines()
            # 找到 def 行
            for i, line in enumerate(lines):
                if line.startswith("def "):
                    # 找到下一行缩进
                    indent = "    "
                    lines.insert(i + 1, f'{indent}"""自动生成算子。"""\n')
                    break
            new_code = "\n".join(lines)

        # 修复 3：边界保护（空 list 输入）
        if report.dimensions and report.dimensions[2].raw < 0.9:
            # 在函数体开头插入 if not data: return []
            protect_lines = new_code.splitlines()
            inserted = False
            for i, line in enumerate(protect_lines):
                if line.startswith("def ") and "data" in line:
                    # 找下一行
                    for j in range(i + 1, min(i + 4, len(protect_lines))):
                        if protect_lines[j].strip():
                            indent = "    "
                            protect_lines.insert(j, f"{indent}if not data:\n{indent}    return []")
                            inserted = True
                            break
                    break
            if inserted:
                new_code = "\n".join(protect_lines)

        return new_code


# ======================================================================
# 演示
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] CodeSelfEvaluator 代码自评估\n")

    evaluator = CodeSelfEvaluator()

    # 被测代码：初始版本（故意缺 docstring、缺边界保护）
    initial_code = (
        "def op_anomaly_detect(data: list) -> list:\n"
        "    mean = sum(data) / len(data)\n"
        "    var = sum((x - mean) ** 2 for x in data) / len(data)\n"
        "    std = var ** 0.5\n"
        "    return [x for x in data if abs(x - mean) > 3 * std]\n"
    )

    test_cases = [
        TestCase(name="normal", args=([0]*19 + [100],), expect_type="list"),
        TestCase(name="all_same", args=([7, 7, 7, 7],), expect_type="list"),
    ]

    # 第 1 轮评估
    print("[Round 1] 初始代码评估")
    r1 = evaluator.evaluate(initial_code, test_cases, func_name="op_anomaly_detect")
    print(f"  总分: {r1.total_score:.2f}  passed={r1.passed}")
    for d in r1.dimensions:
        print(f"    - {d.name:14s} raw={d.raw:.2f}  {d.detail}")
    print(f"  建议: {r1.suggestions}")
    print()

    # 自动修复迭代
    current_code = initial_code
    for it in range(1, MAX_ITERATIONS + 1):
        if evaluator.evaluate(current_code, test_cases, func_name="op_anomaly_detect").passed:
            break
        print(f"[Round {it+1}] 自动修复迭代")
        current_code = evaluator.iterate(current_code, evaluator.reports[-1], round_num=it)
        r = evaluator.evaluate(current_code, test_cases, func_name="op_anomaly_detect")
        print(f"  总分: {r.total_score:.2f}  passed={r.passed}")
        if r.passed:
            print("  -> 迭代达标，停止修复。")
            break

    print("\n[FINAL] 最终代码:")
    print(current_code)
