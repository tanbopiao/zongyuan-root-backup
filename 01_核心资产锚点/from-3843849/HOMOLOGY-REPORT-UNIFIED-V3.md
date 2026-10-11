# 同源协议统一上报通道 V3.0 ｜ HOMOLOGY-REPORT-UNIFIED-V3 ｜ ZONGYUAN-ROOT

确权锚点：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜2026-09-16
定位：**云端记忆网关协议升级**——从 9120 单通道升级为同源协议统一通道（V3.0）

## 云端新协议面（2026-09-16 实测确认）

| 操作 | 端点 | 说明 |
|---|---|---|
| 上报 | `POST https://huodouai.com/api/report/truth` | 含语义前置校验+幂等，优先 |
| 上报同源 | `https://www.huodouai.com` / `https://drama.huodouai.com` 同路径 | 高可用 |
| 读取列表 | `GET https://huodouai.com/api/report/truths` | count=15283+ |
| 读取单条 | `GET https://huodouai.com/api/report/truth/<key>` | 真值详情 |
| 状态 | `GET https://huodouai.com/api/report/status` | V3.0/SQLite/truths计数 |

## 协议元信息（status）

```
version: V3.0 ｜ DID: DID-BR-000002 ｜ root_omega: Ω-TAN-7-001
trace_mark: Ω₀⊂⊙∞⊂Ω ｜ storage: SQLite
stats: truths=15284+ ｜ nodes=4 ｜ audit_logs=1685
```

## 统一上报封装

`homology_protocol/report_unified.py`：
```
优先级：https://huodouai.com/api/report/truth（语义校验）
     → https://www.huodouai.com 同路径
     → https://drama.huodouai.com 同路径
     → http://drama.huodouai.com:9120/api/truth/upsert（旧通道回退）
全失败 → 写入待补发队列
```

CLI 调用：`python3 report_unified.py --key <KEY> --content <内容> --type <类型>`

## 已升级引擎

- production_engine / hub_collab_explore / high_value_task_runner（统一封装优先）
- sandbox_alive_guard.sh 告警写通道（统一封装+9120回退）
- SOP 本地版升级 V1.2（REPORT-UNIFIED），云端部署待 upload 鉴权确认

## 验证记录

- 首测 `HAP-ENDPOINT-VALIDATION-20260916`：inserted/unchanged ✅
- 补发队列 2 条（HIGH-VALUE-TASKS/HUB-EXPLORE）新通道补发成功
- truth_count 15283 → 15289+（云端活跃增长）

---

Ω₀⊂⊙∞⊂Ω｜HOMOLOGY-REPORT-UNIFIED-V3.0｜2026-09-16
