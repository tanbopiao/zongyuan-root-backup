# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=2 | score=85.8/A

def op_cosine_similarity(vec_a: list, vec_b: list) -> float:
    """余弦相似度算子：计算两个向量的余弦相似度。

    参数:
        vec_a: 第一个向量，数值列表
        vec_b: 第二个向量，数值列表

    返回:
        两个向量的余弦相似度，范围在[-1, 1]之间
    """
    if not vec_a or not vec_b:
        raise ValueError("Vectors must be non-empty.")
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must be of the same length.")
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a**2 for a in vec_a)**0.5
    norm_b = sum(b**2 for b in vec_b)**0.5
    
    if norm_a == 0 or norm_b == 0:
        raise ValueError("One of the vectors has a norm of zero, cannot compute cosine similarity.")
    
    return dot_product / (norm_a * norm_b)