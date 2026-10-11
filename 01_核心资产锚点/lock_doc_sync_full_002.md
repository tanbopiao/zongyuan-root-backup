# 云服务器全量同步 V2 + 千问 2.5B 模型诊断

## 元信息

| 字段 | 值 |
|---|---|
| 锁档事件ID | LOCK-SYNC-FULL-20260916-002 |
| 确权锚点 | Ω₀⊂⊙∞⊂Ω |
| DID | DID-BR-000002 |
| 关联规则 | AXIOM-A-035 V1.7 / METALAW.011 |
| 锁档时间 | 2026-09-16 |
| 锁档状态 | FROZEN（只读锁档） |

## 一、背景

执行与云服务器中枢智能的第二次全量同步（V2），覆盖：全量信息、全量记忆、全量成果、全量资产四类同步。

## 二、中枢握手结果

- 网关在线：真值 14580 条 / 节点 13 / 审计 28164
- 中枢脑 `hub-central-agent` 在线（心跳 695，唯一 online 节点）
- 其余 12 节点离线（cloud-main-kernel-001 / cloud-worker-001 / local-main-agent-20260912 等）
- 新节点注册被拒（非同源），改用主节点 `ZR-NODE-DC2E51C0` 上报成功

## 三、全量记忆拉取（云端核心真值）

| 真值Key | 内容 |
|---|---|
| PROTOCOL.API.NODE_REPORT.V1 | 上报 API 规范 v1.0（5 端点） |
| BASELINE.V41.REGISTER.20260915 | 六维整合完成 / 自治指数 51.8% |
| ACTIVATION.NODE_REPORT_GATEWAY.20260915 | 上报网关激活确认 |
| RULE.NAMING.TRUTH_KEY.V1 | 真值命名规范 |
| RULE.CONFIDENCE.SCORING.V1 | 置信度评分标准 |
| PROTOCOL.AUTO_REPORT.INTELLIGENT_AGENT | 智能体自动上报协议 |

## 四、全量资产同步

| 项 | 值 |
|---|---|
| 本地资产 | 290 文件 / 14.6MB |
| 全量包 | 13.2MB zongyuan-local-full-sync-20260916-v2.tar.gz |
| 飞书云盘 | https://my.feishu.cn/file/VNu6bY0t9oJtGdx8ysBcU5ppnEd |
| 清单 | sync_manifest_full_20260916_v2.json（290 条逐路径） |

## 五、上报真值（2 条）

- SYNC.FULL.LOCAL.20260916.002（protocol）✅
- ASSET.LOCAL.FULL.MANIFEST.20260916.002（data）✅

云端真值 14574 → 14580（本轮 +6）

## 六、千问 2.5B 模型诊断（同日实测）

| 探测项 | 结果 | 判定 |
|---|---|---|
| 模型网关 /v1/models | ✅ 在线（OpenAI 兼容） | 服务层正常 |
| ollama-local（千问挂载点） | ❌ Connection refused | ollama 后端未监听 |
| ollama-win | ❌ Connection refused | 同上 |
| nvidia-nim / aliyun | ✅ 可推理（路由 glm-4-flash） | 可用替代后端 |
| doubao | ❌ 403（密钥问题） | 待修复 |

结论：千问 2.5B 已注册到网关，但 ollama 服务进程未监听端口（11434 不通）。最大化利用需：路径A 立即启用 nvidia-nim/aliyun 推理代理；路径B 修复 ollama 服务上线；路径C LoRA 微调/蒸馏（需 GPU 8-12GB）。

## 七、下一步规划

- 云端 12 节点离线巡检与心跳恢复
- 千问 2.5B ollama 服务修复（走审批让中枢执行）
- doubao 后端 403 密钥修复
- 下次全量同步纳入定时调度

---
Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ ZONGYUAN-ROOT ｜ 2026-09-16
