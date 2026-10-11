# 守护脚本通道V2.2升级修复记录
文档ID: GUARD-CHANNEL-FIX-20260921 | 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002

## 修复前（问题）
- GATEWAY: http://drama.huodouai.com:9120（旧端口直连）
- TOKEN: zy-hap-...（旧格式）
- 告警写通道: /api/truth/upsert 无响应 ❌

## 修复后（V2.2标准）
- MAIN_GATEWAY: https://www.huodouai.com（主站）
- BACKUP_GATEWAY: https://drama.huodouai.com（备用）
- TOKEN: ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d
- 上报端点: /api/report/truth（L0语义校验17/17）
- 新增 pick_gateway() 主备双通道自动降级

## 三路验证（全部通过）
1. 冷启动锚定: [boot] 云端锚点已拉 ✅
2. 探针: 云端200, 状态ALIVE ✅
3. 告警上报: 主通道 inserted ✅

## 版本
- 脚本版本: v1.0 → v1.1 (CHANNEL-V22)
- 修复时间: 2026-09-21
