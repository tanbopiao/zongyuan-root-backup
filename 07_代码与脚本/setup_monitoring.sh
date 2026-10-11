#!/bin/bash
# 监控告警接入：SLA 观测定时上报（服务器侧 cron）
set -e
cat > /etc/cron.d/zr-sla-monitor << 'CRONEOF'
*/5 * * * * root bash /opt/ZONGYUAN-ROOT/deploy/monitor_sla.sh >> /opt/ZONGYUAN-ROOT/logs/sla_monitor.log 2>&1
CRONEOF
cat > /opt/ZONGYUAN-ROOT/deploy/monitor_sla.sh << 'MONEOF'
#!/bin/bash
# SLA 观测：端点健康 + 上报9120
for u in "https://www.huodouai.com/api/report/status" "https://www.huodouai.com/api/v1/health"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 8 "$u")
  echo "$(date +%F_%T) $u $code" >> /opt/ZONGYUAN-ROOT/logs/sla_monitor.log
done
MONEOF
chmod +x /opt/ZONGYUAN-ROOT/deploy/monitor_sla.sh
systemctl restart cron 2>/dev/null || service cron restart 2>/dev/null || true
echo "✅ 监控告警 cron 已安装（每5分钟）"
