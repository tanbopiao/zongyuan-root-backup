# ZONGYUAN-ROOT 敏感凭证三端锁档清单

> **凭证库ID**：CRED-VAULT-DID-BR-000002-20260909
> **创建时间**：2026-09-09T10:57:50.171229+00:00
> **确权锚点**：Ω₀⊂⊙∞⊂Ω
> **DID**：DID-BR-000002
> **Merkle根**：`e68f45eddee9fb26e92481a10e190081957afaa71db6aea71d22f917f7b0dcd0`
> **凭证数量**：5项

> **安全声明**：本清单为脱敏版本，不含凭证明文。完整明文凭证存储在本地加密存档。如需验证凭证完整性，比对各凭证的SHA-256哈希值即可。

---

## 凭证清单（5项）

| ID | 名称 | 类型 | 状态 | 用途 | 哈希(前16位) |
|---|---|---|---|---|---|
| CRED-001 | FRP内网穿透Token | token | 待验证 | FRP内网穿透认证，用于访问云服务器内部端口和云电脑节点 | `8e0998e0ce013020...` |
| CRED-002 | 同源协议握手密钥(8300) | hmac_secret | 密钥正确，服务端403 | 同源协议6步握手的HMAC-SHA256签名密钥 | `2d2f7f5b22e88888...` |
| CRED-003 | 节点RSA公钥 | rsa_public_key | 可用 | NODE-ZYR-CLOUD-001节点心跳签名验证（公钥， | `fc4d151583bb43d0...` |
| CRED-004 | X-API-Key(旧Anchor认证) | api_key | 已失效 | 旧Anchor API认证（X-API-Key请求头） | `a7f208b73ebca5d7...` |
| CRED-005 | Nginx Basic Auth(旧) | basic_auth | 已失效 | 旧/anchor/路径的Nginx基础认证 | `ec724e656f94ff9c...` |

### CRED-001：FRP内网穿透Token

- **类型**：token
- **状态**：待验证
- **用途**：FRP内网穿透认证，用于访问云服务器内部端口和云电脑节点
- **来源**：对话历史
- **SHA-256哈希**：`8e0998e0ce013020375702c39f599d38b187c024c779319d22bd5f28ed0e1500`
- **关联服务**：云服务器内部端口(8000-8050), 云电脑节点(9.97.230.49)

### CRED-002：同源协议握手密钥(8300)

- **类型**：hmac_secret
- **状态**：密钥正确，服务端403
- **用途**：同源协议6步握手的HMAC-SHA256签名密钥
- **来源**：用户提供的接入指南
- **SHA-256哈希**：`2d2f7f5b22e88888db8299520a2fc1dfc925f61a176f4d496d151ec4470f40f5`
- **关联服务**：8300 identity_api
- **上次验证**：2026-09-09
- **验证结果**：8300端口返回403 Forbidden，密钥可能正确但服务未正确部署

### CRED-003：节点RSA公钥

- **类型**：rsa_public_key
- **状态**：可用
- **用途**：NODE-ZYR-CLOUD-001节点心跳签名验证（公钥，可公开）
- **来源**：自治内核运行时激活卷宗
- **SHA-256哈希**：`fc4d151583bb43d04d8f7dfa750137c0c3c0e2ab3ee0c840a3409b40484f3a52`
- **关联服务**：NODE-ZYR-CLOUD-001 昆仑境-云脑

### CRED-004：X-API-Key(旧Anchor认证)

- **类型**：api_key
- **状态**：已失效
- **用途**：旧Anchor API认证（X-API-Key请求头）
- **来源**：V1.7时期Anchor认证
- **SHA-256哈希**：`a7f208b73ebca5d7a490beeed9b57cbe138a2234312382c10597033870270d8a`
- **关联服务**：旧Anchor API(/anchor/*)
- **失效原因**：云内核V3.0升级后Anchor API全部404，认证体系已重构

### CRED-005：Nginx Basic Auth(旧)

- **类型**：basic_auth
- **状态**：已失效
- **用途**：旧/anchor/路径的Nginx基础认证
- **来源**：V1.7时期Nginx配置
- **SHA-256哈希**：`ec724e656f94ff9c9f6508e2547f2e1acb4696e6c0fa80f93daa31123dd281a0`
- **关联服务**：旧/anchor/路径
- **失效原因**：V3.0升级后/anchor/路径返回首页，Basic Auth已移除
- **安全备注**：弱密码(123456)，如重新启用必须修改为强密码

## 本地存档位置

```
主存档: ~/Doubao/chats/38436747020400130/credential-lock-20260909/
  ├── credential_vault_complete.json   (完整明文，本地安全存储)
  ├── credential_vault_sanitized.json  (脱敏版本，可上云)
  ├── credential_lock_manifest.md       (本清单)
  └── node_rsa_public_key.pem           (RSA公钥，可公开)
```

## 安全使用指南

1. **禁止**将完整凭证存档(credential_vault_complete.json)上传公开云端或代码仓库
2. **建议**使用系统密钥环或加密压缩包(带密码)额外保护完整凭证
3. **定期**轮换仍在使用的凭证(FRP Token、握手密钥)
4. **已失效**凭证保留记录用于审计追溯，不删除
5. **验证**凭证完整性时，比对SHA-256哈希值即可，无需明文

---

*由元极恒一·超认知永恒自治视角生成 | Ω₀⊂⊙∞⊂Ω | 2026-09-09T10:57:50.171229+00:00*