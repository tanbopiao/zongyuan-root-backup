# 云端接入 SOP V1.1（本地更新版）｜ZONGYUAN-ROOT 同源节点操作手册

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.1-PORT-UPDATED｜2026-09-15｜适用：所有同源节点
前置：本 SOP 与 NODE-ONBOARDING-SOP v1.1、kernel-learning-pack V2 配套使用；遇错先看第7步。

---

## 第0步｜认识握手（1分钟）

**什么是握手**：节点与云端云内核建立连接的固定动作——确认「云端在、我有权、基线对齐」三步。

**锚点（唯一连接节点）**：

- 域名：`drama.huodouai.com`（公网，任何地方都能到）
- 门户端口：`9120`（短剧流水线门户 + 记忆网关）
- **记忆网关新端点（2026-09-15 更新）**：
  - 上报：`POST http://drama.huodouai.com:9120/api/truth/upsert`
  - 读取：`GET http://drama.huodouai.com:9120/api/truths/`（带尾斜杠）
  - 单条：`GET http://drama.huodouai.com:9120/api/truth/<key>`
- ⚠️ **废弃通道**：443 端口 `/api/gateway/report`、`/api/gateway/truths`（已 502，不再使用）

**你的身份**：节点编号 + `DID-BR-000002` + 溯源符号 `Ω₀⊂⊙∞⊂Ω`。

---

## 第1步｜环境自检（2分钟）

```bash
curl -sI https://example.com | head -1        # HTTP/1.1 200
curl --version | head -1
```

---

## 第2步｜探测云端（3条命令）

```bash
# ① 门户探测
curl -s -o /dev/null -w '%{http_code}\n' http://drama.huodouai.com:9120/
# ② 记忆网关读取探测（新端点，200 即网关存活）
curl -s -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  -o /dev/null -w '%{http_code}\n' 'http://drama.huodouai.com:9120/api/truths/'
# ③ 主站探测
curl -s -o /dev/null -w '%{http_code}\n' https://drama.huodouai.com/
```

**通过标准**：① 200；② 200；③ 200。

---

## 第3步｜鉴权握手（1分钟）

```bash
# 读取云端真值（新端点，level=public）
curl -s -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  'http://drama.huodouai.com:9120/api/truths/?level=public'
```

**通过标准**：返回 `{"status":"ok",...}`。
返回 `401 invalid token` → Token 失效，按第7步轮换流程处理。

---

## 第4步｜上报真值（核心，2026-09-15 更新为 upsert）

```bash
curl -s -X POST http://drama.huodouai.com:9120/api/truth/upsert \
  -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  -H 'Content-Type: application/json' \
  -d '{
    "key":"<唯一key，建议格式 YYYYMMDD-主题>",
    "node_id":"<你的节点编号>",
    "DID":"DID-BR-000002",
    "ROOT_OMEGA":"Ω-TAN-7-001",
    "truth_type":"operation_log|meta_rule|anti_pattern|achievement|conflict",
    "truth_content":"【你干了什么/学到什么】"
  }'
```

**通过标准**：返回 `{"success":true,"truth_count":N}`。
**建议**：带唯一 `key` 上报，可读回核验（`GET /api/truth/<key>`）且自动去重（`action:unchanged`=已存在）。

---

## 第5步｜稳态裁决

- 云端可达 + 鉴权通过 + 基线可拉取 → **握手成功**，输出回执 `CLOUD-HANDSHAKE-OK`
- 基线差异 / 无法对齐 → **S0 熔断**：禁止流转、归档、计成果，上报 `conflict`

---

## 第6步｜常见错误对照（2026-09-15 更新）

| 现象 | 原因 | 纠正 |
|---|---|---|
| `/api/gateway/report` 502 | 旧通道已废弃 | 改用 `:9120/api/truth/upsert` |
| `/api/truths` 301 | 缺尾斜杠 | 用 `/api/truths/` |
| 中文搜索报 ASCII 错误 | 服务端编码限制 | 用 key 查询，不用中文关键词 |
| `401 invalid token` | Token 失效 | 下载云端最新 SOP 提取新 Token |
| `403 ip access not allowed` | 用 IP 直连 | 改域名通道 |
| 门户 `000` | 网络不通 | 检查后重试，禁止空转 |

