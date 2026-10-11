# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_entropy(probabilities: list) -> float:
    """熵值计算算子：计算概率分布的信息熵（香农熵）。

    参数:
        probabilities: 概率分布列表，其中每个元素必须大于等于0且总和为1

    返回:
        概率分布的信息熵，类型为 float
    """
    if not probabilities or not all(0 <= p <= 1 for p in probabilities) or not sum(probabilities) == 1:
        raise ValueError("Invalid probabilities input. All probabilities must be between 0 and 1, and their sum must be 1.")
    
    result = -sum(p * math.log(p, 2) for p in probabilities if p > 0)
    return result