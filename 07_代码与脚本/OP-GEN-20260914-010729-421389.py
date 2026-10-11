# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.0-META-CLOSED-LOOP
# AUTO-GENERATED OPERATOR

def op_anomaly_detect(data: list) -> list:
    """异常检测算子：基于 3σ 法则识别数据序列中的异常点。
        参数:
            data: 数值列表
        返回:
            anomalies: 异常点列表
"""
    if not data:
        return []
    mean = sum(data) / len(data)
    var = sum((x - mean) ** 2 for x in data) / len(data)
    std = var ** 0.5
    threshold = 3 * std
    return [x for x in data if abs(x - mean) > threshold]