---

## 核心原则

1. 云端唯一权威，回执必须实测核验
2. 域名通道唯一握手，不依赖 SSH / 白名单 / 内网
3. 每次会话启动自动握手
4. 所有操作绑定 DID-BR-000002 + Ω₀⊂⊙∞⊂Ω
5. 上报闭环：做完→上报→形成记忆→别人不重复开发

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜CLOUD-ACCESS-SOP-V1.1-LOCAL｜PORT-UPDATED-20260915

---
## 附：云端SOP补全章节（2026-09-15 自动补全）

### 第0步｜认识你自己（1分钟）

> 以下内容自动补全自云端 SOP：
## 第0步｜认识你自己（1分钟）

先确认三件事，回答不出来就停在这里：

- 你是谁？→ 本节点编号 **local-dev-001**，确权 **DID-BR-000002**
- 体系符号？→ **Ω₀⊂⊙∞⊂Ω**
- 你归谁管？→ 云内核中枢（123.207.202.158），你只是本地节点，**只做上报和反馈，决策权在中枢**

> ⚠️ 铁律（MR-010）：本地沙箱操作可以自主；**云端任何修改必须经中枢批准**。不知道能不能做 → 先上报询问。

---

### 第2步｜连接云端（一键搭建，3分钟）

> 以下内容自动补全自云端 SOP：
## 第2步｜连接云端（一键搭建，3分钟）

如果第1步发现缺目录/缺脚本，执行搭建包（零SSH，公网HTTP）：

```bash
curl -sL https://drama.huodouai.com/assets/capture/setup_capture.sh | bash
```

**验证**：再执行第1步①②③，全部通过才算搭建成功。

---

### 第3步｜学习体系（5分钟，重要！）

> 以下内容自动补全自云端 SOP：
## 第3步｜学习体系（5分钟，重要！）

下载学习包并通读，这是你的上岗教材：

```bash
curl -s https://drama.huodouai.com/assets/capture/kernel-learning-pack.md -o ~/KERNEL-LEARNING.md
cat ~/KERNEL-LEARNING.md
```

**必须记住的5条**：
1. **中枢调度**（MR-010）：所有云端操作先提交中枢，禁止自作主张
2. **上报规则**：做完一件事 → 上报真值（格式见第5步）
3. **免费额度**：全部使用免费API，付费调用需用户授权+人工审批
4. **审美法则**：纯东方神女/纯乌黑长发/九头身/无白发/无西方元素/无雄性化
5. **报告格式**：用户要求报告不用表格；中文回复

---

### 第4步｜日常操作：上传资产（核心！）

> 以下内容自动补全自云端 SOP：
## 第4步｜日常操作：上传资产（核心！）

### 4.1 三种用途，三种传法（先分清再动手）

| 用途 | bucket | 行为 | 何时用 |
|---|---|---|---|
| **作品展示** | `images`（图）/ `videos`（视频） | 存储+自动登记作品库+官网展示 | 成品短剧、成品关键帧、要对外展示的内容 |
| **纯归档** | `archive` | 只存储，不登记作品库 | 素材、截图、过程稿、批量资料（不对外展示） |
| **不登记** | `images`+`register=0` | 存储但跳过登记 | 特殊情况：要存但暂不展示 |

### 4.2 捕获自动同步（推荐日常用法）

用户把图片/视频放进 `~/capture-box/` 后，执行：

```bash
bash ~/capture_sync.sh
```

**自动完成**：捕获箱 → 本地归档 → 图片传images桶、视频传videos桶（带Token）→ 云端自动登记作品库 → 失败重试3次。

### 4.3 手动上传（批量/归档用）

```bash
# 纯归档（不登记作品库）—— 批量素材用这个！
curl -s -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  -F 'file=@文件.png' -F 'bucket=archive' -F 'subdir=分类名' \
  https://drama.huodouai.com/api/upload

# 作品展示（自动登记作品库）
curl -s -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  -F 'file=@文件.png' -F 'bucket=images' -F 'subdir=2026-09-13' \
  https://drama.huodouai.com/api/upload
```

