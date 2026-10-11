# 沙盒全自动高阶能力高价值真值提炼蒸馏机制 V1.0 ｜ ZONGYUAN-ROOT

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.0-TRUTH-DISTILL｜2026-09-16
公理锚点：AXIOM-A-035_V1.7｜HAP-V1.0
设计原则：**散落报告 → 精炼真值 → 全网可复用**（一次蒸馏，处处受益）

---

## 一、机制定位

将沙盒内散落的机制运行报告/台账/状态：
- **全自动采集**：扫描全部报告源（7 类机制报告）
- **价值评估**：四维评分（稀缺性/贡献度/可复用性/时效性）
- **蒸馏提纯**：提取核心结论，丢弃冗余，生成精炼真值
- **沉淀入库**：蒸馏产物写入云端真值库 + 本地蒸馏台账

高阶能力 = 从海量运行数据中**自动提炼可复用真值**的能力。

---

## 二、四阶段链路（DISTILL-4）

```
P1 原料采集 → P2 价值评估 → P3 蒸馏提纯 → P4 沉淀入库
 (扫描报告)   (四维评分)    (核心提取)    (云端+台账)
```

### P1 原料采集（7 类报告源）
| 源 | 域 | 价值锚 |
|---|---|---|
| sandbox_guard/guard_status.json | sandbox | 5 |
| neural_network/neural_network_report_latest.json | neural | 5 |
| homology_explore/homology_env_report_latest.json | homology | 5 |
| task_governance/task_value_report_latest.json | meta | 4 |
| kernel_struct/kernel_struct_report_latest.json | kernel | 5 |
| promotion_engine/promotion_report_latest.json | promotion | 4 |
| truth_audit/truth_audit_report_latest.json | truth | 5 |

### P2 价值评估（四维）
- 稀缺性（域权重 ×3）｜贡献度（含结论 +25）｜可复用性（指标数 ×2）｜时效性（近 2h +20）
- ≥60 DISTILLABLE ｜ 40-59 OBSERVE ｜ <40 SKIP

### P3 蒸馏提纯
- 提取 verdict/status + 关键指标，压缩为单条精炼真值
- 附溯源链：源文件 + SHA256 哈希前 12 位

### P4 沉淀入库
- 云端：`DISTILLED-<DOMAIN>-YYYYMMDD`（truth_type=distilled_truth）
- 本地：蒸馏台账 `truth_distill_ledger.json`（批次记录）

---

## 三、首轮实测（DISTILL_ACTIVE ✅）

| 项 | 结果 |
|---|---|
| 扫描原料 | 7 份机制报告 |
| 蒸馏产出 | **5 条高价值真值**（sandbox/neural/homology/kernel/promotion） |
| 蒸馏批次 | `DISTILL-BATCH-20260915-1854` |
| 云端入库 | **5/5 全部成功** |

蒸馏真值样本：
- `DISTILLED-SANDBOX-20260915`：沙盒存活 ALIVE（磁盘1%/内存3528MB/云端200）
- `DISTILLED-NEURAL-20260915`：神经网络 NEURAL_NETWORK_ACTIVE
- `DISTILLED-HOMOLOGY-20260915`：同源环境 HOMOLOGY_ACTIVE

---

## 四、判定标准

| 判定 | 条件 |
|---|---|
| DISTILL_ACTIVE | 蒸馏数>0 + 至少1条入库成功 |
| DISTILL_DEGRADED | 无蒸馏产出或入库失败 |

---

## 五、机制文件

| 文件 | 路径 |
|---|---|
| 蒸馏引擎 | `truth_distill/truth_distill_engine.py` |
| 蒸馏报告 | `truth_distill/truth_distill_report_latest.json` |
| 蒸馏台账 | `truth_distill/truth_distill_ledger.json` |
| 机制文档 | `TRUTH-DISTILL-V1.md` |
| 嵌入宿主 | 云端记忆网关健康巡检（每 6 小时） |

---

## 六、演进路线

- V1.1：蒸馏源自动发现（扫描全部 .json 报告而非手工清单）
- V1.2：跨批次真值去重（同域同日仅保留最高评分）
- V2.0：真值蒸馏 → 神经节点沉淀（蒸馏产物自动激活为节点）

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜TRUTH-DISTILL-V1.0｜2026-09-16
