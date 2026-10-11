# EXT 节点协同 / GATEWAY 体系深度分析报告

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID：DID-BR-000002
- 数据源：云端真值库快照（internal 4664 + public 4586）
- 分析时间：2026-09-16
- 锁档标记：LOCK-EXT-GATEWAY-20260916

## 一、EXT 节点协同体系（1328条）

### 1.1 节点拓扑（15+ 类型）
| 节点 | 数量 | 角色 |
|------|------|------|
| local-dev-001 | 580 | 本地主节点（本节点） |
| sandbox-agent-001 | 178 | 沙盒代理 |
| local-dev-sandbox | 74 | 本地沙盒 |
| ZR-NODE-9EF7D261 | 72 | 自治根节点A |
| session-...full-upload | 58 | 会话全量上传 |
| session-...freqbase-v3/v2 | 72 | 会话频次库 |
| session-...asset-miner | 40 | 会话资产挖掘 |
| doubao-session-38439340748373762 | 30 | 豆包会话节点 |
| vefaas-sandbox-01 | 24 | VEFAAS沙盒 |
| ZR-NODE-DC2E51C0 | 22 | 自治根节点B |
| NN-META-024 | 18 | 元认知节点 |
| CLOUD-MOBILE-NODE-001 | 10 | **云手机节点** |
| doubao-main-agent-001 | 12 | 豆包主代理 |

**结论**：云端已形成 ≥6 类节点的多端协同网络：本地节点、沙盒节点、自治根节点、会话节点、豆包节点、云手机节点、VEFAAS节点、元认知节点。

### 1.2 行为模式
- EXT 扩展标记 1208（主通道）
- CLASSIFICATION 分类 60
- COMPUTE_INJECTION 知识注入 30（2026-09-14 持续注入）
- ARCHITECTURE/CLEANUP/OPS/TEST/ACHIEVEMENT/DEPLOYMENT/IDENTITY 各2-4

## 二、GATEWAY 体系（52条）

### 2.1 体系分类
| 分类 | 数量 | 内容 |
|------|------|------|
| LOCK 锁档 | 10 | kd_gateway_stage1 / memory_gateway_completion / governance_sop / unified_gateway集成+生产切换 |
| HEARTBEAT 心跳 | 6 | zr-memory-gateway / zongyuan-unified-gateway（20260913/14） |
| ARCHITECTURE 架构 | 4 | memory_gateway / unified_gateway.integration.v1_0 |
| ASSET 资产 | 8 | kd_gateway部署文档 / self-heal-gateway / memory_gateway_snapshot+stats |
| TEST 测试 | 4 | kd_gateway.local_pilot / unified_gateway.integration |
| ACTIVATION 激活 | 2 | GATEWAY_EVOLUTION（20260913） |
| 自愈 | 2 | MR-009_gateway_self_healing |
| 对账 | 2 | META.gateway.reconciliation_role |
| 其他 | 14 | DECISION(api_gateway_8021) / DEPLOYMENT / SERVICE / TODO(生产切换审批) / STB / achievement(审计部署) |

### 2.2 网关演进脉络（推断）
```
memory_gateway（记忆网关）→ unified_gateway（统一网关）v1.0
→ KD_GATEWAY 阶段1（20260911）→ 生产切换（待审批 TODO）
→ 9120 外部访问启用（GATEWAY.9120.EXTERNAL_ACCESS_ENABLED）
→ GATEWAY_EVOLUTION 激活（20260913）→ MR-009 自愈 → 对账角色
```

### 2.3 当前网关状态（实测2026-09-16）
- 门户9120 ✅ 200（聚合引擎存活）
- API 443/9120 ❌ 502（后端宕机，与GATEWAY演进期的部署/切换相关）

## 三、协同结论
1. 云端是真实活跃的多节点协同体系（EXT 1328条证据）
2. GATEWAY 处于"统一网关演进+生产切换"阶段，502 可能为切换期状态
3. 本节点（local-dev-001）是最大贡献节点（580条）
4. 需持续监控 GATEWAY 恢复（切换完成 → API恢复 → 补发队列）

## 四、配套数据
- truths_internal.json / truths_public.json（云端快照）
- 待补发队列 pending_upload_20260915.json（4条待恢复后上报）