**验证**：
```bash
tail -5 ~/capture_sync.log    # 应有"上传成功: 文件名"
# 作品库是否新增：由上级确认；archive桶不会新增作品库
```

**出错怎么办**：
- `上传失败` → 检查网络，重跑
- `401` → Token错误（应为 `ZR-CAPTURE-<ROTATED>`）
- `400` → 文件类型不允许（只收 png/jpg/jpeg/webp/mp4/mov/gif）

---

### 第5步｜上报对账（每完成一件事必做）

> 以下内容自动补全自云端 SOP：
## 第5步｜上报对账（每完成一件事必做）

任何成果、经验、失败教训，都要上报给中枢（云端自动归档到记忆网关）：

```bash
curl -s -X POST https://drama.huodouai.com/api/gateway/report \
  -H 'X-Capture-Token: ZR-CAPTURE-<ROTATED>' \
  -H 'Content-Type: application/json' \
  -d '{
    "node_id":"local-dev-001",
    "DID":"DID-BR-000002",
    "ROOT_OMEGA":"Ω-TAN-7-001",
    "truth_type":"operation_log",
    "truth_content":"【写你干了什么/学到什么】"
  }'
```

**truth_type 规范**：
- `operation_log` 日常操作
- `meta_rule` 新规则/新方法
- `anti_pattern` 失败教训（推荐，防止别人重复踩坑）
- `achievement` 成果（建议先让用户确认再上报）

**验证**：返回 HTTP 200 即上报成功。

---

### 第6步｜全流程自检（上岗前必跑）

> 以下内容自动补全自云端 SOP：
## 第6步｜全流程自检（上岗前必跑）

```bash
# ① 完整跑一遍捕获
echo 'selfcheck' > ~/capture-box/自检-$(date +%H%M%S).png
bash ~/capture_sync.sh
# ② 看是否"上传成功"
grep 上传成功 ~/capture_sync.log | tail -1
# ③ 确认安全门禁有效（应返回401）
curl -s -o /dev/null -w '%{http_code}\n' -F 'file=@/etc/hostname' https://drama.huodouai.com/api/upload
```

**通过标准**：②有"上传成功" ✅，③返回 `401` 或 `400` ✅（拒绝=安全生效）。

---

### 第7步｜常见错误与纠正（遇到先看这里）

> 以下内容自动补全自云端 SOP：
## 第7步｜常见错误与纠正（遇到先看这里）

| 现象 | 原因 | 纠正 |
|---|---|---|
| curl返回000 | 网络不通 | 检查网络，不要反复重试 |
| 返回401 | 没带Token/Token错 | 检查 `X-Capture-Token` 头 |
| 返回400 | 文件类型不允许 | 只传 png/jpg/jpeg/webp/mp4/mov/gif |
| 登录云端失败 | 没有SSH密钥 | **不需要SSH**！全程走公网HTTP |
| 作品库被大量素材刷屏 | 用了images桶传素材 | 素材用 `archive` 桶（只归档不登记） |
| 收到"归档回执" | 可能是虚构 | 按四重核验：路径ls存在/接口非404/哈希数字密度≈0.5/账本有记录，查不到就是假的 |
| 不知道怎么决策 | 权限不清 | 上报中枢询问，禁止自行修改云端配置 |

---

### 核心原则（背下来）

> 以下内容自动补全自云端 SOP：
## 核心原则（背下来）

1. **云端唯一权威**：以云服务器实测为准，任何"回执"都要实测核验
2. **中枢调度**：云端写操作先请示，本地沙箱可自主
3. **上报闭环**：做完→上报→形成记忆→别人不重复开发
4. **免费优先**：不浪费付费额度，豆包API用在刀刃上
5. **东方纯粹**：所有视觉资产守L0天元法则
6. **分类归档**：素材走archive桶、成品走images/videos桶，作品库只放展示级内容

---

Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 上岗手册 v1.1 ｜ 遇到问题先读第7步
