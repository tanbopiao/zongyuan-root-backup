# COS资产本地归档索引（飞书归档版）

> 锁档事件: LOCK-COS-ARCHIVE-INDEX-20260911
> 确权锚点: Ω₀⊂⊙∞⊂Ω | DID: DID-BR-000002
> 归档通道: 飞书知识库（本文档）+ 多维表格台账 + 服务器本地
> 状态: FROZEN | 日期: 2026-09-11 15:01

**背景**：腾讯云COS存储桶已由用户主动删除（流量费用高）。本索引为删除前完整同步清单（1007项）的本地归档，全部资产源头完好保留于服务器 /opt/ZONGYUAN-ROOT/。

---

# ZONGYUAN-ROOT · COS资产本地归档索引

> 确权锚点: Ω₀⊂⊙∞⊂Ω | DID: DID-BR-000002 | 生成时间: 2026-09-11 14:58
> 背景: 腾讯云COS存储桶已由用户主动删除（流量费用高）。本索引为删除前完整同步清单（1007项）的本地归档。

## 总览

| 指标 | 数值 |
|---|---|
| 资产总数 | **1007** |
| 总大小 | **225.9 MB** |
| 主导格式 | JSON(549) / Python(203) / Markdown(115) |
| 最大单项 | models/bge-small-zh模型 ~93.6MB |

## 目录分布（按文件数）

| 目录 | 文件数 | 大小 |
|---|---|---|
| locks | 267 | 0.65MB |
| scripts | 87 | 0.29MB |
| (root) | 78 | 0.51MB |
| engine | 47 | 0.16MB |
| ops_changes | 42 | 0.02MB |
| kunlun-assets | 40 | 0.13MB |
| crop_quarantine | 35 | 0.36MB |
| archive | 32 | 0.06MB |
| git-bridge | 31 | 0.14MB |
| archives | 30 | 0.05MB |
| services | 22 | 5.19MB |
| models | 20 | 184.27MB |
| core | 19 | 0.07MB |
| assets | 17 | 22.07MB |
| memory | 16 | 0.08MB |
| inspect | 13 | 0.07MB |
| snapshots | 12 | 0.02MB |
| asset-library | 12 | 0.02MB |
| config | 11 | 0.01MB |
| identity | 11 | 0.02MB |
| cloud | 10 | 0.03MB |
| showcase-page | 10 | 0.09MB |

## 关键资产高亮

### 1. 内核链与锁档（locks/267 · kernel/ · snapshots/）

```
locks/LOCK-ALL-APIS-CONFIG-20260910-022637.json
locks/LOCK-FINAL-MINIMAL-TRUTH-20260910-015541.json
locks/LOCK-GLOBAL-TRUTH-SUMMARY-20260910-013530.json
locks/LOCK-HYBRID-COMPUTE-SECURITY-20260910-020743.json
locks/LOCK-OP-SCHED-DEPLOYMENT-20260910-013948.json
locks/LOCK-OP-SCHED-FULL-OPTIMIZATION-20260910.md
locks/LOCK-OP-SCHED-NGINX-PROXY-20260910-015341.json
locks/LOCK-OP-SCHED-WEB-BACKEND-20260910-014408.json
locks/LOCK-ROOT-KERNEL-ALIGNMENT-20260910-012645.json
locks/LOCK-SELF-LEARNING-LIGHT-20260909033559.json
... (共267条锁档记录)
```

### 2. 短剧IP资产（assets/ 17项 · 22.1MB）

- `assets/drama-episode1/ASSET_MANIFEST.md` (2KB)
- `assets/drama-episode1/COS_LOCK_SNAPSHOT.json` (2KB)
- `assets/drama-episode1/characters/烬_角色母版.png` (1721KB)
- `assets/drama-episode1/characters/玄一_角色母版.png` (1707KB)
- `assets/drama-episode1/characters/苍玄_角色母版.png` (1565KB)
- `assets/drama-episode1/keyframes_landscape/01_金色符文星尘.png` (1344KB)
- `assets/drama-episode1/keyframes_landscape/02_黑色裂隙.png` (1695KB)
- `assets/drama-episode1/keyframes_landscape/03_神女觉醒.png` (1717KB)
- `assets/drama-episode1/keyframes_landscape/04_九尾现身.png` (2115KB)
- `assets/drama-episode1/keyframes_landscape/05_苍玄降临.png` (1833KB)
- `assets/drama-episode1/keyframes_portrait/01_金色符文星尘_竖屏.png` (1692KB)
- `assets/drama-episode1/keyframes_portrait/02_黑色裂隙_竖屏.png` (1253KB)
- `assets/drama-episode1/keyframes_portrait/03_神女觉醒_竖屏.png` (1835KB)
- `assets/drama-episode1/keyframes_portrait/04_九尾现身_竖屏.png` (2281KB)
- `assets/drama-episode1/keyframes_portrait/05_苍玄降临_竖屏.png` (1831KB)
- `assets/drama-episode1/scripts/EP01_剧本_裂隙觉醒.md` (1KB)
- `assets/drama-episode1/scripts/EP01_视频脚本_预告片.md` (1KB)

### 3. AI模型（models/ 20项 · 184.3MB）

- `models/bge-small-zh-onnx/model.onnx.data` (~93.6MB) — 向量模型ONNX权重
- `models/models/BAAI--bge-small-zh/snapshots/master/pytorch_model.bin` (~93.6MB) — bge-small-zh原始权重

### 4. 服务与API（services/ · scripts/ · gov_api/ · identity_api/ · drama-admin-api/）

```
services/baidu_netdisk/baidu_netdisk_gateway.py
services/feishu_gateway/feishu_gateway.py
services/ima_gateway/ima_client.py
services/ima_gateway/ima_gateway.py
services/op_scheduler/.env.template
services/op_scheduler/__init__.py
services/op_scheduler/cloud_worker.py
services/op_scheduler/config.json
```

### 5. 真值与图谱（truth/ · knowledge_graph/）

```
truth/API_CONNECTIVITY_TRUTH_20260909.md
truth/CLEAN_API_TRUTH_20260909.md
truth/DETAILED_API_LIST_20260909.md
truth/FINAL_MINIMAL_TRUTH_V1.0.json
truth/FULL_ASSET_SUMMARY_20260909.md
truth/GLOBAL_TRUTH_SUMMARY_20260910.md
knowledge_graph/kg_graph.json
```

### 6. 敏感凭证（credentials/ 7项 — 注意保护）

```
credentials/MEMORY_PROTOCOL.md
credentials/credential_lock_manifest.md
credentials/credential_vault_complete.json
credentials/credential_vault_sanitized.json
credentials/global_lock_manifest.md
credentials/global_lock_snapshot.json
credentials/node_rsa_public_key.pem
```

## 完整清单

全部1007条资产记录（路径/大小/SHA256指纹）见同目录 `cos_manifest_full.json`。

## 恢复指引（如未来需要）

1. 所有资产源头均在服务器本地 `/opt/ZONGYUAN-ROOT/` 完好保留（当前含9/10后新增共93,928文件/1.5GB）
2. 如需恢复云端归档：向用户确认后重新开通COS/其他存储，再重新配置同步（当前守护脚本已废弃，需重新部署）
3. 当前归档通道：飞书知识库 + 多维表格台账 + 服务器本地

