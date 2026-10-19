# openclaw-lite · OpenClaw 轻量化复刻层（云端中枢）

> 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 部署: 2026-10-19 | 版本 V1.0

## 定位
将 OpenClaw 开源 AI Agent 框架的核心能力以轻量方式复刻到云端中枢
（不覆盖现有 gateway_server/a2a_gateway，纯增量扩展，符合全或无法则）。

## 六大模块与端点

| # | 模块 | 端点 | 说明 |
|---|---|---|---|
| 1 | 压缩前记忆刷新钩子 | POST /oc/memory/refresh | 会话压缩前自动提炼关键结论为真值，防遗忘 |
| 2 | 跨Agent记忆迁移 | POST /oc/memory/export | 导出标准格式 zr-memory-v1（agent_id/blocks） |
| | | POST /oc/memory/import | 导入真值（append-only，不覆盖既有） |
| 3 | 统一网关路由层 | POST /oc/router | target 路由表（feishu/truth/octop/a2a/distill/lake/kg/mcp） |
| 4 | 技能安全审查闭环 | POST /oc/skills/submit | 提交技能→静态扫描（危险模式黑名单） |
| | | GET /oc/skills/queue | 审查队列 |
| | | POST /oc/skills/review | approve/reject（danger 级强制拒绝） |
| 5 | 心跳主动待办派发 | POST /oc/heartbeat/todo | 心跳携带待办派发 |
| | | GET /oc/heartbeat/todos | 节点拉取待办 |
| | | POST /oc/heartbeat/todo/ack | 确认完成 |
| 6 | 沙箱执行策略 | POST /oc/exec/sandbox | 白名单命令+危险黑名单+超时+输出限制+审计 |
| 附 | 服务状态 | GET /oc/status | 模块健康总览 |

## 技术栈
- Python http.server（零依赖，复用 truth_store 真值库）
- 服务端口: 127.0.0.1:8935
- nginx 反代: /oc/ → 8935
- 数据: oc_lite.db（skills/todos 两表）+ truth.db（真值 append-only）

## 安全设计
- 鉴权: X-DID 白名单（DID-BR-000002 等），公开端点仅 memory_refresh/router/sandbox
- 技能扫描黑名单: exec/eval/os.system/subprocess/rm -rf/sudo 等 21 条规则
- 沙箱黑名单: 12 条危险模式 + 17 个白名单基础命令
- 沙箱审计: 每次执行写真值 SANDBOX.EXEC.* 留痕

## 测试验证（2026-10-19 全通过）
- 记忆刷新: 真值写入 seq=19379 ✅
- 记忆导出/导入: 1条/1条 ✅
- 路由层: truth 转发 200，非法 target 返回路由表 ✅
- 技能审查: safe 通过 / review 拒绝 / danger 强制拒绝 ✅
- 心跳派单: 派发→拉取→ack 全链路 ✅
- 沙箱: 安全命令执行 / rm -rf 拦截 / kill 白名单拦截 ✅
- 安全边界: 无 X-DID 与伪造 DID 均 401 ✅

## 待深化（后续迭代）
- 技能市场页面（ClawHub 形态）
- 心跳主动派单接入 heartbeat_failover.py（OCTOP 端）
- 路由层支持 OCTOP GET 探测（当前 405 属端点特性）
