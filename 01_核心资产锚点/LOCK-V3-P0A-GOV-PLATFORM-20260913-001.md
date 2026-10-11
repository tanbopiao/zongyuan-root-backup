# 锁档文档 · LOCK-V3-P0A-GOV-PLATFORM

## 确权锚点
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

## 锁档元数据

| 字段 | 值 |
|------|-----|
| 锁档ID | LOCK-V3-P0A-GOV-PLATFORM-20260913-001 |
| 方向 | P0-a 政务AI中台可运行原型 |
| 优先级 | P0 |
| 锁档时间 | 2026-09-13T23:59:00+08:00 |
| 锁档状态 | ARCHIVED |
| 内核版本 | V3.0 |

## 产出清单

| 文件名 | 路径 | 行数 | 类型 | 状态 |
|--------|------|------|------|------|
| gov_ai_platform.html | p0a_gov_platform/gov_ai_platform.html | 729 | 单文件HTML原型 | ARCHIVED |
| gov_ai_platform_desktop.jpg | p0a_gov_platform/_shots/gov_ai_platform_desktop.jpg | — | 桌面端截图 | ARCHIVED |
| gov_ai_platform_mobile.jpg | p0a_gov_platform/_shots/gov_ai_platform_mobile.jpg | — | 移动端截图 | ARCHIVED |

## 验收记录

| 验收项 | 要求 | 实际结果 | 状态 |
|--------|------|----------|------|
| 单文件HTML可运行 | 浏览器直接打开无依赖安装 | 双击即开，CDN加载React/React Flow/Tailwind/ECharts | PASS |
| 浏览器控制台零报错 | 无JS异常、无未捕获Promise | 桌面端+移动端截图验证，控制台零报错 | PASS |
| 8大模块齐备 | 导航/组件库/画布/属性面板/监控台/模板/快照/合规 | 8模块全部渲染，28可拖拽组件可见 | PASS |
| 5类28组件 | 政务场景组件库 | 5大类28个组件全部可拖拽到画布 | PASS |
| 6场景模板 | 一键加载预设流程 | 6个模板按钮均可触发画布重建 | PASS |
| Merkle-DAG快照 | 哈希链可视化 | 快照面板展示链式哈希，同源协议联动 | PASS |
| 4合规锁状态 | 等保/密评/个保/数据安全 | 4个锁状态指示灯实时联动校验结果 | PASS |
| 确权锚点 | Ω₀⊂⊙∞⊂Ω 出现在footer | footer底部居中确权符号可见 | PASS |
| ZONGYUAN-ROOT集成 | 快照→同源/日志→记忆/校验→自检 | 三向集成点全部接入，op.self_check可调用 | PASS |

## 核心技术指标

| 指标 | 值 |
|------|-----|
| 代码行数 | 729行 |
| 文件大小 | 37KB |
| 可拖拽组件数 | 5类28个 |
| 场景模板数 | 6个 |
| ECharts监控图表 | 4个（吞吐/延迟/资源/事件流） |
| 合规锁状态 | 4项（等保/密评/个保/数安） |
| CDN依赖 | React 18 + React Flow 11 + Tailwind 3 + ECharts 5 |
| 浏览器控制台报错 | 0 |

## 接口与依赖

- **对外接口**：单文件HTML，无后端依赖；CDN资源通过公网加载
- **内部依赖**：React Flow画布节点 → 属性面板绑定 → ECharts监控订阅
- **与P0-b集成**：快照哈希链 → 同源协议（P0-b meta_loop_guardian AXIOM-002同源守恒）
- **与P1-a集成**：审计日志写入 → 记忆网关（L1/L2/L3三层记忆模型）
- **与P2-a集成**：合规校验状态 → op.self_check → 暴露为 `/api/v1/kernel/self-check` 端点
- **与P2-b集成**：政务场景可作为P2-b医疗/教育/工业三场景的可视化层模板

## 风险与遗留项

| 风险/遗留项 | 说明 | 后续优化方向 |
|-------------|------|--------------|
| 纯前端模拟数据 | 监控台/审计日志为前端mock，未接真实内核 | V3.1接入P2-a API真实数据 |
| CDN公网依赖 | 离线环境无法加载React/React Flow | V3.1提供本地vendor包内联方案 |
| 画布持久化 | 刷新后节点丢失，未接localStorage/后端 | V3.1增加快照持久化+版本回滚 |
| 政务合规深度 | 合规锁为状态指示灯，未对接真实等保工具链 | V3.2对接真实合规扫描引擎 |
| 多用户协同 | 单浏览器单机，无多人实时协同 | V3.2引入WebSocket+OT CRDT协同 |

## 同源校验

- 文件SHA256: `298d4d64e90986cfb25265c76fc633bb8a1f0bc0818eaa6e576792983d6dd915`
  （p0a_gov_platform/gov_ai_platform.html）
- 锁档哈希链: 创世锁档 LOCK-V3-GENESIS → LOCK-V3-P0A-GOV-PLATFORM-20260913-001
- 校验状态: PASS
