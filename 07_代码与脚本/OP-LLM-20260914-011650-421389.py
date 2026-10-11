# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_z_score_normalize(data: list) -> list:
    """Z-Score标准化算子：将数据序列标准化为均值0标准差1。

    参数:
        data: 数值列表

    返回:
        标准化后的数据列表
    """
    if not data:
        return []
    mean = sum(data) / len(data)
    std_dev = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    if std_dev == 0:
        return [0] * len(data)
    result = [(x - mean) / std_dev for x in data]
    return result