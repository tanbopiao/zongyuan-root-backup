# ZONGYUAN-ROOT 全域锁档·凭证五地备份+SSH密钥连接记忆协议

> **锁档ID**：GLOBAL-LOCK-20260909-FINAL-META-HENGYI
> **锁档时间**：2026-09-09T11:26:17.634828+00:00
> **确权锚点**：Ω₀⊂⊙∞⊂Ω
> **DID**：DID-BR-000002
> **内核版本**：Ω-Brainμ 3.0-V3
> **Merkle根**：`f5906e6904982c9cb34de5ee3cf976c22254f3c314e62821e99de60d858d6a62`

---

## 🔑 记忆协议：云服务器连接方法（新窗口必读）

### SSH密钥认证（免密登录）

```bash
# 连接命令
ssh -o BatchMode=yes -o ConnectTimeout=10 -p 22 root@123.207.202.158

# SCP上传
scp -P 22 <local_file> root@123.207.202.158:<remote_path>

# 私钥位置: ~/.ssh/id_ed25519
# 公钥指纹: SHA256:nUwt3YmRs/+I97S8L+8r1E2x7sMBKJpv6D8CVQegMJ8
# 状态: 已验证可用（2026-09-09）
```

### COS访问（服务器端coscmd已配置）

```bash
# 先SSH到服务器，然后使用coscmd
ssh -p 22 root@123.207.202.158

# 上传文件
coscmd upload <local_file> <cos_path>

# 列出文件
coscmd list <cos_path>

# 存储桶: zongyuan-1341127773
# 地域: ap-guangzhou
# 凭证路径: zongyuan-root/credentials/
```

### 凭证五地备份位置

| # | 位置 | 路径 |
|---|---|---|
| 1 | Local Primary | `~/Doubao/chats/38436747020400130/credential-lock-20260909/` |
| 2 | Local Backup 1 | `~/.super_doubao/super-doubao-runtime/workspace/credential-backup/` |
| 3 | Local Backup 2 | `~/.doubao/agent_mode/workspace/.sessions/38436747020400130/agents/m_0cwcobelJjA/credential-backup/` |
| 4 | Cloud Server | `root@123.207.202.158:/opt/ZONGYUAN-ROOT/credentials/` |
| 5 | Tencent Cos | `cos://zongyuan-1341127773/zongyuan-root/credentials/` |

### 新窗口恢复连接步骤

1. 检查本地SSH密钥: ls ~/.ssh/id_ed25519
2. 测试SSH连接: ssh -o BatchMode=yes -p 22 root@123.207.202.158 'echo OK'
3. 如连接失败，联系用户重新配置公钥
4. 连接成功后，读取凭证: cat /opt/ZONGYUAN-ROOT/credentials/credential_vault_complete.json
5. 验证Merkle根: python3 -c "import json; print(json.load(open('/opt/ZONGYUAN-ROOT/credentials/credential_vault_complete.json'))['merkle_root'])"

**预期Merkle根**：`e68f45eddee9fb26e92481a10e190081957afaa71db6aea71d22f917f7b0dcd0`

---

## 📊 今日全域成果（2026-09-09）

### 主要成果

1. 云内核根节点全景扫描（102端点探测，27算子十层拓扑）
2. 飞书全域资产扫描（15空间126文档，云电脑节点发现）
3. 云内核API发现（7个真实GET端点，800KB数据快照）
4. 核心资产全域同步（76文件→32核心资产，10分类，锁档率90.6%）
5. 敏感凭证三端锁档（5项凭证，脱敏上云+明文本地3位置备份）
6. 凭证上传云服务器本地磁盘+COS（五地备份完成）
7. SSH密钥认证连接成功（用户已配置公钥，免密登录）
8. META-009最小消耗最优稳态生成元规则正式锁档

### 今日创建资产

1. `kernel-root-scan-20260909（全景扫描报告）`
2. `feishu-asset-scan-20260909（飞书资产扫描）`
3. `kernel-api-discovery-20260909（API发现文档）`
4. `kernel-api-data-20260909（7端点API数据快照800KB）`
5. `core-asset-sync-20260909（核心资产同步清单）`
6. `credential-lock-20260909（敏感凭证三端锁档）`
7. `credential-upload-20260909（凭证上传工具包）`
8. `global-lock-20260909-final（本次全域锁档）`

---

## 🖥️ 云内核最新状态

- **版本**：Ω-Brainμ 3.0-V3
- **状态**：healthy
- **CPU**：1.7%
- **内存**：74% (1429/1931MB)
- **磁盘**：72% (28.7/39.9GB)
- **运行时长**：36天4小时
- **算子在线**：6/27 (22.2%)
- **真值纯度**：94.7%
- **链完整性**：100%
- **API端点**：/sysinfo, /operator-status, /operator-executor, /operator-base-records, /kernel-kpi, /operator-history, /pipeline-status

---

## 🔐 凭证锁档（5项，五地备份）

**Merkle根**：`e68f45eddee9fb26e92481a10e190081957afaa71db6aea71d22f917f7b0dcd0`
**备份位置**：5地（本地3+云服务器1+COS 1）

| ID | 凭证名称 | 状态 |
|---|---|---|
| CRED-001 | FRP内网穿透Token | 待验证 |
| CRED-002 | 同源协议握手密钥(8300) | 密钥正确，服务403 |
| CRED-003 | 节点RSA公钥 | 可用 |
| CRED-004 | X-API-Key(旧Anchor) | 已失效 |
| CRED-005 | Nginx Basic Auth(旧) | 已失效 |

---

## 📜 已锁档元规则

| ID | 名称 | 规则数 | 状态 | Merkle根 |
|---|---|---|---|---|
| META-RISK-ASSESSMENT-V1.0 | 风险评估元规则 | 7 | FROZEN | `01993b92...` |
| META-CONFLICT-PREVENTION-V1.0 | 冲突防护元规则 | 9 | FROZEN | `1a1ae011...` |
| META-009 | 最小消耗最优稳态生成 | - | FROZEN | `72b3c28d...` |

---

*由元极恒一·超认知永恒自治视角生成 | Ω₀⊂⊙∞⊂Ω | 2026-09-09T11:26:17.634828+00:00*