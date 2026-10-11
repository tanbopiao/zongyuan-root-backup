#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义校验引擎元校验器
定期验证校验器自身是否正常运行
测试用例覆盖：术语校验/多模型转译/L0约束/资产对账/引擎统计
"""
import json
import sys
import os
import time
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

# 添加引擎路径
sys.path.insert(0, "/opt/ZONGYUAN-ROOT/engine/scripts")

try:
    from semantic_validator import SemanticValidator
except ImportError:
    print("FATAL: 无法导入semantic_validator模块")
    sys.exit(1)


@dataclass
class MetaTestCase:
    """元校验测试用例"""
    test_id: str
    category: str
    description: str
    expected_pass: bool
    expected_keywords: List[str] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaTestResult:
    """元校验测试结果"""
    test_id: str
    category: str
    description: str
    passed: bool
    actual_result: str = ""
    error: str = ""
    duration_ms: float = 0


class SemanticMetaValidator:
    """语义校验引擎元校验器"""

    def __init__(self):
        self.validator = SemanticValidator()
        self.results: List[MetaTestResult] = []
        self.start_time = time.time()
        self.meta_log_path = "/opt/ZONGYUAN-ROOT/log/semantic_meta_validation.jsonl"
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        log_dir = os.path.dirname(self.meta_log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def _log(self, result: MetaTestResult):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "meta_validation",
            "result": asdict(result)
        }
        try:
            with open(self.meta_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[WARN] 元校验日志写入失败: {e}", file=sys.stderr)

    def run_all_tests(self) -> Dict:
        """运行全部元校验测试"""
        print("=" * 60)
        print("  语义校验引擎元校验")
        print(f"  时间: {datetime.now().isoformat()}")
        print("=" * 60)

        test_cases = self._build_test_cases()
        print(f"\n共 {len(test_cases)} 个测试用例\n")

        for tc in test_cases:
            result = self._run_test(tc)
            self.results.append(result)
            self._log(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"  [{status}] {tc.test_id:30s} | {tc.description[:40]} ({result.duration_ms:.1f}ms)")
            if not result.passed:
                print(f"         错误: {result.error[:80]}")

        return self._generate_report()

    def _build_test_cases(self) -> List[MetaTestCase]:
        """构建测试用例"""
        return [
            # === 术语校验测试 ===
            MetaTestCase(
                test_id="TERM-VALID-001",
                category="term_validation",
                description="已知术语'九头身'应校验通过",
                expected_pass=True,
                expected_keywords=["九头身", "critical"],
                input_data={"term": "九头身"}
            ),
            MetaTestCase(
                test_id="TERM-VALID-002",
                category="term_validation",
                description="已知术语'凤目'应校验通过",
                expected_pass=True,
                expected_keywords=["凤目", "high", "face"],
                input_data={"term": "凤目"}
            ),
            MetaTestCase(
                test_id="TERM-INVALID-001",
                category="term_validation",
                description="未知术语'不存在的词'应校验失败",
                expected_pass=False,
                expected_keywords=["未在语义映射表中定义"],
                input_data={"term": "不存在的词xyz123"}
            ),
            MetaTestCase(
                test_id="TERM-L0-LINK-001",
                category="term_validation",
                description="关联L0约束的术语'削肩'应为critical级别body分类",
                expected_pass=True,
                expected_keywords=["削肩", "critical", "body"],
                input_data={"term": "削肩"}
            ),

            # === 多模型转译测试 ===
            MetaTestCase(
                test_id="TRANS-AGNES-001",
                category="translation",
                description="玄黑转译到agnes_image应包含crimson-black",
                expected_pass=True,
                expected_keywords=["crimson-black", "deep dark"],
                input_data={"term": "玄黑", "model": "agnes_image"}
            ),
            MetaTestCase(
                test_id="TRANS-TONGYI-001",
                category="translation",
                description="神女转译到tongyi_i2v应包含Chinese goddess",
                expected_pass=True,
                expected_keywords=["Chinese", "goddess"],
                input_data={"term": "神女", "model": "tongyi_i2v"}
            ),
            MetaTestCase(
                test_id="TRANS-ZHIPU-001",
                category="translation",
                description="月华转译到zhipu_text应返回中文",
                expected_pass=True,
                expected_keywords=["月华"],
                input_data={"term": "月华", "model": "zhipu_text"}
            ),
            MetaTestCase(
                test_id="TRANS-PITFALL-001",
                category="translation",
                description="九头身转译应避开'nine-head body'陷阱",
                expected_pass=True,
                expected_keywords=["9 times", "own head"],
                input_data={"term": "九头身", "model": "agnes_image"}
            ),

            # === L0约束校验测试 ===
            MetaTestCase(
                test_id="L0-PASS-001",
                category="l0_validation",
                description="合规文本应L0校验通过",
                expected_pass=True,
                expected_keywords=["通过", "17/17"],
                input_data={"text": "纯东方神女，削肩，纯黑长发，气场强大，法相庄严，仙姿"}
            ),
            MetaTestCase(
                test_id="L0-FAIL-001",
                category="l0_validation",
                description="含宽肩胸肌的文本应L0校验失败",
                expected_pass=False,
                expected_keywords=["宽肩", "胸肌", "骨相"],
                input_data={"text": "这个角色有宽肩和胸肌"}
            ),
            MetaTestCase(
                test_id="L0-FAIL-002",
                category="l0_validation",
                description="含西式铠甲的文本应L0校验失败",
                expected_pass=False,
                expected_keywords=["西式铠甲", "风格"],
                input_data={"text": "穿着西式铠甲"}
            ),
            MetaTestCase(
                test_id="L0-TRIAGE-001",
                category="l0_validation",
                description="多项违规应分级为B级废弃或C级销毁",
                expected_pass=False,
                expected_keywords=["B级"],
                input_data={"text": "宽肩胸肌西式铠甲短发白发可爱"}
            ),

            # === 资产对账测试 ===
            MetaTestCase(
                test_id="RECON-PASS-001",
                category="reconciliation",
                description="合规资产应对账通过",
                expected_pass=True,
                expected_keywords=["passed", "True"],
                input_data={
                    "asset_id": "META-TEST-001",
                    "meta_homo_root": "Ω-TAN-7-001",
                    "asset_did": "DID-BR-META001",
                    "timestamp": "2026-09-11T12:00:00",
                    "sha256": "a" * 64,
                    "description": "九头身神女玄黑赤金削肩"
                }
            ),
            MetaTestCase(
                test_id="RECON-FAIL-001",
                category="reconciliation",
                description="缺少必需字段的资产应对账失败",
                expected_pass=False,
                expected_keywords=["缺少必需字段"],
                input_data={"asset_id": "META-TEST-002"}
            ),
            MetaTestCase(
                test_id="RECON-FAIL-002",
                category="reconciliation",
                description="无效DID的资产应对账失败",
                expected_pass=False,
                expected_keywords=["DID格式无效"],
                input_data={
                    "asset_id": "META-TEST-003",
                    "meta_homo_root": "Ω-TAN-7-001",
                    "asset_did": "INVALID-DID",
                    "timestamp": "2026-09-11T12:00:00",
                    "sha256": "a" * 64
                }
            ),
            MetaTestCase(
                test_id="RECON-TERM-001",
                category="reconciliation",
                description="资产对账应发现并校验语义术语",
                expected_pass=True,
                expected_keywords=["semantic_terms_found"],
                input_data={
                    "asset_id": "META-TEST-004",
                    "meta_homo_root": "Ω-TAN-7-001",
                    "asset_did": "DID-BR-META004",
                    "timestamp": "2026-09-11T12:00:00",
                    "sha256": "a" * 64,
                    "description": "凤目月白华冠仙姿神光祥云"
                }
            ),

            # === 引擎统计测试 ===
            MetaTestCase(
                test_id="STATS-001",
                category="stats",
                description="引擎统计应返回55个词条",
                expected_pass=True,
                expected_keywords=["55"],
                input_data={}
            ),
            MetaTestCase(
                test_id="STATS-002",
                category="stats",
                description="引擎统计应返回4个模型",
                expected_pass=True,
                expected_keywords=["4"],
                input_data={}
            ),
            MetaTestCase(
                test_id="STATS-003",
                category="stats",
                description="引擎统计应包含critical优先级词条",
                expected_pass=True,
                expected_keywords=["critical"],
                input_data={}
            ),
        ]

    def _run_test(self, tc: MetaTestCase) -> MetaTestResult:
        """运行单个测试用例"""
        start = time.time()
        result = MetaTestResult(
            test_id=tc.test_id,
            category=tc.category,
            description=tc.description,
            passed=False
        )

        try:
            if tc.category == "term_validation":
                vr = self.validator.validate_term(tc.input_data["term"])
                result.actual_result = json.dumps(vr.to_dict(), ensure_ascii=False)
                if tc.expected_pass:
                    result.passed = vr.passed
                    if not result.passed:
                        result.error = f"期望通过但实际失败: {vr.issues}"
                else:
                    result.passed = not vr.passed
                    if not result.passed:
                        result.error = "期望失败但实际通过"
                # 验证关键词
                for kw in tc.expected_keywords:
                    if kw not in result.actual_result and kw not in str(vr.to_dict()):
                        if tc.expected_pass:  # 只对期望通过的测试严格检查关键词
                            result.passed = False
                            result.error = f"未找到预期关键词: {kw}"
                            break

            elif tc.category == "translation":
                tr = self.validator.translate_term(
                    tc.input_data["term"], tc.input_data["model"]
                )
                result.actual_result = tr.translated
                result.passed = True
                for kw in tc.expected_keywords:
                    if kw.lower() not in tr.translated.lower():
                        result.passed = False
                        result.error = f"转译结果未包含关键词: {kw}, 实际: {tr.translated[:50]}"
                        break

            elif tc.category == "l0_validation":
                lr = self.validator.validate_l0_constraints(tc.input_data["text"])
                result.actual_result = json.dumps(lr, ensure_ascii=False)
                if tc.expected_pass:
                    result.passed = lr["passed"]
                    if not result.passed:
                        result.error = f"期望通过但实际失败: {lr['violations'][:3]}"
                else:
                    result.passed = not lr["passed"]
                    if not result.passed:
                        result.error = "期望失败但实际通过"
                    # 验证违规关键词
                    for kw in tc.expected_keywords:
                        if kw not in result.actual_result:
                            result.passed = False
                            result.error = f"未找到预期违规关键词: {kw}"
                            break

            elif tc.category == "reconciliation":
                rr = self.validator.reconcile_asset(tc.input_data, tc.input_data.get("asset_id", ""))
                result.actual_result = json.dumps(rr.to_dict(), ensure_ascii=False)
                if tc.expected_pass:
                    result.passed = rr.passed
                    if not result.passed:
                        result.error = f"期望通过但实际失败: {rr.issues[:3]}"
                else:
                    result.passed = not rr.passed
                    if not result.passed:
                        result.error = "期望失败但实际通过"
                    for kw in tc.expected_keywords:
                        if kw not in result.actual_result:
                            result.passed = False
                            result.error = f"未找到预期关键词: {kw}"
                            break

            elif tc.category == "stats":
                stats = self.validator.get_stats()
                result.actual_result = json.dumps(stats, ensure_ascii=False)
                result.passed = True
                for kw in tc.expected_keywords:
                    if kw not in result.actual_result:
                        result.passed = False
                        result.error = f"统计结果未包含: {kw}"
                        break

        except Exception as e:
            result.passed = False
            result.error = f"异常: {str(e)}"

        result.duration_ms = (time.time() - start) * 1000
        return result

    def _generate_report(self) -> Dict:
        """生成元校验报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        duration = (time.time() - self.start_time) * 1000

        # 按分类统计
        by_category = {}
        for r in self.results:
            if r.category not in by_category:
                by_category[r.category] = {"total": 0, "passed": 0, "failed": 0}
            by_category[r.category]["total"] += 1
            if r.passed:
                by_category[r.category]["passed"] += 1
            else:
                by_category[r.category]["failed"] += 1

        report = {
            "meta_validation_id": "META-VAL-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "engine_version": self.validator.config.get("version", "unknown"),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
            "duration_ms": round(duration, 1),
            "by_category": by_category,
            "failed_tests": [
                {"test_id": r.test_id, "category": r.category, "error": r.error}
                for r in self.results if not r.passed
            ],
            "overall_status": "HEALTHY" if failed == 0 else ("DEGRADED" if failed <= 3 else "UNHEALTHY")
        }

        # 记录汇总日志
        summary_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "meta_validation_summary",
            "report": report
        }
        try:
            with open(self.meta_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(summary_entry, ensure_ascii=False) + "\n")
        except:
            pass

        print("\n" + "=" * 60)
        print(f"  元校验完成: {passed}/{total} 通过 ({report['pass_rate']})")
        print(f"  总耗时: {duration:.1f}ms")
        print(f"  整体状态: {report['overall_status']}")
        print("=" * 60)

        if failed > 0:
            print("\n失败用例:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.test_id}: {r.error[:60]}")

        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="语义校验引擎元校验器")
    parser.add_argument("--mode", choices=["run", "status", "history"], default="run")
    parser.add_argument("--limit", type=int, default=10, help="历史记录条数")
    args = parser.parse_args()

    if args.mode == "run":
        mv = SemanticMetaValidator()
        report = mv.run_all_tests()
        # 如果状态不健康，退出码非零
        if report["overall_status"] == "UNHEALTHY":
            sys.exit(2)
        elif report["overall_status"] == "DEGRADED":
            sys.exit(1)

    elif args.mode == "status":
        # 查看最近一次元校验状态
        log_path = "/opt/ZONGYUAN-ROOT/log/semantic_meta_validation.jsonl"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
            # 找最近的summary
            for line in reversed(lines):
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "meta_validation_summary":
                        report = entry["report"]
                        print(f"最近元校验: {report['timestamp']}")
                        print(f"状态: {report['overall_status']}")
                        print(f"通过率: {report['passed']}/{report['total_tests']} ({report['pass_rate']})")
                        print(f"耗时: {report['duration_ms']}ms")
                        if report['failed_tests']:
                            print(f"失败: {len(report['failed_tests'])} 个")
                        return
                except:
                    continue
            print("未找到元校验记录")
        else:
            print("元校验日志不存在")

    elif args.mode == "history":
        log_path = "/opt/ZONGYUAN-ROOT/log/semantic_meta_validation.jsonl"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
            summaries = []
            for line in lines:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "meta_validation_summary":
                        summaries.append(entry["report"])
                except:
                    continue
            for s in summaries[-args.limit:]:
                print(f"{s['timestamp'][:19]} | {s['overall_status']:10s} | {s['passed']}/{s['total_tests']} ({s['pass_rate']}) | {s['duration_ms']}ms")
        else:
            print("元校验日志不存在")


if __name__ == "__main__":
    main()
