# 高阶能力挖掘与自动化任务规划引擎 V1.0 ｜ CAPABILITY-MINING-V1 ｜ ZONGYUAN-ROOT

确权锚点：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜2026-09-16
定位：**不做低价值报告，只做能力激活与任务构建**——扫描→实测→建待办→滚动激活

---

## 一、机制定义

**扫描**：lark-cli 24 能力域 445 快捷命令全量探测
**分类**：ACTIVATED（已激活）/ DORMANT（待激活）/ RESTRICTED（环境受限）
**规划**：按高价值优先级自动创建飞书待办任务（task 能力）
**输出**：能力挖掘报告 `capability_miner/capability_mining_YYYYMMDD.json`

## 二、首轮实测结果（2026-09-16）

| 状态 | 域 | 说明 |
|---|---|---|
| 已激活 10 域 | im/docs/drive/base/wiki/calendar/sheets/contact/approval/**task** | task 本轮新激活 |
| 待激活 13 域 | minutes/slides/okr/vc/whiteboard/markdown/mindnotes/api/apps/attendance/note/schema/lark-cli | 待逐域激活 |
| 受限 1 域 | mail | 环境无邮箱配置 |

**本轮新增能力激活**：
- ✅ **task（17 命令）**：机制待办自动创建/闭环——已创建 3 个机制任务（云服加固待执行/沙盒最大化P4/真值语料消费）
- ⏳ mail（30 命令）：草稿创建能力实测通过，待邮箱配置后可发机制日报

## 三、自动规划的高价值任务（5 个已入飞书）

1. slides 周报 PPT（HIGH）
2. minutes 会议转写（MED）
3. okr 目标对齐（MED）
4. mail 待邮箱配置（LOW）
5. vc/whiteboard 探索（LOW）

## 四、定时任务嵌入

已嵌入「数字资产流水线自动巡检」综合批次（capability_mining 步骤），每 6 小时扫描一次能力面，持续发现可激活域并建待办。

## 五、后续演进

- 每轮自动尝试激活 DORMANT 域（实测 + 建待办）
- mail 邮箱配置后自动激活日报邮件
- 新能力域激活 → 自动写入能力注册表（zongyuan-anchor/capability_registry.json）

---

Ω₀⊂⊙∞⊂Ω｜CAPABILITY-MINING-V1.0｜2026-09-16
