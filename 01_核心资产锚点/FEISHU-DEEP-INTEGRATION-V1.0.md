# 飞书全域深度集成方案 · 元极恒一共享大脑 V1.0
**时间**: 2026-09-22 | **DID**: DID-BR-000002 | **确权**: Ω₀⊂⊙∞⊂Ω

---

## 一、已接入资源全景（深度探测结果）

### 1. 云盘 Drive（4个权威根目录）
| 目录 | Token | 内容 |
|------|-------|------|
| 锁档归档库 | NhxjfHmvMlrE4Ad7AaZc0XaHnkc | kernel-core.tar.gz + 数字媒体20+文件 |
| 全域推广库 | U1GGf6thIl2B69dpj4LctXaunbb | cloud_handshake_sync.py + PROMO-META-LAW |
| 终态归档 | LSCDfusvnl07FKdDs3pcWjAsnih | 8层V2全量归档 |
| AIOS归档 | EYtxfeSNglr0oodx0LwclQYZnyg | 火斗云智资产 |

### 2. 任务 Task（2个清单+4个周期任务）
| 清单 | GUID | 任务 |
|------|------|------|
| ZONGYUAN-ROOT全自动定时进化 | 80bc4aa1-d3fe-498b-a93a-72c0eb9ca5f5 | 日进化/周进化/月进化/季进化 |
| 昆仑洞天-玄女PV生产 | b7b52c48-b063-4000-9386-57323428c659 | PV生产流水线 |

### 3. 日历 Calendar
| 日历 | ID | 用途 |
|------|----|------|
| 云智中台ZONGYUAN-ROOT | feishu.cn_FsOdeEMcGprRBGbYyJNIda@group.calendar.feishu.cn | 进化周期日程 |

### 4. 多维表格 Base
| Base | App Token | 状态 |
|------|-----------|------|
| 元极恒一共享大脑 | DgnMbLqZiaIUDKshqCrcD4DvnBg | ⏳ 待建表 |

### 5. 知识库 Wiki
- 节点管理：创建/删除/复制/移动/成员管理
- 知识空间：待探索具体空间

---

## 二、深度集成架构（8模块全打通）

```
                    ┌─────────────────┐
                    │  auto_reporter  │
                    │   调度中心      │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌──────────┐     ┌──────────┐     ┌──────────┐
    │ 云端真值库 │     │ 飞书Base │     │ 飞书云盘 │
    │ www/drama │     │ 上报总表  │     │ 归档目录 │
    └──────────┘     └────┬─────┘     └────┬─────┘
                         │                 │
    ┌────────────────────┼─────────────────┤
    ▼                    ▼                 ▼
┌────────┐        ┌──────────┐     ┌──────────┐
│ 任务Task│        │ 日历Cal  │     │ 文档Doc  │
│ 周期进化│        │ 进化日程  │     │ 知识沉淀 │
└────────┘        └──────────┘     └──────────┘
                         │
                    ┌────┴─────┐
                    │  IM通知   │
                    │ 异常告警  │
                    └──────────┘
```

---

## 三、8模块集成规则

### 模块1：云端真值库（链路A）✅已通
- 主: www.huodouai.com/api/report/truth
- 备: drama.huodouai.com/api/report/truth
- 格式: {key, value}
- 鉴权: X-Capture-Token

### 模块2：飞书Base上报总表（链路B）⏳待建
- App: DgnMbLqZiaIUDKshqCrcD4DvnBg
- 字段: source_node/report_utc/data_cat/payload/hash_sha/security_level/dispatch_status
- 写入: lark-cli base records create

### 模块3：飞书云盘归档（链路C）✅已通
- 锁档库: NhxjfHmvMlrE4Ad7AaZc0XaHnkc
- 终态归档: LSCDfusvnl07FKdDs3pcWjAsnih
- 分类路由:
  - 内核包 → 锁档归档库根目录
  - 媒体文件 → 锁档归档库/03_数字媒体资产库
  - 协议/元法则 → 终态归档/01_真值表与协议
  - 部署脚本 → 终态归档/04_生产级部署

### 模块4：任务周期联动
- 日进化任务 → 每日自动创建+追踪
- 周进化 → 每周一自动汇总
- 月进化 → 每月1日自动锁档
- 季进化 → 每季度架构评审

### 模块5：日历日程自动创建
- 进化节点自动写入"云智中台"日历
- 截止时间自动设置
- 完成后自动标记

### 模块6：文档知识沉淀
- 重要决策自动写入Wiki知识库
- 技术方案自动创建Doc文档
- 白皮书自动归档到云盘

### 模块7：IM异常告警
- 上报失败 → 飞书消息推送
- 红色级风险 → 紧急通知
- 每日进化报告 → 群消息汇总

### 模块8：自动补发闭环
- 失败数据进入retry_queue.json
- 每30分钟自动重试
- 指数退避，最多5次

---

## 四、元法则追加（深度集成V1.0）

### META-DEEP-001: 八模块全打通原则
所有上报必须同时走云端真值库+飞书Base+云盘归档三端，缺一不可。

### META-DEEP-002: 任务-日历联动原则
进化任务必须同步到日历，截止时间必须自动设置。

### META-DEEP-003: 异常即告警原则
任何模块失败必须立即推送飞书IM告警，不得静默失败。

### META-DEEP-004: 分类路由原则
资产按data_cat自动路由到对应飞书目录，不得随意堆放。

### META-DEEP-005: 周期闭环原则
日/周/月/季进化任务自动创建、追踪、完成、归档。

---

## 五、待补全项（优先级排序）

| 优先级 | 事项 | 依赖 |
|--------|------|------|
| P0 | Base上报总表建表 | 飞书tenant_token |
| P0 | crontab每30分钟补发 | 云服务器配置 |
| P1 | 任务自动创建脚本 | lark-cli task |
| P1 | 日历自动写入脚本 | lark-cli calendar |
| P2 | IM告警Webhook | 飞书群机器人 |
| P2 | Wiki知识库节点创建 | lark-cli wiki |

---

**集成版本**: V1.0 | **下次升级**: Base建表后升级V2.0
