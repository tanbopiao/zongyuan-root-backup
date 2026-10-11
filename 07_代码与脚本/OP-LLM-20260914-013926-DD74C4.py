# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_deduplicate(data: list) -> list:
    """去重算子：去除列表中的重复元素并保持原顺序。

    参数:
        data: 列表，可能包含重复元素

    返回:
        一个新的列表，去除了重复元素但保持原有顺序
    """
    if not data:
        return []
    seen = set()
    result = []
    for item in data:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result