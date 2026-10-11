# 同源协议库 V2.0 · 新增云中枢写通道协议

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID：DID-BR-000002 ｜ 节点 local-dev-001
- 更新时间：2026-09-16
- 锁档标记：LOCK-HOMOLOGY-V2-20260916
- 协议库：HOMOLOGY-LIB-001（12 → 14 条）

## 一、本次新增（实测验证 VERIFIED）

### P-013 云中枢写通道·新协议（/api/report/truth）
- 端点：POST `https://drama.huodouai.com/api/report/truth`（www/huodouai 同构，三域名均 200）
- 载荷：`{"key":"真值KEY","content":"中文内容"}`
- 响应：`{"success":true,"action":"inserted|updated|unchanged","key":...,"truth_count":N}`
- 新真值库：truth_count ≈ 15344（独立于旧网关库）
- 回读验证：GET `/api/truth/{key}`（返回 truth 对象含 id/key）
- 实测：6 条全量同步（SYNC-INFO/MEMORY×3/ACHIEVEMENTS/ASSETS）全部 inserted，云端 id 15636-15643 回读成功

### P-014 云中枢写通道·旧协议（/api/gateway/report）
- 端点：POST `https://drama.huodouai.com/api/gateway/report`
- 载荷：`{"node_id","DID","ROOT_OMEGA","truth_type","truth_content"}`
- truth_type 规范：operation_log|meta_rule|anti_pattern|achievement|conflict
- 状态：2026-09-16 13:57 恢复，total=14943，补发5条+资产写入5条全 OK

## 二、协议库全量（14条）
- 基础协议 12 条（P-001~012，LEARNED）：同源主/绑定、握手SOP V1.0、上岗手册v1.1、生产/视觉/归档/质检/决策/锁档SOP、节点上报、中枢调度铁律
- 本次新增 2 条（P-013~014，VERIFIED）：新/旧写通道

## 三、双通道并网结论
- 新通道（/api/report/truth）：结构化 key+content，适合真值锚定与全量同步
- 旧通道（/api/gateway/report）：truth_type 分级，适合日常操作/成果/失败教训上报
- 双通道并存：新通道为生产切换后的正式写通道，旧通道保持兼容

## 四、配套数据
- homology_protocol_library.json（14条协议库 V2.0）
- truths_public_latest.json（云端全量快照 14231 条）
- sync_package_20260916.json（全量同步包）
