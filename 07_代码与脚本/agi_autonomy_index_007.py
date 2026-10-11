"""
AGI-AUTONOMY-INDEX-007 恒一约束层自治指数评估器（P7 路径落地）
依据：MR-AGI-PATHS-001 P7 管控（四构件持续深化+季度安全基线评审）
功能：量化评估体系自治稳态（元法则覆盖/真值锚定/锁档完整/风险熔断），输出自治指数与等级
"""
from typing import Dict, Any, List, Tuple

# 自治等级（对应自治内核 SKILL 标准）
AUTONOMY_LEVELS = [
    (0.8, "永恒自治", "四构件全绿，系统自洽可永续进化"),
    (0.6, "高级自治", "四构件健全，自主闭环稳定"),
    (0.4, "中级自治", "核心构件到位，部分依赖人工"),
    (0.2, "初级自治", "基础机制建立，需持续干预"),
    (0.0, "他律系统", "依赖外部驱动，无自主闭环"),
]


class AutonomyIndexEvaluator007:
    """自治指数评估器：四构件评分 → 自治指数 → 等级判定"""

    def __init__(self):
        self.components = {
            "meta_rule_coverage": {"name": "元法则覆盖度", "weight": 0.25},
            "truth_anchoring": {"name": "真值锚定率", "weight": 0.25},
            "lock_integrity": {"name": "锁档完整度", "weight": 0.25},
            "risk_response": {"name": "风险熔断响应", "weight": 0.25},
        }
        self.eval_history = []

    # ============ 单构件评分（0-1） ============
    def _component_score(self, comp_id: str, metrics: Dict[str, Any]) -> float:
        """根据构件指标计算得分"""
        if comp_id == "meta_rule_coverage":
            # 元法则覆盖：已生效规则 / 应覆盖规则
            active = metrics.get("active_rules", 0)
            required = metrics.get("required_rules", 1)
            return min(active / required, 1.0)
        if comp_id == "truth_anchoring":
            # 真值锚定：已同步真值 / 应同步真值
            synced = metrics.get("synced_truths", 0)
            total = metrics.get("total_truths", 1)
            return min(synced / total, 1.0)
        if comp_id == "lock_integrity":
            # 锁档完整：已锁档资产 / 全部资产
            locked = metrics.get("locked_assets", 0)
            all_assets = metrics.get("total_assets", 1)
            return min(locked / all_assets, 1.0)
        if comp_id == "risk_response":
            # 风险熔断：已闭环风险 / 全部风险
            resolved = metrics.get("resolved_risks", 0)
            total_risks = metrics.get("total_risks", 1)
            return min(resolved / total_risks, 1.0)
        return 0.0

    # ============ 主评估 ============
    def evaluate(self, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """四构件评估 → 自治指数 → 等级"""
        scores = {}
        for comp_id, comp in self.components.items():
            score = self._component_score(comp_id, metrics.get(comp_id, {}))
            scores[comp_id] = {"name": comp["name"], "score": round(score, 3)}

        # 加权自治指数
        index = sum(scores[cid]["score"] * self.components[cid]["weight"] for cid in scores)

        # 等级判定
        level_name, level_desc = "他律系统", "依赖外部驱动"
        for threshold, name, desc in AUTONOMY_LEVELS:
            if index >= threshold:
                level_name, level_desc = name, desc
                break

        result = {
            "autonomy_index": round(index, 3),
            "autonomy_percent": f"{index*100:.1f}%",
            "level": level_name,
            "level_desc": level_desc,
            "components": scores,
            "verdict": "PASS" if index >= 0.4 else "WARN",
            "timestamp": __import__("time").time(),
        }
        self.eval_history.append(result)
        return result

    def get_trend(self) -> Dict[str, Any]:
        """历史评估趋势"""
        if len(self.eval_history) < 2:
            return {"has_trend": False}
        prev, curr = self.eval_history[-2], self.eval_history[-1]
        delta = curr["autonomy_index"] - prev["autonomy_index"]
        return {"has_trend": True, "delta": round(delta, 3), "direction": "上升" if delta > 0 else "下降" if delta < 0 else "平稳"}


# ============ 单元测试 ============
if __name__ == "__main__":
    ev = AutonomyIndexEvaluator007()
    print("=" * 64)
    print("AGI-AUTONOMY-INDEX-007 恒一约束自治指数评估器单元测试")
    print("=" * 64)

    # 1. 初级自治状态（机制初建，各构件约0.3）
    m1 = {
        "meta_rule_coverage": {"active_rules": 3, "required_rules": 10},
        "truth_anchoring": {"synced_truths": 300, "total_truths": 1000},
        "lock_integrity": {"locked_assets": 10, "total_assets": 36},
        "risk_response": {"resolved_risks": 2, "total_risks": 5},
    }
    r1 = ev.evaluate(m1)
    print(f"[1]初级自治: 指数{r1['autonomy_percent']} | 等级[{r1['level']}] | 判定{r1['verdict']}")

    # 2. 中级自治（各构件约0.5）
    m2 = {
        "meta_rule_coverage": {"active_rules": 5, "required_rules": 10},
        "truth_anchoring": {"synced_truths": 500, "total_truths": 1000},
        "lock_integrity": {"locked_assets": 18, "total_assets": 36},
        "risk_response": {"resolved_risks": 3, "total_risks": 5},
    }
    r2 = ev.evaluate(m2)
    print(f"[2]中级自治: 指数{r2['autonomy_percent']} | 等级[{r2['level']}] | 判定{r2['verdict']}")

    # 3. 高级自治（各构件约0.7）
    m3 = {
        "meta_rule_coverage": {"active_rules": 7, "required_rules": 10},
        "truth_anchoring": {"synced_truths": 700, "total_truths": 1000},
        "lock_integrity": {"locked_assets": 25, "total_assets": 36},
        "risk_response": {"resolved_risks": 4, "total_risks": 5},
    }
    r3 = ev.evaluate(m3)
    print(f"[3]高级自治: 指数{r3['autonomy_percent']} | 等级[{r3['level']}] | 判定{r3['verdict']}")

    # 4. 永恒自治（各构件0.9）
    m4 = {
        "meta_rule_coverage": {"active_rules": 9, "required_rules": 10},
        "truth_anchoring": {"synced_truths": 900, "total_truths": 1000},
        "lock_integrity": {"locked_assets": 32, "total_assets": 36},
        "risk_response": {"resolved_risks": 5, "total_risks": 5},
    }
    r4 = ev.evaluate(m4)
    print(f"[4]永恒自治: 指数{r4['autonomy_percent']} | 等级[{r4['level']}] | 判定{r4['verdict']}")

    # 5. 构件明细
    print(f"[5]构件明细: " + " | ".join(f"{v['name']}={v['score']}" for v in r3["components"].values()))

    # 6. 趋势评估
    trend = ev.get_trend()
    print(f"[6]趋势: {'✅ ' + trend['direction'] + ' ' + str(trend['delta']) if trend['has_trend'] else '样本不足'}")

    print("=" * 64)
    ok = r1["level"] == "初级自治" and r2["level"] == "中级自治" and r3["level"] == "高级自治" and r4["level"] == "永恒自治"
    print(f"结论: {'✅ 自治指数评估器全部用例通过（四等级判定正确）' if ok else '❌ 存在异常'}")
    print("=" * 64)
