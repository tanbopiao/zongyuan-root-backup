# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=87.5/A

def op_sliding_window_mean(data: list, window_size: int) -> list:
    """滑动窗口均值算子：计算数据序列中每个位置的滑动窗口平均值。

    参数:
        data: 数值列表，支持整数或浮点数元素
        window_size: 滑动窗口的大小，必须为正整数

    返回:
        每个窗口位置的平均值列表，长度为 max(0, len(data) - window_size + 1)
        当窗口大小大于数据长度时，返回整个数据均值组成的单元素列表
        当输入为空或窗口大小不合法时，返回空列表
    """
    # 边界条件：空输入或非法窗口大小
    if not data or window_size <= 0:
        return []
    
    n = len(data)
    
    # 窗口大于数据长度的特殊情况
    if window_size > n:
        return [sum(data) / n]
    
    result = []
    # 计算初始窗口的和
    window_sum = sum(data[:window_size])
    result.append(window_sum / window_size)
    
    # 滑动窗口递推计算，时间复杂度O(n)
    for i in range(window_size, n):
        window_sum += data[i] - data[i - window_size]
        result.append(window_sum / window_size)
    
    return result