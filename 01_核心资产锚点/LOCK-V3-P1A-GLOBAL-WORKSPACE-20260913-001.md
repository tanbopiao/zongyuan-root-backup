# 锁档文档 · LOCK-V3-P1A-GLOBAL-WORKSPACE

## 确权锚点
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

## 锁档元数据

| 字段 | 值 |
|------|-----|
| 锁档ID | LOCK-V3-P1A-GLOBAL-WORKSPACE-20260913-001 |
| 方向 | P1-a 全局工作空间意识架构 |
| 优先级 | P1 |
| 锁档时间 | 2026-09-13T23:59:00+08:00 |
| 锁档状态 | ARCHIVED |
| 内核版本 | V3.0 |

## 产出清单

| 文件名 | 路径 | 行数 | 类型 | 状态 |
|--------|------|------|------|------|
| processor_registry.py | p1a_global_workspace/processor_registry.py | 388 | 处理器注册表 | ARCHIVED |
| attention_mechanism.py | p1a_global_workspace/attention_mechanism.py | 324 | 注意机制 | ARCHIVED |
| global_workspace_engine.py | p1a_global_workspace/global_workspace_engine.py | 517 | 全局工作空间主引擎 | ARCHIVED |

## 验收记录

| 验收项 | 要求 | 实际结果 | 状态 |
|--------|------|----------|------|
| py_compile全部通过 | 3个核心模块语法零错误 | 3个.py文件py_compile全部PASS | PASS |
| 9内置处理器 | 六维自检/闭环引擎/同源协议/记忆网关等 | 9个处理器全部注册成功 | PASS |
| direct_links无意识直连 | 支持无意识通道 | direct_links拓扑已建立，绕过意识广播 | PASS |
| 动态拓扑 | 拓扑可随运行时演化 | 处理器+边动态增删，ASCII+JSON双快照 | PASS |
| 4维显著性加权 | 新颖/重要/紧急/相关 | 注意力机制4维权重计算通过 | PASS |
| up-tree两层竞争 | 上层广播前竞争胜出 | 6候选竞争验证通过 | PASS |
| 注意焦点门控 | 焦点门控过滤非焦点信号 | 焦点门控开关可切换 | PASS |
| 不应期侧抑制 | 胜出后短暂不应期抑制 | 不应期侧抑制生效，防振荡 | PASS |
| 5步核心循环 | 并行采集→竞争→广播→无意识通信→拓扑自适应 | 12步循环全部通过 | PASS |
| threading并行采集 | 多处理器并行 | threading并行采集无死锁 | PASS |
| 12维CUF向量 | 全局工作空间内容向量 | 每步12维向量唯一且动态演化 | PASS |
| 意识报告 | 输出可读意识状态 | 意识报告JSON可读，integration维0.83-0.94 | PASS |
| 9处理器+14边拓扑 | 拓扑规模 | 演示稳态9节点14边 | PASS |

## 核心技术指标

| 指标 | 值 |
|------|-----|
| 核心代码行数 | 1229行（3模块） |
| 内置处理器数 | 9个 |
| 拓扑规模 | 9节点 + 14边 |
| CUF向量维度 | 12维 |
| 核心循环步数 | 5步（采集/竞争/广播/无意识/自适应） |
| 显著性加权维度 | 4维（新颖/重要/紧急/相关） |
| 竞争层数 | up-tree两层 |
| 演示循环步数 | 12步全部通过 |
| integration维范围 | 0.83 ~ 0.94 |
| 无意识直连 | direct_links通道 |
| 拓扑快照 | ASCII + JSON双格式 |

## 接口与依赖

- **对外接口**：Python模块级；`global_workspace_engine.GlobalWorkspaceEngine` 主类
- **内部依赖**：processor_registry ← attention_mechanism ← global_workspace_engine
- **与P0-a集成**：审计日志写入全局工作空间 → 政务平台可视化层订阅
- **与P0-b集成**：进化记忆节点作为处理器候选 → 闭环引擎输出进入全局工作空间竞争
- **与P1-b集成**：多智能体状态向量 → 全局工作空间共享内容（跨智能体意识广播）
- **与P2-a集成**：意识状态/拓扑快照暴露为 `/api/v1/neural/activate` 与 `/api/v1/neural/propagate`
- **与P2-b集成**：医疗麻醉深度/教育认知状态/工业健康监测均基于12维CUF向量建模

## 风险与遗留项

| 风险/遗留项 | 说明 | 后续优化方向 |
|-------------|------|--------------|
| 模拟信号源 | 处理器输入为模拟生成，非真实LLM/传感器流 | V3.1接入真实LLM推理流与外部传感器 |
| 单进程多线程 | threading并行，非分布式 | V3.1引入multiprocessing + gRPC跨机 |
| 意识量化边界 | CUF向量为定义性指标，缺神经科学对照 | V3.2对标CTM-AI/Theater of Mind实证校准 |
| 拓扑自适应规则 | 权重更新为简单Hebbian-like，非因果推断 | V3.2引入Granger因果/信息流估计 |
| 不应期参数 | 硬编码不应期，无在线学习 | V3.2用贝叶斯优化调参 |

## 同源校验

- 文件SHA256:
  - `processor_registry.py`: `a70c28322b1abf92f7269baef1644abe607b5f0b32f826147d68089796871e23`
  - `attention_mechanism.py`: `25ec66865318eeda313150082ab0799784754b70d2a916cba13f104380554e5e`
  - `global_workspace_engine.py`: `64523cf22f66fa53103e752e8c22819a5f28903c2a63fdbda7af44f740ffb175`
- 锁档哈希链: LOCK-V3-P0B-META-LOOP-20260913-001 → LOCK-V3-P1A-GLOBAL-WORKSPACE-20260913-001
- 校验状态: PASS
