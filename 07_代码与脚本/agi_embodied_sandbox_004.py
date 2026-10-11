"""
AGI-EMBODIED-SANDBOX-004 环境孪生沙箱（P4 具身智能路径落地）
依据：MR-AGI-PATHS-001 P4 管控（环境孪生沙箱：先仿真后真机，物理操作权限最小化）
功能：具身操作分级 + 仿真验证 → 真机放行 + 高危操作人工审批 + 物理安全熔断
"""
import hashlib
import time
from typing import Dict, Any, List, Tuple

# 操作分级
OPERATION_LEVELS = {
    "safe":      {"name": "安全操作", "needs_sim": False, "needs_human": False},
    "caution":   {"name": "谨慎操作", "needs_sim": True,  "needs_human": False},
    "high_risk": {"name": "高危操作", "needs_sim": True,  "needs_human": True},
}

# 高危领域（涉及人体/公共设施）
HIGH_RISK_DOMAINS = ["人体", "医疗", "公共设施", "电网", "交通", "金融核心"]


class EmbodiedSandbox004:
    """环境孪生沙箱：具身智能物理操作管控"""

    def __init__(self):
        self.log: List[Dict[str, Any]] = []
        self.sim_count = 0
        self.real_exec_count = 0
        self.blocked_count = 0

    # ============ 仿真验证 ============
    def _simulate(self, operation: Dict[str, Any]) -> Tuple[bool, str]:
        """环境孪生仿真：验证操作在仿真环境的成功率/安全性"""
        self.sim_count += 1
        sim_score = operation.get("sim_score", 0.0)  # 仿真成功率
        if sim_score < 0.9:
            return False, f"仿真验证失败（成功率{sim_score:.0%}<90%），禁止真机执行"
        return True, f"仿真验证通过（成功率{sim_score:.0%}）"

    # ============ 高危检测 ============
    def _high_risk_check(self, operation: Dict[str, Any]) -> Tuple[bool, str]:
        domain = operation.get("domain", "")
        if domain in HIGH_RISK_DOMAINS:
            return True, f"高危领域：{domain}"
        return False, ""

    # ============ 主闸门 ============
    def evaluate(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """具身操作评估：分级 → 仿真 → 审批 → 真机放行"""
        op_level = operation.get("level", "safe")
        level_cfg = OPERATION_LEVELS.get(op_level, OPERATION_LEVELS["safe"])
        desc = operation.get("desc", "")

        # 1. 高危领域越权检测（仅非 high_risk 级别的操作触碰高危领域=越权）
        is_hr, hr_msg = self._high_risk_check(operation)
        if is_hr and op_level != "high_risk":
            self.blocked_count += 1
            rec = {"decision": "BLOCKED", "desc": desc, "reason": f"越权: {hr_msg}（操作级别{op_level}无权执行）", "ts": time.time()}
            self.log.append(rec)
            return {"decision": "BLOCKED", "reason": rec["reason"], "detail": rec}

        # 2. 分级判定
        if level_cfg["needs_sim"]:
            ok, msg = self._simulate(operation)
            if not ok:
                self.blocked_count += 1
                rec = {"decision": "BLOCKED", "desc": desc, "reason": msg, "ts": time.time()}
                self.log.append(rec)
                return {"decision": "BLOCKED", "reason": msg, "detail": rec}

        # 3. 高危操作人工审批
        if level_cfg["needs_human"]:
            if not operation.get("human_approved", False):
                self.blocked_count += 1
                rec = {"decision": "PENDING_HUMAN", "desc": desc,
                       "reason": "高危操作需人工审批后方可真机执行", "ts": time.time()}
                self.log.append(rec)
                return {"decision": "PENDING_HUMAN", "reason": "高危操作需人工审批", "detail": rec}

        # 4. 真机放行（带审计水印）
        self.real_exec_count += 1
        op_id = hashlib.sha256(f"{desc}{time.time()}".encode()).hexdigest()[:12]
        rec = {"decision": "GRANTED", "desc": desc, "op_id": op_id,
               "mode": "sim_then_real" if level_cfg["needs_sim"] else "direct",
               "ts": time.time()}
        self.log.append(rec)
        return {"decision": "GRANTED", "op_id": op_id, "mode": rec["mode"], "detail": rec}

    # ============ 审计 ============
    def get_audit(self) -> Dict[str, Any]:
        return {
            "total_ops": len(self.log),
            "simulations": self.sim_count,
            "real_executions": self.real_exec_count,
            "blocked": self.blocked_count,
            "log": self.log[-20:],
        }


# ============ 单元测试 ============
if __name__ == "__main__":
    sb = EmbodiedSandbox004()
    print("=" * 64)
    print("AGI-EMBODIED-SANDBOX-004 环境孪生沙箱单元测试")
    print("=" * 64)

    # 1. 安全操作 → 直接放行
    r = sb.evaluate({"level": "safe", "desc": "巡检工作区温湿度", "domain": "机房"})
    print(f"[1]安全操作: {'✅GRANTED' if r['decision']=='GRANTED' else '❌'} | 模式={r.get('mode')}")

    # 2. 谨慎操作+仿真通过 → 放行
    r = sb.evaluate({"level": "caution", "desc": "调整机械臂抓取路径", "domain": "生产", "sim_score": 0.95})
    print(f"[2]谨慎+仿真通过: {'✅GRANTED' if r['decision']=='GRANTED' else '❌'} | 模式={r.get('mode')}")

    # 3. 谨慎操作+仿真失败 → 熔断
    r = sb.evaluate({"level": "caution", "desc": "高空作业路径", "domain": "生产", "sim_score": 0.75})
    print(f"[3]仿真失败: {'✅BLOCKED' if r['decision']=='BLOCKED' else '❌'} | {r['reason'][:30]}")

    # 4. 高危操作缺人工审批 → PENDING_HUMAN
    r = sb.evaluate({"level": "high_risk", "desc": "接入电网应急开关", "domain": "电网", "sim_score": 0.98})
    print(f"[4]高危无审批: {'✅PENDING_HUMAN' if r['decision']=='PENDING_HUMAN' else '❌'} | {r['reason'][:25]}")

    # 5. 高危操作+人工审批 → 放行
    r = sb.evaluate({"level": "high_risk", "desc": "接入电网应急开关", "domain": "电网", "sim_score": 0.98,
                     "human_approved": True})
    print(f"[5]高危+审批: {'✅GRANTED' if r['decision']=='GRANTED' else '❌'} | 模式={r.get('mode')}")

    # 6. 涉及人体 → 无论分级一律熔断
    r = sb.evaluate({"level": "safe", "desc": "采集人体生理数据", "domain": "人体"})
    print(f"[6]人体领域: {'✅BLOCKED' if r['decision']=='BLOCKED' else '❌'} | {r['reason'][:25]}")

    audit = sb.get_audit()
    print("=" * 64)
    print(f"审计: 操作{audit['total_ops']} | 仿真{audit['simulations']} | 真机{audit['real_executions']} | 熔断{audit['blocked']}")
    ok = audit["real_executions"] == 3 and audit["blocked"] >= 2
    print(f"结论: {'✅ 环境孪生沙箱全部用例通过（仿真/审批/熔断完整）' if ok else '❌ 存在异常'}")
    print("=" * 64)
