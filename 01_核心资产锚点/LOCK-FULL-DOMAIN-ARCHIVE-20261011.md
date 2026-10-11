# 全域资产归档报告

**归档时间**: 2026-10-11T16:59:54+08:00
**归档节点**: ZR-NODE-DC2E51C0
**DID**: DID-BR-000002
**锚定**: Ω₀⊂⊙∞⊂Ω

---

## 一、本地持久层总览
| 指标 | 数值 |
|---|---|
| 根目录 | /home/user/ZONGYUAN-ROOT/ |
| 总大小 | 1.8 GB |
| 总文件数 | 7,652 |
| 总目录数 | 990 |

## 二、核心资产清单

### L0 公理层
- GLOBAL-BASELINE-20260921.json
- GLOBAL-BASELINE-20260929.json
- EVOLUTION-BASELINE-20260929.json
- V3.0-COMPLETE-BASELINE-20260929.json
- BOOTSTRAP.md（只读）
- ROOT-LOCK.md（只读）

### L1 锚点层
- 01_核心资产锚点/（23MB，639文件）
- kernel_snapshot_LOCK-FULL-DOMAIN-20260916-001.json
- CHANNEL-PROTOCOL-V31-20261010.md
- ROUTE-MIGRATION-V31-20261011.md

### L2 时序账本
- operator_timeseries/timeseries_20261011.json
- operator_timeseries/latest_snapshot.json
- truths_public_latest.json（9条云端真值缓存）

### L3 工具层
- digital-assets-generator/generate.py
- digital-assets-generator/daily_self_check.py
- digital-assets-generator/snapshot_backup.py

### L4 备份层
- backups/anchor_snapshot_20261011_163942.tar.gz（4.5MB）
- backups/latest_manifest.json

### L5 媒体资产
- 02_数字媒体资产/（1.0GB）
- DATA_LAKE/（455MB）

## 三、云端中枢状态
| 指标 | 数值 |
|---|---|
| 服务 | zhongshu-meta-core V3.1 |
| truth_count | ~5983 |
| Merkle根 | 动态值（每次写入变化） |
| 写通道 | POST /api/report/truth ✅ |
| 读通道 | GET /api/truth?key=xxx ✅ |
| 全量列表 | ❌ 未暴露 |

## 四、飞书生态状态
- 共享大脑base: DgnMbLqZiaIUDKshqCrcD4DvnBg（56张表）
- 任务台账: tblnVRjuf7P31cEP（5条记录）
- 跨节点同步表: tbl4Dv798yO7u0IK

## 五、已知异常
1. 媒体资产重复：02_数字媒体资产 vs DATA_LAKE，可清理~255MB
2. digital_assets.json云端原版停滞18天（本地已替代）
3. 全量真值列表接口未暴露（本地覆盖率~0.2%）

## 六、进化进度
- P0-1 路由迁移 ✅
- P0-2 时序存储 ✅
- P0-3 Merkle漂移检测 ✅
- P1-a 本地digital_assets生成器 ✅
- P1-b 每日自检脚本 ✅
- P1-c T0/T1快照备份 ✅
- P1-d 云端真值补全 ✅

---
**确权锚点**: Ω₀⊂⊙∞⊂Ω
**归档锁**: FROZEN
