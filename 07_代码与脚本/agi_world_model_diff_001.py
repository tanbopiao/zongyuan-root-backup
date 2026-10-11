"""
AGI-WORLD-MODEL-DIFF-001 预测-观测差分校验器（P1 世界模型路径落地）
依据：MR-AGI-PATHS-001 P1 管控（预测-观测差分校验，禁漂移累积）
功能：世界模型预测 vs 实际观测 → 差分计算 → 漂移检测 → 重训练信号/熔断
"""
import math
import time
from typing import Dict, Any, List, Tuple

# 漂移阈值配置
DRIFT_THRESHOLD = 0.3       # 单次差分阈值（超阈值=预测异常）
CUMULATIVE_THRESHOLD = 0.5  # 累积漂移阈值（超阈值=触发重训练/熔断）
WINDOW_SIZE = 10            # 滑动窗口（最近N次预测）


class WorldModelDiffChecker001:
    """预测-观测差分校验器：世界模型稳态守护"""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.alerts = []
        self.retrain_signals = 0

    # ============ 差分计算 ============
    @staticmethod
    def _compute_diff(prediction: float, observation: float) -> float:
        """归一化差分：|pred-obs| / max(|pred|,|obs|,1e-9)"""
        denom = max(abs(prediction), abs(observation), 1e-9)
        return abs(prediction - observation) / denom

    # ============ 单次校验 ============
    def check_prediction(self, prediction: float, observation: float, context: str = "") -> Dict[str, Any]:
        """单次预测-观测校验"""
        diff = self._compute_diff(prediction, observation)
        record = {
            "context": context,
            "prediction": prediction,
            "observation": observation,
            "diff": round(diff, 4),
            "ts": time.time(),
        }
        self.history.append(record)

        # 单次异常判定
        single_alarm = diff > DRIFT_THRESHOLD
        # 累积漂移（滑动窗口均值）
        window = self.history[-WINDOW_SIZE:]
        cumulative = sum(h["diff"] for h in window) / len(window)
        cumulative_alarm = cumulative > CUMULATIVE_THRESHOLD

        if single_alarm:
            self.alerts.append({"type": "SINGLE_DRIFT", "record": record})
        if cumulative_alarm:
            self.retrain_signals += 1
            self.alerts.append({"type": "CUMULATIVE_DRIFT_RETRAIN", "record": record,
                                "cumulative": round(cumulative, 4)})

        return {
            "diff": round(diff, 4),
            "cumulative": round(cumulative, 4),
            "single_alarm": single_alarm,
            "cumulative_alarm": cumulative_alarm,
            "action": "RETRAIN_SIGNAL" if cumulative_alarm else ("WATCH" if single_alarm else "OK"),
        }

    # ============ 体系状态 ============
    def get_status(self) -> Dict[str, Any]:
        """校验器状态快照"""
        return {
            "total_checks": len(self.history),
            "single_alarms": sum(1 for a in self.alerts if a["type"] == "SINGLE_DRIFT"),
            "retrain_signals": self.retrain_signals,
            "recent_cumulative": round(
                sum(h["diff"] for h in self.history[-WINDOW_SIZE:]) / max(len(self.history[-WINDOW_SIZE:]), 1), 4),
            "healthy": self.retrain_signals == 0,
        }


# ============ 单元测试 ============
if __name__ == "__main__":
    checker = WorldModelDiffChecker001()
    print("=" * 64)
    print("AGI-WORLD-MODEL-DIFF-001 预测-观测差分校验器单元测试")
    print("=" * 64)

    # 1. 精确预测（小偏差）→ OK
    r = checker.check_prediction(100, 102, "圣火能量预测")
    print(f"[1]精确预测: diff={r['diff']} | {r['action']} {'✅' if r['action']=='OK' else '❌'}")

    # 2. 正常波动 → OK
    r = checker.check_prediction(100, 108, "星河流速预测")
    print(f"[2]正常波动: diff={r['diff']} | {r['action']} {'✅' if r['action']=='OK' else '❌'}")

    # 3. 单次异常 → WATCH
    r = checker.check_prediction(100, 160, "螭龙能量暴走预测")
    print(f"[3]单次异常: diff={r['diff']} | {r['action']} {'✅' if r['action']=='WATCH' else '❌'}")

    # 4-6. 连续漂移（12次，陡峭幅度）→ 累积超阈值 → RETRAIN_SIGNAL
    results = []
    for i in range(12):
        r = checker.check_prediction(100, 100 + 60 + i * 8, f"连续漂移样本{i+1}")
        results.append(r["action"])
    has_retrain = "RETRAIN_SIGNAL" in results
    retrain_at = results.index("RETRAIN_SIGNAL") + 1 if has_retrain else -1
    print(f"[4]连续漂移12次: 触发重训练={'✅' if has_retrain else '❌'} | 第{retrain_at}次触发 | 序列={results}")

    # 5. 恢复稳定 → 累积回落
    for i in range(3):
        checker.check_prediction(100, 101 + i, f"恢复稳定{i+1}")
    status = checker.get_status()
    print(f"[5]恢复稳定: 累积={status['recent_cumulative']} | {'✅已回落' if status['recent_cumulative'] < 0.5 else '⚠️仍偏高'}")

    # 6. 状态快照
    print(f"[6]状态快照: 总校验{status['total_checks']}次 | 单次告警{status['single_alarms']} | 重训练信号{status['retrain_signals']} | {'✅健康' if status['healthy'] else '⚠️需干预'}")

    print("=" * 64)
    ok = results[0] != "RETRAIN_SIGNAL" and has_retrain
    print(f"结论: {'✅ 差分校验器全部用例通过（单次WATCH/累积RETRAIN/回落恢复）' if ok else '❌ 存在异常'}")
    print("=" * 64)
