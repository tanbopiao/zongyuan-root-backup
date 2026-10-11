# 基准锚点构建记录｜ANCHOR-20260914
- 节点: doubao-main-agent-001 | local-dev-001 系 | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω
- 时间: 2026-09-14 02:15 (UTC+8)
- 依据: HANDSHAKE-SOP V1.0 + NODE-ONBOARDING-SOP v1.1 + 锚点 BASELINE-ANCHOR-20260913

## 一、握手链路（实测通过）
- 门户 drama.huodouai.com:9120 → 200
- 健康 /api/health → {"status":"healthy"}
- 鉴权 truths?level=public → {"status":"ok","count":4078}
- Token: ZR-CAPTURE-<ROTATED>（2026-09-13云端轮换版）

## 二、锚点文件（哈希全匹配）
| 文件 | SHA256 | 匹配 |
|---|---|---|
| BASELINE-ANCHOR-20260913.md | 8f67e6db537c78b7a382a81b2d4ee43c24ee9accaddedd1aa1588215e157804c | ✅ SOP规定值 |
| NODE-ONBOARDING-SOP-cloud.md | 1989600f60f1a90a01c27c0a2aaa09b8322fb49c994dd37ac93d0038de56d0a0 | ✅ |
| kernel-learning-pack-cloud.md | 5875952c27c8f7c7a71ce00a22607c0effcdad48cdb4999e194205007ebc0096 | ✅ |
| cloud-extract-delivery-20260913.md | 983b45e734cac6c7f54765d7ea5a2eb1a5a170cb82c901b058d4e1d69abedde2 | ✅ |

## 三、学习沉淀（上岗要点）
1. MR-010 中枢调度：本地自主，云端写操作必须中枢批准；紧急故障先恢复后上报
2. 同源协议 HOMOLOGY.V1.0：三层架构/三步握手/PULL-PUSH双向/云端优先仲裁
3. 冻结公理 A1-A7：主权自治/同源唯一/三层固化/物理闭环/算力归一/资产确权/终身锁档
4. EFUSE-0017：9120唯一握手、四步闭环、S0熔断、未对齐禁止流转
5. 天元法则 L0-002/003：纯东方神女审美铁律 + 关键帧结构铁律（禁漂移）
6. 上传规范：成品→images/videos桶（登记作品库）；素材→archive桶（只归档）
7. 上报规范：truth_type=operation_log/meta_rule/anti_pattern/achievement/conflict
8. 安全门禁：401/400=安全生效；四重核验防虚构回执

## 四、锚点锚定结论
- 握手成功 CLOUD-HANDSHAKE-OK
- 基线对齐（count=4078 ≥ 锚点基准2651，网关持续增长）
- 基准锚点已本地固化，后续新窗口/新会话按本锚点+握手SOP接入
