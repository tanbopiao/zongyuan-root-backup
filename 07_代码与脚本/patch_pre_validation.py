#!/usr/bin/env python3
"""
为unified_gateway添加记忆网关写入前置校验拦截
拦截 /api/truth/upsert，先进行语义校验，通过后再写入
"""
FILE = "/opt/ZONGYUAN-ROOT/engine/scripts/unified_gateway_9120.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 在do_POST中，在"其他路径交给记忆网关处理"之前添加前置校验拦截
old_post_tail = '''        # 其他路径交给记忆网关处理
        super().do_POST()'''

new_post_tail = '''        # 记忆网关写入前置校验拦截
        if path == "/api/truth/upsert":
            self._handle_truth_upsert_with_validation()
            return

        # 其他路径交给记忆网关处理
        super().do_POST()'''

content = content.replace(old_post_tail, new_post_tail)

# 在语义校验处理方法之后添加前置校验处理方法
preval_handler = '''
    def _handle_truth_upsert_with_validation(self):
        """
        记忆网关真值写入前置校验
        1. 读取请求体
        2. 提取文本字段进行语义校验（术语提取+L0约束）
        3. 校验通过则交给记忆网关处理，不通过则返回422
        """
        body = self._read_body()
        key = body.get("key", "")
        value = body.get("value", "")
        category = body.get("category", "")
        node_id = body.get("node_id", "unknown")

        # 提取需要校验的文本内容
        text_to_validate = ""
        if isinstance(value, str):
            text_to_validate = value
        elif isinstance(value, dict):
            text_to_validate = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, list):
            text_to_validate = json.dumps(value, ensure_ascii=False)

        # 如果有描述字段也加入校验
        if body.get("description"):
            text_to_validate += " " + body["description"]
        if body.get("summary"):
            text_to_validate += " " + body["summary"]

        validation_result = {
            "skipped": False,
            "semantic_check": None,
            "l0_check": None,
            "issues": []
        }

        # 只有当文本内容足够长且包含中文字符时才进行校验
        if _semantic_available and len(text_to_validate) >= 5 and any('\\u4e00' <= c <= '\\u9fff' for c in text_to_validate):
            try:
                # 1. 语义术语提取校验
                sem_result = _semantic_validator.extract_and_validate_terms(text_to_validate)
                validation_result["semantic_check"] = {
                    "found": sem_result["total_found"],
                    "valid": sem_result["valid_count"],
                    "invalid": sem_result["invalid_count"],
                    "invalid_terms": sem_result["invalid_terms"],
                    "pass_rate": sem_result["pass_rate"]
                }

                # 2. L0约束校验（仅对包含描述性文本的内容）
                if len(text_to_validate) >= 10:
                    l0_result = _semantic_validator.validate_l0_constraints(text_to_validate)
                    validation_result["l0_check"] = {
                        "passed": l0_result["passed"],
                        "passed_count": l0_result["passed_count"],
                        "total_checks": l0_result["total_checks"],
                        "violation_count": l0_result["violation_count"],
                        "violations": l0_result["violations"],
                        "triage": l0_result["violation_triage"]
                    }

                    # L0严重违规则拒绝写入
                    if not l0_result["passed"] and l0_result["violation_count"] >= 3:
                        validation_result["issues"].append(
                            f"L0约束严重违规({l0_result['violation_count']}项)，分级: {l0_result['violation_triage']}"
                        )

                # 有未定义术语则警告但不拒绝（可能是新术语）
                if sem_result["invalid_count"] > 0:
                    validation_result["issues"].append(
                        f"发现{sem_result['invalid_count']}个未定义术语: {sem_result['invalid_terms']}"
                    )

            except Exception as e:
                validation_result["issues"].append(f"语义校验异常: {str(e)}")
        else:
            validation_result["skipped"] = True
            validation_result["issues"].append("文本内容过短或无中文，跳过语义校验")

        # 如果有严重问题则拒绝写入
        has_blocking_issue = any("严重违规" in issue or "L0约束" in issue and "严重" in issue for issue in validation_result["issues"])

        if has_blocking_issue:
            # 记录审计
            try:
                mg.db.add_audit_log(
                    "truth_upsert_rejected",
                    f"语义校验拒绝写入: key={key}, issues={validation_result['issues']}",
                    node_id
                )
            except:
                pass

            self._send_json_unified({
                "success": False,
                "error": "semantic_validation_failed",
                "key": key,
                "validation": validation_result,
                "message": "真值写入被语义校验拦截，请修正后重试"
            }, 422)
            return

        # 校验通过，交给记忆网关处理
        # 重新构造请求体（因为_read_body已经消费了rfile）
        # 注意：由于HTTP请求体只能读取一次，我们需要重新设置rfile
        # 这里直接调用记忆网关的数据库操作
        try:
            result = mg.db.upsert_truth(key, value, node_id, category)
            mg.db.add_audit_log(
                "truth_upsert_validated",
                f"语义校验通过后写入: key={key}, category={category}, validation_issues={len(validation_result['issues'])}",
                node_id
            )
            self._send_json_unified({
                "success": True,
                "action": result.get("action", "upsert"),
                "key": key,
                "validation": validation_result,
                "truth_count": mg.db.get_truth_count(),
                "message": "真值写入成功（已通过语义前置校验）"
            })
        except Exception as e:
            self._send_json_unified({
                "success": False,
                "error": str(e),
                "key": key
            }, 500)

'''

# 在"def _handle_comm_execute(self):"之前插入（如果还没插入的话，这里追加到语义校验方法后面）
# 找到语义校验方法的最后一个方法_handle_semantic_l0_check，在它后面插入
content = content.replace(
    "    def _handle_comm_execute(self):",
    preval_handler + "    def _handle_comm_execute(self):"
)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 前置校验拦截补丁已应用")
print(f"文件大小: {len(content)} bytes")
