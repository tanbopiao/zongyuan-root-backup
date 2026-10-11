"""
API网关规范单元测试
覆盖 MR-API-GLOBAL-INTEGRATION-V1.0 全部12条公理的校验逻辑
正向用例 + 反向用例全覆盖
"""
import sys
import time
import json
import unittest
from api_gateway_validator import APIGatewayValidator, REQUIRED_HEADERS


def make_valid_headers(ts_offset=0):
    """生成合法请求头"""
    return {
        "X-ZONGYUAN-NODE-ID": "NODE-TEST-001",
        "X-ZONGYUAN-SIGN": "a" * 64,  # 模拟64位签名
        "X-TIMESTAMP": str(int(time.time()) + ts_offset),
        "Authorization": "Bearer test-token-12345",
    }


def make_valid_task(task_id="TASK-TEST-001"):
    """生成合法任务模型"""
    return {
        "task_id": task_id,
        "task_type": "keyframe_gen",
        "status": "pending",
        "priority": 1,
        "payload": {"prompt": "test", "style": "国风"},
        "output_asset": [],
        "error_info": {},
        "callback_webhook": "https://example.com/callback",
        "creator_node": "NODE-TEST-001",
    }


def make_valid_response():
    """生成合法返回体"""
    return {
        "code": 200,
        "msg": "success",
        "data": {"result": "ok"},
        "trace_id": "trace-abc123",
        "timestamp": int(time.time()),
    }


class TestAuthHeaders(unittest.TestCase):
    """API-AXIOM-03 统一鉴权可信公理 - 鉴权头校验"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_valid_headers_pass(self):
        """正向：完整四重头通过"""
        ok, msg = self.v.validate_auth_headers(make_valid_headers())
        self.assertTrue(ok, msg)

    def test_missing_node_id_fail(self):
        """反向：缺失X-ZONGYUAN-NODE-ID被拒"""
        h = make_valid_headers()
        del h["X-ZONGYUAN-NODE-ID"]
        ok, msg = self.v.validate_auth_headers(h)
        self.assertFalse(ok)
        self.assertIn("X-ZONGYUAN-NODE-ID", msg)

    def test_missing_sign_fail(self):
        """反向：缺失签名被拒"""
        h = make_valid_headers()
        del h["X-ZONGYUAN-SIGN"]
        ok, _ = self.v.validate_auth_headers(h)
        self.assertFalse(ok)

    def test_missing_timestamp_fail(self):
        """反向：缺失时间戳被拒"""
        h = make_valid_headers()
        del h["X-TIMESTAMP"]
        ok, _ = self.v.validate_auth_headers(h)
        self.assertFalse(ok)

    def test_missing_auth_fail(self):
        """反向：缺失Authorization被拒"""
        h = make_valid_headers()
        del h["Authorization"]
        ok, _ = self.v.validate_auth_headers(h)
        self.assertFalse(ok)

    def test_bad_auth_format_fail(self):
        """反向：Authorization非Bearer格式被拒"""
        h = make_valid_headers()
        h["Authorization"] = "Basic abc"
        ok, msg = self.v.validate_auth_headers(h)
        self.assertFalse(ok)
        self.assertIn("Bearer", msg)

    def test_empty_header_value_fail(self):
        """反向：头值为空被拒"""
        h = make_valid_headers()
        h["X-ZONGYUAN-NODE-ID"] = ""
        ok, _ = self.v.validate_auth_headers(h)
        self.assertFalse(ok)


class TestTimestamp(unittest.TestCase):
    """API-AXIOM-03 时间戳防重放"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_valid_timestamp_pass(self):
        """正向：当前时间戳通过"""
        h = make_valid_headers()
        ok, _ = self.v.validate_timestamp(h)
        self.assertTrue(ok)

    def test_expired_timestamp_fail(self):
        """反向：过期时间戳（60秒前）被拒"""
        h = make_valid_headers(ts_offset=-60)
        ok, msg = self.v.validate_timestamp(h)
        self.assertFalse(ok)
        self.assertIn("防重放", msg)

    def test_future_timestamp_fail(self):
        """反向：未来时间戳（60秒后）被拒"""
        h = make_valid_headers(ts_offset=60)
        ok, _ = self.v.validate_timestamp(h)
        self.assertFalse(ok)

    def test_invalid_timestamp_format_fail(self):
        """反向：非数字时间戳被拒"""
        h = make_valid_headers()
        h["X-TIMESTAMP"] = "not-a-number"
        ok, _ = self.v.validate_timestamp(h)
        self.assertFalse(ok)

    def test_boundary_timestamp_pass(self):
        """边界：±29秒内通过"""
        h = make_valid_headers(ts_offset=-29)
        ok, _ = self.v.validate_timestamp(h)
        self.assertTrue(ok)


