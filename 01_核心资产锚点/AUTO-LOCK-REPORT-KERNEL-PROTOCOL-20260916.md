# 全自动锁档·真值上报·云内核写入协议 AUTO-LOCK-REPORT-KERNEL-V1.0
- 协议ID: ALRK-V1.0 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

## 一、六段闭环流水线
```
①三端锁档 → ②真值生成 → ③主通道上报 → ④同态备援 → ⑤云内核确认 → ⑥回执固化+守卫校验
```

## 二、执行引擎
```bash
python3 auto_lock_report.py \
  --lock-name "锁档名称" --lock-id "LOCK-XXX-20260916" \
  --content-md ./doc.md --truth-key "EVOL.XXX.20260916" \
  --truth-value "真值内容" --truth-type achievement \
  [--sync-key "X-API-Key"]   # 提供则启用同态备援
```

## 三、各段规范
| 段 | 动作 | 成功判定 |
|---|---|---|
| ①锁档 | kernel_lock.sh lock（知识库+台账+云盘+快照） | FROZEN |
| ③上报 | POST /api/report/truth（3次退避重试） | status=reported |
| ④备援 | POST /api/v1/truths/sync（需X-API-Key） | 200 |
| ⑤确认 | GET /api/report/status | 200 |
| ⑥回执 | .lock_report_receipts/{lock_id}_receipt.json + 真值不灭verify | 三源一致 |

## 四、容错
- 主通道阻塞（仲裁积压）→ 退避3次 → 回执标记 blocked → 载荷固化不丢失
- 同态备援Key缺失 → 跳过并记录（SSH可取kg_api.py）
- 锁档失败 → 中断，不进入上报

## 五、衔接
- 真值不灭守卫（NN-META-134/135/136）为收尾校验
- 调度器V1.2部署后，可加段：写入调度器任务队列
- 定时任务（doubao-cron-scheduler）可周期调用本引擎实现"周期锁档上报"
