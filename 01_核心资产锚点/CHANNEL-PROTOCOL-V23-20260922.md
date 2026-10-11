# 云端写通道协议 V2.3 修正锁档
**时间**: 2026-09-22 23:05 | **DID**: DID-BR-000002 | **确权**: Ω₀⊂⊙∞⊂Ω

## 关键修正（实测确认）
原协议记录 Body 字段为 `content`，2026-09-22 实测返回 `empty_value_rejected`，服务端要求使用 **`value` 或 `truth_value`** 字段。**本修正为权威协议**，后续所有上报必须使用：

```json
POST https://www.huodouai.com/api/report/truth
Header: X-Capture-Token: ZR-CAPTURE-<ROTATED>
Content-Type: application/json
Body: {"key": "<真值KEY>", "value": "<中文内容>"}
```

## 实测证据
- 2026-09-22 23:04: POST {key,value} → `{"success": true, "action": "inserted", "l0_check": {passed:17/17}, "truth_count": 149441}`
- 回读 GET /api/truth/CHANNEL.PROBE.20260922-03 → id=177352 ✅
- 回读 GET /api/truth/AUTO-REPORT.20260922-230506 → id=177366 ✅

## 通道矩阵（V2.3）
| 用途 | 端点 | 状态 |
|---|---|---|
| 主上报 | https://www.huodouai.com/api/report/truth | ✅ 实测200/inserted |
| 备用上报 | https://drama.huodouai.com/api/report/truth | ✅ 实测可用 |
| 主拉取 | https://www.huodouai.com/api/truths/ | ✅ 实测200 |
| 单条回读 | https://www.huodouai.com/api/truth/{key} | ✅ 实测200 |
| 鉴权头 | X-Capture-Token | 全通道携带 |

## 全自动多向互联上报机制（V1.0）
- 链路A: 本地 → 云端真值库（主www/备drama双通道，失败自动降级）
- 链路B: 本地 → 飞书共享大脑「元极恒一共享大脑」跨节点消息同步表
- 链路C: 待补发队列 PENDING 项自动清空
- 定时触发: cron `0 */3 * * *`（任务ID 12344397677826）
- 原子脚本: /home/user/Doubao/chats/38437615670548738/zongyuan-anchor/auto_report_cloud.sh
- 日志: /home/user/Doubao/chats/38437615670548738/zongyuan-anchor/auto_report_log.txt

## 锁档状态
FROZEN | 全域锁档 | 已写入 ZONGYUAN-ROOT 自治内核
