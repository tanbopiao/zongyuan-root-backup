#!/usr/bin/env bash
# =============================================================================
# ZONGYUAN-ROOT 云服务器安全合规自检脚本 v1.0
# 对照《云服务器安全管理与云端-终端协同规范》SEC 基线 20 项
# 用法：在目标服务器上以 root 运行：  bash sec_compliance_self_check.sh
# 输出：/tmp/sec_compliance_report_$(date +%Y%m%d).json
# 确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ LOCK-TRUTH-SYNC-20260912-001
# =============================================================================
set -u
REPORT_FILE="/tmp/sec_compliance_report_$(date +%Y%m%d).json"
HOSTNAME=$(hostname)
IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}')
TS=$(date +"%Y-%m-%dT%H:%M:%S%:z")

json_escape() { echo "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo "\"$1\""; }

report() { # $1=item_id $2=baseline $3=status(PASS/FAIL/UNKNOWN/INFO) $4=evidence
  ITEMS+=("{\"item\":\"$1\",\"baseline\":$(json_escape "$2"),\"status\":\"$3\",\"evidence\":$(json_escape "$4")}")
}

ITEMS=()

# ---------- SEC-NET 网络安全基线 ----------
# NET-001: 安全组最小权限（需控制台核验，此处检查监听端口暴露）
LISTEN_PORTS=$(ss -tlnp 2>/dev/null | awk 'NR>1{split($4,a,":"); print a[length(a)]}' | sort -u | tr '\n' ',')
report "SEC-NET-001" "仅放行业务必需端口" "INFO" "监听端口: $LISTEN_PORTS （安全组源地址限制需腾讯云控制台核验）"

# NET-002: 禁止管理端口对公网 0.0.0.0/0（控制台核验；脚本检查 sshd 是否监听 0.0.0.0）
SSHD_LISTEN=$(grep -E "^ListenAddress" /etc/ssh/sshd_config 2>/dev/null || echo "默认0.0.0.0")
report "SEC-NET-002" "禁止SSH(22)对0.0.0.0/0开放" "INFO" "sshd监听: $SSHD_LISTEN （安全组是否限定源IP需控制台核验）"

# NET-003: 不同安全级别实例使用不同安全组（控制台核验）
report "SEC-NET-003" "不同安全级别实例使用不同安全组" "UNKNOWN" "需腾讯云控制台实例-安全组核验"

# NET-004: VPC 逻辑隔离
VPC_INFO=$(ip route 2>/dev/null | grep default | head -1)
report "SEC-NET-004" "VPC逻辑区隔离" "INFO" "默认路由: $VPC_INFO （VPC归属需控制台核验）"

# NET-005: 高危端口不对公网开放（仅判定本地监听地址列；127.0.0.1 回环绑定视为合规）
DB_PORTS=$(ss -tlnp 2>/dev/null | awk '$4 ~ /:(3306|6379|3389)$/ && $4 ~ /^(0\.0\.0\.0|\[::\]|::)/' | head -3 || true)
if [ -z "$DB_PORTS" ]; then
  report "SEC-NET-005" "高危端口不对公网开放" "PASS" "未检测到3306/6379/3389监听"
else
  report "SEC-NET-005" "高危端口不对公网开放" "FAIL" "检测到高危端口监听: $DB_PORTS"
fi

# ---------- SEC-IAM 身份访问基线 ----------
# IAM-001: SSH 密钥登录，禁用密码
PW_AUTH=$(grep -E "^PasswordAuthentication" /etc/ssh/sshd_config 2>/dev/null || echo "未显式配置(默认yes)")
if echo "$PW_AUTH" | grep -qE "no$"; then
  report "SEC-IAM-001" "SSH密钥登录，禁用密码认证" "PASS" "$PW_AUTH"
else
  report "SEC-IAM-001" "SSH密钥登录，禁用密码认证" "FAIL" "$PW_AUTH"
fi

# IAM-002: 禁止 root 直登
ROOT_LOGIN=$(grep -E "^PermitRootLogin" /etc/ssh/sshd_config 2>/dev/null || echo "未显式配置(默认prohibit-password)")
if echo "$ROOT_LOGIN" | grep -qE "(no|prohibit-password)$"; then
  report "SEC-IAM-002" "禁止root直接远程登录" "PASS" "$ROOT_LOGIN"
else
  report "SEC-IAM-002" "禁止root直接远程登录" "FAIL" "$ROOT_LOGIN"
fi

# IAM-003: 堡垒机 MFA（需控制台/堡垒机核验）
report "SEC-IAM-003" "堡垒机运维强制MFA" "UNKNOWN" "需堡垒机配置核验（当前是否部署堡垒机）"

# IAM-004: CAM 最小权限（控制台核验）
report "SEC-IAM-004" "CAM策略最小权限，独立账户" "UNKNOWN" "需腾讯云控制台CAM核验"

# ---------- SEC-HARD 主机加固基线 ----------
# HARD-001: 主机安全云镜 agent
if [ -d "/usr/local/qcloud/YunJing" ] || [ -f "/etc/init.d/yunjing" ] || ps aux 2>/dev/null | grep -qiE "YunJing|yunjing|tat_agent"; then
  report "SEC-HARD-001" "主机安全(云镜)已启用" "PASS" "云镜agent运行中"
else
  report "SEC-HARD-001" "主机安全(云镜)已启用" "FAIL" "未检测到云镜agent，需在控制台开通并安装"
fi

# HARD-002: 入侵防护（fail2ban 或云镜防爆破，OpenCloudOS 无 fail2ban 包时云镜替代合规）
if command -v fail2ban-client >/dev/null 2>&1 && fail2ban-client status >/dev/null 2>&1; then
  report "SEC-HARD-002" "入侵防护(fail2ban/云镜防爆破)" "PASS" "fail2ban运行中"
