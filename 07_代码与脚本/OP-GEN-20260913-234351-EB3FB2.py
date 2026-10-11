# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.0-META-CLOSED-LOOP
# AUTO-GENERATED OPERATOR

def op_data_validate(record: dict, required_fields: list) -> tuple:
    """数据校验算子：校验记录字典是否包含必填字段且值非空。
        参数:
            record: 待校验字典
            required_fields: 必填字段名列表
        返回:
            (ok, missing_fields) 元组
"""
    if not isinstance(record, dict):
        return False, ['__not_a_dict__']
    missing = [f for f in required_fields if f not in record or record[f] in (None, '')]
    return (len(missing) == 0), missing

