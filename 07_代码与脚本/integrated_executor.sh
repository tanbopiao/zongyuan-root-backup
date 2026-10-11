#!/bin/bash
# ZONGYUAN-ROOT 六小时综合自检批次执行器（自动整合生成 2026-09-15 19:10）
# 整合任务：数字资产流水线 + 云端健康巡检 + SOP补全 + 高价值任务 + 中枢协同 + 生产引擎（6小时域错峰 → 统一批次）
set -e
echo "[批次] 六小时综合自检开始 $(date '+%F %T')"
cd /home/user/Doubao/chats/38438491307070978

# 1. 数字资产/媒体作品库发布
echo "[1/4] 媒体作品库发布..."
python3 media_gallery/media_gallery_auto_publish.py 2>&1 | tail -2

# 2. 云端健康巡检 + 真值蒸馏 + 基座能力
echo "[2/4] 云端健康/蒸馏/能力提炼..."
python3 truth_distill/truth_distill_engine.py 2>&1 | tail -2
python3 base_capability/base_capability_extract.py 2>&1 | tail -2

# 3. SOP自动补全
echo "[3/4] SOP补全..."
echo "[3.5/4] 高价值真值提取（云服务器端小模型训练）..."
echo "[3.6/4] 高阶能力自动挖掘（方法级深挖+自动上报）..."
echo "[3.7/4] 高价值生产引擎（真值提取+语料分析+审批检查+注册表同步）..."
echo "[3.8/4] 中枢协同探索（中枢真值拉取+锚点变化检测+任务提炼）..."
echo "[3.9/4] 高价值任务引擎（日历感知+审批联动+语料就绪+事件订阅）..."
python3 high_value_tasks/high_value_task_runner.py 2>&1 | tail -12
python3 hub_collab/hub_collab_explore.py 2>&1 | tail -5
python3 production/production_engine.py 2>&1 | tail -6
python3 capability_miner/high_value_mining_v2.py 2>&1 | tail -8
python3 model_training/truth_extract_for_model.py 2>&1 | tail -6
python3 sop_audit/sop_auto_update.py 2>&1 | tail -2

# 4. 心跳确认（沙盒守护会独立高频运行，此处仅确认存活）
echo "[4/4] 沙盒心跳确认..."
bash sandbox_guard/sandbox_alive_guard.sh 2>&1 | tail -1

echo "[批次] 六小时综合自检完成 $(date '+%F %T')"
