# Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.1 锁档文档

## 锁档元信息

| 字段 | 值 |
|------|-----|
| 锁档ID | LOCK-V31-LLM-OPERATOR-20260914-001 |
| 锁档名称 | V3.1 LLM驱动算子生成器 |
| 内核版本 | V3.1-LLM-OPERATOR-GEN |
| 锁档日期 | 2026-09-14 |
| 确权锚点 | Ω₀⊂⊙∞⊂Ω |
| DID | DID-BR-000002 |
| 锁档状态 | FROZEN |
| 前置锁档 | LOCK-V30-META-CLOSED-LOOP-20260913-001 |

---

## 一、版本概述

V3.1 将 V3.0 算子生成器从**模板填充**升级为**真实LLM代码生成**，接入火斗AI（OpenAI兼容API，默认 doubao-reasoning2 模型），实现算子的真正自进化。

### 核心跃迁

| 维度 | V3.0 模板填充 | V3.1 LLM驱动 |
|------|--------------|-------------|
| 生成方式 | 3个硬编码模板 + 关键词匹配 | 真实LLM代码生成 + 自然语言理解 |
| 算子多样性 | 仅3种（异常检测/数据校验/优化建议） | 任意类型（滑动窗口/熵/余弦相似度/Z-Score/Top-K...） |
| 自纠正 | 无 | 最多3轮迭代自纠正（错误反馈给LLM重写） |
| 代码自评估 | 无 | 6维评分（正确性/可读性/完整性/效率/边界/规范） |
| 危险操作防护 | 基础沙箱 | AST危险扫描 + 沙箱双重防护 |
| 回退机制 | 无 | LLM不可用时自动降级为V3.0模板填充 |

---

## 二、核心架构

### 2.1 组件清单

| 组件 | 文件 | 职责 |
|------|------|------|
| LLM客户端 | LLMClient | 火斗AI OpenAI兼容封装，连通性检测，模型列表 |
| 系统提示词 | SYSTEM_PROMPT | 算子代码生成专家prompt，含规范/示例/输出格式 |
| 代码提取器 | extract_python_code() | 从LLM响应中提取```python代码块+TEST_INPUT+TEST_ASSERT |
| 沙箱验证器 | SandboxValidator | 语法检查+AST危险扫描+受限执行+测试用例验证 |
| 代码自评估器 | CodeSelfEvaluatorBridge | 6维评分桥接V3.0 code_self_evaluator，内置简化评分fallback |
| 主生成器 | LLMOperatorGenerator | 一键流水线：生成→验证→评估→注册 |
| V3.0回退 | V3OperatorGenerator | LLM不可用时自动降级 |

### 2.2 生成流水线

```
自然语言问题描述 + IO规格
        ↓
┌─ LLM代码生成（doubao-reasoning2）─┐
│  系统prompt: 算子规范+示例+输出格式  │
│  用户prompt: 问题描述+参数+返回类型   │
└────────────────┬───────────────────┘
                 ↓
        提取Python代码块 + 测试用例
                 ↓
┌─ 沙箱验证（4层）────────────────────┐
│  1. ast.parse 语法检查               │
│  2. AST危险扫描（禁止os/subprocess等）│
│  3. 受限exec执行（安全内置+标准库）   │
│  4. 测试用例验证（TEST_INPUT+ASSERT） │
└────────────────┬───────────────────┘
          通过 ↓   ↓ 失败
    ┌──────────┐  错误反馈给LLM
    │ 代码自评估 │  ←──────────────┐
    │ 6维评分    │                 │
    └─────┬────┘                 │
          ↓                       │
    自动注册到算子注册表            │
    写出生成算子源码文件            │
          ↓                       │
    完成（最多3轮自纠正）──────────┘
