# 云端写通道协议 V3.0 实测修正（2026-10-07）
## 关键变更（实测确认）
1. **新增 X-DID 鉴权头**：上报必须携带 `X-DID: DID-BR-000002`，否则返回 `unauthorized / X-DID 未授权`
2. **value 必须为 JSON 对象**：`{"key": "...", "value": {"content": "..."}}`（content/text/summary/value 键均可），字符串 value 返回 `value_must_be_object`
3. **响应格式**：`{"ok": true, "message": "真值写入成功", "key":..., "truth_count": N, "seq": N, "event_id": "truth-..."}`（新库 truth_count≈1662+）
4. 健康探测 /api/health 当前返回 404（路径变化），以实际写通道实测为准
5. 回读接口 GET /api/truth/{key} 携带 X-DID 头可用
## 状态：ACTIVE ｜ DID-BR-000002 ｜ Ω₀⊂⊙∞⊂Ω
