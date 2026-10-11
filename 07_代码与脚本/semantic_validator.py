#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
昆仑洞天统一语义校验引擎 V3.0
作为记忆网关前置校验器，提供：
- 术语真值校验（validate_term）
- 多模型语义转译（translate_term）
- 资产对账校验（reconcile_asset）
- L0审美约束校验（validate_l0_constraints）
- 审计日志记录（audit_log）

确权锚点：Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class ValidationLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ViolationTriage(Enum):
    A_REDRAW = "A级重绘97%"
    B_DISCARD = "B级废弃"
    C_DESTROY = "C级彻底销毁"


@dataclass
class ValidationResult:
    """校验结果"""
    passed: bool
    term: str = ""
    level: str = ""
    truth: str = ""
    truth_cn: str = ""
    category: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    l0_violations: List[str] = field(default_factory=list)
    timestamp: str = ""
    check_id: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TranslateResult:
    """转译结果"""
    term: str
    target_model: str
    translated: str
    truth: str
    pitfalls_avoided: List[str] = field(default_factory=list)
    prefix_applied: bool = False
    suffix_applied: bool = False
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReconcileResult:
    """对账结果"""
    asset_id: str
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    semantic_terms_found: List[str] = field(default_factory=list)
    semantic_terms_valid: List[str] = field(default_factory=list)
    semantic_terms_invalid: List[str] = field(default_factory=list)
    merkle_hash: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class SemanticValidator:
    """统一语义校验引擎"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.environ.get(
                "SEMANTIC_ADAPTER_CONFIG",
                "/opt/ZONGYUAN-ROOT/config/semantic-adapter-v3.json"
            )
        self.config_path = config_path
        self.config = self._load_config()
        self.audit_log_path = os.environ.get(
            "SEMANTIC_AUDIT_LOG",
            "/opt/ZONGYUAN-ROOT/log/semantic_validator_audit.jsonl"
        )
        self._ensure_audit_dir()

    def _load_config(self) -> Dict:
        """加载配置"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"语义校验配置不存在: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _ensure_audit_dir(self):
        """确保审计日志目录存在"""
        audit_dir = os.path.dirname(self.audit_log_path)
        if audit_dir and not os.path.exists(audit_dir):
            os.makedirs(audit_dir, exist_ok=True)

    def _gen_check_id(self) -> str:
        """生成校验ID"""
        raw = f"{datetime.now().isoformat()}-{os.getpid()}-{time.time()}"
        return "SV-" + hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _audit(self, action: str, detail: Dict, node_id: str = "system"):
        """记录审计日志"""
        entry = {
            "timestamp": self._now(),
            "action": action,
            "detail": detail,
            "node_id": node_id,
            "did": self.config.get("did", "DID-BR-000002"),
            "anchor": self.config.get("anchor", "Ω₀⊂⊙∞⊂Ω")
        }
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[WARN] 审计日志写入失败: {e}", file=sys.stderr)

    # ========== 术语校验 ==========

    def validate_term(self, term: str, context: str = "") -> ValidationResult:
        """
        校验单个术语是否符合真值定义
        """
        check_id = self._gen_check_id()
        result = ValidationResult(
            passed=True,
            term=term,
            timestamp=self._now(),
            check_id=check_id
        )

        mappings = self.config.get("semantic_mapping", {})

        if term not in mappings:
            result.passed = False
            result.issues.append(f"术语 '{term}' 未在语义映射表中定义")
            result.suggestions.append(f"请添加 '{term}' 的真值定义，或使用已定义术语")
            self._audit("term_validation_failed", {"term": term, "reason": "undefined", "check_id": check_id})
            return result

        mapping = mappings[term]
        result.level = mapping.get("priority", "medium")
        result.truth = mapping.get("truth", "")
        result.truth_cn = mapping.get("truth_cn", "")
        result.category = mapping.get("category", "")

        # L0约束关联检查
        l0_constraint = mapping.get("l0_constraint", "")
        if l0_constraint:
            l0 = self.config.get("l0_aesthetic_constraints", {})
            five_prohibitions = l0.get("five_prohibitions", [])
            self_check = l0.get("self_check_12", [])

            # 检查上下文中是否有违反L0的表述
            if context:
                context_lower = context.lower()
                violation_keywords = {
                    "骨相绝对纯净": ["宽肩", "胸肌", "方下颌", "厚背", "宽腰", "muscle", "broad shoulder"],
                    "面部绝对神性": ["粗犷", "雄性眉骨", "高突颧骨", "masculine face"],
                    "体型绝对": ["骶椎", "壮硬", "肌肉块", "muscular"],
                    "力量绝对隔离": ["肌肉力量", "体格强壮", "physical power", "muscle power"],
                    "风格绝对去外源": ["西式战神", "现代超英", "中性伪雄", "western armor", "superhero"]
                }
                for constraint_name, keywords in violation_keywords.items():
                    for kw in keywords:
                        if kw.lower() in context_lower:
                            result.l0_violations.append(f"违反{constraint_name}: 上下文中包含 '{kw}'")
                            result.passed = False

        if result.l0_violations:
            result.issues.extend(result.l0_violations)
            result.suggestions.append("请修正L0审美约束违反项，参考五禁令和12项自检")

        self._audit("term_validation", {
            "term": term,
            "passed": result.passed,
            "level": result.level,
            "category": result.category,
            "l0_violations": len(result.l0_violations),
            "check_id": check_id
        })

        return result

    def validate_terms_batch(self, terms: List[str], context: str = "") -> List[ValidationResult]:
        """批量校验术语"""
        return [self.validate_term(t, context) for t in terms]

    def extract_and_validate_terms(self, text: str) -> Dict:
        """从文本中提取术语并校验"""
        mappings = self.config.get("semantic_mapping", {})
        found = []
        valid = []
        invalid = []

        for term in mappings.keys():
            if term in text:
                found.append(term)
                result = self.validate_term(term, text)
                if result.passed:
                    valid.append(term)
                else:
                    invalid.append(term)

        return {
            "total_found": len(found),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "found_terms": found,
            "valid_terms": valid,
            "invalid_terms": invalid,
            "pass_rate": f"{len(valid)/len(found)*100:.1f}%" if found else "N/A"
        }

    # ========== 多模型转译 ==========

    def translate_term(self, term: str, target_model: str,
                        apply_prefix: bool = False, apply_suffix: bool = False) -> TranslateResult:
        """
        将术语转译为目标模型的准确表述
        """
        mappings = self.config.get("semantic_mapping", {})
        models = self.config.get("model_profiles", {})

        result = TranslateResult(
            term=term,
            target_model=target_model,
            translated="",
            truth="",
            timestamp=self._now()
        )

        if term not in mappings:
            result.translated = term
            result.pitfalls_avoided.append(f"术语 '{term}' 未定义，原样返回")
            self._audit("translate_failed", {"term": term, "model": target_model, "reason": "undefined"})
            return result

        if target_model not in models:
            result.translated = mappings[term].get("truth", term)
            result.pitfalls_avoided.append(f"模型 '{target_model}' 未配置，返回通用真值")
            self._audit("translate_warning", {"term": term, "model": target_model, "reason": "model_not_configured"})
            return result

        model_key = f"for_{target_model}"
        translated = mappings[term].get(model_key, mappings[term].get("truth", term))
        result.translated = translated
        result.truth = mappings[term].get("truth", "")

        # 应用模型前缀/后缀
        model_config = models[target_model]
        if apply_prefix and model_config.get("prompt_prefix"):
            result.translated = model_config["prompt_prefix"] + " " + translated
            result.prefix_applied = True
        if apply_suffix and model_config.get("prompt_suffix"):
            result.translated = translated + " " + model_config["prompt_suffix"]
            result.suffix_applied = True

        # 记录避开的陷阱
        pitfalls = model_config.get("known_pitfalls", {})
        if term in pitfalls:
            result.pitfalls_avoided.append(pitfalls[term])

        self._audit("translate", {
            "term": term,
            "model": target_model,
            "translated": translated[:80],
            "pitfalls_avoided": len(result.pitfalls_avoided)
        })

        return result

    def build_full_prompt(self, terms: List[str], target_model: str,
                           character_details: str = "") -> str:
        """
        构建完整的模型prompt（应用全局规则+术语转译+模型前后缀）
        """
        models = self.config.get("model_profiles", {})
        if target_model not in models:
            return " ".join(terms)

        model_config = models[target_model]
        parts = []

        # 前缀
        if model_config.get("prompt_prefix"):
            parts.append(model_config["prompt_prefix"])

        # 角色细节
        if character_details:
            parts.append(character_details)

        # 术语转译
        for term in terms:
            trans = self.translate_term(term, target_model)
            parts.append(trans.translated)

        # 后缀
        if model_config.get("prompt_suffix"):
            parts.append(model_config["prompt_suffix"])

        return ", ".join(parts)

    # ========== L0审美约束校验 ==========

    def validate_l0_constraints(self, text_or_image_desc: str) -> Dict:
        """
        校验内容是否符合L0审美约束
        """
        l0 = self.config.get("l0_aesthetic_constraints", {})
        five_prohibitions = l0.get("five_prohibitions", [])
        self_check = l0.get("self_check_12", [])

        text_lower = text_or_image_desc.lower()
        violations = []
        passed_checks = []

        # 五禁令关键词检查
        prohibition_keywords = {
            "骨相绝对纯净": ["宽肩", "胸肌", "方下颌", "厚背", "宽腰", "broad shoulder", "muscle chest", "square jaw"],
            "面部绝对神性": ["粗犷", "雄性眉骨", "高突颧骨", "masculine face", "rough features"],
            "体型绝对": ["骶椎", "壮硬", "肌肉块", "muscular", "buff"],
            "力量绝对隔离": ["肌肉力量", "体格强壮", "physical power", "muscle power"],
            "风格绝对去外源": ["西式战神", "现代超英", "中性伪雄", "western armor", "superhero", "androgynous"]
        }

        for constraint_name, keywords in prohibition_keywords.items():
            found = [kw for kw in keywords if kw.lower() in text_lower]
            if found:
                violations.append(f"违反{constraint_name}: {', '.join(found)}")
            else:
                passed_checks.append(constraint_name)

        # 12项自检关键词检查
        self_check_keywords = {
            "纯东方女相": ["西方", "western", "欧式"],
            "无男宽肩": ["宽肩", "broad shoulder"],
            "无男胸肌": ["胸肌", "muscle chest"],
            "无男方下颌": ["方下颌", "square jaw"],
            "无粗犷五官": ["粗犷", "rough"],
            "无厚背宽腰": ["厚背", "宽腰"],
            "无肌肉块": ["肌肉块", "muscle"],
            "无短发": ["短发", "short hair"],
            "无白发彩发": ["白发", "彩发", "white hair", "colorful hair"],
            "无西式铠甲": ["西式铠甲", "western armor"],
            "无幼态娇媚": ["幼态", "娇媚", "cute", "childlike"],
            "保留角色专属标识": []  # 此项需人工确认
        }

        for check_name, keywords in self_check_keywords.items():
            if check_name == "保留角色专属标识":
                passed_checks.append(check_name + "（需人工确认）")
                continue
            found = [kw for kw in keywords if kw.lower() in text_lower]
            if found:
                violations.append(f"自检不通过-{check_name}: 发现 {', '.join(found)}")
            else:
                passed_checks.append(check_name)

        result = {
            "passed": len(violations) == 0,
            "total_checks": len(five_prohibitions) + len(self_check),
            "passed_count": len(passed_checks),
            "violation_count": len(violations),
            "violations": violations,
            "passed_checks": passed_checks,
            "violation_triage": self._determine_triage(violations),
            "timestamp": self._now()
        }

        self._audit("l0_validation", {
            "passed": result["passed"],
            "violations": len(violations),
            "triage": result["violation_triage"]
        })

        return result

    def _determine_triage(self, violations: List[str]) -> str:
        """根据违规情况确定分级处理"""
        if not violations:
            return "通过"
        critical_count = sum(1 for v in violations if any(
            kw in v for kw in ["骨相", "面部", "力量", "风格"]
        ))
        if critical_count >= 3:
            return ViolationTriage.C_DESTROY.value
        elif critical_count >= 1:
            return ViolationTriage.B_DISCARD.value
        else:
            return ViolationTriage.A_REDRAW.value

    # ========== 资产对账 ==========

    def reconcile_asset(self, asset_data: Dict, asset_id: str = "") -> ReconcileResult:
        """
        对资产进行全方位对账校验
        包括：真值字段校验 + 语义术语校验 + 哈希校验 + L0约束校验
        """
        result = ReconcileResult(
            asset_id=asset_id or asset_data.get("asset_id", "unknown"),
            passed=True,
            timestamp=self._now()
        )

        # 1. 真值字段校验（对齐truth_validator的5项）
        required_fields = ["meta_homo_root", "asset_did", "timestamp"]
        valid_roots = ["Ω-TAN-7-001", "Ω₀⊂⊙∞⊂Ω"]
        valid_did_prefix = "DID-BR-"

        for field in required_fields:
            if field in asset_data:
                result.checks[f"field_{field}"] = True
            else:
                result.checks[f"field_{field}"] = False
                result.issues.append(f"缺少必需字段: {field}")
                result.passed = False

        # 根标识校验
        root = asset_data.get("meta_homo_root", "")
        if root:
            result.checks["root_valid"] = root in valid_roots
            if root not in valid_roots:
                result.issues.append(f"根标识无效: {root}（应为 {valid_roots}）")
                result.passed = False

        # DID校验
        did = asset_data.get("asset_did", "")
        if did:
            result.checks["did_valid"] = did.startswith(valid_did_prefix)
            if not did.startswith(valid_did_prefix):
                result.issues.append(f"DID格式无效: {did}（应以 {valid_did_prefix} 开头）")
                result.passed = False

        # 哈希校验
        sha256 = asset_data.get("sha256", "")
        if sha256:
            result.checks["hash_present"] = True
            if len(sha256) == 64:
                result.checks["hash_format"] = True
            else:
                result.checks["hash_format"] = False
                result.issues.append(f"SHA256格式无效: 长度{len(sha256)}（应为64）")
                result.passed = False
        else:
            result.checks["hash_present"] = False
            result.issues.append("缺少SHA256哈希")
            result.passed = False

        # 2. 语义术语校验
        asset_text = json.dumps(asset_data, ensure_ascii=False)
        semantic_result = self.extract_and_validate_terms(asset_text)
        result.semantic_terms_found = semantic_result["found_terms"]
        result.semantic_terms_valid = semantic_result["valid_terms"]
        result.semantic_terms_invalid = semantic_result["invalid_terms"]

        if semantic_result["invalid_count"] > 0:
            result.issues.append(f"语义术语校验未通过: {semantic_result['invalid_count']}个术语无效")
            result.passed = False

        # 3. L0约束校验（如果资产包含描述文本）
        description = asset_data.get("description", "") or asset_data.get("summary", "")
        if description:
            l0_result = self.validate_l0_constraints(description)
            result.checks["l0_constraints"] = l0_result["passed"]
            if not l0_result["passed"]:
                result.issues.extend([f"L0: {v}" for v in l0_result["violations"]])
                result.passed = False

        # 4. 生成Merkle哈希
        result.merkle_hash = hashlib.sha256(
            json.dumps(asset_data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        self._audit("asset_reconcile", {
            "asset_id": result.asset_id,
            "passed": result.passed,
            "checks_passed": sum(1 for v in result.checks.values() if v),
            "checks_total": len(result.checks),
            "issues": len(result.issues),
            "semantic_terms": len(result.semantic_terms_found)
        })

        return result

    # ========== 统计与状态 ==========

    def get_stats(self) -> Dict:
        """获取引擎统计信息"""
        mappings = self.config.get("semantic_mapping", {})
        models = self.config.get("model_profiles", {})

        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_category = {}
        for term, info in mappings.items():
            p = info.get("priority", "medium")
            by_priority[p] = by_priority.get(p, 0) + 1
            c = info.get("category", "unknown")
            by_category[c] = by_category.get(c, 0) + 1

        # 审计日志统计
        audit_count = 0
        if os.path.exists(self.audit_log_path):
            with open(self.audit_log_path, 'r') as f:
                audit_count = sum(1 for _ in f)

        return {
            "engine_version": self.config.get("version", "unknown"),
            "engine_name": self.config.get("adapter_name", "unknown"),
            "role": self.config.get("role_in_system", ""),
            "total_terms": len(mappings),
            "total_models": len(models),
            "terms_by_priority": by_priority,
            "terms_by_category": by_category,
            "l0_constraints": {
                "five_prohibitions": len(self.config.get("l0_aesthetic_constraints", {}).get("five_prohibitions", [])),
                "self_check_12": len(self.config.get("l0_aesthetic_constraints", {}).get("self_check_12", [])),
                "character_ids": len(self.config.get("l0_aesthetic_constraints", {}).get("character_ids", {}))
            },
            "validation_rules_groups": len(self.config.get("validation_rules", {})),
            "core_rules": len(self.config.get("rules_v2", [])),
            "audit_log_count": audit_count,
            "audit_log_path": self.audit_log_path,
            "config_path": self.config_path,
            "did": self.config.get("did", ""),
            "anchor": self.config.get("anchor", ""),
            "timestamp": self._now()
        }

    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        logs = []
        if os.path.exists(self.audit_log_path):
            with open(self.audit_log_path, 'r') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        pass
        return logs[-limit:]


# ========== 命令行入口 ==========

def main():
    import argparse
    parser = argparse.ArgumentParser(description="昆仑洞天统一语义校验引擎 V3.0")
    parser.add_argument("--mode", choices=["validate", "translate", "reconcile", "l0-check", "stats", "audit"],
                        default="stats", help="运行模式")
    parser.add_argument("--term", help="要校验/转译的术语")
    parser.add_argument("--terms", nargs="+", help="批量术语列表")
    parser.add_argument("--model", default="agnes_image", help="目标模型")
    parser.add_argument("--context", default="", help="上下文文本")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--limit", type=int, default=100, help="审计日志条数")
    parser.add_argument("--apply-prefix", action="store_true", help="转译时应用模型前缀")
    parser.add_argument("--apply-suffix", action="store_true", help="转译时应用模型后缀")

    args = parser.parse_args()

    validator = SemanticValidator(args.config)

    if args.mode == "validate":
        if args.terms:
            results = validator.validate_terms_batch(args.terms, args.context)
        elif args.term:
            results = [validator.validate_term(args.term, args.context)]
        else:
            print("错误: 请指定 --term 或 --terms")
            sys.exit(1)
        for r in results:
            print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))

    elif args.mode == "translate":
        if not args.term:
            print("错误: 请指定 --term")
            sys.exit(1)
        result = validator.translate_term(args.term, args.model, args.apply_prefix, args.apply_suffix)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    elif args.mode == "reconcile":
        # 从stdin读取资产JSON
        asset_data = json.load(sys.stdin)
        result = validator.reconcile_asset(asset_data)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    elif args.mode == "l0-check":
        text = args.context or sys.stdin.read()
        result = validator.validate_l0_constraints(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.mode == "stats":
        print(json.dumps(validator.get_stats(), ensure_ascii=False, indent=2))

    elif args.mode == "audit":
        logs = validator.get_audit_logs(args.limit)
        print(json.dumps(logs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
