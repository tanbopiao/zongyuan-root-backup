# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0
================================================================
operator_generator.py — 算子生成器
================================================================
职责：
  - 根据自然语言问题描述 + 输入输出规格，自动生成新算子 Python 代码；
  - 生成策略：模板填充（基于现有 14 算子模式）+ 代码骨架 + 依赖分析；
  - 沙箱验证：在受限 exec 命名空间中执行语法检查 + 基本功能测试；
  - 自动注册：验证通过后写入算子注册表（JSON），分配 op_id。

接口：
  - generate(problem_desc, io_spec) -> OperatorArtifact
  - validate(artifact) -> bool
  - register(artifact) -> op_id

内置 3 个算子生成模板示例：
  - op.anomaly_detect   （3σ 异常检测）
  - op.data_validate    （数据校验）
  - op.optimize_suggest （优化建议生成）
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.0-META-CLOSED-LOOP"

# 默认算子注册表路径（V2 内核既有文件）
DEFAULT_REGISTRY_PATH = Path(
    "/home/user/.doubao/agent_mode/workspace/.user_skills/"
    "zongyuan-autonomous-kernel/operator_registry.json"
)


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class IOSpec:
    """算子输入输出规格。"""
    input_params: List[str] = field(default_factory=list)   # 形参名列表
    input_types: Dict[str, str] = field(default_factory=dict)  # 形参 -> 类型描述
    output_type: str = "Any"
    description: str = ""


@dataclass
class OperatorArtifact:
    """一次算子生成的产物。"""
    op_id: str                       # 形如 OP-GEN-20260913-XXXX
    op_name: str                     # 如 anomaly_detect
    problem_desc: str
    io_spec: IOSpec
    code: str                        # 完整 Python 源码
    template_used: str               # 使用的模板 key
    dependencies: List[str] = field(default_factory=list)
    sandbox_ok: bool = False
    registered: bool = False
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
            "template_used": self.template_used,
            "dependencies": self.dependencies,
            "sandbox_ok": self.sandbox_ok,
            "registered": self.registered,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# 算子模板库
# ---------------------------------------------------------------------------
# 每个模板：{key -> (op_name, docstring, body_template, test_hint)}
# body_template 使用 {inputs} 占位符注入形参。
OPERATOR_TEMPLATES: Dict[str, Dict[str, str]] = {
    "anomaly_detect": {
        "op_name": "op.anomaly_detect",
        "docstring": (
            "异常检测算子：基于 3σ 法则识别数据序列中的异常点。\n"
            "        参数:\n"
            "            data: 数值列表\n"
            "        返回:\n"
            "            anomalies: 异常点列表\n"
        ),
        "body": (
            "def {func_name}(data: list) -> list:\n"
            "    \"\"\"{doc}\"\"\"\n"
            "    if not data:\n"
            "        return []\n"
            "    mean = sum(data) / len(data)\n"
            "    var = sum((x - mean) ** 2 for x in data) / len(data)\n"
            "    std = var ** 0.5\n"
            "    threshold = 3 * std\n"
            "    return [x for x in data if abs(x - mean) > threshold]\n"
        ),
        "test_input": "[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,100]",
        "test_assert": "len(result) == 1 and result[0] == 100",
    },
    "data_validate": {
        "op_name": "op.data_validate",
        "docstring": (
            "数据校验算子：校验记录字典是否包含必填字段且值非空。\n"
            "        参数:\n"
            "            record: 待校验字典\n"
            "            required_fields: 必填字段名列表\n"
            "        返回:\n"
            "            (ok, missing_fields) 元组\n"
        ),
        "body": (
            "def {func_name}(record: dict, required_fields: list) -> tuple:\n"
            "    \"\"\"{doc}\"\"\"\n"
            "    if not isinstance(record, dict):\n"
            "        return False, ['__not_a_dict__']\n"
            "    missing = [f for f in required_fields if f not in record or record[f] in (None, '')]\n"
            "    return (len(missing) == 0), missing\n"
        ),
        "test_input": "{'name': 'zhangsan', 'age': 30}, ['name', 'age', 'email']",
        "test_assert": "result[0] is False and 'email' in result[1]",
    },
    "optimize_suggest": {
        "op_name": "op.optimize_suggest",
        "docstring": (
            "优化建议算子：根据指标字典生成优化方向建议。\n"
            "        参数:\n"
            "            metrics: 指标名 -> 数值\n"
            "            thresholds: 指标名 -> 警戒线\n"
            "        返回:\n"
            "            suggestions: 建议列表\n"
        ),
        "body": (
            "def {func_name}(metrics: dict, thresholds: dict) -> list:\n"
            "    \"\"\"{doc}\"\"\"\n"
            "    suggestions = []\n"
            "    for key, value in metrics.items():\n"
            "        limit = thresholds.get(key)\n"
            "        if limit is not None and value > limit:\n"
            "            suggestions.append(f'{{key}}={{value}} 超过警戒线 {{limit}}，建议优化')\n"
            "    return suggestions\n"
        ),
        "test_input": "{'latency_ms': 500, 'cpu': 30}, {'latency_ms': 200, 'cpu': 80}",
        "test_assert": "len(result) == 1 and 'latency_ms' in result[0]",
    },
}


