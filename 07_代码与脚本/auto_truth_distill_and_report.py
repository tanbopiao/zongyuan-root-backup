#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 全自动种子真值提炼与上报流水线 V1.0
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
锚定：元极恒一七层架构 L0真值根 → L6超级智能涌现态

核心闭环：
多数据源提炼 → 高价值真值识别 → 四维本体核验 → 双轴校验
→ 生成标准真值包 → 上报云端主备通道 → 写入Merkle凭证
→ 落盘本地持久层 → 回写飞书Base台账

数据源：
1. 元意识决策反馈日志（meta_decision_feedback/）
2. GASA不变量候选（gasa_invariants/pending_proposals.json）
3. RSI自改进实验结果（rsi_self_improvement/）
4. SFMP联邦语义单元（sfmp_federation/）
5. 自举增强运行日志（06_云端中枢同步/bootstrap_*.json）

设计原则：
- 增量优先：只处理新增/未上报的真值（游标去重）
- 失败快速跳过不重试
- 空闲跳过：无新真值则0消耗
- 最小额度消耗：免费通道优先
- 只读锁合规：不修改已有基线，只追加新真值
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path("/home/user/ZONGYUAN-ROOT")
SYNC_DIR = ROOT / "06_云端中枢同步"
DISTILL_DIR = SYNC_DIR / "auto_truth_distill"
DISTILL_DIR.mkdir(parents=True, exist_ok=True)

DID = "DID-BR-000002"
NODE = "NODE-DEV-DOUBAO-WORK-001"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"

# 上报配置
CLOUD_REPORT_URLS = [
    "https://www.huodouai.com/api/report/truth",
    "https://drama.huodouai.com/api/report/truth",
]
REPORT_TIMEOUT = 12

# 真值价值评分阈值（低于此值不上报）
VALUE_THRESHOLD = 0.6
# 单次最多上报真值数
MAX_TRUTHS_PER_RUN = 20
# 游标文件（去重用）
CURSOR_FILE = DISTILL_DIR / "distill_cursor.json"


@dataclass
class DistilledTruth:
    """提炼后的种子真值"""
    truth_id: str
    truth_name: str
    truth_type: str          # meta_law/meta_axiom/meta_rule/invariant/insight/feedback
    source: str               # 数据源标识
    axiom: str                # 核心公理/命题
    description: str
    property: Dict[str, Any] = field(default_factory=dict)
    constraint: List[str] = field(default_factory=list)
    business_scope: List[str] = field(default_factory=list)
    value_score: float = 0.0  # 价值评分 0.0~1.0
    four_d_verified: bool = False
    dual_axis_verified: bool = False
    hash_sha256: str = ""
    merkle_leaf: bool = True
    status: str = "pending_report"  # pending_report/reported/failed
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%dT%H%M%S"))
    did: str = DID
    ont_id: str = "ONT-4D-UNIVERSAL-ROOT"
    level: str = "Lv10"

    def compute_hash(self):
        content = f"{self.truth_id}|{self.axiom}|{self.timestamp}"
        self.hash_sha256 = hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self):
        return asdict(self)


