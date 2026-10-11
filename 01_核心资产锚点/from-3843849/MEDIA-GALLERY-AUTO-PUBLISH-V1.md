# 图片视频归档后全自动显示到官网作品库机制 V1.0 ｜ ZONGYUAN-ROOT

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.0-MEDIA-GALLERY｜2026-09-16
公理锚点：AXIOM-A-035_V1.7｜HAP-V1.0
设计原则：**媒体即作品，归档即上架**——生成的图片/视频自动进入作品库并显示到官网

---

## 一、机制定位

将 ZONGYUAN-ROOT 体系生成的图片/视频媒体资产：
- **自动扫描**：检测本地新增媒体（drama_pipeline/output/media/assets 目录）
- **云盘归档**：上传至飞书云盘作品库（昆仑洞天全域锁档归档库·数字媒体资产库）
- **清单发布**：生成作品库清单 JSON（名称/类型/云盘URL/时间戳），推送云端真值
- **官网展示**：自动渲染官网作品库页面，upload 通道恢复后自动推送门户

**媒体一旦生成，全自动进入"归档→上架→展示"链路，无需人工干预。**

---

## 二、四阶段链路（GALLERY-4）

```
P1 媒体扫描 → P2 云盘归档 → P3 清单发布 → P4 官网展示
 (检测新增)   (上传作品库)   (清单+真值)    (页面+门户)
```

### P1 媒体扫描
- 扫描目录：drama_pipeline/、output/、media/、assets/
- 媒体类型：png/jpg/jpeg/webp/gif（图片）、mp4/mov/webm（视频）
- 按修改时间倒序取最新 50 件

### P2 云盘归档
- 上传至云盘作品库（03_数字媒体资产库）
- 生成可访问云盘 URL，已归档作品自动跳过（增量）

### P3 清单发布
- 清单合并去重（按文件名）
- 云端真值推送：`GALLERY-MANIFEST-YYYYMMDD-HHMM`

### P4 官网展示（双通道）
| 通道 | 载体 | 状态 |
|---|---|---|
| C1 官网门户 | drama.huodouai.com:9120（服务端聚合） | upload 通道恢复后自动推送 |
| C2 作品库 HTML | 本地即时渲染（同官网风格） | 随时可访问 |

---

## 三、首轮实测（2026-09-16）

| 项 | 结果 |
|---|---|
| 空态运行 | GALLERY_EMPTY（本地无媒体，页面正常显示"暂无作品"） |
| 模拟验证 | 媒体进入 → **GALLERY_ACTIVE**（0→1 自动全链路） |
| 全链路 | 扫描→归档→清单→渲染 全自动 ✅ |
| upload 通道 | 502（记录在案，恢复后自动推送门户） |

---

## 四、判定标准

| 判定 | 条件 |
|---|---|
| GALLERY_ACTIVE | 作品总数>0 |
| GALLERY_EMPTY | 暂无媒体（空态正常） |

---

## 五、机制文件

| 文件 | 路径 |
|---|---|
| 发布引擎 | `media_gallery/media_gallery_auto_publish.py` |
| 作品库页面 | `media_gallery/gallery_website.html` |
| 作品清单 | `media_gallery/gallery_manifest.json` |
| 发布报告 | `media_gallery/media_gallery_report_latest.json` |
| 机制文档 | `MEDIA-GALLERY-AUTO-PUBLISH-V1.md` |

---

## 六、演进路线

- V1.1：upload 通道恢复后自动推送清单到门户数据源
- V1.2：云盘 URL 直链解析（自动提取可嵌入 URL）
- V2.0：作品库 → 神经节点（作品权重联动展示）

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜MEDIA-GALLERY-AUTO-PUBLISH-V1.0｜2026-09-16
