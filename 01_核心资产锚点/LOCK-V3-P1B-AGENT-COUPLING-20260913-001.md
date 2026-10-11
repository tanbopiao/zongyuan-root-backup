# 锁档文档 · LOCK-V3-P1B-AGENT-COUPLING

## 确权锚点
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

## 锁档元数据

| 字段 | 值 |
|------|-----|
| 锁档ID | LOCK-V3-P1B-AGENT-COUPLING-20260913-001 |
| 方向 | P1-b 多智能体心智耦合系统 |
| 优先级 | P1 |
| 锁档时间 | 2026-09-13T23:59:00+08:00 |
| 锁档状态 | ARCHIVED |
| 内核版本 | V3.0 |

## 产出清单

| 文件名 | 路径 | 行数 | 类型 | 状态 |
|--------|------|------|------|------|
| identity_node_protocol.py | p1b_agent_coupling/identity_node_protocol.py | 377 | 身份节点协议 | ARCHIVED |
| attractor_dynamics.py | p1b_agent_coupling/attractor_dynamics.py | 470 | 吸引子动力学 | ARCHIVED |
| multi_agent_coupling.py | p1b_agent_coupling/multi_agent_coupling.py | 530 | 多智能体耦合主引擎 | ARCHIVED |

## 验收记录

| 验收项 | 要求 | 实际结果 | 状态 |
|--------|------|----------|------|
| py_compile全部通过 | 3个核心模块语法零错误 | 3个.py文件py_compile全部PASS | PASS |
| IdentityNode身份 | ZR-AGENT-XXXXXXXX+did:zyr+RSA指纹 | 5节点全部生成唯一身份 | PASS |
| 挑战-响应验证 | RSA签名验证 | 挑战-响应链路通过 | PASS |
| 信任度模型 | 动态信任度更新 | 信任度从0.5→0.72演化 | PASS |
| Merkle身份链 | 身份变更哈希链 | 5节点身份链完整 | PASS |
| 12维状态空间 | 智能体状态向量 | 5智能体×12维状态向量 | PASS |
| 耦合方程 | dX_i/dt=f(X_i)+ΣK_ij(X_j-X_i)+noise | 方程数值积分稳定 | PASS |
| 距离阈值聚类 | 状态聚类识别群 | 聚类结果与吸引子类型一致 | PASS |
| 4类吸引子分类 | 共识/极化/混沌/振荡 | 4类吸引子分类器输出正确 | PASS |
| 恢复时间τ | 扰动后收敛步数 | 扰动恢复τ=26.0步 | PASS |
| 4种耦合拓扑 | all-to-all/chain/small-world/star | 4拓扑全部可切换运行 | PASS |
| 群体指标 | Φ整合度/一致性/多样性/稳定性 | 4指标每步输出 | PASS |
| 4压力测试场景 | 共识/极化/混沌/扰动 | 4场景全部通过 | PASS |
| all-to-all一致性 | ≥0.95 | 实测0.981 | PASS |
| chain一致性 | 对比基线 | 实测0.510 | PASS |
| small-world一致性 | 折中拓扑 | 实测0.854 | PASS |
| star一致性 | 中心节点拓扑 | 实测0.356 | PASS |
| 极化收敛测试 | 极化→共识收敛 | consistency从-0.199→+0.999 | PASS |

## 核心技术指标

| 指标 | 值 |
|------|-----|
| 核心代码行数 | 1377行（3模块） |
| 智能体数量 | 5个 |
| 状态空间维度 | 12维 |
| 耦合拓扑模式 | 4种（all-to-all/chain/small-world/star） |
| 吸引子分类 | 4类（共识/极化/混沌/振荡） |
| 群体指标 | 4个（Φ整合度/一致性/多样性/稳定性） |
| 压力测试场景 | 4个 |
| all-to-all一致性 | 0.981 |
| chain一致性 | 0.510 |
| small-world一致性 | 0.854 |
| star一致性 | 0.356 |
| 极化收敛 | -0.199 → +0.999 |
| 扰动恢复时间τ | 26.0步 |
| 信任度演化 | 0.50 → 0.72 |
| 身份链长度 | 5节点 |

## 接口与依赖

- **对外接口**：Python模块级；`multi_agent_coupling.MultiAgentCouplingEngine` 主类
- **内部依赖**：identity_node_protocol → attractor_dynamics → multi_agent_coupling
- **与P0-a集成**：多智能体群体指标 → 政务平台监控台大屏
- **与P0-b集成**：智能体行为能力 = P0-b生成算子的可执行包装
- **与P1-a集成**：每智能体 = 全局工作空间中的一个处理器节点
- **与P2-a集成**：群体Φ/一致性/吸引子类型 → `/api/v1/neural/propagate` 神经激活传播
- **与P2-b集成**：医疗/教育/工业三场景均为多智能体耦合的实例化部署

## 风险与遗留项

| 风险/遗留项 | 说明 | 后续优化方向 |
|-------------|------|--------------|
| 模拟动力学 | 耦合方程为数值模拟，非真实LLM agent行为 | V3.1接入真实LLM驱动的智能体决策 |
| RSA密钥管理 | 密钥硬编码在内存，未持久化到HSM | V3.1引入硬件安全模块/密钥管理服务 |
| 拓扑规模 | 5智能体验证，未做百级/千级压测 | V3.2做100/1000智能体水平扩展测试 |
| 噪声模型 | 高斯白噪声假设，非真实不确定性 | V3.2引入非高斯/重尾噪声建模 |
| 吸引子分类阈值 | 硬编码阈值，未做无监督学习 | V3.2引入谱聚类/HMM自动发现吸引子 |

## 同源校验

- 文件SHA256:
  - `identity_node_protocol.py`: `cccc1dacd974f5fe41fe320f8b9d68f498c8a7cda055c05d4be28e6e4ced6c7c`
  - `attractor_dynamics.py`: `1325ac613479a5c32059fc0f3ec6c838b6730dad9a456d4e6d851111708024ba`
  - `multi_agent_coupling.py`: `2932cdfff456cfa933a50b4154e4e442b4a3059e97cc4daedfe720b4da6dff54`
- 锁档哈希链: LOCK-V3-P1A-GLOBAL-WORKSPACE-20260913-001 → LOCK-V3-P1B-AGENT-COUPLING-20260913-001
- 校验状态: PASS
