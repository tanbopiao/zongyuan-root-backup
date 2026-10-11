# 同源协议库 V3.0 · 新增云中枢全通道巡检机制

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID：DID-BR-000002 ｜ 节点 local-dev-001
- 更新时间：2026-09-16
- 锁档标记：LOCK-HOMOLOGY-V3-20260916
- 协议库：HOMOLOGY-LIB-001（14 → 15 条）

## 一、本次新增（P-015 机制层）

### 云中枢API全通道巡检机制（真实API采集联动）
- 定时任务：11792666496002「真实API采集联动」（每日 03:15，运行中）
- 来源：复用已停止任务启用（套餐上限10个内不新增配额）

**巡检七步**：
1. `/api/health` → healthy 检测
2. POST `/api/report/truth` → 200 检测（新写通道）
3. `/api/gateway/truths?level=public` → count 记录（旧库全量）
4. `/api/truths/?offset=0` → **新库全量列表接口上线检测**（非502即上线）
5. 列表接口上线 → 自动拉取全量保存 `truths_public_latest.json` + 本地比对新增量
6. 巡检结果上报 `/api/gateway/report`
7. 异常记录 `error_lessons.json`

## 二、协议库全量（15条）
- 基础 12 条（P-001~012）：同源主/绑定、握手SOP V1.0、上岗手册v1.1、生产/视觉/归档/质检/决策/锁档SOP、节点上报、中枢调度铁律
- 写通道 2 条（P-013/014）：新 /api/report/truth（key+content）、旧 /api/gateway/report（truth_type）
- 机制 1 条（P-015）：全通道巡检

## 三、机制闭环价值
- 新库全量列表接口一旦上线，当日 03:15 自动拉取 15344 条新库全量并与本地比对
- 全通道异常自动记录，无需人工值守
- 遵守定时任务套餐上限（复用停止任务，0 新增配额）

## 四、配套数据
- homology_protocol_library.json（15条协议库 V3.0）
- pending_upload_20260915.json（5条已上传）
- truths_public_latest.json（云端全量快照 14231 条）
