"""
ZONGYUAN-ROOT API网关规范校验器
适配 MR-API-GLOBAL-INTEGRATION-V1.0 元法则
实现：鉴权校验、时间戳防重放、返回格式校验、任务模型校验、幂等控制、状态码规范
"""
import time
import hashlib
import json
from typing import Dict, Any, Tuple, Optional

# ============ 规范常量 ============
REQUIRED_HEADERS = [
    "X-ZONGYUAN-NODE-ID",
    "X-ZONGYUAN-SIGN",
    "X-TIMESTAMP",
    "Authorization",
]
TIMESTAMP_WINDOW = 30  # ±30秒防重放
VALID_TASK_TYPES = ["keyframe_gen", "video_render", "asset_archive", "data_sync", "global_lock"]
VALID_TASK_STATUS = ["pending", "running", "success", "failed", "cancel"]
VALID_STATUS_CODES = [200, 400, 401, 403, 404, 409, 429, 500, 502, 503]
REQUIRED_RESPONSE_FIELDS = ["code", "msg", "data", "trace_id", "timestamp"]
REQUIRED_TASK_FIELDS = ["task_id", "task_type", "status", "priority", "payload", "output_asset", "error_info", "callback_webhook", "creator_node"]


class APIGatewayValidator:
    """API网关规范校验器"""

    def __init__(self):
        self.processed_tasks = set()  # 幂等控制：已处理task_id
        self.audit_log = []

    def _audit(self, check_name: str, passed: bool, detail: str = ""):
        self.audit_log.append({
            "check": check_name,
            "passed": passed,
            "detail": detail,
            "timestamp": time.time(),
        })

    # ============ 1. 鉴权头校验 ============
    def validate_auth_headers(self, headers: Dict[str, str]) -> Tuple[bool, str]:
        """校验请求鉴权头完整性（API-AXIOM-03 统一鉴权可信公理）"""
        missing = [h for h in REQUIRED_HEADERS if h not in headers or not headers[h]]
        if missing:
            self._audit("auth_headers", False, f"缺失头: {missing}")
            return False, f"鉴权失败：缺失请求头 {missing}"
        # Authorization格式校验
        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._audit("auth_headers", False, "Authorization格式错误")
            return False, "鉴权失败：Authorization必须为Bearer格式"
        self._audit("auth_headers", True, "四重头校验通过")
        return True, "鉴权通过"

    # ============ 2. 时间戳防重放 ============
    def validate_timestamp(self, headers: Dict[str, str], current_time: Optional[float] = None) -> Tuple[bool, str]:
        """校验时间戳防重放（API-AXIOM-03）"""
        ts_str = headers.get("X-TIMESTAMP", "")
        try:
            ts = float(ts_str)
        except (ValueError, TypeError):
            self._audit("timestamp", False, "时间戳格式错误")
            return False, "时间戳格式错误"
        now = current_time if current_time else time.time()
        if abs(now - ts) > TIMESTAMP_WINDOW:
            self._audit("timestamp", False, f"时间戳超出±{TIMESTAMP_WINDOW}s窗口")
            return False, f"请求过期：时间戳超出±{TIMESTAMP_WINDOW}秒防重放窗口"
        self._audit("timestamp", True, "时间戳校验通过")
        return True, "时间戳有效"

    # ============ 3. 节点签名校验（模拟） ============
    def validate_node_sign(self, headers: Dict[str, str]) -> Tuple[bool, str]:
        """校验节点Ed25519签名（模拟实现，实际对接签名验证库）"""
        node_id = headers.get("X-ZONGYUAN-NODE-ID", "")
        sign = headers.get("X-ZONGYUAN-SIGN", "")
        if not node_id or not sign:
            self._audit("node_sign", False, "节点ID或签名为空")
            return False, "节点签名校验失败"
        # 模拟：签名长度校验（实际应为Ed25519验签）
        if len(sign) < 32:
            self._audit("node_sign", False, "签名长度不足")
            return False, "节点签名长度不足"
        self._audit("node_sign", True, f"节点{node_id}签名校验通过")
        return True, "节点签名有效"

    # ============ 4. 返回格式校验 ============
    def validate_response_format(self, response: Dict[str, Any]) -> Tuple[bool, str]:
        """校验全局返回结构体（API-AXIOM-04 统一格式归一公理）"""
        missing = [f for f in REQUIRED_RESPONSE_FIELDS if f not in response]
        if missing:
            self._audit("response_format", False, f"缺失字段: {missing}")
            return False, f"返回格式错误：缺失字段 {missing}"
        # 状态码规范
        code = response.get("code")
        if code not in VALID_STATUS_CODES:
            self._audit("response_format", False, f"非法状态码: {code}")
            return False, f"非法状态码: {code}"
        # trace_id非空
        if not response.get("trace_id"):
            self._audit("response_format", False, "trace_id为空")
            return False, "trace_id不能为空"
        self._audit("response_format", True, "返回格式校验通过")
        return True, "返回格式合规"

    # ============ 5. 任务模型校验 ============
    def validate_task_model(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        """校验全局任务模型（API-AXIOM-04）"""
        missing = [f for f in REQUIRED_TASK_FIELDS if f not in task]
        if missing:
            self._audit("task_model", False, f"缺失字段: {missing}")
            return False, f"任务模型错误：缺失字段 {missing}"
        # task_type枚举
        if task["task_type"] not in VALID_TASK_TYPES:
            self._audit("task_model", False, f"非法task_type: {task['task_type']}")
            return False, f"非法任务类型: {task['task_type']}"
        # status枚举
        if task["status"] not in VALID_TASK_STATUS:
            self._audit("task_model", False, f"非法status: {task['status']}")
            return False, f"非法任务状态: {task['status']}"
        # task_id非空
        if not task["task_id"]:
            self._audit("task_model", False, "task_id为空")
            return False, "task_id不能为空"
        self._audit("task_model", True, f"任务{task['task_id']}模型校验通过")
        return True, "任务模型合规"

    # ============ 6. 幂等性校验 ============
    def check_idempotency(self, task_id: str) -> Tuple[bool, str]:
        """幂等防重校验（API-AXIOM-06 幂等防重安全公理）"""
        if task_id in self.processed_tasks:
            self._audit("idempotency", False, f"任务{task_id}重复提交")
            return False, f"幂等拦截：任务{task_id}已处理，重复提交被拒绝"
        self.processed_tasks.add(task_id)
        self._audit("idempotency", True, f"任务{task_id}首次提交")
        return True, "幂等校验通过"

    # ============ 7. 全链路鉴权（组合校验） ============
    def full_auth_check(self, headers: Dict[str, str]) -> Tuple[bool, str]:
        """全链路鉴权：头完整性+时间戳+节点签名"""
        ok, msg = self.validate_auth_headers(headers)
        if not ok:
            return False, msg
        ok, msg = self.validate_timestamp(headers)
        if not ok:
            return False, msg
        ok, msg = self.validate_node_sign(headers)
        if not ok:
            return False, msg
        return True, "全链路鉴权通过"

    # ============ 8. 任务提交全流程 ============
    def submit_task(self, headers: Dict[str, str], task: Dict[str, Any]) -> Dict[str, Any]:
        """任务提交全流程：鉴权→任务模型→幂等→处理"""
        trace_id = hashlib.sha256(f"{task.get('task_id','')}{time.time()}".encode()).hexdigest()[:16]
        # 鉴权
        auth_ok, auth_msg = self.full_auth_check(headers)
        if not auth_ok:
            return {"code": 401, "msg": auth_msg, "data": {}, "trace_id": trace_id, "timestamp": int(time.time())}
        # 任务模型
        task_ok, task_msg = self.validate_task_model(task)
        if not task_ok:
            return {"code": 400, "msg": task_msg, "data": {}, "trace_id": trace_id, "timestamp": int(time.time())}
        # 幂等
        idem_ok, idem_msg = self.check_idempotency(task["task_id"])
        if not idem_ok:
            return {"code": 409, "msg": idem_msg, "data": {"task_id": task["task_id"]}, "trace_id": trace_id, "timestamp": int(time.time())}
        # 成功
        self._audit("task_submit", True, f"任务{task['task_id']}提交成功")
        return {
            "code": 200,
            "msg": "任务提交成功",
            "data": {"task_id": task["task_id"], "status": "pending", "priority": task["priority"]},
            "trace_id": trace_id,
            "timestamp": int(time.time()),
        }

    def get_audit_report(self) -> Dict[str, Any]:
        """生成审计报告"""
        total = len(self.audit_log)
        passed = sum(1 for l in self.audit_log if l["passed"])
        failed = total - passed
        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%" if total else "N/A",
            "details": self.audit_log,
        }
