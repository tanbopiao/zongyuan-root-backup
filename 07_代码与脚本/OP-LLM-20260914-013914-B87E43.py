# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=89.2/A

def op_median(data: list) -> Any:
    """中位数计算算子：返回数据序列的中位数。

    参数:
        data: 数值列表

    返回:
        数据序列的中位数，如果数据为空或非数值列表，则返回 None
    """
    if not data:
        return None
    try:
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 1:
            return sorted_data[n // 2]
        else:
            return (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
    except TypeError:
        return None