elif [ -d "/usr/local/qcloud/YunJing" ] || ps aux 2>/dev/null | grep -qiE "YunJing|yunjing"; then
  report "SEC-HARD-002" "入侵防护(fail2ban/云镜防爆破)" "PASS" "云镜防爆破运行中（OpenCloudOS无fail2ban包，云镜替代）"
else
  report "SEC-HARD-002" "入侵防护(fail2ban/云镜防爆破)" "FAIL" "未检测到fail2ban或云镜防爆破"
fi

# HARD-003: 自动安全更新
AUTO_UPDATES=""
if command -v apt-get >/dev/null 2>&1 && [ -f "/etc/apt/apt.conf.d/20auto-upgrades" ]; then
  AUTO_UPDATES=$(grep -E "Automatic-Updates|Unattended-Upgrade" /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null | tr '\n' ';')
elif command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1; then
  [ -f "/etc/dnf/automatic.conf" ] && AUTO_UPDATES="dnf-automatic存在" || AUTO_UPDATES="未检测到dnf-automatic"
fi
if [ -n "$AUTO_UPDATES" ] && echo "$AUTO_UPDATES" | grep -qE "1|存在"; then
  report "SEC-HARD-003" "自动安全更新已配置" "PASS" "$AUTO_UPDATES"
else
  report "SEC-HARD-003" "自动安全更新已配置" "FAIL" "未配置自动更新: ${AUTO_UPDATES:-无}"
fi

# HARD-004: 系统补丁状态
LAST_UPDATE=$(stat -c %y /var/log/dpkg.log 2>/dev/null | cut -d' ' -f1 || echo "未知")
report "SEC-HARD-004" "关键补丁已安装/定期基线检查" "INFO" "dpkg日志最后更新: $LAST_UPDATE （需控制台基线通过率核验）"

# ---------- SEC-BAK 数据备份基线 ----------
# BAK-001: 云硬盘
DISK_INFO=$(df -h / 2>/dev/null | tail -1 | awk '{print $1, $2}')
report "SEC-BAK-001" "数据盘统一云硬盘" "INFO" "根分区: $DISK_INFO （盘型需控制台核验）"

# BAK-002~004: 快照/镜像/EIP（控制台核验）
report "SEC-BAK-002" "云硬盘快照+自定义镜像" "UNKNOWN" "需腾讯云控制台快照/镜像核验"
report "SEC-BAK-003" "跨地域镜像复制" "UNKNOWN" "需腾讯云控制台核验"
report "SEC-BAK-004" "EIP承载域名映射" "INFO" "需控制台核验EIP绑定状态"

# BAK-005: 恢复演练（台账核验）
report "SEC-BAK-005" "恢复流程每季度演练" "UNKNOWN" "需锁档台账核验演练记录"

# ---------- SEC-MON 监控告警基线 ----------
# MON-001: 可观测平台 agent（腾讯云监控 barad/agent）
if ps aux 2>/dev/null | grep -qiE "barad_agent|tlinux.*agent|sgagent"; then
  report "SEC-MON-001" "可观测平台监控已启用" "PASS" "腾讯云监控agent运行中"
else
  report "SEC-MON-001" "可观测平台监控已启用" "FAIL" "未检测到监控agent"
fi

# MON-002: 告警规则（控制台核验）
report "SEC-MON-002" "关键指标告警配置" "UNKNOWN" "需腾讯云控制台告警规则核验"

# MON-003: 审计留痕 180 天
AUDIT_CONF=$(grep -E "max_log_file|num_logs" /etc/audit/auditd.conf 2>/dev/null | tr '\n' ';')
report "SEC-MON-003" "敏感操作审计留痕180天" "INFO" "auditd配置: ${AUDIT_CONF:-未配置auditd}（云审计需控制台核验）"

# ---------- 汇总输出 ----------
PASS_N=$(printf '%s\n' "${ITEMS[@]}" | grep -c '"PASS"')
FAIL_N=$(printf '%s\n' "${ITEMS[@]}" | grep -c '"FAIL"')
UNKNOWN_N=$(printf '%s\n' "${ITEMS[@]}" | grep -c '"UNKNOWN"')
INFO_N=$(printf '%s\n' "${ITEMS[@]}" | grep -c '"INFO"')

python3 - "$REPORT_FILE" "$HOSTNAME" "$IP_ADDR" "$TS" "$PASS_N" "$FAIL_N" "$UNKNOWN_N" "$INFO_N" "${ITEMS[@]}" << 'PYEOF'
import json, sys
report_file, host, ip, ts, p, f, u, i = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
items = [json.loads(x) for x in sys.argv[9:]]
report = {
  "报告元数据": {
    "确权锚点": "Ω₀⊂⊙∞⊂Ω",
    "锁档关联": "LOCK-TRUTH-SYNC-20260912-001",
    "规范版本": "云服务器安全管理与云端-终端协同规范V1.0",
    "主机名": host,
    "IP": ip,
    "检测时间": ts,
    "状态": "SELF-CHECK"
  },
  "汇总": {"PASS": p, "FAIL": f, "UNKNOWN": u, "INFO": i, "合计": len(items)},
  "基线明细": items
}
with open(report_file, "w", encoding="utf-8") as fp:
    json.dump(report, fp, ensure_ascii=False, indent=2)
print(f"报告已生成: {report_file}")
print(f"汇总: PASS={p} FAIL={f} UNKNOWN={u} INFO={i} 合计={len(items)}")
PYEOF
