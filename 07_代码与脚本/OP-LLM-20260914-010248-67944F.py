# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_sliding_window_mean(data: list, window_size: int) -> list:
    """滑动窗口均值算子：计算数据序列中每个位置的滑动窗口平均值。

    参数:
        data: 数值列表
        window_size: 窗口大小（正整数）

    返回:
        每个位置的窗口平均值列表，长度为 max(0, len(data) - window_size + 1)
    """
    if not data or window_size <= 0:
        return []
    n = len(data)
    if window_size > n:
        return [sum(data) / n]
    result = []
    window_sum = sum(data[:window_size])
    result.append(window_sum / window_size)
    for i in range(window_size, n):
        window_sum += data[i] - data[i - window_size]
        result.append(window_sum / window_size)
    return result