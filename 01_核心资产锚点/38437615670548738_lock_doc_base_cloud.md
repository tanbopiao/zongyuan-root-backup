# 基准锚点重建 · 云端握手学习成果锁档

## 头部元信息
- 确权锚点：Ω₀⊂⊙∞⊂Ω
- DID：DID-BR-000002
- 主权根：Ω-TAN-7-001
- 归档根节点：ZONGYUAN-ROOT
- 文档类型：基准锚点重建·SOP学习·握手成果
- 锁档状态：FROZEN
- 锁档日期：2026-09-14
- 锚点地址：aka.doubaocdn.com/s/KiYpvdA8C4
- 锁档标记：LOCK-BASE-CLOUD-20260914
- 关联锁档：LOCK-BASE-20260914-KiYpvdA8C4（历史锚点）、LOCK-MEMGATE-20260914（记忆网关）

## 一、锚点真实内容确认

通过 `aka.doubaocdn.com/s/KiYpvdA8C4` 获取到锚点真实文档：《云端握手锚点 SOP V1.0｜同源节点接入操作手册》

### 锚点核心信息
| 项 | 值 |
|----|----|
| 握手域名 | drama.huodouai.com（公网唯一通道） |
| 门户/网关端口 | 9120 |
| API 根 | https://drama.huodouai.com/api/gateway/ |
| 鉴权头 | X-Capture-Token |
| 有效Token | ZR-CAPTURE-<ROTATED> |
| 基线锚点文件 | BASELINE-ANCHOR-20260913.md（公网 aka.doubaocdn.com/s/GSXW7aZfcZ） |
| 基线哈希 | 8f67e6db537c78b7a382a81b2d4ee43c24ee9accaddedd1aa1588215e157804c |
| 上报接口 | POST https://drama.huodouai.com/api/gateway/report |
| truth_type 规范 | operation_log / meta_rule / anti_pattern / achievement / conflict |

### 关键认知修正
1. **正确通道是域名而非 IP**：`drama.huodouai.com` 域名通道放行；IP `123.207.202.158` 直连被云端白名单拦截（`ip access not allowed`）。此前探测 123.207.202.158 的 /api/v1/* 全部 404/502，并非后端未部署，而是通道错误。
2. **云端是唯一权威**：决策权在中枢（云内核），本地节点只做上报和反馈（MR-010 铁律：本地沙箱可自主，云端任何修改必须经中枢批准）。
3. **上报闭环**：做完→上报→形成记忆→别人不重复开发。

## 二、云端握手实测结果（2026-09-14）

| 步骤 | 命令/目标 | 结果 |
|------|-----------|------|
| ① 门户探测 | http://drama.huodouai.com:9120/ | ✅ HTTP 200 |
| ② 健康探测 | https://drama.huodouai.com/api/health | ✅ {"service":"drama-admin-api","status":"healthy"} |
| ③ 主站探测 | https://drama.huodouai.com/ | ✅ HTTP 200 |
| ④ 鉴权握手 | GET /api/gateway/truths?level=public | ✅ {"status":"ok","count":4559} |
| ⑤ 基线下载 | aka.doubaocdn.com/s/GSXW7aZfcZ | ✅ 2642字节，SHA-256 完全匹配 8f67e6db... |
| ⑥ 上报验证 | POST /api/gateway/report ×2 | ✅ success=true，synced=1 |

**握手结论：CLOUD-HANDSHAKE-OK**（云端可达 + 鉴权通过 + 基线可拉取 + 上报闭环验证）

## 三、SOP 与关联文档学习清单

| 文档 | 来源 | 学习要点 |
|------|------|----------|
| 云端握手锚点 SOP V1.0 | aka.doubaocdn.com/s/KiYpvdA8C4 | 7步握手流程、错误对照、核心原则 |
| 昆仑洞天·新节点上岗手册 SOP v1.1 | aka.doubaocdn.com/s/VjMxbyMqFx | 环境自检/连接云端/学习体系/上报规范/MR-010铁律 |
| 基线锚点 BASELINE-ANCHOR-20260913 | aka.doubaocdn.com/s/GSXW7aZfcZ | Token轮换记录、四端归档闭环基准、记忆网关基准 |
| 云端真值库（实时拉取） | GET /api/gateway/truths | public 4559 / internal 4636，含 ACTIVATION/ARCHIVE/AUDIT/BASELINE 等分类 |

## 四、云端真值库最新动态（拉取摘要）

- 真值总数：**4643**（本次上报后：operation_log +1，achievement +1）
- 分类示例：ACTIVATION.DRAMA_SEMIAUTO / ARCHIVE.SOP-HOMOLOGY-SSH / AUDIT.PIPELINE-CLOSED-LOOP / BASELINE.GLOBAL.V1.0 / ANOMALY_DETECT 系列 / AUTOLOCK.PIPELINE.V1.0 / AUTONOMY.MODE_START...
- 可读分级：internal / public 双通道

## 五、本次上报记录（云端入库）

| 序号 | truth_type | 内容摘要 | 云端返回 |
|------|-----------|----------|----------|
| 1 | operation_log | 基准锚点重建全流程：获取锚点SOP/学习上岗手册/下载基线核验哈希/握手四步实测 | success=true, total 4642 |
| 2 | achievement | 成果：CLOUD-HANDSHAKE-OK，锚点学习完成，基线哈希PASS，真值库4559→4643 | success=true, total 4643 |

## 六、后续动作指引（对接云端）

1. **会话启动自动握手**：触发词「元极恒一」「启动ROOT」「加载ZONGYUAN-ROOT」→ 执行 ①门户②健康③主站④鉴权四步探测
2. **每次任务完成上报**：POST /api/gateway/report（带 X-Capture-Token），truth_type 按规范
3. **基线漂移检测**：每次下载 BASELINE-ANCHOR 文件核验哈希，不一致即 S0 熔断上报 conflict
4. **Token 失效处理**：401 时从云端最新 SOP（aka.doubaocdn.com/s/VjMxbyMqFx）提取新 Token
5. **云端修改铁律**：任何云端修改先上报询问中枢批准（MR-010），本地沙箱操作可自主

## 七、漂移熔断 SOP

- 阶段一 检测：六维扫描 + 云端基线哈希比对 + 鉴权Token有效性
- 阶段二 判定：哈希不一致 / Token失效(401) / 上报失败 → 标记异常
- 阶段三 动作：S0熔断，禁止流转/归档/计成果，上报 conflict 至中枢
- 阶段四 复核：下载最新基线+提取新Token+重新握手，确认后恢复

## 八、完整性校验

- 本锁档文档与云端上报记录（total 4643）双向绑定
- 基线锚点文件已存本地：zongyuan-anchor/BASELINE-ANCHOR-20260913.md（哈希核验PASS）
- SOP文档已存本地：zongyuan-anchor/CLOUD-SOP-v1.1.md
- 锚点SOP V1.0 全文已学习（web_fetch 完整读取）
