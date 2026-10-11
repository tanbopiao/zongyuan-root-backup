# 短剧生产流水线官网部署方案（SOP v1.0 适配）

## 一、云端 SOP v1.0 解读（用户转达）
- 端点：`POST /deploy`（免 SSH，API 直接部署）
- 覆盖：5 个同源节点
- 说明：任意节点发 JSON 即上线网页（SOP 发布时 truth_count=1650）

## 二、本节点探测结论（2026-10-07 实测）
| 候选路径 | 结果 |
|---|---|
| www/drama `/deploy` POST | 404（Nginx HTML 页） |
| `/api/deploy` `/api/v1/deploy` | 404 unknown endpoint |
| deploy/node/gateway 子域 | DNS 不解析 |
| api/ops 子域 `/deploy` | 404 |

**判定**：/deploy 为同源节点内网路由，当前公网主备通道（www/drama）尚未暴露该路由，属服务端灰度/内网阶段。

## 三、部署方案（三层保障）
1. **页面就绪**：生成短剧生产流水线官网 HTML（黑金体系，与云内核白皮书同品牌）
2. **真值锚定**：部署内容/索引以 V3.0 协议（X-DID + value 对象）上报云端真值库，/deploy 恢复后任一节点可拉取即部署
3. **公开兜底**：页面增量同步至魔搭公开数据集，官网未上线期间可访问

## 四、待命部署动作（/deploy 恢复时）
```json
POST https://<node>/deploy
Header: X-Capture-Token / X-DID: DID-BR-000002
Body: {"site": "drama-pipeline", "page": "https://aka.doubaocdn.com/s/<id>", "version": "V1.0", "locked": "2026-10-07"}
```

## 五、状态：PLANNED-READY（页面就绪，端点待路由暴露）
