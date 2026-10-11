# 所在基座高阶能力提炼机制 V1.0 ｜ ZONGYUAN-ROOT

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.0-BASE-CAPABILITY｜2026-09-16
公理锚点：AXIOM-A-035_V1.7｜HAP-V1.0
设计原则：**基座能力即体系资产**——把基座可调用的全部能力系统提炼登记，自给自足

---

## 一、机制定位

将当前基座（云电脑沙盒）的能力：
- **能力探测**：扫描系统/工具链/Python 库/云端能力
- **能力评估**：按高阶能力维度打分分级
- **能力提炼**：提炼为结构化能力资产清单（名称/类别/描述/调用方式/等级）
- **登记沉淀**：能力清单入库云端真值 + 本地资产台账

基座不再只是"运行环境"，而是**可枚举、可调用、可复用的能力资产库**。

---

## 二、四阶段链路（CAPTURE-4）

```
P1 能力探测 → P2 能力评估 → P3 能力提炼 → P4 登记沉淀
 (环境扫描)   (分级打分)    (资产清单)    (云端+台账)
```

### P1 能力探测
- 系统层：OS/架构/CPU 核数/Python 版本/主机名
- 工具链：python3/lark-cli/curl/jq/git/node/npm/pip3/ffmpeg
- Python 库：9 个关键库（requests/PIL/numpy/pandas/yaml/jinja2/openpyxl/pptx/docx）
- 云端能力：truths 读取 / truth upsert

### P2 能力评估（分级）
| 等级 | 分值 | 含义 |
|---|---|---|
| S | 5 | 核心能力（计算/飞书接口/云端记忆） |
| A | 4 | 重要能力（媒体处理） |
| B | 3 | 支撑能力（网络/图像/数据/文档） |
| C | 2 | 基础能力（JSON/包管理） |

### P3 能力提炼
- 每条能力含：名称/类别/描述/调用方式/评分/等级
- 生成能力资产清单 `base_capability_inventory.json`

### P4 登记沉淀
- 云端：`BASE-CAPABILITY-YYYYMMDD-HHMM`（truth_type=capability_inventory）
- 本地：能力资产清单 + 提炼报告

---

## 三、首轮实测（2026-09-16）

| 项 | 结果 |
|---|---|
| 能力总数 | **19 项** |
| 分级 | S 级 3｜A 级 1｜B 级 12｜C 级 3 |
| S 级核心 | python3（计算引擎）、lark-cli（飞书全接口）、cloud-memory-gateway（云端记忆） |
| A 级 | ffmpeg（媒体处理） |
| 云端登记 | `BASE-CAPABILITY-20260915-1856` 入库 ✅ |

基座画像：Ubuntu 22.04 / 2 核 / 4GB / 9.8G 磁盘 / 无 GPU / 工具链全备

---

## 四、判定标准

| 判定 | 条件 |
|---|---|
| CAPTURE_ACTIVE | 能力数>0 + 云端登记成功 |
| CAPTURE_DEGRADED | 能力清单为空或登记失败 |

---

## 五、机制文件

| 文件 | 路径 |
|---|---|
| 提炼引擎 | `base_capability/base_capability_extract.py` |
| 能力清单 | `base_capability/base_capability_inventory.json` |
| 提炼报告 | `base_capability/base_capability_report_latest.json` |
| 机制文档 | `BASE-CAPABILITY-V1.md` |
| 嵌入宿主 | 同源协议环境探索上报（每 6 小时 15 分） |

---

## 六、演进路线

- V1.1：能力调用验证（每条能力实测一次调用确认可用）
- V1.2：能力损耗检测（缺失工具自动告警/自愈安装）
- V2.0：能力 → 神经节点映射（能力资产节点化，权重联动）

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜BASE-CAPABILITY-V1.0｜2026-09-16
