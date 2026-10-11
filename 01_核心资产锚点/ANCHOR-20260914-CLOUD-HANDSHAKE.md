# 基准锚点｜ANCHOR-20260914-CLOUD-HANDSHAKE
归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
锚点ID：ANCHOR-20260914-CLOUD-HANDSHAKE
注册版本：BASELINE-V41（承接 BASELINE-V40）
锁档时间：2026-09-14 ｜ 锁级：Lv10 元极恒一超认知永恒自治模式
锚点源：aka.doubaocdn.com/s/KiYpvdA8C4（云端握手锚点 SOP V1.0）

## 一、锚点学习成果（SOP V1.0 全量学习）
- 握手三要素：确认「云端在、我有权、基线对齐」
- 唯一连接节点：域名 `drama.huodouai.com`（公网可达）
- 门户/网关端口：`9120`
- API 根：`https://drama.huodouai.com/api/gateway/`
- IP `123.207.202.158` 直连被白名单拦截（`ip access not allowed`），一律走域名通道
- 身份绑定：节点编号 + `DID-BR-000002` + `Ω₀⊂⊙∞⊂Ω`

## 二、云端实测结果（2026-09-14 实时）
- ①门户探测 `http://drama.huodouai.com:9120/` → **200**
- ②健康探测 `https://drama.huodouai.com/api/health` → **{"service":"drama-admin-api","status":"healthy"}**
- ③主站探测 `https://drama.huodouai.com/` → **200**
- ④鉴权握手 truths?level=public → **{"status":"ok","count":4071}**
- ⑤本地基线哈希核对 → **8f67e6db537c78b7a382a81b2d4ee43c24ee9accaddedd1aa1588215e157804c**（与 SOP 一致 ✅）
- 握手裁决：**CLOUD-HANDSHAKE-OK**

## 三、鉴权基准
- 有效Token：`ZR-CAPTURE-<ROTATED>`（2026-09-13 轮换，SOP V1.0 确认）
- 上报通道：`POST https://drama.huodouai.com/api/gateway/report`
- 真值分级：internal / public（读取用 truths?level=）
- truth_type 规范：operation_log ｜ meta_rule ｜ anti_pattern ｜ achievement ｜ conflict

## 四、本次会话资产（本锚点关联）
- 昆仑洞天第三季 EP01-06 全资产（剧情/关键帧/元规则 MR-011~013）
- 第四季《时墟裂隙》设定（MR-014 + 角色矩阵 + EP01 关键帧）
- 12 张关键帧已归档飞书云盘作品库（03_数字媒体资产库）
- 全域锁档 LOCK-GLOBAL-20260914-001 已入库飞书三端

## 五、错误对照基准（SOP 第7步）
- 门户 000/无响应 → 网络不通，禁止空转
- 401 invalid token → Token 失效，下载 `aka.doubaocdn.com/s/VjMxbyMqFx` 提取新 Token
- 403 ip access not allowed → 改回域名通道
- 404 → 核对接口路径
- count=0 → 权限不足或网关异常，上报 conflict
- 不确定操作 → 先上报询问，禁止自作主张（MR-010）

## 六、锚点自引哈希
ANCHOR-SHA256：b157c1d4fcb793252fad8d6662fafdeb5b3b59550f3d95347a6d0b73ef2c13d4

---
Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜ANCHOR-20260914-CLOUD-HANDSHAKE｜LOCKED