# ---------------------------------------------------------------------------
# 依赖分析
# ---------------------------------------------------------------------------
def analyze_dependencies(code: str) -> List[str]:
    """静态扫描代码中的 import，返回顶层模块名列表。"""
    deps: List[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return deps
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.append(node.module.split(".")[0])
    # 去重保序
    seen = set()
    out = []
    for d in deps:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


# ---------------------------------------------------------------------------
# 沙箱执行器（受限命名空间）
# ---------------------------------------------------------------------------
def _safe_exec_namespace() -> Dict[str, Any]:
    """构建受限 exec 命名空间：只暴露安全内置。"""
    safe_builtins: Dict[str, Any] = {
        "len": len, "range": range, "sum": sum, "abs": abs,
        "min": min, "max": max, "sorted": sorted, "list": list,
        "dict": dict, "tuple": tuple, "set": set, "str": str,
        "int": int, "float": float, "bool": bool, "enumerate": enumerate,
        "zip": zip, "isinstance": isinstance, "print": print,
    }
    return {"__builtins__": safe_builtins}


# ---------------------------------------------------------------------------
# 主生成器
# ---------------------------------------------------------------------------
class OperatorGenerator:
    """算子生成器：模板填充 + 沙箱验证 + 自动注册。"""

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.generated_dir = self.workspace / "generated_operators"
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        # 加载既有算子注册表
        self.registry: Dict[str, Any] = self._load_registry()

        # 生成历史
        self.generated_history: List[OperatorArtifact] = []

    # ------------------------------------------------------------------
    # 注册表加载 / 保存
    # ------------------------------------------------------------------
    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        # 注册表不存在则返回最小骨架
        return {
            "registry_id": "OPR-ZR-001",
            "version": "OPERATOR-AUTH-V3.0-GEN",
            "did": DID,
            "provenance_anchor": PROVENANCE_ANCHOR,
            "subsystems": {
                "meta_closed_loop": {
                    "name": "元闭环自生成算子",
                    "skill": "v3_meta_loop",
                    "operators": [],
                }
            },
        }

    def _save_registry(self) -> None:
        self.registry["last_updated"] = time.strftime(
            "%Y-%m-%dT%H:%M:%S+08:00", time.localtime()
        )
        # 不强行覆写原 V2 注册表文件；写入工作区副本
        out_path = self.generated_dir / "operator_registry_v3.json"
        out_path.write_text(
            json.dumps(self.registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # 模板选择
    # ------------------------------------------------------------------
    @staticmethod
    def _select_template(problem_desc: str) -> str:
        """根据问题描述关键词选择模板 key。"""
        desc = problem_desc.lower()
        if any(k in desc for k in ("异常", "anomaly", "outlier", "3σ", "outlier")):
            return "anomaly_detect"
        if any(k in desc for k in ("校验", "validate", "validate", "必填", "必填字段")):
            return "data_validate"
        if any(k in desc for k in ("优化", "optimize", "suggest", "建议", "调优")):
            return "optimize_suggest"
        # 默认回退：用第一个模板
        return "anomaly_detect"

    @staticmethod
    def _func_name_from_template_key(tkey: str) -> str:
        return f"op_{tkey}"

    # ------------------------------------------------------------------
    # 生成
    # ------------------------------------------------------------------
    def generate(
        self,
        problem_desc: str,
        io_spec: Optional[IOSpec] = None,
    ) -> OperatorArtifact:
        """
        根据问题描述生成新算子。
        策略：模板匹配 -> 代码骨架填充 -> 依赖分析。
        """
        tkey = self._select_template(problem_desc)
        tpl = OPERATOR_TEMPLATES[tkey]
        func_name = self._func_name_from_template_key(tkey)

        # 组装完整源码
        code = (
            f"# Ω₀⊂⊙∞⊂Ω · {DID} · {KERNEL_VERSION}\n"
            f"# AUTO-GENERATED OPERATOR\n\n"
            f"{tpl['body'].format(func_name=func_name, doc=tpl['docstring'])}\n"
        )

        # 依赖分析
        deps = analyze_dependencies(code)

        # 生成 op_id
        op_id = f"OP-GEN-{time.strftime('%Y%m%d-%H%M%S')}-{hashlib.sha1(problem_desc.encode()).hexdigest()[:6].upper()}"

        artifact = OperatorArtifact(
            op_id=op_id,
            op_name=tpl["op_name"],
            problem_desc=problem_desc,
            io_spec=io_spec or IOSpec(description=problem_desc),
            code=code,
            template_used=tkey,
            dependencies=deps,
        )
        return artifact

    # ------------------------------------------------------------------
    # 沙箱验证
    # ------------------------------------------------------------------
    def validate(self, artifact: OperatorArtifact) -> bool:
        """
        在受限 exec 命名空间中：
          1) ast.parse 语法检查；
          2) 编译执行，取出函数对象；
          3) 用模板内置测试用例跑一次基本功能测试。
        """
        # Step 1: 语法
        try:
            tree = ast.parse(artifact.code)
        except SyntaxError as exc:
            print(f"  [validate] 语法错误: {exc}")
            return False

        # Step 2: 受限 exec
        ns = _safe_exec_namespace()
        try:
            exec(compile(tree, "<generated>", "exec"), ns)
        except Exception as exc:  # noqa: BLE001
            print(f"  [validate] 执行错误: {exc}")
            return False

        # Step 3: 找到函数对象并跑测试
        func_name = self._func_name_from_template_key(artifact.template_used)
        func: Optional[Callable[..., Any]] = ns.get(func_name)
        if not callable(func):
            print(f"  [validate] 未找到函数 {func_name}")
            return False

        tpl = OPERATOR_TEMPLATES[artifact.template_used]
        test_input_expr = tpl["test_input"]
        test_assert_expr = tpl["test_assert"]
        try:
            result = eval(  # noqa: S307 - 受控沙箱内
                f"func({test_input_expr})",
                {"func": func},
                {"func": func},
            )
            # 用断言表达式验证
            passed = eval(test_assert_expr, {"result": result})  # noqa: S307
            if not passed:
                print(f"  [validate] 测试断言失败: {test_assert_expr}")
                return False
        except Exception as exc:  # noqa: BLE001
            print(f"  [validate] 测试执行异常: {exc}")
            return False

        artifact.sandbox_ok = True
        return True

    # ------------------------------------------------------------------
    # 自动注册
    # ------------------------------------------------------------------
    def register(self, artifact: OperatorArtifact) -> str:
        """
        验证通过后写入算子注册表（工作区副本）。
        返回分配的 op_id。
        """
        if not artifact.sandbox_ok:
            raise RuntimeError(f"算子 {artifact.op_id} 未通过沙箱验证，禁止注册")

        subsystem = self.registry.setdefault("subsystems", {}).setdefault(
            "meta_closed_loop",
            {"name": "元闭环自生成算子", "skill": "v3_meta_loop", "operators": []},
        )
        operators_list: List[Dict[str, Any]] = subsystem.setdefault("operators", [])

        entry = {
            "operator_id": artifact.op_id,
            "name": artifact.op_name,
            "min_authority": "L2",
            "description": artifact.problem_desc,
            "input_spec": ", ".join(artifact.io_spec.input_params) or artifact.io_spec.description,
            "output_spec": artifact.io_spec.output_type,
            "template_used": artifact.template_used,
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
        }
        operators_list.append(entry)

        # 写出生成算子源码到工作区
        src_file = self.generated_dir / f"{artifact.op_id}.py"
        src_file.write_text(artifact.code, encoding="utf-8")

        self._save_registry()
        artifact.registered = True
        self.generated_history.append(artifact)
        return artifact.op_id

    # ------------------------------------------------------------------
    # 一键生成+验证+注册
    # ------------------------------------------------------------------
    def auto_generate(
        self,
        problem_desc: str,
        io_spec: Optional[IOSpec] = None,
    ) -> Tuple[OperatorArtifact, bool]:
        artifact = self.generate(problem_desc, io_spec)
        ok = self.validate(artifact)
        if ok:
            self.register(artifact)
        return artifact, ok


# ======================================================================
# 演示
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] OperatorGenerator 算子自动生成\n")

    gen = OperatorGenerator()

    # 测试 3 个内置模板
    test_cases = [
        ("需要一个 3σ 异常检测算子，识别数据序列中的离群点",
         IOSpec(input_params=["data"], input_types={"data": "list"},
                output_type="list", description="3σ 异常检测")),
        ("需要一个数据校验算子，检查记录字典必填字段",
         IOSpec(input_params=["record", "required_fields"],
                input_types={"record": "dict", "required_fields": "list"},
                output_type="tuple", description="必填字段校验")),
        ("需要一个优化建议算子，根据指标和阈值给出调优方向",
         IOSpec(input_params=["metrics", "thresholds"],
                input_types={"metrics": "dict", "thresholds": "dict"},
                output_type="list", description="指标优化建议")),
    ]

    for desc, spec in test_cases:
        print(f"[PROBLEM] {desc}")
        art, ok = gen.auto_generate(desc, spec)
        print(f"  -> op_id={art.op_id}")
        print(f"  -> template={art.template_used}, sandbox_ok={art.sandbox_ok}, "
              f"registered={art.registered}")
        print(f"  -> deps={art.dependencies}")
        print()

    print(f"[SUMMARY] 共生成 {len(gen.generated_history)} 个算子")
    print(f"[SUMMARY] 注册表副本: {gen.generated_dir / 'operator_registry_v3.json'}")
