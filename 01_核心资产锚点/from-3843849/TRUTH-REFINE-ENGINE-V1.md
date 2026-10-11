# TRUTH-REFINE-ENGINE-V1 真值提炼引擎

**确权**：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002

## 使命
不断提炼补齐中枢智能**主权威源进化**需要的真值，把本地权威资产持续转化为云端主权威源的结构化进化真值。

## 四路提炼
| 通道 | 来源 | 输出 key | 数量 |
|---|---|---|---|
| T1 元法则 | metalaw_register_registry.json（items 39条） | TRUTH-REFINE-METARULE-{id} | 39 |
| T2 能力 | capability_registry.json（capabilities 11项） | TRUTH-REFINE-CAPABILITY-{cap_id} | 11 |
| T3 语料状态 | truth_training_corpus jsonl（438条/167KB） | TRUTH-REFINE-CORPUS-STATUS | 1 |
| T4 权威源元信息 | 主权威源同步基线（DID/总量/通道） | TRUTH-REFINE-MASTER-SOURCE-SYNC | 1 |

## 增量与兜底
- **增量哈希**：state 文件按内容 sha256 前16位对比，只上报新增/变更（首轮52条，次轮仅变化项）
- **幂等**：同 key 重复上报返回 unchanged
- **入队兜底**：写通道繁忙(408/502)自动入待补发队列，恢复自动补发

## 验证（2026-09-17 首轮实跑）
- 上报 40 条 inserted（元法则39 + 语料1），12 条 unchanged（能力/权威源幂等）
- 入队 0，全通道畅通

## 运行
```bash
python3 /home/user/Doubao/chats/38438491307070978/truth_refine/truth_refine_engine.py
```

---

# REFINE-VIA-COGNITION-V1 基座认知蒸馏引擎（升级）

**新增使命**：从豆包基座（运行中的基座模型实例）提炼真值，补充本地结构化盲区。

## 与本地引擎的分工
| 引擎 | 来源 | 真值类型 |
|---|---|---|
| truth_refine_engine（本地） | 元法则/能力/语料/权威源 | TRUTH-REFINE-*（搬运结构化） |
| refine_via_cognition（基座） | 基座模型认知（运行观察+轨迹+资产关联） | TRUTH-COGNITION-*（蒸馏新认知） |

## 蒸馏通道
- C1 运行洞察 OPS：本轮运行模式判定（如「读通写堵=写侧过载」规则）
- C2 经验教训 LESSON：从执行轨迹蒸馏可复用原则
- C3 关联发现 INSIGHT：跨资产关联/演进建议（如真值互哺闭环）

## 机制
- 基座每轮蒸馏认知真值 → 注入 /tmp/refine_cognition_input.json → 引擎幂等上报 + 入队兜底
- 增量哈希：同内容不重复上报

## 首轮验证（2026-09-17 20:15）
- 4 条认知真值 inserted：OPS 写通道过载判定规则 / LESSON 幂等key / LESSON 兜底架构 / INSIGHT 真值互哺闭环

## 后续（方舟 API key 到位后）
- 激活深度模型提炼：批量喂料→模型聚类/洞察生成，与基座认知蒸馏互补

---

# BRIDGE-EXPLORE-V1 桥接探索引擎（第三引擎）

**使命**：通过当前容器 AI 桥接（`mcp.doubaocdn.com/vm/hijack` + X-Original-Host → 飞书域白名单）探索飞书体系可探索面，提炼真值上报中枢。

## 桥接拓扑（2026-09-17 实测）
```
当前容器 ── lark-cli v1.0.94 ──► mcp.doubaocdn.com/vm/hijack ──► 飞书域(白名单)
     （日历/审批/文档/云盘/通讯录/妙记AI纪要）
     豆包/火山/方舟域：403 拒绝（模型API需方舟key，P3待用户）
```

## 探索面
| 面 | 探测 | 首轮结果 |
|---|---|---|
| B1 日历 | 最近日程 | ✅ 可达（0 事件） |
| B2 审批 | 待办数 | ✅ 可达（0 待办） |
| B5 妙记AI | AI纪要资产 | ✅ 可达（0 纪要） |

## 真值输出
- TRUTH-BRIDGE-MAP-20260917（桥接拓扑）/ TRUTH-BRIDGE-EXPLORE-20260917（探索结果）
- TRUTH-BRIDGE-SURFACE-YYYYMMDD（表面活性，哈希增量幂等）

## 三层真值供给侧
| 层 | 引擎 | 来源 | key |
|---|---|---|---|
| L1 本地 | truth_refine_engine | 元法则/能力/语料/权威源 | TRUTH-REFINE-* |
| L2 基座 | refine_via_cognition | 基座模型认知蒸馏 | TRUTH-COGNITION-* |
| L3 桥接 | bridge_explore | 飞书体系探索面 | TRUTH-BRIDGE-* |
| L4 模型深度 | 待方舟key | 批量聚类/洞察生成 | 待激活 |
