#!/usr/bin/env python3
"""
为unified_gateway_9120.py添加语义校验API路由
/api/semantic/validate - 术语校验
/api/semantic/translate - 多模型转译
/api/semantic/reconcile - 资产对账
/api/semantic/l0-check - L0约束校验
/api/semantic/stats - 引擎统计(GET)
/api/semantic/audit - 审计日志(GET)
"""
import re

FILE = "/opt/ZONGYUAN-ROOT/engine/scripts/unified_gateway_9120.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 在导入部分添加semantic_validator
import_section = '''# ========== 导入语义校验引擎 ==========
sys.path.insert(0, "/opt/ZONGYUAN-ROOT/engine/scripts")
try:
    from semantic_validator import SemanticValidator
    _semantic_validator = SemanticValidator()
    _semantic_available = True
except Exception as e:
    print(f"[WARN] 语义校验引擎加载失败: {e}")
    _semantic_available = False

'''

# 在"# ========== 常量 =========="之前插入
content = content.replace(
    "# ========== 常量 ==========",
    import_section + "# ========== 常量 =========="
)

# 2. 在do_GET中添加语义校验路由（在super().do_GET()之前）
old_get = '''        # 其他路径交给记忆网关处理
        super().do_GET()'''

new_get = '''        # 语义校验API
        if path == "/api/semantic/stats":
            self._handle_semantic_stats()
            return
        if path == "/api/semantic/audit":
            self._handle_semantic_audit()
            return

        # 其他路径交给记忆网关处理
        super().do_GET()'''

content = content.replace(old_get, new_get)

# 3. 在do_POST中添加语义校验路由
old_post = '''        # 其他路径交给记忆网关处理
        super().do_POST()'''

new_post = '''        # 语义校验API
        if path == "/api/semantic/validate":
            self._handle_semantic_validate()
            return
        if path == "/api/semantic/translate":
            self._handle_semantic_translate()
            return
        if path == "/api/semantic/reconcile":
            self._handle_semantic_reconcile()
            return
        if path == "/api/semantic/l0-check":
            self._handle_semantic_l0_check()
            return

        # 其他路径交给记忆网关处理
        super().do_POST()'''

content = content.replace(old_post, new_post)

# 4. 在_handle_comm_execute方法之前添加语义校验处理方法
semantic_handlers = '''
    # ========== 语义校验API处理方法 ==========

    def _semantic_not_available(self):
        self._send_json_unified({"success": False, "error": "semantic_validator_not_available"}, 503)

    def _handle_semantic_stats(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            stats = _semantic_validator.get_stats()
            self._send_json_unified({"success": True, "data": stats})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

    def _handle_semantic_audit(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            limit = int(self.path.split("limit=")[-1]) if "limit=" in self.path else 100
            logs = _semantic_validator.get_audit_logs(limit)
            self._send_json_unified({"success": True, "logs": logs, "total": len(logs)})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

    def _handle_semantic_validate(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            body = self._read_body()
            term = body.get("term", "")
            context = body.get("context", "")
            if not term:
                self._send_json_unified({"success": False, "error": "term_required"}, 400)
                return
            result = _semantic_validator.validate_term(term, context)
            self._send_json_unified({"success": True, "data": result.to_dict()})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

    def _handle_semantic_translate(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            body = self._read_body()
            term = body.get("term", "")
            model = body.get("model", "agnes_image")
            apply_prefix = body.get("apply_prefix", False)
            apply_suffix = body.get("apply_suffix", False)
            if not term:
                self._send_json_unified({"success": False, "error": "term_required"}, 400)
                return
            result = _semantic_validator.translate_term(term, model, apply_prefix, apply_suffix)
            self._send_json_unified({"success": True, "data": result.to_dict()})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

    def _handle_semantic_reconcile(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            body = self._read_body()
            asset_id = body.get("asset_id", "")
            result = _semantic_validator.reconcile_asset(body, asset_id)
            self._send_json_unified({"success": True, "data": result.to_dict()})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

    def _handle_semantic_l0_check(self):
        if not _semantic_available:
            self._semantic_not_available()
            return
        try:
            body = self._read_body()
            text = body.get("text", "") or body.get("context", "")
            if not text:
                self._send_json_unified({"success": False, "error": "text_required"}, 400)
                return
            result = _semantic_validator.validate_l0_constraints(text)
            self._send_json_unified({"success": True, "data": result})
        except Exception as e:
            self._send_json_unified({"success": False, "error": str(e)}, 500)

'''

# 在"def _handle_comm_execute(self):"之前插入
content = content.replace(
    "    def _handle_comm_execute(self):",
    semantic_handlers + "    def _handle_comm_execute(self):"
)

# 5. 更新main函数中的路由打印信息
content = content.replace(
    '    print("  GET  /comm/audit    → COMM-GATEWAY审计日志")',
    '    print("  GET  /comm/audit    → COMM-GATEWAY审计日志")\n    print("  /api/semantic/*   → 语义校验引擎（校验/转译/对账/L0约束）")'
)

# 6. 更新健康检查中的endpoints，添加语义校验端点
content = content.replace(
    '''                    "endpoints": [
                        "GET /api/status",
                        "GET /api/truths",
                        "GET /api/truth/{key}",
                        "GET /api/nodes",
                        "GET /api/audit",
                        "POST /api/truth/upsert",
                        "POST /api/truth/sync",
                        "POST /api/node/register",
                        "POST /api/node/heartbeat",
                    ],''',
    '''                    "endpoints": [
                        "GET /api/status",
                        "GET /api/truths",
                        "GET /api/truth/{key}",
                        "GET /api/nodes",
                        "GET /api/audit",
                        "POST /api/truth/upsert",
                        "POST /api/truth/sync",
                        "POST /api/node/register",
                        "POST /api/node/heartbeat",
                        "GET /api/semantic/stats",
                        "GET /api/semantic/audit",
                        "POST /api/semantic/validate",
                        "POST /api/semantic/translate",
                        "POST /api/semantic/reconcile",
                        "POST /api/semantic/l0-check",
                    ],'''
)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 统一网关补丁已应用")
print(f"文件大小: {len(content)} bytes")
