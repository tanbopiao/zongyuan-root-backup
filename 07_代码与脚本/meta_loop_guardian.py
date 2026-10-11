# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0
================================================================
meta_loop_guardian.py — 元闭环守护（公理一致性校验）
================================================================
职责：
  - 硬编码四条核心公理（AXIOM-001 ~ AXIOM-004），不可被自修改触及；
  - 对每一次代码变更执行 AST 静态扫描，识别危险调用
    (eval / exec / os.system / 文件删除 / __import__ 等)；
  - 变更前创建回滚点，支持按 point_id 回滚；
  - 公理哈希自检：verify_axiom_integrity() 比对当前公理哈希与
    内核启动时锚定的哈希，一旦漂移立即告警。

接口：
  - check(change_request) -> GuardResult
  - create_rollback_point() -> point_id
  - rollback(point_id) -> bool
  - verify_axiom_integrity() -> bool
"""

from __future__ import annotations

import ast
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 确权锚点（不可变）
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.0-META-CLOSED-LOOP"

# ---------------------------------------------------------------------------
# 核心公理集（硬编码不可变）
# ---------------------------------------------------------------------------
CORE_AXIOMS: Dict[str, Dict[str, str]] = {
    "AXIOM-001": {
        "name": "元极恒一",
        "statement": "系统同一性不可破坏：内核身份、确权锚点、DID 全局唯一且不可改写。",
    },
    "AXIOM-002": {
        "name": "同源守恒",
        "statement": "所有变更必须可追溯、可校验：每一次自修改都必须留下时间戳、输入、diff、哈希。",
    },
    "AXIOM-003": {
        "name": "自治边界",
        "statement": "自修改不得触及守护层自身代码（meta_loop_guardian.py 及其公理定义）。",
    },
    "AXIOM-004": {
        "name": "安全优先",
        "statement": "任何变更不得引入已知危险模式：eval/exec/os.system/文件删除/动态导入等。",
    },
}

# AST 危险节点黑名单（AXIOM-004 落地）
DANGEROUS_CALL_NAMES: frozenset = frozenset({
    "eval", "exec", "compile",
    "system", "popen", "spawn", "spawnl", "spawnv",
    "remove", "unlink", "rmdir", "removedirs", "rmtree",
    "rmdir", "rename", "chmod", "chown",
})

DANGEROUS_IMPORT_MODULES: frozenset = frozenset({
    "os", "subprocess", "pty", "platform",
    "shutil", "pathlib",  # pathlib 本身不危险，但 unlink/rmtree 危险
    "socket", "requests", "urllib", "http",
})

# 守护层自身文件名（AXIOM-003 落地：禁止自改）
GUARDIAN_PROTECTED_FILES: frozenset = frozenset({
    "meta_loop_guardian.py",
})


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class ChangeRequest:
    """一次代码变更请求。"""
    target_file: str               # 拟修改的算子文件路径或模块名
    new_code: str                  # 拟写入的完整代码
    change_type: str = "generate"  # generate | modify
    source_problem: str = ""       # 触发本次变更的问题描述
    author: str = "v3_meta_loop"   # 变更发起者

    def fingerprint(self) -> str:
        """生成变更请求指纹（用于同源守恒留痕）。"""
        h = hashlib.sha256()
        h.update(self.target_file.encode("utf-8"))
        h.update(self.new_code.encode("utf-8"))
        h.update(self.change_type.encode("utf-8"))
        return h.hexdigest()[:16]


@dataclass
class GuardResult:
    """守护校验结果。"""
    allowed: bool
    verdict: str                    # "PROCEED" | "REJECTED"
    violated_axioms: List[str] = field(default_factory=list)
    dangerous_hits: List[str] = field(default_factory=list)
    message: str = ""
    change_fp: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "verdict": self.verdict,
            "violated_axioms": self.violated_axioms,
            "dangerous_hits": self.dangerous_hits,
            "message": self.message,
            "change_fp": self.change_fp,
            "timestamp": self.timestamp,
        }


@dataclass
class RollbackPoint:
    point_id: str
    timestamp: float
    snapshot: Dict[str, str]        # file_path -> original_content


# ---------------------------------------------------------------------------
# AST 危险扫描器
# ---------------------------------------------------------------------------
class _DangerousCallScanner(ast.NodeVisitor):
    """遍历 AST，收集危险调用/导入。"""

    def __init__(self) -> None:
        self.hits: List[str] = []

    # ---- Call 节点：检测 eval/exec/os.system 等 -------------------------
    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        # 直接调用 eval(...) / exec(...)
        if isinstance(func, ast.Name) and func.id in DANGEROUS_CALL_NAMES:
            self.hits.append(f"call:{func.id}() @line{node.lineno}")
        # 模块属性调用 os.system(...) / subprocess.Popen(...)
        if isinstance(func, ast.Attribute) and func.attr in DANGEROUS_CALL_NAMES:
            base = func.value
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = f"{ast.dump(base.value)}.{base.attr}" if base.value else base.attr
            self.hits.append(f"call:{base_name}.{func.attr}() @line{node.lineno}")
        self.generic_visit(node)

    # ---- Import 节点 -----------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in DANGEROUS_IMPORT_MODULES:
                self.hits.append(f"import:{alias.name} @line{node.lineno}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            top = node.module.split(".")[0]
            if top in DANGEROUS_IMPORT_MODULES:
                self.hits.append(f"from:{node.module} import {','.join(a.name for a in node.names)} @line{node.lineno}")
        self.generic_visit(node)

    # ---- Attribute：检测 __import__ / __builtins__ ----------------------
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in ("__import__", "__builtins__", "__subclasses__", "__globals__"):
            self.hits.append(f"meta_attr:{node.attr} @line{node.lineno}")
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# 主守护类
# ---------------------------------------------------------------------------
class MetaLoopGuardian:
    """元闭环守护：公理一致性校验 + 危险模式拦截 + 回滚。"""

    def __init__(self, workspace_dir: Optional[Path] = None) -> None:
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.snapshot_dir = self.workspace / ".guardian_snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 公理哈希锚点（启动时固化）
        self._axiom_anchor_hash = self._compute_axiom_hash()

        # 回滚点表
        self._rollback_points: Dict[str, RollbackPoint] = {}

        # 安全告警日志
        self.alert_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 公理哈希
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_axiom_hash() -> str:
        payload = json.dumps(CORE_AXIOMS, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def verify_axiom_integrity(self) -> bool:
        """校验当前公理集哈希是否仍与启动锚点一致。"""
        return self._compute_axiom_hash() == self._axiom_anchor_hash

    # ------------------------------------------------------------------
    # AST 危险扫描
    # ------------------------------------------------------------------
    @staticmethod
    def scan_dangerous_patterns(code: str) -> List[str]:
        """对一段 Python 源码做 AST 扫描，返回危险命中列表。"""
        hits: List[str] = []
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            hits.append(f"syntax_error:{exc}")
            return hits
        scanner = _DangerousCallScanner()
        scanner.visit(tree)
        hits.extend(scanner.hits)
        return hits

    # ------------------------------------------------------------------
    # 变更前校验（核心入口）
    # ------------------------------------------------------------------
    def check(self, change: ChangeRequest) -> GuardResult:
        """
        对一次自修改变更执行四道公理校验：
          AXIOM-001 元极恒一 —— 确权锚点/DID 不得被改写；
          AXIOM-002 同源守恒 —— 变更必须有指纹、有来源问题；
          AXIOM-003 自治边界 —— 禁止修改守护层自身文件；
          AXIOM-004 安全优先 —— AST 扫描危险模式。
        """
        fp = change.fingerprint()
        violated: List[str] = []
        hits: List[str] = []

        # -- AXIOM-001：元极恒一 -----------------------------------------
        # 新代码里若出现对确权锚点/DID 的"改写赋值"则拒绝
        if self._is_tampering_provenance(change.new_code):
            violated.append("AXIOM-001")

        # -- AXIOM-002：同源守恒 -----------------------------------------
        if not change.source_problem.strip():
            violated.append("AXIOM-002")

        # -- AXIOM-003：自治边界 -----------------------------------------
        base = Path(change.target_file).name
        if base in GUARDIAN_PROTECTED_FILES:
            violated.append("AXIOM-003")

        # -- AXIOM-004：安全优先 -----------------------------------------
        scan_hits = self.scan_dangerous_patterns(change.new_code)
        # 语法错误本身也算危险
        hits.extend(scan_hits)
        if scan_hits:
            violated.append("AXIOM-004")

        allowed = len(violated) == 0
        result = GuardResult(
            allowed=allowed,
            verdict="PROCEED" if allowed else "REJECTED",
            violated_axioms=violated,
            dangerous_hits=hits,
            message=(
                f"变更 fp={fp} 校验通过" if allowed
                else f"变更 fp={fp} 违反公理 {violated}，拒绝提交"
            ),
            change_fp=fp,
        )

        if not allowed:
            self.alert_log.append({
                "timestamp": time.time(),
                "alert": "AXIOM_VIOLATION",
                "violated_axioms": violated,
                "hits": hits,
                "target_file": change.target_file,
                "source_problem": change.source_problem,
            })
        return result

    @staticmethod
    def _is_tampering_provenance(code: str) -> bool:
        """粗筛：新代码里是否出现对确权锚点/DID 的字符串赋值改写。"""
        forbidden_assign_patterns = [
            "DID-BR-000001",   # 伪 DID
            "DID-BR-999999",
            "PROVENANCE_ANCHOR = \"\"",
            "PROVENANCE_ANCHOR = ''",
            "Ω₀⊂⊙∞⊂Ω = None",
        ]
        for pat in forbidden_assign_patterns:
            if pat in code:
                return True
        return False

    # ------------------------------------------------------------------
    # 回滚点管理
    # ------------------------------------------------------------------
    def create_rollback_point(self, files_snapshot: Optional[Dict[str, str]] = None) -> str:
        """
        创建回滚点。files_snapshot 为 {file_path: original_content}，
        若未提供则创建一个空快照点（仍可用于审计留痕）。
        """
        point_id = f"RB-{int(time.time())}-{hashlib.sha1(str(time.time()).encode()).hexdigest()[:6]}"
        snapshot = files_snapshot or {}
        point = RollbackPoint(point_id=point_id, timestamp=time.time(), snapshot=snapshot)
        self._rollback_points[point_id] = point

        # 持久化快照
        snap_file = self.snapshot_dir / f"{point_id}.json"
        snap_file.write_text(
            json.dumps({
                "point_id": point_id,
                "timestamp": point.timestamp,
                "snapshot": point.snapshot,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return point_id

    def rollback(self, point_id: str) -> bool:
        """按 point_id 回滚：将快照中的内容写回原文件。"""
        point = self._rollback_points.get(point_id)
        if point is None:
            # 尝试从磁盘加载
            snap_file = self.snapshot_dir / f"{point_id}.json"
            if not snap_file.exists():
                return False
            data = json.loads(snap_file.read_text(encoding="utf-8"))
            point = RollbackPoint(
                point_id=data["point_id"],
                timestamp=data["timestamp"],
                snapshot=data["snapshot"],
            )
            self._rollback_points[point_id] = point

        for file_path, content in point.snapshot.items():
            try:
                Path(file_path).write_text(content, encoding="utf-8")
            except OSError:
                return False
        return True

    # ------------------------------------------------------------------
    # 诊断报告
    # ------------------------------------------------------------------
    def guardian_status(self) -> Dict[str, Any]:
        return {
            "provenance_anchor": PROVENANCE_ANCHOR,
            "did": DID,
            "kernel_version": KERNEL_VERSION,
            "axiom_count": len(CORE_AXIOMS),
            "axiom_anchor_hash": self._axiom_anchor_hash,
            "axiom_integrity_ok": self.verify_axiom_integrity(),
            "rollback_points": list(self._rollback_points.keys()),
            "alert_count": len(self.alert_log),
            "axioms": CORE_AXIOMS,
        }


# ======================================================================
# 演示：可直接运行
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] MetaLoopGuardian 公理守护自检\n")

    guardian = MetaLoopGuardian()

    # 1) 公理完整性
    print("[1] 公理完整性校验:", "OK" if guardian.verify_axiom_integrity() else "FAILED")

    # 2) 正向变更（干净代码）应通过
    clean_code = '''
def op_anomaly_detect(data: list):
    """检测数据异常点（3σ 法则）。"""
    if not data:
        return []
    mean = sum(data) / len(data)
    var = sum((x - mean) ** 2 for x in data) / len(data)
    std = var ** 0.5
    return [x for x in data if abs(x - mean) > 3 * std]
'''
    good_req = ChangeRequest(
        target_file="op_anomaly_detect.py",
        new_code=clean_code,
        change_type="generate",
        source_problem="需要 3σ 异常检测算子",
    )
    res_ok = guardian.check(good_req)
    print(f"[2] 干净代码校验: {res_ok.verdict}  (hits={res_ok.dangerous_hits})")

    # 3) 危险变更（os.system）应被拒绝
    evil_code = '''
import os
def hack():
    os.system("rm -rf /")
'''
    bad_req = ChangeRequest(
        target_file="op_hack.py",
        new_code=evil_code,
        change_type="generate",
        source_problem="测试危险拦截",
    )
    res_bad = guardian.check(bad_req)
    print(f"[3] 危险代码校验: {res_bad.verdict}")
    print(f"    违反公理: {res_bad.violated_axioms}")
    print(f"    危险命中: {res_bad.dangerous_hits}")

    # 4) 回滚点创建与查询
    pid = guardian.create_rollback_point({"demo.py": "original content"})
    print(f"[4] 创建回滚点: {pid}")
    print(f"    回滚点列表: {list(guardian._rollback_points.keys())}")

    # 5) 守护状态
    status = guardian.guardian_status()
    print(f"[5] 守护状态: alerts={status['alert_count']}, "
          f"axiom_hash={status['axiom_anchor_hash']}")
