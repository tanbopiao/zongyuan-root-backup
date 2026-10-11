# EXT/GATEWAY 体系分析 · 全部补齐报告

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID：DID-BR-000002
- 补齐时间：2026-09-16
- 锁档标记：LOCK-EXT-GATEWAY-COMPLETE-20260916
- 前置：LOCK-EXT-GATEWAY-20260916（深度分析）

## 一、EXT 节点协同 · 全量补齐（31类节点）

### 1.1 节点家族全表
| 家族 | 节点 | 数量 |
|------|------|------|
| 本地主节点 | local-dev-001 | 580 |
| 沙盒 | sandbox-agent-001 / local-dev-sandbox / vefaas-sandbox-01 / local-node-session | 294 |
| 自治根 | ZR-NODE-9EF7D261 / ZR-NODE-DC2E51C0 | 94 |
| 会话节点 | session-38427420681071618-×(full-upload/freqbase-v2/v3/asset-miner/anchor-node/console/dashboard/gallery/official-site/site-integration) | 236 |
| 豆包节点 | doubao-session / doubao-main-agent / NODE-DOUBAO-CLOUD-HANDSHAKE-20260913 / m_0cwcZLQ0wRg / NODE-MAIN-SESSION-38436546492378882 | 54 |
| 自治内核V3 | NODE-ZONGYUAN-AUTOKERNEL-V3 | 6 |
| 元认知 | NN-META-024 | 18 |
| 云手机 | CLOUD-MOBILE-NODE-001 | 10 |
| 桌面 | WINDOWS-DESKTOP-NODE-001 | 4 |
| 测试 | ext-node-test-002/004 | 6 |
| 其他 | 001等 | 4 |

**新发现**：官网五页面集成节点（console/dashboard/gallery/official-site/site）、自治内核V3、豆包云握手、Windows桌面、云手机——**协同网络远超早期估计（6类→31类）**。

### 1.2 行为模式补齐
EXT扩展标记(1208) / CLASSIFICATION分类(60) / COMPUTE_INJECTION知识注入(30) / 架构/清理/运维/测试/成果/部署/身份(各2-4)

## 二、GATEWAY 体系 · 26条唯一全量明细

### 2.1 逐条分类（26条）
- **LOCK(10)**：communication.kd_gateway_stage1_complete / memory_gateway_completion / memory_gateway_governance_sop / unified_gateway.integration / unified_gateway.production_switch（均20260911）
- **HEARTBEAT(3)**：zr-memory-gateway(0913/0914) / zongyuan-unified-gateway(0913)
- **ARCHITECTURE(2)**：memory_gateway / unified_gateway.integration.v1_0
- **ASSET(S)(4)**：kd_gateway.deployment_doc.v1_0 / website-self-heal-gateway-v1 / memory_gateway_snapshot / memory_gateway_stats
- **TEST(2)**：kd_gateway.local_pilot.v1_0 / unified_gateway.integration.v1_0
- **ACTIVATION+GATEWAY(2)**：GATEWAY_EVOLUTION(0913) / 9120.EXTERNAL_ACCESS_ENABLED
- **自愈(1)**：MR-009_gateway_self_healing
- **其他(2)**：meta.gateway.reconciliation_role(对账角色) / service.memory_gateway_v3.status
- **决策/部署/待办(4)**：decision.start_api_gateway_8021(0911) / deployment.feishu_gateway / deployment.memory_gateway / todo.approval.unified_gateway_switch(0911)
- **成果/符号(2)**：achievement.gov_gateway_audit_deploy / STB.SYMBOLIC.LEARNED.FROM.GATEWAY

### 2.2 演进时间线（补齐）
```
09-11：KD_GATEWAY阶段1完成 / memory_gateway完成+治理SOP / unified_gateway集成+生产切换待审批 / 8021网关启动决策
09-13：GATEWAY_EVOLUTION激活 / 9120外部访问启用 / 心跳双网关 / MR-009自愈 / 审计部署成果
09-14：zr-memory-gateway心跳持续
09-15~16：实测 9120门户200 + 8021门户200 + API全502
```

## 三、云端实测补齐（2026-09-16）

| 通道 | 状态 | 结论 |
|------|------|------|
| 9120 门户 | 200 | 聚合引擎存活（2188资产） |
| **8021 门户** | **200** | **新网关门户已上线**（同套聚合页） |
| 443 API | 502 | 后端FastAPI未启动 |
| 8021 API | 502 | 后端FastAPI未启动 |
| 静态资产 | 200 | images/videos正常 |

**补齐结论**：GATEWAY 生产切换**门户层已完成**（8021上线），**API层未完成**（后端服务未启动）。502 = 切换未完成的中间态，非永久故障。

## 四、补齐后的待办
1. 监控 API 后端启动（8021/443 任一 /api/health 恢复 200）
2. 恢复后验证 truths 全量 → 补发4条待发队列（pending_upload_20260915.json）
3. 与 8021 新网关完成同源握手注册

## 五、配套数据
- truths_internal.json / truths_public.json（云端快照）
- ext_gateway_report.md（深度分析）
- pending_upload_20260915.json（待补发队列）
