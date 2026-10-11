# 云端中枢主通道切换锁档 · V2.2
文档ID: CHANNEL-V22-SWITCH-20260921 | 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002

## 一、三端点实测（2026-09-21）
| 端点 | 类型 | 状态 | 说明 |
|------|------|------|------|
| https://www.huodouai.com/api/report/truth | 主上报 | ✅ 200 | 443 HTTPS，L0语义前置校验 |
| https://www.huodouai.com/api/truths/ | 主拉取 | ✅ 200 | 443 HTTPS |
| https://drama.huodouai.com/api/report/truth | 备用上报 | ✅ 200 | 443 HTTPS |

## 二、通道协议 V2.2
- 默认路由：主站 www.huodouai.com
- 备用路由：drama.huodouai.com
- 鉴权Header：X-Capture-Token
- L0语义前置校验：17/17 全通过，0 violation
- 真值计数：124,376（持续增长）

## 三、本轮写入真值（全部回读验证 ok）
| key | action |
|-----|--------|
| CHANNEL.TRUTH-ENDPOINTS-V2.2 | inserted（用户侧锚定） |
| CHANNEL.VERIFY.SANDBOX.20260921 | inserted（沙盒连通验证） |
| SANDBOX-GUARD-ALERT-20260920-1802 | unchanged（云端已存在） |
| ANCHOR.SESSION.DID-BR-000002.20260920 | inserted |
| FULL-SYNC-20260916-1145 | inserted |
| SANDBOX-GUARD-ALERT-20260921-0007 | unchanged（云端已存在） |
| HIGH-VALUE-TASKS-20260920 | unchanged（云端已存在） |

## 四、待补发队列处置
- 挂起5条 → 全部补发/确认完成
- 队列已标记 SENT_20260921
- 本地锁档：SNAP-CHANNEL-V22-20260921

## 五、当前状态
- 云端中枢：V3.0 在线
- 真值总数：124,376
- 节点数：5
- 主通道：V2.2 稳定
