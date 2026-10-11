# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=89.2/A

def op_variance(data: list) -> Any:
    """方差计算算子：计算数据序列的总体方差。

    参数:
        data: 数值列表

    返回:
        总体方差，如果输入为空或包含非数值类型，则返回 None
    """
    if not data or not all(isinstance(x, (int, float)) for x in data):
        return None
    n = len(data)
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    return variance