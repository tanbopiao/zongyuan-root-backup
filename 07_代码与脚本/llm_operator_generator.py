# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.1
================================================================
llm_operator_generator.py — LLM 驱动算子生成器
================================================================
职责：
  - 将 V3.0 模板填充升级为真实 LLM 代码生成；
  - 接入火斗AI（OpenAI兼容），默认 doubao-reasoning2 模型；
  - 迭代自纠正：生成 → 沙箱验证 → 失败则将错误反馈给LLM重写（最多3轮）；
  - 代码自评估：通过后调用 code_self_evaluator 6维评分；
  - 模板回退：LLM不可用时自动降级为V3.0模板填充；
  - 自动注册：验证通过后写入算子注册表。

接口：
  - generate(problem_desc, io_spec) -> OperatorArtifact
  - validate(artifact) -> bool
  - self_correct(artifact, error_msg) -> OperatorArtifact
  - register(artifact) -> op_id
  - auto_generate(problem_desc, io_spec) -> (artifact, score, grade)

确权锚点：Ω₀⊂⊙∞⊂Ω
DID：DID-BR-000002
内核版本：V3.1-LLM-OPERATOR-GEN
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.1-LLM-OPERATOR-GEN"

# 火斗AI API配置
HUODOU_API_BASE = "https://www.huodouai.com/v1"
HUODOU_API_KEY = "zy-101e3e6f7188482f87bca9e806ca7c5d775a6e44e4784772"
DEFAULT_LLM_MODEL = "doubao-reasoning2"
MAX_CORRECTION_ROUNDS = 3

# 默认算子注册表路径
DEFAULT_REGISTRY_PATH = Path(
    "/home/user/.doubao/agent_mode/workspace/.user_skills/"
    "zongyuan-autonomous-kernel/operator_registry.json"
)

# V3.0模板回退导入
try:
    from operator_generator_v3 import (
        IOSpec as V3IOSpec,
        OperatorArtifact as V3OperatorArtifact,
        OperatorGenerator as V3OperatorGenerator,
        OPERATOR_TEMPLATES,
        analyze_dependencies,
        _safe_exec_namespace,
    )
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class IOSpec:
    """算子输入输出规格。"""
    input_params: List[str] = field(default_factory=list)
    input_types: Dict[str, str] = field(default_factory=dict)
    output_type: str = "Any"
    description: str = ""


@dataclass
class LLMGenerationResult:
    """一次LLM生成的完整结果。"""
    artifact: Optional["OperatorArtifact"] = None
    llm_model: str = ""
    llm_raw_response: str = ""
    generation_round: int = 0
    validation_errors: List[str] = field(default_factory=list)
    self_eval_score: float = 0.0
    self_eval_grade: str = ""
    template_fallback_used: bool = False
    total_time_seconds: float = 0.0


@dataclass
class OperatorArtifact:
    """一次算子生成的产物。"""
    op_id: str
    op_name: str
    problem_desc: str
    io_spec: IOSpec
    code: str
    generation_method: str = "llm"  # llm | template_fallback
    llm_model: str = ""
    generation_round: int = 1
    dependencies: List[str] = field(default_factory=list)
    sandbox_ok: bool = False
    registered: bool = False
    self_eval_score: float = 0.0
    self_eval_grade: str = ""
    test_input: str = ""
    test_assert: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_id": self.op_id,
            "op_name": self.op_name,
            "problem_desc": self.problem_desc,
            "io_spec": {
                "input_params": self.io_spec.input_params,
                "input_types": self.io_spec.input_types,
                "output_type": self.io_spec.output_type,
                "description": self.io_spec.description,
            },
            "generation_method": self.generation_method,
            "llm_model": self.llm_model,
            "generation_round": self.generation_round,
            "dependencies": self.dependencies,
            "sandbox_ok": self.sandbox_ok,
            "registered": self.registered,
            "self_eval_score": self.self_eval_score,
            "self_eval_grade": self.self_eval_grade,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# LLM 系统提示词（算子生成专家）
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是 ZONGYUAN-ROOT 自治内核的算子代码生成专家。你的任务是根据自然语言问题描述，生成符合内核规范的 Python 算子函数。

## 算子规范

