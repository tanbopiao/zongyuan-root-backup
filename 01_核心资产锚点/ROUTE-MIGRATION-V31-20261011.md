# 云端读取路由迁移说明 V3.1

## 变更时间
2026-10-11 四端对账发现

## 旧路由（已废弃，全部404）
- GET /api/truth/{key}  （路径参数）
- GET /api/truths/      （列表）

## 新路由（当前可用）
- GET /api/truth?key={key}  （query参数）
- GET /api/status           （健康状态+Merkle根+truth_count）
- POST /api/report/truth    （写入，不变）

## 迁移规则
所有脚本中：
  curl .../api/truth/KEY  →  curl .../api/truth?key=KEY

## 注意
- Merkle根是动态值，每次写入都会变化，不能做固定基线对比
- 应做时序漂移检测：记录每次采集的merkle_root，监控异常跳变
- 待复核队列pending_verify_20260921.json中2条key已过期，标记归档

## 影响范围
- 待复核队列：已用新路由回读，2条过期
- 运行时脚本：需在云端母本节点批量迁移
- 本地历史文档/训练数据集：含旧路由引用但不影响运行