class TestNodeSign(unittest.TestCase):
    """节点签名校验"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_valid_sign_pass(self):
        """正向：合法签名通过"""
        h = make_valid_headers()
        ok, _ = self.v.validate_node_sign(h)
        self.assertTrue(ok)

    def test_short_sign_fail(self):
        """反向：签名过短被拒"""
        h = make_valid_headers()
        h["X-ZONGYUAN-SIGN"] = "short"
        ok, _ = self.v.validate_node_sign(h)
        self.assertFalse(ok)

    def test_empty_node_id_fail(self):
        """反向：空节点ID被拒"""
        h = make_valid_headers()
        h["X-ZONGYUAN-NODE-ID"] = ""
        ok, _ = self.v.validate_node_sign(h)
        self.assertFalse(ok)


class TestResponseFormat(unittest.TestCase):
    """API-AXIOM-04 统一格式归一公理 - 返回格式校验"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_valid_response_pass(self):
        """正向：合法返回体通过"""
        ok, _ = self.v.validate_response_format(make_valid_response())
        self.assertTrue(ok)

    def test_missing_code_fail(self):
        """反向：缺失code被拒"""
        r = make_valid_response()
        del r["code"]
        ok, _ = self.v.validate_response_format(r)
        self.assertFalse(ok)

    def test_missing_trace_id_fail(self):
        """反向：缺失trace_id被拒"""
        r = make_valid_response()
        del r["trace_id"]
        ok, _ = self.v.validate_response_format(r)
        self.assertFalse(ok)

    def test_empty_trace_id_fail(self):
        """反向：trace_id为空被拒"""
        r = make_valid_response()
        r["trace_id"] = ""
        ok, _ = self.v.validate_response_format(r)
        self.assertFalse(ok)

    def test_invalid_status_code_fail(self):
        """反向：非法状态码被拒"""
        r = make_valid_response()
        r["code"] = 999
        ok, _ = self.v.validate_response_format(r)
        self.assertFalse(ok)

    def test_all_valid_codes_pass(self):
        """正向：所有合法状态码通过"""
        for code in [200, 400, 401, 403, 404, 409, 429, 500, 502, 503]:
            r = make_valid_response()
            r["code"] = code
            ok, _ = self.v.validate_response_format(r)
            self.assertTrue(ok, f"状态码{code}应通过")


class TestTaskModel(unittest.TestCase):
    """API-AXIOM-04 任务模型校验"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_valid_task_pass(self):
        """正向：合法任务模型通过"""
        ok, _ = self.v.validate_task_model(make_valid_task())
        self.assertTrue(ok)

    def test_missing_task_id_fail(self):
        """反向：缺失task_id被拒"""
        t = make_valid_task()
        del t["task_id"]
        ok, _ = self.v.validate_task_model(t)
        self.assertFalse(ok)

    def test_invalid_task_type_fail(self):
        """反向：非法task_type被拒"""
        t = make_valid_task()
        t["task_type"] = "invalid_type"
        ok, _ = self.v.validate_task_model(t)
        self.assertFalse(ok)

    def test_all_valid_task_types_pass(self):
        """正向：所有合法task_type通过"""
        for tt in ["keyframe_gen", "video_render", "asset_archive", "data_sync", "global_lock"]:
            t = make_valid_task()
            t["task_type"] = tt
            ok, _ = self.v.validate_task_model(t)
            self.assertTrue(ok, f"任务类型{tt}应通过")

    def test_invalid_status_fail(self):
        """反向：非法status被拒"""
        t = make_valid_task()
        t["status"] = "unknown"
        ok, _ = self.v.validate_task_model(t)
        self.assertFalse(ok)

    def test_all_valid_status_pass(self):
        """正向：所有合法status通过"""
        for s in ["pending", "running", "success", "failed", "cancel"]:
            t = make_valid_task()
            t["status"] = s
            ok, _ = self.v.validate_task_model(t)
            self.assertTrue(ok, f"状态{s}应通过")

    def test_empty_task_id_fail(self):
        """反向：空task_id被拒"""
        t = make_valid_task()
        t["task_id"] = ""
        ok, _ = self.v.validate_task_model(t)
        self.assertFalse(ok)


class TestIdempotency(unittest.TestCase):
    """API-AXIOM-06 幂等防重安全公理"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_first_submit_pass(self):
        """正向：首次提交通过"""
        ok, _ = self.v.check_idempotency("TASK-IDEM-001")
        self.assertTrue(ok)

    def test_duplicate_submit_fail(self):
        """反向：重复提交被幂等拦截"""
        self.v.check_idempotency("TASK-IDEM-002")
        ok, msg = self.v.check_idempotency("TASK-IDEM-002")
        self.assertFalse(ok)
        self.assertIn("幂等", msg)

    def test_different_tasks_pass(self):
        """正向：不同task_id互不影响"""
        ok1, _ = self.v.check_idempotency("TASK-A")
        ok2, _ = self.v.check_idempotency("TASK-B")
        self.assertTrue(ok1)
        self.assertTrue(ok2)


