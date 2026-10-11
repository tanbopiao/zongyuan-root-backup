# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_entropy(probabilities: list) -> float:
    """熵值计算算子：计算概率分布的信息熵（香农熵）。

    参数:
        probabilities: 概率分布列表，其中每个概率值应在0和1之间，并且所有概率值之和应为1。

    返回:
        概率分布的信息熵值，类型为浮点数。
    """
    if not probabilities or any(p <= 0 or p >= 1 for p in probabilities) or not sum(probabilities) == 1:
        raise ValueError("Invalid probabilities: probabilities must sum to 1 and be in the range (0, 1).")
    
    result = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return result