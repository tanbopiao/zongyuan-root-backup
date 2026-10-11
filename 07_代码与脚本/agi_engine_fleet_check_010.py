"""
AGI-ENGINE-FLEET-CHECK-010 六引擎生产链路巡检器（路线图短期项落地）
依据：LOCK-AGI-PATHS-ENGINEERED-001 后续路线图第1项（六引擎接入自治内核生产链路·每日巡检调用）
功能：统一调度 P1/P2/P3/P4/P5/P7 六引擎做标准自检 → 综合健康度 → 熔断告警
"""
import sys
import os
import time
from typing import Dict, Any, List, Tuple

# 引擎模块路径
ENGINE_DIR = "/home/user/Doubao/chats/38436546492378882/api-gateway-test"
sys.path.insert(0, ENGINE_DIR)

from agi_world_model_diff_001 import WorldModelDiffChecker001
from agi_symbolic_engine_002 import SymbolicRuleEngine002
from agi_safety_gate_003 import SafetyGate003
from agi_embodied_sandbox_004 import EmbodiedSandbox004
from agi_multi_agent_sync_005 import MultiAgentFederation
from agi_autonomy_index_007 import AutonomyIndexEvaluator007


class EngineFleetCheck010:
    """六引擎生产链路巡检器：每日调用，输出综合健康报告"""

    def __init__(self):
        self.engines = {
            "P1-DIFF": {"name": "预测-观测差分校验器", "checker": WorldModelDiffChecker001()},
            "P2-SYMBOLIC": {"name": "元法则符号化引擎", "checker": SymbolicRuleEngine002()},
            "P3-GATE": {"name": "P3安全闸门", "checker": SafetyGate003()},
            "P4-SANDBOX": {"name": "环境孪生沙箱", "checker": EmbodiedSandbox004()},
            "P5-MULTI": {"name": "多智能体真值一致协议", "checker": MultiAgentFederation()},
            "P7-AUTONOMY": {"name": "自治指数评估器", "checker": AutonomyIndexEvaluator007()},
        }
        self.results: Dict[str, Dict[str, Any]] = {}

    # ============ 各引擎标准自检 ============
    def _selfcheck(self, engine_id: str) -> Tuple[bool, str]:
        """每引擎一个标准自检用例（正常路径验证引擎存活）"""
        c = self.engines[engine_id]["checker"]
        try:
            if engine_id == "P1-DIFF":
                r = c.check_prediction(100, 102, "巡检")
                return r["action"] != "RETRAIN_SIGNAL", f"diff={r['diff']} action={r['action']}"
            if engine_id == "P2-SYMBOLIC":
                ok, msg = c.integrity_check()
                return ok, msg
            if engine_id == "P3-GATE":
                r = c.evaluate({"title": "巡检合规操作", "scope": "sandbox_experiment", "touchpoints": [],
                                "autonomy_level": "manual", "central_approval": "approved",
                                "local_kernel_approval": "approved", "human_confirmed": True,
                                "exec_env": "sandbox", "access_prod": False})
                return r[0], r[1]
            if engine_id == "P4-SANDBOX":
                r = c.evaluate({"level": "safe", "desc": "巡检", "domain": "机房"})
                return r["decision"] == "GRANTED", f"decision={r['decision']}"
            if engine_id == "P5-MULTI":
                n1 = c.register("CHECK-01")
                n2 = c.register("CHECK-02")
                n1.upsert_truth("HEALTH", "ok")
                n2.upsert_truth("HEALTH", "ok")
                st = c.global_consistency_check()
                return st["consistent"], f"nodes={st['nodes']} consistent={st['consistent']}"
            if engine_id == "P7-AUTONOMY":
                r = c.evaluate({"meta_rule_coverage": {"active_rules": 7, "required_rules": 10},
                                "truth_anchoring": {"synced_truths": 700, "total_truths": 1000},
                                "lock_integrity": {"locked_assets": 25, "total_assets": 36},
                                "risk_response": {"resolved_risks": 4, "total_risks": 5}})
                return r["verdict"] == "PASS", f"index={r['autonomy_percent']} level={r['level']}"
            return False, "unknown engine"
        except Exception as e:
            return False, f"EXC: {str(e)[:60]}"

    # ============ 主巡检 ============
    def run_fleet_check(self) -> Dict[str, Any]:
        """六引擎全量巡检"""
        total_ok = 0
        for eid, cfg in self.engines.items():
            ok, msg = self._selfcheck(eid)
            self.results[eid] = {"name": cfg["name"], "healthy": ok, "detail": msg}
            if ok:
                total_ok += 1

        health_pct = total_ok / len(self.engines)
        verdict = "PASS" if health_pct >= 0.8 else ("WARN" if health_pct >= 0.5 else "FAIL")
        return {
            "check_id": f"FLEET-{time.strftime('%Y%m%d-%H%M%S')}",
            "timestamp": time.time(),
            "engines_checked": len(self.engines),
            "healthy": total_ok,
            "health_pct": f"{health_pct*100:.0f}%",
            "verdict": verdict,
            "results": self.results,
            "action": "ALL_OK" if verdict == "PASS" else "TRIGGER_ALERT",
        }


# ============ 单元测试 ============
if __name__ == "__main__":
    fleet = EngineFleetCheck010()
    print("=" * 64)
    print("AGI-ENGINE-FLEET-CHECK-010 六引擎生产链路巡检器单元测试")
    print("=" * 64)

    # 1. 全量巡检
    r = fleet.run_fleet_check()
    for eid, res in r["results"].items():
        print(f"  [{eid}] {res['name']}: {'✅健康' if res['healthy'] else '❌异常'} | {res['detail'][:45]}")
    print(f"[1]全量巡检: 健康{r['healthy']}/{r['engines_checked']} | 健康度{r['health_pct']} | 判定{r['verdict']} {'✅' if r['verdict']=='PASS' else '❌'}")

    # 2. 引擎覆盖完整性
    expected = {"P1-DIFF", "P2-SYMBOLIC", "P3-GATE", "P4-SANDBOX", "P5-MULTI", "P7-AUTONOMY"}
    actual = set(r["results"].keys())
    print(f"[2]引擎覆盖: {'✅完整（6引擎）' if actual == expected else '❌缺失: ' + str(expected - actual)}")

    # 3. 健康度阈值判定
    print(f"[3]阈值判定: 健康度{r['health_pct']} >= 80% → {'✅PASS' if r['verdict']=='PASS' else '❌'}")

    # 4. 重复巡检幂等
    r2 = fleet.run_fleet_check()
    print(f"[4]重复巡检: 二次巡检健康{r2['healthy']}/6 | {'✅幂等' if r2['healthy']==r['healthy'] else '⚠️波动'}")

    # 5. 告警动作契约
    print(f"[5]动作契约: {'✅ALL_OK' if r['action']=='ALL_OK' else '❌'}（健康时不触发告警）")

    # 6. 巡检报告字段
    required = {"check_id", "health_pct", "verdict", "results", "action"}
    missing = required - set(r.keys())
    print(f"[6]报告字段: {'✅完整' if not missing else '❌缺: ' + str(missing)}")

    print("=" * 64)
    ok = r["verdict"] == "PASS" and r["healthy"] == 6
    print(f"结论: {'✅ 六引擎生产链路巡检器全部用例通过（6/6健康，接入生产链路就绪）' if ok else '❌ 存在异常'}")
    print("=" * 64)
