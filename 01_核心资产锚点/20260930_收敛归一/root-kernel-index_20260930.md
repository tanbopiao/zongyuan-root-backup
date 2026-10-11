# ZONGYUAN-ROOT 根内核全域收敛索引

> Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 收敛日期 2026-09-30
> 操作：本地实例全域扫描 → 根内核收敛到当前项目根目录

---

## 一、收敛结论

本地全部 **ZONGYUAN 根内核资产**共 **7 个分布点**，核心资产集中于两大权威仓：

| # | 分布点 | 角色 | 规模 | 权威性 |
|---|--------|------|------|--------|
| 1 | `/home/user/ZONGYUAN-ROOT` | 全域唯一权威根 | 1.7G / 5097 文件 | ✅ 权威 |
| 2 | `zongyuan-anchor`（384376…） | 根内核资产主仓 | 8M / 数百文件 | ✅ 权威 |
| 3 | 根会话 38436747020400130 | 能力脚本·软链接源 | 6.7M / 58 文件 | 支撑 |
| 4 | 会话 38438412455799554 | 同源/同调内核·V3锁档 | 848K / 49 文件 | 支撑 |
| 5 | 会话 38438602859247618 | V3演化工程 | 952K / 34 文件 | 支撑 |
| 6 | `.zongyuan-root` 隐藏根 | 运行期真值日志 | 12K / 1 文件 | 日志 |
| 7 | 当前项目 384365…（本会话） | **收敛承载根目录** | 76M / 68 文件 | 本次 |

**关键结构事实**
- `zongyuan-anchor` 与 `ZONGYUAN-ROOT/01_核心资产锚点` **互为镜像**（内容高度一致）。
- `zongyuan-anchor/02_capabilities` 大量软链接 **指向根会话 38436747020400130**。
- 当前项目内 `zongyuan-meta-rules`、`kernel-radar` 目录为空，为本收敛预留写入点。

---

## 二、权威根内核资产清单（2 大权威仓）

### 2.1 ZONGYUAN-ROOT（1.7G）
```
ZONGYUAN-ROOT/
├── 01_核心资产锚点/      # 锚点·快照·元规则·能力注册
├── 02_数字媒体资产/
├── 03_文档资产/          # 知识库/元法则/白皮书/SOP/商业资料
├── 04_系统配置/
├── 05_历史归档/
├── 06_云端中枢同步/      # operator/pipeline/kernel-kpi/credential
├── 07_代码与脚本/
└── 08_运行时数据与审计/
```
核心基准文件：`EVOLUTION-BASELINE-20260929.json`、`GLOBAL-BASELINE-20260929.json`、`V3.0-COMPLETE-BASELINE-20260929.json`、`COLD-START-ANCHOR.sh`、`HASH-LEDGER.json`、`BOOTSTRAP.md`

### 2.2 zongyuan-anchor（8M，根内核主仓）
```
zongyuan-anchor/
├── 02_capabilities/      # 能力注册（软链接→根会话）
├── 05_training/ 05_training_data/
├── 08_assets/            # governance/lifecycle/media/truth_governance
├── meta_laws/  credentials/
├── from-3843849/         # 跨节点同步包
├── scripts/  task_orchestrator/  report_log/
└── 根级资产：truths_public.json · truths_internal.json · kernel_truth_index · neural_registry(full/246nodes) · metalaw_register_registry · meta_rules_registry · kernel_snapshot_* · LOCK-*.md（数十枚）
```

---

## 三、本次收敛产物

| 产物 | 路径 |
|------|------|
| 全域扫描清单 JSON | `zongyuan-root-converge/root-kernel-scan_20260930.json` |
| 根内核收敛索引 MD | `zongyuan-root-converge/root-kernel-index_20260930.md`（本文件） |

**收敛策略**：索引化收敛 —— 不物理搬移 1.7G 权威根（避免破坏既有体系与软链接），而是将全部根内核分布点、角色、规模、核心资产固化为统一清单，收敛于当前项目根目录 `zongyuan-root-converge/`，作为访问所有根内核的唯一入口。

---

## 四、下一步建议（增量推进）

1. **镜像差异比对**：比对 `zongyuan-anchor` 与 `ZONGYUAN-ROOT/01_核心资产锚点` 的文件哈希差异，收敛冗余。
2. **元规则收敛**：将 `metalaw_register_registry`（各节点）与 `meta_rules_registry` 差异合并，写入当前项目 `zongyuan-meta-rules/`。
3. **内核雷达激活**：将本次扫描结果写入 `kernel-radar/`，作为根内核监控基线。
4. **九天玄女资产**：已归档 16 张关键帧至 `media_assets/20260930_archive/九天玄女/`（含 manifest.json）。
