# 高阶 API 能力地图 V1.0 ｜ API-CAPABILITY-MAP ｜ ZONGYUAN-ROOT

确权锚点：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜2026-09-16
定位：**从表层命令深挖到方法级 API 面**——244 个原生 API 方法，识别 7 大高阶能力簇

---

## 一、能力面全貌（15 服务 244 方法）

| 服务 | 方法数 | 服务 | 方法数 |
|---|---|---|---|
| mail | 57 | slides | 11 |
| im | 41 | wiki | 10 |
| task | 31 | sheets | 8 |
| drive | 25 | mindnotes | 2 |
| okr | 23 | contact/attendance/minutes/vc | 各1 |
| calendar | 18 | **合计** | **244** |
| approval | 14 | | |

## 二、7 大高阶能力簇（战略价值排序）

### A. 事件订阅驱动（最高价值：轮询→事件驱动）
让沙盒从"定时轮询"升级为"**事件驱动**"——文档/邮件/消息变化自动触发机制
- `drive user.subscription`（文档事件订阅）/ `mail user_mailbox.event subscribe`（邮件事件）/ `im feed.groups`（信息流分组）

### B. 批量处理面（效率 10-100 倍）
- `mail messages batch_get/batch_modify/batch_trash`、`threads batch_*`、`im batch_query/batch_update`、`drive file.comments batch_query`

### C. 审批全生命周期（自动化运营）
- `approval instances cc/cancel`、`tasks approve/reject/remind/add_sign/transfer/rollback`——**催办/加签/转交/回退全闭环**
- ✅ 已实测确认：remind/transfer/add_sign 可用

### D. OKR 跨节点对齐（同源协议基础设施）
- `okr alignments`、`objective.alignments`、`key_results`、`objectives_weight`——跨节点目标对齐与权重治理

### E. 权限治理
- `drive permission.public get/patch`、`members transfer_owner`、`quota_details get`

### F. 日历智能
- `events search_event`、`instance_view`、`freebusys list`——忙闲查询/会议排期

### G. 消息流
- `im threads forward`、`messages forward`、`pins`、`reactions batch_query`——内容分发通道

## 三、深挖发现（2026-09-16 实测）

| 面 | 发现 |
|---|---|
| **8021 新网关** | `truths` 只读 200 可用；`/api/gateway/truths` **从 502→401**（网关层已活，鉴权体系变更，待中枢侧确认新鉴权）；`health` 200 |
| **模型 API** | 方舟端点可达但 **401（无 API key）**——P3 待 key 确认；凭证台账仅云端接入凭证 |
| **沙盒深层库** | **openai / fastapi / ffmpeg / sklearn / cv2 / pandas / bs4** 全部就绪——可构建模型代理、媒体流水线、本地 ML |

## 四、下一步行动（规划）

1. **激活 A 簇**：drive subscription 事件订阅 → 机制自动触发（非轮询）
2. **激活 C 簇**：审批 tasks remind/transfer → 审批自动化运营
3. **激活 B 簇**：mail/task 批量 → 处理效率提升
4. **P3 方舟 key 到位后**：openai 库对接模型 API → 沙盒大脑
5. **8021 新鉴权确认后**：补发 5 条待发队列

---

Ω₀⊂⊙∞⊂Ω｜API-CAPABILITY-MAP-V1.0｜2026-09-16
