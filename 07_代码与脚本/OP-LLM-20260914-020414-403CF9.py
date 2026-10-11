# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · V3.1-LLM-OPERATOR-GEN
# LLM-GENERATED OPERATOR | model=doubao-reasoning2 | round=1 | score=89.2/A

import math
from typing import List, Any


def op_entropy_calculate(prob_dist: List[float], base: float = 2.0) -> Any:
    """熵值计算算子：计算给定概率分布的信息熵（香农熵）。

    信息熵是对系统不确定性的度量，公式为 H = -Σ(p_i * log_b(p_i))，
    其中 p_i 是第i个事件的发生概率，b 是对数底数。
    当概率为 0 时，约定 0 * log(0) = 0，不贡献熵值。

    参数:
        prob_dist: 概率分布列表，每个元素应为 [0, 1] 区间内的非负数值
        base: 对数的底数，默认为 2.0（此时熵的单位为比特 bit）

    返回:
        计算得到的信息熵值（浮点数）。若输入无效（空列表、None、含负概率）则返回 0.0
    """
    # 边界条件：空输入或 None
    if prob_dist is None or not isinstance(prob_dist, list) or len(prob_dist) == 0:
        return 0.0

    # 底数校验
    if base <= 0 or base == 1 or not isinstance(base, (int, float)):
        return 0.0

    entropy = 0.0
    for p in prob_dist:
        # 类型校验
        if not isinstance(p, (int, float)):
            return 0.0
        # 概率不能为负
        if p < 0:
            return 0.0
        # 0 概率项不贡献熵值（约定 0*log(0) = 0），跳过计算避免 log(0) 错误
        if p > 0:
            entropy -= p * (math.log(p) / math.log(base))

    return entropy