1. **函数命名**：函数名必须以 `op_` 开头，后跟描述性名称（如 op_anomaly_detect, op_data_validate）
2. **函数签名**：根据输入输出规格定义参数和返回类型注解
3. **文档字符串**：每个函数必须有完整的 docstring，包含：功能描述、参数说明（每个参数的类型和含义）、返回值说明
4. **代码质量**：
   - 纯函数设计，不依赖全局状态
   - 边界条件处理（空输入、None、类型错误）
   - 不使用危险操作：禁止 os.system, subprocess, eval, exec, 文件读写, 网络请求
   - 只使用 Python 标准库（math, json, re, collections, itertools, statistics, typing, dataclasses）
   - 代码简洁高效，有适当注释
5. **测试用例**：在代码末尾的注释中提供测试输入和断言：
   - `# TEST_INPUT: <函数调用参数表达式，如 [1,2,3], 2>`
   - `# TEST_ASSERT: <使用 result 变量的断言表达式，如 abs(result - 2.0) < 1e-9>`
   - **重要**：TEST_ASSERT 中必须使用 `result` 变量（即函数调用的返回值），不要直接调用函数名。

## 输出格式

只输出 Python 代码，用 ```python 代码块包裹。代码块中只包含函数定义，不要包含 if __name__ == "__main__" 块。

## 示例

问题：需要一个滑动窗口均值算子，计算数据序列中每个位置的窗口平均值
输入：data: list, window_size: int
输出：list

```python
def op_sliding_window_mean(data: list, window_size: int) -> list:
    \"\"\"滑动窗口均值算子：计算数据序列中每个位置的滑动窗口平均值。

    参数:
        data: 数值列表
        window_size: 窗口大小（正整数）

    返回:
        每个位置的窗口平均值列表，长度为 max(0, len(data) - window_size + 1)
    \"\"\"
    if not data or window_size <= 0:
        return []
    n = len(data)
    if window_size > n:
        return [sum(data) / n]
    result = []
    window_sum = sum(data[:window_size])
    result.append(window_sum / window_size)
    for i in range(window_size, n):
        window_sum += data[i] - data[i - window_size]
        result.append(window_sum / window_size)
    return result

# TEST_INPUT: [1, 2, 3, 4, 5], 3
# TEST_ASSERT: abs(result[0] - 2.0) < 1e-9 and abs(result[2] - 4.0) < 1e-9 and len(result) == 3
```
"""


# ---------------------------------------------------------------------------
# LLM 客户端封装
# ---------------------------------------------------------------------------
class LLMClient:
    """火斗AI OpenAI兼容客户端封装。"""

    def __init__(
        self,
        api_base: str = HUODOU_API_BASE,
        api_key: str = HUODOU_API_KEY,
        model: str = DEFAULT_LLM_MODEL,
        timeout: int = 60,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        """初始化OpenAI客户端。"""
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout,
            )
            # 简单连通性测试
            _ = self._client.models.list()
            self._available = True
        except Exception as exc:  # noqa: BLE001
            print(f"  [LLMClient] 初始化失败: {exc}")
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def chat(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """调用LLM聊天补全，返回原始文本。"""
        if not self._available:
            raise RuntimeError("LLM客户端不可用")
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"LLM调用失败: {exc}") from exc


# ---------------------------------------------------------------------------
# 代码提取与解析
# ---------------------------------------------------------------------------
def extract_python_code(raw_text: str) -> Tuple[str, str, str]:
    """
    从LLM原始响应中提取Python代码块。
    返回 (code, test_input, test_assert)。
    """
    # 提取 ```python 代码块
    code_match = re.search(
        r"```python\s*\n(.*?)```",
        raw_text,
        re.DOTALL,
    )
    if not code_match:
        # 尝试无语言标签的代码块
        code_match = re.search(r"```\s*\n(.*?)```", raw_text, re.DOTALL)
    if not code_match:
        return "", "", ""

    code = code_match.group(1).strip()

    # 提取测试用例注释
    test_input = ""
    test_assert = ""
    ti_match = re.search(r"#\s*TEST_INPUT:\s*(.+)", code)
    ta_match = re.search(r"#\s*TEST_ASSERT:\s*(.+)", code)
    if ti_match:
        test_input = ti_match.group(1).strip()
    if ta_match:
        test_assert = ta_match.group(1).strip()

    # 从代码中移除测试注释（保留函数定义）
    code = re.sub(r"#\s*TEST_INPUT:.*\n?", "", code)
    code = re.sub(r"#\s*TEST_ASSERT:.*\n?", "", code)
    code = code.strip()

    return code, test_input, test_assert


