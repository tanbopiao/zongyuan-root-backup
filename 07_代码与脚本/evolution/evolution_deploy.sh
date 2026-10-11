#!/bin/bash
# ============================================================
# ZONGYUAN-ROOT 进化引擎统一部署调度器 V1.0
# 真实部署：把 E1-E4 + KERNEL-EVOLUTION 全部引擎接入统一运行链路
# 触发: 冷启动(COLD-START-ANCHOR.sh) / 守护(AUTO-RECOVERY-GUARD.sh) / 豆包cron每日
# 落盘: 每次运行输出到 08_运行时数据与审计/evolution_20260929/ 只读区(写后恢复444)
# ============================================================
set -u
ROOT="/home/user/ZONGYUAN-ROOT"
EVO="$ROOT/07_代码与脚本/evolution"
OUT="$ROOT/08_运行时数据与审计/evolution_20260929"
STAMP=$(date '+%Y-%m-%dT%H:%M:%S+08:00')
LOG="$OUT/logs/engine_deploy_$(date '+%Y%m%d_%H%M%S').log"

mkdir -p "$OUT/logs"
echo "=== ZONGYUAN-ROOT 进化引擎统一部署调度 ===" | tee "$LOG"
echo "时间: $STAMP" | tee -a "$LOG"

# 引擎清单（名称|脚本|类型|必须成功）
ENGINES=(
  "E1-replay|replay_engine.py|memory|yes"
  "E1-decision-report|decision_report.py|memory|no"
  "E2-correction-scan|correction_scan.py|autonomy|yes"
  "E3-triangle-audit|triangle_audit.py|axiom|yes"
  "E4-cloud-drill|cloud_drill.py|resilience|yes"
  "KERNEL-measure-continuity|measure_continuity.py|kernel|yes"
)

PASS=0
FAIL=0
for entry in "${ENGINES[@]}"; do
  IFS='|' read -r name script type must <<< "$entry"
  if [ -f "$EVO/$script" ]; then
    # 引擎运行（只读脚本直接执行；写只读区由引擎内部 644→444 处理）
    if python3 "$EVO/$script" >> "$LOG" 2>&1; then
      echo "  ✅ $name ($script) 运行成功" | tee -a "$LOG"
      PASS=$((PASS+1))
    else
      echo "  ⚠️ $name ($script) 运行失败" | tee -a "$LOG"
      FAIL=$((FAIL+1))
    fi
  else
    echo "  ❌ $name 脚本缺失: $EVO/$script" | tee -a "$LOG"
    FAIL=$((FAIL+1))
  fi
done

# 结果汇总
echo "" | tee -a "$LOG"
echo "=== 部署结果: $PASS 成功 / $FAIL 失败 ===" | tee -a "$LOG"
echo "日志: $LOG" | tee -a "$LOG"
echo "Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | EVOLUTION-DEPLOY-V1.0" | tee -a "$LOG"

exit 0