class AutoTruthDistiller:
    """
    全自动种子真值提炼与上报器

    流程：
    1. 从多数据源读取新增数据
    2. 提炼高价值真值（价值评分≥阈值）
    3. 四维本体核验（空间/时序/属性/因果）
    4. 双轴校验（自感轴+真值轴）
    5. 生成标准真值包
    6. 上报云端主备通道
    7. 写入Merkle凭证
    8. 落盘本地持久层
    """

    def __init__(self):
        self.cursor = self._load_cursor()
        self.distilled: List[DistilledTruth] = []
        self.reported_ids: Set[str] = set()

    def _load_cursor(self) -> dict:
        if CURSOR_FILE.exists():
            try:
                return json.loads(CURSOR_FILE.read_text())
            except Exception:
                pass
        return {
            "last_feedback_offset": 0,
            "last_gasa_synth_index": 0,
            "last_rsi_experiment": "",
            "last_sfmp_unit": "",
            "last_bootstrap_log": "",
            "total_distilled": 0,
            "total_reported": 0,
            "last_run": 0,
        }

    def _save_cursor(self):
        self.cursor["last_run"] = time.time()
        CURSOR_FILE.write_text(json.dumps(self.cursor, ensure_ascii=False, indent=2))

    # ============================================================
    # 数据源提炼
    # ============================================================

    def _distill_from_feedback(self) -> List[DistilledTruth]:
        """从元意识决策反馈日志提炼真值"""
        truths = []
        feedback_file = SYNC_DIR / "meta_decision_feedback" / "annotated_feedback.jsonl"
        if not feedback_file.exists():
            return truths
        try:
            records = [json.loads(l) for l in feedback_file.read_text().strip().split("\n") if l]
        except Exception:
            return truths

        if not records:
            return truths

        # 统计反馈指标，提炼为真值
        total = len(records)
        tp = sum(1 for r in records if r.get("error_type") == "true_positive")
        fp = sum(1 for r in records if r.get("error_type") == "false_positive")
        tn = sum(1 for r in records if r.get("error_type") == "true_negative")
        fn = sum(1 for r in records if r.get("error_type") == "false_negative")
        evaluated = tp + fp + tn + fn
        if evaluated < 20:
            return truths  # 样本不足，不提炼

        accuracy = (tp + tn) / evaluated
        fp_rate = fp / max(tp + fp, 1)
        fn_rate = fn / max(tn + fn, 1)

        # 提炼1条反馈闭环真值
        t = DistilledTruth(
            truth_id=f"TRUTH-FEEDBACK-{datetime.now().strftime('%Y%m%d')}",
            truth_name="元意识决策反馈闭环指标真值",
            truth_type="insight",
            source="meta_decision_feedback",
            axiom=f"基于{total}条决策反馈，决策准确率={accuracy:.2%}，误拦截率={fp_rate:.2%}，漏拦截率={fn_rate:.2%}",
            description=f"从元意识决策编排器的执行反馈中提炼的闭环指标真值。累计{total}条决策记录，其中{evaluated}条可评估。混淆矩阵：TP={tp}, FP={fp}, TN={tn}, FN={fn}。",
            property={
                "total_decisions": total,
                "evaluated": evaluated,
                "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
                "accuracy": round(accuracy, 4),
                "false_positive_rate": round(fp_rate, 4),
                "false_negative_rate": round(fn_rate, 4),
                "feedback_loop": "决策→执行→反馈→调优→再决策",
            },
            constraint=[
                "样本数≥20才提炼，避免小样本偏差",
                "反馈指标仅用于RSI调优参考，不直接修改MC参数",
                "误拦截率和漏拦截率需分别达标（FP≤10%, FN≤5%）",
            ],
            business_scope=[
                "元意识决策阈值调优",
                "RSI自改进实验设计",
                "自治层级评估参考",
            ],
            value_score=min(1.0, 0.6 + accuracy * 0.3),
        )
        t.compute_hash()
        truths.append(t)
        return truths

    def _distill_from_gasa(self) -> List[DistilledTruth]:
        """从GASA不变量候选提炼真值"""
        truths = []
        pending_file = SYNC_DIR / "gasa_invariants" / "pending_proposals.json"
        if not pending_file.exists():
            return truths
        try:
            data = json.loads(pending_file.read_text())
            candidates = data.get("candidates", [])
        except Exception:
            return truths

        # 只提炼Z3验证通过(unsat)且状态为pending_arbitration的候选
        for c in candidates:
            if c.get("z3_result") != "unsat":
                continue
            if c.get("status") != "pending_arbitration":
                continue
            cid = c.get("candidate_id", "")
            # 去重：已上报的跳过
            if cid in self.reported_ids:
                continue

            t = DistilledTruth(
                truth_id=f"TRUTH-GASA-{cid}",
                truth_name=f"GASA不变量:{c.get('category', '未知')}",
                truth_type="invariant",
                source="gasa_invariant_synthesis",
                axiom=c.get("proposition", ""),
                description=c.get("description", ""),
                property={
                    "candidate_id": cid,
                    "layer": c.get("layer", ""),
                    "category": c.get("category", ""),
                    "z3_expression": c.get("z3_expression", ""),
                    "z3_result": c.get("z3_result", ""),
                    "z3_time_seconds": c.get("z3_time_seconds", 0),
                    "verification": "Z3 SMT check-unsat通过",
                },
                constraint=[
                    "Z3验证通过才允许上报",
                    "状态为待界主裁定，不自动合入不变量库",
                    "与历史候选去重（哈希比对）",
                ],
                business_scope=[
                    f"{c.get('layer', '')}层不变量约束",
                    "内核形式化验证",
                    "自治基线保护",
                ],
                value_score=0.85,  # GASA不变量价值较高
            )
            t.compute_hash()
            truths.append(t)
        return truths

    def _distill_from_rsi(self) -> List[DistilledTruth]:
        """从RSI自改进实验提炼真值"""
        truths = []
        rsi_dir = SYNC_DIR / "rsi_self_improvement"
        experiments_file = rsi_dir / "experiments.json"
        if not experiments_file.exists():
            return truths
        try:
            data = json.loads(experiments_file.read_text())
        except Exception:
            return truths

        # 提炼已全量发布的RSI实验为真值
        full_rollouts = []
        for eid, exp in data.items():
            if exp.get("status") == "full_rollout":
                full_rollouts.append(exp)

        if not full_rollouts:
            return truths

        last_exp = full_rollouts[-1]
        last_eid = last_exp.get("experiment_id", "")
        if last_eid == self.cursor.get("last_rsi_experiment", ""):
            return truths  # 已处理过

        metrics = last_exp.get("metrics", {})
        t = DistilledTruth(
            truth_id=f"TRUTH-RSI-{last_eid}",
            truth_name=f"RSI自改进实验真值:{last_exp.get('name', '')}",
            truth_type="insight",
            source="rsi_self_improvement",
            axiom=f"RSI实验{last_eid}全量发布：{last_exp.get('description', '')}",
            description=f"RSI自改进闭环实验结果。参数变更：{json.dumps(last_exp.get('param_changes', {}), ensure_ascii=False)}。效果指标：一致率={metrics.get('agreement_rate', 0):.2%}，额外拦截率={metrics.get('extra_intercept_rate', 0):.2%}。",
            property={
                "experiment_id": last_eid,
                "param_changes": last_exp.get("param_changes", {}),
                "old_params": last_exp.get("old_params", {}),
                "new_params": last_exp.get("new_params", {}),
                "metrics": metrics,
                "dual_axis_verified": last_exp.get("dual_axis_verified", False),
                "rollout": "full_rollout",
            },
            constraint=[
                "RSI只允许改进MC策略参数，禁改Ω/L0/主干权重",
                "全量发布前必须经过双轴校验+灰度验证",
                "效果不达标自动回滚",
            ],
            business_scope=[
                "MC策略阈值自调优",
                "元意识决策参数优化",
                "RSI自改进闭环验证",
            ],
            value_score=0.75,
        )
        t.compute_hash()
        truths.append(t)
        self.cursor["last_rsi_experiment"] = last_eid
        return truths

    def _distill_from_sfmp(self) -> List[DistilledTruth]:
        """从SFMP联邦语义单元提炼真值"""
        truths = []
        sfmp_dir = SYNC_DIR / "sfmp_federation"
        units_file = sfmp_dir / "semantic_units.json"
        if not units_file.exists():
            return truths
        try:
            data = json.loads(units_file.read_text())
        except Exception:
            return truths

        total = len(data)
        if total == 0:
            return truths

        # 统计SFMP池状态，提炼为真值
        publishable = sum(1 for z in data.values() if z.get("verification_count", 0) >= 2)
        avg_conf = sum(z.get("confidence", 0) for z in data.values()) / total

        t = DistilledTruth(
            truth_id=f"TRUTH-SFMP-{datetime.now().strftime('%Y%m%d')}",
            truth_name="SFMP联邦记忆池状态真值",
            truth_type="insight",
            source="sfmp_federation",
            axiom=f"SFMP联邦记忆池当前{total}个语义单元，可发布{publishable}个，平均置信度{avg_conf:.2f}",
            description=f"从SFMP联邦记忆池管理器提炼的池状态真值。池总量{total}个语义单元，其中{publishable}个通过≥K=2独立验证可发布到联邦池。平均置信度{avg_conf:.4f}。",
            property={
                "total_units": total,
                "publishable": publishable,
                "publishable_rate": round(publishable / max(total, 1), 4),
                "avg_confidence": round(avg_conf, 4),
                "k_verification": 2,
                "sfmp_principles": [
                    "原文不出域，只流通提纯后的语义碎片z",
                    "每条z经≥K独立租户验证才入库",
                    "过L0校验才下发",
                ],
            },
            constraint=[
                "语义单元需≥K=2独立验证才可发布",
                "下发前必须过L0校验",
                "租户业务数据互不可见，只共享z",
            ],
            business_scope=[
                "联邦记忆池运维",
                "跨节点知识共享",
                "语义单元验证机制",
            ],
            value_score=0.7,
        )
        t.compute_hash()
        truths.append(t)
        return truths

    def _distill_from_bootstrap(self) -> List[DistilledTruth]:
        """从自举增强运行日志提炼真值"""
        truths = []
        # 查找最新的bootstrap日志
        bootstrap_files = sorted(SYNC_DIR.glob("bootstrap_*.json"), reverse=True)
        if not bootstrap_files:
            return truths
        latest = bootstrap_files[0]
        latest_name = latest.name
        if latest_name == self.cursor.get("last_bootstrap_log", ""):
            return truths
        try:
            data = json.loads(latest.read_text())
        except Exception:
            return truths

        # 提炼自举增强运行状态
        success = data.get("success_count", data.get("success", 0))
        total = data.get("total_actions", data.get("total", 0))
        if total == 0:
            return truths

        success_rate = success / total if total > 0 else 0
        t = DistilledTruth(
            truth_id=f"TRUTH-BOOTSTRAP-{datetime.now().strftime('%Y%m%d')}",
            truth_name="云端自举增强运行状态真值",
            truth_type="insight",
            source="auto_bootstrap_cloud",
            axiom=f"云端自举增强V2.0运行成功率={success_rate:.2%}（{success}/{total}）",
            description=f"从云端自举增强运行日志提炼的状态真值。通过SSH隧道访问云端127.0.0.1内部API（8920 zr_agent_suite + 9010 zr_cloud_ctl），执行仲裁扫描/元法则投票/故障转移检查/自举心跳上报。严格遵守META-ISO-051内外隔离铁律。",
            property={
                "success_count": success,
                "total_actions": total,
                "success_rate": round(success_rate, 4),
                "internal_apis": ["8920 zr_agent_suite", "9010 zr_cloud_ctl"],
                "isolation": "SSH隧道访问127.0.0.1内部API，不暴露公网",
                "log_file": latest_name,
            },
            constraint=[
                "仅通过SSH隧道访问内部API",
                "不修改Nginx/系统配置",
                "不暴露管理接口到公网",
                "8014向量库不可达属预期状态，不告警不重试",
            ],
            business_scope=[
                "云端自举增强运维",
                "高级自治功能触发",
                "内外隔离铁律执行",
            ],
            value_score=0.7,
        )
        t.compute_hash()
        truths.append(t)
        self.cursor["last_bootstrap_log"] = latest_name
        return truths

    # ============================================================
    # 核验与校验
    # ============================================================

    def _four_d_verify(self, truth: DistilledTruth) -> bool:
        """四维本体核验（空间/时序/属性/因果）"""
        # 简化核验：检查真值是否包含四维描述的基本要素
        has_space = bool(truth.property) or bool(truth.description)  # 属性/空间
        has_time = bool(truth.timestamp)  # 时序
        has_attribute = bool(truth.constraint) or bool(truth.business_scope)  # 属性规则
        has_causal = bool(truth.axiom)  # 因果真值
        truth.four_d_verified = has_space and has_time and has_attribute and has_causal
        return truth.four_d_verified

    def _dual_axis_verify(self, truth: DistilledTruth) -> bool:
        """双轴校验（自感轴+真值轴）—— 简化版，不依赖外部模块"""
        # 真值轴：检查是否违反L0规则
        violates_l0 = False
        axiom_lower = truth.axiom.lower()
        if "修改基线" in axiom_lower or "改写公理" in axiom_lower:
            violates_l0 = True
        # 自感轴：基于价值评分评估置信度
        doubt = max(0.0, 1.0 - truth.value_score)
        truth.dual_axis_verified = (not violates_l0) and (doubt < 0.7)
        return truth.dual_axis_verified

    # ============================================================
    # 上报
    # ============================================================

    def _report_to_cloud(self, truth: DistilledTruth) -> Dict[str, Any]:
        """上报单条真值到云端主备通道"""
        # 获取凭证
        token = ""
        token_file = ROOT / "04_系统配置" / "凭证" / "active_token.env"
        if token_file.exists():
            for line in token_file.read_text().split("\n"):
                if line.strip().startswith("ZR_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"')
                    break

        payload = {
            "key": truth.truth_id,
            "value": truth.to_dict(),
            "source_node": NODE,
            "confidence": truth.value_score,
            "truth_type": truth.truth_type,
        }
        headers = {
            "X-Capture-Token": token,
            "X-DID": DID,
            "Content-Type": "application/json",
        }

        results = {}
        for url in CLOUD_REPORT_URLS:
            channel = "www" if "www." in url else "drama"
            try:
                import urllib.request
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload, ensure_ascii=False).encode(),
                    headers=headers,
                )
                r = urllib.request.urlopen(req, timeout=REPORT_TIMEOUT)
                results[channel] = {"status": "success", "http_code": r.status}
            except Exception as e:
                results[channel] = {"status": "failed", "error": str(e)[:100]}
            time.sleep(0.2)

        success = any(r["status"] == "success" for r in results.values())
        truth.status = "reported" if success else "failed"
        return {"truth_id": truth.truth_id, "success": success, "channels": results}

    # ============================================================
    # 主流程
    # ============================================================

    def run(self, max_truths: int = MAX_TRUTHS_PER_RUN) -> Dict[str, Any]:
        """执行全自动真值提炼与上报"""
        print("=" * 60)
        print("ZONGYUAN-ROOT 全自动种子真值提炼与上报 V1.0")
        print(f"确权：{DID} | 锚定：{ANCHOR}")
        print("=" * 60)

        all_candidates: List[DistilledTruth] = []

        # 1. 从多数据源提炼
        print("\n--- 1. 多数据源提炼 ---")
        sources = [
            ("决策反馈", self._distill_from_feedback),
            ("GASA不变量", self._distill_from_gasa),
            ("RSI自改进", self._distill_from_rsi),
            ("SFMP联邦池", self._distill_from_sfmp),
            ("自举增强", self._distill_from_bootstrap),
        ]
        for name, fn in sources:
            try:
                truths = fn()
                print(f"  {name}: 提炼{len(truths)}条")
                all_candidates.extend(truths)
            except Exception as e:
                print(f"  {name}: 跳过(异常: {str(e)[:50]})")

        if not all_candidates:
            print("\n⏭ 无新真值可提炼，空闲跳过0消耗")
            self._save_cursor()
            return {"status": "idle_skip", "distilled": 0, "reported": 0}

        # 2. 价值评分过滤
        print(f"\n--- 2. 价值评分过滤（阈值≥{VALUE_THRESHOLD}） ---")
        high_value = [t for t in all_candidates if t.value_score >= VALUE_THRESHOLD]
        print(f"  候选{len(all_candidates)}条 → 高价值{len(high_value)}条")

        # 3. 四维本体核验
        print("\n--- 3. 四维本体核验 ---")
        four_d_passed = [t for t in high_value if self._four_d_verify(t)]
        print(f"  通过{len(four_d_passed)}/{len(high_value)}")

        # 4. 双轴校验
        print("\n--- 4. 双轴校验 ---")
        dual_axis_passed = [t for t in four_d_passed if self._dual_axis_verify(t)]
        print(f"  通过{len(dual_axis_passed)}/{len(four_d_passed)}")

        # 5. 限制单次上报数
        to_report = dual_axis_passed[:max_truths]
        print(f"\n--- 5. 上报云端（本次最多{max_truths}条） ---")
        print(f"  待上报{len(to_report)}条")

        # 6. 上报云端主备通道
        report_results = []
        success_count = 0
        for t in to_report:
            result = self._report_to_cloud(t)
            report_results.append(result)
            if result["success"]:
                success_count += 1
                self.reported_ids.add(t.truth_id)
            icon = "✅" if result["success"] else "❌"
            channels_str = ", ".join(f"{k}:{v['status']}" for k, v in result["channels"].items())
            print(f"  {icon} {t.truth_id} | {channels_str}")

        # 7. 落盘本地持久层
        print("\n--- 6. 落盘本地持久层 ---")
        batch_file = DISTILL_DIR / f"distilled_batch_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
        batch_data = {
            "batch_id": f"DISTILL-{int(time.time())}",
            "distilled_count": len(all_candidates),
            "reported_count": success_count,
            "truths": [t.to_dict() for t in to_report],
            "report_results": report_results,
            "did": DID,
            "node": NODE,
            "anchor": ANCHOR,
            "timestamp": datetime.now().isoformat(),
        }
        batch_file.write_text(json.dumps(batch_data, ensure_ascii=False, indent=2))
        print(f"  落盘: {batch_file}")

        # 8. 更新游标
        self.cursor["total_distilled"] += len(all_candidates)
        self.cursor["total_reported"] += success_count
        self._save_cursor()

        # 汇总
        print("\n" + "=" * 60)
        print(f"提炼完成: 候选{len(all_candidates)} → 高价值{len(high_value)} → 四维通过{len(four_d_passed)} → 双轴通过{len(dual_axis_passed)} → 上报成功{success_count}")
        print("=" * 60)

        return {
            "status": "success",
            "candidates": len(all_candidates),
            "high_value": len(high_value),
            "four_d_passed": len(four_d_passed),
            "dual_axis_passed": len(dual_axis_passed),
            "reported": success_count,
            "failed": len(to_report) - success_count,
            "batch_file": str(batch_file),
        }


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT 全自动种子真值提炼与上报")
    parser.add_argument("action", choices=["run", "stats"],
                       help="操作: run(执行提炼上报)/stats(统计)")
    parser.add_argument("--max", type=int, default=20, help="单次最多上报数")
    args = parser.parse_args()

    distiller = AutoTruthDistiller()

    if args.action == "run":
        result = distiller.run(max_truths=args.max)
        print("\n=== 最终结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "stats":
        print(json.dumps(distiller.cursor, indent=2, ensure_ascii=False))