def extract_func_name(code: str) -> Optional[str]:
    """从代码中提取第一个 def 函数名。"""
    match = re.search(r"^def\s+(\w+)\s*\(", code, re.MULTILINE)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# 沙箱验证器（V3.1增强版）
# ---------------------------------------------------------------------------
class SandboxValidator:
    """算子沙箱验证器：语法检查 + 受限执行 + 测试用例验证。"""

    def __init__(self) -> None:
        self.last_error: str = ""

    def validate(
        self,
        code: str,
        func_name: Optional[str] = None,
        test_input: str = "",
        test_assert: str = "",
    ) -> Tuple[bool, str]:
        """
        验证算子代码。返回 (通过, 错误信息)。
        """
        self.last_error = ""

        # Step 1: 语法检查
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            self.last_error = f"语法错误: {exc}"
            return False, self.last_error

        # Step 2: 危险操作AST扫描
        danger_check = self._scan_dangerous_ops(tree)
        if danger_check:
            self.last_error = f"危险操作检测: {danger_check}"
            return False, self.last_error

        # Step 3: 提取函数名
        if not func_name:
            func_name = extract_func_name(code)
        if not func_name:
            self.last_error = "未找到函数定义"
            return False, self.last_error

        # Step 4: 受限执行
        ns = self._safe_namespace()
        try:
            exec(compile(tree, "<llm_generated>", "exec"), ns)  # noqa: S102
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"执行错误: {exc}\n{traceback.format_exc()}"
            return False, self.last_error

        func = ns.get(func_name)
        if not callable(func):
            self.last_error = f"函数 {func_name} 不可调用"
            return False, self.last_error

        # Step 5: 测试用例验证（如果提供了）
        if test_input and test_assert:
            try:
                result = eval(  # noqa: S307
                    f"func({test_input})",
                    {"func": func},
                    {"func": func},
                )
                # 断言命名空间同时传入result和函数本身（兼容LLM直接调用函数名的写法）
                assert_ns = {"result": result, "math": __import__("math")}
                if func_name:
                    assert_ns[func_name] = func
                passed = eval(test_assert, assert_ns)  # noqa: S307
                if not passed:
                    self.last_error = (
                        f"测试断言失败: {test_assert}\n"
                        f"  输入: {test_input}\n"
                        f"  实际结果: {result!r}"
                    )
                    return False, self.last_error
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"测试执行异常: {exc}\n{traceback.format_exc()}"
                return False, self.last_error

        return True, ""

    @staticmethod
    def _scan_dangerous_ops(tree: ast.AST) -> str:
        """AST扫描危险操作。"""
        danger_modules = {"os", "subprocess", "sys", "socket", "urllib", "requests", "http"}
        danger_funcs = {"eval", "exec", "compile", "__import__", "open", "input"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in danger_modules:
                        return f"禁止导入模块: {mod}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                if mod in danger_modules:
                    return f"禁止从模块导入: {mod}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in danger_funcs:
                        return f"禁止调用函数: {node.func.id}"
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in danger_funcs and node.func.attr != "compile":
                        return f"禁止调用方法: {node.func.attr}"
        return ""

    @staticmethod
    def _safe_namespace() -> Dict[str, Any]:
        safe_builtins: Dict[str, Any] = {
            "len": len, "range": range, "sum": sum, "abs": abs,
            "min": min, "max": max, "sorted": sorted, "list": list,
            "dict": dict, "tuple": tuple, "set": set, "str": str,
            "int": int, "float": float, "bool": bool, "enumerate": enumerate,
            "zip": zip, "isinstance": isinstance, "print": print,
            "round": round, "reversed": reversed, "any": any, "all": all,
            "__import__": __import__,  # 允许标准库import（已通过AST危险扫描过滤）
        }
        return {
            "__builtins__": safe_builtins,
            "math": __import__("math"),
            "json": __import__("json"),
            "re": __import__("re"),
            "collections": __import__("collections"),
            "itertools": __import__("itertools"),
            "statistics": __import__("statistics"),
        }


# ---------------------------------------------------------------------------
# 代码自评估器集成
# ---------------------------------------------------------------------------
class CodeSelfEvaluatorBridge:
    """桥接V3.0 code_self_evaluator，提供6维评分。"""

    def __init__(self) -> None:
        self._evaluator = None
        self._available = False
        self._try_load()

    def _try_load(self) -> None:
        try:
            # 动态导入V3.0代码自评估器
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "code_self_evaluator",
                str(Path(__file__).parent / "code_self_evaluator.py"),
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # 查找评估器类
                for attr in dir(mod):
                    if "eval" in attr.lower() and attr[0].isupper():
                        cls = getattr(mod, attr)
                        if isinstance(cls, type):
                            self._evaluator = cls()
                            self._available = True
                            break
        except Exception:  # noqa: BLE001
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def evaluate(self, code: str, problem_desc: str = "") -> Tuple[float, str]:
        """
        6维代码自评估。返回 (分数0-100, 等级)。
        如果评估器不可用，使用内置简化评分。
        """
        if self._available and self._evaluator:
            try:
                result = self._evaluator.evaluate(code, problem_desc)
                if isinstance(result, dict):
                    score = result.get("total_score", result.get("score", 0))
                    grade = result.get("grade", "")
                    return float(score), grade
                elif isinstance(result, tuple):
                    return float(result[0]), str(result[1]) if len(result) > 1 else ""
            except Exception:  # noqa: BLE001
                pass

        # 内置简化6维评分
        return self._simplified_evaluate(code, problem_desc)

    @staticmethod
    def _simplified_evaluate(code: str, problem_desc: str = "") -> Tuple[float, str]:
        """简化6维评分：正确性/可读性/完整性/效率/边界/规范。"""
        scores = {}

        # 正确性（语法通过基础分）
        try:
            ast.parse(code)
            scores["correctness"] = 85.0
        except SyntaxError:
            scores["correctness"] = 30.0

        # 可读性（行数适中+有docstring+有注释）
        lines = code.split("\n")
        scores["readability"] = 70.0
        if '"""' in code or "'''" in code:
            scores["readability"] += 10
        if any("#" in line and not line.strip().startswith("#") for line in lines):
            scores["readability"] += 5
        if 10 <= len(lines) <= 80:
            scores["readability"] += 5

        # 完整性（有参数注解+返回注解+docstring）
        scores["completeness"] = 60.0
        if "->" in code:
            scores["completeness"] += 15
        if re.search(r":\s*(list|dict|int|float|str|bool|tuple|Any)", code):
            scores["completeness"] += 15
        if '"""' in code:
            scores["completeness"] += 10

        # 效率（无明显O(n²)以上嵌套）
        scores["efficiency"] = 75.0
        for_count = code.count("for ")
        if for_count >= 3:
            scores["efficiency"] -= 10

        # 边界处理
        scores["boundary"] = 55.0
        if "if not" in code or "if len" in code or "is None" in code:
            scores["boundary"] += 25
        if "isinstance" in code:
            scores["boundary"] += 10
        if "try" in code and "except" in code:
            scores["boundary"] += 10

        # 规范（op_前缀+无危险操作）
        scores["convention"] = 70.0
        if "def op_" in code:
            scores["convention"] += 20
        if "import os" not in code and "subprocess" not in code:
            scores["convention"] += 10

        total = sum(scores.values()) / len(scores)
        total = min(100.0, max(0.0, total))

        if total >= 90:
            grade = "A+"
        elif total >= 85:
            grade = "A"
        elif total >= 80:
            grade = "A-"
        elif total >= 75:
            grade = "B+"
        elif total >= 70:
            grade = "B"
        else:
            grade = "C"

        return total, grade


# ---------------------------------------------------------------------------
# 主生成器：LLM驱动算子生成器
# ---------------------------------------------------------------------------
class LLMOperatorGenerator:
    """
    V3.1 LLM驱动算子生成器。
    生成策略：LLM代码生成 → 沙箱验证 → 迭代自纠正（最多3轮）→ 代码自评估 → 自动注册。
    LLM不可用时自动降级为V3.0模板填充。
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        workspace_dir: Optional[Path] = None,
        llm_model: str = DEFAULT_LLM_MODEL,
        max_correction_rounds: int = MAX_CORRECTION_ROUNDS,
    ) -> None:
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.generated_dir = self.workspace / "generated_operators_llm"
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        self.max_correction_rounds = max_correction_rounds

        # 初始化组件
        self.llm = LLMClient(model=llm_model)
        self.validator = SandboxValidator()
        self.evaluator = CodeSelfEvaluatorBridge()
        self.registry: Dict[str, Any] = self._load_registry()

        # V3.0模板回退生成器
        self._v3_generator: Optional[Any] = None
        if V3_AVAILABLE:
            try:
                self._v3_generator = V3OperatorGenerator(
                    workspace_dir=str(self.workspace),
                )
            except Exception:  # noqa: BLE001
                self._v3_generator = None

        # 生成历史
        self.generation_history: List[LLMGenerationResult] = []

    # ------------------------------------------------------------------
    # 注册表
    # ------------------------------------------------------------------
    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "registry_id": "OPR-ZR-001",
            "version": "OPERATOR-AUTH-V3.1-LLM",
            "did": DID,
            "provenance_anchor": PROVENANCE_ANCHOR,
            "subsystems": {
                "llm_generated": {
                    "name": "LLM自生成算子",
                    "skill": "v31_llm_operator_gen",
                    "operators": [],
                }
            },
        }

    def _save_registry(self) -> None:
        self.registry["last_updated"] = time.strftime(
            "%Y-%m-%dT%H:%M:%S+08:00", time.localtime()
        )
        out_path = self.generated_dir / "operator_registry_v31.json"
        out_path.write_text(
            json.dumps(self.registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # LLM提示词构建
    # ------------------------------------------------------------------
    @staticmethod
    def _build_generation_prompt(
        problem_desc: str,
        io_spec: IOSpec,
        existing_operators: List[str] = None,
    ) -> str:
        """构建首次生成的用户提示词。"""
        parts = [f"## 问题描述\n{problem_desc}\n"]

        if io_spec.input_params:
            params_str = ", ".join(
                f"{p}: {io_spec.input_types.get(p, 'Any')}"
                for p in io_spec.input_params
            )
            parts.append(f"## 输入参数\n{params_str}\n")
        parts.append(f"## 返回类型\n{io_spec.output_type}\n")

        if existing_operators:
            parts.append(
                "## 已有算子（避免重复）\n"
                + "\n".join(f"- {op}" for op in existing_operators[:10])
                + "\n"
            )

        parts.append("请生成符合规范的算子代码。")
        return "\n".join(parts)

    @staticmethod
    def _build_correction_prompt(
        problem_desc: str,
        io_spec: IOSpec,
        previous_code: str,
        error_msg: str,
        round_num: int,
    ) -> str:
        """构建自纠正提示词。"""
        return (
            f"## 问题描述\n{problem_desc}\n\n"
            f"## 之前生成的代码（第{round_num}轮验证失败）\n"
            f"```python\n{previous_code}\n```\n\n"
            f"## 验证错误信息\n```\n{error_msg}\n```\n\n"
            f"请修复上述错误，重新生成完整的算子代码。"
            f"确保：1) 语法正确 2) 无危险操作 3) 测试用例能通过 4) 边界条件处理完善。"
        )

    # ------------------------------------------------------------------
    # 生成
    # ------------------------------------------------------------------
    def generate(
        self,
        problem_desc: str,
        io_spec: Optional[IOSpec] = None,
    ) -> OperatorArtifact:
        """
        LLM生成算子。如果LLM不可用，自动降级为模板填充。
        """
        io_spec = io_spec or IOSpec(description=problem_desc)
        start_time = time.time()
        result = LLMGenerationResult()

        # 获取已有算子列表（用于避免重复）
        existing_ops = self._get_existing_operator_names()

        if self.llm.available:
            # LLM生成路径
            result.llm_model = self.llm.model
            code = ""
            test_input = ""
            test_assert = ""
            error_msg = ""

            for round_num in range(1, self.max_correction_rounds + 1):
                result.generation_round = round_num

                if round_num == 1:
                    prompt = self._build_generation_prompt(
                        problem_desc, io_spec, existing_ops
                    )
                else:
                    prompt = self._build_correction_prompt(
                        problem_desc, io_spec, code, error_msg, round_num
                    )

                try:
                    raw_response = self.llm.chat(prompt)
                    result.llm_raw_response = raw_response
                    code, test_input, test_assert = extract_python_code(raw_response)

                    if not code:
                        error_msg = "未能从LLM响应中提取Python代码"
                        result.validation_errors.append(error_msg)
                        continue

                    # 沙箱验证
                    func_name = extract_func_name(code)
                    ok, err = self.validator.validate(
                        code, func_name, test_input, test_assert
                    )

                    if ok:
                        # 验证通过，构建artifact
                        op_id = self._generate_op_id(problem_desc)
                        artifact = OperatorArtifact(
                            op_id=op_id,
                            op_name=func_name or "op_unknown",
                            problem_desc=problem_desc,
                            io_spec=io_spec,
                            code=code,
                            generation_method="llm",
                            llm_model=self.llm.model,
                            generation_round=round_num,
                            dependencies=analyze_dependencies(code) if V3_AVAILABLE else [],
                            sandbox_ok=True,
                            test_input=test_input,
                            test_assert=test_assert,
                        )
                        result.artifact = artifact
                        result.total_time_seconds = time.time() - start_time
                        self.generation_history.append(result)
                        return artifact
                    else:
                        error_msg = err
                        result.validation_errors.append(f"第{round_num}轮: {err}")

                except Exception as exc:  # noqa: BLE001
                    error_msg = f"LLM调用异常: {exc}"
                    result.validation_errors.append(error_msg)

            # 所有轮次都失败，尝试模板回退
            print(f"  [generate] LLM {self.max_correction_rounds}轮均失败，尝试模板回退")
            artifact = self._template_fallback(problem_desc, io_spec)
            if artifact:
                result.artifact = artifact
                result.template_fallback_used = True
                result.total_time_seconds = time.time() - start_time
                self.generation_history.append(result)
                return artifact

            # 完全失败，返回失败artifact
            op_id = self._generate_op_id(problem_desc)
            artifact = OperatorArtifact(
                op_id=op_id,
                op_name="op_failed",
                problem_desc=problem_desc,
                io_spec=io_spec,
                code="# GENERATION FAILED\n# " + "; ".join(result.validation_errors),
                generation_method="failed",
                sandbox_ok=False,
            )
            result.artifact = artifact
            result.total_time_seconds = time.time() - start_time
            self.generation_history.append(result)
            return artifact

        else:
            # LLM不可用，直接模板回退
            artifact = self._template_fallback(problem_desc, io_spec)
            if artifact:
                result.artifact = artifact
                result.template_fallback_used = True
                result.total_time_seconds = time.time() - start_time
                self.generation_history.append(result)
                return artifact

            op_id = self._generate_op_id(problem_desc)
            artifact = OperatorArtifact(
                op_id=op_id,
                op_name="op_fallback_unavailable",
                problem_desc=problem_desc,
                io_spec=io_spec,
                code="# FALLBACK UNAVAILABLE",
                generation_method="unavailable",
                sandbox_ok=False,
            )
            result.artifact = artifact
            result.total_time_seconds = time.time() - start_time
            self.generation_history.append(result)
            return artifact

    def _template_fallback(
        self, problem_desc: str, io_spec: IOSpec
    ) -> Optional[OperatorArtifact]:
        """V3.0模板填充回退。"""
        if not self._v3_generator or not V3_AVAILABLE:
            return None
        try:
            v3_spec = V3IOSpec(
                input_params=io_spec.input_params,
                input_types=io_spec.input_types,
                output_type=io_spec.output_type,
                description=io_spec.description,
            )
            v3_artifact, ok = self._v3_generator.auto_generate(problem_desc, v3_spec)
            if ok:
                return OperatorArtifact(
                    op_id=v3_artifact.op_id,
                    op_name=v3_artifact.op_name,
                    problem_desc=problem_desc,
                    io_spec=io_spec,
                    code=v3_artifact.code,
                    generation_method="template_fallback",
                    template_used=getattr(v3_artifact, "template_used", ""),
                    dependencies=v3_artifact.dependencies,
                    sandbox_ok=True,
                )
        except Exception:  # noqa: BLE001
            pass
        return None

    def _get_existing_operator_names(self) -> List[str]:
        """获取已有算子名称列表。"""
        names = []
        for subsystem in self.registry.get("subsystems", {}).values():
            for op in subsystem.get("operators", []):
                name = op.get("name", "")
                if name:
                    names.append(name)
        return names

    @staticmethod
    def _generate_op_id(problem_desc: str) -> str:
        return (
            f"OP-LLM-{time.strftime('%Y%m%d-%H%M%S')}-"
            f"{hashlib.sha1(problem_desc.encode()).hexdigest()[:6].upper()}"
        )

    # ------------------------------------------------------------------
    # 验证（委托给SandboxValidator）
    # ------------------------------------------------------------------
    def validate(self, artifact: OperatorArtifact) -> bool:
        if artifact.sandbox_ok:
            return True
        ok, _ = self.validator.validate(
            artifact.code,
            extract_func_name(artifact.code),
            artifact.test_input,
            artifact.test_assert,
        )
        artifact.sandbox_ok = ok
        return ok

    # ------------------------------------------------------------------
    # 代码自评估
    # ------------------------------------------------------------------
    def self_evaluate(self, artifact: OperatorArtifact) -> Tuple[float, str]:
        """对已验证的算子执行6维代码自评估。"""
        if not artifact.sandbox_ok:
            return 0.0, "UNVALIDATED"
        score, grade = self.evaluator.evaluate(artifact.code, artifact.problem_desc)
        artifact.self_eval_score = score
        artifact.self_eval_grade = grade
        return score, grade

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------
    def register(self, artifact: OperatorArtifact) -> str:
        """验证通过后写入算子注册表。"""
        if not artifact.sandbox_ok:
            raise RuntimeError(f"算子 {artifact.op_id} 未通过沙箱验证，禁止注册")

        subsystem = self.registry.setdefault("subsystems", {}).setdefault(
            "llm_generated",
            {"name": "LLM自生成算子", "skill": "v31_llm_operator_gen", "operators": []},
        )
        operators_list: List[Dict[str, Any]] = subsystem.setdefault("operators", [])

        entry = {
            "operator_id": artifact.op_id,
            "name": artifact.op_name,
            "min_authority": "L2",
            "description": artifact.problem_desc,
            "generation_method": artifact.generation_method,
            "llm_model": artifact.llm_model,
            "generation_round": artifact.generation_round,
            "self_eval_score": artifact.self_eval_score,
            "self_eval_grade": artifact.self_eval_grade,
            "input_spec": ", ".join(artifact.io_spec.input_params) or artifact.io_spec.description,
            "output_spec": artifact.io_spec.output_type,
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
        }
        operators_list.append(entry)

        # 写出生成算子源码
        src_file = self.generated_dir / f"{artifact.op_id}.py"
        header = (
            f"# {PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}\n"
            f"# LLM-GENERATED OPERATOR | model={artifact.llm_model} | "
            f"round={artifact.generation_round} | score={artifact.self_eval_score:.1f}/{artifact.self_eval_grade}\n\n"
        )
        src_file.write_text(header + artifact.code, encoding="utf-8")

        self._save_registry()
        artifact.registered = True
        return artifact.op_id

    # ------------------------------------------------------------------
    # 一键生成+验证+评估+注册
    # ------------------------------------------------------------------
    def auto_generate(
        self,
        problem_desc: str,
        io_spec: Optional[IOSpec] = None,
    ) -> Tuple[OperatorArtifact, float, str]:
        """
        完整流水线：LLM生成 → 沙箱验证 → 代码自评估 → 自动注册。
        返回 (artifact, score, grade)。
        """
        artifact = self.generate(problem_desc, io_spec)

        if not artifact.sandbox_ok:
            print(f"  [auto_generate] 算子生成失败: {artifact.op_id}")
            return artifact, 0.0, "FAILED"

        score, grade = self.self_evaluate(artifact)
        self.register(artifact)

        print(
            f"  [auto_generate] {artifact.op_name} | "
            f"method={artifact.generation_method} | "
            f"round={artifact.generation_round} | "
            f"score={score:.1f}/{grade}"
        )
        return artifact, score, grade


# ======================================================================
# 演示
# ======================================================================
def run_demo() -> None:
    """V3.1 LLM算子生成器演示。"""
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 70)
    print("[DEMO] V3.1 LLM驱动算子生成器\n")

    gen = LLMOperatorGenerator()

    print(f"[INFO] LLM可用: {gen.llm.available} (模型: {gen.llm.model})")
    print(f"[INFO] 代码自评估器可用: {gen.evaluator.available}")
    print(f"[INFO] V3.0模板回退可用: {gen._v3_generator is not None}")
    print()

    # 测试用例：5个不同类型的算子生成任务
    test_cases = [
        (
            "需要一个滑动窗口均值算子，计算数据序列中每个位置的滑动窗口平均值",
            IOSpec(
                input_params=["data", "window_size"],
                input_types={"data": "list", "window_size": "int"},
                output_type="list",
                description="滑动窗口均值",
            ),
        ),
        (
            "需要一个熵值计算算子，计算概率分布的信息熵（香农熵）",
            IOSpec(
                input_params=["probabilities"],
                input_types={"probabilities": "list"},
                output_type="float",
                description="香农熵计算",
            ),
        ),
        (
            "需要一个余弦相似度算子，计算两个向量的余弦相似度",
            IOSpec(
                input_params=["vec_a", "vec_b"],
                input_types={"vec_a": "list", "vec_b": "list"},
                output_type="float",
                description="余弦相似度",
            ),
        ),
        (
            "需要一个Z-Score标准化算子，将数据序列标准化为均值0标准差1",
            IOSpec(
                input_params=["data"],
                input_types={"data": "list"},
                output_type="list",
                description="Z-Score标准化",
            ),
        ),
        (
            "需要一个Top-K选择算子，从数据中选出最大的K个元素",
            IOSpec(
                input_params=["data", "k"],
                input_types={"data": "list", "k": "int"},
                output_type="list",
                description="Top-K选择",
            ),
        ),
    ]

    results = []
    for i, (desc, spec) in enumerate(test_cases, 1):
        print(f"[TEST {i}/{len(test_cases)}] {desc}")
        print("-" * 50)
        artifact, score, grade = gen.auto_generate(desc, spec)
        results.append((artifact, score, grade))
        if artifact.sandbox_ok:
            print(f"  函数: {artifact.op_name}")
            print(f"  方法: {artifact.generation_method} (round={artifact.generation_round})")
            print(f"  评分: {score:.1f}/{grade}")
            print(f"  代码行数: {len(artifact.code.split(chr(10)))}")
            # 显示代码前5行
            code_lines = artifact.code.split("\n")
            print(f"  代码预览:")
            for line in code_lines[:5]:
                print(f"    {line}")
            if len(code_lines) > 5:
                print(f"    ... ({len(code_lines) - 5} more lines)")
        else:
            print(f"  状态: 生成失败")
        print()

    # 汇总
    print("=" * 70)
    print("[SUMMARY] V3.1 LLM算子生成器演示汇总")
    print("-" * 50)
    success_count = sum(1 for _, _, g in results if g != "FAILED")
    llm_count = sum(1 for a, _, _ in results if a.generation_method == "llm")
    fallback_count = sum(1 for a, _, _ in results if a.generation_method == "template_fallback")
    avg_score = sum(s for _, s, g in results if g != "FAILED") / max(1, success_count)

    print(f"  总测试数: {len(results)}")
    print(f"  成功: {success_count} | LLM生成: {llm_count} | 模板回退: {fallback_count}")
    print(f"  平均评分: {avg_score:.1f}")
    print(f"  生成目录: {gen.generated_dir}")
    print(f"  注册表: {gen.generated_dir / 'operator_registry_v31.json'}")
    print()
    print(f"{PROVENANCE_ANCHOR} · V3.1 LLM算子生成器演示完成")


if __name__ == "__main__":
    run_demo()
