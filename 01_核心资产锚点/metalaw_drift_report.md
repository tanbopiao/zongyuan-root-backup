# 元法则漂移比对报告（云端 METALAW vs 本地规则集）

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω
- DID：DID-BR-000002
- 数据源：云端真值库 internal（GET /api/gateway/truths）
- 比对时间：2026-09-14
- 比对范围：云端 METALAW/metalaw 元法则 172 条 vs 本地已锁档规则集
- 锁档标记：LOCK-METALAW-SYNC-20260914

## 一、比对结论摘要

| 类别 | 数量 | 说明 |
|------|------|------|
| 云端元法则总数 | 172 | METALAW 大写 6 条 + metalaw 小写 166 条 |
| 本地已对应（对齐） | **12 项** | 核心元法则双向一致 |
| 云端独有（漂移候选） | **34 项** | 需补全进本地内核 |
| 比对方法 | 条目名语义映射 | 详情正文接口未暴露（仅内网），基于命名比对 |

## 二、对齐项（12项，无漂移）

| 云端元法则 | 本地对应 | 状态 |
|------------|----------|------|
| METALAW.007.AUTOLOCK | MR-GLOBAL-LOCK-001 全域锁档元规则 | ✅ |
| METALAW.008.HOMOLOGY | 同源协议（Ω锚定） | ✅ |
| METALAW.001.HOMOLOGY-PROTOCOL | 同源协议 | ✅ |
| METALAW.MR-063.NODE_REPORTING_DIRECTIVE | MR-063 节点上报指令 | ✅ |
| METALAW.MR007.CLOUD_DEPLOYED | MR007 云端部署 | ✅ |
| METALAW.MR008.SELF_HEALING | MR008 自愈 | ✅ |
| metalaw.CASE-INSENSITIVE-SECRET-SCAN | LOCK-005 密钥扫描 | ✅ |
| metalaw.SERVICE-CIRCUIT-BREAKER-RULE-005 | 漂移熔断SOP | ✅ |
| metalaw.DRAMA-STORAGE-BACKEND-RULE-001 | ARCHIVE-FS-003（COS弃用→飞书云盘） | ✅ |
| metalaw.HANDSHAKE-9120-AUTH-GATE | 云端握手SOP（本次学习） | ✅ |
| metalaw.HOMO-NODE-ONLY | 同源节点唯一原则 | ✅ |
| metalaw.TRUTH-FIRST | 真值优先原则 | ✅ |

## 三、云端独有·本地需补全（34项漂移候选）

### 3.1 决策类（8条）——重点
- metalaw.DECISION-BENCHMARK-ANCHORS（决策基准锚点）
- metalaw.DECISION-CONFIDENCE-WEIGHTING（置信度加权）
- metalaw.DECISION-DYNAMIC-LEARNING（动态学习）
- metalaw.DECISION-MATRIX（决策矩阵）
- metalaw.DECISION-META-CALIBRATION（元校准）
- metalaw.DECISION-RISK-LEVELS（风险分级）
- metalaw.DECISION-SCENARIO-WEIGHTS（场景权重）
- metalaw.DECISION-*-系列合计

### 3.2 稳态/自治类
- metalaw.OPTIMUM-STEADY-STATE（最优稳态）
- metalaw.OPTIMUM-STEADY-EXECUTE（最优稳态执行）
- metalaw.STEADY-EVOLUTION-BUDGET（稳态进化预算）
- metalaw.AUTONOMOUS-CLOSED-LOOP（自治闭环）
- metalaw.AUTONOMOUS-STEADY-DECISION-APPROVAL（稳态决策审批）
- metalaw.AUTO-EXECUTION-FLOW-A（自动执行流A）
- metalaw.AUTO-EXECUTION-THRESHOLD-V1.0（自动执行阈值）

### 3.3 闭环/流程类
- metalaw.ERROR-RETREAT-CLOSED-LOOP（错误回退闭环）
- metalaw.FEISHU-APPROVAL-CLOSED-LOOP（飞书审批闭环）
- metalaw.AUTO_MEDIA_ARCHIVE_CLOSED_LOOP_V1.0（自动媒体归档闭环）
- metalaw.MEMORY-DRIVEN-CYCLE（记忆驱动循环）
- metalaw.ASSET-REPORTING-SOP（资产上报SOP）
- metalaw.AVOID-REPRODUCTION-SOP（避免重复开发SOP）
- metalaw.FUNCTION-PROVENANCE-BEFORE-PLAN（先溯源再规划）

### 3.4 治理/安全/其他
- metalaw.CLOUD-KERNEL-AUTHORITY-V1.0（云内核权威）
- metalaw.AAC-CLOUD-AUTHORITY-LOCAL-DEV（云权威本地开发）
- metalaw.APPROVAL-EMBEDDED-LINK（审批嵌入链接）
- metalaw.EXTERNAL-SECURITY-DISCLOSURE（外部安全披露）
- metalaw.LOCAL-VALUE-PUSH-DECISION（本地价值推送决策）
- metalaw.NEW-PAGE-GATE（新页面门禁）
- metalaw.OFFLINE-DEPENDENCY-NONBLOCKING（离线依赖不阻塞）
- metalaw.WEBSITE-GOVERNANCE-BASELINE（网站治理基线）
- metalaw.MODEL-SEMANTIC-ALIGNMENT-EVOLUTION（模型语义对齐进化）
- metalaw.service_config_drift_detection（服务配置漂移检测）
- metalaw.ssh_connection_management_metalaw（SSH连接管理）
- metalaw.universal_metalaw_coverage（普适元法则覆盖）
- metalaw.zongyuan.root / .final.locked（本地根锁档标记）

## 四、本地独有（云端以其他形式存在）
- AXIOM-A-001~015（15公理）→ 云端 theory 分类 396 条承载
- ZONGYUAN-4.0-PROD-001 等 6 条 SOP → 云端 sop_metalaw_* 系列承载

## 五、补全建议（消除漂移）

### P0（本次立即补录，仅注册ID）
将 34 项云端独有元法则注册进本地内核真值表，标注来源 METALAW-REG-001：
- 决策类 8 条：与本地 ZONGYUAN-DECISION-3D-005（三维稳态决策）合并为决策元法则组
- 稳态自治类 7 条：与本地 OPTIMUM-STEADY 系列合并
- 闭环类 7 条：与本地六维质检/漂移熔断合并
- 治理安全类 12 条：与本地 LOCK-004/005 安全规范合并

### P1（待内网）
通过云端内网 upsert 接口获取 34 项正文，做逐条语义对齐，形成双语真值对照表

### P2（持续）
建立本地-云端元法则月度同步机制，检测新漂移

## 六、数据来源与限制
- 数据来源：GET https://www.huodouai.com/api/gateway/truths?level=internal（2026-09-14）
- 限制：云端仅暴露 truths 列表与 report 上报接口；详情接口（/api/truth/upsert）仅内网存在，正文比对待内网访问
- 比对口径：条目名语义映射，非正文比对
