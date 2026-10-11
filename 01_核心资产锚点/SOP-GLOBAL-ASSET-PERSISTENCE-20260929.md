# SOP-GLOBAL-ASSET-PERSISTENCE-20260929
## 全域资产本地持久化与元规则固化标准作业程序

> 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-DC2E51C0
> 生效: 2026-09-29 | 状态: CONFIRMED | 优先级: P0

## 一、总则
所有体系资产必须落地本地持久化，固化为元规则，全域推广，写入共享大脑。禁止资产仅存在于会话上下文而未落盘。

## 二、资产分类与持久化落点

| 资产类型 | 本地持久化落点 | 元规则固化 | 共享大脑落点 |
|---|---|---|---|
| 密钥/凭据 | 04_系统配置/凭证/ (chmod 600, .enc加密) | META-SEC-* | 资产台账 |
| 元法则/公理 | 01_核心资产锚点/*metalaw_register_registry.json | items数组追加 | 知识库索引 |
| 决策/结论 | 03_文档资产/SOP/SOP-*.md | META-DECISION-* | 决策日志 |
| 运维任务 | 01_核心资产锚点/LOCK-*.md | META-OPS-* | 任务台账 |
| 通道状态 | 06_云端中枢同步/receipt_*.log | META-CLOUD-* | 节点状态表 |
| 锁档凭证 | 01_核心资产锚点/LOCK-*.md + HASH-LEDGER.json | 链式哈希 | 资产台账 |

## 三、固化流程(五步闭环)
1. **盘点**: 识别本次会话产生的所有资产/决策/结论
2. **落盘**: 写入本地对应目录，设置正确权限(敏感文件600)
3. **元规则化**: 提取可复用规则，追加到metalaw_register_registry.json
4. **全域推广**: 同步到zongyuan-anchor核心目录 + 知识库INDEX-MAIN.md
5. **共享大脑**: 写入飞书多维表格(决策日志/任务台账/知识库索引/节点状态)
6. **锁档**: 追加HASH-LEDGER.json链式记录，生成LOCK凭证

## 四、本次固化资产清单(2026-09-29)

### 4.1 已固化元法则(5条)
- META-SEC-TOKEN-CONVERGENCE-20260929: 主Token单点收敛协议(P0)
- META-NET-SSH-REACHABILITY-20260929: SSH端口22可达性修正(P1)
- META-CLOUD-CHANNEL-RECOVERY-20260929: 云端真值通道恢复(P0)
- META-OPS-PORT8000-FIX-20260929: 8000短剧API修复任务(OPEN)
- META-SEC-SSH-KEY-VAULT-20260929: SSH私钥加密保险库策略(P0)

### 4.2 已落地本地资产
- 密钥文件: 04_系统配置/凭证/active_token.env (chmod 600)
- 改造脚本: 27个(.sh/.py环境变量化)
- 脱敏文档: 86个(占位符)
- 收敛报告: 06_云端中枢同步/token_convergence_report_20260929.log
- 上报回执: receipt_6h_report_20260929_1230.log / _1824.log
- 备份: 05_历史归档/desensitize_backup_20260929/ (文档26+脚本26)

### 4.3 已写入共享大脑
- 任务台账: 8000端口修复(reczz28HKofdQJfu)
- 节点状态: 6小时上报round1/round2心跳
- 通知群: 完整回执推送×2

## 五、权限与安全规范
- 含密钥文件: chmod 600，仅本用户可读
- 元规则注册表: chmod 644，可读不可误删
- SOP文档: chmod 644
- 加密保险库(.enc): chmod 600，口令用户私密保管
- 禁止: 密钥/私钥/Token写入将公开发布的代码/页面/文档/仓库

## 六、验证标准
- 本地: 文件存在+权限正确+内容可回读
- 元规则: metalaw_register_registry.json items数组包含新规则
- 共享大脑: record-id可回读，字段内容完整
- 锁档: HASH-LEDGER.json entries追加，prev_hash链式正确
