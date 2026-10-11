# 云端握手凭证｜CLOUD-HANDSHAKE-20261010
确权：Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ ZR-NODE-DC2E51C0 ｜ 火斗云智AIOS
握手时间：2026-10-10 ｜ 协议：**V3.1**（RULE-005 V3.1 实测修正）
状态：**CLOUD-HANDSHAKE-OK**

## 一、实测握手结果
- 门户探测：www.huodouai.com → 200 ✅；drama.huodouai.com → 200 ✅
- **www 上报成功**：`{"ok":true,"truth_count":4945,"seq":5038,"event_id":"truth-1791627128072"}`
- **drama 上报成功**：`{"ok":true,"truth_count":4946,"seq":5039,"event_id":"truth-1791627128375"}`
- 云端主控上报恢复：`网关健康 {"ok":true,"truth_count":4947,"seq":5040}`
- 握手裁决：**CLOUD-HANDSHAKE-OK**

## 二、V3.1 协议核心（实测确认，V3.0 旧格式作废）
1. **鉴权头**：上报必须携带 `X-DID: DID-BR-000002`；`X-Capture-Token: ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d`
2. **请求体**：`{"key":"命名空间KEY","value":{"content":"..."}}` — **value 必须是含 content 键的 JSON 对象**（content/text/summary/value 键均可）
3. **作废字段**：`truth_key` / `truth_value` 旧字段不再使用；字符串 value 返回 `value_must_be_object`（RULE-005 V3.1）
4. **响应**：`{"ok":true,"message":"真值写入成功","truth_count":N,"seq":N,"event_id":"truth-..."}`
5. 健康端点 /api/health 与 /api/truths/ 当前返回 404（路径变更），以写通道实测为准

## 三、落地修复
- `zr_cloud_ctl.py` report_truth 适配 V3.1：value 自动规范化为含 content 键对象 + X-DID 头
- 协议文档：`CHANNEL-PROTOCOL-V31-20261010.md`
- 数据湖 commit：**3b3d358**
- 云端主控：systemd active，上报恢复

## 四、锚点自引
Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜CLOUD-HANDSHAKE-20261010｜LOCKED