class TestFullAuth(unittest.TestCase):
    """全链路鉴权组合校验"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_full_auth_pass(self):
        """正向：全链路鉴权通过"""
        ok, msg = self.v.full_auth_check(make_valid_headers())
        self.assertTrue(ok, msg)

    def test_full_auth_fail_bad_timestamp(self):
        """反向：时间戳过期导致全链路失败"""
        h = make_valid_headers(ts_offset=-100)
        ok, _ = self.v.full_auth_check(h)
        self.assertFalse(ok)

    def test_full_auth_fail_missing_header(self):
        """反向：缺失头导致全链路失败"""
        h = make_valid_headers()
        del h["Authorization"]
        ok, _ = self.v.full_auth_check(h)
        self.assertFalse(ok)


class TestTaskSubmitFlow(unittest.TestCase):
    """任务提交全流程集成测试"""

    def setUp(self):
        self.v = APIGatewayValidator()

    def test_successful_submit(self):
        """正向：合法请求+合法任务提交成功，返回200"""
        result = self.v.submit_task(make_valid_headers(), make_valid_task("TASK-FLOW-001"))
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["data"]["status"], "pending")
        self.assertIn("trace_id", result)

    def test_submit_unauthorized(self):
        """反向：无鉴权提交返回401"""
        h = make_valid_headers()
        del h["Authorization"]
        result = self.v.submit_task(h, make_valid_task("TASK-FLOW-002"))
        self.assertEqual(result["code"], 401)

    def test_submit_invalid_task(self):
        """反向：非法任务模型返回400"""
        t = make_valid_task("TASK-FLOW-003")
        t["task_type"] = "bad_type"
        result = self.v.submit_task(make_valid_headers(), t)
        self.assertEqual(result["code"], 400)

    def test_submit_duplicate_idempotent(self):
        """反向：重复提交返回409幂等拦截"""
        t = make_valid_task("TASK-FLOW-004")
        r1 = self.v.submit_task(make_valid_headers(), t)
        self.assertEqual(r1["code"], 200)
        r2 = self.v.submit_task(make_valid_headers(), t)
        self.assertEqual(r2["code"], 409)

    def test_submit_response_format_compliant(self):
        """正向：提交返回体符合全局返回格式规范"""
        result = self.v.submit_task(make_valid_headers(), make_valid_task("TASK-FLOW-005"))
        ok, _ = self.v.validate_response_format(result)
        self.assertTrue(ok)


class TestAuditReport(unittest.TestCase):
    """审计报告生成"""

    def test_audit_report_generation(self):
        """正向：审计报告正确生成"""
        v = APIGatewayValidator()
        v.validate_auth_headers(make_valid_headers())
        v.validate_timestamp(make_valid_headers())
        report = v.get_audit_report()
        self.assertEqual(report["total_checks"], 2)
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 0)
        self.assertIn("pass_rate", report)

    def test_audit_report_with_failures(self):
        """正向：含失败用例的审计报告正确"""
        v = APIGatewayValidator()
        v.validate_auth_headers(make_valid_headers())  # pass
        h = make_valid_headers()
        del h["Authorization"]
        v.validate_auth_headers(h)  # fail
        report = v.get_audit_report()
        self.assertEqual(report["total_checks"], 2)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 1)


if __name__ == "__main__":
    # 运行测试并输出详细结果
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))

    # 输出汇总
    print("\n" + "=" * 60)
    print("API网关规范单元测试汇总")
    print("=" * 60)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"总用例数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%" if total else "N/A")
    print(f"测试结果: {'✅ 全部通过' if failed == 0 else '❌ 存在失败'}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
