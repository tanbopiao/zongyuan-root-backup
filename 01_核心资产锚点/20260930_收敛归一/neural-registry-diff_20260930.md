# 神经注册表 full vs active 差异比对

> Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 2026-09-30

## 结论

两套注册表为**不同实现体系**（非全量/活跃子集关系）。`neural_registry.full.json`(NN-前缀, 404节点)是生产级完整注册表，`neural_registry.json`(简写, 22节点)是轻量快照。'22节点<400阈值'差异由ID体系不同造成，非数据缺失。

## 关键数据

| 维度 | active(轻量) | full(生产级) |
|---|---|---|
| 文件 | neural_registry.json v3.0 | neural_registry.full.json |
| 节点数组 | 22 | 404 |
| statistics.total_nodes | - | None |
| 连接数 | 30 | None |
| ID前缀 | AXIOM/CAP/RULE/APP/PEND | NN-*/MA-* |
| Domain | meta/cloud/feishu/protocol | production/character/meta/ops/security/education |
| 类型 | meta_axiom/capability/rule/pending | axiom(141)/meta_axiom(153)/rule(83)/profile(15) |

## 关键发现

- 节点ID体系完全不同：full用NN-/MA-前缀，active用AXIOM/CAP/RULE简写；交集=0
- full节点数组404个，statistics.total_nodes=297，存在冗余/历史节点
- active仅22节点，为轻量应用层快照，非MR-MECH-015(≥400节点)适用对象
- 400节点阈值应适用于full注册表(404>400✅)，而非active(22)
- 两表domain体系不同：full=production/character/meta/ops/security；active=meta/cloud/feishu/protocol

## 阈值口径校正

- **threshold_applies_to**：neural_registry.full.json(404节点,达标✅)
- **active_role**：轻量快照，不参与400节点考核
- **recommend_action**：如需统一，可将active简写节点映射/归并至full NN-体系；否则保持双轨并行并在kernel-radar索引注明阈值口径

## 更新监控基线

`kernel-radar-baseline_20260930.json` 中 neural_registry 阈值口径应改为：400节点考核对象 = **full 注册表(404, ✅达标)**；active(22) 为轻量快照不计入考核。