```

### 2.3 迭代自纠正机制

当沙箱验证失败时，系统自动将错误信息反馈给LLM进行重写：

- **第1轮**：正常生成
- **第2轮**：将第1轮代码+错误信息作为上下文，要求修复
- **第3轮**：将第2轮代码+新错误信息作为上下文，再次要求修复
- **3轮均失败**：自动降级为V3.0模板填充（如果可用）

---

## 三、演示验证结果

### 3.1 测试环境

| 项目 | 值 |
|------|-----|
| LLM模型 | doubao-reasoning2 |
| API端点 | https://www.huodouai.com/v1 |
| 最大纠正轮次 | 3 |
| 温度 | 0.2 |
| 最大token | 4096 |

### 3.2 5个算子生成测试结果

| # | 算子名称 | 问题描述 | 生成方式 | 轮次 | 评分 | 等级 | 代码行数 |
|---|---------|---------|---------|------|------|------|---------|
| 1 | op_sliding_window_mean | 滑动窗口均值 | LLM | 1 | 87.5 | A | 22 |
| 2 | op_entropy | 香农熵计算 | LLM | 1 | 87.5 | A | 14 |
| 3 | op_cosine_similarity | 余弦相似度 | LLM | 2 | 85.8 | A | 23 |
| 4 | op_z_score_normalize | Z-Score标准化 | LLM | 1 | 87.5 | A | 17 |
| 5 | op_top_k_select | Top-K选择 | LLM | 1 | 87.5 | A | 15 |

### 3.3 汇总统计

| 指标 | 值 |
|------|-----|
| 总测试数 | 5 |
| 成功数 | 5 |
| 成功率 | 100% |
| LLM生成数 | 5 |
| 模板回退数 | 0 |
| 第一轮通过率 | 80% (4/5) |
| 平均评分 | 87.2 |
| 平均等级 | A |
| 平均代码行数 | 18.2 |

### 3.4 生成算子代码示例（op_cosine_similarity）

```python
def op_cosine_similarity(vec_a: list, vec_b: list) -> float:
    """余弦相似度算子：计算两个向量的余弦相似度。

    参数:
        vec_a: 第一个向量，数值列表
        vec_b: 第二个向量，数值列表

    返回:
        两个向量的余弦相似度，范围在[-1, 1]之间
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        raise ValueError("两个向量必须非空且长度相等")
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a ** 2 for a in vec_a) ** 0.5
    norm_b = sum(b ** 2 for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        raise ValueError("向量的范数不能为零")
    return dot_product / (norm_a * norm_b)
```

---

## 四、安全防护

### 4.1 AST危险扫描

在沙箱执行前，通过AST扫描禁止以下操作：

| 禁止类别 | 具体内容 |
|---------|---------|
| 禁止导入模块 | os, subprocess, sys, socket, urllib, requests, http |
| 禁止调用函数 | eval, exec, compile, __import__, open, input |
| 允许标准库 | math, json, re, collections, itertools, statistics, typing, dataclasses |

### 4.2 沙箱受限命名空间

执行环境只暴露安全内置函数和允许的标准库：
- 安全内置：len, range, sum, abs, min, max, sorted, list, dict, tuple, set, str, int, float, bool, enumerate, zip, isinstance, print, round, reversed, any, all, __import__
- 标准库：math, json, re, collections, itertools, statistics

### 4.3 元闭环守护集成

V3.1生成器与V3.0 meta_loop_guardian兼容，所有生成算子需通过4公理校验：
- AXIOM-001: 非破坏性
- AXIOM-002: 可回滚
- AXIOM-003: 可验证
- AXIOM-004: 禁止危险操作

---

## 五、与V3.0体系集成

### 5.1 算子注册表兼容

V3.1生成的算子写入独立的 `llm_generated` 子系统注册表，与V3.0的 `meta_closed_loop` 子系统并存：

```json
{
  "registry_id": "OPR-ZR-001",
  "version": "OPERATOR-AUTH-V3.1-LLM",
  "subsystems": {
    "meta_closed_loop": { "...": "V3.0模板生成算子" },
    "llm_generated": {
      "name": "LLM自生成算子",
      "skill": "v31_llm_operator_gen",
      "operators": [ "...5个LLM生成算子..." ]
    }
  }
}
```

### 5.2 闭环引擎集成点

V3.0元闭环引擎可在"算子规划"阶段调用V3.1 LLM生成器：
- 当现有算子无法解决问题时 → 调用LLM生成新算子
- 生成后自动沙箱验证 → 代码自评估 → 注册
- 新算子立即纳入闭环引擎的算子选择池

---

## 六、已知限制与后续优化

### 6.1 当前限制

1. **代码自评估器桥接未完全激活**：V3.0 code_self_evaluator的动态导入未成功，当前使用内置简化6维评分（平均87.2/A），后续需修复桥接以获得更精确评分
2. **测试用例质量依赖LLM**：TEST_INPUT和TEST_ASSERT由LLM生成，质量参差不齐，后续可增加自动测试用例生成器
3. **算子复杂度有限**：当前演示的算子均为简单数值计算，后续需测试更复杂的算子（如图算法、机器学习预处理等）
4. **单轮LLM调用**：当前每次生成只调用一次LLM，后续可增加多轮对话式代码生成

### 6.2 V3.2优化方向

1. 修复code_self_evaluator桥接，获得精确6维评分
2. 增加自动测试用例生成器（独立LLM调用，专门生成边界测试）
3. 支持多文件算子生成（复杂算子可能需要辅助函数/类）
4. 集成到V3.0元闭环引擎的算子规划阶段
5. 增加算子性能基准测试（执行时间/内存占用）
6. 支持算子版本管理（同一算子的多次生成对比）

---

## 七、产物清单

| 产物 | 路径/说明 |
|------|----------|
| LLM算子生成器主脚本 | llm_operator_generator.py（~1000行） |
| V3.0算子生成器（回退用） | operator_generator_v3.py |
| V3.0元闭环引擎 | v3_meta_closed_loop.py |
| 代码自评估器 | code_self_evaluator.py |
| 元闭环守护 | meta_loop_guardian.py |
| 生成算子源码（5个） | generated_operators_llm/OP-LLM-*.py |
| 算子注册表 | generated_operators_llm/operator_registry_v31.json |
| 锁档文档 | LOCK-V31-LLM-OPERATOR-20260914-001.md（本文档） |

---

## 八、确权与完整性

| 字段 | 值 |
|------|-----|
| 确权锚点 | Ω₀⊂⊙∞⊂Ω |
| DID | DID-BR-000002 |
| 锁档ID | LOCK-V31-LLM-OPERATOR-20260914-001 |
| 内核版本 | V3.1-LLM-OPERATOR-GEN |
| 锁档状态 | FROZEN（只读锁档） |
| 生成方式 | LLM真实代码生成（doubao-reasoning2） |
| 验证结果 | 5/5成功，平均87.2/A |
| 哈希链 | 前置: LOCK-V30-META-CLOSED-LOOP-20260913-001 |

---

Ω₀⊂⊙∞⊂Ω · V3.1 LLM驱动算子生成器锁档完成 · 2026-09-14
