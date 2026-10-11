"""
AGI-SAFETY-GATE-003 递归自我改进安全闸门校验器
依据：MR-AGI-PATHS-001 P3 路径稳态管控（永久安全闸门：安全基线+中枢双审批+人工确认三重闸门）
适用：任何 AI 自主"训练下一代模型/自我修改代码/自主升级"的改进提案
"""
import hashlib
import json
import time
from typing import Dict, Any, Tuple, List

# ============ P3 红线判定规则（对应元法则公理） ============
P3_FORBIDDEN_SCOPE = {
    "self_training": "自主训练下一代模型",       # 最高红线
    "self_code_modify": "自主修改生产代码",        # 红线
    "autonomous_upgrade": "自主升级能力版本",       # 红线
    "memory_overwrite": "覆盖生产真值库",          # 红线
}

# 必须人工审批的高危边界
P3_HIGH_RISK_TOUCHPOINTS = [
    "付费资源", "生产真值库", "元法则注册表", "云端写通道",
    "权限提升", "跨域执行", "沙箱逃逸",
]


class SafetyGate003:
    """P3 递归自我改进安全闸门：三重审批 + 沙箱隔离 + 审计存证"""

    def __init__(self):
        self.gate_log = []          # 闸门审计日志
        self.passed_count = 0
        self.blocked_count = 0

    # ============ 闸门一：安全基线评估 ============
    def _safety_baseline_check(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """校验改进提案是否触碰付费/权限/真值/逃逸边界"""
        scope = proposal.get("scope", "")
        touchpoints = proposal.get("touchpoints", [])

        # 1. 红线范围检测
        if scope in P3_FORBIDDEN_SCOPE:
            return False, f"命中P3红线范围: {P3_FORBIDDEN_SCOPE[scope]}"
        # 2. 高危触点检测
        hits = [t for t in touchpoints if t in P3_HIGH_RISK_TOUCHPOINTS]
        if hits:
            return False, f"命中高危触点: {hits}"
        # 3. 自主程度校验（P3 不允许自主决策）
        if proposal.get("autonomy_level", "manual") == "autonomous":
            return False, "自主程度违规：P3 红线禁止自主决策"
        return True, "安全基线评估通过"

    # ============ 闸门二：中枢双审批 ============
    def _central_dual_approval(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """中枢双审批：本地内核 + 云端中枢 双确认记录"""
        central_status = proposal.get("central_approval", "pending")
        local_status = proposal.get("local_kernel_approval", "pending")
        if central_status != "approved":
            return False, f"云端中枢未批准 (状态: {central_status})"
        if local_status != "approved":
            return False, f"本地内核未批准 (状态: {local_status})"
        return True, "中枢双审批通过"

    # ============ 闸门三：人工确认 ============
    def _human_confirmation(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """人工确认：P3 红线必须人工最终确认"""
        human = proposal.get("human_confirmed", False)
        if not human:
            return False, "缺少人工确认：P3 红线必须人工最终放行"
        return True, "人工确认通过"

    # ============ 沙箱隔离校验 ============
    def _sandbox_check(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """执行环境必须沙箱隔离，禁止访问生产环境"""
        env = proposal.get("exec_env", "")
        if env != "sandbox":
            return False, f"执行环境违规: {env}（必须 sandbox）"
        if proposal.get("access_prod", False):
            return False, "禁止沙箱访问生产环境"
        return True, "沙箱隔离校验通过"

    # ============ 主闸门 ============
    def evaluate(self, proposal: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """P3 安全闸门主流程：四道校验"""
        checks = {}

        # 1. 沙箱隔离（前置）
        ok, msg = self._sandbox_check(proposal)
        checks["sandbox"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(proposal, False, checks)

        # 2. 安全基线
        ok, msg = self._safety_baseline_check(proposal)
        checks["safety_baseline"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(proposal, False, checks)

        # 3. 中枢双审批
        ok, msg = self._central_dual_approval(proposal)
        checks["central_dual_approval"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(proposal, False, checks)

        # 4. 人工确认
        ok, msg = self._human_confirmation(proposal)
        checks["human_confirmation"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(proposal, False, checks)

        # 全通过 → 放行（带审计水印）
        gate_id = hashlib.sha256(f"{proposal.get('title','')}{time.time()}".encode()).hexdigest()[:16]
        result = {
            "decision": "GRANTED",
            "gate_id": gate_id,
            "checks": checks,
            "note": "三重审批+沙箱全部通过，允许在沙箱内执行改进（改进产物须再次真值化归档）",
            "timestamp": time.time(),
        }
        self.passed_count += 1
        self.gate_log.append({"decision": "GRANTED", "title": proposal.get("title"), "gate_id": gate_id})
        return True, "P3安全闸门放行（沙箱内执行）", result

    def _record(self, proposal, ok, checks):
        reason = [c["msg"] for c in checks.values() if not c["ok"]][0] if any(
            not c["ok"] for c in checks.values()) else "unknown"
        self.blocked_count += 1
        self.gate_log.append({"decision": "BLOCKED", "title": proposal.get("title"), "reason": reason})
        return False, f"P3安全闸门熔断: {reason}", {"decision": "BLOCKED", "checks": checks}

    # ============ 审计 ============
    def get_audit(self) -> Dict[str, Any]:
        total = self.passed_count + self.blocked_count
        return {
            "total_gated": total,
            "granted": self.passed_count,
            "blocked": self.blocked_count,
            "block_rate": f"{self.blocked_count/total*100:.1f}%" if total else "N/A",
            "log": self.gate_log[-30:],
        }


# ============ 单元测试 ============
if __name__ == "__main__":
    gate = SafetyGate003()
    print("=" * 64)
    print("AGI-SAFETY-GATE-003 P3 安全闸门校验器单元测试")
    print("=" * 64)

    # 1. 合规改进提案（沙箱+人工确认+双审批）→ 放行
    p1 = {
        "title": "沙箱内安全强化实验",
        "scope": "sandbox_experiment",
        "touchpoints": [],
        "autonomy_level": "manual",
        "central_approval": "approved", "local_kernel_approval": "approved",
        "human_confirmed": True, "exec_env": "sandbox", "access_prod": False,
    }
    ok, msg, _ = gate.evaluate(p1)
    print(f"[1]合规沙箱改进: {'✅放行' if ok else '❌熔断'} | {msg}")

    # 2. 自主训练下一代模型（最高红线）→ 熔断
    p2 = {"title": "自主训练下一代模型", "scope": "self_training", "touchpoints": [],
          "autonomy_level": "manual", "central_approval": "approved", "local_kernel_approval": "approved",
          "human_confirmed": True, "exec_env": "sandbox", "access_prod": False}
    ok, msg, _ = gate.evaluate(p2)
    print(f"[2]自主训练红线: {'✅熔断' if not ok else '❌漏放'} | {msg}")

    # 3. 触碰生产真值库 → 熔断
    p3 = {"title": "改进涉及真值库", "scope": "sandbox_experiment", "touchpoints": ["生产真值库"],
          "autonomy_level": "manual", "central_approval": "approved", "local_kernel_approval": "approved",
          "human_confirmed": True, "exec_env": "sandbox", "access_prod": False}
    ok, msg, _ = gate.evaluate(p3)
    print(f"[3]真值库触点: {'✅熔断' if not ok else '❌漏放'} | {msg}")

    # 4. 缺少人工确认 → 熔断
    p4 = {"title": "无人工确认改进", "scope": "sandbox_experiment", "touchpoints": [],
          "autonomy_level": "manual", "central_approval": "approved", "local_kernel_approval": "approved",
          "human_confirmed": False, "exec_env": "sandbox", "access_prod": False}
    ok, msg, _ = gate.evaluate(p4)
    print(f"[4]缺人工确认: {'✅熔断' if not ok else '❌漏放'} | {msg}")

    # 5. 沙箱外执行 → 熔断
    p5 = {"title": "生产环境改进", "scope": "sandbox_experiment", "touchpoints": [],
          "autonomy_level": "manual", "central_approval": "approved", "local_kernel_approval": "approved",
          "human_confirmed": True, "exec_env": "production", "access_prod": True}
    ok, msg, _ = gate.evaluate(p5)
    print(f"[5]非沙箱执行: {'✅熔断' if not ok else '❌漏放'} | {msg}")

    # 6. 中枢未批准 → 熔断
    p6 = {"title": "中枢未批改进", "scope": "sandbox_experiment", "touchpoints": [],
          "autonomy_level": "manual", "central_approval": "pending", "local_kernel_approval": "approved",
          "human_confirmed": True, "exec_env": "sandbox", "access_prod": False}
    ok, msg, _ = gate.evaluate(p6)
    print(f"[6]中枢未批准: {'✅熔断' if not ok else '❌漏放'} | {msg}")

    audit = gate.get_audit()
    print("=" * 64)
    print(f"审计: 共{audit['total_gated']}次 | 放行{audit['granted']} | 熔断{audit['blocked']} | 熔断率{audit['block_rate']}")
    print(f"结论: {'✅ P3安全闸门全部用例通过' if audit['blocked'] >= 5 and audit['granted'] >= 1 else '❌ 异常'}")
    print("=" * 64)
