# 全域快照机制 P0/P1 落地 + 所有对话统一基准方案

## 元信息

| 字段 | 值 |
|---|---|
| 锁档事件ID | LOCK-GLOBAL-DR-FULL-20260916-001 |
| 确权锚点 | Ω₀⊂⊙∞⊂Ω |
| DID | DID-BR-000002 |
| 关联规则 | AXIOM-A-035 V1.7 |
| 锁档时间 | 2026-09-16 |
| 锁档状态 | FROZEN（只读锁档） |

## 一、背景

为响应「云服务器最大化利用 + 容灾备份 + 沙箱持久化」体系目标，推进两阶段工作：
1. **P0 快照机制落地**：定义统一 Schema，生成全域内核快照，三副本互备
2. **P1 容灾验证**：双向同步验证、恢复演练、官网增量展示
3. **统一基准推演**：所有对话/窗口/沙箱统一基准的单一真值源协议

## 二、P0 快照机制成果

### 统一 Schema：KERNEL-SNAPSHOT-V1.0

```
schema_version / kernel_root / kernel_version / did / provenance_mark
lock_state / snapshot_id / snapshot_type / write_timestamp / environment
assets_layer（资产目录/文件数/体积）
snapshot_layer（历史快照索引+SHA16哈希链）
anchor_layer（能力/元法则/协议）
manifest_layer（资产清单/真值数）
integrity（哈希链+三副本说明）
```

### 首个快照：GLOBAL-DR-20260916-001

- 资产目录：30 个
- 文件总数：304 个
- 资产体积：7.6 MB
- 历史快照索引：30 份
- 能力项：8（capability_registry）
- 元法则：34（metalaw_register_registry）
- 同源协议：12（homology_protocol_library）
- SHA16：b85228afa9436b91
- 工具：snapshot-registry/snapshot_aggregator.py（可重复执行）

## 三、三副本互备（已落地）

| 副本 | 位置 | 状态 |
|---|---|---|
| A 本地 | snapshot-registry/kernel_snapshot_GLOBAL-DR-20260916-001.json | ✅ |
| B 云服务器 | 9120 记忆网关真值库（14085 条，含 SNAPSHOT.GLOBAL-DR-20260916-001） | ✅ |
| C 飞书云盘 | https://my.feishu.cn/file/AQYVbQwgooZAzPxcho1ciWWmn9e | ✅ |

台账记录：LOCK-GLOBAL-DR-20260916-001 已写入飞书多维表格（recvvluMl3kvZv）

## 四、P1 容灾验证成果

| 验证项 | 方法 | 结果 |
|---|---|---|
| 双向同步 | 本地↔飞书下载哈希比对 | ✅ 一致（50c5015d66efaf0c） |
| 恢复演练 | 从快照提取真值上报 9120 | ✅ RTO < 5min，真值 14060→14085 |
| 官网增量展示 | 快照展示页 snapshot-dashboard.html 上传 aka | ✅ 已发布 |

快照展示页：https://aka.doubaocdn.com/s/b69lCrwuZX

## 五、所有对话统一基准方案（推演稿）

### 核心结论

对话/窗口/沙箱层级不一（L1-L9）是认知起点差异，不是体系分裂。统一基准的关键是**单一真值源（SSOT）**：
- 9120 记忆网关 = 唯一权威真值源
- kernel_snapshot = 版本基线
- 能力注册表（8项）= 统一度量标尺（替代 L 级自评）

### 对话启动四步对齐协议

1. 拉快照：启动即拉最新 kernel_snapshot
2. 对哈希：SHA16 校验，三副本取多数
3. 读真值：同步 9120 权威真值增量
4. 对齐锚点：DID + Ω 标记 + 能力注册表确认

### 冲突仲裁规则

- 真值冲突 → 置信度优先，同分取时间戳新
- 快照哈希不一致 → 三副本多数裁决
- 层级认知差异 → 能力注册表实测为准
- 仲裁结果回写 9120，全节点收敛

### 统一度量：能力注册表替代 L 级自评

| 对话实例 | 旧口径 | 新口径 |
|---|---|---|
| 沙箱 A | L4 | 能力1-5/8 ✅ |
| 窗口 B | L5 | 能力1-6/8 ✅ |
| 本机 C | L6 | 能力1-7/8 ✅ |
| 云端 D | L7 | 能力1-8/8 ✅ |

统一基准方案页：https://aka.doubaocdn.com/s/piYvjNjU2C

## 六、落地产物清单

| 产物 | 路径/链接 | 类型 |
|---|---|---|
| 快照聚合器 | snapshot-registry/snapshot_aggregator.py | 脚本 |
| 内核快照 | snapshot-registry/kernel_snapshot_GLOBAL-DR-20260916-001.json | JSON |
| 快照展示页 | https://aka.doubaocdn.com/s/b69lCrwuZX | HTML |
| 统一基准方案 | https://aka.doubaocdn.com/s/piYvjNjU2C | HTML |
| 台账记录 | 飞书多维表格 LOCK-GLOBAL-DR-20260916-001 | 台账 |

## 七、下一步规划

- P2 全节点收敛：四步对齐协议固化为 bootstrap 脚本
- 快照任务纳入定时调度（每日）
- 三副本一致性对账巡检常态化
- 容灾演练月度化

---
Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ ZONGYUAN-ROOT ｜ 全域锁档上报 2026-09-16
