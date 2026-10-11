# 锁档文档 · LOCK-V3-P2A-API-OPEN

## 确权锚点
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

## 锁档元数据

| 字段 | 值 |
|------|-----|
| 锁档ID | LOCK-V3-P2A-API-OPEN-20260913-001 |
| 方向 | P2-a 行业标准化API开放 |
| 优先级 | P2 |
| 锁档时间 | 2026-09-13T23:59:00+08:00 |
| 锁档状态 | ARCHIVED |
| 内核版本 | V3.0 |

## 产出清单

| 文件名 | 路径 | 行数 | 类型 | 状态 |
|--------|------|------|------|------|
| kernel_api_server.py | p2a_api/kernel_api_server.py | 835 | FastAPI+uvicorn主服务 | ARCHIVED |
| api_spec.md | p2a_api/api_spec.md | 693 | OpenAPI 3.0.3规范 | ARCHIVED |

## 验收记录

| 验收项 | 要求 | 实际结果 | 状态 |
|--------|------|----------|------|
| py_compile通过 | 主服务语法零错误 | kernel_api_server.py py_compile PASS | PASS |
| FastAPI主路径 | uvicorn可启动 | FastAPI+uvicorn主路径可运行 | PASS |
| 零依赖兜底 | run_standalone() http.server | 无FastAPI环境时自动切换http.server兜底 | PASS |
| 10端点全实现 | /info+内核4+记忆2+同源+本体+神经激活 | 10端点全部实现 | PASS |
| 模拟数据完整 | 57资产/180实例/327关系/48神经节点 | 模拟数据规模达标 | PASS |
| 三层记忆 | L1工作/L2情景/L3语义 | 三层记忆端点可读可写 | PASS |
| 12维状态向量 | 神经激活传播 | 神经激活+传播16节点返回结构完整 | PASS |
| 中间件完整 | 请求日志/X-API-Key认证/120req/min限速/CORS | 4中间件全部挂载 | PASS |
| 业务逻辑解耦 | 业务与Web框架分离 | 核心逻辑不依赖FastAPI | PASS |
| OpenAPI 3.0.3 | 规范文档 | 每端点含method/summary/parameters/requestBody/responses+示例JSON | PASS |
| MCP Tool映射 | 10端点→MCP工具映射表 | 映射表完整 | PASS |
| A2A Task映射 | 10端点→A2A任务说明 | 映射说明完整 | PASS |
| 统一错误格式 | 错误响应schema统一 | 统一错误schema | PASS |
| 冒烟测试 | 10端点全部返回结构完整 | mount/self-check(六维)/evolve/status/memory write+read/homology(漂移检测)/ontology(9实体+200关系)/neural全部PASS | PASS |

## 核心技术指标

| 指标 | 值 |
|------|-----|
| 服务代码行数 | 835行 |
| API规范行数 | 693行 |
| 总代码行数 | 1528行 |
| API端点数 | 10个 |
| Web框架 | FastAPI + uvicorn（主）；http.server（兜底） |
| 中间件 | 4个（日志/认证/限速/CORS） |
| 限速阈值 | 120 req/min |
| 模拟资产 | 57个资产 |
| 模拟实例 | 180个实例 |
| 模拟关系 | 327条关系 |
| 模拟神经节点 | 48个 |
| 三层记忆 | L1工作 / L2情景 / L3语义 |
| 状态向量维度 | 12维 |
| 神经传播节点 | 16节点 |
| 本体实体数 | 9实体 + 200关系 |
| OpenAPI版本 | 3.0.3 |

## 接口与依赖

- **对外接口**：HTTP RESTful API，10端点；OpenAPI 3.0.3规范文档
- **MCP兼容**：10端点映射为MCP Tool，供Claude/类MCP客户端调用
- **A2A兼容**：10端点映射为A2A Task，供Google A2A协议智能体调用
- **内部依赖**：业务逻辑层独立于Web框架，FastAPI与http.server双实现
- **与P0-a集成**：政务平台可视化层通过本API拉取内核状态/审计日志
- **与P0-b集成**：`/kernel/evolve` 触发元闭环；`/kernel/status` 返回内核状态
- **与P1-a集成**：`/neural/activate` 与 `/neural/propagate` 暴露全局工作空间状态
- **与P1-b集成**：`/neural/propagate` 暴露多智能体耦合的群体指标
- **与P2-b集成**：三行业场景通过本API接入内核能力

## 风险与遗留项

| 风险/遗留项 | 说明 | 后续优化方向 |
|-------------|------|--------------|
| 模拟数据 | 当前返回mock数据，未接真实内核 | V3.1接入真实内核对象/记忆/同源数据 |
| 认证简化 | X-API-Key单密钥，无OAuth2/SSO | V3.1引入OAuth2/OIDC/JWT+RBAC |
| 限速单进程 | 进程内限速，多实例需分布式 | V3.2引入Redis分布式限速 |
| 无WebSocket | 仅HTTP请求-响应，无推送 | V3.2引入WebSocket/SSE事件流 |
| 无容器化 | 未提供Dockerfile/K8s manifest | V3.2提供容器化部署方案 |
| 无SDK | 仅HTTP裸接口，无Python/TS SDK | V3.2自动生成OpenAPI SDK |

## 同源校验

- 文件SHA256:
  - `kernel_api_server.py`: `4851951a6a942677501e7eeefc49d6d5357be62eed21739b5f41e9c2cd6416c4`
  - `api_spec.md`: `befe6d6a94085a950f3dc6c64bb75908ce545e2da438619519f337df01ca34f2`
- 锁档哈希链: LOCK-V3-P1B-AGENT-COUPLING-20260913-001 → LOCK-V3-P2A-API-OPEN-20260913-001
- 校验状态: PASS
