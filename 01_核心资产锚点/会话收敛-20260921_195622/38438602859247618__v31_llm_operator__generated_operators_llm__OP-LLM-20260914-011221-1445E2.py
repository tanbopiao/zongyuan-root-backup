# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=2 | score=87.5/A

def op_top_k(data: list, k: int) -> list:
    """Top-K选择算子：从数据中选出最大的K个元素。

    参数:
        data: 数值列表
        k: 需要选择的元素数量（正整数）

    返回:
        最大的K个元素列表，如果数据长度小于K，则返回所有元素
    """
    if not data or k <= 0:
        return []
    if k >= len(data):
        return sorted(data, reverse=True)
    return sorted(data, key=lambda x: -x)[:k]